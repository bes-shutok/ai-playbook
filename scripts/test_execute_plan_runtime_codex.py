#!/usr/bin/env python3
"""Hermetic tests for the Codex runtime adapter boundary."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from execute_plan_runtime_codex import CodexAdapter, _cancel_process_tree, _verify_process_terminated, _subprocess_runner
from execute_plan_worker_registry import validate_provider_observation
import runtime_capabilities as capabilities


FIXTURE_DIR = Path(__file__).resolve().parent / "testdata/execute-plan/codex"

# Frame modules that never own an intercepted open: only the pathlib/io
# plumbing the observation wrapper wraps. The first frame outside this set is
# the open's caller (a test-module caller stays attributed to the test module
# and is therefore filtered out of the denial assertion).
_OBSERVATION_PLUMBING_MODULES = {"pathlib", "io", "os", "genericpath", "posixpath"}
_GUARDED_READ_MODULES = {"execute_plan_runtime_codex", "runtime_capabilities"}


def _worker_guard_argv(guard_path: Path, model: str) -> list[str]:
    event = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"model": model}})
    source = (
        "import importlib.util,io,os,sys; from pathlib import Path; "
        "spec=importlib.util.spec_from_file_location('worker_guard',sys.argv[1]); "
        "guard=importlib.util.module_from_spec(spec); spec.loader.exec_module(guard); "
        f"sys.stdin=io.StringIO({event!r}); guard.main(); "
        "config=Path(os.environ.get('CODEX_CONFIG') or (Path.home()/'.codex/config.toml')); "
        "print('EFFECTIVE_CONFIG='+str(config.resolve()))"
    )
    return [sys.executable, "-c", source, str(guard_path)]


def _nearest_caller_module() -> str:
    frame = sys._getframe(1).f_back
    while frame is not None:
        module = str(frame.f_globals.get("__name__", ""))
        if module not in _OBSERVATION_PLUMBING_MODULES:
            return module
        frame = frame.f_back
    return "<unknown>"


class RecordedRunner:
    def __init__(self, timeout=False, cleanup_verified=True):
        self.calls = []
        self.timeout = timeout
        self.cleanup_verified = cleanup_verified

    def __call__(self, argv, timeout_seconds, operation, policy_token=None):
        self.calls.append((list(argv), timeout_seconds, operation, policy_token))
        if self.timeout and operation == "launch":
            return {"timed_out": True, "handle": "owned-process-tree"}
        if argv[:3] == ["codex", "--version"]:
            return {"returncode": 0, "stdout": "codex-cli 0.153.4\n"}
        if argv[:3] == ["codex", "exec", "--help"]:
            return {"returncode": 0, "stdout": "Usage: codex exec [OPTIONS] [PROMPT]\n--json\n"}
        if argv[:4] == ["codex", "exec", "resume", "--help"]:
            return {"returncode": 0, "stdout": "Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]\n--json\n"}
        name = "wait.json" if operation == "wait" else ("resume.json" if "resume" in argv else "launch.json")
        return {"returncode": 0, "stdout": (FIXTURE_DIR / name).read_text()}

    def cancel(self, handle):
        self.calls.append(("cancel", handle))

    def verify_terminated(self, handle):
        return self.cleanup_verified


class LongWaitRunner(RecordedRunner):
    """Fake runner whose wait consumes a fixed duration on a simulated clock.

    The adapter's deadline is injected into the runner as ``timeout_seconds``,
    so the simulated wait times out exactly when the wait deadline is shorter
    than the simulated wait duration: the subprocess boundary's own deadline
    semantics, replayed deterministically without sleeping.
    """

    def __init__(self, simulated_wait_seconds):
        super().__init__()
        self.simulated_wait_seconds = simulated_wait_seconds

    def __call__(self, argv, timeout_seconds, operation, policy_token=None):
        if operation == "wait" and timeout_seconds < self.simulated_wait_seconds:
            return {"timed_out": True, "handle": "owned-process-tree", "stderr": "deadline exceeded"}
        return super().__call__(argv, timeout_seconds, operation, policy_token=policy_token)


class CodexAdapterTest(unittest.TestCase):
    def worker_launch(self, adapter, task_id, generation, *, policy_token="default", prompt=None, deadline_seconds=None):
        scope = self.policy() if policy_token == "default" or policy_token is None else policy_token
        role = {
            "role": "single-task-worker",
            "task_id": task_id,
            "claim_token": "fixture-claim",
            "generation": generation,
            "task_body": "Implement the fixture task.",
            "allowed_paths": list(scope["allowed_paths"]),
            "validation_commands": [{"id": "verify", "argv": ["python3", "-m", "unittest"], "criteria": ["fixture criterion"]}],
            "required_criteria": ["fixture criterion"],
            "evidence_owner": "worker",
            "worker_log_destination": "task-worker.log.md",
            "parent_obligations": [],
            "parent_obligations": [],
        }
        return adapter.launch(
            {"id": task_id, "worker_role": role},
            json.dumps(role) if prompt is None else prompt,
            generation,
            deadline_seconds=deadline_seconds,
            policy_token=None if policy_token is None else scope,
        )

    def test_translates_terminal_exec_json_events(self):
        adapter = CodexAdapter(Path.cwd(), runner=lambda *_args, **_kwargs: {"returncode": 0, "stdout": ""})
        completed = adapter.translate_host_result({"type": "turn.completed", "usage": {}}, 3, "task-4")
        self.assertEqual(completed["status"], "success")
        self.assertEqual(completed["reason_code"], "completed")
        self.assertEqual(completed["evidence"], ["Codex emitted turn.completed"])

        failed = adapter.translate_host_result(
            {"type": "turn.failed", "error": {"message": "worker failed"}}, 3, "task-4"
        )
        self.assertEqual(failed["status"], "blocked")
        self.assertEqual(failed["reason_code"], "runtime-error")
        self.assertIn("worker failed", failed["evidence"])

    def setUp(self) -> None:
        # Pin ambient execute-plan env inputs (hermeticity).
        self._saved_env = {key: os.environ.pop(key) for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST") if key in os.environ}

    def tearDown(self) -> None:
        os.environ.update(self._saved_env)
        for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST"):
            if key not in self._saved_env:
                os.environ.pop(key, None)

    @staticmethod
    def policy():
        return {"token": "policy", "repo_root": "/repo", "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}

    def test_recorded_codex_lifecycle(self):
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        launch = self.worker_launch(adapter, "task-4", 1)
        self.assertEqual(launch["status"], "success")
        self.assertEqual(launch["session_id"], "session-task-4")
        wait = adapter.wait(launch["session_id"], policy_token=self.policy())
        self.assertEqual(wait["status"], "success")
        resume = adapter.resume(launch["session_id"], "continue", 1, policy_token=self.policy())
        self.assertEqual(resume["status"], "success")
        self.assertTrue(any(call[0][0:4] == ["codex", "exec", "resume", "session-task-4"] for call in runner.calls if isinstance(call[0], list)))
        self.assertEqual(wait["evidence"], ["wait-checkpoint"])
        self.assertTrue(all(call[3] is not None for call in runner.calls if call[2] in {"launch", "resume"}))
        approval = adapter.translate_host_result({"status": "approval-required", "action_scope": "external-write:publish"}, 1, "task-4")
        self.assertEqual(approval["status"], "blocked")
        self.assertEqual(approval["retry_policy"]["mode"], "none")

    def test_launch_receipt_exposes_identity_needed_to_consume_handoff_binding(self):
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        p = self.policy()
        receipt = self.worker_launch(adapter, "task-4", 1, policy_token=p)
        self.assertEqual(receipt["status"], "success")
        for field in ("provider_session_id", "worker_id", "launch_id", "capacity_entry_id", "command_identity", "process_identity", "observed_at"):
            self.assertTrue(receipt.get(field), field)

    def test_launch_preserves_validated_task_role(self):
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        adapter.activation_check()
        policy = self.policy()
        result = self.worker_launch(adapter, "task-4", 1, policy_token=policy)
        self.assertEqual(result["status"], "success")
        launch_call = next(call for call in runner.calls if call[2] == "launch")
        self.assertEqual(json.loads(launch_call[0][-1])["role"], "single-task-worker")
        self.assertEqual(json.loads(launch_call[0][-1])["task_id"], "task-4")

        before = len([call for call in runner.calls if call[2] == "launch"])
        missing = adapter.launch({"id": "task-4"}, "{}", 1, policy_token=policy)
        after = len([call for call in runner.calls if call[2] == "launch"])
        self.assertEqual(missing["reason_code"], "contract-violation")
        self.assertEqual(after, before)

    def test_observe_inventory_accepts_an_empty_successful_process_snapshot(self):
        completed = subprocess.CompletedProcess([], 0, "  101 Tue Sep 22 11:41:37 2026 /sbin/launchd\n", "")
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: completed)

        observation = adapter.observe_inventory()

        self.assertEqual(observation["state"], "available")
        self.assertEqual(observation["inventory"], [])
        self.assertEqual(observation["capacity_slot_effect"], "retain")

    def test_observe_inventory_reports_codex_exec_pid_and_start_time(self):
        completed = subprocess.CompletedProcess(
            [],
            0,
            "  320 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec interactive\n"
            "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n"
            "  322 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume session-id --json\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: completed)

        observation = adapter.observe_inventory()

        self.assertEqual(observation["state"], "available")
        self.assertEqual(len(observation["inventory"]), 2)
        worker = observation["inventory"][0]
        self.assertEqual(worker["process_identity"], {"pid": 321, "start_time": "Tue Sep 22 11:41:37 2026"})
        self.assertTrue(worker["provider_session_id"].startswith("codex-process-321-"))

    def test_inventory_ignores_unrelated_process_command_with_unbalanced_quote(self):
        completed = subprocess.CompletedProcess(
            [],
            0,
            "  101 Tue Sep 22 11:41:37 2026 /sbin/launchd --note 'unfinished\n"
            "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: completed)

        observation = adapter.observe_inventory()

        self.assertEqual(observation["state"], "available")
        self.assertEqual(len(observation["inventory"]), 1)
        self.assertEqual(observation["inventory"][0]["process_identity"]["pid"], 321)

    def test_observe_inventory_fails_closed_for_failed_or_malformed_process_snapshot(self):
        failed = subprocess.CompletedProcess([], 1, "", "ps failed")
        malformed = subprocess.CompletedProcess([], 0, "not a process row\n", "")

        for snapshot in (failed, malformed):
            with self.subTest(snapshot=snapshot):
                adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda value=snapshot: value)
                observation = adapter.observe_inventory()
                self.assertEqual(observation["state"], "unavailable")
                self.assertIsNone(observation["inventory"])

    def test_launch_refuses_when_capacity_lock_is_already_held(self):
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "capacity.lock"
            runner = RecordedRunner()
            adapter = CodexAdapter(
                "/repo",
                runner=runner,
                approval_verified=True,
                process_snapshot=lambda: subprocess.CompletedProcess([], 0, "  101 Tue Sep 22 11:41:37 2026 /sbin/launchd\n", ""),
                capacity_lock_path=lock_path,
            )
            self.assertEqual(adapter.activation_check()["status"], "success")
            lock_path.touch()
            import fcntl
            with lock_path.open("r+") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = self.worker_launch(adapter, "task-4", 1)

        self.assertEqual(result["reason_code"], "capacity-unavailable")
        self.assertFalse(any(isinstance(call[0], list) and call[2] == "launch" for call in runner.calls))

    def test_launch_refuses_when_process_inventory_contains_active_codex_worker(self):
        snapshot = subprocess.CompletedProcess(
            [],
            0,
            "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n",
            "",
        )
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True, process_snapshot=lambda: snapshot)
        self.assertEqual(adapter.activation_check()["status"], "success")

        result = self.worker_launch(adapter, "task-4", 1)

        self.assertEqual(result["reason_code"], "capacity-unavailable")
        self.assertFalse(any(isinstance(call[0], list) and call[2] == "launch" for call in runner.calls))

    def test_inventory_survives_unmatched_quote_in_codex_prompt_arguments(self):
        # One live worker's unmatched shell quote in its prompt arguments
        # must not quarantine the host's capacity: the inventory reads quote
        # characters as literal characters and never parses prompt text as
        # shell, so the row stays present with its identity intact.
        snapshots = [
            subprocess.CompletedProcess(
                [], 0,
                "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement 'task\n",
                "",
            ),
            subprocess.CompletedProcess(
                [], 0,
                "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement \"task\n",
                "",
            ),
            subprocess.CompletedProcess(
                [], 0,
                "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement it's \"done\n",
                "",
            ),
        ]
        for snapshot in snapshots:
            with self.subTest(stdout=snapshot.stdout):
                adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda value=snapshot: value)

                observation = adapter.observe_inventory()

                self.assertEqual(observation["state"], "available")
                self.assertEqual(len(observation["inventory"]), 1)
                row = observation["inventory"][0]
                self.assertEqual(row["process_identity"], {"pid": 321, "start_time": "Tue Sep 22 11:41:37 2026"})

    def test_inventory_still_fails_closed_on_malformed_identity_fields(self):
        # Regression pin, expected green at RED: malformed identity fields
        # keep failing closed around the tolerant token scan.
        non_integer_pid = subprocess.CompletedProcess(
            [], 0,
            "  notapid Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n",
            "",
        )
        short_start_time = subprocess.CompletedProcess(
            [], 0,
            "  321 Sep 22 2026 /opt/homebrew/bin/codex exec\n",
            "",
        )
        for snapshot in (non_integer_pid, short_start_time):
            with self.subTest(stdout=snapshot.stdout):
                adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda value=snapshot: value)

                observation = adapter.observe_inventory()

                self.assertEqual(observation["state"], "unavailable")
                self.assertIsNone(observation["inventory"])

    def test_inventory_keeps_row_shape_and_empty_snapshot_guards(self):
        # Regression pin, expected green at RED: the row-shape guard and the
        # empty-snapshot guard keep failing closed around the tolerant token
        # scan.
        wrong_field_count = subprocess.CompletedProcess([], 0, "  321 Tue Sep 22 11:41:37 2026\n", "")
        empty_snapshot = subprocess.CompletedProcess([], 0, "\n", "")
        for snapshot in (wrong_field_count, empty_snapshot):
            with self.subTest(stdout=snapshot.stdout):
                adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda value=snapshot: value)

                observation = adapter.observe_inventory()

                self.assertEqual(observation["state"], "unavailable")
                self.assertIsNone(observation["inventory"])

    def test_inventory_resume_conversation_id_from_tolerant_tokens(self):
        # The conversation-id extraction consumes the tolerant token list
        # with its value-flag shadowing rule and option-like test unchanged.
        intact_id = subprocess.CompletedProcess(
            [], 0,
            "  330 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume session-id --json repair the 'quote\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: intact_id)
        observation = adapter.observe_inventory()
        self.assertEqual(observation["state"], "available")
        self.assertEqual(observation["inventory"][0]["conversation_id"], "session-id")

        shadowed_id = subprocess.CompletedProcess(
            [], 0,
            "  331 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume -C /repo --json session-id\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: shadowed_id)
        observation = adapter.observe_inventory()
        self.assertEqual(observation["state"], "available")
        self.assertNotIn("conversation_id", observation["inventory"][0])

        literal_json_after_id = subprocess.CompletedProcess(
            [], 0,
            "  332 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume session-id --json emit --json records\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: literal_json_after_id)
        observation = adapter.observe_inventory()
        self.assertEqual(observation["state"], "available")
        self.assertEqual(observation["inventory"][0]["conversation_id"], "session-id")

    def test_inventory_unrelated_live_exec_still_blocks_capacity(self):
        # Regression pin, expected green at RED: a clean-argv recognized exec
        # row still occupies the single capacity slot. Its discrimination
        # value is at GREEN, catching a narrowing rewrite that drops clean
        # rows from the inventory.
        snapshot = subprocess.CompletedProcess(
            [],
            0,
            "  333 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n",
            "",
        )
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True, process_snapshot=lambda: snapshot)
        self.assertEqual(adapter.activation_check()["status"], "success")

        result = self.worker_launch(adapter, "task-4", 1)

        self.assertEqual(result["reason_code"], "capacity-unavailable")
        self.assertFalse(any(isinstance(call[0], list) and call[2] == "launch" for call in runner.calls))

    def test_parallel_group_allows_registered_member_but_blocks_unrelated_process(self):
        process = {"pid": 41, "start_time": "Tue Sep 22 11:41:37 2026"}
        snapshot = subprocess.CompletedProcess([], 0, "  41 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n", "")
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True, process_snapshot=lambda: snapshot)
        self.assertEqual(adapter.activation_check()["status"], "success")
        policy = self.policy() | {"generation": 2, "parallel_member_processes": [process]}

        allowed = self.worker_launch(adapter, "task-5", 2, policy_token=policy)

        self.assertEqual(allowed["status"], "success", allowed)
        self.assertTrue(any(isinstance(call[0], list) and call[2] == "launch" for call in runner.calls))
        other_runner = RecordedRunner()
        other = CodexAdapter("/repo", runner=other_runner, approval_verified=True, process_snapshot=lambda: snapshot)
        self.assertEqual(other.activation_check()["status"], "success")
        fresh = self.policy() | {"generation": 2}
        refused = self.worker_launch(other, "task-5", 2, policy_token=fresh)
        self.assertEqual(refused["reason_code"], "capacity-unavailable")
        self.assertFalse(any(isinstance(call[0], list) and call[2] == "launch" for call in other_runner.calls))

    def test_batch_progress_translation_and_anchor_resume(self):
        # given: a host envelope with ordered member progress, attempt, batch
        # id, member ordinal, and one session id
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        progress = {"batch_id": "group-1", "member_id": "task-1", "member_ordinal": 1, "attempt": 1, "session_id": "sess-anchor"}
        host = {"status": "success", "reason_code": "completed", "evidence": ["member-one-checkpoint"], "batch_progress": dict(progress)}
        translated = adapter.translate_host_result(host, 1, "task-1")
        # expects: the normalized result preserves those fields
        self.assertEqual(translated["status"], "success")
        self.assertEqual(translated["batch_progress"], progress)
        self.assertEqual(translated["session_id"], "sess-anchor")
        # a malformed partial-progress envelope fails closed
        malformed = adapter.translate_host_result(
            {"status": "success", "reason_code": "completed", "evidence": ["m"], "batch_progress": {"batch_id": "group-1"}},
            1,
            "task-1",
        )
        self.assertEqual(malformed["status"], "blocked")
        self.assertEqual(malformed["reason_code"], "malformed-result")
        # a non-mapping progress envelope fails closed too
        broken = adapter.translate_host_result(
            {"status": "success", "reason_code": "completed", "evidence": ["m"], "batch_progress": ["group-1"]},
            1,
            "task-1",
        )
        self.assertEqual(broken["status"], "blocked")
        self.assertEqual(broken["reason_code"], "malformed-result")
        # expects: resume uses the anchor session with the active member
        # prompt and policy token
        member_token = {"token": "member-2", "repo_root": "/repo", "allowed_paths": ["task2.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}
        resumed = adapter.resume("sess-anchor", "implement member 2", 1, task_id="task-2", policy_token=member_token)
        self.assertEqual(resumed["status"], "success")
        resumed_calls = [call for call in runner.calls if isinstance(call[0], list) and call[0][:3] == ["codex", "exec", "resume"]]
        self.assertTrue(any(call[0][:5] == ["codex", "exec", "resume", "sess-anchor", "--json"] and call[0][5] == "implement member 2" for call in resumed_calls))
        self.assertTrue(any(call[3] is member_token for call in resumed_calls))

    def test_codex_timeout_cleans_descendants(self):
        runner = RecordedRunner(timeout=True, cleanup_verified=False)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        result = self.worker_launch(adapter, "task-4", 1, deadline_seconds=0.01)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "cleanup-unverified")
        self.assertEqual(result["retry_policy"]["mode"], "none")
        self.assertTrue(any(call[0] == "cancel" for call in runner.calls))

    def test_cleanup_unverified_timeout_never_relaunches(self):
        # Characterization of the cleanup fence (green before any Task 4
        # change): a timed-out worker whose process cleanup cannot be
        # verified produces the terminal cleanup-unverified receipt with
        # retry fully disabled, and the adapter never issues a second
        # process invocation after the cancellation - no automatic relaunch
        # of the same worker. The claim stays fenced downstream because the
        # reason code is outside RESUMABLE_REASONS, so the driver's retry
        # and resume machinery cannot read this receipt as free capacity.
        runner = RecordedRunner(timeout=True, cleanup_verified=False)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        process_calls_after_activation = len(runner.calls)
        result = self.worker_launch(adapter, "task-4", 1, deadline_seconds=0.01)
        # expects: the cleanup-unverified classification, never a plain
        # timeout and never a success
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "cleanup-unverified")
        # expects: retry disabled by the full standard shape
        self.assertEqual(result["retry_policy"], {"mode": "none", "max_attempts": 0, "attempts_remaining": 0})
        self.assertEqual(result["recovery_action"], "preserve-and-reconcile")
        # expects: the claim stays fenced - the reason code is outside the
        # resumable set, so no consumer may treat the timed-out worker's
        # slot as resumable or relaunchable
        self.assertNotIn(result["reason_code"], capabilities.RESUMABLE_REASONS)
        # expects: exactly one launch invocation happened (the activation
        # probes used --help shapes and do not count), the cancellation ran
        # once, and no relaunch attempt followed the unverified cleanup
        launch_calls = [call for call in runner.calls if isinstance(call[0], list) and call[0][:3] == ["codex", "exec", "--json"]]
        self.assertEqual(len(launch_calls), 1)
        self.assertEqual([call for call in runner.calls if call[0] == "cancel"], [("cancel", "owned-process-tree")])
        self.assertEqual(len(runner.calls), process_calls_after_activation + 2)

    def test_bounded_timeout_preserves_evidence(self):
        # Regression pin (green before and after the deadline baseline
        # change): a real deadline expiry preserves its evidence instead of
        # collapsing into a generic failure. The verified-timeout arm names
        # the deadline exceeded and carries the owned-process handle
        # representation; the unverified arm degrades to cleanup-unverified
        # with retry mode none so an unverifiable kill never reaps into a
        # silent retry.
        runner = RecordedRunner(timeout=True, cleanup_verified=True)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        verified = self.worker_launch(adapter, "task-4", 1, deadline_seconds=0.01)
        self.assertEqual(verified["status"], "blocked")
        self.assertEqual(verified["reason_code"], "timeout")
        self.assertIn("launch deadline exceeded", verified["evidence"])
        handle_entries = [entry for entry in verified["evidence"] if entry.startswith("owned_process=")]
        self.assertEqual(len(handle_entries), 1, verified["evidence"])
        self.assertIn("owned-process-tree", handle_entries[0])
        unverified_runner = RecordedRunner(timeout=True, cleanup_verified=False)
        unverified_adapter = CodexAdapter("/repo", runner=unverified_runner, approval_verified=True)
        self.assertEqual(unverified_adapter.activation_check()["status"], "success")
        unverified = self.worker_launch(unverified_adapter, "task-4", 1, deadline_seconds=0.01)
        self.assertEqual(unverified["status"], "blocked")
        self.assertEqual(unverified["reason_code"], "cleanup-unverified")
        self.assertEqual(unverified["retry_policy"]["mode"], "none")
        self.assertTrue(any("deadline exceeded" in entry for entry in unverified["evidence"]))
        self.assertTrue(any(call[0] == "cancel" for call in unverified_runner.calls))

    def test_timeout_receipt_distinct_from_malformed_result(self):
        # Regression pin: the same translation path must keep the timeout and
        # malformed-result reason codes distinct over the same argv, so a
        # deadline kill is never misread as a malformed worker envelope (or
        # vice versa) by downstream recovery.
        timeout_runner = RecordedRunner(timeout=True, cleanup_verified=True)
        timeout_adapter = CodexAdapter("/repo", runner=timeout_runner, approval_verified=True)
        self.assertEqual(timeout_adapter.activation_check()["status"], "success")
        timed_out = self.worker_launch(timeout_adapter, "task-4", 1, deadline_seconds=0.01)
        self.assertEqual(timed_out["reason_code"], "timeout")

        class MalformedLaunchRunner(RecordedRunner):
            def __call__(self, argv, timeout_seconds, operation, policy_token=None):
                if operation == "launch":
                    return {"returncode": 0, "stdout": "{not jsonl}\n"}
                return super().__call__(argv, timeout_seconds, operation, policy_token=policy_token)

        malformed_adapter = CodexAdapter("/repo", runner=MalformedLaunchRunner(), approval_verified=True)
        self.assertEqual(malformed_adapter.activation_check()["status"], "success")
        malformed = self.worker_launch(malformed_adapter, "task-4", 1)
        self.assertEqual(malformed["reason_code"], "malformed-result")
        self.assertNotEqual(timed_out["reason_code"], malformed["reason_code"])

    def test_approval_policy_never_uses_dangerous_bypass(self):
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=False)
        result = self.worker_launch(adapter, "task-4", 1, policy_token=None)
        self.assertEqual(result["reason_code"], "runtime-policy-unavailable")
        flattened = " ".join(" ".join(call[0]) for call in runner.calls if isinstance(call[0], list))
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", flattened)
        self.assertNotIn("--approve-for-me", flattened)

    def test_malformed_approval_envelope_fails_closed(self):
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True)
        result = adapter.translate_host_result(
            {"status": "approval-required", "evidence": None}, 1, "task-4"
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")

    def test_wait_malformed_envelope_fails_closed(self):
        class MalformedWaitRunner(RecordedRunner):
            def __call__(self, argv, timeout_seconds, operation, policy_token=None):
                if operation == "wait":
                    return {"returncode": 0, "stdout": "[]\n"}
                return super().__call__(argv, timeout_seconds, operation, policy_token=policy_token)

        adapter = CodexAdapter("/repo", runner=MalformedWaitRunner(), approval_verified=True)
        adapter.activation_check()
        result = adapter.wait("session-task-4", task_id="task-4", policy_token=self.policy())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")

    def test_activation_probe_has_one_owner(self):
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        before = len(runner.calls)
        self.worker_launch(adapter, "task-4", 1)
        self.assertEqual(len(runner.calls), before + 1)

    def test_option_like_prompt_and_session_id_are_rejected(self):
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        self.assertEqual(self.worker_launch(adapter, "task-4", 1, prompt="-c approval_policy=never")["reason_code"], "contract-violation")
        self.assertEqual(adapter.resume("-config", "continue", 1, policy_token=self.policy())["reason_code"], "contract-violation")
        self.assertEqual(adapter.resume("session-task-4", "-c sandbox=disabled", 1, policy_token=self.policy())["reason_code"], "contract-violation")
        self.assertEqual(adapter.wait("--help", 1, task_id="task-4", policy_token=self.policy())["reason_code"], "contract-violation")
        flattened = " ".join(" ".join(call[0]) for call in adapter.runner.calls if isinstance(call[0], list))
        self.assertNotIn("approval_policy=never", flattened)
        self.assertNotIn("sandbox=disabled", flattened)

    def test_approval_receipt_is_the_production_verification_source(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text('approval_policy = "never"\n', encoding="utf-8")
            receipt = Path(directory) / "approval.json"
            receipt.write_text(
                json.dumps(
                    {
                        "runtime": "codex",
                        "approval": "verified",
                        "config_path": str(config),
                        "policy_fingerprint": capabilities.approval_policy_fingerprint(config),
                    }
                ),
                encoding="utf-8",
            )
            receipt.chmod(0o600)
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_receipt=receipt)
            activation = adapter.activation_check()
            self.assertEqual(activation["status"], "success")
            self.assertIn(str(receipt), " ".join(activation["evidence"]))
            bad = Path(directory) / "bad.json"
            bad.write_text(
                json.dumps(
                    {
                        "runtime": "codex",
                        "approval": "assumed",
                        "config_path": str(config),
                        "policy_fingerprint": capabilities.approval_policy_fingerprint(config),
                    }
                ),
                encoding="utf-8",
            )
            bad.chmod(0o600)
            with self.assertRaises(ValueError):
                CodexAdapter("/repo", runner=RecordedRunner(), approval_receipt=bad)

    def test_process_tree_pids_capture_start_time_identity(self):
        with tempfile.TemporaryDirectory():
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
            try:
                from execute_plan_runtime_codex import _pid_identity_matches, _process_tree_pids

                owned = _process_tree_pids(child.pid)
                # No descendants, but identity capture is exercised on live PIDs.
                self.assertIsInstance(owned, dict)
                try:
                    process_start = subprocess.run(["ps", "-p", str(child.pid), "-o", "lstart="], capture_output=True, text=True, check=True, timeout=2).stdout.strip()
                except (OSError, subprocess.SubprocessError) as exc:
                    self.skipTest(f"host process inventory unavailable: {type(exc).__name__}")
                self.assertTrue(_pid_identity_matches(child.pid, process_start))
                self.assertFalse(_pid_identity_matches(child.pid, "Mon Jan  1 00:00:00 1999"))
            finally:
                child.terminate()
                child.wait()

    def test_recycled_pid_test_uses_disposable_child(self):
        # The recycled-PID witness runs against a real disposable child
        # process, never os.getpid(): a regressed identity guard must fail an
        # assertion here instead of risking the test runner's own process.
        with tempfile.TemporaryDirectory():
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                start_new_session=True,
            )
            try:
                runner = RecordedRunner(timeout=True, cleanup_verified=True)
                adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
                self.assertEqual(adapter.activation_check()["status"], "success")
                with mock.patch("execute_plan_runtime_codex._pid_identity_matches", return_value=False):
                    result = adapter._timeout_result(
                        {"handle": child, "owned_pids": {child.pid: "Mon Jan  1 00:00:00 1999"}},
                        "launch",
                        1,
                        "task-4:worker",
                    )
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "timeout")
                self.assertTrue(any(call[0] == "cancel" for call in runner.calls))
                # The live foreign process reusing the captured PID must not be
                # signalled: the captured identity no longer matches. Grace
                # pause first so a delivered SIGKILL is observed as an exit.
                time.sleep(0.2)
                self.assertIsNone(child.poll())
            finally:
                child.terminate()
                child.wait()

    def test_identity_check_precedes_sigkill(self):
        # The identity must be consulted immediately before os.kill(pid,
        # SIGKILL): when the match flips to false between the poll loop and
        # the kill, the recycled foreign process must not be signalled.
        with tempfile.TemporaryDirectory():
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                start_new_session=True,
            )
            try:
                runner = RecordedRunner(timeout=True, cleanup_verified=True)
                adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
                self.assertEqual(adapter.activation_check()["status"], "success")
                calls = {"count": 0}

                def flip_after_first(pid, identity):
                    calls["count"] += 1
                    return calls["count"] == 1

                with mock.patch(
                    "execute_plan_runtime_codex._pid_identity_matches",
                    side_effect=flip_after_first,
                ):
                    result = adapter._timeout_result(
                        {"handle": child, "owned_pids": {child.pid: "captured-identity"}},
                        "launch",
                        1,
                        "task-4:worker",
                    )
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "timeout")
                # No SIGKILL landed on the recycled foreign PID; give a
                # delivered signal time to surface as an exit before polling.
                time.sleep(0.2)
                self.assertIsNone(child.poll())
                self.assertGreaterEqual(calls["count"], 2)
            finally:
                child.terminate()
                child.wait()

    def test_real_owned_process_group_is_cleaned_on_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "child.pid"

            class ProcessRunner(RecordedRunner):
                def __call__(self, argv, timeout_seconds, operation, policy_token=None):
                    if operation.startswith("activation-"):
                        return super().__call__(argv, timeout_seconds, operation, policy_token=policy_token)
                    code = "import pathlib, signal, subprocess, sys, time; child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); pathlib.Path(sys.argv[1]).write_text(str(child.pid)); signal.signal(signal.SIGTERM, lambda *_: (child.terminate(), child.wait(), sys.exit(0))); time.sleep(30)"
                    process = subprocess.Popen([sys.executable, "-c", code, str(pid_file)], start_new_session=True)
                    for _ in range(100):
                        if pid_file.exists():
                            break
                        time.sleep(0.01)
                    from execute_plan_runtime_codex import _process_tree_pids

                    return {"timed_out": True, "handle": process, "owned_pids": _process_tree_pids(process.pid)}

                def cancel(self, handle):
                    self.calls.append(("cancel", handle))
                    _cancel_process_tree(handle)

                def verify_terminated(self, handle):
                    return _verify_process_terminated(handle)

            adapter = CodexAdapter("/repo", runner=ProcessRunner(), approval_verified=True)
            self.assertEqual(adapter.activation_check()["status"], "success")
            result = self.worker_launch(adapter, "task-4", 1)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "timeout")
            self.assertTrue(any(call[0] == "cancel" for call in adapter.runner.calls))
            child_pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)


    def test_subprocess_env_sanitized(self):
        # Literal expectation, deliberately NOT derived from SAFE_ENV_KEYS:
        # a mutation that widens the allowlist must fail this assertion, not
        # silently re-derive the expected set.
        expected_child_keys = {
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "TZ",
            "TMPDIR",
            "EXECUTE_PLAN_POLICY_TOKEN",
            "EXECUTE_PLAN_ALLOWED_PATHS",
        }
        original_env = dict(os.environ)
        with tempfile.TemporaryDirectory() as repo:
            poisoned = dict(original_env)
            poisoned.update(
                {
                    "HOME": str(Path(repo) / "home"),
                    "LANG": "C",
                    "LC_ALL": "C",
                    "TZ": "UTC",
                    "TMPDIR": str(Path(repo) / "tmp"),
                    # Poison: none of these may survive into the child.
                    "PYTHONPATH": "/hostile/site-packages",
                    "EXECUTE_PLAN_SECRET": "leak-me",
                    "OPENAI_API_KEY": "sk-leak",
                }
            )
            try:
                os.environ.clear()
                os.environ.update(poisoned)
                policy = {"token": "policy", "repo_root": repo, "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}
                result = _subprocess_runner(
                    [sys.executable, "-c", "import json, os; print(json.dumps(sorted(os.environ)))"],
                    15,
                    "launch",
                    policy_token=policy,
                )
            finally:
                os.environ.clear()
                os.environ.update(original_env)
        self.assertEqual(result.get("returncode"), 0, result.get("stderr"))
        # __CF_USER_TEXT_ENCODING is injected by macOS posix_spawn itself, not
        # by the runner's allowlist; everything else must match the literal set.
        self.assertEqual(set(json.loads(result["stdout"])) - {"__CF_USER_TEXT_ENCODING"}, expected_child_keys)

    def test_relative_codex_config_is_normalized_from_repo_root_and_forwarded(self):
        from codex_model_guard_probe import effective_config

        original_env = dict(os.environ)
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            (root / "config").mkdir(parents=True)
            config = root / "config" / "codex.toml"
            config.write_text("[agents]\ndefault_subagent_model = 'gpt-5.6-sol'\n")
            codex_dir = Path(temp) / "isolated-home" / ".codex"
            codex_dir.mkdir(parents=True)
            installed_guard = codex_dir / "require-luna.py"
            versioned_guard = Path(__file__).resolve().parents[1] / "agents/hooks/codex-model-guard/require-luna.py"
            installed_guard.write_bytes(versioned_guard.read_bytes())
            registration = codex_dir / "hooks.json"
            registration.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Agent", "hooks": [{"type": "command", "command": f"python3 {installed_guard}"}]}]}}))
            caller = Path(temp) / "elsewhere"
            caller.mkdir()
            try:
                os.chdir(caller)
                os.environ.clear()
                os.environ.update({"HOME": str(Path(temp) / "isolated-home"), "PATH": original_env.get("PATH", ""), "CODEX_CONFIG": "config/codex.toml"})
                adapter = CodexAdapter(root, runner=_subprocess_runner, approval_verified=True, model_guard_registration=registration, model_guard_source=versioned_guard)
                self.assertEqual(adapter.codex_config, str(config.resolve()))
                self.assertEqual(effective_config(dict(os.environ), root), config.resolve())
                self.assertNotEqual(effective_config(dict(os.environ), caller), adapter.codex_config)
                opened = []
                os_open = os.open

                def observe_open(file, flags, *args, **kwargs):
                    opened.append(Path(file).resolve())
                    return os_open(file, flags, *args, **kwargs)

                with mock.patch("os.open", side_effect=observe_open):
                    policy = adapter.model_guard_check()
                self.assertEqual(policy["status"], "ok", policy)
                self.assertEqual(Path(policy["config_path"]), config.resolve())
                self.assertEqual(set(opened), {registration.resolve(), installed_guard.resolve(), versioned_guard.resolve(), config.resolve()})
                worker_policy = {"token": "policy", "repo_root": str(root), "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}
                result = adapter._run(
                    _worker_guard_argv(installed_guard, "gpt-5.6-sol"),
                    15,
                    "launch",
                    policy_token=worker_policy,
                )
            finally:
                os.chdir(original_cwd)
                os.environ.clear()
                os.environ.update(original_env)
        self.assertEqual(result.get("returncode"), 0, result.get("stderr"))
        self.assertEqual(result["stdout"].strip(), f"EFFECTIVE_CONFIG={policy['config_path']}")

    def test_model_guard_check_matches_absolute_and_default_config_paths(self):
        from codex_model_guard_probe import effective_config

        source = Path(__file__).resolve().parents[1] / "agents/hooks/codex-model-guard/require-luna.py"
        original_env = dict(os.environ)
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            codex_dir = home / ".codex"
            codex_dir.mkdir(parents=True)
            installed = codex_dir / "require-luna.py"
            installed.write_bytes(source.read_bytes())
            registration = codex_dir / "hooks.json"
            registration.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Agent", "hooks": [{"type": "command", "command": f"python3 {installed}"}]}]}}))
            root = Path(temp) / "repo"
            root.mkdir()
            caller = Path(temp) / "caller"
            caller.mkdir()
            absolute = root / "absolute.toml"
            fallback = codex_dir / "config.toml"
            for path in (absolute, fallback):
                path.write_text("[agents]\ndefault_subagent_model = 'fixture-model'\n")
            try:
                for override, expected in ((str(absolute), absolute), (None, fallback)):
                    with self.subTest(override=override):
                        os.chdir(caller)
                        os.environ.clear()
                        os.environ.update({"HOME": str(home), "PATH": original_env.get("PATH", "")})
                        if override is not None:
                            os.environ["CODEX_CONFIG"] = override
                        adapter = CodexAdapter(root, runner=_subprocess_runner, model_guard_registration=registration, model_guard_source=source)
                        policy = adapter.model_guard_check()
                        self.assertEqual(policy["status"], "ok", policy)
                        self.assertEqual(Path(policy["config_path"]), expected.resolve())
                        self.assertEqual(effective_config(dict(os.environ), root, default_config=fallback), expected.resolve())
                        worker_policy = {"token": "policy", "repo_root": str(root), "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}
                        result = adapter._run(_worker_guard_argv(installed, "fixture-model"), 15, "launch", policy_token=worker_policy)
                        self.assertEqual(result.get("returncode"), 0, result.get("stderr"))
                        self.assertEqual(result["stdout"].strip(), f"EFFECTIVE_CONFIG={policy['config_path']}")
            finally:
                os.chdir(original_cwd)
                os.environ.clear()
                os.environ.update(original_env)

    def test_symlink_loop_config_override_refuses_without_mutation(self):
        # Characterization pin: on the pinned interpreter the loop override
        # refuses inside the probe's structured resolution (selected_config),
        # never at adapter construction, and the refusal mutates no run state.
        source = Path(__file__).resolve().parents[1] / "agents/hooks/codex-model-guard/require-luna.py"
        original_env = dict(os.environ)
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            codex_dir = home / ".codex"
            codex_dir.mkdir(parents=True)
            installed = codex_dir / "require-luna.py"
            installed.write_bytes(source.read_bytes())
            registration = codex_dir / "hooks.json"
            registration.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Agent", "hooks": [{"type": "command", "command": f"python3 {installed}"}]}]}}))
            root = Path(temp) / "repo"
            root.mkdir()
            config_loop = root / "config-loop.toml"
            config_loop.symlink_to(config_loop)
            snapshot = {path: (path.exists(), path.read_bytes() if path.is_file() and not path.is_symlink() else None) for path in (registration, installed)}
            try:
                os.chdir(root)
                os.environ.clear()
                os.environ.update({"HOME": str(home), "PATH": original_env.get("PATH", ""), "CODEX_CONFIG": str(config_loop)})
                adapter = CodexAdapter(root, runner=_subprocess_runner)
                policy = adapter.model_guard_check()
                self.assertEqual(policy["status"], "runtime-policy-unavailable", policy)
                self.assertEqual(policy["failed_check"], "selected_config")
                self.assertNotIn(str(root), json.dumps(policy))
                after = {path: (path.exists(), path.read_bytes() if path.is_file() and not path.is_symlink() else None) for path in (registration, installed)}
                self.assertEqual(after, snapshot)
                self.assertFalse((root / "runtime_state.json").exists())
            finally:
                os.chdir(original_cwd)
                os.environ.clear()
                os.environ.update(original_env)

    def test_no_live_installation_read(self):
        # The adapter lifecycle must not read any live installation path when
        # HOME and the package manifest point into a fixture root. Reads are
        # observed via module-scoped patches of the pathlib/io open call sites
        # (never process-wide audit hooks); the denial fires only for opens
        # whose nearest caller module is execute_plan_runtime_codex or
        # runtime_capabilities, while the zero-observation guard stays
        # unfiltered. Child-process reads are covered by the env-allowlist
        # witness, not here.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "home").mkdir()
            (root / "tmp").mkdir()
            (root / "repo").mkdir()
            config = root / "config.toml"
            config.write_text('approval_policy = "never"\n', encoding="utf-8")
            receipt = root / "approval.json"
            receipt.write_text(
                json.dumps(
                    {
                        "runtime": "codex",
                        "approval": "verified",
                        "config_path": str(config),
                        "policy_fingerprint": capabilities.approval_policy_fingerprint(config),
                    }
                ),
                encoding="utf-8",
            )
            receipt.chmod(0o600)
            manifest = root / "package-manifest.toml"
            manifest.write_text(
                "[adapters.codex]\nlaunch_deadline_seconds = 17.5\nwait_deadline_seconds = 42.0\n",
                encoding="utf-8",
            )
            original_env = dict(os.environ)
            observed: list[tuple[str, str]] = []
            # All target modules are pre-imported before arming, so importlib
            # opens cannot fire inside the observation window.
            self.assertIn("execute_plan_runtime_codex", sys.modules)
            self.assertIn("runtime_capabilities", sys.modules)

            def recording_path_open(path, *args, **kwargs):
                observed.append((str(path), _nearest_caller_module()))
                return original_path_open(path, *args, **kwargs)

            original_path_open = Path.open
            original_read_text = Path.read_text
            original_read_bytes = Path.read_bytes

            def recording_read_text(path, *args, **kwargs):
                observed.append((str(path), _nearest_caller_module()))
                return original_read_text(path, *args, **kwargs)

            def recording_read_bytes(path, *args, **kwargs):
                observed.append((str(path), _nearest_caller_module()))
                return original_read_bytes(path, *args, **kwargs)

            original_io_open = io.open

            def recording_io_open(file, *args, **kwargs):
                observed.append((str(file), _nearest_caller_module()))
                return original_io_open(file, *args, **kwargs)

            try:
                os.environ["HOME"] = str(root / "home")
                # TMPDIR pinned into the fixture root so system-temp reads
                # cannot false-positive as live-installation access.
                os.environ["TMPDIR"] = str(root / "tmp")
                os.environ["EXECUTE_PLAN_PACKAGE_MANIFEST"] = str(manifest)
                with mock.patch.object(Path, "open", recording_path_open), mock.patch.object(
                    Path, "read_text", recording_read_text
                ), mock.patch.object(Path, "read_bytes", recording_read_bytes), mock.patch(
                    "io.open", recording_io_open
                ):
                    adapter = CodexAdapter(root / "repo", runner=RecordedRunner(), approval_receipt=receipt)
                    self.assertEqual(adapter.launch_deadline, 17.5)
                    self.assertEqual(adapter.activation_check()["status"], "success")
                    policy = {"token": "policy", "repo_root": str((root / "repo").resolve()), "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1}
                    launch = self.worker_launch(adapter, "task-4", 1, policy_token=policy)
                    self.assertEqual(launch["status"], "success")
            finally:
                os.environ.clear()
                os.environ.update(original_env)
            fixture_prefix = str(root)
            inside = [entry for entry in observed if entry[0].startswith(fixture_prefix)]
            # Zero-observation guard: the interception must have seen real
            # opens inside the fixture root, unfiltered by caller module.
            self.assertTrue(inside, observed)
            violations = [
                entry for entry in observed if entry[1] in _GUARDED_READ_MODULES and not entry[0].startswith(fixture_prefix)
            ]
            self.assertEqual(violations, [], observed)

    def test_package_manifest_ambient_read(self):
        # Absent-var branch: the documented default-deadline fallback is the
        # current contract baseline (launch 900 / wait 1500). (Failing closed
        # on a missing manifest is declined as a behavior change that would
        # break non-activated runs; recorded in the Task 12 disposition.)
        # Literals 900.0/1500.0 on purpose: a mutation of the default
        # constants away from the contract baseline must fail these
        # assertions.
        self.assertNotIn("EXECUTE_PLAN_PACKAGE_MANIFEST", os.environ)
        adapter = CodexAdapter("/repo", runner=RecordedRunner())
        self.assertEqual(adapter.launch_deadline, 900.0)
        self.assertEqual(adapter.wait_deadline, 1500.0)

        # Valid-manifest branch: the manifest deadlines are loaded and used.
        # try/finally restores the environment (mirroring the no-live-read
        # witness) so the exported manifest pointer cannot leak into later
        # tests in the same process.
        try:
            with tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "package-manifest.toml"
                manifest.write_text(
                    "[adapters.codex]\nlaunch_deadline_seconds = 17.5\nwait_deadline_seconds = 42.0\n",
                    encoding="utf-8",
                )
                os.environ["EXECUTE_PLAN_PACKAGE_MANIFEST"] = str(manifest)
                adapter = CodexAdapter("/repo", runner=RecordedRunner())
        finally:
            os.environ.pop("EXECUTE_PLAN_PACKAGE_MANIFEST", None)
        self.assertEqual(adapter.launch_deadline, 17.5)
        self.assertEqual(adapter.wait_deadline, 42.0)

    def test_package_manifest_pins_cross_runtime_baseline(self):
        # The shipped package manifest and Codex adapter profile are the
        # two host-specific deadline surfaces and must stay in sync.
        repo_root = Path(__file__).resolve().parents[1]
        manifest_path = repo_root / "agents/skills/execute-plan/package-manifest.toml"
        with manifest_path.open("rb") as stream:
            values = tomllib.load(stream).get("adapters", {}).get("codex", {})
        self.assertEqual(values.get("launch_deadline_seconds"), 900)
        self.assertEqual(values.get("wait_deadline_seconds"), 1500)
        profile_text = (repo_root / "agents/skills/execute-plan/runtime-adapters/codex.md").read_text(encoding="utf-8")
        baseline_lines = [
            line for line in profile_text.splitlines()
            if "`launch_deadline_seconds = 900`" in line and "`wait_deadline_seconds = 1500`" in line
        ]
        self.assertTrue(baseline_lines, "Codex adapter profile baseline naming both deadline values is missing")

    def test_omitted_manifest_keys_fall_back_to_contract_baseline(self):
        # A manifest document whose [adapters.codex] block omits both
        # deadline keys must fall back to the in-code defaults, and those
        # defaults equal the contract baseline (900/1500): the normal
        # defaults cover the actual worker contract, not an arbitrary short
        # window.
        try:
            with tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "package-manifest.toml"
                manifest.write_text('[adapters.codex]\nadapter_version = "1.0"\n', encoding="utf-8")
                os.environ["EXECUTE_PLAN_PACKAGE_MANIFEST"] = str(manifest)
                adapter = CodexAdapter("/repo", runner=RecordedRunner())
        finally:
            os.environ.pop("EXECUTE_PLAN_PACKAGE_MANIFEST", None)
        self.assertEqual(adapter.launch_deadline, 900.0)
        self.assertEqual(adapter.wait_deadline, 1500.0)

    def test_legitimate_long_wait_within_deadline_completes(self):
        # A legitimate 20-minute worker body of work (1200 simulated seconds
        # on the runner's simulated clock) must complete under the in-code
        # default wait deadline: constructed with no explicit wait_deadline
        # argument and no temp manifest, so the default constants themselves
        # decide the outcome and the pre-baseline RED expectation is
        # deterministic.
        runner = LongWaitRunner(1200.0)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        result = adapter.wait("session-task-4", task_id="task-4", policy_token=self.policy())
        self.assertEqual(result["status"], "success", result)
        self.assertNotEqual(result["reason_code"], "timeout")


class CodexAdapterTerminalEvidenceTest(unittest.TestCase):
    """Task 1 rows: the conversation-keyed terminal-evidence port.

    Retrieval-boundary seam: every consult-bearing row injects the records
    root (an injected temp records root), never the ambient home-relative
    default. The read time is pinned by a before/after monotonic bracket
    around the consult plus a magnitude guard proving the record's
    completion wall-clock timestamp is never used as ``observed_at``.
    """

    def setUp(self) -> None:
        # Pin ambient execute-plan env inputs (hermeticity), exactly as the
        # sibling adapter test class: adapter construction reads no ambient
        # configuration.
        self._saved_env = {key: os.environ.pop(key) for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST") if key in os.environ}

    def tearDown(self) -> None:
        os.environ.update(self._saved_env)
        for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST"):
            if key not in self._saved_env:
                os.environ.pop(key, None)

    @staticmethod
    def record_text(*envelopes) -> str:
        return "".join(json.dumps(item) + "\n" for item in envelopes)

    @classmethod
    def completed_record(cls, thread_id="session-task-4", completed_at="2026-09-28T12:00:00Z") -> str:
        # The provider's own conversation record: the same JSONL envelope
        # stream the live boundary emits. The completion wall-clock stamp
        # rides on the completion envelope as metadata only.
        return cls.record_text(
            {"type": "thread.started", "thread_id": thread_id},
            {"type": "turn.completed", "status": "success", "reason_code": "completed", "evidence": ["worker-checkpoint"], "action_scope": "repository-task", "checkpoint_identity": "task-4:worker", "generation": 1, "timestamp": completed_at},
        )

    @classmethod
    def running_record(cls, thread_id="session-task-4") -> str:
        # Record present, turn not proven completed: no decision-bearing
        # final envelope exists yet.
        return cls.record_text({"type": "thread.started", "thread_id": thread_id})

    def test_terminal_observation_for_completed_conversation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.completed_record(), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            before = time.monotonic()
            observation = adapter.observe_terminal_evidence("session-task-4")
            after = time.monotonic()
            # The port never caches: a second consult re-reads the record
            # source and reports its current state with a fresh read.
            (root / "session-task-4.jsonl").write_text(self.running_record(), encoding="utf-8")
            second = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(observation["state"], "terminal")
        self.assertEqual(observation["observation_kind"], "terminal-evidence")
        self.assertEqual(observation["provider_identity"], {"session_id": "session-task-4"})
        self.assertIs(observation["proof"]["verified"], True)
        self.assertEqual(observation["proof"]["kind"], "provider-terminal")
        self.assertEqual(observation["capacity_slot_effect"], "release")
        # observed_at is the port's own read time in the monotonic domain...
        self.assertGreaterEqual(observation["observed_at"], before)
        self.assertLessEqual(observation["observed_at"], after)
        # ...never the record's completion wall-clock timestamp: the
        # magnitude guard keeps the 2026 wall epoch (about 1.79e9) out of
        # the boot-relative monotonic domain, and the completion stamp
        # rides as proof metadata only.
        self.assertLess(observation["observed_at"], 1_000_000_000.0)
        self.assertEqual(observation["proof"]["record_completed_at"], "2026-09-28T12:00:00Z")
        self.assertNotEqual(second["state"], "terminal")
        self.assertEqual(second["detail_signal"], "record-not-terminal")
        self.assertGreaterEqual(second["observed_at"], observation["observed_at"])

    def test_terminal_observation_reads_native_codex_record_envelopes(self):
        # Codex session JSONL stores provider identity and event data inside
        # each envelope's payload, rather than using the flat exec JSONL
        # result shape handled by the live process adapter.
        native_record = self.record_text(
            {
                "type": "session_meta",
                "payload": {"session_id": "session-task-4", "id": "session-task-4"},
            },
            {
                "type": "event_msg",
                "timestamp": "2026-09-28T12:00:00Z",
                "payload": {"type": "task_complete", "completed_at": "2026-09-28T12:00:00Z"},
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(native_record, encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(observation["state"], "terminal")
        self.assertEqual(observation["provider_identity"], {"session_id": "session-task-4"})
        self.assertTrue(observation["proof"]["verified"])
        self.assertEqual(observation["proof"]["record_completed_at"], "2026-09-28T12:00:00Z")

    def test_missing_process_is_not_terminal(self):
        # No provider record under the canonical root and no OS process:
        # the port refuses, it never infers completion from process absence.
        with tempfile.TemporaryDirectory() as directory:
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=Path(directory))
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertNotEqual(observation["state"], "terminal")
        self.assertIn(observation["state"], {"unavailable", "stale", "malformed", "timed-out", "unsupported"})
        self.assertEqual(observation["detail_signal"], "record-not-found")
        self.assertFalse(observation["proof"]["verified"])
        self.assertEqual(observation["process_identity"], {})
        # A nonexistent records root is contained the same way (port
        # totality): non-terminal, never a raise.
        with tempfile.TemporaryDirectory() as directory:
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=Path(directory) / "absent")
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertNotEqual(observation["state"], "terminal")
        self.assertFalse(observation["proof"]["verified"])

    def test_record_identity_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.completed_record("other-conversation"), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertNotEqual(observation["state"], "terminal")
        self.assertEqual(observation["detail_signal"], "identity-mismatch")
        # The lookup argument is never echoed onto the observation: identity
        # derives from the record's content and refuses on mismatch.
        self.assertEqual(observation["provider_identity"], {})
        # A record with no internal provider id at all cannot be bound.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.record_text({"type": "turn.completed", "status": "success"}), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertNotEqual(observation["state"], "terminal")
        self.assertEqual(observation["detail_signal"], "identity-mismatch")
        self.assertEqual(observation["provider_identity"], {})

    def test_port_is_read_only_against_provider_state(self):
        runner = RecordedRunner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.completed_record(), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=runner, approval_verified=True, terminal_records_root=root)
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(observation["state"], "terminal")
        argv_calls = [call[0] for call in runner.calls if isinstance(call[0], list)]
        turn_starting = [argv for argv in argv_calls if len(argv) > 1 and argv[1] == "exec"]
        self.assertEqual(turn_starting, [])
        # File retrieval spawns no process at all over the consult.
        self.assertEqual(argv_calls, [])
        # The consult carries the explicit ps-snapshot-precedent timeout.
        self.assertEqual(adapter.consult_timeout_seconds, 2.0)

    def test_resume_argv_extraction(self):
        extract = CodexAdapter._resume_conversation_id
        accepted = [
            (["codex", "exec", "resume", "session-id", "--json"], "session-id"),
            (["codex", "exec", "resume", "--json", "session-id"], "session-id"),
            (["codex", "exec", "resume", "session-id", "--json", "-C", "/repo"], "session-id"),
            (["/opt/homebrew/bin/codex", "exec", "resume", "wrap-id", "--json"], "wrap-id"),
            (["/usr/local/bin/codex.exe", "exec", "resume", "win-id", "--json"], "win-id"),
        ]
        for argv, expected in accepted:
            with self.subTest(argv=argv):
                self.assertEqual(extract(argv), expected)
        negative = [
            ["codex", "exec", "resume", "--json"],
            ["codex", "exec", "resume"],
            # A value-taking flag before the first positional token shadows
            # the id position: extraction refuses rather than mis-attribute.
            ["codex", "exec", "resume", "-C", "/repo", "--json", "session-id"],
            ["codex", "exec", "--json", "-C", "/repo", "prompt"],
        ]
        for argv in negative:
            with self.subTest(argv=argv):
                self.assertIsNone(extract(argv))
        # Parse integration: the extracted id is an additive row key only
        # where it applies; the process-keyed row shape is untouched
        # otherwise (the frozen inventory pin stays green).
        snapshot = (
            "  321 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec --json -C /repo implement\n"
            "  322 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume session-id --json\n"
        )
        inventory = CodexAdapter._parse_process_snapshot(snapshot)
        self.assertNotIn("conversation_id", inventory[0])
        self.assertEqual(inventory[1]["conversation_id"], "session-id")

    def test_conversation_id_shape_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.completed_record(), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)

            # Control: the interception below sees real record reads for a
            # well-formed lookup key.
            original_read_text = Path.read_text
            reads: list[str] = []

            def recording_read_text(path, *args, **kwargs):
                reads.append(str(path))
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", recording_read_text):
                good = adapter.observe_terminal_evidence("session-task-4")
            self.assertEqual(good["state"], "terminal")
            self.assertTrue(reads)

            original_is_file = Path.is_file
            original_rglob = Path.rglob
            touched: list[str] = []

            def recording_is_file(path):
                touched.append(f"is_file:{path}")
                return original_is_file(path)

            def recording_rglob(path, pattern):
                touched.append(f"rglob:{path}:{pattern}")
                return original_rglob(path, pattern)

            for bad_id in ("../escape", "with/slash", "back\\slash", "..", ".", "", "   ", "id with space", "dots.in.id"):
                with self.subTest(bad_id=bad_id):
                    touched.clear()
                    reads.clear()
                    with mock.patch.object(Path, "read_text", recording_read_text), mock.patch.object(
                        Path, "is_file", recording_is_file
                    ), mock.patch.object(Path, "rglob", recording_rglob):
                        refused = adapter.observe_terminal_evidence(bad_id)
                    self.assertEqual(refused["detail_signal"], "invalid-conversation-id")
                    self.assertNotEqual(refused["state"], "terminal")
                    self.assertFalse(refused["proof"]["verified"])
                    # The refusal fires before any record path is derived or
                    # read.
                    self.assertEqual(touched, [], touched)
                    self.assertEqual(reads, [], reads)

    def test_non_terminal_detail_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=Path(directory))
            not_found = adapter.observe_terminal_evidence("session-task-4")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text(self.running_record(), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            not_terminal = adapter.observe_terminal_evidence("session-task-4")
        # A present-but-unparseable record is record present, turn not
        # proven completed.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "session-task-4.jsonl").write_text("{not jsonl}\n", encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            unparseable = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(not_found["detail_signal"], "record-not-found")
        self.assertEqual(not_terminal["detail_signal"], "record-not-terminal")
        self.assertEqual(unparseable["detail_signal"], "record-not-terminal")
        self.assertNotEqual(not_found["detail_signal"], not_terminal["detail_signal"])
        for observation in (not_found, not_terminal, unparseable):
            self.assertNotEqual(observation["state"], "terminal")
            self.assertFalse(observation["proof"]["verified"])

    def test_retrieval_boundary(self):
        # Direct canonical layout under the injected records root: the port
        # obtains the record through the seam and translates it correctly.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "records"
            root.mkdir()
            (root / "session-task-4.jsonl").write_text(self.completed_record(), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=root)
            observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(observation["state"], "terminal")
        self.assertEqual(observation["provider_identity"], {"session_id": "session-task-4"})
        self.assertTrue(observation["proof"]["verified"])
        # Date-partitioned rollout naming is found through the bounded scan.
        with tempfile.TemporaryDirectory() as directory:
            nested = Path(directory) / "sessions" / "2026" / "09" / "28"
            nested.mkdir(parents=True)
            (nested / "rollout-2026-09-28T12-00-00-session-task-9.jsonl").write_text(self.completed_record("session-task-9"), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True, terminal_records_root=Path(directory))
            observation = adapter.observe_terminal_evidence("session-task-9")
        self.assertEqual(observation["state"], "terminal")
        # An injected runner with no explicit root must default to a
        # session-local temp root, never a home-relative read.
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True)
        self.assertNotEqual(adapter.terminal_records_root, Path.home() / ".codex" / "sessions")
        observation = adapter.observe_terminal_evidence("session-task-4")
        self.assertEqual(observation["detail_signal"], "record-not-found")

    def test_live_process_inventory_unchanged(self):
        # Regression pin, green before and after the parse extension: a live
        # `codex exec resume` row is reported as process-keyed available
        # inventory exactly as today, whatever additive row keys land.
        snapshot = subprocess.CompletedProcess(
            [],
            0,
            "  322 Tue Sep 22 11:41:37 2026 /opt/homebrew/bin/codex exec resume session-id --json\n",
            "",
        )
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), process_snapshot=lambda: snapshot)

        observation = adapter.observe_inventory()

        self.assertEqual(observation["observation_kind"], "inventory")
        self.assertEqual(observation["state"], "available")
        self.assertEqual(observation["capacity_slot_effect"], "retain")
        self.assertEqual(len(observation["inventory"]), 1)
        row = observation["inventory"][0]
        self.assertEqual(row["process_identity"], {"pid": 322, "start_time": "Tue Sep 22 11:41:37 2026"})
        self.assertTrue(row["provider_session_id"].startswith("codex-process-322-"))

    def test_stale_consumer_normalization_unchanged(self):
        # The chosen wiring keeps the freshness comparison consumer-owned:
        # the driver wraps the port observation and re-enters the validating
        # observation layer. An aged observation, injected as an aged cached
        # read (its observed_at aged relative to the consumer's now, not an
        # old completion timestamp), must still normalize to state stale
        # with quarantine effect there. The port's own no-cache freshness is
        # pinned by the record-mutation arm of the completed-observation
        # row; this row stays green before the port exists.
        now = time.monotonic()
        item = {
            "provider_session_id": "session-task-4",
            "state": "terminal",
            "proof": {"verified": True, "kind": "provider-terminal"},
            "worker_id": "worker-task-4-session-task-4",
        }
        aged = {
            "version": 1,
            "observation_kind": "terminal-evidence",
            "state": "terminal",
            "observed_at": now - 3600.0,
            "freshness_window": 5.0,
            "provider_identity": {"session_id": "session-task-4"},
            "process_identity": {},
            "capacity_slot_effect": "release",
            "proof": {"verified": True, "kind": "provider-terminal"},
            "inventory": [item],
        }
        normalized = validate_provider_observation(aged, now=now, expected_kind="terminal-evidence")
        self.assertEqual(normalized["state"], "stale")
        self.assertEqual(normalized["capacity_slot_effect"], "quarantine")
        # Control: the same envelope shape at a fresh read passes
        # validation, so the stale outcome above is the freshness
        # comparison, not the envelope shape.
        fresh = dict(aged, observed_at=now)
        normalized = validate_provider_observation(fresh, now=now, expected_kind="terminal-evidence")
        self.assertEqual(normalized["state"], "terminal")


if __name__ == "__main__":
    unittest.main()
