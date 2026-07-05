#!/usr/bin/env python3
"""Facts-file key resolution and repo-anchor/project-key derivation (SRP leaf).

Two responsibilities, both stdlib-only and agent-agnostic:

1. **Facts-FILE key resolution.** Parses ``.ai-playbook/facts.md`` for keys that
   live in DIFFERENT on-disk formats (r2 Blocker - they cannot share one parser):
   - ``plans_dir`` / ``tmp_dir`` are TOML-fence ``key = "value"`` lines in the
     REPO facts file -> ``resolve_toml_key`` -> ``resolve_plans_dir`` /
     ``resolve_tmp_dir``.
   - ``shared_docs_dir`` is a markdown table row ``| `key` | `value` |`` searched
     repo-first then home -> ``resolve_table_key`` -> ``resolve_shared_docs_dir``
     / ``user_corpus_path`` (MOVED byte-identical from ``lessons_migrate.py``).
   There is NO generic ``resolve_facts_key``: the format split is real, and one
   parser silently returns ``None`` for the other format (Family H/D).

2. **Repo-anchor / project-key derivation** (git-based; does NOT read the facts
   file). ``resolve_project_key(start_dir) -> str`` returns a stable 16-char hex
   project hash for the skill-gate marker filename, composing git-toplevel
   resolution + sha1 hexdigest. On the git-failure branch it writes
   ``keying=no-anchor`` to ``~/.ai-playbook/logs/hooks.log`` via the shared
   ``_append_hooks_log_line`` helper before returning a cwd-derived hash. NEVER
   raises. See the plan's Terms (Skill-gate marker steps 1-4).

r15-L4 NOTE: the project-key path owns ONE observability side effect (the
``no-anchor`` log line); acceptable for v1. If a SECOND leaf-side log token
appears, extract ``resolve_project_key`` (and its log write) into its own leaf
(``project_key.py``), leaving this file as pure facts-file parsing.

Stdlib only. No sibling imports (the bootstrap line below is harmless and keeps
the scripts-dir leaf set uniform with ``lessons_corpus.py`` / ``lessons_adopt.py``).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow sibling imports whether run as a script or via ``python -m``. This leaf is
# stdlib-only today; the bootstrap is harmless and keeps the scripts-dir leaves
# uniform (mirrors lessons_corpus.py / lessons_adopt.py).
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Named constant (r17): the SINGLE source for the resolver's
# ``subprocess.run(..., timeout=RESOLVER_GIT_TIMEOUT_S)``. The doctor's
# ``timeout > RESOLVER_GIT_TIMEOUT_S`` bound and the #doctor_agy_timeout selftest
# import this symbol, so a rename/move breaks them loudly at import time.
RESOLVER_GIT_TIMEOUT_S = 5


# --------------------------------------------------------------------------- #
# hooks.log shared helper (r17). The SINGLE contract home for the hooks.log
# write: the resolver's ``no-anchor`` line and (later) the cores'
# ``env-var`` / ``project-only`` lines all call this. Stated NOWHERE else.
# --------------------------------------------------------------------------- #
def _append_hooks_log_line(payload: dict) -> None:
    """Append ONE JSON line to ``~/.ai-playbook/logs/hooks.log``.

    Body (the makedirs + open + write recipe, stated ONCE here): makedirs the
    logs dir, open the file with ``O_WRONLY|O_CREAT|O_APPEND|O_NOFOLLOW``, and
    write ``json.dumps(payload, default=str) + "\\n"`` in a single ``os.write``.

    The makedirs, the open, AND the write are ALL wrapped in ONE
    ``try/except OSError`` and SILENT on failure (NEVER raises). Defensive
    choices:
    - ``default=str`` is REQUIRED (SERIALIZE-DEFENSIVELY, r18-M3): bare
      ``json.dumps`` raises ``TypeError``/``ValueError`` (NOT ``OSError``) on a
      non-serializable field (a caller passing ``datetime.now()`` for ``ts``),
      which escapes the silent-catch and violates NEVER-raises. ``default=str``
      covers the realistic non-serializable scalars (``datetime``/``Path``/
      ``bytes``). A circular payload or a value whose ``__str__`` raises still
      escapes and is the caller's responsibility (PRECONDITION: ``payload`` is an
      acyclic dict of str-coercible-without-raising values).
    - makedirs in the SAME except (r17-L1): a read-only ``~/.ai-playbook/``
      parent makes makedirs raise ``PermissionError``; the single
      ``try/except OSError`` covers it so the gate stays unaffected.
    - ``O_NOFOLLOW`` refuses a pre-planted symlink at the leaf; ``O_APPEND``
      offset-atomicity + the single sub-4096-byte write keep concurrent appends
      non-interleaving and parseable line-by-line.
    """
    try:
        logs_dir = Path.home() / ".ai-playbook" / "logs"
        os.makedirs(logs_dir, exist_ok=True, mode=0o700)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        fd = os.open(logs_dir / "hooks.log", flags, 0o600)
        try:
            line = (json.dumps(payload, default=str) + "\n").encode()
            os.write(fd, line)
        finally:
            os.close(fd)
    except OSError:
        # Silent: this is observability-only metadata. NEVER raises.
        return


# --------------------------------------------------------------------------- #
# Facts-FILE key resolution (TWO parsers; no generic resolver).
# --------------------------------------------------------------------------- #
def resolve_toml_key(start_dir: Path, key: str) -> Path | None:
    """Parse the REPO ``.ai-playbook/facts.md`` TOML-fence block for ``key``.

    The repo facts file opens a ```toml fenced block containing
    ``key = "value"`` lines. Returns the resolved value as a ``Path`` (tilde-
    expanded, resolved), or ``None`` if the file or key is absent.

    ``start_dir`` is the directory whose ``.ai-playbook/facts.md`` is read (the
    repo root). TOML-fence keys are repo-scoped, so ONLY the repo candidate is
    consulted (NOT the home facts file).
    """
    facts_path = Path(start_dir) / ".ai-playbook" / "facts.md"
    if not facts_path.is_file():
        return None
    try:
        text = facts_path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Extract the FIRST ```toml fenced block (opening fence to its closer).
    in_toml = False
    for line in text.splitlines():
        if not in_toml:
            if line.lstrip().startswith("```toml"):
                in_toml = True
            continue
        # Inside the fence: a closing fence ends the block.
        if line.lstrip().startswith("```"):
            break
        m = re.match(r'^\s*(' + re.escape(key) + r')\s*=\s*"([^"]*)"\s*$', line)
        if m:
            return Path(m.group(2).strip()).expanduser().resolve()
    return None


