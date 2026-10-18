#!/usr/bin/env python3
"""Hermetic tests for the standing resume watcher state machine.

Fake clock, fake automation, fake launchd, and temporary authoring state.
The integration cases exercise the authoring watcher CLI operations, injected
clock behavior, and schedule / replace / progress / cancellation / reload /
callback paths. No live ``docs/tmp/`` fixtures; guard-flag interleavings run
against real temporary files with the real probe writer and budget-guard core.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
HOOK_DIR = SCRIPTS.parent / "agents/hooks/budget-guard"
sys.path.insert(0, str(HOOK_DIR))

import budget_guard_core  # noqa: E402
import execute_plan_resume_watcher as watcher  # noqa: E402
import execute_plan_runtime as runtime  # noqa: E402
import plan_shape  # noqa: E402
import quota_window_probe as probe  # noqa: E402

import plistlib  # noqa: E402
import shlex  # noqa: E402
import subprocess  # noqa: E402


class FakeClock:
    """Deterministic clock the driver and the watcher both read."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = float(start)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)

    def iso(self) -> str:
        return datetime.fromtimestamp(self.now).astimezone().isoformat()


class FakeStateAdapter(watcher.WatcherStateAdapter):
    """In-memory machine state implementing the adapter protocol.

    Mirrors the driver's compare-and-swap semantics (watcher id, generation,
    boundary generation) so the workflow-neutral state machine can be
    exercised without any file system.
    """

    def __init__(self, state: dict | None = None) -> None:
        self.state = {
            "plan_slug": "fixture",
            "workflow_state": "active",
            "generation": 0,
            "progress_revision": 0,
            "boundary_generation": 0,
            "resume_watcher": None,
            "user_interrupt": None,
            "updated_at": 0.0,
            "repo_root": "/tmp/fixture-root",
            "plan_path": "/tmp/fixture-root/plan.md",
            "plan_digest": "a" * 64,
        }
        if state:
            self.state.update(state)
        self.peer_touched = False
        self.history: list[dict] = []

    def read_state(self) -> dict:
        return dict(self.state)

    def _cas_guard(self, transition: dict) -> dict | None:
        current = self.state["resume_watcher"]
        current_id = current["watcher_id"] if isinstance(current, dict) else None
        if (
            transition.get("expected_watcher_id") != current_id
            or transition.get("expected_generation") != self.state["generation"]
            or transition.get("expected_boundary_generation") != self.state["boundary_generation"]
        ):
            return {
                "status": "blocked",
                "reason_code": "stale-attempt",
                "cas_applied": False,
                "resume_watcher": current,
                "superseded_watcher_id": None,
            }
        return None

    def compare_and_swap_schedule(self, transition: dict) -> dict:
        stale = self._cas_guard(transition)
        if stale:
            return stale
        receipt = dict(transition["receipt"])
        current = self.state["resume_watcher"]
        receipt["replaces"] = current["watcher_id"] if isinstance(current, dict) else None
        self.state["resume_watcher"] = receipt
        self.state["boundary_generation"] += 1
        self.history.append({"event": "resume-watcher-scheduled", "watcher_id": receipt["watcher_id"]})
        return {"status": "success", "reason_code": "resume-watcher-scheduled", "resume_watcher": receipt, "cas_applied": True}

    def compare_and_swap_supersede(self, transition: dict) -> dict:
        stale = self._cas_guard(transition)
        if stale:
            return stale
        current = self.state["resume_watcher"]
        superseded = current["watcher_id"] if isinstance(current, dict) else None
        self.state["resume_watcher"] = None
        self.state["boundary_generation"] += 1
        self.history.append({"event": "resume-watcher-superseded", "watcher_id": superseded})
        return {
            "status": "success",
            "reason_code": "resume-watcher-cleared",
            "resume_watcher": None,
            "superseded_watcher_id": superseded,
            "cas_applied": True,
        }

    def semantic_progress_changed(self, snapshot: dict, expected_progress_revision: int) -> bool:
        return int(snapshot["progress_revision"]) != int(expected_progress_revision)

    def peer_resumed(self, snapshot: dict, scheduled_at_epoch: int) -> bool:
        return self.peer_touched

    def archived_or_completed(self, snapshot: dict) -> bool:
        return snapshot["workflow_state"] in {"complete", "terminal"}

    def aborted_or_interrupted(self, snapshot: dict, scheduled_at_epoch: int) -> bool:
        if snapshot["workflow_state"] == "aborted":
            return True
        return watcher.interrupt_after(snapshot.get("user_interrupt"), scheduled_at_epoch)

    def boundary_generation(self, snapshot: dict) -> int:
        return int(snapshot["boundary_generation"])

    def projection(self, snapshot: dict) -> str:
        return watcher.render_manifest_projection(snapshot)


def known_continue_report(reset_at_epoch: int, binding: str = "primary") -> dict:
    return {
        "runtime": "fixture",
        "status": "ok",
        "binding": binding,
        "pause_decision": "continue",
        "reasons": [],
        "limits": [
            {
                "kind": binding,
                "used_percent": 40.0,
                "reset_at_epoch": int(reset_at_epoch),
                "reset_at_iso": datetime.fromtimestamp(int(reset_at_epoch)).astimezone().isoformat(),
                "minutes_remaining": 90,
            }
        ],
    }


