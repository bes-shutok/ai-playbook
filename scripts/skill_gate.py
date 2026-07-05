#!/usr/bin/env python3
"""Skill-gate core: agent-agnostic PreToolUse gate on gated plan files.

On each consultation, the gate decides ALLOW or BLOCK for a target write path:
  - CLASSIFY the target path against the gated-class set (v1: plans-dir only).
  - If NOT gated -> ALLOW (silent).
  - If gated -> consult the per-(project, session) skill-gate marker at a
    HOME-ANCHORED path. ALLOW iff a fresh marker EXISTS; BLOCK otherwise.

The marker proves the ``plans`` skill ran RECENTLY in THIS project AND THIS
session. The marker lives at
``~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`` and
is written/refreshed by the plans skill (``--write-marker`` here exercises the
same atomic recipe).

Key invariants (see plan Terms + Design Invariants; this docstring states only
the LOCAL element pointers, NOT the full contract):

- Agent-agnostic: accepts ``--session-id`` as OPAQUE data; ZERO agent-channel
  knowledge (``session_channel.py`` is the adapter's concern, NEVER imported
  here). The core CANNOT emit ``keying=no-anchor`` (that is the resolver's job
  on its git-failure branch).
- ``project`` is derived by CALLING ``facts_paths.resolve_project_key`` (single
  shared function object with ``lessons_recall.py``; asserted IDENTITY in
  ``#project_single_source``). The core NEVER re-implements the derivation.
- ``session`` is SANITIZED: emptiness check first; empty-after-strip -> literal
  ``no-session``; otherwise ``sha1(value)[:16]`` hex (path-safe).
- ONE full ``SKILL_GATE_WINDOW`` (default 4h, FLAGGED) for ALL agents
  unconditionally. The halved-window steady state is COLLAPSED.
- LOUD keying: logs ``keying=env-var|project-only`` to
  ``~/.ai-playbook/logs/hooks.log`` via the shared ``_append_hooks_log_line``
  helper. ``keying`` is PURE LOG METADATA and drives NO core branch.
- Path classification is a ``realpath`` subtree check (never ``str.startswith``;
  never the lexical ``plans_dir`` string).
- Fail-CLOSED-by-default with a NARROW fail-open aperture: an ``OSError`` from
  the marker store fails open (r2-M1: widened from ``PermissionError``-only so
  EROFS/EIO/ELOOP/ENOSPC fail-open EXPLICITLY with the loud warning instead of
  falling through silently; r3-M1: the ``try`` now wraps the whole
  resolve/classify/consult chain so an ``OSError`` from any
  ``os.path.realpath`` / ``Path.resolve()`` in ``resolve_plans_dir`` /
  ``classify_path`` / ``resolve_project_key`` ALSO fails open LOUDLY instead of
  escaping to the generic arm; ``PermissionError`` is a subclass of
  ``OSError``),
  and a crash inside ``_consult`` that escapes its own narrow catches ALSO fails
  open (Family G: a gate that crashes the host agent in a way that disables the
  gate silently is worse than no gate). Both paths log ``keying=fail-open``/
  ``keying=error`` and emit a stderr warning. ``KeyboardInterrupt`` /
  ``SystemExit`` PROPAGATE (Ctrl-C during a consultation is NOT silently
  allowed); ``FileNotFoundError`` is NOT fail-open at the ``check_marker`` layer
  (makedirs-before-stat + absent-marker branch handle it).
- Marker write is ATOMIC via ``lessons_corpus.atomic_write_text``
  (``O_EXCL|O_NOFOLLOW`` + ``os.replace``); ``--write-marker`` CATCHES
  ``FileExistsError`` at the CALL SITE and treats it as benign (loser exits 0
  without writing).

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
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

# Sibling-import bootstrap (r14-M2): MUST be the FIRST line after stdlib
# imports. The core is symlinked into ~/.ai-playbook/scripts/ and imports
# sibling leaves (facts_paths / lessons_corpus) from the repo scripts dir;
# Path(__file__).resolve().parent follows the symlink to the repo dir where
# the siblings exist. Mirrors lessons_adopt.py:38-41.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths  # noqa: E402
import lessons_corpus  # noqa: E402
import lessons_recall  # noqa: E402
from lessons_recall import PROJECT_CORPUS_REL  # noqa: E402

#: Default gate window. FLAGGED threshold (confirm at implementation; see plan
#: Monitor). ALL agents use the FULL window unconditionally (r10-M10 collapsed
#: the halved-window steady state). Too short and a long planning session
#: re-trips the gate; too long and the marker admits writes well after the
#: skill context is gone.
SKILL_GATE_WINDOW = 14400  # seconds (4h)

#: Literal session component for the empty-after-strip / absent case. NOT
#: ``sha1("").hexdigest()[:16]`` (which would be the constant ``da39a3ee5e6b4b0d``
#: and a silent collision - r10-M4).
NO_SESSION_KEY = "no-session"

#: The default plans_dir suffix when no repo facts file resolves it (FLAGGED
#: hardcoded convention). Works in worktrees because they contain
#: ``docs/plans/`` without resolving a worktree-absent facts file.
DEFAULT_PLANS_DIR_SUFFIX = Path("docs") / "plans"

#: Marker filename prefix (the full name is
#: ``plans.<project>.<session>.marker``).
MARKER_PREFIX = "plans"
MARKER_SUFFIX = "marker"

#: Home-anchored runtime dir (created 0o700 on first write and on each gate
#: consultation). Present in worktrees/subdirs, never depends on a
#: cwd-relative tmp_dir (r5-B1).
DEFAULT_RUNTIME_DIR = Path.home() / ".ai-playbook" / "runtime" / "skill-invoked"

#: The plans-class block message EXACT text (emitted as ``deny_reason``).
BLOCK_MESSAGE = "Invoke the plans skill before authoring a plan file."

#: The learn-class block message EXACT text (emitted as ``deny_reason``).
LEARN_BLOCK_MESSAGE = (
    "Invoke the learn skill before editing the project lessons corpus."
)

#: Gated-class registry: ``class_name -> (path_matcher, marker_prefix, deny_message)``.
#: Matchers receive ``(target, plans_dir)``; ``plans_dir`` is the cwd-resolved
#: value from ``facts_paths.resolve_plans_dir`` (``None`` when absent).
GatedClassEntry = tuple[
    Callable[[str | Path, str | Path | None], bool],
    str,
    str,
]


# --------------------------------------------------------------------------- #
# Re-export for IDENTITY selftest (#project_single_source). The core MUST
# expose the SAME function object as facts_paths.resolve_project_key; a copied
# body would drift and desync the marker key from the dedup state key (Family D).
# --------------------------------------------------------------------------- #
resolve_project_key = facts_paths.resolve_project_key


# --------------------------------------------------------------------------- #
# Session component derivation (per Terms "Session key").
# --------------------------------------------------------------------------- #
def _derive_session_component(raw_session_id: str | None) -> str:
    """Derive the SANITIZED ``session`` filename component.

    The emptiness check (``.strip() == ""``) is the FIRST operation, before
    any hashing (r11-M3). An empty-after-strip ``--session-id`` is treated
    IDENTICALLY to absent -> literal ``no-session`` (NOT ``sha1("")[:16]`` =
    ``da39a3ee5e6b4b0d``, a constant collision - r10-M4). Otherwise the value
    is hashed to hex (path-safe; a hostile env var like ``../foo`` cannot
    traverse the runtime dir or alias another session's marker).
    """
    if raw_session_id is None or raw_session_id.strip() == "":
        return NO_SESSION_KEY
    return hashlib.sha1(raw_session_id.encode()).hexdigest()[:16]


def _marker_path(
    runtime_dir: Path,
    project: str,
    session: str,
    *,
    marker_prefix: str = MARKER_PREFIX,
) -> Path:
    """Return the per-(project, session) marker path.

    The filename encodes both isolation keys (project + session); the body is
    forensic-only and never a checked guard (r7-M4).
    """
    return runtime_dir / f"{marker_prefix}.{project}.{session}.{MARKER_SUFFIX}"


def _ends_with_rel_suffix(target_real: Path, suffix: Path) -> bool:
    """True iff ``target_real``'s path ends with ``suffix`` parts (structural)."""
    suffix_parts = suffix.parts
    target_parts = target_real.parts
    if len(target_parts) < len(suffix_parts):
        return False
    return target_parts[-len(suffix_parts):] == suffix_parts


def _plans_path_matcher(target: str | Path, plans_dir: str | Path | None) -> bool:
    """Classify ``target`` as a gated plan-file path via a realpath subtree test.

    ``plans_dir`` is resolved from repo ``.ai-playbook/facts.md`` by the caller
    (``facts_paths.resolve_plans_dir``); pass ``None`` to use the default
    ``docs/plans/`` suffix. Classification resolves BOTH the target and
    ``plans_dir`` through ``os.path.realpath`` and uses ``Path.relative_to``/
    ``os.path.commonpath`` - never ``str.startswith``, never the lexical
    ``plans_dir`` string (M4: ``..``/symlink/absolute-path evasion bypasses a
    naive prefix check).

    Cross-tree absolute target (r10-L5): when the gate cwd is a worktree, an
    absolute Write target into the MAIN repo is NOT classified by the
    cwd-resolved ``plans_dir``. This function ALSO checks the target against
    the default ``docs/plans/`` suffix on the target's OWN realpath, so a
    cross-tree plan write is still gated.
    """
    target_real = Path(os.path.realpath(str(target)))

    # Arm 1: the cwd-resolved plans_dir (if any).
    if plans_dir is not None:
        plans_real = Path(os.path.realpath(str(plans_dir)))
        if _is_subpath(target_real, plans_real):
            return True

    # Arm 2 (r10-L5): the default ``docs/plans/`` suffix on the target's OWN
    # realpath, independent of the cwd-resolved plans_dir.
    if _under_default_plans_suffix(target_real):
        return True

    return False


def _learn_path_matcher(target: str | Path, plans_dir: str | Path | None) -> bool:
    """True iff ``target`` realpath ends with ``PROJECT_CORPUS_REL`` (Arm 2 discipline).

    ``plans_dir`` is unused; kept for a uniform matcher signature.
    """
    del plans_dir  # unused; uniform registry signature
    target_real = Path(os.path.realpath(str(target)))
    return _ends_with_rel_suffix(target_real, PROJECT_CORPUS_REL)


GATED_CLASS_REGISTRY: dict[str, GatedClassEntry] = {
    "plans": (_plans_path_matcher, MARKER_PREFIX, BLOCK_MESSAGE),
    "learn": (_learn_path_matcher, "learn", LEARN_BLOCK_MESSAGE),
}


def resolve_gated_class(
    target: str | Path,
    plans_dir: str | Path | None,
) -> tuple[str, str, str] | None:
    """Return ``(class_name, marker_prefix, deny_message)`` or ``None`` if ungated."""
    for class_name, (matcher, prefix, deny_msg) in GATED_CLASS_REGISTRY.items():
        if matcher(target, plans_dir):
            return (class_name, prefix, deny_msg)
    return None


# --------------------------------------------------------------------------- #
# Public surface (the doctor asserts both symbols).
# --------------------------------------------------------------------------- #
def classify_path(target: str | Path, plans_dir: str | Path | None) -> bool:
    """Public plans-class matcher (doctor asserts this symbol).

    Delegates to ``_plans_path_matcher``; registry adds other classes via
    ``resolve_gated_class`` without changing this function's behavior.
    """
    return _plans_path_matcher(target, plans_dir)


def _is_subpath(child: Path, parent: Path) -> bool:
    """True iff ``child`` is ``parent`` or under it (realpath subtree test).

    Uses ``os.path.commonpath`` so a lexical-prefix coincidence (e.g.
    ``/a/plans-extra`` vs ``/a/plans``) does not false-classify. Both operands
    must be realpath'd by the caller.
    """
    try:
        common = os.path.commonpath([str(child), str(parent)])
    except ValueError:
        # Different drives on Windows; treat as not-subpath.
        return False
    if common != str(parent):
        return False
    # commonpath can return str(parent) even when child == parent; that is a
    # gated path (editing a plan file whose path is exactly plans_dir is not
    # possible since plans_dir is a dir, but the equality case is harmless).
    return True


def _under_default_plans_suffix(target_real: Path) -> bool:
    """True iff ``target_real`` is under a ``docs/plans`` directory.

    Walks the realpath ancestors of ``target_real``; if any ancestor is named
    ``plans`` AND its own parent is named ``docs``, the target is a plan file
    under the default convention. This is independent of the cwd-resolved
    ``plans_dir`` (closes the cross-tree-worktree hole, r10-L5).

    BREADTH (r1-L10): the classification is GLOBAL - ANY ``docs/plans`` path on
    the filesystem is gated, not just ones under the current repo's toplevel.
    A user editing ``~/notes/docs/plans/random.md`` (unrelated to any plan
    skill invocation) is blocked unless they recently invoked the plans skill
    for that project hash. This breadth is the documented design (the
    cross-tree-worktree hole requires the global fallback); restricting Arm 2
    to the git toplevel would re-open the hole for worktree writes.
    """
    # Build the realpath of the conventional docs/plans anchor by walking up.
    # Compare each (parent.name == "docs", dir.name == "plans") pair along the
    # target's own realpath ancestors.
    cur = target_real
    # Iterate parent chain. cur.parent eventually == cur at the root.
    while True:
        parent = cur.parent
        if parent == cur:
            # Reached filesystem root.
            return False
        if cur.name == "plans" and parent.name == "docs":
            return True
        cur = parent


def check_marker(
    project: str,
    session: str,
    *,
    marker_prefix: str = MARKER_PREFIX,
    now: float | None = None,
    runtime_dir: Path | None = None,
) -> bool:
    """Return True iff a fresh skill-gate marker EXISTS for (project, session).

    Looks up ``~/.ai-playbook/runtime/skill-invoked/<prefix>.<project>.<session>.marker``.
    FIRST ``os.makedirs(dir, exist_ok=True, 0o700)`` BEFORE ``os.lstat``, so a
    missing dir on a fresh install cannot raise ``FileNotFoundError`` (an
    OSError) and fail-OPEN the gate (r8-M4). Accept iff the file EXISTS, is a
    REGULAR file (not a symlink; r2-M7 read-path hardening mirroring the
    O_NOFOLLOW write path), AND
    ``0 <= (now - mtime) <= SKILL_GATE_WINDOW`` (a future-dated/negative delta
    or ``mtime == 0`` is STALE -> block, NOT a perpetual allow - M4).

    The marker BODY is forensic/debug metadata ONLY (r7-M4); this function
    never reads it.

    Raises ``OSError`` (NOT swallowed here) when the marker store is
    truly unwritable/unreadable (``PermissionError`` is a subclass of
    ``OSError``); the consult core fail-opens on any such ``OSError`` (r2-M1).
    ``FileNotFoundError`` is handled by the makedirs + absent-marker branch.
    """
    rdir = runtime_dir if runtime_dir is not None else DEFAULT_RUNTIME_DIR
    marker = _marker_path(rdir, project, session, marker_prefix=marker_prefix)
    # makedirs BEFORE stat (r8-M4): a missing dir cannot FileNotFoundError
    # fail-OPEN the gate; the absent-marker branch is always reachable.
    os.makedirs(str(rdir), exist_ok=True, mode=0o700)
    # r2-M7: READ path hardening. The WRITE path uses O_EXCL|O_NOFOLLOW
    # (lessons_corpus.atomic_write_text); the READ path must REFUSE a planted
    # symlink at the marker leaf too. os.lstat does NOT follow the symlink; if
    # the leaf is a symlink, treat it as ABSENT (return False -> BLOCK), which
    # matches the writer's O_NOFOLLOW refusal. A real marker is always a
    # regular file (the writer never creates a symlink).
    try:
        st = os.lstat(str(marker))
    except FileNotFoundError:
        return False
    import stat as _statmod
    if _statmod.S_ISLNK(st.st_mode):
        # Planted symlink leaf: refuse (do NOT follow). BLOCK, NOT fail-open.
        return False
    # Any OSError on stat (PermissionError, EROFS, EIO, ELOOP, ...) propagates
    # to the caller's fail-open policy (r2-M1).
    mtime = st.st_mtime
    ts = time.time() if now is None else now
    delta = ts - mtime
    # 0 <= delta AND delta <= window. A future-dated marker (delta < 0) or
    # mtime == 0 (epoch; delta huge but check explicitly for clarity) is STALE.
    if mtime == 0:
        return False
    return 0 <= delta <= SKILL_GATE_WINDOW


# --------------------------------------------------------------------------- #
# Consultation core.
# --------------------------------------------------------------------------- #
def _consult(
    target: str,
    *,
    start_dir: Path,
    session_id: str | None,
    runtime_dir: Path | None = None,
    now: float | None = None,
) -> tuple[bool, str]:
    """Run one consultation. Returns ``(allow, deny_reason)``.

    On ALLOW the ``deny_reason`` is ``""``. On BLOCK it is the message the
    adapter emits (data-influenced; the caller wraps it via ``json.dumps``).

    Steps:
    1. LOUD keying: append one hooks.log line (env-var vs project-only).
    2. Classify the target path against the gated-class set.
    3. If NOT gated -> ALLOW.
    4. If gated -> consult the marker. ALLOW iff fresh; BLOCK otherwise.

    Fail-open policy (this function's own catch): an ``OSError`` from the
    marker store (``PermissionError`` is a subclass; r2-M1 widened this from
    ``PermissionError``-only so EROFS/EIO/ELOOP/ENOSPC fail-open EXPLICITLY
    with the loud warning instead of falling through to ``main``'s generic
    ``except Exception``; r3-M1 widened the ``try`` to cover the whole
    resolve/classify/consult chain so an ``OSError`` from
    ``resolve_plans_dir`` / ``classify_path`` / ``resolve_project_key``
    realpath calls - ELOOP on a symlink loop, ENAMETOOLONG, EIO - ALSO
    fail-opens LOUDLY, pinning the whole Family-A partition instead of the
    single ``check_marker`` cell) -> ALLOW + stderr warning + hooks.log line
    whose path label is HARDCODED (exception fields passed as a json.dumps
    field, never f-interpolated raw - L9/r8-L6). ``FileNotFoundError`` is NOT
    fail-open (makedirs + absent-marker branch handle it). ``main`` ADDS a
    broader ``except Exception`` fail-open arm for any OTHER unexpected
    exception escaping this catch (see module docstring).
    """
    # Step 1: LOUD keying (PURE LOG METADATA, drives NO core branch; r11-M2).
    keying = (
        "env-var"
        if (session_id is not None and session_id.strip() != "")
        else "project-only"
    )
    facts_paths._append_hooks_log_line({
        "ts": datetime.now(timezone.utc).isoformat(),
        "keying": keying,
    })

    # Step 2-4: resolve/classify/consult. The whole chain is wrapped in ONE
    # try/except OSError so a marker-store OS error (EROFS/EIO/ELOOP/ENOSPC,
    # or an ELOOP/ENAMETOOLONG/EIO from any ``os.path.realpath`` /
    # ``Path.resolve()`` in resolve_plans_dir / classify_path /
    # resolve_project_key) fail-opens LOUDLY with the warning below instead of
    # escaping to main's generic ``except Exception`` and fail-opening
    # SILENTLY (r3-M1: r2-M1 widened the catch from PermissionError to OSError
    # but only around check_marker; the sibling resolve/classify cells of the
    # same partition were Family-A stragglers).
    try:
        # Step 2: classify via registry. plans_dir is resolved from repo facts
        # when present, else None (_plans_path_matcher falls back to default suffix).
        plans_dir = facts_paths.resolve_plans_dir(start_dir)
        gated = resolve_gated_class(target, plans_dir)

        # Step 3: non-gated -> ALLOW (silent).
        if gated is None:
            return (True, "")

        _class_name, marker_prefix, deny_message = gated

        # Step 4: gated -> consult the per-class marker.
        project = resolve_project_key(start_dir)
        session = _derive_session_component(session_id)
        fresh = check_marker(
            project,
            session,
            marker_prefix=marker_prefix,
            now=now,
            runtime_dir=runtime_dir,
        )
    except OSError as e:
        # Fail-open on ANY marker-store OSError (r2-M1: was PermissionError
        # only, which let EROFS/EIO/ELOOP/ENOSPC escape to main's generic
        # ``except Exception`` and fail-open SILENTLY). ``PermissionError`` is a
        # subclass of ``OSError`` so the existing policy is preserved; the
        # wider catch makes the fail-open aperture EXPLICIT and logged instead
        # of an accidental fall-through. ``FileNotFoundError`` is NOT fail-open
        # (check_marker handles it via the absent-marker branch). r3-M1 widened
        # the try to ALSO cover resolve_plans_dir / classify_path /
        # resolve_project_key, whose ``os.path.realpath`` / ``Path.resolve()``
        # calls can raise OSError (ELOOP on a symlink loop, ENAMETOOLONG, EIO)
        # from the repo's facts-file path values.
        # Path label HARDCODED; exception fields passed as a json.dumps field,
        # never f-interpolated raw (L9/r8-L6). ``filename``/``strerror`` may be
        # None on some OSError subclasses (e.g. a bare OSError()); pass through
        # as-is (the logger tolerates None).
        sys.stderr.write(
            "skill-gate: marker store unreadable; failing open (allow).\n"
        )
        facts_paths._append_hooks_log_line({
            "ts": datetime.now(timezone.utc).isoformat(),
            "keying": "fail-open",
            "path": "~/.ai-playbook/runtime/skill-invoked/",
            "error_filename": e.filename,
            "error_strerror": e.strerror,
        })
        return (True, "")

    if fresh:
        return (True, "")
    return (False, deny_message)


def _write_marker(
    *,
    start_dir: Path,
    session_id: str | None,
    marker_prefix: str = MARKER_PREFIX,
    runtime_dir: Path | None = None,
    now: float | None = None,
) -> int:
    """Write/refresh the skill-gate marker ATOMICALLY.

    Recipe (per Terms, the single-source marker WRITE RECIPE):
    1. ``os.makedirs(~/.ai-playbook/runtime/skill-invoked/, exist_ok=True,
       mode=0o700)``.
    2. ``lessons_corpus.atomic_write_text(marker, body)`` at mode 0o600
       (``O_EXCL|O_NOFOLLOW`` + ``os.replace``).
    3. CATCH ``FileExistsError`` at THIS call site and treat as BENIGN: the
       loser returns exit 0 WITHOUT writing (no retry, no ``os.replace``, no
       deletion of a pre-existing ``.tmp`` out from under its holder).

    The marker BODY stores the writer's ``realpath(cwd)`` AND the resolved
    repo-anchor path as FORENSIC/debug metadata ONLY (r7-M4; it is NOT a
    checked guard). The marker filename encodes both isolation keys.
    """
    rdir = runtime_dir if runtime_dir is not None else DEFAULT_RUNTIME_DIR
    os.makedirs(str(rdir), exist_ok=True, mode=0o700)

    project = resolve_project_key(start_dir)
    session = _derive_session_component(session_id)
    marker = _marker_path(rdir, project, session, marker_prefix=marker_prefix)
    ts = time.time() if now is None else now

    # Body is forensic-only (r7-M4): writer cwd + resolved anchor path.
    cwd_real = os.path.realpath(str(start_dir))
    body = json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "writer_cwd": cwd_real,
        "project": project,
        "session": session,
    })

    try:
        lessons_corpus.atomic_write_text(str(marker), body)
    except FileExistsError:
        # r10-L1/r12-M6/r13-M4: ``atomic_write_text`` opens the ``.tmp`` with
        # ``O_EXCL`` -> raises ``FileExistsError`` BEFORE its internal cleanup
        # runs. The catch is at THIS call site (NOT inside
        # ``atomic_write_text``). The loser returns exit 0 WITHOUT writing: no
        # retry, no ``os.replace``, no deletion of a pre-existing ``.tmp`` out
        # from under its holder.
        return 0

    # Touch the marker's mtime to ``ts`` so a stale-marker selftest can set a
    # deterministic mtime. The atomic write just happened, so the file exists,
    # but a concurrent deletion of the runtime dir (a cleanup tool, a manual
    # ``rm``) between ``os.replace`` and ``os.utime`` would raise
    # ``FileNotFoundError``. That TOCTOU window is microseconds, but the
    # ``--write-marker`` path has NO top-level guard (the ``except Exception``
    # in ``main()`` wraps only the ``_consult`` branch), so an unwrapped
    # ``os.utime`` would crash the hook process with a traceback and leave the
    # marker missing -> the gate BLOCKS the next gated write. The mtime
    # normalization is cosmetic (the ``check_marker`` window is 4h, so the
    # wall-clock-at-replace mtime is always inside it); swallow the rare
    # concurrent deletion and return 0 (the marker was written; mtime just
    # could not be set). r1-M4.
    try:
        os.utime(str(marker), (ts, ts))
    except FileNotFoundError:
        pass
    return 0


