#!/usr/bin/env python3
"""Read-only summary of ``~/.ai-playbook/logs/hooks.log``.

Parses JSONL lines for recall observability (Task 3 schema) and legacy
``keying`` metadata. Surfaces fire vs suppress counts and suppress ratio for
operator monitoring. Stdlib-only leaf; no runtime effect on agents.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Pinned recall schema (must match lessons_recall.py Task 3 constants).
RECALL_EVENT = "recall"
RECALL_OUTCOME_FIRE = "fire"
RECALL_OUTCOME_SUPPRESS_DEDUP = "suppress-dedup"
RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS = "suppress-empty-corpus"
RECALL_OUTCOME_SUPPRESS_CLASSIFY = "suppress-classify"
RECALL_OUTCOMES = (
    RECALL_OUTCOME_FIRE,
    RECALL_OUTCOME_SUPPRESS_DEDUP,
    RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS,
    RECALL_OUTCOME_SUPPRESS_CLASSIFY,
)

DEFAULT_LOG_PATH = Path.home() / ".ai-playbook" / "logs" / "hooks.log"
DEFAULT_DAYS = 7


@dataclass
class LogSummary:
    """Aggregated counts from hooks.log JSONL lines."""

    recall_fire: int = 0
    recall_suppress_dedup: int = 0
    recall_suppress_empty_corpus: int = 0
    recall_suppress_classify: int = 0
    keying_counts: dict[str, int] = field(default_factory=dict)
    lines_read: int = 0
    lines_in_window: int = 0

    @property
    def recall_total(self) -> int:
        return (
            self.recall_fire
            + self.recall_suppress_dedup
            + self.recall_suppress_empty_corpus
            + self.recall_suppress_classify
        )

    @property
    def recall_suppress_total(self) -> int:
        return (
            self.recall_suppress_dedup
            + self.recall_suppress_empty_corpus
            + self.recall_suppress_classify
        )

    @property
    def suppress_ratio(self) -> float | None:
        if self.recall_total == 0:
            return None
        return self.recall_suppress_total / self.recall_total

    @property
    def keying_no_anchor(self) -> int:
        return self.keying_counts.get("no-anchor", 0)


def _parse_ts(ts: object) -> datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_window(ts: datetime | None, *, cutoff: datetime) -> bool:
    if ts is None:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts >= cutoff


def summarize_log(log_path: Path, *, days: int) -> LogSummary:
    """Parse ``log_path`` and return aggregated counts for the last ``days`` days."""
    summary = LogSummary()
    if not log_path.is_file():
        return summary

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        raw = log_path.read_text(encoding="utf-8")
    except OSError:
        return summary

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        summary.lines_read += 1
        try:
            obj = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            continue
        if not isinstance(obj, dict):
            continue

        ts = _parse_ts(obj.get("ts"))
        if not _in_window(ts, cutoff=cutoff):
            continue
        summary.lines_in_window += 1

        event = obj.get("event")
        if event == RECALL_EVENT:
            outcome = obj.get("outcome")
            if outcome == RECALL_OUTCOME_FIRE:
                summary.recall_fire += 1
            elif outcome == RECALL_OUTCOME_SUPPRESS_DEDUP:
                summary.recall_suppress_dedup += 1
            elif outcome == RECALL_OUTCOME_SUPPRESS_EMPTY_CORPUS:
                summary.recall_suppress_empty_corpus += 1
            elif outcome == RECALL_OUTCOME_SUPPRESS_CLASSIFY:
                summary.recall_suppress_classify += 1

        keying = obj.get("keying")
        if isinstance(keying, str) and keying:
            summary.keying_counts[keying] = summary.keying_counts.get(keying, 0) + 1

    return summary


def _format_summary(summary: LogSummary, *, days: int, log_path: Path) -> str:
    ratio = summary.suppress_ratio
    ratio_text = f"{ratio:.3f}" if ratio is not None else "n/a"
    keying_parts = [
        f"{name}={summary.keying_counts.get(name, 0)}"
        for name in ("env-var", "project-only", "no-anchor", "error", "fail-open")
    ]
    extra_keying = sorted(
        k for k in summary.keying_counts if k not in {
            "env-var", "project-only", "no-anchor", "error", "fail-open",
        }
    )
    for name in extra_keying:
        keying_parts.append(f"{name}={summary.keying_counts[name]}")

    return "\n".join(
        [
            f"hooks.log summary (last {days} days)",
            f"log: {log_path}",
            (
                "recall: "
                f"fire={summary.recall_fire} "
                f"suppress-dedup={summary.recall_suppress_dedup} "
                f"suppress-empty-corpus={summary.recall_suppress_empty_corpus} "
                f"suppress-classify={summary.recall_suppress_classify} "
                f"total={summary.recall_total} "
                f"suppress_ratio={ratio_text}"
            ),
            f"keying: {' '.join(keying_parts)}",
            f"lines: read={summary.lines_read} in_window={summary.lines_in_window}",
        ]
    )


def selftest(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    filter_name: str | None = None
    for arg in args:
        if arg.startswith("--selftest#"):
            filter_name = arg[len("--selftest#") :]
            break

    all_ok = True

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal all_ok
        if filter_name is not None and filter_name not in label:
            return
        if condition:
            print(f"PASS: {label}")
        else:
            suffix = f" - {detail}" if detail else ""
            print(f"FAIL: {label}{suffix}")
            all_ok = False

    # ------------------------------------------------------------------ #
    # empty_log: missing log -> exit 0, zero counts.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        missing = Path(td) / "missing-hooks.log"
        empty_summary = summarize_log(missing, days=7)
        check(
            "empty_log: missing file recall_total == 0",
            empty_summary.recall_total == 0,
            str(empty_summary.recall_total),
        )
        check(
            "empty_log: missing file keying empty",
            empty_summary.keying_counts == {},
            str(empty_summary.keying_counts),
        )
        check(
            "empty_log: missing file lines_read == 0",
            empty_summary.lines_read == 0,
            str(empty_summary.lines_read),
        )

    # ------------------------------------------------------------------ #
    # suppress_ratio: Task 3 recall JSONL fixture -> correct fire/suppress.
    # ------------------------------------------------------------------ #
    now = datetime.now(timezone.utc)
    recent_ts = now.isoformat()
    old_ts = (now - timedelta(days=30)).isoformat()

    fixture_lines = [
        {
            "ts": recent_ts,
            "event": RECALL_EVENT,
            "outcome": RECALL_OUTCOME_FIRE,
            "family": "G",
        },
        {
            "ts": recent_ts,
            "event": RECALL_EVENT,
            "outcome": RECALL_OUTCOME_SUPPRESS_DEDUP,
            "family": "G",
        },
        {
            "ts": recent_ts,
            "event": RECALL_EVENT,
            "outcome": RECALL_OUTCOME_SUPPRESS_CLASSIFY,
        },
        {"ts": recent_ts, "keying": "env-var"},
        {"ts": recent_ts, "keying": "project-only"},
        {"ts": recent_ts, "keying": "no-anchor"},
        {
            "ts": old_ts,
            "event": RECALL_EVENT,
            "outcome": RECALL_OUTCOME_FIRE,
            "family": "A",
        },
    ]

    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "hooks.log"
        log_path.write_text(
            "\n".join(json.dumps(row) for row in fixture_lines) + "\n",
            encoding="utf-8",
        )
        ratio_summary = summarize_log(log_path, days=7)
        check(
            "suppress_ratio: recall fire == 1",
            ratio_summary.recall_fire == 1,
            str(ratio_summary.recall_fire),
        )
        check(
            "suppress_ratio: recall suppress-dedup == 1",
            ratio_summary.recall_suppress_dedup == 1,
            str(ratio_summary.recall_suppress_dedup),
        )
        check(
            "suppress_ratio: recall suppress-classify == 1",
            ratio_summary.recall_suppress_classify == 1,
            str(ratio_summary.recall_suppress_classify),
        )
        check(
            "suppress_ratio: recall total == 3",
            ratio_summary.recall_total == 3,
            str(ratio_summary.recall_total),
        )
        check(
            "suppress_ratio: suppress total == 2",
            ratio_summary.recall_suppress_total == 2,
            str(ratio_summary.recall_suppress_total),
        )
        check(
            "suppress_ratio: ratio == 2/3",
            ratio_summary.suppress_ratio is not None
            and abs(ratio_summary.suppress_ratio - (2 / 3)) < 1e-9,
            str(ratio_summary.suppress_ratio),
        )
        check(
            "suppress_ratio: keying env-var == 1",
            ratio_summary.keying_counts.get("env-var") == 1,
            str(ratio_summary.keying_counts),
        )
        check(
            "suppress_ratio: keying project-only == 1",
            ratio_summary.keying_counts.get("project-only") == 1,
            str(ratio_summary.keying_counts),
        )
        check(
            "suppress_ratio: keying no-anchor == 1",
            ratio_summary.keying_no_anchor == 1,
            str(ratio_summary.keying_counts),
        )
        check(
            "suppress_ratio: old fire line excluded by --days window",
            ratio_summary.lines_in_window == 6,
            str(ratio_summary.lines_in_window),
        )

    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--selftest" in args or any(a.startswith("--selftest#") for a in args):
        return selftest(args)

    parser = argparse.ArgumentParser(
        description="Summarize recall and keying lines from hooks.log (read-only).",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help=f"Path to hooks.log (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Include lines from the last N days (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run in-memory selftests.",
    )
    ns = parser.parse_args(args)

    if ns.days < 0:
        print("error: --days must be >= 0", file=sys.stderr)
        return 2

    summary = summarize_log(ns.log.expanduser(), days=ns.days)
    print(_format_summary(summary, days=ns.days, log_path=ns.log.expanduser()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
