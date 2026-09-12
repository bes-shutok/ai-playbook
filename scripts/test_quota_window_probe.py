#!/usr/bin/env python3
"""Hermetic tests for the quota window probe pure core (parsing, binding, thresholds)."""

from __future__ import annotations

import contextlib
import json
from datetime import datetime
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Mapping
import unittest
from unittest import mock

import quota_window_probe as probe

ROOT = Path(__file__).resolve().parents[1]
QUOTA_DIR = ROOT / "scripts/testdata/quota"
ZCODE_FIXTURE = QUOTA_DIR / "zcode_limit_response.json"
CODEX_FIXTURE = QUOTA_DIR / "codex_rollout.jsonl"


class QuotaWindowProbeTest(unittest.TestCase):
    def test_parse_zcode_limits(self) -> None:
        payload = json.loads(ZCODE_FIXTURE.read_text(encoding="utf-8"))
        # 12 minutes before the TOKENS_LIMIT reset; local tz never hardcodes a zone.
        now = 1789146000 - 12 * 60
        limits = probe.parse_zcode_limits(payload, now=now)
        self.assertEqual(len(limits), 2)
        primary = limits[0]
        self.assertEqual(primary["kind"], "primary")
        self.assertEqual(primary["used_percent"], 87.5)
        self.assertEqual(primary["reset_at_epoch"], 1789146000)
        # reset_at_iso round-trips back to the same epoch in the local zone.
        self.assertEqual(
            int(datetime.fromisoformat(primary["reset_at_iso"]).timestamp()),
            1789146000,
        )
        self.assertEqual(primary["minutes_remaining"], 12)
        secondary = limits[1]
        self.assertEqual(secondary["kind"], "secondary")
        self.assertEqual(secondary["used_percent"], 43.2)
        self.assertEqual(secondary["reset_at_epoch"], 1789577400)
        self.assertEqual(
            int(datetime.fromisoformat(secondary["reset_at_iso"]).timestamp()),
            1789577400,
        )

    def test_parse_codex_rollout_windows(self) -> None:
        lines = CODEX_FIXTURE.read_text(encoding="utf-8").splitlines()
        now = 1789182137 - 40 * 60
        limits = probe.parse_codex_rollout(lines, now=now)
        self.assertEqual(len(limits), 2)
        primary = limits[0]
        self.assertEqual(primary["kind"], "primary")
        self.assertEqual(primary["used_percent"], 4.0)
        self.assertEqual(primary["reset_at_epoch"], 1789182137)
        self.assertEqual(
            int(datetime.fromisoformat(primary["reset_at_iso"]).timestamp()),
            1789182137,
        )
        self.assertEqual(primary["minutes_remaining"], 40)
        secondary = limits[1]
        self.assertEqual(secondary["kind"], "secondary")
        self.assertEqual(secondary["used_percent"], 96.0)
        self.assertEqual(secondary["reset_at_epoch"], 1789577839)
        self.assertEqual(
            int(datetime.fromisoformat(secondary["reset_at_iso"]).timestamp()),
            1789577839,
        )

    def test_binding_earliest_reset(self) -> None:
        late_primary = probe.make_limit("primary", 10.0, 2000, now=1000)
        early_secondary = probe.make_limit("secondary", 10.0, 1500, now=1000)
        self.assertEqual(probe.select_binding([late_primary, early_secondary]), "secondary")
        early_primary = probe.make_limit("primary", 10.0, 1200, now=1000)
        self.assertEqual(probe.select_binding([early_primary, early_secondary]), "primary")

    def test_all_windows_expired_maps_to_fail_open_unknown(self) -> None:
        expired = probe.make_limit("primary", 10.0, 500, now=1000)
        self.assertLessEqual(expired["minutes_remaining"], 0)
        # Stale data must not force a pause that immediately thrashes into a
        # resume: an all-expired limit set fails open to status unknown.
        report = probe.build_report("zcode", [expired], now=1000)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual(report["limits"], [])
        self.assertTrue(
            any("already reset" in r for r in report["reasons"]), report["reasons"]
        )

    def test_empty_limits_maps_to_fail_open_unknown(self) -> None:
        # Pure-core direct callers pass no windows at all; "no data" must
        # never be treated as an all-clear, so it also fails open to unknown.
        report = probe.build_report("zcode", [], now=1000)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual(report["limits"], [])
        self.assertIn("no limits supplied", report["reasons"])

    def test_mixed_expired_and_live_binding_uses_live_only(self) -> None:
        # One expired (earliest reset) plus one live, comfortable limit: the
        # expired window must not win binding nor force a pause; the live
        # window's semantics decide.
        expired = probe.make_limit("secondary", 95.0, 500, now=1000)
        live = probe.make_limit("primary", 10.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [expired, live], now=1000)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["binding"], "primary")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual(len(report["limits"]), 1)
        self.assertEqual(report["limits"][0]["kind"], "primary")
        # Same mix but the live window is hot: the live window still decides.
        hot_live = probe.make_limit("primary", 95.0, 1000 + 5 * 60, now=1000)
        hot = probe.build_report("zcode", [expired, hot_live], now=1000)
        self.assertEqual(hot["pause_decision"], "pause")

    def test_pause_decision_minutes_boundary(self) -> None:
        exactly = probe.build_report(
            "zcode", [probe.make_limit("primary", 10.0, 1000 + 20 * 60, now=1000)], now=1000
        )
        self.assertEqual(exactly["pause_decision"], "continue")
        below = probe.build_report(
            "zcode", [probe.make_limit("primary", 10.0, 1000 + 19 * 60, now=1000)], now=1000
        )
        self.assertEqual(below["pause_decision"], "pause")

    def test_pause_decision_percent_boundary(self) -> None:
        exactly = probe.build_report(
            "zcode", [probe.make_limit("primary", 90.0, 1000 + 120 * 60, now=1000)], now=1000
        )
        self.assertEqual(exactly["pause_decision"], "pause")
        under = probe.build_report(
            "zcode", [probe.make_limit("primary", 89.0, 1000 + 120 * 60, now=1000)], now=1000
        )
        self.assertEqual(under["pause_decision"], "continue")

    def test_build_report_contract(self) -> None:
        limit = probe.make_limit("primary", 87.5, 1000 + 12 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000)
        self.assertEqual(
            sorted(report),
            sorted(["runtime", "limits", "binding", "pause_decision", "reasons", "status"]),
        )
        self.assertEqual(report["runtime"], "zcode")
        self.assertEqual(report["binding"], "primary")
        self.assertEqual(report["pause_decision"], "pause")
        self.assertTrue(any("minutes_remaining" in r for r in report["reasons"]))
        self.assertEqual(report["status"], "ok")

    def test_thresholds_overridable(self) -> None:
        # 30 minutes left pauses only when the minutes threshold is raised to 31.
        limit = probe.make_limit("primary", 10.0, 1000 + 30 * 60, now=1000)
        default = probe.build_report("zcode", [limit], now=1000)
        self.assertEqual(default["pause_decision"], "continue")
        raised = probe.build_report("zcode", [limit], minutes_threshold=31, now=1000)
        self.assertEqual(raised["pause_decision"], "pause")
        # 50% pauses only when the percent threshold is lowered to 50.
        hot = probe.make_limit("primary", 50.0, 1000 + 120 * 60, now=1000)
        strict = probe.build_report("zcode", [hot], percent_threshold=50, now=1000)
        self.assertEqual(strict["pause_decision"], "pause")


    # --- Task 2: transports, discovery, runtime detection, flag write ---

    def _write_config(self, tmp: Path, with_key: bool = True) -> Path:
        options: dict = {}
        if with_key:
            options["apiKey"] = "sk-test-raw-key"
        config = {"provider": {"zai": {"options": options}}}
        path = tmp / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def _fake_transport(self, payload_json: str):
        calls: list[dict] = []

        def transport(url: str, headers: Mapping[str, str]) -> str:
            calls.append({"url": url, "headers": dict(headers)})
            return payload_json

        return transport, calls

    def test_zcode_fetch_via_injected_transport(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            payload = ZCODE_FIXTURE.read_text(encoding="utf-8")
            transport, calls = self._fake_transport(payload)
            report = probe.probe_zcode(
                config_path=config,
                url="https://api.z.ai/api/quota/limit-test",
                transport=transport,
                now=1789146000 - 12 * 60,
            )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(calls), 1)
        headers = calls[0]["headers"]
        # Raw key in Authorization; no Bearer prefix.
        self.assertEqual(headers.get("Authorization"), "sk-test-raw-key")
        self.assertEqual(len(report["limits"]), 2)
        self.assertEqual(report["binding"], "primary")

    def test_zcode_missing_key_fail_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir), with_key=False)
            transport, calls = self._fake_transport("{}")
            report = probe.probe_zcode(config_path=config, transport=transport)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertTrue(report["reasons"])
        self.assertEqual(calls, [])

    def test_zcode_transport_error_fail_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))

            def failing_transport(url: str, headers: Mapping[str, str]) -> str:
                raise OSError("connection refused")

            report = probe.probe_zcode(config_path=config, transport=failing_transport)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertTrue(report["reasons"])

    def test_codex_rollout_discovery_newest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions = Path(tmpdir) / "sessions"
            (sessions / "2026" / "09" / "10").mkdir(parents=True)
            (sessions / "2026" / "09" / "11").mkdir(parents=True)
            for name in (
                "rollout-2026-09-10T10-00-00.jsonl",
                "rollout-2026-09-11T09-00-00.jsonl",
                "rollout-2026-09-11T18-30-00.jsonl",
            ):
                day = name.split("T")[0].removeprefix("rollout-").replace("-", "/")
                (sessions.joinpath(day, name)).write_text(
                    CODEX_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
                )
            found = probe.discover_codex_rollout(sessions)
            self.assertIsNotNone(found)
            self.assertEqual(found.name, "rollout-2026-09-11T18-30-00.jsonl")
            report = probe.probe_codex(
                sessions_dir=sessions, now=1789182137 - 40 * 60
            )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["runtime"], "codex")
        self.assertEqual(len(report["limits"]), 2)

    def test_codex_missing_rollout_fail_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions = Path(tmpdir) / "sessions"
            sessions.mkdir()
            report = probe.probe_codex(sessions_dir=sessions)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertTrue(report["reasons"])

    def test_codex_malformed_used_percent_fail_open(self) -> None:
        # A rollout record whose used_percent is non-numeric (or absent)
        # while resets_at is present must fail open to an unknown report,
        # not escape probe_codex as a traceback (fail-open parse boundary).
        for used_percent in ('"high"', None):
            with self.subTest(used_percent=used_percent):
                window = {"resets_at": int(time.time()) + 3600}
                if used_percent is not None:
                    window["used_percent"] = used_percent
                rollout = json.dumps({"rate_limits": {"primary": window}}) + "\n"
                with tempfile.TemporaryDirectory() as tmpdir:
                    sessions = Path(tmpdir) / "sessions"
                    sessions.mkdir()
                    (sessions / "rollout-2026-09-12T10-00-00.jsonl").write_text(
                        rollout, encoding="utf-8"
                    )
                    report = probe.probe_codex(sessions_dir=sessions)
            self.assertEqual(report["runtime"], "codex")
            self.assertEqual(report["status"], "unknown")
            self.assertEqual(report["pause_decision"], "continue")
            self.assertTrue(
                any("parse failed" in r for r in report["reasons"]), report["reasons"]
            )

    def test_runtime_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            zcode_config = self._write_config(tmp)
            sessions = tmp / "sessions"
            sessions.mkdir()
            self.assertEqual(
                probe.detect_runtime("codex", zcode_config=zcode_config, codex_sessions=sessions),
                "codex",
            )
            self.assertEqual(
                probe.detect_runtime("zcode", zcode_config=zcode_config, codex_sessions=sessions),
                "zcode",
            )

    def test_runtime_autodetect_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            zcode_config = self._write_config(tmp)
            sessions = tmp / "sessions"
            sessions.mkdir()
            # Both markers present: documented precedence picks zcode.
            self.assertEqual(
                probe.detect_runtime(zcode_config=zcode_config, codex_sessions=sessions),
                "zcode",
            )
            # Only codex present.
            self.assertEqual(
                probe.detect_runtime(zcode_config=tmp / "missing.json", codex_sessions=sessions),
                "codex",
            )
            # Neither present.
            self.assertIsNone(
                probe.detect_runtime(zcode_config=tmp / "missing.json", codex_sessions=tmp / "none")
            )

    def test_write_flag_writes_on_pause_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            pausing = probe.make_limit("primary", 95.0, 1000 + 10 * 60, now=1000)
            continue_limit = probe.make_limit("primary", 10.0, 1000 + 120 * 60, now=1000)
            probe.write_flag_if_paused(flag, "zcode", [pausing], "pause", plan="my-plan")
            self.assertTrue(flag.exists())
            content = flag.read_text(encoding="utf-8")
            self.assertIn("runtime=zcode", content)
            self.assertIn("reset_at_epoch={}".format(1000 + 10 * 60), content)
            self.assertIn("reset_at_iso=", content)
            self.assertIn("plan=my-plan", content)
            self.assertEqual(flag.stat().st_mode & 0o777, 0o600)
            flag.unlink()
            probe.write_flag_if_paused(flag, "zcode", [continue_limit], "continue")
            self.assertFalse(flag.exists())

    def test_secondary_binding_reports_no_schedule(self) -> None:
        early_secondary = probe.make_limit("secondary", 95.0, 1000 + 10 * 60, now=1000)
        late_primary = probe.make_limit("primary", 10.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [early_secondary, late_primary], now=1000)
        report = probe.add_secondary_report_only_reason(report)
        self.assertEqual(report["binding"], "secondary")
        self.assertTrue(
            any("secondary" in r and "same-day" in r for r in report["reasons"])
        )

    def test_secondary_binding_pause_writes_no_flag(self) -> None:
        # Report-only must be real: a weekly secondary window pauses the
        # decision but must NOT arm the host-global guard flag.
        early_secondary = probe.make_limit("secondary", 95.0, 1000 + 10 * 60, now=1000)
        late_primary = probe.make_limit("primary", 10.0, 1000 + 120 * 60, now=1000)
        report = probe.add_secondary_report_only_reason(
            probe.build_report("zcode", [early_secondary, late_primary], now=1000)
        )
        self.assertEqual(report["pause_decision"], "pause")
        self.assertTrue(any("secondary" in r for r in report["reasons"]))
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            written = probe.write_flag_if_paused(
                flag, "zcode", report["limits"], report["pause_decision"]
            )
            self.assertFalse(written)
            self.assertFalse(flag.exists())

    # --- CLI-level wiring: main() exit codes and --write-flag ---

    def _run_cli(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/quota_window_probe.py"), *extra],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_cli_continue_exits_one_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            sessions = tmp / "sessions"
            sessions.mkdir()
            flag = tmp / "budget-guard.flag"
            result = self._run_cli(
                "--runtime", "codex",
                "--config", str(tmp / "missing-config.json"),
                "--sessions-dir", str(sessions),
                "--write-flag", str(flag),
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["pause_decision"], "continue")
            self.assertEqual(report["status"], "unknown")
            self.assertFalse(flag.exists())

    def test_cli_pause_exits_zero_and_writes_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            sessions = tmp / "sessions" / "2026" / "09" / "12"
            sessions.mkdir(parents=True)
            resets = int(time.time()) + 3600
            rollout = (
                '{"rate_limits": {"primary": {"used_percent": 50, "resets_at": %d}, '
                '"secondary": {"used_percent": 10, "resets_at": %d}}}\n'
                % (resets, resets + 5 * 86400)
            )
            (sessions / "rollout-2026-09-12T10-00-00.jsonl").write_text(
                rollout, encoding="utf-8"
            )
            flag = tmp / "budget-guard.flag"
            result = self._run_cli(
                "--runtime", "codex",
                "--minutes-before", "999",
                "--config", str(tmp / "missing-config.json"),
                "--sessions-dir", str(sessions.parent),
                "--write-flag", str(flag),
                "--plan", "my-plan",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["pause_decision"], "pause")
            self.assertEqual(report["binding"], "primary")
            self.assertTrue(flag.exists())
            content = flag.read_text(encoding="utf-8")
            self.assertIn("runtime=codex", content)
            self.assertIn("plan=my-plan", content)

    def test_cli_nul_config_path_fails_open_without_traceback(self) -> None:
        # A NUL byte in the --config path can make detect_runtime raise
        # (ValueError from the embedded NUL, version-dependent) before any
        # probe runs; main() must fail open with a JSON unknown report on
        # stdout, never a traceback. NUL cannot cross a real exec argv, and
        # newer pathlib swallows the ValueError inside .exists(), so the
        # detection failure is injected at the detect_runtime boundary while
        # the NUL path still flows through argv parsing.
        out = io.StringIO()
        with mock.patch.object(
            probe, "detect_runtime", side_effect=ValueError("embedded null byte")
        ), contextlib.redirect_stdout(out):
            code = probe.main(["--config", "/tmp/\x00missing.json"])
        self.assertEqual(code, 1)
        report = json.loads(out.getvalue())
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertTrue(
            any("runtime detection failed" in r for r in report["reasons"]),
            report["reasons"],
        )


if __name__ == "__main__":
    unittest.main()
