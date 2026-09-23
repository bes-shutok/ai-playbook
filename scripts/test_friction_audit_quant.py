#!/usr/bin/env python3
"""Hermetic tests for the friction-audit quantitative pass (audit lane Task 1).

Synthetic sqlite/logs fixtures are built under a mktemp directory with an
explicit tearDown teardown; no host db, no host logs, no host clock (the
completion clock is injected), and no network. Fixtures mirror the runtime
overlay's audit-recipe data map: epoch-millisecond integer timestamps in the
sqlite tables, `tool_name`/`payload` columns, and daily
`zcode-YYYY-MM-DD.jsonl` log files.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import friction_audit_quant as fa

# Injected completion clock: deterministic next_due assertions, never the
# host's wall clock.
FIXED_NOW = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
CADENCE_DAYS = 7
EXPECTED_NEXT_DUE = FIXED_NOW + timedelta(days=CADENCE_DAYS)


def _ms(iso: str) -> int:
    """Epoch-millisecond form of an ISO UTC timestamp (the host column shape)."""
    return int(fa._parse_ts(iso).timestamp() * 1000)


# Synthetic corpus. Timestamps are ISO-8601 UTC strings here and stored as
# epoch milliseconds (the host shape) by the fixture builders.
TOOL_ROWS = [
    ("2026-09-20T10:00:00Z", "Read", "ok", None, None),
    ("2026-09-20T10:05:00Z", "Bash", "error", None, "command not found: foo"),
    ("2026-09-20T11:00:00Z", "Bash", "error", 1302, "rate limit [1302] after 3 retries"),
    ("2026-09-21T09:00:00Z", "Edit", "ok", None, None),
    ("2026-09-21T09:30:00Z", "Bash", "error", 1308, "usage quota exhausted before retry"),
    ("2026-09-21T10:00:00Z", "Read", "ok", None, None),
    ("2026-09-22T08:00:00Z", "Bash", "ok", None, None),
    ("2026-09-22T09:00:00Z", "Edit", "error", None, "file changed on disk"),
    ("2026-09-22T10:00:00Z", "Bash", "ok", None, None),
]

INPUT_ROWS = [
    ("2026-09-20T10:10:00Z", "sess-1", "user", "fix the failing test"),
    ("2026-09-21T09:35:00Z", "sess-2", "user", "actually, use asyncio instead of threads"),
    ("2026-09-22T09:05:00Z", "sess-3", "user", "revert the last change, it broke lint"),
]

# Per-day log files named per the audit recipe; the line shape mirrors the
# host fields (timestamp, level, event, module, message). The
# persistence/compaction lines mirror the module-level NOISE_PATTERNS prefixes
# and must never reach the histograms.
LOG_DAYS = {
    "2026-09-20": [
        {"timestamp": "2026-09-20T10:00:30Z", "level": "info", "event": "session.event.persistence.row_written", "module": "store", "message": "row"},
        {"timestamp": "2026-09-20T10:01:00Z", "level": "info", "event": "session.event.tool.call", "module": "agent", "message": "call"},
        {"timestamp": "2026-09-20T10:02:00Z", "level": "warn", "event": "provider.request.rejected", "module": "gateway", "message": "rejected"},
        {"timestamp": "2026-09-20T10:03:00Z", "level": "info", "event": "session.event.compaction.started", "module": "store", "message": "compaction"},
    ],
    "2026-09-21": [
        {"timestamp": "2026-09-21T11:00:30Z", "level": "info", "event": "session.event.persistence.row_written", "module": "store", "message": "row"},
        {"timestamp": "2026-09-21T11:01:00Z", "level": "info", "event": "session.event.tool.call", "module": "agent", "message": "call"},
        {"timestamp": "2026-09-21T11:02:00Z", "level": "warn", "event": "provider.request.rejected", "module": "gateway", "message": "rejected"},
        {"timestamp": "2026-09-21T11:03:00Z", "level": "warn", "event": "provider.request.rejected", "module": "gateway", "message": "rejected"},
    ],
    "2026-09-22": [
        {"timestamp": "2026-09-22T12:01:00Z", "level": "info", "event": "session.event.tool.call", "module": "agent", "message": "call"},
        {"timestamp": "2026-09-22T12:02:00Z", "level": "warn", "event": "provider.request.rejected", "module": "gateway", "message": "rejected"},
        {"timestamp": "2026-09-22T12:03:00Z", "level": "info", "event": "session.event.turn.completed", "module": "agent", "message": "turn"},
    ],
}

LOG_FILE_TOTAL_ROWS = sum(len(lines) for lines in LOG_DAYS.values())


class FrictionAuditQuantTest(unittest.TestCase):
    """Audit-lane quant pass: cold start, watermark delta, noise filter,
    artifact fields, in-progress-day watermark, wrong-typed state."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="friction-audit-quant-test-"))
        self.db = self.base / "db.sqlite"
        self.logs_dir = self.base / "log"
        self.out_dir = self.base / "out"
        self.logs_dir.mkdir()
        self._build_db()
        self._build_logs()

    def tearDown(self):
        shutil.rmtree(self.base)

    # --- fixture builders -------------------------------------------------

    def _build_db(self):
        con = sqlite3.connect(str(self.db))
        try:
            # error_code is TEXT affinity on the host (values arrive as
            # numeric strings); the fixture mirrors that shape.
            con.execute(
                "CREATE TABLE tool_usage ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, tool_name TEXT, "
                "status TEXT, started_at INTEGER, error_code TEXT, error_message TEXT)"
            )
            con.execute(
                "CREATE TABLE session_input ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, kind TEXT, "
                "payload TEXT, time_created INTEGER)"
            )
            con.executemany(
                "INSERT INTO tool_usage (tool_name, status, error_code, error_message, started_at) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    (tool, status, error_code, msg, _ms(ts))
                    for (ts, tool, status, error_code, msg) in TOOL_ROWS
                ],
            )
            con.executemany(
                "INSERT INTO session_input (session_id, kind, payload, time_created) "
                "VALUES (?, ?, ?, ?)",
                [(sid, kind, payload, _ms(ts)) for (ts, sid, kind, payload) in INPUT_ROWS],
            )
            con.commit()
        finally:
            con.close()

    def _build_logs(self):
        for day, lines in LOG_DAYS.items():
            path = self.logs_dir / f"zcode-{day}.jsonl"
            path.write_text(
                "".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8"
            )

    def _write_state(self, watermarks):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        state = {"version": fa.STATE_VERSION, "watermarks": watermarks}
        (self.out_dir / "state.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _run(self, extra_args=()):
        args = [
            "--db", str(self.db),
            "--logs-dir", str(self.logs_dir),
            "--out-dir", str(self.out_dir),
            "--cadence-days", str(CADENCE_DAYS),
            *extra_args,
        ]
        with mock.patch.object(fa, "_utcnow", lambda: FIXED_NOW):
            rc = fa.main(args)
        self.assertEqual(rc, 0)
        return json.loads((self.out_dir / "counts.json").read_text(encoding="utf-8"))

    def _read_state(self):
        return json.loads((self.out_dir / "state.json").read_text(encoding="utf-8"))

    # --- tests ------------------------------------------------------------

    def test_cold_start_full_scan(self):
        """Empty state file: full-range aggregates written and next_due stamped
        completion plus 7 days."""
        self._write_state({})
        counts = self._run()

        self.assertEqual(counts["rows_processed"]["tool_usage"], len(TOOL_ROWS))
        self.assertEqual(counts["rows_processed"]["session_input"], len(INPUT_ROWS))
        self.assertEqual(
            counts["rows_processed"]["log_lines"],
            LOG_FILE_TOTAL_ROWS,
        )
        self.assertEqual(counts["tools"]["Bash"]["total"], 5)
        self.assertEqual(counts["tools"]["Bash"]["errors"], 3)
        self.assertEqual(counts["tools"]["Bash"]["error_rate"], 0.6)
        self.assertEqual(counts["tools"]["Read"], {"total": 2, "errors": 0, "error_rate": 0.0, "message_classes": {}})
        self.assertEqual(counts["tools"]["Edit"]["errors"], 1)
        self.assertEqual(len(counts["correction_candidates"]), 2)

        state = self._read_state()
        self.assertEqual(
            state["watermarks"]["tool_usage"],
            {"max_ts": str(_ms("2026-09-22T10:00:00Z")), "rows": len(TOOL_ROWS)},
        )
        self.assertEqual(
            state["watermarks"]["session_input"],
            {"max_ts": str(_ms("2026-09-22T09:05:00Z")), "rows": len(INPUT_ROWS)},
        )
        self.assertEqual(
            state["watermarks"]["logs"],
            {"last_file": "zcode-2026-09-22.jsonl", "rows": LOG_FILE_TOTAL_ROWS},
        )
        self.assertEqual(fa._parse_ts(state["next_due"]), EXPECTED_NEXT_DUE)
        self.assertEqual(fa._parse_ts(counts["next_due"]), EXPECTED_NEXT_DUE)

    def test_watermark_delta_only(self):
        """Watermarks mid-corpus: only post-watermark rows aggregate and the
        watermarks advance to the corpus maxima."""
        self._write_state({
            "tool_usage": {"max_ts": str(_ms("2026-09-21T09:30:00Z")), "rows": 5},
            "session_input": {"max_ts": str(_ms("2026-09-20T10:10:00Z")), "rows": 1},
            "logs": {"last_file": "zcode-2026-09-20.jsonl", "rows": 4},
        })
        counts = self._run()

        # Delta rows only: t6..t9 for tool_usage, s2..s3 for session_input,
        # whole day files after zcode-2026-09-20.jsonl for logs.
        self.assertEqual(counts["rows_processed"]["tool_usage"], 4)
        self.assertEqual(counts["rows_processed"]["session_input"], 2)
        self.assertEqual(counts["rows_processed"]["log_files"], 2)
        self.assertEqual(sorted(counts["daily_events"]), ["2026-09-21", "2026-09-22"])
        self.assertNotIn("2026-09-20", counts["daily_events"])
        self.assertEqual(counts["tools"]["Bash"]["total"], 2)
        self.assertEqual(counts["tools"]["Bash"]["errors"], 0)
        self.assertEqual(counts["tools"]["Edit"], {"total": 1, "errors": 1, "error_rate": 1.0, "message_classes": {"file changed on disk": 1}})
        self.assertEqual(counts["tools"]["Read"]["total"], 1)
        self.assertEqual(len(counts["correction_candidates"]), 2)

        state = self._read_state()
        self.assertEqual(state["watermarks"]["tool_usage"], {"max_ts": str(_ms("2026-09-22T10:00:00Z")), "rows": len(TOOL_ROWS)})
        self.assertEqual(state["watermarks"]["session_input"], {"max_ts": str(_ms("2026-09-22T09:05:00Z")), "rows": len(INPUT_ROWS)})
        self.assertEqual(
            state["watermarks"]["logs"],
            {"last_file": "zcode-2026-09-22.jsonl", "rows": LOG_FILE_TOTAL_ROWS},
        )

    def test_noise_filter(self):
        """Persistence-event lines are excluded from the digest counts; the
        fixture noise lines mirror the module-level NOISE_PATTERNS. Provider
        codes come from tool_usage.error_code per the recipe, so they are
        unaffected by the log noise filter."""
        for day, lines in LOG_DAYS.items():
            for line in lines:
                if any(line["event"].startswith(p) for p in fa.NOISE_PATTERNS):
                    self.assertTrue(fa._is_noise(line["event"]))

        self._write_state({})
        counts = self._run()

        # Only non-noise classes survive, with exact per-day counts.
        self.assertEqual(
            counts["daily_events"],
            {
                "2026-09-20": {"provider.request.rejected": 1, "session.event.tool.call": 1},
                "2026-09-21": {"provider.request.rejected": 2, "session.event.tool.call": 1},
                "2026-09-22": {
                    "provider.request.rejected": 1,
                    "session.event.tool.call": 1,
                    "session.event.turn.completed": 1,
                },
            },
        )
        digest = (self.out_dir / "digest.md").read_text(encoding="utf-8")
        self.assertNotIn("session.event.persistence", digest)
        self.assertNotIn("session.event.compaction", digest)
        self.assertNotIn("persistence", json.dumps(counts))
        self.assertNotIn("compaction", json.dumps(counts))
        # Provider 429 codes are counted per code from tool_usage.error_code
        # (1302 rate limit, 1308 quota exhaustion), never conflated.
        self.assertEqual(counts["provider_429_codes"], {"1302": 1, "1308": 1})

    def test_digest_and_counts_written(self):
        """Both artifacts exist with the documented fields, including next_due;
        state.json records the same next_due and the watermarks."""
        self._write_state({})
        counts = self._run()

        counts_path = self.out_dir / "counts.json"
        digest_path = self.out_dir / "digest.md"
        self.assertTrue(counts_path.exists())
        self.assertTrue(digest_path.exists())

        for field in (
            "completed_at",
            "since",
            "cadence_days",
            "next_due",
            "rows_processed",
            "watermarks",
            "tools",
            "daily_events",
            "provider_429_codes",
            "correction_candidates",
            "warnings",
        ):
            self.assertIn(field, counts)

        self.assertEqual(counts["cadence_days"], CADENCE_DAYS)
        self.assertIsNone(counts["since"])

        digest = digest_path.read_text(encoding="utf-8")
        for heading in (
            "# Friction audit digest",
            "## Per-tool error rates and message classes",
            "## Per-day event histogram (noise-filtered)",
            "## Provider 429 code counts",
            "## Correction-heuristic candidates",
        ):
            self.assertIn(heading, digest)
        self.assertIn(f"next_due: {counts['next_due']}", digest)
        self.assertIn("Bash", digest)

        state = self._read_state()
        self.assertEqual(state["next_due"], counts["next_due"])
        self.assertEqual(state["watermarks"], counts["watermarks"])
        self.assertEqual(state["last_run_completed_at"], counts["completed_at"])

    def test_in_progress_day_not_watermarked(self):
        """A run mid-day mines today's partial file but advances last_file only
        through the last COMPLETE UTC day; appending rows later the same day,
        the second run re-mines the file in full and aggregates the appended
        rows."""
        self._write_state({})
        today_log = self.logs_dir / "zcode-2026-09-23.jsonl"
        today_log.write_text(
            "".join(json.dumps(line) + "\n" for line in [
                {"timestamp": "2026-09-23T10:00:00Z", "level": "info",
                 "event": "session.event.tool.call", "module": "agent", "message": "call"},
                {"timestamp": "2026-09-23T11:00:00Z", "level": "info",
                 "event": "session.event.turn.started", "module": "agent", "message": "turn"},
            ]),
            encoding="utf-8",
        )

        counts1 = self._run()
        self.assertEqual(counts1["daily_events"]["2026-09-23"]["session.event.tool.call"], 1)
        self.assertEqual(counts1["rows_processed"]["log_files"], 4)
        state1 = self._read_state()
        # The current day is not marked fully processed; the watermark stops
        # at the last complete UTC day (2026-09-23 today, so at most 09-22).
        self.assertEqual(state1["watermarks"]["logs"]["last_file"], "zcode-2026-09-22.jsonl")

        # Later the same UTC day: the file grows by one line.
        with today_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "timestamp": "2026-09-23T11:30:00Z", "level": "info",
                "event": "session.event.tool.call", "module": "agent", "message": "call",
            }) + "\n")

        counts2 = self._run()
        self.assertEqual(counts2["daily_events"]["2026-09-23"]["session.event.tool.call"], 2)
        # Only the in-progress day is re-mined; the complete days stay
        # behind the watermark.
        self.assertEqual(counts2["rows_processed"]["log_files"], 1)
        self.assertEqual(
            self._read_state()["watermarks"]["logs"]["last_file"],
            "zcode-2026-09-22.jsonl",
        )

    def test_state_wrong_field_types_degrade_to_cold_start(self):
        """A valid-JSON state whose watermark fields carry wrong types (rows
        null) degrades to a warned cold start instead of crashing."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "state.json").write_text(
            json.dumps({"version": fa.STATE_VERSION, "watermarks": {
                "tool_usage": {"max_ts": "2026-09-21T09:30:00Z", "rows": None},
            }}) + "\n",
            encoding="utf-8",
        )
        err = io.StringIO()
        args = [
            "--db", str(self.db),
            "--logs-dir", str(self.logs_dir),
            "--out-dir", str(self.out_dir),
            "--cadence-days", str(CADENCE_DAYS),
        ]
        with mock.patch.object(fa, "_utcnow", lambda: FIXED_NOW), \
                contextlib.redirect_stderr(err):
            rc = fa.main(args)
        self.assertEqual(rc, 0)
        self.assertIn("cold start", err.getvalue())
        counts = json.loads((self.out_dir / "counts.json").read_text(encoding="utf-8"))
        self.assertEqual(counts["rows_processed"]["tool_usage"], len(TOOL_ROWS))
        self.assertEqual(counts["rows_processed"]["session_input"], len(INPUT_ROWS))
        state = self._read_state()
        self.assertEqual(state["watermarks"]["tool_usage"]["rows"], len(TOOL_ROWS))


if __name__ == "__main__":
    unittest.main()
