#!/usr/bin/env python3
"""Hermetic tests for the quota window probe pure core (parsing, binding, thresholds)."""

from __future__ import annotations

import contextlib
import gc
import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from typing import Mapping, Optional
import unittest
import urllib.request
import warnings
from unittest import mock

import quota_window_probe as probe
import harness_detection


@contextlib.contextmanager
def _scrubbed_harness_env(extra: dict = None):
    """Scrub ZCODE_* keys and pin a hermetic ancestry for live-signal tests.

    The host may carry ZCODE_* markers (this repo's own runtime), so every
    auto-detect test scrubs them explicitly and replaces the default ps walk
    with a canned chain; no real process tree is consulted.
    """
    extra = extra or {}
    removed = {key: os.environ.pop(key) for key in list(os.environ) if key.startswith("ZCODE_")}
    with mock.patch.object(harness_detection, "_default_ancestry", lambda: []):
        for key, value in extra.items():
            os.environ[key] = value
        try:
            yield
        finally:
            for key in extra:
                os.environ.pop(key, None)
            os.environ.update(removed)

ROOT = Path(__file__).resolve().parents[1]
QUOTA_DIR = ROOT / "scripts/testdata/quota"
ZCODE_FIXTURE = QUOTA_DIR / "zcode_limit_response.json"

# --- Task 1 (P6 origins 1-2): --fire-at fixtures. 2026-09-23 is a
# Wednesday; every fixture instant is stated in the default peak zone
# UTC+8 and never pins the host's local zone. Review r1 F2: the payload-
# driven fit tests are clock-independent through an INJECTED now (FIRE_NOW_
# EPOCH below, threaded main -> _fire_at_cli -> run_probe/evaluate_fire_at),
# so these fixed fixture dates can never go stale against the host clock -
# the live-primary filter and the 40-day reset horizon both read the
# injected instant, never time.time(). The plan's Validation Commands smoke
# keeps the same 2026-09-23 dates (its pure-pricing calls consult no clock
# at all).
TZ8 = timezone(timedelta(hours=8))
FIRE_PEAK_EPOCH = int(datetime(2026, 9, 23, 15, 0, tzinfo=TZ8).timestamp())
FIRE_OFFPEAK_EPOCH = int(datetime(2026, 9, 23, 13, 0, tzinfo=TZ8).timestamp())
FIRE_WINDOW_END_EPOCH = int(datetime(2026, 9, 23, 18, 0, tzinfo=TZ8).timestamp())
# Injected clock for the payload-driven fit tests: one hour before the
# earliest fixture fire instant, so every fixture reset stays live
# (reset_at_epoch > now) and unclamped (within the 40-day horizon of now)
# regardless of when the suite runs.
FIRE_NOW_EPOCH = FIRE_OFFPEAK_EPOCH - 3600


def _native_codex_result(now: Optional[float] = None, primary: Optional[dict] = None,
                         secondary: Optional[dict] = None) -> dict:
    now = time.time() if now is None else now
    primary = primary or {
        "usedPercent": 42.0, "windowDurationMins": 300,
        "resetsAt": int(now) + 3600, "limitName": "primary",
    }
    secondary = secondary or {
        "usedPercent": 18.0, "windowDurationMins": 10080,
        "resetsAt": int(now) + 7 * 86400, "limitName": "secondary",
    }
    windows = {}
    if primary is not None:
        windows["primary"] = primary
    if secondary is not None:
        windows["secondary"] = secondary
    return {"rateLimits": windows}


def _fake_codex_environment(root: Path, result: Optional[dict] = None,
                            mode: str = "normal") -> tuple[dict, Path, Path, str]:
    """Build isolated HOME/PATH and a fake Codex app-server executable.

    The fake records requests and responds over the actual JSON-RPC stdio
    channel. A sitecustomize guard detects attempted credential-canary reads
    in both the CLI process and the fake app-server process.
    """
    home = root / "home"
    codex_home = home / ".codex"
    codex_home.mkdir(parents=True)
    credential = codex_home / "auth.json"
    secret = "test-only-codex-credential-canary"
    credential.write_text(json.dumps({"access_token": secret}), encoding="utf-8")
    fake_bin = root / "fake-bin"
    fake_bin.mkdir()
    executable = fake_bin / "codex"
    audit = root / "fake-app-server.json"
    read_attempt = root / "credential-read-attempted"
    fake_program = """import json, os, pathlib, sys, time
events = []
def record():
    pathlib.Path(os.environ['FAKE_CODEX_AUDIT']).write_text(json.dumps({
        'argv': sys.argv, 'home': os.environ.get('HOME'), 'events': events,
        'pid': os.getpid(),
    }), encoding='utf-8')
mode = os.environ.get('FAKE_CODEX_MODE', 'normal')
for raw in sys.stdin:
    request = json.loads(raw)
    events.append(request)
    record()
    method = request.get('method')
    if method == 'initialize':
        if mode == 'timeout':
            time.sleep(30)
        response_id = 99 if mode == 'bad-init-id' else request['id']
        print(json.dumps({'id': response_id, 'result': {}}), flush=True)
    elif method == 'account/rateLimits/read':
        if mode == 'oversize':
            sys.stdout.write('x' * (1024 * 1024 + 1))
            sys.stdout.flush()
            time.sleep(30)
        elif mode == 'malformed':
            print('not-json', flush=True)
        elif mode == 'bad-quota-id':
            print(json.dumps({'id': 99, 'result': {}}), flush=True)
        elif mode == 'quota-error':
            print(json.dumps({'id': request['id'],
                              'error': {'code': -1, 'message': 'failed'}}), flush=True)
        elif mode == 'auth-error':
            print(json.dumps({'id': request['id'],
                              'error': {'code': -32001, 'message': 'unauthorized'}}), flush=True)
        else:
            payload = json.loads(os.environ['FAKE_CODEX_RESULT'])
            print(json.dumps({'id': request['id'],
                              'result': payload}), flush=True)
record()
"""
    executable.write_text("#!{}\n".format(sys.executable) + fake_program, encoding="utf-8")
    executable.chmod(0o755)
    guard = root / "python-guard"
    guard.mkdir()
    sitecustomize = """import builtins, io, os
canary = os.path.realpath(os.environ.get('CODEX_AUTH_CANARY', ''))
marker = os.environ.get('CODEX_READ_MARKER')
_open, _io_open, _os_open = builtins.open, io.open, os.open
def _check(path):
    try:
        candidate = os.path.realpath(os.fspath(path))
    except (TypeError, ValueError):
        return
    if canary and candidate == canary:
        fd = _os_open(marker, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, b'credential read attempted')
        os.close(fd)
        raise PermissionError('credential canary access denied')
def _builtins_open(path, *args, **kwargs):
    _check(path)
    return _open(path, *args, **kwargs)
def _io_open_guard(path, *args, **kwargs):
    _check(path)
    return _io_open(path, *args, **kwargs)
def _os_open_guard(path, *args, **kwargs):
    _check(path)
    return _os_open(path, *args, **kwargs)
builtins.open, io.open, os.open = _builtins_open, _io_open_guard, _os_open_guard
"""
    (guard / "sitecustomize.py").write_text(sitecustomize, encoding="utf-8")
    env = {
        "PATH": str(fake_bin), "HOME": str(home), "CODEX_HOME": str(codex_home),
        "PYTHONPATH": str(guard), "FAKE_CODEX_AUDIT": str(audit),
        "CODEX_AUTH_CANARY": str(credential), "CODEX_READ_MARKER": str(read_attempt),
        "FAKE_CODEX_RESULT": json.dumps(result or _native_codex_result()),
        "FAKE_CODEX_MODE": mode,
    }
    return env, audit, read_attempt, secret


@contextlib.contextmanager
def _forbid_credential_reads(credential: Path):
    """Fail in-process tests on any credential-path open attempt."""
    target = os.path.realpath(credential)
    builtins_open, io_open, os_open = open, io.open, os.open

    def check(path) -> None:
        try:
            candidate = os.path.realpath(os.fspath(path))
        except (TypeError, ValueError):
            return
        if candidate == target:
            raise AssertionError("quota probe attempted to read Codex credentials")

    def guard_builtins(path, *args, **kwargs):
        check(path)
        return builtins_open(path, *args, **kwargs)

    def guard_io(path, *args, **kwargs):
        check(path)
        return io_open(path, *args, **kwargs)

    def guard_os(path, *args, **kwargs):
        check(path)
        return os_open(path, *args, **kwargs)

    with mock.patch("builtins.open", guard_builtins), \
         mock.patch("io.open", guard_io), \
         mock.patch("os.open", guard_os):
        yield

# Review r4 F1: flag-content assertions parse through the REAL hook core,
# not a reimplementation of its contract.
sys.path.insert(0, str(ROOT / "agents/hooks/budget-guard"))
import budget_guard_core  # noqa: E402

