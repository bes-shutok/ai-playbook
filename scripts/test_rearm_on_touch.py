#!/usr/bin/env python3
"""Hermetic pytest suite for the rearm-on-touch mechanical check (plan Task 3).

Plan: docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md,
section "Task 3: Rearm-on-touch mechanical check". Every test below mirrors one
plan checkbox one-for-one and carries the plan's class tag in its docstring
(`[class: REPOSITORY_TEST]`).

Hermeticity contract:
- every fixture lives under pytest ``tmp_path``: the scheduler state file and
  the listing JSON are ordinary files and the repo root is a plain directory
  (no git repo needed: the check is file-driven);
- no network, no real ``~/.ai-playbook`` dependency, and no automation
  primitives: the script under test reads files and prints a verdict, so every
  timestamp is computed relative to real ``now`` (all horizons are hours, far
  beyond test runtime);
- classification tests run the script as a subprocess (black-box CLI contract:
  rc, stdout verdict, stderr loudness); the atomic-write test runs it
  in-process so the ``os.replace`` seam can be spied.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import rearm_on_touch  # noqa: E402  (in-process use for the atomic-write seam)

SCRIPT = SCRIPTS_DIR / "rearm_on_touch.py"

# Mirror of the recognition literals for fixture construction. The pinned
# source of record is agents/skills/maintenance/zcode.md ("Recurring
# automation recipe"); this suite only mirrors them into fixtures.
RECOGNITION_TITLE = "Maintenance scheduler turn (every 2 hours)"
RECOGNITION_OPENING = "You are the maintenance scheduler for the repository at"


# --------------------------------------------------------------------------- #
# Fixture plumbing.
# --------------------------------------------------------------------------- #
def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def child_entry(fire_at: str | None, outcome: str = "pending",
                created_at: str | None = None, kind: str = "execute",
                target: str = "docs/history/plans/some-plan.md") -> dict:
    return {
        "automation_id": "child-1",
        "kind": kind,
        "target": target,
        "created_at": created_at or iso_z(datetime.now(timezone.utc) - timedelta(hours=2)),
        "requested_at": None,
        "fire_at": fire_at,
        "quota_status": "ok",
        "outcome": outcome,
        "outcome_checked_at": None,
        "progress_mark": None,
        "resume_count": 0,
        "outcome_reason": None,
        "dispatch_plan_sha": None,
    }


def listing_entry(repo_root: str, entry_id: str, enabled: bool = True,
                  title: str = RECOGNITION_TITLE, prompt: str | None = None) -> dict:
    if prompt is None:
        prompt = (
            RECOGNITION_OPENING + " " + repo_root
            + ". Run the maintenance skill scheduler turn end to end."
        )
    return {
        "automationId": entry_id,
        "title": title,
        "prompt": prompt,
        "enabled": enabled,
        "lifecycleStatus": "active" if enabled else "completed",
        "nextRunAt": iso_z(datetime.now(timezone.utc) + timedelta(minutes=90)),
        "runCount": 3,
        "recurring": True,
    }


def write_state(root: Path, drop_keys: tuple[str, ...] = (), **overrides) -> Path:
    """Write a full schema-4-shaped scheduler state file under the fixture root."""
    now = datetime.now(timezone.utc)
    state = {
        "schema": 4,
        "last_run_at": iso_z(now - timedelta(hours=1)),
        "parent_automation_id": "parent-live-1",
        "parent_absent_since": None,
        "pending_dispatch": None,
        "park_proposals": [],
        "rate_limited_events": [],
        "survey": {"open_backlog": 0, "open_plans": 0, "digest_intact_plans": 0},
        "decision": {"execution": "noop", "authoring": "noop"},
        "decision_reason": {"execution": "nothing dispatchable", "authoring": "nothing uncovered"},
        "pricing_cache": {
            "peak_window": "Mon-Fri 14:00-18:00 UTC+8",
            "multipliers": "0.4x off-peak, 1.2x peak",
            "last_verified": "2026-09-01",
            "source": "usage-revision notice",
        },
        "turn_error": None,
        "rearm_note": None,
        "children": [],
        "consecutive_failures": 0,
        "consecutive_turn_errors": 0,
        "alert": None,
    }
    state.update(overrides)
    for key in drop_keys:
        state.pop(key, None)
    path = root / ".ai-playbook" / "scheduler-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def run_check(repo_root: str, state_path: Path | None = None,
              listing: Path | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(SCRIPT), "--repo-root", repo_root]
    if state_path is not None:
        args += ["--state-path", str(state_path)]
    if listing is not None:
        args += ["--listing-json", str(listing)]
    return subprocess.run(args, capture_output=True, text=True, timeout=120)


def parse_verdict(proc: subprocess.CompletedProcess) -> dict:
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert lines, "no verdict on stdout: rc=%s stderr=%r" % (proc.returncode, proc.stderr)
    return json.loads(lines[0])


def with_field_value(raw: str, field: str, json_value: str) -> str:
    """Test-local surgical substitution of one top-level field's value."""
    pattern = re.compile(r'("%s"\s*:\s*)(null|"(?:[^"\\]|\\.)*")' % re.escape(field))
    out, count = pattern.subn(lambda m: m.group(1) + json_value, raw, count=1)
    assert count == 1, "field %s not found in fixture text" % field
    return out


