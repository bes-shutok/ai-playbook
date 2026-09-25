#!/usr/bin/env python3
"""Reject backlog-inbox filename shapes outside the resolved backlog home.

Filename-only gate (content is never inspected), case-insensitive on the
basename:

- rule 1: basename contains ``backlog`` OR ``deferred`` AND the path is under
  one of the named hot dirs (``docs/maintenance/``, ``docs/architecture/``,
  ``docs/tmp/``); scanned over a FILESYSTEM walk so untracked and gitignored
  files are seen. Intentional precedence: rule 1 fires BEFORE the backlog-home
  exclusion, so named hot dirs gate regardless of facts state, including when
  a configured backlog home sits under a hot dir. Symlinked DIRECTORIES
  inside a hot dir whose targets stay inside it are traversed and their
  files reported under the symlink (link) path; escaping or broken
  directory targets (and broken file links) are skipped with a
  ``hot-dir symlink not traversed`` warning on stderr (unreadable subtrees
  warn ``cannot read hot-dir subtree``). A symlinked FILE is reported
  under its link name regardless of the target location (classification is
  filename-shape only; the target is never read).
- rule 2: basename contains BOTH ``backlog`` AND ``deferred`` AND the path is
  outside the backlog home; scanned over tracked files (``git ls-files -z``).

Backlog home resolves from ``.ai-playbook/facts.md`` TOML keys
``backlog_dir`` / ``backlog_completed_dir`` with fallback defaults and a
stderr warning when missing. A value resolving (e.g. through a symlink)
outside the repo root, or to the repo root itself, warns and falls back
to the default. Two ``docs/tmp/`` carve-outs (path-segment
boundaries / basename prefix only) keep this repo's own conventions green.

Rule 1's hot dirs come from the optional ``backlog_hot_dirs`` key: a
quoted string of repo-relative directories separated by whitespace
and/or commas (the TOML fence parser is scalar-only, so an array literal
parses as missing). The configured list REPLACES the built-in defaults
(``docs/maintenance``, ``docs/architecture``, ``docs/tmp``). A missing
key falls back to the defaults silently. A blank key, or an effective
set that ends up empty after validation, warns on stderr and falls
  back to the defaults. Invalid entries (absolute, ``.``, ``..`` itself or
  a path whose first segment escapes with ``..``), entries resolving to a
  nonexistent repo path, and symlinked entries resolving outside the repo
  root warn on stderr and
  are DROPPED while surviving configured entries stay active, so rule 1
  can never silently disable. ``~``-prefixed entries are
expanduser-ed first; an expanded absolute result is dropped by the
invalid-entry rule.

Exit 0 when clean, 1 when any violation (each printed as ``<path>: rule <N>``).
The default scan root anchors at the git toplevel of the current directory
and warns on stderr before falling back to the CWD when git is unavailable.

The same run also carries a WARN-ONLY nested-``.git`` detection pass: entries
named ``.git`` (directory, gitfile, or symlink) within depth 3 of the repo
root, excluding the root ``.git`` itself, registered worktrees, submodule
shaped gitdirs (resolving into ``GIT_COMMON_DIR/modules`` or containing
``/modules/``), and gitignored paths. Each remaining entry prints a stderr
warning naming the likely owner class (scratch fixture, interrupted lane,
GUI-visible detached commits) so a human decides; nothing is ever deleted
and the pass never affects the exit code.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover
    facts_paths = None  # type: ignore

HOT_DIRS = ("docs/maintenance", "docs/architecture", "docs/tmp")
DEFAULT_BACKLOG_DIR = "docs/history/backlog"
DEFAULT_BACKLOG_COMPLETED_DIR = "docs/history/backlog/completed"
TOKENS = ("backlog", "deferred")


def _hot_dir_parts(hot_dirs: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Segment hot-dir entries into parts tuples for ``Path.parts`` matching.

    Separator normalization (``\\`` to ``/`` before splitting) keeps
    Windows-native entries (e.g. ``docs\\maintenance``, which passes
    ``os.path.normpath`` validation on Windows) matchable against scanned
    ``Path.parts``; forward-slash entries split exactly as before.
    """
    return tuple(tuple(h.replace("\\", "/").split("/")) for h in hot_dirs)


def resolve_backlog_home(repo_root: Path) -> tuple[Path, Path]:
    """Resolve (backlog_dir, backlog_completed_dir) from repo facts TOML.

    Missing, blank, or degenerate (``.`` or a relpath whose FIRST segment
    is ``..``, i.e. at or above the repo root; a name merely starting with
    ``..`` such as ``..backlog`` is a valid in-repo directory) values fall
    back to the documented defaults
    with a warning on stderr; such a home would make ``is_relative_to`` match
    every path (or escape the repo) and silently disable rule 2. Values are anchored at ``repo_root`` (raw resolution, so
    a repo-relative value is never anchored against the process CWD). A
    value resolving (e.g. through a symlink) outside the repo root, or to
    the repo root itself, warns and falls back to the default.
    """
    resolved: list[Path] = []
    if facts_paths is None:
        print(
            "warning: facts parser unavailable (facts_paths.py not "
            "importable); using default backlog home",
            file=sys.stderr,
        )
    for key, default in (
        ("backlog_dir", DEFAULT_BACKLOG_DIR),
        ("backlog_completed_dir", DEFAULT_BACKLOG_COMPLETED_DIR),
    ):
        home: Path | None = None
        raw = (
            facts_paths.resolve_toml_key_raw(repo_root, key)
            if facts_paths is not None
            else None
        )
        if raw is not None and not raw.strip():
            print(
                f"warning: {key} present but empty in "
                f".ai-playbook/facts.md; falling back to {default}",
                file=sys.stderr,
            )
        elif raw is not None:
            p = Path(raw).expanduser()
            home = p if p.is_absolute() else repo_root / p
            try:
                rel = os.path.relpath(home, repo_root)
            except ValueError:
                # Cross-drive homes (Windows): relpath raises instead of
                # producing an escaping path; treat it as the degenerate
                # case so the standard warn-and-fallback keeps rule 2 up.
                print(
                    f"warning: {key} resolves outside the repo root; "
                    f"falling back to {default}",
                    file=sys.stderr,
                )
                home = None
            else:
                if (
                    rel == "."
                    or rel == ".."
                    or rel.startswith(".." + os.sep)
                ):
                    print(
                        f"warning: {key} resolves to {rel} of the repo root; "
                        f"falling back to {default}",
                        file=sys.stderr,
                    )
                    home = None
                elif not home.resolve().is_relative_to(repo_root):
                    # Resolved containment, mirroring the resolve_hot_dirs
                    # sibling key: a lexically inside-repo value that resolves
                    # (e.g. through a symlink) outside the repo root must not
                    # anchor the backlog home there.
                    print(
                        f"warning: {key} resolves outside the repo root; "
                        f"falling back to {default}",
                        file=sys.stderr,
                    )
                    home = None
                elif home.resolve() == repo_root:
                    # Resolved-equal-to-root: the lexical guard above cannot
                    # see this (the value itself is inside-repo, e.g. a
                    # symlink to "."), yet a root-equal home makes
                    # is_relative_to match every path and silently disable
                    # rule 2.
                    print(
                        f"warning: {key} resolves to the repo root; "
                        f"falling back to {default}",
                        file=sys.stderr,
                    )
                    home = None
        if home is None:
            if raw is None and facts_paths is not None:
                print(
                    f"warning: {key} missing from .ai-playbook/facts.md; "
                    f"falling back to {default}",
                    file=sys.stderr,
                )
            home = repo_root / default
        resolved.append(home)
    return resolved[0], resolved[1]


def resolve_hot_dirs(repo_root: Path) -> tuple[str, ...]:
    """Hot dirs for rule 1: optional facts key, defaults as fallback.

    ``backlog_hot_dirs`` is an optional quoted string of repo-relative
    directories separated by whitespace and/or commas (the TOML fence
    parser is scalar-only; an array literal parses as missing). A missing
    key falls back to ``HOT_DIRS`` silently (normal vendored case);
    ``facts_paths`` unavailable also falls back silently (the parser
    warning already fired). ``~``-prefixed entries are expanduser-ed
    first; an expanded absolute result is dropped by the invalid-entry
    rule (sibling facts keys honor ``~``). A blank key, or an effective
    set that ends up empty after validation, warns on stderr and falls
    back to ``HOT_DIRS``. Invalid entries (absolute, ``.``, ``..`` itself
    or a path whose first segment escapes with ``..``), entries resolving
    to a nonexistent repo path, and symlinked entries resolving outside
    the repo root warn on stderr and
    are DROPPED while surviving configured entries stay active, so rule 1
    never silently disables.
    """
    defaults = tuple(HOT_DIRS)
    if facts_paths is None:
        return defaults
    raw = facts_paths.resolve_toml_key_raw(repo_root, "backlog_hot_dirs")
    if raw is None:
        return defaults
    if not raw.strip():
        print("warning: backlog_hot_dirs present but empty in "
              ".ai-playbook/facts.md; falling back to defaults",
              file=sys.stderr)
        return defaults
    dirs: list[str] = []
    for entry in re.split(r"[,\s]+", raw.strip()):
        if not entry:
            continue
        entry = os.path.expanduser(entry)
        norm = os.path.normpath(entry)
        if os.path.isabs(norm) or norm == "." or (
            norm == ".." or norm.startswith(".." + os.sep)
        ):
            print(f"warning: backlog_hot_dirs entry {entry!r} is not a "
                  "repo-relative directory; dropping it", file=sys.stderr)
            continue
        if not (repo_root / norm).is_dir():
            print(f"warning: backlog_hot_dirs entry {entry!r} does not "
                  "exist in the repo; dropping it", file=sys.stderr)
            continue
        if not (repo_root / norm).resolve().is_relative_to(repo_root):
            print(f"warning: backlog_hot_dirs entry {entry!r} resolves "
                  "outside the repo root; dropping it", file=sys.stderr)
            continue
        if norm not in dirs:
            dirs.append(norm)
    if not dirs:
        print("warning: backlog_hot_dirs has no valid entries; "
              "falling back to defaults", file=sys.stderr)
        return defaults
    return tuple(dirs)


