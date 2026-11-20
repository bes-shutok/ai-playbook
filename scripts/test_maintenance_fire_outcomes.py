#!/usr/bin/env python3
"""Selftest for maintenance_fire_outcomes.py (warning-only post-fire
verification arm; plan
docs/history/plans/2026-11-05-automation-fire-time-failure-verification.md
Task 1).

Every fixture is hermetic: the task-index SQLite database, the scheduler
state file, and the memory index are temporary paths injected explicitly
into every helper and CLI call; fixed UTC epochs are pinned; no helper is
ever invoked without an explicit path, and a suite-level guard asserts the
live scheduler state and the live memory-index surfaces are byte-unchanged
across the whole suite.

Covered: terminal success and failure recording, duplicate observation,
nonterminal and missing-event unknowns (no state or memory write), absent
error detail (error=unknown), recurring-carrier overlap with both run ids,
missing prompt (mandate_match unknown), the newest-30 retention cap pruning
only same-prefix older notes, append-first keyed supersession with the
armed line preserved, failed-append recovery through re-derivation,
concurrent identical observation coalescing on both the state and the index
drift retry, conflicting outcomes (state unknown, index ambiguous), missing
database/table/columns unknowns, sensitive raw-field omission, the
read-only connection contract, the path resolver precedence, the CLI
entry points, unavailable-source visibility on the re-derivation and
overlaps paths (a workspace-level unknown entry instead of an
indistinguishable empty list, the aged-out empty read unchanged), the
skill-text read-side suppression clause witness, the re-derivation done
flip gated on the exact derived correction body (a single conflicting
body keeps the note pending with the index unchanged, a matching body
flips done), and outcome-data-only idempotency that reuses a note after
a correction-status flip while a differing outcome datum still conflicts.

The dispatch cells (plan
docs/history/plans/2026-11-18-fire-outcome-dispatch-failure-skip-blind-spot.md
Task 1) cover the failed_to_dispatch and skipped classes reading terminal
failed through their dispatch-failed and asleep-skip tokens with the
compound attempts value, the claimed negative boundary, dispatch precedence
over session attribution, the attempts schema gate over the generalized
drop helper, record and correction end to end, raw-message containment,
and the read-only connect witness.

The Task 2 dispatch cells (same plan, Task 2) retain the dispatch-terminal
interval as an overlap candidate while the claimed row forms none,
re-derive a missing keyed correction from a retained dispatch-terminal
row, list the dispatch-terminal member as terminal evidence in the landed
census CLI verdict (a claimed row stays in the unknown class), and pin
the appended correction's suppression key to the armed line's carrier-id
token and fire instant.

The census cells (plan
docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md
Task 1) cover runs-driven member enumeration, the recurring and
not-yet-fired exclusions, the nonterminal and aged-out unknown class, the
window default and its override, the unwired signal, the read-only connect
witness, and error containment.

The Task 2 census matrix cells pin the CLI dispatch verdict, the note,
correction, and ambiguous trace reads, the unreadable and absent surface
degradation, the mixed traced/untraced set, and the read-only negative
control with HOME and ZCODE_DATA_BASE_DIR redirected.
"""

import json
import re
import sqlite3
import sys
import unittest.mock as mock
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import maintenance_fire_outcomes as mfo

# --- pinned UTC epochs (all fixtures use these; nothing reads the clock) ---
FIRE_MS = 1793934000000          # 2026-11-06T03:00:00Z, the incident fire time
LATE_FIRE_MS = 1793937600000     # 2026-11-06T04:00:00Z
RUN_END_MS = FIRE_MS + 60_000    # terminal updated_at one minute after fire
OVERLAP_FIRE_MS = FIRE_MS + 30_000
OVERLAP_END_MS = FIRE_MS + 90_000
NOW_ISO = "2026-11-06T03:05:00+00:00"
CENSUS_NOW_MS = FIRE_MS + 48 * 60 * 60 * 1000  # pinned census clock for the function-level window cells

WORKSPACE = "/fixtures/repo"
AUTO_ID = "automation-1111"
AUTO_ID_OTHER = "automation-2222"
AUTO_ID_RECURRING = "automation-recurring"
SESSION_ID = "sess-abcdef01-2345-6789"
RAW_MESSAGE = "exceed quota limit"
RAW_REQUEST_ID = "req-9f8e7d6c-5b4a"
# a raw localized host error as the dispatch rows' error column carries it;
# it must never reach any persisted surface (plan Task 1 safety witness)
RAW_DISPATCH_ERROR = "Verbindung zum Ausfuehrungshost fehlgeschlagen (Fehler 10060)"

SCHEMA_SQL = [
    """CREATE TABLE automation_runs (
        run_id TEXT PRIMARY KEY,
        automation_id TEXT NOT NULL,
        workspace_key TEXT NOT NULL,
        scheduled_at INTEGER,
        trigger TEXT NOT NULL DEFAULT 'schedule',
        dispatch_status TEXT NOT NULL DEFAULT 'claimed',
        outcome TEXT,
        session_id TEXT,
        error TEXT,
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )""",
    """CREATE TABLE tasks (
        workspace_key TEXT NOT NULL,
        task_id TEXT NOT NULL,
        meta_json TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (workspace_key, task_id)
      )""",
    """CREATE TABLE automations (
        automation_id TEXT PRIMARY KEY,
        workspace_key TEXT NOT NULL,
        prompt TEXT NOT NULL DEFAULT '',
        recurring INTEGER NOT NULL DEFAULT 1
      )""",
]


def run_row(automation_id, scheduled_at, outcome, session_id, updated_at,
            run_id=None, dispatch_status="dispatched", attempts=1,
            error="{}"):
    return (
        run_id or "%s:%s" % (automation_id, scheduled_at),
        automation_id,
        WORKSPACE,
        scheduled_at,
        "schedule",
        dispatch_status,
        outcome,
        session_id,
        error,
        attempts,
        scheduled_at - 1000,
        updated_at,
    )


def build_db(tmp_path, runs=(), tasks_meta=None, automations=(),
             drop_required_column=None, name="tasks-index.sqlite"):
    db_path = tmp_path / name
    conn = sqlite3.connect(str(db_path))
    for statement in SCHEMA_SQL:
        if drop_required_column and drop_required_column in statement \
                and "automation_runs" in statement:
            # build a schema missing the required column (missing-columns
            # arm): rename the named column's own DDL fragment whatever its
            # type and constraints, so any required column (outcome,
            # attempts, ...) can be dropped, not only the outcome column
            statement = re.sub(
                r"(?m)^(\s*)%s\s+[^,]+" % re.escape(drop_required_column),
                r"\1%s_x TEXT" % drop_required_column,
                statement, count=1)
        conn.execute(statement)
    for row in runs:
        conn.execute(
            "INSERT INTO automation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
    for workspace_key, task_id, meta in (tasks_meta or []):
        conn.execute("INSERT INTO tasks VALUES (?,?,?)", (workspace_key, task_id, meta))
    for automation in automations:
        # positional automations inserts grew the recurring column (census
        # fixture amendment); suite fixtures are one-shot records unless a
        # cell passes an explicit recurring value
        automation_id, prompt = automation[0], automation[1]
        recurring = automation[2] if len(automation) > 2 else 0
        conn.execute(
            "INSERT INTO automations (automation_id, workspace_key, prompt,"
            " recurring) VALUES (?,?,?,?)",
            (automation_id, WORKSPACE, prompt, recurring))
    conn.commit()
    conn.close()
    return db_path


def failed_meta():
    """A live-shaped meta_json: the raw message/detail/request id sit next
    to the structured attribution the adapter may extract."""
    return json.dumps({
        "taskId": SESSION_ID,
        "cronAutomationId": AUTO_ID,
        "lastError": {
            "code": "1005",
            "message": RAW_MESSAGE,
            "detail": "turn failed request=%s provider=acct reason=quota" % RAW_REQUEST_ID,
            "attribution": {
                "source": "provider",
                "exceptionKind": "provider_business",
                "reason": "invalid_request",
                "retryable": False,
                "providerErrorCode": "1005",
            },
        },
    })


def write_state(tmp_path, notes=None):
    state_path = tmp_path / "scheduler-state.json"
    state = {
        "schema": 4,
        "last_run_at": "2026-11-06T02:00:00+00:00",
        "children": [],
        "notes": notes if notes is not None else [],
        "alert": None,
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state_path


def write_index(tmp_path, lines, name="MEMORY.md"):
    index_path = tmp_path / name
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def armed_line(automation_id):
    return ("scheduler armed one-shot %s fires at 2026-11-06T03:00:00Z "
            "(mandate: nightly maintenance)" % automation_id)


@pytest.fixture
def failed_db(tmp_path):
    return build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        tasks_meta=[(WORKSPACE, SESSION_ID, failed_meta())],
        automations=[(AUTO_ID, "Run the   maintenance turn")],
    )


@pytest.fixture
def succeeded_db(tmp_path):
    return build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "succeeded", SESSION_ID, RUN_END_MS)],
        automations=[(AUTO_ID, "Run the   maintenance turn")],
    )


@pytest.fixture
def dispatch_failed_db(tmp_path):
    # the witnessed incident shape: a final failed_to_dispatch verdict,
    # outcome NULL, attempts 4, the raw localized host error in the error
    # column, no session id (the payload never ran)
    return build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                      dispatch_status="failed_to_dispatch", attempts=4,
                      error=RAW_DISPATCH_ERROR)],
        name="dispatch-failed.sqlite",
    )


@pytest.fixture
def skipped_db(tmp_path):
    # the live skipped shape (2026-11-18 probe receipt): attempts 0,
    # outcome NULL
    return build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                      dispatch_status="skipped", attempts=0,
                      error=RAW_DISPATCH_ERROR)],
        name="dispatch-skipped.sqlite",
    )


# ---------------------------------------------------------------------------
# Terminal success and failure recording
# ---------------------------------------------------------------------------


