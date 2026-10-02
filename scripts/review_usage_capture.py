#!/usr/bin/env python3
"""Capture provider token usage for a review round from the runtime store.

Read-only. Adapter precedence is zcode-first: the zcode-sqlite adapter
(``~/.zcode/cli/db/db.sqlite``) is tried first and codex-rollout is the
fallback. KNOWN AMBIGUITY: the fallback fires both when the zcode store
has no data AND when it errored (lock/corrupt), so a transient zcode
failure re-attributes a round to the codex store; each adapter prints a
one-line stderr diagnostic from its own exception path so real store
failures are visible. Capture is fail-open: every adapter error path
returns ``None``; capture never raises into the sidecar-writing flow and
never estimates values. Capture requires a git work tree: the repo
	anchor is resolved from ``git rev-parse --show-toplevel`` from the
	caller's cwd, and a non-git cwd yields no record.

Window and grain semantics: interval attribution is PRIMARY when the
review-run identity is passed (``mint`` mints it at round start; the
identity invocation joins usage rows whose ``completed_at`` falls in
``(review_started_at_ms, captured_at_ms]`` for the repo anchor's root
sessions, over turn-grain ``turn_usage`` rows preferred with a
missing-table-only fallback to ``model_usage`` attempt grain). A record
is attributable only when exactly one root session contributed; the
model-attempt fallback is never attributable (its grain double-counts
``attempt_index`` retries). The 6-hour look-back window survives as the
mint's candidate-discovery bound and as the legacy fallback for the bare
``--json`` invocation and the codex-rollout adapter (whose cumulative
per-file counters cannot be sliced into intervals without estimation,
which the contract prohibits). Legacy accepted limitations of the
window path: rows/files are counted
when they complete (sqlite) or were last touched (rollout mtime) inside the
6-hour look-back window ending at capture time, but cumulative counters
are SESSION- or FILE-lifetime totals, so long-lived sessions over-attribute
tokens accrued before the window (zcode session-grain over-attribution).
Codex rollout files are grouped on ``session_meta.session_id`` (worker
rollouts name the parent thread); each file's counters are that thread's
own lifetime usage starting at zero, so a group's totals are the SUM of
each file's last cumulative ``token_count`` totals. Rollout formats whose
``session_meta`` carries no ``payload.session_id`` fall back to the file
uuid, so root collapse degrades for them (worker files surface as
distinct sessions); mitigated by the 6-hour window.

Selftest pattern follows the sibling scripts (``--selftest`` flag); dotted
selftest names match the plan's checkbox ids.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

ADAPTER_NAME = "zcode-sqlite"
CODEX_ADAPTER_NAME = "codex-rollout"
USAGE_WINDOW_MS = 6 * 60 * 60 * 1000
BUSY_TIMEOUT_MS = 500
SESSION_ID_PREFIX_LEN = 12

TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "computed_total_tokens",
)

_KIND_BY_QUERY_SOURCE = {
    "main_turn": "main",
    "subagent": "subagent",
}

# Review-run identity: minted by the ``mint`` subcommand (uuid4 hex),
# validated on the identity invocation; an invalid value is treated as
# absent (the window-legacy path) with a stderr diagnostic.
_RUN_ID_RE = re.compile(r"^[0-9a-f]{32}$")

_SCHEMA_SESSIONS = """
CREATE TABLE session (
    id TEXT PRIMARY KEY,
    directory TEXT,
    parent_id TEXT
)
"""
_SCHEMA_MODEL_USAGE = """
CREATE TABLE model_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    reasoning_tokens INTEGER,
    cache_creation_input_tokens INTEGER,
    cache_read_input_tokens INTEGER,
    computed_total_tokens INTEGER,
    provider_id TEXT,
    model_id TEXT,
    agent TEXT,
    query_source TEXT,
    status TEXT,
    started_at INTEGER,
    completed_at INTEGER
)
"""

# Probed live shape 2026-10-03: turn grain, same six token fields, NO
# query_source and NO agent column (so turn-grain records bucket all rows
# under "other").
_SCHEMA_TURN_USAGE = """
CREATE TABLE turn_usage (
    session_id TEXT,
    turn_id TEXT,
    status TEXT,
    started_at INTEGER,
    completed_at INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    reasoning_tokens INTEGER,
    cache_creation_input_tokens INTEGER,
    cache_read_input_tokens INTEGER,
    computed_total_tokens INTEGER
)
"""


# --------------------------------------------------------------------------- #
# Capture (zcode-sqlite adapter).
# --------------------------------------------------------------------------- #


def _resolve_repo_anchor(
    cwd: Path, allow_cwd_fallback: bool = False
) -> Path | None:
    """Realpath of ``git rev-parse --show-toplevel`` from ``cwd``.

    Production-strict (N3): when git is unavailable or the directory is
    not a work tree, return ``None`` — a bare cwd anchor (run from ``~``)
    would match every session under home. Selftests opt in to the cwd
    fallback explicitly via ``allow_cwd_fallback=True`` to stay hermetic
    against non-git fixture dirs.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        anchor = Path(os.path.realpath(out.stdout.strip()))
    except Exception:  # noqa: BLE001
        if not allow_cwd_fallback:
            return None
        try:
            anchor = Path(os.path.realpath(str(cwd)))
        except Exception:  # noqa: BLE001
            return None
    if anchor == anchor.parent:
        return None  # degenerate "/" anchor would match every session
    return anchor


def _directory_matches(
    directory: str, anchor: Path, cache: dict[str, Path] | None = None
) -> bool:
    """True when ``directory`` realpath-resolves to the anchor or inside it.

    Never a bare ``startswith`` prefix match. ``cache`` memoizes the
    realpath per distinct directory string (the zcode row loop sees the
    same directory string many times; one syscall per distinct string).
    """
    try:
        if cache is not None and directory in cache:
            real = cache[directory]
        else:
            real = Path(os.path.realpath(directory))
            if cache is not None:
                cache[directory] = real
        return real == anchor or anchor in real.parents
    except Exception:  # noqa: BLE001
        return False


def _root_session_id(session_id: str, parents: dict[str, str]) -> str:
    """Walk ``session.parent_id`` links to the top (root session).

    N2: a corrupt parent cycle (A->B->A) would otherwise collapse
    asymmetrically (entry at A returns A, entry at B returns B) and
    surface a spurious ambiguous union. N1 (r4): on cycle detection the
    walk collapses deterministically to the smallest id among the CYCLE
    nodes only — the suffix of the walked path starting at the current
    node's first occurrence — so any entry into the same strongly
    connected component yields the same root; a non-cycle tail leading
    into the cycle (tail->A->B->A) collapses to the cycle's min, not the
    tail's id.
    """
    path: list[str] = []
    index: dict[str, int] = {}
    current = session_id
    while current in parents and current not in index:
        index[current] = len(path)
        path.append(current)
        current = parents[current]
    if current in index:
        return min(path[index[current]:])  # cycle nodes only
    return current


def _empty_bucket() -> dict[str, int]:
    return {field: 0 for field in TOKEN_FIELDS}


def _add_row(bucket: dict[str, int], row: dict[str, Any]) -> None:
    for field in TOKEN_FIELDS:
        bucket[field] += int(row.get(field) or 0)


def _abbreviate_home_str(s: str, home: Path) -> str:
    """String with EVERY occurrence of the ``home`` path ``~``-abbreviated.

    Rationale (B2 hygiene, N2 r4): paths under the runtime home
    (``~/.zcode/...``, ``~/.codex/...``) and home paths embedded mid-text
    in exception messages (``[Errno 2] ...: '<home>/...'``) are emitted in
    tilde form so no expanded absolute home path reaches a sidecar, stderr
    diagnostics, or the pushed docs branch; strings outside ``home`` pass
    through unchanged. Plain textual replacement on the ``home`` string
    (no realpath): inputs are home-derived store paths or diagnostics
    built from the same ``home`` prefix.
    """
    return s.replace(str(home), "~")


def _sanitize_exc(exc: BaseException, home: Path) -> str:
    """Diagnostic-safe exception text (N4): ``~``-abbreviated, capped ~200."""
    return _abbreviate_home_str(f"{type(exc).__name__}: {exc}", home)[:200]


def _build_record(
    adapter: str,
    db_display: str,
    session_ids: list[str],
    now: int,
    window_start: int,
    totals: dict[str, int],
    by_agent_kind: dict[str, dict[str, int]],
) -> dict:
    """Shared record/provenance builder used by both adapters (N9)."""
    return {
        "adapter": adapter,
        "provenance": {
            "db": db_display,
            "session_ids": [
                sid[:SESSION_ID_PREFIX_LEN] for sid in session_ids
            ],
            "ambiguous": len(session_ids) > 1,
            "window_started_at_ms": window_start,
            "window_ended_at_ms": now,
            # Derived from the injected ``now`` (hermetic under fixtures),
            # not from wall-clock time.time().
            "captured_at_ms": now,
            "estimated": False,
        },
        "totals": totals,
        "by_agent_kind": by_agent_kind,
    }


