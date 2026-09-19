#!/usr/bin/env python3
"""Hermetic tests for the standing resume watcher state machine.

Fake clock, fake automation, fake launchd, temporary machine state, plus a
real ``RuntimeDriver`` file-backed integration fixture: the integration cases
exercise the real ``runtime_state.json``, the real ``_manifest_lock``, an
injected clock, and the schedule / replace / progress / cancellation /
reload / callback paths. No live ``docs/tmp/`` fixtures; the guard-flag
interleavings run against real temporary files with the real probe writer
and the real budget-guard hook core.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
HOOK_DIR = SCRIPTS.parent / "agents/hooks/budget-guard"
sys.path.insert(0, str(HOOK_DIR))

import budget_guard_core  # noqa: E402
import execute_plan_resume_watcher as watcher  # noqa: E402
import execute_plan_runtime as runtime  # noqa: E402
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


class RuntimeFixture:
    """Real RuntimeDriver over a real runtime_state.json in a temp directory."""

    PLAN_TEXT = "# fixture plan\n\n- [ ] task body\n"

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self._tmp = tempfile.TemporaryDirectory()
        # Canonicalize: the driver's repo-root fence compares against the
        # resolved root, and the macOS temp parent is a symlink.
        self.root = Path(self._tmp.name).resolve()
        self.state_path = self.root / "runtime_state.json"
        self.plan_path = self.root / "fixture-plan.md"
        self.plan_path.write_text(self.PLAN_TEXT, encoding="utf-8")
        runtime.create_manifest(
            self.state_path,
            "fixture",
            [{"id": "task-1", "number": 1, "status": "complete", "checkbox": True}],
        )
        self.driver = runtime.RuntimeDriver(
            self.state_path,
            plan_slug="fixture",
            repo_root=self.root,
            commit_lookup=lambda _commit: True,
            clock=clock,
        )

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def adapter(self) -> watcher.RuntimeResumeWatcherAdapter:
        return watcher.RuntimeResumeWatcherAdapter(self.driver)

    def plan_digest(self) -> str:
        return hashlib.sha256(self.plan_path.read_bytes()).hexdigest()

    def peek_state(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, mutate) -> None:
        state = self.peek_state()
        mutate(state)
        runtime._safe_write_json(self.state_path, state)


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


class RuntimeWatcherIntegrationTest(unittest.TestCase):
    """Real RuntimeDriver file-backed cases: runtime_state.json, _manifest_lock,
    injected clock, schedule / replace / progress / cancellation / reload /
    callback paths."""

    def setUp(self) -> None:
        self.clock = FakeClock(3_000_000.0)
        self.fixture = RuntimeFixture(self.clock)
        self.addCleanup(self.fixture.cleanup)

    def install_watcher(self, adapter, reset_at_epoch: int, watcher_id: str, **overrides) -> dict:
        snapshot = adapter.read_state()
        transition = watcher.build_schedule_transition(
            snapshot,
            watcher_id=watcher_id,
            plan_slug="fixture",
            repo_root=str(self.fixture.root),
            plan_path=str(self.fixture.plan_path),
            plan_digest=self.fixture.plan_digest(),
            reset_at_epoch=reset_at_epoch,
            scheduled_at_epoch=int(self.clock()),
            binding="primary",
        )
        transition["receipt"].update(overrides)
        outcome = adapter.compare_and_swap_schedule(transition)
        self.assertEqual(outcome["status"], "success", outcome)
        return outcome

    def test_watcher_stands_down_on_semantic_progress(self) -> None:
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-progress")
        flag = self.fixture.root / "budget-guard.flag"
        write_guard_flag(flag, 3_600_000_000)
        adapter = self.fixture.adapter()
        # The orchestrator records semantic progress after the boundary.
        self.clock.advance(60)
        self.assertEqual(self.fixture.driver.record_progress(["task-1:done"])["status"], "success")
        receipt = self.fixture.peek_state()["resume_watcher"]
        decision = watcher.fire_watcher(adapter, receipt, flag_path=flag)
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "semantic-progress")
        self.assertFalse(decision["guards_cleared"])
        # The guard flag is untouched by a stand-down.
        self.assertTrue(flag.exists())
        self.assertEqual(flag_epoch(flag), 3_600_000_000)

    def test_peer_resume_stands_down(self) -> None:
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-peer")
        adapter = self.fixture.adapter()
        # A peer session constructs its own driver: construction alone moves
        # no peer-resume marker, so the watcher still resumes.
        self.clock.advance(120)
        peer = runtime.RuntimeDriver(
            self.fixture.state_path,
            plan_slug="fixture",
            repo_root=self.fixture.root,
            commit_lookup=lambda _commit: True,
            clock=self.clock,
        )
        self.assertEqual(peer.resume_watcher_snapshot()["progress_revision"], 0)
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(watcher.evaluate_fire(adapter, receipt)["decision"], "resume")
        # The peer re-enters through the resume path: the dedicated
        # peer-resume marker is written after the scheduling epoch (the
        # marker write happens at operation entry, whatever the resume
        # selection returns), and the watcher stands down (r1 F11). The
        # fire-session adapter is constructed AFTER the peer write, so the
        # pre-construction peer window stays visible too.
        peer.resume()
        firing = self.fixture.adapter()
        decision = watcher.evaluate_fire(firing, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "stand_down")
        self.assertEqual(decision["reason"], "peer-resumed")
        # The watcher's own construction and bookkeeping writes never
        # false-trip the fence: a fresh marker-free install still resumes.
        self.fixture.write_state(lambda state: state.update({"resume_watcher": None, "peer_resumed_at_epoch": 0.0}))
        self.install_watcher(self.fixture.adapter(), 3_600_000_120, "rw-peer-2")
        decision = watcher.evaluate_fire(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "resume")

    def test_archived_completed_abort_and_interrupt_stand_downs(self) -> None:
        # Archived / completed: workflow_state complete in machine state.
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-archived")
        self.clock.advance(30)
        archived = self.fixture.root / "docs/plans/completed/fixture.md"
        archived.parent.mkdir(parents=True, exist_ok=True)
        archived.write_text("# fixture\n\n- [x] checklist item\n")
        # Staged terminal: the final stage requires a conforming pre-archive
        # gate receipt, so the fixture seeds one with the same shape as the
        # runtime suite's seed_archive_gate helper (declared destination
        # equal to the archived path, digest over the archived bytes, source
        # at the absent active path).
        self.fixture.write_state(lambda state: state.update({"archive_gate": {
            "plan_path": "docs/plans/fixture.md",
            "declared_destination": "docs/plans/completed/fixture.md",
            "plan_digest": hashlib.sha256(archived.read_bytes()).hexdigest(),
            "last_commit_sha": "abcdef1",
            "phase5_checklist": ["checklist item"],
            "recorded_at": 1234.0,
        }}))
        terminal = self.fixture.driver.mark_terminal("docs/plans/completed/fixture.md", "abcdef1", ["checklist item"])
        self.assertEqual(terminal["status"], "success", terminal)
        adapter = self.fixture.adapter()
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["reason"], "archived-or-completed")
        self.assertEqual(decision["decision"], "stand_down")

        # Aborted workflow state.
        self.fixture.write_state(lambda state: state.update({"workflow_state": "active", "resume_watcher": None}))
        self.install_watcher(self.fixture.adapter(), 3_600_000_060, "rw-aborted")
        self.fixture.write_state(lambda state: state.update({"workflow_state": "aborted"}))
        adapter = self.fixture.adapter()
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["reason"], "aborted-or-interrupted")

        # Interrupted after scheduling: user_interrupt newer than the
        # scheduling epoch.
        self.fixture.write_state(lambda state: state.update({"workflow_state": "active", "resume_watcher": None}))
        self.install_watcher(self.fixture.adapter(), 3_600_000_120, "rw-interrupted")
        self.clock.advance(300)
        interrupted = self.fixture.driver.record_interrupt()
        self.assertEqual(interrupted["status"], "success")
        self.assertEqual(self.fixture.peek_state()["workflow_state"], "active")
        adapter = self.fixture.adapter()
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["reason"], "aborted-or-interrupted")
        # A plain interrupt kept the run resumable (workflow_state unchanged).
        self.assertEqual(self.fixture.peek_state()["workflow_state"], "active")

    def test_latched_old_interrupt_does_not_trip_later_watcher(self) -> None:
        # The interrupt is recorded BEFORE the watcher is scheduled.
        self.clock.advance(10)
        self.assertEqual(self.fixture.driver.record_interrupt()["status"], "success")
        old_interrupt = self.fixture.peek_state()["user_interrupt"]
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-latched")
        adapter = self.fixture.adapter()
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "resume")
        self.assertEqual(self.fixture.peek_state()["user_interrupt"], old_interrupt)

    def test_untouched_state_resumes_with_exact_plan_path_prompt(self) -> None:
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-untouched")
        adapter = self.fixture.adapter()
        receipt = self.fixture.peek_state()["resume_watcher"]
        decision = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(decision["decision"], "resume")
        self.assertEqual(decision["reason"], "untouched-state")
        # The prompt re-enters execute-plan on the exact canonical plan path.
        self.assertIn(str(self.fixture.plan_path), decision["prompt"])
        self.assertIn("Step 0.5", decision["prompt"])

    def test_deleted_plan_digest_fails_closed(self) -> None:
        # r2 F6: a receipt naming a plan digest must see the same digest
        # live. A deleted (or unreadable) plan digests to None at fire time;
        # the old None-skip cleared the fence for exactly the deletion or
        # archive window the digest fence exists for.
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-deleted")
        adapter = self.fixture.adapter()
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.fixture.plan_path.unlink()
        decision = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(decision["decision"], "refuse")
        self.assertEqual(decision["reason"], "fence-mismatch")
        self.assertIn("plan-digest", decision["mismatches"])
        self.assertFalse(decision["relaunch"])

    def test_receipt_without_digest_facing_live_digest_refuses(self) -> None:
        # r3 F21: the receipt-without-digest arm of the plan-digest fence.
        # A receipt carrying no plan digest that faces a live digest is a
        # mismatch, so a mutant deleting the elif arm fails here; the
        # symmetric shape (no digest on either side) still passes.
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-no-digest")
        adapter = self.fixture.adapter()
        receipt = dict(self.fixture.peek_state()["resume_watcher"])
        receipt["plan_digest"] = None
        decision = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(decision["decision"], "refuse")
        self.assertEqual(decision["reason"], "fence-mismatch")
        self.assertIn("plan-digest", decision["mismatches"])
        self.assertFalse(decision["relaunch"])

    def test_watcher_fire_default_flag_path_and_guards_cleared_field(self) -> None:
        # r3 F4: a CLI fire without a payload flag_path defaults to the
        # canonical guard path on BOTH boundaries (the plans boundary used
        # to skip the cleanup silently), and guards_cleared is emitted on
        # every decision: True through the default-path cleanup here, and
        # False with a guard sentence that claims no clearing when no
        # cleanup is configured.
        def fake_bootstrap(_job):
            return True, ""

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        flag = self.fixture.root / "default-arm-budget-guard.flag"
        fired = self.fixture.root / "default-arm-budget-guard.fired"
        original_default = watcher.DEFAULT_FLAG_PATH
        watcher.DEFAULT_FLAG_PATH = flag
        self.addCleanup(setattr, watcher, "DEFAULT_FLAG_PATH", original_default)
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-default-flag")
        write_guard_flag(flag, 3_600_000_000)
        fire_out = io.StringIO()
        with contextlib.redirect_stdout(fire_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-fire",
                    "--input", json.dumps({"fired_path": str(fired), "sentinel_path": str(self.fixture.root / "default-arm.sentinel")}),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        decision = json.loads(fire_out.getvalue())
        self.assertEqual(decision["decision"], "resume", decision)
        self.assertTrue(decision["guards_cleared"])
        self.assertFalse(flag.exists(), "the default-path arm must clear the canonical guard path")
        self.assertIn("already cleared", decision["prompt"])
        # r4 F4: the resume decision consumed the receipt inside the fire
        # operation, so this arm installs a fresh watcher before re-firing.
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])
        self.assertGreater(int(self.fixture.peek_state()["boundary_generation"]), 0)
        self.assertGreater(float(self.fixture.peek_state()["peer_resumed_at_epoch"]), 0.0)
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-default-flag-2")
        # No configured cleanup: guards_cleared is still emitted, False, and
        # the prompt must not claim a clearing that never happened.
        stand_out = io.StringIO()
        with contextlib.redirect_stdout(stand_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-fire",
                    "--input", json.dumps({"flag_path": None, "sentinel_path": str(self.fixture.root / "default-arm.sentinel")}),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        no_cleanup = json.loads(stand_out.getvalue())
        self.assertIn(no_cleanup["decision"], {"resume", "stand_down", "refuse"})
        self.assertFalse(no_cleanup["guards_cleared"])
        if no_cleanup["decision"] == "resume":
            self.assertNotIn("the guards were already cleared", no_cleanup["prompt"])
            self.assertIn("no guard cleanup is configured", no_cleanup["prompt"])

    def test_watcher_fire_consumes_receipt_two_fires(self) -> None:
        # r4 F4: a resume decision consumes the receipt inside the fire
        # operation. Two consecutive fires with NO intervening driver call
        # must not both resume: the first fire records the peer-resume mark
        # and supersedes the receipt (compare-and-swap bumping the boundary
        # generation), so the second fire is refused on machine state - the
        # pending receipt is gone (stale-attempt) and a fire that somehow
        # re-evaluated the consumed receipt still refuses on the
        # boundary-generation fence, never on the peer timestamp.
        reset = 3_600_000_000
        self.install_watcher(self.fixture.adapter(), reset, "rw-fire-once")
        flag = self.fixture.root / "fire-once-budget-guard.flag"
        write_guard_flag(flag, reset)
        receipt = dict(self.fixture.peek_state()["resume_watcher"])

        def fire(payload):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-fire",
                        "--input", json.dumps(payload),
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        first = fire({"flag_path": str(flag), "sentinel_path": str(self.fixture.root / "fire-once.sentinel")})
        self.assertEqual(first["decision"], "resume", first)
        self.assertEqual(first["receipt_superseded"]["status"], "success", first)
        state = self.fixture.peek_state()
        self.assertIsNone(state["resume_watcher"])
        # The receipt's own boundary generation was bumped past: machine
        # state, not the peer timestamp, fences the consumed receipt.
        self.assertGreater(int(state["boundary_generation"]), int(receipt["boundary_generation"]))
        self.assertGreater(float(state["peer_resumed_at_epoch"]), 0.0)
        # The duplicate fire: refused before any evaluation on machine
        # state (nothing pending), never a second resume prompt.
        second = fire({"flag_path": str(flag), "sentinel_path": str(self.fixture.root / "fire-once.sentinel")})
        self.assertEqual(second["reason_code"], "stale-attempt", second)
        self.assertNotIn("prompt", second)
        # Even a fire that somehow re-evaluated the consumed receipt is
        # refused deterministically on the boundary-generation fence.
        stale_decision = watcher.evaluate_fire(self.fixture.adapter(), receipt)
        self.assertEqual(stale_decision["decision"], "refuse")
        self.assertIn("boundary-generation", stale_decision["mismatches"])

    def test_watcher_fire_consumes_armed_receipt_sentinel(self):
        # r4 F3: the schedule arm persists the launchd identity it armed
        # into the watcher receipt, and fire consumes exactly that armed
        # sentinel. A custom-sentinel arm used to be consumed as
        # sentinel-absent by the fire's default derivation while the real
        # sentinel survived, permanently degrading later pauses to
        # report-only.
        bootstrap_calls: list[str] = []

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        job_dir = self.fixture.root / "armed-launchd"
        sentinel = self.fixture.root / "armed-custom.sentinel"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-schedule",
                    "--input", json.dumps({
                        "probe_report": known_continue_report(3_600_000_000),
                        "plan_path": str(self.fixture.plan_path),
                        "job_dir": str(job_dir),
                        "sentinel_path": str(sentinel),
                    }),
                    "--plan-slug", "fixture",
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        # r5 F11 bootstrap canary: the fake proves the smoke armed launchd
        # hermetically instead of silently mutating the real gui domain.
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the CLI smoke would be mutating the real gui domain")
        self.assertEqual(json.loads(out.getvalue())["status"], "success")
        receipt = self.fixture.peek_state()["resume_watcher"]
        # G2: the arm persists the FULL carrier identity (label, job dir,
        # plist path, sentinel path, fired marker path), and fire consumes
        # exactly that armed carrier. A custom-sentinel arm used to be
        # consumed as sentinel-absent by the fire's default derivation while
        # the real sentinel survived, permanently degrading later pauses to
        # report-only.
        self.assertEqual(receipt["armed_launchd"], {
            "armed": True,
            "label": "ai-playbook.budget-resume",
            "job_dir": str(job_dir),
            "plist_path": str(job_dir / "ai-playbook.budget-resume.plist"),
            "sentinel_path": str(sentinel),
            "fired_marker_path": str(sentinel) + ".fired",
        })
        # The launchd job fired (sentinel present). A fire whose payload
        # names no sentinel must consume the ARMED one, not the derived
        # default.
        sentinel.write_text("fired\n", encoding="utf-8")
        fire_out = io.StringIO()
        with contextlib.redirect_stdout(fire_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-fire",
                    "--input", json.dumps({"flag_path": str(self.fixture.root / "armed-guard.flag")}),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        decision = json.loads(fire_out.getvalue())
        self.assertEqual(decision["decision"], "resume", decision)
        self.assertTrue(decision["sentinel"]["consumed"])
        self.assertEqual(decision["sentinel"]["sentinel"], str(sentinel))
        self.assertFalse(sentinel.exists())
        # The consumed fired marker is the receipt's own carrier field.
        self.assertEqual(decision["sentinel"]["fired"], str(sentinel) + ".fired")
        self.assertTrue(Path(decision["sentinel"]["fired"]).exists())

    def test_schedule_stamps_armed_launchd_only_when_launchd_reachable(self):
        # r5 F4: the receipt records the launchd identity only when the
        # chain's launchd link is reachable. An automation echo carrying a
        # successful create arms no launchd job, so stamping its paths would
        # record an armed identity that was never armed; a failed echo keeps
        # the launchd fallback reachable and the stamp stands. r6 F5: the
        # launchd arm is faked hermetically (the r5 F11 canary seam) because
        # the receipt now records the arm's ACTUAL outcome - a real
        # bootstrap failure would rectify the record to armed false.
        bootstrap_calls: list[str] = []

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)

        def schedule_with(automation):
            payload = {
                "probe_report": known_continue_report(3_600_000_000),
                "plan_path": str(self.fixture.plan_path),
                "job_dir": str(self.fixture.root / "reach-launchd"),
                "sentinel_path": str(self.fixture.root / "reach.sentinel"),
            }
            if automation is not None:
                payload["automation"] = automation
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-schedule",
                        "--input", json.dumps(payload),
                        "--plan-slug", "fixture",
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue()), self.fixture.peek_state()["resume_watcher"]

        # A successful automation echo: scheduled through automation, and
        # the receipt records that no launchd carrier was armed, explicitly
        # (G2) instead of omitting the field or stamping an identity that
        # was never armed.
        outcome, receipt = schedule_with({"scheduled": True, "id": "auto-1"})
        self.assertEqual(outcome["status"], "success", outcome)
        self.assertEqual(outcome["scheduling"]["mechanism"], "automation")
        self.assertEqual(receipt["armed_launchd"], {"armed": False, "reason": "automation-echo-scheduled"})
        # A refused automation echo: the launchd link arms, and the receipt
        # records exactly the FULL carrier identity the chain was built to
        # arm (G2). The r6 F5 canary: the fake bootstrap ran, so the armed
        # record states an arm that actually happened.
        outcome, receipt = schedule_with({"scheduled": False, "reason": "refused"})
        self.assertEqual(outcome["status"], "success", outcome)
        self.assertEqual(outcome["scheduling"]["mechanism"], "launchd")
        self.assertIsNone(outcome["carrier_rectified"])
        self.assertEqual(
            receipt["armed_launchd"],
            {
                "armed": True,
                "label": "ai-playbook.budget-resume",
                "job_dir": str(self.fixture.root / "reach-launchd"),
                "plist_path": str(self.fixture.root / "reach-launchd" / "ai-playbook.budget-resume.plist"),
                "sentinel_path": str(self.fixture.root / "reach.sentinel"),
                "fired_marker_path": str(self.fixture.root / "reach.sentinel.fired"),
            },
        )
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the smoke would be mutating the real gui domain")

    def test_schedule_receipt_rectifies_the_launchd_refusal_outcomes(self):
        # r6 F5: the carrier record is stamped from the arm's actual launchd
        # outcome. Pre-fix, the CAS-stamped record claimed armed true before
        # the chain ran, so the four launchd-failure paths ended report-only
        # while the receipt claimed an armed carrier - machine-readable
        # authority describing a carrier that was never armed. The arm now
        # rectifies the persisted receipt to an explicit armed:false record
        # naming the launchd refusal, before the schedule result returns.
        def schedule_receipt(payload):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-schedule",
                        "--input", json.dumps(payload),
                        "--plan-slug", "fixture",
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            outcome = json.loads(out.getvalue())
            return outcome, self.fixture.peek_state()["resume_watcher"]

        def base_payload(job_dir, sentinel):
            return {
                "probe_report": known_continue_report(3_600_000_000),
                "plan_path": str(self.fixture.plan_path),
                "job_dir": str(job_dir),
                "sentinel_path": str(sentinel),
            }

        # Arm 1: sentinel self-disable - the sentinel is present without a
        # fired marker, so the launchd link refuses before any side effect.
        sentinel = self.fixture.root / "rectify.sentinel"
        job_dir = self.fixture.root / "rectify-launchd"
        sentinel.write_text("orphan\n", encoding="utf-8")
        outcome, receipt = schedule_receipt(base_payload(job_dir, sentinel))
        self.assertEqual(outcome["scheduling"]["mechanism"], "report-only", outcome["scheduling"])
        expected = {"armed": False, "reason": "sentinel self-disable file present"}
        self.assertEqual(outcome["carrier_rectified"], expected, outcome["carrier_rectified"])
        self.assertEqual(receipt["armed_launchd"], expected)
        sentinel.unlink()

        # Arm 2: label conflict - the job path holds another watcher's job
        # definition, so the arm refuses instead of destroying it.
        job_dir.mkdir(parents=True, exist_ok=True)
        job = job_dir / "ai-playbook.budget-resume.plist"
        import plistlib
        job.write_bytes(plistlib.dumps({"Label": "somebody.else.job"}))
        outcome, receipt = schedule_receipt(base_payload(job_dir, sentinel))
        self.assertEqual(outcome["scheduling"]["mechanism"], "report-only", outcome["scheduling"])
        expected = {"armed": False, "reason": "label-conflict: job path holds another watcher's job definition"}
        self.assertEqual(outcome["carrier_rectified"], expected, outcome["carrier_rectified"])
        self.assertEqual(receipt["armed_launchd"], expected)
        self.assertEqual(receipt["armed_launchd"], outcome["carrier_rectified"])
        # The foreign job definition is untouched by the refused arm.
        self.assertEqual(plistlib.loads(job.read_bytes())["Label"], "somebody.else.job")
        job.unlink()  # clear the foreign job so the next arm reaches launchd

        # Arm 3: bootstrap failure - launchd refuses the just-written job;
        # the fake is the hermetic seam (r5 F11) and the honest outcome is
        # not-scheduled with the bootstrap detail.
        bootstrap_calls: list[str] = []

        def failing_bootstrap(job):
            bootstrap_calls.append(str(job))
            return False, "boom: refused"

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = failing_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        outcome, receipt = schedule_receipt(base_payload(job_dir, sentinel))
        self.assertEqual(outcome["scheduling"]["mechanism"], "report-only", outcome["scheduling"])
        expected = {"armed": False, "reason": "launchd-bootstrap-failed: boom: refused"}
        self.assertEqual(outcome["carrier_rectified"], expected, outcome["carrier_rectified"])
        self.assertEqual(receipt["armed_launchd"], expected)
        self.assertTrue(bootstrap_calls, "bootstrap fake was never invoked; the smoke would be mutating the real gui domain")
        watcher.launchctl_bootstrap = original_bootstrap

        # Arm 4: plist write failure - the job dir path is a file, so the
        # write fails closed and the reason names it.
        file_job_dir = self.fixture.root / "rectify-file-job"
        file_job_dir.write_text("not a directory\n", encoding="utf-8")
        outcome, receipt = schedule_receipt(base_payload(file_job_dir, sentinel))
        self.assertEqual(outcome["scheduling"]["mechanism"], "report-only", outcome["scheduling"])
        self.assertEqual(outcome["carrier_rectified"]["armed"], False)
        self.assertTrue(outcome["carrier_rectified"]["reason"].startswith("launchd-arm-failed: "), outcome["carrier_rectified"])
        self.assertEqual(receipt["armed_launchd"], outcome["carrier_rectified"])

    def test_watcher_fire_sentinel_override_is_scoped(self):
        # r6 F6: the fire payload's explicit sentinel_path is the operator's
        # manual-recovery override, documented and precedence-ordered over
        # the receipt's carrier record - and scoped like the scheduler's
        # spent-pair cleanup (r5 F13): a path outside the sanctioned runtime
        # directory is refused with nothing consumed and no marker written,
        # so a wrong explicit path can never consume or mark the wrong pair.
        reset = 3_600_000_000
        self.install_watcher(self.fixture.adapter(), reset, "rw-scoped-override")
        outside = self.fixture.root / "outside-runtime" / "stray.sentinel"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text("stray\n", encoding="utf-8")

        def fire(sentinel):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-fire",
                        "--input", json.dumps({"flag_path": str(self.fixture.root / "scoped-guard.flag"), "sentinel_path": str(sentinel)}),
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        refused = fire(outside)
        self.assertEqual(refused["decision"], "resume", refused)
        self.assertFalse(refused["sentinel"]["consumed"])
        self.assertEqual(refused["sentinel"]["reason"], "sentinel override outside the sanctioned runtime directory is refused")
        self.assertTrue(outside.exists(), "an out-of-scope override must not consume the named sentinel")
        self.assertFalse(Path(str(outside) + ".fired").exists(), "an out-of-scope override must not write the spent marker")

        # The same override inside the sanctioned directory (patched to the
        # fixture sentinel home) consumes normally: the documented manual
        # recovery keeps working for real runtime paths. A fresh watcher is
        # installed first (a resume decision consumes its receipt, r4 F4),
        # and the fixture clock moves past the real-time peer-resume mark
        # the CLI fire wrote, the same way the legacy-receipt smoke does.
        self.clock.now = time.time() + 120.0
        self.install_watcher(self.fixture.adapter(), reset, "rw-scoped-override-2")
        sanctioned = self.fixture.root / "sanctioned-runtime" / "budget-resume.sentinel"
        sanctioned.parent.mkdir(parents=True, exist_ok=True)
        sanctioned.write_text("fired\n", encoding="utf-8")
        original_sentinel_default = watcher.DEFAULT_RESUME_SENTINEL
        watcher.DEFAULT_RESUME_SENTINEL = sanctioned
        self.addCleanup(setattr, watcher, "DEFAULT_RESUME_SENTINEL", original_sentinel_default)
        consumed = fire(sanctioned)
        self.assertTrue(consumed["sentinel"]["consumed"], consumed["sentinel"])
        self.assertFalse(sanctioned.exists())
        self.assertTrue(Path(str(sanctioned) + ".fired").exists())

    def test_supersede_tears_down_armed_carrier_and_later_arm_succeeds(self):
        # r6 F3, the documented sequence: a continue-boundary launchd arm,
        # a pause supersede, the ORPHAN job's fire (the job was never booted
        # out and still touches its sentinel), then a later continue arm.
        # Pre-fix the supersede tore nothing down, so the orphan's bare
        # sentinel self-disabled every later arm and automated resume
        # silently reverted to manual for the rest of the run. The supersede
        # now tears the recorded carrier down in the same operation,
        # receipt-only, and the later arm re-arms.
        bootstrap_calls: list[str] = []
        bootout_calls: list[str] = []

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        def fake_bootout(job):
            bootout_calls.append(str(job))
            return {"job": str(job), "exited": 0}

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        original_bootout = watcher.launchctl_bootout
        watcher.launchctl_bootout = fake_bootout
        self.addCleanup(setattr, watcher, "launchctl_bootout", original_bootout)
        job_dir = self.fixture.root / "r6f3-launchd"
        sentinel = self.fixture.root / "r6f3" / "budget-resume.sentinel"
        # The scheduler's spent-pair cleanup is scoped to the sanctioned
        # runtime directory: patch it to the fixture home so the final arm
        # runs hermetically.
        original_sentinel_default = watcher.DEFAULT_RESUME_SENTINEL
        watcher.DEFAULT_RESUME_SENTINEL = sentinel
        self.addCleanup(setattr, watcher, "DEFAULT_RESUME_SENTINEL", original_sentinel_default)

        def run(operation, payload):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", operation,
                        "--input", json.dumps(payload),
                        "--plan-slug", "fixture",
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        payload = {
            "probe_report": known_continue_report(3_600_000_000),
            "plan_path": str(self.fixture.plan_path),
            "job_dir": str(job_dir),
            "sentinel_path": str(sentinel),
        }
        scheduled = run("watcher-schedule", payload)
        self.assertEqual(scheduled["status"], "success", scheduled)
        self.assertEqual(scheduled["scheduling"]["mechanism"], "launchd")
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(receipt["armed_launchd"]["armed"], True, receipt["armed_launchd"])
        plist = Path(receipt["armed_launchd"]["plist_path"])
        self.assertTrue(plist.exists())
        # The orphan fire: the still-loaded job touches the sentinel before
        # running the manual command; nothing consumed it (the receipt is
        # still pending), so the bare sentinel is exactly the pre-fix trap.
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("fired\n", encoding="utf-8")

        superseded = run("watcher-supersede", {"reason": "pause"})
        self.assertEqual(superseded["status"], "success", superseded)
        self.assertEqual(superseded["reason_code"], "resume-watcher-cleared")
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])
        # The same-operation teardown: bootout of the recorded plist, the
        # recorded sentinel consumed, the fired marker written, the inert
        # plist removed - all receipt-only.
        teardown = superseded["carrier_teardown"]
        self.assertTrue(teardown["torn_down"], teardown)
        self.assertEqual(bootout_calls, [str(plist)], bootout_calls)
        self.assertEqual(teardown["bootout"]["job"], str(plist))
        self.assertEqual(teardown["sentinel"]["sentinel"], str(sentinel))
        self.assertTrue(teardown["sentinel"]["consumed"])
        self.assertFalse(sentinel.exists())
        self.assertTrue(Path(str(sentinel) + ".fired").exists())
        self.assertFalse(plist.exists())

        # The later continue arm: the spent pair is a sanctioned-directory
        # handshake the scheduler clears, so the arm re-arms launchd instead
        # of self-disabling on the bare sentinel (pre-fix outcome).
        rescheduled = run("watcher-schedule", payload)
        self.assertEqual(rescheduled["status"], "success", rescheduled)
        self.assertEqual(rescheduled["scheduling"]["mechanism"], "launchd", rescheduled["scheduling"])
        self.assertEqual(len(bootstrap_calls), 2, bootstrap_calls)
        self.assertEqual(self.fixture.peek_state()["resume_watcher"]["armed_launchd"]["armed"], True)

    def test_watcher_fire_default_sentinel_and_flag_parent_marker(self):
        # r4 F5: the documented production payload omits sentinel_path and
        # fired_path, so the fire-time default derivation (keyed
        # default_launchd_identity sentinel; flag-parent fired marker) must
        # be exercised by a CLI smoke, not only explicit-path smokes. The
        # defaults are patched to fixture paths, so the smoke stays
        # hermetic. Arms: a CLI schedule plus fire consuming the keyed
        # default sentinel from the receipt's armed carrier record (G2);
        # and a legacy receipt carrying no armed identity, whose fire
        # consumes NOTHING because the receipt is the only carrier-identity
        # source and no identity may be derived at fire time (G2).
        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        bootstrap_calls: list[str] = []
        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        default_job_dir = self.fixture.root / "prod-launchd"
        default_sentinel = self.fixture.root / "prod-runtime" / "budget-resume.sentinel"
        original_job_dir = watcher.DEFAULT_LAUNCHD_JOB_DIR
        original_sentinel = watcher.DEFAULT_RESUME_SENTINEL
        watcher.DEFAULT_LAUNCHD_JOB_DIR = default_job_dir
        watcher.DEFAULT_RESUME_SENTINEL = default_sentinel
        self.addCleanup(setattr, watcher, "DEFAULT_LAUNCHD_JOB_DIR", original_job_dir)
        self.addCleanup(setattr, watcher, "DEFAULT_RESUME_SENTINEL", original_sentinel)
        reset = 3_600_000_000

        def fire_with_defaults():
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-fire",
                        "--input", json.dumps({"flag_path": str(self.fixture.root / "prod-flag" / "budget-guard.flag")}),
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-schedule",
                    "--input", json.dumps({
                        "probe_report": known_continue_report(reset),
                        "plan_path": str(self.fixture.plan_path),
                    }),
                    "--plan-slug", "fixture",
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        scheduled = json.loads(out.getvalue())
        self.assertEqual(scheduled["status"], "success", scheduled)
        # r5 F11 bootstrap canary: the fake proves the smoke armed launchd
        # hermetically instead of silently mutating the real gui domain.
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the CLI smoke would be mutating the real gui domain")
        self.assertEqual(scheduled["scheduling"]["mechanism"], "launchd")
        keyed = watcher.default_launchd_identity("fixture", str(self.fixture.root))
        self.assertTrue((default_job_dir / watcher.launchd_identity_key("fixture", str(self.fixture.root))).exists())
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(receipt["armed_launchd"]["sentinel_path"], keyed["sentinel_path"])
        self.assertEqual(receipt["armed_launchd"]["fired_marker_path"], keyed["sentinel_path"] + ".fired")
        # The launchd job fired: the sentinel sits at the keyed default,
        # and the fired marker for this window sits next to the flag (the
        # payload names no fired_path, so the cleanup derives its home).
        sentinel_path = Path(keyed["sentinel_path"])
        sentinel_path.parent.mkdir(parents=True, exist_ok=True)
        sentinel_path.write_text("fired\n", encoding="utf-8")
        flag = self.fixture.root / "prod-flag" / "budget-guard.flag"
        write_guard_flag(flag, reset)
        marker = flag.parent / watcher.FIRED_MARKER_NAME
        marker.write_text(str(reset), encoding="utf-8")
        decision = fire_with_defaults()
        self.assertEqual(decision["decision"], "resume", decision)
        self.assertTrue(decision["sentinel"]["consumed"])
        self.assertEqual(decision["sentinel"]["sentinel"], keyed["sentinel_path"])
        self.assertFalse(sentinel_path.exists())
        self.assertEqual(decision["guard_cleanup"]["fired_path"], str(marker))
        self.assertTrue(decision["guard_cleanup"]["marker_removed"])
        self.assertFalse(marker.exists())
        # Legacy receipt arm (G2): a receipt with NO armed carrier record
        # consumes nothing - the receipt is the only carrier-identity
        # source, so the fire must not re-derive the keyed default
        # sentinel. The fixture clock moves past the real-time peer-resume
        # mark the CLI fire wrote (the CLI entry constructs its driver
        # without the fixture's fake clock), so the fresh window is newer
        # than the mark and the fire reaches the consumption decision
        # instead of standing down.
        self.clock.now = time.time() + 120.0
        self.install_watcher(self.fixture.adapter(), reset, "rw-legacy-fire")
        self.assertNotIn("armed_launchd", self.fixture.peek_state()["resume_watcher"])
        sentinel_path.write_text("fired\n", encoding="utf-8")
        write_guard_flag(flag, reset)
        legacy = fire_with_defaults()
        self.assertEqual(legacy["decision"], "resume", legacy)
        # No sentinel consumption happened: the armed carrier is unknown,
        # and deriving it at fire time is forbidden (the structural test
        # pins the same invariant on the module source).
        self.assertNotIn("sentinel", legacy)
        self.assertTrue(sentinel_path.exists(), "the fire must not consume a sentinel it did not record")

    def test_watcher_fire_watcher_id_echo_guard(self):
        # r4 F6: a fire naming a stale watcher id is refused before any
        # guard cleanup: a regression removing the echo guard would let the
        # stale-id fire resume the replacement early and clear budget
        # guards inside the still-armed window (evaluate_fire evaluates the
        # CURRENT receipt). Control arm: the current id fires through.
        reset = 3_600_000_000
        self.install_watcher(self.fixture.adapter(), reset, "rw-fire-a")
        # The replacement window: B replaces A (machine state records the
        # predecessor), and B's guards are armed.
        self.install_watcher(self.fixture.adapter(), reset + 60, "rw-fire-b")
        flag = self.fixture.root / "echo-guard.flag"
        write_guard_flag(flag, reset + 60)

        def fire(watcher_id):
            payload = {"flag_path": str(flag), "sentinel_path": str(self.fixture.root / "echo.sentinel")}
            if watcher_id is not None:
                payload["watcher_id"] = watcher_id
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(
                    [
                        "--manifest", str(self.fixture.state_path),
                        "--operation", "watcher-fire",
                        "--input", json.dumps(payload),
                        "--repo-root", str(self.fixture.root),
                    ]
                )
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        stale = fire("rw-fire-a")
        self.assertEqual(stale["reason_code"], "stale-attempt", stale)
        self.assertIn("rw-fire-b", stale["evidence"][0])
        self.assertNotIn("prompt", stale)
        self.assertTrue(flag.exists(), "a stale-id fire must never clear guards")
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertEqual(receipt["watcher_id"], "rw-fire-b")
        self.assertEqual(receipt["status"], "pending")
        # Control: the current id fires through and clears the guards.
        current = fire("rw-fire-b")
        self.assertEqual(current["decision"], "resume", current)
        self.assertTrue(current["guards_cleared"])
        self.assertFalse(flag.exists())

    def test_plans_watcher_fire_default_flag_path(self):
        # r4 O19: the plans boundary's fire defaults to the canonical guard
        # path when the payload names no flag_path - the exact shared-handler
        # line an r3 F4 revert would change. The default is patched to a
        # fixture flag so the smoke proves the default was consumed
        # hermetically.
        bootstrap_calls: list[str] = []

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        default_flag = self.fixture.root / "plans-default-flag" / "budget-guard.flag"
        original_default = watcher.DEFAULT_FLAG_PATH
        watcher.DEFAULT_FLAG_PATH = default_flag
        self.addCleanup(setattr, watcher, "DEFAULT_FLAG_PATH", original_default)
        root = self.fixture.root
        state_path = root / "plan-requirements-o19.json"
        plan_path = root / "o19-plan.md"
        plan_path.write_text("# fixture plan\n", encoding="utf-8")
        reset = 3_600_000_000

        def run(operation, payload):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = runtime.main(["--operation", operation, "--input", json.dumps(payload), "--repo-root", str(root)])
            self.assertEqual(code, 0, out.getvalue())
            return json.loads(out.getvalue())

        scheduled = run("plans-watcher-schedule", {
            "state_path": str(state_path),
            "plan_path": str(plan_path),
            "plan_slug": "fixture",
            "probe_report": known_continue_report(reset),
            "job_dir": str(root / "o19-launchd"),
            "sentinel_path": str(root / "o19.sentinel"),
        })
        self.assertEqual(scheduled["reason_code"], "resume-watcher-scheduled", scheduled)
        # r5 F11 bootstrap canary: the fake proves the smoke armed launchd
        # hermetically instead of silently mutating the real gui domain.
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the plans CLI smoke would be mutating the real gui domain")
        write_guard_flag(default_flag, reset)
        fired = run("plans-watcher-fire", {
            "state_path": str(state_path),
            "sentinel_path": str(root / "o19.sentinel"),
        })
        self.assertEqual(fired["decision"], "resume", fired)
        self.assertTrue(fired["guards_cleared"])
        self.assertFalse(default_flag.exists(), "the omitted flag_path must default to the canonical guard path")
        self.assertIn("already cleared", fired["prompt"])

    def test_resume_prompt_is_fire_aware(self) -> None:
        # r2 F12: the fire-rendered prompt must not re-teach the manual
        # pre-CLI stand-down procedure (the fences and checks already
        # passed); a literal agent following the old prompt looped and the
        # composed automation never invoked watcher-fire. The manual
        # procedure stays the SKILL.md no-CLI fallback only.
        prompt = watcher.build_resume_prompt({"watcher_id": "rw-x", "plan_path": "/tmp/p.md"})
        self.assertIn("/tmp/p.md", prompt)
        self.assertIn("Step 0.5", prompt)
        self.assertIn("already cleared", prompt)
        self.assertNotIn("four stand-down checks", prompt)

    def test_resume_prompt_guard_sentence_renders_three_cleanup_outcomes(self) -> None:
        # r5 F5 / r5 F14: the resume prompt's guard sentence renders from
        # the actual guard_cleanup receipt across its three outcomes. The
        # attempted-but-not-achieved outcome must claim no clearing and
        # carry the retry guidance; the not-configured outcome must claim
        # no clearing; only a cleared (or absent-guard) cleanup may claim
        # the clearing.
        receipt = {"watcher_id": "rw-guard", "plan_path": "/tmp/p.md"}
        cleared = watcher.build_resume_prompt(receipt, {"removed": True, "reason": "cleared"})
        self.assertIn("already cleared through the atomic compare-and-delete", cleared)
        absent = watcher.build_resume_prompt(receipt, {"removed": False, "reason": "flag-absent"})
        self.assertIn("already cleared through the atomic compare-and-delete", absent)
        refused = watcher.build_resume_prompt(receipt, {"removed": False, "refused": True, "reason": "newer-window"})
        self.assertIn("did not complete (reason: newer-window)", refused)
        self.assertIn("retry that cleanup after the single block", refused)
        self.assertNotIn("already cleared through the atomic compare-and-delete", refused)
        self.assertNotIn("no guard cleanup is configured", refused)
        unconfigured = watcher.build_resume_prompt(receipt, None)
        self.assertIn("no guard cleanup is configured", unconfigured)
        self.assertNotIn("already cleared through the atomic compare-and-delete", unconfigured)

        # Integration arm: a resume decision whose configured cleanup is
        # refused (the flag encodes a newer window) renders the attempted
        # sentence from the actual receipt, and guards_cleared stays False.
        reset = 3_600_000_000
        self.install_watcher(self.fixture.adapter(), reset, "rw-guard-render")
        newer = self.fixture.root / "guard-render" / "budget-guard.flag"
        write_guard_flag(newer, reset + 60)
        decision = watcher.fire_watcher(self.fixture.adapter(), self.fixture.peek_state()["resume_watcher"], flag_path=str(newer))
        self.assertEqual(decision["decision"], "resume", decision)
        self.assertFalse(decision["guards_cleared"])
        self.assertTrue(decision["guard_cleanup"]["refused"])
        self.assertIn("did not complete (reason: newer-window)", decision["prompt"])

    def test_resume_watcher_receipt_validator_negative_arms(self) -> None:
        # r5 F10: the receipt validator's negative arms. A valid receipt
        # passes; each mutation (missing field, empty or non-string
        # identity field, non-pending status, malformed replaces, non-
        # numeric or bool epoch, malformed digest) fails closed with
        # ValueError.
        def valid_receipt() -> dict:
            return {
                "watcher_id": "rw-validate",
                "plan_slug": "fixture",
                "repo_root": "/repo",
                "plan_path": "/repo/plan.md",
                "plan_digest": "a" * 64,
                "scheduled_at_epoch": 1_000,
                "reset_at_epoch": 3_600_000_000,
                "expected_generation": 0,
                "expected_progress_revision": 0,
                "boundary_generation": 1,
                "binding": "primary",
                "status": "pending",
                "replaces": None,
            }

        watcher.validate_resume_watcher_receipt(valid_receipt())
        with self.assertRaises(ValueError):
            watcher.validate_resume_watcher_receipt("not-a-mapping")
        mutations = [
            lambda r: r.pop("plan_digest"),
            lambda r: r.update(watcher_id=""),
            lambda r: r.update(watcher_id=7),
            lambda r: r.update(plan_slug="  "),
            lambda r: r.update(repo_root=None),
            lambda r: r.update(plan_path=""),
            lambda r: r.update(binding=""),
            lambda r: r.update(status="fired"),
            lambda r: r.update(replaces=5),
            lambda r: r.update(reset_at_epoch="3600000000"),
            lambda r: r.update(scheduled_at_epoch=True),
            lambda r: r.update(expected_progress_revision=False),
            lambda r: r.update(plan_digest="nothex"),
            lambda r: r.update(plan_digest="a" * 63),
        ]
        for mutate in mutations:
            receipt = valid_receipt()
            mutate(receipt)
            with self.assertRaises(ValueError, msg=repr(sorted(receipt.items()))):
                watcher.validate_resume_watcher_receipt(receipt)

    def test_canonical_plan_path_and_digest_mismatch_refuse(self) -> None:
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-digest")
        adapter = self.fixture.adapter()
        # Plan bytes changed after scheduling: the live digest fence refuses.
        self.fixture.plan_path.write_text("# fixture plan\n\n- [x] mutated body\n", encoding="utf-8")
        decision = watcher.evaluate_fire(adapter, self.fixture.peek_state()["resume_watcher"])
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("plan-digest", decision["mismatches"])
        self.assertFalse(decision["relaunch"])
        # A receipt for a different canonical plan path is fenced too.
        moved = dict(self.fixture.peek_state()["resume_watcher"])
        moved["plan_path"] = str(self.fixture.root / "elsewhere.md")
        decision = watcher.evaluate_fire(adapter, moved)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("plan-path", decision["mismatches"])
        # A receipt whose canonical repository root differs is fenced.
        rooted = dict(self.fixture.peek_state()["resume_watcher"])
        rooted["repo_root"] = str(self.fixture.root / "other")
        decision = watcher.evaluate_fire(adapter, rooted)
        self.assertEqual(decision["decision"], "refuse")
        self.assertIn("repository-root", decision["mismatches"])

    def test_watcher_runtime_driver_persistence_round_trip(self) -> None:
        first = self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-round-1")
        # Reload through a brand new driver: the receipt is durable.
        reloaded = runtime.RuntimeDriver(
            self.fixture.state_path,
            plan_slug="fixture",
            repo_root=self.fixture.root,
            commit_lookup=lambda _commit: True,
            clock=self.clock,
        )
        adapter = watcher.RuntimeResumeWatcherAdapter(reloaded)
        receipt = adapter.read_state()["resume_watcher"]
        self.assertEqual(receipt["watcher_id"], "rw-round-1")
        self.assertEqual(set(receipt), set(watcher.RESUME_WATCHER_FIELDS))
        self.assertEqual(receipt["expected_progress_revision"], 0)
        self.assertEqual(receipt["boundary_generation"], 1)
        self.assertEqual(receipt["status"], "pending")
        # Replacement through the reloaded driver records the predecessor.
        self.clock.advance(60)
        second = self.install_watcher(adapter, 3_660_000_000, "rw-round-2")
        self.assertEqual(second["resume_watcher"]["replaces"], "rw-round-1")
        self.assertEqual(second["resume_watcher"]["boundary_generation"], 2)
        # Progress and interrupt persist; supersede clears under the lock.
        self.assertEqual(reloaded.record_progress(["evidence"])["progress_revision"], 1)
        self.clock.advance(10)
        self.assertEqual(reloaded.record_interrupt()["status"], "success")
        snapshot = adapter.read_state()
        self.assertEqual(snapshot["progress_revision"], 1)
        self.assertIsNotNone(snapshot["user_interrupt"])
        supersedes = adapter.compare_and_swap_supersede(
            watcher.build_supersede_transition(snapshot, reason="complete")
        )
        self.assertEqual(supersedes["status"], "success")
        self.assertEqual(supersedes["superseded_watcher_id"], "rw-round-2")
        self.assertIsNone(adapter.read_state()["resume_watcher"])
        # manifest.md receives a projection only; machine state is authority.
        self.assertTrue(adapter.projection(adapter.read_state()).startswith("pending_resume_watcher: none"))
        projected = watcher.render_manifest_projection({"resume_watcher": first["resume_watcher"]})
        self.assertIn("rw-round-1", projected)
        self.assertIn("reset_at_epoch=3600000000", projected)
        history = [event["event"] for event in self.fixture.peek_state()["history"]]
        self.assertEqual(
            history,
            [
                "resume-watcher-scheduled",
                "resume-watcher-scheduled",
                "progress-recorded",
                "user-interrupt-recorded",
                "resume-watcher-superseded",
            ],
        )

    def test_stale_schedule_transition_never_mutates_machine_state(self) -> None:
        adapter = self.fixture.adapter()
        self.install_watcher(adapter, 3_600_000_000, "rw-cas-1")
        before = self.fixture.peek_state()
        stale = adapter.compare_and_swap_schedule(
            watcher.build_schedule_transition(
                {**adapter.read_state(), "boundary_generation": 0},
                watcher_id="rw-cas-2",
                plan_slug="fixture",
                repo_root=str(self.fixture.root),
                plan_path=str(self.fixture.plan_path),
                plan_digest=self.fixture.plan_digest(),
                reset_at_epoch=3_600_000_060,
                scheduled_at_epoch=int(self.clock()),
                binding="primary",
            )
        )
        self.assertEqual(stale["status"], "blocked")
        self.assertEqual(stale["reason_code"], "stale-attempt")
        self.assertFalse(stale["cas_applied"])
        after = self.fixture.peek_state()
        self.assertEqual(after["resume_watcher"]["watcher_id"], "rw-cas-1")
        self.assertEqual(after["boundary_generation"], before["boundary_generation"])

    def test_crash_after_pre_relaunch_manifest_refresh_is_recoverable(self) -> None:
        flag = self.fixture.root / "budget-guard.flag"
        fired = self.fixture.root / "budget-guard.fired"
        self.install_watcher(self.fixture.adapter(), 3_600_000_000, "rw-crash")
        write_guard_flag(flag, 3_600_000_000)
        fired.write_text("3600000000\n", encoding="utf-8")
        adapter = self.fixture.adapter()
        receipt = self.fixture.peek_state()["resume_watcher"]
        # The pre-relaunch manifest refresh happens; then the watcher crashes
        # before clearing guards or relaunching.
        first = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(first["decision"], "resume")
        # Recovery: a fresh evaluation of the same untouched state reaches the
        # same single relaunch decision.
        second = watcher.evaluate_fire(adapter, receipt)
        self.assertEqual(second["decision"], "resume")
        self.assertEqual(first["prompt"], second["prompt"])
        # The guard clear is an idempotent compare-and-delete: the first pass
        # removes both files, a replayed clear finds nothing to remove.
        cleared = watcher.fire_watcher(adapter, receipt, flag_path=flag, fired_path=fired)
        self.assertTrue(cleared["guards_cleared"])
        self.assertTrue(cleared["guard_cleanup"]["removed"])
        self.assertTrue(cleared["guard_cleanup"]["marker_removed"])
        self.assertFalse(flag.exists())
        self.assertFalse(fired.exists())
        replayed = watcher.fire_watcher(adapter, receipt, flag_path=flag, fired_path=fired)
        self.assertTrue(replayed["guards_cleared"])
        self.assertEqual(replayed["guard_cleanup"]["reason"], "flag-absent")

    def test_cli_watcher_schedule_and_fire_live_path(self) -> None:
        """r1 F5: the CLI watcher operations are the production invocation
        path. Scheduling through the CLI persists the receipt in machine
        state and arms the launchd fallback (never an arm-time sentinel,
        r1 F1; the arm bootstraps the job into launchd, r2 F4, faked here
        so the suite stays hermetic); firing through the CLI evaluates the
        fences and clears the guard flag and fired marker only on a resume
        decision."""

        def fake_bootstrap(_job):
            bootstrap_calls.append(str(_job))
            return True, ""

        bootstrap_calls: list[str] = []
        original_bootstrap = watcher.launchctl_bootstrap
        watcher.launchctl_bootstrap = fake_bootstrap
        self.addCleanup(setattr, watcher, "launchctl_bootstrap", original_bootstrap)
        flag = self.fixture.root / "budget-guard.flag"
        fired = self.fixture.root / "budget-guard.fired"
        job_dir = self.fixture.root / "launchd"
        sentinel = self.fixture.root / "budget-resume.sentinel"
        reset = 3_600_000_000
        write_guard_flag(flag, reset)
        schedule_payload = json.dumps(
            {
                "probe_report": known_continue_report(reset),
                "plan_path": str(self.fixture.plan_path),
                "job_dir": str(job_dir),
                "sentinel_path": str(sentinel),
            }
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-schedule",
                    "--input", schedule_payload,
                    "--plan-slug", "fixture",
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        # r3 F22 hermeticity canary: the fake bootstrap must actually be the
        # bound seam. A refactor freezing the launchctl default at import
        # time would run real launchctl from this smoke and leave the call
        # record empty.
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the CLI smoke would be mutating the real gui domain")
        scheduled = json.loads(out.getvalue())
        self.assertEqual(scheduled["status"], "success", scheduled)
        self.assertEqual(scheduled["scheduling"]["mechanism"], "launchd")
        receipt = self.fixture.peek_state()["resume_watcher"]
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["reset_at_epoch"], reset)
        self.assertEqual(receipt["status"], "pending")
        self.assertTrue((job_dir / "ai-playbook.budget-resume.plist").exists())
        self.assertFalse(sentinel.exists(), "no arm-time sentinel (r1 F1)")

        # Fire through the CLI: untouched machine state resumes and the
        # compare-and-delete clears both guards for this window. The payload
        # names the fixture sentinel, so the one-shot consumption receipt
        # (r3 F16) is exercised hermetically: the job never ran here, so the
        # sentinel is absent and the consumption is an honest no-op. r6 F6:
        # the payload override is scoped to the sanctioned runtime directory,
        # so the smoke patches the sanctioned directory to the fixture
        # sentinel and the consume stays an in-scope honest no-op.
        original_sentinel_default = watcher.DEFAULT_RESUME_SENTINEL
        watcher.DEFAULT_RESUME_SENTINEL = sentinel
        self.addCleanup(setattr, watcher, "DEFAULT_RESUME_SENTINEL", original_sentinel_default)
        fire_out = io.StringIO()
        with contextlib.redirect_stdout(fire_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-fire",
                    "--input", json.dumps({"flag_path": str(flag), "fired_path": str(fired), "sentinel_path": str(sentinel)}),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        decision = json.loads(fire_out.getvalue())
        self.assertEqual(decision["decision"], "resume", decision)
        self.assertEqual(decision["reason"], "untouched-state")
        self.assertIn(str(self.fixture.plan_path), decision["prompt"])
        self.assertTrue(decision["guards_cleared"])
        self.assertFalse(flag.exists())
        self.assertFalse(fired.exists())
        self.assertEqual(decision["sentinel"]["consumed"], False)
        self.assertEqual(decision["sentinel"]["reason"], "sentinel-absent")

        # A supersede through the CLI clears the pending watcher under CAS.
        sup_out = io.StringIO()
        with contextlib.redirect_stdout(sup_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-supersede",
                    "--input", json.dumps({"reason": "boundary-decision"}),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sup_out.getvalue())["status"], "success")
        self.assertIsNone(self.fixture.peek_state()["resume_watcher"])
        # Firing with nothing pending is a blocked stale-attempt, never a
        # traceback. The guard paths are pinned explicitly (r2 F20): the
        # empty-payload arm is hermetic by construction even under a
        # production regression in the supersede/no-pending guard, because
        # a fire that reached the cleanup would touch only these fixture
        # files, never the developer's real guard flag.
        none_out = io.StringIO()
        with contextlib.redirect_stdout(none_out):
            code = runtime.main(
                [
                    "--manifest", str(self.fixture.state_path),
                    "--operation", "watcher-fire",
                    "--input", json.dumps({
                        "flag_path": str(self.fixture.root / "budget-guard.flag"),
                        "fired_path": str(self.fixture.root / "budget-guard.fired"),
                    }),
                    "--repo-root", str(self.fixture.root),
                ]
            )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(none_out.getvalue())["reason_code"], "stale-attempt")

    def test_plans_authoring_watcher_cli_operations(self) -> None:
        # r2 F11: the authoring watcher machinery is invocable end to end
        # through the manifest-free plans-* operations: schedule over the
        # authoring state JSON, the resume marker the shared peer fence
        # reads, a fire that stands down on that marker, and supersede.
        root = self.fixture.root
        state_path = root / "plan-requirements-fixture.json"
        plan_path = root / "authoring-plan.md"
        plan_path.write_text("# fixture plan\n", encoding="utf-8")

        # Hermetic launchd: the fallback arm writes the plist into the
        # fixture job dir and the launchctl bootstrap is faked, so the
        # suite never touches the host's launchd domain (r2 F4).
        bootstrap_calls: list[str] = []

        def fake_bootstrap(_job):
            bootstrap_calls.append(str(_job))
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
            "state_path": str(state_path),
            "plan_path": str(plan_path),
            "plan_slug": "fixture",
            "probe_report": known_continue_report(3_600_000_000),
            "job_dir": str(job_dir),
            "sentinel_path": str(sentinel),
        })
        self.assertEqual(scheduled["reason_code"], "resume-watcher-scheduled", scheduled)
        # r3 F22 hermeticity canary (plans boundary): the fake bootstrap is
        # the live seam, not an import-time-frozen real launchctl.
        self.assertTrue(bootstrap_calls, "launchd bootstrap fake was never invoked; the plans CLI smoke would be mutating the real gui domain")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIsNotNone(state["resume_watcher"])
        marker = run("plans-resume-marker", {"state_path": str(state_path), "evidence": ["peer re-entry"]})
        self.assertEqual(marker["status"], "success")
        # The fire payload names the fixture guard paths explicitly: the
        # boundary default is now the canonical flag path (r3 F4), and the
        # smoke stays hermetic by construction instead of by stand-down
        # luck. guards_cleared is present on the stand-down too.
        fired = run("plans-watcher-fire", {
            "state_path": str(state_path),
            "flag_path": str(root / "plans-fire-budget-guard.flag"),
            "sentinel_path": str(sentinel),
        })
        self.assertEqual(fired["decision"], "stand_down", fired)
        self.assertEqual(fired["reason"], "peer-resumed")
        self.assertIn("guards_cleared", fired)
        self.assertFalse(fired["guards_cleared"])
        self.assertEqual(fired["sentinel"]["consumed"], False)
        superseded = run("plans-watcher-supersede", {"state_path": str(state_path), "reason": "boundary-decision"})
        self.assertEqual(superseded["status"], "success")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIsNone(state["resume_watcher"])
        # A malformed payload fails closed through the shared handler:
        # exit 1 with the error on stderr, never a traceback.
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = runtime.main(["--operation", "plans-resume-marker", "--input", json.dumps({}), "--repo-root", str(root)])
        self.assertEqual(code, 1)
        self.assertIn("state_path", err.getvalue())

    def test_watcher_compare_and_delete_does_not_remove_newer_flag(self) -> None:
        flag = self.fixture.root / "budget-guard.flag"
        expired = int(self.clock()) - 60
        newer = int(self.clock()) + 3_600
        # The cleanup's decision was made against the expired window...
        write_guard_flag(flag, expired)
        # ...but the probe writer has since replaced it with a newer window.
        self.assertTrue(
            probe.write_flag_if_paused(
                flag,
                "fixture",
                [{"kind": "primary", "used_percent": 95.0, "reset_at_epoch": newer, "reset_at_iso": "x", "minutes_remaining": 60}],
                "pause",
            )
        )
        self.assertEqual(flag_epoch(flag), newer)
        result = watcher.compare_and_delete_flag(flag, expired)
        self.assertFalse(result["removed"])
        self.assertTrue(result["refused"])
        self.assertEqual(result["reason"], "newer-window")
        self.assertTrue(flag.exists())
        self.assertEqual(flag_epoch(flag), newer)
        # The matching epoch is removed; a second replay finds nothing.
        self.assertTrue(watcher.compare_and_delete_flag(flag, newer)["removed"])
        self.assertFalse(flag.exists())
        self.assertEqual(watcher.compare_and_delete_flag(flag, newer)["reason"], "flag-absent")
        # Lock participation: a compare-and-delete blocked on the held shared
        # lock cannot decide until the holder releases. The `started` marker
        # (r1 F29) proves the thread reached its body before the blocked
        # assertion, so scheduler starvation cannot make the witness vacuous.
        write_guard_flag(flag, expired)
        lock_file = watcher.guard_lock_path(flag)
        self.assertEqual(lock_file.name, "budget-guard.lock")
        with watcher.budget_guard_lock(flag) as held:
            self.assertTrue(held)
            outcome: dict = {}
            started = threading.Event()

            def compare_delete() -> None:
                started.set()
                outcome.update(watcher.compare_and_delete_flag(flag, expired))

            thread = threading.Thread(target=compare_delete)
            thread.start()
            self.assertTrue(started.wait(5), "compare-and-delete witness never started")
            thread.join(0.5)
            self.assertTrue(thread.is_alive(), "compare-and-delete did not block on the shared guard lock")
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertTrue(outcome["removed"])

    def test_fired_marker_replacement_protected_from_watcher_cleanup(self) -> None:
        # r1 F20: the standalone compare_and_delete_fired_marker surface is
        # deleted; the marker branch of compare_and_delete_flag carries the
        # fired-marker replacement protection.
        flag = self.fixture.root / "budget-guard.flag"
        fired = self.fixture.root / "budget-guard.fired"
        old_window = int(self.clock()) - 60
        new_window = int(self.clock()) + 3_600
        # The flag and its marker were re-written for the newer window (the
        # probe writer and block path did): a cleanup deciding on the old
        # window is refused by the epoch fence, and the newer marker
        # survives.
        write_guard_flag(flag, new_window)
        fired.write_text(f"{new_window}\n", encoding="utf-8")
        result = watcher.compare_and_delete_flag(flag, old_window, fired_path=fired)
        self.assertFalse(result["removed"])
        self.assertTrue(result["refused"])
        self.assertEqual(result["reason"], "newer-window")
        self.assertTrue(fired.exists())
        self.assertEqual(fired.read_text(encoding="utf-8").strip(), str(new_window))
        self.assertTrue(flag.exists())
        # The marker that binds to the watcher's own window is removed with
        # the flag (marker_removed), and a replay finds nothing.
        write_guard_flag(flag, old_window)
        fired.write_text(f"{old_window}\n", encoding="utf-8")
        removed = watcher.compare_and_delete_flag(flag, old_window, fired_path=fired)
        self.assertTrue(removed["removed"])
        self.assertTrue(removed["marker_removed"])
        self.assertFalse(fired.exists())
        self.assertFalse(flag.exists())
        # A replayed clear finds nothing to remove.
        replay = watcher.compare_and_delete_flag(flag, old_window, fired_path=fired)
        self.assertEqual(replay["reason"], "flag-absent")

    def test_guard_interleaving_with_probe_writer_and_backstop_hook(self) -> None:
        flag = self.fixture.root / "budget-guard.flag"
        fired = self.fixture.root / "budget-guard.fired"
        expired = int(time.time()) - 120
        newer = int(time.time()) + 3_600
        # The probe writer arms an expired window through the shared lock.
        self.assertTrue(
            probe.write_flag_if_paused(
                flag,
                "fixture",
                [{"kind": "primary", "used_percent": 95.0, "reset_at_epoch": expired, "reset_at_iso": "x", "minutes_remaining": 0}],
                "pause",
            )
        )
        out = io.StringIO()
        hook_outcome: dict = {}
        cleaner_started = threading.Event()

        def hook_cleanup() -> None:
            cleaner_started.set()
            with contextlib.redirect_stdout(out):
                hook_outcome["code"] = budget_guard_core.main(
                    ["--runtime", "zcode", "--flag-path", str(flag), "--fired-path", str(fired)]
                )

        with watcher.budget_guard_lock(flag) as held:
            self.assertTrue(held)
            cleaner = threading.Thread(target=hook_cleanup)
            cleaner.start()
            self.assertTrue(cleaner_started.wait(5), "hook cleanup witness never started")
            cleaner.join(0.5)
            self.assertTrue(cleaner.is_alive(), "hook cleanup did not block on the shared guard lock")
            # The probe writer's replacement also waits for the same lock.
            writer_outcome: dict = {}
            writer_started = threading.Event()

            def writer_replacement() -> None:
                writer_started.set()
                writer_outcome["armed"] = probe.write_flag_if_paused(
                    flag,
                    "fixture",
                    [{"kind": "primary", "used_percent": 95.0, "reset_at_epoch": newer, "reset_at_iso": "x", "minutes_remaining": 60}],
                    "pause",
                )

            writer = threading.Thread(target=writer_replacement)
            writer.start()
            self.assertTrue(writer_started.wait(5), "probe writer witness never started")
            writer.join(0.5)
            self.assertTrue(writer.is_alive(), "probe writer did not participate in the shared guard lock")
        cleaner.join(5)
        writer.join(5)
        self.assertFalse(cleaner.is_alive())
        self.assertFalse(writer.is_alive())
        self.assertTrue(writer_outcome["armed"])
        # Whichever way the two unblocked participants ordered, the newer
        # window's flag survives and the hook's expired cleanup passed.
        self.assertEqual(hook_outcome["code"], budget_guard_core.EXIT_OK)
        self.assertEqual(out.getvalue(), "")
        self.assertTrue(flag.exists())
        self.assertEqual(flag_epoch(flag), newer)


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
        self.plan_path = self.root / "docs" / "plans" / "fixture-authoring.md"
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
            runtime._safe_write_json(self.state_path, state)

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
        # The same fenced receipt shape as the runtime adapter.
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
        moved["plan_path"] = str(self.fixture.root / "docs" / "plans" / "elsewhere.md")
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

    def test_authoring_and_runtime_adapters_share_one_state_machine(self) -> None:
        runtime_fixture = RuntimeFixture(self.clock)
        self.addCleanup(runtime_fixture.cleanup)
        authoring_writer = self.fixture.adapter()
        runtime_writer = runtime_fixture.adapter()
        # Both workflows implement the one adapter protocol.
        self.assertIsInstance(authoring_writer, watcher.WatcherStateAdapter)
        self.assertIsInstance(runtime_writer, watcher.WatcherStateAdapter)

        def all_subclasses(cls) -> set:
            found = set()
            for sub in cls.__subclasses__():
                found.add(sub)
                found |= all_subclasses(sub)
            return found

        # Exactly one state-machine hierarchy exists: the shared protocol
        # with the runtime and authoring adapters under it (plus this file's
        # in-memory fake); no second watcher machine.
        self.assertEqual(
            {cls.__name__ for cls in all_subclasses(watcher.WatcherStateAdapter)},
            {"RuntimeResumeWatcherAdapter", "PlansAuthoringWatcherAdapter", "FakeStateAdapter"},
        )
        # The same fenced receipt shape lands in both workflows' machine state.
        authoring_result = self.boundary(known_continue_report(7_200_000_090))
        runtime_transition = watcher.build_schedule_transition(
            runtime_writer.read_state(),
            watcher_id="rw-runtime-mirror",
            plan_slug="fixture",
            repo_root=str(runtime_fixture.root),
            plan_path=str(runtime_fixture.plan_path),
            plan_digest=runtime_fixture.plan_digest(),
            reset_at_epoch=7_200_000_090,
            scheduled_at_epoch=int(self.clock()),
            binding="primary",
        )
        runtime_outcome = runtime_writer.compare_and_swap_schedule(runtime_transition)
        self.assertEqual(runtime_outcome["status"], "success", runtime_outcome)
        self.assertEqual(
            set(authoring_result["machine"]["resume_watcher"]),
            set(runtime_outcome["resume_watcher"]),
            set(watcher.RESUME_WATCHER_FIELDS),
        )
        # Firing adapters are constructed after the scheduling writes, exactly
        # as a later watcher process would be; the same untouched-state fire
        # evaluation on both adapters resumes.
        authoring_fire = self.fixture.adapter()
        runtime_fire = runtime_fixture.adapter()
        authoring_decision = watcher.evaluate_fire(authoring_fire, self.fixture.peek_state()["resume_watcher"])
        runtime_decision = watcher.evaluate_fire(runtime_fire, runtime_fixture.peek_state()["resume_watcher"])
        for decision in (authoring_decision, runtime_decision):
            self.assertEqual(decision["decision"], "resume")
            self.assertEqual(decision["reason"], "untouched-state")
        # And the same semantic-progress stand-down on both.
        self.clock.advance(60)
        self.assertEqual(authoring_writer.record_progress(["round folded"])["status"], "success")
        self.assertEqual(runtime_fixture.driver.record_progress(["task-1:done"])["status"], "success")
        for adapter, state_path in (
            (authoring_fire, self.fixture.state_path),
            (runtime_fire, runtime_fixture.state_path),
        ):
            receipt = json.loads(state_path.read_text(encoding="utf-8"))["resume_watcher"]
            self.assertEqual(watcher.evaluate_fire(adapter, receipt)["reason"], "semantic-progress")


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
    # allowlist transitively over the call graph.
    DERIVATION_SYMBOLS = {
        "default_launchd_identity",
        "resolve_launchd_identity",
        "launchd_identity_key",
        "armed_launchd_identity",
        "launchd_plist_path",
        "cli_scheduler_chain",
    }
    # Which production function may call each derivation helper, and where
    # the schedule arm's branch sits inside the shared CLI handler.
    ALLOWED_CALLERS = {
        "default_launchd_identity": {"resolve_launchd_identity"},
        "resolve_launchd_identity": {"resolve_launchd_identity", "cli_scheduler_chain", "run_cli_watcher_operation"},
        "launchd_identity_key": {"launchd_identity_key", "default_launchd_identity"},
        "armed_launchd_identity": {"armed_launchd_identity", "run_cli_watcher_operation"},
        "launchd_plist_path": {"launchd_plist_path", "armed_launchd_identity", "schedule"},
        "cli_scheduler_chain": {"cli_scheduler_chain", "run_cli_watcher_operation"},
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
            # The one handler call site must sit in the SCHEDULE branch of
            # run_cli_watcher_operation (the arm), never the fire branch.
            if owner_name == "run_cli_watcher_operation":
                schedule_span = self._branch_span(owner_node, "schedule")
                fire_span = self._branch_span(owner_node, "fire")
                self.assertIsNotNone(schedule_span)
                self.assertIsNotNone(fire_span)
                self.assertGreaterEqual(node.lineno, schedule_span[0])
                self.assertLessEqual(node.lineno, schedule_span[1])
                self.assertFalse(
                    fire_span[0] <= node.lineno <= fire_span[1],
                    "carrier-identity derivation inside the fire branch",
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


if __name__ == "__main__":
    unittest.main()