def test_success_records_note_and_keyed_correction(tmp_path, succeeded_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(succeeded_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["outcome"] == "succeeded"
    assert result["session_id"] == SESSION_ID
    assert result["error_class"] == mfo.UNKNOWN

    recorded = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert recorded["status"] == "recorded"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(state["notes"]) == 1
    note = state["notes"][0]
    assert note["at"] == NOW_ISO
    assert note["note"].startswith(mfo.NOTE_PREFIX)
    assert "correction=pending" in note["note"]
    assert "automation_id=%s" % AUTO_ID in note["note"]
    assert "scheduled_at=%s" % FIRE_MS in note["note"]
    assert "outcome=succeeded" in note["note"]
    assert "session_id=%s" % SESSION_ID in note["note"]
    assert "type=" not in note["note"]

    appended = mfo.append_correction(index_path, result)
    assert appended["status"] == "appended"
    index_text = index_path.read_text(encoding="utf-8")
    # the armed memory line stays intact; the correction supersedes it keyed
    assert armed_line(AUTO_ID) in index_text
    lines = index_text.splitlines()
    correction = [l for l in lines if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(correction) == 1
    assert "automation_id=%s" % AUTO_ID in correction[0]
    assert "scheduled_at=%s" % FIRE_MS in correction[0]
    assert "supersedes=%s@%s" % (AUTO_ID, FIRE_MS) in correction[0]
    assert "outcome=succeeded" in correction[0]
    assert "session_id=%s" % SESSION_ID in correction[0]

    confirmed = mfo.read_correction(index_path, AUTO_ID, FIRE_MS)
    assert confirmed["status"] == "complete"
    marked = mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")
    assert marked["status"] == "updated"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=done" in state["notes"][0]["note"]


def test_failure_records_structured_error_class(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["outcome"] == "failed"
    assert result["error_class"] == "provider_business/invalid_request"
    assert result["retryable"] is False

    recorded = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert recorded["status"] == "recorded"
    note = json.loads(state_path.read_text(encoding="utf-8"))["notes"][0]["note"]
    assert "error=provider_business/invalid_request" in note
    assert "retryable=false" in note
    assert "scheduled_at=%s" % FIRE_MS in note

    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    appended = mfo.append_correction(index_path, result)
    assert appended["status"] == "appended"
    correction = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                  if l.startswith(mfo.CORRECTION_PREFIX)][0]
    assert "outcome=failed" in correction
    assert "scheduled_at=%s" % FIRE_MS in correction
    assert "error=provider_business/invalid_request" in correction
    assert "supersedes=%s@%s" % (AUTO_ID, FIRE_MS) in correction


def test_no_type_field_in_note_grammar(tmp_path, failed_db):
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    text = mfo.outcome_note_text(result)
    fields = mfo.parse_outcome_note(text)
    assert "type" not in fields
    assert fields["correction"] == "pending"
    assert set(fields) == {
        "automation_id", "scheduled_at", "outcome", "session_id",
        "error", "retryable", "correction",
    }


# ---------------------------------------------------------------------------
# Unknown without write: duplicate, nonterminal, missing event, bad schema
# ---------------------------------------------------------------------------


def test_duplicate_observation_is_idempotent(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    first = mfo.record_outcome_note(state_path, result, NOW_ISO)
    second = mfo.record_outcome_note(state_path, result, "2026-11-06T04:05:00+00:00")
    assert second["status"] == "unchanged"
    assert second["reason"] == "identical-note-reused"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(state["notes"]) == 1
    assert state["notes"][0]["at"] == NOW_ISO  # the first stamp is kept


def test_nonterminal_yields_unknown_and_writes_nothing(tmp_path):
    db_path = build_db(tmp_path,
                       runs=[run_row(AUTO_ID, FIRE_MS, "running", SESSION_ID,
                                     RUN_END_MS)])
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    before_state = state_path.read_bytes()
    before_index = index_path.read_bytes()
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "unknown"
    assert result["reason"] == "nonterminal"
    assert result["observed_outcome"] == "running"
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "unknown"
    assert mfo.append_correction(index_path, result)["status"] == "unknown"
    assert state_path.read_bytes() == before_state
    assert index_path.read_bytes() == before_index


def test_missing_event_yields_unknown_and_writes_nothing(tmp_path):
    db_path = build_db(tmp_path)  # empty ledger
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "unknown"
    assert result["reason"] == "missing-event"
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "unknown"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["notes"] == []


def test_ambiguous_multiple_rows_yield_unknown(tmp_path):
    db_path = build_db(tmp_path, runs=[
        run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS),
        run_row(AUTO_ID, FIRE_MS, "failed", "sess-other", RUN_END_MS,
                run_id="dup-run"),
    ])
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "unknown"
    assert result["reason"] == "ambiguous"
    assert len(result["matched_run_ids"]) == 2


def test_unknown_database_and_schema_write_nothing(tmp_path):
    missing_db = tmp_path / "absent.sqlite"
    no_table_db = tmp_path / "empty.sqlite"
    conn = sqlite3.connect(str(no_table_db))
    conn.execute("CREATE TABLE unrelated (x INTEGER)")
    conn.commit()
    conn.close()
    bad_column_db = build_db(tmp_path, drop_required_column="outcome")
    state_path = write_state(tmp_path, notes=[{"at": "t0", "note": "keep me"}])
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    before_state = state_path.read_bytes()
    before_index = index_path.read_bytes()

    for db_path, reason in ((missing_db, "missing-database"),
                            (no_table_db, "missing-table"),
                            (bad_column_db, "missing-columns")):
        result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
        assert result["status"] == "unknown", db_path
        assert result["reason"] == reason, (db_path, result)
        outcome = mfo.record_outcome_note(state_path, result, NOW_ISO)
        assert outcome["status"] == "unknown"
        append = mfo.append_correction(index_path, result)
        assert append["status"] != "appended"

    assert state_path.read_bytes() == before_state
    assert index_path.read_bytes() == before_index
    assert json.loads(state_path.read_text(encoding="utf-8"))["notes"] == \
        [{"at": "t0", "note": "keep me"}]


# ---------------------------------------------------------------------------
# Dispatch-terminal classification (plan
# docs/history/plans/2026-11-18-fire-outcome-dispatch-failure-skip-blind-spot.md
# Task 1): the failed_to_dispatch and skipped classes read terminal failed
# with their class tokens, the claimed pre-dispatch state stays unknown and
# writes nothing, record and correction flow end to end, and the raw error
# column never reaches a persisted surface. Every cell carries dispatch in
# its name so the pinned -k dispatch selector collects it.
# ---------------------------------------------------------------------------


def test_dispatch_failed_read_classifies_terminal_failed(tmp_path, dispatch_failed_db):
    result = mfo.read_fire_outcome(dispatch_failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["outcome"] == "failed"
    assert result["error_class"] == "dispatch-failed/attempts=4"
    assert result["retryable"] is None
    assert result["session_id"] == mfo.UNKNOWN  # the payload never ran
    assert RAW_DISPATCH_ERROR not in json.dumps(result, sort_keys=True)


def test_dispatch_skipped_read_classifies_asleep_skip(tmp_path, skipped_db):
    result = mfo.read_fire_outcome(skipped_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["outcome"] == "failed"
    assert result["error_class"] == "asleep-skip/attempts=0"
    assert RAW_DISPATCH_ERROR not in json.dumps(result, sort_keys=True)


def test_dispatch_null_attempts_render_unknown_at_helper_seam():
    # the pinned suite schema declares attempts NOT NULL, so the null case
    # runs at the classification helper's seam, never through a DB row
    classed = mfo.dispatch_terminal_class("failed_to_dispatch", None)
    assert classed["outcome"] == "failed"
    assert classed["error_class"] == "dispatch-failed/attempts=unknown"
    assert mfo.dispatch_terminal_class("skipped", None)["error_class"] == \
        "asleep-skip/attempts=unknown"
    # non-dispatch verdicts classify to nothing
    assert mfo.dispatch_terminal_class("dispatched", 1) is None
    assert mfo.dispatch_terminal_class("claimed", 0) is None
    assert mfo.dispatch_terminal_class(None, 0) is None


def test_dispatch_claimed_empty_outcome_stays_unknown_and_writes_nothing(tmp_path):
    # the pre-dispatch state never classifies terminal: a claimed verdict
    # with an empty outcome keeps every path unknown, interval-free, and
    # write-free
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                    dispatch_status="claimed"),
            run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, "succeeded", "sess-peer",
                    OVERLAP_END_MS),
        ],
        name="dispatch-claimed.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    before_state = state_path.read_bytes()
    before_index = index_path.read_bytes()
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "unknown"
    assert result["reason"] == "nonterminal"
    assert result["dispatch_status"] == "claimed"
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "unknown"
    assert mfo.append_correction(index_path, result)["status"] == "unknown"
    # no overlap interval forms for the claimed row even beside a
    # time-overlapping terminal peer
    runs = mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000)
    assert mfo.find_overlaps(runs) == []
    # the rederivation walk reports a nonterminal entry and writes nothing
    report = mfo.rederive_missing_corrections(db_path, index_path, WORKSPACE,
                                              automation_id=AUTO_ID)
    assert len(report) == 1
    assert report[0]["status"] == "unknown"
    assert report[0]["reason"] == "nonterminal"
    assert state_path.read_bytes() == before_state
    assert index_path.read_bytes() == before_index


def test_dispatch_token_survives_session_id_precedence(tmp_path):
    # the dispatch verdict outranks session attribution: a dispatch-terminal
    # row that also carries a session id keeps the dispatch token; the
    # attribution branch runs only for genuinely executed failed rows
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, None, SESSION_ID, RUN_END_MS,
                      dispatch_status="failed_to_dispatch", attempts=4,
                      error=RAW_DISPATCH_ERROR)],
        tasks_meta=[(WORKSPACE, SESSION_ID, failed_meta())],
        name="dispatch-precedence.sqlite",
    )
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["error_class"] == "dispatch-failed/attempts=4"
    assert result["retryable"] is None
    assert result["session_id"] == SESSION_ID