def _tmp_carve_out(path: Path) -> bool:
    """docs/tmp/ carve-outs, segment boundaries / basename prefix only.

    - any path segment below ``docs/tmp`` equal to ``execute-plan`` (session
      log trees named after plan slugs; segment boundary, so
      ``docs/tmp/execute-plan-sibling/`` is NOT covered);
    - basename prefix ``plan-requirements-`` (plans-skill requirements
      buffers; prefix-only, so a directory named
      ``plan-requirements-fake`` does not carve anything out).
    """
    if path.parts[:2] != ("docs", "tmp"):
        return False
    if "execute-plan" in path.parts[2:]:
        return True
    # Lowered so the prefix test matches the case-insensitive token match
    # above (an uppercase-variant buffer is carved out, never flagged).
    return path.name.lower().startswith("plan-requirements-")


def classify_path(
    rel_path: str,
    backlog_home: tuple[Path, Path],
    hot_dir_parts: tuple[tuple[str, ...], ...],
) -> int | None:
    """Return the fired rule number (1 or 2) for a repo-relative path.

    Only the file BASENAME is token-matched (case-insensitively); directory
    names never fire. Hot-dir membership and the backlog home are matched on
    path-segment boundaries. ``backlog_home`` entries must be repo-RELATIVE
    paths (see scan_repo), so ``is_relative_to`` compares like-for-like parts.
    ``hot_dir_parts`` carries the per-repo resolved hot dirs as segment
    tuples of arbitrary length (configured dirs need not be two segments).
    """
    path = Path(os.path.normpath(rel_path))
    basename = path.name.lower()
    has_backlog = "backlog" in basename
    has_deferred = "deferred" in basename
    if not has_backlog and not has_deferred:
        return None
    under_hot = any(path.parts[:len(hp)] == hp for hp in hot_dir_parts)
    if under_hot:
        if _tmp_carve_out(path):
            return None
        return 1  # hot dir + either token
    if has_backlog and has_deferred:
        if any(path.is_relative_to(home) for home in backlog_home):
            return None
        return 2  # token pair outside the backlog home
    return None


def _flag_untraversed(entry: Path) -> None:
    print(f"warning: hot-dir symlink not traversed: {entry!r}", file=sys.stderr)


def _iter_hot_dir_files(hot_path: Path):
    """Yield file paths under hot_path along their traversal path.

    Symlinked dir entries resolve against the hot-dir root: targets inside
    the hot dir are traversed (link-path reporting, visited-set cycle
    safety); targets outside are flagged on stderr and skipped, so the
    walk never leaves the hot dir (followlinks stays off). Symlinked
    files yield under their link name (os.walk parity); broken symlinks
    are flagged; already-visited targets are skipped silently. The stack
    carries (link_path, resolved_dir) pairs and iterates the RESOLVED
    directory captured at containment-check time, so a post-check symlink
    swap cannot redirect the read (TOCTOU hardening; a real directory
    itself being swapped for a symlink after the check is an accepted
    residual). Directory read errors warn and skip the subtree,
    preserving os.walk's tolerance. A target reachable through several
    routes is flagged once per traversal encounter, not globally once.
    """
    root = hot_path.resolve()
    stack = [(hot_path, root)]
    visited = {root}
    while stack:
        dirpath, real = stack.pop()
        try:
            entries = sorted(real.iterdir())
        except OSError as exc:
            print(f"warning: cannot read hot-dir subtree {dirpath!r}: {exc}",
                  file=sys.stderr)
            continue
        for entry_real in entries:
            entry = dirpath / entry_real.name
            if entry_real.is_symlink():
                try:
                    resolved = entry_real.resolve()
                except OSError:
                    _flag_untraversed(entry)
                    continue
                if resolved.is_dir():
                    if not resolved.is_relative_to(root):
                        _flag_untraversed(entry)
                    elif resolved not in visited:
                        visited.add(resolved)
                        stack.append((entry, resolved))
                elif resolved.exists():
                    yield entry
                else:
                    _flag_untraversed(entry)
                continue
            if entry_real.is_dir():
                stack.append((entry, entry_real))
            elif entry_real.is_file():
                yield entry


def _record(
    rel_path: str,
    backlog_home: tuple[Path, Path],
    hot_dir_parts: tuple[tuple[str, ...], ...],
    violations: dict[str, int],
) -> None:
    """Classify one repo-relative path and record it (first rule wins).

    Shared tail of both scan loops (rule-1 walk and rule-2 ls-files):
    classify, then ``setdefault`` so a path seen by both surfaces keeps
    its first-assigned rule. ``hot_dir_parts`` carries the per-repo
    resolved hot dirs through to ``classify_path``.
    """
    rule = classify_path(rel_path, backlog_home, hot_dir_parts)
    if rule is not None:
        violations.setdefault(rel_path, rule)


def _check_home_rel(home_rel: Path) -> bool:
    """Validate a computed backlog-home relpath; warn and reject degenerate.

    Defense-in-depth for scan_repo: a home whose resolved relpath is ``.``
    (the repo root; matches every relative path in ``is_relative_to``) or
    whose FIRST segment is ``..`` (escapes the repo; a name merely starting
    with ``..`` is a valid in-repo directory) must not anchor a rule-2
    exclusion,
    even if it passed the resolve-time checks in resolve_backlog_home
    (resolve-vs-use TOCTOU).
    """
    home_rel_str = str(home_rel)
    if home_rel_str == "." or home_rel_str == ".." or home_rel_str.startswith(
        ".." + os.sep
    ):
        print(
            f"warning: backlog home resolves to {home_rel} of the repo "
            "root; dropping it",
            file=sys.stderr,
        )
        return False
    return True