def _capture_zcode_sqlite(
    home_path: Path,
    anchor: Path,
    now: int,
    window_start: int,
    busy_timeout_ms: int,
) -> dict | None:
    try:
        db_path = home_path / ".zcode" / "cli" / "db" / "db.sqlite"
        if not db_path.is_file():
            return None

        conn = sqlite3.connect(
            # N11: quote the path so '?'/'#' in a home path cannot
            # misparse as URI query/fragment delimiters.
            f"file:{urllib.parse.quote(str(db_path))}?mode=ro",
            uri=True,
            timeout=busy_timeout_ms / 1000.0,
        )
        try:
            conn.row_factory = sqlite3.Row
            session_rows = conn.execute(
                "SELECT id, directory, parent_id FROM session"
            ).fetchall()
            parents = {
                row["id"]: row["parent_id"]
                for row in session_rows
                if row["parent_id"]
            }
            directories = {
                row["id"]: row["directory"] for row in session_rows
            }
            usage_rows = conn.execute(
                "SELECT * FROM model_usage "
                "WHERE status = 'completed' AND completed_at IS NOT NULL "
                "AND completed_at >= ? AND completed_at <= ?",
                (window_start, now),
            ).fetchall()
        finally:
            conn.close()

        candidates: dict[str, dict[str, dict[str, int]]] = {}
        realpath_cache: dict[str, Path] = {}  # N16: one realpath per distinct directory string
        for row in usage_rows:
            session_id = row["session_id"]
            directory = directories.get(session_id)
            if directory is None or not _directory_matches(
                directory, anchor, realpath_cache
            ):
                continue
            root = _root_session_id(session_id, parents)
            kind = _KIND_BY_QUERY_SOURCE.get(
                row["query_source"] or "", "other"
            )
            per_root = candidates.setdefault(root, {})
            bucket = per_root.setdefault(kind, _empty_bucket())
            _add_row(bucket, dict(row))

        if not candidates:
            return None

        totals = _empty_bucket()
        by_kind: dict[str, dict[str, int]] = {}
        for per_root in candidates.values():
            for kind, bucket in per_root.items():
                target = by_kind.setdefault(kind, _empty_bucket())
                for field in TOKEN_FIELDS:
                    target[field] += bucket[field]
                    totals[field] += bucket[field]

        session_ids = sorted(candidates.keys())
        return _build_record(
            ADAPTER_NAME,
            _abbreviate_home_str(str(db_path), home_path),
            session_ids,
            now,
            window_start,
            totals,
            by_kind,
        )
    except Exception as exc:  # noqa: BLE001  fail-open: never raise to the caller
        # N2: no-data (None above) and error are distinct; emit one stderr
        # diagnostic here so a real store failure is visible before the
        # codex fallback runs.
        try:
            sys.stderr.write(
                f"review_usage_capture: {ADAPTER_NAME} capture failed: "
                f"{_sanitize_exc(exc, home_path)}\n"
            )
        except Exception:  # noqa: BLE001
            pass
        return None


# --------------------------------------------------------------------------- #
# Identity minting and validation.
# --------------------------------------------------------------------------- #


def mint_identity(
    home: str | Path | None = None,
    cwd: str | Path | None = None,
    now_ms: int | None = None,
    allow_cwd_fallback: bool = False,
) -> dict:
    """Mint a review-run identity (never raises, never reads token counts).

    ALWAYS prints (returns) ``{"review_run_id", "minted_at_ms",
    "candidate_root_session_ids"}``. The identity itself needs no store;
    the candidate list is best-effort discovery reusing the window-plus-
    directory match and the root collapse walk over completed sessions in
    the 6-hour look-back window, truncated to ``SESSION_ID_PREFIX_LEN``,
    and may be empty.
    """
    home_path = Path(home) if home is not None else Path.home()
    cwd_path = Path(cwd) if cwd is not None else Path.cwd()
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    candidates: list[str] = []
    try:
        anchor = _resolve_repo_anchor(cwd_path, allow_cwd_fallback)
        db_path = home_path / ".zcode" / "cli" / "db" / "db.sqlite"
        if anchor is not None and db_path.is_file():
            conn = sqlite3.connect(
                f"file:{urllib.parse.quote(str(db_path))}?mode=ro",
                uri=True,
                timeout=BUSY_TIMEOUT_MS / 1000.0,
            )
            try:
                conn.row_factory = sqlite3.Row
                session_rows = conn.execute(
                    "SELECT id, directory, parent_id FROM session"
                ).fetchall()
                parents = {
                    row["id"]: row["parent_id"]
                    for row in session_rows
                    if row["parent_id"]
                }
                directories = {
                    row["id"]: row["directory"] for row in session_rows
                }
                # Candidate discovery only: distinct session ids, no
                # token counts are read.
                active = conn.execute(
                    "SELECT DISTINCT session_id FROM model_usage "
                    "WHERE status = 'completed' AND completed_at IS NOT NULL "
                    "AND completed_at >= ? AND completed_at <= ?",
                    (now - USAGE_WINDOW_MS, now),
                ).fetchall()
            finally:
                conn.close()
            roots: set[str] = set()
            cache: dict[str, Path] = {}
            for row in active:
                sid = row["session_id"]
                directory = directories.get(sid)
                if directory is None or not _directory_matches(
                    directory, anchor, cache
                ):
                    continue
                roots.add(_root_session_id(sid, parents))
            candidates = sorted(roots)
    except Exception:  # noqa: BLE001  best-effort discovery, never raises
        candidates = []
    return {
        "review_run_id": uuid.uuid4().hex,
        "minted_at_ms": now,
        "candidate_root_session_ids": [
            c[:SESSION_ID_PREFIX_LEN] for c in candidates
        ],
    }


def _validated_identity(
    review_run_id: str | None,
    review_started_at_ms: int | None,
    home_path: Path,
) -> tuple[str, int] | None:
    """Validate the identity pair; ``None`` means treat as absent.

    A ``review_run_id`` not matching ``^[0-9a-f]{32}$`` or a non-positive
    start is treated as absent (the window-legacy path) with a
    tilde-abbreviated stderr diagnostic. Arity (both-or-neither) is the
    caller's argparse duty.
    """
    if review_run_id is None and review_started_at_ms is None:
        return None
    ok = (
        isinstance(review_run_id, str)
        and _RUN_ID_RE.fullmatch(review_run_id) is not None
        and isinstance(review_started_at_ms, int)
        and not isinstance(review_started_at_ms, bool)
        and review_started_at_ms > 0
    )
    if not ok:
        try:
            diag = _abbreviate_home_str(
                "review_usage_capture: invalid review-run identity "
                f"(run_id={review_run_id!r}, "
                f"review_started_at_ms={review_started_at_ms!r}); "
                "treating as absent (window-legacy, non-attributable)\n",
                home_path,
            )
            sys.stderr.write(diag[:300])
        except Exception:  # noqa: BLE001
            pass
        return None
    return (review_run_id, review_started_at_ms)


# --------------------------------------------------------------------------- #
# Interval capture (zcode-sqlite adapter, identity invocation).
# --------------------------------------------------------------------------- #


def _capture_zcode_interval(
    home_path: Path,
    anchor: Path,
    review_run_id: str,
    review_started_at_ms: int,
    now: int,
    busy_timeout_ms: int,
) -> dict | None:
    """Attribute usage by INTERVAL over turn-grain rows (fail-open).

    Prefers ``turn_usage`` (turn grain, ``source_grain: "turn"``, all
    rows bucketed under "other" because the table carries no
    ``query_source``); falls back to ``model_usage`` (attempt grain,
    ``source_grain: "model-attempt"``, query_source bucketing kept) ONLY
    on the missing-table condition (sqlite_master probe, plus the "no
    such table" error-substring arm); any other OperationalError (locked,
    no such column, disk I/O) takes the fail-open None path. A present-
    but-empty result for the anchor is an honest empty (returns None),
    never a fallback trigger. Attributable only when exactly one root
    session contributed and no truncated-id collision occurred.
    """
    try:
        db_path = home_path / ".zcode" / "cli" / "db" / "db.sqlite"
        if not db_path.is_file():
            return None

        conn = sqlite3.connect(
            f"file:{urllib.parse.quote(str(db_path))}?mode=ro",
            uri=True,
            timeout=busy_timeout_ms / 1000.0,
        )
        try:
            conn.row_factory = sqlite3.Row
            session_rows = conn.execute(
                "SELECT id, directory, parent_id FROM session"
            ).fetchall()
            parents = {
                row["id"]: row["parent_id"]
                for row in session_rows
                if row["parent_id"]
            }
            directories = {
                row["id"]: row["directory"] for row in session_rows
            }
            interval = (
                review_started_at_ms,
                now,
            )
            has_turn = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' "
                "AND name = 'turn_usage'"
            ).fetchone() is not None
            if has_turn:
                rows = conn.execute(
                    "SELECT * FROM turn_usage "
                    "WHERE status = 'completed' AND completed_at IS NOT NULL "
                    "AND completed_at > ? AND completed_at <= ?",
                    interval,
                ).fetchall()
                grain = "turn"
            else:
                try:
                    rows = conn.execute(
                        "SELECT * FROM model_usage "
                        "WHERE status = 'completed' "
                        "AND completed_at IS NOT NULL "
                        "AND completed_at > ? AND completed_at <= ?",
                        interval,
                    ).fetchall()
                except sqlite3.OperationalError as exc:
                    if "no such table" in str(exc).lower():
                        return None  # no usable table at all
                    raise
                grain = "model-attempt"
        finally:
            conn.close()

        # Per-contributor (root session) subtotals over the interval.
        per_root: dict[str, dict[str, int]] = {}
        per_root_kind: dict[str, dict[str, dict[str, int]]] = {}
        cache: dict[str, Path] = {}
        for row in rows:
            session_id = row["session_id"]
            directory = directories.get(session_id)
            if directory is None or not _directory_matches(
                directory, anchor, cache
            ):
                continue
            root = _root_session_id(session_id, parents)
            bucket = per_root.setdefault(root, _empty_bucket())
            _add_row(bucket, dict(row))
            if grain == "turn":
                kind_bucket = per_root_kind.setdefault(
                    root, {}
                ).setdefault("other", _empty_bucket())
                _add_row(kind_bucket, dict(row))
            else:
                kind = _KIND_BY_QUERY_SOURCE.get(
                    row["query_source"] or "", "other"
                )
                kind_bucket = per_root_kind.setdefault(
                    root, {}
                ).setdefault(kind, _empty_bucket())
                _add_row(kind_bucket, dict(row))

        if not per_root:
            return None  # honest empty, never a fallback trigger

        # by_session: truncated keys; a 12-char prefix collision keeps the
        # record non-attributable and is flagged.
        by_session: dict[str, dict[str, int]] = {}
        roots = sorted(per_root.keys())
        collided = False
        seen_prefixes: set[str] = set()
        for root in roots:
            prefix = root[:SESSION_ID_PREFIX_LEN]
            if prefix in seen_prefixes:
                collided = True
            seen_prefixes.add(prefix)
            by_session[prefix] = dict(per_root[root])

        totals = _empty_bucket()
        by_kind: dict[str, dict[str, int]] = {}
        for root in roots:
            for field in TOKEN_FIELDS:
                totals[field] += per_root[root][field]
            for kind, bucket in per_root_kind.get(root, {}).items():
                target = by_kind.setdefault(kind, _empty_bucket())
                for field in TOKEN_FIELDS:
                    target[field] += bucket[field]

        if grain == "turn" and len(roots) == 1 and not collided:
            attribution = "interval-identity"
            attributable = True
        elif grain == "turn":
            attribution = "interval-ambiguous"
            attributable = False
        else:
            attribution = "interval-fallback"
            attributable = False

        provenance = {
            "db": _abbreviate_home_str(str(db_path), home_path),
            "session_ids": [r[:SESSION_ID_PREFIX_LEN] for r in roots],
            "ambiguous": len(roots) > 1,
            "window_started_at_ms": review_started_at_ms,
            "window_ended_at_ms": now,
            "captured_at_ms": now,
            "estimated": False,
            "attribution": attribution,
            "attributable": attributable,
            "review_run_id": review_run_id,
            "review_started_at_ms": review_started_at_ms,
            "source_grain": grain,
            "by_session": by_session,
        }
        if collided:
            provenance["by_session_collided"] = True
        return {
            "adapter": ADAPTER_NAME,
            "provenance": provenance,
            "totals": totals,
            "by_agent_kind": by_kind,
        }
    except Exception as exc:  # noqa: BLE001  fail-open, never raise
        try:
            sys.stderr.write(
                f"review_usage_capture: {ADAPTER_NAME} interval capture "
                f"failed: {_sanitize_exc(exc, home_path)}\n"
            )
        except Exception:  # noqa: BLE001
            pass
        return None


