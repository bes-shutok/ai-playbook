#!/usr/bin/env python3
"""Hermetic tests for the budget-guard PreToolUse backstop hook.

Subprocess-invokes the thin shell adapters and the agent-agnostic core with
synthetic flag files in tmp directories. No network, no credentials.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
from datetime import datetime
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / "agents/hooks/budget-guard"
CORE = HOOK_DIR / "budget_guard_core.py"
ZCODE_SH = HOOK_DIR / "zcode.sh"
CODEX_SH = HOOK_DIR / "codex.sh"

sys.path.insert(0, str(HOOK_DIR))
import budget_guard_core  # noqa: E402

# The canonical shared-guard-lock contract lives in the watcher module; the
# marker interleaving witness below proves the hook cleanup serializes on
# the same lock file the probe writer and the watcher use.
sys.path.insert(0, str(ROOT / "scripts"))
import execute_plan_resume_watcher as resume_watcher  # noqa: E402

# Single source of truth for the shared fixture: the ISO string is derived
# from the same epoch, so the two can never drift apart or go stale.
RESET_EPOCH = int(time.time()) + 3600
RESET_ISO = datetime.fromtimestamp(RESET_EPOCH).astimezone().isoformat()

REASON = (
    "Provider quota window for runtime {runtime} ends at " + RESET_ISO + ". "
    "Do not start new tool work. Finish the current sub-agent step, land the "
    "pending done commit if any, record the budget pause, and schedule the "
    "resume."
)


def write_flag_content(runtime: str = "zcode",
                       reset_at_epoch: int = RESET_EPOCH,
                       reset_at_iso: str = RESET_ISO, plan: str | None = "my-plan",
                       armed_by: str | None = "probe") -> str:
    # Default armed_by=probe mirrors the probe-written fixture flag; None
    # omits the line entirely so the reason's unknown fallback stays pinned.
    lines = [
        "runtime={}".format(runtime),
        "reset_at_epoch={}".format(reset_at_epoch),
        "reset_at_iso={}".format(reset_at_iso),
    ]
    if plan:
        lines.append("plan={}".format(plan))
    if armed_by:
        lines.append("armed_by={}".format(armed_by))
    return "\n".join(lines) + "\n"


def write_flag(dir_path: Path, runtime: str = "zcode",
               reset_at_epoch: int = RESET_EPOCH,
               reset_at_iso: str = RESET_ISO, plan: str | None = "my-plan",
               name: str = "budget-guard.flag",
               armed_by: str | None = "probe") -> Path:
    path = dir_path / name
    path.write_text(
        write_flag_content(runtime, reset_at_epoch, reset_at_iso, plan, armed_by),
        encoding="utf-8",
    )
    return path


def suffix_reason(flag_path: Path, armed_by: str = "probe") -> str:
    # The exact-envelope tail: the reason now ends with the guard flag path
    # and armed-by attribution (Task 3, origin 1 gap 4).
    return " Budget guard flag: {} (armed by {}).".format(flag_path, armed_by)


def run_hook(script: Path, flag_path: Path,
             fired_path: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [str(script), "--flag-path", str(flag_path)]
    if fired_path is not None:
        cmd += ["--fired-path", str(fired_path)]
    return subprocess.run(
        cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=10,
    )


class BudgetGuardHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_flag_absent_passes(self) -> None:
        flag = self.tmp / "absent.flag"
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_zcode_block_shape_and_exit(self) -> None:
        flag = write_flag(self.tmp)
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        expected = json.dumps(
            {"decision": "block",
             "reason": REASON.format(runtime="zcode") + suffix_reason(flag)}
        )
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.returncode, 2)

    def test_codex_deny_shape(self) -> None:
        flag = write_flag(self.tmp, runtime="codex")
        fired = self.tmp / "budget-guard.fired"
        result = run_hook(CODEX_SH, flag, fired)
        expected = json.dumps(
            {"permissionDecision": "deny",
             "reason": REASON.format(runtime="codex") + suffix_reason(flag)}
        )
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.returncode, 0)
        # The codex path must write the fired marker on its block, too: the
        # deny-envelope decision table uses the marker to discriminate
        # "envelope rejected" from "hook never ran" (mirrors the zcode
        # witness in test_fired_marker_written_on_block).
        self.assertTrue(fired.exists())
        self.assertEqual(
            fired.read_text(encoding="utf-8").strip(), str(RESET_EPOCH)
        )

    def test_reason_names_armed_by_manual(self) -> None:
        # A manual drive writes armed_by=manual; the reason must attribute
        # the arming, not assume the probe.
        flag = write_flag(self.tmp, armed_by="manual")
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        expected = json.dumps(
            {"decision": "block",
             "reason": REASON.format(runtime="zcode") + suffix_reason(flag, "manual")}
        )
        self.assertEqual(result.stdout, expected)

    def test_reason_names_armed_by_unknown_when_line_missing(self) -> None:
        # A legacy flag with no armed_by line reads unknown.
        flag = write_flag(self.tmp, armed_by=None)
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        expected = json.dumps(
            {"decision": "block",
             "reason": REASON.format(runtime="zcode") + suffix_reason(flag, "unknown")}
        )
        self.assertEqual(result.stdout, expected)

    def test_flag_runtime_wins_over_adapter_runtime(self) -> None:
        # The flag's own runtime line is the forensic truth: a codex adapter
        # reading a flag armed by zcode must name zcode in the reason.
        flag = write_flag(self.tmp, runtime="zcode")
        result = run_hook(CODEX_SH, flag, self.tmp / "budget-guard.fired")
        self.assertIn(REASON.format(runtime="zcode") + suffix_reason(flag), result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_non_integer_reset_epoch_fails_open(self) -> None:
        flag = write_flag(self.tmp, reset_at_epoch="not-a-number")  # type: ignore[arg-type]
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_garbage_flag_content_fails_open(self) -> None:
        flag = self.tmp / "budget-guard.flag"
        flag.write_text("total garbage, no key=value lines\n", encoding="utf-8")
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_flag_missing_required_keys_fails_open(self) -> None:
        flag = self.tmp / "budget-guard.flag"
        flag.write_text("runtime=zcode\nplan=x\n", encoding="utf-8")
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fired_marker_single_intervention(self) -> None:
        flag = write_flag(self.tmp)
        fired = self.tmp / "budget-guard.fired"
        # Matching marker (same window epoch): suppress further blocks.
        fired.write_text(str(RESET_EPOCH) + "\n", encoding="utf-8")
        result = run_hook(ZCODE_SH, flag, fired)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fired_marker_written_on_block(self) -> None:
        flag = write_flag(self.tmp)
        fired = self.tmp / "budget-guard.fired"
        result = run_hook(ZCODE_SH, flag, fired)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(fired.exists())
        # The marker binds to the window: it records the flag's reset epoch.
        self.assertEqual(
            fired.read_text(encoding="utf-8").strip(), str(RESET_EPOCH)
        )

    def test_stale_fired_marker_still_blocks(self) -> None:
        # A marker left over from an older window must not suppress the new
        # window's single block: mismatched epoch → marker removed, block fires.
        flag = write_flag(self.tmp)
        fired = self.tmp / "budget-guard.fired"
        fired.write_text(str(RESET_EPOCH - 5 * 86400) + "\n", encoding="utf-8")
        result = run_hook(ZCODE_SH, flag, fired)
        self.assertEqual(result.returncode, 2)
        self.assertIn("block", result.stdout)
        self.assertEqual(
            fired.read_text(encoding="utf-8").strip(), str(RESET_EPOCH)
        )

    def test_fired_marker_write_failure_still_blocks(self) -> None:
        flag = write_flag(self.tmp)
        # A directory at the fired-marker path makes the marker write fail.
        fired = self.tmp / "budget-guard.fired"
        fired.mkdir()
        result = run_hook(ZCODE_SH, flag, fired)
        self.assertEqual(result.returncode, 2)
        self.assertIn("block", result.stdout)

    def test_expired_flag_ignored_and_removed(self) -> None:
        flag = write_flag(self.tmp, reset_at_epoch=int(time.time()) - 60)
        fired = self.tmp / "budget-guard.fired"
        fired.write_text(str(int(time.time()) - 60) + "\n", encoding="utf-8")
        result = run_hook(ZCODE_SH, flag, fired)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse(flag.exists())
        self.assertFalse(fired.exists())

    def test_flag_read_error_fail_open(self) -> None:
        # A directory at the flag path makes the flag read fail: fail open.
        flag_dir = self.tmp / "not-a-file.flag"
        flag_dir.mkdir()
        result = run_hook(ZCODE_SH, flag_dir, self.tmp / "budget-guard.fired")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_hook_completes_within_host_timeout(self) -> None:
        flag = write_flag(self.tmp)
        start = time.monotonic()
        result = run_hook(ZCODE_SH, flag, self.tmp / "budget-guard.fired")
        elapsed = time.monotonic() - start
        # Plan budget: the hook must finish well inside the 5-10s host
        # timeout, so assert the tighter 5s bound here; the subprocess hard
        # timeout below stays at 10s as the last-resort backstop.
        self.assertLess(elapsed, 5)
        self.assertEqual(result.returncode, 2)
        # Static arm, scoped to import lines only: the module must not import
        # any network-rooted package. Checking bare words anywhere in the
        # source would false-positive on prose (for example a docstring that
        # merely mentions the word "socket").
        banned_roots = {"urllib", "socket", "http", "requests"}
        for line in CORE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                module = stripped.split(" ", 2)[1]
                root = module.lstrip(".").split(".")[0]
                self.assertNotIn(root, banned_roots, "network import: " + stripped)

    def test_expired_flag_replaced_by_probe_not_unlinked(self) -> None:
        # In-process witness for the expiry re-read guard: the first read
        # sees an expired window, but a concurrent probe has meanwhile
        # replaced the flag with a live one; the re-read sees the future
        # epoch and the hook must NOT unlink the flag (and must not block).
        flag = write_flag(self.tmp, reset_at_epoch=int(time.time()) - 60)
        fired = self.tmp / "budget-guard.fired"
        fired.write_text("fired\n", encoding="utf-8")
        future_content = write_flag_content(reset_at_epoch=int(time.time()) + 3600)
        expired_content = flag.read_text(encoding="utf-8")
        out = io.StringIO()
        with mock.patch.object(
            Path, "read_text", side_effect=[expired_content, future_content]
        ), contextlib.redirect_stdout(out):
            code = budget_guard_core.main(
                ["--runtime", "zcode", "--flag-path", str(flag), "--fired-path", str(fired)]
            )
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")
        self.assertTrue(flag.exists())
        self.assertTrue(fired.exists())

    def test_guard_cleanup_does_not_remove_replaced_marker(self) -> None:
        # Shared guard-lock replacement interleaving on the fired marker: the
        # stale-marker cleanup re-checks the marker content while holding the
        # shared budget-guard.lock (the same lock the probe writer and the
        # watcher's compare-and-delete use), so a marker re-written for the
        # current window between the cleanup's decision and its removal
        # survives and the hook still fires its single block for this window.
        flag = write_flag(self.tmp)
        fired = self.tmp / "budget-guard.fired"
        old_marker = str(RESET_EPOCH - 5 * 86400)
        fired.write_text(old_marker + "\n", encoding="utf-8")
        lock_path = resume_watcher.guard_lock_path(flag)
        self.assertEqual(lock_path.name, "budget-guard.lock")
        self.assertEqual(lock_path.parent, flag.parent)
        out = io.StringIO()
        hook_outcome = {}

        with resume_watcher.budget_guard_lock(flag) as held:
            self.assertTrue(held)
            started = threading.Event()

            def hook_run() -> None:
                started.set()
                with contextlib.redirect_stdout(out):
                    hook_outcome["code"] = budget_guard_core.main(
                        ["--runtime", "zcode", "--flag-path", str(flag), "--fired-path", str(fired)]
                    )

            cleaner = threading.Thread(target=hook_run)
            cleaner.start()
            # The `started` marker (r1 F29) proves the thread reached its
            # body before the blocked assertion, so scheduler starvation
            # cannot make the blocking-half witness vacuous.
            self.assertTrue(started.wait(5), "stale-marker cleanup witness never started")
            cleaner.join(0.5)
            # The hook decided to remove the stale marker and is blocked at
            # the shared-lock removal, not past it.
            self.assertTrue(cleaner.is_alive(), "stale-marker cleanup did not block on the shared guard lock")
            # The replacement interleaving: the current window's marker is
            # written while the cleanup waits (the block path's critical
            # section holds this same lock).
            fired.write_text(str(RESET_EPOCH) + "\n", encoding="utf-8")
        cleaner.join(5)
        self.assertFalse(cleaner.is_alive())
        # The locked re-check saw the current window's marker, skipped the
        # removal, and fell through to the single block for this window.
        self.assertEqual(hook_outcome["code"], budget_guard_core.EXIT_BLOCK_ZCODE)
        self.assertIn('"decision": "block"', out.getvalue())
        self.assertTrue(fired.exists())
        self.assertEqual(fired.read_text(encoding="utf-8").strip(), str(RESET_EPOCH))

    def test_core_blocks_without_any_socket(self) -> None:
        # In-process network-abstinence arm: the core's full blocking path
        # (live flag, no fired marker) runs to a block decision while any
        # socket construction is denied; an attempted connection would raise
        # AssertionError and fail this test.
        flag = write_flag(self.tmp)
        fired = self.tmp / "budget-guard.fired"
        out = io.StringIO()
        with mock.patch.object(
            socket, "socket", side_effect=AssertionError("network disabled")
        ), contextlib.redirect_stdout(out):
            code = budget_guard_core.main(
                ["--runtime", "zcode", "--flag-path", str(flag), "--fired-path", str(fired)]
            )
        self.assertEqual(code, budget_guard_core.EXIT_BLOCK_ZCODE)
        self.assertIn('"decision": "block"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
