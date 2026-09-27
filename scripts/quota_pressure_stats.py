#!/usr/bin/env python3
"""Mine rate-limit episodes and exhaustion events from the daily CLI log.

Account-level quota governor feed (2026-09-28 account-quota-governor plan).
Episodes are provider rate-limit incidents deduplicated by the incident-grade
bracket-tail token (the third bracket of ``context.statusMessage``); a trace
id is never the dedup key (a trace context spans sessions and incidents).
Exhaustion events are window citations (``TOKENS_LIMIT`` / ``TIME_LIMIT``) or
surfaced provider code 1308 in the miner's only reachable structured carrier,
the bracket prefix of ``context.statusMessage`` on the two failure event
types. A bare ``1308`` substring elsewhere in a record payload never counts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

EPISODE_EVENTS = frozenset({"model.request.failed", "model.network.failed"})
RATE_LIMIT_STATUS = 429
RATE_LIMIT_REASON = "rate_limited"
EXHAUSTION_CITATIONS = ("TOKENS_LIMIT", "TIME_LIMIT")
EXHAUSTION_PROVIDER_CODE = "1308"
BRACKET_RE = re.compile(r"\[([^\[\]]*)\]")
EPISODE_TIMESTAMP_CAP = 500
METRICS_DAY_CAP = 7
SOURCE_BUCKETS = ("main_turn", "subagent", "other")


def _brackets(message):
    """All bracket-group contents of a statusMessage, in order."""
    if not isinstance(message, str):
        return []
    return BRACKET_RE.findall(message)


def _episode_key(record, context):
    """Incident-grade dedup key: third bracket token, else a session fallback."""
    brackets = _brackets(context.get("statusMessage"))
    if len(brackets) >= 3 and brackets[2]:
        return "token:{}".format(brackets[2])
    session = record.get("sessionId") or context.get("sessionId") or "unknown-session"
    turn = record.get("turnId") or context.get("turnId") or "unknown-turn"
    timestamp = record.get("timestamp") or ""
    return "fallback:{}:{}:{}".format(session, turn, timestamp.split(".")[0])


def _source_bucket(context):
    source = context.get("querySource")
    if source in ("main_turn", "subagent"):
        return source
    return "other"


def _parse_ts(record):
    """Epoch seconds from an ISO record timestamp; 0.0 when unparseable."""
    raw = record.get("timestamp")
    if not isinstance(raw, str) or not raw:
        return 0.0
    try:
        from datetime import datetime, timezone
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _is_rate_limited(context):
    return (context.get("statusCode") == RATE_LIMIT_STATUS
            or context.get("reason") == RATE_LIMIT_REASON)


def _is_exhaustion(record, context):
    """Exhaustion evidence on a failure record, per the plan's carrier rules.

    A window citation (TOKENS_LIMIT / TIME_LIMIT) anywhere in the record
    payload counts; a bare 1308 counts only in its sanctioned carrier, the
    statusMessage bracket prefix.
    """
    brackets = _brackets(context.get("statusMessage"))
    if brackets and brackets[0] == EXHAUSTION_PROVIDER_CODE:
        return True
    if any(c in str(record.get("message", "")) for c in EXHAUSTION_CITATIONS):
        return True
    if any(c in str(context.get("statusMessage", "")) for c in EXHAUSTION_CITATIONS):
        return True
    return False


def mine_day_detailed(day, log_dir):
    """Return (summary, meta) where meta carries records_parsed for usability."""
    path = Path(log_dir) / "zcode-{}.jsonl".format(day)
    episodes = {}
    episode_order = []
    exhaustion_count = 0
    last_exhaustion_ts = None
    records_parsed = 0
    if not path.is_file():
        summary = _empty_summary(day)
        return summary, {"records_parsed": 0, "file_readable": False}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict):
                continue
            records_parsed += 1
            event = record.get("event")
            if event not in EPISODE_EVENTS:
                continue
            context = record.get("context")
            if not isinstance(context, dict):
                continue
            ts = _parse_ts(record)
            if _is_rate_limited(context):
                key = _episode_key(record, context)
                if key not in episodes:
                    episodes[key] = {
                        "first_ts_epoch": ts,
                        "source": _source_bucket(context),
                    }
                    episode_order.append(key)
            if _is_exhaustion(record, context):
                exhaustion_count += 1
                if last_exhaustion_ts is None or ts > last_exhaustion_ts:
                    last_exhaustion_ts = ts
    by_source = {bucket: 0 for bucket in SOURCE_BUCKETS}
    for key in episode_order:
        by_source[episodes[key]["source"]] += 1
    timestamps = sorted(episodes[key]["first_ts_epoch"] for key in episode_order)
    timestamps = [ts for ts in timestamps if ts]
    summary = {
        "day": day,
        "rate_limited_episodes": len(episode_order),
        "episodes_by_source": by_source,
        "episode_timestamps": timestamps[-EPISODE_TIMESTAMP_CAP:],
        "exhaustion_event_count": exhaustion_count,
        "last_exhaustion_ts": last_exhaustion_ts,
    }
    return summary, {"records_parsed": records_parsed, "file_readable": True}


def mine_day(day, log_dir):
    """Pinned output shape; a missing day file mines to zeros, never errors."""
    summary, _meta = mine_day_detailed(day, log_dir)
    return summary


def _empty_summary(day):
    return {
        "day": day,
        "rate_limited_episodes": 0,
        "episodes_by_source": {bucket: 0 for bucket in SOURCE_BUCKETS},
        "episode_timestamps": [],
        "exhaustion_event_count": 0,
        "last_exhaustion_ts": None,
    }


def _local_day(epoch=None):
    from datetime import datetime
    return datetime.fromtimestamp(epoch if epoch is not None else _now()).strftime("%Y-%m-%d")


def _now():
    import time
    return time.time()


def _shift_day(day, days):
    from datetime import datetime, timedelta
    parsed = datetime.strptime(day, "%Y-%m-%d")
    return (parsed + timedelta(days=days)).strftime("%Y-%m-%d")


def merge_into_state(summary, state_path):
    """Write the summary into the shared state's metrics.by_day under the
    governor lock with 7-day pruning; atomic replace."""
    import quota_governor
    with quota_governor.governor_lock(state_path):
        state = quota_governor.read_state(state_path)
        if state is None:
            state = quota_governor.new_state()
        metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
        by_day = metrics.get("by_day") if isinstance(metrics.get("by_day"), dict) else {}
        by_day[summary["day"]] = summary
        metrics["by_day"] = dict(sorted(by_day.items())[-METRICS_DAY_CAP:])
        state["metrics"] = metrics
        quota_governor._write_state_locked(state_path, state)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default=None, help="YYYY-MM-DD (default: today, host-local)")
    parser.add_argument("--log-dir", default=os.path.expanduser("~/.zcode/cli/log"))
    parser.add_argument("--merge-state", default=None,
                        help="also merge the summary into the shared governor state")
    args = parser.parse_args(argv)
    day = args.day or _local_day()
    summary, _meta = mine_day_detailed(day, args.log_dir)
    if args.merge_state:
        merge_into_state(summary, os.path.expanduser(args.merge_state))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