# --------------------------------------------------------------------------- #
# Doctor (5 checks). Parameterizable for selftests via ``doctor_kwargs``.
# --------------------------------------------------------------------------- #
#: The 11 doctor paths (helper + 2 cores + 8 adapters) as ``~``-relative
#: strings. The doctor expands ``~`` against the current HOME at call time.
#: r13-L9 literalizes the lessons-recall paths; r13-M6 pins the predicate.
#: OUT OF SCOPE: the leaves (facts_paths.py, lessons_classify.py) are reached
#: at runtime via the cores' Path(__file__).resolve().parent resolve, NOT via
#: ~/.ai-playbook/scripts/, so they are NOT enumerated here. They ARE symlinked
#: for direct invocation (see agents/hooks/{lessons-recall,skill-gate}/README.md
#: install blocks); a missing leaf surfaces via the plan's Validation block, not
#: doctor (whose scope is strictly the adapter install surface).
_DOCTOR_PATHS = [
    "~/.ai-playbook/scripts/session_channel.py",
    "~/.ai-playbook/scripts/lessons_recall.py",
    "~/.ai-playbook/scripts/skill_gate.py",
    "~/.claude/hooks/lessons-recall.sh",
    "~/.codex/hooks/lessons-recall.sh",
    "~/.cursor/hooks/lessons-recall.sh",
    "~/.gemini/antigravity-cli/hooks/lessons-recall.sh",
    "~/.claude/hooks/skill-gate.sh",
    "~/.codex/hooks/skill-gate.sh",
    "~/.cursor/hooks/skill-gate.sh",
    "~/.gemini/antigravity-cli/hooks/skill-gate.sh",
]

