#!/usr/bin/env python3
"""Tests for the tool and script runtime statistics miner (tool_runtime_stats.py).

Hermetic suite: every test builds fixture stores shaped like the real host
session-store columns pinned in the plan Terms, runs the miner offline, and
asserts on emitted aggregates only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_PATH = Path(__file__).resolve().parent / "tool_runtime_stats.py"


def run_main(module, argv):
    """Run the CLI with captured streams; return (rc, stdout, stderr)."""
    import io
    import contextlib

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = module.main(["run", *argv])
    return rc, out.getvalue(), err.getvalue()


def _load_script_module():
    if not SCRIPT_PATH.exists():
        raise ModuleNotFoundError(
            f"tool_runtime_stats.py not found at {SCRIPT_PATH}"
        )
    spec = importlib.util.spec_from_file_location("tool_runtime_stats_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ms(year, month, day, hour=12, minute=0, second=0):
    """Epoch-ms for a local wall-clock datetime (noon default dodges DST edges)."""
    import datetime

    return int(datetime.datetime(year, month, day, hour, minute, second).timestamp() * 1000)


def _build_store(path: Path, tool_rows, turn_rows=(), part_rows=(), message_rows=()):
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE tool_usage (id TEXT PRIMARY KEY, session_id TEXT, turn_id TEXT,"
        " tool_call_id TEXT, tool_name TEXT, status TEXT, started_at INTEGER,"
        " completed_at INTEGER, duration_ms INTEGER, error_type TEXT);"
        "CREATE TABLE turn_usage (session_id TEXT, turn_id TEXT, started_at INTEGER,"
        " status TEXT, tool_call_count INTEGER, input_tokens INTEGER, output_tokens INTEGER,"
        " computed_total_tokens INTEGER, PRIMARY KEY (session_id, turn_id));"
        "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, data TEXT, sequence INTEGER);"
        "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT,"
        " sequence INTEGER);"
    )
    conn.executemany("INSERT INTO tool_usage VALUES (?,?,?,?,?,?,?,?,?,?)", tool_rows)
    conn.executemany("INSERT INTO turn_usage VALUES (?,?,?,?,?,?,?,?)", turn_rows)
    conn.executemany("INSERT INTO message VALUES (?,?,?,?)", message_rows)
    conn.executemany("INSERT INTO part VALUES (?,?,?,?,?)", part_rows)
    conn.commit()
    conn.close()


class ToolRuntimeStatsTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_script_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)

    def _run(self, argv):
        return self.module.main(["run", *argv])

    def test_per_day_call_and_error_counts(self):
        store = self.tmpdir / "store.sqlite"
        day1 = _ms(2026, 9, 21)
        day2 = _ms(2026, 9, 22)
        rows = [
            # two Edit rows on day1, one error
            ("tu1", "s1", "t1", "c1", "Edit", "completed", day1, day1 + 1000, 1000, None),
            ("tu2", "s1", "t2", "c2", "Edit", "error", day1 + 100, day1 + 300, 200, "ValueError"),
            # one Read row on day1
            ("tu3", "s1", "t3", "c3", "Read", "completed", day1, day1 + 500, 500, None),
            # two Bash rows on day2, one error
            ("tu4", "s2", "t4", "c4", "Bash", "completed", day2, day2 + 2000, 2000, None),
            ("tu5", "s2", "t5", "c5", "Bash", "error", day2 + 10, day2 + 20, 10, "OSError"),
        ]
        _build_store(store, rows)
        report = self._capture_json(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        by_key = {(r["date"], r["tool"]): r for r in report["days"]}
        d1 = report["days"][0]["date"]
        d2 = report["days"][-1]["date"]
        self.assertEqual(len(report["days"]), 3)
        self.assertEqual(by_key[(d1, "Edit")]["calls"], 2)
        self.assertEqual(by_key[(d1, "Edit")]["errors"], 1)
        self.assertEqual(by_key[(d1, "Read")]["calls"], 1)
        self.assertEqual(by_key[(d1, "Read")]["errors"], 0)
        self.assertEqual(by_key[(d2, "Bash")]["calls"], 2)
        self.assertEqual(by_key[(d2, "Bash")]["errors"], 1)

    def test_duration_present_uses_store_timing(self):
        store = self.tmpdir / "store.sqlite"
        base = _ms(2026, 9, 21)
        # twenty rows with store durations 1..20 seconds whose wall-clock
        # bounds span three times that (store column must win per row), plus
        # one NULL-duration row whose fallback delta is 2.0 s: modes mix in
        # one bucket and every p95 rank below the maximum is exercised
        rows = [
            (
                f"tu{i}", "s1", f"t{i}", f"c{i}", "Edit", "completed",
                base + i * 1000, base + i * 1000 + i * 3000, i * 1000, None,
            )
            for i in range(1, 21)
        ]
        rows.append(
            ("tu21", "s1", "t21", "c21", "Edit", "completed",
             base + 21000, base + 23000, None, None)
        )
        _build_store(store, rows)
        report = self._capture_json(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        row = report["days"][0]
        self.assertEqual(row["calls"], 21)
        # durations 1..20 s plus the 2.0 s fallback row
        expected_total = sum(range(1, 21)) + 2.0
        self.assertAlmostEqual(row["total_seconds"], expected_total)
        expected_mean = expected_total / 21
        self.assertAlmostEqual(row["mean_seconds"], expected_mean, places=2)
        # nearest-rank p95 at n=21 is the 20th of [1,2,2,3,...,19,20] = 19 s:
        # distinct from both the max (20) and any wall-clock-derived value
        self.assertAlmostEqual(row["p95_seconds"], 19.0)

    def test_duration_absent_derives_wallclock_delta(self):
        store = self.tmpdir / "store.sqlite"
        base = _ms(2026, 9, 21)
        rows = [
            # NULL duration_ms; completed_at - started_at = 7500ms
            ("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 7500, None, None),
            ("tu2", "s1", "t2", "c2", "Edit", "completed", base + 10000, base + 12500, None, None),
        ]
        _build_store(store, rows)
        report = self._capture_json(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        row = report["days"][0]
        self.assertAlmostEqual(row["mean_seconds"], (7500 + 2500) / 2 / 1000)
        self.assertAlmostEqual(row["total_seconds"], 10.0)

    def test_store_opened_read_only_and_unmodified(self):
        store = self.tmpdir / "store.sqlite"
        base = _ms(2026, 9, 21)
        rows = [
            ("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 1000, 1000, None),
        ]
        _build_store(store, rows)
        before = hashlib.sha256(store.read_bytes()).hexdigest()
        rc = self._run(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        self.assertEqual(rc, 0)
        after = hashlib.sha256(store.read_bytes()).hexdigest()
        self.assertEqual(before, after, "store file bytes changed during a full run")
        # the miner connects in SQLite read-only URI mode
        with mock.patch.object(sqlite3, "connect", wraps=sqlite3.connect) as connect_mock:
            self._run(["--store", str(store), "--out-root", str(self.tmpdir / "out2")])
        ro_calls = [
            c for c in connect_mock.call_args_list
            if c.kwargs.get("uri") and "mode=ro" in str(c.args[0])
        ]
        self.assertTrue(ro_calls, "miner never opened the store with a mode=ro URI")

    def test_missing_store_fails_open(self):
        absent = self.tmpdir / "absent.sqlite"
        rc, stdout, stderr = run_main(self.module, ["--store", str(absent), "--out-root", str(self.tmpdir / "out")])
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, f"expected exactly one report line, got: {lines}")
        self.assertIn("store", lines[0])

    def test_missing_tables_fails_open(self):
        empty = self.tmpdir / "empty.sqlite"
        sqlite3.connect(empty).close()
        rc, stdout, stderr = run_main(self.module, ["--store", str(empty), "--out-root", str(self.tmpdir / "out")])
        self.assertEqual(rc, 0)
        self.assertEqual(stderr, "")
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, f"expected exactly one report line, got: {lines}")
        self.assertIn("table", lines[0].lower())

    def test_bare_invocation_defaults_to_run(self):
        # the maintenance rider invokes the script without a subcommand
        store = self.tmpdir / "store.sqlite"
        base = _ms(2026, 9, 21)
        _build_store(store, [("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 1000, 1000, None)])
        import io
        import contextlib

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = self.module.main(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        self.assertEqual(rc, 0)
        self.assertTrue(out.getvalue().strip())
        report = json.loads(out.getvalue())
        self.assertEqual(report["days"][0]["tool"], "Edit")

    def test_missing_pinned_columns_raise_as_drift(self):
        # a present table missing a pinned column is schema drift: a genuine
        # defect that raises (only absent DATA takes the fail-open arms)
        store = self.tmpdir / "drifted.sqlite"
        conn = sqlite3.connect(store)
        conn.executescript(
            "CREATE TABLE tool_usage (id TEXT PRIMARY KEY, session_id TEXT, turn_id TEXT,"
            " tool_call_id TEXT, tool_name TEXT, status TEXT, started_at INTEGER,"
            " completed_at INTEGER, error_type TEXT);"  # duration_ms absent
            "CREATE TABLE turn_usage (session_id TEXT, turn_id TEXT, started_at INTEGER,"
            " status TEXT, tool_call_count INTEGER, input_tokens INTEGER, output_tokens INTEGER,"
            " computed_total_tokens INTEGER, PRIMARY KEY (session_id, turn_id));"
            "CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT,"
            " sequence INTEGER);"
        )
        conn.commit()
        conn.close()
        with self.assertRaises(self.module.SchemaDriftError) as caught:
            run_main(self.module, ["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        self.assertIn("duration_ms", str(caught.exception))

    def test_default_store_fallback_when_facts_absent(self):
        # with no facts key at all, the adapter default store resolves
        from unittest import mock

        fakehome = self.tmpdir / "fakehome"
        store = fakehome / ".zcode" / "cli" / "db" / "db.sqlite"
        store.parent.mkdir(parents=True, exist_ok=True)
        base = _ms(2026, 9, 21)
        _build_store(store, [("tu1", "s1", "t1", "c1", "Grep", "completed", base, base + 1000, 1000, None)])
        missing_facts = self.tmpdir / "absent-facts.md"
        with mock.patch.object(self.module, "DEFAULT_STORE", store):
            rc, stdout, _ = run_main(self.module, ["--facts", str(missing_facts), "--out-root", str(self.tmpdir / "out")])
        self.assertEqual(rc, 0)
        report = json.loads(stdout)
        self.assertEqual(report["days"][0]["tool"], "Grep")

    def test_null_tool_name_buckets_under_unknown(self):
        store = self.tmpdir / "store.sqlite"
        base = _ms(2026, 9, 21)
        _build_store(store, [("tu1", "s1", "t1", "c1", None, "completed", base, base + 1000, 1000, None)])
        stdout = self._report_for_store(store)
        report = json.loads(stdout)
        self.assertEqual(report["days"][0]["tool"], "unknown")

    def _report_for_store(self, store):
        argv = ["--store", str(store), "--out-root", str(self.tmpdir / "out")]
        rc, stdout, _ = run_main(self.module, argv)
        self.assertEqual(rc, 0)
        return stdout

    def test_malformed_facts_fails_loud(self):
        # a malformed facts document is a genuine config defect: the miner
        # must not silently mine a different (default) store
        facts = self.tmpdir / "facts-broken.md"
        facts.write_text("```toml\nsession_store_path = [broken\n```\n", encoding="utf-8")
        import tomllib

        with self.assertRaises(tomllib.TOMLDecodeError):
            self._run(["--facts", str(facts), "--out-root", str(self.tmpdir / "out")])

    def test_store_path_resolves_from_facts_with_cli_override(self):
        facts = self.tmpdir / "facts.md"
        store_a = self.tmpdir / "a.sqlite"
        store_b = self.tmpdir / "b.sqlite"
        base = _ms(2026, 9, 21)
        _build_store(store_a, [("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 1000, 1000, None)])
        _build_store(store_b, [("tu1", "s1", "t1", "c1", "Grep", "completed", base, base + 1000, 1000, None)])
        facts.write_text(
            "```toml\n"
            'session_store_path = "%s"\n'
            "```\n" % store_a,
            encoding="utf-8",
        )
        # no --store: the facts value resolves the store
        report = self._capture_json(["--facts", str(facts), "--out-root", str(self.tmpdir / "out1")])
        self.assertEqual([r["tool"] for r in report["days"]], ["Edit"])
        # --store wins over the facts value
        report = self._capture_json(
            ["--facts", str(facts), "--store", str(store_b), "--out-root", str(self.tmpdir / "out2")]
        )
        self.assertEqual([r["tool"] for r in report["days"]], ["Grep"])

    # -- helpers --

    def _capture_json(self, argv):
        stdout = self._run_capture_stdout(argv)
        return json.loads(stdout)

    def _run_capture_stdout(self, argv):
        rc, stdout, _ = run_main(self.module, argv)
        self.assertEqual(rc, 0)
        return stdout


SANCTIONED_TOOL_PART = json.dumps(
    {"type": "tool", "callID": "CALLID", "tool": "Bash",
     "state": {"input": {"command": "COMMAND"}, "status": "completed"}}
)


class TokenJoinTests(unittest.TestCase):
    """Task 3: per-turn tokens joined to tool rows; no-judgment share."""

    def setUp(self):
        self.module = _load_script_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.base = _ms(2026, 9, 21)

    def _run_and_read(self, tool_rows, turn_rows):
        store = self.tmpdir / "store.sqlite"
        _build_store(store, tool_rows, turn_rows=turn_rows)
        stdout, _ = self._streams(
            ["--store", str(store), "--out-root", str(self.tmpdir / "out")]
        )
        return json.loads(stdout)

    def _streams(self, argv):
        rc, stdout, stderr = run_main(self.module, argv)
        self.assertEqual(rc, 0)
        return stdout, stderr

    def test_tokens_joined_by_session_and_turn(self):
        base = self.base
        tool_rows = [
            # turn t1 joins two tool rows: its 1000 input tokens split evenly
            ("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 100, 100, None),
            ("tu2", "s1", "t1", "c2", "Read", "completed", base, base + 100, 100, None),
            # turn t2 joins one tool row: its 300 input tokens go entirely there
            ("tu3", "s1", "t2", "c3", "Bash", "completed", base, base + 100, 100, None),
        ]
        turn_rows = [
            ("s1", "t1", base, "completed", 2, 1000, 200, 1200),
            ("s1", "t2", base, "completed", 1, 300, 50, 350),
        ]
        report = self._run_and_read(tool_rows, turn_rows)
        self.assertEqual(len(report["day_summaries"]), 1)
        summary = report["day_summaries"][0]
        # day totals are the joined tokens: 1000 + 300 in, 200 + 50 out
        self.assertEqual(summary["tokens_in"], 1300)
        self.assertEqual(summary["tokens_out"], 250)
        # even allocation across joined rows, no duplication: the two rows of
        # turn t1 carry 600 each, the single row of t2 carries the full 350
        per_tool = {r["tool"]: r["tokens"] for r in report["days"]}
        self.assertEqual(per_tool["Edit"], 600.0)
        self.assertEqual(per_tool["Read"], 600.0)
        self.assertEqual(per_tool["Bash"], 350.0)
        self.assertAlmostEqual(sum(per_tool.values()), 1200 + 350)

    def test_no_judgment_share_is_single_tool_turns_per_day(self):
        base = self.base
        tool_rows = [
            ("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 100, 100, None),
            ("tu2", "s1", "t1", "c2", "Read", "completed", base, base + 100, 100, None),
            ("tu3", "s1", "t2", "c3", "Bash", "completed", base, base + 100, 100, None),
        ]
        turn_rows = [
            # multi-tool turn: 900 tokens
            ("s1", "t1", base, "completed", 2, 900, 0, 900),
            # single-tool turn: 300 tokens
            ("s1", "t2", base, "completed", 1, 300, 0, 300),
        ]
        report = self._run_and_read(tool_rows, turn_rows)
        summary = report["day_summaries"][0]
        self.assertAlmostEqual(summary["est_no_judgment_token_share"], 0.25)

    def test_token_join_zero_division_guards(self):
        base = self.base
        # store with turns but no tool rows: the pinned empty-window arm fires
        # (one-line report, exit 0) before any share is computed; no crash.
        store = self.tmpdir / "store1.sqlite"
        _build_store(
            store,
            [],
            turn_rows=[("s1", "t9", base, "completed", 1, 500, 10, 510)],
        )
        stdout, stderr = self._streams(["--store", str(store), "--out-root", str(self.tmpdir / "o1")])
        self.assertIn("nothing collected", stdout + stderr)
        # store with tool rows but no turns at all: rows report, summaries are
        # empty, the zero share is computed without a zero-division crash.
        store2 = self.tmpdir / "store2.sqlite"
        _build_store(
            store2,
            [("tu1", "s1", "t1", "c1", "Edit", "completed", base, base + 100, 100, None)],
            turn_rows=[],
        )
        stdout, _ = self._streams(["--store", str(store2), "--out-root", str(self.tmpdir / "o2")])
        report = json.loads(stdout)
        self.assertEqual(len(report["days"]), 1)
        # the day exists in the report window: the plan pins a zero share,
        # not an absent summary row
        summary = report["day_summaries"][0]
        self.assertEqual(summary["tokens_in"], 0)
        self.assertEqual(summary["tokens_out"], 0)
        self.assertEqual(summary["est_no_judgment_token_share"], 0.0)



class RankingReportTests(unittest.TestCase):
    """Task 5: rankings, error floor, filing thresholds, predicates, trend."""

    def setUp(self):
        self.module = _load_script_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()
        self.base = _ms(2026, 9, 21)

    # -- fixture builders --

    _store_counter = 0

    def _touch_repo_file(self, rel: str):
        target = self.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# fixture script\n", encoding="utf-8")

    def _store(self, tool_rows, turn_rows, part_rows=()):
        RankingReportTests._store_counter += 1
        store = self.tmpdir / f"store-{RankingReportTests._store_counter}.sqlite"
        _build_store(store, tool_rows, turn_rows=turn_rows, part_rows=part_rows)
        return store

    def _simple_rows(self, per_tool_seconds, tool="Bash", slug=None):
        """One single-row turn per entry; durations give the totals.

        ``tool`` may be a list (one name per entry) to create distinct rows.
        """
        tool_rows, turn_rows = [], []
        tools = tool if isinstance(tool, list) else [tool] * len(per_tool_seconds)
        for i, seconds in enumerate(per_tool_seconds):
            turn_id = f"t{i}"
            duration_ms = round(seconds * 1000)
            tool_rows.append(
                (f"tu{i}", "s1", turn_id, f"c{i}", tools[i], "completed",
                 self.base + i * 1000, self.base + i * 1000 + duration_ms,
                 duration_ms, None)
            )
            turn_rows.append(("s1", turn_id, self.base + i * 1000, "completed", 1, 10, 2, 12))
        part_rows = ()
        if slug:
            self._touch_repo_file(f"scripts/{slug}")
            part_rows = tuple(
                (f"p{i}", "m1", "s1",
                 json.dumps({"type": "tool", "callID": f"c{i}", "tool": tools[i],
                             "state": {"input": {"command": f"python3 scripts/{slug}"}, "status": "completed"}}),
                 i)
                for i in range(len(per_tool_seconds))
            )
        return tool_rows, turn_rows, part_rows

    def _candidate_rows(self, total_calls, single_calls, mean_seconds, slug):
        """total_calls Bash rows attributed to slug; single_calls of them in
        one-row turns, the rest in two-row turns."""
        tool_rows, turn_rows, part_rows = [], [], []
        shared = total_calls - single_calls
        for i in range(single_calls):
            turn_id = f"ts{i}"
            tool_rows.append(
                (f"tu{i}", "s1", turn_id, f"c{i}", "Bash", "completed",
                 self.base + i * 1000, self.base + i * 1000 + mean_seconds * 1000,
                 mean_seconds * 1000, None)
            )
            turn_rows.append(("s1", turn_id, self.base + i * 1000, "completed", 1, 10, 2, 12))
        for j in range(shared):
            pair_index = j // 2
            # an odd leftover shared row joins the first pair's turn as a third
            # member so it never lands in a single-row turn
            turn_id = f"td{pair_index}" if not (shared % 2 and j == shared - 1) else "td0"
            idx = single_calls + j
            tool_rows.append(
                (f"tu{idx}", "s1", turn_id, f"c{idx}", "Bash", "completed",
                 self.base + idx * 1000, self.base + idx * 1000 + mean_seconds * 1000,
                 mean_seconds * 1000, None)
            )
        if shared:
            shared_turn_ids = sorted({row[2] for row in tool_rows if row[2].startswith("td")})
            for turn_id in shared_turn_ids:
                members = sum(1 for row in tool_rows if row[2] == turn_id)
                turn_rows.append(("s1", turn_id, self.base, "completed", members, 20, 4, 24))
        if slug:
            self._touch_repo_file(f"scripts/{slug}")
        for i in range(total_calls):
            part_rows.append(
                (f"p{i}", "m1", "s1",
                 json.dumps({"type": "tool", "callID": f"c{i}", "tool": "Bash",
                             "state": {"input": {"command": f"python3 scripts/{slug}"}, "status": "completed"}}),
                 i)
            )
        return tool_rows, turn_rows, part_rows

    # -- helpers --

    _out_counter = 0

    def _digest_for(self, tool_rows, turn_rows, part_rows=(), extra_args=()):
        store = self._store(tool_rows, turn_rows, part_rows)
        RankingReportTests._out_counter += 1
        out_root = self.tmpdir / f"out{RankingReportTests._out_counter}"
        rc, stdout, stderr = run_main(
            self.module,
            ["--store", str(store), "--out-root", str(out_root),
             "--repo-root", str(self.repo), *extra_args],
        )
        self.assertEqual(rc, 0)
        digest = next((out_root / "tool-runtime-stats").glob("*.md")).read_text(encoding="utf-8")
        report = json.loads(stdout)
        return digest, report, out_root

    def test_ranking_top_n_by_total_time_and_tokens(self):
        seconds = [700, 600, 500, 400, 300, 200, 100]
        tools = [f"Tool{i}" for i in range(len(seconds))]
        tool_rows, turn_rows, _ = self._simple_rows(seconds, tool=tools)
        digest, report, _ = self._digest_for(tool_rows, turn_rows)
        time_section = digest.split("## Time ranking")[1].split("##")[0]
        listed = [int(ln.split("total=")[1].split()[0]) for ln in time_section.splitlines() if " total=" in ln]
        self.assertEqual(listed, [700, 600, 500, 400, 300])  # order desc, default cap 5
        token_section = digest.split("## Token ranking")[1].split("##")[0]
        token_counts = [int(ln.split("tokens=")[1].split()[0]) for ln in token_section.splitlines() if "tokens=" in ln]
        self.assertEqual(len(token_counts), 5)
        self.assertEqual(token_counts, sorted(token_counts, reverse=True))
        # CLI override shrinks the ranking
        digest, _, _ = self._digest_for(tool_rows, turn_rows, extra_args=("--top", "3"))
        time_section = digest.split("## Time ranking")[1].split("##")[0]
        listed = [int(ln.split("total=")[1].split()[0]) for ln in time_section.splitlines() if " total=" in ln]
        self.assertEqual(listed, [700, 600, 500])

    def test_ranking_orders_by_per_day_rate_not_window_total(self):
        # row A: 900 s across two days (450 s/day); row B: 800 s on one day
        # (800 s/day). Per-day ranking must put B first despite A's larger
        # window total.
        base2 = self.base + 24 * 3600 * 1000
        rows_a = [
            ("tuA1", "s1", "tA1", "cA1", "ToolA", "completed", self.base,
             self.base + 450000, 450000, None),
            ("tuA2", "s1", "tA2", "cA2", "ToolA", "completed", base2,
             base2 + 450000, 450000, None),
        ]
        turns_a = [
            ("s1", "tA1", self.base, "completed", 1, 10, 2, 12),
            ("s1", "tA2", base2, "completed", 1, 10, 2, 12),
        ]
        rows_b = [
            ("tuB1", "s1", "tB1", "cB1", "ToolB", "completed", self.base,
             self.base + 800000, 800000, None),
        ]
        turns_b = [("s1", "tB1", self.base, "completed", 1, 10, 2, 12)]
        digest, _, _ = self._digest_for(rows_a + rows_b, turns_a + turns_b)
        time_section = digest.split("## Time ranking")[1].split("##")[0]
        pos_a = time_section.index("ToolA")
        pos_b = time_section.index("ToolB")
        self.assertLess(pos_b, pos_a, "window total outranked the higher per-day rate")

    def test_error_rate_ranking_respects_count_floor(self):
        # 49 calls at mean 6s (294 s/day, below the aggregate arm), 100% errors
        tool_rows, turn_rows, part_rows = self._candidate_rows(49, 49, 6, "floor_probe.py")
        for i, row in enumerate(tool_rows):
            tool_rows[i] = row[:5] + ("error",) + row[6:]
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        error_section = digest.split("## Error ranking")[1].split("##")[0]
        self.assertNotIn("floor_probe.py", error_section)
        # exactly 50 calls: included
        tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 6, "floor_probe.py")
        for i, row in enumerate(tool_rows):
            tool_rows[i] = row[:5] + ("error",) + row[6:]
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        error_section = digest.split("## Error ranking")[1].split("##")[0]
        self.assertIn("floor_probe.py", error_section)

    def test_filing_threshold_aggregate_boundary(self):
        # exactly 300 total seconds/day: 50 calls at 6s mean, 100% single turns
        tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 6, "boundary.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        self.assertIn("filed: yes", digest)
        # 299 total seconds/day: 50 calls at 5.98s mean
        tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 5.98, "boundary.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        self.assertNotIn("filed: yes", digest)

    def test_filing_threshold_mean_count_arm_positive(self):
        # mean exactly 10.0s at exactly 50 calls (total 500 s/day): filed
        tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 10, "arm.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        self.assertIn("filed: yes", digest)
        # documented: the mean/count arm is subsumed by the aggregate arm under
        # total = count x mean; no negative witness exists for this arm alone.

    def test_scriptable_requires_all_three_predicates(self):
        # failing deterministic: same volume but unattributed commands (other)
        tool_rows, turn_rows, part_rows = self._candidate_rows(100, 100, 10, None)
        digest, _, _ = self._digest_for(tool_rows, turn_rows)
        self.assertNotIn("filed: yes", digest)
        # failing frequent: attributed but only 10 calls at 10s (100 s/day)
        tool_rows, turn_rows, part_rows = self._candidate_rows(10, 10, 10, "rare.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        self.assertNotIn("filed: yes", digest)
        # the top-row verdict names the failed predicate directly, so this
        # witness cannot pass with the frequent predicate wrongly true
        time_section = digest.split("## Time ranking")[1].split("##")[0]
        self.assertIn("scriptable candidate: no (below the call floor)", time_section)
        # failing judgment-free: 79 of 100 calls in single turns (79 percent)
        tool_rows, turn_rows, part_rows = self._candidate_rows(100, 79, 10, "busy.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        candidates = digest.split("## Scriptable candidates")[1].split("##")[0]
        self.assertNotIn("filed: yes", candidates)
        # boundary: exactly 80 of 100 in single turns (80 percent): scriptable
        tool_rows, turn_rows, part_rows = self._candidate_rows(100, 80, 10, "busy.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        candidates = digest.split("## Scriptable candidates")[1].split("##")[0]
        self.assertIn("busy.py", candidates)
        self.assertIn("filed: yes", candidates)
        # a candidate names measured cost, replacement shape, and est saving
        self.assertIn("measured cost", candidates)
        self.assertIn("replacement shape:", candidates)
        self.assertIn("estimated saving", candidates)

    def test_report_names_top_three_when_present(self):
        slugs = ["alpha.py", "beta.py", "gamma.py"]
        all_tool, all_turn, all_part = [], [], []
        for slug in slugs:
            tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 10, slug)
            offset = len(all_tool)
            all_tool += [
                (f"tu{offset + i}",) + (r[1], f"u{slug[:2]}{r[2]}", f"u{slug[:2]}{r[3]}") + tuple(r[4:])
                for i, r in enumerate(tool_rows)
            ]
            all_turn += [(r[0], f"u{slug[:2]}{r[1]}") + r[2:] for r in turn_rows]
            all_part += [
                (f"p{offset + i}",) + r[1:3] + (r[3].replace(f'"callID": "c{i}"', f'"callID": "u{slug[:2]}c{i}"'),) + r[4:]
                for i, r in enumerate(part_rows)
            ]
        digest, _, _ = self._digest_for(all_tool, all_turn, all_part)
        time_section = digest.split("## Time ranking")[1].split("##")[0]
        named = [s for s in slugs if f"script_slug={s}" in time_section]
        self.assertEqual(len(named), 3)
        # each named top row carries its measured numbers, not just a name
        for slug in named:
            line = next(ln for ln in time_section.splitlines() if f"script_slug={slug}" in ln)
            self.assertIn("total=500", line)
            self.assertIn("calls=50", line)
        candidates = digest.split("## Scriptable candidates")[1].split("##")[0]
        named_candidates = [s for s in slugs if s in candidates]
        self.assertEqual(len(named_candidates), 3)
        for slug in named_candidates:
            line = next(ln for ln in candidates.splitlines() if slug in ln)
            self.assertIn("measured cost", line)
            self.assertIn("estimated saving", line)

    def test_digest_names_attributed_rows_by_slug(self):
        tool_rows, turn_rows, part_rows = self._candidate_rows(50, 50, 10, "named.py")
        digest, _, _ = self._digest_for(tool_rows, turn_rows, part_rows)
        for section in digest.split("## ")[1:]:
            for ln in section.splitlines():
                if "named.py" in ln and "script_slug=" not in ln and ln.strip().startswith(("1.", "2.", "3.", "4.", "5.", "-")):
                    self.fail(f"digest line names an attributed row without its slug: {ln}")
        self.assertIn("script_slug=named.py", digest)

    def test_trend_compares_newest_prior_report(self):
        # prior run: Edit total 500s; new run: Edit total 900s
        prior_rows, prior_turns, _ = self._simple_rows([500], tool="Edit")
        store = self._store(prior_rows, prior_turns)
        out_root = self.tmpdir / "trend-out"
        import io
        import contextlib

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.module.main(["run", "--store", str(store), "--out-root", str(out_root),
                              "--repo-root", str(self.repo)])
        new_rows, new_turns, _ = self._simple_rows([900], tool="Edit")
        store2 = self.tmpdir / "store2.sqlite"
        _build_store(store2, new_rows, turn_rows=new_turns)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.module.main(["run", "--store", str(store2), "--out-root", str(out_root),
                              "--repo-root", str(self.repo)])
        digest = sorted((out_root / "tool-runtime-stats").glob("*.md"))[-1].read_text(encoding="utf-8")
        trend_section = digest.split("## Weekly trend")[1].split("##")[0]
        self.assertIn("Edit", trend_section)
        self.assertIn("+400", trend_section)
        self.assertIn("delta", trend_section)
        # empty out-root: a no-prior-report line
        out_root2 = self.tmpdir / "trend-empty"
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.module.main(["run", "--store", str(store), "--out-root", str(out_root2),
                              "--repo-root", str(self.repo)])
        digest = next((out_root2 / "tool-runtime-stats").glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("no prior report", digest)


class OutputContractTests(unittest.TestCase):
    """Task 4: stamped artifacts, retention line, keep-newest-eight, privacy."""

    def setUp(self):
        self.module = _load_script_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)
        self.base = _ms(2026, 9, 21)
        self.leak = "PW-SYNTHETIC-LEAK-CANARY"

    def _store_with_leak(self, path):
        """Fixture whose message content and mid-command token carry the leak."""
        command = f"python3 scripts/probe.py --flag {self.leak} --flag2 value"
        tool_rows, part_rows = [], []
        for i in range(3):
            tool_rows.append(
                (f"tu{i}", "s1", f"t{i}", f"c{i}", "Bash", "completed",
                 self.base + i * 1000, self.base + i * 1000 + 500, 500, None)
            )
            part_rows.append(
                (f"p{i}", "m1", "s1",
                 json.dumps({"type": "tool", "callID": f"c{i}", "tool": "Bash",
                             "state": {"input": {"command": command}, "status": "completed"}}),
                 i)
            )
        message_rows = [
            ("m1", "s1", json.dumps({"role": "user", "content": f"hello {self.leak} world"}), 1)
        ]
        _build_store(path, tool_rows, part_rows=part_rows, message_rows=message_rows)

    def _run(self, argv, expect_rc=0):
        rc, stdout, stderr = run_main(self.module, argv)
        self.assertEqual(rc, expect_rc)
        return stdout, stderr

    def _seed_prior_runs(self, out_root: Path, stamps: list[str]):
        home = out_root / "tool-runtime-stats"
        home.mkdir(parents=True, exist_ok=True)
        for stamp in stamps:
            (home / f"tool-runtime-stats-{stamp}.json").write_text("{}", encoding="utf-8")
            (home / f"tool-runtime-stats-{stamp}.md").write_text("digest", encoding="utf-8")

    def test_run_writes_json_and_digest_under_out_root(self):
        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        self._run(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        home = self.tmpdir / "out" / "tool-runtime-stats"
        json_files = sorted(home.glob("*.json"))
        md_files = sorted(home.glob("*.md"))
        self.assertEqual(len(json_files), 1)
        self.assertEqual(len(md_files), 1)

    def test_digest_carries_retention_line(self):
        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        self._run(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        digest = next((self.tmpdir / "out" / "tool-runtime-stats").glob("*.md")).read_text(encoding="utf-8")
        retention_lines = [ln for ln in digest.splitlines() if ln.startswith("retention:")]
        self.assertEqual(len(retention_lines), 1)
        self.assertIn("8", retention_lines[0])

    def test_retention_prunes_oldest_runs(self):
        import os
        import time

        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        out_root = self.tmpdir / "out"
        self._seed_prior_runs(out_root, [f"2026090{i}T000000" for i in range(1, 10)])  # nine prior runs
        # an orphan digest without its JSON table is pruned too
        orphan = out_root / "tool-runtime-stats" / "tool-runtime-stats-20260831T000000.md"
        orphan.write_text("orphan", encoding="utf-8")
        # backdate the seeded runs: fresh stamps are never pruned (concurrent-rider guard)
        old = time.time() - 3600
        for f in (out_root / "tool-runtime-stats").iterdir():
            os.utime(f, (old, old))
        self._run(["--store", str(store), "--out-root", str(out_root)])
        remaining = sorted(p.name for p in (out_root / "tool-runtime-stats").iterdir())
        stamps = sorted(n.split("-")[-1].rsplit(".", 1)[0] for n in remaining)
        self.assertEqual(len(remaining), 16)  # newest eight runs, json+md pairs
        self.assertNotIn("20260901T000000", stamps)
        self.assertNotIn("20260902T000000", stamps)
        self.assertIn("20260909T000000", stamps)
        self.assertNotIn("20260831T000000", stamps)  # orphan digest pruned

    def test_artifacts_carry_aggregates_only(self):
        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        self._run(["--store", str(store), "--out-root", str(self.tmpdir / "out")])
        home = self.tmpdir / "out" / "tool-runtime-stats"
        combined = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in home.iterdir())
        self.assertNotIn(self.leak, combined, "prompt-like string leaked into an artifact")

    def test_retention_fresh_partial_pair_survives_complete_pairs_pruned(self):
        # keep-newest-eight is the contract: a fresh COMPLETE pair beyond the
        # keep window is pruned; only a fresh PARTIAL pair (a concurrent rider
        # mid-write) survives one prune cycle
        import os
        import time

        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        out_root = self.tmpdir / "out"
        self._seed_prior_runs(out_root, [f"2026090{i}T000000" for i in range(1, 10)])
        home = out_root / "tool-runtime-stats"
        # a fresh partial pair beyond keep (json only, newer than the seeds)
        (home / "tool-runtime-stats-20260910T000000.json").write_text("{}", encoding="utf-8")
        self._run(["--store", str(store), "--out-root", str(out_root)])
        stamps = sorted(n.name.split("-")[-1].rsplit(".", 1)[0] for n in home.iterdir())
        # the fresh complete pair was pruned on the keep-newest-eight contract
        self.assertNotIn("20260901T000000", stamps)
        # the fresh partial pair survives one cycle (concurrent-rider guard)
        self.assertIn("20260910T000000", stamps)

    def test_stamp_collision_bumps_seconds(self):
        import datetime as dt

        home = self.tmpdir / "out" / "tool-runtime-stats"
        home.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
        (home / f"tool-runtime-stats-{stamp}.json").write_text("{}", encoding="utf-8")
        bumped = self.module._run_stamp(home)
        self.assertGreater(bumped, stamp)

    def test_facts_resolved_default_out_root(self):
        store = self.tmpdir / "store.sqlite"
        self._store_with_leak(store)
        facts = self.tmpdir / "facts.md"
        facts.write_text(
            "```toml\n" 'tmp_dir = "%s"\n' "```\n" % (self.tmpdir / "docs-tmp"),
            encoding="utf-8",
        )
        self._run(["--store", str(store), "--facts", str(facts)])
        home = self.tmpdir / "docs-tmp" / "tool-runtime-stats"
        self.assertTrue(home.is_dir())
        self.assertEqual(len(list(home.glob("*.json"))), 1)
        self.assertEqual(len(list(home.glob("*.md"))), 1)


class BashAttributionTests(unittest.TestCase):
    """Task 2: repo-anchored script attribution for Bash rows."""




    def setUp(self):
        self.module = _load_script_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.base = _ms(2026, 9, 21)

    _fixture_counter = 0

    def _touch_repo_file(self, rel: str):
        target = self.repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# fixture script\n", encoding="utf-8")

    def _fixture(self, commands, tool="Bash"):
        """One Bash row + part row per command; CALLID tokens join the part."""
        BashAttributionTests._fixture_counter += 1
        store = Path(self.tmp.name) / f"store-{BashAttributionTests._fixture_counter}.sqlite"
        tool_rows, part_rows = [], []
        for i, command in enumerate(commands):
            call_id = f"c{i}"
            tool_rows.append(
                (f"tu{i}", "s1", f"t{i}", call_id, tool, "completed",
                 self.base + i * 1000, self.base + i * 1000 + 100, 100, None)
            )
            if command is not None:
                part_rows.append(
                    (f"p{i}", "m1", "s1",
                     SANCTIONED_TOOL_PART.replace("CALLID", call_id).replace("COMMAND", command),
                     i)
                )
        _build_store(store, tool_rows, part_rows=part_rows)
        return store

    def _slugs(self, store):
        report = self._capture_json(
            ["--store", str(store), "--out-root", str(Path(self.tmp.name) / "out"),
             "--repo-root", str(self.repo)]
        )
        return [(r["tool"], r["script_slug"]) for r in report["days"]]

    def _capture_json(self, argv):
        stdout, _ = self._run_capture_streams(argv)
        return json.loads(stdout)

    def _run_capture_streams(self, argv):
        rc, stdout, stderr = run_main(self.module, argv)
        self.assertEqual(rc, 0)
        return stdout, stderr

    def test_bash_command_attribution_to_script_slug(self):
        self._touch_repo_file("scripts/quota_window_probe.py")
        store = self._fixture(["python3 scripts/quota_window_probe.py --plan x"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "quota_window_probe.py")])

    def test_command_outside_sanctioned_prefixes_aggregates_as_other(self):
        foreign = Path(self.tmp.name) / "foreign-project"
        foreign.mkdir()
        store = self._fixture([f"{foreign}/tool.sh run fast"])
        out_root = Path(self.tmp.name) / "out-privacy"
        stdout, stderr = self._run_capture_streams(
            ["--store", str(store), "--out-root", str(out_root),
             "--repo-root", str(self.repo)]
        )
        rows = [(r["tool"], r["script_slug"]) for r in json.loads(stdout)["days"]]
        self.assertEqual(rows, [("Bash", "other")])
        # the foreign path string must never reach any artifact of this run
        artifacts = [p for p in out_root.rglob("*") if p.is_file()]
        self.assertTrue(artifacts, "privacy run produced no artifacts to inspect")
        combined = stdout + stderr + "".join(p.read_text(errors="ignore") for p in artifacts)
        self.assertNotIn(str(foreign), combined)

    def test_attribution_first_scripts_token_wins(self):
        self._touch_repo_file("scripts/first_tool.py")
        self._touch_repo_file("scripts/second_tool.py")
        store = self._fixture(["python3 scripts/first_tool.py lint scripts/second_tool.py"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "first_tool.py")])

    def test_non_bash_tools_unaffected(self):
        store = self._fixture(["ignored-command-a", "ignored-command-b"], tool="Edit")
        # Edit rows carry no Bash attribution even when parts exist
        report = self._capture_json(
            ["--store", str(store), "--out-root", str(Path(self.tmp.name) / "out"),
             "--repo-root", str(self.repo)]
        )
        self.assertEqual({(r["tool"], r["script_slug"]) for r in report["days"]}, {("Edit", None)})

    def test_missing_part_rows_degrade_to_other(self):
        store = self._fixture([None, None])  # Bash rows with no matching part rows
        stdout, stderr = self._run_capture_streams(
            ["--store", str(store), "--out-root", str(Path(self.tmp.name) / "out"),
             "--repo-root", str(self.repo)]
        )
        report = json.loads(stdout)
        self.assertEqual({(r["tool"], r["script_slug"]) for r in report["days"]}, {("Bash", "other")})
        degradation_lines = [ln for ln in stderr.splitlines() if "part" in ln.lower()]
        self.assertTrue(degradation_lines, "no degradation note printed")

    def test_foreign_relative_command_requires_existing_file(self):
        # a foreign relative command shape must not attribute to this repo
        # when the referenced script does not exist here (repo-anchor invariant)
        store = self._fixture(["python3 scripts/foreign_secret.py --flag x"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "other")])
        # once the file exists under the sanctioned repo root, it attributes
        self._touch_repo_file("scripts/foreign_secret.py")
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "foreign_secret.py")])

    def test_home_relative_sanctioned_path_attributed(self):
        # ~ and $HOME forms resolve against the HOME env and attribute when
        # the file exists under the sanctioned home playbook prefix
        fakehome = self.repo.parent / "fakehome"
        script = fakehome / ".ai-playbook" / "scripts" / "home_probe.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# fixture\n", encoding="utf-8")
        import os
        from unittest import mock

        prefixes = (self.repo.resolve(), (fakehome / ".ai-playbook").resolve())
        with mock.patch.dict(os.environ, {"HOME": str(fakehome)}):
            slug = self.module._token_script_slug("~/.ai-playbook/scripts/home_probe.py", prefixes)
            self.assertEqual(slug, "home_probe.py")
            slug = self.module._token_script_slug(
                "$HOME/.ai-playbook/scripts/home_probe.py", prefixes
            )
            self.assertEqual(slug, "home_probe.py")

    def test_malformed_part_data_raises(self):
        # malformed JSON in part data is a genuine store defect, not an
        # absent-data arm: the miner raises and the rider's fail-open wrapping
        # reports it without failing the maintenance turn
        BashAttributionTests._fixture_counter += 1
        store = Path(self.tmp.name) / f"store-{BashAttributionTests._fixture_counter}.sqlite"
        tool_rows = [
            ("tu0", "s1", "t0", "c0", "Bash", "completed", self.base, self.base + 100, 100, None),
        ]
        part_rows = [("p0", "m1", "s1", "not-json{", 0)]
        _build_store(store, tool_rows, part_rows=part_rows)
        with self.assertRaises(sqlite3.OperationalError):
            self._run_capture_streams(
                ["--store", str(store), "--out-root", str(Path(self.tmp.name) / "out"),
                 "--repo-root", str(self.repo)]
            )

    def test_glued_redirection_token_not_attributed(self):
        # 2>/dev/null must not become a "null" slug; the real script after it wins
        self._touch_repo_file("scripts/real_script.py")
        store = self._fixture(["2>/dev/null python3 scripts/real_script.py --flag x"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "real_script.py")])

    def test_shell_punctuation_stripped_from_slugs(self):
        self._touch_repo_file("scripts/done-lock.sh")
        store = self._fixture(["bash scripts/done-lock.sh} && echo hi;"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "done-lock.sh")])

    def test_pattern_tokens_not_attributed(self):
        # grep/sed pattern arguments with path separators are not script names
        self._touch_repo_file("docs/x.py")
        store = self._fixture(["grep -c 'docs/(tax|domain)/' docs/x.py"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "x.py")])
        self._touch_repo_file("docs/real.py")
        store = self._fixture(["rg --files docs '*.md' docs/real.py"])
        rows = self._slugs(store)
        self.assertEqual(rows, [("Bash", "real.py")])


if __name__ == "__main__":
    unittest.main()