# --------------------------------------------------------------------------- #
# Capture (codex-rollout adapter).
# --------------------------------------------------------------------------- #

_ROLLOUT_FIELD_MAP = {
    "input_tokens": "input_tokens",
    "cached_input_tokens": "cache_read_input_tokens",
    "cache_write_input_tokens": "cache_creation_input_tokens",
    "output_tokens": "output_tokens",
    "reasoning_output_tokens": "reasoning_tokens",
    "total_tokens": "computed_total_tokens",
}


def _mapped_usage(usage: dict[str, Any]) -> dict[str, int]:
    bucket = _empty_bucket()
    for src, dst in _ROLLOUT_FIELD_MAP.items():
        bucket[dst] = int(usage.get(src) or 0)
    return bucket


def _capture_codex_rollout(
    home_path: Path,
    anchor: Path,
    now: int,
    window_start: int,
    include_by_session: bool = False,
) -> dict | None:
    """Usage from ``~/.codex/sessions/**/rollout-*.jsonl`` (fail-open).

    Accepted limitations (see the module docstring): the mtime pre-filter
    plus last-cumulative-``token_count``-wins attributes session-lifetime
    tokens for long-lived sessions (window-vs-lifetime granularity), and
    within a root group each rollout file's counters are that thread's own
    lifetime usage starting at zero, so group totals are the SUM of each
    file's last cumulative totals (per-file cumulative sums).
    """
    try:
        sessions_dir = home_path / ".codex" / "sessions"
        if not sessions_dir.is_dir():
            return None

        rollouts: list[Path] = []
        try:
            for path in sessions_dir.rglob("rollout-*.jsonl"):
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                if mtime * 1000.0 < window_start:
                    continue  # mtime pre-filter: not touched in the window.
                # N13: upper bound — a future mtime (clock skew, touch)
                # must not count as in-window either.
                if mtime * 1000.0 > now:
                    continue
                rollouts.append(path)
        except OSError:
            return None
        if not rollouts:
            return None

        # Group rollouts on session_meta.session_id (the parent thread id):
        # worker files record the parent id, so they collapse into the root
        # and never surface as distinct candidates.
        groups: dict[str, dict[str, int]] = {}
        for path in rollouts:
            meta_sid: str | None = None
            meta_cwd: str | None = None
            meta_decided = False  # N1: FIRST session_meta decides identity.
            # N5 (r4): cwd_ok is computed ONCE, when the first session_meta
            # decides the file's identity, and reused at the post-loop
            # accept check — at most one _directory_matches call per file.
            cwd_ok = False
            last_usage: dict[str, int] | None = None
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        try:
                            obj = json.loads(line)
                        except Exception:  # noqa: BLE001  skip bad lines
                            continue
                        if not isinstance(obj, dict):
                            continue
                        payload = obj.get("payload")
                        if not isinstance(payload, dict):
                            payload = {}
                        if obj.get("type") == "session_meta" and not meta_decided:
                            meta_decided = True
                            meta_sid = (
                                obj.get("session_id")
                                or payload.get("session_id")
                                or payload.get("id")
                            )
                            meta_cwd = obj.get("cwd") or payload.get("cwd")
                            # N9: the FIRST session_meta names a foreign-repo
                            # cwd — stop reading this file (its token_count
                            # events belong to another repo). A LATER foreign
                            # session_meta does not override the identity:
                            # usage already parsed under the matching first
                            # identity is kept (N1).
                            cwd_ok = isinstance(meta_cwd, str) and (
                                _directory_matches(meta_cwd, anchor)
                            )
                            if not cwd_ok:
                                break
                        elif (
                            obj.get("type") == "event_msg"
                            and isinstance(payload, dict)
                            and payload.get("type") == "token_count"
                        ):
                            # Real rollout shape:
                            # {"type":"event_msg","payload":{"type":
                            #  "token_count","info":{"total_token_usage":
                            #  {...}}}}. Tolerant fallbacks keep the flat
                            # legacy shapes (obj/payload .total_token_usage)
                            # parseable.
                            info = payload.get("info")
                            usage = (
                                info.get("total_token_usage")
                                if isinstance(info, dict)
                                else None
                            ) or obj.get("total_token_usage") or payload.get(
                                "total_token_usage"
                            )
                            if isinstance(usage, dict):
                                # Cumulative counters: LAST event wins.
                                last_usage = _mapped_usage(usage)
                        elif obj.get("type") == "token_count":
                            # Legacy flat shape (tolerant fallback).
                            usage = (
                                obj.get("total_token_usage")
                                or payload.get("total_token_usage")
                            )
                            if isinstance(usage, dict):
                                last_usage = _mapped_usage(usage)
            except Exception:  # noqa: BLE001  fail-open per file
                continue
            if not isinstance(meta_sid, str) or last_usage is None:
                continue
            if not cwd_ok:
                continue
            # Per-file cumulative sums (N1): each rollout file is a distinct
            # thread process whose counters start at zero, so a group's
            # totals are the SUM of each file's last cumulative totals (a
            # plain overwrite would discard sibling worker rollouts).
            group_bucket = groups.setdefault(meta_sid, _empty_bucket())
            for field in TOKEN_FIELDS:
                group_bucket[field] += last_usage[field]

        if not groups:
            return None

        totals = _empty_bucket()
        for bucket in groups.values():
            for field in TOKEN_FIELDS:
                totals[field] += bucket[field]

        session_ids = sorted(groups.keys())
        record = _build_record(
            CODEX_ADAPTER_NAME,
            _abbreviate_home_str(str(sessions_dir), home_path),
            session_ids,
            now,
            window_start,
            totals,
            {"other": dict(totals)},
        )
        if include_by_session:
            # Identity invocation: per-session subtotals (truncated keys),
            # keeping the six additive provenance fields symmetric with the
            # zcode identity record. A 12-char prefix collision merges the
            # subtotals under one key; mirror the zcode doctrine and flag
            # it so the map is never read as per-session truth.
            by_session: dict[str, dict[str, int]] = {}
            collided = False
            seen: set[str] = set()
            for sid, bucket in groups.items():
                prefix = sid[:SESSION_ID_PREFIX_LEN]
                if prefix in seen:
                    collided = True
                seen.add(prefix)
                merged = by_session.setdefault(prefix, _empty_bucket())
                for field in TOKEN_FIELDS:
                    merged[field] += bucket[field]
            record["provenance"]["by_session"] = by_session
            if collided:
                record["provenance"]["by_session_collided"] = True
        return record
    except Exception as exc:  # noqa: BLE001  fail-open: never raise to the caller
        # N2: mirror the zcode adapter — one stderr diagnostic on the
        # adapter error path; stdout contract stays "JSON record or
        # nothing" in all modes.
        try:
            sys.stderr.write(
                f"review_usage_capture: {CODEX_ADAPTER_NAME} capture failed: "
                f"{_sanitize_exc(exc, home_path)}\n"
            )
        except Exception:  # noqa: BLE001
            pass
        return None