#: Parent dirs of the 11 paths that must also exist.
_DOCTOR_PARENT_DIRS = [
    "~/.ai-playbook/scripts/",
    "~/.codex/hooks/",
    "~/.gemini/antigravity-cli/hooks/",
    "~/.claude/hooks/",
    "~/.cursor/hooks/",
]


def _doctor() -> tuple[bool, list[str]]:
    """Run the FIVE doctor checks against the REAL install. Returns ``(ok, failures)``.

    Reads the REAL install paths (``~/.claude/settings.json``,
    ``~/.gemini/antigravity-cli/hooks.json``, the repo ``agents/hooks/`` dirs).
    The per-check functions (``_doctor_check_pretooluse_array`` etc.) are
    parameterizable and are what the selftests call directly with SYNTHETIC
    paths; this orchestrator always reads the real install (r1-L7: the five
    kwargs were never passed a non-None value by any caller, so they were dead
    surface; the honest model is per-check parameterization for tests, real
    paths here).

    Checks:
    (1) PreToolUse array: iterate ``settings.json['hooks']['PreToolUse']``;
        find an entry whose matcher ``|``-split alternation is a SUPERSET of
        ``{Write,Edit,MultiEdit}``; FAIL iff none. ALSO assert a SEPARATE
        ``"Bash"`` entry is preserved.
    (2) 11 paths live + parent dirs exist: for EACH of the 11 paths FAIL LOUD
        iff ``test -e`` is false OR (``[ -L ] && [ ! -e ]`` dangling);
        ``readlink -f`` is informational only. ALSO each parent dir exists.
    (3) Subprocess idiom: grep each adapter (``agents/hooks/skill-gate/*.sh``
        AND ``agents/hooks/lessons-recall/*.sh``) AND the plans-skill marker
        recipe for the literal
        ``python3 ~/.ai-playbook/scripts/session_channel.py``; FAIL if any
        adapter reads ``CLAUDE_CODE_SESSION_ID`` directly or omits the helper.
    (4) Core-symbol + writable runtime: verify the installed core IMPORTS and
        resolves ``classify_path``/``check_marker``; CREATE
        ``~/.ai-playbook/runtime/skill-invoked/`` if absent; confirm that dir
        is WRITABLE BY THE SKILL's uid.
    (5) agy hook timeout: read ``~/.gemini/antigravity-cli/hooks.json`` and
        FAIL iff NO ``PreToolUse`` entry carrying the skill-gate matcher has
        ``timeout > RESOLVER_GIT_TIMEOUT_S``.
    """
    failures: list[str] = []

    # --------------------------------------------------------------- #
    # Check (1): PreToolUse array.
    # --------------------------------------------------------------- #
    sp = Path.home() / ".claude" / "settings.json"
    pretooluse_ok, pretooluse_fail = _doctor_check_pretooluse_array(sp)
    if not pretooluse_ok:
        failures.extend(pretooluse_fail)

    # --------------------------------------------------------------- #
    # Check (2): 11 paths live + parent dirs exist.
    # --------------------------------------------------------------- #
    paths_ok, paths_fail = _doctor_check_paths()
    if not paths_ok:
        failures.extend(paths_fail)

    # --------------------------------------------------------------- #
    # Check (3): Subprocess idiom in adapters + plans-skill marker recipe.
    # --------------------------------------------------------------- #
    idiom_ok, idiom_fail = _doctor_check_subprocess_idiom(None, None)
    if not idiom_ok:
        failures.extend(idiom_fail)

    # --------------------------------------------------------------- #
    # Check (4): Core-symbol + writable runtime.
    # --------------------------------------------------------------- #
    core_ok, core_fail = _doctor_check_core_and_runtime(None)
    if not core_ok:
        failures.extend(core_fail)

    # --------------------------------------------------------------- #
    # Check (5): agy hook timeout.
    # --------------------------------------------------------------- #
    hjp = Path.home() / ".gemini" / "antigravity-cli" / "hooks.json"
    agy_ok, agy_fail = _doctor_check_agy_timeout(hjp)
    if not agy_ok:
        failures.extend(agy_fail)

    return (len(failures) == 0, failures)


def _doctor_check_pretooluse_array(settings_path: Path) -> tuple[bool, list[str]]:
    """Check (1): PreToolUse array has a Write|Edit|MultiEdit SUPERSET matcher
    AND a SEPARATE Bash entry is preserved.
    """
    failures: list[str] = []
    try:
        text = settings_path.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError) as e:
        return (False, [f"check(1) PreToolUse: cannot read {settings_path}: {e!r}"])
    try:
        doc = json.loads(text)
    except ValueError as e:
        return (False, [f"check(1) PreToolUse: invalid JSON in {settings_path}: {e!r}"])

    array = doc.get("hooks", {}).get("PreToolUse", [])
    if not isinstance(array, list) or not array:
        return (False, ["check(1) PreToolUse: array absent or empty"])

    required = {"Write", "Edit", "MultiEdit"}
    found_file_matcher = False
    found_bash = False
    for entry in array:
        if not isinstance(entry, dict):
            continue
        matcher = entry.get("matcher", "")
        if not isinstance(matcher, str):
            continue
        alts = {a.strip() for a in matcher.split("|") if a.strip()}
        if alts >= required:
            found_file_matcher = True
        if "Bash" in alts:
            found_bash = True

    if not found_file_matcher:
        failures.append(
            "check(1) PreToolUse: no entry whose matcher |-split alternation is "
            "a SUPERSET of {Write,Edit,MultiEdit}"
        )
    if not found_bash:
        failures.append(
            'check(1) PreToolUse: separate "Bash" entry missing '
            "(check-plan-review-gate.sh regression)"
        )
    return (len(failures) == 0, failures)


def _doctor_check_paths() -> tuple[bool, list[str]]:
    """Check (2): 11 paths live + parent dirs exist.

    Predicate (r13-M6): for each path FAIL LOUD iff ``test -e <path>`` is false
    OR (``[ -L <path> ] && [ ! -e <path> ]`` dangling symlink). ``readlink -f``
    is informational only (it returns a non-empty canonicalized target even for
    a dangling link and would false-pass).
    """
    failures: list[str] = []
    home = Path.home()
    for raw in _DOCTOR_PATHS:
        p = Path(raw).expanduser()
        exists = p.exists()  # test -e (follows symlinks; False on dangling)
        is_link = p.is_symlink()  # [ -L ]
        dangling = is_link and not exists
        if not exists:
            canonical = ""
            if is_link:
                try:
                    canonical = str(os.path.realpath(str(p)))
                except OSError:
                    canonical = "?"
            failures.append(
                f"check(2) path live: {raw} MISSING or DANGLING "
                f"(canonical target via readlink -f: {canonical})"
            )
    for raw in _DOCTOR_PARENT_DIRS:
        d = Path(raw).expanduser()
        if not d.is_dir():
            failures.append(f"check(2) parent dir: {raw} does not exist")
    return (len(failures) == 0, failures)


def _doctor_check_subprocess_idiom(
    adapter_dirs: list[Path] | None,
    plans_skill_recipe_path: Path | None,
) -> tuple[bool, list[str]]:
    """Check (3): adapters and the plans-skill marker recipe invoke the helper
    via the literal subprocess idiom; no adapter reads
    ``CLAUDE_CODE_SESSION_ID`` directly.

    "Reads directly" means an actual shell expansion of the env var: a ``$``
    immediately before the token, with an optional ``{`` (e.g.
    ``$CLAUDE_CODE_SESSION_ID`` or ``${CLAUDE_CODE_SESSION_ID}``). The bare token
    inside comments, inside a printf/echo message string, or inside the helper's
    own filename does NOT count: the mandated Claude adapter MUST emit a stderr
    warning ``CLAUDE_CODE_SESSION_ID absent; ...`` (plan r12-M4) whose text
    carries the bare token with no ``$`` prefix, and the adapter derives the
    session via the helper ``SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"``
    without ever naming the env var. A predicate that matched the bare token
    false-failed the correct install (Family H: verified the abstraction, not
    the real thing).
    """
    failures: list[str] = []
    helper_token = "python3 ~/.ai-playbook/scripts/session_channel.py"
    direct_token = "CLAUDE_CODE_SESSION_ID"
    # Shell READ of the env var: ``$`` then optional ``{`` then the token.
    # Anchored to the token so the helper filename / comments / printf strings
    # (which have no preceding ``$``) do not match.
    direct_read_re = re.compile(r"\$\{?" + re.escape(direct_token))

    if adapter_dirs is None:
        # Real install: repo agents/hooks/{skill-gate,lessons-recall}/.
        repo_root = Path(__file__).resolve().parent.parent
        adapter_dirs = [
            repo_root / "agents" / "hooks" / "skill-gate",
            repo_root / "agents" / "hooks" / "lessons-recall",
        ]

    # Env-bridge scripts (sessionStart writers) do not derive session via the helper.
    idiom_exempt = frozenset({"cursor-session-bridge.sh"})

    checked_any = False
    for d in adapter_dirs:
        if not d.is_dir():
            continue
        for sh in sorted(d.glob("*.sh")):
            if sh.name in idiom_exempt:
                continue
            checked_any = True
            try:
                body = sh.read_text(encoding="utf-8")
            except OSError as e:
                failures.append(f"check(3) idiom: cannot read {sh}: {e!r}")
                continue
            if helper_token not in body:
                failures.append(
                    f"check(3) idiom: {sh} omits literal '{helper_token}'"
                )
            if direct_read_re.search(body):
                failures.append(
                    f"check(3) idiom: {sh} reads {direct_token} directly "
                    "(must use the helper)"
                )

    if plans_skill_recipe_path is not None and plans_skill_recipe_path.is_file():
        checked_any = True
        try:
            body = plans_skill_recipe_path.read_text(encoding="utf-8")
            if helper_token not in body:
                failures.append(
                    f"check(3) idiom: {plans_skill_recipe_path} omits literal "
                    f"'{helper_token}'"
                )
        except OSError as e:
            failures.append(
                f"check(3) idiom: cannot read {plans_skill_recipe_path}: {e!r}"
            )

    if not checked_any:
        # No adapters found is itself a doctor failure in the real install,
        # but selftests pass explicit dirs so this branch is informational.
        failures.append("check(3) idiom: no adapter files found to grep")

    return (len(failures) == 0, failures)


def _doctor_check_core_and_runtime(
    runtime_dir: Path | None,
) -> tuple[bool, list[str]]:
    """Check (4): core-symbol imports + writable runtime dir.
    """
    failures: list[str] = []
    # Core-symbol: the installed core (this module) must resolve both symbols.
    if not callable(classify_path):
        failures.append("check(4) core-symbol: classify_path not callable")
    if not callable(check_marker):
        failures.append("check(4) core-symbol: check_marker not callable")

    rdir = runtime_dir if runtime_dir is not None else DEFAULT_RUNTIME_DIR
    try:
        os.makedirs(str(rdir), exist_ok=True, mode=0o700)
    except OSError as e:
        failures.append(
            f"check(4) runtime: cannot create {rdir}: {e!r}"
        )
        return (len(failures) == 0, failures)
    # Confirm writable by this uid.
    probe = rdir / ".doctor-probe"
    try:
        fd = os.open(str(probe), os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, b"ok")
        finally:
            os.close(fd)
        os.unlink(str(probe))
    except OSError as e:
        failures.append(
            f"check(4) runtime: {rdir} not writable by skill uid: {e!r}"
        )
    return (len(failures) == 0, failures)