def test_dispatch_failed_record_and_correct_end_to_end(tmp_path, dispatch_failed_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(dispatch_failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    recorded = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert recorded["status"] == "recorded"
    note = json.loads(state_path.read_text(encoding="utf-8"))["notes"][0]["note"]
    assert "outcome=failed" in note
    assert "error=dispatch-failed/attempts=4" in note
    assert "correction=pending" in note
    assert "session_id=%s" % mfo.UNKNOWN in note
    appended = mfo.append_correction(index_path, result)
    assert appended["status"] == "appended"
    correction = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                  if l.startswith(mfo.CORRECTION_PREFIX)][0]
    assert "outcome=failed" in correction
    assert "error=dispatch-failed/attempts=4" in correction
    assert "supersedes=%s@%s" % (AUTO_ID, FIRE_MS) in correction
    confirmed = mfo.read_correction(index_path, AUTO_ID, FIRE_MS)
    assert confirmed["status"] == "complete"
    marked = mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")
    assert marked["status"] == "updated"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=done" in state["notes"][0]["note"]


def test_dispatch_skipped_record_and_correct_end_to_end(tmp_path, skipped_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(skipped_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    recorded = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert recorded["status"] == "recorded"
    note = json.loads(state_path.read_text(encoding="utf-8"))["notes"][0]["note"]
    assert "error=asleep-skip/attempts=0" in note
    assert "correction=pending" in note
    assert "session_id=%s" % mfo.UNKNOWN in note
    appended = mfo.append_correction(index_path, result)
    assert appended["status"] == "appended"
    correction = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                  if l.startswith(mfo.CORRECTION_PREFIX)][0]
    assert "error=asleep-skip/attempts=0" in correction
    assert "supersedes=%s@%s" % (AUTO_ID, FIRE_MS) in correction


def test_dispatch_schema_gate_missing_attempts_reads_unknown(tmp_path):
    db_path = build_db(tmp_path, drop_required_column="attempts",
                       name="dispatch-missing-attempts.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "unknown"
    assert result["reason"] == "missing-columns"
    assert result["missing"] == ["attempts"]


def test_dispatch_raw_host_error_never_persisted(tmp_path, dispatch_failed_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(dispatch_failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"  # the classed row flows through the writes
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    mfo.append_correction(index_path, result)
    mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")
    note = json.loads(state_path.read_text(encoding="utf-8"))["notes"][0]["note"]
    for surface in (json.dumps(result, sort_keys=True),
                    state_path.read_text(encoding="utf-8"),
                    index_path.read_text(encoding="utf-8")):
        assert RAW_DISPATCH_ERROR not in surface
    # the persisted note carries only the token and the attempts count
    assert "error=dispatch-failed/attempts=4" in note


def test_dispatch_read_connect_opens_read_only_uri(tmp_path, dispatch_failed_db):
    real_connect = sqlite3.connect
    recorded = []

    def recording_connect(*args, **kwargs):
        recorded.append((args[0], kwargs))
        return real_connect(*args, **kwargs)

    with mock.patch.object(mfo.sqlite3, "connect",
                           side_effect=recording_connect):
        result = mfo.read_fire_outcome(dispatch_failed_db, AUTO_ID, FIRE_MS,
                                       WORKSPACE)
    assert result["status"] == "terminal"
    assert recorded
    for uri, kwargs in recorded:
        assert uri.startswith("file:")
        assert "mode=ro" in uri
        assert kwargs.get("uri") is True


# ---------------------------------------------------------------------------
# Dispatch-terminal retention (same plan, Task 2): the workspace overlap
# filter and the rederivation walk and the census retain a dispatch-terminal
# row as terminal non-success evidence; the claimed-and-empty row still
# forms no interval and stays in the unknown class; the appended keyed
# correction carries the suppression identity the survey matches on.
# ---------------------------------------------------------------------------


def test_dispatch_terminal_row_retained_as_overlap_candidate(tmp_path):
    # a dispatch-terminal row's interval (scheduled_at through updated_at)
    # is an overlap candidate: read_workspace_runs already returns the row,
    # so the RED leg is the overlap filter that dropped it as nonterminal
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                    dispatch_status="failed_to_dispatch", attempts=4,
                    error=RAW_DISPATCH_ERROR),
            run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, "succeeded", "sess-peer",
                    OVERLAP_END_MS),
        ],
        name="dispatch-overlap.sqlite",
    )
    runs = mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000)
    assert [run["run_id"] for run in runs] == [
        "%s:%s" % (AUTO_ID, FIRE_MS),
        "%s:%s" % (AUTO_ID_OTHER, OVERLAP_FIRE_MS),
    ]
    candidates = mfo.find_overlaps(runs)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert set(candidate["run_ids"]) == {
        "%s:%s" % (AUTO_ID, FIRE_MS),
        "%s:%s" % (AUTO_ID_OTHER, OVERLAP_FIRE_MS),
    }
    intervals = {iv["run_id"]: (iv["start"], iv["end"])
                 for iv in candidate["intervals"]}
    assert intervals["%s:%s" % (AUTO_ID, FIRE_MS)] == (FIRE_MS, RUN_END_MS)
    assert candidate["mandate_match"] == mfo.UNKNOWN  # no automations rows


def test_dispatch_claimed_row_forms_no_overlap_interval(tmp_path):
    # negative reuse of the claimed-and-empty boundary: the claimed row
    # joins no candidate even in a workspace whose dispatch-terminal row is
    # retained beside the same time-overlapping terminal peer
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                    dispatch_status="claimed"),
            run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, None, None, OVERLAP_END_MS,
                    dispatch_status="failed_to_dispatch", attempts=4,
                    error=RAW_DISPATCH_ERROR),
            run_row("automation-peer", FIRE_MS + 10_000, "succeeded",
                    "sess-peer", FIRE_MS + 50_000),
        ],
        name="dispatch-claimed-overlap.sqlite",
    )
    claimed_run_id = "%s:%s" % (AUTO_ID, FIRE_MS)
    runs = mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000)
    assert claimed_run_id in {run["run_id"] for run in runs}
    candidates = mfo.find_overlaps(runs)
    assert len(candidates) == 1  # only the dispatch-terminal + peer pair
    assert claimed_run_id not in candidates[0]["run_ids"]
    assert set(candidates[0]["run_ids"]) == {
        "%s:%s" % (AUTO_ID_OTHER, OVERLAP_FIRE_MS),
        "automation-peer:%s" % (FIRE_MS + 10_000),
    }


def test_dispatch_rederive_processes_member_with_missing_correction(
        tmp_path, dispatch_failed_db):
    # a retained dispatch-terminal member whose keyed correction is missing
    # is processed by the rederivation walk instead of being skipped as
    # nonterminal: the walk appends the keyed correction and the armed line
    # stays intact
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    report = mfo.rederive_missing_corrections(dispatch_failed_db, index_path,
                                              WORKSPACE)
    assert len(report) == 1
    entry = report[0]
    assert entry["automation_id"] == AUTO_ID
    assert entry["scheduled_at"] == FIRE_MS
    assert entry["status"] == "appended"
    index_text = index_path.read_text(encoding="utf-8")
    assert armed_line(AUTO_ID) in index_text  # armed line preserved
    corrections = [l for l in index_text.splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(corrections) == 1
    assert "outcome=failed" in corrections[0]
    assert "error=dispatch-failed/attempts=4" in corrections[0]
    # a second survey turn coalesces instead of duplicating
    report2 = mfo.rederive_missing_corrections(dispatch_failed_db, index_path,
                                               WORKSPACE)
    assert report2[0]["status"] == "complete"
    assert len([l for l in index_path.read_text(encoding="utf-8").splitlines()
                if l.startswith(mfo.CORRECTION_PREFIX)]) == 1


def test_census_dispatch_terminal_member_listed_terminal(tmp_path, capsys):
    # the landed census subcommand over a fixture holding a
    # dispatch-terminal one-shot row, invoked with explicit --since-ms and
    # explicit --db, --state, and --index paths per the suite's CLI
    # convention: the member is listed as terminal non-success evidence
    # (eligible) instead of the unknown nonterminal class
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                      dispatch_status="failed_to_dispatch", attempts=4,
                      error=RAW_DISPATCH_ERROR)],
        automations=[(AUTO_ID, "the maintenance turn")],
        name="census-dispatch-eligible.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc = mfo.main([
        "census", "--db", str(db_path), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000),
        "--state", str(state_path), "--index", str(index_path),
    ])
    assert rc == 0
    verdict = json.loads(capsys.readouterr().out)
    assert verdict["status"] == "ok"
    assert verdict["eligible_count"] == 1
    member = verdict["members"][0]
    assert member["automation_id"] == AUTO_ID
    assert member["scheduled_at"] == FIRE_MS
    assert member["dispatch_status"] == "failed_to_dispatch"
    assert member["class"] == "eligible"
    assert member["eligible"] is True
    assert member["unknown_reason"] is None
    assert verdict["unwired"] is True  # readable surfaces, zero traces
    # the terminal non-success evidence flows through the arm's writes
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["error_class"] == "dispatch-failed/attempts=4"
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == \
        "recorded"
    assert mfo.append_correction(index_path, result)["status"] == "appended"


def test_census_dispatch_claimed_row_stays_unknown(tmp_path, capsys):
    # census negative direction over the same landed subcommand: a
    # claimed-and-empty row stays in the unknown class and is never listed
    # as terminal evidence
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, None, None, RUN_END_MS,
                      dispatch_status="claimed")],
        automations=[(AUTO_ID, "the maintenance turn")],
        name="census-dispatch-claimed.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc = mfo.main([
        "census", "--db", str(db_path), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000),
        "--state", str(state_path), "--index", str(index_path),
    ])
    assert rc == 0
    verdict = json.loads(capsys.readouterr().out)
    assert verdict["status"] == "ok"
    assert verdict["eligible_count"] == 0
    member = verdict["members"][0]
    assert member["class"] == "unknown"
    assert member["eligible"] is False
    assert member["unknown_reason"] == "nonterminal"
    assert verdict["unwired"] == mfo.UNKNOWN


def test_dispatch_correction_suppression_key_matches_armed_line(
        tmp_path, dispatch_failed_db):
    # the survey's read-side suppression matches on (automation_id,
    # scheduled_at): the appended correction's automation_id equals the
    # armed line's carrier-id token and its scheduled_at equals the epoch
    # ms of the armed line's ISO instant
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(dispatch_failed_db, AUTO_ID, FIRE_MS,
                                   WORKSPACE)
    assert mfo.append_correction(index_path, result)["status"] == "appended"
    armed = [l for l in index_path.read_text(encoding="utf-8").splitlines()
             if "scheduler armed one-shot" in l][0]
    match = re.search(r"armed one-shot (\S+) fires at (\S+)", armed)
    carrier_id, instant = match.group(1), match.group(2)
    armed_epoch_ms = int(datetime.fromisoformat(
        instant.replace("Z", "+00:00")).timestamp() * 1000)
    assert armed_epoch_ms == FIRE_MS  # the armed instant is the fire time
    correction = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                  if l.startswith(mfo.CORRECTION_PREFIX)][0]
    fields = {}
    for chunk in correction.split("|"):
        if "=" in chunk:
            name, _, value = chunk.partition("=")
            fields[name] = value
    assert fields["automation_id"] == carrier_id
    assert fields["scheduled_at"] == str(armed_epoch_ms)


# ---------------------------------------------------------------------------
# Error attribution: absent detail and sensitive-field omission
# ---------------------------------------------------------------------------


def test_absent_error_detail_yields_unknown_class(tmp_path):
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        # no tasks row at all: attribution absent
    )
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert result["outcome"] == "failed"
    assert result["error_class"] == mfo.UNKNOWN
    assert result["retryable"] is None
    state_path = write_state(tmp_path)
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    note = json.loads(state_path.read_text(encoding="utf-8"))["notes"][0]["note"]
    assert "error=unknown" in note
    assert "retryable=unknown" in note


def test_absent_attribution_member_yields_unknown_class(tmp_path):
    partial = json.dumps({
        "lastError": {"attribution": {"exceptionKind": "provider_business"}}})
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        tasks_meta=[(WORKSPACE, SESSION_ID, partial)],
    )
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["error_class"] == mfo.UNKNOWN
    assert result["retryable"] is None


def test_sensitive_raw_fields_are_never_persisted(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    mfo.append_correction(index_path, result)
    mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")
    for surface in (json.dumps(result), state_path.read_text(encoding="utf-8"),
                    index_path.read_text(encoding="utf-8")):
        assert RAW_MESSAGE not in surface
        assert RAW_REQUEST_ID not in surface
        assert "providerErrorCode" not in surface
        assert "detail" not in surface


def test_sqlite_connection_is_read_only(tmp_path):
    db_path = build_db(tmp_path,
                       runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID,
                                     RUN_END_MS)])
    conn = mfo._connect_ro(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO automation_runs (run_id, automation_id,"
                         " workspace_key, created_at, updated_at)"
                         " VALUES ('x','y','z',1,2)")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Overlap candidates (post-fire, report-only)
# ---------------------------------------------------------------------------


def overlap_db(tmp_path, prompts=(("Run the   maintenance turn",),
                                  ("Run the maintenance turn",))):
    runs = [
        run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS),
        run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, "succeeded", "sess-peer",
                OVERLAP_END_MS),
    ]
    return build_db(
        tmp_path, runs=runs, name="overlap.sqlite",
        automations=[(AUTO_ID, prompts[0][0]), (AUTO_ID_OTHER, prompts[1][0])],
    )


