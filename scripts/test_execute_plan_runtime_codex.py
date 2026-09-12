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
import unittest
from pathlib import Path
from unittest import mock

from execute_plan_runtime_codex import CodexAdapter, _cancel_process_tree, _verify_process_terminated, _subprocess_runner
import runtime_capabilities as capabilities


FIXTURE_DIR = Path(__file__).resolve().parent / "testdata/execute-plan/codex"

# Frame modules that never own an intercepted open: only the pathlib/io
# plumbing the observation wrapper wraps. The first frame outside this set is
# the open's caller (a test-module caller stays attributed to the test module
# and is therefore filtered out of the denial assertion).
_OBSERVATION_PLUMBING_MODULES = {"pathlib", "io", "os", "genericpath", "posixpath"}
_GUARDED_READ_MODULES = {"execute_plan_runtime_codex", "runtime_capabilities"}


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
                self.assertTrue(_pid_identity_matches(child.pid, subprocess.run(["ps", "-p", str(child.pid), "-o", "lstart="], capture_output=True, text=True).stdout.strip()))
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
            result = adapter.launch({"id": "task-4"}, "implement", 1, policy_token=self.policy())
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
                    launch = adapter.launch({"id": "task-4"}, "implement task", 1, policy_token=policy)
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
        # current contract. (Failing closed on a missing manifest is declined
        # as a behavior change that would break non-activated runs; recorded
        # in the Task 12 disposition.) Literals 30.0/300.0 on purpose: a
        # mutation of the default constants must fail these assertions.
        self.assertNotIn("EXECUTE_PLAN_PACKAGE_MANIFEST", os.environ)
        adapter = CodexAdapter("/repo", runner=RecordedRunner())
        self.assertEqual(adapter.launch_deadline, 30.0)
        self.assertEqual(adapter.wait_deadline, 300.0)

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


if __name__ == "__main__":
    unittest.main()