def detect_nested_git(repo_root: Path) -> list[tuple[str, str]]:
    """Warn-only nested-``.git`` detection; return (path, owner_class) pairs.

    Candidates: entries named ``.git`` (real dir, gitfile, or symlink) at
    relative depth 1..3 from the repo root, excluding the root ``.git``.
    Silent exclusions, classified BEFORE any removal consideration and
    never deleting anything:
    - registered worktrees: the candidate's parent matches a
      ``git worktree list --porcelain`` entry, or the candidate gitfile's
      ``gitdir:`` target resolves under the main ``.git/worktrees/`` tree;
    - submodule-shaped gitdirs: the target resolves under
      ``GIT_COMMON_DIR/modules`` or contains a ``/modules/`` segment;
    - gitignored paths: ``git check-ignore`` names the candidate.
    Remaining candidates get a likely owner class by shape: a real
    ``.git`` directory with in-progress state markers
    (``MERGE_HEAD``/``rebase-merge``/``rebase-apply``/
    ``CHERRY_PICK_HEAD``/``BISECT_LOG``) is an interrupted lane, any
    other real ``.git`` directory is a scratch fixture (an inited or
    cloned repo), and a ``.git`` file is a linked-worktree gitfile
    (GUI-visible detached commits). Best-effort: git probe failures fail
    open (no exclusions from that probe) since the pass is warn-only.
    """
    results: list[tuple[str, str]] = []
    candidates: list[Path] = []
    root_git = repo_root / ".git"
    for dirpath, dirnames, filenames in os.walk(repo_root, followlinks=False):
        rel_dir = Path(dirpath).relative_to(repo_root)
        depth = 0 if str(rel_dir) == "." else len(rel_dir.parts)
        if depth >= 3:
            dirnames[:] = []
        for name in list(dirnames) + filenames:
            if name != ".git":
                continue
            entry = Path(dirpath) / name
            if entry == root_git:
                continue
            if depth + 1 > 3:
                continue
            candidates.append(entry)
        # Do not descend into any nested .git directory itself.
        dirnames[:] = [d for d in dirnames if d != ".git"]

    if not candidates:
        return results

    worktree_dirs: set[Path] = set()
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
            capture_output=True, check=True,
        ).stdout.decode("utf-8", "surrogateescape")
        for line in out.splitlines():
            # git 2.x porcelain emits no "gitdir" lines (verified 2026-09-19);
            # the worktree paths themselves are the carrier. Retained as a
            # fail-open no-op for future porcelain extensions.
            if line.startswith("worktree "):
                worktree_dirs.add(Path(line[len("worktree "):]).resolve())
    except (OSError, subprocess.SubprocessError):
        pass  # fail open: warn-only pass must not raise on git problems

    modules_dir = (root_git / "modules").resolve()

    def gitfile_target(entry: Path) -> Path | None:
        if entry.is_dir() or entry.is_symlink() and entry.resolve().is_dir():
            return None
        try:
            text = entry.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        text = text.strip()
        if not text.startswith("gitdir:"):
            return None
        raw = text[len("gitdir:"):].strip()
        if not raw:
            return None
        target = Path(raw)
        if not target.is_absolute():
            target = entry.parent / target
        try:
            return target.resolve()
        except OSError:
            return target

    ignored: set[Path] = set()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "check-ignore", "-z", "--stdin"],
            capture_output=True, check=True,
            input=("\0".join(str(c) for c in candidates) + "\0").encode(
                "utf-8", "surrogateescape"
            ),
        ).stdout
        for raw in proc.split(b"\0"):
            if raw:
                ignored.add(
                    Path(raw.decode("utf-8", "surrogateescape")).resolve()
                )
    except (OSError, subprocess.SubprocessError):
        pass  # fail open

    for entry in candidates:
        rel = str(entry.relative_to(repo_root))
        try:
            resolved = entry.resolve()
        except OSError:
            resolved = entry
        if resolved in ignored:
            continue
        if entry.parent.resolve() in worktree_dirs:
            continue
        target = gitfile_target(entry)
        if target is not None:
            target_posix = target.as_posix()
            if (
                target == modules_dir
                or str(target).startswith(str(modules_dir) + os.sep)
                or "/modules/" in target_posix
            ):
                continue
            if ".git/worktrees/" in target_posix:
                continue
        is_real_dir = entry.is_dir() and not entry.is_symlink()
        if is_real_dir and any(
            (entry / marker).exists()
            for marker in (
                "MERGE_HEAD", "rebase-merge", "rebase-apply",
                "CHERRY_PICK_HEAD", "BISECT_LOG",
            )
        ):
            owner = "interrupted lane"
        elif is_real_dir:
            # A real nested .git directory is an inited/cloned repo: the
            # scratch-fixture shape. A .git FILE is a linked-worktree
            # gitfile (the GUI detached-checkout shape).
            owner = "scratch fixture"
        else:
            owner = "GUI-visible detached commits"
        results.append((rel, owner))
    return results


def scan_repo(repo_root: Path) -> list[tuple[str, int]]:
    """Scan both surfaces; return sorted (relative-path, rule) violations."""
    repo_root = repo_root.resolve()
    backlog_home = tuple(
        home
        for home in (
            Path(os.path.relpath(r.resolve(), repo_root))
            for r in resolve_backlog_home(repo_root)
        )
        # Defensive TOCTOU guard: a home swapped to the repo root (or
        # outside it) between the resolve-time checks and this use must
        # not exempt every rule-2 candidate (``.`` matches all relative
        # paths) or anchor exclusions outside the repo.
        if _check_home_rel(home)
    )
    violations: dict[str, int] = {}
    hot_dirs = resolve_hot_dirs(repo_root)
    hot_dir_parts = _hot_dir_parts(hot_dirs)

    # Rule 1: filesystem walk of the hot dirs (untracked files included;
    # absent dirs tolerated).
    for hot in hot_dirs:
        hot_path = repo_root / hot
        if not hot_path.is_dir():
            continue
        # Top-level containment: the facts key turns the entry set into
        # per-repo input consumed by the shared ``done`` skill in every
        # vendored repo, so a committed symlinked entry must not walk
        # outside the repo (lexical ``..`` validation alone is
        # insufficient).
        if not (repo_root / hot).resolve().is_relative_to(repo_root):
            print(
                f"warning: hot dir '{hot}' resolves outside the repo "
                "root; skipping",
                file=sys.stderr,
            )
            continue
        for absolute in _iter_hot_dir_files(hot_path):
            rel = os.path.relpath(absolute, repo_root)
            _record(rel, backlog_home, hot_dir_parts, violations)

    # Warn-only nested-.git detection (same run; never affects exit code).
    for rel, owner in detect_nested_git(repo_root):
        print(
            f"warning: nested .git ({owner}): {rel} "
            "(warn-only; no action taken)",
            file=sys.stderr,
        )

    # Rule 2: tracked files only.
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        ).stdout
    except OSError as exc:
        # git absent: fail open with a warning; the rule-1 hot-dir walk
        # still covers the incident shape.
        print(f"warning: git ls-files unavailable; rule 2 skipped: {exc}", file=sys.stderr)
        out = b""
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", "surrogateescape") if exc.stderr else str(exc)
        if "not a git repository" in detail:
            # A non-repo directory is a legitimate scan target (rule-1 walk
            # only); same fail-open treatment as git being absent.
            print(
                f"warning: {repo_root} is not a git repo; rule 2 skipped",
                file=sys.stderr,
            )
            out = b""
        else:
            # git exists yet refused (index.lock, corrupt repo): fail closed
            # so a transient git failure cannot silently skip the
            # tracked-tree scan.
            print(f"error: git ls-files failed: {detail}", file=sys.stderr)
            # Report already-collected violations before aborting so the
            # fail-closed exit does not swallow the rule-1 walk's findings.
            for rel, rule in sorted(violations.items()):
                print(f"{rel}: rule {rule}")
            sys.exit(1)
    for raw in out.split(b"\0"):
        if not raw:
            continue
        rel = os.path.normpath(raw.decode("utf-8", "surrogateescape"))
        _record(rel, backlog_home, hot_dir_parts, violations)

    return sorted(violations.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject backlog-inbox filename shapes outside the backlog home"
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to scan (default: git toplevel of the "
        "current directory, falling back to the current directory when "
        "git is unavailable)",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run fixture checks and exit",
    )
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).expanduser().resolve()
    else:
        # Anchor the default scan surface at the git toplevel, not the CWD,
        # so a subdirectory invocation cannot silently shrink the scan to
        # its own subtree. Fail open to the CWD when git is absent or fails.
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            repo_root = Path(out).resolve()
        except (OSError, subprocess.SubprocessError):
            print(
                "warning: git rev-parse unavailable; scanning CWD",
                file=sys.stderr,
            )
            repo_root = Path.cwd().resolve()
    violations = scan_repo(repo_root)
    for rel, rule in violations:
        print(f"{rel}: rule {rule}")
    if violations:
        print(
            f"check_backlog_inbox_location: {len(violations)} violation(s)",
            file=sys.stderr,
        )
        return 1
    print("check_backlog_inbox_location: ok")
    return 0


# --------------------------------------------------------------------------- #
# Selftest
# --------------------------------------------------------------------------- #

_CHECK_FAILURES = [0]


def _make_check():
    def check(condition: bool, label: str) -> None:
        if not condition:
            _CHECK_FAILURES[0] += 1
            print(f"selftest FAIL: {label}", file=sys.stderr)

    return check