def test_recurring_overlap_reported_with_both_run_ids(tmp_path):
    db_path = overlap_db(tmp_path)
    runs = mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000)
    candidates = mfo.find_overlaps(runs)
    assert len(candidates) == 1
    candidate = candidates[0]
    ids = set(candidate["run_ids"])
    assert "%s:%s" % (AUTO_ID, FIRE_MS) in ids
    assert "%s:%s" % (AUTO_ID_OTHER, OVERLAP_FIRE_MS) in ids
    assert candidate["mandate_match"] is True  # prompts normalize equal
    # non-overlapping intervals produce no candidate
    runs_disjoint = [dict(r) for r in runs]
    runs_disjoint[1]["scheduled_at"] = RUN_END_MS + 1
    runs_disjoint[1]["updated_at"] = RUN_END_MS + 1000
    assert mfo.find_overlaps(runs_disjoint) == []


def test_recurring_carrier_runs_are_included(tmp_path):
    runs = [
        run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS),
        run_row(AUTO_ID_RECURRING, FIRE_MS + 10_000, "succeeded", "sess-rec",
                FIRE_MS + 40_000),
    ]
    db_path = build_db(tmp_path, runs=runs,
                       automations=[(AUTO_ID, "prompt one"),
                                    (AUTO_ID_RECURRING, "prompt two")])
    candidates = mfo.find_overlaps(
        mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000))
    assert len(candidates) == 1
    assert candidates[0]["mandate_match"] is False  # both prompts differ


def test_missing_prompt_mandate_match_unknown(tmp_path):
    # no automations rows at all: prompts absent for both runs
    db_path = build_db(tmp_path, runs=[
        run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS),
        run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, "succeeded", "sess-peer",
                OVERLAP_END_MS),
    ])
    candidates = mfo.find_overlaps(
        mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000))
    assert len(candidates) == 1
    assert candidates[0]["mandate_match"] == mfo.UNKNOWN
    assert len(candidates[0]["run_ids"]) == 2


def test_nonterminal_rows_form_no_interval(tmp_path):
    db_path = build_db(tmp_path, runs=[
        run_row(AUTO_ID, FIRE_MS, "running", SESSION_ID, RUN_END_MS),
        run_row(AUTO_ID_OTHER, OVERLAP_FIRE_MS, "succeeded", "sess-peer",
                OVERLAP_END_MS),
    ])
    candidates = mfo.find_overlaps(
        mfo.read_workspace_runs(db_path, WORKSPACE, FIRE_MS - 1000))
    assert candidates == []


# ---------------------------------------------------------------------------
# Retention cap: newest 30 outcome notes, unrelated notes preserved
# ---------------------------------------------------------------------------


def test_retention_keeps_newest_30_same_prefix_only(tmp_path):
    state_path = write_state(
        tmp_path,
        notes=[{"at": "old", "note": "unrelated incident note"}],
    )
    base = {
        "automation_id": AUTO_ID,
        "session_id": SESSION_ID,
        "error_class": mfo.UNKNOWN,
        "retryable": None,
    }
    for index in range(31):
        result = dict(base, outcome="succeeded", scheduled_at=FIRE_MS + index * 1000)
        outcome = mfo.record_outcome_note(state_path, result, NOW_ISO)
        assert outcome["status"] == "recorded"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    outcome_notes = [n for n in state["notes"]
                     if n["note"].startswith(mfo.NOTE_PREFIX)]
    assert len(outcome_notes) == mfo.RETENTION_CAP
    # the oldest same-prefix note (FIRE_MS itself) was pruned
    scheduled = {int(mfo.parse_outcome_note(n["note"])["scheduled_at"])
                 for n in outcome_notes}
    assert FIRE_MS not in scheduled
    assert FIRE_MS + 1000 in scheduled
    # the unrelated note survives every prune
    assert {"at": "old", "note": "unrelated incident note"} in state["notes"]


def test_retention_ignores_correction_status(tmp_path):
    state_path = write_state(tmp_path)
    base = {"automation_id": AUTO_ID, "session_id": SESSION_ID,
            "error_class": mfo.UNKNOWN, "retryable": None,
            "outcome": "succeeded", "scheduled_at": FIRE_MS}
    mfo.record_outcome_note(state_path, base, NOW_ISO)
    mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")
    for index in range(30):
        result = dict(base, scheduled_at=FIRE_MS + 5000 + index * 1000)
        mfo.record_outcome_note(state_path, result, NOW_ISO)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    outcome_notes = [n for n in state["notes"]
                     if n["note"].startswith(mfo.NOTE_PREFIX)]
    assert len(outcome_notes) == mfo.RETENTION_CAP
    scheduled = {int(mfo.parse_outcome_note(n["note"])["scheduled_at"])
                 for n in outcome_notes}
    assert FIRE_MS not in scheduled  # the done note aged out like any other


# ---------------------------------------------------------------------------
# Memory correction: append-first supersession, recovery, concurrency
# ---------------------------------------------------------------------------


