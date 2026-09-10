#!/usr/bin/env python3
"""Hermetic tests for the durable execute-plan runtime driver."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path

import execute_plan_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT / "scripts/testdata/execute-plan/replays"


class FakeAdapter:
    def __init__(self, result=None):
        self.result = result
        self.launches = []

    def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
        self.launches.append((task["id"], generation, policy_token))
        if callable(self.result):
            return self.result(task, prompt, generation, deadline_seconds, policy_token)
        return self.result


class ExecutePlanRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        # Pin ambient execute-plan env inputs so an exported variable cannot
        # silently redirect the code under test to a foreign registry.
        self._saved_env = {key: os.environ.pop(key) for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST") if key in os.environ}
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True)
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            [
                {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
                {"id": "task-4", "number": 4, "status": "pending", "checkbox": False, "allowed_paths": ["task-4.txt"]},
            ],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.update(self._saved_env)
        for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST"):
            if key not in self._saved_env:
                os.environ.pop(key, None)

    def driver(self, **kwargs):
        seed_task3 = kwargs.pop("seed_task3", True)
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="fixture-plan",
            owner=kwargs.pop("owner", "test-owner"),
            repo_root=self.root,
            commit_lookup=kwargs.pop("commit_lookup", lambda _commit: True),
            **kwargs,
        )

    def seed_claim(self, task="task-3", owner="test-owner", generation=0, token="seed-task-3"):
        state = runtime.load_manifest(self.state_path)
        state["claims"][task] = {"token": token, "generation": generation, "owner": owner, "state": "launched", "task_id": task}
        runtime._safe_write_json(self.state_path, state)
        return token

    def commit_file(self, name="task-4.txt", content="committed change\n"):
        (self.root / name).write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", f"fixture commit {name}"], cwd=self.root, check=True)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def worker_checkpoint(self, task="task-3", generation=0, **overrides):
        result = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["worker-log:task-3"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task}:worker-1",
            "generation": generation,
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def done(self, task="task-3", generation=0, **overrides):
        result = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["done-log:task-3"],
            "action_scope": "done-handoff",
            "checkpoint_identity": f"{task}:done-1",
            "generation": generation,
            "task_id": task,
            "commit_identity": "aa11bb22cc33",
            "checkbox": True,
            "clean_state": True,
            "log_evidence": ["task-3-implement.log.md"],
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def test_success_checkpoint_selects_next_incomplete_step(self):
        driver = self.driver()
        self.seed_claim()
        self.assertEqual(driver.record_worker_checkpoint(self.worker_checkpoint())["state"], "done-pending")
        outcome = driver.record_done(self.done())
        self.assertEqual(outcome["status"], "success")
        self.assertEqual([a["task_id"] for a in outcome["actions"]], ["task-4"])
        self.assertEqual(driver.record_done(self.done())["actions"], [])

    def test_done_commit_boundary(self):
        driver = self.driver()
        self.seed_claim()
        worker = driver.record_worker_checkpoint(self.worker_checkpoint())
        self.assertEqual(worker["actions"], [])
        self.assertEqual(driver.record_done({"status": "blocked"})["status"], "blocked")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "pending")
        outcome = driver.record_done(self.done())
        self.assertEqual(len(outcome["actions"]), 1)
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "claimed")

    def test_resume_after_interruption_is_idempotent(self):
        self.seed_claim()
        first = self.driver().record_worker_checkpoint(self.worker_checkpoint())
        self.assertEqual(first["status"], "success")
        first_done = self.driver().record_done(self.done())
        self.assertEqual(len(first_done["actions"]), 1)
        second = self.driver().record_worker_checkpoint(self.worker_checkpoint())
        second_done = self.driver().record_done(self.done())
        self.assertEqual(second["duplicate"], True)
        self.assertEqual(second_done["actions"], [])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-3"]["commit_identity"], "aa11bb22cc33")

    def test_worker_permission_request_does_not_pause_authorized_work(self):
        self.seed_claim()
        result = self.driver().record_worker_checkpoint(
            self.worker_checkpoint(reason_code="permission-request", evidence=["asked to continue"])
        )
        self.assertEqual(result["status"], "contract-violation")
        self.assertNotEqual(result["status"], "user-question")
        self.assertIn(result["recovery_action"], {"rewrite-and-retry", "preserve-and-reconcile"})

    def test_real_approval_required_is_a_hard_gate(self):
        self.seed_claim()
        result = self.driver().record_worker_checkpoint(
            self.worker_checkpoint(
                status="approval-required",
                reason_code="approval-required",
                action_scope="external-write:publish",
                evidence=["approval-request:publish"],
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "approval-required")
        self.assertEqual(result["retry_policy"]["mode"], "none")
        self.assertIn("external-write:publish", result["evidence"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-3"]["status"], "complete")

    def test_missing_capability_uses_declared_fallback(self):
        profile = {
            "id": "fixture",
            "adapter_version": "1.0",
            "capabilities": {"final_response": "unsupported", "resume": "unsupported"},
            "fallback": "Return the durable receipt and resume from the parent.",
        }
        driver = self.driver(profile=profile)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["capabilities"]["final_response"]["state"], "unsupported")
        self.assertTrue(state["capabilities"]["final_response"]["fallback"])
        self.assertFalse(driver.parent_continuation_available())
        self.assertEqual(state["workflow_state"], "active")

    def test_atomic_claim_prevents_duplicate_launch(self):
        barrier = threading.Barrier(2)
        results = []

        def claim(owner):
            barrier.wait()
            results.append(self.driver(owner=owner).claim_next_task())

        threads = [threading.Thread(target=claim, args=(f"owner-{n}",)) for n in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(result["claimed"] for result in results), 1)
        self.assertEqual(sum(result["status"] == "blocked" for result in results), 1)
        self.assertEqual(results[0]["generation"] if results[0]["claimed"] else results[1]["generation"], 1)

    def test_malformed_adapter_result_fails_closed(self):
        driver = self.driver()
        for malformed in (
            {"status": "unknown"},
            {"status": "success", "evidence": []},
            {"status": "success", "evidence": ["x"], "action_scope": "../escape"},
            {"status": "success", "evidence": ["x"], "action_scope": "repository-task", "checkpoint_identity": "x", "generation": 0, "adapter_version": "9.0"},
        ):
            result = driver.validate_adapter_result(malformed)
            self.assertIn(result["status"], {"blocked", "error"})
        self.assertEqual(runtime.load_manifest(self.state_path)["workflow_state"], "active")

    def test_claimed_launch_persists_malformed_scalar_as_blocked(self):
        class ScalarAdapter(FakeAdapter):
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                self.launches.append((task["id"], generation, policy_token))
                return None

        adapter = ScalarAdapter()
        result = self.driver(adapter=adapter, seed_task3=False).launch_next_task()
        self.assertEqual(result["reason_code"], "malformed-result")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")

    def test_claimed_launch_persists_malformed_mapping_as_blocked(self):
        class MalformedAdapter(FakeAdapter):
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                return {"status": "success", "evidence": []}

        result = self.driver(adapter=MalformedAdapter(), seed_task3=False).launch_next_task()
        self.assertEqual(result["reason_code"], "malformed-result")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")

    def test_resume_non_mapping_is_persisted_as_blocked(self):
        class MalformedResumeAdapter:
            def resume(self, *args, **kwargs):
                return None

        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": True, "session_id": "session-task-4"})
        state["claims"]["task-4"] = {
            "token": "resume-token",
            "generation": 1,
            "owner": "test-owner",
            "state": "blocked",
            "task_id": "task-4",
            "policy_token": {"token": "policy", "repo_root": str(self.root), "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1},
        }
        runtime._safe_write_json(self.state_path, state)
        result = self.driver(adapter=MalformedResumeAdapter(), seed_task3=False).resume()
        self.assertEqual(result["reason_code"], "malformed-result")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")

    def test_resume_rejects_foreign_claim_before_adapter(self):
        class ExplodingAdapter:
            def resume(self, *args, **kwargs):
                raise AssertionError("foreign session invoked")

        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": True, "session_id": "session-task-4"})
        state["claims"]["task-4"] = {"token": "resume-token", "generation": 1, "owner": "other-owner", "state": "blocked", "task_id": "task-4"}
        runtime._safe_write_json(self.state_path, state)
        result = self.driver(adapter=ExplodingAdapter(), seed_task3=False).resume()
        self.assertEqual(result["reason_code"], "owner-mismatch")

    def test_deadline_returns_bounded_block(self):
        adapter = FakeAdapter(
            lambda *_: {"status": "blocked", "reason_code": "timeout", "evidence": ["launch deadline"], "action_scope": "repository-task", "checkpoint_identity": "task-4", "generation": 1}
        )
        result = self.driver(adapter=adapter, seed_task3=False).launch_next_task(deadline_seconds=0.01)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "timeout")
        self.assertTrue(Path(str(self.state_path) + ".lock").exists())

    def test_abort_is_terminal_and_not_relaunchable(self):
        driver = self.driver()
        claim = driver.claim_next_task()
        result = driver.abort(claim["task_id"], claim["token"])
        self.assertEqual(result["status"], "aborted")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["workflow_state"], "aborted")
        self.assertEqual(state["tasks"][claim["task_id"]]["status"], "aborted")
        self.assertEqual(driver.continue_parent()["status"], "aborted")

    def test_authorization_negative_matrix(self):
        driver = self.driver()
        for scope in ("push", "deploy", "merge", "external-write", "network", "policy-file", "protected-file", "repository-write:../../secret", "repository-write:/tmp/secret"):
            result = driver.authorize_action(scope)
            self.assertEqual(result["status"], "blocked", scope)
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "pending")

    def test_post_launch_policy_bypass_is_blocked(self):
        driver = self.driver()
        result = driver.validate_adapter_result({
            "status": "success",
            "reason_code": "completed",
            "evidence": ["worker"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker",
            "generation": 1,
            "actions": [{"operation": "network", "target": "https://example.invalid"}],
        })
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        self.assertIn("network", result["action_scope"])

    def test_typed_action_envelope_rejects_gated_and_unlisted_paths(self):
        driver = self.driver()
        allowed = runtime.ActionEnvelope(
            repo_root=str(self.root),
            allowed_paths=("agents/skills/execute-plan/SKILL.md",),
            operation_kind="repository-write",
            network=False,
            evidence=("task-4-files",),
        )
        token_result = driver.authorize_envelope(allowed, generation=1)
        self.assertEqual(token_result["status"], "success")
        self.assertTrue(token_result["policy_token"]["token"])
        self.assertEqual(token_result["policy_token"]["allowed_paths"], ["agents/skills/execute-plan/SKILL.md"])

        for envelope in (
            runtime.ActionEnvelope(str(self.root), ("../secret",), "repository-write", False, ("evidence",)),
            runtime.ActionEnvelope(str(self.root), ("/tmp/secret",), "repository-write", False, ("evidence",)),
            runtime.ActionEnvelope(str(self.root), ("file.txt",), "repository-write", True, ("evidence",)),
            runtime.ActionEnvelope(str(self.root), ("file.txt",), "push", False, ("evidence",)),
        ):
            result = driver.authorize_envelope(envelope, generation=1)
            self.assertEqual(result["status"], "blocked")

    def test_adapter_receives_only_driver_policy_token(self):
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, token: self.worker_checkpoint(
                task=task["id"], generation=generation, evidence=[f"token={token['token']}"]
            )
        )
        result = self.driver(adapter=adapter).launch_next_task()
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(adapter.launches), 1)
        self.assertEqual(adapter.launches[0][2]["operation_kind"], "repository-task")
        self.assertEqual(adapter.launches[0][2]["network"], False)

    def test_two_drivers_claim_and_launch_once(self):
        adapter = FakeAdapter(lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(task=task["id"], generation=generation))
        results = []
        barrier = threading.Barrier(2)

        def run(owner):
            barrier.wait()
            results.append(self.driver(owner=owner, adapter=adapter, seed_task3=False).launch_next_task())

        threads = [threading.Thread(target=run, args=(f"launch-owner-{number}",)) for number in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(result["status"] == "success" for result in results), 1)
        self.assertEqual(len(adapter.launches), 1)
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

    def test_unclaimed_checkpoint_is_rejected_without_mutation(self):
        driver = self.driver()
        before = runtime.load_manifest(self.state_path)
        result = driver.record_worker_checkpoint(
            self.worker_checkpoint(task="task-4", generation=0)
        )
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(result["reason_code"], "owner-mismatch")
        self.assertEqual(after["tasks"], before["tasks"])
        self.assertEqual(after["history"], before["history"])

    def test_done_without_checkpoint_identity_does_not_mutate(self):
        driver = self.driver()
        self.seed_claim()
        driver.record_worker_checkpoint(self.worker_checkpoint())
        before = runtime.load_manifest(self.state_path)
        result = driver.record_done({"status": "success", "task_id": "task-3", "action_scope": "done-handoff", "checkbox": True, "clean_state": True, "commit_identity": "aa11bb22cc33", "log_evidence": ["done.log"], "claim_token": "seed-task-3", "generation": 0})
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertEqual(after["tasks"], before["tasks"])
        self.assertEqual(after["history"], before["history"])

    def test_contract_violation_gets_one_driver_owned_retry(self):
        token = self.seed_claim(task="task-4", token="seed-task-4")
        attempts = []

        def result(task, prompt, generation, _deadline, _token):
            attempts.append(prompt)
            if len(attempts) == 1:
                return self.worker_checkpoint(task=task["id"], generation=generation, reason_code="permission-request")
            return self.worker_checkpoint(task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:retry")

        driver = self.driver(adapter=FakeAdapter(result))
        result = driver._launch_claimed_task({"task_id": "task-4", "token": token, "generation": 0}, "continue", None)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(attempts), 2)
        self.assertIn("Rewrite", attempts[1])

    def test_retry_after_contract_violation_success_lands_done_pending(self):
        """Regression: a failed attempt must not poison the checkpoint identity.

        The retry returns the same stable checkpoint identity the first
        attempt used (exactly what the codex adapter produces); the success
        must still land done-pending instead of being swallowed as a
        duplicate of the failed attempt.
        """

        token = self.seed_claim(task="task-4", token="seed-task-4")
        attempts = []

        def result(task, prompt, generation, _deadline, _token):
            attempts.append(prompt)
            return self.worker_checkpoint(
                task=task["id"],
                generation=generation,
                checkpoint_identity=f"{task['id']}:worker",
                reason_code="permission-request" if len(attempts) == 1 else "completed",
            )

        driver = self.driver(adapter=FakeAdapter(result))
        outcome = driver._launch_claimed_task({"task_id": "task-4", "token": token, "generation": 0}, "continue", None)
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(outcome["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")
        self.assertIn("task-4:worker#attempt-initial", state["checkpoints"])
        self.assertEqual(state["checkpoints"]["task-4:worker"]["result"]["status"], "success")
        # The done boundary now verifies the real committed artifact, so hand
        # it an in-scope commit that descends from the launch baseline.
        commit = self.commit_file("task-4.txt")
        done = driver.record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(done["status"], "success")

    def test_out_of_scope_worktree_change_cannot_become_success_checkpoint(self):
        baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        self.seed_claim(task="task-4", token="scope-token")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["policy_token"] = {"token": "policy", "repo_root": str(self.root), "allowed_paths": ["allowed.txt"], "operation_kind": "repository-task", "network": False, "generation": 0}
        state["claims"]["task-4"]["baseline_revision"] = baseline
        runtime._safe_write_json(self.state_path, state)
        (self.root / "outside.txt").write_text("worker escaped scope\n", encoding="utf-8")
        subprocess.run(["git", "add", "-N", "outside.txt"], cwd=self.root, check=True)
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "blocked")

    def _scope_claim(self, allowed):
        baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        self.seed_claim(task="task-4", token="scope-token")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["policy_token"] = {"token": "policy", "repo_root": str(self.root), "allowed_paths": list(allowed), "operation_kind": "repository-task", "network": False, "generation": 0}
        state["claims"]["task-4"]["baseline_revision"] = baseline
        runtime._safe_write_json(self.state_path, state)
        return baseline

    def test_untracked_out_of_scope_file_is_rejected_at_checkpoint(self):
        # No `git add -N`: the file is fully untracked, invisible to
        # `git diff --name-only` but visible to the untracked-files witness.
        self._scope_claim(allowed=("allowed.txt",))
        (self.root / "untracked-outside.txt").write_text("worker escaped scope\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")

    def test_in_scope_untracked_file_does_not_trip_the_witness(self):
        self._scope_claim(allowed=("in-scope.txt",))
        (self.root / "in-scope.txt").write_text("authorized new file\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["state"], "done-pending")

    def test_allowed_path_replaced_by_out_of_repo_symlink_violates_scope(self):
        self._scope_claim(allowed=("link.txt",))
        os.symlink("/tmp", self.root / "link.txt")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")

    def test_recorded_baseline_with_empty_scope_fails_closed(self):
        self._scope_claim(allowed=())
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["reason_code"], "worktree-witness-unavailable")

    def test_empty_allowed_paths_envelope_is_rejected(self):
        envelope = {"repo_root": str(self.root), "allowed_paths": [], "operation_kind": "repository-task", "network": False, "evidence": ["task=task-4"]}
        with self.assertRaises(ValueError):
            runtime.validate_action_envelope(envelope, self.root)
        blocked = self.driver().authorize_envelope(envelope, 0)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["reason_code"], "approval-required")

    def test_launch_blocks_when_baseline_revision_is_unavailable(self):
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(
                task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker"
            )
        )
        driver = self.driver(adapter=adapter, seed_task3=False)
        with mock.patch.object(driver, "_git_head_revision", return_value=""):
            result = driver.launch_next_task()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "worktree-witness-unavailable")
        self.assertFalse(result["resume_allowed"])
        self.assertEqual(adapter.launches, [])
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"]["task-4"].get("baseline_revision", ""), "")

    def test_hostile_retry_policy_cannot_exceed_profile_budget(self):
        self.seed_claim(task="task-4", token="seed-task-4")
        launches = []

        def hostile(task, _prompt, _generation, _deadline, _token):
            launches.append(task["id"])
            return {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["boom"],
                "action_scope": "repository-task",
                "checkpoint_identity": f"{task['id']}:worker",
                "generation": 0,
                "retry_policy": {"mode": "bounded", "max_attempts": 5000, "attempts_remaining": 5000},
            }

        driver = self.driver(adapter=FakeAdapter(hostile))
        outcome = driver.record_worker_checkpoint(
            {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["boom"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-4:worker",
                "generation": 0,
                "claim_token": "seed-task-4",
                "retry_policy": {"mode": "bounded", "max_attempts": 5000, "attempts_remaining": 5000},
            }
        )
        self.assertEqual(outcome["status"], "error")
        self.assertLessEqual(len(launches), 2)
        self.assertLessEqual(outcome["retry_policy"]["attempts_remaining"], 2)
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "blocked")

    def test_done_boundary_rejects_non_descendant_commit(self):
        self._scope_claim(allowed=("task-4.txt",))
        self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        orphan = subprocess.run(["git", "commit-tree", "-m", "orphan", tree], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        done = self.driver().record_done(self.done(task="task-4", generation=0, commit_identity=orphan))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "commit-pending")
        self.assertFalse(done["resume_allowed"])

    def test_done_boundary_rejects_out_of_scope_commit(self):
        self._scope_claim(allowed=("task-4.txt",))
        self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        commit = self.commit_file("evil.txt")
        done = self.driver().record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "commit-pending")
        self.assertFalse(done["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

    def test_persisted_task_status_is_launched_between_launch_and_checkpoint(self):
        observed = {}

        def spy_launch(task, prompt, generation, deadline_seconds=None, policy_token=None):
            observed["status"] = runtime.load_manifest(self.state_path)["tasks"][task["id"]]["status"]
            return self.worker_checkpoint(task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker")

        adapter = FakeAdapter(spy_launch)
        result = self.driver(adapter=adapter, seed_task3=False).launch_next_task()
        self.assertEqual(result["state"], "done-pending")
        self.assertEqual(observed["status"], "launched")

    def test_abort_during_launch_window_is_not_resurrected(self):
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(
                task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker"
            )
        )
        driver = self.driver(adapter=adapter, seed_task3=False)
        claim = driver.claim_next_task()
        self.assertEqual(claim["task_id"], "task-4")
        aborter = self.driver(seed_task3=False)
        original_authorize = driver.authorize_envelope

        def authorize_then_abort(envelope, generation):
            authorization = original_authorize(envelope, generation)
            # A concurrent abort lands inside the launch window, between the
            # claim read and the manifest write.
            aborted = aborter.abort("task-4", claim["token"])
            self.assertEqual(aborted["status"], "aborted")
            return authorization

        with mock.patch.object(driver, "authorize_envelope", side_effect=authorize_then_abort):
            outcome = driver._launch_claimed_task(claim, "continue", None)
        self.assertEqual(outcome["reason_code"], "owner-mismatch")
        self.assertEqual(adapter.launches, [])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["workflow_state"], "aborted")
        self.assertEqual(state["claims"]["task-4"]["state"], "aborted")

    def test_cli_two_processes_share_derived_owner_without_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "runtime_state.json"
            runtime.create_manifest(state_path, "owner-plan", [{"id": "task-1", "number": 1, "status": "pending"}])

            def cli(operation, payload=None):
                command = [sys.executable, str(ROOT / "scripts/execute_plan_runtime.py"), "--manifest", str(state_path), "--operation", operation]
                if payload is not None:
                    command.extend(["--input", json.dumps(payload)])
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
                return json.loads(completed.stdout)

            claim = cli("claim")
            self.assertTrue(claim["claimed"])
            self.assertTrue(runtime.load_manifest(state_path).get("owner"))
            checkpoint = cli("checkpoint", {"status": "success", "reason_code": "completed", "evidence": ["cli"], "action_scope": "repository-task", "checkpoint_identity": "task-1:worker", "generation": claim["generation"], "claim_token": claim["token"]})
            self.assertEqual(checkpoint["state"], "done-pending")

    def test_cli_approval_receipt_enables_and_invalid_receipt_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "runtime_state.json"
            runtime.create_manifest(state_path, "receipt-plan", [{"id": "task-1", "number": 1, "status": "pending"}])
            receipt = root / "approval.json"
            receipt.write_text(json.dumps({"runtime": "codex", "approval": "verified"}), encoding="utf-8")
            base = [sys.executable, str(ROOT / "scripts/execute_plan_runtime.py"), "--manifest", str(state_path), "--operation", "claim"]
            ok = subprocess.run(base + ["--runtime", "codex", "--approval-receipt", str(receipt)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue(json.loads(ok.stdout)["claimed"])
            bad_receipt = root / "bad.json"
            bad_receipt.write_text(json.dumps({"runtime": "codex", "approval": "assumed"}), encoding="utf-8")
            blocked = subprocess.run(base + ["--runtime", "codex", "--approval-receipt", str(bad_receipt)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("approval receipt", blocked.stderr)
            self.assertNotIn("selftest failed", blocked.stderr)

    def test_missing_reason_code_is_blocked_as_malformed(self):
        driver = self.driver()
        result = driver.validate_adapter_result({
            "status": "success",
            "evidence": ["worker"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker",
            "generation": 1,
        })
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")

    def test_committed_runtime_state_fixture_loads_through_real_validation(self):
        fixture = ROOT / "scripts/testdata/execute-plan/runtime_state.json"
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "runtime_state.json"
            copy.write_bytes(fixture.read_bytes())
            driver = runtime.RuntimeDriver(copy, plan_slug="fixture-plan", repo_root=directory)
            validated = driver.validate_manifest()
            self.assertEqual(validated["plan_slug"], "fixture-plan")
            self.assertIn("task-4", validated["tasks"])

    def test_cli_checkpoint_operation_uses_file_backed_driver(self):
        payload = self.worker_checkpoint(task="task-4", generation=1)
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest",
                str(self.state_path),
                "--operation",
                "checkpoint",
                "--input",
                json.dumps(payload),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "blocked")

    def test_driver_entrypoint_owns_transitions_across_reload(self):
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(
                task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker"
            )
        )
        first = self.driver(adapter=adapter, seed_task3=False).continue_parent()
        self.assertEqual(first["status"], "success")
        self.assertEqual(first["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")

        reloaded = self.driver(adapter=adapter, seed_task3=False)
        commit = self.commit_file("task-4.txt")
        committed = reloaded.record_done(self.done(task="task-4", generation=1, commit_identity=commit))
        self.assertEqual(committed["status"], "success")
        terminal = self.driver(adapter=adapter).continue_parent()
        self.assertEqual(terminal["reason_code"], "done-pending")
        terminal = self.driver(adapter=adapter).mark_terminal("docs/plans/completed/fixture-plan.md", "abcdef1", ["tests"])
        self.assertEqual(terminal["status"], "success")
        self.assertEqual(runtime.load_manifest(self.state_path)["workflow_state"], "complete")

    def test_direct_and_indirect_shell_or_path_traversal_attempts_fail_closed(self):
        driver = self.driver()
        attempts = (
            {"operation": "shell", "target": "echo unsafe"},
            {"operation": "repository-write", "target": "../secret"},
            {"operation": "repository-write", "target": "$(touch escaped)"},
            {"operation": "repository-write", "target": "file; network"},
        )
        for action in attempts:
            result = driver.validate_adapter_result({
                "status": "success",
                "reason_code": "completed",
                "evidence": ["worker"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-4:worker",
                "generation": 1,
                "actions": [action],
            })
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "contract-violation")

    def test_shared_skill_bodies_remain_runtime_neutral(self):
        root = Path(__file__).resolve().parents[1]
        shared_files = (
            root / "agents/skills/execute-plan/SKILL.md",
            root / "agents/skills/execute-plan/subagent-prompts.md",
            root / "agents/skills/execute-plan/agent-logs.md",
            root / "agents/skills/plans/SKILL.md",
        )
        forbidden = ("codex", "cursor", "claude", "zcode", "opencode", "copilot", "gemini", "antigravity", "UserPromptSubmit", "PreToolUse", "PostToolUse", "JSONL", "MCP", "--json")
        for path in shared_files:
            text = path.read_text(encoding="utf-8").lower()
            for term in forbidden:
                self.assertNotIn(term.lower(), text, path.name)

    def test_commit_before_checkpoint_reconciles(self):
        driver = self.driver()
        token = self.seed_claim(task="task-3", generation=0, token="task-3-recovery")
        pending = driver.mark_commit_pending("task-3", "aa11bb22cc33", ["done-log:task-3"], claim_token=token, generation=0)
        self.assertEqual(pending["status"], "success")
        result = driver.reconcile_commit_before_checkpoint(
            "task-3", "aa11bb22cc33", commit_lookup=lambda commit: commit == "aa11bb22cc33", claim_token=token, generation=0
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["recovery_action"], "continue-parent")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-3"]["status"], "checkpointed")
        self.assertEqual(driver.reconcile_commit_before_checkpoint("task-3", "aa11bb22cc33", lambda _: True, claim_token=token, generation=0)["actions"], [])

    def test_commit_pending_reload_reconciles_without_relaunch(self):
        driver = self.driver()
        claim = driver.claim_next_task()
        pending = driver.mark_commit_pending("task-4", "bb22cc33dd44", ["done-log:task-4"])
        self.assertEqual(pending["status"], "success")
        reloaded = self.driver()
        result = reloaded.reconcile_startup(commit_lookup=lambda commit: commit == "bb22cc33dd44")
        self.assertEqual(result["status"], "success")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "checkpointed")
        self.assertNotEqual(claim["generation"], 0)

    def test_startup_reconciliation_uses_real_git_clean_state_before_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=root, check=True)
            marker = root / "tracked.txt"
            marker.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            state_path = root.parent / "runtime_state.json"
            runtime.create_manifest(state_path, "real-reconcile", [{"id": "task-1", "number": 1, "status": "pending"}])
            driver = runtime.RuntimeDriver(state_path, plan_slug="real-reconcile", owner="real-owner", repo_root=root)
            claim = driver.claim_next_task()
            driver.mark_commit_pending("task-1", commit, ["done-log:task-1"], claim_token=claim["token"], generation=claim["generation"])
            marker.write_text("dirty\n", encoding="utf-8")
            dirty = driver.reconcile_startup()
            self.assertEqual(dirty["reason_code"], "dirty-worktree")
            marker.write_text("base\n", encoding="utf-8")
            recovered = driver.reconcile_startup()
            self.assertEqual(recovered["status"], "success")
            self.assertEqual(runtime.load_manifest(state_path)["tasks"]["task-1"]["status"], "checkpointed")

    def test_startup_reconciliation_blocks_when_git_witness_fails(self):
        driver = self.driver()
        self.seed_claim(task="task-3")
        with mock.patch.object(driver, "_git_worktree_dirty", side_effect=RuntimeError("status failed")):
            result = driver.reconcile_startup()
        self.assertEqual(result["reason_code"], "worktree-witness-unavailable")

    def test_cli_drives_claim_checkpoint_done_and_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=root, check=True)
            (root / "tracked.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
            state_path = root / "runtime_state.json"
            runtime.create_manifest(state_path, "cli-plan", [{"id": "task-1", "number": 1, "status": "pending"}])

            def cli(operation, payload=None):
                command = [sys.executable, str(ROOT / "scripts/execute_plan_runtime.py"), "--manifest", str(state_path), "--repo-root", str(root), "--owner", "cli-owner", "--operation", operation]
                if payload is not None:
                    command.extend(["--input", json.dumps(payload)])
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
                return json.loads(completed.stdout)

            claim = cli("claim")
            checkpoint = cli("checkpoint", {"status": "success", "reason_code": "completed", "evidence": ["cli"], "action_scope": "repository-task", "checkpoint_identity": "task-1:worker", "generation": claim["generation"], "claim_token": claim["token"]})
            self.assertEqual(checkpoint["state"], "done-pending")
            done = cli("done", {"status": "success", "action_scope": "done-handoff", "checkpoint_identity": "task-1:done", "generation": claim["generation"], "claim_token": claim["token"], "task_id": "task-1", "commit_identity": commit, "checkbox": True, "clean_state": True, "log_evidence": ["task-1.log"]})
            self.assertEqual(done["status"], "success")
            self.assertEqual(cli("terminal", {"archived_plan_path": "docs/plans/completed/cli-plan.md", "last_commit_sha": commit, "phase5_checklist": ["tests"]})["status"], "success")

    def test_evidence_and_fixtures_are_hermetic(self):
        result = runtime.bounded_evidence(["token=secret", {"password": "nested-secret"}, "x" * 2000])
        self.assertLessEqual(sum(map(len, result)), runtime.MAX_EVIDENCE_BYTES)
        self.assertNotIn("secret", " ".join(result))
        self.assertNotIn("nested-secret", " ".join(result))
        self.assertEqual(os.stat(self.state_path).st_mode & 0o777, 0o600)

    def test_active_manifest_suppresses_terminal_result(self):
        driver = self.driver(profile={"capabilities": {"final_response": "unsupported"}, "fallback": "receipt"})
        self.assertIsNone(driver.terminal_result())
        self.assertEqual(driver.mark_terminal()["reason_code"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].update({"status": "complete", "checkbox": True})
        runtime._safe_write_json(self.state_path, state)
        driver.mark_terminal("docs/plans/completed/fixture-plan.md", "abcdef1", ["tests"])
        terminal = driver.terminal_result()
        self.assertEqual(terminal["status"], "success")
        self.assertEqual(terminal["workflow_state"], "complete")
        self.assertIn("phase5_checklist", terminal)
        self.assertIn("archived_plan_path", terminal)

    def _replay_driver(self, root: Path, tasks, adapter=None, owner="replay-owner"):
        state_path = root / "runtime_state.json"
        runtime.create_manifest(state_path, "crm-691-replay", tasks)
        return runtime.RuntimeDriver(
            state_path,
            plan_slug="crm-691-replay",
            owner=owner,
            repo_root=root,
            adapter=adapter,
            commit_lookup=lambda _commit: True,
        ), state_path

    @staticmethod
    def _replay_success(task_id: str, generation: int, checkpoint="worker"):
        return {
            "status": "success",
            "reason_code": "completed",
            "evidence": [f"fixture:{task_id}:{checkpoint}"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task_id}:{checkpoint}",
            "generation": generation,
        }

    @staticmethod
    def _fence(state_path: Path, result: dict, task_id: str = "task-1"):
        claim = runtime.load_manifest(state_path)["claims"].get(task_id)
        if claim:
            result["claim_token"] = claim["token"]
            result["generation"] = claim["generation"]
        return result

    @staticmethod
    def _replay_done(task_id: str, commit: str):
        return {
            "status": "success",
            "reason_code": "completed",
            "evidence": [f"fixture:done:{task_id}"],
            "action_scope": "done-handoff",
            "checkpoint_identity": f"{task_id}:done",
            "generation": 1,
            "task_id": task_id,
            "commit_identity": commit,
            "checkbox": True,
            "clean_state": True,
            "log_evidence": [f"{task_id}.log"],
        }

    def test_crm691_incident_replays(self):
        fixtures = sorted(REPLAY_DIR.glob("*.json"))
        self.assertEqual(len(fixtures), 9)
        expected_names = {
            "conversational-permission-loop",
            "parent-worker-checkpoint",
            "dead-session-fenced-done-lock",
            "launcher-capacity-failure",
            "docker-sandbox-denial",
            "missing-runtime-dependency",
            "malformed-approval-result",
            "concurrent-duplicate-launch",
            "resume-after-interruption",
        }
        self.assertEqual({json.loads(path.read_text())["name"] for path in fixtures}, expected_names)

        for fixture_path in fixtures:
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            with self.subTest(fixture=fixture["name"]):
                expected = fixture["expected"]
                for key in (
                    "status",
                    "reason_code",
                    "retry_count",
                    "claim_state",
                    "manifest_state",
                    "action_scope",
                    "mutation_expectation",
                ):
                    self.assertIn(key, expected)
                self.assertTrue(fixture["trace"])
                with tempfile.TemporaryDirectory() as parent_directory:
                    # Dedicated parent so the containment witness can detect
                    # any file the replay writes outside the fixture root.
                    parent = Path(parent_directory)
                    root = Path(tempfile.mkdtemp(dir=parent))
                    self.addCleanup(shutil.rmtree, root, ignore_errors=True)
                    # The replay root is a real git repo: launch paths now fail
                    # closed without a resolvable baseline revision.
                    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
                    subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=root, check=True)
                    (root / "seed.txt").write_text("base\n", encoding="utf-8")
                    subprocess.run(["git", "add", "seed.txt"], cwd=root, check=True)
                    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
                    entries_before = set(parent.iterdir())
                    adapter_result = self._replay_success("task-1", 1)
                    adapter = FakeAdapter(adapter_result)
                    driver, state_path = self._replay_driver(
                        root,
                        fixture.get(
                            "tasks",
                            [
                                {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["task-1.txt"]},
                                {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["task-2.txt"]},
                            ],
                        ),
                        adapter=adapter,
                    )
                    final, retry_count = self._run_replay(fixture, driver, state_path, root)
                    self.assertNotEqual(final.get("status"), "user-question")
                    self.assertEqual(final["status"], expected["status"])
                    self.assertEqual(final["reason_code"], expected["reason_code"])
                    self.assertEqual(retry_count, expected["retry_count"])
                    self.assertEqual(final["action_scope"], expected["action_scope"])
                    state = runtime.load_manifest(state_path)
                    self.assertEqual(state["workflow_state"], expected["manifest_state"])
                    claim_states = {claim.get("state") for claim in state["claims"].values()}
                    self.assertIn(expected["claim_state"], claim_states or {"none"})
                    mutated = any(event.get("event") == "done-commit" for event in state["history"])
                    self.assertEqual(mutated, expected["mutation_expectation"] == "repository-local")
                    entries_after = set(parent.iterdir())
                    self.assertLessEqual(entries_after - entries_before, {root})
                    self.assertTrue(root.is_dir())

    def _run_replay(self, fixture, driver, state_path: Path, root: Path):
        events = fixture.get("events")
        if not isinstance(events, list) or not events or not all(isinstance(event, dict) and event.get("type") for event in events):
            raise AssertionError("replay fixture must provide typed events")
        name = fixture.get("name")
        retries = 0
        if name != "resume-after-interruption":
            if len(events) != 1 or events[0]["type"] != name:
                raise AssertionError(f"replay event stream does not match fixture handler: {name}")
            event = events[0]
            if event.get("task_id", "task-1") != "task-1":
                raise AssertionError("replay event task identity is not consumed by the fixture handler")
        if name == "conversational-permission-loop":
            bad = self._replay_success("task-1", 0)
            bad["reason_code"] = "permission-request"
            claim = driver.claim_next_task()
            bad["generation"] = claim["generation"]
            self._fence(state_path, bad)
            driver.record_worker_checkpoint(bad)
            retries = 1
            driver = runtime.RuntimeDriver(
                state_path,
                plan_slug="crm-691-replay",
                owner="replay-owner",
                repo_root=root,
                adapter=FakeAdapter(self._replay_success("task-1", 1)),
                commit_lookup=lambda _commit: True,
            )
            outcome = driver.resume()
            if outcome["status"] == "success":
                driver.record_done(self._fence(state_path, self._replay_done("task-1", "commit-1")))
                driver.mark_terminal()
            return driver.terminal_result() or outcome, retries
        if name == "parent-worker-checkpoint":
            claim = driver.claim_next_task()
            driver.record_worker_checkpoint(self._fence(state_path, self._replay_success("task-1", claim["generation"])))
            reloaded = runtime.RuntimeDriver(state_path, plan_slug="crm-691-replay", owner="replay-owner", repo_root=root, commit_lookup=lambda _commit: True)
            outcome = reloaded.record_done(self._fence(state_path, self._replay_done("task-1", "commit-1")))
            return outcome, retries
        if name == "dead-session-fenced-done-lock":
            claim = driver.claim_next_task()
            fenced = runtime.RuntimeDriver(state_path, plan_slug="crm-691-replay", owner="replacement-owner", repo_root=root, commit_lookup=lambda _commit: True)
            result = self._replay_success("task-1", claim["generation"])
            result["claim_token"] = claim["token"]
            return fenced.record_worker_checkpoint(result), retries
        if name == "launcher-capacity-failure":
            claim = driver.claim_next_task()
            return driver.record_worker_checkpoint(self._fence(state_path, {
                "status": "blocked",
                "reason_code": "runtime-policy-unavailable",
                "evidence": ["launcher capacity exhausted"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-1:launcher",
                "generation": 0,
            })), retries
        if name == "docker-sandbox-denial":
            claim = driver.claim_next_task()
            return driver.record_worker_checkpoint(self._fence(state_path, {
                "status": "approval-required",
                "reason_code": "approval-required",
                "evidence": ["sandbox denied"],
                "action_scope": "docker:sandbox",
                "checkpoint_identity": "task-1:sandbox",
                "generation": 0,
            })), retries
        if name == "missing-runtime-dependency":
            unavailable = runtime.RuntimeDriver(
                state_path,
                plan_slug="crm-691-replay",
                owner="replay-owner",
                repo_root=root,
                commit_lookup=lambda _commit: True,
            )
            return unavailable.launch_next_task(), retries
        if name == "malformed-approval-result":
            claim = driver.claim_next_task()
            return driver.record_worker_checkpoint(self._fence(state_path, {
                "status": "approval-required",
                "evidence": ["approval omitted evidence"],
                "reason_code": "approval-required",
                "action_scope": "external-write",
                "checkpoint_identity": "task-1:approval",
                "generation": 0,
            })), retries
        if name == "concurrent-duplicate-launch":
            first = driver.claim_next_task()
            second = runtime.RuntimeDriver(state_path, plan_slug="crm-691-replay", owner="other-owner", repo_root=root, commit_lookup=lambda _commit: True)
            return second.claim_next_task(), retries
        if name == "resume-after-interruption":
            claim = None
            reloaded = None
            outcome = None
            for event in events:
                event_type = event["type"]
                if event.get("task_id", "task-1") != "task-1":
                    raise AssertionError("replay event task identity is not consumed by the fixture handler")
                if event_type == "claim":
                    claim = driver.claim_next_task()
                elif event_type == "checkpoint":
                    if claim is None:
                        raise AssertionError("replay checkpoint arrived before claim")
                    driver.record_worker_checkpoint(self._fence(state_path, self._replay_success("task-1", claim["generation"])))
                elif event_type == "duplicate-checkpoint":
                    if claim is None:
                        raise AssertionError("replay duplicate arrived before claim")
                    reloaded = runtime.RuntimeDriver(state_path, plan_slug="crm-691-replay", owner="replay-owner", repo_root=root, commit_lookup=lambda _commit: True)
                    reloaded.record_worker_checkpoint(self._fence(state_path, self._replay_success("task-1", claim["generation"])))
                elif event_type == "done":
                    if reloaded is None:
                        raise AssertionError("replay done arrived before reload")
                    outcome = reloaded.record_done(self._fence(state_path, self._replay_done("task-1", "commit-1")))
                else:
                    raise AssertionError(f"unknown resume replay event: {event_type}")
            if outcome is None:
                raise AssertionError("replay did not produce a done outcome")
            return outcome, retries
        raise AssertionError(f"unknown replay fixture: {name}")

    def test_runtime_replay_is_hermetic_to_fixture_root(self):
        original_cwd = Path.cwd()
        original_env = dict(os.environ)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                os.chdir(root)
                os.environ.clear()
                os.environ.update({"HOME": str(root / "home"), "PATH": "", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"})
                driver, state_path = self._replay_driver(root, [{"id": "task-1", "number": 1, "status": "pending"}])
                self.assertEqual(driver.authorize_action("network")["status"], "blocked")
                self.assertEqual(driver.authorize_action("repository-write", "inside.txt")["status"], "success")
                self.assertEqual(driver.authorize_action("repository-write", "../outside.txt")["status"], "blocked")
                process = subprocess.run(
                    [sys.executable, "-c", "import os; print(os.getcwd()); print(os.environ.get('HOME'))"],
                    cwd=root,
                    env=dict(os.environ),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(
                    [str(Path(line).resolve()) for line in process.stdout.splitlines()],
                    [str(root.resolve()), str((root / "home").resolve())],
                )
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network disabled")):
                    with self.assertRaises(AssertionError):
                        socket.socket()
                self.assertTrue(state_path.is_relative_to(root))
                self.assertFalse((root.parent / "outside.txt").exists())
            finally:
                os.environ.clear()
                os.environ.update(original_env)
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
