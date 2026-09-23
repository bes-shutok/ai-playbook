#!/usr/bin/env python3
"""Friction-audit quantitative pass (scheduler maintenance audit lane).

Deterministic, watermark-driven script pass of the audit lane: it recomputes
the mechanical part of the friction audit so the model pass reads only the
digest plus targeted samples. The data map (store locator, table shapes, log
location and event schema, noise filter, provider code meanings) is owned by
the maintenance overlay's "Audit recipe" section; this script implements it.

Computed per run (over the delta rows only, see watermarks below):
  - per-tool error rates and error-message classes (sqlite `tool_usage`);
  - per-day log event histograms with the persistence-noise filter applied
    (daily `zcode-YYYY-MM-DD.jsonl` files under the logs dir, one JSON object
    per line);
  - provider 429 code counts sourced from `tool_usage.error_code` (per the
    audit recipe; 1302 per-request rate limit, 1308 quota exhaustion);
  - correction-heuristic candidates from sqlite `session_input`.

Artifacts written under --out-dir:
  - digest.md      human-readable digest (markdown);
  - counts.json    machine-readable counts with the documented fields:
                   completed_at, since, cadence_days, next_due, rows_processed,
                   watermarks, tools, daily_events, provider_429_codes,
                   correction_candidates, warnings;
  - state.json     per-source watermarks plus run bookkeeping:
                   {
                     "version": 1,
                     "watermarks": {
                       "tool_usage":    {"max_ts": "...", "rows": 12},
                       "session_input": {"max_ts": "...", "rows": 3},
                       "logs":          {"last_file": "zcode-2026-09-22.jsonl",
                                          "rows": 40}
                     },
                     "last_run_completed_at": "...",
                     "next_due": "..."
                   }
  Watermark semantics: max timestamp / last fully mined daily log mark what
  has been fully processed; `rows` is the cumulative count of rows aggregated
  so far. The log watermark advances only through the last COMPLETE UTC day,
  so the current day's partially grown file is re-mined in full (and its later
  appended tail aggregated) on the next run. Watermarks advance only after the
  sources are fully processed and the artifacts are written (state.json is
  written last, atomically). A missing state file means cold start: the full
  corpus is scanned (bounded only by --since). next_due is written at each
  processing completion as the completion time plus --cadence-days (default 7);
  the scheduler turn's survey reads it.

Timestamps are epoch milliseconds (the host sqlite integer columns) or
ISO-8601 strings (fixtures); comparisons parse both as UTC datetimes.

Expected db schema (the runtime overlay's audit recipe owns the real locator
literals and table shapes; the script reads only these columns and opens the
store read-only, never writing it):
  tool_usage(started_at INTEGER epoch-ms, tool_name TEXT, status TEXT,
             error_code INTEGER|TEXT, error_message TEXT, ...)
  session_input(time_created INTEGER epoch-ms, session_id TEXT,
                payload TEXT, ...)

Log line schema (per the audit recipe): one JSON object per line carrying
`timestamp`, `level`, `event`, `module`, and `message`; the histogram keys on
`event`. Unparseable lines count under the event class "unparseable" so no
line is silently dropped from the histogram.

CLI (all optional; tilde-form and repo-relative defaults, never commit
resolved absolute paths):
  --db           sqlite db path            (default ~/.zcode/cli/db/db.sqlite)
  --logs-dir     daily zcode-*.jsonl dir   (default ~/.zcode/cli/log)
  --out-dir      audit artifacts dir       (default .ai-playbook/friction-audit,
                                            repo/working-dir relative, the audit
                                            recipe's friction_audit_dir fallback)
  --since        ISO lower bound for rows  (default: empty, no lower bound)
  --cadence-days days added to completion  (default 7) for next_due
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATE_VERSION = 1

# Persistence-noise filter: deterministic message patterns (event-name
# prefixes) excluded from the per-day histograms before any counting. These
# are compaction/persistence row classes: high-volume bookkeeping events that
# drown the operative signal (~28 percent of lines in the 2026-09-19 audit).
NOISE_PATTERNS = (
    "session.event.persistence.",
    "session.event.compaction.",
)

# tool_usage.error_code values that are 429-family rate-limit rejections (per
# the audit recipe: 1302 per-request rate limit, 1308 5-hour quota
# exhaustion); the digest counts occurrences per code, never conflated. The
# host column is TEXT affinity, so numeric strings are accepted too.
PROVIDER_429_CODES = (1302, 1308)

# Correction-heuristic keywords (case-insensitive substring match on
# session_input payload): prompts that read as corrections of a previous turn.
CORRECTION_KEYWORDS = (
    "actually",
    "instead",
    "wrong",
    "revert",
    "undo",
    "mistake",
    "correction",
)

UNPARSEABLE_EVENT_CLASS = "unparseable"
SNIPPET_LIMIT = 120
LOG_PREFIX = "zcode-"
LOG_SUFFIX = ".jsonl"
LOG_DAY_START = len(LOG_PREFIX)
LOG_DAY_END = LOG_DAY_START + 10  # YYYY-MM-DD


def _utcnow() -> datetime:
    """Completion clock; injectable in tests."""
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(value) -> datetime:
    """Parse a timestamp as UTC: epoch milliseconds (the host sqlite integer
    columns; int, float, or digit string) or an ISO-8601 string."""
    if isinstance(value, bool):
        raise ValueError(f"not a timestamp: {value!r}")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if text.isdigit():
        return datetime.fromtimestamp(int(text) / 1000.0, tz=timezone.utc)
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_noise(event: str) -> bool:
    return any(event.startswith(pattern) for pattern in NOISE_PATTERNS)


def _message_class(message: str) -> str:
    """Normalize an error message into a stable class: digits collapse to <n>,
    whitespace collapses, case folds, so variable ids do not fragment classes."""
    collapsed = " ".join(str(message).split()).lower()
    out = []
    digits = ""
    for ch in collapsed:
        if ch.isdigit():
            digits += ch
        else:
            if digits:
                out.append("<n>")
                digits = ""
            out.append(ch)
    if digits:
        out.append("<n>")
    return "".join(out)


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    """Read-only store connection; the audit never writes the store (the
    audit recipe pins the store locator read-only)."""
    return sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)


def _watermarks_well_typed(watermarks) -> bool:
    """True when every watermark entry is a dict whose fields carry the
    documented types (rows: int; max_ts/last_file: str or null); anything
    else is a wrong-typed state and degrades to a warned cold start."""
    for value in watermarks.values():
        if not isinstance(value, dict):
            return False
        for key, item in value.items():
            if key == "rows":
                if isinstance(item, bool) or not isinstance(item, int):
                    return False
            elif key in ("max_ts", "last_file"):
                if item is not None and not isinstance(item, str):
                    return False
        max_ts = value.get("max_ts")
        if isinstance(max_ts, str) and max_ts:
            try:
                _parse_ts(max_ts)
            except ValueError:
                return False
    return True


def _load_state(state_path: Path) -> dict:
    """Load prior state; a missing, empty, malformed, or wrong-typed state
    file means a warned cold start (empty watermarks), per the audit-lane
    state semantics."""
    if not state_path.exists():
        return {}
    raw = state_path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        state = json.loads(raw)
    except json.JSONDecodeError:
        print(f"warning: malformed {state_path.name}; treating as cold start", file=sys.stderr)
        return {}
    watermarks = state.get("watermarks") if isinstance(state, dict) else None
    if not isinstance(watermarks, dict) or not _watermarks_well_typed(watermarks):
        print(
            f"warning: {state_path.name} has wrong-typed fields; treating as cold start",
            file=sys.stderr,
        )
        return {}
    return state


def _watermark(state: dict, source: str) -> dict:
    value = state.get("watermarks", {}).get(source, {})
    return value if isinstance(value, dict) else {}


def _filter_rows(rows, ts_index: int, since_dt, floor_dt, warnings: list):
    """Keep rows whose timestamp is strictly after the watermark floor and at
    or after --since. Returns [(row, dt)] sorted by timestamp. Rows with an
    unparseable timestamp are skipped with a warning and never advance the
    watermark."""
    kept = []
    skipped = 0
    for row in rows:
        raw_ts = row[ts_index]
        if raw_ts is None or str(raw_ts).strip() == "":
            skipped += 1
            continue
        try:
            dt = _parse_ts(raw_ts)
        except ValueError:
            skipped += 1
            continue
        if floor_dt is not None and not dt > floor_dt:
            continue
        if since_dt is not None and dt < since_dt:
            continue
        kept.append((row, dt))
    kept.sort(key=lambda item: item[1])
    if skipped:
        warnings.append(f"{skipped} row(s) with missing or unparseable timestamps skipped")
    return kept


def _advance_max_ts(prev_max: str, kept, ts_index: int) -> str:
    """New max-timestamp watermark: the raw timestamp of the newest processed
    row (rows are sorted by parsed timestamp), or the previous watermark when
    the delta is empty."""
    if kept:
        return str(kept[-1][0][ts_index])
    return prev_max or ""


def _scan_tool_usage(db_path: Path, since_dt, floor_dt, warnings: list):
    """Delta rows from tool_usage: (tool_name, status, error_code,
    error_message, started_at); started_at is epoch milliseconds."""
    if not db_path.exists():
        warnings.append(f"db not found: {db_path.name}; tool_usage contributes no rows")
        return []
    con = _connect_ro(db_path)
    try:
        rows = con.execute(
            "SELECT tool_name, status, error_code, error_message, started_at FROM tool_usage"
        ).fetchall()
    finally:
        con.close()
    return _filter_rows(rows, 4, since_dt, floor_dt, warnings)


def _scan_session_input(db_path: Path, since_dt, floor_dt, warnings: list):
    """Delta rows from session_input: (time_created, session_id, payload);
    time_created is epoch milliseconds."""
    if not db_path.exists():
        warnings.append(f"db not found: {db_path.name}; session_input contributes no rows")
        return []
    con = _connect_ro(db_path)
    try:
        rows = con.execute(
            "SELECT time_created, session_id, payload FROM session_input"
        ).fetchall()
    finally:
        con.close()
    return _filter_rows(rows, 0, since_dt, floor_dt, warnings)


def _daily_log_files(logs_dir: Path, warnings: list):
    """Daily logs, sorted: files named zcode-YYYY-MM-DD.jsonl under the logs
    dir; the embedded YYYY-MM-DD span is the day bucket."""
    if not logs_dir.exists():
        warnings.append(f"logs dir not found: {logs_dir.name}; log histogram empty")
        return []
    files = []
    for path in sorted(logs_dir.iterdir()):
        if not path.is_file():
            continue
        if not (path.name.startswith(LOG_PREFIX) and path.name.endswith(LOG_SUFFIX)):
            continue
        if len(path.name) != LOG_DAY_END + len(LOG_SUFFIX):
            continue
        day = path.name[LOG_DAY_START:LOG_DAY_END]
        if (day[4] == "-" and day[7] == "-" and day[:4].isdigit()
                and day[5:7].isdigit() and day[8:10].isdigit()):
            files.append(path)
    return files


def _scan_logs(logs_dir: Path, last_file: str, warnings: list):
    """Mine every daily log file whose day is strictly after the watermark
    file's day. The watermark advances only to the newest COMPLETE UTC day
    among them: today's partially grown file is mined now but never recorded
    as fully processed, so the next run re-mines it in full and aggregates
    its later appended tail. Returns (file_day_pairs, new_last_file) where
    file_day_pairs is a list of (day, [line_dict_or_None]) in file order."""
    today = _utcnow().strftime("%Y-%m-%d")
    last_day = last_file[LOG_DAY_START:LOG_DAY_END] if len(last_file) >= LOG_DAY_END else ""
    processed = []
    new_last = last_file or ""
    for path in _daily_log_files(logs_dir, warnings):
        day = path.name[LOG_DAY_START:LOG_DAY_END]
        if last_day and day <= last_day:
            continue
        lines = []
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                lines.append(json.loads(stripped))
            except json.JSONDecodeError:
                lines.append(None)
        processed.append((day, lines))
        if day < today:
            new_last = path.name
    return processed, new_last


def _aggregate_tools(rows) -> dict:
    """Per-tool totals, error counts, error rates, and message classes."""
    tools = {}
    for row, _dt in rows:
        tool = str(row[0])
        status = "" if row[1] is None else str(row[1])
        entry = tools.setdefault(tool, {"total": 0, "errors": 0, "message_classes": Counter()})
        entry["total"] += 1
        if status == "error":
            entry["errors"] += 1
            entry["message_classes"][_message_class(row[3] or "")] += 1
    out = {}
    for tool in sorted(tools):
        entry = tools[tool]
        total = entry["total"]
        out[tool] = {
            "total": total,
            "errors": entry["errors"],
            "error_rate": round(entry["errors"] / total, 4) if total else 0.0,
            "message_classes": dict(sorted(entry["message_classes"].items())),
        }
    return out


def _aggregate_logs(file_day_pairs) -> dict:
    """Noise-filtered per-day histograms. The noise filter runs before any
    counting, so noise lines never reach the histogram."""
    daily = {}
    for day, lines in file_day_pairs:
        bucket = daily.setdefault(day, Counter())
        for line in lines:
            if line is None:
                event = UNPARSEABLE_EVENT_CLASS
            else:
                event = str(line.get("event", UNPARSEABLE_EVENT_CLASS))
            if _is_noise(event):
                continue
            bucket[event] += 1
    return {day: dict(sorted(bucket.items())) for day, bucket in sorted(daily.items())}


def _aggregate_provider_codes(rows) -> dict:
    """Provider 429-family code counts, sourced from tool_usage.error_code
    per the audit recipe (1302 per-request rate limit, 1308 quota
    exhaustion); counted per code, never conflated. The host column is TEXT
    affinity, so numeric strings are accepted."""
    codes = Counter()
    for row, _dt in rows:
        raw = row[2]
        if raw is None or isinstance(raw, bool):
            continue
        try:
            code = int(raw)
        except (TypeError, ValueError):
            continue
        if code in PROVIDER_429_CODES:
            codes[code] += 1
    return {str(code): count for code, count in sorted(codes.items())}


def _correction_candidates(rows) -> list:
    candidates = []
    for row, _dt in rows:
        _ts, session_id, payload = row[0], row[1], row[2]
        text = "" if payload is None else str(payload)
        lowered = text.lower()
        if any(keyword in lowered for keyword in CORRECTION_KEYWORDS):
            candidates.append({
                "ts": str(_ts),
                "session_id": "" if session_id is None else str(session_id),
                "snippet": text[:SNIPPET_LIMIT],
            })
    return candidates


def _render_digest(counts: dict) -> str:
    lines = ["# Friction audit digest", ""]
    lines.append(f"- completed_at: {counts['completed_at']}")
    lines.append(f"- since: {counts['since'] if counts['since'] else '(none)'}")
    lines.append(f"- cadence_days: {counts['cadence_days']}")
    lines.append(f"- next_due: {counts['next_due']}")
    rp = counts["rows_processed"]
    lines.append(
        f"- rows processed: tool_usage {rp['tool_usage']}, session_input {rp['session_input']}, "
        f"log files {rp['log_files']} ({rp['log_lines']} lines)"
    )
    lines.append("")
    lines.append("## Per-tool error rates and message classes")
    lines.append("")
    if counts["tools"]:
        lines.append("| tool | total | errors | error_rate |")
        lines.append("| --- | --- | --- | --- |")
        for tool in sorted(counts["tools"]):
            entry = counts["tools"][tool]
            lines.append(
                f"| {tool} | {entry['total']} | {entry['errors']} | {entry['error_rate']} |"
            )
        lines.append("")
        for tool in sorted(counts["tools"]):
            classes = counts["tools"][tool]["message_classes"]
            if not classes:
                continue
            lines.append(f"{tool} message classes:")
            for cls, count in sorted(classes.items()):
                lines.append(f"- `{cls}`: {count}")
            lines.append("")
    else:
        lines.append("(no tool_usage rows in this delta)")
        lines.append("")
    lines.append("## Per-day event histogram (noise-filtered)")
    lines.append("")
    if counts["daily_events"]:
        for day in sorted(counts["daily_events"]):
            lines.append(f"- {day}:")
            for event, count in sorted(counts["daily_events"][day].items()):
                lines.append(f"  - {event}: {count}")
    else:
        lines.append("(no log events in this delta)")
    lines.append("")
    lines.append("## Provider 429 code counts")
    lines.append("")
    if counts["provider_429_codes"]:
        for code, count in sorted(counts["provider_429_codes"].items()):
            lines.append(f"- {code}: {count}")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Correction-heuristic candidates")
    lines.append("")
    if counts["correction_candidates"]:
        for cand in counts["correction_candidates"]:
            lines.append(f"- {cand['ts']} session {cand['session_id']}: \"{cand['snippet']}\"")
    else:
        lines.append("(none)")
    lines.append("")
    if counts["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for warning in counts["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")
    return "\n".join(lines)


def run_audit(db: Path, logs_dir: Path, out_dir: Path, since: str, cadence_days: int) -> dict:
    """One audit pass: scan deltas, write digest.md + counts.json, then advance
    state.json (watermarks and next_due) only after full processing."""
    since_dt = _parse_ts(since) if since else None
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    prior = _load_state(state_path)
    warnings: list = []

    tu_wm = _watermark(prior, "tool_usage")
    si_wm = _watermark(prior, "session_input")
    logs_wm = _watermark(prior, "logs")
    tu_floor = _parse_ts(tu_wm["max_ts"]) if tu_wm.get("max_ts") else None
    si_floor = _parse_ts(si_wm["max_ts"]) if si_wm.get("max_ts") else None

    tu_rows = _scan_tool_usage(db, since_dt, tu_floor, warnings)
    si_rows = _scan_session_input(db, since_dt, si_floor, warnings)
    file_day_pairs, new_last_file = _scan_logs(
        logs_dir, logs_wm.get("last_file") or "", warnings
    )

    tools = _aggregate_tools(tu_rows)
    daily_events = _aggregate_logs(file_day_pairs)
    provider_codes = _aggregate_provider_codes(tu_rows)
    candidates = _correction_candidates(si_rows)

    log_lines = sum(len(lines) for _day, lines in file_day_pairs)
    completed = _utcnow()
    next_due = completed + timedelta(days=cadence_days)

    watermarks = {
        "tool_usage": {
            "max_ts": _advance_max_ts(tu_wm.get("max_ts", ""), tu_rows, 4),
            "rows": int(tu_wm.get("rows", 0)) + len(tu_rows),
        },
        "session_input": {
            "max_ts": _advance_max_ts(si_wm.get("max_ts", ""), si_rows, 0),
            "rows": int(si_wm.get("rows", 0)) + len(si_rows),
        },
        "logs": {
            "last_file": new_last_file,
            "rows": int(logs_wm.get("rows", 0)) + log_lines,
        },
    }

    counts = {
        "completed_at": _iso(completed),
        "since": since or None,
        "cadence_days": cadence_days,
        "next_due": _iso(next_due),
        "rows_processed": {
            "tool_usage": len(tu_rows),
            "session_input": len(si_rows),
            "log_files": len(file_day_pairs),
            "log_lines": log_lines,
        },
        "watermarks": watermarks,
        "tools": tools,
        "daily_events": daily_events,
        "provider_429_codes": provider_codes,
        "correction_candidates": candidates,
        "warnings": warnings,
    }

    # Artifacts first, state last: watermarks and next_due advance only after
    # the sources are fully processed and the digest is durably written.
    _atomic_write_text(out_dir / "digest.md", _render_digest(counts))
    _atomic_write_text(out_dir / "counts.json", json.dumps(counts, indent=2, sort_keys=True) + "\n")

    new_state = {
        "version": STATE_VERSION,
        "watermarks": watermarks,
        "last_run_completed_at": counts["completed_at"],
        "next_due": counts["next_due"],
    }
    _atomic_write_text(state_path, json.dumps(new_state, indent=2, sort_keys=True) + "\n")
    return counts


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Friction-audit quantitative pass (watermark-driven).",
    )
    parser.add_argument(
        "--db",
        default="~/.zcode/cli/db/db.sqlite",
        help="sqlite db path; tilde-form default, expanded at use time",
    )
    parser.add_argument(
        "--logs-dir",
        default="~/.zcode/cli/log",
        help="daily zcode-*.jsonl logs dir; tilde-form default, expanded at use time",
    )
    parser.add_argument(
        "--out-dir",
        default=".ai-playbook/friction-audit",
        help="audit artifacts dir; repo/working-dir-relative default "
             "(the audit recipe's friction_audit_dir fallback), expanded at use time",
    )
    parser.add_argument(
        "--since",
        default="",
        help="ISO-8601 lower bound for scanned rows (default: empty, no bound)",
    )
    parser.add_argument(
        "--cadence-days",
        type=int,
        default=7,
        help="days added to the completion time when writing next_due (default 7)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.cadence_days < 1:
        print("error: --cadence-days must be >= 1", file=sys.stderr)
        return 2
    try:
        if args.since:
            _parse_ts(args.since)
    except ValueError:
        print(f"error: --since is not an ISO-8601 timestamp: {args.since}", file=sys.stderr)
        return 2
    counts = run_audit(
        db=Path(args.db).expanduser(),
        logs_dir=Path(args.logs_dir).expanduser(),
        out_dir=Path(args.out_dir).expanduser(),
        since=args.since,
        cadence_days=args.cadence_days,
    )
    rp = counts["rows_processed"]
    print(
        "friction audit: "
        f"tool_usage {rp['tool_usage']} rows, session_input {rp['session_input']} rows, "
        f"{rp['log_files']} log files; next_due {counts['next_due']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