def test_append_first_supersession_keeps_armed_line(tmp_path, failed_db):
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    first = mfo.append_correction(index_path, result)
    assert first["status"] == "appended"
    text = index_path.read_text(encoding="utf-8")
    assert text.splitlines().index(armed_line(AUTO_ID)) == 0  # line preserved
    # exact-key read: identical entry is complete; a retry appends nothing
    second = mfo.append_correction(index_path, result)
    assert second["status"] == "complete"
    assert second["reason"] == "identical-entry-present"
    lines = [l for l in text.splitlines() if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(index_path.read_text(encoding="utf-8").splitlines()) == \
        len(text.splitlines())  # no duplicate appended
    assert lines == [l for l in
                     index_path.read_text(encoding="utf-8").splitlines()
                     if l.startswith(mfo.CORRECTION_PREFIX)]


def test_failed_append_recovery_via_rederivation(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    index_path = write_index(
        tmp_path, [armed_line(AUTO_ID), armed_line(AUTO_ID)])  # non-unique
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    mfo.record_outcome_note(state_path, result, NOW_ISO)

    blocked = mfo.append_correction(index_path, result)
    assert blocked["status"] == "blocked"
    assert blocked["reason"] == "armed-target-not-uniquely-identified"
    # no correction may exist after a blocked append
    assert mfo.read_correction(index_path, AUTO_ID, FIRE_MS)["status"] == "absent"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=pending" in state["notes"][0]["note"]

    # repair the index to a uniquely identified armed target, then the
    # survey's re-derivation retries the append and closes the correction
    index_path.write_text(armed_line(AUTO_ID) + "\n", encoding="utf-8")
    report = mfo.rederive_missing_corrections(failed_db, index_path, WORKSPACE,
                                              state_path=state_path)
    assert report and report[0]["status"] == "appended"
    assert report[0]["note_status"] == "updated"
    assert mfo.read_correction(index_path, AUTO_ID, FIRE_MS)["status"] == "complete"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=done" in state["notes"][0]["note"]


def test_missing_correction_rederived_after_note_ages_out(tmp_path, failed_db):
    # runtime row retained; the state note was pruned by retention earlier
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    report = mfo.rederive_missing_corrections(failed_db, index_path, WORKSPACE)
    assert report and report[0]["status"] == "appended"
    assert mfo.read_correction(index_path, AUTO_ID, FIRE_MS)["status"] == "complete"
    # a second survey re-derivation coalesces instead of duplicating
    report2 = mfo.rederive_missing_corrections(failed_db, index_path, WORKSPACE)
    assert report2 and report2[0]["status"] == "complete"
    corrections = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(corrections) == 1


def test_run_row_aged_out_reports_unknown(tmp_path):
    db_path = build_db(tmp_path)  # the row aged out of the ledger
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    report = mfo.rederive_missing_corrections(db_path, index_path, WORKSPACE)
    assert report == []


# ---------------------------------------------------------------------------
# Unavailable source: visible unknown entries, never an empty-list fold
# (pass 2 focused fix; a present store with no retained rows still reads
# empty, which is the aged-out case asserted directly above)
# ---------------------------------------------------------------------------


def test_workspace_read_raises_source_unavailable(tmp_path):
    missing_db = tmp_path / "absent-workspace.sqlite"
    no_table_db = tmp_path / "no-runs-table.sqlite"
    conn = sqlite3.connect(str(no_table_db))
    conn.execute("CREATE TABLE unrelated (x INTEGER)")
    conn.commit()
    conn.close()
    bad_column_db = build_db(tmp_path, drop_required_column="outcome",
                             name="bad-runs-columns.sqlite")
    corrupt_db = tmp_path / "corrupt-workspace.sqlite"
    corrupt_db.write_bytes(b"definitely not a sqlite database")
    expected = {
        missing_db: "missing-database",
        no_table_db: "missing-table",
        bad_column_db: "missing-columns",
        corrupt_db: "db-error",
    }
    for db_path, reason in expected.items():
        with pytest.raises(mfo.SourceUnavailable) as excinfo:
            mfo.read_workspace_runs(db_path, WORKSPACE, 0)
        assert excinfo.value.reason == reason, (db_path, excinfo.value.reason)
        assert excinfo.value.unknown_payload()["status"] == mfo.UNKNOWN


def test_rederive_reports_unavailable_source_as_unknown_entry(tmp_path):
    missing_db = tmp_path / "absent-rederive.sqlite"
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    state_path = write_state(tmp_path)
    before_index = index_path.read_bytes()
    report = mfo.rederive_missing_corrections(
        missing_db, index_path, WORKSPACE, state_path=state_path)
    assert len(report) == 1
    entry = report[0]
    assert entry["status"] == mfo.UNKNOWN
    assert entry["reason"] == "missing-database"
    # a workspace-level unknown entry, not a per-run entry
    assert "automation_id" not in entry
    assert "scheduled_at" not in entry
    # nothing inferred, nothing written
    assert index_path.read_bytes() == before_index
    assert json.loads(state_path.read_text(encoding="utf-8"))["notes"] == []

    # a corrupt store reports the same visibility with the db-error reason
    corrupt_db = tmp_path / "corrupt-rederive.sqlite"
    corrupt_db.write_bytes(b"still not a database")
    report = mfo.rederive_missing_corrections(corrupt_db, index_path, WORKSPACE)
    assert len(report) == 1
    assert report[0]["status"] == mfo.UNKNOWN
    assert report[0]["reason"] == "db-error"


def test_cli_overlaps_reports_unavailable_source(tmp_path, capsys):
    absent_db = tmp_path / "absent-overlaps.sqlite"
    rc = mfo.main([
        "overlaps", "--db", str(absent_db), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    assert payload[0]["status"] == mfo.UNKNOWN
    assert payload[0]["reason"] == "missing-database"
    # a present-but-empty ledger still prints a plain empty candidate list
    empty_db = build_db(tmp_path, name="empty-overlaps.sqlite")
    rc = mfo.main([
        "overlaps", "--db", str(empty_db), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000),
    ])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_rederive_reports_unavailable_source(tmp_path, capsys):
    absent_db = tmp_path / "absent-rederive-cli.sqlite"
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc = mfo.main([
        "rederive-corrections", "--db", str(absent_db), "--workspace-key",
        WORKSPACE, "--index", str(index_path),
    ])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert len(report) == 1
    assert report[0]["status"] == mfo.UNKNOWN
    assert report[0]["reason"] == "missing-database"


# ---------------------------------------------------------------------------
# Skill-text witness: the survey's read-side suppression clause (pass 2
# focused fix), pinned in check_maintenance_pins.sh and asserted here
# ---------------------------------------------------------------------------


def test_read_side_suppression_clause_pinned_in_skill_text():
    repo_root = Path(__file__).resolve().parent.parent
    survey_arms = (repo_root / "agents" / "skills" / "maintenance"
                   / "survey-arms.md").read_text(encoding="utf-8")
    # a later survey reading an armed memory line whose exact key has a
    # fire-outcome-correction entry treats the correction as authoritative
    # and suppresses the armed line's pending wording; report-only, the
    # armed line itself stays immutable
    assert "treats the correction as authoritative and suppresses the armed line" \
        in survey_arms
    assert "the armed line itself stays immutable" in survey_arms
    state_file = (repo_root / "agents" / "skills" / "maintenance"
                  / "state-file.md").read_text(encoding="utf-8")
    assert "authoritative over its armed line" in state_file


def test_concurrent_identical_state_observation_coalesces(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    peer_note = {"at": "2026-11-06T03:04:00+00:00",
                 "note": mfo.outcome_note_text(result)}

    real_load = mfo._load_state
    state = {"calls": 0}

    def racing_load(path):
        state["calls"] += 1
        if state["calls"] == 1:
            # the peer lands its identical note before our drift re-read
            current = json.loads(Path(path).read_text(encoding="utf-8"))
            current["notes"].append(peer_note)
            Path(path).write_text(json.dumps(current, indent=2) + "\n",
                                  encoding="utf-8")
        return real_load(path)

    with mock.patch.object(mfo, "_load_state", side_effect=racing_load):
        outcome = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert outcome["status"] == "unchanged"
    assert outcome["reason"] == "identical-note-reused"
    notes = json.loads(state_path.read_text(encoding="utf-8"))["notes"]
    matching = [n for n in notes if mfo.outcome_note_key(n["note"]) ==
                (AUTO_ID, str(FIRE_MS))]
    assert len(matching) == 1  # coalesced with the peer's identical note


def test_concurrent_identical_index_observation_coalesces(tmp_path, failed_db):
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    peer_line = mfo.correction_line_text(result)

    real_read = mfo._read_bytes
    state = {"calls": 0}

    def racing_read(path):
        state["calls"] += 1
        if state["calls"] == 1:
            # the peer appends its identical correction before our re-read
            current = Path(path).read_bytes()
            Path(path).write_bytes(current + peer_line.encode("utf-8") + b"\n")
            return current
        return real_read(path)

    with mock.patch.object(mfo, "_read_bytes", side_effect=racing_read):
        outcome = mfo.append_correction(index_path, result)
    assert outcome["status"] == "complete"
    assert outcome["reason"] == "identical-entry-present"
    corrections = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert corrections == [peer_line]


def test_second_drift_records_loss_without_writing(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)

    real_load = mfo._load_state
    state = {"calls": 0}

    def always_drifting_load(path):
        state["calls"] += 1
        if state["calls"] > 1 and state["calls"] % 2 == 0:
            # a concurrent writer keeps moving the file before every commit
            current = Path(path).read_text(encoding="utf-8")
            Path(path).write_text(current.replace(
                '"children": []', '"children": [], "drift": %d' % state["calls"]),
                encoding="utf-8")
        return real_load(path)

    with mock.patch.object(mfo, "_load_state", side_effect=always_drifting_load):
        outcome = mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert outcome["status"] == "unknown"
    assert outcome["reason"] == "state-drift-unresolved"
    notes = json.loads(state_path.read_text(encoding="utf-8"))["notes"]
    assert not [n for n in notes if n["note"].startswith(mfo.NOTE_PREFIX)]


# ---------------------------------------------------------------------------
# Conflicting outcomes
# ---------------------------------------------------------------------------


def test_conflicting_state_outcome_is_unknown_without_write(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "recorded"

    conflicting = dict(result, outcome="succeeded")
    outcome = mfo.record_outcome_note(state_path, conflicting, NOW_ISO)
    assert outcome["status"] == "unknown"
    assert outcome["reason"] == "conflicting-outcome-data"
    notes = json.loads(state_path.read_text(encoding="utf-8"))["notes"]
    assert len(notes) == 1  # the original note stands; no second note written
    assert "outcome=failed" in notes[0]["note"]


def test_re_record_identical_data_after_done_flip_reuses_note(tmp_path, failed_db):
    # idempotency is decided on the outcome-data fields only: the
    # writer-managed correction status never collides with it, so
    # re-recording identical data after this module flipped the note to
    # done is idempotent reuse, not unknown
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "recorded"
    mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")

    again = mfo.record_outcome_note(state_path, result, "2026-11-06T05:05:00+00:00")
    assert again["status"] == "unchanged"
    assert again["reason"] == "identical-note-reused"
    notes = json.loads(state_path.read_text(encoding="utf-8"))["notes"]
    assert len(notes) == 1  # no duplicate note
    assert "correction=done" in notes[0]["note"]  # the flip stands
    assert notes[0]["at"] == NOW_ISO  # the first stamp is kept


def test_re_record_different_outcome_after_done_flip_still_conflicts(tmp_path, failed_db):
    # a genuinely different outcome datum is a conflict even when the
    # correction status also differs
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    mfo.update_correction_status(state_path, AUTO_ID, FIRE_MS, "done")

    conflicting = dict(result, outcome="succeeded")
    outcome = mfo.record_outcome_note(state_path, conflicting, NOW_ISO)
    assert outcome["status"] == "unknown"
    assert outcome["reason"] == "conflicting-outcome-data"
    notes = json.loads(state_path.read_text(encoding="utf-8"))["notes"]
    assert len(notes) == 1
    assert "outcome=failed" in notes[0]["note"]
    assert "correction=done" in notes[0]["note"]


def test_conflicting_index_entries_are_ambiguous(tmp_path, failed_db):
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    assert mfo.append_correction(index_path, result)["status"] == "appended"
    conflicting = dict(result, outcome="succeeded")
    outcome = mfo.append_correction(index_path, conflicting)
    assert outcome["status"] == "ambiguous"
    assert outcome["reason"] == "conflicting-entries-present"
    # the rejected append wrote nothing: one valid entry stands, the plain
    # exact-key read stays complete
    assert mfo.read_correction(index_path, AUTO_ID, FIRE_MS)["status"] == "complete"
    corrections = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(corrections) == 1
    # when two conflicting bodies do exist at the exact key (an older
    # writer's residue), the read is ambiguous and further appends refuse
    with open(index_path, "a", encoding="utf-8") as handle:
        handle.write(mfo.correction_line_text(conflicting) + "\n")
    assert mfo.read_correction(index_path, AUTO_ID, FIRE_MS)["status"] == "ambiguous"
    assert mfo.append_correction(index_path, result)["status"] == "ambiguous"
    assert mfo.append_correction(index_path, conflicting)["status"] == "ambiguous"
    corrections = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(corrections) == 2  # report-only; nothing is deleted


def test_ambiguous_conflict_is_reported_not_corrected(tmp_path, failed_db):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    mfo.append_correction(index_path, result)
    conflicting = dict(result, outcome="succeeded")
    with open(index_path, "a", encoding="utf-8") as handle:
        handle.write(mfo.correction_line_text(conflicting) + "\n")
    report = mfo.rederive_missing_corrections(failed_db, index_path, WORKSPACE,
                                              state_path=state_path)
    assert report[0]["status"] == "ambiguous"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=pending" in state["notes"][0]["note"]  # never flipped done


def test_rederive_done_flip_requires_matching_body(tmp_path):
    # a single same-key correction whose body conflicts with the derived
    # body (here: appended from an attribution-absent read, error=unknown,
    # then re-derived from a run row WITH attribution) keeps the note
    # pending and is reported ambiguous; nothing is written to the index
    db_plain = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        name="plain-fire.sqlite",
    )
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    plain = mfo.read_fire_outcome(db_plain, AUTO_ID, FIRE_MS, WORKSPACE)
    assert plain["error_class"] == mfo.UNKNOWN
    assert mfo.append_correction(index_path, plain)["status"] == "appended"
    before_index = index_path.read_bytes()

    db_attribution = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        tasks_meta=[(WORKSPACE, SESSION_ID, failed_meta())],
        name="attribution-fire.sqlite",
    )
    state_path = write_state(tmp_path)
    result = mfo.read_fire_outcome(db_attribution, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["error_class"] != plain["error_class"]
    mfo.record_outcome_note(state_path, result, NOW_ISO)

    report = mfo.rederive_missing_corrections(
        db_attribution, index_path, WORKSPACE, state_path=state_path)
    assert report and report[0]["status"] == "ambiguous"
    assert report[0]["index_status"] == "ambiguous"
    assert "note_status" not in report[0]  # no done flip attempted
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=pending" in state["notes"][0]["note"]
    assert index_path.read_bytes() == before_index  # nothing appended
    # the gate is the expected-body read itself, not a plain same-key hit
    confirmed = mfo.read_correction(index_path, AUTO_ID, FIRE_MS,
                                    expected_line=mfo.correction_line_text(result))
    assert confirmed["status"] == "ambiguous"


def test_rederive_done_flip_with_matching_body(tmp_path, failed_db):
    # the index already holds the identical derived correction body; the
    # re-derivation confirms complete-with-matching-body and flips done
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    result = mfo.read_fire_outcome(failed_db, AUTO_ID, FIRE_MS, WORKSPACE)
    mfo.record_outcome_note(state_path, result, NOW_ISO)
    assert mfo.append_correction(index_path, result)["status"] == "appended"

    report = mfo.rederive_missing_corrections(
        failed_db, index_path, WORKSPACE, state_path=state_path)
    assert report and report[0]["status"] == "complete"
    assert report[0]["note_status"] == "updated"
    assert report[0]["note_reason"] == "correction-done"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "correction=done" in state["notes"][0]["note"]


# ---------------------------------------------------------------------------
# Path resolution and CLI entry points
# ---------------------------------------------------------------------------


def test_resolver_precedence(tmp_path, monkeypatch):
    explicit = tmp_path / "explicit.sqlite"
    env_base = tmp_path / "envbase"
    home = tmp_path / "home"
    monkeypatch.setenv("ZCODE_DATA_BASE_DIR", str(env_base))
    assert mfo.resolve_db_path(explicit=explicit) == explicit
    assert mfo.resolve_db_path(env=str(env_base)) == env_base / "v2" / "tasks-index.sqlite"
    monkeypatch.delenv("ZCODE_DATA_BASE_DIR", raising=False)
    assert mfo.resolve_db_path(home=home) == home / ".zcode" / "v2" / "tasks-index.sqlite"


def test_resolver_defaults_never_probe_live_paths(tmp_path, monkeypatch):
    # with the env and home redirected, no resolution can reach the live
    # store; the live task-index is only read via an explicit path.
    monkeypatch.delenv("ZCODE_DATA_BASE_DIR", raising=False)
    monkeypatch.setattr(mfo, "expand_path", lambda value, home=None: str(tmp_path))
    resolved = mfo.resolve_db_path()
    assert str(tmp_path) in str(resolved)
    assert "~" not in str(resolved)


def test_cli_record_and_append(tmp_path, failed_db, capsys):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc = mfo.main([
        "record-outcome", "--db", str(failed_db), "--workspace-key", WORKSPACE,
        "--automation-id", AUTO_ID, "--scheduled-at", str(FIRE_MS),
        "--state", str(state_path), "--at", NOW_ISO,
    ])
    assert rc == 0
    rc = mfo.main([
        "append-correction", "--db", str(failed_db), "--workspace-key", WORKSPACE,
        "--automation-id", AUTO_ID, "--scheduled-at", str(FIRE_MS),
        "--index", str(index_path),
    ])
    assert rc == 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(state["notes"]) == 1
    corrections = [l for l in index_path.read_text(encoding="utf-8").splitlines()
                   if l.startswith(mfo.CORRECTION_PREFIX)]
    assert len(corrections) == 1


def test_cli_unknown_reports_failure_without_write(tmp_path, capsys):
    state_path = write_state(tmp_path)
    absent_db = tmp_path / "absent.sqlite"
    rc = mfo.main([
        "record-outcome", "--db", str(absent_db), "--workspace-key", WORKSPACE,
        "--automation-id", AUTO_ID, "--scheduled-at", str(FIRE_MS),
        "--state", str(state_path), "--at", NOW_ISO,
    ])
    assert rc == 1
    assert json.loads(state_path.read_text(encoding="utf-8"))["notes"] == []


def test_cli_read_outcome_and_overlaps(tmp_path, failed_db, capsys):
    rc = mfo.main([
        "read-outcome", "--db", str(failed_db), "--workspace-key", WORKSPACE,
        "--automation-id", AUTO_ID, "--scheduled-at", str(FIRE_MS),
    ])
    assert rc == 0
    assert '"status": "terminal"' in capsys.readouterr().out
    db_with_overlap = overlap_db(tmp_path)
    rc = mfo.main([
        "overlaps", "--db", str(db_with_overlap), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000),
    ])
    assert rc == 0
    assert '"mandate_match": true' in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Census enumeration (post-fire verification arm; plan
# docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md
# Task 1): runs-driven member enumeration, exclusions, the unknown class,
# the unwired signal, read-only safety, and error containment. Warning-only:
# every classified verdict exits 0 and the census writes nothing.
# ---------------------------------------------------------------------------


def test_census_enumerates_terminal_one_shot_members(tmp_path):
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, "succeeded", SESSION_ID, RUN_END_MS),
            run_row(AUTO_ID_OTHER, LATE_FIRE_MS, "failed", "sess-peer",
                    LATE_FIRE_MS + 60_000),
        ],
        automations=[(AUTO_ID, "prompt one"), (AUTO_ID_OTHER, "prompt two")],
        name="census-enumerate.sqlite",
    )
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000)
    assert verdict["status"] == "ok"
    assert verdict["eligible_count"] == 2
    members = {(m["automation_id"], m["scheduled_at"]): m
               for m in verdict["members"]}
    assert len(members) == 2
    first = members[(AUTO_ID, FIRE_MS)]
    assert first["outcome"] == "succeeded"
    assert first["session_id"] == SESSION_ID
    assert first["recurring"] == 0
    assert first["record_present"] is True
    assert first["eligible"] is True
    assert first["class"] == "eligible"
    second = members[(AUTO_ID_OTHER, LATE_FIRE_MS)]
    assert second["outcome"] == "failed"
    assert second["session_id"] == "sess-peer"
    assert second["eligible"] is True