def write_guard_flag(flag_path: Path, reset_at_epoch: int) -> None:
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text(
        "\n".join(
            [
                "runtime=fixture",
                f"reset_at_epoch={int(reset_at_epoch)}",
                "reset_at_iso=" + datetime.fromtimestamp(int(reset_at_epoch)).astimezone().isoformat(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def flag_epoch(flag_path: Path) -> int | None:
    fields = watcher.parse_guard_flag(flag_path.read_text(encoding="utf-8"))
    value = fields.get("reset_at_epoch", "")
    try:
        return int(value)
    except ValueError:
        return None


class WatcherStateMachineTest(unittest.TestCase):
    """Pure state-machine cases over the fake in-memory machine state."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.adapter = FakeStateAdapter()
        self.automation_calls: list[dict] = []
        self.chain = [
            watcher.AutomationScheduler(self.automation_result),
            watcher.LaunchdOneShotScheduler(self.tmp / "job", self.tmp / "sentinel", bootstrap=lambda _job: (True, "")),
            watcher.ReportOnlyScheduler(),
        ]
        self.plan_path = "/tmp/fixture-root/plan.md"

    def automation_result(self, request: dict) -> dict:
        self.automation_calls.append(request)
        return {"scheduled": True, "id": f"auto-{len(self.automation_calls)}"}

    def boundary(self, report: dict, **kwargs) -> dict:
        return watcher.record_budget_boundary(
            self.adapter,
            self.chain,
            probe_report=report,
            plan_slug="fixture",
            plan_path=kwargs.pop("plan_path", self.plan_path),
            plan_digest=kwargs.pop("plan_digest", "a" * 64),
            repo_root=kwargs.pop("repo_root", "/tmp/fixture-root"),
            watcher_id_factory=kwargs.pop("watcher_id_factory", None),
            clock=kwargs.pop("clock", lambda: 5_000.0),
            **kwargs,
        )

    def test_reset_rounds_up_to_whole_minute_plus_one(self) -> None:
        # A reset landing exactly on a minute still resumes one minute after
        # that boundary; a reset one second past it rounds up first.
        self.assertEqual(watcher.compute_fire_epoch(1_800_000_000), 1_800_000_060)
        self.assertEqual(watcher.compute_fire_epoch(1_800_000_001), 1_800_000_120)
        self.assertEqual(watcher.compute_fire_epoch(1_800_000_059), 1_800_000_120)
        self.assertEqual(watcher.compute_fire_epoch(1_800_000_060), 1_800_000_120)
        fire = watcher.compute_fire_epoch(1_800_000_001)
        iso = watcher.compute_resume_at_iso(fire)
        self.assertEqual(int(datetime.fromisoformat(iso).timestamp()), fire)

    def test_interrupt_after_same_second_boundary_decides_resume(self) -> None:
        # r1 O30: the equality boundary is decisive. An interrupt recorded
        # in the same second as the scheduling epoch is not newer, so the
        # watcher resumes; one second later it stands down. Malformed or
        # absent fields never trip.
        scheduled = 1_000.0
        same_second = datetime.fromtimestamp(scheduled, timezone.utc).astimezone().isoformat()
        self.assertFalse(watcher.interrupt_after(same_second, scheduled))
        self.assertTrue(
            watcher.interrupt_after(datetime.fromtimestamp(scheduled + 1, timezone.utc).astimezone().isoformat(), scheduled)
        )
        self.assertFalse(watcher.interrupt_after(None, scheduled))
        self.assertFalse(watcher.interrupt_after("   ", scheduled))
        self.assertFalse(watcher.interrupt_after("not-a-timestamp", scheduled))

    def test_known_continue_schedules_single_watcher_at_reset_plus_one_minute(self) -> None:
        reset = 5_400_000_030
        result = self.boundary(known_continue_report(reset))
        self.assertEqual(result["boundary"], "install")
        self.assertEqual(result["replaces"], None)
        self.assertEqual(result["fire_epoch"], watcher.compute_fire_epoch(reset))
        receipt = self.adapter.read_state()["resume_watcher"]
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["reset_at_epoch"], reset)
        self.assertEqual(receipt["status"], "pending")
        # Exactly one automation create, carrying the rounded fire epoch.
        self.assertEqual(len(self.automation_calls), 1)
        self.assertEqual(self.automation_calls[0]["fire_at_epoch"], result["fire_epoch"])

    def test_double_schedule_is_idempotent_and_never_stacks(self) -> None:
        self.boundary(known_continue_report(5_400_000_090))
        first = self.adapter.read_state()["resume_watcher"]
        # A replayed schedule transition with the pre-install expectations is
        # a stale compare-and-swap: exactly one watcher stays in machine state.
        stale = self.adapter.compare_and_swap_schedule(
            watcher.build_schedule_transition(
                FakeStateAdapter().read_state(),
                watcher_id="rw-replay",
                plan_slug="fixture",
                repo_root="/tmp/fixture-root",
                plan_path=self.plan_path,
                plan_digest="a" * 64,
                reset_at_epoch=5_400_000_090,
                scheduled_at_epoch=5_000,
                binding="primary",
            )
        )
        self.assertEqual(stale["status"], "blocked")
        self.assertEqual(stale["reason_code"], "stale-attempt")
        again = self.adapter.read_state()["resume_watcher"]
        self.assertEqual(again, first)

    def test_watcher_unknown_budget_is_report_only(self) -> None:
        unknown = probe._unknown_report("fixture", ["no usable limits"])
        result = self.boundary(unknown)
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["classification"], "unknown")
        self.assertIsNone(result["scheduling"])
        self.assertIsNone(self.adapter.read_state()["resume_watcher"])
        # Report-only bookkeeping: the exact manual resume command is named.
        self.assertEqual(result["manual_command"], f"execute {self.plan_path}")
        self.assertEqual(self.automation_calls, [])

    def test_watcher_known_then_unknown_supersedes_pending(self) -> None:
        installed = self.boundary(known_continue_report(5_400_000_090))
        self.assertEqual(installed["boundary"], "install")
        result = self.boundary(probe._unknown_report("fixture", ["stale data"]))
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["superseded_watcher_id"], installed["watcher_id"])
        self.assertIsNone(self.adapter.read_state()["resume_watcher"])
        self.assertIn(
            "resume-watcher-superseded",
            [event["event"] for event in self.adapter.history],
        )
        # A late callback from the superseded watcher is fenced by the
        # watcher-id fence it is subsumed by (r1 F20: no self_disarm
        # surface): the superseded receipt refuses with a watcher-id
        # mismatch and mutates nothing.
        late = dict(installed["machine"]["resume_watcher"])
        decision = watcher.evaluate_fire(self.adapter, late)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("watcher-id", decision["mismatches"])
        self.assertIsNone(self.adapter.read_state()["resume_watcher"])

    def test_watcher_known_then_weekly_secondary_supersedes_pending(self) -> None:
        installed = self.boundary(known_continue_report(5_400_000_090))
        self.assertEqual(installed["boundary"], "install")
        automation_calls_before = len(self.automation_calls)
        secondary = known_continue_report(6_000_000_000, binding="secondary")
        result = self.boundary(secondary)
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["classification"], "weekly-secondary")
        self.assertEqual(result["superseded_watcher_id"], installed["watcher_id"])
        self.assertIsNone(result["scheduling"])
        self.assertIsNone(self.adapter.read_state()["resume_watcher"])
        # The weekly secondary binding schedules no watcher at all.
        self.assertEqual(len(self.automation_calls), automation_calls_before)

    def test_pause_abort_and_complete_boundaries_clear_pending_watcher(self) -> None:
        for report, kind in (
            ({**known_continue_report(5_400_000_090), "pause_decision": "pause"}, "pause"),
            (known_continue_report(5_400_000_090), "abort"),
            (known_continue_report(5_400_000_090), "complete"),
        ):
            installed = self.boundary(known_continue_report(5_400_000_120))
            self.assertEqual(installed["boundary"], "install")
            result = self.boundary(report, boundary_kind=kind)
            self.assertEqual(result["boundary"], "supersede")
            self.assertEqual(result["classification"], kind)
            self.assertIsNone(self.adapter.read_state()["resume_watcher"])

    def test_classify_boundary_wait_for_reset_is_non_schedulable(self) -> None:
        # A wait-for-reset boundary is a supersede-and-clear class: even
        # with status ok and a trusted binding reset epoch it never
        # installs a watcher (a watcher firing at reset+1min would
        # double-head a lane that is alive and waiting in-session), and any
        # pending watcher is cleared through the supersede operation.
        self.assertEqual(
            watcher.classify_boundary(
                {**known_continue_report(5_400_000_150), "pause_decision": "wait-for-reset"}
            ),
            "wait-for-reset",
        )
        installed = self.boundary(known_continue_report(5_400_000_090))
        self.assertEqual(installed["boundary"], "install")
        automation_calls_before = len(self.automation_calls)
        waiting = {
            **known_continue_report(5_400_000_150),
            "pause_decision": "wait-for-reset",
        }
        result = self.boundary(waiting)
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["classification"], "wait-for-reset")
        self.assertEqual(result["superseded_watcher_id"], installed["watcher_id"])
        self.assertIsNone(result["scheduling"])
        self.assertIsNone(self.adapter.read_state()["resume_watcher"])
        # The ride-through boundary schedules nothing at all.
        self.assertEqual(len(self.automation_calls), automation_calls_before)

    def test_classify_boundary_regression_fence(self) -> None:
        # No existing classification changes: pause classifies pause, a
        # known continue with a trusted binding epoch installs, an unknown
        # status is unknown, and the weekly secondary binding is
        # weekly-secondary.
        self.assertEqual(
            watcher.classify_boundary(
                {**known_continue_report(5_400_000_090), "pause_decision": "pause"}
            ),
            "pause",
        )
        self.assertEqual(
            watcher.classify_boundary(known_continue_report(5_400_000_090)),
            "install",
        )
        self.assertEqual(
            watcher.classify_boundary(probe._unknown_report("fixture", ["no data"])),
            "unknown",
        )
        self.assertEqual(
            watcher.classify_boundary(known_continue_report(5_400_000_090, binding="secondary")),
            "weekly-secondary",
        )
        # Precedence fence (review r1 F11): the decision check runs before
        # the status and binding checks, so a wait-for-reset decision
        # classifies wait-for-reset even on a weekly-secondary binding or
        # an unknown status (both non-schedulable anyway).
        self.assertEqual(
            watcher.classify_boundary(
                {
                    **known_continue_report(5_400_000_090, binding="secondary"),
                    "pause_decision": "wait-for-reset",
                }
            ),
            "wait-for-reset",
        )
        self.assertEqual(
            watcher.classify_boundary(
                {
                    **probe._unknown_report("fixture", ["no data"]),
                    "pause_decision": "wait-for-reset",
                }
            ),
            "wait-for-reset",
        )

    def test_watcher_replacement_is_single_and_fenced(self) -> None:
        first = self.boundary(known_continue_report(5_400_000_090))
        second = self.boundary(known_continue_report(5_400_000_150))
        self.assertEqual(second["boundary"], "install")
        self.assertEqual(second["replaces"], first["watcher_id"])
        receipt = self.adapter.read_state()["resume_watcher"]
        # One-watcher cardinality: the replacement, never a stack.
        self.assertEqual(receipt["watcher_id"], second["watcher_id"])
        self.assertEqual(receipt["replaces"], first["watcher_id"])
        self.assertEqual(receipt["boundary_generation"], 2)
        self.assertEqual(len(self.automation_calls), 2)
        # The replaced watcher's receipt is gone; a late callback from it is
        # fenced by the watcher-id mismatch (r1 F20: the self_disarm surface
        # is subsumed by evaluate_fire's fence), and the fire evaluation is
        # fenced outright without changing current state.
        decision = watcher.evaluate_fire(self.adapter, first["machine"]["resume_watcher"])
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("watcher-id", decision["mismatches"])
        after = self.adapter.read_state()
        self.assertEqual(after["resume_watcher"]["watcher_id"], second["watcher_id"])

    def test_stand_downs_and_untouched_state_resume(self) -> None:
        receipt = {
            "watcher_id": "rw-1",
            "plan_slug": "fixture",
            "repo_root": "/tmp/fixture-root",
            "plan_path": self.plan_path,
            "plan_digest": "a" * 64,
            "scheduled_at_epoch": 1_000,
            "reset_at_epoch": 2_000,
            "expected_generation": 0,
            "expected_progress_revision": 0,
            "boundary_generation": 1,
            "binding": "primary",
            "status": "pending",
            "replaces": None,
        }
        # The receipt is pending in machine state (scheduled earlier), and
        # the boundary generation moved with it.
        self.adapter.state["resume_watcher"] = dict(receipt)
        self.adapter.state["boundary_generation"] = 1
        # Untouched machine state: the watcher resumes with the plan-path prompt.
        decision = watcher.evaluate_fire(self.adapter, receipt)
        self.assertEqual(decision["decision"], "resume")
        self.assertEqual(decision["reason"], "untouched-state")
        self.assertIn(self.plan_path, decision["prompt"])
        # Semantic progress revision changed after the scheduling point.
        self.adapter.state["progress_revision"] = 3
        self.assertEqual(
            watcher.evaluate_fire(self.adapter, receipt),
            {"decision": "stand_down", "reason": "semantic-progress", "guards_cleared": False, "relaunch": False},
        )
        self.adapter.state["progress_revision"] = 0
        # A peer session resumed the work.
        self.adapter.peer_touched = True
        self.assertEqual(watcher.evaluate_fire(self.adapter, receipt)["reason"], "peer-resumed")
        self.adapter.peer_touched = False
        # The plan is archived or completed.
        self.adapter.state["workflow_state"] = "complete"
        self.assertEqual(watcher.evaluate_fire(self.adapter, receipt)["reason"], "archived-or-completed")
        self.adapter.state["workflow_state"] = "active"
        # The run was explicitly aborted.
        self.adapter.state["workflow_state"] = "aborted"
        self.assertEqual(watcher.evaluate_fire(self.adapter, receipt)["reason"], "aborted-or-interrupted")
        self.adapter.state["workflow_state"] = "active"
        # Interrupted after scheduling (newer than the scheduling epoch).
        self.adapter.state["user_interrupt"] = datetime.fromtimestamp(1_500, timezone.utc).astimezone().isoformat()
        self.assertEqual(watcher.evaluate_fire(self.adapter, receipt)["reason"], "aborted-or-interrupted")
        # A latched old interrupt (before the scheduling epoch) never trips.
        self.adapter.state["user_interrupt"] = datetime.fromtimestamp(500, timezone.utc).astimezone().isoformat()
        self.assertEqual(watcher.evaluate_fire(self.adapter, receipt)["decision"], "resume")

    def test_launchd_sentinel_self_disable_falls_back_to_report_only(self) -> None:
        job_dir = self.tmp / "launchd"
        sentinel = self.tmp / "launchd" / "self-disable"
        chain = [
            watcher.AutomationScheduler(None),
            watcher.LaunchdOneShotScheduler(job_dir, sentinel, bootstrap=lambda _job: (True, "")),
            watcher.ReportOnlyScheduler(),
        ]
        # First arm: the job definition is written, and the sentinel is NOT
        # created at arm time (r1 F1): the job's first fire creates it, so
        # the fire-time guard cannot short-circuit the job it guards.
        first = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertTrue(first["scheduled"])
        self.assertEqual(first["mechanism"], "launchd")
        self.assertFalse(sentinel.exists(), "arm-time sentinel creation makes the one-shot a no-op")
        self.assertTrue((job_dir / "ai-playbook.budget-resume.plist").exists())
        # Fire the job's command once for real: the sentinel is created by
        # the touch, and the manual command runs (a real pause would resume).
        payload = plistlib.loads((job_dir / "ai-playbook.budget-resume.plist").read_bytes())
        self.assertEqual(payload["ProgramArguments"][:2], ["/bin/sh", "-c"])
        marker = self.tmp / "resumed"
        command = payload["ProgramArguments"][2].replace("execute /tmp/p.md", f"touch '{marker}'")
        subprocess.run(["/bin/sh", "-c", command], check=True, capture_output=True)
        self.assertTrue(sentinel.exists())
        self.assertTrue(marker.exists())
        # A second fire self-disables: the guard short-circuits, the manual
        # command never runs again (the daily StartCalendarInterval is inert).
        marker.unlink()
        subprocess.run(["/bin/sh", "-c", command], check=True, capture_output=True)
        self.assertFalse(marker.exists())
        # Second arm while the sentinel exists: self-disable, then the
        # chain terminates in report-only naming the exact command and time.
        second = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_180, "resume_at_iso": "y", "manual_command": "execute /tmp/p.md"},
        )
        self.assertFalse(second["scheduled"])
        self.assertEqual(second["mechanism"], "report-only")
        self.assertEqual(second["result"]["manual_command"], "execute /tmp/p.md")
        self.assertEqual(second["result"]["resume_at_iso"], "y")
        self.assertEqual(
            [step["mechanism"] for step in second["trail"]],
            ["automation", "launchd", "report-only"],
        )
        self.assertEqual(second["trail"][1]["reason"], "sentinel self-disable file present")

    def test_launchd_bootstrap_failure_falls_through_to_report_only(self) -> None:
        # r2 F4: arming bootstraps the written plist into launchd; a failed
        # bootstrap is an honest not-scheduled (the inert plist is removed,
        # so no dead definition lingers) and the chain terminates in
        # report-only naming the exact manual command, never a false
        # scheduled=True that silently ends the pause chain with a resume
        # launchd never fires.
        job_dir = self.tmp / "launchd-boot-fail"
        sentinel = self.tmp / "sentinel-boot-fail"

        def failing_bootstrap(_job):
            return False, "Bootstrap failed: 5: Input/output error"

        chain = [
            watcher.AutomationScheduler(None),
            watcher.LaunchdOneShotScheduler(job_dir, sentinel, bootstrap=failing_bootstrap),
            watcher.ReportOnlyScheduler(),
        ]
        result = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "iso-boot", "manual_command": "execute /tmp/p.md"},
        )
        self.assertFalse(result["scheduled"])
        self.assertEqual(result["mechanism"], "report-only")
        self.assertEqual(result["result"]["manual_command"], "execute /tmp/p.md")
        self.assertEqual(result["result"]["resume_at_iso"], "iso-boot")
        self.assertEqual([step["mechanism"] for step in result["trail"]], ["automation", "launchd", "report-only"])
        self.assertIn("launchd-bootstrap-failed", result["trail"][1]["reason"])
        self.assertFalse((job_dir / "ai-playbook.budget-resume.plist").exists())

    def test_default_launchd_paths_are_absolute(self) -> None:
        # r2 F4 follow-up: the tilde defaults expand at import time; a
        # literal "~" in a pathlib default never expands, so a default-path
        # arm wrote the job plist into a "./~" directory under the caller's
        # working directory and bootstrapped launchd with that path.
        self.assertTrue(watcher.DEFAULT_LAUNCHD_JOB_DIR.is_absolute())
        self.assertTrue(watcher.DEFAULT_RESUME_SENTINEL.is_absolute())

    def test_launchd_job_definition_escapes_metacharacters(self) -> None:
        # r1 F14: a plan path with shell metacharacters and XML-hostile
        # characters must reach the fire-time command quoted and survive the
        # plist round trip; the quoted command runs the real path as data.
        hostile = self.tmp / "evil dir;$(touch pwned)`x`&<>.md"
        hostile.write_text("# plan\n", encoding="utf-8")
        scheduler = watcher.LaunchdOneShotScheduler(self.tmp / "job-esc", self.tmp / "sentinel-esc", bootstrap=lambda _job: (True, ""))
        manual = watcher.build_manual_resume_command(str(hostile))
        self.assertIn("'", manual)
        result = scheduler.schedule(
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": manual}
        )
        self.assertTrue(result["scheduled"], result)
        payload = plistlib.loads((self.tmp / "job-esc" / "ai-playbook.budget-resume.plist").read_bytes())
        command = payload["ProgramArguments"][2]
        # The hostile path appears exactly once, as quoted data; nothing
        # executed at arm time.
        self.assertEqual(payload["Label"], "ai-playbook.budget-resume")
        self.assertIn("evil dir", command)
        self.assertFalse((self.tmp / "pwned").exists())
        # Simulate the fire: the command string runs without executing the
        # injected segments and the manual command sees the quoted path.
        fired = command.replace(f"execute {shlex.quote(str(hostile))}", f"touch '{shlex.quote(str(self.tmp / 'resumed-esc'))}'")
        subprocess.run(["/bin/sh", "-c", fired], check=True, capture_output=True)
        self.assertFalse((self.tmp / "pwned").exists())
        self.assertTrue((self.tmp / "resumed-esc").exists())

    def test_launchd_identity_keys_isolate_concurrent_schedules(self):
        # r3 F14: concurrent schedules for different runs must never share
        # one launchd label, job path, or sentinel (run B's plist write
        # clobbers the shared file and its bootout removes run A's loaded
        # job). The identity key digests plan slug and repository root, so
        # only the same run collides; a caller bringing both explicit paths
        # keeps the unkeyed identity for those paths.
        key_a = watcher.launchd_identity_key("plan-a", "/repo/a")
        key_b = watcher.launchd_identity_key("plan-b", "/repo/b")
        self.assertEqual(key_a, watcher.launchd_identity_key("plan-a", "/repo/a"))
        self.assertNotEqual(key_a, key_b)
        identity_a = watcher.default_launchd_identity("plan-a", "/repo/a")
        identity_b = watcher.default_launchd_identity("plan-b", "/repo/b")
        self.assertNotEqual(identity_a["job_dir"], identity_b["job_dir"])
        self.assertNotEqual(identity_a["sentinel_path"], identity_b["sentinel_path"])
        self.assertNotEqual(identity_a["label"], identity_b["label"])
        self.assertTrue(identity_a["label"].startswith("ai-playbook.budget-resume."))
        keyed_chain = watcher.cli_scheduler_chain(plan_slug="plan-a", repo_root="/repo/a")
        launchd = [step for step in keyed_chain if isinstance(step, watcher.LaunchdOneShotScheduler)][0]
        self.assertEqual(launchd._label, identity_a["label"])
        self.assertEqual(str(launchd._sentinel_path), identity_a["sentinel_path"])
        explicit_chain = watcher.cli_scheduler_chain(
            job_dir=self.tmp / "explicit-job",
            sentinel_path=self.tmp / "explicit-sentinel",
            plan_slug="plan-a",
            repo_root="/repo/a",
        )
        explicit = [step for step in explicit_chain if isinstance(step, watcher.LaunchdOneShotScheduler)][0]
        self.assertEqual(explicit._label, "ai-playbook.budget-resume")
        self.assertEqual(explicit._job_dir, self.tmp / "explicit-job")

    def test_half_custom_launchd_payload_stays_keyed(self):
        # r4 F3: the launchd identity is keyed whenever EITHER path is left
        # at its default. A half-custom payload that named exactly one
        # documented key used to take the shared unkeyed identity for BOTH
        # paths, so a second run's arm overwrote the first run's job file
        # and bootout its loaded resume without a label-conflict refusal.
        # Each defaulted path now takes the keyed identity; a payload with
        # both paths explicit keeps the unkeyed identity (control).
        identity = watcher.default_launchd_identity("plan-a", "/repo/a")
        custom_job = watcher.cli_scheduler_chain(job_dir=self.tmp / "half-job", plan_slug="plan-a", repo_root="/repo/a")
        launchd = [step for step in custom_job if isinstance(step, watcher.LaunchdOneShotScheduler)][0]
        self.assertEqual(launchd._label, identity["label"])
        self.assertEqual(str(launchd._sentinel_path), identity["sentinel_path"])
        self.assertEqual(str(launchd._job_dir), str(self.tmp / "half-job"))
        custom_sentinel = watcher.cli_scheduler_chain(sentinel_path=self.tmp / "half-sentinel", plan_slug="plan-a", repo_root="/repo/a")
        launchd = [step for step in custom_sentinel if isinstance(step, watcher.LaunchdOneShotScheduler)][0]
        self.assertEqual(launchd._label, identity["label"])
        self.assertEqual(str(launchd._job_dir), identity["job_dir"])
        self.assertEqual(str(launchd._sentinel_path), str(self.tmp / "half-sentinel"))
        both = watcher.cli_scheduler_chain(
            job_dir=self.tmp / "full-job",
            sentinel_path=self.tmp / "full-sentinel",
            plan_slug="plan-a",
            repo_root="/repo/a",
        )
        launchd = [step for step in both if isinstance(step, watcher.LaunchdOneShotScheduler)][0]
        self.assertEqual(launchd._label, "ai-playbook.budget-resume")
        self.assertEqual(launchd._job_dir, self.tmp / "full-job")
        self.assertEqual(launchd._sentinel_path, self.tmp / "full-sentinel")

    def test_label_conflict_falls_through_chain_to_report_only(self):
        # r4 O20: a label-conflict refusal must fall through the fallback
        # chain to report-only (naming the exact manual command), never end
        # the pause chain with a dead launchd arm that reports scheduled.
        job_dir = self.tmp / "chain-conflict"
        sentinel = self.tmp / "chain-conflict-sentinel"
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "ai-playbook.budget-resume.plist").write_bytes(plistlib.dumps({"Label": "other.run"}))
        result = watcher.schedule_with_fallback(
            watcher.cli_scheduler_chain(job_dir=job_dir, sentinel_path=sentinel),
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertFalse(result["scheduled"])
        self.assertEqual(result["mechanism"], "report-only")
        self.assertIn("label-conflict", result["trail"][0]["reason"])
        self.assertEqual(result["trail"][-1]["mechanism"], "report-only")
        self.assertEqual(result["result"]["manual_command"], "execute /tmp/p.md")

    def test_cli_scheduler_chain_automation_echo_arms_no_launchd(self):
        # r4 O21: an already-successful orchestrator automation create is
        # echoed as the scheduled mechanism, so the chain's launchd fallback
        # is never reached: no plist is written, no job is armed on top of
        # the create, and the trail holds the single echo result.
        job_dir = self.tmp / "echo-job"
        sentinel = self.tmp / "echo-sentinel"
        result = watcher.schedule_with_fallback(
            watcher.cli_scheduler_chain(
                automation_result={"scheduled": True, "id": "auto-1"},
                job_dir=job_dir,
                sentinel_path=sentinel,
                plan_slug="plan-a",
                repo_root="/repo/a",
            ),
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertTrue(result["scheduled"])
        self.assertEqual(result["mechanism"], "automation")
        self.assertEqual(result["result"]["automation"], {"scheduled": True, "id": "auto-1"})
        self.assertEqual(len(result["trail"]), 1)
        self.assertFalse(job_dir.exists(), "the automation echo must arm no launchd job")

    def test_launchd_label_conflict_refuses_foreign_job(self):
        # r3 F14: a foreign job sitting at this watcher's job path is never
        # overwritten and booted out (that would silently destroy another
        # run's armed resume): the arm refuses with label-conflict so the
        # fallback chain proceeds to report-only. The control arm proves a
        # stale own-label job still arms over it.
        job_dir = self.tmp / "job-conflict"
        sentinel = self.tmp / "sentinel-conflict"
        scheduler = watcher.LaunchdOneShotScheduler(job_dir, sentinel, bootstrap=lambda _job: (True, ""))
        job_dir.mkdir(parents=True, exist_ok=True)
        foreign = job_dir / "ai-playbook.budget-resume.plist"
        foreign.write_bytes(plistlib.dumps({"Label": "some.other.run"}))
        result = scheduler.schedule({"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"})
        self.assertFalse(result["scheduled"])
        self.assertIn("label-conflict", result["reason"])
        self.assertEqual(result["conflict_label"], "some.other.run")
        self.assertEqual(plistlib.loads(foreign.read_bytes())["Label"], "some.other.run")
        # A stale job of our own label is a prior window: re-arm over it.
        foreign.write_bytes(plistlib.dumps({"Label": "ai-playbook.budget-resume"}))
        own = scheduler.schedule({"fire_at_epoch": 5_400_000_120, "resume_at_iso": "y", "manual_command": "execute /tmp/p.md"})
        self.assertTrue(own["scheduled"], own)
        self.assertEqual(plistlib.loads(foreign.read_bytes())["Label"], "ai-playbook.budget-resume")

    def test_launchd_one_shot_decision_marker_rearm_and_logs(self):
        # r3 F16: the fired job writes its output to durable log files (a
        # fire that never reaches a resume leaves its decision on disk, not
        # in launchd's void); watcher-fire consumes the sentinel on any
        # terminal decision (marker written, sentinel removed) so the
        # still-loaded daily job stays inert AND the next window's arm
        # re-arms instead of ending report-only forever.
        job_dir = self.tmp / "launchd-logs"
        sentinel = self.tmp / "sentinel-logs"
        chain = [
            watcher.AutomationScheduler(None),
            # The tmp dir is this smoke's sanctioned runtime directory (r5
            # F13): the spent-pair re-arm cleanup may unlink only inside it.
            watcher.LaunchdOneShotScheduler(job_dir, sentinel, bootstrap=lambda _job: (True, ""), cleanup_dir=self.tmp),
            watcher.ReportOnlyScheduler(),
        ]
        first = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertTrue(first["scheduled"])
        payload = plistlib.loads((job_dir / "ai-playbook.budget-resume.plist").read_bytes())
        self.assertIn("StandardOutPath", payload)
        self.assertIn("StandardErrorPath", payload)
        self.assertEqual(payload["StandardOutPath"], str(job_dir / "ai-playbook.budget-resume.out.log"))
        self.assertEqual(payload["StandardErrorPath"], str(job_dir / "ai-playbook.budget-resume.err.log"))
        command = payload["ProgramArguments"][2]
        self.assertIn("test -e", command.split(";")[0])
        marker = self.tmp / "resumed-logs"
        fired_command = command.replace("execute /tmp/p.md", f"touch '{marker}'")
        subprocess.run(["/bin/sh", "-c", fired_command], check=True, capture_output=True)
        self.assertTrue(sentinel.exists())
        self.assertTrue(marker.exists())
        # The fire reached a terminal decision through watcher-fire: the
        # one-shot is consumed (marker written, sentinel removed) and the
        # next daily calendar fire is inert.
        consumed = watcher.consume_resume_sentinel(sentinel)
        self.assertTrue(consumed["consumed"])
        self.assertTrue(sentinel.with_name(sentinel.name + ".fired").exists())
        marker.unlink()
        subprocess.run(["/bin/sh", "-c", fired_command], check=True, capture_output=True)
        self.assertFalse(marker.exists(), "a consumed one-shot must never re-run the resume")
        # The spent pair re-arms the next window instead of self-disabling.
        second = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_180, "resume_at_iso": "y", "manual_command": "execute /tmp/p.md"},
        )
        self.assertTrue(second["scheduled"], second)
        self.assertFalse(sentinel.exists(), "re-arm clears the spent sentinel (r1 F1: the next fire re-creates it)")
        self.assertFalse(sentinel.with_name(sentinel.name + ".fired").exists())

    def test_launchd_spent_pair_outside_sanctioned_dir_refuses_cleanup(self):
        # r5 F13: the spent-pair cleanup unlinks paths, so it may only run
        # inside the sanctioned runtime directory. A payload-named sentinel
        # outside it (with a spent marker or a stale marker alone) refuses
        # the arm with a named reason, deletes nothing, and the chain falls
        # through to report-only.
        outside = self.tmp / "elsewhere" / "user-file"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text("keep me\n", encoding="utf-8")
        marker = outside.with_name(outside.name + ".fired")
        marker.write_text("1700000000\n", encoding="utf-8")
        scheduler = watcher.LaunchdOneShotScheduler(
            self.tmp / "job-esc2", outside, bootstrap=lambda _job: (True, "")
        )
        spent_pair = scheduler.schedule({"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"})
        self.assertFalse(spent_pair["scheduled"])
        self.assertIn("sanctioned runtime directory", spent_pair["reason"])
        self.assertTrue(outside.exists(), "a spent pair outside the sanctioned directory must never be unlinked")
        self.assertTrue(marker.exists())
        # The marker-alone arm refuses the same way.
        outside.unlink()
        stale_marker = scheduler.schedule({"fire_at_epoch": 5_400_000_180, "resume_at_iso": "y", "manual_command": "execute /tmp/p.md"})
        self.assertFalse(stale_marker["scheduled"])
        self.assertIn("sanctioned runtime directory", stale_marker["reason"])
        self.assertTrue(marker.exists())
        # Inside the sanctioned directory the cleanup still runs: the same
        # spent pair at a scoped sentinel re-arms.
        scoped = self.tmp / "scoped.sentinel"
        scoped.write_text("fired\n", encoding="utf-8")
        scoped_marker = scoped.with_name(scoped.name + ".fired")
        scoped_marker.write_text("1700000000\n", encoding="utf-8")
        scoped_scheduler = watcher.LaunchdOneShotScheduler(
            self.tmp / "job-scoped", scoped, bootstrap=lambda _job: (True, ""), cleanup_dir=self.tmp
        )
        rearm = scoped_scheduler.schedule({"fire_at_epoch": 5_400_000_240, "resume_at_iso": "z", "manual_command": "execute /tmp/p.md"})
        self.assertTrue(rearm["scheduled"], rearm)
        self.assertFalse(scoped.exists())
        self.assertFalse(scoped_marker.exists())

    def test_report_only_fallback_names_exact_command_and_time(self) -> None:
        chain = [watcher.ReportOnlyScheduler()]
        result = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "iso-x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertFalse(result["scheduled"])
        self.assertEqual(result["mechanism"], "report-only")
        self.assertEqual(result["result"]["manual_command"], "execute /tmp/p.md")
        self.assertEqual(result["result"]["resume_at_iso"], "iso-x")

    def test_automation_create_refusal_falls_through_to_launchd(self) -> None:
        def refusing(_request: dict) -> dict:
            raise RuntimeError("host refused the automation create")

        sentinel = self.tmp / "sentinel-refusal"
        chain = [
            watcher.AutomationScheduler(refusing),
            watcher.LaunchdOneShotScheduler(self.tmp / "job-refusal", sentinel, bootstrap=lambda _job: (True, "")),
            watcher.ReportOnlyScheduler(),
        ]
        result = watcher.schedule_with_fallback(
            chain,
            {"fire_at_epoch": 5_400_000_120, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"},
        )
        self.assertTrue(result["scheduled"])
        self.assertEqual(result["mechanism"], "launchd")
        self.assertIn("automation-create-refused", result["trail"][0]["reason"])


class PlansAuthoringFixture:
    """Hermetic plans authoring workspace: a canonical plan file plus the
    authoring machine-state JSON home and its Markdown notes projection
    under a temporary ``tmp_dir``."""

    PLAN_TEXT = "# authoring fixture plan\n\n- [ ] task body\n"

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self._tmp = tempfile.TemporaryDirectory()
        # Canonicalize: the repo-root fence compares against the resolved
        # root, and the macOS temp parent is a symlink.
        self.root = Path(self._tmp.name).resolve()
        self.tmp_dir = self.root / "tmp"
        self.tmp_dir.mkdir()
        self.plan_path = self.root / "docs" / "history" / "plans" / "fixture-authoring.md"
        self.plan_path.parent.mkdir(parents=True)
        self.plan_path.write_text(self.PLAN_TEXT, encoding="utf-8")
        self.state_path = self.tmp_dir / "plan-requirements-fixture-authoring.json"
        self.notes_path = self.tmp_dir / "plan-requirements-fixture-authoring.md"
        self.notes_path.write_text("# requirements notes\n\nupdated: nothing yet\n", encoding="utf-8")

    def adapter(self) -> watcher.PlansAuthoringWatcherAdapter:
        return watcher.PlansAuthoringWatcherAdapter(
            self.state_path,
            self.notes_path,
            repo_root=str(self.root),
            clock=self.clock,
        )

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def plan_digest(self) -> str:
        return hashlib.sha256(self.plan_path.read_bytes()).hexdigest()

    def peek_state(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, mutate) -> None:
        """A raw machine-state write under the shared watcher lock (the
        witness path for peer-session writes)."""

        with watcher.authoring_state_lock(self.state_path):
            state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {}
            mutate(state)
            state["updated_at"] = float(self.clock())
            self.state_path.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def note_lines(self) -> list[str]:
        return [line for line in self.notes_path.read_text(encoding="utf-8").splitlines() if line.startswith("pending_resume_watcher:")]


class PlansAuthoringWatcherAdapterTest(unittest.TestCase):
    """Plans authoring mirror over the shared watcher state machine: the
    authoring JSON is authority, the Markdown notes are projection only."""

    def setUp(self) -> None:
        self.clock = FakeClock(7_000_000.0)
        self.fixture = PlansAuthoringFixture(self.clock)
        self.addCleanup(self.fixture.cleanup)
        self.automation_calls: list[dict] = []
        self.chain = [
            watcher.AutomationScheduler(self.automation_result),
            watcher.ReportOnlyScheduler(),
        ]

    def automation_result(self, request: dict) -> dict:
        self.automation_calls.append(request)
        return {"scheduled": True, "id": f"auto-{len(self.automation_calls)}"}

    def boundary(self, report: dict, **kwargs) -> dict:
        return watcher.record_budget_boundary(
            self.fixture.adapter(),
            self.chain,
            probe_report=report,
            plan_slug=kwargs.pop("plan_slug", "fixture-authoring"),
            plan_path=kwargs.pop("plan_path", str(self.fixture.plan_path)),
            plan_digest=kwargs.pop("plan_digest", self.fixture.plan_digest()),
            repo_root=kwargs.pop("repo_root", str(self.fixture.root)),
            watcher_id_factory=kwargs.pop("watcher_id_factory", None),
            clock=kwargs.pop("clock", self.clock),
            **kwargs,
        )

    def test_authoring_known_continue_installs_watcher_and_projects_notes(self) -> None:
        reset = 7_200_000_030
        result = self.boundary(known_continue_report(reset))
        self.assertEqual(result["boundary"], "install")
        receipt = self.fixture.peek_state()["resume_watcher"]
        # The same fenced receipt shape is enforced by the shared state machine.
        self.assertEqual(set(receipt), set(watcher.RESUME_WATCHER_FIELDS))
        self.assertEqual(receipt["status"], "pending")
        self.assertEqual(receipt["reset_at_epoch"], reset)
        self.assertEqual(receipt["plan_path"], str(self.fixture.plan_path))
        # The JSON home is the machine-state authority named by the mirror.
        self.assertEqual(self.fixture.state_path.name, "plan-requirements-fixture-authoring.json")
        # Exactly one automation at reset time plus one minute.
        self.assertEqual(len(self.automation_calls), 1)
        self.assertEqual(self.automation_calls[0]["fire_at_epoch"], watcher.compute_fire_epoch(reset))
        # The notes received exactly one projection line, after the transition.
        lines = self.fixture.note_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(f"pending_resume_watcher: {receipt['watcher_id']} ("))
        self.assertIn("status=pending", lines[0])

    def _installed_receipt(self):
        result = self.boundary(known_continue_report(7_200_000_090))
        self.assertEqual(result["boundary"], "install")
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(receipt["status"], "pending")
        return receipt

    @staticmethod
    def _re_carrier(receipt, *, generation=None, boundary_generation=None, armed_launchd=None):
        return {
            "action": "re-carrier",
            "expected_watcher_id": receipt.get("watcher_id"),
            "expected_generation": receipt.get("expected_generation") if generation is None else generation,
            "expected_boundary_generation": receipt.get("boundary_generation") if boundary_generation is None else boundary_generation,
            "armed_launchd": {"armed": False, "reason": "launchd-arm-outcome-refused"} if armed_launchd is None else armed_launchd,
            "reason": "launchd-arm-outcome",
        }

    def test_authoring_cas_success_records_rectification_and_projects(self) -> None:
        # Mirror of the runtime rectification arm: CAS success on a matching
        # expected generation records the rectification event and projects
        # the authoring notes state, leaving the boundary generation alone.
        receipt = self._installed_receipt()
        notes_before = self.fixture.note_lines()
        result = self.fixture.adapter().compare_and_swap_carrier(self._re_carrier(receipt))
        self.assertEqual(result["status"], "success", result)
        self.assertEqual(result["reason_code"], "resume-watcher-carrier-rectified")
        self.assertTrue(result["cas_applied"])
        patched = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(patched["armed_launchd"], {"armed": False, "reason": "launchd-arm-outcome-refused"})
        self.assertEqual(patched["boundary_generation"], receipt["boundary_generation"])
        self.assertEqual(patched["watcher_id"], receipt["watcher_id"])
        self.assertNotEqual(self.fixture.note_lines(), notes_before)

    def test_authoring_cas_refusal_on_stale_generation_does_not_mutate(self) -> None:
        receipt = self._installed_receipt()
        before = self.fixture.peek_state()
        result = self.fixture.adapter().compare_and_swap_carrier(
            self._re_carrier(receipt, generation=receipt["expected_generation"] + 1)
        )
        self.assertEqual(result["status"], "blocked", result)
        self.assertEqual(result["reason_code"], "stale-attempt")
        self.assertFalse(result["cas_applied"])
        self.assertEqual(self.fixture.peek_state(), before)

    def test_authoring_cas_rejects_invalid_carrier_payload_without_state_change(self) -> None:
        receipt = self._installed_receipt()
        before = self.fixture.peek_state()
        result = self.fixture.adapter().compare_and_swap_carrier(
            self._re_carrier(receipt, armed_launchd={"reason": "no-armed-key"})
        )
        self.assertEqual(result["status"], "blocked", result)
        self.assertEqual(result["reason_code"], "malformed-result")
        self.assertFalse(result["cas_applied"])
        self.assertEqual(self.fixture.peek_state(), before)

    def test_authoring_replacement_is_single_and_projects_each_transition(self) -> None:
        first = self.boundary(known_continue_report(7_200_000_090))
        second = self.boundary(known_continue_report(7_200_000_150))
        self.assertEqual(second["boundary"], "install")
        self.assertEqual(second["replaces"], first["watcher_id"])
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(receipt["watcher_id"], second["watcher_id"])
        self.assertEqual(receipt["replaces"], first["watcher_id"])
        self.assertEqual(receipt["boundary_generation"], 2)
        self.assertEqual(len(self.automation_calls), 2)
        lines = self.fixture.note_lines()
        self.assertEqual(len(lines), 2)
        self.assertIn(second["watcher_id"], lines[1])
        self.assertIn(f"replaces={first['watcher_id']}", lines[1])

    def test_authoring_unknown_report_supersedes_pending_and_schedules_nothing(self) -> None:
        installed = self.boundary(known_continue_report(7_200_000_090))
        calls_after_install = len(self.automation_calls)
        result = self.boundary(probe._unknown_report("fixture", ["stale probe"]))
        # Known-binding-only: the unknown branch supersedes, never schedules.
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["classification"], "unknown")
        self.assertEqual(result["superseded_watcher_id"], installed["watcher_id"])
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(len(self.automation_calls), calls_after_install)
        lines = self.fixture.note_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1], "pending_resume_watcher: none")
        # A late callback from the superseded watcher is fenced by the
        # watcher-id mismatch (r1 F20: self_disarm is subsumed by the
        # evaluate_fire fence) and mutates nothing.
        decision = watcher.evaluate_fire(self.fixture.adapter(), installed["machine"]["resume_watcher"])
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("watcher-id", decision["mismatches"])
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])

    def test_authoring_weekly_secondary_supersedes_pending_without_scheduling(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        result = self.boundary(known_continue_report(8_000_000_000, binding="secondary"))
        self.assertEqual(result["boundary"], "supersede")
        self.assertEqual(result["classification"], "weekly-secondary")
        self.assertIsNone(result["scheduling"])
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])

    def test_authoring_stale_cas_is_blocked_and_projects_nothing(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        before_lines = self.fixture.note_lines()
        snapshot = self.fixture.adapter().read_state()
        stale = self.fixture.adapter().compare_and_swap_schedule(
            watcher.build_schedule_transition(
                {**snapshot, "boundary_generation": 0},
                watcher_id="rw-authoring-stale",
                plan_slug="fixture-authoring",
                repo_root=str(self.fixture.root),
                plan_path=str(self.fixture.plan_path),
                plan_digest=self.fixture.plan_digest(),
                reset_at_epoch=7_200_000_120,
                scheduled_at_epoch=int(self.clock()),
                binding="primary",
            )
        )
        self.assertEqual(stale["status"], "blocked")
        self.assertEqual(stale["reason_code"], "stale-attempt")
        self.assertFalse(stale["cas_applied"])
        # Projection only after a lock-held state transition: a blocked
        # transition appends nothing to the notes.
        self.assertEqual(self.fixture.note_lines(), before_lines)

    def test_authoring_progress_stand_down_and_markdown_is_never_authority(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        adapter = self.fixture.adapter()
        # The authoring loop updates machine state after the review round.
        self.clock.advance(120)
        self.assertEqual(self.fixture.adapter().record_progress(["round 1 folded"])["status"], "success")
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "semantic-progress")
        # Editing the notes' `updated:` text moves no machine state: the
        # watcher never infers authoring progress from Markdown.
        notes = self.fixture.notes_path
        notes.write_text(notes.read_text(encoding="utf-8") + "updated: round 1 folded, digest moved\n", encoding="utf-8")
        self.clock.advance(120)
        # New watcher scheduled now (fresh boundary), then more notes edits.
        result = self.boundary(known_continue_report(7_200_000_150))
        self.assertEqual(result["boundary"], "install")
        firing = self.fixture.adapter()
        notes.write_text(notes.read_text(encoding="utf-8") + "updated: round 2 started\n", encoding="utf-8")
        decision = watcher.evaluate_fire(firing, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "resume")
        self.assertEqual(decision["reason"], "untouched-state")

    def test_authoring_canonical_plan_path_and_digest_fences(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        adapter = self.fixture.adapter()
        receipt = self.fixture.peek_state()["resume_watcher"]
        # Plan bytes changed after scheduling: the live digest fence refuses.
        self.fixture.plan_path.write_text("# authoring fixture plan\n\n- [x] mutated body\n", encoding="utf-8")
        decision = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("plan-digest", decision["mismatches"])
        # A receipt for a different canonical plan path is fenced too.
        self.fixture.plan_path.write_text(self.fixture.PLAN_TEXT, encoding="utf-8")
        moved = dict(receipt)
        moved["plan_path"] = str(self.fixture.root / "docs" / "history" / "plans" / "elsewhere.md")
        decision = watcher.evaluate_fire(adapter, moved)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("plan-path", decision["mismatches"])
        # A receipt whose canonical repository root differs is fenced.
        rooted = dict(receipt)
        rooted["repo_root"] = str(self.fixture.root / "elsewhere")
        decision = watcher.evaluate_fire(adapter, rooted)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("repository-root", decision["mismatches"])

    def test_authoring_interrupt_fence_newer_than_scheduling_and_latched_old(self) -> None:
        # Latched old interrupt: recorded BEFORE the watcher is scheduled,
        # so a later watcher must not trip on it.
        self.clock.advance(10)
        self.assertEqual(self.fixture.adapter().record_interrupt()["status"], "success")
        old_interrupt = self.fixture.peek_state()["user_interrupt"]
        self.boundary(known_continue_report(7_200_000_090))
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "resume")
        self.assertEqual(self.fixture.peek_state()["user_interrupt"], old_interrupt)
        # Interrupted after scheduling: the authoring runtime records an
        # interrupt newer than the scheduling epoch; the watcher stands down
        # and the plain interrupt keeps the run resumable.
        self.clock.advance(300)
        interrupted = self.fixture.adapter().record_interrupt()
        self.assertEqual(interrupted["status"], "success")
        self.assertEqual(self.fixture.peek_state()["workflow_state"], "active")
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "aborted-or-interrupted")

    def test_authoring_archived_and_completed_stand_downs(self) -> None:
        # Archived: plan_status archived, workflow_state still active.
        self.boundary(known_continue_report(7_200_000_090))
        self.assertEqual(self.fixture.adapter().record_terminal("archived")["status"], "success")
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "archived-or-completed")
        # Completed: workflow_state complete (the declared completed-plan
        # stand-down trigger of this mirror).
        self.fixture.write_state(lambda state: state.update({"plan_status": None}))
        self.assertEqual(self.fixture.adapter().record_terminal("complete")["status"], "success")
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "archived-or-completed")

    def test_authoring_aborted_workflow_state_stands_down(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        self.assertEqual(self.fixture.adapter().record_terminal("aborted")["status"], "success")
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "aborted-or-interrupted")

    def test_authoring_peer_session_write_stands_down(self) -> None:
        self.boundary(known_continue_report(7_200_000_090))
        firing = self.fixture.adapter()
        # A peer plans session re-enters authoring through the resume path
        # after the firing adapter's baseline, with no progress recorded:
        # the dedicated peer marker (r1 F11) trips the shared fence, and
        # construction-only writes never do.
        decision = watcher.evaluate_fire(firing, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "resume")
        self.clock.advance(60)
        self.assertEqual(self.fixture.adapter().record_resume(["peer session resumed authoring"])["status"], "success")
        decision = watcher.evaluate_fire(firing, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "peer-resumed")

    def test_authoring_cli_operations_remain_reachable(self) -> None:
        root = self.fixture.root
        state_path = root / "plan-requirements-fixture.json"
        plan_path = root / "authoring-plan.md"
        plan_path.write_text("# fixture plan\n", encoding="utf-8")
        bootstrap_calls: list[str] = []

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        job_dir = root / "launchd"
        sentinel = root / "budget-resume.sentinel"

        def run(operation, payload):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(["--operation", operation, "--input", json.dumps(payload), "--repo-root", str(root)])
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        scheduled = run("plans-watcher-schedule", {
            "state_path": str(state_path), "plan_path": str(plan_path),
            "plan_slug": "fixture", "probe_report": known_continue_report(3_600_000_000),
            "job_dir": str(job_dir), "sentinel_path": str(sentinel),
        })
        self.assertEqual(scheduled["reason_code"], "resume-watcher-scheduled", scheduled)
        self.assertTrue(bootstrap_calls)
        marker = run("plans-resume-marker", {"state_path": str(state_path), "evidence": ["peer re-entry"]})
        self.assertEqual(marker["status"], "success")
        fired = run("plans-watcher-fire", {
            "state_path": str(state_path), "flag_path": str(root / "guard.flag"),
            "sentinel_path": str(sentinel),
        })
        self.assertEqual(fired["decision"], "stand_down", fired)
        self.assertEqual(fired["reason"], "peer-resumed")
        superseded = run("plans-watcher-supersede", {"state_path": str(state_path), "reason": "boundary-decision"})
        self.assertEqual(superseded["status"], "success")
        self.assertIsNone(json.loads(state_path.read_text(encoding="utf-8"))["resume_watcher"])
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = runtime.main(["--operation", "plans-resume-marker", "--input", json.dumps({}), "--repo-root", str(root)])
        self.assertEqual(code, 1)
        self.assertIn("state_path", err.getvalue())

    def test_resume_prompt_remains_fire_aware(self) -> None:
        prompt = watcher.build_resume_prompt({"watcher_id": "rw-x", "plan_path": "/tmp/p.md"})
        self.assertIn("/tmp/p.md", prompt)
        self.assertIn("already cleared", prompt)
        self.assertNotIn("four stand-down checks", prompt)



class ClockedOrderFixture:
    """Hermetic clocked-order workspace (the plan's Task 1 fixture).

    A fixture repository root whose name carries a space (so every quoted
    shell boundary in the fire payload is provably quoted), the real scripts
    directory reachable through a symlink (the fire payload executes the real
    CLI through it), an injected clock, and temp ledger paths; the keyed
    launchd defaults are patched into the fixture root and the launchctl
    bootstrap/bootout seams are faked so arming never touches the host
    launchd domain (the r5 F11 canary discipline).
    """

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "fixture repo"
        self.root.mkdir(parents=True)
        self.state_dir = self.root / ".ai-playbook" / "maintenance"
        self.ledger_path = self.state_dir / "clocked-orders.json"
        self.payload_home = self.state_dir / "clocked-order-payloads"
        (self.root / "scripts").symlink_to(SCRIPTS, target_is_directory=True)

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def ledger(self):
        return watcher.ClockedOrderLedger(
            self.ledger_path,
            self.payload_home,
            repo_root=str(self.root),
            clock=self.clock,
        )

    def requested_iso(self, minutes_ahead: int = 90, seconds: int = 0) -> str:
        moment = datetime.fromtimestamp(self.clock.now).astimezone() + timedelta(minutes=minutes_ahead)
        return moment.replace(second=seconds, microsecond=0).isoformat()

    def schedule_payload(self, **overrides) -> dict:
        payload = {
            "requested_at_iso": self.requested_iso(),
            "payload_text": "# clocked order payload\n\nResume the authoring loop.\n",
            "payload_slug": "fixture-order",
        }
        payload.update(overrides)
        return payload

    def schedule(self, payload=None, clock=None) -> dict:
        return watcher.run_clocked_order_operation(
            "schedule",
            self.schedule_payload() if payload is None else payload,
            repo_root=str(self.root),
            ledger=self.ledger(),
            clock=self.clock if clock is None else clock,
        )

    def discharge(self, order_id: str, **overrides) -> dict:
        payload = {"order_id": order_id, "payload_slug": "fixture-order"}
        payload.update(overrides)
        return watcher.run_clocked_order_operation(
            "discharge-on-fire",
            payload,
            repo_root=str(self.root),
            ledger=self.ledger(),
            clock=self.clock,
        )


class ClockedOrderTest(unittest.TestCase):
    """The clocked-order ledger, its four operations, and the discharge path.

    RED contract (plan 2026-10-05-authoring-clocked-resume-order Task 1): no
    clocked-order operations, ledger, or discharge path exist today (the
    watcher is budget-resume-scoped, and its CLI kinds are registered in
    scripts/execute_plan_runtime.py). Every arm pins one named path: the
    schedule-arm proof, the automation-cap fall-through, the both-refused
    park, the single-consumption discharge, the env-complete executable fire
    payload, the early-fire sentinel consume and re-arm, coexistence with the
    budget-resume watcher, and the stale-target / late-fire / cancellation
    fences.
    """

    def setUp(self) -> None:
        self.clock = FakeClock(1_000_000.0)
        self.fixture = ClockedOrderFixture(self.clock)
        self.addCleanup(self.fixture.cleanup)
        job_dir = self.fixture.root / "launchd"
        sentinel = self.fixture.root / ".ai-playbook" / "runtime" / "clocked-order.sentinel"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        original_job_dir = watcher.DEFAULT_LAUNCHD_JOB_DIR
        original_sentinel = watcher.DEFAULT_RESUME_SENTINEL
        watcher.DEFAULT_LAUNCHD_JOB_DIR = job_dir
        watcher.DEFAULT_RESUME_SENTINEL = sentinel
        self.addCleanup(setattr, watcher, "DEFAULT_LAUNCHD_JOB_DIR", original_job_dir)
        self.addCleanup(setattr, watcher, "DEFAULT_RESUME_SENTINEL", original_sentinel)
        self.bootstrap_calls: list[str] = []
        original_bootstrap = watcher.launchctl_bootstrap

        def fake_bootstrap(job):
            self.bootstrap_calls.append(str(job))
            return True, ""

        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        self.bootout_calls: list[str] = []
        original_bootout = watcher.launchctl_bootout

        def fake_bootout(job):
            self.bootout_calls.append(str(job))
            return {"job": str(job), "exited": 0}

        watcher.launchctl_bootout = fake_bootout
        self.addCleanup(setattr, watcher, "launchctl_bootout", original_bootout)

    @contextlib.contextmanager
    def pinned_timezone(self, zone: str):
        """Ported from the runtime suite: pin the local timezone (POSIX)."""
        if not hasattr(time, "tzset"):
            self.skipTest("time.tzset is absent; timezone pinning is POSIX-only")
        previous = os.environ.get("TZ")
        os.environ["TZ"] = zone
        time.tzset()
        try:
            yield
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def armed_order(self, overrides=None, launchd_canary: bool = True) -> dict:
        payload = self.fixture.schedule_payload(**(overrides or {}))
        result = self.fixture.schedule(payload)
        self.assertEqual(result["status"], "success", result)
        # r5 F11 canary discipline: every launchd-form arm proves it ran the
        # faked bootstrap instead of silently mutating the real gui domain
        # (an automation-echo order arms no launchd and skips the canary).
        if launchd_canary:
            self.assertTrue(self.bootstrap_calls, "launchd bootstrap fake was never invoked; the smoke would be mutating the real gui domain")
        return result

    def test_schedule_arms_at_requested_minute_and_proves(self) -> None:
        requested_epoch = int(datetime.fromisoformat(self.fixture.requested_iso()).timestamp())
        result = self.armed_order()
        self.assertEqual(result["fire_epoch"], requested_epoch)
        self.assertEqual(result["state"], "armed")
        self.assertEqual(result["requested_epoch"], requested_epoch)
        order = self.fixture.ledger().order(result["order_id"])
        self.assertEqual(order["state"], "armed")
        carrier = order["carrier"]
        self.assertTrue(carrier["armed"], carrier)
        # The full carrier record persisted, under the distinct order label.
        self.assertTrue(carrier["label"].startswith("ai-playbook.clocked-order."), carrier)
        for field in ("job_dir", "plist_path", "sentinel_path", "fired_marker_path"):
            self.assertTrue(str(carrier[field]).strip(), carrier)
        # The A3 proof: the armed carrier's recorded fire time equals the
        # requested minute.
        plist = plistlib.loads(Path(carrier["plist_path"]).read_bytes())
        fire_at = datetime.fromtimestamp(requested_epoch).astimezone()
        self.assertEqual(plist["StartCalendarInterval"], {"Minute": fire_at.minute, "Hour": fire_at.hour})
        # The payload copy is retained beside the ledger, digest recorded.
        copy = Path(order["payload_path"])
        self.assertTrue(copy.exists())
        self.assertEqual(order["payload_digest"], hashlib.sha256(copy.read_bytes()).hexdigest())
        self.assertIn("order-armed", [event["event"] for event in order["history"]])

    def test_schedule_refuses_sub_minute_and_iso_epoch_mismatch(self) -> None:
        # Sub-minute precision is refused with a named refusal (the carrier's
        # calendar granularity is minutes); no ledger state is written.
        blocked = self.fixture.schedule(self.fixture.schedule_payload(requested_at_iso=self.fixture.requested_iso(seconds=30)))
        self.assertEqual(blocked["status"], "blocked", blocked)
        self.assertIn("sub-minute", blocked["reason_code"], blocked)
        self.assertFalse(self.fixture.ledger_path.exists(), "a refused schedule must not write ledger state")
        # An ISO whose re-derived epoch disagrees with the recorded wall clock
        # (a nonexistent local time across the spring-forward boundary)
        # refuses with the ledger still untouched.
        with self.pinned_timezone("America/Los_Angeles"):
            mismatch = self.fixture.schedule(self.fixture.schedule_payload(requested_at_iso="2026-03-08T02:30:00"))
        self.assertEqual(mismatch["status"], "blocked", mismatch)
        self.assertIn("iso-epoch", mismatch["reason_code"], mismatch)
        self.assertFalse(self.fixture.ledger_path.exists(), "a refused schedule must not write ledger state")
        # Two pinned zones across a DST boundary: the derived epoch follows
        # the recorded ISO in each zone, so the same wall-clock request
        # records two different epochs 15 hours apart.
        fold_iso = "2026-11-01T01:30:00"
        la_epoch = int(datetime(2026, 11, 1, 1, 30, tzinfo=timezone(timedelta(hours=-7))).timestamp())
        sg_epoch = int(datetime(2026, 11, 1, 1, 30, tzinfo=timezone(timedelta(hours=8))).timestamp())
        self.assertNotEqual(la_epoch, sg_epoch)
        with self.pinned_timezone("America/Los_Angeles"):
            la_result = self.armed_order({"requested_at_iso": fold_iso, "automation": {"scheduled": True, "id": "auto-la"}}, launchd_canary=False)
        with self.pinned_timezone("Asia/Singapore"):
            sg_result = self.armed_order({"requested_at_iso": fold_iso, "automation": {"scheduled": True, "id": "auto-sg"}}, launchd_canary=False)
        ledger = self.fixture.ledger()
        self.assertEqual(int(ledger.order(la_result["order_id"])["requested_epoch"]), la_epoch)
        self.assertEqual(int(ledger.order(sg_result["order_id"])["requested_epoch"]), sg_epoch)

    def test_automation_cap_refusal_falls_through_to_launchd(self) -> None:
        # The witnessed receiving-session shape: the automation link refuses
        # with the capability-unavailable shape and the chain's launchd link
        # arms with the proven fire epoch.
        requested_epoch = int(datetime.fromisoformat(self.fixture.requested_iso()).timestamp())
        result = self.armed_order({"automation": {"scheduled": False, "reason": "automation-capability-unavailable"}})
        self.assertEqual(result["scheduling"]["mechanism"], "launchd", result["scheduling"])
        trail = result["scheduling"]["trail"]
        self.assertEqual(trail[0]["mechanism"], "automation")
        self.assertFalse(trail[0]["scheduled"])
        self.assertEqual(result["fire_epoch"], requested_epoch)
        self.assertEqual(self.fixture.ledger().order(result["order_id"])["state"], "armed")

    def test_both_carriers_refused_parks_with_payload_copy(self) -> None:
        order_id = "co-park-fixture"
        job_dir = self.fixture.root / "park-launchd"
        sentinel = self.fixture.root / ".ai-playbook" / "runtime" / "park.sentinel"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("orphan\n", encoding="utf-8")
        payload = self.fixture.schedule_payload(
            order_id=order_id,
            job_dir=str(job_dir),
            sentinel_path=str(sentinel),
            automation={"scheduled": False, "reason": "refused"},
        )
        result = self.fixture.schedule(payload)
        self.assertEqual(result["status"], "blocked", result)
        self.assertEqual(result["reason_code"], "clocked-order-parked-report-only", result)
        self.assertEqual(result["scheduling"]["mechanism"], "report-only", result["scheduling"])
        order = self.fixture.ledger().order(order_id)
        self.assertEqual(order["state"], "pending", order)
        self.assertFalse(order["carrier"]["armed"], order["carrier"])
        self.assertTrue(order["carrier"].get("reason"), order["carrier"])
        # The payload copy is retained at its ledger path and the report-only
        # result is recorded in the order history.
        self.assertTrue(Path(order["payload_path"]).exists(), "a parked order retains its payload copy")
        self.assertIn("order-parked", [event["event"] for event in order["history"]])

    def test_discharge_exactly_once_on_matching_digest_and_target(self) -> None:
        result = self.armed_order()
        order_id = result["order_id"]
        self.clock.advance(result["fire_epoch"] - self.clock.now)
        first = self.fixture.discharge(order_id)
        self.assertTrue(first["discharged"], first)
        self.assertFalse(first["late"], first)
        self.assertEqual(self.fixture.ledger().order(order_id)["state"], "discharged")
        second = self.fixture.discharge(order_id)
        self.assertEqual(second["status"], "blocked", second)
        self.assertEqual(second["reason_code"], "clocked-order-duplicate-fire", second)
        self.assertEqual(self.fixture.ledger().order(order_id)["state"], "discharged")

    def test_armed_payload_is_executable_env_complete_form(self) -> None:
        config_value = "/fixture/provider-config"
        os.environ["ZCODE_BUILTIN_PROVIDER_CONFIG_FILE"] = config_value
        self.addCleanup(os.environ.pop, "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE", None)
        result = self.armed_order()
        carrier = self.fixture.ledger().order(result["order_id"])["carrier"]
        plist_path = Path(carrier["plist_path"])
        command = plistlib.loads(plist_path.read_bytes())["ProgramArguments"][2]
        # The payload is the env-complete headless invocation of the
        # discharge-on-fire operation (the overlay's Launchd carrier bullet):
        # the provider-config export rides in the payload itself.
        self.assertIn("clocked-order-discharge-on-fire", command)
        self.assertIn(f"export ZCODE_BUILTIN_PROVIDER_CONFIG_FILE={shlex.quote(config_value)}", command)
        # Every shell boundary is a quoted file path: the fixture root name
        # carries a space, so an unquoted insertion would break the command.
        script = self.fixture.root / "scripts" / "execute_plan_runtime.py"
        self.assertIn(shlex.quote(str(script)), command)
        self.assertIn(shlex.quote(str(self.fixture.root)), command)
        # The ledger path reaches the discharge operation inside the quoted
        # --input JSON blob (one quoted shell boundary carrying the recorded
        # order identity).
        self.assertIn(str(self.fixture.ledger_path), command)
        self.assertIn("--input '", command)
        # Executing the payload through the shell reaches the discharge
        # operation: the requested minute is long past in real time (the
        # fixture clock holds 1970), so the payload discharge is a late one,
        # and the physical one-shot is consumed end to end.
        subprocess.run(["/bin/sh", "-c", command], check=True, capture_output=True)
        order = self.fixture.ledger().order(result["order_id"])
        self.assertEqual(order["state"], "discharged")
        self.assertFalse(Path(carrier["sentinel_path"]).exists())
        self.assertTrue(Path(carrier["fired_marker_path"]).exists())

    def test_early_fire_consumes_sentinel_and_re_arms(self) -> None:
        result = self.armed_order()
        order_id = result["order_id"]
        order = self.fixture.ledger().order(order_id)
        carrier = order["carrier"]
        sentinel = Path(carrier["sentinel_path"])
        plist_path = Path(carrier["plist_path"])
        requested_epoch = result["fire_epoch"]
        # The carrier fires early: the job touches its sentinel before the
        # discharge command runs, well before the requested epoch.
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("fired\n", encoding="utf-8")
        bootstrap_calls_before = len(self.bootstrap_calls)
        early = self.fixture.discharge(order_id)
        self.assertTrue(early["early_fire"], early)
        self.assertFalse(early["discharged"], early)
        self.assertTrue(early["sentinel"]["consumed"], early)
        # The check-and-arm-if-none re-arm drove the real launchd shapes (the
        # faked bootstrap is the live seam), not a record-and-return fake:
        # the spent pair is cleared and the armed receipt for the requested
        # minute is rewritten at the recorded plist path.
        self.assertEqual(len(self.bootstrap_calls), bootstrap_calls_before + 1, self.bootstrap_calls)
        self.assertFalse(sentinel.exists())
        self.assertFalse(Path(carrier["fired_marker_path"]).exists(), "the re-arm clears the spent pair")
        rearmed = self.fixture.ledger().order(order_id)
        self.assertEqual(rearmed["state"], "armed")
        self.assertTrue(rearmed["carrier"]["armed"])
        payload = plistlib.loads(plist_path.read_bytes())
        fire_at = datetime.fromtimestamp(requested_epoch).astimezone()
        self.assertEqual(payload["StartCalendarInterval"], {"Minute": fire_at.minute, "Hour": fire_at.hour})
        self.assertIn("early-fire-rearm", [event["event"] for event in rearmed["history"]])

    def test_stale_target_and_late_fire_and_cancellation(self) -> None:
        # Target-identity mismatch: refusal without state change, for both
        # halves of the recorded identity (the payload slug and the canonical
        # repository root).
        result = self.armed_order()
        order_id = result["order_id"]
        stale_slug = self.fixture.discharge(order_id, payload_slug="some-other-payload")
        self.assertEqual(stale_slug["status"], "blocked", stale_slug)
        self.assertEqual(stale_slug["reason_code"], "clocked-order-stale-target", stale_slug)
        self.assertEqual(self.fixture.ledger().order(order_id)["state"], "armed")
        stale_root = watcher.run_clocked_order_operation(
            "discharge-on-fire",
            {"order_id": order_id, "payload_slug": "fixture-order"},
            repo_root=str(self.fixture.root / "elsewhere"),
            ledger=self.fixture.ledger(),
            clock=self.clock,
        )
        self.assertEqual(stale_root["status"], "blocked", stale_root)
        self.assertEqual(stale_root["reason_code"], "clocked-order-stale-target", stale_root)
        self.assertEqual(self.fixture.ledger().order(order_id)["state"], "armed")

        # A fire after the requested minute discharges with the lateness
        # witness recorded in the order history.
        self.clock.advance(result["fire_epoch"] - self.clock.now + 600)
        late = self.fixture.discharge(order_id)
        self.assertTrue(late["discharged"], late)
        self.assertTrue(late["late"], late)
        self.assertGreater(late["late_by_seconds"], 0)
        discharged_order = self.fixture.ledger().order(order_id)
        self.assertEqual(discharged_order["state"], "discharged")
        late_events = [event for event in discharged_order["history"] if event["event"] == "order-discharged"]
        self.assertEqual(len(late_events), 1)
        self.assertEqual(late_events[0]["late_by_seconds"], late["late_by_seconds"])

        # Explicit cancellation: the armed carrier tears down (bootout plus
        # sentinel consume) and the terminal state refuses further fires.
        cancel_seed = self.armed_order()
        cancel_id = cancel_seed["order_id"]
        cancel_order = self.fixture.ledger().order(cancel_id)
        sentinel = Path(cancel_order["carrier"]["sentinel_path"])
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("fired\n", encoding="utf-8")
        plist_path = Path(cancel_order["carrier"]["plist_path"])
        self.assertTrue(plist_path.exists())
        bootout_calls_before = len(self.bootout_calls)
        cancelled = watcher.run_clocked_order_operation(
            "cancel", {"order_id": cancel_id},
            repo_root=str(self.fixture.root), ledger=self.fixture.ledger(), clock=self.clock,
        )
        self.assertEqual(cancelled["status"], "success", cancelled)
        self.assertEqual(cancelled["state"], "cancelled", cancelled)
        self.assertIn(str(plist_path), self.bootout_calls[bootout_calls_before:])
        self.assertFalse(plist_path.exists())
        self.assertFalse(sentinel.exists())
        self.assertTrue(Path(cancel_order["carrier"]["fired_marker_path"]).exists())
        self.assertEqual(self.fixture.ledger().order(cancel_id)["state"], "cancelled")
        refused = self.fixture.discharge(cancel_id)
        self.assertEqual(refused["status"], "blocked", refused)
        self.assertEqual(refused["reason_code"], "clocked-order-terminal-state", refused)
        self.assertIn("cancelled", json.dumps(refused))

        # An automation-form carrier retires through the retirement record.
        auto = self.armed_order({"automation": {"scheduled": True, "id": "auto-retire"}}, launchd_canary=False)
        retired = watcher.run_clocked_order_operation(
            "cancel", {"order_id": auto["order_id"]},
            repo_root=str(self.fixture.root), ledger=self.fixture.ledger(), clock=self.clock,
        )
        self.assertEqual(retired["status"], "success", retired)
        self.assertEqual(retired["carrier_teardown"]["carrier_form"], "automation", retired)
        self.assertEqual(retired["carrier_teardown"]["automation_id"], "auto-retire", retired)
        self.assertEqual(self.fixture.ledger().order(auto["order_id"])["state"], "cancelled")


class ClockedOrderDueReaderTest(unittest.TestCase):
    """The due-time reader's classification (plan Task 2's named arms).

    The plan's RED contract ("no due classification exists today") was authored
    against the pre-Task-1 watcher; Task 1 landed the ``due`` operation
    un-tested by design (its log Deviation 5 defers this class to Task 2), so
    the class witnesses the landed classification's contract instead of a red
    interpreter error: an order whose requested epoch passed undischarged
    classifies ``missed`` exactly once (naming the order id and requested
    time; the terminal state suppresses the second classification), a fired
    marker from the carrier record (a discharge in flight) never classifies,
    discharged and cancelled orders never classify missed, and a still-future
    order is never classified (the A7 pickup boundary, not the reader's).
    """

    def setUp(self) -> None:
        self.clock = FakeClock(2_000_000_000.0)
        self.fixture = ClockedOrderFixture(self.clock)
        self.addCleanup(self.fixture.cleanup)

    def record_order(self, order_id: str, *, requested_epoch: int, carrier: dict | None = None) -> None:
        ledger = self.fixture.ledger()
        ledger.record_order(
            order_id=order_id,
            requested_at_iso="2020-01-01T11:00:00",
            requested_epoch=requested_epoch,
            payload_text="# clocked order payload\n",
            payload_slug="fixture-order",
        )
        if carrier is not None:
            armed = ledger.mutate(
                order_id,
                event="order-armed",
                from_states={"pending"},
                to_state="armed",
                carrier=carrier,
            )
            self.assertEqual(armed["status"], "success", armed)

    def due(self) -> dict:
        return watcher.run_clocked_order_operation(
            "due", {},
            repo_root=str(self.fixture.root),
            ledger=self.fixture.ledger(),
            clock=self.clock,
        )

    def test_overdue_order_classified_missed_once(self) -> None:
        ledger = self.fixture.ledger()
        # Pending and overdue: the due classification is `missed`, naming the
        # order id and its requested time.
        self.record_order("co-due-pending", requested_epoch=1_578_876_400)
        first = self.due()
        self.assertEqual(first["operation"], "clocked-order-due", first)
        self.assertEqual(first["status"], "success", first)
        self.assertEqual(
            first["missed"],
            [{"order_id": "co-due-pending", "requested_at_iso": "2020-01-01T11:00:00", "requested_epoch": 1_578_876_400}],
            first,
        )
        order = ledger.order("co-due-pending")
        self.assertEqual(order["state"], "missed", order)
        missed_events = [event for event in order["history"] if event["event"] == "order-missed"]
        self.assertEqual(len(missed_events), 1, order["history"])
        self.assertEqual(missed_events[0]["requested_at_iso"], "2020-01-01T11:00:00")
        self.assertEqual(missed_events[0]["requested_epoch"], 1_578_876_400)
        # The second classification is suppressed by the terminal state: an
        # empty list, the ledger state unchanged, exactly one missed event.
        second = self.due()
        self.assertEqual(second["missed"], [], second)
        self.assertEqual(ledger.order("co-due-pending")["state"], "missed")
        self.assertEqual(
            len([event for event in ledger.order("co-due-pending")["history"] if event["event"] == "order-missed"]),
            1,
        )

        # Armed and overdue with a fired marker from the carrier record (a
        # discharge in flight): no missed classification, the order stays
        # armed.
        fired_marker = self.fixture.state_dir / "co-due-fired.sentinel.fired"
        fired_marker.parent.mkdir(parents=True, exist_ok=True)
        fired_marker.write_text("fired\n", encoding="utf-8")
        self.record_order(
            "co-due-firing",
            requested_epoch=1_578_876_400,
            carrier={"armed": True, "sentinel_path": str(self.fixture.state_dir / "co-due-fired.sentinel"), "fired_marker_path": str(fired_marker)},
        )
        firing = self.due()
        self.assertEqual(firing["missed"], [], firing)
        self.assertEqual(ledger.order("co-due-firing")["state"], "armed")

        # Armed and overdue with no fired marker: classified missed (the
        # classification admits the armed state, not only pending).
        self.record_order(
            "co-due-armed",
            requested_epoch=1_578_876_400,
            carrier={"armed": True, "sentinel_path": str(self.fixture.state_dir / "co-due-armed.sentinel")},
        )
        armed = self.due()
        self.assertEqual(
            armed["missed"],
            [{"order_id": "co-due-armed", "requested_at_iso": "2020-01-01T11:00:00", "requested_epoch": 1_578_876_400}],
            armed,
        )
        self.assertEqual(ledger.order("co-due-armed")["state"], "missed")

        # A discharged order never classifies missed; the state stays
        # discharged and the missed list stays empty.
        self.record_order("co-due-discharged", requested_epoch=1_578_876_400)
        discharged = ledger.mutate("co-due-discharged", event="order-discharged", from_states={"pending"}, to_state="discharged")
        self.assertEqual(discharged["status"], "success", discharged)
        still_none = self.due()
        self.assertEqual(still_none["missed"], [], still_none)
        self.assertEqual(ledger.order("co-due-discharged")["state"], "discharged")

        # A cancelled order never classifies missed either.
        self.record_order("co-due-cancelled", requested_epoch=1_578_876_400)
        cancelled = ledger.mutate("co-due-cancelled", event="order-cancelled", from_states={"pending"}, to_state="cancelled")
        self.assertEqual(cancelled["status"], "success", cancelled)
        cancelled_due = self.due()
        self.assertEqual(cancelled_due["missed"], [], cancelled_due)
        self.assertEqual(ledger.order("co-due-cancelled")["state"], "cancelled")

        # A still-future order is never classified (the A7 pickup boundary:
        # the reader marks only a passed deadline).
        self.record_order("co-due-future", requested_epoch=2_100_000_000)
        future = self.due()
        self.assertEqual(future["missed"], [], future)
        self.assertEqual(ledger.order("co-due-future")["state"], "pending")


class LaunchdCarrierIdentityStructuralTest(unittest.TestCase):
    """G2 structural invariant: the receipt is the only carrier-identity source.

    The launchd carrier-identity helpers may be called only on the
    arm/schedule path of production modules, so no fire, clean, or consume
    path can ever reconstruct a carrier identity the receipt does not
    record. Test files are excluded: they exercise the helpers directly.
    """

    # r6 F9: the full carrier-identity surface is pinned, not only the
    # label/dir derivation: the record builder (armed_launchd_identity),
    # the plist-path derivation it consumes (launchd_plist_path), and the
    # chain builder that arms the resolved identity (cli_scheduler_chain,
    # r6 F10: its own callers are constrained so a fire-path re-entry
    # through the chain cannot re-enable derivation) all close the
    # allowlist transitively over the call graph. The clocked-order
    # identity family (plan 2026-10-05-authoring-clocked-resume-order) is
    # part of the same closed surface: the per-order key derivation and its
    # resolver beside the plan-keyed ones.
    DERIVATION_SYMBOLS = {
        "default_launchd_identity",
        "resolve_launchd_identity",
        "launchd_identity_key",
        "armed_launchd_identity",
        "launchd_plist_path",
        "cli_scheduler_chain",
        "default_clocked_order_identity",
        "resolve_clocked_order_identity",
    }
    # Which production function may call each derivation helper, and where
    # the arm handlers' schedule branches sit (the budget-resume shared CLI
    # handler and the clocked-order operation handler).
    ARM_HANDLERS = {"run_cli_watcher_operation", "run_clocked_order_operation"}
    CONSUMING_BRANCH_KIND = {"run_cli_watcher_operation": "fire", "run_clocked_order_operation": "discharge-on-fire"}
    ALLOWED_CALLERS = {
        "default_launchd_identity": {"resolve_launchd_identity"},
        "resolve_launchd_identity": {"resolve_launchd_identity", "cli_scheduler_chain", "run_cli_watcher_operation"},
        "launchd_identity_key": {"launchd_identity_key", "default_launchd_identity", "default_clocked_order_identity"},
        "armed_launchd_identity": {"armed_launchd_identity", "run_cli_watcher_operation", "run_clocked_order_operation"},
        "launchd_plist_path": {"launchd_plist_path", "armed_launchd_identity", "schedule"},
        "cli_scheduler_chain": {"cli_scheduler_chain", "run_cli_watcher_operation", "run_clocked_order_operation"},
        "default_clocked_order_identity": {"resolve_clocked_order_identity", "run_clocked_order_operation"},
        "resolve_clocked_order_identity": {"run_clocked_order_operation"},
    }

    @staticmethod
    def _production_sources():
        for path in sorted(SCRIPTS.glob("*.py")):
            if path.name.startswith("test_") or path.name == "__init__.py":
                continue
            yield path

    @staticmethod
    def _parent_map(tree):
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        return parents

    @staticmethod
    def _enclosing_function(node, parents):
        while node is not None:
            node = parents.get(node)
            if isinstance(node, ast.FunctionDef):
                return node
        return None

    @staticmethod
    def _branch_span(function_node, kind_value):
        """The ``(start, end)`` line span of ``if kind == <kind_value>:``."""

        for statement in function_node.body:
            if not isinstance(statement, ast.If):
                continue
            test = statement.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "kind"
                and any(isinstance(op, ast.Eq) for op in test.ops)
                and any(isinstance(c, ast.Constant) and c.value == kind_value for c in test.comparators)
            ):
                return statement.lineno, statement.end_lineno
        return None

    def _derivation_calls(self):
        """All production call sites of the derivation helpers.

        Yields ``(module, symbol, enclosing_function_or_module, node)``.
        """

        for path in self._production_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            parents = self._parent_map(tree)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else None)
                if name not in self.DERIVATION_SYMBOLS:
                    continue
                owner = self._enclosing_function(node, parents)
                yield path.name, name, (owner.name if owner is not None else "<module>"), owner, node

    def test_identity_derivation_has_no_call_sites_outside_the_arm_path(self):
        witnessed = set()
        for module, symbol, owner_name, owner_node, node in self._derivation_calls():
            witnessed.add(module)
            self.assertEqual(
                module,
                "execute_plan_resume_watcher.py",
                f"{symbol} called outside the watcher module in {module}",
            )
            self.assertIn(
                owner_name,
                self.ALLOWED_CALLERS[symbol],
                f"{symbol} called outside the arm path: enclosing production function {owner_name}",
            )
            # A handler call site must sit in the SCHEDULE branch of its arm
            # handler (the budget-resume shared CLI handler and the
            # clocked-order operation handler), never the consuming branch
            # (the fire branch, respectively the discharge-on-fire branch).
            if owner_name in self.ARM_HANDLERS:
                schedule_span = self._branch_span(owner_node, "schedule")
                fire_span = self._branch_span(owner_node, self.CONSUMING_BRANCH_KIND[owner_name])
                self.assertIsNotNone(schedule_span)
                self.assertIsNotNone(fire_span)
                self.assertGreaterEqual(node.lineno, schedule_span[0])
                self.assertLessEqual(node.lineno, schedule_span[1])
                self.assertFalse(
                    fire_span[0] <= node.lineno <= fire_span[1],
                    "carrier-identity derivation inside the consuming branch",
                )
        self.assertEqual(
            witnessed,
            {"execute_plan_resume_watcher.py"},
            "identity-derivation helpers leaked into another production module",
        )

    def test_fire_branch_reads_only_the_receipt_carrier(self):
        # The fire branch's sentinel consumption consults only the payload's
        # explicit path and the receipt's armed_launchd record; grep the
        # branch source for the derivation symbols as a belt over the AST
        # walk above.
        tree = ast.parse((SCRIPTS / "execute_plan_resume_watcher.py").read_text(encoding="utf-8"))
        handler = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "run_cli_watcher_operation"
        )
        fire_span = self._branch_span(handler, "fire")
        self.assertIsNotNone(fire_span)
        branch_source = "\n".join(
            (SCRIPTS / "execute_plan_resume_watcher.py").read_text(encoding="utf-8").splitlines()[fire_span[0] - 1 : fire_span[1]]
        )
        for symbol in self.DERIVATION_SYMBOLS:
            self.assertNotIn(symbol, branch_source, f"{symbol} referenced inside the fire branch")
        # The receipt's carrier record is what the branch consumes.
        self.assertIn("armed_launchd", branch_source)
        self.assertIn("fired_marker_path", branch_source)

    def test_armed_carrier_record_carries_the_full_identity(self):
        # The arm-side record the receipt persists carries every carrier
        # field: label, job dir, plist path, sentinel path, fired marker.
        # Hermetic temp paths: the scheduler smoke must never write into the
        # working directory.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job_dir = root / "job-dir"
            sentinel = root / "sentinel-file"
            record = watcher.armed_launchd_identity(job_dir, sentinel, "the.label")
            self.assertEqual(
                record,
                {
                    "armed": True,
                    "label": "the.label",
                    "job_dir": str(job_dir),
                    "plist_path": str(watcher.launchd_plist_path(job_dir, "the.label")),
                    "sentinel_path": str(sentinel),
                    "fired_marker_path": str(watcher.fired_marker_path(sentinel)),
                },
            )
            # The scheduler writes its job at exactly the recorded plist path.
            scheduler = watcher.LaunchdOneShotScheduler(job_dir, sentinel, label="the.label", bootstrap=lambda _job: (True, ""))
            result = scheduler.schedule({"fire_at_epoch": 1, "resume_at_iso": "x", "manual_command": "execute /tmp/p.md"})
            self.assertTrue(result["scheduled"], result)
            self.assertEqual(result["job"], record["plist_path"])
            self.assertTrue(Path(record["plist_path"]).exists())


class DirectoryPlanPassthroughTest(unittest.TestCase):
    """The schedule arm's plan operand passthrough under the directory plan shape.

    Plan 2026-10-08-plan-directory-shape Task 3. The watcher resolves a
    well-formed plan directory through the shared shape resolver: the
    scheduled receipt carries the manifest digest, and the live digest
    re-derivation over the same directory returns it unchanged; a malformed
    directory refuses through the resolver's named arm instead of the
    legacy unreadable refusal.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _plan_dir(self) -> Path:
        plan_dir = self.root / "2026-10-08-watcher-dir-plan"
        (plan_dir / "tasks").mkdir(parents=True)
        (plan_dir / plan_shape.CHARTER_FILENAME).write_text(
            "# Plan: watcher fixture\n\n## Why\nCharter why line.\n", encoding="utf-8"
        )
        (plan_dir / "tasks" / "01-only.md").write_text(
            "### Task 1: only\n\n- [ ] work item\n", encoding="utf-8"
        )
        return plan_dir

    def _expected_manifest_digest(self, plan_dir: Path) -> str:
        charter = plan_dir / plan_shape.CHARTER_FILENAME
        entries = [
            (plan_shape.CHARTER_FILENAME, charter.read_bytes()),
            (f"{plan_shape.TASKS_DIRNAME}/01-only.md", (plan_dir / "tasks" / "01-only.md").read_bytes()),
        ]
        return hashlib.sha256(plan_shape.manifest_digest_payload(entries)).hexdigest()

    def _schedule(self, plan_path: Path, state_path: Path) -> dict:
        adapter = watcher.PlansAuthoringWatcherAdapter(state_path, repo_root=str(self.root))
        return watcher.run_cli_watcher_operation(
            "schedule",
            {
                "state_path": str(state_path),
                "plan_path": str(plan_path),
                "probe_report": known_continue_report(3_600_000_000),
                "plan_slug": "2026-10-08-watcher-dir-plan",
                # An automation echo keeps the chain off the launchd link.
                "automation": {"scheduled": True, "id": "auto-fixture"},
            },
            adapter=adapter,
            supersede=adapter.compare_and_swap_supersede,
            outcome_factory=runtime._outcome,
            identity_prefix="plans-watcher",
            plan_slug="2026-10-08-watcher-dir-plan",
            repo_root=str(self.root),
        )

    def test_resume_watcher_directory_passthrough(self) -> None:
        plan_dir = self._plan_dir()
        state_path = self.root / "plan-requirements-watcher-dir.json"
        outcome = self._schedule(plan_dir, state_path)
        self.assertEqual(outcome["status"], "success", outcome)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        receipt = state["resume_watcher"]
        self.assertEqual(receipt["plan_path"], str(plan_dir.resolve()))
        self.assertEqual(receipt["plan_digest"], self._expected_manifest_digest(plan_dir))
        # The live fire fence re-derives the same manifest digest over the
        # directory operand, so the receipt-versus-live digest fence holds.
        self.assertEqual(watcher.file_digest(plan_dir), self._expected_manifest_digest(plan_dir))
        # A malformed directory refuses through the resolver's named arm,
        # naming the defect and the operand path.
        charterless = self.root / "2026-10-08-charterless"
        charterless.mkdir()
        with self.assertRaisesRegex(ValueError, "plan operand refused.*not a file"):
            self._schedule(charterless, self.root / "plan-requirements-charterless.json")
        # A FILE operand the resolver refuses (non-UTF-8 bytes) falls back
        # to the raw-bytes sha256 digest, the pre-Task-3 behavior: the
        # schedule succeeds and the receipt binds the file's byte digest.
        raw_file = self.root / "2026-10-08-latin1-plan.md"
        raw_bytes = b"# plan\n\nalpha \x97 bravo.\n"
        raw_file.write_bytes(raw_bytes)
        raw_state = self.root / "plan-requirements-latin1.json"
        raw_outcome = self._schedule(raw_file, raw_state)
        self.assertEqual(raw_outcome["status"], "success", raw_outcome)
        raw_receipt = json.loads(raw_state.read_text(encoding="utf-8"))["resume_watcher"]
        self.assertEqual(raw_receipt["plan_digest"], hashlib.sha256(raw_bytes).hexdigest())


if __name__ == "__main__":
    unittest.main()
