#!/usr/bin/env python3
"""Fail-open per-invocation wall-time telemetry writer (SRP leaf).

Plan: docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md. One
JSONL line per script invocation into ``invocation-costs.jsonl`` inside the
facts-resolved metrics home, beside the landing-cost family. The writer is
read-only forever: it NEVER raises, NEVER writes to the caller's stdout or
stderr, and its boolean return is the only failure signal, so a broken or
missing telemetry home can never gate a lane.

Line schema (keys emitted sorted, mirroring the landing-cost writer):
``script`` (basename), ``invocation_kind``, ``wall_ms`` (number, at least
0), ``lane_class``, ``worker``, ``recorded_at`` (UTC ISO-8601), plus a
``note`` field naming an absent field's reason (the landing-cost family's
absence-note precedent). ``lane_class``/``worker`` stay null at every site
of the landing plan: no session-to-lane source exists yet.

Append discipline: the target opens once with ``O_APPEND`` and the complete
line leaves in ONE ``os.write`` (no read-modify-write, no temp-file
rename), so parallel invocations cannot interleave mid-line. A truncated or
corrupt trailing line gets its separating newline PREFIXED into that same
single write payload (last-byte check via ``os.pread``), so the corrupt
bytes are never rewritten and the file gains exactly one new parseable
line. The sub-4096-byte line keeps the append atomic per POSIX
``O_APPEND`` semantics.

Home resolution (``resolve_metrics_home``): the repo root is the first
ancestor of the working directory carrying ``.ai-playbook/facts.md`` (or a
``.git`` marker), then the first ancestor of this file's own installed
location, so a script copy inside a checkout still records when the working
directory has no repo. ``metrics_dir`` parses through
``scripts/facts_paths.py`` (the repo's single TOML-fence parser) with the
``.ai-playbook/metrics`` default applied by this library when the key is
absent or the parser is (a deployed copy fails open with no line).
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover - deployed-copy degradation
    facts_paths = None  # type: ignore

# The JSONL home this plan adds: a sibling of landing-costs.jsonl.
INVOCATION_COSTS_FILENAME = "invocation-costs.jsonl"
# The metrics home default, applied by this library when the facts key is
# absent (the same default the landing-cost writer applies).
DEFAULT_METRICS_DIR = ".ai-playbook/metrics"

# Named absence reasons (the landing-cost family's named-note precedent).
_LANE_ABSENT_NOTE = "lane_class absent: no session-to-lane source at this site"
_WORKER_ABSENT_NOTE = "worker absent: no dispatch context at this site"

# Strictly-increasing stamp guard: raw wall clocks tick coarsely enough
# (about one microsecond here) that two consecutive reads can land on the
# same tick, so start_stamp guarantees each stamp differs from the one it
# returned before, bumping by one tick at most. The bump moves a start
# stamp LATER, so elapsed values stay conservative (never inflated).
_stamp_lock = threading.Lock()
_last_stamp = 0.0


def start_stamp() -> float:
    """The entry-side wall-clock record: fractional epoch seconds.

    Sub-second resolution is the precision contract (the unit suite pins a
    fractional value and that two consecutive stamps differ).
    """
    global _last_stamp
    with _stamp_lock:
        stamp = time.time()
        if stamp <= _last_stamp:
            stamp = _last_stamp + 1e-6
        _last_stamp = stamp
        return stamp


def elapsed_ms(start: float) -> float:
    """Wall milliseconds since ``start_stamp()``, clamped at 0."""
    return max(0.0, (time.time() - start) * 1000.0)


def _first_anchored_dir(start: Path) -> Path | None:
    """First ancestor of ``start`` carrying a repo-root marker."""
    current = start
    while True:
        if (current / ".ai-playbook" / "facts.md").is_file():
            return current
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def resolve_repo_root() -> Path | None:
    """The repo root anchoring facts resolution: the working directory's
    root first, then the walk up from this file's own installed location
    (the not-inside-a-repo working directory arm)."""
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        found = _first_anchored_dir(start)
        if found is not None:
            return found
    return None


def resolve_metrics_home() -> Path | None:
    """The facts-resolved metrics home, or ``None`` when no repo root is
    resolvable (the caller fails open with no line)."""
    root = resolve_repo_root()
    if root is None:
        return None
    raw = None
    if facts_paths is not None:
        raw = facts_paths.resolve_toml_key_raw(root, "metrics_dir")
    if raw is None:
        raw = DEFAULT_METRICS_DIR
    resolved = Path(raw).expanduser()
    if not resolved.is_absolute():
        resolved = root / resolved
    return resolved


def record_invocation(
    script: str,
    invocation_kind: str,
    wall_ms: float,
    lane_class: str | None = None,
    worker: bool | None = None,
    home: str | Path | None = None,
) -> bool:
    """Append ONE invocation-costs JSONL line; return success as a bool.

    Fail-open contract: every failure mode (unresolvable home, unwritable
    home, non-serializable input) returns ``False`` without raising and
    without touching the caller's exit status, stdout, or stderr.

    Args:
      script: the invoking script's path; only its basename is recorded.
      invocation_kind: the declared integration label (pins-suite,
        review-validation, readiness-gate, or closeout-battery).
      wall_ms: the self-timed wall milliseconds (clamped at 0).
      lane_class: authoring, exec, review-carrier, or unknown (null).
      worker: dispatched-subagent flag (true), in-session (false), or
        unknown (null).
      home: metrics-home override for tests; resolution is skipped when
        given.
    """
    try:
        if home is not None:
            metrics_home = Path(home).expanduser()
        else:
            resolved = resolve_metrics_home()
            if resolved is None:
                return False
            metrics_home = resolved
        entry = {
            "script": Path(str(script)).name,
            "invocation_kind": str(invocation_kind),
            "wall_ms": max(0.0, float(wall_ms)),
            "lane_class": lane_class,
            "worker": worker,
            "recorded_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
        }
        notes = []
        if lane_class is None:
            notes.append(_LANE_ABSENT_NOTE)
        if worker is None:
            notes.append(_WORKER_ABSENT_NOTE)
        if notes:
            entry["note"] = "; ".join(notes)
        payload = (json.dumps(entry, sort_keys=True) + "\n").encode("utf-8")
        # Home created on first write; an unwritable home raises here and
        # degrades to the single fail-open False below.
        os.makedirs(metrics_home, exist_ok=True)
        fd = os.open(
            metrics_home / INVOCATION_COSTS_FILENAME,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            prefix = b""
            try:
                # Last-byte check on a SEPARATE read-only descriptor (pread
                # refuses a write-only fd): a torn trailing line gets its
                # separating newline prefixed into the SAME single write
                # payload; the corrupt bytes are never read back or
                # rewritten. A concurrent append slipping in between the
                # check and the write can only add an empty line, which the
                # parseability witnesses skip.
                size = os.path.getsize(metrics_home / INVOCATION_COSTS_FILENAME)
                if size > 0:
                    read_fd = os.open(
                        metrics_home / INVOCATION_COSTS_FILENAME, os.O_RDONLY
                    )
                    try:
                        if os.pread(read_fd, 1, size - 1) != b"\n":
                            prefix = b"\n"
                    finally:
                        os.close(read_fd)
            except OSError:
                prefix = b""
            os.write(fd, prefix + payload)
        finally:
            os.close(fd)
        return True
    except Exception:
        # Fail-open: the writer's own failure never propagates.
        return False