def test_census_excludes_recurring_record_members(tmp_path):
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID_RECURRING, FIRE_MS, "succeeded", SESSION_ID,
                      RUN_END_MS)],
        automations=[(AUTO_ID_RECURRING, "nightly prompt", 1)],
        name="census-recurring.sqlite",
    )
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000)
    assert verdict["status"] == "ok"
    # a recurring record never becomes a member at all
    assert verdict["members"] == []
    assert verdict["eligible_count"] == 0
    assert verdict["unwired"] == mfo.UNKNOWN


def test_census_excludes_not_yet_fired_one_shot(tmp_path):
    # a one-shot record armed for a future slot has no run row yet, so the
    # runs-driven enumeration lists no member for it
    db_path = build_db(tmp_path, runs=[],
                       automations=[(AUTO_ID, "future one-shot")],
                       name="census-future.sqlite")
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=0)
    assert verdict["status"] == "ok"
    assert verdict["members"] == []
    assert verdict["unwired"] == mfo.UNKNOWN


def test_census_lists_nonterminal_members_in_unknown_class(tmp_path):
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, "running", SESSION_ID, RUN_END_MS),
            run_row(AUTO_ID_OTHER, LATE_FIRE_MS, "", "sess-peer",
                    LATE_FIRE_MS + 60_000),
        ],
        automations=[(AUTO_ID, "prompt one"), (AUTO_ID_OTHER, "prompt two")],
        name="census-nonterminal.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    before_state = state_path.read_bytes()
    before_index = index_path.read_bytes()
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["status"] == "ok"
    assert len(verdict["members"]) == 2
    for member in verdict["members"]:
        assert member["class"] == "unknown"
        assert member["unknown_reason"] == "nonterminal"
        assert member["eligible"] is False
        assert member["note_state"] == "absent"
        assert member["correction_state"] == "absent"
    assert verdict["eligible_count"] == 0
    assert verdict["unwired"] == mfo.UNKNOWN
    # no note or correction write: the census only reads
    assert state_path.read_bytes() == before_state
    assert index_path.read_bytes() == before_index


def test_census_aged_out_record_lists_unknown_and_processes_like_terminal(tmp_path):
    # the automation record aged out of the automations table while the
    # terminal run row is still retained
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "failed", SESSION_ID, RUN_END_MS)],
        automations=[],
        name="census-aged-out.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["status"] == "ok"
    assert len(verdict["members"]) == 1
    member = verdict["members"][0]
    assert member["automation_id"] == AUTO_ID
    assert member["scheduled_at"] == FIRE_MS
    assert member["outcome"] == "failed"
    assert member["record_present"] is False
    assert member["recurring"] == mfo.UNKNOWN  # record-derived field unknown
    assert member["eligible"] is False  # never counts eligible
    assert member["class"] == "unknown"
    assert member["unknown_reason"] == "aged-out"
    assert verdict["eligible_count"] == 0
    # a member set holding only aged-out records is never unwired true/false
    assert verdict["unwired"] == mfo.UNKNOWN
    # the arm's existing writes process it like a terminal member: the
    # writes read only the retained run rows
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    assert result["status"] == "terminal"
    assert mfo.record_outcome_note(state_path, result, NOW_ISO)["status"] == "recorded"
    assert mfo.append_correction(index_path, result)["status"] == "appended"


def test_census_empty_member_set_reports_unwired_unknown(tmp_path):
    # only a recurring carrier fired: the passed-fire one-shot set is empty
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID_RECURRING, FIRE_MS, "succeeded", SESSION_ID,
                      RUN_END_MS)],
        automations=[(AUTO_ID_RECURRING, "nightly prompt", 1)],
        name="census-empty-recurring.sqlite",
    )
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [])
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["members"] == []
    assert verdict["unwired"] == mfo.UNKNOWN  # never true or false
    # an entirely empty ledger is the same no-member case
    empty_db = build_db(tmp_path, runs=[], automations=[],
                        name="census-empty-ledger.sqlite")
    verdict = mfo.census_members(empty_db, WORKSPACE, since_ms=0,
                                 state_path=state_path, index_path=index_path)
    assert verdict["members"] == []
    assert verdict["unwired"] == mfo.UNKNOWN


def test_census_window_bounding_excludes_out_of_window_runs(tmp_path):
    hour = 60 * 60 * 1000
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, CENSUS_NOW_MS - 25 * hour, "succeeded",
                    SESSION_ID, CENSUS_NOW_MS - 25 * hour + 60_000),
            run_row(AUTO_ID_OTHER, CENSUS_NOW_MS - 23 * hour, "succeeded",
                    "sess-peer", CENSUS_NOW_MS - 23 * hour + 60_000),
            run_row("automation-future", CENSUS_NOW_MS + hour, "succeeded",
                    "sess-future", CENSUS_NOW_MS + hour + 60_000),
        ],
        automations=[(AUTO_ID, "older than window"),
                     (AUTO_ID_OTHER, "inside window"),
                     ("automation-future", "not yet fired")],
        name="census-window.sqlite",
    )
    verdict = mfo.census_members(
        db_path, WORKSPACE,
        since_ms=CENSUS_NOW_MS - mfo.DEFAULT_WINDOW_MS, now_ms=CENSUS_NOW_MS)
    assert verdict["status"] == "ok"
    # only the run inside the window is a member: older-than-lookback and
    # not-yet-fired slots are both outside the window
    assert [(m["automation_id"], m["scheduled_at"])
            for m in verdict["members"]] == \
        [(AUTO_ID_OTHER, CENSUS_NOW_MS - 23 * hour)]


def test_census_window_defaults_to_24h_and_since_ms_overrides(tmp_path):
    hour = 60 * 60 * 1000
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, CENSUS_NOW_MS - 25 * hour, "succeeded",
                    SESSION_ID, CENSUS_NOW_MS - 25 * hour + 60_000),
            run_row(AUTO_ID_OTHER, CENSUS_NOW_MS - 23 * hour, "succeeded",
                    "sess-peer", CENSUS_NOW_MS - 23 * hour + 60_000),
        ],
        automations=[(AUTO_ID, "older"), (AUTO_ID_OTHER, "newer")],
        name="census-default-window.sqlite",
    )
    default_verdict = mfo.census_members(db_path, WORKSPACE,
                                         now_ms=CENSUS_NOW_MS)
    assert default_verdict["since_ms"] == CENSUS_NOW_MS - mfo.DEFAULT_WINDOW_MS
    assert [m["automation_id"] for m in default_verdict["members"]] == \
        [AUTO_ID_OTHER]
    override_verdict = mfo.census_members(db_path, WORKSPACE,
                                          since_ms=CENSUS_NOW_MS - 26 * hour,
                                          now_ms=CENSUS_NOW_MS)
    assert {m["automation_id"] for m in override_verdict["members"]} == \
        {AUTO_ID, AUTO_ID_OTHER}


