#!/usr/bin/env python3
"""Hermetic suite for the daily-log miner (fixture log in a temp dir)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import quota_pressure_stats as stats  # noqa: E402

DAY = "2026-09-28"


def rec(ts, event="model.request.failed", status=None, reason=None, message=None,
        query_source=None, session="sess_1", turn="turn_1", extra=None):
    context = {}
    if status is not None:
        context["statusCode"] = status
    if reason is not None:
        context["reason"] = reason
    if message is not None:
        context["statusMessage"] = message
    if query_source is not None:
        context["querySource"] = query_source
    if extra:
        context.update(extra)
    return {"timestamp": ts, "event": event, "sessionId": session, "turnId": turn,
            "context": context}


def write_log(tmp_path, records, day=DAY):
    path = tmp_path / "zcode-{}.jsonl".format(day)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    return path


def mine(tmp_path, day=DAY):
    return stats.mine_day(day, tmp_path)


# --- episode dedup -----------------------------------------------------------

def test_same_trace_distinct_tokens_two_episodes(tmp_path):
    trace = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    records = []
    for token in ("tokA", "tokB"):
        records.append(rec("2026-09-28T10:00:00.000Z", status=429,
                           message="[1302][Rate limit reached for requests][{}]".format(token)))
    for r in records:
        r["traceId"] = trace
    write_log(tmp_path, records)
    summary = mine(tmp_path)
    assert summary["rate_limited_episodes"] == 2


def test_eleven_same_token_one_episode(tmp_path):
    records = [rec("2026-09-28T10:00:{:02d}.000Z".format(i), status=429,
                   message="[1302][Rate limit][tokX]") for i in range(11)]
    write_log(tmp_path, records)
    summary = mine(tmp_path)
    assert summary["rate_limited_episodes"] == 1
    assert isinstance(summary["episode_timestamps"][0], float)


def test_bracketless_fallback_key(tmp_path):
    records = [rec("2026-09-28T10:00:0{}.000Z".format(i), status=429,
                   message="Model request failed.")
               for i in range(5)]
    write_log(tmp_path, records)
    summary = mine(tmp_path)
    # The fallback key carries the second-precision timestamp, so five
    # records in five distinct seconds are five episodes.
    assert summary["rate_limited_episodes"] == 5


def test_reason_rate_limited_counts_without_status(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", reason="rate_limited",
                             message="[1302][Rate limit][tokR]")])
    assert mine(tmp_path)["rate_limited_episodes"] == 1


def test_source_bucketing(tmp_path):
    records = [
        rec("2026-09-28T10:00:00.000Z", status=429, message="[1302][R][t1]", query_source="main_turn"),
        rec("2026-09-28T10:00:01.000Z", status=429, message="[1302][R][t2]", query_source="subagent"),
        rec("2026-09-28T10:00:02.000Z", status=429, message="[1302][R][t3]", query_source="weird"),
        rec("2026-09-28T10:00:03.000Z", status=429, message="[1302][R][t4]"),
    ]
    write_log(tmp_path, records)
    summary = mine(tmp_path)
    assert summary["episodes_by_source"] == {"main_turn": 1, "subagent": 1, "other": 2}


# --- exhaustion cells (measured shapes) ---------------------------------------

def test_measured_1308_bracket_counts(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", status=429, reason="rate_limited",
                             message="[1308][Usage limit reached for 5 hour. Your limit will "
                                     "reset at 18:00][tok1308]")])
    summary = mine(tmp_path)
    assert summary["exhaustion_event_count"] == 1
    assert summary["rate_limited_episodes"] == 1  # counts in both families
    assert summary["last_exhaustion_ts"] is not None


def test_tokens_limit_citation_counts(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", status=500,
                             message="Quota window TOKENS_LIMIT exceeded")])
    assert mine(tmp_path)["exhaustion_event_count"] == 1


def test_time_limit_citation_counts(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", status=500,
                             message="Weekly TIME_LIMIT reached")])
    assert mine(tmp_path)["exhaustion_event_count"] == 1


def test_non_1308_bracket_prefix_not_exhaustion(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", status=429,
                             message="[1302][Rate limit reached for requests][tokZ]")])
    summary = mine(tmp_path)
    assert summary["exhaustion_event_count"] == 0
    assert summary["rate_limited_episodes"] == 1  # 1302 stays in the episode family


def test_bare_1308_elsewhere_never_counts(tmp_path):
    records = [
        rec("2026-09-28T10:00:00.000Z", status=500,
            message="field value 1308 drifted", extra={"errorCode": 1308}),
        rec("2026-09-28T10:00:01.000Z", event="model.sdk.stream.completed", status=200,
            message="ok 1308"),
    ]
    write_log(tmp_path, records)
    assert mine(tmp_path)["exhaustion_event_count"] == 0


def test_non_failure_event_ignored(tmp_path):
    write_log(tmp_path, [rec("2026-09-28T10:00:00.000Z", event="model.request.started",
                             status=429, message="[1308][x][y]")])
    summary = mine(tmp_path)
    assert summary["rate_limited_episodes"] == 0
    assert summary["exhaustion_event_count"] == 0


# --- missing day file, merge-state -------------------------------------------

def test_missing_day_file_mines_to_zeros(tmp_path):
    summary = mine(tmp_path)
    assert summary["rate_limited_episodes"] == 0
    assert summary["exhaustion_event_count"] == 0
    assert summary["last_exhaustion_ts"] is None
    assert summary["day"] == DAY


def test_merge_state_prunes_to_seven_days_and_atomic(tmp_path):
    import quota_governor as g
    state_path = tmp_path / "state.json"
    g.write_state(state_path, g.new_state(1_800_000_000.0))
    # Pre-seed 8 old days.
    state = g.read_state(state_path)
    for i in range(8):
        state["metrics"]["by_day"]["2026-09-{:02d}".format(i + 1)] = {"day": "seed-{}".format(i)}
    g.write_state(state_path, state)
    summary = mine(tmp_path)
    stats.merge_into_state(summary, state_path)
    merged = g.read_state(state_path)
    assert len(merged["metrics"]["by_day"]) == 7
    assert DAY in merged["metrics"]["by_day"]


def test_timestamp_cap_500(tmp_path):
    records = [rec("2026-09-28T10:00:00.000Z", status=429,
                   message="[1302][R][tok{}]" .format(i)) for i in range(600)]
    write_log(tmp_path, records)
    assert len(mine(tmp_path)["episode_timestamps"]) == 500


def test_cli_missing_log_dir_zeros(tmp_path):
    out = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "quota_pressure_stats.py"),
         "--day", DAY, "--log-dir", str(tmp_path / "absent")],
        capture_output=True, text=True)
    assert out.returncode == 0
    assert json.loads(out.stdout)["rate_limited_episodes"] == 0
