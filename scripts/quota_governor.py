#!/usr/bin/env python3
"""Account-level quota governor: shared pressure state, four-class evaluator,
per-lane dispatch verdicts (2026-09-28 account-quota-governor plan).

The class-to-dispatch policy table lives only here; skill prose names the
classes qualitatively and obeys the verdicts, so the two homes cannot drift.
Class vocabulary: abundant, tightening, constrained, exhausted, plus unknown
(unusable inputs; fail-open, never read as abundant).
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

TIGHTENING_PERCENT = 60.0
CONSTRAINED_PERCENT = 80.0
EXHAUSTED_PERCENT = 95.0
RATE_EPISODES_CONSTRAINED_PER_HOUR = 20
RESERVE_PERCENT = 15.0
TIGHTENING_EXECUTION_FLOOR_PERCENT = RESERVE_PERCENT + 10
CONSTRAINED_AUTHORING_FLOOR_PERCENT = 30.0
LOCK_TIMEOUT_SECONDS = 2.0
STATE_STALE_SECONDS = 1800
STATE_VERSION = 1
CADENCE_SECONDS = 5 * 3600
WINDOW_SAMPLES_CAP = 24
METRICS_DAY_CAP = 7
DEFAULT_STATE_PATH = "~/.ai-playbook/runtime/quota-governor-state.json"
DEFAULT_LOG_DIR = "~/.zcode/cli/log"
TRAILING_HOUR_SECONDS = 3600


# ---------------------------------------------------------------------------
# Pure core

def _primary_limit(probe_report):
    """The primary window limit dict, or None when unusable/absent."""
    if not isinstance(probe_report, dict):
        return None
    limits = probe_report.get("limits")
    if not isinstance(limits, list):
        return None
    for limit in limits:
        if isinstance(limit, dict) and limit.get("kind") == "primary":
            return limit
    return None


def _probe_usable(probe_report):
    return isinstance(probe_report, dict) and probe_report.get("status") == "ok"


def _mining_usable(mining):
    """Mining is usable only when a readable day file yielded >=1 parsed record."""
    if not isinstance(mining, dict):
        return False
    return bool(mining.get("usable"))


def evaluate_pressure(probe_report, mining, now=None):
    """The four-class evaluator over the probe report plus mined evidence.

    Percent arms and the pause arm classify from the primary window only; a
    secondary-binding report contributes context but never a class by itself.
    ``unknown`` when the probe report is unusable and the mining is unusable;
    absence of data never reads as abundant.
    """
    if now is None:
        now = time.time()
    mining_usable = _mining_usable(mining)
    probe_usable = _probe_usable(probe_report)
    primary = _primary_limit(probe_report) if probe_usable else None
    used = primary.get("used_percent") if primary else None
    if not isinstance(used, (int, float)) or not (0.0 <= float(used) <= 100.0):
        used = None
    reasons = []

    # Exhaustion arm (evidence-anchored; never a previous window's line).
    exhaustion_ts = None
    if mining_usable and isinstance(mining.get("exhaustion_ts_list"), list):
        stamps = [ts for ts in mining["exhaustion_ts_list"] if isinstance(ts, (int, float))]
        if stamps:
            exhaustion_ts = max(stamps)
    if exhaustion_ts is not None:
        if primary and isinstance(primary.get("reset_at_epoch"), (int, float)):
            window_start = primary["reset_at_epoch"] - CADENCE_SECONDS
            if exhaustion_ts >= window_start:
                reasons.append("exhaustion event inside the live primary window")
                return "exhausted", reasons
        elif exhaustion_ts >= now - CADENCE_SECONDS:
            # Probe-less fallback: trailing-cadence lookback.
            reasons.append("exhaustion event within the trailing cadence (no probe)")
            return "exhausted", reasons

    if used is not None:
        if used >= EXHAUSTED_PERCENT:
            reasons.append("primary used_percent {} at or above {}".format(used, EXHAUSTED_PERCENT))
            return "exhausted", reasons
        if used >= CONSTRAINED_PERCENT:
            reasons.append("primary used_percent {} at or above {}".format(used, CONSTRAINED_PERCENT))
            return "constrained", reasons
        if used >= TIGHTENING_PERCENT:
            reasons.append("primary used_percent {} at or above {}".format(used, TIGHTENING_PERCENT))
            return "tightening", reasons
    elif probe_usable and probe_report.get("pause_decision") == "pause" \
            and probe_report.get("binding") == "primary":
        reasons.append("probe pause arm engaged on the primary window")
        return "exhausted", reasons

    if mining_usable and isinstance(mining.get("episode_timestamps"), list):
        stamps = [ts for ts in mining["episode_timestamps"] if isinstance(ts, (int, float))]
        trailing = [ts for ts in stamps if ts >= now - TRAILING_HOUR_SECONDS]
        if len(trailing) >= RATE_EPISODES_CONSTRAINED_PER_HOUR:
            reasons.append(
                "{} rate-limited episodes in the trailing hour (>= {})".format(
                    len(trailing), RATE_EPISODES_CONSTRAINED_PER_HOUR))
            return "constrained", reasons

    if not probe_usable and not mining_usable:
        return "unknown", ["probe report unusable and mining unusable"]

    if used is None:
        reasons.append("no usable primary window reading; class from available evidence")
    reasons.append("all classification arms below their thresholds")
    return "abundant", reasons


def policy_verdicts(pressure, now=None):
    """Per-lane dispatch verdicts from the stored pressure. The single home
    of the class-to-dispatch policy; the skill obeys, never restates."""
    if now is None:
        now = time.time()
    klass = pressure.get("class")
    used = pressure.get("inputs", {}).get("primary_used_percent")
    headroom = (100.0 - used) if isinstance(used, (int, float)) else None

    def allow(reason):
        return {"verdict": "allow", "reason": reason}

    def defer(reason):
        return {"verdict": "defer", "reason": reason}

    def headroom_cell(floor, lane):
        # Fail-open over a missing reading: allow with the absent-reading named.
        if headroom is None:
            return allow("headroom-gated cell allows on the absent primary reading")
        if headroom >= floor:
            return allow("headroom {:.0f} at or above floor {:.0f}".format(headroom, floor))
        return defer("headroom {:.0f} below floor {:.0f}".format(headroom, floor))

    if klass == "abundant":
        return {"execution": allow("pressure abundant"), "authoring": allow("pressure abundant")}
    if klass == "tightening":
        return {"execution": headroom_cell(TIGHTENING_EXECUTION_FLOOR_PERCENT, "execution"),
                "authoring": allow("pressure tightening; authoring allowed")}
    if klass == "constrained":
        return {"execution": defer("pressure constrained; execution deferred"),
                "authoring": headroom_cell(CONSTRAINED_AUTHORING_FLOOR_PERCENT, "authoring")}
    if klass == "exhausted":
        reset_iso = None
        reset_epoch = pressure.get("reset_at_epoch")
        if isinstance(reset_epoch, (int, float)):
            reset_iso = datetime.fromtimestamp(reset_epoch).astimezone().isoformat()
        reason = "pressure exhausted; window resets at {}".format(reset_iso or "unknown time")
        return {"execution": defer(reason), "authoring": defer(reason)}
    return {"execution": allow("pressure unknown; fail-open defaults"),
            "authoring": allow("pressure unknown; fail-open defaults")}


# ---------------------------------------------------------------------------
# Shared state

def new_state(now=None):
    if now is None:
        now = time.time()
    return {
        "version": STATE_VERSION,
        "updated_at_epoch": now,
        "updated_by": "unknown",
        "pressure": {
            "class": "unknown",
            "computed_at_epoch": now,
            "inputs": {
                "primary_used_percent": None,
                "primary_minutes_remaining": None,
                "rate_limited_episodes_trailing_hour": 0,
                "exhaustion_event_count": 0,
            },
        },
        "reset_at_epoch": None,
        "reset_at_iso": None,
        "reserve_percent": RESERVE_PERCENT,
        "window_samples": [],
        "metrics": {"by_day": {}},
    }


def lock_path_for(state_path):
    state_path = os.path.expanduser(str(state_path))
    return str(Path(state_path).parent / "quota-governor.lock")


@contextmanager
def governor_lock(state_path, timeout=LOCK_TIMEOUT_SECONDS):
    """fcntl exclusive lock on <state-dir>/quota-governor.lock, bounded acquire.
    Yields False on timeout (the caller skips the write, fail-open)."""
    path = lock_path_for(state_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
        yield acquired
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def read_state(state_path):
    """Parsed state dict, or None when absent/corrupt (corrupt reads unknown,
    never raises; version skew is reported by the caller via the raw bytes)."""
    path = os.path.expanduser(str(state_path))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError:
        return None
    try:
        state = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(state, dict) or "version" not in state:
        return None
    return state


def _write_state_locked(state_path, state):
    """Write through a lock the CALLER already holds (pid-unique tmp, atomic
    replace, version-refusal). Never acquires the lock itself."""
    path = os.path.expanduser(str(state_path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = read_state(path)
    if existing and isinstance(existing.get("version"), int) \
            and existing["version"] > STATE_VERSION:
        return False
    tmp = "{}.{}.tmp".format(path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return True


def write_state(state_path, state):
    """Pid-unique tmp plus atomic replace under the governor lock.
    Refuses when the stored version is greater than this script's."""
    path = os.path.expanduser(str(state_path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with governor_lock(state_path) as acquired:
        if not acquired:
            return False
        return _write_state_locked(path, state)


def _stale(state, now):
    updated = state.get("updated_at_epoch")
    if not isinstance(updated, (int, float)):
        return True
    return now - updated > STATE_STALE_SECONDS


def consult(state_path, now=None):
    """Read-only consult; exit 0 on every non-usage-error path. The verdict
    is parsed from the returned report, never from an exit code."""
    if now is None:
        now = time.time()
    path = os.path.expanduser(str(state_path))
    state = read_state(path)
    if state is None:
        return _unknown_report("no usable state file (absent or corrupt)")
    version = state.get("version")
    if isinstance(version, int) and version > STATE_VERSION:
        return _unknown_report(
            "stored state version {} greater than script version {}".format(version, STATE_VERSION))
    if _stale(state, now):
        return _unknown_report("state older than {} seconds".format(STATE_STALE_SECONDS))
    pressure = state.get("pressure") if isinstance(state.get("pressure"), dict) else {}
    report = {
        "class": pressure.get("class", "unknown"),
        "computed_at_epoch": pressure.get("computed_at_epoch"),
        "dispatch": policy_verdicts(pressure, now),
        "reset_at_epoch": state.get("reset_at_epoch"),
        "reset_at_iso": state.get("reset_at_iso"),
        "reserve_percent": state.get("reserve_percent", RESERVE_PERCENT),
        "state_path": path,
        "status": "ok",
    }
    return report


def _unknown_report(reason):
    return {
        "class": "unknown",
        "reason": reason,
        "dispatch": policy_verdicts({"class": "unknown"}),
        "reset_at_epoch": None,
        "reset_at_iso": None,
        "reserve_percent": RESERVE_PERCENT,
        "status": "unknown",
    }


# ---------------------------------------------------------------------------
# Refresh

def _mine_merge(log_dir, now):
    """Mine the previous and current local days; union evidence, usable when
    either day file yielded at least one parsed record."""
    import quota_pressure_stats
    today = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
    yesterday = quota_pressure_stats._shift_day(today, -1)
    summaries = []
    usable = False
    episode_timestamps = []
    exhaustion_ts_list = []
    for day in (yesterday, today):
        summary, meta = quota_pressure_stats.mine_day_detailed(day, log_dir)
        summaries.append(summary)
        if meta.get("records_parsed"):
            usable = True
        episode_timestamps.extend(summary["episode_timestamps"])
        if summary["last_exhaustion_ts"] is not None:
            exhaustion_ts_list.append(summary["last_exhaustion_ts"])
    mining = {
        "usable": usable,
        "episode_timestamps": episode_timestamps,
        "exhaustion_ts_list": exhaustion_ts_list,
        "days": {s["day"]: s for s in summaries},
    }
    return mining


def refresh(state_path, log_dir=None, updated_by=None, now=None,
            probe_report=None):
    """Probe, mine, evaluate, write the shared state, print the consult report.
    The probe transport and the log mining run outside the lock; only the
    read-merge-stage-replace window holds it."""
    if now is None:
        now = time.time()
    import quota_window_probe
    import quota_pressure_stats
    unusable = None
    if probe_report is None:
        try:
            runtime = quota_window_probe.detect_runtime()
        except Exception as exc:  # transport/detection failures fail open
            runtime = None
            unusable = "runtime detection failed: {}".format(exc)
        if runtime in (None, "none", "unknown"):
            unusable = unusable or "runtime detection degraded ({}); refresh unknown".format(runtime)
            probe_report = None
        else:
            try:
                probe_report = quota_window_probe.run_probe(runtime)
            except Exception as exc:
                probe_report = None
                unusable = "probe transport failed: {}".format(exc)
    log_dir = os.path.expanduser(log_dir or DEFAULT_LOG_DIR)
    mining = _mine_merge(log_dir, now)
    klass, reasons = evaluate_pressure(probe_report, mining, now)

    primary = _primary_limit(probe_report) if _probe_usable(probe_report) else None
    used = primary.get("used_percent") if primary else None
    minutes = primary.get("minutes_remaining") if primary else None
    reset_epoch = primary.get("reset_at_epoch") if primary else None
    if not isinstance(used, (int, float)):
        used = None
    if not isinstance(minutes, (int, float)):
        minutes = None
    if not isinstance(reset_epoch, (int, float)):
        reset_epoch = None
    trailing_hour = 0
    if mining["episode_timestamps"]:
        trailing_hour = sum(1 for ts in mining["episode_timestamps"]
                            if isinstance(ts, (int, float)) and ts >= now - TRAILING_HOUR_SECONDS)
    exhaustion_count = sum(
        s["exhaustion_event_count"] for s in mining["days"].values()
        if isinstance(s, dict) and isinstance(s.get("exhaustion_event_count"), int))

    # Read-merge-stage-replace under the lock.
    with governor_lock(state_path) as acquired:
        if acquired:
            state = read_state(state_path)
            if state is None or not isinstance(state, dict) or "version" not in state:
                state = new_state(now)
            if isinstance(state.get("version"), int) and state["version"] > STATE_VERSION:
                stored_newer = True
            else:
                stored_newer = False
            samples = state.get("window_samples")
            if not isinstance(samples, list):
                samples = []
            if used is not None:
                samples.append({"ts_epoch": now, "used_percent": used})
            samples = samples[-WINDOW_SAMPLES_CAP:]
            metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
            by_day = metrics.get("by_day") if isinstance(metrics.get("by_day"), dict) else {}
            for day, summary in mining["days"].items():
                by_day[day] = summary
            by_day = dict(sorted(by_day.items())[-METRICS_DAY_CAP:])
            if stored_newer:
                wrote = False  # fail closed: never clobber a newer schema
            else:
                state.update({
                    "version": STATE_VERSION,
                    "updated_at_epoch": now,
                    "updated_by": updated_by or _default_updated_by(),
                    "pressure": {
                        "class": klass,
                        "computed_at_epoch": now,
                        "reasons": reasons,
                        "inputs": {
                            "primary_used_percent": used,
                            "primary_minutes_remaining": minutes,
                            "rate_limited_episodes_trailing_hour": trailing_hour,
                            "exhaustion_event_count": exhaustion_count,
                        },
                    },
                    "reset_at_epoch": reset_epoch,
                    "reset_at_iso": (datetime.fromtimestamp(reset_epoch).astimezone().isoformat()
                                     if reset_epoch is not None else None),
                    "reserve_percent": RESERVE_PERCENT,
                    "window_samples": samples,
                    "metrics": {"by_day": by_day},
                })
                wrote = _write_state_locked(state_path, state)
        else:
            wrote = False  # lock timeout: skip the write without blocking

    report = consult(state_path, now)
    report["refresh_wrote_state"] = wrote
    if klass == "unknown" and unusable:
        report["reason"] = unusable
    return report


def _default_updated_by():
    runtime_id = None
    for key in ("ZCODE_SESSION_ID", "CODEX_SESSION_ID", "SESSION_ID"):
        value = os.environ.get(key)
        if value:
            runtime_id = value
            break
    return "{}:{}".format(os.path.basename(os.getcwd()), runtime_id or "unknown")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh", action="store_true")
    group.add_argument("--consult", action="store_true")
    parser.add_argument("--state-path", default=DEFAULT_STATE_PATH)
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    parser.add_argument("--updated-by", default=None)
    args = parser.parse_args(argv)
    state_path = os.path.expanduser(args.state_path)
    if args.refresh:
        report = refresh(state_path, log_dir=args.log_dir, updated_by=args.updated_by)
    else:
        report = consult(state_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