def test_census_cli_window_default_and_since_ms_override(tmp_path, capsys):
    db_path = build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "succeeded", SESSION_ID, RUN_END_MS)],
        automations=[(AUTO_ID, "the maintenance turn")],
        name="census-cli-window.sqlite",
    )
    rc = mfo.main(["census", "--db", str(db_path),
                   "--workspace-key", WORKSPACE])
    assert rc == 0
    verdict = json.loads(capsys.readouterr().out)
    # the fixture fire is far older than the default 24h lookback
    assert verdict["members"] == []
    rc = mfo.main(["census", "--db", str(db_path), "--workspace-key", WORKSPACE,
                   "--since-ms", str(FIRE_MS - 1000)])
    assert rc == 0
    verdict = json.loads(capsys.readouterr().out)
    assert len(verdict["members"]) == 1
    assert verdict["eligible_count"] == 1


def _census_eligible_db(tmp_path, name):
    return build_db(
        tmp_path,
        runs=[run_row(AUTO_ID, FIRE_MS, "succeeded", SESSION_ID, RUN_END_MS)],
        automations=[(AUTO_ID, "the maintenance turn")],
        name=name,
    )


def test_census_unwired_true_when_no_traces_exist(tmp_path):
    db_path = _census_eligible_db(tmp_path, "census-unwired-true.sqlite")
    state_path = write_state(tmp_path)  # readable, zero outcome notes
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])  # zero corrections
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["eligible_count"] == 1
    assert verdict["unwired"] is True
    assert verdict["unwired_reason"] == "no-traces"
    member = verdict["members"][0]
    assert member["note_state"] == "absent"
    assert member["correction_state"] == "absent"


def test_census_unwired_false_when_note_trace_exists(tmp_path):
    db_path = _census_eligible_db(tmp_path, "census-unwired-note.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(
        tmp_path, notes=[{"at": NOW_ISO, "note": mfo.outcome_note_text(result)}])
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    assert verdict["members"][0]["note_state"] == "present"


def test_census_unwired_false_when_correction_trace_exists(tmp_path):
    db_path = _census_eligible_db(tmp_path, "census-unwired-correction.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID),
                                        mfo.correction_line_text(result)])
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path, index_path=index_path)
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    assert verdict["members"][0]["correction_state"] == "present"
    assert verdict["members"][0]["note_state"] == "absent"


def test_census_unwired_unknown_when_trace_surface_unsupplied(tmp_path):
    db_path = _census_eligible_db(tmp_path, "census-unwired-unsupplied.sqlite")
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    # neither surface supplied
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000)
    assert verdict["unwired"] == mfo.UNKNOWN
    assert verdict["unwired_reason"] == "trace-surface-unsupplied"
    # state supplied and readable, index unsupplied
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 state_path=state_path)
    assert verdict["unwired"] == mfo.UNKNOWN
    assert verdict["members"][0]["note_state"] == "absent"
    assert verdict["members"][0]["correction_state"] == mfo.UNKNOWN
    # index supplied and readable, state unsupplied
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 index_path=index_path)
    assert verdict["unwired"] == mfo.UNKNOWN
    assert verdict["members"][0]["note_state"] == mfo.UNKNOWN
    assert verdict["members"][0]["correction_state"] == "absent"
    # a readable surface's traces never produce unwired false while the
    # other surface is unsupplied
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    index_with_trace = write_index(
        tmp_path, [armed_line(AUTO_ID), mfo.correction_line_text(result)],
        name="MEMORY-with-trace.md")
    verdict = mfo.census_members(db_path, WORKSPACE, since_ms=FIRE_MS - 1000,
                                 index_path=index_with_trace)
    assert verdict["unwired"] == mfo.UNKNOWN
    assert verdict["unwired"] is not False


def _census_dir_snapshot(root):
    snapshot = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        if path.is_dir():
            snapshot[key + "/"] = b""
        else:
            snapshot[key] = path.read_bytes()
    return snapshot


def test_census_connect_is_read_only_and_writes_nothing(tmp_path):
    db_path = _census_eligible_db(tmp_path, "census-readonly.sqlite")
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    snapshot = _census_dir_snapshot(tmp_path)
    real_connect = sqlite3.connect
    recorded = []

    def recording_connect(*args, **kwargs):
        recorded.append((args[0], kwargs))
        return real_connect(*args, **kwargs)

    with mock.patch.object(mfo.sqlite3, "connect",
                           side_effect=recording_connect):
        verdict = mfo.census_members(db_path, WORKSPACE,
                                     since_ms=FIRE_MS - 1000,
                                     state_path=state_path,
                                     index_path=index_path)
    assert verdict["status"] == "ok"
    assert recorded
    for uri, kwargs in recorded:
        assert uri.startswith("file:")
        assert "mode=ro" in uri
        assert kwargs.get("uri") is True
    # byte snapshot plus no-sidecar directory assertion: nothing in the
    # fixture tree changed and no journal or wal sidecar appeared
    assert _census_dir_snapshot(tmp_path) == snapshot


def test_census_error_containment_reports_unknown_and_exits_zero(tmp_path, capsys):
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    before_state = state_path.read_bytes()
    before_index = index_path.read_bytes()
    runs_sql, tasks_sql, automations_sql = SCHEMA_SQL

    missing_db = tmp_path / "absent-census.sqlite"

    corrupt_db = tmp_path / "corrupt-census.sqlite"
    corrupt_db.write_bytes(b"definitely not a sqlite database")

    no_runs_table_db = tmp_path / "no-runs-table.sqlite"
    conn = sqlite3.connect(str(no_runs_table_db))
    conn.execute(tasks_sql)
    conn.execute(automations_sql)
    conn.commit()
    conn.close()

    no_automations_table_db = tmp_path / "no-automations-table.sqlite"
    conn = sqlite3.connect(str(no_automations_table_db))
    conn.execute(runs_sql)
    conn.execute(tasks_sql)
    conn.commit()
    conn.close()

    no_recurring_column_db = tmp_path / "no-recurring-column.sqlite"
    conn = sqlite3.connect(str(no_recurring_column_db))
    conn.execute(runs_sql)
    conn.execute(tasks_sql)
    conn.execute(
        "CREATE TABLE automations ("
        " automation_id TEXT PRIMARY KEY,"
        " workspace_key TEXT NOT NULL,"
        " prompt TEXT NOT NULL DEFAULT '')")
    conn.commit()
    conn.close()

    bad_runs_column_db = build_db(tmp_path, drop_required_column="outcome",
                                  name="census-bad-runs-column.sqlite")

    expected = [
        (missing_db, "missing-database", None),
        (corrupt_db, "db-error", None),
        (no_runs_table_db, "missing-table", "automation_runs"),
        (no_automations_table_db, "missing-table", "automations"),
        (no_recurring_column_db, "missing-columns", "automations"),
        (bad_runs_column_db, "missing-columns", "automation_runs"),
    ]
    for db_path, reason, table in expected:
        verdict = mfo.census_members(db_path, WORKSPACE, since_ms=0,
                                     state_path=state_path,
                                     index_path=index_path)
        assert verdict["status"] == mfo.UNKNOWN, (db_path, verdict)
        assert verdict["reason"] == reason, (db_path, verdict)
        if table is not None:
            assert verdict["table"] == table, (db_path, verdict)
        assert verdict["members"] == []
        assert verdict["eligible_count"] == 0
        assert verdict["unwired"] == mfo.UNKNOWN

    # the CLI reports the same source-unavailable unknown verdict, exit 0
    rc = mfo.main(["census", "--db", str(missing_db),
                   "--workspace-key", WORKSPACE])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == mfo.UNKNOWN
    assert payload["reason"] == "missing-database"
    # nothing was written to either trace surface across the whole cell
    assert state_path.read_bytes() == before_state
    assert index_path.read_bytes() == before_index


# ---------------------------------------------------------------------------
# Census classification matrix (same plan, Task 2): the CLI dispatch
# surface, per-member trace reads, unreadable and absent surface
# degradation, the mixed traced/untraced member set, and the read-only
# negative control. Every cell carries census in its name so the pinned
# -k census selector collects it.
# ---------------------------------------------------------------------------


def _census_cli_verdict(db_path, state_path, index_path, capsys,
                        since_ms=None):
    """Dispatch the census subcommand over injected fixture paths and
    return (rc, verdict)."""
    argv = [
        "census", "--db", str(db_path), "--workspace-key", WORKSPACE,
        "--since-ms", str(FIRE_MS - 1000 if since_ms is None else since_ms),
        "--state", str(state_path), "--index", str(index_path),
    ]
    rc = mfo.main(argv)
    return rc, json.loads(capsys.readouterr().out)


def test_census_cells_carry_the_pinned_selector_token():
    # naming contract: every cell touching the census surface carries
    # census in its name so the pinned -k census selector collects it
    source = Path(__file__).resolve().read_text(encoding="utf-8")
    starts = [match.start() for match in
              re.finditer(r"^def test_\w+", source, flags=re.M)]
    starts.append(len(source))
    for start, end in zip(starts, starts[1:]):
        block = source[start:end]
        if not re.search(
            r"census_members|\"census\"|_census_cli_verdict|_census_eligible_db",
            block,
        ):
            continue
        name = block.splitlines()[0][len("def "):].split("(")[0]
        assert "census" in name, \
            "census-surface cell %s must carry census in its name" % name


def test_census_cli_dispatch_reports_members_and_unwired(tmp_path, capsys):
    # the census subcommand over fixture stores exits 0 and prints a JSON
    # verdict carrying members and unwired
    eligible_db = _census_eligible_db(tmp_path, "census-cli-dispatch.sqlite")
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc, verdict = _census_cli_verdict(eligible_db, state_path, index_path,
                                      capsys)
    assert rc == 0
    assert verdict["members"] and \
        verdict["members"][0]["automation_id"] == AUTO_ID
    assert verdict["eligible_count"] == 1
    assert verdict["unwired"] is True  # readable surfaces, zero traces
    # a second fixture store with no members keeps the same verdict shape
    empty_db = build_db(tmp_path, runs=[], automations=[],
                        name="census-cli-dispatch-empty.sqlite")
    rc, verdict = _census_cli_verdict(empty_db, state_path, index_path,
                                      capsys, since_ms=0)
    assert rc == 0
    assert verdict["members"] == []
    assert verdict["unwired"] == mfo.UNKNOWN


def test_census_cli_note_trace_present_sets_unwired_false(tmp_path, capsys):
    db_path = _census_eligible_db(tmp_path, "census-cli-note-trace.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(
        tmp_path, notes=[{"at": NOW_ISO, "note": mfo.outcome_note_text(result)}])
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    rc, verdict = _census_cli_verdict(db_path, state_path, index_path, capsys)
    assert rc == 0
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    member = verdict["members"][0]
    assert member["note_state"] == "present"
    assert member["correction_state"] == "absent"