# --------------------------------------------------------------------------- #
# The eleven plan checkboxes, one test per checkbox, in plan order.
# --------------------------------------------------------------------------- #
def test_class_parent_ok(tmp_path):
    """[class: REPOSITORY_TEST] Recorded live parent and null
    parent_absent_since: class parent-ok, no bookkeeping edits, rc 0."""
    root = str(tmp_path)
    state = write_state(tmp_path, parent_automation_id="parent-live-1",
                        parent_absent_since=None)
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "parent-ok"
    assert verdict["bookkeeping"] is None
    assert verdict["listing_used"] is False
    assert verdict["rearm_required"] is False
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


def test_class_surrendered_live_child(tmp_path):
    """[class: REPOSITORY_TEST] Absent parent with a pending children[] entry
    whose fire_at is 1 hour past and no failed outcome: class
    surrendered-live-child and no re-arm decision."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)
    child = child_entry(fire_at=iso_z(now - timedelta(hours=1)), outcome="pending")
    state = write_state(tmp_path, parent_automation_id="parent-live-1",
                        parent_absent_since=iso_z(now - timedelta(minutes=30)),
                        children=[child])
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "surrendered-live-child"
    assert verdict["rearm_required"] is False
    assert verdict["bookkeeping"] is None
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


def test_class_ghost_pending_does_not_suppress_darkness(tmp_path):
    """[class: REPOSITORY_TEST] Pending entry whose fire_at is 7 hours past
    with a failed outcome and parent_absent_since older than one cadence
    period (2 hours): class darkness-rearm-required."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)
    ghost = child_entry(fire_at=iso_z(now - timedelta(hours=7)), outcome="failed")
    write_state(tmp_path, parent_automation_id="parent-live-1",
                parent_absent_since=iso_z(now - timedelta(hours=3)),
                children=[ghost])

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "darkness-rearm-required"
    assert verdict["rearm_required"] is True
    assert verdict["bookkeeping"] is None