def capture_usage(
    home: str | Path | None = None,
    cwd: str | Path | None = None,
    now_ms: int | None = None,
    busy_timeout_ms: int = BUSY_TIMEOUT_MS,
    allow_cwd_fallback: bool = False,
    review_run_id: str | None = None,
    review_started_at_ms: int | None = None,
) -> dict | None:
    """Capture the usage record for the current repo, or ``None``.

    With a validated review-run identity (both ``review_run_id`` and
    ``review_started_at_ms`` passed and shape-valid), attribution runs by
    INTERVAL over turn-grain rows (the identity invocation); the codex
    adapter on that path stays window-legacy (cumulative counters cannot
    be interval-sliced). Without an identity, the 6-hour window join runs
    unchanged (byte-compatible record shape). ``home``/``cwd`` are
    injectable so selftests can point capture at a fixture home/repo dir
    instead of the real ``~``. ``allow_cwd_fallback`` gates the non-git
    cwd anchor fallback (N3): default is production-strict (git failure
    -> ``None``); hermetic selftests that point at non-git fixture dirs
    pass ``True`` explicitly.
    """
    try:
        home_path = Path(home) if home is not None else Path.home()
        cwd_path = Path(cwd) if cwd is not None else Path.cwd()
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        window_start = now - USAGE_WINDOW_MS

        anchor = _resolve_repo_anchor(cwd_path, allow_cwd_fallback)
        if anchor is None:
            return None

        identity = _validated_identity(
            review_run_id, review_started_at_ms, home_path
        )
        if identity is not None:
            run_id, review_start = identity
            record = _capture_zcode_interval(
                home_path, anchor, run_id, review_start, now,
                busy_timeout_ms,
            )
            if record is not None:
                return record
            # Codex rollout counters are cumulative per file: interval
            # slicing would be estimation, which the contract prohibits.
            # The window-legacy record still carries the identity for
            # forensics but is never attributable.
            record = _capture_codex_rollout(
                home_path, anchor, now, window_start,
                include_by_session=True,
            )
            if record is not None:
                record["provenance"]["attribution"] = "window-legacy"
                record["provenance"]["attributable"] = False
                record["provenance"]["review_run_id"] = run_id
                record["provenance"]["review_started_at_ms"] = review_start
                record["provenance"]["source_grain"] = "rollout"
                return record
            return None

        record = _capture_zcode_sqlite(
            home_path, anchor, now, window_start, busy_timeout_ms
        )
        if record is not None:
            return record
        return _capture_codex_rollout(home_path, anchor, now, window_start)
    except Exception as exc:  # noqa: BLE001  fail-open: never raise
        # One stderr diagnostic at the outermost handler only (N3): stdout
        # contract untouched; inner per-store/per-file handlers stay quiet.
        try:
            sys.stderr.write(
                f"review_usage_capture: capture failed: "
                f"{_sanitize_exc(exc, home_path)}\n"
            )
        except Exception:  # noqa: BLE001
            pass
        return None


# --------------------------------------------------------------------------- #
# Selftests. Dotted names match the plan's checkbox ids.
# --------------------------------------------------------------------------- #

_registry: dict[str, Callable[[Callable], None]] = {}


def _test(name: str) -> Callable[[Callable], None]:
    def deco(fn: Callable) -> Callable:
        _registry[name] = fn
        return fn

    return deco