def resolve_table_key(start_dir: Path, key: str) -> Path | None:
    """Parse a markdown table row ``| `key` | `value` |`` for ``key``.

    Searches ``<start_dir>/.ai-playbook/facts.md`` FIRST then
    ``~/.ai-playbook/facts.md`` (repo-first two-candidate order, byte-identical
    to the original ``resolve_shared_docs_dir``). The key cell is
    inline-code-wrapped (`` `key` ``); the value cell may be tilde-prefixed
    (e.g. `` `~/Projects/.ai-playbook/` ``). Returns the resolved value as a
    ``Path`` (tilde-expanded, resolved), or ``None`` if absent.
    """
    pattern = re.compile(
        r"^\|\s*`" + re.escape(key) + r"`\s*\|\s*`?([^|`]+?)`?\s*\|",
        re.MULTILINE,
    )
    candidates = [
        Path(start_dir) / ".ai-playbook" / "facts.md",
        Path.home() / ".ai-playbook" / "facts.md",
    ]
    for facts_path in candidates:
        if not facts_path.is_file():
            continue
        try:
            text = facts_path.read_text(encoding="utf-8")
        except OSError:
            continue
        m = pattern.search(text)
        if m:
            return Path(m.group(1).strip()).expanduser().resolve()
    return None


def resolve_plans_dir(start_dir: Path) -> Path | None:
    """Resolve ``plans_dir`` (TOML-fence key; backs plan-file classification)."""
    return resolve_toml_key(start_dir, "plans_dir")


def resolve_tmp_dir(start_dir: Path) -> Path | None:
    """Resolve ``tmp_dir`` (TOML-fence key; backs temp-artifact placement)."""
    return resolve_toml_key(start_dir, "tmp_dir")


def resolve_shared_docs_dir(start_dir: Path) -> Path | None:
    """Resolve ``shared_docs_dir`` (markdown table row; backs user corpus path).

    MOVED byte-identical from ``lessons_migrate.py`` (including the repo-first
    two-candidate search order). The value lives in ``.ai-playbook/facts.md`` as
    a markdown table row whose key cell is inline-code-wrapped and whose value
    cell is tilde-prefixed. Searched repo-first then user-home. Returns ``None``
    if absent.
    """
    return resolve_table_key(start_dir, "shared_docs_dir")


