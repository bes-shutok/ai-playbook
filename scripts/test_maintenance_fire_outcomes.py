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
"""

import json
import sqlite3
import sys
import unittest.mock as mock
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

WORKSPACE = "/fixtures/repo"
AUTO_ID = "automation-1111"
AUTO_ID_OTHER = "automation-2222"
AUTO_ID_RECURRING = "automation-recurring"
SESSION_ID = "sess-abcdef01-2345-6789"
RAW_MESSAGE = "exceed quota limit"
RAW_REQUEST_ID = "req-9f8e7d6c-5b4a"

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
        prompt TEXT NOT NULL DEFAULT ''
      )""",
]


def run_row(automation_id, scheduled_at, outcome, session_id, updated_at,
            run_id=None):
    return (
        run_id or "%s:%s" % (automation_id, scheduled_at),
        automation_id,
        WORKSPACE,
        scheduled_at,
        "schedule",
        "dispatched",
        outcome,
        session_id,
        "{}",
        1,
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
            # build a schema missing the required column (missing-columns arm)
            statement = statement.replace("outcome TEXT,", "outcome_x TEXT,")
        conn.execute(statement)
    for row in runs:
        conn.execute(
            "INSERT INTO automation_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
    for workspace_key, task_id, meta in (tasks_meta or []):
        conn.execute("INSERT INTO tasks VALUES (?,?,?)", (workspace_key, task_id, meta))
    for automation_id, prompt in automations:
        conn.execute("INSERT INTO automations VALUES (?,?,?)",
                     (automation_id, WORKSPACE, prompt))
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


def write_index(tmp_path, lines):
    index_path = tmp_path / "MEMORY.md"
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
