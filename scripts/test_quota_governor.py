#!/usr/bin/env python3
"""Hermetic suite for the account quota governor (injected probe reports,
injected mining payloads, temp state paths)."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import quota_governor as g  # noqa: E402


def probe_report(used, binding="primary", decision="continue", now=None):
    now = now if now is not None else time.time()
    limits = []
    if binding == "primary":
        limits.append({"kind": "primary", "used_percent": used,
                       "reset_at_epoch": int(now) + 3600,
                       "minutes_remaining": 60,
                       "reset_at_iso": datetime.fromtimestamp(int(now) + 3600).astimezone().isoformat()})
    if binding == "secondary":
        limits.append({"kind": "primary", "used_percent": 10.0,
                       "reset_at_epoch": int(now) + 3600, "minutes_remaining": 60})
        limits.append({"kind": "secondary", "used_percent": used,
                       "reset_at_epoch": int(now) + 7200, "minutes_remaining": 120})
    return {"runtime": "zcode", "limits": limits, "binding": binding,
            "pause_decision": decision, "reasons": [], "status": "ok"}


def mining(usable=True, episodes=(), exhaustion=()):
    return {"usable": usable, "episode_timestamps": list(episodes),
            "exhaustion_ts_list": list(exhaustion), "days": {}}


NOW = 1_800_000_000.0


# --- class boundaries -------------------------------------------------------

def test_tightening_boundary():
    assert g.evaluate_pressure(probe_report(59.9), mining(), NOW)[0] == "abundant"
    assert g.evaluate_pressure(probe_report(60.0), mining(), NOW)[0] == "tightening"


def test_constrained_boundary():
    assert g.evaluate_pressure(probe_report(79.9), mining(), NOW)[0] == "tightening"
    assert g.evaluate_pressure(probe_report(80.0), mining(), NOW)[0] == "constrained"


def test_exhausted_boundary():
    assert g.evaluate_pressure(probe_report(94.9), mining(), NOW)[0] == "constrained"
    assert g.evaluate_pressure(probe_report(95.0), mining(), NOW)[0] == "exhausted"


def test_pause_arm_primary_only():
    assert g.evaluate_pressure(probe_report(96.0, decision="pause"), mining(), NOW)[0] == "exhausted"
    # Secondary binding at 97 percent with no primary window: percent arms inert.
    no_primary = {"runtime": "zcode", "limits": [{"kind": "secondary", "used_percent": 97.0,
                                                  "reset_at_epoch": int(NOW) + 7200,
                                                  "minutes_remaining": 120}],
                  "binding": "secondary", "pause_decision": "continue", "status": "ok"}
    assert g.evaluate_pressure(no_primary, mining(), NOW)[0] == "abundant"
    # Secondary-binding pause with a low binding percent never reads exhausted.
    sec_pause = {"runtime": "zcode", "limits": [{"kind": "secondary", "used_percent": 10.0,
                                                 "reset_at_epoch": int(NOW) + 7200,
                                                 "minutes_remaining": 120}],
                 "binding": "secondary", "pause_decision": "pause", "status": "ok"}
    assert g.evaluate_pressure(sec_pause, mining(), NOW)[0] == "abundant"


# --- exhaustion window anchoring --------------------------------------------

def test_exhaustion_inside_live_window_counts():
    primary = probe_report(10.0, now=NOW)["limits"][0]
    window_start = primary["reset_at_epoch"] - g.CADENCE_SECONDS
    klass, _ = g.evaluate_pressure(probe_report(10.0, now=NOW),
                                   mining(exhaustion=[window_start + 60]), NOW)
    assert klass == "exhausted"


def test_exhaustion_previous_window_does_not_count():
    primary = probe_report(10.0, now=NOW)["limits"][0]
    window_start = primary["reset_at_epoch"] - g.CADENCE_SECONDS
    klass, _ = g.evaluate_pressure(probe_report(10.0, now=NOW),
                                   mining(exhaustion=[window_start - 60]), NOW)
    assert klass == "abundant"


def test_exhaustion_probeless_trailing_cadence_fallback():
    klass, _ = g.evaluate_pressure(None, mining(exhaustion=[NOW - 60]), NOW)
    assert klass == "exhausted"
    klass, _ = g.evaluate_pressure(None, mining(exhaustion=[NOW - g.CADENCE_SECONDS - 60]), NOW)
    # Mining is usable (a readable day yielded records) and the evidence is
    # stale, so the evidence-based class is abundant, not unknown.
    assert klass == "abundant"


def test_cross_midnight_union_counts():
    # Evidence logged on the previous local day, evaluated just after midnight:
    # the union of the two days' timestamps must carry it.
    yesterday_ts = NOW - 60
    merged = mining(episodes=[yesterday_ts] * 25)
    klass, _ = g.evaluate_pressure(probe_report(10.0, now=NOW), merged, NOW)
    assert klass == "constrained"


# --- unknown fail-open ------------------------------------------------------

def test_unknown_unusable_probe_and_mining():
    assert g.evaluate_pressure(None, mining(usable=False), NOW)[0] == "unknown"
    assert g.evaluate_pressure({"status": "unknown", "limits": []}, mining(usable=False), NOW)[0] == "unknown"
    # Never reads as abundant.
    report = g.evaluate_pressure(None, {"usable": False}, NOW)
    assert report[0] == "unknown"


def test_unknown_missing_day_file_cell():
    summary = {"day": "x", "rate_limited_episodes": 0,
               "episodes_by_source": {"main_turn": 0, "subagent": 0, "other": 0},
               "episode_timestamps": [], "exhaustion_event_count": 0,
               "last_exhaustion_ts": None}
    # A record-free day is not usable evidence even when merged into mining.
    m = {"usable": False, "episode_timestamps": [], "exhaustion_ts_list": [],
         "days": {"x": summary}}
    assert g.evaluate_pressure(None, m, NOW)[0] == "unknown"


def test_episodes_only_constrained_with_unusable_probe():
    episodes = [NOW - i for i in range(25)]
    klass, reasons = g.evaluate_pressure(None, mining(episodes=episodes), NOW)
    assert klass == "constrained"
    # Headroom-gated cells allow with the absent-reading named.
    verdicts = g.policy_verdicts({"class": "constrained", "inputs": {"primary_used_percent": None}}, NOW)
    assert verdicts["execution"]["verdict"] == "defer"
    assert verdicts["authoring"]["verdict"] == "allow"
    assert "absent primary reading" in verdicts["authoring"]["reason"]


# --- state schema, lock, version skew ---------------------------------------

def test_state_roundtrip_and_mode(tmp_path):
    path = tmp_path / "runtime" / "quota-governor-state.json"
    state = g.new_state(NOW)
    assert g.write_state(path, state)
    loaded = g.read_state(path)
    assert loaded["version"] == g.STATE_VERSION
    assert set(loaded) == {"version", "updated_at_epoch", "updated_by", "pressure",
                           "reset_at_epoch", "reset_at_iso", "reserve_percent",
                           "window_samples", "metrics"}
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"


def test_lock_file_name(tmp_path):
    path = tmp_path / "quota-governor-state.json"
    assert g.lock_path_for(path) == str(tmp_path / "quota-governor.lock")


def test_version_skew_fails_closed(tmp_path):
    path = tmp_path / "quota-governor-state.json"
    future = g.new_state(NOW)
    future["version"] = g.STATE_VERSION + 1
    g.write_state(path, future)
    # Writer refuses to clobber the newer schema.
    assert not g.write_state(path, g.new_state(NOW + 1))
    assert g.read_state(path)["version"] == g.STATE_VERSION + 1
    # Consult reports unknown with that reason.
    report = g.consult(path, NOW)
    assert report["class"] == "unknown"
    assert "greater than script version" in report["reason"]


def test_stale_state_unknown(tmp_path):
    path = tmp_path / "s.json"
    state = g.new_state(NOW - g.STATE_STALE_SECONDS - 1)
    g.write_state(path, state)
    assert g.consult(path, NOW)["class"] == "unknown"
    fresh = g.new_state(NOW)
    fresh["pressure"]["class"] = "abundant"
    g.write_state(path, fresh)
    assert g.consult(path, NOW)["class"] == "abundant"


@pytest.mark.parametrize("payload", ["{not json", "[1,2,3]", '{"nope": 1}'])
def test_corrupt_state_unknown(tmp_path, payload):
    path = tmp_path / "c.json"
    path.write_text(payload)
    assert g.consult(path, NOW)["class"] == "unknown"


# --- policy cells -----------------------------------------------------------

def policy_inputs(used):
    return {"class": None, "inputs": {"primary_used_percent": used}}


def test_policy_cells():
    verdicts = g.policy_verdicts({"class": "abundant", "inputs": {}}, NOW)
    assert verdicts["execution"]["verdict"] == "allow"
    assert verdicts["authoring"]["verdict"] == "allow"

    # tightening: execution gated at RESERVE + 10 (used <= 75).
    v = g.policy_verdicts({"class": "tightening", "inputs": {"primary_used_percent": 74.0}}, NOW)
    assert v["execution"]["verdict"] == "allow"
    v = g.policy_verdicts({"class": "tightening", "inputs": {"primary_used_percent": 76.0}}, NOW)
    assert v["execution"]["verdict"] == "defer"

    # constrained: execution always deferred, authoring gated at floor (used <= 70).
    v = g.policy_verdicts({"class": "constrained", "inputs": {"primary_used_percent": 69.0}}, NOW)
    assert v["execution"]["verdict"] == "defer" and v["authoring"]["verdict"] == "allow"
    v = g.policy_verdicts({"class": "constrained", "inputs": {"primary_used_percent": 71.0}}, NOW)
    assert v["authoring"]["verdict"] == "defer"

    # exhausted: both deferred with the host-local reset time in the reason.
    v = g.policy_verdicts({"class": "exhausted", "inputs": {},
                           "reset_at_epoch": int(NOW) + 600}, NOW)
    assert v["execution"]["verdict"] == "defer" and v["authoring"]["verdict"] == "defer"
    assert "resets at" in v["execution"]["reason"]

    # unknown: fail-open both allowed.
    v = g.policy_verdicts({"class": "unknown", "inputs": {}}, NOW)
    assert v["execution"]["verdict"] == "allow" and v["authoring"]["verdict"] == "allow"


# --- refresh merging and caps -----------------------------------------------

def test_refresh_merges_and_caps(tmp_path, monkeypatch):
    state_path = tmp_path / "s.json"
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    # Build a readable day file so mining is usable and merges into by_day.
    import quota_pressure_stats as stats
    day = stats._shift_day(datetime.fromtimestamp(NOW).strftime("%Y-%m-%d"), -1)
    (log_dir / "zcode-{}.jsonl".format(day)).write_text(
        json.dumps({"timestamp": "2026-09-28T10:00:00.000Z", "event": "model.request.failed",
                    "sessionId": "s1", "turnId": "t1",
                    "context": {"statusCode": 429, "reason": "rate_limited",
                                "querySource": "main_turn",
                                "statusMessage": "[1302][Rate limit][tok1]"}}) + "\n")
    probe = probe_report(83.0, now=NOW)
    report = g.refresh(str(state_path), log_dir=str(log_dir), updated_by="test:1",
                       now=NOW, probe_report=probe)
    assert report["class"] == "constrained"
    assert report["refresh_wrote_state"] is True
    state = g.read_state(state_path)
    assert state["pressure"]["inputs"]["primary_used_percent"] == 83.0
    assert day in state["metrics"]["by_day"]
    assert state["window_samples"][-1]["used_percent"] == 83.0
    assert len(state["window_samples"]) <= g.WINDOW_SAMPLES_CAP


def test_refresh_lock_timeout_skips_write(tmp_path, monkeypatch):
    import fcntl as f
    state_path = tmp_path / "s.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(g.lock_path_for(state_path), os.O_CREAT | os.O_RDWR, 0o600)
    f.flock(lock_fd, f.LOCK_EX)
    try:
        report = g.refresh(str(state_path), log_dir=str(tmp_path),
                           updated_by="t", now=NOW, probe_report=probe_report(50.0, now=NOW))
        assert report["refresh_wrote_state"] is False
        assert not state_path.exists() or g.read_state(state_path) is None
    finally:
        f.flock(lock_fd, f.LOCK_UN)
        os.close(lock_fd)


def test_two_refresh_interlock(tmp_path):
    state_path = tmp_path / "s.json"
    r1 = g.refresh(str(state_path), log_dir=str(tmp_path), updated_by="a",
                   now=NOW, probe_report=probe_report(10.0, now=NOW))
    r2 = g.refresh(str(state_path), log_dir=str(tmp_path), updated_by="b",
                   now=NOW + 5, probe_report=probe_report(20.0, now=NOW + 5))
    assert r1["refresh_wrote_state"] and r2["refresh_wrote_state"]
    assert g.read_state(state_path)["pressure"]["inputs"]["primary_used_percent"] == 20.0


def test_refresh_none_runtime_degrades_unknown(tmp_path, monkeypatch):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "none")
    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(tmp_path),
                       updated_by="t", now=NOW)
    assert report["class"] == "unknown"
    assert "runtime detection degraded" in report.get("reason", "")


def test_refresh_probe_transport_failure_fails_open(tmp_path, monkeypatch):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "zcode")
    def boom(*a, **k):
        raise OSError("transport down")
    monkeypatch.setattr(probe, "run_probe", boom)
    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(tmp_path),
                       updated_by="t", now=NOW)
    assert report["class"] == "unknown"
    assert "probe transport failed" in report.get("reason", "")


# --- consult CLI contract ----------------------------------------------------

def test_consult_cli_absent_state(tmp_path):
    out = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "quota_governor.py"),
         "--consult", "--state-path", str(tmp_path / "absent.json")],
        capture_output=True, text=True)
    assert out.returncode == 0
    report = json.loads(out.stdout)
    assert report["class"] == "unknown"
