"""Scenario agreement for the Codex primary quota reset wake."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import execute_plan_resume_watcher as watcher
import execute_plan_runtime as runtime

CODEX = (ROOT / "agents/skills/maintenance/codex.md").read_text(encoding="utf-8")
QUOTA = (ROOT / "agents/skills/maintenance/quota-policy.md").read_text(encoding="utf-8")
STATE = (ROOT / "agents/skills/maintenance/state-file.md").read_text(encoding="utf-8")
SCHEDULING = (ROOT / "agents/skills/maintenance/scheduling.md").read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == heading), None)
    if start is None:
        return ""
    level = len(heading) - len(heading.lstrip("#"))
    end = next(
        (index for index in range(start + 1, len(lines))
         if lines[index].startswith("#") and len(lines[index]) - len(lines[index].lstrip("#")) <= level),
        len(lines),
    )
    return "\n".join(lines[start:end])


PRIMARY_WAKE = section(CODEX, "## Primary quota pause")


class CodexQuotaWakeScenarioTest(unittest.TestCase):
    def _route_schedule(self, *, binding="primary", reset_delta=0, state=None):
        base = Path(tempfile.mkdtemp(prefix="maintenance-codex-wake-route-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(base, ignore_errors=True))
        root = base / "repo"
        root.mkdir()
        state_dir = root / ".ai-playbook" / "maintenance"
        codex_bin = base / "bin"
        codex_bin.mkdir()
        executable = codex_bin / "codex"
        executable.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
        executable.chmod(0o755)
        codex_home = base / "codex-home"
        codex_home.mkdir()
        now = int(__import__("time").time())
        reset = now + 3600
        target = "docs/history/plans/route-target.md"
        target_path = root / target
        target_path.parent.mkdir(parents=True)
        target_path.write_text("open plan\n", encoding="utf-8")
        scheduler_state = root / ".ai-playbook" / "scheduler-state.json"
        scheduler_state.parent.mkdir(parents=True, exist_ok=True)
        scheduler_state.write_text(json.dumps(state if state is not None else {
            "pending_dispatch": {"kind": "execute", "target": target},
            "authoring_cycle_gate": None,
            "alert": None,
        }), encoding="utf-8")
        thread_id = str(uuid.uuid4())
        bootstrap_calls = []
        scheduler_type = watcher.CodexQuotaWakeScheduler

        def scheduler_factory(**kwargs):
            return scheduler_type(
                state_dir=kwargs["state_dir"],
                repo_root=root,
                env={"CODEX_THREAD_ID": thread_id, "CODEX_HOME": str(codex_home)},
                clock=lambda: now,
                timezone=ZoneInfo("UTC"),
                which=lambda name: str(executable) if name == "codex" else sys.executable if name == "python3" else None,
                bootstrap=lambda path: (bootstrap_calls.append(path) or (True, "loaded")),
                verify_loaded=lambda _label: (True, "loaded"),
                bootout=lambda _path: {"exited": 0},
                schedule_guard=kwargs["schedule_guard"],
            )

        quota_report = {
            "runtime": "codex",
            "status": "ok",
            "binding": binding,
            "pause_decision": "pause",
            "limits": [{"kind": "primary", "reset_at_epoch": reset + reset_delta}],
        }
        payload = {
            "thread_id": thread_id,
            "kind": "execute",
            "target": target,
            "phase": "task-3",
            "reset_at_epoch": reset,
            "repo_root": str(root),
        }
        with mock.patch.object(watcher, "CodexQuotaWakeScheduler", side_effect=scheduler_factory):
            with mock.patch.object(runtime, "_codex_quota_wake_quota_report", return_value=quota_report):
                result = runtime._codex_quota_wake_operation(payload, root)
        return result, bootstrap_calls

    def test_primary_pause_carries_exact_target_and_phase_to_verified_schedule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="maintenance-codex-wake-") as temporary:
            base = Path(temporary)
            root = base / "repo"
            root.mkdir()
            state_dir = root / ".ai-playbook" / "maintenance"
            codex_bin = base / "bin"
            codex_bin.mkdir()
            executable = codex_bin / "codex"
            executable.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
            executable.chmod(0o755)
            codex_home = base / "codex-home"
            codex_home.mkdir()
            thread_id = str(uuid.uuid4())
            now = 1_800_000_000
            env = {"CODEX_THREAD_ID": thread_id, "CODEX_HOME": str(codex_home)}
            bootstrap_calls: list[Path] = []
            loaded_calls: list[str] = []
            scheduler = watcher.CodexQuotaWakeScheduler(
                state_dir=state_dir,
                repo_root=root,
                env=env,
                clock=lambda: now,
                timezone=ZoneInfo("UTC"),
                which=lambda name: str(executable) if name == "codex" else sys.executable if name == "python3" else None,
                bootstrap=lambda path: (bootstrap_calls.append(path) or (True, "loaded")),
                verify_loaded=lambda label: (loaded_calls.append(label) or (True, "loaded")),
                bootout=lambda _path: {"exited": 0},
                schedule_guard=lambda _payload: {"ready": True},
            )
            payload = {
                "thread_id": thread_id,
                "kind": "execute",
                "target": "docs/history/plans/2026-11-08-example.md",
                "phase": "task-3",
                "reset_at_epoch": now + 300,
                "repo_root": str(root),
            }
            output = io.StringIO()
            with mock.patch.object(watcher, "CodexQuotaWakeScheduler", return_value=scheduler):
                with mock.patch.dict(__import__("os").environ, env, clear=True):
                    with redirect_stdout(output):
                        exit_code = runtime.main([
                            "--operation", "codex-quota-wake-schedule",
                            "--repo-root", str(root),
                            "--input", json.dumps(payload),
                        ])

            result = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(result["scheduled"], result)
            self.assertEqual(len(bootstrap_calls), 1)
            self.assertEqual(loaded_calls, [result["label"]])
            payload_path = Path(result["payload_path"])
            stored_payload = json.loads(payload_path.read_text(encoding="utf-8"))
            arm_receipt = json.loads((payload_path.parent / "arm-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual({key: stored_payload[key] for key in payload}, {**payload, "repo_root": str(root.resolve())})
            self.assertEqual(arm_receipt, {"payload_digest": result["payload_digest"], "payload": stored_payload})
            self.assertGreaterEqual(result["fire_epoch"], payload["reset_at_epoch"] + 600)
            self.assertEqual(
                watcher.compute_unique_launchd_minute(payload["reset_at_epoch"], timezone=ZoneInfo("UTC"))[0],
                result["fire_epoch"],
            )
            self.assertIn("binding` is `primary`", PRIMARY_WAKE)
            self.assertIn("pause_decision", PRIMARY_WAKE)
            self.assertIn("pending_dispatch", PRIMARY_WAKE)
            self.assertIn("codex-quota-wake-schedule", PRIMARY_WAKE)
            self.assertIn("reset_at_epoch", PRIMARY_WAKE)
            self.assertIn("+ 600", PRIMARY_WAKE)
            self.assertIn("loaded label", PRIMARY_WAKE)
            self.assertIn("arm receipt", PRIMARY_WAKE)
            self.assertIn("scheduled: true", PRIMARY_WAKE)
            self.assertIn("phase", PRIMARY_WAKE)

    def test_route_schedule_refuses_guard_failures_before_launchd_bootstrap(self) -> None:
        cases = [
            ("secondary binding", {"binding": "secondary"}, None),
            ("stale reset", {"reset_delta": 60}, None),
            ("explicit stop", {}, {"pending_dispatch": {"kind": "execute", "target": "docs/history/plans/route-target.md"}, "authoring_cycle_gate": {"gate": True}, "alert": None}),
            ("safety hold", {}, {"pending_dispatch": {"kind": "execute", "target": "docs/history/plans/route-target.md"}, "authoring_cycle_gate": None, "alert": {"reason": "hold"}}),
            ("empty queue", {}, {"pending_dispatch": None, "authoring_cycle_gate": None, "alert": None}),
            ("changed target", {}, {"pending_dispatch": {"kind": "execute", "target": "docs/history/plans/other.md"}, "authoring_cycle_gate": None, "alert": None}),
        ]
        for name, kwargs, state in cases:
            with self.subTest(case=name):
                result, bootstrap_calls = self._route_schedule(**kwargs, state=state)
                self.assertFalse(result["scheduled"], result)
                self.assertEqual(bootstrap_calls, [], f"{name} reached launchd bootstrap")

        positive, bootstrap_calls = self._route_schedule()
        self.assertTrue(positive["scheduled"], positive)
        self.assertEqual(len(bootstrap_calls), 1)

    def test_secondary_stop_and_empty_target_do_not_schedule(self) -> None:
        self.assertIn("secondary-only", PRIMARY_WAKE)
        self.assertIn("report-only", PRIMARY_WAKE)
        for token in ("explicit stop", "safety hold", "normal lane guards"):
            with self.subTest(token=token):
                self.assertIn(token, PRIMARY_WAKE)
        self.assertIn("Missing or stale values mean hold", PRIMARY_WAKE)
        for token in ("three-cap",):
            with self.subTest(token=token):
                self.assertIn(token, CODEX)
        self.assertNotIn("Do not follow up for quota pauses", CODEX)
        self.assertIn("secondary-binding reading stays report-only", QUOTA)

    def test_changed_primary_reset_replaces_wake_without_losing_target(self) -> None:
        for token in (
            "If the fresh primary decision is `continue`",
            "If the decision remains `pause` or `wait-for-reset`",
            "from that report's primary reset",
            "exactly one replacement",
            "retain the target",
        ):
            with self.subTest(token=token):
                self.assertIn(token, PRIMARY_WAKE)
        self.assertIn("same pending target", PRIMARY_WAKE)

    def test_fire_operation_wires_fresh_primary_quota_guard_at_final_queue_boundary(self) -> None:
        reset = 1_800_000_000
        new_reset = reset + 3600
        reports = [
            {
                "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "continue",
                "limits": [{"kind": "primary", "reset_at_epoch": reset}],
            },
            {
                "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "pause",
                "limits": [{"kind": "primary", "reset_at_epoch": new_reset}],
            },
        ]
        observed = {}

        class CapturingScheduler:
            def __init__(self, **kwargs):
                observed.update(kwargs)

            def fire(self, wake):
                return {
                    "initial": observed["fire_guard"](wake),
                    "final": observed["pre_queue_guard"](wake),
                }

        wake = {"target": "docs/history/plans/example.md", "reset_at_epoch": reset, "kind": "execute"}
        with mock.patch.object(watcher, "CodexQuotaWakeScheduler", CapturingScheduler), \
                mock.patch.object(runtime, "_codex_quota_wake_state_guard", return_value={"ready": True}), \
                mock.patch.object(runtime, "_codex_quota_wake_quota_report", side_effect=reports) as quota_probe:
            result = runtime._codex_quota_wake_fire_operation(wake, ROOT)

        self.assertTrue(result["initial"]["ready"], result)
        self.assertFalse(result["final"]["ready"], result)
        self.assertEqual(result["final"]["reason"], "primary-reset-changed")
        self.assertEqual(result["final"]["reset_at_epoch"], new_reset)
        self.assertEqual(quota_probe.call_count, 2, "the final queue callback must take a fresh quota reading")

    def test_production_fire_wait_for_reset_replaces_stale_wake_on_same_thread_without_queueing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="maintenance-codex-wait-for-reset-fire-") as temporary:
            base = Path(temporary)
            root = base / "repo"
            root.mkdir()
            target = "docs/history/plans/wait-for-reset-target.md"
            target_path = root / target
            target_path.parent.mkdir(parents=True)
            target_path.write_text("open plan\n", encoding="utf-8")
            state_path = root / ".ai-playbook" / "scheduler-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({
                "pending_dispatch": {"kind": "execute", "target": target},
                "authoring_cycle_gate": None,
                "alert": None,
            }), encoding="utf-8")

            codex_bin = base / "bin"
            codex_bin.mkdir()
            executable = codex_bin / "codex"
            executable.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
            executable.chmod(0o755)
            codex_home = base / "codex-home"
            codex_home.mkdir()
            thread_id = str(uuid.uuid4())
            env = {"CODEX_THREAD_ID": thread_id, "CODEX_HOME": str(codex_home)}
            now = {"epoch": 1_800_000_000}
            old_reset = now["epoch"] + 60
            fresh_reset = now["epoch"] + 3600
            initial_report = {
                "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "pause",
                "limits": [{"kind": "primary", "reset_at_epoch": old_reset}],
            }
            wait_report = {
                "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "wait-for-reset",
                "limits": [{"kind": "primary", "reset_at_epoch": fresh_reset, "minutes_remaining": 2}],
            }
            reports = []
            bootstrap_calls = []
            queue_calls = []
            verify_calls = []
            verify_results = iter([(True, "loaded"), (False, "booted out"), (True, "loaded")])
            scheduler_type = watcher.CodexQuotaWakeScheduler

            def quota_report(_root, _wake):
                if not reports:
                    reports.append(initial_report)
                    return initial_report
                return wait_report

            def scheduler_factory(**kwargs):
                return scheduler_type(
                    state_dir=kwargs["state_dir"],
                    repo_root=root,
                    env=env,
                    clock=lambda: now["epoch"],
                    timezone=ZoneInfo("UTC"),
                    which=lambda name: str(executable) if name == "codex" else sys.executable if name == "python3" else None,
                    bootstrap=lambda path: (bootstrap_calls.append(path) or (True, "loaded")),
                    verify_loaded=lambda label: (verify_calls.append(label) or next(verify_results)),
                    bootout=lambda _path: {"exited": 0},
                    queue_command=lambda argv, *_args: (queue_calls.append(list(argv)) or __import__("subprocess").CompletedProcess(argv, 0, "queued", "")),
                    fire_guard=kwargs.get("fire_guard"),
                    pre_queue_guard=kwargs.get("pre_queue_guard"),
                    schedule_guard=kwargs.get("schedule_guard"),
                )

            payload = {
                "thread_id": thread_id,
                "kind": "execute",
                "target": target,
                "phase": "task-3",
                "reset_at_epoch": old_reset,
                "repo_root": str(root),
            }
            output = io.StringIO()
            with mock.patch.object(watcher, "CodexQuotaWakeScheduler", side_effect=scheduler_factory), \
                    mock.patch.object(runtime, "_codex_quota_wake_quota_report", side_effect=quota_report), \
                    mock.patch.dict(__import__("os").environ, env, clear=True), \
                    redirect_stdout(output):
                schedule_exit = runtime.main([
                    "--operation", "codex-quota-wake-schedule", "--repo-root", str(root),
                    "--input", json.dumps(payload),
                ])

            scheduled = json.loads(output.getvalue())
            self.assertEqual(schedule_exit, 0)
            self.assertTrue(scheduled["scheduled"], scheduled)
            now["epoch"] = scheduled["fire_epoch"]
            output = io.StringIO()
            with mock.patch.object(watcher, "CodexQuotaWakeScheduler", side_effect=scheduler_factory), \
                    mock.patch.object(runtime, "_codex_quota_wake_quota_report", side_effect=quota_report), \
                    mock.patch.dict(__import__("os").environ, env, clear=True), \
                    redirect_stdout(output):
                fire_exit = runtime.main([
                    "--operation", "codex-quota-wake-fire", "--repo-root", str(root),
                    "--input", json.dumps({
                        "payload_path": scheduled["payload_path"],
                        "expected_fire_epoch": scheduled["fire_epoch"],
                    }),
                ])

            fired = json.loads(output.getvalue())
            self.assertEqual(fire_exit, 0)
            self.assertEqual(fired["decision"], "replacement-scheduled", fired)
            self.assertEqual(fired["target"], target)
            self.assertTrue(fired["replacement"]["scheduled"], fired)
            replacement = json.loads(Path(fired["replacement"]["payload_path"]).read_text(encoding="utf-8"))
            self.assertEqual(replacement["target"], target)
            self.assertEqual(replacement["thread_id"], thread_id)
            self.assertEqual(replacement["reset_at_epoch"], fresh_reset)
            self.assertGreaterEqual(fired["replacement"]["fire_epoch"], fresh_reset + 600)
            self.assertEqual(queue_calls, [], "a wait-for-reset replacement must never queue the stale wake")
            self.assertEqual(len(bootstrap_calls), 2, "the production fire path must arm exactly one replacement")

    def test_production_fire_wait_for_reset_suppresses_replacement_after_fresh_state_refusal(self) -> None:
        cases = {
            "explicit stop": lambda target: {
                "pending_dispatch": {"kind": "execute", "target": target},
                "authoring_cycle_gate": {"gate": True}, "alert": None,
            },
            "survey-only stop": lambda target: {
                "pending_dispatch": {"kind": "execute", "target": target},
                "authoring_cycle_gate": None, "survey_only": True, "alert": None,
            },
            "safety hold": lambda target: {
                "pending_dispatch": {"kind": "execute", "target": target},
                "authoring_cycle_gate": None, "alert": {"reason": "hold"},
            },
            "empty queue": lambda _target: {
                "pending_dispatch": None, "authoring_cycle_gate": None, "alert": None,
            },
            "changed target": lambda _target: {
                "pending_dispatch": {"kind": "execute", "target": "docs/history/plans/other-target.md"},
                "authoring_cycle_gate": None, "alert": None,
            },
        }
        for case_name, replacement_state in cases.items():
            with self.subTest(case=case_name), tempfile.TemporaryDirectory(prefix="maintenance-codex-fire-refusal-") as temporary:
                base = Path(temporary)
                root = base / "repo"
                root.mkdir()
                target = "docs/history/plans/wait-for-reset-target.md"
                target_path = root / target
                target_path.parent.mkdir(parents=True)
                target_path.write_text("open plan\n", encoding="utf-8")
                state_path = root / ".ai-playbook" / "scheduler-state.json"
                state_path.parent.mkdir(parents=True)
                state = {"pending_dispatch": {"kind": "execute", "target": target}, "authoring_cycle_gate": None, "alert": None}
                state_path.write_text(json.dumps(state), encoding="utf-8")
                codex_bin = base / "bin"
                codex_bin.mkdir()
                executable = codex_bin / "codex"
                executable.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
                executable.chmod(0o755)
                codex_home = base / "codex-home"
                codex_home.mkdir()
                thread_id = str(uuid.uuid4())
                env = {"CODEX_THREAD_ID": thread_id, "CODEX_HOME": str(codex_home)}
                now = {"epoch": 1_800_000_000}
                old_reset = now["epoch"] + 60
                fresh_reset = now["epoch"] + 3600
                reports = []
                bootstrap_calls = []
                queue_calls = []
                scheduler_type = watcher.CodexQuotaWakeScheduler

                def quota_report(_root, _wake):
                    if not reports:
                        report = {
                            "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "pause",
                            "limits": [{"kind": "primary", "reset_at_epoch": old_reset}],
                        }
                        reports.append(report)
                        return report
                    return {
                        "runtime": "codex", "status": "ok", "binding": "primary", "pause_decision": "wait-for-reset",
                        "limits": [{"kind": "primary", "reset_at_epoch": fresh_reset, "minutes_remaining": 2}],
                    }

                def scheduler_factory(**kwargs):
                    base_fire_guard = kwargs.get("fire_guard")
                    if base_fire_guard is not None:
                        def mutate_after_wait(wake):
                            result = dict(base_fire_guard(wake))
                            if result.get("reason") == "primary-quota-wait-for-reset":
                                state_path.write_text(json.dumps(replacement_state(target)), encoding="utf-8")
                            return result
                        fire_guard = mutate_after_wait
                    else:
                        fire_guard = None
                    return scheduler_type(
                        state_dir=kwargs["state_dir"], repo_root=root, env=env,
                        clock=lambda: now["epoch"], timezone=ZoneInfo("UTC"),
                        which=lambda name: str(executable) if name == "codex" else sys.executable if name == "python3" else None,
                        bootstrap=lambda path: (bootstrap_calls.append(path) or (True, "loaded")),
                        verify_loaded=lambda _label: (True, "loaded"), bootout=lambda _path: {"exited": 0},
                        queue_command=lambda argv, *_args: (queue_calls.append(list(argv)) or __import__("subprocess").CompletedProcess(argv, 0, "queued", "")),
                        fire_guard=fire_guard, pre_queue_guard=kwargs.get("pre_queue_guard"),
                        schedule_guard=kwargs.get("schedule_guard"),
                    )

                payload = {
                    "thread_id": thread_id, "kind": "execute", "target": target,
                    "phase": "task-3", "reset_at_epoch": old_reset, "repo_root": str(root),
                }
                with mock.patch.object(watcher, "CodexQuotaWakeScheduler", side_effect=scheduler_factory), \
                        mock.patch.object(runtime, "_codex_quota_wake_quota_report", side_effect=quota_report), \
                        mock.patch.dict(__import__("os").environ, env, clear=True):
                    output = io.StringIO()
                    with redirect_stdout(output), redirect_stderr(output):
                        self.assertEqual(runtime.main([
                            "--operation", "codex-quota-wake-schedule", "--repo-root", str(root),
                            "--input", json.dumps(payload),
                        ]), 0)
                    scheduled = json.loads(output.getvalue())
                    self.assertTrue(scheduled["scheduled"], scheduled)
                    now["epoch"] = scheduled["fire_epoch"]
                    output = io.StringIO()
                    with redirect_stdout(output), redirect_stderr(output):
                        fire_exit = runtime.main([
                            "--operation", "codex-quota-wake-fire", "--repo-root", str(root),
                            "--input", json.dumps({"payload_path": scheduled["payload_path"], "expected_fire_epoch": scheduled["fire_epoch"]}),
                        ])
                    self.assertEqual(fire_exit, 0, output.getvalue())

                fired = json.loads(output.getvalue())
                self.assertEqual(fired["decision"], "stand_down", fired)
                self.assertEqual(fired["reason"], {
                    "explicit stop": "stop", "survey-only stop": "survey-only-stop",
                    "safety hold": "safety-hold", "empty queue": "empty-queue", "changed target": "target-changed",
                }[case_name])
                self.assertEqual(len(bootstrap_calls), 1, "only the initial stale wake may be armed")
                self.assertEqual(queue_calls, [], "a fresh refusal must never queue the stale wake")
                persisted = json.loads(state_path.read_text(encoding="utf-8"))
                if case_name == "empty queue":
                    self.assertIsNone(persisted.get("pending_dispatch"))
                elif case_name == "changed target":
                    self.assertEqual(persisted["pending_dispatch"]["target"], "docs/history/plans/other-target.md")
                else:
                    self.assertEqual(persisted["pending_dispatch"]["target"], target)

    def test_existing_pending_dispatch_remains_authoritative_and_no_new_state_field(self) -> None:
        self.assertIn("existing `pending_dispatch`", PRIMARY_WAKE)
        self.assertIn("Preserve the selected work", PRIMARY_WAKE)
        self.assertIn("Do not add a scheduler-state field", PRIMARY_WAKE)
        self.assertIn("Codex primary-quota reset wake", STATE)
        self.assertIn("authoritative for the target and kind", STATE)
        self.assertIn("derive the continuation phase from the active run checkpoint", STATE)
        self.assertIn("Codex primary-quota reset wake", SCHEDULING)

    def test_shared_quota_policy_routes_runtime_specific_pause_handling_to_adapter(self) -> None:
        self.assertIn("Codex primary-pause wake routing", QUOTA)
        self.assertIn("codex.md", QUOTA)


if __name__ == "__main__":
    unittest.main()
