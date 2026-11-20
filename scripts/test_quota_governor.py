#!/usr/bin/env python3
"""Hermetic suite for the account quota governor (injected probe reports,
injected mining payloads, temp state paths)."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import quota_governor as g  # noqa: E402


def test_runtime_source_registry_is_shared_by_probe_and_governor():
    import quota_sources
    import quota_window_probe as probe

    assert g.RUNTIME_SOURCES is quota_sources.RUNTIME_SOURCES
    assert probe.RUNTIME_SOURCES is quota_sources.RUNTIME_SOURCES


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
    return {"runtime": "zcode", "source": "zcode-quota-endpoint",
            "observed_at_epoch": now, "limits": limits, "binding": binding,
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
    assert g.evaluate_pressure(no_primary, mining(), NOW)[0] == "unknown"
    # Secondary-binding pause with a low binding percent never reads exhausted.
    sec_pause = {"runtime": "zcode", "limits": [{"kind": "secondary", "used_percent": 10.0,
                                                 "reset_at_epoch": int(NOW) + 7200,
                                                 "minutes_remaining": 120}],
                 "binding": "secondary", "pause_decision": "pause", "status": "ok"}
    assert g.evaluate_pressure(sec_pause, mining(), NOW)[0] == "unknown"


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
    # Quiet or stale logs do not establish an all-clear without a live primary.
    assert klass == "unknown"


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
    fresh["pressure"].update({"runtime": "zcode", "source": "zcode-quota-endpoint",
                              "observed_at_epoch": NOW, "windows": []})
    g.write_state(path, fresh)
    assert g.consult(path, NOW, runtime="zcode")["class"] == "abundant"


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
                       now=NOW, probe_report=probe, runtime="zcode")
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
                           updated_by="t", now=NOW, probe_report=probe_report(50.0, now=NOW),
                           runtime="zcode")
        assert report["refresh_wrote_state"] is False
        assert not state_path.exists() or g.read_state(state_path) is None
    finally:
        f.flock(lock_fd, f.LOCK_UN)
        os.close(lock_fd)


def test_refresh_lock_timeout_without_matching_cache_returns_unknown(tmp_path, monkeypatch):
    from contextlib import contextmanager

    import quota_window_probe as probe

    state_path = tmp_path / "s.json"
    @contextmanager
    def timed_out_lock(*args, **kwargs):
        yield False

    monkeypatch.setattr(g, "governor_lock", timed_out_lock)
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "codex")
    monkeypatch.setattr(probe, "run_probe", lambda runtime: codex_report(10, NOW))

    report = g.refresh(str(state_path), log_dir=str(tmp_path), updated_by="t",
                       now=NOW + 1)

    assert report["class"] == "unknown"
    assert report["refresh_wrote_state"] is False
    assert report["dispatch"]["execution"]["verdict"] == "allow"
    assert report["dispatch"]["authoring"]["verdict"] == "allow"
    assert not state_path.exists()


def test_refresh_response_survives_other_runtime_overwrite_after_lock_release(
        tmp_path, monkeypatch):
    from contextlib import contextmanager

    state_path = tmp_path / "s.json"
    original_refresh = g.refresh
    interleaved = False

    @contextmanager
    def interleaving_lock(*args, **kwargs):
        nonlocal interleaved
        yield True
        if not interleaved:
            interleaved = True
            zcode = probe_report(96.0, decision="pause", now=NOW + 1)
            original_refresh(str(state_path), log_dir=str(tmp_path),
                             updated_by="zcode", now=NOW + 1,
                             probe_report=zcode, runtime="zcode")

    monkeypatch.setattr(g, "governor_lock", interleaving_lock)
    codex = codex_report(10.0, NOW)

    report = original_refresh(str(state_path), log_dir=str(tmp_path),
                              updated_by="codex", now=NOW,
                              probe_report=codex, runtime="codex")

    assert interleaved
    assert g.read_state(state_path)["pressure"]["class"] == "exhausted"
    assert report["class"] == "abundant"
    assert report["refresh_wrote_state"] is True
    assert report["dispatch"]["execution"]["verdict"] == "allow"
    assert report["dispatch"]["authoring"]["verdict"] == "allow"


def test_two_refresh_interlock(tmp_path):
    state_path = tmp_path / "s.json"
    r1 = g.refresh(str(state_path), log_dir=str(tmp_path), updated_by="a",
                   now=NOW, probe_report=probe_report(10.0, now=NOW), runtime="zcode")
    r2 = g.refresh(str(state_path), log_dir=str(tmp_path), updated_by="b",
                   now=NOW + 5, probe_report=probe_report(20.0, now=NOW + 5), runtime="zcode")
    assert r1["refresh_wrote_state"] and r2["refresh_wrote_state"]
    assert g.read_state(state_path)["pressure"]["inputs"]["primary_used_percent"] == 20.0


def test_refresh_none_runtime_degrades_unknown(tmp_path, monkeypatch):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "none")
    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(tmp_path),
                       updated_by="t", now=NOW)
    assert report["class"] == "unknown"
    assert "runtime detection degraded" in report.get("reason", "")


def test_refresh_injected_report_must_match_detected_runtime(tmp_path, monkeypatch):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "codex")

    report = g.refresh(str(tmp_path / "state.json"), log_dir=str(tmp_path),
                       updated_by="mismatched-injection", now=NOW,
                       probe_report=probe_report(10.0, now=NOW))

    assert report["class"] == "unknown"
    assert report["runtime"] == "codex"
    assert report["source"] == "codex-app-server/account/rateLimits/read"
    assert report["windows"] == []
    assert "detected runtime" in report["reason"]


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


def _write_current_zcode_exhaustion(log_dir):
    day = datetime.fromtimestamp(NOW).strftime("%Y-%m-%d")
    timestamp = datetime.fromtimestamp(NOW).astimezone().isoformat()
    (log_dir / "zcode-{}.jsonl".format(day)).write_text(json.dumps({
        "timestamp": timestamp,
        "event": "model.request.failed",
        "sessionId": "s1",
        "turnId": "t1",
        "context": {"statusCode": 429, "reason": "rate_limited",
                    "statusMessage": "[1308][Usage limit reached][tok1308]"},
    }) + "\n")


def test_refresh_codex_ignores_zcode_exhaustion_log(tmp_path, monkeypatch):
    import quota_window_probe as probe
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write_current_zcode_exhaustion(log_dir)
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "codex")
    monkeypatch.setattr(probe, "run_probe", lambda runtime: {
        "runtime": runtime, "limits": [], "binding": None,
        "pause_decision": "continue", "status": "ok"})

    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(log_dir),
                       updated_by="t", now=NOW)

    assert report["class"] == "unknown"
    assert report["dispatch"]["execution"]["verdict"] == "allow"
    assert report["dispatch"]["authoring"]["verdict"] == "allow"


def test_zcode_unusable_probe_and_ordinary_parseable_logs_remain_unknown(
        tmp_path, monkeypatch):
    import quota_window_probe as probe

    class UTCDateTime(datetime):
        @classmethod
        def fromtimestamp(cls, timestamp, tz=None):
            return datetime.fromtimestamp(timestamp, timezone.utc)

    monkeypatch.setattr(g, "datetime", UTCDateTime)
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    fixture_time = UTCDateTime.fromtimestamp(NOW)
    day = fixture_time.strftime("%Y-%m-%d")
    timestamp = fixture_time.isoformat()
    (log_dir / "zcode-{}.jsonl".format(day)).write_text(json.dumps({
        "timestamp": timestamp, "event": "model.request.started",
        "sessionId": "s1", "turnId": "t1",
        "context": {"statusCode": 429, "statusMessage": "ordinary parseable event"},
    }) + "\n")
    monkeypatch.setattr(probe, "detect_runtime", lambda: "zcode")
    monkeypatch.setattr(probe, "run_probe", lambda runtime: {
        "runtime": "zcode", "source": ZCODE_SOURCE,
        "observed_at_epoch": NOW, "limits": [], "status": "unknown"})

    report = g.refresh(str(tmp_path / "state.json"), log_dir=str(log_dir),
                       now=NOW)

    assert report["class"] == "unknown"
    assert report["runtime"] == "zcode"
    assert report["source"] == ZCODE_SOURCE
    assert report["windows"] == []


def test_refresh_zcode_uses_its_own_exhaustion_log(tmp_path, monkeypatch):
    import quota_window_probe as probe
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write_current_zcode_exhaustion(log_dir)
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "zcode")
    monkeypatch.setattr(probe, "run_probe", lambda runtime: probe_report(10.0, now=NOW))

    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(log_dir),
                       updated_by="t", now=NOW)

    assert report["class"] == "exhausted"
    assert report["dispatch"]["execution"]["verdict"] == "defer"
    assert report["dispatch"]["authoring"]["verdict"] == "defer"


def test_refresh_primary_exhaustion_still_pauses_codex(tmp_path, monkeypatch):
    import quota_window_probe as probe
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "codex")
    probed_runtimes = []

    def run_probe(runtime):
        probed_runtimes.append(runtime)
        return codex_report(96.0, NOW)

    monkeypatch.setattr(probe, "run_probe", run_probe)

    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(log_dir),
                       updated_by="t", now=NOW)

    assert probed_runtimes == ["codex"]
    assert report["class"] == "exhausted"
    assert report["dispatch"]["execution"]["verdict"] == "defer"
    assert report["dispatch"]["authoring"]["verdict"] == "defer"


def test_refresh_unrecognized_runtime_ignores_zcode_exhaustion_log(tmp_path, monkeypatch):
    import quota_window_probe as probe
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write_current_zcode_exhaustion(log_dir)
    monkeypatch.setattr(probe, "detect_runtime", lambda *a, **k: "unrecognized")

    report = g.refresh(str(tmp_path / "s.json"), log_dir=str(log_dir),
                       updated_by="t", now=NOW)

    assert report["class"] == "unknown"
    assert report["dispatch"]["execution"]["verdict"] == "allow"
    assert report["dispatch"]["authoring"]["verdict"] == "allow"


CODEX_SOURCE = "codex-app-server/account/rateLimits/read"
ZCODE_SOURCE = "zcode-quota-endpoint"


def codex_report(used=42.0, observed=NOW - 20):
    return {
        "runtime": "codex",
        "source": CODEX_SOURCE,
        "observed_at_epoch": observed,
        "limits": [
            {"kind": "primary", "used_percent": used,
             "window_minutes": 300, "window_name": "short",
             "reset_at_epoch": int(NOW) + 3600, "minutes_remaining": 60,
             "reset_at_iso": "2030-01-01T00:00:00+00:00"},
            {"kind": "secondary", "used_percent": 12.0,
             "window_minutes": 10080, "window_name": "long",
             "reset_at_epoch": int(NOW) + 7200, "minutes_remaining": 120,
             "reset_at_iso": "2030-01-01T01:00:00+00:00"},
        ],
        "binding": "primary", "pause_decision": "continue", "status": "ok",
    }


def test_refresh_preserves_probe_provenance_windows_and_classification_time(
        tmp_path, monkeypatch):
    import quota_window_probe as probe

    state_path = tmp_path / "state.json"
    report_from_probe = codex_report()
    monkeypatch.setattr(probe, "detect_runtime", lambda: pytest.fail("explicit runtime must skip auto-detect"))
    seen = []

    def run_probe(runtime):
        seen.append(runtime)
        return report_from_probe

    monkeypatch.setattr(probe, "run_probe", run_probe)
    report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW,
                       runtime="codex")

    state_pressure = g.read_state(state_path)["pressure"]
    assert seen == ["codex"]
    assert report["runtime"] == state_pressure["runtime"] == "codex"
    assert report["source"] == state_pressure["source"] == CODEX_SOURCE
    assert report["observed_at_epoch"] == state_pressure["observed_at_epoch"] == NOW - 20
    assert report["computed_at_epoch"] == state_pressure["computed_at_epoch"] == NOW
    assert report["windows"] == state_pressure["windows"] == report_from_probe["limits"]
    assert [w["window_minutes"] for w in report["windows"]] == [300, 10080]


def test_refresh_rejects_unrepresentably_large_probe_observation(tmp_path):
    report = g.refresh(
        str(tmp_path / "state.json"), now=NOW, runtime="codex",
        probe_report=codex_report(observed=10 ** 1000),
    )

    assert report["class"] == "unknown"
    assert report["windows"] == []
    assert report["observed_at_epoch"] is None


def test_oversized_primary_usage_is_unknown_in_classifier_and_refresh(tmp_path):
    malformed = codex_report(used=10 ** 1000)
    state_path = tmp_path / "state.json"

    pressure_class, _reasons = g.evaluate_pressure(malformed, mining(), NOW)
    report = g.refresh(
        str(state_path), now=NOW, runtime="codex",
        probe_report=malformed,
    )

    assert pressure_class == "unknown"
    assert report["class"] == "unknown"
    assert report["windows"] == []
    assert g.read_state(state_path)["pressure"]["inputs"]["primary_used_percent"] is None


def test_refresh_rejects_probe_report_with_mismatched_source(tmp_path):
    state_path = tmp_path / "state.json"
    bad_report = codex_report(96.0)
    bad_report["source"] = ZCODE_SOURCE

    report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW,
                       runtime="codex", probe_report=bad_report)

    assert report["class"] == "unknown"
    assert report["windows"] == []
    assert g.read_state(state_path)["pressure"]["windows"] == []


def test_consult_requires_matching_runtime_and_source(tmp_path):
    state_path = tmp_path / "state.json"
    pressure = {"class": "exhausted", "computed_at_epoch": NOW,
                "runtime": "codex", "source": CODEX_SOURCE,
                "observed_at_epoch": NOW - 20,
                "windows": codex_report()["limits"],
                "inputs": {"primary_used_percent": 96.0}}
    state = g.new_state(NOW)
    state["pressure"] = pressure
    assert g.write_state(state_path, state)

    assert g.consult(state_path, NOW, runtime="codex")["class"] == "exhausted"
    assert g.consult(state_path, NOW, runtime="zcode")["class"] == "unknown"
    assert g.consult(state_path, NOW, runtime="codex", source=ZCODE_SOURCE)["class"] == "unknown"


@pytest.mark.parametrize("klass", ["abundant", "tightening", "constrained", "exhausted"])
@pytest.mark.parametrize("inputs", [None, {}])
def test_consult_rejects_non_unknown_codex_cache_without_primary_usage(tmp_path, klass, inputs):
    state_path = tmp_path / "state.json"
    state = g.new_state(NOW)
    state["pressure"].update({
        "class": klass,
        "runtime": "codex",
        "source": CODEX_SOURCE,
        "inputs": {"primary_used_percent": None} if inputs is None else inputs,
    })
    assert g.write_state(state_path, state)

    report = g.consult(state_path, NOW, runtime="codex")

    assert report["status"] == "unknown"
    assert report["class"] == "unknown"
    assert report["dispatch"]["execution"]["verdict"] == "allow"


@pytest.mark.parametrize("klass,inputs,reset", [
    ("tightening", {"primary_used_percent": 10 ** 1000}, NOW + 3600),
    ("exhausted", {}, 10 ** 1000),
])
def test_consult_rejects_unusable_cached_numeric_evidence(tmp_path, klass, inputs, reset):
    state_path = tmp_path / "state.json"
    state = g.new_state(NOW)
    state["pressure"].update({
        "class": klass,
        "runtime": "codex",
        "source": CODEX_SOURCE,
        "inputs": inputs,
        "reset_at_epoch": reset,
    })
    state["reset_at_epoch"] = reset
    assert g.write_state(state_path, state)

    report = g.consult(state_path, NOW, runtime="codex")

    assert report["status"] == "unknown"
    assert report["class"] == "unknown"
    assert report["dispatch"]["execution"]["verdict"] == "allow"


@pytest.mark.parametrize("field,value", [
    ("updated_at_epoch", float("inf")),
    ("updated_at_epoch", float("nan")),
    ("updated_at_epoch", 1e300),
    ("pressure.observed_at_epoch", float("inf")),
    ("pressure.observed_at_epoch", float("nan")),
    ("pressure.observed_at_epoch", 1e300),
    ("pressure.computed_at_epoch", float("inf")),
    ("pressure.computed_at_epoch", float("nan")),
    ("pressure.computed_at_epoch", 1e300),
])
def test_consult_rejects_invalid_cached_timestamps(tmp_path, field, value):
    state_path = tmp_path / "state.json"
    state = g.new_state(NOW)
    state["pressure"].update({
        "class": "exhausted",
        "runtime": "codex",
        "source": CODEX_SOURCE,
        "observed_at_epoch": NOW,
        "inputs": {"primary_used_percent": 96.0},
        "reset_at_epoch": NOW + 3600,
    })
    if field == "updated_at_epoch":
        state[field] = value
    else:
        state["pressure"][field.split(".", 1)[1]] = value
    assert g.write_state(state_path, state)

    report = g.consult(state_path, NOW, runtime="codex")

    assert report["status"] == "unknown"
    assert report["class"] == "unknown"
    assert report["dispatch"]["execution"]["verdict"] == "allow"


@pytest.mark.parametrize("stored_observed", [float("inf"), float("nan"), 1e300])
def test_refresh_replaces_invalid_cached_observation(tmp_path, stored_observed):
    state_path = tmp_path / "state.json"
    state = g.new_state(NOW)
    state["pressure"].update({
        "class": "exhausted",
        "runtime": "codex",
        "source": CODEX_SOURCE,
        "observed_at_epoch": stored_observed,
        "inputs": {"primary_used_percent": 96.0},
        "reset_at_epoch": NOW + 3600,
    })
    assert g.write_state(state_path, state)
    fresh_probe = {
        "runtime": "codex", "source": CODEX_SOURCE,
        "observed_at_epoch": NOW + 10, "status": "ok",
        "binding": "primary", "pause_decision": "continue",
        "limits": [{"kind": "primary", "used_percent": 10.0,
                    "minutes_remaining": 50, "reset_at_epoch": NOW + 3600}],
    }

    report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW,
                       runtime="codex", probe_report=fresh_probe)

    assert report["class"] == "abundant"
    assert report["refresh_wrote_state"] is True
    assert g.read_state(state_path)["pressure"]["observed_at_epoch"] == NOW + 10


@pytest.mark.parametrize("older_used,newer_used,stored_runtime,stored_source,expected", [
    (10.0, 96.0, "codex", CODEX_SOURCE, "exhausted"),
    (96.0, 10.0, "codex", CODEX_SOURCE, "abundant"),
    (10.0, 96.0, "zcode", ZCODE_SOURCE, "unknown"),
    (10.0, 96.0, "codex", ZCODE_SOURCE, "unknown"),
])
def test_older_observation_loses_under_lock_and_returns_only_newer_matching_cache(
        tmp_path, monkeypatch, older_used, newer_used, stored_runtime, stored_source, expected):
    from contextlib import contextmanager

    state_path = tmp_path / "state.json"
    newer = codex_report(newer_used, NOW - 1)
    newer_state = g.new_state(NOW + 1)
    newer_state["pressure"].update({
        "class": "exhausted" if newer_used >= 95 else "abundant",
        "computed_at_epoch": NOW + 1,
        "runtime": stored_runtime, "source": stored_source,
        "observed_at_epoch": newer["observed_at_epoch"],
        "windows": newer["limits"],
        "inputs": {"primary_used_percent": newer_used},
    })

    @contextmanager
    def store_newer_before_read(*args, **kwargs):
        state_path.write_text(json.dumps(newer_state))
        yield True

    monkeypatch.setattr(g, "governor_lock", store_newer_before_read)
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda: pytest.fail("explicit runtime must skip auto-detect"))
    monkeypatch.setattr(probe, "run_probe", lambda runtime: codex_report(older_used, NOW - 30))

    report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW,
                       runtime="codex")

    assert report["class"] == expected
    assert report["runtime"] == "codex"
    if expected == "unknown":
        assert report["windows"] == []
    else:
        assert report["observed_at_epoch"] == NOW - 1
    assert g.read_state(state_path)["pressure"]["observed_at_epoch"] == NOW - 1
    assert report["refresh_wrote_state"] is False


@pytest.mark.parametrize("cache_kind,expected", [
    ("matching-newer", "exhausted"),
    ("matching-stale", "unknown"),
    ("mismatched-runtime", "unknown"),
    ("mismatched-source", "unknown"),
    ("absent", "unknown"),
])
def test_lock_timeout_uses_only_newer_matching_runtime_cache(
        tmp_path, monkeypatch, cache_kind, expected):
    from contextlib import contextmanager
    import quota_window_probe as probe

    state_path = tmp_path / "state.json"
    if cache_kind != "absent":
        cached = g.new_state(NOW)
        cached["pressure"].update({
            "class": "exhausted", "computed_at_epoch": NOW,
            "runtime": "codex", "source": CODEX_SOURCE,
            "observed_at_epoch": NOW + 1 if cache_kind == "matching-newer" else NOW - 10,
            "windows": codex_report(96, NOW + 1 if cache_kind == "matching-newer" else NOW - 10)["limits"],
            "inputs": {"primary_used_percent": 96.0},
        })
        if cache_kind == "matching-stale":
            cached["updated_at_epoch"] = NOW - g.STATE_STALE_SECONDS - 1
        elif cache_kind == "mismatched-runtime":
            cached["pressure"]["runtime"] = "zcode"
        elif cache_kind == "mismatched-source":
            cached["pressure"]["source"] = ZCODE_SOURCE
        assert g.write_state(state_path, cached)

    @contextmanager
    def timed_out_lock(*args, **kwargs):
        yield False

    monkeypatch.setattr(g, "governor_lock", timed_out_lock)
    monkeypatch.setattr(probe, "detect_runtime", lambda: pytest.fail("explicit runtime must skip auto-detect"))
    monkeypatch.setattr(probe, "run_probe", lambda runtime: codex_report(10, NOW - 2))
    report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW,
                       runtime="codex")

    assert report["class"] == expected
    assert report["refresh_wrote_state"] is False
    if expected == "unknown":
        assert report.get("runtime") == "codex"


def test_unsupported_explicit_runtime_does_not_detect_or_probe(tmp_path, monkeypatch):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda: pytest.fail("explicit unsupported runtime must not autodetect"))
    monkeypatch.setattr(probe, "run_probe", lambda runtime: pytest.fail("unsupported runtime must not probe"))
    report = g.refresh(str(tmp_path / "state.json"), log_dir=str(tmp_path),
                       now=NOW, runtime="other")
    assert report["class"] == "unknown"
    assert report["status"] == "unknown"


@pytest.mark.parametrize("runtime", [[], {}], ids=["list", "dict"])
@pytest.mark.parametrize("operation", ["consult", "refresh"])
def test_unhashable_explicit_runtime_returns_unknown(tmp_path, monkeypatch, runtime, operation):
    import quota_window_probe as probe
    monkeypatch.setattr(probe, "detect_runtime", lambda: pytest.fail("explicit runtime must not autodetect"))
    monkeypatch.setattr(probe, "run_probe", lambda value: pytest.fail("unsupported runtime must not probe"))
    state_path = tmp_path / "state.json"

    if operation == "consult":
        report = g.consult(state_path, NOW, runtime=runtime)
    else:
        report = g.refresh(str(state_path), log_dir=str(tmp_path), now=NOW, runtime=runtime)

    assert report["status"] == "unknown"
    assert report["class"] == "unknown"


def test_governor_cli_codex_refresh_and_consult_are_hermetic(tmp_path):
    fixed_now = 1_900_000_000.0
    fake_bin = tmp_path / "bin"
    fake_home = tmp_path / "home"
    canary_dir = tmp_path / "canary"
    fake_bin.mkdir()
    fake_home.mkdir()
    canary_dir.mkdir()
    (fake_home / ".codex").mkdir()
    (fake_home / ".codex" / "auth.json").write_text('{"token":"DO_NOT_READ"}')
    marker = tmp_path / "credential-read.txt"
    (canary_dir / "sitecustomize.py").write_text(
        "import builtins, io, os, time\n"
        f"time.time = lambda: {fixed_now!r}\n"
        "_open = builtins.open\n"
        "_io_open = io.open\n"
        "_os_open = os.open\n"
        "def _guard(path, *a, **kw):\n"
        "    value = os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else ''\n"
        f"    if 'auth.json' in value: _open({str(marker)!r}, 'w').write('read')\n"
        "    return _open(path, *a, **kw)\n"
        "def _guard_io(path, *a, **kw):\n"
        "    value = os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else ''\n"
        f"    if 'auth.json' in value: _open({str(marker)!r}, 'w').write('read')\n"
        "    return _io_open(path, *a, **kw)\n"
        "def _guard_os(path, *a, **kw):\n"
        "    value = os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else ''\n"
        f"    if 'auth.json' in value: _open({str(marker)!r}, 'w').write('read')\n"
        "    return _os_open(path, *a, **kw)\n"
        "builtins.open = _guard\n"
        "io.open = _guard_io\n"
        "os.open = _guard_os\n")
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "assert sys.argv[1:] == ['app-server']\n"
        "for line in sys.stdin:\n"
        "    request = json.loads(line)\n"
        "    assert 'jsonrpc' not in request\n"
        "    if request.get('method') == 'initialize':\n"
        "        result = {}\n"
        "    elif request.get('method') == 'account/rateLimits/read':\n"
        "        result = {'rateLimits': {'primary': {'usedPercent': 22, 'windowDurationMins': 300, 'resetsAt': 1900003600}, 'secondary': {'usedPercent': 8, 'windowDurationMins': 10080, 'resetsAt': 1900007200}}}\n"
        "    else:\n"
        "        continue\n"
        "    print(json.dumps({'id':request['id'], 'result':result}), flush=True)\n")
    fake_codex.chmod(0o755)
    state_path = tmp_path / "state.json"
    env = {"HOME": str(fake_home), "PATH": str(fake_bin),
           "PYTHONPATH": str(canary_dir), "ZCODE_SESSION_ID": "inherited-zcode",
           "CODEX_SESSION_ID": "", "TZ": "UTC"}
    pathlib_probe = subprocess.run(
        [sys.executable, "-c", f"from pathlib import Path; Path({str(fake_home / '.codex' / 'auth.json')!r}).read_text()"],
        capture_output=True, text=True, env=env,
    )
    assert pathlib_probe.returncode == 0, pathlib_probe.stderr
    assert marker.exists()
    marker.unlink()
    command = [sys.executable, str(Path(__file__).parent / "quota_governor.py"),
               "--runtime", "codex", "--refresh", "--state-path", str(state_path),
               "--log-dir", str(tmp_path / "logs"), "--updated-by", "cli-test"]
    refreshed = subprocess.run(command, capture_output=True, text=True, env=env)
    assert refreshed.returncode == 0, refreshed.stderr
    report = json.loads(refreshed.stdout)
    assert report["class"] == "abundant"
    assert report["runtime"] == "codex"
    assert report["source"] == CODEX_SOURCE
    assert report["computed_at_epoch"] == fixed_now
    assert report["observed_at_epoch"] == fixed_now
    assert report["reset_at_iso"] == datetime.fromtimestamp(
        1_900_003_600, timezone.utc).isoformat()
    assert [w["window_minutes"] for w in report["windows"]] == [300, 10080]

    consulted = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "quota_governor.py"),
         "--runtime", "codex", "--consult", "--state-path", str(state_path)],
        capture_output=True, text=True, env=env)
    assert consulted.returncode == 0, consulted.stderr
    consult_report = json.loads(consulted.stdout)
    assert consult_report["class"] == "abundant"
    assert consult_report["runtime"] == "codex"
    assert consult_report["source"] == CODEX_SOURCE
    assert consult_report["observed_at_epoch"] == report["observed_at_epoch"]
    assert consult_report["windows"] == report["windows"]

    wrong_runtime = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "quota_governor.py"),
         "--runtime", "zcode", "--consult", "--state-path", str(state_path)],
        capture_output=True, text=True, env=env)
    assert wrong_runtime.returncode == 0, wrong_runtime.stderr
    assert json.loads(wrong_runtime.stdout)["class"] == "unknown"
    assert not marker.exists(), "Codex credentials must not be read"


# --- consult CLI contract ----------------------------------------------------

def test_consult_cli_absent_state(tmp_path):
    out = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "quota_governor.py"),
         "--consult", "--state-path", str(tmp_path / "absent.json")],
        capture_output=True, text=True)
    assert out.returncode == 0
    report = json.loads(out.stdout)
    assert report["class"] == "unknown"