def user_corpus_path(start_dir: Path) -> Path | None:
    """Return the user-level corpus path (``<shared_docs_dir>/development_lessons.md``)."""
    base = resolve_shared_docs_dir(start_dir)
    if base is None:
        return None
    return base / "development_lessons.md"


# --------------------------------------------------------------------------- #
# Repo-anchor / project-key derivation (git-based; does NOT read the facts file).
# --------------------------------------------------------------------------- #
def resolve_project_key(start_dir) -> str:
    """Return a stable 16-char hex project hash for ``start_dir``.

    Algorithm (Terms, Skill-gate marker steps 1-4):
    1. ``git -C <start_dir> rev-parse --show-toplevel`` (list-form argv,
       ``shell=False``, ``timeout=RESOLVER_GIT_TIMEOUT_S``).
    2. On success (exit 0): return ``sha1(realpath(toplevel)).hexdigest()[:16]``.
    3. On git-failure (nonzero exit / ``FileNotFoundError`` / ``PermissionError``
       / ``TimeoutExpired``): anchor = ``realpath(start_dir)``; call
       ``_append_hooks_log_line({"ts": <iso8601 utc>, "keying": "no-anchor"})``
       BEFORE returning; then return ``sha1(anchor).hexdigest()[:16]``.

    NEVER raises (so the gate's fail-open policy does not need to cover this
    path). The catch is ``(subprocess.SubprocessError, OSError)``:
    ``SubprocessError`` covers ``CalledProcessError`` and ``TimeoutExpired``;
    ``OSError`` covers ``FileNotFoundError``/``PermissionError`` on the git
    binary.
    """
    anchor = None
    try:
        result = subprocess.run(
            ["git", "-C", str(start_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=RESOLVER_GIT_TIMEOUT_S,
        )
        if result.returncode == 0:
            toplevel = result.stdout.strip()
            if toplevel:
                anchor = os.path.realpath(toplevel)
    except (subprocess.SubprocessError, OSError):
        anchor = None

    if anchor is None:
        anchor = os.path.realpath(str(start_dir))
        _append_hooks_log_line({
            "ts": datetime.now(timezone.utc).isoformat(),
            "keying": "no-anchor",
        })
    return hashlib.sha1(anchor.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Self-test.
# --------------------------------------------------------------------------- #
def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def selftest() -> int:
    """In-memory fixtures. Exercises the plan's Task-1 selftest bullets."""
    import tempfile

    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    # r1-M6 isolation baseline (mirrors lessons_recall.py _m13_before): every
    # resolve_project_key/_append_hooks_log_line call below must run under an
    # isolated HOME so keying=no-anchor lines land in a tmp tree, NOT the
    # developer's REAL ~/.ai-playbook/logs/hooks.log. The final
    # selftest_isolation assertion pins this; a future bare call outside the
    # HOME patch trips it.
    _real_log = Path.home() / ".ai-playbook" / "logs" / "hooks.log"
    _iso_before = 0
    try:
        if _real_log.is_file():
            _iso_before = sum(
                1 for _ in _real_log.read_text(encoding="utf-8").splitlines()
                if _.strip()
            )
    except OSError:
        _iso_before = -1

    # ---- resolves_all_keys: REAL-SHAPED facts file with BOTH formats ----
    # A ```toml fence block carries plans_dir/tmp_dir (TOML parser); a separate
    # markdown table row carries shared_docs_dir (table parser). Each parser
    # must return ITS OWN format's value; a stub hardcoding one parser fails.
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        plans_value = "docs/plans/"
        tmp_value = "docs/tmp/"
        shared_value = "/tmp/zz-shared-docs-X/"
        facts_body = (
            "```toml\n"
            f'plans_dir = "{plans_value}"\n'
            "\n"
            f'tmp_dir = "{tmp_value}"\n'
            "\n"
            "```\n"
            "\n"
            "Some prose here.\n"
            "\n"
            "| Key | Value |\n"
            "|-----|-------|\n"
            f"| `shared_docs_dir` | `{shared_value}` |\n"
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(facts_body, encoding="utf-8")

        plans = resolve_plans_dir(td_path)
        tmp = resolve_tmp_dir(td_path)
        shared = resolve_shared_docs_dir(td_path)
        check(
            "resolves_all_keys: plans_dir from TOML fence",
            plans is not None and plans.name == "plans",
            str(plans),
        )
        check(
            "resolves_all_keys: tmp_dir from TOML fence",
            tmp is not None and tmp.name == "tmp",
            str(tmp),
        )
        check(
            "resolves_all_keys: shared_docs_dir from table row",
            shared is not None and shared == Path(shared_value).expanduser().resolve(),
            str(shared),
        )
        # The two parsers return DIFFERENT values (pins the format split).
        check(
            "resolves_all_keys: TOML value != table value (format split real)",
            plans != shared,
            f"plans={plans} shared={shared}",
        )

    # ---- shared_docs_dir_unchanged: against the REAL home facts file ----
    # The table parser must return the SAME Path the migrator returned before
    # the move (byte-identical). NOT a fake fixture.
    home_shared = resolve_shared_docs_dir(Path("."))
    check(
        "shared_docs_dir_unchanged: resolves against the real home facts file",
        home_shared is not None,
        str(home_shared),
    )
    if home_shared is not None:
        # The expected value: the migrator's pre-move value (captured at plan
        # time) was ``<repo>/projects/.ai-playbook``. The repo facts file has a
        # shared_docs_dir row pointing there; the parser must resolve it.
        check(
            "shared_docs_dir_unchanged: value matches the migrator's pre-move path",
            home_shared.name == ".ai-playbook",
            str(home_shared),
        )

    # ---- table_key_repo_first: repo value wins over home value ----
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        repo_value = "/tmp/zz-repo-shared-AAA/"
        (td_path / ".ai-playbook" / "facts.md").write_text(
            "| `shared_docs_dir` | `" + repo_value + "` |\n",
            encoding="utf-8",
        )
        got = resolve_shared_docs_dir(td_path)
        check(
            "table_key_repo_first: repo value returned, NOT home value",
            got is not None and got == Path(repo_value).expanduser().resolve(),
            f"got={got}",
        )

    # ---- resolve_project_key_no_raise_on_missing_git (parametrized) ----
    import subprocess as _sp

    start = Path(tempfile.gettempdir())

    real_run = _sp.run

    def _make_raiser(exc):
        def _raiser(*a, **k):
            raise exc
        return _raiser

    expected_anchor = os.path.realpath(str(start))
    expected_hash = hashlib.sha1(expected_anchor.encode()).hexdigest()[:16]

    # r1-M6: arms 1 and 2 call resolve_project_key, which writes a
    # keying=no-anchor line to the hooks.log resolved from Path.home() at call
    # time. They MUST run under an isolated HOME so that write lands in a tmp
    # tree, NOT the developer's REAL ~/.ai-playbook/logs/hooks.log (the same
    # discipline lessons_recall.py and skill_gate.py apply to their _consult
    # calls). The arms below (absent-parent, read-only-parent, non-serializable)
    # already patch HOME; arms 1-2 were the leaf missed in r1/r2/r3.
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            # Arm 1: FileNotFoundError (git binary absent).
            _sp.run = _make_raiser(FileNotFoundError("[Errno 2] No such file or directory: 'git'"))
            try:
                h1 = resolve_project_key(start)
            except BaseException as e:
                h1 = None
                check("resolve_project_key: FileNotFoundError does not propagate", False, repr(e))
            finally:
                _sp.run = real_run

            check(
                "resolve_project_key: FileNotFoundError returns sha1(realpath(start_dir))[:16]",
                isinstance(h1, str) and h1 == expected_hash,
                f"h1={h1!r} expected={expected_hash!r}",
            )

            # Arm 2: subprocess.TimeoutExpired(cmd, 5) (hung git).
            _sp.run = _make_raiser(_sp.TimeoutExpired(cmd=["git"], timeout=5))
            try:
                h2 = resolve_project_key(start)
            except BaseException as e:
                h2 = None
                check("resolve_project_key: TimeoutExpired does not propagate", False, repr(e))
            finally:
                _sp.run = real_run

            check(
                "resolve_project_key: TimeoutExpired returns sha1(realpath(start_dir))[:16]",
                isinstance(h2, str) and h2 == expected_hash,
                f"h2={h2!r} expected={expected_hash!r}",
            )
            check(
                "resolve_project_key: return is a plain str, NOT a tuple",
                isinstance(h2, str) and not isinstance(h2, tuple),
                repr(h2),
            )

            # The resolver WROTE keying=no-anchor to the hooks.log FILE under
            # the patched HOME. Verify the line reached it.
            hooks_log = Path(home_tmp) / ".ai-playbook" / "logs" / "hooks.log"
            check(
                "resolve_project_key: hooks.log file exists under patched HOME",
                hooks_log.is_file(),
                str(hooks_log),
            )
            if hooks_log.is_file():
                lines = [
                    json.loads(ln) for ln in hooks_log.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                ]
                last = lines[-1] if lines else None
                check(
                    "resolve_project_key: last line parses to a dict",
                    isinstance(last, dict),
                    repr(last),
                )
                if isinstance(last, dict):
                    check(
                        "resolve_project_key: keys EXACTLY {ts, keying}",
                        set(last.keys()) == {"ts", "keying"},
                        str(sorted(last.keys())),
                    )
                    check(
                        "resolve_project_key: keying == 'no-anchor'",
                        last.get("keying") == "no-anchor",
                        str(last.get("keying")),
                    )
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home

    # ABSENT-PARENT arm: HOME tmp dir whose .ai-playbook/logs/ does NOT pre-exist.
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            # Ensure logs dir does NOT pre-exist.
            assert not (Path(home_tmp) / ".ai-playbook" / "logs").exists()
            _sp.run = _make_raiser(FileNotFoundError("no git"))
            raised = False
            try:
                h3 = resolve_project_key(start)
            except BaseException:
                raised = True
                h3 = None
            finally:
                _sp.run = real_run
            check(
                "resolve_project_key: absent-parent arm does not raise",
                not raised,
                "",
            )
            check(
                "resolve_project_key: absent-parent arm still returns the hash",
                isinstance(h3, str) and h3 == expected_hash,
                repr(h3),
            )
            hooks_log = Path(home_tmp) / ".ai-playbook" / "logs" / "hooks.log"
            check(
                "resolve_project_key: absent-parent arm line reaches the file",
                hooks_log.is_file() and hooks_log.read_text(encoding="utf-8").strip() != "",
                str(hooks_log),
            )
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home

    # READ-ONLY-PARENT arm: ~/.ai-playbook/ read-only (chmod 0500) so makedirs
    # raises PermissionError. The single try/except OSError covers makedirs too.
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            ap_root = Path(home_tmp) / ".ai-playbook"
            ap_root.mkdir()
            ap_root.chmod(0o500)  # read+execute, no write
            _sp.run = _make_raiser(FileNotFoundError("no git"))
            raised = False
            try:
                h4 = resolve_project_key(start)
            except BaseException:
                raised = True
                h4 = None
            finally:
                _sp.run = real_run
                # Restore writability so the tmpdir cleanup can remove it.
                try:
                    ap_root.chmod(0o700)
                except OSError:
                    pass
            check(
                "resolve_project_key: read-only-parent arm does not raise",
                not raised,
                "",
            )
            check(
                "resolve_project_key: read-only-parent arm still returns the hash",
                isinstance(h4, str) and h4 == expected_hash,
                repr(h4),
            )
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home

    # NON-SERIALIZABLE-PAYLOAD arm: call the shared helper directly with a
    # payload whose ts is a non-JSON-serializable object (datetime.now(tz),
    # NOT .isoformat()). The helper must return WITHOUT raising (only
    # json.dumps(payload, default=str) degrades the field to str and passes).
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            bad_payload = {"ts": datetime.now(timezone.utc), "keying": "no-anchor"}
            raised = False
            try:
                _append_hooks_log_line(bad_payload)
            except BaseException:
                raised = True
            check(
                "_append_hooks_log_line: non-serializable payload does not raise",
                not raised,
                "",
            )
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home

    # r1-M6 regression guard: no selftest block leaked a keying line into the
    # REAL ~/.ai-playbook/logs/hooks.log. Every resolve_project_key call now
    # runs under an isolated HOME; a future bare call outside isolation would
    # trip this.
    if _iso_before >= 0:
        try:
            _iso_after = sum(
                1 for _ in _real_log.read_text(encoding="utf-8").splitlines()
                if _.strip()
            ) if _real_log.is_file() else 0
        except OSError:
            _iso_after = _iso_before
        check(
            "selftest_isolation: no leak into REAL ~/.ai-playbook/logs/hooks.log",
            _iso_after == _iso_before,
            f"before={_iso_before} after={_iso_after} (a block wrote to the real log outside isolated HOME)",
        )

    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "--selftest":
        return selftest()
    sys.stderr.write("usage: facts_paths.py --selftest\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