def test_class_fresh_absence_listing_required(tmp_path):
    """[class: REPOSITORY_TEST] Absent parent, no live pending child, and
    parent_absent_since younger than one cadence period: class
    listing-required with reason fresh-absence and no bookkeeping edits."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)
    state = write_state(tmp_path, parent_automation_id="parent-live-1",
                        parent_absent_since=iso_z(now - timedelta(minutes=30)),
                        children=[])
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "listing-required"
    assert verdict["reason"] == "fresh-absence"
    assert verdict["rearm_required"] is False
    assert verdict["bookkeeping"] is None
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


@pytest.mark.parametrize("variant", ["null", "missing"])
def test_class_null_parent_id_listing_required(tmp_path, variant):
    """[class: REPOSITORY_TEST] Null or missing parent_automation_id and no
    live pending child: class listing-required with reason null-parent-id and
    no bookkeeping edits."""
    root = str(tmp_path)
    drop = ("parent_automation_id",) if variant == "missing" else ()
    state = write_state(tmp_path, drop_keys=drop,
                        parent_automation_id=None, children=[])
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "listing-required"
    assert verdict["reason"] == "null-parent-id"
    assert verdict["bookkeeping"] is None
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


def test_class_stale_state_file(tmp_path):
    """[class: REPOSITORY_TEST] State file whose last write is older than one
    cadence period: class stale-state-listing-required (the staleness escape)
    and no bookkeeping edits."""
    root = str(tmp_path)
    state = write_state(tmp_path, parent_automation_id="parent-live-1",
                        parent_absent_since=None)
    past = time.time() - 3 * 3600
    os.utime(state, (past, past))
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "stale-state-listing-required"
    assert verdict["rearm_required"] is False
    assert verdict["bookkeeping"] is None
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


def test_no_state_file_skipped_reason(tmp_path):
    """[class: REPOSITORY_TEST] No scheduler state file: the explicit
    skipped-reason no-scheduler-state-file, rc 0, and an inert verdict."""
    root = str(tmp_path)
    missing = tmp_path / "nowhere" / "scheduler-state.json"

    proc = run_check(root, state_path=missing)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "no-scheduler-state-file"
    assert verdict["reason"] == "no-scheduler-state-file"
    assert verdict["skipped"] is True
    assert verdict["bookkeeping"] is None
    assert not missing.exists(), "the check created the state file it did not find"


def test_malformed_state_file_fails_loud(tmp_path):
    """[class: REPOSITORY_TEST] Unparseable JSON: rc 2 and a loud error, never
    a silent pass."""
    root = str(tmp_path)
    state = write_state(tmp_path)
    state.write_text("{ this is not json", encoding="utf-8")
    raw_before = state.read_text(encoding="utf-8")

    proc = run_check(root)

    assert proc.returncode == 2
    verdict = parse_verdict(proc)
    assert verdict["class"] == "malformed"
    assert proc.stderr.strip(), "malformed state must fail loud on stderr"
    assert "not parseable JSON" in proc.stderr
    assert state.read_text(encoding="utf-8") == raw_before, "state file was edited"


def test_listing_input_armed_again_bookkeeping(tmp_path):
    """[class: REPOSITORY_TEST] --listing-json whose parsed content shows an
    ENABLED recognition match (title match, prompt opening match, resolved
    repo root contained) and a set parent_absent_since: parent_absent_since
    cleared and rearm_note cleared in one atomic targeted edit with no other
    field touched."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)
    state = write_state(tmp_path, parent_automation_id="parent-live-1",
                        parent_absent_since=iso_z(now - timedelta(hours=3)),
                        rearm_note="re-arm refused: create refused twice")
    raw_before = state.read_text(encoding="utf-8")
    listing_path = tmp_path / "listing.json"
    listing_path.write_text(
        json.dumps([listing_entry(root, "parent-live-1", enabled=True)]),
        encoding="utf-8",
    )

    proc = run_check(root, listing=listing_path)

    assert proc.returncode == 0
    verdict = parse_verdict(proc)
    assert verdict["class"] == "parent-ok"
    assert verdict["listing_used"] is True
    assert verdict["recognition_matches"] == 1
    raw_after = state.read_text(encoding="utf-8")
    after = json.loads(raw_after)
    assert after["parent_absent_since"] is None
    assert after["rearm_note"] is None
    assert after["parent_automation_id"] == "parent-live-1"
    # Byte-for-byte: exactly the two named field values moved, nothing else.
    expected = with_field_value(raw_before, "parent_absent_since", "null")
    expected = with_field_value(expected, "rearm_note", "null")
    assert raw_after == expected