def _write(root: Path, rel: str, content: str = "fixture\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _clean_git_env() -> dict[str, str]:
    """Env copy without ambient GIT_* redirections (GIT_DIR/GIT_WORK_TREE/
    GIT_INDEX_FILE/GIT_COMMON_DIR, GIT_CONFIG_COUNT + GIT_CONFIG_KEY_*/
    GIT_CONFIG_VALUE_* config injection, GIT_OBJECT_DIRECTORY, and
    GIT_ALTERNATE_OBJECT_DIRECTORIES) so fixture repos are isolated from
    whatever the invoking machine exported."""
    _exact = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_CONFIG_COUNT",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    }
    _prefixes = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
    return {
        k: v
        for k, v in os.environ.items()
        if k not in _exact and not k.startswith(_prefixes)
    }


def _git(root: Path, *git_args: str) -> None:
    # Pin ambient-config inputs beyond identity: no signing, no global hooks,
    # so machines with commit.gpgsign=true or a core.hooksPath cannot make
    # the selftest fail for unrelated reasons.
    subprocess.run(
        ["git", "-c", "user.email=selftest@example.invalid",
         "-c", "user.name=selftest",
         "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=/dev/null",
         "-c", "core.excludesFile=/dev/null", *git_args],
        cwd=root,
        check=True,
        capture_output=True,
        env=_clean_git_env(),
    )


def _run_script(
    root: Path,
    *,
    bare: bool = False,
    cwd: Path | None = None,
    env_extra: dict[str, str] | None = None,
    timeout: float | None = None,
) -> tuple[int, str, str]:
    env = _clean_git_env()
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, str(Path(__file__).resolve())]
    if not bare:
        cmd += ["--repo-root", str(root)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(cwd) if cwd is not None else None,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "subprocess.TimeoutExpired"
    return proc.returncode, proc.stdout, proc.stderr


def _selftest_main_repo(root: Path, check) -> None:
    """Synthetic git repo: violation + allowed fixtures, facts present."""
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")

    # facts with backlog keys (committed so the resolution path is exercised).
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        'backlog_dir = "docs/history/backlog/"\n'
        'backlog_completed_dir = "docs/history/backlog/completed/"\n'
        "```\n",
    )

    # Rule-1 hot-dir violations (filesystem walk; tracked or not).
    _write(repo, "docs/maintenance/TT-123-deferred-backlog.md")
    _write(repo, "docs/tmp/round-2-backlog-notes.md")
    _write(repo, "docs/architecture/deferred-queue-design.md")
    _write(repo, "docs/maintenance/sub/sub-deferred-backlog.md")
    # Uppercase token: case-insensitive basename match.
    _write(repo, "docs/architecture/BACKLOG-notes.md")

    # Rule-2 violation (both tokens outside the backlog home); committed.
    _write(repo, "docs/history/plans/2026-09-03-x-deferred-backlog.md")

    # Carve-out discriminators under docs/tmp that MUST FAIL:
    # segment boundary (execute-plan-sibling is not execute-plan) and
    # carve-opt-out (plan-requirements- is a BASENAME prefix, never a
    # substring anywhere in the path).
    _write(repo, "docs/tmp/execute-plan-sibling/evil-backlog.md")
    _write(repo, "docs/tmp/notes/plan-requirements-fake/evil-backlog.md")

    # Allowed fixtures. The pair-token files inside the home guard the
    # rule-2 backlog-home exclusion: removing the exclusion (or breaking it,
    # e.g. absolute-vs-relative parts comparison) fails these assertions.
    _write(repo, "docs/history/backlog/2026-09-03-anything.md")
    _write(repo, "docs/history/backlog/2026-09-03-pair-deferred-backlog-ok.md")
    _write(repo, "docs/history/backlog/completed/2026-08-28-fence-scanner-family.md")
    _write(repo, "docs/history/backlog/completed/2026-08-28-pair-deferred-backlog-ok.md")
    _write(repo, "docs/maintenance/confluence-sync-manifest.json")
    # Asymmetry (intentional): a single token outside every hot dir and
    # without the second token is allowed by rule 2 (``backlog`` absent);
    # only the token PAIR fires outside the hot dirs.
    _write(repo, "docs/reviews/x-deferred.md")

    # Carve-out allowed fixtures under docs/tmp: the requirements-buffer
    # basename prefix with a backlog slug, and a session-log tree named after
    # a plan slug whose file BASENAME itself contains the token (a token-free
    # basename would pass even without the carve-out, since directory names
    # never fire).
    _write(repo, "docs/tmp/plan-requirements-2026-09-03-backlog-gate.md")
    # Uppercase variant: guards the case-insensitive carve-out prefix
    # (removing ``.lower()`` from the prefix test fails this fixture).
    _write(repo, "docs/tmp/PLAN-REQUIREMENTS-2026-09-03-BACKLOG-gate.md")
    _write(
        repo,
        "docs/tmp/execute-plan/2026-09-03-backlog-location-gate/"
        "task-1-backlog-log.md",
    )

    # Single commit with explicit identity so no ambient git config is
    # needed; every rule-2 fixture is committed for `git ls-files` to see.
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    # UNTRACKED gitignored violation inside a hot dir: created after the
    # commit and never added, proving the rule-1 filesystem walk sees
    # shadow-tree files a tracked-only scan would miss.
    _write(repo, ".gitignore", "docs/maintenance/untracked-deferred-inbox.md\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "gitignore")
    _write(repo, "docs/maintenance/untracked-deferred-inbox.md")

    expected = {
        "docs/maintenance/TT-123-deferred-backlog.md": 1,
        "docs/tmp/round-2-backlog-notes.md": 1,
        "docs/architecture/deferred-queue-design.md": 1,
        "docs/maintenance/sub/sub-deferred-backlog.md": 1,
        "docs/architecture/BACKLOG-notes.md": 1,
        "docs/history/plans/2026-09-03-x-deferred-backlog.md": 2,
        "docs/tmp/execute-plan-sibling/evil-backlog.md": 1,
        "docs/tmp/notes/plan-requirements-fake/evil-backlog.md": 1,
        "docs/maintenance/untracked-deferred-inbox.md": 1,
    }
    allowed = [
        "docs/history/backlog/2026-09-03-anything.md",
        "docs/history/backlog/2026-09-03-pair-deferred-backlog-ok.md",
        "docs/history/backlog/completed/2026-08-28-fence-scanner-family.md",
        "docs/history/backlog/completed/2026-08-28-pair-deferred-backlog-ok.md",
        "docs/maintenance/confluence-sync-manifest.json",
        "docs/reviews/x-deferred.md",
        "docs/tmp/plan-requirements-2026-09-03-backlog-gate.md",
        "docs/tmp/PLAN-REQUIREMENTS-2026-09-03-BACKLOG-gate.md",
        "docs/tmp/execute-plan/2026-09-03-backlog-location-gate/task-1-backlog-log.md",
    ]

    code, stdout, stderr = _run_script(repo)
    check(code == 1, f"main repo: expected exit 1, got {code} (stderr: {stderr})")
    reported: dict[str, int] = {}
    for line in stdout.splitlines():
        if ": rule " in line:
            path, _, rule = line.rpartition(": rule ")
            reported[path] = int(rule)
    check(
        reported == expected,
        f"main repo: reported violations {reported} != expected {expected}",
    )
    for path in allowed:
        check(path not in reported, f"main repo: allowed fixture flagged: {path}")

    # Fail-closed branch: git present but refusing (corrupt index). Note a
    # stale .git/index.lock does NOT drive this branch — `git ls-files` is
    # read-only and never takes the index lock — so the fixture corrupts the
    # index bytes instead. The gate must abort (exit 1) with the
    # 'git ls-files failed' error, not fail open. try/finally restores the
    # index so a failed check cannot corrupt later fixtures.
    index = repo / ".git" / "index"
    backup = index.read_bytes()
    index.write_bytes(b"corrupt\n")
    try:
        code, _stdout, stderr = _run_script(repo)
        check(
            code == 1,
            f"main repo (corrupt index): expected exit 1, got {code} (stderr: {stderr})",
        )
        check(
            "git ls-files failed" in stderr,
            f"main repo (corrupt index): fail-closed error missing (stderr: {stderr!r})",
        )
        # F7: already-collected rule-1 violations must still be printed
        # before the fail-closed exit, not swallowed by the git error.
        check(
            "docs/maintenance/TT-123-deferred-backlog.md: rule 1" in _stdout,
            "main repo (corrupt index): collected violations dropped on "
            f"fail-closed exit (stdout: {_stdout!r})",
        )
    finally:
        index.write_bytes(backup)


def _selftest_factsless_repo(root: Path, check) -> None:
    """Facts-less variant: fallback backlog home with a stderr warning."""
    repo = root / "factsless"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(repo, "docs/history/plans/fallback-deferred-backlog.md")
    # Both tokens inside the FALLBACK home: guards the exclusion on the
    # default-home resolution path (no facts keys).
    _write(repo, "docs/history/backlog/fallback-ok-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    code, stdout, stderr = _run_script(repo)
    check(code == 1, f"factsless repo: expected exit 1, got {code}")
    check(
        "docs/history/plans/fallback-deferred-backlog.md: rule 2" in stdout,
        f"factsless repo: rule-2 fallback violation missing (stdout: {stdout!r})",
    )
    check(
        "docs/history/backlog/fallback-ok-deferred-backlog.md" not in stdout,
        "factsless repo: fallback backlog-home fixture flagged",
    )
    check(
        "falling back" in stderr,
        f"factsless repo: fallback warning missing on stderr (stderr: {stderr!r})",
    )


def _selftest_blank_key_repo(root: Path, check) -> None:
    """Blank ``backlog_dir`` value must NOT disable the rule-2 exclusion.

    A present-but-empty key previously anchored the home at the repo root
    itself, making ``is_relative_to`` match every path (silent rule-2
    bypass). It must instead warn and fall back to the default home, so a
    committed both-token violation outside that home still fails.
    """
    repo = root / "blankkey"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        'backlog_dir = ""\n'
        'backlog_completed_dir = "docs/history/backlog/completed/"\n'
        "```\n",
    )
    _write(repo, "docs/history/plans/blank-key-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    code, stdout, stderr = _run_script(repo)
    check(code == 1, f"blank-key repo: expected exit 1, got {code} (stdout: {stdout!r})")
    check(
        "docs/history/plans/blank-key-deferred-backlog.md: rule 2" in stdout,
        f"blank-key repo: rule-2 violation missing (stdout: {stdout!r})",
    )
    check(
        "present but empty" in stderr,
        f"blank-key repo: empty-key warning missing (stderr: {stderr!r})",
    )


def _selftest_degenerate_home_repo(root: Path, check) -> None:
    """Degenerate ``..`` home (F5): warn + default, rule 2 still fires.

    Also guards the widened above-root arm (F2) via the shared helper below
    with an escaping ``../..`` value: without the ``rel.startswith("..")``
    guard the rule-2 exclusion dies and the committed pair-token violation
    is silently allowed.
    """

    def run_case(name: str, backlog_value: str) -> None:
        repo = root / name
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(
            repo,
            ".ai-playbook/facts.md",
            "```toml\n"
            f'backlog_dir = "{backlog_value}"\n'
            'backlog_completed_dir = "docs/history/backlog/completed/"\n'
            "```\n",
        )
        _write(repo, "docs/history/plans/degenerate-deferred-backlog.md")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "init")

        code, stdout, stderr = _run_script(repo)
        check(code == 1, f"{name}: expected exit 1, got {code} (stdout: {stdout!r})")
        check(
            "docs/history/plans/degenerate-deferred-backlog.md: rule 2" in stdout,
            f"{name}: rule-2 violation missing (stdout: {stdout!r})",
        )
        check(
            "of the repo root" in stderr and "falling back" in stderr,
            f"{name}: degenerate-home warning missing (stderr: {stderr!r})",
        )

    run_case("dotdot", "..")
    run_case("aboveroot", "../..")
    run_case("dot", ".")


def _selftest_hot_dir_home_repo(root: Path, check) -> None:
    """Backlog home under a hot dir (F6): rule 1 precedence witness.

    Documented precedence says rule 1 fires BEFORE the backlog-home
    exclusion; a configured home inside ``docs/tmp`` must not exempt a
    token-named file there.
    """
    repo = root / "hotdirhome"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        'backlog_dir = "docs/tmp/backlog"\n'
        'backlog_completed_dir = "docs/history/backlog/completed/"\n'
        "```\n",
    )
    _write(repo, "docs/tmp/backlog/pair-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    code, stdout, stderr = _run_script(repo)
    check(code == 1, f"hot-dir home: expected exit 1, got {code} (stdout: {stdout!r})")
    check(
        "docs/tmp/backlog/pair-deferred-backlog.md: rule 1" in stdout,
        f"hot-dir home: rule-1 precedence violation missing (stdout: {stdout!r})",
    )


def _selftest_absolute_home_repo(root: Path, check) -> None:
    """Absolute/``~``/symlinked backlog-home anchoring characterization.

    Five arms: (1) an absolute home composed from the RESOLVED repo path
    must be honored (exit 0, no warning) — an unresolved composition on a
    symlinked temp root would trip the degenerate guard; (2) an absolute
    home OUTSIDE the repo trips the degenerate guard, warns, falls back
    to the default home, and rule 2 still fires on a committed pair-token
    file; (3) a ``~``-prefixed home is expanduser-ed (HOME overridden via
    env), anchoring the home outside the fixture repo so the degenerate
    guard rejects it — a no-expansion regression anchors the literal
    ``~/tilde-home`` inside the repo, emits no warning, and fails the
    stderr assertions; (4) abs-outside-link: a repo-relative symlinked
    home whose target resolves OUTSIDE the repo root trips the
    resolved-containment guard, warns, falls back, and rule 2 still fires
    (pins the resolve_backlog_home containment branch); (5) abs-rootlink:
    a repo-relative symlinked home resolving to the repo root itself
    trips the resolved-equal-root guard, warns, falls back, and rule 2
    still fires (without the guard the computed ``.`` relpath would match
    every path and silently disable rule 2).
    """

    def run_case(name: str, backlog_value: str, completed_value: str) -> Path:
        repo = root / name
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(
            repo,
            ".ai-playbook/facts.md",
            "```toml\n"
            f'backlog_dir = "{backlog_value}"\n'
            f'backlog_completed_dir = "{completed_value}"\n'
            "```\n",
        )
        return repo

    # abs-inside: absolute homes composed from the RESOLVED repo path (the
    # facts content depends on the repo location, so it is written directly
    # rather than via the run_case template).
    repo = root / "abs-inside"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        f'backlog_dir = "{repo.resolve() / "abs-home"}"\n'
        f'backlog_completed_dir = "{repo.resolve() / "abs-done"}"\n'
        "```\n",
    )
    _write(repo, "abs-home/pair-deferred-backlog.md")
    _write(repo, "abs-done/pair-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 0,
        f"abs-inside: expected exit 0, got {code} (stdout: {stdout!r}, "
        f"stderr: {stderr!r})",
    )
    check(
        "check_backlog_inbox_location: ok" in stdout,
        f"abs-inside: ok line missing (stdout: {stdout!r})",
    )
    check(
        "warning" not in stderr,
        f"abs-inside: unexpected warning on stderr (stderr: {stderr!r})",
    )

    # abs-outside: both keys anchored outside the repo.
    outside = root / "outside-home"
    outside.mkdir()
    repo = run_case(
        "abs-outside", str(outside), str(outside)
    )
    _write(repo, "docs/history/plans/outside-home-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"abs-outside: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/history/plans/outside-home-deferred-backlog.md: rule 2" in stdout,
        f"abs-outside: rule-2 violation missing (stdout: {stdout!r})",
    )
    check(
        "outside-home" not in stdout.replace(
            "docs/history/plans/outside-home-deferred-backlog.md", ""
        ),
        f"abs-outside: outside-home leaked into stdout (stdout: {stdout!r})",
    )
    check(
        "of the repo root" in stderr and "falling back" in stderr,
        f"abs-outside: degenerate-home warning missing (stderr: {stderr!r})",
    )

    # tilde: ~-prefixed home expanded under a fake HOME outside the repo.
    fakehome = root / "fakehome"
    _write(fakehome, "tilde-home/tilde-pair-deferred-backlog.md")
    repo = run_case("tilde", "~/tilde-home", "~/tilde-home/done")
    _write(repo, "docs/history/plans/tilde-home-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(
        repo, env_extra={"HOME": str(fakehome)}
    )
    check(
        code == 1,
        f"tilde: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/history/plans/tilde-home-deferred-backlog.md: rule 2" in stdout,
        f"tilde: rule-2 violation missing (stdout: {stdout!r})",
    )
    check(
        "tilde-pair-deferred-backlog.md" not in stdout,
        f"tilde: fakehome fixture leaked into stdout (stdout: {stdout!r})",
    )
    check(
        "of the repo root" in stderr and "falling back" in stderr,
        f"tilde: degenerate-home warning missing (stderr: {stderr!r})",
    )

    # abs-outside-link: repo-relative symlinked home whose target resolves
    # OUTSIDE the repo root. Pins the resolve_backlog_home resolved-
    # containment guard: without it the home lexically sits inside the
    # repo (degenerate guard passes) while anchoring rule-2 exclusions
    # outside it, silently exempting the outside pair-token file.
    outside2 = root / "outside-home2"
    _write(outside2, "outside-link-pair-deferred-backlog.md")
    repo = run_case("abs-outside-link", "home-link", "home-link/done")
    (repo / "home-link").symlink_to(outside2)
    _write(repo, "docs/history/plans/victim-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"abs-outside-link: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/history/plans/victim-deferred-backlog.md: rule 2" in stdout,
        f"abs-outside-link: rule-2 violation missing (stdout: {stdout!r})",
    )
    check(
        "resolves outside the repo root" in stderr and "falling back" in stderr,
        f"abs-outside-link: containment warning missing (stderr: {stderr!r})",
    )
    check(
        "outside-link-pair-deferred-backlog.md" not in stdout,
        f"abs-outside-link: outside file leaked into stdout (stdout: {stdout!r})",
    )

    # abs-rootlink: repo-relative symlinked home resolving to the repo
    # root itself (symlink target "."). Pins the resolved-equal-root
    # guard: without it the lexically valid value passes both earlier
    # guards, the scan-side relpath computes to ".", and
    # is_relative_to(Path(".")) matches every path, silently disabling
    # rule 2 on the whole tracked tree.
    repo = run_case("abs-rootlink", "rootlink", "rootlink/done")
    (repo / "rootlink").symlink_to(".")
    _write(repo, "docs/history/plans/rootlink-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"abs-rootlink: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/history/plans/rootlink-deferred-backlog.md: rule 2" in stdout,
        f"abs-rootlink: rule-2 violation missing (stdout: {stdout!r})",
    )
    check(
        "resolves to the repo root" in stderr and "falling back" in stderr,
        f"abs-rootlink: root-equal warning missing (stderr: {stderr!r})",
    )
    check(
        "check_backlog_inbox_location: ok" not in stdout,
        f"abs-rootlink: unexpected ok line (stdout: {stdout!r})",
    )


