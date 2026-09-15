#!/usr/bin/env python3
"""Hermetic tests for the quota window probe pure core (parsing, binding, thresholds)."""

from __future__ import annotations

import contextlib
import gc
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from typing import Mapping
import unittest
import urllib.request
import warnings
from unittest import mock

import quota_window_probe as probe

ROOT = Path(__file__).resolve().parents[1]
QUOTA_DIR = ROOT / "scripts/testdata/quota"
ZCODE_FIXTURE = QUOTA_DIR / "zcode_limit_response.json"
CODEX_FIXTURE = QUOTA_DIR / "codex_rollout.jsonl"

# Review r4 F1: flag-content assertions parse through the REAL hook core,
# not a reimplementation of its contract.
sys.path.insert(0, str(ROOT / "agents/hooks/budget-guard"))
import budget_guard_core  # noqa: E402


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

    def test_zcode_default_url_targets_monitor_endpoint(self) -> None:
        # The legacy api/quota/limit path answers 404-NOT_FOUND inside HTTP
        # 200; the live monitor endpoint (extracted from the ZCode desktop
        # app bundle) is the only supported default.
        self.assertEqual(
            probe.ZCODE_QUOTA_URL,
            "https://api.z.ai/api/monitor/usage/quota/limit",
        )

    def test_zcode_default_url_reaches_transport(self) -> None:
        # Review r1 F8, widened r2 F6: pins the default-parameter WIRING at
        # the two in-process call sites driven below (probe_zcode and
        # run_probe, both called with NO url=), not just the constant
        # value. The argparse --url default (the production entry surface)
        # is pinned separately by test_cli_zcode_default_url_reaches_
        # transport (review r3 F5), which drives main() itself. A
        # refactor that rebinds any pinned default site to a legacy
        # literal fails one of these even while the constant itself stays
        # correct.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            payload = ZCODE_FIXTURE.read_text(encoding="utf-8")
            transport, calls = self._fake_transport(payload)
            report = probe.probe_zcode(
                config_path=config,
                transport=transport,
                now=1789146000 - 12 * 60,
            )
            self.assertEqual(calls[0]["url"], probe.ZCODE_QUOTA_URL)
            self.assertEqual(
                calls[0]["url"], "https://api.z.ai/api/monitor/usage/quota/limit"
            )
            self.assertEqual(report["status"], "ok")
            # Same recording transport through run_probe with no url=:
            # pins run_probe's default-parameter wiring too (sessions_dir
            # is unused on the zcode leg but passed for hermeticity).
            run_transport, run_calls = self._fake_transport(payload)
            run_report = probe.run_probe(
                "zcode",
                config_path=config,
                sessions_dir=tmpdir,
                transport=run_transport,
                now=1789146000 - 12 * 60,
            )
        self.assertEqual(run_calls[0]["url"], probe.ZCODE_QUOTA_URL)
        self.assertEqual(
            run_calls[0]["url"], "https://api.z.ai/api/monitor/usage/quota/limit"
        )
        self.assertEqual(run_report["status"], "ok")

    def test_default_transport_opener_has_no_redirect_handler(self) -> None:
        # Review r1 F1, structural pin updated by r2 F9: the opener must
        # never FOLLOW a redirect. Since the r2 F9 idiom swap the opener
        # carries an HTTPRedirectHandler subclass whose redirect_request
        # returns None (the documented replacement idiom); pin that the
        # only redirect handler installed is that subclass and that it
        # refuses every redirect. Behavioral witness:
        # test_zcode_transport_never_follows_redirects.
        redirect_handlers = [
            handler
            for handler in probe._OPENER_NO_REDIRECTS.handlers
            if isinstance(handler, urllib.request.HTTPRedirectHandler)
        ]
        self.assertEqual(len(redirect_handlers), 1)
        self.assertIsInstance(redirect_handlers[0], probe._NoRedirectHandler)
        self.assertIsNone(
            redirect_handlers[0].redirect_request(
                None, None, 302, "Found", {}, "https://example.invalid/quota"
            )
        )

    def test_zcode_transport_never_follows_redirects(self) -> None:
        # Review r1 F1, behavioral witness: a 3xx from the endpoint must
        # fail open to status unknown and the Authorization header must
        # never reach the redirect target. Hermetic: two loopback servers;
        # the first answers 302 pointing at the second, which records any
        # request that arrives. Ambient proxy configuration is pinned
        # (review r2 F2): the opener is rebuilt while
        # urllib.request.getproxies returns an empty mapping, so the run
        # exercises redirect rejection, not the host's proxy environment
        # or macOS system proxies (reproduced with a single env var).
        hits: list[dict] = []

        class TargetHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                hits.append(dict(self.headers))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *args: object) -> None:
                pass

        class RedirectingHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(302)
                self.send_header("Location", target_url + self.path)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        target_srv = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
        redirect_srv = ThreadingHTTPServer(("127.0.0.1", 0), RedirectingHandler)
        target_url = "http://127.0.0.1:{}/quota".format(target_srv.server_address[1])
        for srv in (target_srv, redirect_srv):
            threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = self._write_config(Path(tmpdir))
                with mock.patch.object(urllib.request, "getproxies", lambda: {}):
                    with mock.patch.object(
                        probe,
                        "_OPENER_NO_REDIRECTS",
                        probe._build_no_redirect_opener(),
                    ):
                        # Review r4 F2, reshaped (plan Task 2):
                        # ResourceWarning witness for the r3 F9 exc.close()
                        # branch. The plain escalation is vacuous on
                        # python 3.14 (mutation-verified 2026-09-14): a
                        # warning-as-error raised inside the HTTPError body
                        # destructor becomes an unraisable that never
                        # propagates to the gc.collect() call site. The
                        # witness therefore records unraisables:
                        # sys.unraisablehook is swapped for a list-appending
                        # recorder across BOTH the probe call and the forced
                        # collection pass, and the trailing assertion fails
                        # when any recorded unraisable is a ResourceWarning.
                        # On 3.14 the HTTPError body is tempfile-backed, so
                        # the recorded warning surfaces through
                        # _TemporaryFileCloser.__del__ as "Implicitly
                        # cleaning up <HTTPError ...>". The transport closes
                        # the error, so the intact branch records nothing.
                        _unraisables: list = []
                        _orig_hook = sys.unraisablehook
                        with warnings.catch_warnings():
                            warnings.simplefilter("error", ResourceWarning)
                            sys.unraisablehook = _unraisables.append
                            try:
                                report = probe.probe_zcode(
                                    config_path=config,
                                    url="http://127.0.0.1:{}/quota".format(
                                        redirect_srv.server_address[1]
                                    ),
                                    transport=probe.urllib_transport,
                                    now=time.time(),
                                )
                                gc.collect()
                            finally:
                                sys.unraisablehook = _orig_hook
        finally:
            for srv in (target_srv, redirect_srv):
                srv.shutdown()
                srv.server_close()
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertTrue(any("302" in r for r in report["reasons"]), report["reasons"])
        # The credential must never reach the redirect target.
        self.assertEqual(hits, [])
        # Review r1 F6, accepted surface (no behavior change): any
        # in-window ResourceWarning unraisable counts as a failure. The
        # recorder is deliberately not scoped to the probe's own objects,
        # so foreign garbage collected inside the window would fail loudly
        # by design; the recorded unraisable names its source, keeping a
        # future flake diagnosable without weakening the assertion.
        self.assertFalse(any(u.exc_type is ResourceWarning for u in _unraisables), [str(u) for u in _unraisables])

    def test_parse_zcode_clamps_implausible_reset_horizon(self) -> None:
        # Review r1 F2: a hostile or buggy reset beyond the clamp horizon
        # must not arm an unbounded host-global lockout; it is clamped to
        # now + MAX_RESET_HORIZON_SECONDS (40 days: covers the observed
        # monthly-scale secondary window in the live payload, about 26 days
        # out; an 8-day bound would clamp that benign data).
        now = 1789146000
        payload = {"data": {"limits": [
            {
                "type": "TOKENS_LIMIT",
                "percentage": 62,
                "nextResetTime": (now + 100 * 86400) * 1000,
            },
        ]}}
        limits = probe.parse_zcode_limits(payload, now=now)
        self.assertEqual(len(limits), 1)
        self.assertEqual(
            limits[0]["reset_at_epoch"], now + probe.MAX_RESET_HORIZON_SECONDS
        )

    def test_clamped_reset_is_observable_in_report_reasons(self) -> None:
        # Review r2 F7: an engaged horizon clamp must not silently present
        # now + 40 days as the provider's real reset; the limit carries a
        # reset_clamped marker and build_report appends a reason so the
        # report and the manifest note can observe the clamp.
        now = 1789146000
        payload = {"data": {"limits": [
            {
                "type": "TOKENS_LIMIT",
                "percentage": 95,
                "nextResetTime": (now + 100 * 86400) * 1000,
            },
        ]}}
        limits = probe.parse_zcode_limits(payload, now=now)
        self.assertTrue(limits[0].get("reset_clamped"))
        report = probe.build_report("zcode", limits, now=now)
        self.assertTrue(
            any("clamped" in reason for reason in report["reasons"]),
            report["reasons"],
        )

    def test_parse_zcode_unrepresentable_epoch_drops_entry_alone(self) -> None:
        # Review r2 F3: limit CONSTRUCTION sits inside the per-entry guard.
        # An epoch datetime cannot represent (negative value, year outside
        # 1..9999) or a non-mapping list element drops its own entry
        # instead of aborting the whole parse (which blinded both windows
        # to status unknown). Review r3 F2 adds the two remaining escape
        # shapes: an OSError-band epoch (datetime.fromtimestamp raises
        # OSError, not ValueError, roughly one magnitude beyond the
        # year-range band) and an unhashable ``type`` (the kind-map
        # lookup previously sat outside every guard).
        now = 1789146000
        good = {
            "type": "TIME_LIMIT",
            "percentage": 2,
            "nextResetTime": (now + 3600) * 1000,
        }
        bad_epoch = {
            "type": "TOKENS_LIMIT",
            "percentage": 62,
            "nextResetTime": -(10 ** 15),
        }
        limits = probe.parse_zcode_limits(
            {"data": {"limits": [bad_epoch, good]}}, now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        limits = probe.parse_zcode_limits(
            {"data": {"limits": ["garbage", good]}}, now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        # Review r3 F2: an epoch in the OSError band (platform localtime
        # failure) drops alone while the healthy sibling survives.
        oserror_epoch = {
            "type": "TOKENS_LIMIT",
            "percentage": 62,
            "nextResetTime": -(10 ** 20),
        }
        limits = probe.parse_zcode_limits(
            {"data": {"limits": [oserror_epoch, good]}}, now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        # Review r3 F2: an unhashable (list-typed) ``type`` drops alone
        # instead of aborting the whole parse at the kind-map lookup.
        unhashable_type = {
            "type": ["TOKENS_LIMIT"],
            "percentage": 62,
            "nextResetTime": (now + 7200) * 1000,
        }
        limits = probe.parse_zcode_limits(
            {"data": {"limits": [unhashable_type, good]}}, now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])

    def test_parse_zcode_drops_out_of_domain_entries_only(self) -> None:
        # Review r1 F2: non-finite or out-of-range percentages (and a
        # malformed epoch) drop ONLY their own entry; the healthy sibling
        # limit still parses, so one bad field cannot blind the whole gate.
        now = 1789146000
        good = {
            "type": "TIME_LIMIT",
            "percentage": 2,
            "nextResetTime": (now + 3600) * 1000,
        }
        for bad_percent in (150, -5, float("nan"), float("inf"), "1e400"):
            with self.subTest(bad_percent=bad_percent):
                bad = {
                    "type": "TOKENS_LIMIT",
                    "percentage": bad_percent,
                    "nextResetTime": (now + 7200) * 1000,
                }
                limits = probe.parse_zcode_limits(
                    {"data": {"limits": [bad, good]}}, now=now
                )
                self.assertEqual(
                    [limit["kind"] for limit in limits], ["secondary"]
                )
        # A malformed epoch string drops its entry alone, too.
        bad_epoch = {
            "type": "TOKENS_LIMIT",
            "percentage": 62,
            "nextResetTime": "soon",
        }
        limits = probe.parse_zcode_limits(
            {"data": {"limits": [bad_epoch, good]}}, now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])

    def test_parse_zcode_missing_percentage_drops_only_that_entry(self) -> None:
        # Review r1 F6: the entry guard is symmetric; an entry with a type
        # and epoch but NO percentage drops alone instead of aborting both
        # limits (a single-entry defect must not degrade the whole report
        # to status unknown).
        now = 1789146000
        payload = {"data": {"limits": [
            {"type": "TOKENS_LIMIT", "nextResetTime": (now + 7200) * 1000},
            {"type": "TIME_LIMIT", "percentage": 2, "nextResetTime": (now + 3600) * 1000},
        ]}}
        limits = probe.parse_zcode_limits(payload, now=now)
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])

    def test_write_flag_refuses_epoch_beyond_horizon(self) -> None:
        # Review r1 F2 defense in depth: a direct build_report caller can
        # hand the flag writer an unclamped limit; the writer must refuse to
        # arm the host-global flag beyond the horizon (not arming is the
        # fail-open direction).
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            far = probe.make_limit(
                "primary", 95.0, int(time.time()) + 90 * 86400, now=time.time()
            )
            written = probe.write_flag_if_paused(flag, "zcode", [far], "pause")
            self.assertFalse(written)
            self.assertFalse(flag.exists())

    def test_parse_zcode_live_payload_with_extra_fields(self) -> None:
        # Characterization of the live monitor-endpoint body captured on
        # 2026-09-13: data.limits lists TIME_LIMIT (percentage 2) first and
        # TOKENS_LIMIT (percentage 62) second, plus unknown extras
        # (unit/number/usage/usageDetails/level). The parser must tolerate
        # the extra fields and identify each limit by kind, never by list
        # position; it must stay green across the URL change.
        payload = {
            "code": 200,
            "success": True,
            "data": {
                "limits": [
                    {
                        "type": "TIME_LIMIT",
                        "percentage": 2,
                        "nextResetTime": 1791551411983,
                        "unit": "TIME",
                        "number": 604800000,
                        "usage": 12096000,
                        "usageDetails": {"1p": 12096000},
                        "level": "standard",
                    },
                    {
                        "type": "TOKENS_LIMIT",
                        "percentage": 62,
                        "nextResetTime": 1789315099416,
                        "unit": "TOKENS",
                        "number": 288000000,
                        "usage": 178560000,
                        "usageDetails": {"1p": 178560000},
                        "level": "standard",
                    },
                ]
            },
        }
        limits = probe.parse_zcode_limits(payload, now=1789315099 - 3600)
        self.assertEqual(len(limits), 2)
        by_kind = {limit["kind"]: limit for limit in limits}
        self.assertEqual(sorted(by_kind), ["primary", "secondary"])
        self.assertEqual(by_kind["primary"]["used_percent"], 62.0)
        self.assertEqual(by_kind["primary"]["reset_at_epoch"], 1789315099)
        self.assertEqual(by_kind["secondary"]["used_percent"], 2.0)
        self.assertEqual(by_kind["secondary"]["reset_at_epoch"], 1791551411)

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

    def test_codex_recordless_rollout_keeps_old_reason(self) -> None:
        # A rollout with no rate_limits record at all (an unrelated JSON
        # line only) keeps the original record-less reason: there is no
        # rate_limits record whose windows could have been dropped.
        rollout = json.dumps({"type": "session_meta", "payload": {}}) + "\n"
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
        self.assertEqual(
            report["reasons"], ["rollout carried no rate_limits record"]
        )

    def test_codex_all_windows_dropped_reason_distinct(self) -> None:
        # A rollout whose only rate_limits record carries a single
        # malformed window (non-numeric used_percent) and no valid sibling
        # is an all-windows-dropped shape: its reason must be distinct
        # from the record-less case.
        rollout = json.dumps({
            "rate_limits": {
                "primary": {"used_percent": "high", "resets_at": 1789182137}
            }
        }) + "\n"
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
        self.assertEqual(
            report["reasons"],
            ["rollout rate_limits record carried no usable windows"],
        )

    def test_codex_garbage_line_with_dropped_windows_keeps_new_reason(self) -> None:
        # Review r1 F1: pins the fail-open branch for a MIXED rollout (a
        # non-JSON garbage line plus a rate_limits record whose only window
        # is malformed). The predicate's blank/unparseable-line skip must
        # keep the all-windows-dropped reason; if its try/except or
        # skip logic regressed, the garbage line would raise outside
        # probe_codex's guard or collapse to the record-less reason.
        rollout = (
            "not json at all\n"
            + json.dumps({
                "rate_limits": {
                    "primary": {"used_percent": "high", "resets_at": 1789182137}
                }
            })
            + "\n"
        )
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
        self.assertEqual(
            report["reasons"],
            ["rollout rate_limits record carried no usable windows"],
        )

    def test_codex_malformed_used_percent_fail_open(self) -> None:
        # Review r2 F3/F5: a rollout whose rate_limits window carries a
        # non-numeric (or absent, or non-finite) used_percent drops at
        # per-entry parse level; probe_codex then fails open to an unknown
        # report ("rollout rate_limits record carried no usable windows"),
        # never a traceback.
        resets = int(time.time()) + 3600
        for used_percent in ('"high"', None, "Infinity"):
            with self.subTest(used_percent=used_percent):
                if used_percent == "Infinity":
                    # Raw non-standard JSON literal: json.loads accepts it
                    # and parses it to a non-finite float.
                    rollout = (
                        '{"rate_limits": {"primary": {"used_percent": Infinity, '
                        '"resets_at": %d}}}\n' % resets
                    )
                else:
                    window: dict = {"resets_at": resets}
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
                self.assertEqual(
                    report["reasons"],
                    ["rollout rate_limits record carried no usable windows"],
                )
        # Per-entry, not whole-parse: a healthy sibling window survives a
        # malformed primary and the report stays ok.
        rollout = json.dumps({"rate_limits": {
            "primary": {"used_percent": "high", "resets_at": resets},
            "secondary": {"used_percent": 10.0, "resets_at": resets + 5 * 86400},
        }}) + "\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions = Path(tmpdir) / "sessions"
            sessions.mkdir()
            (sessions / "rollout-2026-09-12T10-00-00.jsonl").write_text(
                rollout, encoding="utf-8"
            )
            report = probe.probe_codex(sessions_dir=sessions)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            [limit["kind"] for limit in report["limits"]], ["secondary"]
        )

    def test_parse_codex_bad_entry_drops_alone_and_clamps(self) -> None:
        # Review r2 F3 + F5: the codex path carries the same per-entry
        # guard as the zcode path. A negative epoch drops only its own
        # window while the sibling survives; an Infinity percent drops;
        # a far-future resets_at is clamped to the 40-day horizon and
        # marked observable.
        now = 1789182137 - 40 * 60
        good = {"used_percent": 10.0, "resets_at": now + 3600}

        def rollout_lines(primary: dict) -> list[str]:
            return [
                json.dumps({"rate_limits": {"primary": primary, "secondary": good}})
            ]

        limits = probe.parse_codex_rollout(
            rollout_lines({"used_percent": 50.0, "resets_at": -(10 ** 12)}), now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        limits = probe.parse_codex_rollout(
            rollout_lines({"used_percent": float("inf"), "resets_at": now + 7200}),
            now=now,
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        limits = probe.parse_codex_rollout(
            rollout_lines({"used_percent": 95.0, "resets_at": now + 200 * 86400}),
            now=now,
        )
        self.assertEqual([limit["kind"] for limit in limits], ["primary", "secondary"])
        clamped_limit = limits[0]
        self.assertEqual(
            clamped_limit["reset_at_epoch"], now + probe.MAX_RESET_HORIZON_SECONDS
        )
        self.assertTrue(clamped_limit.get("reset_clamped"))
        self.assertFalse(limits[1].get("reset_clamped"))
        # Review r3 F2: an OSError-band epoch (platform localtime failure,
        # roughly one magnitude beyond the ValueError year-range band)
        # drops only its own window while the sibling survives.
        limits = probe.parse_codex_rollout(
            rollout_lines({"used_percent": 50.0, "resets_at": -(10 ** 17)}),
            now=now,
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])
        # Review r3 F8: the codex non-mapping-window drop arm is pinned
        # like the zcode garbage-entry case; a non-mapping primary window
        # drops alone and the healthy secondary survives.
        limits = probe.parse_codex_rollout(
            rollout_lines("high"), now=now
        )
        self.assertEqual([limit["kind"] for limit in limits], ["secondary"])

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

    def test_write_flag_plan_value_cannot_inject_flag_keys(self) -> None:
        # Review r4 F1: the plan slug is forensic metadata, never trusted
        # key material. budget_guard_core.parse_flag keeps the LAST
        # occurrence of each key, so a newline-bearing --plan value could
        # inject forged reset_at_epoch/runtime lines into the host-global
        # flag (reproduced end-to-end pre-fix: the hook parsed the injected
        # epoch as live until year 2286 with spoofed runtime). The writer
        # keeps only the plan's first line; parsed through the REAL hook
        # core, the contract keys stay the writer's originals.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            pausing = probe.make_limit("primary", 95.0, 1000 + 10 * 60, now=1000)
            self.assertTrue(probe.write_flag_if_paused(
                flag, "zcode", [pausing], "pause",
                plan="my-plan\nreset_at_epoch=9999999999\nruntime=codex",
            ))
            content = flag.read_text(encoding="utf-8")
            self.assertIn("plan=my-plan", content)
            self.assertNotIn("9999999999", content)
            self.assertEqual(content.count("runtime="), 1)
            parsed = budget_guard_core.parse_flag(content)
            self.assertEqual(parsed["runtime"], "zcode")
            # parse_flag coerces reset_at_epoch to int.
            self.assertEqual(parsed["reset_at_epoch"], 1000 + 10 * 60)
            self.assertEqual(parsed["plan"], "my-plan")

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

    # test_cli_write_flag_refusal_reason_is_observable (review r2 F5) was
    # removed in review r4 F4: it pinned main()'s "guard flag not armed"
    # else-branch, which is unreachable in the shipped CLI path (both
    # parsers clamp every limit before main() sees it) and was reachable
    # only by mocking the writer. The writer-level horizon refusal remains
    # pinned by test_write_flag_refuses_epoch_beyond_horizon.

    def test_cli_zcode_default_url_reaches_transport(self) -> None:
        # Review r3 F5: main()'s argparse --url default is the production
        # entry surface (the plan's gate command passes no --url); all
        # earlier CLI tests drove the codex rollout path, so a legacy
        # literal rebound into add_argument("--url", default=...) shipped
        # green while re-creating the silent never-pause failure. In-process
        # wiring pin: main() with an explicit zcode runtime must hand the
        # module-default URL to the default transport (patched at the
        # probe boundary, so probe_zcode's `transport = urllib_transport`
        # global lookup resolves the recording stand-in). Hermetic:
        # fixture config plus recording transport, no network.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            payload = ZCODE_FIXTURE.read_text(encoding="utf-8")
            calls: list[dict] = []

            def recording(url: str, headers: Mapping[str, str]) -> str:
                calls.append({"url": url, "headers": dict(headers)})
                return payload

            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", recording
            ), contextlib.redirect_stdout(out):
                code = probe.main(["--runtime", "zcode", "--config", str(config)])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["url"], probe.ZCODE_QUOTA_URL)
        self.assertEqual(
            calls[0]["url"], "https://api.z.ai/api/monitor/usage/quota/limit"
        )
        # Review r4 F3: an explicit --url must propagate through main() to
        # the transport. A regression to a hardcoded constant at the
        # run_probe call site shipped green before this pin (mutation-
        # proven); the recording transport answers with the fixture body
        # regardless of the URL, so the pin is the observed URL alone.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            calls.clear()
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", recording
            ), contextlib.redirect_stdout(out):
                code = probe.main([
                    "--runtime", "zcode",
                    "--config", str(config),
                    "--url", "https://example.invalid/q",
                ])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["url"], "https://example.invalid/q")
        # The fixture epochs sit in the past relative to the real clock,
        # so the report fails open to unknown/continue (exit 1); the pin
        # is the URL, not the decision.
        self.assertEqual(code, 1)

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