def _doctor_check_agy_timeout(hooks_json_path: Path) -> tuple[bool, list[str]]:
    """Check (5): the agy PreToolUse entry whose command runs the skill-gate
    adapter has ``timeout > RESOLVER_GIT_TIMEOUT_S``.

    Reads ``~/.gemini/antigravity-cli/hooks.json`` and FAILs iff the
    PreToolUse entry whose ``hooks[].command`` path contains ``skill-gate``
    is absent, or its ``timeout`` is absent / not greater than the resolver's
    internal git timeout (else a hung git makes agy kill the hook before the
    resolver's ``TimeoutExpired`` catch fires -> agy treats hook-kill as
    failure, not block -> gate silently off).

    The skill-gate entry is identified by its COMMAND path containing
    ``skill-gate`` (NOT by matcher token): matchers differ per agent, and the
    agy matcher is the AGY tool vocabulary ``write_to_file|replace_file_content|
    multi_replace_file_content`` (plan line 1168), NOT the Claude
    ``Write|Edit|MultiEdit``. A predicate that looked for the Claude matcher
    false-failed the correct agy install (Family H: verified the abstraction,
    not the real thing).
    """
    failures: list[str] = []
    try:
        text = hooks_json_path.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError) as e:
        # Selftests synthesize this file; the real install asserts it exists
        # (Task 5 README). Absent -> FAIL (cannot verify the timeout).
        return (
            False,
            [f"check(5) agy timeout: cannot read {hooks_json_path}: {e!r}"],
        )
    try:
        doc = json.loads(text)
    except ValueError as e:
        return (
            False,
            [f"check(5) agy timeout: invalid JSON in {hooks_json_path}: {e!r}"],
        )

    array = doc.get("hooks", {}).get("PreToolUse", [])
    if not isinstance(array, list):
        array = []

    found_skill_gate_entry = False
    found_adequate_timeout = False
    for entry in array:
        if not isinstance(entry, dict):
            continue
        hooks = entry.get("hooks")
        if not isinstance(hooks, list):
            continue
        # An entry is the skill-gate entry iff ANY of its command hooks runs a
        # command path containing the literal ``skill-gate`` segment.
        is_skill_gate_entry = any(
            isinstance(h, dict)
            and isinstance(h.get("command"), str)
            and "skill-gate" in h["command"]
            for h in hooks
        )
        if not is_skill_gate_entry:
            continue
        found_skill_gate_entry = True
        timeout = entry.get("timeout")
        if isinstance(timeout, (int, float)) and timeout > facts_paths.RESOLVER_GIT_TIMEOUT_S:
            found_adequate_timeout = True

    if not found_skill_gate_entry:
        failures.append(
            "check(5) agy timeout: no PreToolUse entry whose command path "
            "contains 'skill-gate'"
        )
    elif not found_adequate_timeout:
        failures.append(
            f"check(5) agy timeout: skill-gate PreToolUse entry has no "
            f"timeout > RESOLVER_GIT_TIMEOUT_S "
            f"({facts_paths.RESOLVER_GIT_TIMEOUT_S})"
        )
    return (len(failures) == 0, failures)


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skill_gate.py",
        description=(
            "Agent-agnostic skill-gate core. Classifies the target write path, "
            "consults the per-(project, session) skill-gate marker, and emits "
            "an allow/block decision. May block (exit 2 + stderr on Claude; "
            "exit 0 + JSON on agy)."
        ),
    )
    p.add_argument("--target", help="Target write path to gate.")
    p.add_argument(
        "--session-id",
        default=None,
        help=(
            "Adapter-supplied opaque session value. Absent/empty-after-strip "
            "-> 'no-session' key + FULL window."
        ),
    )
    p.add_argument(
        "--cwd",
        default=None,
        help=(
            "Working directory the gate fires from (defaults to the agent's "
            "cwd). Used for project/plans_dir resolution."
        ),
    )
    p.add_argument(
        "--write-marker",
        nargs="?",
        const="plans",
        default=None,
        metavar="CLASS",
        help=(
            "Write/refresh the skill-gate marker ATOMICALLY (used by gated skills). "
            "Bare --write-marker writes the plans class; --write-marker learn "
            "writes learn.<project>.<session>.marker. Catches FileExistsError as benign."
        ),
    )
    p.add_argument(
        "--doctor",
        action="store_true",
        help="Run the FIVE doctor checks against the live install.",
    )
    p.add_argument("--selftest", action="store_true", help="Run selftests.")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    # Pre-scan for the ``--selftest#<name>`` filter convention (the plan's
    # Validation Commands use it). argparse rejects ``--selftest#name`` as an
    # unrecognized arg, so normalize to ``--selftest`` here; ``selftest()``
    # re-reads the original token from ``sys.argv`` to pick up the filter name.
    args: list[str] = []
    for a in raw:
        if a.startswith("--selftest#"):
            args.append("--selftest")
        else:
            args.append(a)
    parser = _build_parser()
    ns = parser.parse_args(args)

    if ns.selftest:
        return selftest()

    if ns.doctor:
        ok, failures = _doctor()
        if ok:
            print("doctor: OK")
            return 0
        for f in failures:
            print(f"doctor FAIL: {f}")
        return 1

    # Resolve start_dir = --cwd or cwd.
    start_dir = Path(ns.cwd).expanduser() if ns.cwd else Path.cwd()

    if ns.write_marker is not None:
        class_name = ns.write_marker
        if class_name not in GATED_CLASS_REGISTRY:
            sys.stderr.write(
                f"skill-gate: unknown gated class {class_name!r}; "
                f"expected one of {sorted(GATED_CLASS_REGISTRY)}\n"
            )
            return 2
        _, marker_prefix, _ = GATED_CLASS_REGISTRY[class_name]
        return _write_marker(
            start_dir=start_dir,
            session_id=ns.session_id,
            marker_prefix=marker_prefix,
        )

    # Gate consultation. --target is required.
    if not ns.target:
        sys.stderr.write("usage: skill_gate.py --target PATH [--session-id ID] [--cwd DIR]\n")
        return 2

    try:
        allow, deny_reason = _consult(
            ns.target,
            start_dir=start_dir,
            session_id=ns.session_id,
        )
    except (KeyboardInterrupt, SystemExit):
        # Propagate Ctrl-C / SystemExit: a user interrupt during a consultation
        # must NOT silently fail-open the gate (r1-M1/M9). Narrowing away from
        # ``BaseException`` keeps the defensive fail-open for unexpected
        # ``Exception`` subclasses (Family G: a gate that crashes the host agent
        # is worse than no gate) without swallowing interactive interrupts.
        raise
    except Exception as e:  # defensive: NEVER silently fail-OFF.
        # Family G discipline: a gate that crashes the host agent in a way
        # that disables the gate silently is worse than no gate. Log and
        # fail-open with a loud stderr warning (the block path may be
        # unreachable if the gate itself is broken).
        sys.stderr.write(f"skill-gate: internal error; failing open (allow): {e!r}\n")
        facts_paths._append_hooks_log_line({
            "ts": datetime.now(timezone.utc).isoformat(),
            "keying": "error",
            "error": repr(e),
        })
        return 0

    if allow:
        # Emit an allow JSON line (adapter-shaped; agy expects top-level
        # {"allow_tool": true}). Adapters re-shape as needed.
        sys.stdout.write(json.dumps({"allow_tool": True}))
        return 0

    # Block. deny_reason is data-influenced -> json.dumps (L9). Emit a
    # top-level JSON object (agy shape). Claude adapter extracts deny_reason
    # and re-emits on stderr + exit 2.
    envelope = {"allow_tool": False, "deny_reason": deny_reason}
    sys.stdout.write(json.dumps(envelope))
    # Core exits 0; the adapter layer chooses exit 2 (Claude) or 0 (agy).
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


