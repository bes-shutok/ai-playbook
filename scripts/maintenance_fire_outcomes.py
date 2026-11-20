#!/usr/bin/env python3
"""Read-only ZCode task-index fire-outcome adapter and bounded state-note helper.

Warning-only post-fire verification arm for the maintenance skill (plan
docs/history/plans/2026-11-05-automation-fire-time-failure-verification.md,
Task 1; origin incident
docs/history/backlog/2026-11-05-automation-fire-time-failure-verification.md).

Machinery admission: warning-only through review date 2026-12-05; promotion
requires a true catch and a pre-registered registry-removal row. This module
never adds a pre-fire lookup, a retry, a dispatch-blocking condition, or a
new scheduler-state schema field: the only writes it performs are bounded
edits to the existing ``notes[]`` array of the scheduler state file and
append-first one-line entries in the persistent memory index, both through
explicit paths the caller passes.

The SQLite reads are read-only (``mode=ro`` URI); the database is resolved
from ``ZCODE_DATA_BASE_DIR`` falling back to ``~/.zcode/v2/tasks-index.sqlite``
when no explicit path is passed, and every helper accepts explicit database
and state paths so fixtures never touch live surfaces. The multi-run
workspace reader raises :class:`SourceUnavailable` when the store is
missing or unreadable, so the re-derivation and overlaps reports carry a
visible unknown entry instead of an indistinguishable empty list; a
present store with no retained rows still reads empty.

Error classes come only from the structured ``lastError.attribution``
fields (``exceptionKind``, ``reason``, ``retryable``) of the linked task
row; raw ``message``/``detail``/request id/payload values are never returned
or persisted.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

NOTE_PREFIX = "one-shot-fire-outcome|"
CORRECTION_PREFIX = "fire-outcome-correction|"
TERMINAL_OUTCOMES = frozenset({"succeeded", "failed"})
CORRECTION_STATUSES = ("pending", "done", "ambiguous")
RETENTION_CAP = 30
UNKNOWN = "unknown"
# The outcome-data members the idempotency decision compares: everything
# the runtime observation determines. The writer-managed ``correction``
# status is deliberately absent, so re-recording identical outcome data
# after this module flipped a note to done or ambiguous is idempotent
# reuse, never a conflict.
OUTCOME_DATA_FIELDS = ("automation_id", "scheduled_at", "outcome",
                       "session_id", "error", "retryable")

REQUIRED_RUN_COLUMNS = frozenset(
    {
        "run_id",
        "automation_id",
        "workspace_key",
        "scheduled_at",
        "dispatch_status",
        "outcome",
        "session_id",
        "created_at",
        "updated_at",
    }
)
REQUIRED_TASK_COLUMNS = frozenset({"workspace_key", "task_id", "meta_json"})
REQUIRED_AUTOMATION_COLUMNS = frozenset({"automation_id", "workspace_key", "prompt"})

# The only lastError.attribution members the adapter may extract. Everything
# else in the task row (message, detail, request ids, provider payload) is
# structurally unreachable from the return values below.
ATTRIBUTION_ALLOWLIST = ("exceptionKind", "reason", "retryable")

_RUNS_TABLE = "automation_runs"
_TASKS_TABLE = "tasks"
_AUTOMATIONS_TABLE = "automations"

DEFAULT_WINDOW_MS = 24 * 60 * 60 * 1000


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_db_path(explicit=None, env=None, home=None):
    """Resolve the task-index database path: explicit, then
    ``ZCODE_DATA_BASE_DIR``/v2/tasks-index.sqlite, then the home fallback.
    Existence is the reader's unknown case, not the resolver's."""
    if explicit:
        return Path(expand_path(explicit, home=home))
    base = env if env is not None else os.environ.get("ZCODE_DATA_BASE_DIR")
    if base:
        return Path(base) / "v2" / "tasks-index.sqlite"
    home_dir = Path(expand_path("~", home=home))
    return home_dir / ".zcode" / "v2" / "tasks-index.sqlite"


def expand_path(value, home=None):
    """Expand a leading ~ against the given (or real) home, so tests can
    redirect the fallback away from the live home."""
    if home is not None and value == "~":
        return str(home)
    return os.path.expanduser(value)


# ---------------------------------------------------------------------------
# Read-only SQLite access
# ---------------------------------------------------------------------------


def _connect_ro(db_path):
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    uri = "file:%s?mode=ro" % path.resolve().as_posix()
    return sqlite3.connect(uri, uri=True)


def _table_columns(conn, table):
    cur = conn.execute("PRAGMA table_info(%s)" % table)
    columns = {row[1] for row in cur.fetchall()}
    return columns or None  # a missing table has no columns


def _unknown(reason, **extra):
    result = {"status": "unknown", "reason": reason}
    result.update(extra)
    return result


class SourceUnavailable(Exception):
    """Raised by :func:`read_workspace_runs` when the task-index source is
    unavailable (missing database file, sqlite error, missing table, or
    missing required columns). The multi-run readers must never fold this
    condition into an indistinguishable empty list: the re-derivation and
    overlaps paths catch it and report a workspace-level unknown entry
    instead, per the plan invariant that an unavailable source reports
    unknown and infers no outcome. A present store with no retained rows
    still reads empty (that is the aged-out case, not unavailability)."""

    def __init__(self, reason, **extra):
        super().__init__(reason)
        self.reason = reason
        self.extra = dict(extra)

    def unknown_payload(self):
        payload = {"status": UNKNOWN, "reason": self.reason}
        payload.update(self.extra)
        return payload


def read_fire_outcome(db_path, automation_id, scheduled_at_ms, workspace_key):
    """Read one terminal fire outcome keyed by automation id, fire time, and
    workspace key. Require exactly one terminal row at the expected
    ``scheduled_at``; missing database/schema or absent, ambiguous, or
    nonterminal rows yield unknown. Read-only over the whole database."""
    try:
        conn = _connect_ro(db_path)
    except FileNotFoundError:
        return _unknown("missing-database")
    except sqlite3.Error as exc:
        return _unknown("db-error", detail=str(exc))
    try:
        try:
            columns = _table_columns(conn, _RUNS_TABLE)
        except sqlite3.Error as exc:
            return _unknown("db-error", detail=str(exc))
        if columns is None:
            return _unknown("missing-table", table=_RUNS_TABLE)
        if not REQUIRED_RUN_COLUMNS.issubset(columns):
            missing = sorted(REQUIRED_RUN_COLUMNS - columns)
            return _unknown("missing-columns", table=_RUNS_TABLE, missing=missing)
        cur = conn.execute(
            "SELECT run_id, outcome, session_id, dispatch_status, updated_at"
            " FROM %s WHERE automation_id = ? AND workspace_key = ?"
            " AND scheduled_at = ?" % _RUNS_TABLE,
            (automation_id, workspace_key, int(scheduled_at_ms)),
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    if not rows:
        return _unknown("missing-event")
    if len(rows) > 1:
        return _unknown("ambiguous", matched_run_ids=[r[0] for r in rows])
    run_id, outcome, session_id, dispatch_status, updated_at = rows[0]
    if outcome not in TERMINAL_OUTCOMES:
        return _unknown(
            "nonterminal",
            observed_outcome=outcome,
            dispatch_status=dispatch_status,
            run_id=run_id,
        )
    result = {
        "status": "terminal",
        "reason": "ok",
        "outcome": outcome,
        "run_id": run_id,
        "automation_id": automation_id,
        "scheduled_at": int(scheduled_at_ms),
        "workspace_key": workspace_key,
        "session_id": session_id or UNKNOWN,
        "updated_at": updated_at,
        "error_class": UNKNOWN,
        "retryable": None,
    }
    if outcome == "failed" and session_id:
        attribution = read_error_class(db_path, workspace_key, session_id)
        result["error_class"] = attribution["error_class"]
        result["retryable"] = attribution["retryable"]
    return result


def read_error_class(db_path, workspace_key, session_id):
    """Extract the structured error class of the task row linked by
    workspace key and session id. Only the allowlisted attribution members
    are extracted; an absent field is stored as unknown. Never surfaces a
    raw message, detail, request id, or provider payload."""
    result = {"error_class": UNKNOWN, "retryable": None}
    try:
        conn = _connect_ro(db_path)
    except (FileNotFoundError, sqlite3.Error):
        return result
    try:
        try:
            columns = _table_columns(conn, _TASKS_TABLE)
        except sqlite3.Error:
            return result
        if columns is None or not REQUIRED_TASK_COLUMNS.issubset(columns):
            return result
        cur = conn.execute(
            "SELECT meta_json FROM %s WHERE workspace_key = ? AND task_id = ?"
            % _TASKS_TABLE,
            (workspace_key, session_id),
        )
        row = cur.fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return result
    try:
        meta = json.loads(row[0])
    except (ValueError, TypeError):
        return result
    if not isinstance(meta, dict):
        return result
    last_error = meta.get("lastError")
    if not isinstance(last_error, dict):
        return result
    attribution = last_error.get("attribution")
    if not isinstance(attribution, dict):
        return result
    exception_kind = attribution.get("exceptionKind")
    reason = attribution.get("reason")
    if isinstance(exception_kind, str) and exception_kind.strip() \
            and isinstance(reason, str) and reason.strip():
        result["error_class"] = "%s/%s" % (exception_kind, reason)
    retryable = attribution.get("retryable")
    if isinstance(retryable, bool):
        result["retryable"] = retryable
    return result


# ---------------------------------------------------------------------------
# Overlap candidates (post-fire, report-only)
# ---------------------------------------------------------------------------


def read_workspace_runs(db_path, workspace_key, since_ms):
    """Read recent run rows in the workspace (including recurring carriers)
    with their automation prompt when the automation record is still
    present. Missing prompts are absent fields, never guesses. Read-only.

    Raises :class:`SourceUnavailable` when the store is unavailable
    (missing database, db error, missing table, or missing required
    columns), so the re-derivation and overlaps paths can report the
    condition instead of an indistinguishable empty list; a present store
    with no retained rows still returns ``[]``."""
    try:
        conn = _connect_ro(db_path)
    except FileNotFoundError as exc:
        raise SourceUnavailable("missing-database", path=str(db_path)) from exc
    except sqlite3.Error as exc:
        raise SourceUnavailable("db-error", detail=str(exc)) from exc
    try:
        try:
            runs = []
            prompts = {}
            columns = _table_columns(conn, _RUNS_TABLE)
            if columns is None:
                raise SourceUnavailable("missing-table", table=_RUNS_TABLE)
            if not REQUIRED_RUN_COLUMNS.issubset(columns):
                raise SourceUnavailable(
                    "missing-columns",
                    table=_RUNS_TABLE,
                    missing=sorted(REQUIRED_RUN_COLUMNS - columns),
                )
            auto_columns = _table_columns(conn, _AUTOMATIONS_TABLE)
            if auto_columns is not None and REQUIRED_AUTOMATION_COLUMNS.issubset(auto_columns):
                cur = conn.execute(
                    "SELECT automation_id, prompt FROM %s WHERE workspace_key = ?"
                    % _AUTOMATIONS_TABLE,
                    (workspace_key,),
                )
                prompts = {row[0]: row[1] for row in cur.fetchall()}
            cur = conn.execute(
                "SELECT run_id, automation_id, scheduled_at, outcome, session_id,"
                " dispatch_status, updated_at FROM %s"
                " WHERE workspace_key = ? AND scheduled_at >= ?"
                " ORDER BY scheduled_at ASC, run_id ASC" % _RUNS_TABLE,
                (workspace_key, int(since_ms)),
            )
            for row in cur.fetchall():
                run_id, automation_id, scheduled_at, outcome, session_id, dispatch_status, updated_at = row
                runs.append(
                    {
                        "run_id": run_id,
                        "automation_id": automation_id,
                        "scheduled_at": scheduled_at,
                        "outcome": outcome,
                        "session_id": session_id,
                        "dispatch_status": dispatch_status,
                        "updated_at": updated_at,
                        "prompt": prompts.get(automation_id),
                    }
                )
            return runs
        except sqlite3.Error as exc:
            raise SourceUnavailable("db-error", detail=str(exc)) from exc
    finally:
        conn.close()


def normalize_prompt(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    return " ".join(prompt.split())


def find_overlaps(runs):
    """Compare terminal-run intervals (``scheduled_at`` through terminal
    ``updated_at``) pairwise and report overlapping intervals as candidates
    with both run ids. Compare normalized prompts only when both are
    available, else report ``mandate_match: "unknown"``. Timing alone never
    claims a duplicate mandate, and nothing here prevents, cancels, or
    reschedules a carrier."""
    intervals = []
    for index, run in enumerate(runs):
        if run.get("outcome") not in TERMINAL_OUTCOMES:
            continue
        start = run.get("scheduled_at")
        end = run.get("updated_at")
        if not isinstance(start, int) or not isinstance(end, int) or end <= start:
            continue
        intervals.append((index, start, end))
    candidates = []
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            index_i, start_i, end_i = intervals[i]
            index_j, start_j, end_j = intervals[j]
            # Half-open [start, end) intervals: touching intervals are
            # back-to-back, not overlapping.
            if not (start_i < end_j and start_j < end_i):
                continue
            run_i = runs[index_i]
            run_j = runs[index_j]
            prompt_i = normalize_prompt(run_i.get("prompt"))
            prompt_j = normalize_prompt(run_j.get("prompt"))
            if prompt_i is not None and prompt_j is not None:
                mandate_match = prompt_i == prompt_j
            else:
                mandate_match = UNKNOWN
            candidates.append(
                {
                    "run_ids": [run_i["run_id"], run_j["run_id"]],
                    "automation_ids": [run_i["automation_id"], run_j["automation_id"]],
                    "intervals": [
                        {"run_id": run_i["run_id"], "start": start_i, "end": end_i},
                        {"run_id": run_j["run_id"], "start": start_j, "end": end_j},
                    ],
                    "mandate_match": mandate_match,
                }
            )
    return candidates


# ---------------------------------------------------------------------------
# Outcome notes (the existing scheduler-state notes[] shape)
# ---------------------------------------------------------------------------


def outcome_note_text(result, correction="pending"):
    """The fixed-shape outcome note. The ``(automation_id, scheduled_at)``
    key fields and the ``correction`` status are stable; no ``type`` field
    is ever added."""
    if correction not in CORRECTION_STATUSES:
        raise ValueError("correction status must be one of %s" % (CORRECTION_STATUSES,))
    outcome = result.get("outcome")
    if outcome not in TERMINAL_OUTCOMES:
        raise ValueError("outcome note requires an explicit terminal outcome")
    parts = [
        NOTE_PREFIX.rstrip("|"),
        "automation_id=%s" % result["automation_id"],
        "scheduled_at=%s" % result["scheduled_at"],
        "outcome=%s" % outcome,
        "session_id=%s" % (result.get("session_id") or UNKNOWN),
        "error=%s" % (result.get("error_class") or UNKNOWN),
        "retryable=%s" % _bool_token(result.get("retryable")),
        "correction=%s" % correction,
    ]
    return "|".join(parts)


def _bool_token(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return UNKNOWN


def _outcome_data_fields(note_text):
    """The outcome-data field dict of an outcome note: the fixed data
    fields only, the writer-managed ``correction`` status excluded so the
    idempotency decision compares what the runtime observed, never a
    status this module itself flips."""
    fields = parse_outcome_note(note_text)
    if fields is None:
        return None
    return {name: fields.get(name) for name in OUTCOME_DATA_FIELDS}


def parse_outcome_note(note_text):
    """Parse an outcome note into its field dict, or None when the text is
    not an outcome note. Unknown fields are tolerated for forward
    compatibility; the key fields must parse."""
    if not isinstance(note_text, str) or not note_text.startswith(NOTE_PREFIX):
        return None
    fields = {}
    for chunk in note_text.split("|"):
        if not chunk or "=" not in chunk:
            continue
        key, _, value = chunk.partition("=")
        fields[key] = value
    if "automation_id" not in fields or "scheduled_at" not in fields:
        return None
    return fields


def outcome_note_key(note_text):
    fields = parse_outcome_note(note_text)
    if fields is None:
        return None
    return (fields["automation_id"], fields["scheduled_at"])


def _load_state(state_path):
    raw = Path(state_path).read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def _atomic_write(path, payload_bytes):
    directory = os.path.dirname(os.path.abspath(str(path))) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".fire-outcome-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload_bytes)
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _targeted_notes_edit(state_path, mutate):
    """One targeted notes[] edit under the existing writer rule: read,
    decide, re-read immediately before the atomic replace, retry once on
    drift, and report a second drift as a recorded loss without writing.

    ``mutate(state_dict) -> (new_notes, outcome_dict) | None`` returns the
    new notes array and the outcome to report, or None when the decision is
    a no-op under the freshly read state (idempotent reuse, conflicting
    data, absent target).
    """
    for _attempt in (0, 1):
        raw, state = _load_state(state_path)
        decision = mutate(state)
        if decision is None:
            return None
        new_notes, outcome = decision
        fresh_raw, _ = _load_state(state_path)
        if fresh_raw != raw:
            continue  # drift: retry the whole decision against fresh bytes
        payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        _atomic_write(state_path, payload.encode("utf-8"))
        return outcome
    return {
        "status": "unknown",
        "reason": "state-drift-unresolved",
        "note": "second drift recorded as a loss; no write performed",
    }


def record_outcome_note(state_path, result, now_iso):
    """Record one outcome note in the scheduler state's existing notes[]
    array, idempotent by the exact ``(automation_id, scheduled_at)`` key:
    an identical outcome-data note is reused unchanged, conflicting outcome
    data is reported unknown with no write, and retention keeps at most the
    newest 30 outcome notes by ``scheduled_at`` regardless of correction
    status, pruning only same-prefix older notes and preserving unrelated
    notes. A non-terminal result is unknown and writes nothing. The
    idempotency decision compares the outcome-data fields only; the
    writer-managed ``correction`` status is excluded, so re-recording
    identical outcome data after this module flipped the note to done or
    ambiguous is idempotent reuse, never a conflict."""
    if result.get("outcome") not in TERMINAL_OUTCOMES:
        return {"status": "unknown", "reason": "non-terminal-outcome-no-write",
                "observed_outcome": result.get("outcome")}
    note_text = outcome_note_text(result, correction="pending")
    key = outcome_note_key(note_text)
    candidate_data = _outcome_data_fields(note_text)

    def mutate(state):
        notes = state.get("notes")
        if not isinstance(notes, list):
            notes = []
            state["notes"] = notes
        for existing in notes:
            note_value = existing.get("note") if isinstance(existing, dict) else None
            if outcome_note_key(note_value) == key:
                return None  # same-key note present; conflict decided below on data fields
        notes.append({"at": now_iso, "note": note_text})
        pruned = _apply_retention(notes)
        reason = "recorded"
        if pruned:
            reason = "recorded-with-retention-prune"
        return (notes, {"status": "recorded", "reason": reason,
                        "note": note_text, "pruned": pruned})

    outcome = _targeted_notes_edit(state_path, mutate)
    if outcome is None:
        existing = _find_note(state_path, key)
        if existing is None:
            return {"status": "unknown", "reason": "outcome-note-absent-after-noop"}
        if _outcome_data_fields(existing) == candidate_data:
            return {"status": "unchanged", "reason": "identical-note-reused",
                    "note": existing}
        return {"status": "unknown", "reason": "conflicting-outcome-data",
                "note": existing}
    return outcome


def _apply_retention(notes):
    """Keep at most the newest 30 outcome notes by ``scheduled_at``
    regardless of correction status; prune only same-prefix older notes and
    preserve unrelated notes. Returns the pruned note texts."""
    outcome_entries = []
    for index, entry in enumerate(notes):
        key = outcome_note_key(entry.get("note") if isinstance(entry, dict) else None)
        if key is None:
            continue
        try:
            scheduled_at = int(key[1])
        except (TypeError, ValueError):
            scheduled_at = None
        outcome_entries.append((index, scheduled_at, entry))
    pruned = []
    if len(outcome_entries) <= RETENTION_CAP:
        return pruned
    # newest first by scheduled_at; unparseable keys sort oldest
    ordered = sorted(
        outcome_entries,
        key=lambda item: (-(item[1] if item[1] is not None else float("-inf"))),
    )
    keep_indices = {item[0] for item in ordered[:RETENTION_CAP]}
    outcome_indices = {item[0] for item in outcome_entries}
    kept = []
    for index, entry in enumerate(notes):
        if index not in outcome_indices or index in keep_indices:
            kept.append(entry)
        else:
            pruned.append(entry.get("note"))
    notes[:] = kept
    return pruned


def _find_note(state_path, key):
    try:
        _, state = _load_state(state_path)
    except (OSError, ValueError):
        return None
    for existing in state.get("notes") or []:
        note_value = existing.get("note") if isinstance(existing, dict) else None
        if outcome_note_key(note_value) == key:
            return note_value
    return None


def update_correction_status(state_path, automation_id, scheduled_at_ms,
                             new_status, now_iso=None):
    """Flip one outcome note's ``correction`` status (pending -> done once
    the memory index confirms the correction, or -> ambiguous on a
    conflicting entry) as one targeted notes[] edit under the same
    drift-retry rule. Never touches unrelated notes."""
    if new_status not in CORRECTION_STATUSES:
        raise ValueError("correction status must be one of %s" % (CORRECTION_STATUSES,))
    key = (str(automation_id), str(int(scheduled_at_ms)))

    def mutate(state):
        notes = state.get("notes")
        if not isinstance(notes, list):
            return None
        for entry in notes:
            note_value = entry.get("note") if isinstance(entry, dict) else None
            if outcome_note_key(note_value) == key:
                fields = parse_outcome_note(note_value)
                fields["correction"] = new_status
                updated = "|".join(
                    [NOTE_PREFIX.rstrip("|")]
                    + ["%s=%s" % (k, v) for k, v in fields.items()]
                )
                if updated == note_value:
                    return None
                if now_iso is not None and isinstance(entry, dict):
                    entry["at"] = now_iso
                entry["note"] = updated
                return (notes, {"status": "updated", "reason":
                                "correction-%s" % new_status, "note": updated})
        return None

    outcome = _targeted_notes_edit(state_path, mutate)
    if outcome is None:
        existing = _find_note(state_path, key)
        if existing is None:
            return {"status": "unknown", "reason": "outcome-note-absent"}
        return {"status": "unchanged", "reason": "status-already-%s" % new_status,
                "note": existing}
    return outcome


# ---------------------------------------------------------------------------
# Memory correction (append-first keyed supersession entry)
# ---------------------------------------------------------------------------


def correction_line_text(result):
    """The keyed correction line: exact key
    ``(automation_id, scheduled_at)``, explicit
    ``supersedes=<automation_id>@<scheduled_at>`` identity, one line, in
    the append-first one-line entry shape the memory index uses."""
    parts = [
        CORRECTION_PREFIX.rstrip("|"),
        "automation_id=%s" % result["automation_id"],
        "scheduled_at=%s" % result["scheduled_at"],
        "outcome=%s" % result.get("outcome"),
        "supersedes=%s@%s" % (result["automation_id"], result["scheduled_at"]),
        "session_id=%s" % (result.get("session_id") or UNKNOWN),
        "error=%s" % (result.get("error_class") or UNKNOWN),
        "retryable=%s" % _bool_token(result.get("retryable")),
    ]
    return "|".join(parts)


def _correction_key(automation_id, scheduled_at_ms):
    return "%sautomation_id=%s|scheduled_at=%s" % (
        CORRECTION_PREFIX, automation_id, int(scheduled_at_ms))


def _decide_from_lines(lines, automation_id, scheduled_at_ms,
                       expected_line=None, armed_check=True):
    """One append-first decision against the given index lines: absent,
    complete, ambiguous, blocked (armed target not uniquely identified),
    or None when absent-and-unique (appendable). The armed-target check is
    an append-side precondition only; a plain exact-key read skips it. With
    an ``expected_line``, a single existing body that differs from it is a
    conflict (ambiguous), never a coalescible match."""
    key = _correction_key(automation_id, scheduled_at_ms)
    matched = [line for line in lines if line.startswith(key)]
    if matched:
        bodies = {line for line in matched if line.startswith(CORRECTION_PREFIX)}
        if len(bodies) > 1 or (expected_line is not None
                               and bodies != {expected_line}):
            return {"status": "ambiguous", "reason": "conflicting-entries-present",
                    "matched": sorted(bodies)}
        return {"status": "complete", "reason": "identical-entry-present",
                "line": matched[0]}
    if not armed_check:
        return None  # plain read: absent, no armed-target precondition
    armed = _armed_matches(lines, automation_id)
    if len(armed) != 1:
        return {"status": "blocked",
                "reason": "armed-target-not-uniquely-identified",
                "armed_matches": armed}
    return None  # absent and uniquely identified: appendable


def _index_lines(index_path):
    path = Path(index_path)
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def read_correction(index_path, automation_id, scheduled_at_ms,
                    expected_line=None):
    """Read the exact correction key from the index: absent, complete (an
    identical entry), or ambiguous (conflicting entries). With an
    ``expected_line``, a single existing body that differs from it is
    ambiguous too, so a caller that derived the expected body can gate a
    done-flip on a real body match instead of any same-key hit."""
    decision = _decide_from_lines(_index_lines(index_path), automation_id,
                                  scheduled_at_ms, expected_line=expected_line,
                                  armed_check=False)
    if decision is None:
        return {"status": "absent", "matched": []}
    if decision["status"] == "complete":
        return {"status": "complete", "matched": [decision["line"]]}
    return {"status": decision["status"], "matched": decision.get("matched", [])}


def find_armed_target(index_path, automation_id, scheduled_at_ms):
    """Locate the armed memory line naming this carrier. A line matches
    when it names the automation id and is neither the correction entry
    nor an outcome-record surface. Zero or multiple matches are not a
    uniquely identified target."""
    armed = _armed_matches(_index_lines(index_path), automation_id)
    return {"unique": len(armed) == 1, "count": len(armed), "matched": armed}


def _armed_matches(lines, automation_id):
    return [
        line
        for line in lines
        if automation_id in line
        and not line.startswith(CORRECTION_PREFIX)
        and not line.startswith(NOTE_PREFIX)
    ]


def append_correction(index_path, result):
    """Append the keyed correction entry, append-first: read the exact key
    first (identical entry is complete, conflicting entries are ambiguous,
    absent may append only when the armed target is uniquely identified);
    re-read before the append and let a drift retry coalesce with a peer's
    identical correction or report a conflict as ambiguous. The armed
    memory line is never rewritten. A non-terminal result is unknown and
    appends nothing."""
    if result.get("outcome") not in TERMINAL_OUTCOMES:
        return {"status": "unknown", "reason": "non-terminal-outcome-no-write",
                "observed_outcome": result.get("outcome")}
    for _attempt in (0, 1):
        before = _read_bytes(index_path)
        candidate_line = correction_line_text(result)
        decision = _decide_from_lines(
            _split_lines(before), result["automation_id"],
            int(result["scheduled_at"]), expected_line=candidate_line)
        if decision is not None:
            return decision
        line = candidate_line
        if _read_bytes(index_path) != before:
            continue  # drifted between decision and write: retry once
        payload = before + (b"" if not before or before.endswith(b"\n") else b"\n") \
            + line.encode("utf-8") + b"\n"
        _atomic_write(index_path, payload)
        return {"status": "appended", "reason": "correction-appended", "line": line}
    return {"status": "unknown", "reason": "index-drift-unresolved",
            "note": "second drift recorded as a loss; no append performed"}


def _read_bytes(index_path):
    path = Path(index_path)
    return path.read_bytes() if path.is_file() else b""


def _split_lines(raw):
    return raw.decode("utf-8", errors="replace").splitlines()


def rederive_missing_corrections(db_path, index_path, workspace_key,
                                 automation_id=None, state_path=None,
                                 since_ms=None):
    """Re-derive missing corrections from terminal runtime rows still
    retained for the workspace: for each terminal row's exact key, read the
    index; an absent correction retries the append (coalescing with a
    peer's identical entry), a conflicting body is reported ambiguous, and
    a confirmed correction marks the outcome note resolved (correction=done)
    only after the index confirms the exact derived body: a single
    same-key entry whose body differs from the derived body is ambiguous,
    keeps the note pending, and writes nothing to the index. Aged-out
    state notes are re-derived
    from the retained runtime rows; a run row aged out or a source
    unavailable yields unknown and infers nothing. An unavailable source
    (missing database, db error, missing table, or missing required
    columns) is reported as one workspace-level unknown entry instead of an
    indistinguishable empty report; a present store with no retained rows
    still reports empty (the aged-out case)."""
    report = []
    if since_ms is None:
        since_ms = 0
    try:
        runs = read_workspace_runs(db_path, workspace_key, since_ms)
    except SourceUnavailable as exc:
        # the unavailable source must stay visible: one workspace-level
        # unknown entry instead of an empty report that reads as "no runs
        # retained"; no outcome is inferred and nothing is written
        report.append(exc.unknown_payload())
        return report
    for run in runs:
        if automation_id is not None and run["automation_id"] != automation_id:
            continue
        if run["outcome"] not in TERMINAL_OUTCOMES:
            report.append({"automation_id": run["automation_id"],
                           "scheduled_at": run["scheduled_at"],
                           "status": "unknown", "reason": "nonterminal"})
            continue
        result = read_fire_outcome(db_path, run["automation_id"],
                                   run["scheduled_at"], workspace_key)
        if result.get("status") != "terminal":
            report.append({"automation_id": run["automation_id"],
                           "scheduled_at": run["scheduled_at"],
                           "status": "unknown", "reason": result.get("reason")})
            continue
        append_outcome = append_correction(index_path, result)
        entry = {"automation_id": run["automation_id"],
                 "scheduled_at": run["scheduled_at"],
                 "status": append_outcome.get("status"),
                 "reason": append_outcome.get("reason")}
        # mark the note resolved only after the index confirms the exact
        # derived body: any single same-key line is not enough, a
        # conflicting body keeps the note pending and is reported
        # ambiguous, and nothing is written to the index
        confirmed = read_correction(index_path, run["automation_id"],
                                    run["scheduled_at"],
                                    expected_line=correction_line_text(result))
        if confirmed["status"] == "complete" and state_path is not None:
            marked = update_correction_status(
                state_path, run["automation_id"], run["scheduled_at"], "done")
            entry["note_status"] = marked.get("status")
            entry["note_reason"] = marked.get("reason")
        elif confirmed["status"] == "ambiguous":
            entry["index_status"] = "ambiguous"
        report.append(entry)
    return report


# ---------------------------------------------------------------------------
# ISO stamps
# ---------------------------------------------------------------------------


def iso_from_epoch_ms(epoch_ms):
    return datetime.fromtimestamp(int(epoch_ms) / 1000, tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CLI (explicit paths; the survey arm invokes these mechanically)
# ---------------------------------------------------------------------------


def _add_common(parser):
    parser.add_argument("--db", default=None,
                        help="explicit task-index database path (default: "
                             "ZCODE_DATA_BASE_DIR then ~/.zcode/v2/tasks-index.sqlite)")
    parser.add_argument("--workspace-key", required=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_read = sub.add_parser("read-outcome", help="read one terminal fire outcome")
    _add_common(p_read)
    p_read.add_argument("--automation-id", required=True)
    p_read.add_argument("--scheduled-at", type=int, required=True, help="epoch ms")

    p_overlaps = sub.add_parser("overlaps", help="report overlap candidates")
    _add_common(p_overlaps)
    p_overlaps.add_argument("--since-ms", type=int, default=None,
                            help="lower bound for recent runs (default: now-24h)")

    p_record = sub.add_parser("record-outcome",
                              help="read the outcome and record one state note")
    _add_common(p_record)
    p_record.add_argument("--automation-id", required=True)
    p_record.add_argument("--scheduled-at", type=int, required=True, help="epoch ms")
    p_record.add_argument("--state", required=True,
                          help="explicit scheduler-state path (required; never defaulted)")
    p_record.add_argument("--at", default=None, help="ISO 8601 stamp for the note")

    p_correction = sub.add_parser("append-correction",
                                  help="append the keyed memory correction")
    _add_common(p_correction)
    p_correction.add_argument("--automation-id", required=True)
    p_correction.add_argument("--scheduled-at", type=int, required=True, help="epoch ms")
    p_correction.add_argument("--index", required=True,
                              help="explicit memory-index path (required; never defaulted)")

    p_rederive = sub.add_parser("rederive-corrections",
                                help="re-derive missing corrections from retained rows")
    _add_common(p_rederive)
    p_rederive.add_argument("--index", required=True)
    p_rederive.add_argument("--state", default=None)
    p_rederive.add_argument("--since-ms", type=int, default=0)

    args = parser.parse_args(argv)
    db_path = resolve_db_path(args.db)

    if args.command == "read-outcome":
        result = read_fire_outcome(db_path, args.automation_id, args.scheduled_at,
                                   args.workspace_key)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "overlaps":
        since = args.since_ms
        if since is None:
            since = int(datetime.now(tz=timezone.utc).timestamp() * 1000) - DEFAULT_WINDOW_MS
        try:
            runs = read_workspace_runs(db_path, args.workspace_key, since)
        except SourceUnavailable as exc:
            # report the unavailable source as a visible unknown entry
            # instead of an empty candidate list
            print(json.dumps([exc.unknown_payload()], indent=2, sort_keys=True))
            return 0
        print(json.dumps(find_overlaps(runs), indent=2, sort_keys=True))
        return 0

    if args.command == "record-outcome":
        result = read_fire_outcome(db_path, args.automation_id, args.scheduled_at,
                                   args.workspace_key)
        if result.get("status") != "terminal":
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1
        stamp = args.at or iso_from_epoch_ms(
            datetime.now(tz=timezone.utc).timestamp() * 1000)
        recorded = record_outcome_note(args.state, result, stamp)
        recorded["outcome_read"] = result
        print(json.dumps(recorded, indent=2, sort_keys=True))
        return 0

    if args.command == "append-correction":
        result = read_fire_outcome(db_path, args.automation_id, args.scheduled_at,
                                   args.workspace_key)
        if result.get("status") != "terminal":
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1
        appended = append_correction(args.index, result)
        print(json.dumps(appended, indent=2, sort_keys=True))
        return 0

    if args.command == "rederive-corrections":
        report = rederive_missing_corrections(
            db_path, args.index, args.workspace_key,
            state_path=args.state, since_ms=args.since_ms)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