def test_census_cli_correction_trace_present_sets_unwired_false(tmp_path, capsys):
    db_path = _census_eligible_db(tmp_path,
                                  "census-cli-correction-trace.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(tmp_path)
    index_path = write_index(tmp_path, [armed_line(AUTO_ID),
                                        mfo.correction_line_text(result)])
    rc, verdict = _census_cli_verdict(db_path, state_path, index_path, capsys)
    assert rc == 0
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    member = verdict["members"][0]
    assert member["correction_state"] == "present"
    assert member["note_state"] == "absent"


def test_census_cli_ambiguous_correction_reports_ambiguous_and_writes_nothing(tmp_path, capsys):
    db_path = _census_eligible_db(tmp_path, "census-cli-ambiguous.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    # the fixture outcome is succeeded; the conflicting body differs at the
    # same exact key
    conflicting = dict(result, outcome="failed")
    index_path = write_index(tmp_path, [
        armed_line(AUTO_ID),
        mfo.correction_line_text(result),
        mfo.correction_line_text(conflicting),
    ])
    before_index = index_path.read_bytes()
    state_path = write_state(tmp_path)
    rc, verdict = _census_cli_verdict(db_path, state_path, index_path, capsys)
    assert rc == 0
    member = verdict["members"][0]
    assert member["correction_state"] == "ambiguous"
    assert member["note_state"] == "absent"
    # an ambiguous body is still a trace: the set-level signal reads false
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    assert index_path.read_bytes() == before_index  # nothing written


def test_census_unreadable_trace_surfaces_degrade_unwired_to_unknown(tmp_path, capsys):
    db_path = _census_eligible_db(tmp_path,
                                  "census-unreadable-surfaces.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    # a corrupt state file is unreadable (json.loads fails); the denied
    # index raises OSError on read_bytes (deterministic regardless of euid)
    corrupt_state = tmp_path / "corrupt-scheduler-state.json"
    corrupt_state.write_bytes(b"{not json")
    denied_index = tmp_path / "denied-MEMORY.md"
    denied_index.write_bytes(b"armed line\n")
    before = (corrupt_state.read_bytes(), denied_index.read_bytes())
    real_read_bytes = Path.read_bytes

    def denying_read_bytes(path_self):
        if path_self == Path(denied_index):
            raise PermissionError(13, "unreadable fixture surface")
        return real_read_bytes(path_self)

    with mock.patch.object(Path, "read_bytes", denying_read_bytes):
        # both surfaces unreadable: per-member states unknown, unwired unknown
        rc, verdict = _census_cli_verdict(db_path, corrupt_state,
                                          denied_index, capsys)
        assert rc == 0
        member = verdict["members"][0]
        assert member["note_state"] == mfo.UNKNOWN
        assert member["correction_state"] == mfo.UNKNOWN
        assert verdict["unwired"] == mfo.UNKNOWN
        assert verdict["unwired_reason"] == "trace-surface-unreadable"
        assert verdict["trace_state_status"] == "unreadable"
        assert verdict["trace_index_status"] == "unreadable"
        # state unreadable + index readable with a trace: the signal stays
        # unknown regardless of the readable surface's content
        traced_index = write_index(
            tmp_path,
            [armed_line(AUTO_ID), mfo.correction_line_text(result)],
            name="MEMORY-state-unreadable.md")
        rc, verdict = _census_cli_verdict(db_path, corrupt_state,
                                          traced_index, capsys)
        assert rc == 0
        assert verdict["unwired"] == mfo.UNKNOWN
        member = verdict["members"][0]
        assert member["note_state"] == mfo.UNKNOWN
        assert member["correction_state"] == "present"
        # state readable with a trace + index unreadable: the same unknown
        traced_state = write_state(
            tmp_path, notes=[{"at": NOW_ISO,
                              "note": mfo.outcome_note_text(result)}])
        rc, verdict = _census_cli_verdict(db_path, traced_state,
                                          denied_index, capsys)
        assert rc == 0
        assert verdict["unwired"] == mfo.UNKNOWN
        member = verdict["members"][0]
        assert member["note_state"] == "present"
        assert member["correction_state"] == mfo.UNKNOWN
    # nothing written: both unreadable surfaces kept their bytes
    assert (corrupt_state.read_bytes(), denied_index.read_bytes()) == before


def test_census_absent_trace_surfaces_degrade_unwired_to_unknown(tmp_path, capsys):
    db_path = _census_eligible_db(tmp_path, "census-absent-surfaces.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    absent_state = tmp_path / "never-created-scheduler-state.json"
    absent_index = tmp_path / "never-created-MEMORY.md"
    # both surfaces supplied but absent: per-member states unknown and the
    # unwired signal unknown, never a false unwired from the index reader's
    # empty-file behavior
    rc, verdict = _census_cli_verdict(db_path, absent_state, absent_index,
                                      capsys)
    assert rc == 0
    member = verdict["members"][0]
    assert member["note_state"] == mfo.UNKNOWN
    assert member["correction_state"] == mfo.UNKNOWN
    assert verdict["unwired"] == mfo.UNKNOWN
    assert verdict["unwired_reason"] == "trace-surface-absent"
    assert verdict["trace_state_status"] == "absent"
    assert verdict["trace_index_status"] == "absent"
    assert not absent_state.exists()  # nothing written, files still absent
    assert not absent_index.exists()
    # one supplied-but-absent + the other readable with a trace: the signal
    # stays unknown regardless of the readable surface's content
    traced_index = write_index(
        tmp_path, [armed_line(AUTO_ID), mfo.correction_line_text(result)],
        name="MEMORY-state-absent.md")
    rc, verdict = _census_cli_verdict(db_path, absent_state, traced_index,
                                      capsys)
    assert rc == 0
    assert verdict["unwired"] == mfo.UNKNOWN
    member = verdict["members"][0]
    assert member["note_state"] == mfo.UNKNOWN
    assert member["correction_state"] == "present"
    traced_state = write_state(
        tmp_path, notes=[{"at": NOW_ISO,
                          "note": mfo.outcome_note_text(result)}])
    rc, verdict = _census_cli_verdict(db_path, traced_state, absent_index,
                                      capsys)
    assert rc == 0
    assert verdict["unwired"] == mfo.UNKNOWN
    member = verdict["members"][0]
    assert member["note_state"] == "present"
    assert member["correction_state"] == mfo.UNKNOWN
    assert not absent_state.exists()
    assert not absent_index.exists()


def test_census_mixed_traced_and_untraced_members_report_per_member_states(tmp_path, capsys):
    db_path = build_db(
        tmp_path,
        runs=[
            run_row(AUTO_ID, FIRE_MS, "succeeded", SESSION_ID, RUN_END_MS),
            run_row(AUTO_ID_OTHER, LATE_FIRE_MS, "failed", "sess-peer",
                    LATE_FIRE_MS + 60_000),
        ],
        automations=[(AUTO_ID, "prompt one"), (AUTO_ID_OTHER, "prompt two")],
        name="census-mixed-set.sqlite",
    )
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(
        tmp_path, notes=[{"at": NOW_ISO, "note": mfo.outcome_note_text(result)}])
    index_path = write_index(tmp_path, [armed_line(AUTO_ID),
                                        armed_line(AUTO_ID_OTHER)])
    rc, verdict = _census_cli_verdict(db_path, state_path, index_path, capsys)
    assert rc == 0
    # the unwired signal is set-level: one traced member is enough for false
    assert verdict["unwired"] is False
    assert verdict["unwired_reason"] == "traces-present"
    members = {(m["automation_id"], m["scheduled_at"]): m
               for m in verdict["members"]}
    traced = members[(AUTO_ID, FIRE_MS)]
    untraced = members[(AUTO_ID_OTHER, LATE_FIRE_MS)]
    assert traced["note_state"] == "present"
    assert traced["correction_state"] == "absent"
    # the untraced member's note and correction states are reported absent
    assert untraced["note_state"] == "absent"
    assert untraced["correction_state"] == "absent"


def test_census_negative_control_redirects_resolution_and_writes_nothing(tmp_path, monkeypatch, capsys):
    db_path = _census_eligible_db(tmp_path, "census-negative-control.sqlite")
    result = mfo.read_fire_outcome(db_path, AUTO_ID, FIRE_MS, WORKSPACE)
    state_path = write_state(
        tmp_path, notes=[{"at": NOW_ISO, "note": mfo.outcome_note_text(result)}])
    index_path = write_index(tmp_path, [armed_line(AUTO_ID)])
    # HOME and ZCODE_DATA_BASE_DIR redirected to the temp root: a fallback
    # resolution would miss there, so the ok verdict proves the injected
    # store was read
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("ZCODE_DATA_BASE_DIR", str(tmp_path))
    snapshot = _census_dir_snapshot(tmp_path)
    recorded = []
    real_resolve = mfo.resolve_db_path

    def recording_resolve(explicit=None, env=None, home=None):
        resolved = real_resolve(explicit=explicit, env=env, home=home)
        recorded.append((explicit, str(resolved)))
        return resolved

    with mock.patch.object(mfo, "resolve_db_path",
                           side_effect=recording_resolve):
        rc, verdict = _census_cli_verdict(db_path, state_path, index_path,
                                          capsys)
    assert rc == 0
    # no fallback resolution consulted: every resolution was explicit
    assert recorded and all(explicit is not None for explicit, _ in recorded)
    assert recorded[0][1] == str(db_path)
    assert verdict["status"] == "ok"
    assert verdict["eligible_count"] == 1
    assert verdict["unwired"] is False  # the injected surfaces were read
    assert verdict["members"][0]["note_state"] == "present"
    # nothing written anywhere in the fixture tree (no sidecars either)
    assert _census_dir_snapshot(tmp_path) == snapshot


# ---------------------------------------------------------------------------
# Suite-level guard: the live scheduler state and memory index surfaces
# are never touched (snapshot at import; verified at suite end).
# ---------------------------------------------------------------------------


def _primary_checkout():
    import subprocess
    try:
        common_dir = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(common_dir).resolve().parent
    except (subprocess.CalledProcessError, OSError):
        return None


def _live_surface_paths():
    paths = {}
    checkout = _primary_checkout()
    if checkout is not None:
        paths["live-scheduler-state"] = checkout / ".ai-playbook" / "scheduler-state.json"
    home = Path.home()
    for name, candidate in (
        ("live-memory-claude", home / ".claude" / "MEMORY.md"),
        ("live-memory-codex", home / ".codex" / "MEMORY.md"),
        ("live-memory-agents", home / ".agents" / "MEMORY.md"),
        ("live-memory-cursor", home / ".cursor" / "MEMORY.md"),
    ):
        paths[name] = candidate
    return paths


def _digest(path):
    try:
        return path.read_bytes()
    except OSError:
        return None  # absent surface


LIVE_SNAPSHOT_AT_IMPORT = {name: _digest(path)
                           for name, path in _live_surface_paths().items()}


def test_live_surfaces_untouched_across_suite():
    current = {name: _digest(path) for name, path in _live_surface_paths().items()}
    assert current == LIVE_SNAPSHOT_AT_IMPORT, (
        "a live maintenance surface changed bytes during the suite; every "
        "helper in this suite must be invoked with explicit temporary paths")
