#!/usr/bin/env python3
"""Hermetic tests for the Codex runtime adapter boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from execute_plan_runtime_codex import CodexAdapter, _cancel_process_tree, _verify_process_terminated


FIXTURE_DIR = Path(__file__).resolve().parent / "testdata/execute-plan/codex"


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


class CodexAdapterTest(unittest.TestCase):
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
        launch = adapter.launch({"id": "task-4"}, "implement task", 1, policy_token=self.policy())
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

    def test_codex_timeout_cleans_descendants(self):
        runner = RecordedRunner(timeout=True, cleanup_verified=False)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        result = adapter.launch({"id": "task-4"}, "implement task", 1, deadline_seconds=0.01, policy_token=self.policy())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "cleanup-unverified")
        self.assertEqual(result["retry_policy"]["mode"], "none")
        self.assertTrue(any(call[0] == "cancel" for call in runner.calls))

    def test_approval_policy_never_uses_dangerous_bypass(self):
        runner = RecordedRunner()
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=False)
        result = adapter.launch({"id": "task-4"}, "implement task", 1)
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
        adapter.launch({"id": "task-4"}, "implement", 1, policy_token=self.policy())
        self.assertEqual(len(runner.calls), before + 1)

    def test_option_like_prompt_and_session_id_are_rejected(self):
        adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        self.assertEqual(adapter.launch({"id": "task-4"}, "-c approval_policy=never", 1, policy_token=self.policy())["reason_code"], "contract-violation")
        self.assertEqual(adapter.resume("-config", "continue", 1, policy_token=self.policy())["reason_code"], "contract-violation")
        self.assertEqual(adapter.resume("session-task-4", "-c sandbox=disabled", 1, policy_token=self.policy())["reason_code"], "contract-violation")
        self.assertEqual(adapter.wait("--help", 1, task_id="task-4", policy_token=self.policy())["reason_code"], "contract-violation")
        flattened = " ".join(" ".join(call[0]) for call in adapter.runner.calls if isinstance(call[0], list))
        self.assertNotIn("approval_policy=never", flattened)
        self.assertNotIn("sandbox=disabled", flattened)

    def test_approval_receipt_is_the_production_verification_source(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "approval.json"
            receipt.write_text(json.dumps({"runtime": "codex", "approval": "verified"}), encoding="utf-8")
            adapter = CodexAdapter("/repo", runner=RecordedRunner(), approval_receipt=receipt)
            activation = adapter.activation_check()
            self.assertEqual(activation["status"], "success")
            self.assertIn(str(receipt), " ".join(activation["evidence"]))
            bad = Path(directory) / "bad.json"
            bad.write_text(json.dumps({"runtime": "codex", "approval": "assumed"}), encoding="utf-8")
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
                self.assertTrue(_pid_identity_matches(child.pid, subprocess.run(["ps", "-p", str(child.pid), "-o", "lstart="], capture_output=True, text=True).stdout.strip()))
                self.assertFalse(_pid_identity_matches(child.pid, "Mon Jan  1 00:00:00 1999"))
            finally:
                child.terminate()
                child.wait()

    def test_timeout_cleanup_treats_recycled_pid_identity_as_exited(self):
        # A live foreign process (this test process) reusing a captured PID
        # must not be signalled: the captured identity no longer matches.
        runner = RecordedRunner(timeout=True, cleanup_verified=True)
        adapter = CodexAdapter("/repo", runner=runner, approval_verified=True)
        self.assertEqual(adapter.activation_check()["status"], "success")
        result = adapter._timeout_result(
            {"handle": "recycled-handle", "owned_pids": {os.getpid(): "Mon Jan  1 00:00:00 1999"}},
            "launch",
            1,
            "task-4:worker",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "timeout")
        self.assertTrue(any(call[0] == "cancel" for call in runner.calls))

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
            result = adapter.launch({"id": "task-4"}, "implement", 1, policy_token=self.policy())
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "timeout")
            self.assertTrue(any(call[0] == "cancel" for call in adapter.runner.calls))
            child_pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)


if __name__ == "__main__":
    unittest.main()