class _Fixture:
    """Fixture runtime store under a temp dir, at real ms scale."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.home = tmp / "home"
        self.repo = tmp / "repo"
        (self.home / ".zcode" / "cli" / "db").mkdir(parents=True)
        self.repo.mkdir(parents=True)
        self.db = self.home / ".zcode" / "cli" / "db" / "db.sqlite"
        self.now = 1_788_707_239_036  # measured live ms scale (2026-09-06)
        self._sessions: list[tuple[str, str, str | None]] = []
        self._rows: list[dict] = []
        self._turn_rows: list[dict] = []
        self._turn_table_forced = False

    def session(self, sid: str, *, parent: str | None = None,
                directory: Path | None = None) -> None:
        self._sessions.append(
            (sid, str(directory or self.repo), parent)
        )

    def row(self, session_id: str, *, source: str = "main_turn",
            completed_at: int | None = None, started_at: int | None = None,
            status: str = "completed", **tokens: int) -> None:
        base = {
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "computed_total_tokens": 0,
        }
        base.update(tokens)
        self._rows.append(
            {
                "session_id": session_id,
                "query_source": source,
                "status": status,
                "started_at": started_at if started_at is not None
                else self.now - 1000,
                "completed_at": completed_at if completed_at is not None
                else self.now - 500,
                **base,
            }
        )

    def turn_row(self, session_id: str, *, turn_id: str = "t1",
                 completed_at: int | None = None,
                 started_at: int | None = None,
                 status: str = "completed", **tokens: int) -> None:
        base = {
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "computed_total_tokens": 0,
        }
        base.update(tokens)
        self._turn_rows.append(
            {
                "session_id": session_id,
                "turn_id": turn_id,
                "status": status,
                "started_at": started_at if started_at is not None
                else self.now - 1000,
                "completed_at": completed_at if completed_at is not None
                else self.now - 500,
                **base,
            }
        )

    def force_turn_table(self) -> None:
        """Create the ``turn_usage`` table even with no turn rows."""
        self._turn_table_forced = True

    def drop_turn_table(self) -> None:
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("DROP TABLE turn_usage")
            conn.commit()
        finally:
            conn.close()

    def build(self) -> None:
        conn = sqlite3.connect(self.db)
        try:
            conn.execute(_SCHEMA_SESSIONS)
            conn.execute(_SCHEMA_MODEL_USAGE)
            if self._turn_rows or self._turn_table_forced:
                conn.execute(_SCHEMA_TURN_USAGE)
            conn.executemany(
                "INSERT INTO session (id, directory, parent_id) "
                "VALUES (?, ?, ?)",
                self._sessions,
            )
            conn.executemany(
                "INSERT INTO model_usage (session_id, input_tokens, "
                "output_tokens, reasoning_tokens, "
                "cache_creation_input_tokens, cache_read_input_tokens, "
                "computed_total_tokens, query_source, status, started_at, "
                "completed_at) VALUES (:session_id, :input_tokens, "
                ":output_tokens, :reasoning_tokens, "
                ":cache_creation_input_tokens, :cache_read_input_tokens, "
                ":computed_total_tokens, :query_source, :status, "
                ":started_at, :completed_at)",
                self._rows,
            )
            if self._turn_rows:
                conn.executemany(
                    "INSERT INTO turn_usage (session_id, turn_id, status, "
                    "started_at, completed_at, input_tokens, output_tokens, "
                    "reasoning_tokens, cache_creation_input_tokens, "
                    "cache_read_input_tokens, computed_total_tokens) "
                    "VALUES (:session_id, :turn_id, :status, :started_at, "
                    ":completed_at, :input_tokens, :output_tokens, "
                    ":reasoning_tokens, :cache_creation_input_tokens, "
                    ":cache_read_input_tokens, :computed_total_tokens)",
                    self._turn_rows,
                )
            conn.commit()
        finally:
            conn.close()

    def capture_identity(
        self,
        run_id: str,
        started_at: int,
        now: int | None = None,
    ) -> dict | None:
        """Identity-invocation capture with explicit window/identity args."""
        return capture_usage(
            home=self.home, cwd=self.repo,
            now_ms=self.now if now is None else now,
            allow_cwd_fallback=True,
            review_run_id=run_id,
            review_started_at_ms=started_at,
        )

    def capture(self) -> dict | None:
        # allow_cwd_fallback=True: fixture repos are not git work trees
        # (hermetic opt-in to the cwd anchor, N3).
        return capture_usage(
            home=self.home, cwd=self.repo, now_ms=self.now,
            allow_cwd_fallback=True,
        )


    # -- codex rollout fixtures ------------------------------------------- #

    def codex_rollout(
        self,
        session_id: str,
        *,
        cwd: Path | None = None,
        parent_thread_id: str | None = None,
        token_usages: tuple[dict, ...] = (),
        garbage_lines: tuple[str, ...] = (),
        mtime_s: float | None = None,
        file_tag: str = "aaaa",
        shape: str = "event_msg",
    ) -> Path:
        """Write one ``~/.codex/sessions/2026/09/06/rollout-*.jsonl`` file.

        ``shape="event_msg"`` mirrors real rollout files: token usage rides
        an ``event_msg`` envelope
        (``payload.type="token_count"``, counters in
        ``payload.info.total_token_usage``) and session identity lives
        inside the ``session_meta`` payload. ``shape="flat"`` emits the
        legacy flat ``{"type":"token_count","total_token_usage":...}``
        line as a tolerant-fallback witness.
        """
        import uuid as _uuid

        day_dir = self.home / ".codex" / "sessions" / "2026" / "09" / "06"
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / (
            f"rollout-2026-09-06T12-00-00-{file_tag}-{_uuid.uuid4().hex}.jsonl"
        )
        meta: dict[str, Any] = {
            "timestamp": "2026-09-06T12:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "id": f"rollout-2026-09-06T12-00-00-{file_tag}",
                "session_id": session_id,
                "cwd": str(cwd or self.repo),
            },
        }
        if parent_thread_id is not None:
            meta["payload"]["parent_thread_id"] = parent_thread_id
        lines: list[str] = [json.dumps(meta)]
        for usage in token_usages:
            if shape == "flat":
                token_line: dict[str, Any] = {
                    "timestamp": "2026-09-06T12:00:01.000Z",
                    "type": "token_count",
                    "total_token_usage": usage,
                }
            else:
                token_line = {
                    "timestamp": "2026-09-06T12:00:01.000Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {"total_token_usage": usage},
                    },
                }
            lines.append(json.dumps(token_line))
            if garbage_lines:
                lines.append(garbage_lines[0])
        lines.extend(garbage_lines[len(token_usages):])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        mtime = mtime_s if mtime_s is not None else self.now / 1000.0 - 60
        os.utime(path, (mtime, mtime))
        return path

    @property
    def codex_sessions_dir(self) -> Path:
        return self.home / ".codex" / "sessions"


def _tmp_dir() -> Path:
    import tempfile

    return Path(tempfile.mkdtemp(prefix="ruc-selftest-"))


@_test("review_usage_capture#selftest_single_session")
def _selftest_single_session(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123", source="main_turn",
           input_tokens=1000, output_tokens=100, computed_total_tokens=1100)
    fx.row("sess_main_abc123", source="subagent",
           input_tokens=5000, output_tokens=500, computed_total_tokens=5500)
    fx.row("sess_main_abc123", source="compact",
           input_tokens=200, output_tokens=20, computed_total_tokens=220)
    fx.build()
    rec = fx.capture()
    check("record produced", rec is not None)
    if rec is None:
        return
    check("adapter", rec["adapter"] == "zcode-sqlite")
    t = rec["totals"]
    check("totals input", t["input_tokens"] == 6200,
          f"got {t['input_tokens']}")
    check("totals output", t["output_tokens"] == 620,
          f"got {t['output_tokens']}")
    check("totals computed", t["computed_total_tokens"] == 6820,
          f"got {t['computed_total_tokens']}")
    check("totals ints", all(isinstance(v, int) for v in t.values()))
    k = rec["by_agent_kind"]
    check("main bucket", k["main"]["input_tokens"] == 1000)
    check("subagent bucket", k["subagent"]["input_tokens"] == 5000)
    check("other bucket (compact)", k["other"]["input_tokens"] == 200)
    p = rec["provenance"]
    check("db path tilde-abbreviated",
          p["db"] == "~/.zcode/cli/db/db.sqlite", f"got {p['db']}")
    check("session id truncated",
          p["session_ids"] == ["sess_main_ab"])
    check("window start ms",
          p["window_started_at_ms"] == fx.now - USAGE_WINDOW_MS)
    check("window end ms", p["window_ended_at_ms"] == fx.now)
    check("ms scale", p["window_ended_at_ms"] > 10**12)
    check("estimated false", p["estimated"] is False)
    check("not ambiguous", p["ambiguous"] is False)

    # N2 (r4) witness: home embedded MID-message (errno-style text) is
    # abbreviated too, not just a leading home prefix.
    exc_text = f"[Errno 2] No such file: '{fx.home}/nope/x.txt'"
    sanitized = _sanitize_exc(ValueError(exc_text), fx.home)
    check("mid-message home abbreviated (N2 r4)",
          str(fx.home) not in sanitized and "~/nope/x.txt" in sanitized,
          f"got {sanitized!r}")


@_test("review_usage_capture#selftest_no_db")
def _selftest_no_db(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123")
    # No build(): db file absent.
    check("no db -> None, no exception", fx.capture() is None)


@_test("review_usage_capture#selftest_missing_table")
def _selftest_missing_table(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    conn = sqlite3.connect(fx.db)
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, "
                 "directory TEXT, parent_id TEXT)")
    conn.commit()
    conn.close()
    check("missing model_usage -> None", fx.capture() is None)


@_test("review_usage_capture#selftest_empty_window")
def _selftest_empty_window(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123",
           completed_at=fx.now - USAGE_WINDOW_MS - 1,
           started_at=fx.now - USAGE_WINDOW_MS - 2000,
           input_tokens=1000)
    fx.build()
    check("empty window -> None", fx.capture() is None)


@_test("review_usage_capture#selftest_straddling_row_included")
def _selftest_straddling_row_included(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123",
           started_at=fx.now - USAGE_WINDOW_MS - 3_600_000,
           completed_at=fx.now - 1000,
           input_tokens=1000, output_tokens=10,
           computed_total_tokens=1010)
    fx.build()
    rec = fx.capture()
    check("straddling row counted", rec is not None)
    if rec is not None:
        check("straddling tokens",
              rec["totals"]["input_tokens"] == 1000)

    # N5 boundary witness: a row completing EXACTLY at the window start is
    # counted (filter is inclusive: completed_at >= window_start).
    tmp2 = _tmp_dir()
    fx2 = _Fixture(tmp2)
    fx2.session("sess_main_abc123")
    fx2.row("sess_main_abc123",
            completed_at=fx2.now - USAGE_WINDOW_MS,
            input_tokens=7, computed_total_tokens=7)
    fx2.build()
    rec2 = fx2.capture()
    check("window-start boundary row counted", rec2 is not None)
    if rec2 is not None:
        check("boundary tokens",
              rec2["totals"]["input_tokens"] == 7,
              f"got {rec2['totals']['input_tokens']}")


@_test("review_usage_capture#selftest_child_sessions_collapse")
def _selftest_child_sessions_collapse(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_xyz789")
    fx.session("sess_subagent_agent_w1", parent="sess_root_xyz789")
    fx.session("sess_subagent_agent_w2", parent="sess_root_xyz789")
    fx.row("sess_root_xyz789", source="main_turn",
           input_tokens=100, computed_total_tokens=100)
    fx.row("sess_subagent_agent_w1", source="subagent",
           input_tokens=400, computed_total_tokens=400)
    fx.row("sess_subagent_agent_w2", source="subagent",
           input_tokens=500, computed_total_tokens=500)
    fx.build()
    rec = fx.capture()
    check("single attributed record", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("root id only", p["session_ids"] == ["sess_root_xy"])
    check("not ambiguous", p["ambiguous"] is False)
    check("child rows in totals",
          rec["totals"]["input_tokens"] == 1000)
    check("child rows bucketed by query_source",
          rec["by_agent_kind"]["subagent"]["input_tokens"] == 900)
    check("main bucket from root rows",
          rec["by_agent_kind"]["main"]["input_tokens"] == 100)

    # N2 witness: corrupt parent cycle (c1->c2->c1) collapses
    # deterministically to the smallest cycle id from either entry point —
    # no spurious ambiguous union of two roots.
    tmp_c = _tmp_dir()
    fx_c = _Fixture(tmp_c)
    fx_c.session("sess_cyca1111", parent="sess_cycb2222")
    fx_c.session("sess_cycb2222", parent="sess_cyca1111")
    fx_c.row("sess_cyca1111", source="subagent",
             input_tokens=10, computed_total_tokens=10)
    fx_c.row("sess_cycb2222", source="subagent",
             input_tokens=20, computed_total_tokens=20)
    fx_c.build()
    rec_c = fx_c.capture()
    check("cycle collapses to one root", rec_c is not None)
    if rec_c is not None:
        check("cycle root deterministic (smallest id, N2)",
              rec_c["provenance"]["session_ids"] == ["sess_cyca111"],
              f"got {rec_c['provenance']['session_ids']}")
        check("cycle not ambiguous (N2)",
              rec_c["provenance"]["ambiguous"] is False)
        check("cycle rows summed",
              rec_c["totals"]["input_tokens"] == 30)

    # N1 (r4) witness: a non-cycle TAIL leading into a cycle
    # (tail -> zzza -> zzzb -> zzza) collapses to the CYCLE's min, not the
    # tail's id — the tail id is the smallest on the walked path, so the
    # pre-fix min-over-path escape is covered from both entry points.
    tmp_t = _tmp_dir()
    fx_t = _Fixture(tmp_t)
    fx_t.session("sess_aaa_tail", parent="sess_zzza1111")
    fx_t.session("sess_zzza1111", parent="sess_zzzb2222")
    fx_t.session("sess_zzzb2222", parent="sess_zzza1111")
    fx_t.row("sess_aaa_tail", source="subagent",
             input_tokens=1, computed_total_tokens=1)
    fx_t.row("sess_zzzb2222", source="subagent",
             input_tokens=2, computed_total_tokens=2)
    fx_t.build()
    rec_t = fx_t.capture()
    check("tail into cycle collapses to one root (N1 r4)",
          rec_t is not None)
    if rec_t is not None:
        check("tail collapses to the CYCLE min, not the tail id (N1 r4)",
              rec_t["provenance"]["session_ids"] == ["sess_zzza111"],
              f"got {rec_t['provenance']['session_ids']}")
        check("tail-into-cycle not ambiguous (N1 r4)",
              rec_t["provenance"]["ambiguous"] is False)
        check("tail + cycle rows summed",
              rec_t["totals"]["input_tokens"] == 3)


@_test("review_usage_capture#selftest_two_sessions_ambiguous")
def _selftest_two_sessions_ambiguous(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_aaa111")
    fx.session("sess_bbb222")
    fx.row("sess_aaa111", source="main_turn",
           input_tokens=100, computed_total_tokens=100)
    fx.row("sess_bbb222", source="main_turn",
           input_tokens=200, computed_total_tokens=200)
    fx.build()
    rec = fx.capture()
    check("union record produced", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("both truncated ids",
          p["session_ids"] == ["sess_aaa111"[:12], "sess_bbb222"[:12]])
    check("ambiguous true", p["ambiguous"] is True)
    check("union totals", rec["totals"]["input_tokens"] == 300)


@_test("review_usage_capture#selftest_foreign_directory")
def _selftest_foreign_directory(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    other = tmp / "other-repo"
    other.mkdir()
    fx.session("sess_main_abc123", directory=other)
    fx.row("sess_main_abc123", input_tokens=1000)
    fx.build()
    check("foreign directory -> None", fx.capture() is None)

    # N3 witness: default is production-strict — git failure (fixture repo
    # is not a work tree) with allow_cwd_fallback unset returns None even
    # though matching data exists; the hermetic fixture capture opts in
    # explicitly.
    check("no cwd fallback by default (N3)",
          capture_usage(home=fx.home, cwd=fx.repo, now_ms=fx.now) is None)


@_test("review_usage_capture#selftest_never_raises")
def _selftest_never_raises(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.db.write_bytes(b"definitely not a sqlite database" * 10)
    try:
        rec = fx.capture()
        check("corrupt db -> None, no exception", rec is None)
    except Exception as exc:  # noqa: BLE001
        check("corrupt db -> None, no exception", False,
              f"raised {type(exc).__name__}: {exc}")


@_test("review_usage_capture#selftest_locked_db")
def _selftest_locked_db(check: Callable) -> None:
    import time as _time

    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123", input_tokens=1000)
    fx.build()
    writer = sqlite3.connect(fx.db, isolation_level=None)
    try:
        writer.execute("BEGIN EXCLUSIVE")
        started = _time.monotonic()
        rec = fx.capture()
        waited = _time.monotonic() - started
        check("locked db -> None, no exception", rec is None)
        check("bounded wait (no fast bail)",
              waited >= BUSY_TIMEOUT_MS / 1000.0 * 0.5,
              f"waited {waited:.2f}s")
        check("bounded wait (no long hang)", waited < 10.0,
              f"waited {waited:.2f}s")
    except Exception as exc:  # noqa: BLE001
        check("locked db -> None, no exception", False,
              f"raised {type(exc).__name__}: {exc}")
    finally:
        writer.close()


@_test("review_usage_capture#selftest_codex_single_rollout")
def _selftest_codex_single_rollout(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    sid = "9f1c2d3e-aaaa-bbbb-cccc-dddddddddddd"
    fx.codex_rollout(
        sid,
        token_usages=(
            {"input_tokens": 100, "cached_input_tokens": 50,
             "cache_write_input_tokens": 10, "output_tokens": 20,
             "reasoning_output_tokens": 5, "total_tokens": 185},
            # Cumulative: LAST token_count event wins.
            {"input_tokens": 200, "cached_input_tokens": 80,
             "cache_write_input_tokens": 30, "output_tokens": 40,
             "reasoning_output_tokens": 15, "total_tokens": 365},
        ),
    )
    rec = fx.capture()
    check("record produced", rec is not None)
    if rec is None:
        return
    check("adapter", rec["adapter"] == "codex-rollout",
          f"got {rec['adapter']}")
    p = rec["provenance"]
    check("provenance db names rollout dir (tilde form)",
          p["db"] == "~/.codex/sessions", f"got {p['db']}")
    check("session id truncated", p["session_ids"] == [sid[:12]],
          f"got {p['session_ids']}")
    t = rec["totals"]
    check("input mapped", t["input_tokens"] == 200,
          f"got {t['input_tokens']}")
    check("cached -> cache_read", t["cache_read_input_tokens"] == 80,
          f"got {t['cache_read_input_tokens']}")
    check("cache_write -> cache_creation",
          t["cache_creation_input_tokens"] == 30,
          f"got {t['cache_creation_input_tokens']}")
    check("output mapped", t["output_tokens"] == 40)
    check("reasoning_output -> reasoning", t["reasoning_tokens"] == 15,
          f"got {t['reasoning_tokens']}")
    check("total_tokens -> computed_total",
          t["computed_total_tokens"] == 365,
          f"got {t['computed_total_tokens']}")
    check("by_agent_kind all under other (N6)",
          rec["by_agent_kind"] == {"other": dict(t)},
          f"got {rec['by_agent_kind']}")
    check("not ambiguous", p["ambiguous"] is False)

    # Legacy flat-shape witness (B1 tolerant fallback): a rollout file with
    # the old flat token_count lines still parses.
    tmp_flat = _tmp_dir()
    fx_flat = _Fixture(tmp_flat)
    flat_sid = "eeee5555-0000-0000-0000-000000000000"
    fx_flat.codex_rollout(
        flat_sid, file_tag="flat",
        shape="flat",
        token_usages=({"input_tokens": 42, "total_tokens": 42},),
    )
    rec_flat = fx_flat.capture()
    check("legacy flat token_count shape still parses",
          rec_flat is not None
          and rec_flat["totals"]["input_tokens"] == 42,
          f"got {rec_flat}")


@_test("review_usage_capture#selftest_codex_root_collapse")
def _selftest_codex_root_collapse(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    parent = "11111111-1111-1111-1111-111111111111"
    fx.codex_rollout(
        parent, file_tag="pare",
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
    )
    # Worker rollouts: own file uuid differs, session_meta.session_id names
    # the parent thread, parent_thread_id links them.
    for tag in ("work1", "work2"):
        fx.codex_rollout(
            parent, file_tag=tag, parent_thread_id=parent,
            mtime_s=fx.now / 1000.0 - 30,
            token_usages=({"input_tokens": 500, "total_tokens": 500},),
        )
    rec = fx.capture()
    check("single attributed record", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("parent id only", p["session_ids"] == [parent[:12]],
          f"got {p['session_ids']}")
    check("not ambiguous", p["ambiguous"] is False)
    check("workers not distinct candidates", len(p["session_ids"]) == 1)
    # N1: group totals are the SUM of each file's last cumulative counters
    # (parent 100 + worker 500 + worker 500), not last-mtime overwrite.
    check("group totals sum per-file cumulative (N1)",
          rec["totals"]["input_tokens"] == 1100
          and rec["totals"]["computed_total_tokens"] == 1100,
          f"got {rec['totals']}")
    check("by_agent_kind mirrors summed totals",
          rec["by_agent_kind"]["other"]["input_tokens"] == 1100)


@_test("review_usage_capture#selftest_codex_no_match")
def _selftest_codex_no_match(check: Callable) -> None:
    # Witness 1: rollout cwd points at a different repo.
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    other = tmp / "other-repo"
    other.mkdir()
    fx.codex_rollout(
        "aaaa1111-0000-0000-0000-000000000000",
        cwd=other,
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
    )
    check("different repo cwd -> None", fx.capture() is None)

    # Witness 2: matching cwd but file mtime before the window start.
    tmp2 = _tmp_dir()
    fx2 = _Fixture(tmp2)
    fx2.codex_rollout(
        "bbbb2222-0000-0000-0000-000000000000",
        mtime_s=(fx2.now - USAGE_WINDOW_MS) / 1000.0 - 3600,
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
    )
    check("stale mtime -> None", fx2.capture() is None)

    # Witness 3 (N13): matching cwd but file mtime in the FUTURE (clock
    # skew) — outside the [window_start, now] pre-filter band -> None.
    tmp3 = _tmp_dir()
    fx3 = _Fixture(tmp3)
    fx3.codex_rollout(
        "eeee3333-0000-0000-0000-000000000000",
        mtime_s=fx3.now / 1000.0 + 3600,
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
    )
    check("future mtime -> None", fx3.capture() is None)

    # Witness 4 (N1): FIRST session_meta cwd matches the anchor, a LATER
    # session_meta names a foreign cwd — the file's identity was already
    # decided by the first meta, so its usage is kept (the early break must
    # not fire). garbage_lines[0] is inserted after the first usage event,
    # i.e. exactly between usage1 and the cumulative usage2.
    tmp4 = _tmp_dir()
    fx4 = _Fixture(tmp4)
    other4 = tmp4 / "other-repo"
    other4.mkdir()
    foreign_meta = json.dumps({
        "timestamp": "2026-09-06T12:00:00.500Z",
        "type": "session_meta",
        "payload": {"id": "rollout-foreign", "session_id": "zzzz9999-0000",
                    "cwd": str(other4)},
    })
    fx4.codex_rollout(
        "dddd4444-0000-0000-0000-000000000000",
        token_usages=(
            {"input_tokens": 100, "total_tokens": 100},
            {"input_tokens": 250, "total_tokens": 250},
        ),
        garbage_lines=(foreign_meta,),
    )
    rec4 = fx4.capture()
    check("later foreign session_meta keeps first-meta usage (N1)",
          rec4 is not None and rec4["totals"]["input_tokens"] == 250,
          f"got {rec4}")


@_test("review_usage_capture#selftest_codex_two_rollouts_ambiguous")
def _selftest_codex_two_rollouts_ambiguous(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    sid_a = "aaaa1111-1111-1111-1111-111111111111"
    sid_b = "bbbb2222-2222-2222-2222-222222222222"
    fx.codex_rollout(sid_a, file_tag="rolla",
                     token_usages=({"input_tokens": 100,
                                    "total_tokens": 100},))
    fx.codex_rollout(sid_b, file_tag="rollb",
                     token_usages=({"input_tokens": 50,
                                    "total_tokens": 50},))
    rec = fx.capture()
    check("union record produced", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("both truncated ids",
          p["session_ids"] == [sid_a[:12], sid_b[:12]],
          f"got {p['session_ids']}")
    check("ambiguous true", p["ambiguous"] is True)
    check("union totals", rec["totals"]["input_tokens"] == 150,
          f"got {rec['totals']['input_tokens']}")


@_test("review_usage_capture#selftest_codex_malformed_jsonl")
def _selftest_codex_malformed_jsonl(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    sid = "cccc3333-0000-0000-0000-000000000000"
    fx.codex_rollout(
        sid,
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
        garbage_lines=('{"truncated": {"garbage',),
    )
    try:
        rec = fx.capture()
        check("bad lines skipped, record from prefix", rec is not None)
        if rec is not None:
            check("prefix totals", rec["totals"]["input_tokens"] == 100,
                  f"got {rec['totals']['input_tokens']}")
    except Exception as exc:  # noqa: BLE001
        check("bad lines skipped, no exception", False,
              f"raised {type(exc).__name__}: {exc}")


@_test("review_usage_capture#selftest_token_fields_match_summarizer")
def _selftest_token_fields_match_summarizer(check: Callable) -> None:
    """N8 drift guard: TOKEN_FIELDS must equal the summarizer's
    ``_USAGE_TOTAL_KEYS`` (the two constants are duplicated by design;
    this cross-check parses the sibling source so drift fails a selftest,
    with no import tricks beyond reading the sibling file)."""
    import re as _re

    sibling = (
        Path(__file__).resolve().parent / "summarize_review_stats.py"
    )
    try:
        src = sibling.read_text(encoding="utf-8")
        m = _re.search(
            r"_USAGE_TOTAL_KEYS\s*=\s*\(([^)]*)\)", src, _re.DOTALL
        )
        sibling_keys = tuple(
            k.strip().strip('"\'') for k in m.group(1).split(",") if k.strip()
        ) if m else ()
        check("sibling _USAGE_TOTAL_KEYS parsed",
              bool(sibling_keys), f"parsed {sibling_keys!r}")
        check("token field tuples match summarizer (N8)",
              TOKEN_FIELDS == sibling_keys,
              f"capture {TOKEN_FIELDS} vs summarizer {sibling_keys}")
    except Exception as exc:  # noqa: BLE001
        check("sibling source readable", False,
              f"{type(exc).__name__}: {exc}")


@_test("review_usage_capture#selftest_adapter_fallback_order")
def _selftest_adapter_fallback_order(check: Callable) -> None:
    # Witness 1: zcode db absent, codex rollout present -> codex wins.
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.codex_rollout("dddd4444-0000-0000-0000-000000000000",
                     token_usages=({"input_tokens": 100,
                                    "total_tokens": 100},))
    rec = fx.capture()
    check("codex fallback record", rec is not None)
    if rec is not None:
        check("codex adapter", rec["adapter"] == "codex-rollout",
              f"got {rec['adapter']}")

    # Witness 2: both stores present -> zcode-sqlite wins.
    fx.session("sess_main_abc123")
    fx.row("sess_main_abc123", source="main_turn",
           input_tokens=1000, computed_total_tokens=1000)
    fx.build()
    rec2 = fx.capture()
    check("both stores -> record", rec2 is not None)
    if rec2 is not None:
        check("zcode wins", rec2["adapter"] == "zcode-sqlite",
              f"got {rec2['adapter']}")


@_test("review_usage_capture#selftest_mint_prints_identity")
def _selftest_mint_prints_identity(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_mint123")
    fx.row("sess_root_mint123", input_tokens=10, computed_total_tokens=10)
    fx.build()
    ident = mint_identity(home=fx.home, cwd=fx.repo, now_ms=fx.now,
                          allow_cwd_fallback=True)
    check("run id 32 lowercase hex",
          re.fullmatch(r"[0-9a-f]{32}", ident["review_run_id"]) is not None,
          f"got {ident['review_run_id']!r}")
    check("minted_at_ms equals injected now",
          ident["minted_at_ms"] == fx.now)
    check("candidate root truncated",
          ident["candidate_root_session_ids"] == ["sess_root_mi"],
          f"got {ident['candidate_root_session_ids']}")
    check("identity keys exactly three",
          set(ident.keys()) == {
              "review_run_id", "minted_at_ms",
              "candidate_root_session_ids"})

    # No store: mint still prints the identity fields, empty candidates,
    # and never raises.
    tmp2 = _tmp_dir()
    home2 = tmp2 / "home"
    home2.mkdir()
    ident2 = mint_identity(home=home2, cwd=tmp2 / "repo", now_ms=fx.now)
    check("no store: identity still minted",
          re.fullmatch(r"[0-9a-f]{32}", ident2["review_run_id"]) is not None)
    check("no store: minted_at_ms injected",
          ident2["minted_at_ms"] == fx.now)
    check("no store: empty candidates",
          ident2["candidate_root_session_ids"] == [])


@_test("review_usage_capture#selftest_interval_single_contributor_attributable")
def _selftest_interval_single_contributor_attributable(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_int001")
    start = fx.now - 10_000_000
    fx.turn_row("sess_root_int001", completed_at=start + 1_000,
                input_tokens=100, computed_total_tokens=100)
    fx.turn_row("sess_root_int001", completed_at=fx.now - 500,
                input_tokens=50, computed_total_tokens=50)
    fx.build()
    run_id = "abcdef01" * 4
    rec = fx.capture_identity(run_id, start)
    check("record produced", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("attribution interval-identity",
          p["attribution"] == "interval-identity", f"got {p['attribution']}")
    check("attributable true", p["attributable"] is True)
    check("review_run_id carried verbatim", p["review_run_id"] == run_id)
    check("review_started_at_ms carried verbatim",
          p["review_started_at_ms"] == start)
    check("source_grain turn", p["source_grain"] == "turn")
    check("turn grain buckets all under other",
          set(rec["by_agent_kind"].keys()) == {"other"},
          f"got {rec['by_agent_kind'].keys()}")
    check("totals equal only in-interval rows",
          rec["totals"]["input_tokens"] == 150,
          f"got {rec['totals']['input_tokens']}")
    check("captured_at_ms is now", p["captured_at_ms"] == fx.now)


@_test("review_usage_capture#selftest_interval_excludes_pre_review_rows")
def _selftest_interval_excludes_pre_review_rows(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_int002")
    start = fx.now - 10_000_000
    fx.turn_row("sess_root_int002", completed_at=start - 5_000,
                input_tokens=9_000, computed_total_tokens=9_000)
    fx.turn_row("sess_root_int002", completed_at=start + 2_000,
                input_tokens=111, computed_total_tokens=111)
    fx.build()
    rec = fx.capture_identity("f" * 32, start)
    check("record produced", rec is not None)
    if rec is None:
        return
    check("pre-review implementation rows excluded",
          rec["totals"]["input_tokens"] == 111,
          f"got {rec['totals']['input_tokens']}")


@_test("review_usage_capture#selftest_interval_two_contributors_ambiguous")
def _selftest_interval_two_contributors_ambiguous(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    start = fx.now - 10_000_000
    fx.session("sess_twoaa000001")
    fx.session("sess_twobb000002")
    fx.turn_row("sess_twoaa000001", completed_at=start + 1_000,
                input_tokens=100, computed_total_tokens=100)
    fx.turn_row("sess_twobb000002", completed_at=start + 2_000,
                input_tokens=200, computed_total_tokens=200)
    fx.build()
    rec = fx.capture_identity("e" * 32, start)
    check("union record produced", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("attribution interval-ambiguous",
          p["attribution"] == "interval-ambiguous",
          f"got {p['attribution']}")
    check("attributable false", p["attributable"] is False)
    check("session_ids both contributors (truncated, ambiguous)",
          p["session_ids"] == ["sess_twoaa00", "sess_twobb00"]
          and p["ambiguous"] is True,
          f"got {p['session_ids']}")
    by_session = p["by_session"]
    check("by_session two keys",
          len(by_session) == 2, f"got {list(by_session)}")
    check("by_session keys at most 12 chars",
          all(len(k) <= 12 for k in by_session))
    check("by_session keys match session_ids",
          set(by_session.keys()) == set(p["session_ids"]))
    check("by_session carries per-contributor subtotals",
          sorted(v["input_tokens"] for v in by_session.values()) == [100, 200],
          f"got {by_session}")
    check("totals equal the union (never assigned to one session)",
          rec["totals"]["input_tokens"] == 300,
          f"got {rec['totals']['input_tokens']}")


@_test("review_usage_capture#selftest_adjacent_rounds_disjoint")
def _selftest_adjacent_rounds_disjoint(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_adj_root001")
    m1 = fx.now - 10_000_000
    m2 = fx.now - 5_000_000
    # Row completing exactly at M1: counts in NEITHER round (open start).
    fx.turn_row("sess_adj_root001", completed_at=m1,
                input_tokens=1, computed_total_tokens=1)
    # Row completing exactly at M2: counts in round 1 ONLY (closed end).
    fx.turn_row("sess_adj_root001", completed_at=m2,
                input_tokens=10, computed_total_tokens=10)
    fx.turn_row("sess_adj_root001", completed_at=m1 + 1_000,
                input_tokens=100, computed_total_tokens=100)
    fx.turn_row("sess_adj_root001", completed_at=m2 + 1_000,
                input_tokens=200, computed_total_tokens=200)
    fx.turn_row("sess_adj_root001", completed_at=m1 - 1_000,
                input_tokens=5, computed_total_tokens=5)
    fx.build()
    r1 = fx.capture_identity("a" * 32, m1, now=m2)
    r2 = fx.capture_identity("b" * 32, m2, now=fx.now)
    check("round 1 attributable", r1 is not None
          and r1["provenance"]["attributable"] is True)
    check("round 2 attributable", r2 is not None
          and r2["provenance"]["attributable"] is True)
    if r1 is None or r2 is None:
        return
    check("round 1 totals: M1+1000 and exactly-M2 rows only",
          r1["totals"]["input_tokens"] == 110,
          f"got {r1['totals']['input_tokens']}")
    check("round 2 totals: M2+1000 row only",
          r2["totals"]["input_tokens"] == 200,
          f"got {r2['totals']['input_tokens']}")
    check("exactly-M1 row counted in neither round",
          r1["totals"]["input_tokens"] != 111
          and r2["totals"]["input_tokens"] != 1)
    check("rounds disjoint and additive",
          r1["totals"]["input_tokens"] + r2["totals"]["input_tokens"] == 310)


@_test("review_usage_capture#selftest_interval_turn_usage_preferred_with_fallback")
def _selftest_interval_turn_usage_preferred_with_fallback(
    check: Callable,
) -> None:
    run_id = "c" * 32
    start = None  # set per fixture
    # (a) turn grain preferred: two model_usage attempt rows of 100 and
    # one turn_usage row of 100 -> totals 100 (double-count avoided).
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    start = fx.now - 10_000_000
    fx.session("sess_turn_pref001")
    fx.row("sess_turn_pref001", completed_at=start + 1_000,
           input_tokens=100, computed_total_tokens=100)
    fx.row("sess_turn_pref001", completed_at=start + 2_000,
           input_tokens=100, computed_total_tokens=100)
    fx.turn_row("sess_turn_pref001", completed_at=start + 3_000,
                input_tokens=100, computed_total_tokens=100)
    fx.build()
    rec = fx.capture_identity(run_id, start)
    check("turn-grain preferred: totals 100, not 200/300", rec is not None
          and rec["totals"]["input_tokens"] == 100,
          f"got {rec['totals'] if rec else None}")
    if rec is not None:
        check("preferred record is turn grain",
              rec["provenance"]["source_grain"] == "turn")

    # (b) turn_usage table DROPPED -> missing-table-only fallback to
    # model_usage attempt grain, never attributable.
    tmp2 = _tmp_dir()
    fx2 = _Fixture(tmp2)
    start2 = fx2.now - 10_000_000
    fx2.session("sess_turn_fb00001")
    fx2.row("sess_turn_fb00001", completed_at=start2 + 1_000,
            input_tokens=100, computed_total_tokens=100)
    fx2.row("sess_turn_fb00001", completed_at=start2 + 2_000,
            input_tokens=100, computed_total_tokens=100)
    fx2.turn_row("sess_turn_fb00001", completed_at=start2 + 3_000,
                 input_tokens=100, computed_total_tokens=100)
    fx2.build()
    fx2.drop_turn_table()
    rec2 = fx2.capture_identity(run_id, start2)
    check("fallback record produced", rec2 is not None)
    if rec2 is not None:
        p2 = rec2["provenance"]
        check("fallback attribution interval-fallback",
              p2["attribution"] == "interval-fallback",
              f"got {p2['attribution']}")
        check("fallback never attributable", p2["attributable"] is False)
        check("fallback source_grain model-attempt",
              p2["source_grain"] == "model-attempt",
              f"got {p2['source_grain']}")
        check("fallback totals from attempt rows (200)",
              rec2["totals"]["input_tokens"] == 200,
              f"got {rec2['totals']['input_tokens']}")

    # (c) turn_usage present but EMPTY for the anchor while model_usage
    # carries in-interval rows -> honest empty (None), never a fallback
    # record (a fallback would produce a record and fail).
    tmp3 = _tmp_dir()
    fx3 = _Fixture(tmp3)
    start3 = fx3.now - 10_000_000
    other = tmp3 / "other-repo"
    other.mkdir()
    fx3.session("sess_turn_anchor1")
    fx3.session("sess_turn_foreig", directory=other)
    fx3.row("sess_turn_anchor1", completed_at=start3 + 1_000,
            input_tokens=100, computed_total_tokens=100)
    fx3.turn_row("sess_turn_foreig", completed_at=start3 + 1_000,
                 input_tokens=999, computed_total_tokens=999)
    fx3.build()
    rec3 = fx3.capture_identity(run_id, start3)
    check("present-but-empty turn rows for anchor -> honest None",
          rec3 is None, f"got {rec3}")


@_test("review_usage_capture#selftest_fallback_discriminator_and_locks")
def _selftest_fallback_discriminator_and_locks(check: Callable) -> None:
    import time as _time

    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    start = fx.now - 10_000_000
    fx.session("sess_turn_lock001")
    fx.turn_row("sess_turn_lock001", completed_at=start + 1_000,
                input_tokens=100, computed_total_tokens=100)
    fx.row("sess_turn_lock001", completed_at=start + 1_000,
           input_tokens=100, computed_total_tokens=100)
    fx.build()
    writer = sqlite3.connect(fx.db, isolation_level=None)
    try:
        writer.execute("BEGIN EXCLUSIVE")
        started = _time.monotonic()
        rec = fx.capture_identity("d" * 32, start)
        waited = _time.monotonic() - started
        check("locked turn_usage -> None, never a fallback record",
              rec is None, f"got {rec}")
        check("bounded wait", waited < 10.0, f"waited {waited:.2f}s")
    except Exception as exc:  # noqa: BLE001
        check("locked db -> None, no exception", False,
              f"raised {type(exc).__name__}: {exc}")
    finally:
        writer.close()


@_test("review_usage_capture#selftest_identity_no_usable_runtime_data")
def _selftest_identity_no_usable_runtime_data(check: Callable) -> None:
    # No db at all: identity invocation yields None (never a codex
    # fallback when no codex store exists either).
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_nodata1")
    start = fx.now - 10_000_000
    check("no db + identity -> None",
          fx.capture_identity("1" * 32, start) is None)

    # Rows all completing before the interval start: None (never an
    # empty-totals attributable record).
    tmp2 = _tmp_dir()
    fx2 = _Fixture(tmp2)
    fx2.session("sess_root_early01")
    fx2.turn_row("sess_root_early01", completed_at=start - 1_000,
                 input_tokens=500, computed_total_tokens=500)
    fx2.build()
    check("rows all pre-interval + identity -> None",
          fx2.capture_identity("2" * 32, start) is None)


@_test("review_usage_capture#selftest_codex_identity_stays_legacy")
def _selftest_codex_identity_stays_legacy(check: Callable) -> None:
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    sid = "9f1c2d3e-aaaa-bbbb-cccc-dddddddddddd"
    fx.codex_rollout(
        sid,
        token_usages=(
            {"input_tokens": 100, "total_tokens": 185},
            # Cumulative: LAST token_count event wins.
            {"input_tokens": 200, "total_tokens": 365},
        ),
    )
    start = fx.now - 10_000_000
    rec = fx.capture_identity("3" * 32, start)
    check("codex record produced with identity", rec is not None)
    if rec is None:
        return
    p = rec["provenance"]
    check("attribution window-legacy",
          p["attribution"] == "window-legacy",
          f"got {p.get('attribution')}")
    check("attributable false", p["attributable"] is False)
    check("review_run_id carried for forensics",
          p["review_run_id"] == "3" * 32)
    check("totals from unchanged cumulative parsing",
          rec["totals"]["input_tokens"] == 200,
          f"got {rec['totals']['input_tokens']}")


@_test("review_usage_capture#selftest_bare_invocation_byte_compat")
def _selftest_bare_invocation_byte_compat(check: Callable) -> None:
    new_keys = (
        "attribution", "attributable", "review_run_id",
        "review_started_at_ms", "source_grain", "by_session",
    )
    # zcode adapter, bare invocation: today's exact shape, no new keys.
    tmp = _tmp_dir()
    fx = _Fixture(tmp)
    fx.session("sess_root_bare001")
    fx.row("sess_root_bare001", input_tokens=100, computed_total_tokens=100)
    fx.build()
    rec = fx.capture()
    check("zcode bare record produced", rec is not None)
    if rec is not None:
        check("zcode bare: no attribution key",
              "attribution" not in rec["provenance"]
              and "attribution" not in rec)
        check("zcode bare: no new provenance keys",
              not [k for k in new_keys if k in rec["provenance"]],
              f"got {[k for k in new_keys if k in rec['provenance']]}")
        check("zcode bare: no new top-level keys",
              not [k for k in new_keys if k in rec])

    # codex adapter, bare invocation: same shape contract.
    tmp2 = _tmp_dir()
    fx2 = _Fixture(tmp2)
    fx2.codex_rollout(
        "bbbb2222-0000-0000-0000-000000000000",
        token_usages=({"input_tokens": 100, "total_tokens": 100},),
    )
    rec2 = fx2.capture()
    check("codex bare record produced", rec2 is not None)
    if rec2 is not None:
        check("codex bare: no new keys anywhere",
              not [k for k in new_keys
                   if k in rec2 or k in rec2["provenance"]])


@_test("review_usage_capture#selftest_identity_invocation_arity_and_shape")
def _selftest_identity_invocation_arity_and_shape(check: Callable) -> None:
    # Arity: either argument alone is an argparse error (exit 2) before
    # any store read; main() is driven with injected argv only.
    for argv in (
        ["--json", "--review-run-id", "a" * 32],
        ["--json", "--review-started-at-ms", "1700000000000"],
    ):
        try:
            main(argv)
            check(f"arity error for {argv[1]}", False, "no SystemExit")
        except SystemExit as exc:
            check(f"arity error exits 2 for {argv[1]}", exc.code == 2,
                  f"got {exc.code}")

    # Shape rules via the injected seam (no store access): invalid run id
    # or non-positive start is treated as absent (window-legacy path).
    tmp = _tmp_dir()
    home = tmp / "home"
    home.mkdir()
    check("short run id treated as absent",
          _validated_identity("abc123", 1700000000000, home) is None)
    check("uppercase run id treated as absent",
          _validated_identity("A" * 32, 1700000000000, home) is None)
    check("non-positive start treated as absent",
          _validated_identity("a" * 32, 0, home) is None)
    check("negative start treated as absent",
          _validated_identity("a" * 32, -5, home) is None)
    check("valid identity passes through",
          _validated_identity("a" * 32, 1700000000000, home)
          == ("a" * 32, 1700000000000))
    check("both absent -> None (bare path)",
          _validated_identity(None, None, home) is None)


def run_selftest() -> int:
    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        if cond:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
            all_ok = False

    for name, fn in _registry.items():
        print(f"--- {name} ---")
        try:
            fn(check)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {name} raised {type(exc).__name__}: {exc}")
            all_ok = False
    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture review token usage from the runtime store."
    )
    parser.add_argument(
        "--selftest", action="store_true", help="run built-in selftests"
    )
    parser.add_argument(
        "subcommand", nargs="?", choices=("mint",),
        help="mint: print a fresh review-run identity as JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the usage record as JSON for merging into a sidecar",
    )
    parser.add_argument(
        "--review-run-id",
        default=None,
        help="review-run identity from the mint output (32-char hex)",
    )
    parser.add_argument(
        "--review-started-at-ms",
        type=int,
        default=None,
        help="review round start (minted_at_ms from the mint output)",
    )
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if args.subcommand == "mint":
        print(json.dumps(mint_identity(), indent=2))
        return 0

    # Identity arity: both arguments or neither; either alone is an
    # argparse error (exit 2) before any store read.
    if (args.review_run_id is None) != (args.review_started_at_ms is None):
        parser.error(
            "--review-run-id and --review-started-at-ms must be passed "
            "together (mint them with the mint subcommand)"
        )

    if not args.json:
        # N10: bare invocation never captures (capture only under --json);
        # the status line goes to stderr so stdout stays "JSON record or
        # nothing" in all modes.
        sys.stderr.write(
            "review_usage_capture: read-only usage capture; "
            "run with --json to print the usage record for a sidecar\n"
        )
        return 0

    record = capture_usage(
        review_run_id=args.review_run_id,
        review_started_at_ms=args.review_started_at_ms,
    )
    if record is not None:
        if args.review_run_id is None:
            # Bare invocation: stdout stays byte-identical; the notice is
            # stderr-only.
            sys.stderr.write(
                "review_usage_capture: record is non-attributable "
                "(bare invocation; run mint and pass --review-run-id with "
                "--review-started-at-ms for interval attribution)\n"
            )
        print(json.dumps(record, indent=2))
    # No store data: print nothing; the caller writes the sidecar
    # without a usage field (missing stays missing).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