def test_adoption_guards(tmp_path):
    """[class: REPOSITORY_TEST] A listing match whose id differs from the
    recorded one: no adoption when the recorded id is itself live-enabled;
    adoption (with the earliest parent_absent_since retention rule) when the
    recorded id is absent-or-disabled."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)

    # (a) recorded id live-enabled in the listing: no adoption.
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=iso_z(now - timedelta(hours=1)),
                        rearm_note="refused once")
    listing_a = tmp_path / "listing-a.json"
    listing_a.write_text(json.dumps([
        listing_entry(root, "parent-A"),
        listing_entry(root, "parent-B"),
    ]), encoding="utf-8")
    proc = run_check(root, listing=listing_a)
    assert proc.returncode == 0
    after = json.loads(state.read_text(encoding="utf-8"))
    assert after["parent_automation_id"] == "parent-A", "adopted over a live parent"
    assert after["parent_absent_since"] is None
    assert after["rearm_note"] is None
    assert parse_verdict(proc)["class"] == "parent-ok"

    # (b) recorded id absent from the listing: adoption happens.
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=iso_z(now - timedelta(hours=3)),
                        rearm_note="refused once")
    listing_b = tmp_path / "listing-b.json"
    listing_b.write_text(json.dumps([listing_entry(root, "parent-B")]),
                         encoding="utf-8")
    proc = run_check(root, listing=listing_b)
    assert proc.returncode == 0
    after = json.loads(state.read_text(encoding="utf-8"))
    assert after["parent_automation_id"] == "parent-B", "differing-id match not adopted"
    assert after["parent_absent_since"] is None
    assert after["rearm_note"] is None
    assert parse_verdict(proc)["class"] == "parent-ok"

    # (b2) recorded id present but disabled (lingered completed record):
    # treated as absent, so adoption still happens.
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=iso_z(now - timedelta(hours=3)))
    listing_b2 = tmp_path / "listing-b2.json"
    listing_b2.write_text(json.dumps([
        listing_entry(root, "parent-A", enabled=False),
        listing_entry(root, "parent-B"),
    ]), encoding="utf-8")
    proc = run_check(root, listing=listing_b2)
    assert proc.returncode == 0
    after = json.loads(state.read_text(encoding="utf-8"))
    assert after["parent_automation_id"] == "parent-B", "disabled recorded id blocked adoption"

    # (c) earliest-value retention: an existing absence keeps the earlier
    # value and is never refreshed to a later observation's timestamp.
    earlier = iso_z(now - timedelta(hours=5))
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=earlier)
    listing_c = tmp_path / "listing-c.json"
    listing_c.write_text(json.dumps([
        listing_entry(root, "foreign-1", enabled=True, title="Some other title",
                      prompt="an unrelated prompt"),
    ]), encoding="utf-8")
    proc = run_check(root, listing=listing_c)
    assert proc.returncode == 0
    after = json.loads(state.read_text(encoding="utf-8"))
    assert after["parent_absent_since"] == earlier, "earliest absence value was refreshed"
    verdict = parse_verdict(proc)
    assert verdict["class"] == "darkness-rearm-required"
    assert verdict["rearm_required"] is True

    # (d) first observation: a null field is set at the observation time.
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=None)
    listing_d = tmp_path / "listing-d.json"
    listing_d.write_text(json.dumps([]), encoding="utf-8")
    before_observation = datetime.now(timezone.utc) - timedelta(seconds=5)
    proc = run_check(root, listing=listing_d)
    assert proc.returncode == 0
    after = json.loads(state.read_text(encoding="utf-8"))
    observed = parse_iso(after["parent_absent_since"])
    assert before_observation <= observed <= datetime.now(timezone.utc) + timedelta(seconds=5)
    verdict = parse_verdict(proc)
    assert verdict["class"] == "listing-required"
    assert verdict["reason"] == "fresh-absence"


def test_bookkeeping_edit_atomic_no_other_field(tmp_path, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] Any bookkeeping scenario: the write goes
    through a temp file plus atomic replace, changing only the named fields,
    preserving all others byte-for-byte."""
    root = str(tmp_path)
    now = datetime.now(timezone.utc)
    state = write_state(tmp_path, parent_automation_id="parent-A",
                        parent_absent_since=iso_z(now - timedelta(minutes=30)),
                        rearm_note="refused once")
    raw_before = state.read_text(encoding="utf-8")
    parsed_before = json.loads(raw_before)
    listing_path = tmp_path / "listing.json"
    listing_path.write_text(json.dumps([listing_entry(root, "parent-B")]),
                             encoding="utf-8")

    calls = []
    real_replace = os.replace

    def spy(src, dst):
        calls.append((os.fspath(src), os.fspath(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)

    rc = rearm_on_touch.main([
        "--repo-root", root,
        "--state-path", str(state),
        "--listing-json", str(listing_path),
    ])

    assert rc == 0
    captured = capsys.readouterr()
    verdict = json.loads(captured.out.splitlines()[0])
    # Atomic replace: exactly one, into the state path, from a sibling temp
    # name that the replace itself consumed.
    assert len(calls) == 1, "bookkeeping must land through one os.replace"
    src, dst = calls[0]
    assert dst == str(state)
    assert src != dst
    assert os.path.dirname(src) == os.path.dirname(dst)
    assert not os.path.exists(src), "temp file survived the replace"
    assert sorted(p.name for p in state.parent.iterdir()) == [state.name], "leftover files"
    # Only the named fields changed; every other line is byte-identical.
    raw_after = state.read_text(encoding="utf-8")
    expected = with_field_value(raw_before, "parent_automation_id", '"parent-B"')
    expected = with_field_value(expected, "parent_absent_since", "null")
    expected = with_field_value(expected, "rearm_note", "null")
    assert raw_after == expected
    parsed_after = json.loads(raw_after)
    for key, value in parsed_before.items():
        if key in ("parent_automation_id", "parent_absent_since", "rearm_note"):
            continue
        assert parsed_after[key] == value, "field %s moved unexpectedly" % key
    # The verdict reports the three applied edits.
    assert set(verdict["bookkeeping"]) == {
        "parent_automation_id", "parent_absent_since", "rearm_note"
    }
    assert verdict["class"] == "parent-ok"
