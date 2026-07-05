#!/usr/bin/env python3
"""Lessons-recall core: agent-agnostic proactive recall hook core.

On each consultation, classify the user's prompt INTENT via
``lessons_classify.classify_prompt``. If it returns a family, select the
family-matched lessons from the corpora, de-dup against a per-(project,
session) append-only state file, and emit a single ``json.dumps(text)``
reminder string. The core NEVER blocks (exit 0, silent or inject).

Key invariants (see plan Terms + Design Invariants):
- Agent-agnostic: accepts ``--session-id`` as OPAQUE data; ZERO agent-channel
  knowledge (``session_channel.py`` is the adapter's concern, NEVER imported
  here).
- De-dup is APPEND-ONLY (``O_APPEND``), time-windowed
  (``RECALL_DEDUP_WINDOW`` default 24h, ALL agents full window),
  per-(project, session), home-anchored, NEVER uses raw cwd as a filename.
- The DE-DUP MEMBERSHIP KEY is ``N`` (lesson number) within the per-(project,
  session) file; ``ts`` is pruning metadata only.
- The SUPPRESSION PREDICATE is PER-LESSON (P1): drop each lesson whose ``N`` is
  in ``seen``, rank+concat+truncate the remainder.
- ``project`` is derived by CALLING ``facts_paths.resolve_project_key`` (single
  shared function object with ``skill_gate.py``; asserted IDENTITY in
  ``#project_single_source``).
- LOUD keying: logs ``keying=env-var|project-only`` to
  ``~/.ai-playbook/logs/hooks.log`` via the shared ``_append_hooks_log_line``
  helper. The core CANNOT emit ``keying=no-anchor`` (that is the resolver's
  job). ``keying`` is PURE LOG METADATA and drives NO core branch.

Sibling-import bootstrap (r14-M2) is REQUIRED because this core is symlinked
into ``~/.ai-playbook/scripts/`` and must import sibling leaves from the REPO
scripts dir (where they live), not ``~/.ai-playbook/scripts/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Sibling-import bootstrap (r14-M2): MUST be the FIRST line after stdlib
# imports. The core is symlinked into ~/.ai-playbook/scripts/ and imports
# sibling leaves (facts_paths / lessons_classify / lessons_corpus) from the
# repo scripts dir; Path(__file__).resolve().parent follows the symlink to the
# repo dir where the siblings exist. Mirrors lessons_adopt.py:38-41.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths  # noqa: E402
import lessons_classify  # noqa: E402
import lessons_corpus  # noqa: E402

#: Default de-dup window. FLAGGED threshold (confirm at implementation; see
#: plan Monitor). ALL agents use the FULL window unconditionally (r10-M10
#: collapsed the halved-window steady state). Without a window, recall
#: silently decays to zero for long-used cwds.
RECALL_DEDUP_WINDOW = 86400  # seconds (24h)

#: Default per-reminder body budget (HEAD truncation; chars). FLAGGED.
DEFAULT_BUDGET = 1500

#: Separator between concatenated lesson bodies in the reminder text.
BODY_SEPARATOR = "\n\n"

#: Literal session component for the empty-after-strip / absent case. NOT
#: ``sha1("").hexdigest()[:16]`` (which would be the constant ``da39a3ee5e6b4b0d``
#: and a silent collision - r10-M4).
NO_SESSION_KEY = "no-session"

#: Default home-anchored state dir (created 0o700). Home-anchored like the
#: skill-gate marker; present in worktrees/subdirs, never depends on a
#: cwd-relative tmp_dir (r5-B1).
DEFAULT_STATE_DIR = Path.home() / ".ai-playbook" / "runtime" / "lessons-recall"

#: Project corpus path relative to the start_dir (cwd). Convention only; the
#: file may be absent.
PROJECT_CORPUS_REL = Path("docs") / "maintenance" / "development_lessons.md"

#: Truncation indicator appended IFF any selected lesson was sliced.
TRUNCATION_INDICATOR = "\n\n[...truncated]"

#: Default prompt classifier (v1). v2 is opt-in via ``--classifier v2``.
DEFAULT_CLASSIFIER = "v1"

#: Pinned recall observability schema (Task 3; consumed by hooks_log_summary Task 4).
RECALL_LOG_EVENT = "recall"
RECALL_OUTCOME_FIRE = "fire"
RECALL_OUTCOME_SUPPRESS_DEDUP = "suppress-dedup"
RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS = "suppress-empty-corpus"
RECALL_OUTCOME_SUPPRESS_CLASSIFY = "suppress-classify"
RECALL_LOG_OUTCOMES = (
    RECALL_OUTCOME_FIRE,
    RECALL_OUTCOME_SUPPRESS_DEDUP,
    RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS,
    RECALL_OUTCOME_SUPPRESS_CLASSIFY,
)


# --------------------------------------------------------------------------- #
# Re-export for IDENTITY selftest (#project_single_source). The core MUST
# expose the SAME function object as facts_paths.resolve_project_key; a copied
# body would drift and desync the dedup state key from the marker key (Family D).
# --------------------------------------------------------------------------- #
resolve_project_key = facts_paths.resolve_project_key


def _derive_session_component(raw_session_id: str | None) -> str:
    """Derive the SANITIZED ``session`` filename component.

    The emptiness check (``.strip() == ""``) is the FIRST operation, before
    any hashing (r11-M3). An empty-after-strip ``--session-id`` is treated
    IDENTICALLY to absent -> literal ``no-session`` (NOT ``sha1("")[:16]`` =
    ``da39a3ee5e6b4b0d``, a constant collision - r10-M4). Otherwise the value
    is hashed to hex (path-safe; a hostile env var like ``../foo`` cannot
    traverse the runtime dir or alias another session's state).
    """
    if raw_session_id is None or raw_session_id.strip() == "":
        return NO_SESSION_KEY
    return hashlib.sha1(raw_session_id.encode()).hexdigest()[:16]


def _state_file_path(state_dir: Path, project: str, session: str) -> Path:
    """Return the per-(project, session) state file path."""
    return state_dir / f"{project}.{session}.state"


def _read_seen_set(state_path: Path, now: float) -> set[int]:
    """Compute the in-memory seen-set of lesson numbers from the append-only
    state file.

    Open ``O_RDONLY | O_NOFOLLOW`` inside ``try/except FileNotFoundError`` (and
    the ``OSError`` family); a MISSING/unreadable file yields ``seen = set()``
    (r8-M3 cold-start), and a SYMLINK leaf at the state path is REFUSED
    (``O_NOFOLLOW`` raises ELOOP, caught by the ``OSError`` arm -> cold-start)
    matching the write-path hardening (r1-M2 ``_append_injection``) and the
    sibling skill_gate marker read (r2-M7 ``check_marker``). Only lines whose
    ``ts >= now - RECALL_DEDUP_WINDOW`` contribute (stale lines are IGNORED on
    read, NEVER truncated out - there is no rewrite race with concurrent
    appenders).

    Decode errors are REPLACED, not raised (r1-M3): a state file containing
    invalid UTF-8 bytes (a half-written record from a crash, or a planted
    garbage file) must NOT raise ``UnicodeDecodeError`` (a ``ValueError``,
    NOT an ``OSError``), escape ``_consult``, and be swallowed by ``main``'s
    defensive catch - silently disabling recall for that (project, session).
    ``errors="replace"`` matches the append-only defensive line-parsing below:
    replaced bytes produce malformed line entries the existing
    ``try: int(...) except ValueError: continue`` loop already skips, so a
    corrupt byte stream yields ``seen = set()`` (cold-start) rather than a
    crash, faithful to the "missing/unreadable file yields seen = set()"
    contract.
    """
    try:
        fd = os.open(str(state_path), os.O_RDONLY | os.O_NOFOLLOW)
    except (FileNotFoundError, OSError):
        return set()
    try:
        with os.fdopen(fd, "r", encoding="utf-8", errors="replace", closefd=True) as f:
            raw = f.read()
    except OSError:
        return set()

    threshold = now - RECALL_DEDUP_WINDOW
    seen: set[int] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # Tolerate malformed lines (never crash on a corrupted record); skip.
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        n_str, ts_str = parts
        try:
            n = int(n_str)
            ts = float(ts_str)
        except ValueError:
            continue
        if ts >= threshold:
            seen.add(n)
    return seen


def _append_injection(state_path: Path, number: int, ts: float) -> None:
    """Append one ``f"{N}\\t{ts}\\n"`` line via ``O_APPEND``.

    Best-effort on the write side (r8-M8): a transient failure (ENOSPC/EMFILE)
    is swallowed so the core still emits its reminder; ``O_APPEND`` guarantees
    state-file INTEGRITY when the write succeeds (no lost/corrupted lines). The
    file is APPEND-ONLY for its entire lifetime and is NEVER rewritten (NOT
    ``atomic_write_text``, which is a full-file ``os.replace`` read-modify-write
    and is NOT concurrency-atomic).

    ``O_NOFOLLOW`` (r1-M2): refuse a pre-planted symlink at the state-file leaf,
    matching the hardened marker writer (``atomic_write_text``) and the
    ``_append_hooks_log_line`` log helper. A planted symlink at
    ``<state_dir>/<project>.<session>.state`` pointing at an arbitrary
    user-owned file would otherwise be FOLLOWED and the append would corrupt
    that target one line per matching prompt. The 0o700 state dir bounds the
    blast radius to attackers who already have write access to the per-user
    runtime dir; ``O_NOFOLLOW`` closes the lone unhardened write path so all
    three writers agree. The existing ``except OSError: return`` covers the
    ``ELOOP`` ``O_NOFOLLOW`` raises on a symlink, so the cold-start path stays
    best-effort.
    """
    line = f"{number}\t{ts}\n"
    try:
        os.makedirs(state_path.parent, exist_ok=True, mode=0o700)
        fd = os.open(
            str(state_path),
            os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW,
            0o600,
        )
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        # Best-effort: state-file write failure (incl. ELOOP on a symlink leaf
        # via O_NOFOLLOW) must not block the reminder.
        return


def _load_corpus_text(path: Path | None) -> str:
    """Read a corpus file as text, returning "" if absent/unreadable. The
    corpus is READ-ONLY (this function never writes; see ``#corpus_readonly``).
    """
    if path is None or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _select_rank_concat(
    family: str,
    prompt: str,
    corpus_text: str,
) -> list[lessons_corpus.Lesson]:
    """Return ALL family-matched lessons RANKED (title-phrase-match first via
    ``phrase_present``, then lowest number). The caller concatenates, budgets,
    and de-dups the returned list.

    Ranking: title-phrase-matched lessons beat non-title-matched; within each
    group, lowest number wins. This makes the HEAD-truncation discriminator
    meaningful (``#budget_rank_priority``): the title-matched lesson survives
    even when it is the longest body.
    """
    prompt_lower = prompt.lower()
    matched: list[lessons_corpus.Lesson] = []
    for lesson in lessons_corpus.iter_lessons(corpus_text):
        if family in lesson.tags:
            matched.append(lesson)

    def title_phrased(lesson: lessons_corpus.Lesson) -> bool:
        title_lower = lesson.title.lower()
        for phrase in lessons_classify.PROMPT_INTENT_VOCAB.get(family, []):
            if lessons_classify.phrase_present(title_lower, phrase.lower()):
                return True
        return False

    # Sort: title-phrase-matched first (True sorts after False, so negate),
    # then lowest number.
    matched.sort(key=lambda L: (not title_phrased(L), L.number))
    return matched


#: Regex matching a family tag line ``**Principle:** Family <X> (...)``. The
#: rendered reminder must OMIT these (they are metadata, not lesson prose); a
#: reminder echoing "Family G" would leak the internal taxonomy into the
#: user-facing prompt (the #realistic_match selftest pins "NO literal family
#: phrase in output").
_TAG_LINE_RE = re.compile(r"^\*\*Principle:\*\*\s+Family\s+\S+.*$")


def _render_body(lesson: lessons_corpus.Lesson) -> str:
    """Render one lesson body line as ``Lesson #{N} ({title}): {body}``.

    The ``#N`` token is the SAME field as the dedup key and the ``#budget``
    selftest count (r8-M7). The body is the joined body_lines (the parsed
    body, NOT the raw source including the heading) with family tag lines
    (``**Principle:** Family <X>``) STRIPPED - those are routing metadata,
    not lesson prose, and must not leak the internal taxonomy into the
    user-facing reminder.
    """
    body_lines = [ln for ln in lesson.body_lines if not _TAG_LINE_RE.match(ln)]
    body = "\n".join(body_lines).strip()
    return f"Lesson #{lesson.number} ({lesson.title}): {body}"


def _classify_prompt(prompt: str, classifier: str) -> tuple[str, list[str]] | None:
    """Dispatch to v1 or v2 prompt classifier."""
    if classifier == "v2":
        return lessons_classify.classify_prompt_v2(prompt)
    return lessons_classify.classify_prompt(prompt)


def _append_recall_log(*, outcome: str, family: str | None = None) -> None:
    """Append one pinned ``event=recall`` JSONL line to hooks.log."""
    payload: dict[str, object] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": RECALL_LOG_EVENT,
        "outcome": outcome,
    }
    if family is not None:
        payload["family"] = family
    facts_paths._append_hooks_log_line(payload)


def _consult(
    prompt: str,
    *,
    start_dir: Path,
    state_dir: Path,
    session_id: str | None,
    budget: int,
    no_dedup: bool,
    classifier: str = DEFAULT_CLASSIFIER,
) -> str:
    """Run one consultation. Returns the reminder text to emit (possibly ""),
    wrapped by the caller in ``json.dumps``.

    Steps:
    1. Classify gate. If ``classify_prompt`` returns None, return "" WITHOUT
       touching the state file (dedup read is GATED behind a successful
       classify; non-matching prompts must not grow the append-only file).
    2. LOUD keying: append one hooks.log line (env-var vs project-only).
    3. Resolve corpora (user-level + project-level), select+rank family-matched
       lessons from the UNION of both corpora.
    4. Read seen-set from the per-(project, session) state file (cold-start ->
       empty set).
    5. PER-LESSON suppression (P1): drop every lesson whose N is in seen.
    6. Rank + concat + HEAD-truncate to budget; add truncation indicator iff
       any selected lesson was sliced.
    7. Append one ``{N}\\t{ts}\\n`` line per injected lesson (best-effort).
    8. Append recall observability (``event=recall``) on EVERY consultation.
    """
    # Step 1: classify gate.
    classified = _classify_prompt(prompt, classifier)
    if classified is None:
        _append_recall_log(outcome=RECALL_OUTCOME_SUPPRESS_CLASSIFY)
        return ""
    family, _matched_phrases = classified

    # Step 2: LOUD keying (PURE LOG METADATA, drives NO core branch).
    keying = "env-var" if (session_id is not None and session_id.strip() != "") else "project-only"
    facts_paths._append_hooks_log_line({
        "ts": datetime.now(timezone.utc).isoformat(),
        "keying": keying,
    })

    # Step 3: resolve corpora (user-level via facts_paths; project-level cwd-
    # relative). Read both, concatenate the text so iter_lessons sees the union.
    user_corpus = facts_paths.user_corpus_path(start_dir)
    project_corpus = start_dir / PROJECT_CORPUS_REL
    corpus_text = _load_corpus_text(user_corpus) + "\n\n" + _load_corpus_text(project_corpus)

    # Select + rank ALL family-matched lessons from the union corpus.
    ranked = _select_rank_concat(family, prompt, corpus_text)

    # Step 4 + 5: de-dup. project is derived by CALLING the resolver (single
    # shared function object with skill_gate.py). session is SANITIZED.
    now = time.time()
    if no_dedup:
        seen: set[int] = set()
        state_path: Path | None = None
    else:
        project = facts_paths.resolve_project_key(start_dir)
        session = _derive_session_component(session_id)
        state_path = _state_file_path(state_dir, project, session)
        seen = _read_seen_set(state_path, now)

    # PER-LESSON (P1) suppression: drop each lesson whose N is in seen.
    survivors = [L for L in ranked if L.number not in seen]
    if not survivors:
        outcome = (
            RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS
            if not ranked
            else RECALL_OUTCOME_SUPPRESS_DEDUP
        )
        _append_recall_log(outcome=outcome, family=family)
        return ""

    # Step 6: concat + HEAD-truncate.
    rendered = [_render_body(L) for L in survivors]
    full = BODY_SEPARATOR.join(rendered)

    truncated = full[:budget]
    sliced = len(full) > budget
    if sliced:
        truncated = truncated + TRUNCATION_INDICATOR

    # Step 7: append one line per injected lesson (best-effort).
    if state_path is not None:
        for L in survivors:
            _append_injection(state_path, L.number, now)

    _append_recall_log(outcome=RECALL_OUTCOME_FIRE, family=family)
    return truncated


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lessons_recall.py",
        description=(
            "Agent-agnostic lessons-recall core. Classifies the prompt, "
            "selects family-matched lessons, de-dups against a per-"
            "(project, session) append-only state file, and emits one "
            "json.dumps(text) reminder string. Never blocks (exit 0)."
        ),
    )
    p.add_argument("--prompt", help="User prompt text (or read from stdin).")
    p.add_argument(
        "--session-id",
        default=None,
        help=(
            "Adapter-supplied opaque session value. Absent/empty-after-strip "
            "-> 'no-session' key + FULL window."
        ),
    )
    p.add_argument(
        "--state-dir",
        default=None,
        help=(
            "State dir for the append-only de-dup files. Defaults to "
            "~/.ai-playbook/runtime/lessons-recall/."
        ),
    )
    p.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help=f"Max chars of the HEAD of the ranked concatenation (default {DEFAULT_BUDGET}).",
    )
    p.add_argument(
        "--no-dedup",
        action="store_true",
        help="Skip de-dup (do not read or write the state file).",
    )
    p.add_argument(
        "--classifier",
        choices=("v1", "v2"),
        default=DEFAULT_CLASSIFIER,
        help=f"Prompt classifier version (default {DEFAULT_CLASSIFIER}).",
    )
    p.add_argument("--selftest", action="store_true", help="Run selftests.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    ns = parser.parse_args(args)

    if ns.selftest:
        return selftest()

    # Resolve start_dir = cwd (the core is invoked from the agent's cwd).
    start_dir = Path.cwd()

    # Resolve state_dir (default home-anchored).
    state_dir = Path(ns.state_dir).expanduser() if ns.state_dir else DEFAULT_STATE_DIR

    # Prompt: flag wins; else stdin (no prompt -> empty -> classify returns None).
    prompt = ns.prompt
    if prompt is None:
        try:
            prompt = sys.stdin.read()
        except OSError:
            prompt = ""
    if prompt is None:
        prompt = ""

    try:
        text = _consult(
            prompt,
            start_dir=start_dir,
            state_dir=state_dir,
            session_id=ns.session_id,
            budget=ns.budget,
            no_dedup=ns.no_dedup,
            classifier=ns.classifier,
        )
    except (KeyboardInterrupt, SystemExit):
        # Propagate Ctrl-C / SystemExit: a user interrupt during a consultation
        # must NOT be silently swallowed and logged as keying=error (r2-M5,
        # mirroring skill_gate.py r1-M1/M9). Narrowing away from
        # ``BaseException`` keeps the defensive fail-open for unexpected
        # ``Exception`` subclasses (Family G: a recall core that crashes the
        # host agent is worse than no recall) without swallowing interactive
        # interrupts.
        raise
    except Exception as e:  # defensive: NEVER block (exit 0, silent).
        # Family G discipline: a recall core that crashes the host agent is
        # worse than no recall. Log and stay silent.
        facts_paths._append_hooks_log_line({
            "ts": datetime.now(timezone.utc).isoformat(),
            "keying": "error",
            "error": repr(e),
        })
        return 0

    # Emit a single json.dumps(text) string value.
    sys.stdout.write(json.dumps(text))
    return 0


# --------------------------------------------------------------------------- #
# Self-test.
# --------------------------------------------------------------------------- #
def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def _make_family_g_corpus(lessons: list[tuple[int, str, str]]) -> str:
    """Build a synthetic corpus text with Family G lessons.

    Each entry: (number, title, body). The body is wrapped so iter_lessons
    parses it and the tag line lands outside any fence.
    """
    parts: list[str] = []
    for number, title, body in lessons:
        parts.append(f"## {number}. {title}\n\n{body}\n\n**Principle:** Family G (synthetic fixture)\n")
    return "\n".join(parts)


def _run_core(
    prompt: str,
    *,
    start_dir: Path,
    state_dir: Path,
    session_id: str | None = None,
    budget: int = DEFAULT_BUDGET,
    no_dedup: bool = False,
    classifier: str = DEFAULT_CLASSIFIER,
) -> str:
    """Run _consult and return the reminder text (unwrapped)."""
    return _consult(
        prompt,
        start_dir=start_dir,
        state_dir=state_dir,
        session_id=session_id,
        budget=budget,
        no_dedup=no_dedup,
        classifier=classifier,
    )


def selftest() -> int:
    import tempfile
    from contextlib import contextmanager

    all_ok = True

    # r1-M13: capture the REAL ~/.ai-playbook/logs/hooks.log size at entry so a
    # final assertion can pin that no selftest block leaked a keying line into
    # the forensic log (every block now runs _consult/resolve_project_key under
    # isolated HOME via run_core/seed_state_file). A future block that adds a
    # bare _consult/resolve_project_key call outside isolation fails here.
    _m13_real_log = Path.home() / ".ai-playbook" / "logs" / "hooks.log"
    _m13_before = 0
    try:
        if _m13_real_log.is_file():
            _m13_before = sum(1 for _ in _m13_real_log.read_text(encoding="utf-8").splitlines() if _.strip())
    except OSError:
        _m13_before = -1

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    @contextmanager
    def isolated_home(home_dir: Path):
        """Patch HOME so facts_paths.user_corpus_path does not read the REAL
        ~/.ai-playbook/facts.md, AND so _append_hooks_log_line does not append
        to the REAL ~/.ai-playbook/logs/hooks.log. Behavioral selftests must
        not depend on the real home corpus (only the Task-1
        #shared_docs_dir_unchanged selftest uses the real home facts, and that
        is not here) and must not pollute the forensic hooks.log the runtime
        emits to (r1-M13: the LOUD-keying line lands in
        ``~/.ai-playbook/logs/hooks.log`` resolved from ``Path.home()`` at call
        time, so isolating HOME reroutes it into the tmp tree).
        """
        orig = os.environ.get("HOME")
        os.environ["HOME"] = str(home_dir)
        try:
            yield
        finally:
            if orig is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig

    # run_core (r1-M13): mirror skill_gate.py's run_consult discipline by
    # wrapping every _consult call in isolated_home(start_dir). The LOUD-keying
    # log write resolves from Path.home() at call time, so without this wrapper
    # ~10 of 13 selftest blocks would append keying=env-var/project-only lines
    # to the developer's REAL ~/.ai-playbook/logs/hooks.log on every --selftest
    # invocation. Isolating HOME to start_dir keeps the log write inside the
    # tmp tree; start_dir is td_path in every block, which is the fixture root
    # (facts resolution searches <start_dir>/.ai-playbook first, so this does
    # not change corpus resolution for blocks that set up repo facts under
    # td_path).
    def run_core(
        prompt: str,
        *,
        start_dir: Path,
        state_dir: Path,
        session_id: str | None = None,
        budget: int = DEFAULT_BUDGET,
        no_dedup: bool = False,
        classifier: str = DEFAULT_CLASSIFIER,
    ) -> str:
        with isolated_home(start_dir):
            return _run_core(
                prompt,
                start_dir=start_dir,
                state_dir=state_dir,
                session_id=session_id,
                budget=budget,
                no_dedup=no_dedup,
                classifier=classifier,
            )

    def seed_state_file(
        state_dir: Path,
        start_dir: Path,
        session_id: str | None,
        lines: list[tuple[int, float]],
    ) -> Path:
        """Pre-seed the per-(project, session) state file under isolated HOME
        (r1-M13). ``resolve_project_key`` writes ``keying=no-anchor`` to
        ``hooks.log`` on its git-failure branch; without isolation the seeding
        step pollutes the REAL ``~/.ai-playbook/logs/hooks.log`` even though the
        subsequent ``run_core`` call is isolated. Isolating HOME to ``start_dir``
        reroutes the log write into the tmp tree, matching ``run_core``.
        """
        with isolated_home(start_dir):
            project = facts_paths.resolve_project_key(start_dir)
            session = _derive_session_component(session_id)
            sf = _state_file_path(state_dir, project, session)
            sf.parent.mkdir(parents=True, exist_ok=True)
            sf.write_text(
                "".join(f"{n}\t{ts}\n" for n, ts in lines),
                encoding="utf-8",
            )
            return sf

    # ------------------------------------------------------------------ #
    # realistic_match: "the report dropped a row" -> Family G reminder.
    # Uses a synthetic fixture corpus (the repo has no project corpus and we
    # must not depend on the real home corpus for behavioral selftests).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Fixture: facts.md with shared_docs_dir pointing at a temp corpus.
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        corpus_path = shared_dir / "development_lessons.md"
        corpus_path.write_text(
            _make_family_g_corpus([
                (42, "Dropped rows must warn", "A silent drop in the matcher caused data loss."),
            ]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n",
            encoding="utf-8",
        )
        state_dir = td_path / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
        )
        check(
            "realistic_match: non-empty output",
            out != "",
            repr(out[:80]),
        )
        check(
            "realistic_match: cites a Family G lesson (Lesson #42)",
            "Lesson #42" in out,
            repr(out[:120]),
        )
        check(
            "realistic_match: NO literal family phrase in output",
            "Family G" not in out,
            repr(out[:120]),
        )
        # r1-L14: close the IFF on the truncation indicator. The single short
        # lesson here is well under budget, so the indicator must be ABSENT
        # (the budget test asserts the PRESENT-when-sliced half; this asserts
        # the ABSENT-when-not-sliced half, so a regression that always appends
        # the indicator fails here).
        check(
            "realistic_match: truncation indicator ABSENT (single short lesson, not sliced)",
            TRUNCATION_INDICATOR not in out,
            repr(out[-80:]),
        )

    # ------------------------------------------------------------------ #
    # no_match: "fix the typo" -> empty stdout, exit 0 (no classify).
    # run_core isolates HOME so the real home corpus cannot leak a match (the
    # classifier is corpus-independent and returns None here, but defense in
    # depth).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state_dir = Path(td) / "state"
        out = run_core("fix the typo", start_dir=td_path, state_dir=state_dir)
        check("no_match: empty stdout", out == "", repr(out[:80]))

    # ------------------------------------------------------------------ #
    # dedup: same matching prompt twice -> FIRST non-empty, SECOND empty.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(7, "Lost record", "A lost record must warn.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        first = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-A",
        )
        second = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-A",
        )
        check("dedup: FIRST non-empty", first != "", repr(first[:80]))
        check("dedup: SECOND (within window) empty", second == "", repr(second[:80]))

    # ------------------------------------------------------------------ #
    # dedup_expiry: third call AFTER simulating now > RECALL_DEDUP_WINDOW
    # -> NON-EMPTY again. We pre-seed the state file with a STALE line so the
    # read path filters it out.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(9, "Skipped row", "A skipped row must warn.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        stale_ts = time.time() - RECALL_DEDUP_WINDOW - 60
        sf = seed_state_file(state_dir, td_path, "sess-B", [(9, stale_ts)])
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-B",
        )
        check(
            "dedup_expiry: NON-EMPTY after stale entry expired",
            out != "" and "Lesson #9" in out,
            repr(out[:120]),
        )

    # ------------------------------------------------------------------ #
    # dedup_window_boundary: state file PRE-SEEDED with two lines straddling
    # the window (same N): one STALE (now - window - 60), one FRESH
    # (now - window + 60). FRESH key suppressed.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(11, "Boundary lesson", "Boundary data loss.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        now = time.time()
        stale_ts = now - RECALL_DEDUP_WINDOW - 60
        fresh_ts = now - RECALL_DEDUP_WINDOW + 60
        # Both lines have the SAME N (11); the FRESH one must suppress.
        sf = seed_state_file(
            state_dir, td_path, "sess-W",
            [(11, stale_ts), (11, fresh_ts)],
        )
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-W",
        )
        check(
            "dedup_window_boundary: FRESH key suppresses (empty output)",
            out == "",
            repr(out[:120]),
        )

    # ------------------------------------------------------------------ #
    # dedup_window_exact_boundary (r2-L11): a record with ts EXACTLY
    # ``now - RECALL_DEDUP_WINDOW`` is FRESH (the implementation is
    # ``ts >= now - RECALL_DEDUP_WINDOW``, inclusive). A regression changing
    # ``>=`` to ``>`` would treat the edge as STALE and re-inject. Calls
    # _read_seen_set directly with a CONTROLLED ``now`` so wall-clock drift
    # between seed and read does not push the record past the edge.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state_dir = Path(td) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        now = time.time()
        edge_ts = now - RECALL_DEDUP_WINDOW
        # Write the state file directly with one record at the exact edge.
        state_path = state_dir / "edgeproj.edge.state"
        state_path.write_text(f"31\t{edge_ts}\n", encoding="utf-8")
        seen = _read_seen_set(state_path, now)
        check(
            "dedup_window_exact_boundary: ts == now - window is FRESH (in seen)",
            31 in seen,
            f"seen={seen}",
        )

    # ------------------------------------------------------------------ #
    # dedup_partial_family: N1 FRESH + N2 STALE for the SAME family -> N2
    # INJECTED, N1 SUPPRESSED (pins PER-LESSON P1).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([
                (21, "First G lesson", "First data-loss observability gap."),
                (22, "Second G lesson", "Second data-loss observability gap."),
            ]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        now = time.time()
        fresh_ts = now - 10  # well inside window
        stale_ts = now - RECALL_DEDUP_WINDOW - 60
        sf = seed_state_file(
            state_dir, td_path, "sess-P",
            [(21, fresh_ts), (22, stale_ts)],
        )
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-P",
        )
        check(
            "dedup_partial_family: N2 (stale) INJECTED",
            "Lesson #22" in out,
            repr(out[:160]),
        )
        check(
            "dedup_partial_family: N1 (fresh) SUPPRESSED",
            "Lesson #21" not in out,
            repr(out[:160]),
        )

    # ------------------------------------------------------------------ #
    # dedup_concurrent: TWO concurrent invocations of the SAME matching
    # prompt against ONE shared --state-dir. No crash; state-file integrity
    # (every line well-formed N\tts\n); 0 <= line_count <= 2 (BOUNDED);
    # combined stdout <= 2 budget-capped blocks.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(55, "Concurrent G", "Concurrent data loss.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        # The selftest CREATES + ASSERTS its OWN fresh empty --state-dir.
        state_dir = Path(td) / "concurrent_state"
        state_dir.mkdir()
        check(
            "dedup_concurrent: state-dir is freshly empty before launch",
            not any(state_dir.iterdir()),
            str(list(state_dir.iterdir())),
        )
        # Launch TWO concurrent invocations via xargs -P 2. Each writes its
        # json.dumps text to a separate outfile so we can inspect combined.
        # Write each command to its OWN script file so xargs argument length
        # stays small (inline commands blow past the command-line length cap).
        out1 = state_dir / "out1.txt"
        out2 = state_dir / "out2.txt"
        core_path = Path(__file__).resolve()
        script1_path = state_dir / "run1.sh"
        script2_path = state_dir / "run2.sh"
        script1_path.write_text(
            f"python3 {core_path} --prompt 'the report dropped a row' "
            f"--session-id sess-C --state-dir {state_dir} > {out1}\n",
            encoding="utf-8",
        )
        script2_path.write_text(
            f"python3 {core_path} --prompt 'the report dropped a row' "
            f"--session-id sess-C --state-dir {state_dir} > {out2}\n",
            encoding="utf-8",
        )
        import subprocess
        # Isolate HOME so (a) the two subprocess core invocations (which
        # resolve HOME from the environment) and (b) the resolve_project_key
        # call below write keying lines into the tmp tree, NOT the real
        # ~/.ai-playbook/logs/hooks.log (r1-M13).
        with isolated_home(td_path):
            proc = subprocess.run(
                ["xargs", "-P", "2", "-I", "{}", "bash", "{}"],
                input=f"{script1_path}\n{script2_path}\n",
                text=True,
                capture_output=True,
            )
            check(
                "dedup_concurrent: no crash (xargs exit 0)",
                proc.returncode == 0,
                proc.stderr[:200],
            )
            # State file integrity: find the state file and parse every line.
            project = facts_paths.resolve_project_key(td_path)
            session = _derive_session_component("sess-C")
            sf = _state_file_path(state_dir, project, session)
        well_formed = 0
        line_count = 0
        crashed = False
        try:
            content = sf.read_text(encoding="utf-8")
        except OSError:
            content = ""
        for line in content.splitlines():
            if not line.strip():
                continue
            line_count += 1
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            try:
                int(parts[0])
                float(parts[1])
                well_formed += 1
            except ValueError:
                crashed = True
        check(
            "dedup_concurrent: every present line is well-formed N\\tts",
            not crashed and well_formed == line_count,
            f"well_formed={well_formed} line_count={line_count}",
        )
        check(
            "dedup_concurrent: 0 <= line_count <= 2 (BOUNDED)",
            0 <= line_count <= 2,
            f"line_count={line_count}",
        )
        # Combined stdout <= 2 budget-capped blocks.
        blocks = 0
        for o in (out1, out2):
            try:
                txt = o.read_text(encoding="utf-8")
            except OSError:
                txt = ""
            if txt.strip():
                blocks += 1
        check(
            "dedup_concurrent: combined stdout <= 2 budget-capped blocks",
            blocks <= 2,
            f"blocks={blocks}",
        )

    # ------------------------------------------------------------------ #
    # budget: N>=5 family-G lessons, each body in (budget/4, budget/2),
    # COMBINED exceed budget -> non-empty; total <= budget; >=2 distinct;
    # truncation indicator IFF sliced.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        budget = 1500
        # Each body length in (budget/4, budget/2): pick budget/3.
        body_unit = "x" * (budget // 3)
        lessons = [(100 + i, f"Budget lesson {i}", body_unit) for i in range(6)]
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus(lessons), encoding="utf-8"
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            budget=budget,
            no_dedup=True,
        )
        check("budget: (a) non-empty", out != "", repr(out[:60]))
        # (b) total lesson-body length == budget when sliced. This fixture
        # sets combined > budget (6 lessons each budget//3 body PLUS the
        # "Lesson #N (title): " prefix), so a correct enforcement MUST
        # truncate to EXACTLY budget bytes. The old `<= budget` assertion was
        # a tautology (slicing always satisfies `<=`); `== budget` proves the
        # cap actually binds (r2-L9).
        body_for_len = out
        sliced = out.endswith(TRUNCATION_INDICATOR)
        if sliced:
            body_for_len = body_for_len[: -len(TRUNCATION_INDICATOR)]
        check(
            "budget: (b) body length == budget (cap binds; sliced)",
            sliced and len(body_for_len) == budget,
            f"len={len(body_for_len)} budget={budget} sliced={sliced}",
        )
        # (c) >=2 distinct lesson numbers cited.
        import re as _re
        nums = set(int(m) for m in _re.findall(r"Lesson #(\d+)", out))
        check(
            "budget: (c) cites >=2 distinct lesson numbers",
            len(nums) >= 2,
            str(sorted(nums)),
        )
        # (d) truncation indicator present IFF sliced.
        check(
            "budget: (d) truncation indicator present (combined exceeds budget)",
            TRUNCATION_INDICATOR in out,
            repr(out[-80:]),
        )

    # ------------------------------------------------------------------ #
    # budget_rank_priority: TITLE-PHRASE-MATCHED lesson is the LONGEST body;
    # combined exceed budget by exactly one body -> title-matched IS PRESENT
    # (HEAD discriminator).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        budget = 1500
        # Three short lessons + one LONG lesson whose TITLE contains a prompt
        # phrase ("dropped"). The long one must survive HEAD truncation.
        short_body = "y" * (budget // 4)
        long_body = "z" * (budget - 100)  # nearly fills the budget alone
        # Short lessons (numbers 1,2,3) each ~budget/4 -> combined ~3*budget/4
        # plus the long one exceeds budget by exactly one (short) body.
        lessons_text = (
            f"## 1. Short one\n\n{short_body}\n\n**Principle:** Family G (fix)\n"
            f"## 2. Short two\n\n{short_body}\n\n**Principle:** Family G (fix)\n"
            f"## 3. Short three\n\n{short_body}\n\n**Principle:** Family G (fix)\n"
            f"## 4. Report dropped rows silently\n\n{long_body}\n\n"
            f"**Principle:** Family G (title-matched)\n"
        )
        (shared_dir / "development_lessons.md").write_text(lessons_text, encoding="utf-8")
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            budget=budget,
            no_dedup=True,
        )
        check(
            "budget_rank_priority: title-matched (longest) lesson IS PRESENT",
            "Lesson #4" in out,
            repr(out[:200]),
        )

    # ------------------------------------------------------------------ #
    # dedup_cold_start_file_absent: matching prompt, NO state file -> NON-EMPTY
    # then file EXISTS with one well-formed N\tts line.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(77, "Cold start G", "Cold-start data loss.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        state_dir.mkdir()
        # Compute the expected state file path under isolated HOME so the
        # resolver's no-anchor log line lands in the tmp tree (r1-M13).
        with isolated_home(td_path):
            project = facts_paths.resolve_project_key(td_path)
            session = _derive_session_component("sess-CS")
            sf = _state_file_path(state_dir, project, session)
            check(
                "dedup_cold_start_file_absent: state file ABSENT before call",
                not sf.exists(),
                str(sf),
            )
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            session_id="sess-CS",
        )
        check(
            "dedup_cold_start_file_absent: NON-EMPTY output",
            out != "" and "Lesson #77" in out,
            repr(out[:120]),
        )
        check(
            "dedup_cold_start_file_absent: state file EXISTS after call",
            sf.is_file(),
            str(sf),
        )
        if sf.is_file():
            lines = [ln for ln in sf.read_text(encoding="utf-8").splitlines() if ln.strip()]
            well = 0
            for ln in lines:
                parts = ln.split("\t")
                if len(parts) == 2:
                    try:
                        int(parts[0])
                        float(parts[1])
                        well += 1
                    except ValueError:
                        pass
            check(
                "dedup_cold_start_file_absent: one well-formed N\\tts line",
                len(lines) == 1 and well == 1,
                f"lines={lines}",
            )

    # ------------------------------------------------------------------ #
    # no_em_dash: no U+2014 in output across several prompts.
    # ------------------------------------------------------------------ #
    # NOTE: build the U+2014 codepoint via escape so this source file itself
    # contains no em dash (check-no-em-dash scans the file; a literal here
    # would fail the gate it is testing for).
    em_dash = chr(0x2014)  # U+2014 built via chr(); no literal em dash in source
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(1, "Em dash test", "No em dash here.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        for prompt in ("the report dropped a row", "fix the typo"):
            out = run_core(prompt, start_dir=td_path, state_dir=state_dir)
            check(
                f"no_em_dash: no U+2014 in output for {prompt!r}",
                em_dash not in out,
                repr(out[:80]),
            )
        # Also assert the module's own constants have no em dash.
        check(
            "no_em_dash: TRUNCATION_INDICATOR has no U+2014",
            em_dash not in TRUNCATION_INDICATOR,
            repr(TRUNCATION_INDICATOR),
        )

    # ------------------------------------------------------------------ #
    # adversarial_corpus: body with ", }, newlines, literal "additionalContext"
    # -> emitted json.dumps string round-trips with body intact.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        adversarial_body = (
            'Has a quote " and a brace } and newlines\n\nand a literal '
            '"additionalContext" key'
        )
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(88, "Adversarial", adversarial_body)]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        text = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            no_dedup=True,
        )
        # The CLI emits json.dumps(text); simulate the wrap and round-trip.
        wrapped = json.dumps(text)
        rt = json.loads(wrapped)
        check(
            "adversarial_corpus: json.dumps round-trips",
            rt == text,
            repr(rt[:80]),
        )
        check(
            "adversarial_corpus: body intact as one string (additionalContext present)",
            "additionalContext" in rt and "}" in rt,
            repr(rt[:120]),
        )

    # ------------------------------------------------------------------ #
    # corpus_readonly: corpus mode 0444 -> still reads/emits, never writes it.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        cpath = shared_dir / "development_lessons.md"
        cpath.write_text(
            _make_family_g_corpus([(99, "Readonly", "Readonly corpus data loss.")]),
            encoding="utf-8",
        )
        os.chmod(cpath, 0o444)
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n", encoding="utf-8"
        )
        state_dir = Path(td) / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            no_dedup=True,
        )
        check(
            "corpus_readonly: still reads/emits",
            "Lesson #99" in out,
            repr(out[:120]),
        )
        # Corpus unchanged (mode + content).
        check(
            "corpus_readonly: corpus content unchanged",
            cpath.read_text(encoding="utf-8").find("Readonly corpus data loss.") != -1,
            "",
        )
        # Restore mode for tmpdir cleanup.
        try:
            os.chmod(cpath, 0o600)
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    # cold_start_project_only: NO user corpus but a PROJECT corpus present
    # with a tagged lesson matching -> NON-EMPTY citing the project lesson.
    # Isolate HOME so the real home corpus does not participate.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # NO .ai-playbook/facts.md -> user_corpus_path returns None.
        # Place a project corpus at docs/maintenance/development_lessons.md.
        proj_corpus = td_path / "docs" / "maintenance"
        proj_corpus.mkdir(parents=True)
        (proj_corpus / "development_lessons.md").write_text(
            "## 5. Project G lesson\n\nProject-only data loss lesson.\n\n"
            "**Principle:** Family G (project fixture)\n",
            encoding="utf-8",
        )
        state_dir = Path(td) / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            no_dedup=True,
        )
        check(
            "cold_start_project_only: NON-EMPTY citing the project lesson",
            "Lesson #5" in out,
            repr(out[:120]),
        )

    # ------------------------------------------------------------------ #
    # cold_start_both_absent: NEITHER corpus present -> EMPTY stdout, exit 0.
    # run_core isolates HOME so the real home corpus is not consulted.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # No facts.md, no docs/maintenance/. Classify still matches (the
        # classifier is corpus-independent), but no lessons are found.
        (td_path / ".ai-playbook").mkdir()
        state_dir = Path(td) / "state"
        out = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            no_dedup=True,
        )
        log_path = td_path / ".ai-playbook" / "logs" / "hooks.log"
        recall_rows = []
        if log_path.is_file():
            for line in log_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if obj.get("event") == RECALL_LOG_EVENT:
                    recall_rows.append(obj)
        check(
            "cold_start_both_absent: EMPTY stdout (no corpus)",
            out == "",
            repr(out[:80]),
        )
        check(
            "cold_start_both_absent: recall log suppress-empty-corpus",
            len(recall_rows) == 1
            and recall_rows[0].get("outcome") == RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS
            and recall_rows[0].get("family") == "G",
            str(recall_rows),
        )

    # ------------------------------------------------------------------ #
    # project_single_source: resolve_project_key IS facts_paths.resolve_project_key
    # (IDENTITY, not equality).
    # ------------------------------------------------------------------ #
    check(
        "project_single_source: resolve_project_key is facts_paths.resolve_project_key",
        resolve_project_key is facts_paths.resolve_project_key,
        "IDENTITY failed",
    )

    # ------------------------------------------------------------------ #
    # project_filename_uses_resolver: fixture start_dir that is a SUBDIR of a
    # git repo -> resolved state filename's project component EQUALS the
    # resolver's output AND DIFFERS from sha1(realpath(start_dir))[:16].
    # ------------------------------------------------------------------ #
    # Use the REAL repo (this one) as the git repo and a subdir as the fixture.
    repo_root = Path(__file__).resolve().parent.parent
    fixture = repo_root / "scripts"
    if (fixture / ".git").exists() or True:
        # Confirm the fixture is inside a git repo and realpath differs.
        import subprocess as _sp
        try:
            res = _sp.run(
                ["git", "-C", str(fixture), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=5,
            )
            toplevel = res.stdout.strip()
        except (OSError, _sp.SubprocessError):
            toplevel = ""
        if res.returncode == 0 and toplevel and os.path.realpath(str(fixture)) != os.path.realpath(toplevel):
            project_component = facts_paths.resolve_project_key(fixture)
            local_hash = hashlib.sha1(os.path.realpath(str(fixture)).encode()).hexdigest()[:16]
            check(
                "project_filename_uses_resolver: project == resolver(fixture)",
                project_component == facts_paths.resolve_project_key(fixture),
                f"{project_component}",
            )
            check(
                "project_filename_uses_resolver: project DIFFERS from sha1(realpath(fixture))[:16]",
                project_component != local_hash,
                f"project={project_component} local={local_hash}",
            )
        else:
            # Not in a git subdir; skip with a visible note (do not silently
            # pass - print a SKIP line so the count is honest).
            print("SKIP: project_filename_uses_resolver (fixture not a git subdir in this env)")

    # ------------------------------------------------------------------ #
    # cursor_adapter_family_index_matches_core (r1-M11): cursor.sh is the only
    # adapter that builds a family INDEX (lowest-numbered lesson per present
    # family) instead of calling _consult. The index selection is a one-shot
    # the core has no equivalent mode for, so it stays inline in the adapter;
    # this arm pins that the adapter (a) imports PROJECT_CORPUS_REL from this
    # core (Family D single source for the path constant) and (b) its
    # family-selection agrees with iterating the SAME corpus via
    # lessons_corpus.iter_lessons. Drift in either would fail here.
    # ------------------------------------------------------------------ #
    cursor_adapter = (
        Path(__file__).resolve().parent.parent
        / "agents" / "hooks" / "lessons-recall" / "cursor.sh"
    )
    if cursor_adapter.is_file():
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            # Fixture corpus with two families; the per-family lowest number
            # must win.
            (td_path / "docs" / "maintenance").mkdir(parents=True)
            (td_path / "docs" / "maintenance" / "development_lessons.md").write_text(
                "## 9. Later G lesson\n\nLater body.\n\n"
                "**Principle:** Family G (later)\n"
                "## 3. First G lesson\n\nFirst body.\n\n"
                "**Principle:** Family G (first)\n"
                "## 7. A lesson\n\nA body.\n\n"
                "**Principle:** Family A (fix)\n",
                encoding="utf-8",
            )
            # cursor.sh resolves the core via ~/.ai-playbook/scripts/. Create
            # the symlinks in the isolated HOME so the adapter runs against the
            # repo scripts (the same model the real install uses).
            scripts_src = Path(__file__).resolve().parent
            scripts_link_dir = td_path / ".ai-playbook" / "scripts"
            scripts_link_dir.mkdir(parents=True)
            for name in ("lessons_recall.py", "session_channel.py",
                         "facts_paths.py", "lessons_classify.py",
                         "lessons_corpus.py"):
                target = scripts_src / name
                if target.is_file():
                    os.symlink(str(target), str(scripts_link_dir / name))
            # Run cursor.sh with cwd inside the fixture and HOME isolated so
            # the real home corpus does not participate.
            with isolated_home(td_path):
                import subprocess as _sp_c
                proc = _sp_c.run(
                    ["bash", str(cursor_adapter)],
                    input=b"{}",
                    capture_output=True,
                    cwd=str(td_path),
                )
            adapter_out = proc.stdout.decode("utf-8", errors="replace")
            # The adapter wraps the index in {"additionalContext": <idx>}; parse.
            adapter_idx = ""
            if adapter_out.strip():
                try:
                    adapter_idx = json.loads(adapter_out).get("additionalContext", "")
                except ValueError:
                    adapter_idx = ""
            # Expected from the core's own iteration: lowest-numbered per family.
            corpus_text = (td_path / "docs" / "maintenance" / "development_lessons.md").read_text(encoding="utf-8")
            expected: dict[str, tuple[int, str]] = {}
            for L in lessons_corpus.iter_lessons(corpus_text):
                for fam in L.tags:
                    if fam in lessons_corpus.VALID_FAMILIES:
                        if fam not in expected or L.number < expected[fam][0]:
                            expected[fam] = (L.number, L.title)
            expected_lines = sorted(
                f"Family {fam}: #{n} {title}" for fam, (n, title) in expected.items()
            )
            check(
                "cursor_adapter_family_index: adapter ran (exit 0)",
                proc.returncode == 0,
                f"rc={proc.returncode} stderr={proc.stderr.decode('utf-8', 'replace')[:200]}",
            )
            check(
                "cursor_adapter_family_index: matches core selection over same fixture",
                adapter_idx.strip().split("\n") == expected_lines,
                f"adapter={adapter_idx.strip()!r} expected={expected_lines!r}",
            )

    # ------------------------------------------------------------------ #
    # dedup_state_writer_refuses_symlink_leaf (r1-M2): _append_injection
    # opens with O_NOFOLLOW, so a pre-planted symlink at the state-file leaf
    # is REFUSED (ELOOP), not followed. Pins parity with the hardened marker
    # writer (atomic_write_text) and the _append_hooks_log_line helper.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state_dir = td_path / "state"
        state_dir.mkdir()
        # Plant a symlink at the state-file path pointing at an arbitrary file.
        victim = td_path / "victim.txt"
        victim.write_text("original-content", encoding="utf-8")
        state_path = state_dir / "deadbeefdeadbeef.no-session.state"
        os.symlink(str(victim), str(state_path))
        # _append_injection must REFUSE the symlink (O_NOFOLLOW -> ELOOP ->
        # except OSError: return). It must NOT append to the victim.
        _append_injection(state_path, 42, time.time())
        check(
            "dedup_state_writer_refuses_symlink_leaf: victim NOT modified",
            victim.read_text(encoding="utf-8") == "original-content",
            repr(victim.read_text(encoding="utf-8")),
        )
        check(
            "dedup_state_writer_refuses_symlink_leaf: symlink leaf still a symlink (not converted to a regular file by a follow-and-write)",
            os.path.islink(str(state_path)),
            "state_path symlink leaf must remain a symlink",
        )

    # ------------------------------------------------------------------ #
    # dedup_state_reader_refuses_symlink_leaf (r4-L2): _read_seen_set opens
    # with O_NOFOLLOW (mirroring the r1-M2 writer and the r2-M7 skill_gate
    # marker read), so a pre-planned symlink at the state-file leaf is REFUSED
    # (ELOOP -> except OSError: return set()), NOT followed. A revert to bare
    # O_RDONLY would FOLLOW the symlink and the victim's content would parse
    # (or be skipped as malformed), not return the cold-start set.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state_dir = td_path / "state"
        state_dir.mkdir()
        victim = td_path / "victim.txt"
        # Plant a victim whose content WOULD parse into the seen-set if the
        # read path followed the symlink: "99\t<float>\n".
        victim.write_text("99\t" + str(time.time()) + "\n", encoding="utf-8")
        state_path = state_dir / "deadbeefdeadbeef.no-session.state"
        os.symlink(str(victim), str(state_path))
        seen = _read_seen_set(state_path, time.time())
        check(
            "dedup_state_reader_refuses_symlink_leaf: returns empty set (symlink refused, cold-start)",
            seen == set(),
            repr(seen),
        )
        check(
            "dedup_state_reader_refuses_symlink_leaf: symlink leaf still a symlink",
            os.path.islink(str(state_path)),
            "state_path symlink leaf must remain a symlink",
        )

    # ------------------------------------------------------------------ #
    # dedup_state_reader_tolerates_invalid_utf8 (r1-M3): a state file with
    # invalid UTF-8 bytes (a half-written record / planted garbage) must NOT
    # raise UnicodeDecodeError and disable recall. errors="replace" degrades
    # the bytes to malformed line entries the existing parse loop skips, so
    # seen = set() (cold-start) rather than a swallowed crash.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state_dir = td_path / "state"
        state_dir.mkdir()
        state_path = state_dir / "deadbeefdeadbeef.no-session.state"
        # Write invalid UTF-8 (0xff is not a valid UTF-8 leading byte) plus a
        # trailing valid record. The reader must NOT raise and must STILL parse
        # the valid record.
        valid_ts = time.time() - 10  # well inside the window
        state_path.write_bytes(
            b"\xff\xfe garbage line\n" + f"7\t{valid_ts}\n".encode("utf-8")
        )
        raised = False
        seen: set[int] = set()
        try:
            seen = _read_seen_set(state_path, time.time())
        except BaseException as e:
            raised = True
            check(
                "dedup_state_reader_tolerates_invalid_utf8: no raise on invalid bytes",
                False,
                repr(e),
            )
        check(
            "dedup_state_reader_tolerates_invalid_utf8: no raise on invalid bytes",
            not raised,
            "UnicodeDecodeError must not escape _read_seen_set",
        )
        # The valid record (N=7) survives the replaced garbage line.
        check(
            "dedup_state_reader_tolerates_invalid_utf8: valid record survives (N=7 in seen)",
            7 in seen,
            f"seen={seen}",
        )

    # ------------------------------------------------------------------ #
    # main_fail_open_on_exception_but_propagate_kbi (r2-M5): a generic
    # Exception inside _consult fails OPEN (recall NEVER blocks; Family G), but
    # KeyboardInterrupt and SystemExit PROPAGATE out of main() (Ctrl-C during a
    # consultation must NOT be silently swallowed as keying=error). Mirrors
    # skill_gate.py r1-M1/M9. Pins the narrowed catch (was BaseException, which
    # swallowed KBI/SystemExit and returned 0).
    # ------------------------------------------------------------------ #
    this_mod = sys.modules[__name__]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        home_dir = td_path / "home"
        home_dir.mkdir()
        orig_consult = this_mod._consult

        def _raise_valueerror(*a, **k):
            raise ValueError("synthetic crash inside _consult")

        def _raise_kbi(*a, **k):
            raise KeyboardInterrupt

        def _raise_sysexit(*a, **k):
            raise SystemExit(7)

        # main() resolves start_dir = Path.cwd(); chdir into the tmp tree so
        # facts resolution has a stable cwd. The fail-open branch calls
        # _append_hooks_log_line, so isolate HOME (reroutes the log write).
        orig_cwd = os.getcwd()
        os.chdir(str(td_path))
        try:
            with isolated_home(home_dir):
                # Arm 1: a generic Exception -> main() returns 0 (fail-open,
                # recall NEVER blocks). Capture stdout to confirm it is empty
                # (the recall contract is silent on failure).
                this_mod._consult = _raise_valueerror
                captured_out = []
                orig_stdout = sys.stdout
                class _Capture:
                    def write(self, s):
                        captured_out.append(s)
                    def flush(self):
                        pass
                try:
                    sys.stdout = _Capture()
                    rc_valueerror = main(["--prompt", "anything"])
                finally:
                    sys.stdout = orig_stdout
                    this_mod._consult = orig_consult
                check(
                    "main_fail_open: generic Exception -> exit 0 (fail-open, recall NEVER blocks)",
                    rc_valueerror == 0,
                    f"rc={rc_valueerror}",
                )
                check(
                    "main_fail_open: generic Exception -> silent (empty stdout)",
                    "".join(captured_out) == "",
                    repr("".join(captured_out)[:80]),
                )

                # Arm 2: KeyboardInterrupt -> main() PROPAGATES (not swallowed).
                this_mod._consult = _raise_kbi
                kbi_propagated = False
                try:
                    main(["--prompt", "anything"])
                except KeyboardInterrupt:
                    kbi_propagated = True
                finally:
                    this_mod._consult = orig_consult
                check(
                    "main_fail_open: KeyboardInterrupt PROPAGATES (not swallowed as keying=error)",
                    kbi_propagated,
                    "expected KeyboardInterrupt to escape main()",
                )

                # Arm 3: SystemExit -> main() PROPAGATES.
                this_mod._consult = _raise_sysexit
                sysexit_propagated = False
                try:
                    main(["--prompt", "anything"])
                except SystemExit:
                    sysexit_propagated = True
                finally:
                    this_mod._consult = orig_consult
                check(
                    "main_fail_open: SystemExit PROPAGATES (not swallowed)",
                    sysexit_propagated,
                    "expected SystemExit to escape main()",
                )
        finally:
            os.chdir(orig_cwd)

    # ------------------------------------------------------------------ #
    # default_classifier_v1: CLI/core default stays v1; v1 behavior unchanged.
    # ------------------------------------------------------------------ #
    check(
        "default_classifier_v1: DEFAULT_CLASSIFIER is v1",
        DEFAULT_CLASSIFIER == "v1",
        DEFAULT_CLASSIFIER,
    )
    parser = _build_parser()
    ns_default = parser.parse_args([])
    check(
        "default_classifier_v1: argparse default --classifier v1",
        ns_default.classifier == "v1",
        ns_default.classifier,
    )
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(42, "Dropped rows must warn", "Silent drop.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n",
            encoding="utf-8",
        )
        state_dir = td_path / "state"
        out_v1 = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
        )
        check(
            "default_classifier_v1: flagship prompt still injects under default v1",
            out_v1 != "" and "Lesson #42" in out_v1,
            repr(out_v1[:80]),
        )
        out_v2_prompt = run_core(
            "the report dropped a row",
            start_dir=td_path,
            state_dir=state_dir,
            classifier="v2",
        )
        check(
            "default_classifier_v1: same prompt suppressed under explicit v2",
            out_v2_prompt == "",
            repr(out_v2_prompt[:80]),
        )

    # ------------------------------------------------------------------ #
    # recall_log_fire_and_suppress: pinned event=recall JSONL on every consult.
    # ------------------------------------------------------------------ #
    def _read_recall_log_lines(home_dir: Path) -> list[dict]:
        log_path = home_dir / ".ai-playbook" / "logs" / "hooks.log"
        if not log_path.is_file():
            return []
        rows: list[dict] = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if obj.get("event") == RECALL_LOG_EVENT:
                rows.append(obj)
        return rows

    def _valid_recall_log_row(obj: dict) -> bool:
        if obj.get("event") != RECALL_LOG_EVENT:
            return False
        if obj.get("outcome") not in RECALL_LOG_OUTCOMES:
            return False
        if not isinstance(obj.get("ts"), str) or not obj["ts"]:
            return False
        family = obj.get("family")
        if family is not None and not isinstance(family, str):
            return False
        if obj["outcome"] == RECALL_OUTCOME_SUPPRESS_CLASSIFY:
            return "family" not in obj
        return isinstance(family, str) and family in lessons_corpus.VALID_FAMILIES

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / ".ai-playbook").mkdir()
        shared_dir = td_path / "shared"
        shared_dir.mkdir()
        (shared_dir / "development_lessons.md").write_text(
            _make_family_g_corpus([(51, "Recall log G", "Recall log data loss.")]),
            encoding="utf-8",
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            f"| `shared_docs_dir` | `{shared_dir}` |\n",
            encoding="utf-8",
        )
        state_dir = td_path / "state"
        with isolated_home(td_path):
            first = _consult(
                "the report dropped a row",
                start_dir=td_path,
                state_dir=state_dir,
                session_id="recall-log",
                budget=DEFAULT_BUDGET,
                no_dedup=False,
                classifier=DEFAULT_CLASSIFIER,
            )
            second = _consult(
                "the report dropped a row",
                start_dir=td_path,
                state_dir=state_dir,
                session_id="recall-log",
                budget=DEFAULT_BUDGET,
                no_dedup=False,
                classifier=DEFAULT_CLASSIFIER,
            )
            _consult(
                "fix the typo",
                start_dir=td_path,
                state_dir=state_dir,
                session_id="recall-log",
                budget=DEFAULT_BUDGET,
                no_dedup=False,
                classifier=DEFAULT_CLASSIFIER,
            )
            recall_rows = _read_recall_log_lines(td_path)
        check(
            "recall_log_fire_and_suppress: first consult injects",
            first != "" and "Lesson #51" in first,
            repr(first[:80]),
        )
        check(
            "recall_log_fire_and_suppress: second consult deduped",
            second == "",
            repr(second[:80]),
        )
        check(
            "recall_log_fire_and_suppress: three recall JSONL lines",
            len(recall_rows) == 3,
            str(recall_rows),
        )
        check(
            "recall_log_fire_and_suppress: all lines match pinned schema",
            all(_valid_recall_log_row(row) for row in recall_rows),
            str(recall_rows),
        )
        outcomes = [row["outcome"] for row in recall_rows]
        check(
            "recall_log_fire_and_suppress: fire then suppress-dedup then suppress-classify",
            outcomes == [
                RECALL_OUTCOME_FIRE,
                RECALL_OUTCOME_SUPPRESS_DEDUP,
                RECALL_OUTCOME_SUPPRESS_CLASSIFY,
            ],
            str(outcomes),
        )
        check(
            "recall_log_fire_and_suppress: fire/dedup rows carry family G",
            recall_rows[0].get("family") == "G"
            and recall_rows[1].get("family") == "G",
            str(recall_rows[:2]),
        )

    # r1-M13 regression guard: no selftest block leaked a keying line into the
    # REAL ~/.ai-playbook/logs/hooks.log. run_core/seed_state_file isolate HOME
    # for every _consult/resolve_project_key call; a future bare call outside
    # isolation would trip this.
    if _m13_before >= 0:
        try:
            _m13_after = sum(
                1 for _ in _m13_real_log.read_text(encoding="utf-8").splitlines()
                if _.strip()
            ) if _m13_real_log.is_file() else 0
        except OSError:
            _m13_after = _m13_before
        check(
            "selftest_isolation: no leak into REAL ~/.ai-playbook/logs/hooks.log",
            _m13_after == _m13_before,
            f"before={_m13_before} after={_m13_after} (a block wrote to the real log outside isolated HOME)",
        )

    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