def selftest() -> int:
    """In-memory + tempdir fixtures. Exercises the plan's Task-4 selftest bullets.

    Selectable via ``--selftest#<name>`` (the harness here runs all and prints
    PASS/FAIL per label; a single name filters to matching labels).
    """
    import tempfile
    from contextlib import contextmanager

    # Filter: ``--selftest#<name>`` runs only labels containing ``name``.
    filter_name: str | None = None
    raw_args = sys.argv[1:]
    for a in raw_args:
        if a.startswith("--selftest#"):
            filter_name = a[len("--selftest#"):]
            break

    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        if filter_name is not None and filter_name not in label:
            return
        all_ok = _selftest_check(label, cond, detail) and all_ok

    @contextmanager
    def isolated_home(home_dir: Path):
        """Patch HOME so resolve_project_key/_append_hooks_log_line do not
        touch the REAL ~/.ai-playbook. The runtime dir + hooks.log resolve
        from Path.home() at call time."""
        orig = os.environ.get("HOME")
        os.environ["HOME"] = str(home_dir)
        try:
            yield
        finally:
            if orig is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig

    def make_git_repo(root: Path) -> None:
        """Initialize a REAL git repo at ``root`` (so resolve_project_key's
        ``git rev-parse`` succeeds)."""
        import subprocess as _sp
        root.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["GIT_AUTHOR_NAME"] = "selftest"
        env["GIT_AUTHOR_EMAIL"] = "selftest@example.com"
        env["GIT_COMMITTER_NAME"] = "selftest"
        env["GIT_COMMITTER_EMAIL"] = "selftest@example.com"
        _sp.run(["git", "init", "-q", str(root)], check=True, env=env)
        _sp.run(["git", "-C", str(root), "add", "-A"], check=True, env=env)
        (root / ".gitkeep").write_text("", encoding="utf-8")
        _sp.run(
            ["git", "-C", str(root), "add", "-A"], check=True, env=env
        )
        _sp.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "init"],
            check=True, env=env,
        )

    # Helper: run _consult with isolated HOME + runtime under tmp.
    def run_consult(
        target: str,
        *,
        start_dir: Path,
        home_dir: Path,
        session_id: str | None,
        runtime_dir: Path,
    ) -> tuple[bool, str]:
        with isolated_home(home_dir):
            return _consult(
                target,
                start_dir=start_dir,
                session_id=session_id,
                runtime_dir=runtime_dir,
            )

    # Helper: write a marker with a deterministic mtime.
    def write_marker_at(
        *,
        start_dir: Path,
        home_dir: Path,
        session_id: str | None,
        runtime_dir: Path,
        mtime_offset: float,
        marker_prefix: str = MARKER_PREFIX,
    ) -> Path:
        """Write a marker via _write_marker then override its mtime."""
        with isolated_home(home_dir):
            ts = time.time() + mtime_offset
            _write_marker(
                start_dir=start_dir,
                session_id=session_id,
                marker_prefix=marker_prefix,
                runtime_dir=runtime_dir,
                now=ts,
            )
            project = resolve_project_key(start_dir)
            session = _derive_session_component(session_id)
            marker = _marker_path(
                runtime_dir, project, session, marker_prefix=marker_prefix
            )
            os.utime(str(marker), (ts, ts))
            return marker

    # ------------------------------------------------------------------ #
    # block_without_marker: gated Write + no marker -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "x.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_without_marker: BLOCK (no marker)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )
        check(
            "block_without_marker: deny names the plans skill",
            "plans skill" in reason,
            repr(reason),
        )

    # ------------------------------------------------------------------ #
    # allow_with_fresh_marker: gated Write + SAME (project,session) fresh
    # marker -> ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        target = str(td_path / "docs" / "plans" / "y.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "allow_with_fresh_marker: ALLOW (fresh marker, same session)",
            allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # block_with_stale_marker: marker older than SKILL_GATE_WINDOW -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=-(SKILL_GATE_WINDOW + 60),
        )
        target = str(td_path / "docs" / "plans" / "z.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_with_stale_marker: BLOCK (marker older than window)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # allow_at_exact_window_boundary (r2-L11): a marker with mtime EXACTLY
    # ``now - SKILL_GATE_WINDOW`` (delta == window) is still ALLOW. The
    # implementation is ``0 <= delta <= SKILL_GATE_WINDOW`` (inclusive); a
    # regression changing ``<=`` to ``<`` would BLOCK here. The stale-marker
    # arm above tests 60s past the boundary; this pins the exact edge.
    # Calls _consult with a CONTROLLED ``now`` (write_marker_at + run_consult
    # use wall-clock and would drift past the edge between write and consult).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        marker_now = time.time()
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        # Force the marker mtime to exactly (marker_now - SKILL_GATE_WINDOW)
        # so delta == window when _consult runs with now=marker_now.
        project = resolve_project_key(td_path)
        session = _derive_session_component("sess-A")
        marker = _marker_path(runtime_dir, project, session)
        edge_mtime = marker_now - SKILL_GATE_WINDOW
        os.utime(str(marker), (edge_mtime, edge_mtime))
        target = str(td_path / "docs" / "plans" / "edge.md")
        with isolated_home(home_dir):
            allow, reason = _consult(
                target,
                start_dir=td_path,
                session_id="sess-A",
                runtime_dir=runtime_dir,
                now=marker_now,
            )
        check(
            "allow_at_exact_window_boundary: ALLOW (delta == window, inclusive)",
            allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # block_with_symlink_marker (r2-M7): a planted SYMLINK at the marker leaf,
    # even pointing at a file with a fresh mtime, must BLOCK (read-path
    # hardening mirroring the O_NOFOLLOW write path). Pins the os.lstat +
    # S_ISLNK refusal; a revert to os.stat would FOLLOW the symlink and ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        # Resolve the marker path the same way check_marker does, then plant a
        # symlink at that leaf pointing at a fresh-mtime regular file.
        with isolated_home(home_dir):
            project = resolve_project_key(td_path)
            session = _derive_session_component("sess-A")
            marker = _marker_path(runtime_dir, project, session)
            # Target file with a FRESH mtime (would ALLOW if the symlink were
            # followed).
            victim = runtime_dir / "victim"
            victim.write_text("forged", encoding="utf-8")
            os.utime(str(victim), (time.time(), time.time()))
            os.symlink(str(victim), str(marker))
            assert os.path.islink(str(marker)), "fixture: symlink must exist"
        target = str(td_path / "docs" / "plans" / "sym.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_with_symlink_marker: BLOCK (symlink leaf refused, not followed)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # block_with_future_dated_marker: mtime = now+86400 OR mtime==0 -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # Arm (a): future-dated.
        marker = write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        future_ts = time.time() + 86400
        os.utime(str(marker), (future_ts, future_ts))
        target = str(td_path / "docs" / "plans" / "fut.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_with_future_dated_marker: BLOCK (future mtime)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )
        # Arm (b): mtime == 0.
        os.utime(str(marker), (0, 0))
        allow0, _ = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_with_future_dated_marker: BLOCK (mtime == 0)",
            not allow0,
            f"allow0={allow0}",
        )

    # ------------------------------------------------------------------ #
    # block_cross_session_marker: SAME project, DIFFERENT session -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # Write marker under session-A.
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        target = str(td_path / "docs" / "plans" / "cross.md")
        # Gate fires for session-B: looks up its OWN marker (ABSENT) -> BLOCK.
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-B",
            runtime_dir=runtime_dir,
        )
        check(
            "block_cross_session_marker: BLOCK (different session_id)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # same_session_pair: TRIVIAL sanity - write(id) then read(id) -> ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="X",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        target = str(td_path / "docs" / "plans" / "pair.md")
        allow, _ = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="X",
            runtime_dir=runtime_dir,
        )
        check(
            "same_session_pair: ALLOW (same session_id read/write)",
            allow,
            f"allow={allow}",
        )

    # ------------------------------------------------------------------ #
    # absent_dir_blocks_not_failopens: runtime dir ABSENT + gated Write ->
    # BLOCK (makedirs-before-stat; not FileNotFoundError fail-open).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        # NOTE: runtime_dir does NOT pre-exist; the gate must makedirs it.
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "fresh.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "absent_dir_blocks_not_failopens: BLOCK (missing runtime dir, no marker)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # block_no_session_fallback: --session-id absent/empty -> no-session key.
    # Fresh marker under no-session -> ALLOW; absent -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "ns.md")
        # Arm (a): absent --session-id, NO marker -> BLOCK.
        allow_none, _ = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id=None,
            runtime_dir=runtime_dir,
        )
        check(
            "block_no_session_fallback: BLOCK (absent session-id, no marker)",
            not allow_none,
            f"allow_none={allow_none}",
        )
        # Write a marker under no-session key, then ALLOW.
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id=None,
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        allow_fresh, _ = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id=None,
            runtime_dir=runtime_dir,
        )
        check(
            "block_no_session_fallback: ALLOW (no-session key, fresh marker)",
            allow_fresh,
            f"allow_fresh={allow_fresh}",
        )

    # ------------------------------------------------------------------ #
    # reroot_absent_path_blocks: repo re-rooted between write and gate ->
    # BLOCK via ABSENT-marker path (project filename component differs).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        repo_a = td_path / "repo_a"
        repo_b = td_path / "repo_b"
        make_git_repo(repo_a)
        make_git_repo(repo_b)
        (repo_a / "docs" / "plans").mkdir(parents=True)
        (repo_b / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # Write marker in repo_a.
        write_marker_at(
            start_dir=repo_a,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        # Gate fires from repo_b: project differs -> marker ABSENT -> BLOCK.
        target = str(repo_b / "docs" / "plans" / "reroot.md")
        allow, reason = run_consult(
            target,
            start_dir=repo_b,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "reroot_absent_path_blocks: BLOCK (re-rooted to a different repo)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # plans_dir_default_classification: NO facts.md (worktree) + target
    # docs/plans/x.md -> STILL CLASSIFIED via the docs/plans/ default.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        # NO .ai-playbook/facts.md (a worktree would not have it).
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "default.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "plans_dir_default_classification: BLOCK (classified via docs/plans default, no facts)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # session_empty_string_treated_as_absent: "" and "   " both -> no-session.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # Both inputs derive the literal "no-session".
        s_empty = _derive_session_component("")
        s_ws = _derive_session_component("   ")
        check(
            'session_empty_string_treated_as_absent: "" -> no-session',
            s_empty == NO_SESSION_KEY,
            repr(s_empty),
        )
        check(
            'session_empty_string_treated_as_absent: "   " -> no-session',
            s_ws == NO_SESSION_KEY,
            repr(s_ws),
        )
        # BYTE-IDENTICAL marker filename for both arms.
        with isolated_home(home_dir):
            project = resolve_project_key(td_path)
            marker_empty = _marker_path(runtime_dir, project, s_empty).name
            marker_ws = _marker_path(runtime_dir, project, s_ws).name
        check(
            "session_empty_string_treated_as_absent: byte-identical marker filename",
            marker_empty == marker_ws and "no-session" in marker_empty,
            f"{marker_empty} vs {marker_ws}",
        )

    # ------------------------------------------------------------------ #
    # cross_tree_absolute_target_classified: gate cwd is a worktree, absolute
    # target into MAIN repo's docs/plans/ -> STILL classified as gated.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        main_repo = td_path / "main"
        worktree = td_path / "worktree"
        make_git_repo(main_repo)
        make_git_repo(worktree)
        (main_repo / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(main_repo / "docs" / "plans" / "crosstree.md")
        # Gate fires from the worktree cwd; absolute target in main repo.
        allow, reason = run_consult(
            target,
            start_dir=worktree,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "cross_tree_absolute_target_classified: BLOCK (cross-tree target gated via default suffix)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # doctor_pretooluse_array: PreToolUse array membership.
    # ------------------------------------------------------------------ #
    def write_settings(p: Path, hooks_array: list) -> None:
        p.write_text(
            json.dumps({"hooks": {"PreToolUse": hooks_array}}),
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        settings = td_path / "settings.json"
        # Arm 1: BOTH Bash and Write|Edit|MultiEdit -> PASS.
        write_settings(settings, [
            {"matcher": "Bash", "hooks": []},
            {"matcher": "Write|Edit|MultiEdit", "hooks": []},
        ])
        ok, fails = _doctor_check_pretooluse_array(settings)
        check(
            "doctor_pretooluse_array: PASS (Bash + Write|Edit|MultiEdit)",
            ok,
            str(fails),
        )
        # Arm 2: ONLY Bash -> FAIL.
        write_settings(settings, [{"matcher": "Bash", "hooks": []}])
        ok2, _ = _doctor_check_pretooluse_array(settings)
        check(
            "doctor_pretooluse_array: FAIL (only Bash)",
            not ok2,
            "expected FAIL",
        )
        # Arm 3: Write|MultiEdit (missing Edit) -> FAIL.
        write_settings(settings, [
            {"matcher": "Bash", "hooks": []},
            {"matcher": "Write|MultiEdit", "hooks": []},
        ])
        ok3, _ = _doctor_check_pretooluse_array(settings)
        check(
            "doctor_pretooluse_array: FAIL (Write|MultiEdit missing Edit)",
            not ok3,
            "expected FAIL",
        )

    # ------------------------------------------------------------------ #
    # doctor_dangling_symlink: dangling symlink among 11 paths -> FAIL.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Build a synthetic HOME tree with all 11 paths live first.
        with isolated_home(td_path):
            for raw in _DOCTOR_PATHS:
                p = Path(raw).expanduser()
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("# live", encoding="utf-8")
            # Now make ONE of them a DANGLING symlink.
            victim = Path(_DOCTOR_PATHS[2]).expanduser()  # skill_gate.py
            victim.unlink()
            dangling_target = td_path / "does_not_exist"
            os.symlink(str(dangling_target), str(victim))
            ok, fails = _doctor_check_paths()
            check(
                "doctor_dangling_symlink: FAIL loud on dangling symlink",
                not ok,
                str(fails),
            )
            check(
                "doctor_dangling_symlink: failure mentions the dangling path",
                any("skill_gate.py" in f for f in fails),
                str(fails),
            )

    # ------------------------------------------------------------------ #
    # doctor_agy_timeout: parametrize timeout against RESOLVER_GIT_TIMEOUT_S.
    # The synthetic hooks.json MIRRORS the REAL agy install: the matcher is the
    # AGY tool vocabulary (write_to_file|replace_file_content|multi_replace_file_content)
    # and the command path contains `skill-gate`. The predicate must identify
    # the skill-gate entry by its COMMAND path, not by the Claude matcher token
    # (matchers differ per agent). A fixture using the Claude matcher would
    # pass the buggy matcher-based predicate and hide the bug (Family H).
    # ------------------------------------------------------------------ #
    AGY_MATCHER = "write_to_file|replace_file_content|multi_replace_file_content"
    AGY_COMMAND = "/home/self/.gemini/antigravity-cli/hooks/skill-gate.sh"

    def write_hooks_json(p: Path, timeout) -> None:
        entry: dict = {
            "matcher": AGY_MATCHER,
            "hooks": [{"type": "command", "command": AGY_COMMAND}],
        }
        if timeout is not None:
            entry["timeout"] = timeout
        p.write_text(
            json.dumps({"hooks": {"PreToolUse": [entry]}}),
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        hj = td_path / "hooks.json"
        R = facts_paths.RESOLVER_GIT_TIMEOUT_S
        # timeout == R -> FAIL.
        write_hooks_json(hj, R)
        ok_eq, _ = _doctor_check_agy_timeout(hj)
        check(
            f"doctor_agy_timeout: FAIL (timeout == RESOLVER_GIT_TIMEOUT_S={R})",
            not ok_eq,
            "expected FAIL",
        )
        # timeout == R+1 -> PASS (lower bound).
        write_hooks_json(hj, R + 1)
        ok_lb, _ = _doctor_check_agy_timeout(hj)
        check(
            f"doctor_agy_timeout: PASS (timeout == RESOLVER_GIT_TIMEOUT_S+1={R+1})",
            ok_lb,
            "expected PASS",
        )
        # timeout == 2*R -> PASS (README value).
        write_hooks_json(hj, 2 * R)
        ok_readme, _ = _doctor_check_agy_timeout(hj)
        check(
            f"doctor_agy_timeout: PASS (timeout == 2*RESOLVER_GIT_TIMEOUT_S={2*R})",
            ok_readme,
            "expected PASS",
        )
        # timeout ABSENT -> FAIL.
        write_hooks_json(hj, None)
        ok_absent, _ = _doctor_check_agy_timeout(hj)
        check(
            "doctor_agy_timeout: FAIL (timeout ABSENT)",
            not ok_absent,
            "expected FAIL",
        )
        # Sanity: a NON-skill-gate command path with a huge timeout -> FAIL
        # (the entry must be identified as the skill-gate entry; an unrelated
        # entry's timeout does not satisfy the check).
        other = {
            "matcher": AGY_MATCHER,
            "timeout": 10 * R,
            "hooks": [
                {"type": "command", "command": "/home/self/.gemini/antigravity-cli/hooks/other.sh"}
            ],
        }
        hj.write_text(json.dumps({"hooks": {"PreToolUse": [other]}}), encoding="utf-8")
        ok_other, _ = _doctor_check_agy_timeout(hj)
        check(
            "doctor_agy_timeout: FAIL (no skill-gate command path)",
            not ok_other,
            "expected FAIL - unrelated command path must not satisfy check",
        )

    # ------------------------------------------------------------------ #
    # doctor_real_install_shape: a synthetic adapter that MIRRORS the real
    # Claude adapter must PASS check(3). The real adapter contains the helper
    # invocation AND a printf warning string carrying the BARE token
    # `CLAUDE_CODE_SESSION_ID` AND comments mentioning the token, but NEVER
    # reads the env var (no `$CLAUDE_CODE_SESSION_ID`). The predicate must
    # detect an actual shell READ, not the bare token in prose/strings.
    # ------------------------------------------------------------------ #
    HELPER = "python3 ~/.ai-playbook/scripts/session_channel.py"
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        adapter_dir = td_path / "skill-gate"
        adapter_dir.mkdir()
        # Shape A: mirrors the real Claude adapter. Bare token appears ONLY in
        # comments and the printf warning string; helper invocation present; NO
        # shell read. Must PASS.
        mirror = adapter_dir / "claude.sh"
        mirror.write_text(
            "#!/usr/bin/env bash\n"
            "# Derives the session via the helper (CLAUDE_CODE_SESSION_ID is read\n"
            "# INSIDE the helper, never here).\n"
            "set -u\n"
            f'SID="$({HELPER})"\n'
            'if [ -z "$SID" ]; then\n'
            "    printf 'CLAUDE_CODE_SESSION_ID absent; running in no-session mode\\n' >&2\n"
            "fi\n"
            'python3 "$HOME/.ai-playbook/scripts/skill_gate.py" --target "$1"\n',
            encoding="utf-8",
        )
        ok_mirror, fails_mirror = _doctor_check_subprocess_idiom([adapter_dir], None)
        check(
            "doctor_real_install_shape: PASS (mirror of real Claude adapter)",
            ok_mirror,
            str(fails_mirror),
        )
        # Shape B: genuinely reads the env var directly ($CLAUDE_CODE_SESSION_ID).
        # Must FAIL even though the helper invocation is also present.
        reader = adapter_dir / "codex.sh"
        reader.write_text(
            "#!/usr/bin/env bash\n"
            "set -u\n"
            f'SID="$({HELPER})"\n'
            'FALLBACK="${CLAUDE_CODE_SESSION_ID:-}"\n'
            'echo "$FALLBACK"\n',
            encoding="utf-8",
        )
        ok_reader, fails_reader = _doctor_check_subprocess_idiom([adapter_dir], None)
        check(
            "doctor_real_install_shape: FAIL (direct $CLAUDE_CODE_SESSION_ID read)",
            not ok_reader,
            str(fails_reader),
        )
        check(
            "doctor_real_install_shape: FAIL cites the direct-read offender",
            any("codex.sh" in f and "directly" in f for f in fails_reader),
            str(fails_reader),
        )
        # Shape C: helper invocation ABSENT. Must FAIL (omits the helper).
        no_helper = adapter_dir / "cursor.sh"
        no_helper.write_text(
            "#!/usr/bin/env bash\n"
            "# mentions CLAUDE_CODE_SESSION_ID in a comment only\n"
            'echo "no helper here"\n',
            encoding="utf-8",
        )
        ok_no, fails_no = _doctor_check_subprocess_idiom([adapter_dir], None)
        check(
            "doctor_real_install_shape: FAIL (helper invocation omitted)",
            not ok_no,
            str(fails_no),
        )

    # ------------------------------------------------------------------ #
    # project_not_aliased_across_sibling_worktree: two sibling external git
    # worktrees derive DIFFERENT project hashes (no aliasing).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        wt_a = td_path / "wt_a"
        wt_b = td_path / "wt_b"
        make_git_repo(wt_a)
        make_git_repo(wt_b)
        home_dir = td_path / "home"
        home_dir.mkdir()
        with isolated_home(home_dir):
            proj_a = resolve_project_key(wt_a)
            proj_b = resolve_project_key(wt_b)
        expected_a = hashlib.sha1(os.path.realpath(str(wt_a)).encode()).hexdigest()[:16]
        expected_b = hashlib.sha1(os.path.realpath(str(wt_b)).encode()).hexdigest()[:16]
        check(
            "project_not_aliased_across_sibling_worktree: proj_a == sha1(realpath(wt_a))[:16]",
            proj_a == expected_a,
            f"proj_a={proj_a} expected={expected_a}",
        )
        check(
            "project_not_aliased_across_sibling_worktree: proj_b == sha1(realpath(wt_b))[:16]",
            proj_b == expected_b,
            f"proj_b={proj_b} expected={expected_b}",
        )
        check(
            "project_not_aliased_across_sibling_worktree: proj_a != proj_b",
            proj_a != proj_b,
            f"proj_a={proj_a} proj_b={proj_b}",
        )
        # The resolver writes ``keying=no-anchor`` ONLY on its git-failure
        # branch. git rev-parse SUCCEEDS for an external worktree, so the
        # resolver must NOT have written ``no-anchor``. (The CORE writes
        # ``env-var``/``project-only`` only when it is consulted; these calls
        # exercise the resolver alone, via _write_marker.) The discriminating
        # assertion is the ABSENCE of a ``no-anchor`` line.
        hooks_log = home_dir / ".ai-playbook" / "logs" / "hooks.log"
        keyings: list[str] = []
        if hooks_log.is_file():
            for ln in hooks_log.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    keyings.append(json.loads(ln).get("keying"))
                except ValueError:
                    continue
        check(
            "project_not_aliased_across_sibling_worktree: NO keying=no-anchor (git succeeded)",
            "no-anchor" not in keyings,
            f"keyings={keyings}",
        )

    # ------------------------------------------------------------------ #
    # project_stable_across_sibling_cwd_in_worktree: SINGLE external worktree,
    # skill writes from ROOT, gate fires from a SUBDIR -> SAME project -> ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        wt = td_path / "wt_single"
        make_git_repo(wt)
        (wt / "docs" / "plans").mkdir(parents=True)
        subdir = wt / "subdir"
        subdir.mkdir()
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # Write marker from the worktree ROOT.
        write_marker_at(
            start_dir=wt,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
            mtime_offset=0,
        )
        # Gate fires from a SUBDIR of the same worktree.
        target = str(wt / "docs" / "plans" / "stable.md")
        allow, reason = run_consult(
            target,
            start_dir=subdir,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "project_stable_across_sibling_cwd_in_worktree: ALLOW (same project from subdir)",
            allow,
            f"allow={allow} reason={reason!r}",
        )
        # Resolved marker filename's project component EQUALS resolver(subdir).
        with isolated_home(home_dir):
            proj_subdir = resolve_project_key(subdir)
            session = _derive_session_component("sess-A")
            marker_name = _marker_path(runtime_dir, proj_subdir, session).name
        check(
            "project_stable_across_sibling_cwd_in_worktree: marker project == resolver(subdir)",
            proj_subdir == facts_paths.resolve_project_key(subdir)
            and proj_subdir in marker_name
            and not isinstance(facts_paths.resolve_project_key(subdir), tuple),
            f"proj_subdir={proj_subdir} marker={marker_name}",
        )

    # ------------------------------------------------------------------ #
    # project_no_anchor_in_non_git_dir: non-git cwd -> project =
    # sha1(realpath(cwd)) AND hooks.log FILE carries keying=no-anchor.
    # r17-M1 ABSENT-PARENT + r18-M2 GIT-REPO CWD PIN.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        nongit = td_path / "nongit"
        nongit.mkdir()
        (nongit / "docs" / "plans").mkdir(parents=True)
        # Primary arm: monkeypatch HOME to a tmp dir whose logs/ does NOT
        # pre-exist; run the core consultation from the non-git cwd.
        home_dir = td_path / "home"
        home_dir.mkdir()
        with isolated_home(home_dir):
            assert not (home_dir / ".ai-playbook" / "logs").exists()
            project = resolve_project_key(nongit)
            expected = hashlib.sha1(os.path.realpath(str(nongit)).encode()).hexdigest()[:16]
            check(
                "project_no_anchor_in_non_git_dir: project == sha1(realpath(cwd))[:16]",
                project == expected,
                f"project={project} expected={expected}",
            )
            hooks_log = home_dir / ".ai-playbook" / "logs" / "hooks.log"
            check(
                "project_no_anchor_in_non_git_dir: hooks.log FILE exists (cold-start dir created)",
                hooks_log.is_file(),
                str(hooks_log),
            )
            if hooks_log.is_file():
                lines = [
                    json.loads(ln) for ln in hooks_log.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                ]
                last = lines[-1] if lines else {}
                check(
                    "project_no_anchor_in_non_git_dir: keying == no-anchor",
                    last.get("keying") == "no-anchor",
                    repr(last),
                )

    # r17-M1 ABSENT-PARENT arm + r18-M2 GIT-REPO CWD PIN: HOME tmp dir whose
    # logs/ does NOT pre-exist AND core consultation from a GIT-REPO cwd so
    # the resolver's git rev-parse SUCCEEDS, no-anchor does NOT fire.
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        git_repo = td_path / "gitrepo"
        make_git_repo(git_repo)
        (git_repo / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        with isolated_home(home_dir):
            assert not (home_dir / ".ai-playbook" / "logs").exists()
            target = str(git_repo / "docs" / "plans" / "p.md")
            # Core consultation from the git-repo cwd.
            _consult(
                target,
                start_dir=git_repo,
                session_id="sess-A",
                runtime_dir=runtime_dir,
            )
            hooks_log = home_dir / ".ai-playbook" / "logs" / "hooks.log"
            check(
                "project_no_anchor_in_non_git_dir: absent-parent arm hooks.log FILE exists",
                hooks_log.is_file(),
                str(hooks_log),
            )
            if hooks_log.is_file():
                lines = [
                    json.loads(ln) for ln in hooks_log.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                ]
                # The core's OWN keying=env-var/project-only line MUST reach the
                # file (the helper's makedirs created the dir). Find a core line
                # (env-var or project-only); it must be present.
                core_keyings = {
                    ln.get("keying") for ln in lines
                    if ln.get("keying") in {"env-var", "project-only"}
                }
                check(
                    "project_no_anchor_in_non_git_dir: core keying line reaches file (absent-parent)",
                    len(core_keyings) > 0,
                    str(lines),
                )

    # ------------------------------------------------------------------ #
    # project_single_source: IDENTITY with facts_paths.resolve_project_key.
    # ------------------------------------------------------------------ #
    check(
        "project_single_source: resolve_project_key is facts_paths.resolve_project_key",
        resolve_project_key is facts_paths.resolve_project_key,
        "IDENTITY failed",
    )

    # ------------------------------------------------------------------ #
    # absent_marker_blocks: gated Write + NO marker -> BLOCK (no second signal).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "absent.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "absent_marker_blocks: BLOCK (no marker, no second signal)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # non_gated_path: Write of src/foo.py -> ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "src").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "src" / "foo.py")
        allow, _ = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-A",
            runtime_dir=runtime_dir,
        )
        check(
            "non_gated_path: ALLOW (src/foo.py not gated)",
            allow,
            f"allow={allow}",
        )

    # ------------------------------------------------------------------ #
    # traversal_bypass: src/../../docs/plans/x.md AND plans_dir-as-symlink ->
    # BOTH classified as gated.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        (td_path / "src").mkdir(parents=True)
        # Arm 1: traversal in the target string.
        target1 = str(td_path / "src" / ".." / ".." / "docs" / "plans" / "trav.md")
        plans_dir_real = td_path / "docs" / "plans"
        gated1 = classify_path(target1, str(plans_dir_real))
        check(
            "traversal_bypass: src/../../docs/plans/x.md classified gated",
            gated1,
            f"gated1={gated1}",
        )
        # Arm 2: plans_dir is itself a SYMLINK to <elsewhere>/plans/.
        elsewhere = td_path / "elsewhere"
        elsewhere.mkdir()
        real_plans = elsewhere / "plans"
        real_plans.mkdir()
        link_plans = td_path / "plans_link"
        os.symlink(str(real_plans), str(link_plans))
        target_inside = link_plans / "y.md"
        gated2 = classify_path(str(target_inside), str(link_plans))
        check(
            "traversal_bypass: symlinked plans_dir target classified gated",
            gated2,
            f"gated2={gated2}",
        )

    # ------------------------------------------------------------------ #
    # fail_open: unreadable marker store (PermissionError) -> ALLOW + stderr.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "p.md")
        # Make check_marker raise PermissionError by monkeypatching os.lstat
        # (r2-M7: check_marker now uses os.lstat, not os.stat).
        real_lstat = os.lstat
        stat_calls: list[str] = []

        def fake_lstat(p):
            stat_calls.append(str(p))
            # Only raise for the marker path; let makedirs probes through.
            if str(p).endswith(".marker"):
                raise PermissionError(errno_EACCES, "denied", str(p))
            return real_lstat(p)

        import errno as _errno

        def fake_lstat_errno(p):
            stat_calls.append(str(p))
            if str(p).endswith(".marker"):
                raise PermissionError(_errno.EACCES, "Permission denied", str(p))
            return real_lstat(p)

        orig_lstat = os.lstat
        os.lstat = fake_lstat_errno
        captured_stderr = []
        real_stderr = sys.stderr
        captured_log_path = home_dir / ".ai-playbook" / "logs" / "hooks.log"
        try:
            class _BufErr:
                def write(self, s):
                    captured_stderr.append(s)
                def flush(self):
                    pass
            sys.stderr = _BufErr()
            with isolated_home(home_dir):
                allow, reason = _consult(
                    target,
                    start_dir=td_path,
                    session_id="sess-A",
                    runtime_dir=runtime_dir,
                )
        finally:
            sys.stderr = real_stderr
            os.lstat = orig_lstat
        check(
            "fail_open: ALLOW on PermissionError",
            allow,
            f"allow={allow} reason={reason!r}",
        )
        check(
            "fail_open: stderr warning emitted",
            any("failing open" in s or "marker store" in s for s in captured_stderr),
            repr(captured_stderr),
        )
        # r4-L5: pin the LOUD keying line, mirroring the sibling
        # fail_open_oserror_resolve_sibling test. A regression that deletes the
        # _append_hooks_log_line({"keying": "fail-open"}) call while keeping
        # the stderr write would PASS the stderr assertion but FAIL this one.
        log_text = captured_log_path.read_text() if captured_log_path.exists() else ""
        check(
            "fail_open: hooks.log keying fail-open (not error)",
            '"keying": "fail-open"' in log_text and '"keying": "error"' not in log_text,
            f"log={log_text!r}",
        )

    # ------------------------------------------------------------------ #
    # fail_open_oserror (r2-M1): a NON-Permission OSError (ELOOP) from the
    # marker store fail-opens EXPLICITLY with the loud warning, instead of
    # falling through to main's generic ``except Exception`` (silent fail-open).
    # Pins the widened ``except OSError`` catch (was ``except PermissionError``
    # only; a revert lets ELOOP escape to the generic arm and would NOT emit
    # the "marker store unreadable" stderr line asserted here).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "eloop.md")
        import errno as _errno2

        # r3-L1: capture-before-patch ordering to match the sibling ``fail_open``
        # selftest above (capture ``real_lstat2`` BEFORE defining the patch that
        # closes over it; the old inverted ordering worked but was fragile).
        real_lstat2 = os.lstat
        orig_lstat2 = os.lstat

        def fake_lstat_eloop(p):
            if str(p).endswith(".marker"):
                # ELOOP = too many symbolic links encountered; NOT a subclass
                # of PermissionError. A bare OSError with errno set.
                raise OSError(_errno2.ELOOP, "Too many levels of symbolic links", str(p))
            return real_lstat2(p)

        os.lstat = fake_lstat_eloop
        captured_stderr2 = []
        real_stderr = sys.stderr
        try:
            class _BufErr2:
                def write(self, s):
                    captured_stderr2.append(s)
                def flush(self):
                    pass
            sys.stderr = _BufErr2()
            with isolated_home(home_dir):
                allow, reason = _consult(
                    target,
                    start_dir=td_path,
                    session_id="sess-A",
                    runtime_dir=runtime_dir,
                )
        finally:
            sys.stderr = real_stderr
            os.lstat = orig_lstat2
        check(
            "fail_open_oserror: ALLOW on non-Permission OSError (ELOOP)",
            allow,
            f"allow={allow} reason={reason!r}",
        )
        check(
            "fail_open_oserror: stderr warning emitted (explicit fail-open, not silent fall-through)",
            any("failing open" in s or "marker store" in s for s in captured_stderr2),
            repr(captured_stderr2),
        )

    # ------------------------------------------------------------------ #
    # fail_open_oserror_resolve_sibling (r3-M1): an OSError from the
    # resolve/classify path (NOT from check_marker) - e.g. an ELOOP raised by
    # ``os.path.realpath`` inside ``classify_path`` or
    # ``resolve_plans_dir``/``resolve_project_key`` - fail-opens LOUDLY with
    # the ``keying=fail-open`` hooks.log label and the ``marker store
    # unreadable`` stderr warning, NOT silently via main's generic arm
    # (``keying=error``). r2-M1 widened the catch but wrapped ONLY
    # check_marker; this test pins the SIBLING cells of the partition
    # (Family-A coverage). A revert to the r2-M1 try scope (check_marker only)
    # would let the realpath OSError escape to main and the test would fail:
    # the captured stderr would NOT contain ``marker store`` and the
    # hooks.log keying would be ``error``, not ``fail-open``.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "resolve_eloop.md")
        import errno as _errno3

        real_realpath = os.path.realpath

        def fake_realpath_eloop(p, *a, **k):
            # Raise on ANY realpath in the resolve/classify chain (the target
            # itself is realpath'd by classify_path at line 170). ELOOP is NOT
            # a subclass of PermissionError.
            raise OSError(_errno3.ELOOP, "Too many levels of symbolic links", str(p))

        orig_realpath = os.path.realpath
        os.path.realpath = fake_realpath_eloop
        captured_stderr3: list[str] = []
        real_stderr = sys.stderr
        captured_log_path = home_dir / ".ai-playbook" / "logs" / "hooks.log"
        try:
            class _BufErr3:
                def write(self, s):
                    captured_stderr3.append(s)
                def flush(self):
                    pass
            sys.stderr = _BufErr3()
            with isolated_home(home_dir):
                allow, reason = _consult(
                    target,
                    start_dir=td_path,
                    session_id="sess-A",
                    runtime_dir=runtime_dir,
                )
        finally:
            sys.stderr = real_stderr
            os.path.realpath = orig_realpath
        check(
            "fail_open_oserror_resolve_sibling: ALLOW on ELOOP from realpath (not check_marker)",
            allow,
            f"allow={allow} reason={reason!r}",
        )
        check(
            "fail_open_oserror_resolve_sibling: LOUD stderr warning (marker store unreadable)",
            any("marker store" in s or "failing open" in s for s in captured_stderr3),
            repr(captured_stderr3),
        )
        # The LOUD path logs a record with ``"keying": "fail-open"``; the
        # SILENT counter-factual (escaping to main's generic arm) logs
        # ``"keying": "error"``. Match the JSON form (the helper writes
        # json.dumps, so the field is ``"keying": "..."`` with a space).
        log_text3 = captured_log_path.read_text() if captured_log_path.exists() else ""
        check(
            "fail_open_oserror_resolve_sibling: hooks.log keying fail-open (not error)",
            '"keying": "fail-open"' in log_text3 and '"keying": "error"' not in log_text3,
            f"log={log_text3!r}",
        )

    # ------------------------------------------------------------------ #
    # main_fail_open_on_exception_but_propagate_kbi (r1-M1/M9): a generic
    # Exception inside _consult fails OPEN (Family G), but KeyboardInterrupt
    # and SystemExit PROPAGATE out of main() (Ctrl-C during a consultation
    # must NOT silently allow). Pins the narrowed catch (was BaseException).
    # ------------------------------------------------------------------ #
    this_mod = sys.modules[__name__]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        target = str(td_path / "docs" / "plans" / "exc.md")
        orig_consult = this_mod._consult

        def _raise_valueerror(*a, **k):
            raise ValueError("synthetic crash inside _consult")

        def _raise_kbi(*a, **k):
            raise KeyboardInterrupt

        def _raise_sysexit(*a, **k):
            raise SystemExit(7)

        # The fail-open branch calls _append_hooks_log_line, so isolate HOME.
        with isolated_home(home_dir):
            # Arm 1: a generic Exception -> main() returns 0 (fail-open).
            this_mod._consult = _raise_valueerror
            try:
                rc_valueerror = main([
                    "--target", target,
                    "--cwd", str(td_path),
                    "--session-id", "sess-A",
                ])
            finally:
                this_mod._consult = orig_consult
            check(
                "main_fail_open: generic Exception -> exit 0 (fail-open)",
                rc_valueerror == 0,
                f"rc={rc_valueerror}",
            )

            # Arm 2: KeyboardInterrupt -> main() PROPAGATES (not swallowed).
            this_mod._consult = _raise_kbi
            kbi_propagated = False
            try:
                main([
                    "--target", target,
                    "--cwd", str(td_path),
                    "--session-id", "sess-A",
                ])
            except KeyboardInterrupt:
                kbi_propagated = True
            finally:
                this_mod._consult = orig_consult
            check(
                "main_fail_open: KeyboardInterrupt PROPAGATES (not fail-open)",
                kbi_propagated,
                "expected KeyboardInterrupt to escape main()",
            )

            # Arm 3: SystemExit -> main() PROPAGATES.
            this_mod._consult = _raise_sysexit
            sysexit_propagated = False
            try:
                main([
                    "--target", target,
                    "--cwd", str(td_path),
                    "--session-id", "sess-A",
                ])
            except SystemExit:
                sysexit_propagated = True
            finally:
                this_mod._consult = orig_consult
            check(
                "main_fail_open: SystemExit PROPAGATES (not fail-open)",
                sysexit_propagated,
                "expected SystemExit to escape main()",
            )

    # ------------------------------------------------------------------ #
    # deny_reason_adversarial: block on a target with ", }, newline, and a
    # literal "allow_tool" field -> envelope round-trips json.loads with
    # deny_reason as ONE string.
    # ------------------------------------------------------------------ #
    adversarial_target = (
        'docs/plans/x"}\n"allow_tool": false, "y.md'
    )
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        # Build a target path containing adversarial chars under docs/plans/.
        # classify_path works on the string; the path need not exist on disk.
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        envelope = None
        with isolated_home(home_dir):
            allow, reason = _consult(
                adversarial_target,
                start_dir=td_path,
                session_id="sess-A",
                runtime_dir=runtime_dir,
            )
            # The block path emits an envelope via main(); here we replicate
            # the adapter envelope shape to test round-trip safety.
            envelope = json.dumps({"allow_tool": False, "deny_reason": reason})
        rt = json.loads(envelope)
        check(
            "deny_reason_adversarial: envelope round-trips json.loads",
            isinstance(rt, dict) and "deny_reason" in rt,
            repr(envelope),
        )
        check(
            "deny_reason_adversarial: deny_reason is ONE string",
            isinstance(rt.get("deny_reason"), str),
            repr(rt.get("deny_reason")),
        )

    # ------------------------------------------------------------------ #
    # no_em_dash: no U+2014 in any output of the core.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "plans" / "em.md")
        with isolated_home(home_dir):
            allow, reason = _consult(
                target,
                start_dir=td_path,
                session_id="sess-A",
                runtime_dir=runtime_dir,
            )
        blob = reason + (json.dumps({"allow_tool": allow}))
        # Construct the em dash via chr(0x2014) so this source file itself
        # contains NO U+2014 (the rule applies to generated text AND source).
        em_dash = chr(0x2014)
        check(
            "no_em_dash: no U+2014 in core output",
            em_dash not in blob,
            repr(blob[:80]),
        )

    # ------------------------------------------------------------------ #
    # write_marker_concurrent: pre-create the .tmp -> FileExistsError caught
    # at call site; exit 0; marker ABSENT/unchanged; .tmp NOT deleted.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        # FIRST ensure the runtime dir exists (the writer uses the same
        # makedirs), so the pre-create cannot FileNotFoundError.
        os.makedirs(str(runtime_dir), exist_ok=True, mode=0o700)
        with isolated_home(home_dir):
            project = resolve_project_key(td_path)
            session = _derive_session_component("sess-C")
            marker = _marker_path(runtime_dir, project, session)
            tmp_path = Path(f"{marker}.tmp")
            # PRE-CREATE the .tmp with a known inode/mtime.
            tmp_path.write_text("pre-created", encoding="utf-8")
            pre_stat = os.stat(str(tmp_path))
            pre_inode = pre_stat.st_ino
            pre_mtime = pre_stat.st_mtime
            # A SINGLE --write-marker call must catch FileExistsError and exit 0.
            rc = _write_marker(
                start_dir=td_path,
                session_id="sess-C",
                runtime_dir=runtime_dir,
            )
            check(
                "write_marker_concurrent: writer exits 0 on pre-created .tmp",
                rc == 0,
                f"rc={rc}",
            )
            # Marker ABSENT/unchanged (no os.replace occurred).
            check(
                "write_marker_concurrent: marker ABSENT (no os.replace)",
                not marker.exists(),
                str(marker),
            )
            # .tmp STILL EXISTS with SAME inode/mtime (not deleted, not replaced).
            post_stat = os.stat(str(tmp_path))
            check(
                "write_marker_concurrent: .tmp still exists (not deleted)",
                tmp_path.exists(),
                str(tmp_path),
            )
            check(
                "write_marker_concurrent: .tmp SAME inode",
                post_stat.st_ino == pre_inode,
                f"pre={pre_inode} post={post_stat.st_ino}",
            )
            check(
                "write_marker_concurrent: .tmp SAME mtime",
                post_stat.st_mtime == pre_mtime,
                f"pre={pre_mtime} post={post_stat.st_mtime}",
            )
            # Cleanup the test's own .tmp.
            try:
                tmp_path.unlink()
            except OSError:
                pass

        # ADDITIONALLY (r13-M4): assert ONE of (i) lessons_corpus.py UNCHANGED
        # by this task (the catch is at the CALL SITE), OR (ii)
        # atomic_write_text RAISES FileExistsError when .tmp exists.
        lc_path = Path(__file__).resolve().parent / "lessons_corpus.py"
        catch_in_atomic = "FileExistsError" in lc_path.read_text(encoding="utf-8")
        # Verify atomic_write_text RAISES (does not catch) FileExistsError.
        atomic_raises = False
        probe_tmp = td_path / "probe_target"
        probe_tmp2 = Path(f"{probe_tmp}.tmp")
        probe_tmp2.write_text("blocker", encoding="utf-8")
        try:
            lessons_corpus.atomic_write_text(str(probe_tmp), "new")
        except FileExistsError:
            atomic_raises = True
        except BaseException:
            atomic_raises = False
        finally:
            try:
                probe_tmp2.unlink()
            except OSError:
                pass
            try:
                probe_tmp.unlink()
            except OSError:
                pass
        check(
            "write_marker_concurrent: lessons_corpus.py does NOT catch FileExistsError (catch at call site)",
            not catch_in_atomic and atomic_raises,
            f"catch_in_atomic={catch_in_atomic} atomic_raises={atomic_raises}",
        )

    # ------------------------------------------------------------------ #
    # write_marker_swallows_concurrent_utime_deletion (r1-M4): a concurrent
    # deletion of the marker between ``atomic_write_text`` and ``os.utime``
    # makes ``os.utime`` raise ``FileNotFoundError``. The ``--write-marker``
    # path has NO top-level guard, so an unwrapped ``os.utime`` would crash the
    # hook process with a traceback. Pins the wrapped call (return 0 anyway;
    # the marker was written, the mtime could not be normalized).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        with isolated_home(home_dir):
            real_utime = os.utime
            import errno as _errno_mod
            errno_enoent = _errno_mod.ENOENT

            def utime_raising_fnf(path, times):
                # Simulate the marker being deleted between os.replace and
                # os.utime: raise FileNotFoundError only for the marker path.
                if str(path).endswith(".marker"):
                    raise FileNotFoundError(errno_enoent, "deleted", str(path))
                return real_utime(path, times)

            orig_utime = os.utime
            os.utime = utime_raising_fnf
            try:
                rc = _write_marker(
                    start_dir=td_path,
                    session_id="sess-M4",
                    runtime_dir=runtime_dir,
                )
            finally:
                os.utime = orig_utime
            check(
                "write_marker_utime_fnf: writer exits 0 on concurrent marker deletion",
                rc == 0,
                f"rc={rc}",
            )

    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # session_value_path_safe (M6/r9; r10-M3 hex format): --session-id
    # "../evil" -> the sanitized filename component stays inside the runtime
    # dir (sha1 hexdigest[:16], no traversal, no aliasing of another session's
    # marker). Pins the core's OWN session sanitization (the leaf
    # session_channel.py is pinned by its own --selftest; this arm pins the
    # core's _derive_session_component).
    # ------------------------------------------------------------------ #
    import re as _re
    evil_session = _derive_session_component("../evil")
    check(
        "session_value_path_safe: '../evil' -> ^[0-9a-f]{16}$ hex",
        bool(_re.match(r"^[0-9a-f]{16}$", evil_session)),
        f"got={evil_session!r}",
    )
    check(
        "session_value_path_safe: hex != literal '../evil' (no traversal)",
        "../evil" not in evil_session and "/" not in evil_session and "." not in evil_session,
        f"got={evil_session!r}",
    )
    # The sanitized value is what lands in the marker filename, so the filename
    # itself stays inside the runtime dir (no path traversal via the session
    # component).
    evil_marker = _marker_path(
        Path("/tmp/runtime"), "deadbeefdeadbeef", evil_session
    ).name
    check(
        "session_value_path_safe: marker filename has no '/' or '..'",
        "/" not in evil_marker and ".." not in evil_marker,
        f"marker={evil_marker!r}",
    )
    # Discriminator: a stub returning the raw session id ("../evil") would
    # put "../evil" in the marker PATH. Because "/" is a path separator, the
    # raw marker's PARENT would NOT be the runtime dir (the marker lands in a
    # weird subdir, not directly in runtime) - that is the escape. Pin that
    # the real impl's marker PARENT is the runtime dir, and a raw stub's is
    # NOT.
    runtime = Path("/tmp/runtime-sanitize")
    real_marker = _marker_path(runtime, "deadbeefdeadbeef", evil_session)
    raw_marker_path = _marker_path(runtime, "deadbeefdeadbeef", "../evil")
    check(
        "session_value_path_safe: real marker PARENT == runtime dir",
        real_marker.parent == runtime,
        f"real_parent={real_marker.parent} runtime={runtime}",
    )
    check(
        "session_value_path_safe: raw '../evil' stub marker PARENT != runtime (discriminator)",
        raw_marker_path.parent != runtime,
        f"raw_parent={raw_marker_path.parent} (a stub returning raw '../evil' would not land the marker in runtime)",
    )

    # ------------------------------------------------------------------ #
    # plans_dir_resolved_from_subdir (M3/r9; r10-M6 EQUALS, not "not None"):
    # pins the REAL contract (the plan's "walks UP" phrasing is looser than
    # the implementation; resolve_plans_dir reads <start_dir>/.ai-playbook/
    # facts.md DIRECTLY and does NOT walk up - by design, see facts_paths
    # resolve_toml_key + skill_gate classify_path Arm 2). The cross-subdir
    # GATING guarantee is delivered by classify_path's DEFAULT-suffix fallback
    # on the TARGET's realpath (Arm 2), NOT by a plans_dir walk-up. So this
    # arm pins: (a) resolve_plans_dir(repo_root) EQUALS the facts value
    # byte-for-byte; (b) a NON-default plans_dir at repo root IS returned
    # from the repo root; (c) the GATE fired from a SUBDIR (no facts file
    # there -> plans_dir None) STILL classifies a docs/plans/foo.md target as
    # gated via the default-suffix fallback - the actual cross-subdir
    # guarantee a default-returning stub would also gate here, so the
    # discriminator is arm (b): a stub ignoring the facts NON-default value
    # would NOT return "my-plans".
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        # Repo facts with a NON-default plans_dir at the repo root. Use an
        # ABSOLUTE path because resolve_toml_key resolves a relative value
        # against the PROCESS CWD (not the facts file location); real facts
        # files use absolute or ~/-relative values, so this is the realistic
        # fixture.
        (td_path / ".ai-playbook").mkdir()
        non_default_abs = td_path / "docs" / "my-plans"
        non_default_abs.mkdir(parents=True, exist_ok=True)
        facts_body = (
            "```toml\n"
            f'plans_dir = "{non_default_abs}"\n'
            "```\n"
        )
        (td_path / ".ai-playbook" / "facts.md").write_text(
            facts_body, encoding="utf-8"
        )
        subdir = td_path / "deep" / "subdir"
        subdir.mkdir(parents=True)
        # (a) resolve_plans_dir at the REPO ROOT EQUALS the facts value.
        resolved_root = facts_paths.resolve_plans_dir(td_path)
        expected = non_default_abs.resolve()
        check(
            "plans_dir_resolved_from_subdir: resolve_plans_dir(root) == facts plans_dir",
            resolved_root is not None and resolved_root == expected,
            f"resolved_root={resolved_root} expected={expected}",
        )
        # (b) NON-default value returned (discriminator: a default-returning
        # stub would say "plans", not "my-plans").
        check(
            "plans_dir_resolved_from_subdir: NON-default plans_dir returned from root",
            resolved_root is not None and resolved_root.name == "my-plans",
            f"resolved_root={resolved_root} (a default-returning stub would say 'plans')",
        )
        # (c) resolve_plans_dir from a SUBDIR returns None (NO walk-up, by
        # design) - documents the carve-out that the cross-subdir guarantee
        # is NOT a plans_dir walk-up.
        resolved_sub = facts_paths.resolve_plans_dir(subdir)
        check(
            "plans_dir_resolved_from_subdir: subdir has no facts -> None (NO walk-up by design)",
            resolved_sub is None,
            f"resolved_sub={resolved_sub} (resolve_plans_dir reads <start_dir>/.ai-playbook directly)",
        )
        # (d) The GATE fired from the subdir STILL classifies a docs/plans
        # target as gated via classify_path's default-suffix fallback (Arm 2
        # on the target realpath) - the ACTUAL cross-subdir guarantee.
        (td_path / "docs" / "plans").mkdir(parents=True)
        target = str(td_path / "docs" / "plans" / "sub.md")
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        allow, reason = run_consult(
            target,
            start_dir=subdir,
            home_dir=home_dir,
            session_id=None,
            runtime_dir=runtime_dir,
        )
        check(
            "plans_dir_resolved_from_subdir: subdir gate STILL classifies docs/plans target (Arm 2 fallback)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # distinct_cursor_session_components: two distinct raw session channel
    # values (as supplied by adapters after session_channel subprocess)
    # produce two distinct _derive_session_component hashes so marker
    # filenames do not alias across Cursor composer tabs.
    # ------------------------------------------------------------------ #
    cursor_a = _derive_session_component("cursor-tab-alpha")
    cursor_b = _derive_session_component("cursor-tab-beta")
    check(
        "distinct_cursor_session_components: two raw ids -> distinct session hashes",
        cursor_a != cursor_b
        and cursor_a != NO_SESSION_KEY
        and cursor_b != NO_SESSION_KEY,
        f"a={cursor_a!r} b={cursor_b!r}",
    )

    # ------------------------------------------------------------------ #
    # block_learn_without_marker: project lessons corpus, no marker -> BLOCK.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "maintenance").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(td_path / "docs" / "maintenance" / "development_lessons.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-learn-A",
            runtime_dir=runtime_dir,
        )
        check(
            "block_learn_without_marker: BLOCK (no learn marker)",
            not allow,
            f"allow={allow} reason={reason!r}",
        )
        check(
            "block_learn_without_marker: exact learn deny message",
            reason == LEARN_BLOCK_MESSAGE,
            repr(reason),
        )

    # ------------------------------------------------------------------ #
    # allow_learn_with_fresh_marker: fresh learn.*.marker -> ALLOW.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "maintenance").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-learn-B",
            runtime_dir=runtime_dir,
            mtime_offset=0,
            marker_prefix="learn",
        )
        target = str(td_path / "docs" / "maintenance" / "development_lessons.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-learn-B",
            runtime_dir=runtime_dir,
        )
        check(
            "allow_learn_with_fresh_marker: ALLOW (fresh learn marker)",
            allow,
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # plans_class_unchanged: registry refactor preserves plans allow/block bytes.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        (td_path / "docs" / "plans").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        plan_target = str(td_path / "docs" / "plans" / "unchanged.md")
        other_target = str(td_path / "README.md")
        (td_path / "README.md").write_text("ok", encoding="utf-8")
        allow_block, reason_block = run_consult(
            plan_target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-plans-unchanged",
            runtime_dir=runtime_dir,
        )
        check(
            "plans_class_unchanged: plan path BLOCK without marker",
            not allow_block and reason_block == BLOCK_MESSAGE,
            f"allow={allow_block} reason={reason_block!r}",
        )
        allow_other, reason_other = run_consult(
            other_target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-plans-unchanged",
            runtime_dir=runtime_dir,
        )
        check(
            "plans_class_unchanged: non-plan path ALLOW",
            allow_other and reason_other == "",
            f"allow={allow_other} reason={reason_other!r}",
        )
        write_marker_at(
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-plans-unchanged",
            runtime_dir=runtime_dir,
            mtime_offset=0,
            marker_prefix=MARKER_PREFIX,
        )
        allow_fresh, reason_fresh = run_consult(
            plan_target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-plans-unchanged",
            runtime_dir=runtime_dir,
        )
        check(
            "plans_class_unchanged: plan path ALLOW with fresh plans marker",
            allow_fresh and reason_fresh == "",
            f"allow={allow_fresh} reason={reason_fresh!r}",
        )

    # ------------------------------------------------------------------ #
    # learn_path_non_lessons: other docs/maintenance paths NOT gated.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        maint = td_path / "docs" / "maintenance"
        maint.mkdir(parents=True)
        (maint / "best-practices.md").write_text("bp", encoding="utf-8")
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(maint / "best-practices.md")
        allow, reason = run_consult(
            target,
            start_dir=td_path,
            home_dir=home_dir,
            session_id="sess-learn-non",
            runtime_dir=runtime_dir,
        )
        check(
            "learn_path_non_lessons: docs/maintenance/best-practices.md ALLOW",
            allow and reason == "",
            f"allow={allow} reason={reason!r}",
        )

    # ------------------------------------------------------------------ #
    # learn_cross_tree_absolute_target: worktree cwd, absolute main-repo
    # development_lessons.md -> BLOCK without marker; ALLOW with learn marker.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        main_repo = td_path / "main"
        worktree = td_path / "worktree"
        make_git_repo(main_repo)
        make_git_repo(worktree)
        (main_repo / "docs" / "maintenance").mkdir(parents=True)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        target = str(main_repo / "docs" / "maintenance" / "development_lessons.md")
        allow, reason = run_consult(
            target,
            start_dir=worktree,
            home_dir=home_dir,
            session_id="sess-learn-cross",
            runtime_dir=runtime_dir,
        )
        check(
            "learn_cross_tree_absolute_target: BLOCK without learn marker",
            not allow and reason == LEARN_BLOCK_MESSAGE,
            f"allow={allow} reason={reason!r}",
        )
        write_marker_at(
            start_dir=worktree,
            home_dir=home_dir,
            session_id="sess-learn-cross",
            runtime_dir=runtime_dir,
            mtime_offset=0,
            marker_prefix="learn",
        )
        allow2, reason2 = run_consult(
            target,
            start_dir=worktree,
            home_dir=home_dir,
            session_id="sess-learn-cross",
            runtime_dir=runtime_dir,
        )
        check(
            "learn_cross_tree_absolute_target: ALLOW with fresh learn marker",
            allow2 and reason2 == "",
            f"allow={allow2} reason={reason2!r}",
        )

    # ------------------------------------------------------------------ #
    # write_marker_learn_cli: --write-marker learn creates learn.*.marker.
    # Uses subprocess so DEFAULT_RUNTIME_DIR resolves under isolated HOME
    # (module-level Path.home() is fixed at import time).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        make_git_repo(td_path)
        home_dir = td_path / "home"
        home_dir.mkdir()
        runtime_dir = home_dir / ".ai-playbook" / "runtime" / "skill-invoked"
        import subprocess as _sp

        core = Path(__file__).resolve()
        env = dict(os.environ)
        env["HOME"] = str(home_dir)
        proc = _sp.run(
            [
                sys.executable,
                str(core),
                "--write-marker",
                "learn",
                "--session-id",
                "sess-learn-cli",
                "--cwd",
                str(td_path),
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        with isolated_home(home_dir):
            project = resolve_project_key(td_path)
            session = _derive_session_component("sess-learn-cli")
            marker = _marker_path(
                runtime_dir, project, session, marker_prefix="learn"
            )
        check(
            "write_marker_learn_cli: exit 0",
            proc.returncode == 0,
            f"rc={proc.returncode} stderr={proc.stderr!r}",
        )
        check(
            "write_marker_learn_cli: learn.<project>.<session>.marker exists",
            marker.exists(),
            str(marker),
        )
        check(
            "write_marker_learn_cli: filename starts with learn.",
            marker.name.startswith("learn."),
            marker.name,
        )

    # ------------------------------------------------------------------ #
    # Supplementary note: #derive_session_channel_env_var pins the
    # session_channel.py LEAF (run via `session_channel.py --selftest`); the
    # core depends on it only as OPAQUE subprocess data, so that arm lives in
    # the leaf, not here. The core's OWN session sanitization is pinned by
    # #session_value_path_safe above.
    # ------------------------------------------------------------------ #

    print()
    if filter_name is not None and all_ok:
        print(f"ALL PASS (filter: {filter_name})")
    elif all_ok:
        print("ALL PASS")
    else:
        print("SOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