def _selftest_parser_unavailable_repo(root: Path, check) -> None:
    """``facts_paths`` import failure branch: facts are ignored.

    The script is copied ALONE into a scratch subdir (no ``facts_paths.py``
    beside the copy) and run with ``--repo-root`` via a direct
    ``subprocess.run``: ``_run_script`` targets ``__file__`` and cannot
    run the copy, and it cannot DELETE env keys (setting
    ``PYTHONPATH=""`` would inject an empty ``sys.path`` entry). The env
    drops ``PYTHONPATH`` entirely so neither an ambient ``PYTHONPATH``
    nor a repo-adjacent ``facts_paths.py`` can satisfy the import. With
    the parser unavailable the facts-configured home is ignored: the
    default home does not contain the committed pair-token file, so rule
    2 fires (exit 1) and the parser warning lands on stderr; with a
    working parser the file sits inside the configured home, is
    excluded, and the run exits 0.
    """
    repo = root / "facts-ignored"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        'backlog_dir = "inside-home"\n'
        'backlog_completed_dir = "inside-home/completed"\n'
        "```\n",
    )
    _write(repo, "inside-home/lone-parser-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    scratch_dir = root / "facts-ignored-scratch"
    scratch_dir.mkdir()
    script_copy = scratch_dir / Path(__file__).name
    shutil.copy(str(Path(__file__).resolve()), str(script_copy))

    env = {k: v for k, v in _clean_git_env().items() if k != "PYTHONPATH"}
    proc = subprocess.run(
        [sys.executable, str(script_copy), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(scratch_dir),
    )
    check(
        proc.returncode == 1,
        f"facts-ignored: expected exit 1, got {proc.returncode} "
        f"(stdout: {proc.stdout!r}, stderr: {proc.stderr!r})",
    )
    check(
        "inside-home/lone-parser-deferred-backlog.md: rule 2"
        in proc.stdout,
        f"facts-ignored: rule-2 violation missing (stdout: {proc.stdout!r})",
    )
    check(
        "facts parser unavailable" in proc.stderr,
        f"facts-ignored: parser-unavailable warning missing "
        f"(stderr: {proc.stderr!r})",
    )


def _selftest_hot_dirs_key_repo(root: Path, check) -> None:
    """``backlog_hot_dirs`` facts key: replace semantics + fallback rules.

    Seven arms: (1) override — the configured list fully replaces the
    defaults, so a token file under a DEFAULT hot dir is not flagged and
    the custom dir fires rule 1; (2) blank — a present-but-empty key
    warns and falls back so rule 1 cannot silently disable; (3) an
    entry whose first segment is ``..`` is dropped with a warning while
    the surviving entries stay active (comma+space mixed separators); (4)
    a lexically valid but ABSENT entry warns and is dropped (built-in
    defaults keep their silent absent-dir tolerance, key entries warn);
    (5) an entirely-invalid effective set warns and falls back to the
    defaults; (6) escaping-top-level — a committed symlinked hot-dir entry
    whose target resolves OUTSIDE the repo root is DROPPED by the
    ``resolve_hot_dirs`` resolved-containment validation (the entry never
    reaches the walk) with the ``resolves outside the repo root``
    warning; the drop empties the effective set, so the defaults apply
    and the committed docs/tmp file fires rule 1. Pins the
    ``resolve_hot_dirs`` containment drop, NOT the ``scan_repo``
    top-level check (unreachable for configured entries because the drop
    fires first; that check is TOCTOU defense-in-depth and is pinned by
    the ``symlink#default-dir-escape`` arm in the symlink-repo selftest);
    (7) dotdot-prefixed-name - a real in-repo directory whose NAME starts
    with ``..`` is honored, pinning the first-segment escape test.
    """

    def run_case(name: str, hot_dirs_value: str) -> Path:
        repo = root / name
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(
            repo,
            ".ai-playbook/facts.md",
            "```toml\n"
            'backlog_dir = "docs/history/backlog/"\n'
            'backlog_completed_dir = "docs/history/backlog/completed/"\n'
            f'backlog_hot_dirs = "{hot_dirs_value}"\n'
            "```\n",
        )
        return repo

    # override: configured list replaces the defaults entirely.
    repo = run_case("override", "custom-hot")
    _write(repo, "custom-hot/override-deferred-backlog.md")
    _write(repo, "docs/maintenance/replaced-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, _stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#override: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "custom-hot/override-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#override: custom rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "docs/maintenance/replaced-backlog.md" not in stdout,
        f"hot_dirs_key#override: default hot dir still scanned — replace semantics broken (stdout: {stdout!r})",
    )

    # blank: present-but-empty key must not disable rule 1.
    repo = run_case("blank", "")
    _write(repo, "docs/tmp/blank-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#blank: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/tmp/blank-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#blank: fallback rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "present but empty" in stderr,
        f"hot_dirs_key#blank: empty-key warning missing (stderr: {stderr!r})",
    )

    # escaping-entry: mixed separators; the ``..`` entry is dropped with
    # a warning, the survivors stay active.
    repo = run_case("escaping-entry", "custom-hot,../outside docs/tmp")
    _write(repo, "custom-hot/kept-deferred-backlog.md")
    _write(repo, "docs/tmp/kept-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#escaping-entry: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "custom-hot/kept-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#escaping-entry: custom-hot rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "docs/tmp/kept-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#escaping-entry: docs/tmp rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "../outside" in stderr,
        f"hot_dirs_key#escaping-entry: escaping-entry drop warning missing (stderr: {stderr!r})",
    )

    # missing-entry: a lexically valid but absent entry warns and is
    # dropped; the surviving entry stays active.
    repo = run_case("missing-entry", "custom-hot ghost-hot")
    _write(repo, "custom-hot/kept-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#missing-entry: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "custom-hot/kept-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#missing-entry: custom-hot rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "does not exist" in stderr and "ghost-hot" in stderr,
        f"hot_dirs_key#missing-entry: absent-entry warning missing (stderr: {stderr!r})",
    )

    # all-escaping: empty effective set warns and falls back to defaults.
    repo = run_case("all-escaping", "../only")
    _write(repo, "docs/tmp/fallback-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#all-escaping: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/tmp/fallback-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#all-escaping: fallback rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "has no valid entries" in stderr,
        f"hot_dirs_key#all-escaping: empty-effective-set warning missing (stderr: {stderr!r})",
    )

    # escaping-top-level: a committed symlinked hot-dir entry whose target
    # resolves OUTSIDE the repo root is DROPPED by the resolve_hot_dirs
    # resolved-containment validation before the walk ever starts; the
    # drop empties the effective set, so the defaults apply and the
    # committed docs/tmp file fires rule 1. Pins the resolve_hot_dirs
    # containment DROP (entry dropped before the walk), NOT the scan_repo
    # top-level check: for configured entries that check is unreachable
    # because the drop fires first, and it serves as TOCTOU
    # defense-in-depth only (pinned separately by
    # symlink#default-dir-escape). Removing the resolve_hot_dirs drop
    # instead lets the walk reach outside the repo and leak the outside
    # file.
    repo = run_case("escaping-top-level", "custom-hot")
    outside = root / "escaping-outside-dir"
    _write(outside, "outside-escaping-deferred-backlog.md")
    esc_link = repo / "custom-hot"
    esc_link.symlink_to(outside)
    _write(repo, "docs/tmp/fallback2-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#escaping-top-level: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "resolves outside the repo root" in stderr and "custom-hot" in stderr,
        f"hot_dirs_key#escaping-top-level: containment warning missing (stderr: {stderr!r})",
    )
    check(
        "outside-escaping-deferred-backlog.md" not in stdout,
        f"hot_dirs_key#escaping-top-level: outside file leaked into stdout (stdout: {stdout!r})",
    )
    check(
        "docs/tmp/fallback2-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#escaping-top-level: default-hot-dirs rule-1 violation missing (stdout: {stdout!r})",
    )

    # dotdot-prefixed-name: a real in-repo directory whose NAME starts with
    # ``..`` (e.g. ``..dotdotdir``) is a valid repo-relative entry and must
    # be HONORED, not dropped by the ``..``-escape check. Pins the
    # first-segment escape test (``..`` exactly or ``../``-prefixed): the
    # old raw-prefix check (``norm.startswith("..")``) falsely rejected
    # such names with a ``not a repo-relative directory`` warning, so the
    # committed token file inside escaped rule 1.
    repo = run_case("dotdot-prefixed-name", "..dotdotdir")
    _write(repo, "..dotdotdir/dotdot-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"hot_dirs_key#dotdot-prefixed-name: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "..dotdotdir/dotdot-deferred-backlog.md: rule 1" in stdout,
        f"hot_dirs_key#dotdot-prefixed-name: dotdot-named-dir rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "not a repo-relative directory" not in stderr,
        f"hot_dirs_key#dotdot-prefixed-name: dotdot-named dir falsely dropped as escaping (stderr: {stderr!r})",
    )


def _selftest_windows_portability(root: Path, check) -> None:
    """Windows-portability probes (in-process; host-independent).

    Two arms: (1) ``winport#hot-dir-backslash-parts`` — the
    ``_hot_dir_parts`` segmentation helper normalizes backslash separators
    before splitting, so a Windows-native configured entry yields
    ``Path.parts``-matchable tuples while a forward-slash entry passes
    through unchanged; (2) ``winport#cross-drive-relpath-fallback`` — a
    cross-drive ``os.path.relpath`` ``ValueError`` (a Windows-only
    condition, forced here by patching ``relpath`` to raise) lands on the
    documented warn-and-fallback default-home path instead of crashing
    ``resolve_backlog_home``.
    """
    import io
    import contextlib
    import inspect
    from unittest import mock

    # (1) hot-dir-backslash-parts: separator-normalizing segmentation,
    # plus the scan_repo wiring pin (a reverted inline segmentation in
    # scan_repo would pass every other fixture on POSIX while silently
    # disabling Windows rule 1; the pinned literal matches the original
    # inline call-site form, which the helper body cannot produce).
    try:
        got = _hot_dir_parts(("docs\\maintenance", "docs/tmp"))
        check(
            got == (("docs", "maintenance"), ("docs", "tmp")),
            f"winport#hot-dir-backslash-parts: got {got!r}, expected "
            "(('docs', 'maintenance'), ('docs', 'tmp'))",
        )
        check(
            _hot_dir_parts(("docs/tmp",)) == (("docs", "tmp"),),
            "winport#hot-dir-backslash-parts: forward-slash entry changed",
        )
        try:
            scan_src = inspect.getsource(scan_repo)
        except (OSError, TypeError):
            # Source unavailable (frozen/zipimport execution): the wiring
            # pin is vacuous there; skip it rather than abort the harness.
            scan_src = ""
        check(
            "tuple(h.split" not in scan_src,
            "winport#hot-dir-backslash-parts: scan_repo inline "
            "segmentation regression",
        )
    except NameError:
        check(
            False,
            "winport#hot-dir-backslash-parts: _hot_dir_parts helper missing",
        )

    # (2) cross-drive-relpath-fallback: relpath ValueError warns + defaults.
    repo = root / "winport-crossdrive"
    repo.mkdir()
    # No git repo needed: resolve_backlog_home is called directly and only
    # reads the facts file (pure in-process probe, no scan).
    _write(
        repo,
        ".ai-playbook/facts.md",
        "```toml\n"
        'backlog_dir = "docs/history/backlog/"\n'
        'backlog_completed_dir = "docs/history/backlog/completed/"\n'
        "```\n",
    )
    err = io.StringIO()
    uncaught = False
    with mock.patch("os.path.relpath", side_effect=ValueError):
        with contextlib.redirect_stderr(err):
            try:
                home_pair = resolve_backlog_home(repo.resolve())
            except ValueError:
                # Record here, FAIL outside the redirect below: the
                # harness prints FAIL labels to stderr, which this
                # context captures.
                uncaught = True
    if uncaught:
        check(
            False,
            "winport#cross-drive-relpath-fallback: uncaught "
            "ValueError (no fallback)",
        )
        return
    expected = (
        repo.resolve() / "docs/history/backlog",
        repo.resolve() / "docs/history/backlog/completed",
    )
    check(
        home_pair == expected,
        f"winport#cross-drive-relpath-fallback: {home_pair!r} != default "
        f"{expected!r}",
    )
    check(
        "falling back" in err.getvalue()
        and "outside the repo root" in err.getvalue(),
        f"winport#cross-drive-relpath-fallback: cross-drive fallback "
        f"warning missing (stderr: {err.getvalue()!r})",
    )


def _selftest_hot_dir_symlink_repo(root: Path, check) -> None:
    """In-hot-dir symlinks: link-path reporting, escape flags, cycle safety.

    Seven arms: (1) link-path — a symlink to a sibling real dir surfaces the
    token file under BOTH its real path and the link path (the link-path
    form is the regression witness); (2) carve-out evasion — the
    ``docs/tmp/execute-plan`` carve-out must not be reachable through a
    symlink; (3) escape — symlink targets outside the hot dir (absolute
    outside the repo, and inside the repo but outside the hot dir) are
    flagged ``hot-dir symlink not traversed`` and NOT scanned; (4) cycle —
    a mutual symlink loop terminates via the visited set with no flag
    (guarded by a 60s timeout); (5) file-link parity — a symlinked FILE
    yields under its link basename; (6) broken — a dangling symlink is
    flagged and produces no violation; (7) default-dir-escape — a
    symlinked DEFAULT hot dir (no ``backlog_hot_dirs`` key) resolving
    outside the repo root trips the ``scan_repo`` top-level containment
    check, which is otherwise unreachable for configured entries (the
    ``resolve_hot_dirs`` drop fires first) and pins it as TOCTOU
    defense-in-depth.
    """

    def run_case(name: str) -> Path:
        repo = root / name
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(
            repo,
            ".ai-playbook/facts.md",
            "```toml\n"
            'backlog_dir = "docs/history/backlog/"\n'
            'backlog_completed_dir = "docs/history/backlog/completed/"\n'
            "```\n",
        )
        return repo

    def link(repo: Path, at: str, target: str) -> None:
        path = repo / at
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)

    # link-path: real dir + symlink to it; BOTH path forms must be reported.
    repo = run_case("symlink-link-path")
    _write(repo, "docs/maintenance/realdir/linked-deferred-backlog.md")
    link(repo, "docs/maintenance/link", "realdir")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, _stderr = _run_script(repo)
    check(
        code == 1,
        f"symlink#link-path: expected exit 1, got {code} (stdout: {stdout!r})",
    )
    check(
        "docs/maintenance/realdir/linked-deferred-backlog.md: rule 1" in stdout,
        f"symlink#link-path: real-path violation missing (stdout: {stdout!r})",
    )
    check(
        "docs/maintenance/link/linked-deferred-backlog.md: rule 1" in stdout,
        f"symlink#link-path: link-path violation missing (stdout: {stdout!r})",
    )

    # carve-out evasion: the allowed execute-plan carve-out reached through
    # a symlink must still be flagged under the link path.
    repo = run_case("symlink-carve-out")
    _write(repo, "docs/tmp/execute-plan/someplan/task-backlog-log.md")
    link(repo, "docs/tmp/evadelink", "execute-plan/someplan")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, _stderr = _run_script(repo)
    check(
        "docs/tmp/evadelink/task-backlog-log.md: rule 1" in stdout,
        f"symlink#carve-out evasion: link-path violation missing (stdout: {stdout!r})",
    )

    # escape: targets outside the hot dir are flagged, not scanned.
    repo = run_case("symlink-escape")
    outside = root / "outside-dir"
    _write(outside, "outside-deferred-backlog.md")
    _write(repo, "docs/history/plans/hide/hidden-backlog-notes.md")
    link(repo, "docs/maintenance/outsidelink", str(outside))
    link(repo, "docs/maintenance/escapelink", "../plans/hide")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 0,
        f"symlink#escape flagged not scanned: expected exit 0, got {code} "
        f"(stdout: {stdout!r}, stderr: {stderr!r})",
    )
    check(
        "outside-deferred-backlog.md" not in stdout,
        f"symlink#escape flagged not scanned: outside target leaked into stdout (stdout: {stdout!r})",
    )
    check(
        "hidden-backlog-notes.md" not in stdout,
        f"symlink#escape flagged not scanned: inside-repo escape target leaked into stdout (stdout: {stdout!r})",
    )
    check(
        "hot-dir symlink not traversed" in stderr
        and "outsidelink" in stderr
        and "escapelink" in stderr,
        f"symlink#escape flagged not scanned: flag warnings missing (stderr: {stderr!r})",
    )

    # cycle: mutual dir symlinks terminate via the visited set, silently.
    repo = run_case("symlink-cycle")
    _write(repo, "docs/maintenance/a/placeholder.md")
    _write(repo, "docs/maintenance/b/placeholder.md")
    link(repo, "docs/maintenance/la", "b")
    link(repo, "docs/maintenance/lb", "a")
    link(repo, "docs/maintenance/b/lc", "../a")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo, timeout=60)
    check(
        code == 0,
        f"symlink#cycle visited-set terminates: expected exit 0 within 60s, "
        f"got {code} (stdout: {stdout!r}, stderr: {stderr!r})",
    )
    check(
        "hot-dir symlink not traversed" not in stderr,
        f"symlink#cycle visited-set terminates: unexpected flag on a "
        f"hot-dir-internal link (stderr: {stderr!r})",
    )

    # file-link parity: a symlinked file reports under its link basename.
    repo = run_case("symlink-file-link")
    _write(repo, "docs/history/plans/plain-notes.txt")
    link(repo, "docs/maintenance/filelink-deferred-backlog.md", "../plans/plain-notes.txt")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, _stderr = _run_script(repo)
    check(
        "docs/maintenance/filelink-deferred-backlog.md: rule 1" in stdout,
        f"symlink#file-link parity: link-path violation missing (stdout: {stdout!r})",
    )

    # broken: dangling symlink flagged, no violation, exit 0.
    repo = run_case("symlink-broken")
    link(repo, "docs/maintenance/brokenlink", "../nonexistent")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 0,
        f"symlink#broken: expected exit 0, got {code} (stdout: {stdout!r})",
    )
    check(
        "hot-dir symlink not traversed" in stderr and "brokenlink" in stderr,
        f"symlink#broken: flag warning missing (stderr: {stderr!r})",
    )

    # default-dir-escape: a symlinked DEFAULT hot dir (no backlog_hot_dirs
    # key) whose target resolves outside the repo root is skipped by the
    # scan_repo top-level containment check before the walk; the outside
    # pair-token file is never scanned, while the surviving default hot
    # dirs keep gating (the committed docs/tmp file fires rule 1). This is
    # the only arm where the scan_repo check is reachable: configured
    # entries are dropped earlier by resolve_hot_dirs, so here it also
    # serves as the regression pin for that TOCTOU defense-in-depth check.
    repo = run_case("symlink-default-dir-escape")
    outside2 = root / "outside-dir2"
    _write(outside2, "outside-default-escape-deferred-backlog.md")
    link(repo, "docs/maintenance", str(outside2))
    _write(repo, "docs/tmp/inside-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    code, stdout, stderr = _run_script(repo)
    check(
        code == 1,
        f"symlink#default-dir-escape: expected exit 1, got {code} "
        f"(stdout: {stdout!r})",
    )
    check(
        "hot dir 'docs/maintenance' resolves outside the repo root; skipping"
        in stderr,
        f"symlink#default-dir-escape: scan_repo containment warning missing "
        f"(stderr: {stderr!r})",
    )
    check(
        "outside-default-escape-deferred-backlog.md" not in stdout,
        f"symlink#default-dir-escape: outside file leaked into stdout "
        f"(stdout: {stdout!r})",
    )
    check(
        "docs/tmp/inside-deferred-backlog.md: rule 1" in stdout,
        f"symlink#default-dir-escape: docs/tmp rule-1 violation missing "
        f"(stdout: {stdout!r})",
    )


def _selftest_toplevel_anchor_repo(root: Path, check) -> None:
    """Bare invocation from a subdirectory (F3): toplevel anchoring.

    Run with cwd INSIDE the fixture repo (``<repo>/docs``) and no
    ``--repo-root``; a violation outside that subdirectory must still be
    reported. A regression to CWD-anchoring (``Path.cwd()``) shrinks the
    scan to ``docs/`` and misses the top-level pair-token file.
    """
    repo = root / "anchored"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(repo, "docs/placeholder.md")
    _write(repo, "plans/toplevel-deferred-backlog.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    code, stdout, _stderr = _run_script(repo, bare=True, cwd=repo / "docs")
    check(code == 1, f"toplevel anchor: expected exit 1, got {code} (stdout: {stdout!r})")
    check(
        "plans/toplevel-deferred-backlog.md: rule 2" in stdout,
        "toplevel anchor: violation outside the cwd subtree missing "
        f"(stdout: {stdout!r})",
    )


def _selftest_git_absent_repo(root: Path, check) -> None:
    """PATH stripped of git (F8): fail-open warnings + rule-1-only scan.

    Bare invocation with cwd at the fixture repo and PATH pointing at an
    empty directory: both git probes fail with OSError, so the run must
    warn for rev-parse and ls-files and still report the rule-1 hot-dir
    violation (exit 1), exercising the CWD-fallback warning of the
    default-root resolution.
    """
    repo = root / "gitabsent"
    repo.mkdir()
    empty_bin = root / "emptybin"
    empty_bin.mkdir()
    _write(repo, "docs/maintenance/untracked-backlog-inbox.md")

    code, stdout, stderr = _run_script(
        repo, bare=True, cwd=repo, env_extra={"PATH": str(empty_bin)}
    )
    check(code == 1, f"git absent: expected exit 1, got {code} (stdout: {stdout!r})")
    check(
        "docs/maintenance/untracked-backlog-inbox.md: rule 1" in stdout,
        f"git absent: rule-1 violation missing (stdout: {stdout!r})",
    )
    check(
        "git rev-parse unavailable; scanning CWD" in stderr,
        f"git absent: rev-parse fallback warning missing (stderr: {stderr!r})",
    )
    check(
        "git ls-files unavailable" in stderr,
        f"git absent: ls-files fail-open warning missing (stderr: {stderr!r})",
    )


def _selftest_clean_tree(root: Path, check) -> None:
    """Clean tree (allowed fixtures only, no git): exit 0."""
    clean = root / "clean"
    _write(clean, "docs/history/backlog/2026-09-03-clean.md")
    _write(clean, "docs/maintenance/confluence-sync-manifest.json")
    _write(clean, "docs/reviews/x-deferred.md")
    _write(clean, "docs/tmp/plan-requirements-2026-09-03-backlog-gate.md")
    code, _stdout, stderr = _run_script(clean)
    check(code == 0, f"clean tree: expected exit 0, got {code}")
    check(
        "rule 2 skipped" in stderr,
        f"clean tree: 'rule 2 skipped' warning missing (stderr: {stderr!r})",
    )


def _selftest_nested_git_repo(root: Path, check) -> None:
    """Warn-only nested-``.git`` detection: four arms.

    (1) nested-git-warns: an untracked nested ``.git`` directory (scratch
    repo shape) inside the repo produces a stderr warning naming the path
    and an owner class, with exit code unaffected; (2) worktree-silent: a
    registered worktree's ``.git`` gitfile inside the repo is silent;
    (3) submodule-silent: a submodule-shaped gitfile pointing into
    ``.git/modules/`` is silent; (4) gitignore-silent: a nested ``.git``
    matched by ``.gitignore`` is silent.
    """

    def init_fixture(name: str) -> Path:
        repo = root / name
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(
            repo,
            ".ai-playbook/facts.md",
            "```toml\n"
            'backlog_dir = "docs/history/backlog/"\n'
            'backlog_completed_dir = "docs/history/backlog/completed/"\n'
            "```\n",
        )
        _write(repo, "docs/history/plans/plain-notes.md")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "init")
        return repo

    # (1) untracked nested .git: warns with named path + owner class.
    repo = init_fixture("nested-git-warns")
    scratch = repo / "scratch-fixture" / "repoX"
    scratch.mkdir(parents=True)
    (scratch / ".git").mkdir()
    (scratch / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    code, stdout, stderr = _run_script(repo)
    check(code == 0, f"nested-git-warns: expected exit 0, got {code} (stderr: {stderr!r})")
    check(
        "scratch-fixture/repoX/.git" in stderr,
        f"nested-git-warns: warning missing named path (stderr: {stderr!r})",
    )
    check(
        "scratch fixture" in stderr and "warn-only" in stderr,
        f"nested-git-warns: owner-class warn-only wording missing (stderr: {stderr!r})",
    )
    check(
        "check_backlog_inbox_location: ok" in stdout,
        f"nested-git-warns: warn-only pass changed the ok exit surface (stdout: {stdout!r})",
    )

    # (2) registered worktree inside the repo: silent.
    repo = init_fixture("nested-git-worktree")
    _git(repo, "worktree", "add", "-b", "wt-branch", "inner-wt")
    code, _stdout, stderr = _run_script(repo)
    check(code == 0, f"nested-git-worktree: expected exit 0, got {code}")
    check(
        "nested .git" not in stderr,
        f"nested-git-worktree: registered worktree flagged (stderr: {stderr!r})",
    )

    # (3) submodule-shaped gitdir: gitfile pointing into .git/modules/.
    repo = init_fixture("nested-git-submodule")
    (repo / ".git" / "modules" / "sub").mkdir(parents=True)
    sub = repo / "sub"
    sub.mkdir()
    (sub / ".git").write_text(
        "gitdir: ../.git/modules/sub\n", encoding="utf-8"
    )
    code, _stdout, stderr = _run_script(repo)
    check(code == 0, f"nested-git-submodule: expected exit 0, got {code}")
    check(
        "nested .git" not in stderr,
        f"nested-git-submodule: submodule-shaped gitdir flagged (stderr: {stderr!r})",
    )

    # (4) gitignored nested .git: silent.
    repo = init_fixture("nested-git-ignored")
    _write(repo, ".gitignore", "runtime/nested/.git\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "gitignore")
    nested = repo / "runtime" / "nested"
    nested.mkdir(parents=True)
    (nested / ".git").mkdir()
    code, _stdout, stderr = _run_script(repo)
    check(code == 0, f"nested-git-ignored: expected exit 0, got {code}")
    check(
        "nested .git" not in stderr,
        f"nested-git-ignored: gitignored path flagged (stderr: {stderr!r})",
    )


def run_selftest() -> int:
    import tempfile

    _CHECK_FAILURES[0] = 0
    check = _make_check()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for _name, fn in (
            ("main_repo", _selftest_main_repo),
            ("factsless_repo", _selftest_factsless_repo),
            ("blank_key_repo", _selftest_blank_key_repo),
            ("degenerate_home_repo", _selftest_degenerate_home_repo),
            ("hot_dir_home_repo", _selftest_hot_dir_home_repo),
            ("absolute_home_repo", _selftest_absolute_home_repo),
            ("parser_unavailable_repo",
             _selftest_parser_unavailable_repo),
            ("hot_dirs_key_repo", _selftest_hot_dirs_key_repo),
            ("windows_portability", _selftest_windows_portability),
            ("hot_dir_symlink_repo", _selftest_hot_dir_symlink_repo),
            ("toplevel_anchor_repo", _selftest_toplevel_anchor_repo),
            ("git_absent_repo", _selftest_git_absent_repo),
            ("clean_tree", _selftest_clean_tree),
            ("nested_git_repo", _selftest_nested_git_repo),
        ):
            fn(root, check)

    if _CHECK_FAILURES[0]:
        print(
            f"check_backlog_inbox_location: --selftest FAILED "
            f"({_CHECK_FAILURES[0]})",
            file=sys.stderr,
        )
        return 1
    print("check_backlog_inbox_location: --selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