# The canonical shared-guard-lock contract lives in the watcher module; the
# replacement-interleaving witness below proves the probe writer, the hook
# cleanup, and the watcher cleanup all serialize on the same lock file.
sys.path.insert(0, str(ROOT / "scripts"))
import execute_plan_resume_watcher as resume_watcher  # noqa: E402


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

    def test_parse_codex_native_account_rate_limits(self) -> None:
        now = 1_789_182_137 - 40 * 60
        payload = _native_codex_result(
            now=now,
            primary={"usedPercent": 4.0, "windowDurationMins": 300,
                     "resetsAt": 1_789_182_137, "limitName": "primary"},
            secondary={"usedPercent": 96.0, "windowDurationMins": 10080,
                       "resetsAt": 1_789_577_839, "limitName": "secondary"},
        )
        limits = probe.parse_codex_rate_limits({"jsonrpc": "2.0", "id": 2,
                                                "result": payload}, now=now)
        self.assertEqual(len(limits), 2)
        self.assertEqual(
            [(item["kind"], item["used_percent"], item["window_minutes"],
              item["reset_at_epoch"]) for item in limits],
            [("primary", 4.0, 300, 1_789_182_137),
             ("secondary", 96.0, 10080, 1_789_577_839)],
        )

    def test_codex_naive_reset_timestamp_keeps_quota_unknown(self) -> None:
        now = 1_789_182_137
        naive_reset = datetime.fromtimestamp(
            now + 3600, timezone.utc
        ).replace(tzinfo=None).isoformat()
        payload = _native_codex_result(
            now=now,
            primary={"usedPercent": 4.0, "windowDurationMins": 300,
                     "resetsAt": naive_reset},
        )

        report = probe.probe_codex(now=now, transport=lambda: payload)

        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["limits"], [])
        self.assertIn("no usable primary window", " ".join(report["reasons"]))

        aware_reset = datetime.fromtimestamp(
            now + 3600, timezone.utc
        ).isoformat().replace("+00:00", "Z")
        aware_limits = probe.parse_codex_rate_limits(
            {"rateLimits": {"primary": {
                "usedPercent": 4.0, "resetsAt": aware_reset,
            }}},
            now=now,
        )
        self.assertEqual(len(aware_limits), 1)
        self.assertEqual(aware_limits[0]["reset_at_epoch"], now + 3600)

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
        # Same mix but the live window is hot and its reset is 5 minutes
        # out: the live window still decides, and as a pause candidate with
        # an imminent reset it rides through as wait-for-reset.
        hot_live = probe.make_limit("primary", 95.0, 1000 + 5 * 60, now=1000)
        hot = probe.build_report("zcode", [expired, hot_live], now=1000)
        self.assertEqual(hot["pause_decision"], "wait-for-reset")
        self.assertEqual(hot["wait_minutes"], 7)

    def test_pause_decision_minutes_boundary(self) -> None:
        exactly = probe.build_report(
            "zcode", [probe.make_limit("primary", 10.0, 1000 + 20 * 60, now=1000)], now=1000
        )
        self.assertEqual(exactly["pause_decision"], "continue")
        # Usage gate first: 19 minutes below the minutes-before threshold
        # with low usage is a continue; clock proximity alone never pauses.
        below = probe.build_report(
            "zcode", [probe.make_limit("primary", 10.0, 1000 + 19 * 60, now=1000)], now=1000
        )
        self.assertEqual(below["pause_decision"], "continue")
        # A pause candidate inside the imminence band rides through:
        # wait-for-reset with a 21-minute wait, never a pause.
        hot_below = probe.build_report(
            "zcode", [probe.make_limit("primary", 92.0, 1000 + 19 * 60, now=1000)], now=1000
        )
        self.assertEqual(hot_below["pause_decision"], "wait-for-reset")
        self.assertEqual(hot_below["wait_minutes"], 21)

    def test_pause_decision_percent_boundary(self) -> None:
        exactly = probe.build_report(
            "zcode", [probe.make_limit("primary", 90.0, 1000 + 120 * 60, now=1000)], now=1000
        )
        self.assertEqual(exactly["pause_decision"], "pause")
        under = probe.build_report(
            "zcode", [probe.make_limit("primary", 89.0, 1000 + 120 * 60, now=1000)], now=1000
        )
        self.assertEqual(under["pause_decision"], "continue")

    def test_low_usage_imminent_reset_never_pauses(self) -> None:
        # The witnessed misfire: 15 percent used with 10 minutes to the
        # five-hour reset (exactly the default protocol margin) must
        # continue - clock proximity with low usage never pauses.
        report = probe.build_report(
            "zcode", [probe.make_limit("primary", 15.0, 1000 + 10 * 60, now=1000)], now=1000
        )
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual(report["reasons"], [])

    def test_high_usage_unfit_wave_pauses(self) -> None:
        # 92 percent used (at or above the 90 default) with a 50-percent
        # next wave against 8 remaining: the wave cannot fit the remaining
        # quota, the reset is 240 minutes out, so the decision is a pause.
        report = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 92.0, 1000 + 240 * 60, now=1000)],
            now=1000,
            plan_cost_percent=50.0,
        )
        self.assertEqual(report["pause_decision"], "pause")
        self.assertTrue(
            any("used_percent" in r for r in report["reasons"]), report["reasons"]
        )

    def test_high_usage_imminent_reset_waits_for_reset(self) -> None:
        # 92 percent used, 15 minutes to reset (below the 20-minute
        # threshold): the gate rides through as wait-for-reset with a
        # 17-minute in-session wait, never a pause.
        report = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 92.0, 1000 + 15 * 60, now=1000)],
            now=1000,
        )
        self.assertEqual(report["pause_decision"], "wait-for-reset")
        self.assertEqual(report["wait_minutes"], 17)
        self.assertNotEqual(report["pause_decision"], "pause")

    def test_usage_gate_fit_arm_alone_pauses(self) -> None:
        # 80 percent (below the 90 threshold) with a 95-percent wave
        # against 20 remaining: the fit arm alone is a pause candidate, and
        # with the reset 240 minutes out it resolves a pause (quota, not
        # time).
        report = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 80.0, 1000 + 240 * 60, now=1000)],
            now=1000,
            plan_cost_percent=95.0,
        )
        self.assertEqual(report["pause_decision"], "pause")

    def test_fit_arm_float_residue_exact_fit_continues(self) -> None:
        # Review r1 F1: fractional percents that exactly exhaust the window
        # (78.2 + 21.8 = 100.0 in true arithmetic) must continue - the raw
        # float 100.0 - 78.2 leaves a residue below 21.8, so the fit
        # comparison tolerates IEEE-754 residue - while a genuinely larger
        # wave (21.9) still pauses through the same fit arm.
        report = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 78.2, 1000 + 240 * 60, now=1000)],
            now=1000,
            plan_cost_percent=21.8,
        )
        self.assertEqual(report["pause_decision"], "continue")
        unfit = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 78.2, 1000 + 240 * 60, now=1000)],
            now=1000,
            plan_cost_percent=21.9,
        )
        self.assertEqual(unfit["pause_decision"], "pause")
        self.assertTrue(
            any("does not fit remaining quota" in r for r in unfit["reasons"]),
            unfit["reasons"],
        )

    def test_wait_for_reset_report_carries_wait_minutes(self) -> None:
        # The wait-for-reset report carries wait_minutes (minutes remaining
        # plus the two-minute buffer); a continue report carries no
        # wait_minutes key at all.
        waiting = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 92.0, 1000 + 15 * 60, now=1000)],
            now=1000,
        )
        self.assertEqual(waiting["pause_decision"], "wait-for-reset")
        self.assertEqual(waiting["wait_minutes"], 17)
        continuing = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 15.0, 1000 + 15 * 60, now=1000)],
            now=1000,
        )
        self.assertEqual(continuing["pause_decision"], "continue")
        self.assertNotIn("wait_minutes", continuing)

    def test_imminence_boundary_is_strict(self) -> None:
        # 92 percent at exactly the minutes-before threshold (20 with
        # defaults) pauses: at-threshold is NOT imminent (strict <), and a
        # regression to at-or-below flips this test to wait-for-reset.
        report = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 92.0, 1000 + 20 * 60, now=1000)],
            now=1000,
        )
        self.assertEqual(report["pause_decision"], "pause")

    def test_build_report_contract(self) -> None:
        limit = probe.make_limit("primary", 87.5, 1000 + 12 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000)
        self.assertEqual(
            sorted(report),
            sorted(["runtime", "limits", "binding", "pause_decision", "reasons", "status"]),
        )
        self.assertEqual(report["runtime"], "zcode")
        self.assertEqual(report["binding"], "primary")
        # Usage gate first: 87.5 percent is below the 90 threshold, so the
        # 12-minute proximity is a continue.
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual(report["status"], "ok")
        # The pause assertion moved to a high-usage, non-imminent case: the
        # report contract keys are identical, only the decision differs.
        pausing = probe.build_report(
            "zcode",
            [probe.make_limit("primary", 92.0, 1000 + 240 * 60, now=1000)],
            now=1000,
        )
        self.assertEqual(
            sorted(pausing),
            sorted(["runtime", "limits", "binding", "pause_decision", "reasons", "status"]),
        )
        self.assertEqual(pausing["pause_decision"], "pause")
        self.assertTrue(any("used_percent" in r for r in pausing["reasons"]))

    def test_thresholds_overridable(self) -> None:
        # The minutes threshold sets imminence for a pause candidate: 92
        # percent with 30 minutes left pauses under the default threshold
        # (not imminent) but rides through as wait-for-reset when the
        # threshold is raised to 31.
        limit = probe.make_limit("primary", 92.0, 1000 + 30 * 60, now=1000)
        default = probe.build_report("zcode", [limit], now=1000)
        self.assertEqual(default["pause_decision"], "pause")
        raised = probe.build_report("zcode", [limit], minutes_threshold=31, now=1000)
        self.assertEqual(raised["pause_decision"], "wait-for-reset")
        self.assertEqual(raised["wait_minutes"], 32)
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
            # Same recording transport through run_probe with no url= pins
            # the ZCode routing default without engaging Codex.
            run_transport, run_calls = self._fake_transport(payload)
            run_report = probe.run_probe(
                "zcode",
                config_path=config,
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

    def test_zcode_primary_is_required_with_valid_primary_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config = self._write_config(root)
            now = time.time()
            secondary_only = {"data": {"limits": [{
                "type": "TIME_LIMIT", "percentage": 10,
                "nextResetTime": int((now + 7 * 86400) * 1000),
            }]}}
            expired_primary_live_secondary = {"data": {"limits": [
                {
                    "type": "TOKENS_LIMIT", "percentage": 10,
                    "nextResetTime": int((now - 1) * 1000),
                },
                secondary_only["data"]["limits"][0],
            ]}}
            valid_primary = {"data": {"limits": [{
                "type": "TOKENS_LIMIT", "percentage": 10,
                "nextResetTime": int((now + 3600) * 1000),
            }]}}
            malformed_primary = {"data": {"limits": [
                {
                    "type": "TOKENS_LIMIT", "percentage": "invalid",
                    "nextResetTime": int((now + 3600) * 1000),
                },
                secondary_only["data"]["limits"][0],
            ]}}
            boolean_primary = {"data": {"limits": [{
                "type": "TOKENS_LIMIT", "percentage": True,
                "nextResetTime": int((now + 3600) * 1000),
            }]}}
            missing_primary = probe.probe_zcode(
                config_path=config,
                transport=lambda *_: json.dumps(secondary_only), now=now,
            )
            expired_primary = probe.probe_zcode(
                config_path=config,
                transport=lambda *_: json.dumps(expired_primary_live_secondary), now=now,
            )
            bad_primary = probe.probe_zcode(
                config_path=config,
                transport=lambda *_: json.dumps(malformed_primary), now=now,
            )
            boolean_percent = probe.probe_zcode(
                config_path=config,
                transport=lambda *_: json.dumps(boolean_primary), now=now,
            )
            with_primary = probe.probe_zcode(
                config_path=config,
                transport=lambda *_: json.dumps(valid_primary), now=now,
            )
        self.assertEqual(missing_primary["status"], "unknown")
        self.assertEqual(missing_primary["limits"], [])
        self.assertEqual(expired_primary["status"], "unknown")
        self.assertEqual(expired_primary["limits"], [])
        self.assertEqual(bad_primary["status"], "unknown")
        self.assertEqual(bad_primary["limits"], [])
        self.assertEqual(boolean_percent["status"], "unknown")
        self.assertEqual(boolean_percent["limits"], [])
        self.assertEqual(with_primary["status"], "ok")
        self.assertEqual([limit["kind"] for limit in with_primary["limits"]], ["primary"])
        self.assertEqual(with_primary["source"], "zcode-quota-endpoint")
        self.assertIn("observed_at_epoch", with_primary)

        response_time = now + 20
        clock = mock.Mock(return_value=now)
        expires_during_fetch = {"data": {"limits": [
            {
                "type": "TOKENS_LIMIT", "percentage": 10,
                "nextResetTime": int((now + 10) * 1000),
            },
            secondary_only["data"]["limits"][0],
        ]}}
        with tempfile.TemporaryDirectory() as response_tmpdir:
            response_config = self._write_config(Path(response_tmpdir))
            with mock.patch.object(probe, "time", mock.Mock(time=clock)):
                def slow_transport(*_args):
                    clock.return_value = response_time
                    return json.dumps(expires_during_fetch)

                expired_before_response = probe.probe_zcode(
                    config_path=response_config,
                    transport=slow_transport,
                )
        self.assertEqual(expired_before_response["status"], "unknown")
        self.assertEqual(expired_before_response["limits"], [])
        self.assertEqual(expired_before_response["observed_at_epoch"], response_time)

    def test_codex_probe_uses_fake_native_server_and_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            now = time.time()
            native = _native_codex_result(now=now)
            env, audit_path, read_attempt, secret = _fake_codex_environment(root, native)
            with mock.patch.dict(os.environ, env, clear=True), \
                 _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                report = probe.probe_codex(now=now)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["runtime"], "codex")
        self.assertEqual(report["source"], "codex-app-server/account/rateLimits/read")
        self.assertGreaterEqual(report["observed_at_epoch"], now)
        self.assertEqual(
            [(item["kind"], item["window_minutes"]) for item in report["limits"]],
            [("primary", 300), ("secondary", 10080)],
        )
        self.assertEqual([event.get("method") for event in audit["events"]], [
            "initialize", "initialized", "account/rateLimits/read",
        ])
        self.assertEqual([event.get("id") for event in audit["events"]], [1, None, 2])
        self.assertTrue(all("jsonrpc" not in event for event in audit["events"]))
        self.assertEqual(audit["argv"][1], "app-server")
        self.assertEqual(audit["home"], env["HOME"])
        self.assertEqual(Path(audit["argv"][0]).resolve(), (Path(env["PATH"]) / "codex").resolve())
        self.assertNotIn(secret, json.dumps(audit["events"]))
        self.assertFalse(read_attempt.exists())
        with self.assertRaises(ProcessLookupError):
            os.kill(audit["pid"], 0)

    def test_codex_primary_is_required_and_bad_secondary_is_diagnostic(self) -> None:
        now = time.time()
        good = _native_codex_result(now=now)
        secondary_only = {"rateLimits": {"secondary": good["rateLimits"]["secondary"]}}
        expired_primary_live_secondary = {"rateLimits": {
            "primary": {
                "usedPercent": 10, "windowDurationMins": 300,
                "resetsAt": int(now) - 1,
            },
            "secondary": good["rateLimits"]["secondary"],
        }}
        invalid_primary = {"rateLimits": {
            "primary": {"usedPercent": "bad", "windowDurationMins": 300,
                        "resetsAt": int(now) + 3600},
            "secondary": good["rateLimits"]["secondary"],
        }}
        malformed_secondary = {"rateLimits": {
            "primary": good["rateLimits"]["primary"],
            "secondary": {"usedPercent": "bad", "windowDurationMins": 10080,
                          "resetsAt": int(now) + 7 * 86400},
        }}
        boolean_primary = {"rateLimits": {
            "primary": {"usedPercent": True, "windowDurationMins": 300,
                        "resetsAt": int(now) + 3600},
        }}
        for payload in (secondary_only, invalid_primary, boolean_primary,
                        expired_primary_live_secondary):
            with self.subTest(payload=payload):
                report = probe.probe_codex(now=now, transport=lambda p=payload: p)
                self.assertEqual(report["status"], "unknown")
                self.assertEqual(report["limits"], [])
        report = probe.probe_codex(now=now, transport=lambda: malformed_secondary)
        self.assertEqual(report["status"], "ok")
        self.assertEqual([limit["kind"] for limit in report["limits"]], ["primary"])
        self.assertTrue(any("secondary window omitted" in reason for reason in report["reasons"]))

        for duration in (True, 1.5):
            with self.subTest(duration=duration):
                malformed_duration = {"rateLimits": {
                    "primary": {
                        **good["rateLimits"]["primary"],
                        "windowDurationMins": duration,
                    },
                }}
                report = probe.probe_codex(
                    now=now, transport=lambda p=malformed_duration: p,
                )
                self.assertEqual(report["status"], "ok")
                self.assertEqual([limit["kind"] for limit in report["limits"]], ["primary"])
                self.assertNotIn("window_minutes", report["limits"][0])

        oversized_secondary = {"rateLimits": {
            "primary": good["rateLimits"]["primary"],
            "secondary": {"usedPercent": 40, "windowDurationMins": 10080,
                          "resetsAt": 10**1000},
        }}
        report = probe.probe_codex(now=now, transport=lambda: oversized_secondary)
        self.assertEqual(report["status"], "ok")
        self.assertEqual([limit["kind"] for limit in report["limits"]], ["primary"])
        self.assertTrue(any("secondary window omitted" in reason for reason in report["reasons"]))

        response_time = now + 20
        clock = mock.Mock(return_value=now)
        expires_during_fetch = {"rateLimits": {
            "primary": {
                "usedPercent": 10, "windowDurationMins": 300,
                "resetsAt": int(now) + 10,
            },
            "secondary": good["rateLimits"]["secondary"],
        }}
        with mock.patch.object(probe, "time", mock.Mock(time=clock)):
            def slow_transport():
                clock.return_value = response_time
                return expires_during_fetch

            expired_before_response = probe.probe_codex(transport=slow_transport)
        self.assertEqual(expired_before_response["status"], "unknown")
        self.assertEqual(expired_before_response["limits"], [])
        self.assertEqual(expired_before_response["observed_at_epoch"], response_time)

    def test_codex_protocol_failures_return_unknown_and_clean_up(self) -> None:
        for mode in ("bad-init-id", "bad-quota-id", "malformed", "quota-error", "auth-error"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                env, audit_path, read_attempt, secret = _fake_codex_environment(
                    root, mode=mode
                )
                with mock.patch.dict(os.environ, env, clear=True), \
                     _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                    report = probe.probe_codex()
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "unknown")
                self.assertEqual(report["source"], "codex-app-server/account/rateLimits/read")
                self.assertIn("observed_at_epoch", report)
                self.assertNotIn(secret, json.dumps(report))
                self.assertNotIn(secret, json.dumps(audit["events"]))
                self.assertFalse(read_attempt.exists())
                self.assertEqual(Path(audit["argv"][0]).resolve(), (Path(env["PATH"]) / "codex").resolve())
                with self.assertRaises(ProcessLookupError):
                    os.kill(audit["pid"], 0)

    def test_codex_rpc_closes_parent_pipe_streams_on_success_and_failure(self) -> None:
        for mode in ("normal", "quota-error"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                env, _audit_path, _read_attempt, _secret = _fake_codex_environment(
                    root, mode=mode
                )
                children = []
                real_popen = subprocess.Popen

                def recording_popen(*args, **kwargs):
                    child = real_popen(*args, **kwargs)
                    children.append(child)
                    return child

                try:
                    with mock.patch.dict(os.environ, env, clear=True), \
                         mock.patch.object(
                             probe.subprocess, "Popen", side_effect=recording_popen,
                         ):
                        if mode == "normal":
                            probe._codex_app_server_request()
                        else:
                            with self.assertRaises(RuntimeError):
                                probe._codex_app_server_request()

                    self.assertEqual(len(children), 1)
                    self.assertTrue(children[0].stdin.closed)
                    self.assertTrue(children[0].stdout.closed)
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                            child.wait()

    def test_source_failures_record_failure_observation_time(self) -> None:
        request_started = 1_800_000_000.0
        failure_observed = request_started + 17.0
        clock = mock.Mock(return_value=request_started)

        def codex_failure():
            clock.return_value = failure_observed
            raise OSError("source unavailable")

        with mock.patch.object(probe, "time", mock.Mock(time=clock)):
            codex_report = probe.probe_codex(transport=codex_failure)
        self.assertEqual(codex_report["status"], "unknown")
        self.assertEqual(codex_report["runtime"], "codex")
        self.assertEqual(codex_report["source"], probe.RUNTIME_SOURCES["codex"])
        self.assertEqual(codex_report["observed_at_epoch"], failure_observed)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "zcode-config.json"
            config_path.write_text(
                json.dumps({"provider": {"zai": {"options": {"apiKey": "test-key"}}}}),
                encoding="utf-8",
            )
            clock.return_value = request_started

            def zcode_failure(_url, _headers):
                clock.return_value = failure_observed
                raise OSError("source unavailable")

            with mock.patch.object(probe, "time", mock.Mock(time=clock)):
                zcode_report = probe.probe_zcode(
                    config_path=config_path,
                    transport=zcode_failure,
                )
        self.assertEqual(zcode_report["status"], "unknown")
        self.assertEqual(zcode_report["runtime"], "zcode")
        self.assertEqual(zcode_report["source"], probe.RUNTIME_SOURCES["zcode"])
        self.assertEqual(zcode_report["observed_at_epoch"], failure_observed)

    def test_codex_selector_setup_failure_reaps_fake_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, _audit_path, _read_attempt, _secret = _fake_codex_environment(root)
            children = []
            real_popen = subprocess.Popen

            class RegisterFailureSelector:
                def register(self, *_args, **_kwargs):
                    raise OSError("selector registration failed")

                def close(self):
                    pass

            def recording_popen(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child

            try:
                with mock.patch.dict(os.environ, env, clear=True), \
                     mock.patch.object(probe.subprocess, "Popen", side_effect=recording_popen), \
                     mock.patch.object(
                         probe.selectors, "DefaultSelector",
                         return_value=RegisterFailureSelector(),
                     ), \
                     _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                    report = probe.probe_codex()
                self.assertEqual(report["status"], "unknown")
                self.assertEqual(len(children), 1)
                self.assertIsNotNone(children[0].poll())
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.wait()

    def test_codex_selector_close_failure_reaps_fake_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, _audit_path, _read_attempt, _secret = _fake_codex_environment(root)
            children = []
            real_popen = subprocess.Popen
            real_selector_type = probe.selectors.DefaultSelector

            class CloseFailureSelector:
                def __init__(self):
                    self.selector = real_selector_type()

                def register(self, *args, **kwargs):
                    return self.selector.register(*args, **kwargs)

                def select(self, *args, **kwargs):
                    return self.selector.select(*args, **kwargs)

                def close(self):
                    self.selector.close()
                    raise OSError("selector close failed")

            def recording_popen(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child

            try:
                with mock.patch.dict(os.environ, env, clear=True), \
                     mock.patch.object(probe.subprocess, "Popen", side_effect=recording_popen), \
                     mock.patch.object(
                         probe.selectors, "DefaultSelector", CloseFailureSelector,
                     ), \
                     _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                    report = probe.probe_codex()
                self.assertEqual(report["status"], "unknown")
                self.assertEqual(len(children), 1)
                self.assertIsNotNone(children[0].poll())
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.wait()

    def test_codex_timeout_and_oversize_kill_fake_child(self) -> None:
        for mode in ("timeout", "oversize"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                env, audit_path, read_attempt, _secret = _fake_codex_environment(root, mode=mode)
                with mock.patch.dict(os.environ, env, clear=True), \
                     _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                    started = time.monotonic()
                    report = probe.probe_codex(
                        transport=lambda: probe._codex_app_server_request(timeout_seconds=2.0)
                    )
                    self.assertLess(time.monotonic() - started, 4.0)
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "unknown")
                self.assertIn("observed_at_epoch", report)
                with self.assertRaises(ProcessLookupError):
                    os.kill(audit["pid"], 0)
                self.assertFalse(read_attempt.exists())

    def test_codex_missing_command_is_unknown_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, audit_path, read_attempt, secret = _fake_codex_environment(root)
            with mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(probe.shutil, "which", return_value=None), \
                 _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                report = probe.probe_codex()
        self.assertEqual(report["status"], "unknown")
        self.assertIn("observed_at_epoch", report)
        self.assertNotIn(secret, json.dumps(report))
        self.assertFalse(audit_path.exists())
        self.assertFalse(read_attempt.exists())

    def test_run_probe_routes_supported_and_unknown_runtimes_explicitly(self) -> None:
        now = time.time()
        native = _native_codex_result(now=now)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, audit_path, read_attempt, _secret = _fake_codex_environment(root, native)
            env["ZCODE_APP_VERSION"] = "test-inherited-zcode-signal"
            with mock.patch.dict(os.environ, env, clear=True), \
                 _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                report = probe.run_probe("codex", now=now)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(report["runtime"], "codex")
            self.assertEqual([event.get("method") for event in audit["events"]], [
                "initialize", "initialized", "account/rateLimits/read",
            ])
            self.assertFalse(read_attempt.exists())
        report = probe.run_probe(
            "unsupported",
            codex_transport=lambda: self.fail("unsupported runtime called Codex"),
            transport=lambda *_: self.fail("unsupported runtime called ZCode"),
        )
        self.assertEqual(report["status"], "unknown")

    def test_cli_unsupported_runtime_does_not_start_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, audit_path, read_attempt, secret = _fake_codex_environment(root)
            result = self._run_cli("--runtime", "unsupported", env=env)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "unknown")
        self.assertFalse(audit_path.exists())
        self.assertFalse(read_attempt.exists())
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_codex_cli_explicit_override_uses_fake_server_and_isolated_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            now = time.time()
            primary = {"usedPercent": 95.0, "windowDurationMins": 300,
                       "resetsAt": int(now) + 3600}
            env, audit_path, read_attempt, secret = _fake_codex_environment(
                root, _native_codex_result(now=now, primary=primary)
            )
            env["ZCODE_APP_VERSION"] = "test-inherited-zcode-signal"
            flag = root / "budget-guard.flag"
            result = self._run_cli("--runtime", "codex", "--write-flag", str(flag),
                                   "--plan", "codex-native-test", env=env)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            flag_exists = flag.exists()
            credential_read_attempted = read_attempt.exists()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["runtime"], "codex")
        self.assertEqual(report["source"], "codex-app-server/account/rateLimits/read")
        self.assertEqual(report["pause_decision"], "pause")
        self.assertEqual(audit["home"], env["HOME"])
        self.assertEqual(Path(audit["argv"][0]).resolve(), (Path(env["PATH"]) / "codex").resolve())
        self.assertNotIn(secret, result.stdout + result.stderr + json.dumps(audit["events"]))
        self.assertFalse(credential_read_attempted)
        self.assertTrue(flag_exists)

    def test_runtime_explicit_override(self) -> None:
        self.assertEqual(probe.detect_runtime("codex"), "codex")
        self.assertEqual(probe.detect_runtime("zcode"), "zcode")
        self.assertIsNone(probe.detect_runtime("unsupported"))

    def test_runtime_autodetect_rejects_conflicting_live_signals(self) -> None:
        with _scrubbed_harness_env({"ZCODE_APP_VERSION": "3.12.3"}):
            with mock.patch.object(
                harness_detection, "_default_ancestry",
                lambda: ["zsh", "codex exec plan X", "launchd"],
            ):
                self.assertIsNone(probe.detect_runtime())
        with _scrubbed_harness_env():
            with mock.patch.object(
                harness_detection, "_default_ancestry",
                lambda: ["zsh", "codex exec plan X", "launchd"],
            ):
                self.assertEqual(probe.detect_runtime(), "codex")
            self.assertIsNone(probe.detect_runtime())

    def test_autodetect_uses_live_env_signal(self) -> None:
        # ZCODE_* in the environment detects zcode even with NO config file
        # on disk (HOME pointed at an empty temp dir).
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_home = Path(tmpdir) / "home"
            empty_home.mkdir()
            with _scrubbed_harness_env({"ZCODE_APP_VERSION": "3.12.3"}):
                old_home = os.environ.get("HOME")
                os.environ["HOME"] = str(empty_home)
                try:
                    self.assertEqual(probe.detect_runtime(None), "zcode")
                finally:
                    if old_home is None:
                        os.environ.pop("HOME", None)
                    else:
                        os.environ["HOME"] = old_home

    def test_autodetect_ignores_file_presence(self) -> None:
        # Mis-bind canary: the real config file exists under HOME, but with
        # no ZCODE_* variable and no codex ancestry, auto-detect answers None.
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir) / "home"
            config = fake_home / ".zcode" / "cli" / "config.json"
            config.parent.mkdir(parents=True)
            config.write_text("{}", encoding="utf-8")
            with _scrubbed_harness_env():
                old_home = os.environ.get("HOME")
                os.environ["HOME"] = str(fake_home)
                try:
                    self.assertIsNone(probe.detect_runtime(None))
                finally:
                    if old_home is None:
                        os.environ.pop("HOME", None)
                    else:
                        os.environ["HOME"] = old_home

    def test_explicit_runtime_still_wins(self) -> None:
        with _scrubbed_harness_env({"ZCODE_APP_VERSION": "3.12.3"}):
            self.assertEqual(probe.detect_runtime("codex"), "codex")

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
            # A wait-for-reset ride-through arms nothing either: the flag
            # writer keys on "pause" and nothing else.
            waiting = probe.make_limit("primary", 92.0, 1000 + 15 * 60, now=1000)
            probe.write_flag_if_paused(flag, "zcode", [waiting], "wait-for-reset")
            self.assertFalse(flag.exists())

    def test_main_write_flag_relays_guard_armed(self) -> None:
        # r4 O18: the --write-flag relay must surface the arm outcome in the
        # report itself: guard_armed True on an armed pause, and
        # guard_armed False plus its reason line when the flag was NOT
        # armed, so a reader trusting the JSON never assumes an armed flag
        # from the pause-only exit code. The probe pipeline is stubbed; the
        # flag writer and the shared guard lock are real.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            pause_report = {
                "runtime": "zcode",
                "status": "ok",
                "binding": "primary",
                "pause_decision": "pause",
                "reasons": [],
                "limits": [probe.make_limit("primary", 95.0, 1000 + 10 * 60, now=1000)],
            }
            original_detect = probe.detect_runtime
            original_run = probe.run_probe
            probe.detect_runtime = lambda *args, **kwargs: object()
            probe.run_probe = lambda *args, **kwargs: dict(pause_report)
            try:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = probe.main(["--write-flag", str(flag), "--runtime", "zcode"])
                self.assertEqual(code, 0)
                report = json.loads(out.getvalue())
                self.assertEqual(report["pause_decision"], "pause")
                self.assertTrue(report["guard_armed"])
                self.assertTrue(flag.exists())
                # Not-armed arm: the guard lock held here fails the arm; the
                # report names that instead of leaving armed assumed.
                flag.unlink()
                held = resume_watcher.budget_guard_lock(flag)
                with held as acquired:
                    self.assertTrue(acquired)
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        code = probe.main(["--write-flag", str(flag), "--runtime", "zcode"])
                    self.assertEqual(code, 0)
                    report = json.loads(out.getvalue())
                    self.assertFalse(report["guard_armed"])
                    self.assertTrue(
                        any("guard flag not armed" in reason for reason in report["reasons"]),
                        report["reasons"],
                    )
            finally:
                probe.detect_runtime = original_detect
                probe.run_probe = original_run

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

    def test_write_flag_expands_tilde_path(self) -> None:
        # r1 F16: a literal-tilde argv must arm the SAME host-global flag
        # file the hooks and the watcher read (expanded), never a
        # "./~/..." path that silently never arms and bypasses the shared
        # lock contract. The HOME env override keeps the case hermetic.
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir) / "home"
            flag = fake_home / ".ai-playbook" / "runtime" / "budget-guard.flag"
            pausing = probe.make_limit("primary", 95.0, 1000 + 10 * 60, now=1000)
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = str(fake_home)
            try:
                self.assertTrue(probe.write_flag_if_paused("~/.ai-playbook/runtime/budget-guard.flag", "zcode", [pausing], "pause"))
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home
            self.assertTrue(flag.exists(), "literal-tilde argv must expanduser to the host-global flag")
            self.assertFalse((Path(tmpdir) / "~").exists())

    def test_write_flag_skips_arming_when_lock_unavailable(self) -> None:
        # r1 F13: on lock-acquire timeout the writer must NOT arm with an
        # unlocked replace: a concurrent locked cleanup could delete the
        # live flag or the unlocked publish could race. Not arming (False)
        # is the fail-open direction; the pid-unique tmp leaves no fixed
        # shared staging file behind either.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            pausing = probe.make_limit("primary", 95.0, 1000 + 10 * 60, now=1000)
            held = resume_watcher.budget_guard_lock(flag)
            with held as acquired:
                self.assertTrue(acquired)
                outcome: dict = {}
                started = threading.Event()

                def blocked_writer() -> None:
                    started.set()
                    outcome["armed"] = probe.write_flag_if_paused(flag, "zcode", [pausing], "pause")

                thread = threading.Thread(target=blocked_writer)
                thread.start()
                self.assertTrue(started.wait(5), "writer witness never started")
                thread.join(5)
                self.assertFalse(thread.is_alive())
            # The writer returned without arming once the lock released
            # behind it: the 2s lock timeout elapsed first.
            self.assertFalse(outcome.get("armed", True))
            self.assertFalse(flag.exists())
            self.assertEqual(list(Path(tmpdir).glob("*.tmp*")), [])

    def test_guard_cleanup_does_not_remove_replaced_flag(self) -> None:
        # Shared guard-lock replacement interleaving: the hook's expired-window
        # cleanup and the probe writer's replacement both wait on the SAME
        # lock file (budget-guard.lock next to the flag; the watcher's
        # compare-and-delete holds it too), so a cleanup that decided on the
        # old window can never unlink the newer window's replacement. The
        # lock handle below comes from the watcher module to prove the
        # cross-module interlock on one file.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            fired = Path(tmpdir) / "budget-guard.fired"
            expired_epoch = int(time.time()) - 120
            newer_epoch = int(time.time()) + 3600
            self.assertTrue(probe.write_flag_if_paused(
                flag, "zcode",
                [probe.make_limit("primary", 95.0, expired_epoch, now=int(time.time()) - 120)],
                "pause",
            ))
            lock_path = resume_watcher.guard_lock_path(flag)
            self.assertEqual(lock_path.name, "budget-guard.lock")
            self.assertEqual(lock_path.parent, flag.parent)
            out = io.StringIO()
            hook_outcome = {}
            writer_outcome = {}
            cleaner_started = threading.Event()

            def hook_cleanup() -> None:
                cleaner_started.set()
                with contextlib.redirect_stdout(out):
                    # Hermeticity: point the decision log into the fixture tmp
                    # dir instead of the host-global hook-outcomes.log.
                    hook_outcome["code"] = budget_guard_core.main(
                        ["--runtime", "zcode", "--flag-path", str(flag), "--fired-path", str(fired),
                         "--hook-outcomes-log", str(flag.parent / "hook-outcomes.log")]
                    )

            def writer_replacement() -> None:
                writer_started.set()
                writer_outcome["armed"] = probe.write_flag_if_paused(
                    flag, "zcode",
                    [probe.make_limit("primary", 95.0, newer_epoch, now=int(time.time()))],
                    "pause",
                )

            writer_started = threading.Event()
            with resume_watcher.budget_guard_lock(flag) as held:
                self.assertTrue(held)
                cleaner = threading.Thread(target=hook_cleanup)
                cleaner.start()
                # The `started` markers (r1 F29) prove each thread reached
                # its body before the blocked assertions, so scheduler
                # starvation cannot make the blocking-half witnesses vacuous.
                self.assertTrue(cleaner_started.wait(5), "hook cleanup witness never started")
                cleaner.join(0.5)
                self.assertTrue(cleaner.is_alive(), "hook cleanup did not block on the shared guard lock")
                writer = threading.Thread(target=writer_replacement)
                writer.start()
                self.assertTrue(writer_started.wait(5), "probe writer witness never started")
                writer.join(0.5)
                self.assertTrue(writer.is_alive(), "probe writer did not participate in the shared guard lock")
            cleaner.join(5)
            writer.join(5)
            self.assertFalse(cleaner.is_alive())
            self.assertFalse(writer.is_alive())
            # Whichever participant unblocked first, the newer flag survives
            # and the expired cleanup passed without blocking.
            self.assertTrue(writer_outcome["armed"])
            self.assertEqual(hook_outcome["code"], budget_guard_core.EXIT_OK)
            self.assertEqual(out.getvalue(), "")
            self.assertTrue(flag.exists())
            parsed = budget_guard_core.parse_flag(flag.read_text(encoding="utf-8"))
            self.assertEqual(parsed["reset_at_epoch"], newer_epoch)
            # The watcher's own compare-and-delete with the stale decision
            # refuses to remove the replaced flag as well.
            result = resume_watcher.compare_and_delete_flag(flag, expired_epoch)
            self.assertFalse(result["removed"])
            self.assertTrue(result["refused"])
            self.assertEqual(result["reason"], "newer-window")
            self.assertTrue(flag.exists())

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
        # decision but must NOT arm the host-global guard flag. The fixture
        # keeps the binding reset 120 minutes out so the decision is a
        # genuine usage-driven pause, not an imminent-reset ride-through.
        early_secondary = probe.make_limit("secondary", 95.0, 1000 + 120 * 60, now=1000)
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

    def _run_cli(self, *extra: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/quota_window_probe.py"), *extra],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

    def test_codex_cli_source_failure_exits_one_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env, audit_path, read_attempt, secret = _fake_codex_environment(
                root, mode="quota-error"
            )
            flag = root / "budget-guard.flag"
            result = self._run_cli("--runtime", "codex", "--write-flag", str(flag), env=env)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertIn("source", report)
        self.assertIn("observed_at_epoch", report)
        self.assertNotIn(secret, result.stdout + result.stderr + json.dumps(audit["events"]))
        self.assertFalse(read_attempt.exists())
        self.assertFalse(flag.exists())

    def test_wait_for_reset_exits_1_and_arms_no_flag(self) -> None:
        # A wait-for-reset report exits 1 (0 stays pause-only) and never
        # arms the guard flag: the in-session ride-through writes nothing.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            flag = Path(tmpdir) / "budget-guard.flag"
            now = time.time()
            payload = {"data": {"limits": [
                {
                    "type": "TOKENS_LIMIT",
                    "percentage": 92.0,
                    "nextResetTime": int((now + 15 * 60) * 1000),
                }
            ]}}
            body = json.dumps(payload)
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", lambda url, headers: body
            ), contextlib.redirect_stdout(out):
                code = probe.main([
                    "--runtime", "zcode",
                    "--config", str(config),
                    "--write-flag", str(flag),
                ])
            self.assertEqual(code, 1)
            report = json.loads(out.getvalue())
            self.assertEqual(report["pause_decision"], "wait-for-reset")
            self.assertFalse(flag.exists())

    # test_cli_write_flag_refusal_reason_is_observable (review r2 F5) was
    # removed in review r4 F4: it pinned main()'s "guard flag not armed"
    # else-branch, which is unreachable in the shipped CLI path (both
    # parsers clamp every limit before main() sees it) and was reachable
    # only by mocking the writer. The writer-level horizon refusal remains
    # pinned by test_write_flag_refuses_epoch_beyond_horizon.

    def test_cli_zcode_default_url_reaches_transport(self) -> None:
        # Review r3 F5: main()'s argparse --url default is the production
        # entry surface (the plan's gate command passes no --url); all
        # the Codex CLI tests use a fake app-server, so a legacy
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



    # --- Task 1: probe protocol-completion margin (origin 2, layer 2) ---

    def test_evaluate_pause_protocol_margin_pauses_above_fixed_threshold(self) -> None:
        # The margin is a structural floor under the pause branch, never a
        # clock-only pause line: with 25 minutes left, the 20-minute line
        # clear, and a 30-minute protocol margin, a low-usage window
        # continues. At 92 percent the margin makes the pause candidate
        # ride through as wait-for-reset (margin 30 over 25 remaining).
        limit = probe.make_limit("primary", 10.0, 1000 + 25 * 60, now=1000)
        decision, reasons = probe.evaluate_pause(
            [limit], "primary",
            minutes_threshold=20, percent_threshold=90, protocol_minutes_threshold=30,
        )
        self.assertEqual(decision, "continue")
        self.assertEqual(reasons, [])
        hot = probe.make_limit("primary", 92.0, 1000 + 25 * 60, now=1000)
        decision, reasons = probe.evaluate_pause(
            [hot], "primary",
            minutes_threshold=20, percent_threshold=90, protocol_minutes_threshold=30,
        )
        self.assertEqual(decision, "wait-for-reset")
        self.assertTrue(
            any("ride-through" in r for r in reasons), reasons
        )

    def test_evaluate_pause_protocol_margin_default_floor_is_subsumed(self) -> None:
        # The 10-minute default is a floor under the 20-minute line, not a
        # second pause line at normal range: a pause candidate with 25
        # minutes remaining under all defaults resolves pause by usage
        # alone, never wait-for-reset — the default margin floor is
        # subsumed by the imminence line.
        limit = probe.make_limit("primary", 92.0, 1000 + 25 * 60, now=1000)
        decision, reasons = probe.evaluate_pause([limit], "primary")
        self.assertEqual(decision, "pause")
        self.assertFalse(any("wait-for-reset" in r for r in reasons), reasons)

    def test_evaluate_pause_protocol_margin_boundary_is_strict(self) -> None:
        # Exactly at the margin does not arm the ride-through, mirroring
        # the strict `<` of the minutes line: a pause candidate with 30
        # minutes left against a 30-minute margin resolves pause by the
        # usage arm alone, never wait-for-reset.
        limit = probe.make_limit("primary", 92.0, 1000 + 30 * 60, now=1000)
        decision, reasons = probe.evaluate_pause(
            [limit], "primary",
            minutes_threshold=20, percent_threshold=90, protocol_minutes_threshold=30,
        )
        self.assertEqual(decision, "pause")
        self.assertFalse(any("wait-for-reset" in r for r in reasons), reasons)

    def test_secondary_binding_margin_stays_report_only(self) -> None:
        # A weekly secondary-only limit set inside the margin continues in
        # the report (usage gate first: 10 percent never becomes a pause
        # candidate) and the flag writer refuses regardless: the margin
        # must not change the secondary report-only contract.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            limit = probe.make_limit("secondary", 10.0, 1000 + 25 * 60, now=1000)
            report = probe.build_report(
                "zcode", [limit], now=1000, protocol_minutes_threshold=30,
            )
            self.assertEqual(report["pause_decision"], "continue")
            self.assertFalse(
                probe.write_flag_if_paused(flag, "zcode", [limit], "pause")
            )
            self.assertFalse(flag.exists())

    def test_cli_min_protocol_minutes_flag_pauses(self) -> None:
        # The CLI flag threads through main() to the probe. With the usage
        # gate first, 50 percent at 25 minutes is a continue (exit 1); at
        # 95 percent the 30-minute margin over a 25-minute remainder
        # resolves wait-for-reset, which also exits 1 (0 stays pause-only).
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            now = time.time()
            # The reset carries one minute of headroom past the 25-minute
            # scenario so the floor-divided minutes_remaining stays exactly
            # 25 despite the parse clock reading a hair past ``now``.
            reset_epoch = int(now + 26 * 60)

            def run(percentage: float) -> tuple[int, dict]:
                payload = {
                    "data": {
                        "limits": [
                            {
                                "type": "TOKENS_LIMIT",
                                "percentage": percentage,
                                "nextResetTime": reset_epoch * 1000,
                            }
                        ]
                    }
                }
                body = json.dumps(payload)
                out = io.StringIO()
                with mock.patch.object(
                    probe, "urllib_transport", lambda url, headers: body
                ), contextlib.redirect_stdout(out):
                    code = probe.main([
                        "--runtime", "zcode",
                        "--config", str(config),
                        "--min-protocol-minutes", "30",
                    ])
                return code, json.loads(out.getvalue())

            code, report = run(50.0)
            self.assertEqual(code, 1)
            self.assertEqual(report["pause_decision"], "continue")
            code, report = run(95.0)
            self.assertEqual(code, 1)
            self.assertEqual(report["pause_decision"], "wait-for-reset")
            self.assertEqual(report["wait_minutes"], 27)

    def test_cli_min_protocol_minutes_rejects_negative(self) -> None:
        # A negative margin is a usage error at the CLI (fail loud), never a
        # silent second pause line.
        with self.assertRaises(SystemExit) as ctx:
            probe.main(["--runtime", "zcode", "--min-protocol-minutes", "-5"])
        self.assertEqual(ctx.exception.code, 2)

    def test_cli_min_protocol_minutes_zero_disables_margin(self) -> None:
        # 0 is accepted (margin disabled) and must not become a pause line.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            now = time.time()
            payload = {"data": {"limits": [{"type": "TOKENS_LIMIT", "percentage": 50.0,
                                            "nextResetTime": int((now + 25 * 60) * 1000)}]}}
            body = json.dumps(payload)
            out = io.StringIO()
            with mock.patch.object(probe, "urllib_transport", lambda url, headers: body), \
                    contextlib.redirect_stdout(out):
                code = probe.main(["--runtime", "zcode", "--config", str(config),
                                   "--min-protocol-minutes", "0"])
            self.assertEqual(code, 1)
            report = json.loads(out.getvalue())
            self.assertEqual(report["pause_decision"], "continue")

    def test_cli_plan_cost_upper_bound_boundary(self) -> None:
        # 100 is the inclusive upper bound (accepted); just above is a usage
        # error. A wave costing 100 percent cannot fit the remaining 20, so
        # the fit arm alone makes the report a pause (exit 0) with the
        # recommendation fields unchanged.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            now = time.time()
            payload = {"data": {"limits": [{"type": "TOKENS_LIMIT", "percentage": 80.0,
                                            "nextResetTime": int((now + 120 * 60) * 1000)}]}}
            body = json.dumps(payload)
            out = io.StringIO()
            with mock.patch.object(probe, "urllib_transport", lambda url, headers: body), \
                    contextlib.redirect_stdout(out):
                code = probe.main(["--runtime", "zcode", "--config", str(config),
                                   "--plan-cost", "100"])
            self.assertEqual(code, 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report["pause_decision"], "pause")
            self.assertEqual(report["wave_recommendation"], "pause")
        with self.assertRaises(SystemExit) as ctx:
            probe.main(["--runtime", "zcode", "--plan-cost", "100.5"])
        self.assertEqual(ctx.exception.code, 2)

    # --- Task 7 (origin 10): wait-window override upper bounds ---

    def test_minutes_before_override_above_cadence_window_refused(self) -> None:
        # Origin 10: --minutes-before has no upper validation, so an
        # override can turn the reported wait into hours or days, silently
        # converting a recoverable pause into an effectively unbounded lane
        # stall. A value above the cadence window is a usage error (exit 2,
        # no JSON on stdout) naming the 300-minute cadence-window bound.
        # The missing --config keeps the RED-stage fallback run hermetic:
        # before the bound lands the parse succeeds and the probe fails
        # open to an unknown report instead of reaching a live endpoint.
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_config = str(Path(tmpdir) / "missing-config.json")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as ctx:
                    probe.main([
                        "--runtime", "zcode",
                        "--config", missing_config,
                        "--minutes-before", "999",
                    ])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("--minutes-before must be <= 300", err.getvalue())
        self.assertIn("300-minute cadence window", err.getvalue())

    def test_min_protocol_minutes_override_above_cadence_window_refused(self) -> None:
        # Same bound for the protocol margin: --min-protocol-minutes only
        # requires >= 0 today, so 1001 parses and the reported wait grows
        # unbounded; above the cadence window it is refused exactly like
        # the oversized --minutes-before override.
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_config = str(Path(tmpdir) / "missing-config.json")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as ctx:
                    probe.main([
                        "--runtime", "zcode",
                        "--config", missing_config,
                        "--min-protocol-minutes", "1001",
                    ])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("--min-protocol-minutes must be <= 300", err.getvalue())
        self.assertIn("300-minute cadence window", err.getvalue())

    def test_override_flags_at_bound_still_parse(self) -> None:
        # The bound rejects only values ABOVE the cadence window: exactly
        # 300 stays a legal override for both flags. Otherwise-default
        # inputs against scrubbed harness env detect no runtime and fail
        # open to the standard unknown report (exit 1), proving the parse
        # passed validation with no argparse error.
        with _scrubbed_harness_env():
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = probe.main([
                    "--minutes-before", "300",
                    "--min-protocol-minutes", "300",
                ])
        self.assertEqual(code, 1)
        report = json.loads(out.getvalue())
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(
            report["reasons"],
            ["runtime is unsupported, ambiguous, or not detected; pass --runtime explicitly"],
        )

    def test_codex_native_margin_threading_reaches_build_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            now = time.time()
            reset_epoch = int(now) + 26 * 60
            primary = {"usedPercent": 10.0, "windowDurationMins": 300,
                       "resetsAt": reset_epoch}
            env, audit_path, read_attempt, _secret = _fake_codex_environment(
                root, _native_codex_result(now=now, primary=primary)
            )
            with mock.patch.dict(os.environ, env, clear=True), \
                 _forbid_credential_reads(Path(env["CODEX_AUTH_CANARY"])):
                report = probe.probe_codex(now=now, protocol_minutes_threshold=30,
                                           plan_cost_percent=40.0)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["pause_decision"], "continue")
        self.assertEqual([event.get("method") for event in audit["events"]], [
            "initialize", "initialized", "account/rateLimits/read",
        ])
        self.assertFalse(read_attempt.exists())

    def test_cli_ninety_eight_percent_pause_drill_ac2_witness(self) -> None:
        # The origin-2 AC2 fixture drill: the pause fires at very high
        # used-percent with wall-clock margin intact (98 percent used, 40
        # minutes remaining, default 10-minute margin), so the protocol runs
        # while budget, not the clock, is the binding constraint.
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            now = time.time()
            payload = {
                "data": {
                    "limits": [
                        {
                            "type": "TOKENS_LIMIT",
                            "percentage": 98.0,
                            "nextResetTime": int((now + 40 * 60) * 1000),
                        }
                    ]
                }
            }
            body = json.dumps(payload)
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", lambda url, headers: body
            ), contextlib.redirect_stdout(out):
                code = probe.main([
                    "--runtime", "zcode",
                    "--config", str(config),
                    "--min-protocol-minutes", "10",
                ])
            self.assertEqual(code, 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report["pause_decision"], "pause")
            self.assertTrue(
                any("used_percent" in r for r in report["reasons"]),
                report["reasons"],
            )


    def test_write_flag_writes_armed_by_probe(self) -> None:
        # The probe is the flag's writer: the flag must carry armed_by=probe
        # so the hook's block reason can attribute the arming.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            now = time.time()
            limit = probe.make_limit("primary", 95.0, int(now) + 30 * 60, now=now)
            self.assertTrue(
                probe.write_flag_if_paused(flag, "zcode", [limit], "pause")
            )
            content = flag.read_text(encoding="utf-8")
            self.assertIn("armed_by=probe", content)

    # --- Task 2: probe plan-cost wave recommendation (origin 1, gaps 1/5) ---

    def test_build_report_plan_cost_full(self) -> None:
        limit = probe.make_limit("primary", 50.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000, plan_cost_percent=40.0)
        self.assertEqual(report["wave_recommendation"], "full")
        self.assertIsNone(report["wave_size"])

    def test_build_report_plan_cost_split(self) -> None:
        # Cost 40 > remaining 20, half-cost 20 <= remaining 20: split in
        # waves of 2.
        limit = probe.make_limit("primary", 80.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000, plan_cost_percent=40.0)
        self.assertEqual(report["wave_recommendation"], "split")
        self.assertEqual(report["wave_size"], 2)

    def test_build_report_plan_cost_pause(self) -> None:
        # Half-cost 20 > remaining 15: not even half a panel fits.
        limit = probe.make_limit("primary", 85.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000, plan_cost_percent=40.0)
        self.assertEqual(report["wave_recommendation"], "pause")
        self.assertIsNone(report["wave_size"])

    def test_build_report_plan_cost_boundary_full_at_exact_remaining(self) -> None:
        # Cost 40 equals remaining 40: the <= boundary is inclusive.
        limit = probe.make_limit("primary", 60.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000, plan_cost_percent=40.0)
        self.assertEqual(report["wave_recommendation"], "full")

    def test_build_report_without_plan_cost_has_no_recommendation_fields(self) -> None:
        # Existing report shape is unchanged for callers that omit the flag.
        limit = probe.make_limit("primary", 50.0, 1000 + 120 * 60, now=1000)
        report = probe.build_report("zcode", [limit], now=1000)
        self.assertNotIn("plan_cost_percent", report)
        self.assertNotIn("wave_recommendation", report)
        self.assertNotIn("wave_size", report)

    def test_cli_plan_cost_split_recommendation(self) -> None:
        # 80 percent with a 40-percent wave against 20 remaining: the fit
        # arm alone is a pause candidate (40 > 20) and with the reset two
        # hours out it resolves a pause (exit 0). The recommendation fields
        # are unchanged: split into waves of 2 (half-cost 20 <= remaining 20).
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            now = time.time()
            payload = {
                "data": {
                    "limits": [
                        {
                            "type": "TOKENS_LIMIT",
                            "percentage": 80.0,
                            "nextResetTime": int((now + 120 * 60) * 1000),
                        }
                    ]
                }
            }
            body = json.dumps(payload)
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", lambda url, headers: body
            ), contextlib.redirect_stdout(out):
                code = probe.main([
                    "--runtime", "zcode",
                    "--config", str(config),
                    "--plan-cost", "40",
                ])
            self.assertEqual(code, 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report["pause_decision"], "pause")
            self.assertEqual(report["wave_recommendation"], "split")
            self.assertEqual(report["wave_size"], 2)

    def test_cli_plan_cost_rejects_out_of_range(self) -> None:
        for bad in ("150", "0", "-5"):
            with self.subTest(bad=bad):
                with self.assertRaises(SystemExit) as ctx:
                    probe.main(["--runtime", "zcode", "--plan-cost", bad])
                self.assertEqual(ctx.exception.code, 2)

    # --- Task 1 (P6 origins 1-2): probe --fire-at mode (pricing and fit) ---

    def _fire_at_main(self, argv: list[str], payload: str = "{}",
                      with_key: bool = True,
                      now: int = FIRE_NOW_EPOCH) -> tuple[int, str]:
        """Drive main() in-process with the zcode transport mocked.

        Reuses the _write_config + urllib_transport patch pattern of the
        existing CLI tests; the transport answers with ``payload`` verbatim
        and is never consulted when the fire-at mode runs pure pricing.
        Review r1 F2: the injected ``now`` (default FIRE_NOW_EPOCH) threads
        through main -> _fire_at_cli -> run_probe/evaluate_fire_at, so the
        payload-driven fit tests read a fixed clock instead of the host's
        wall clock and can never false-REDD once the real date passes the
        fixture windows.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir), with_key=with_key)
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", lambda url, headers: payload
            ), contextlib.redirect_stdout(out):
                code = probe.main(["--runtime", "zcode", "--config", str(config), *argv],
                                  now=now)
            return code, out.getvalue()

    def _limits_payload(self, primary_reset_epoch: int) -> str:
        """A zcode payload whose TOKENS_LIMIT resets at the given epoch."""
        return json.dumps({"data": {"limits": [
            {
                "type": "TOKENS_LIMIT",
                "percentage": 50.0,
                "nextResetTime": int(primary_reset_epoch) * 1000,
            },
        ]}})

    def test_fire_at_peak_defers_with_window_end(self) -> None:
        # Wednesday 2026-09-23 15:00 UTC+8 sits inside the default peak
        # window; without --need-minutes the mode is pure pricing and
        # defers to the same day 18:00 UTC+8 (exit 2).
        self.assertEqual(datetime(2026, 9, 23, tzinfo=TZ8).weekday(), 2)
        code, out = self._fire_at_main(["--fire-at", "2026-09-23T15:00:00+08:00"])
        self.assertEqual(code, 2)
        verdict = json.loads(out)
        self.assertEqual(verdict["status"], "ok")
        self.assertEqual(verdict["verdict"], "defer-peak")
        self.assertTrue(verdict["peak"])
        self.assertIsNone(verdict["fits"])
        self.assertIsNone(verdict["minutes_remaining_at_fire"])
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()),
            FIRE_WINDOW_END_EPOCH,
        )

    def test_fire_at_off_peak_fires(self) -> None:
        # Wednesday 13:00 UTC+8 is off-peak: fire as planned (exit 0); the
        # fit fields stay null in the pure-pricing form.
        code, out = self._fire_at_main(["--fire-at", "2026-09-23T13:00:00+08:00"])
        self.assertEqual(code, 0)
        verdict = json.loads(out)
        self.assertEqual(verdict["status"], "ok")
        self.assertEqual(verdict["verdict"], "fire")
        self.assertFalse(verdict["peak"])
        self.assertIsNone(verdict["defer_to"])
        self.assertIsNone(verdict["fits"])
        self.assertIsNone(verdict["minutes_remaining_at_fire"])

    def test_fire_at_weekend_is_off_peak(self) -> None:
        # Saturday 2026-09-26 15:00 UTC+8: the peak window is Mon-Fri only.
        self.assertEqual(datetime(2026, 9, 26, tzinfo=TZ8).weekday(), 5)
        code, out = self._fire_at_main(["--fire-at", "2026-09-26T15:00:00+08:00"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "fire")

    def test_fire_at_window_boundaries_end_exclusive(self) -> None:
        # Exactly 14:00 is inside (start inclusive, exit 2); exactly 18:00
        # is outside (end exclusive, exit 0).
        code, out = self._fire_at_main(["--fire-at", "2026-09-23T14:00:00+08:00"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["verdict"], "defer-peak")
        code, out = self._fire_at_main(["--fire-at", "2026-09-23T18:00:00+08:00"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "fire")

    def test_fire_at_straddle_param(self) -> None:
        # 13:30 UTC+8 is 30 minutes before the window start: the default
        # straddle of 0 keeps it off-peak; straddle_minutes=60 (the
        # execution lane's margin) makes the same instant peak.
        fire = FIRE_OFFPEAK_EPOCH + 30 * 60
        plain = probe.evaluate_fire_at(fire, now=fire - 3600)
        self.assertEqual(plain["verdict"], "fire")
        self.assertFalse(plain["peak"])
        straddled = probe.evaluate_fire_at(fire, now=fire - 3600, straddle_minutes=60)
        self.assertEqual(straddled["verdict"], "defer-peak")
        self.assertTrue(straddled["peak"])
        self.assertEqual(
            int(datetime.fromisoformat(straddled["defer_to"]).timestamp()),
            FIRE_WINDOW_END_EPOCH,
        )

    def test_fire_at_fit_defers_to_reset(self) -> None:
        # 80 minutes remain at the fire instant on the reported primary
        # window; a 120-minute child cannot finish, so the fire moves past
        # the containing window's reset (fit outranks pricing, exit 3).
        fire = FIRE_OFFPEAK_EPOCH
        reset = fire + 80 * 60
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T13:00:00+08:00", "--need-minutes", "120"],
            payload=self._limits_payload(reset),
        )
        self.assertEqual(code, 3)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertFalse(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 80)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()), reset
        )

    def test_fire_at_fit_and_off_peak_fires(self) -> None:
        # 200 minutes at the fire instant fits the 120-minute estimate on
        # an off-peak Wednesday 13:00: fire as planned (exit 0).
        fire = FIRE_OFFPEAK_EPOCH
        reset = fire + 200 * 60
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T13:00:00+08:00", "--need-minutes", "120"],
            payload=self._limits_payload(reset),
        )
        self.assertEqual(code, 0)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "fire")
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 200)
        self.assertIsNone(verdict["defer_to"])

    def test_fire_at_peak_and_unfit_prefers_reset(self) -> None:
        # Peak fire time whose primary window leaves 60 minutes: fit
        # outranks pricing, so the verdict is defer-reset (exit 3), never
        # a pricing defer-peak.
        fire = FIRE_PEAK_EPOCH
        reset = fire + 60 * 60
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            payload=self._limits_payload(reset),
        )
        self.assertEqual(code, 3)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertTrue(verdict["peak"])
        self.assertFalse(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 60)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()), reset
        )

    def test_fire_at_peak_deferred_slot_unfit_defers_to_reset(self) -> None:
        # The fire instant fits (200 minutes) but the deferred slot at the
        # window's end (18:00) leaves only 20 minutes of the same reported
        # window: the slot is fit-checked before exit 2 is blessed, so the
        # verdict is defer-reset to the containing window's reset.
        fire = FIRE_PEAK_EPOCH
        reset = fire + 200 * 60  # 18:20 UTC+8; the 18:00 slot leaves 20 min
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            payload=self._limits_payload(reset),
        )
        self.assertEqual(code, 3)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertTrue(verdict["peak"])
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 200)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()), reset
        )

    def test_fire_at_fire_time_beyond_current_reset_uses_cadence_window(self) -> None:
        # The fire instant is at (or past) the reported primary
        # reset_at_epoch: the fit computation anchors on the five-hour
        # cadence window. An instant exactly at reset_at_epoch sees the
        # full 300 minutes; an instant half an hour in sees 270; a negative
        # against the stale reported reset is never computed.
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T13:00:00+08:00", "--need-minutes", "300"],
            payload=self._limits_payload(FIRE_OFFPEAK_EPOCH),
        )
        self.assertEqual(code, 0)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "fire")
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 300)
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T13:30:00+08:00", "--need-minutes", "270"],
            payload=self._limits_payload(FIRE_OFFPEAK_EPOCH),
        )
        self.assertEqual(code, 0)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "fire")
        self.assertEqual(verdict["minutes_remaining_at_fire"], 270)

    def test_fire_at_naive_input_rejected(self) -> None:
        # A --fire-at without a UTC offset is a usage error naming the
        # required +HH:MM form; no verdict JSON reaches stdout.
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                probe.main(["--fire-at", "2026-09-23T15:00:00"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("+HH:MM", err.getvalue())

    def test_fire_at_malformed_peak_window_rejected(self) -> None:
        # A --peak-window that is not HH:MM-HH:MM is a usage error with no
        # verdict JSON on stdout (the flag itself must be recognized, so
        # the argparse unknown-flag error would fail this test too).
        # Review r1 F3: a reversed or equal range ("18:00-14:00",
        # "14:00-14:00") is malformed too - the peak predicate could never
        # hold, silently disabling pricing - not a midnight wrap.
        for bad in ("14-18", "25:00-18:00", "14:00", "14:00-18", "1:00-2:00-3:00",
                    "18:00-14:00", "14:00-14:00"):
            with self.subTest(bad=bad):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as ctx:
                        probe.main([
                            "--fire-at", "2026-09-23T15:00:00+08:00",
                            "--peak-window", bad,
                        ])
                self.assertEqual(ctx.exception.code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertNotIn("unrecognized arguments", err.getvalue())

    def test_fire_at_out_of_range_peak_offset_rejected(self) -> None:
        # A fixed timezone cannot carry an offset of 24 hours or more:
        # usage error, no JSON on stdout. A valid non-default offset must
        # thread through to the peak computation (15:00+08:00 is 07:00
        # UTC, off-peak under --peak-offset-hours 0).
        for bad in ("24", "-24"):
            with self.subTest(bad=bad):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as ctx:
                        probe.main([
                            "--fire-at", "2026-09-23T15:00:00+08:00",
                            "--peak-offset-hours", bad,
                        ])
                self.assertEqual(ctx.exception.code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertNotIn("unrecognized arguments", err.getvalue())
        code, out = self._fire_at_main([
            "--fire-at", "2026-09-23T15:00:00+08:00", "--peak-offset-hours", "0",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["verdict"], "fire")

    def test_fire_at_negative_need_minutes_rejected(self) -> None:
        # Review r1 F4: a negative --need-minutes can never lose the fit leg
        # (every window "fits" a negative need), vacating the leg silently;
        # mirror the --straddle-minutes guard and refuse it as a usage error
        # with no verdict JSON on stdout.
        for bad in ("-5", "-1"):
            with self.subTest(bad=bad):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as ctx:
                        probe.main([
                            "--fire-at", "2026-09-23T15:00:00+08:00",
                            "--need-minutes", bad,
                        ])
                self.assertEqual(ctx.exception.code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertIn("--need-minutes must be >= 0", err.getvalue())

    def test_fire_at_negative_straddle_rejected(self) -> None:
        # Review r2 F11: the --straddle-minutes < 0 guard (which review
        # r1 F4's --need-minutes test mirrored) never got its own rejection
        # test; pin it directly. A negative straddle would shrink the peak
        # window's leading edge, silently vacating part of the pricing leg,
        # so the value is refused as a usage error with no verdict JSON on
        # stdout.
        for bad in ("-5", "-1"):
            with self.subTest(bad=bad):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as ctx:
                        probe.main([
                            "--fire-at", "2026-09-23T15:00:00+08:00",
                            "--straddle-minutes", bad,
                        ])
                self.assertEqual(ctx.exception.code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertIn("--straddle-minutes must be >= 0", err.getvalue())

    def test_fire_at_slot_unfit_cadence_arm_defers_to_reset(self) -> None:
        # Review r1 F5: the existing slot-unfit test exercises the in-window
        # branch (slot < reset). These cases cover the cadence arm (slot at
        # or beyond the reported reset):
        #   k = 0 arm: fire exactly AT the reported reset 17:30 UTC+8 (peak,
        #   still before the 18:00 end) sees the full fresh 300-minute
        #   cadence window, so the fire instant fits the 300-minute
        #   estimate; the deferred slot at the pricing window's end (18:00)
        #   sits in the same cadence window whose end is reset + 5h = 22:30,
        #   leaving only 270 minutes < 300 -> defer-reset (exit 3) to
        #   22:30, never a blessed-unfit exit 2.
        #   k >= 1 arm: reset 09:00, fire 14:00 (window start) evaluates
        #   against the SECOND cadence window (end 19:00, 300 minutes), so
        #   a 100-minute estimate fits at the fire instant; the 18:00 slot
        #   lands in that same second cadence window leaving only 60
        #   minutes < 100 -> defer-reset (exit 3) to 19:00.
        reset_k0 = FIRE_PEAK_EPOCH + 150 * 60  # 17:30 UTC+8
        cadence_end_k0 = reset_k0 + 300 * 60  # 22:30 UTC+8
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T17:30:00+08:00", "--need-minutes", "300"],
            payload=self._limits_payload(reset_k0),
        )
        self.assertEqual(code, 3)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertTrue(verdict["peak"])
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 300)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()),
            cadence_end_k0,
        )
        # k >= 1 arm: the 18:00 slot sits one full cadence window past the
        # reported reset (09:00), so this sub-case injects its own earlier
        # clock (08:00) - the shared FIRE_NOW default (12:00) would leave
        # that reset behind the live-primary filter.
        reset_k1 = FIRE_OFFPEAK_EPOCH - 4 * 3600  # 09:00 UTC+8
        cadence_end_k1 = reset_k1 + 600 * 60  # 19:00 UTC+8 (second window)
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T14:00:00+08:00", "--need-minutes", "100"],
            payload=self._limits_payload(reset_k1),
            now=reset_k1 - 3600,
        )
        self.assertEqual(code, 3)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertTrue(verdict["peak"])
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 300)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()),
            cadence_end_k1,
        )

    def test_fire_at_straddle_boundary_is_inclusive(self) -> None:
        # Review r1 F6: the straddle rule reads (start - straddle) <=
        # minute_of_day, so a fire instant exactly N minutes before the
        # window start IS peak; one minute earlier is not. Pin the inclusive
        # reading on both sides of the boundary.
        fire = FIRE_OFFPEAK_EPOCH  # 13:00 UTC+8, exactly 60 minutes before 14:00
        at_boundary = probe.evaluate_fire_at(
            fire, now=fire - 3600, straddle_minutes=60
        )
        self.assertTrue(at_boundary["peak"])
        self.assertEqual(at_boundary["verdict"], "defer-peak")
        self.assertEqual(
            int(datetime.fromisoformat(at_boundary["defer_to"]).timestamp()),
            FIRE_WINDOW_END_EPOCH,
        )
        one_minute_earlier = probe.evaluate_fire_at(
            fire - 60, now=fire - 3600, straddle_minutes=60
        )
        self.assertFalse(one_minute_earlier["peak"])
        self.assertEqual(one_minute_earlier["verdict"], "fire")

    def test_fire_at_clamped_primary_is_unknown(self) -> None:
        # A live primary whose reset was clamped to the horizon carries a
        # bound, not a real window end: cadence arithmetic never anchors
        # on it, so the fit leg degrades to status unknown (exit 1) while
        # the pricing half stays wall-clock-derived. Review r2 F10: the raw
        # reset is stated against the INJECTED clock (FIRE_NOW_EPOCH + 100
        # days, 60 days past the 40-day horizon), so the clamp engages
        # deterministically instead of leaning on the host wall clock.
        payload = json.dumps({"data": {"limits": [
            {
                "type": "TOKENS_LIMIT",
                "percentage": 95.0,
                "nextResetTime": (FIRE_NOW_EPOCH + 100 * 86400) * 1000,
            },
        ]}})
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            payload=payload,
        )
        self.assertEqual(code, 1)
        verdict = json.loads(out)
        self.assertEqual(verdict["status"], "unknown")
        self.assertIsNone(verdict["verdict"])
        self.assertIsNone(verdict["defer_to"])
        self.assertTrue(verdict["peak"])

    def test_fire_at_peak_with_need_minutes_blesses_exit2(self) -> None:
        # Peak fire time with 150 minutes at the fire instant (fits the
        # 120-minute estimate) and a fitting slot at the window's end: the
        # 18:00 slot sits half an hour past the reported reset inside the
        # fresh cadence window (270 minutes), so the pricing deferral to
        # the window end is blessed with exit 2.
        fire = FIRE_PEAK_EPOCH
        reset = fire + 150 * 60  # 17:30 UTC+8
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            payload=self._limits_payload(reset),
        )
        self.assertEqual(code, 2)
        verdict = json.loads(out)
        self.assertEqual(verdict["verdict"], "defer-peak")
        self.assertTrue(verdict["peak"])
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 150)
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()),
            FIRE_WINDOW_END_EPOCH,
        )

    def test_fire_at_never_writes_guard_flag(self) -> None:
        # --fire-at never writes the guard flag regardless of the verdict:
        # the early dispatch precedes the flag writer entirely, so not even
        # the shared lock file appears next to --write-flag's path.
        with tempfile.TemporaryDirectory() as tmpdir:
            flag = Path(tmpdir) / "budget-guard.flag"
            for argv, expected_code in (
                (["--fire-at", "2026-09-23T15:00:00+08:00"], 2),  # defer-peak
                (["--fire-at", "2026-09-23T13:00:00+08:00"], 0),  # fire
            ):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = probe.main([*argv, "--write-flag", str(flag)])
                self.assertEqual(code, expected_code)
                self.assertFalse(flag.exists())
                self.assertEqual(list(Path(tmpdir).iterdir()), [])

    def test_fire_at_unknown_limits_exit_1(self) -> None:
        # With --need-minutes and empty limits (a config without an API key
        # yields none): status unknown, no deferral invented, exit 1.
        direct = probe.evaluate_fire_at(
            FIRE_PEAK_EPOCH, now=FIRE_PEAK_EPOCH - 60, need_minutes=120, limits=[]
        )
        self.assertEqual(direct["status"], "unknown")
        self.assertIsNone(direct["verdict"])
        self.assertIsNone(direct["defer_to"])
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            with_key=False,
        )
        self.assertEqual(code, 1)
        verdict = json.loads(out)
        self.assertEqual(verdict["status"], "unknown")
        self.assertIsNone(verdict.get("verdict"))
        self.assertIsNone(verdict["defer_to"])

    def test_fire_at_without_need_minutes_never_touches_transport(self) -> None:
        # Pure pricing: a transport mock that raises on any call is never
        # invoked; the pricing verdict is computed from wall-clock data.
        def exploding_transport(url: str, headers: Mapping[str, str]) -> str:
            raise AssertionError("fire-at pricing must not invoke a transport")

        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._write_config(Path(tmpdir))
            out = io.StringIO()
            with mock.patch.object(
                probe, "urllib_transport", exploding_transport
            ), contextlib.redirect_stdout(out):
                code = probe.main([
                    "--runtime", "zcode", "--config", str(config),
                    "--fire-at", "2026-09-23T15:00:00+08:00",
                ])
        self.assertEqual(code, 2)
        verdict = json.loads(out.getvalue())
        self.assertEqual(verdict["verdict"], "defer-peak")
        self.assertTrue(verdict["peak"])

    def test_fire_at_secondary_only_binding_is_unknown(self) -> None:
        # A live secondary window never anchors a child deferral: with only
        # a secondary limit and --need-minutes set, the verdict is status
        # unknown (exit 1), never a deferral computed off the weekly window.
        pure = probe.evaluate_fire_at(
            FIRE_PEAK_EPOCH, now=FIRE_PEAK_EPOCH - 60, need_minutes=120,
            limits=[probe.make_limit(
                "secondary", 10.0, FIRE_PEAK_EPOCH + 3600, now=FIRE_PEAK_EPOCH - 60
            )],
        )
        self.assertEqual(pure["status"], "unknown")
        self.assertIsNone(pure["verdict"])
        payload = json.dumps({"data": {"limits": [
            {
                "type": "TIME_LIMIT",
                "percentage": 2.0,
                "nextResetTime": (FIRE_PEAK_EPOCH + 3600) * 1000,
            },
        ]}})
        code, out = self._fire_at_main(
            ["--fire-at", "2026-09-23T15:00:00+08:00", "--need-minutes", "120"],
            payload=payload,
        )
        self.assertEqual(code, 1)
        verdict = json.loads(out)
        self.assertEqual(verdict["status"], "unknown")
        self.assertIsNone(verdict["verdict"])

    # --- Task 2 (F9): fire-at straddle band crosses midnight. Window
    # fixtures 00:30-04:30 UTC+8 with straddle 60: the straddle band's
    # lower bound (30 - 60 = -30) wraps negative, so the peak decision
    # must price the pre-midnight tail band against the WINDOW-START day
    # (the next day) while the wrapped morning arm keeps the fire's own
    # day. Fixture dates: 2026-09-25 Friday, 26 Saturday, 27 Sunday,
    # 28 Monday (2026-09-23 Wednesday stays the anchor from Task 1).

    def test_straddle_tail_crossing_midnight_is_peak_on_weekday_window_start(self) -> None:
        # F9: Sunday 23:45 UTC+8 sits in the pre-midnight straddle tail
        # band before a midnight-crossing Monday window start (00:30-04:30,
        # straddle 60): peak True because the WINDOW-START day (Monday) is
        # Mon-Fri, not the fire day (Sunday). The deferral anchors on the
        # window-start day too: Monday 04:30, never Sunday's end.
        self.assertEqual(datetime(2026, 9, 27, tzinfo=TZ8).weekday(), 6)  # Sunday
        fire = int(datetime(2026, 9, 27, 23, 45, tzinfo=TZ8).timestamp())
        monday_end = int(datetime(2026, 9, 28, 4, 30, tzinfo=TZ8).timestamp())
        pure = probe.evaluate_fire_at(
            fire, now=fire - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertTrue(pure["peak"])
        self.assertEqual(pure["verdict"], "defer-peak")
        self.assertEqual(
            int(datetime.fromisoformat(pure["defer_to"]).timestamp()), monday_end
        )
        # With need_minutes that fits: the fire instant sees 495 minutes of
        # the reported window (resets Monday 08:00) and the Monday 04:30
        # slot sees 210, both fitting the 120-minute estimate, so the
        # deferral is blessed as defer-peak to the window-start day's end.
        reset = int(datetime(2026, 9, 28, 8, 0, tzinfo=TZ8).timestamp())
        fitted = probe.evaluate_fire_at(
            fire, now=fire - 3600, need_minutes=120, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
            limits=[probe.make_limit("primary", 50.0, reset, now=fire - 3600)],
        )
        self.assertTrue(fitted["peak"])
        self.assertEqual(fitted["verdict"], "defer-peak")
        self.assertTrue(fitted["fits"])
        self.assertEqual(
            int(datetime.fromisoformat(fitted["defer_to"]).timestamp()), monday_end
        )

    def test_straddle_tail_slot_unfit_defers_reset_past_anchored_slot(self) -> None:
        # F9 tail-band slot-unfit rung: Sunday 2026-09-27 23:45 UTC+8 sits in
        # the pre-midnight straddle tail band before the midnight-crossing
        # Monday 00:30-04:30 window start (straddle 60), so the deferred
        # pricing slot is Monday 04:30. With the reported primary window
        # resetting Monday 08:00, the fire instant sees 495 minutes (fits
        # the 300-minute estimate) but the Monday 04:30 slot sees only 210:
        # the slot is fit-checked before the deferral is blessed, so the
        # verdict is defer-reset to the containing window's end strictly
        # after the slot (_fire_at_window_end(slot_epoch, R) = Monday 08:00),
        # never the slot itself and never defer-peak.
        self.assertEqual(datetime(2026, 9, 27, tzinfo=TZ8).weekday(), 6)  # Sunday
        fire = int(datetime(2026, 9, 27, 23, 45, tzinfo=TZ8).timestamp())
        monday_reset = int(datetime(2026, 9, 28, 8, 0, tzinfo=TZ8).timestamp())
        monday_slot = int(datetime(2026, 9, 28, 4, 30, tzinfo=TZ8).timestamp())
        slot_epoch = probe._fire_at_peak_window_end(
            datetime(2026, 9, 27, 23, 45, tzinfo=TZ8),
            probe._parse_hhmm("00:30"), probe._parse_hhmm("04:30"), 60,
        )
        self.assertEqual(slot_epoch, monday_slot)
        verdict = probe.evaluate_fire_at(
            fire, now=fire - 3600, need_minutes=300, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
            limits=[probe.make_limit("primary", 50.0, monday_reset, now=fire - 3600)],
        )
        self.assertEqual(verdict["status"], "ok")
        self.assertTrue(verdict["peak"])
        self.assertEqual(verdict["verdict"], "defer-reset")
        self.assertTrue(verdict["fits"])
        self.assertEqual(verdict["minutes_remaining_at_fire"], 495)
        defer_epoch = int(datetime.fromisoformat(verdict["defer_to"]).timestamp())
        self.assertEqual(
            defer_epoch, probe._fire_at_window_end(slot_epoch, monday_reset)
        )
        self.assertEqual(defer_epoch, monday_reset)
        self.assertNotEqual(defer_epoch, slot_epoch)

    def test_straddle_tail_into_weekend_window_is_not_peak(self) -> None:
        # F9 weekend arm: Friday 23:45 sits in the tail band before a
        # SATURDAY window start (00:30-04:30, straddle 60); the
        # window-start day is a weekend day, so there is no weekday peak
        # to straddle into: peak False, verdict fire.
        self.assertEqual(datetime(2026, 9, 25, tzinfo=TZ8).weekday(), 4)  # Friday
        fire = int(datetime(2026, 9, 25, 23, 45, tzinfo=TZ8).timestamp())
        self.assertEqual(datetime(2026, 9, 26, tzinfo=TZ8).weekday(), 5)  # Saturday
        verdict = probe.evaluate_fire_at(
            fire, now=fire - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertFalse(verdict["peak"])
        self.assertEqual(verdict["verdict"], "fire")

    def test_straddle_tail_minute_boundary(self) -> None:
        # F9 tail threshold: start 00:30 (minute 30) with straddle 60 puts
        # the tail-band threshold at 1440 - (60 - 30) = 1410 (23:30). A
        # 23:29 fire (minute 1409) is one minute shy: not peak; a 23:30
        # fire is in the tail band of the Thursday-start window: peak
        # (Wednesday fire, Thursday window-start day - both weekdays, so
        # the minute boundary is the only variable).
        self.assertEqual(datetime(2026, 9, 23, tzinfo=TZ8).weekday(), 2)
        before = int(datetime(2026, 9, 23, 23, 29, tzinfo=TZ8).timestamp())
        not_peak = probe.evaluate_fire_at(
            before, now=before - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertFalse(not_peak["peak"])
        self.assertEqual(not_peak["verdict"], "fire")
        at = int(datetime(2026, 9, 23, 23, 30, tzinfo=TZ8).timestamp())
        peak = probe.evaluate_fire_at(
            at, now=at - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertTrue(peak["peak"])
        self.assertEqual(peak["verdict"], "defer-peak")
        # F9 anchor pin on the boundary: in pure-pricing mode defer_to IS
        # the pricing slot itself, the window-start day's (Thursday's)
        # 04:30 end, never a cadence window end. The expected slot is
        # pinned to a concrete literal (and the helper cross-checked
        # against it), so an anchor regression of any amount (for example
        # a one-hour shift of _fire_at_peak_window_end) fails this gate.
        self.assertEqual(datetime(2026, 9, 24, tzinfo=TZ8).weekday(), 3)  # Thursday
        thursday_end = int(datetime(2026, 9, 24, 4, 30, tzinfo=TZ8).timestamp())
        self.assertEqual(
            int(datetime.fromisoformat(peak["defer_to"]).timestamp()), thursday_end
        )
        self.assertEqual(
            probe._fire_at_peak_window_end(
                datetime(2026, 9, 23, 23, 30, tzinfo=TZ8),
                probe._parse_hhmm("00:30"), probe._parse_hhmm("04:30"), 60,
            ),
            thursday_end,
        )

    def test_post_midnight_morning_before_start_stays_peak(self) -> None:
        # F9 wrapped-morning arm kept: fire Wednesday 00:10 falls inside
        # today's wrapped negative band bound (-30 <= 10 < 270) before the
        # same-day midnight-crossing start: peak True and the deferral
        # anchors on the SAME day's window end (04:30), because the
        # window-start day is the fire's own day here - only the
        # pre-midnight tail band rolls the day forward (a two-band
        # implementation keeping only head+tail arms silently drops this
        # arm). Saturday 00:10 in the same window: the window-start day is
        # the fire's own day and a weekend, so peak False.
        self.assertEqual(datetime(2026, 9, 23, tzinfo=TZ8).weekday(), 2)
        fire = int(datetime(2026, 9, 23, 0, 10, tzinfo=TZ8).timestamp())
        wednesday_end = int(datetime(2026, 9, 23, 4, 30, tzinfo=TZ8).timestamp())
        verdict = probe.evaluate_fire_at(
            fire, now=fire - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertTrue(verdict["peak"])
        self.assertEqual(verdict["verdict"], "defer-peak")
        self.assertEqual(
            int(datetime.fromisoformat(verdict["defer_to"]).timestamp()),
            wednesday_end,
        )
        self.assertEqual(datetime(2026, 9, 26, tzinfo=TZ8).weekday(), 5)
        saturday_fire = int(datetime(2026, 9, 26, 0, 10, tzinfo=TZ8).timestamp())
        weekend = probe.evaluate_fire_at(
            saturday_fire, now=saturday_fire - 3600, straddle_minutes=60,
            peak_start="00:30", peak_end="04:30",
        )
        self.assertFalse(weekend["peak"])
        self.assertEqual(weekend["verdict"], "fire")

if __name__ == "__main__":
    unittest.main()
