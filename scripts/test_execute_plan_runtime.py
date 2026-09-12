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
import runtime_capabilities as capabilities


def write_approval_receipt(receipt: Path, config: Path, payload: dict) -> None:
    """Write an approval receipt under the mandatory hardened reading.

    Mode 0600 (owner-only) plus the mandatory ``config_path`` and
    ``policy_fingerprint`` cross-check fields; the config path points at an
    injected config root, never the ambient environment.
    """

    data = {
        "runtime": "codex",
        "approval": "verified",
        "config_path": str(config),
        "policy_fingerprint": capabilities.approval_policy_fingerprint(config),
    }
    data.update(payload)
    receipt.write_text(json.dumps(data), encoding="utf-8")
    receipt.chmod(0o600)


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
        # Reset durable checkpoint records so each subTest arm proves its own
        # attempt-ordinal witness instead of passing on a prior arm's residue.
        state["checkpoints"] = {}
        # The seeded claim carries a launch-record snapshot (empty baseline:
        # the git witnesses stay inert for these fixtures) so it is a launched
        # claim with a record, not a post-launch claim with a missing record.
        state["claims"][task] = {
            "token": token,
            "generation": generation,
            "owner": owner,
            "state": "launched",
            "task_id": task,
            "launched_at": 111.0,
            "launch_record": {"baseline_revision": "", "generation": generation, "launched_at": 111.0},
        }
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
            "baseline_revision": subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip(),
            "launch_record": {"baseline_revision": subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip(), "generation": 1, "launched_at": 111.0},
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
        self.assertIn("task-4:worker#attempt-1", state["checkpoints"])
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
        state["claims"]["task-4"]["launch_record"] = {"baseline_revision": baseline, "generation": 0, "launched_at": 111.0}
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
        state["claims"]["task-4"]["launch_record"] = {"baseline_revision": baseline, "generation": 0, "launched_at": 111.0}
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

    def test_path_escape_check_fails_closed_on_oserror(self):
        self._scope_claim(allowed=("in-scope.txt",))
        (self.root / "in-scope.txt").write_text("authorized\n", encoding="utf-8")
        driver = self.driver()
        original_resolve = Path.resolve

        def failing_resolve(path, strict=False):
            if path.name == "in-scope.txt":
                raise OSError("injected resolve failure")
            return original_resolve(path, strict=strict)

        with mock.patch.object(Path, "resolve", failing_resolve):
            # An injected OSError must count as escaping, never as contained.
            self.assertTrue(driver._path_escapes_repo("in-scope.txt"))
            result = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertNotEqual(result.get("status"), "success")
        self.assertEqual(result["status"], "blocked")
        self.assertIn(result["reason_code"], {"contract-violation", "worktree-witness-unavailable"})
        self.assertFalse(result["resume_allowed"])

    def test_porcelain_witness_parses_escaped_paths(self):
        # A double quote in a file name is C-quoted by git even with
        # core.quotePath=false in the non -z porcelain format; the witness
        # must compare the literal path, not the quoted rendering.
        self._scope_claim(allowed=("safe.txt",))
        (self.root / 'esc"aped.txt').write_text("out of scope\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        evidence = " ".join(result["evidence"])
        self.assertIn('out-of-scope change: esc"aped.txt', evidence)
        self.assertNotIn("\\", evidence)

    def test_done_boundary_rejects_committed_symlink_escape(self):
        self._scope_claim(allowed=("link.txt",))
        self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        os.symlink("/tmp/execute-plan-escape-target", self.root / "link.txt")
        subprocess.run(["git", "add", "link.txt"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "committed symlink escape"], cwd=self.root, check=True)
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        done = self.driver().record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "commit-pending")
        self.assertFalse(done["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

    def test_reconcile_runs_done_boundary_verification(self):
        self._scope_claim(allowed=("task-4.txt",))
        driver = self.driver()
        driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        commit = self.commit_file("evil.txt")
        blocked = driver.record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(blocked["reason_code"], "commit-pending")
        claim = runtime.load_manifest(self.state_path)["claims"]["task-4"]
        driver.mark_commit_pending("task-4", commit, ["done-log:task-4"], claim_token=claim["token"], generation=0)
        reconciled = driver.reconcile_commit_before_checkpoint(
            "task-4", commit, commit_lookup=lambda value: value == commit, claim_token=claim["token"], generation=0
        )
        self.assertEqual(reconciled["status"], "blocked")
        self.assertEqual(reconciled["reason_code"], blocked["reason_code"])
        self.assertFalse(reconciled["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "commit-pending")

    def test_reconcile_surfaces_stale_claim_on_drifted_launch_record(self):
        # Baseline drift landing between quarantine and reconciliation must
        # surface the resumable stale-claim outcome on the reconcile path too
        # (the same drift check the done handoff runs), with no checkpointed
        # completion persisted.
        self._scope_claim(allowed=("task-4.txt",))
        driver = self.driver()
        claim = runtime.load_manifest(self.state_path)["claims"]["task-4"]
        driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token=claim["token"], generation=0)
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["baseline_revision"] = "0f1e2d3c4b5a6978869deadbeef0000000000001"
        runtime._safe_write_json(self.state_path, state)
        reconciled = driver.reconcile_commit_before_checkpoint(
            "task-4", "aa11bb22cc33", commit_lookup=lambda commit: commit == "aa11bb22cc33", claim_token=claim["token"], generation=0
        )
        self.assertEqual(reconciled["status"], "blocked")
        self.assertEqual(reconciled["reason_code"], "stale-claim")
        self.assertTrue(reconciled["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "commit-pending")
        self.assertNotIn("task-4:commit", after["checkpoints"])

    def test_post_claim_ambient_noise_stays_hard_blocked(self):
        # Characterization pin: ambient noise appearing after the claim's
        # launch record is indistinguishable from a worker-caused escape
        # (mtime is forgeable), so the checkpoint witness stays hard.
        self._launched_claim(allowed=("task-4.txt",))
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        self.assertFalse(result["resume_allowed"])

    def test_post_launch_untracked_escape_stays_hard_blocked(self):
        # Characterization pin: an untracked out-of-policy path after the
        # launch record keeps the non-resumable blocked stance; launch-record
        # presence, not mtime, is the ambient-versus-worker discriminator.
        self._launched_claim(allowed=("task-4.txt",))
        (self.root / "outside-policy.txt").write_text("worker escape\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        self.assertFalse(result["resume_allowed"])

    def _prelaunch_claim(self, task="task-4"):
        state = runtime.load_manifest(self.state_path)
        state["claims"][task] = {"token": "pre-dirty-token", "generation": 0, "owner": "test-owner", "state": "claimed", "task_id": task}
        state["tasks"][task]["status"] = "claimed"
        runtime._safe_write_json(self.state_path, state)

    def test_startup_ambient_noise_is_resumable_cleanup_required(self):
        self._prelaunch_claim()
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        (docs / ".#notes.md").write_text("editor swap\n", encoding="utf-8")
        driver = self.driver()
        startup = driver.reconcile_startup()
        self.assertEqual(startup["status"], "blocked")
        self.assertEqual(startup["reason_code"], "cleanup-required")
        self.assertTrue(startup["resume_allowed"])
        continued = driver.continue_parent()
        self.assertEqual(continued["reason_code"], "cleanup-required")
        self.assertTrue(continued["resume_allowed"])

        # Anything outside the allowlist keeps the hard dirty-worktree block.
        (docs / ".#notes.md").unlink()
        (self.root / "notes.txt").write_text("not ambient\n", encoding="utf-8")
        hard = driver.reconcile_startup()
        self.assertEqual(hard["reason_code"], "dirty-worktree")
        self.assertFalse(hard["resume_allowed"])

        # Tracked modifications are never ambient noise on the same path.
        (self.root / "notes.txt").unlink()
        (self.root / ".DS_Store").unlink()
        gitignore = self.root / ".gitignore"
        gitignore.write_text(gitignore.read_text(encoding="utf-8") + "# touched\n", encoding="utf-8")
        tracked = driver.reconcile_startup()
        self.assertEqual(tracked["reason_code"], "dirty-worktree")
        self.assertFalse(tracked["resume_allowed"])

    def test_startup_ambient_noise_without_live_claim_is_resumable_cleanup(self):
        # No-live-claim case: a fresh manifest with zero claims and purely
        # ambient worktree noise must surface the resumable cleanup-required
        # outcome before any launch, never a non-resumable violation from the
        # subsequent launch path.
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        driver = self.driver()
        startup = driver.reconcile_startup()
        self.assertEqual(startup["status"], "blocked")
        self.assertEqual(startup["reason_code"], "cleanup-required")
        self.assertTrue(startup["resume_allowed"])
        continued = driver.continue_parent()
        self.assertEqual(continued["reason_code"], "cleanup-required")
        self.assertTrue(continued["resume_allowed"])

    def test_startup_ambient_noise_with_launched_claim_stays_hard_blocked(self):
        # A launched claim (launch record present) with an all-ambient dirty
        # worktree falls through to the non-resumable dirty-worktree block:
        # after the launch record exists, ambient-shaped noise is
        # indistinguishable from worker-caused dirt.
        self._launched_claim()
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        driver = self.driver()
        startup = driver.reconcile_startup()
        self.assertEqual(startup["status"], "blocked")
        self.assertEqual(startup["reason_code"], "dirty-worktree")
        self.assertFalse(startup["resume_allowed"])

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
        # An explicit abort racing the launch window surfaces the abort
        # outcome (resume never allowed), not an owner mismatch.
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
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
            config = root / "config.toml"
            config.write_text('approval_policy = "never"\n', encoding="utf-8")
            write_approval_receipt(receipt, config, {})
            base = [sys.executable, str(ROOT / "scripts/execute_plan_runtime.py"), "--manifest", str(state_path), "--operation", "claim"]
            ok = subprocess.run(base + ["--runtime", "codex", "--approval-receipt", str(receipt)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue(json.loads(ok.stdout)["claimed"])
            bad_receipt = root / "bad.json"
            bad_receipt.write_text(json.dumps({"runtime": "codex", "approval": "assumed", "config_path": str(config), "policy_fingerprint": "0" * 64}), encoding="utf-8")
            bad_receipt.chmod(0o600)
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
        # The commit boundary is written inside the live launch window: the
        # F-r4-4 progression fence refuses a commit-pending write onto the
        # seeded fixture's still-complete task, so pin the task to launched.
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-3"]["status"] = "launched"
        runtime._safe_write_json(self.state_path, state)
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

    def test_create_operation_seeds_manifest(self):
        created_path = self.root / "created_state.json"
        command = [
            sys.executable,
            str(ROOT / "scripts/execute_plan_runtime.py"),
            "--manifest", str(created_path),
            "--repo-root", str(self.root),
            "--owner", "create-owner",
            "--plan-slug", "created-plan",
            "--operation", "create",
            "--input", json.dumps(
                {
                    "tasks": [
                        {"id": "task-1", "number": 1, "status": "pending"},
                        {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["task-2.txt"]},
                    ]
                }
            ),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "success")
        manifest = runtime.load_manifest(created_path)
        self.assertEqual(manifest["plan_slug"], "created-plan")
        self.assertEqual(manifest["generation"], 0)
        self.assertEqual(manifest["workflow_state"], "active")
        self.assertEqual(set(manifest["tasks"]), {"task-1", "task-2"})
        self.assertEqual({task["status"] for task in manifest["tasks"].values()}, {"pending"})
        self.assertEqual(manifest["owner"], "create-owner")
        # Shape-identical to the selftest seeding: the create operation wraps
        # create_manifest, so the top-level manifest shape matches exactly.
        reference = runtime.create_manifest(
            self.root / "reference_state.json",
            "created-plan",
            [{"id": "task-1", "number": 1, "status": "pending"}],
        )
        self.assertEqual(set(manifest) - {"owner"}, set(reference))
        self.assertEqual(os.stat(created_path).st_mode & 0o777, 0o600)

    def test_create_operation_fails_closed_under_concurrent_create(self):
        # Exclusive-create contention: a competing owner holding the manifest
        # lock lease makes create fail closed instead of last-writer-wins;
        # the manifest is never seeded and the error names the contention.
        created_path = self.root / "contended_state.json"
        with runtime._manifest_lock(created_path, "competing-owner"):
            command = [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(created_path),
                "--repo-root", str(self.root),
                "--owner", "create-owner",
                "--plan-slug", "contended-plan",
                "--operation", "create",
                "--input", json.dumps({"tasks": [{"id": "task-1", "number": 1, "status": "pending"}]}),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("held by another owner", completed.stderr)
        self.assertFalse(created_path.exists())

    def test_directory_valued_allowed_path_rejected_with_actionable_error(self):
        (self.root / "docsdir").mkdir()
        for index, entry in enumerate(("docsdir", "docsdir/", "missing-dir/")):
            created_path = self.root / f"create-reject-{index}.json"
            command = [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(created_path),
                "--repo-root", str(self.root),
                "--owner", "create-owner",
                "--plan-slug", "reject-plan",
                "--operation", "create",
                "--input", json.dumps({"tasks": [{"id": "task-1", "number": 1, "status": "pending", "allowed_paths": [entry]}]}),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0, entry)
            self.assertIn(entry.rstrip("/"), completed.stderr + completed.stdout)
            self.assertFalse(created_path.exists(), entry)
        driver = self.driver()
        for entry in ("docsdir", "docsdir/", "missing-dir/"):
            envelope = runtime.ActionEnvelope(str(self.root), (entry,), "repository-write", False, ("evidence",))
            result = driver.authorize_envelope(envelope, generation=1)
            self.assertEqual(result["status"], "blocked", entry)
            self.assertTrue(any(entry.rstrip("/") in item for item in result["evidence"]), entry)

    def test_create_operation_malformed_task_item_fails_closed(self):
        # Malformed list items (non-mapping item, mapping without a string id)
        # must raise the fail-closed ValueError naming the shape, never a raw
        # TypeError from subscripting before validation.
        for index, task in enumerate(("bare-string-task", {"number": 1}, {"id": 7})):
            created_path = self.root / f"create-malformed-{index}.json"
            command = [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(created_path),
                "--repo-root", str(self.root),
                "--plan-slug", "malformed-plan",
                "--operation", "create",
                "--input", json.dumps({"tasks": [task]}),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("create operation tasks must be mappings with a string id", completed.stderr)
            self.assertFalse(created_path.exists())

    def test_evidence_and_fixtures_are_hermetic(self):
        result = capabilities.bounded_evidence(["token=secret", {"password": "nested-secret"}, "x" * 2000])
        self.assertLessEqual(sum(map(len, result)), capabilities.MAX_EVIDENCE_BYTES)
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

    def test_launch_record_written_at_claim(self):
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"] = {"token": "pre-launch-token", "generation": 0, "owner": "test-owner", "state": "claimed", "task_id": "task-4"}
        state["tasks"]["task-4"]["status"] = "claimed"
        runtime._safe_write_json(self.state_path, state)
        self.assertIsNone(state["claims"]["task-4"].get("launch_record"))
        observed = {}

        def spy(task, _prompt, generation, deadline_seconds=None, policy_token=None):
            observed["claim"] = dict(runtime.load_manifest(self.state_path)["claims"][task["id"]])
            return self.worker_checkpoint(task=task["id"], generation=generation)

        driver = self.driver(adapter=FakeAdapter(spy), seed_task3=False)
        result = driver._launch_claimed_task({"task_id": "task-4", "token": "pre-launch-token", "generation": 0}, "continue", None)
        self.assertEqual(result["status"], "success")
        baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        claim = observed["claim"]
        # The launch record lands atomically with the claim transition: the
        # worker already observes state=launched together with the snapshot.
        self.assertEqual(claim["state"], "launched")
        record = claim["launch_record"]
        self.assertEqual(record["baseline_revision"], baseline)
        self.assertEqual(record["generation"], claim["generation"])
        self.assertIsInstance(record["launched_at"], float)
        self.assertGreater(record["launched_at"], 0.0)
        # The launch timestamp lives only inside the launch record; no
        # top-level mirror is written on the claim.
        self.assertNotIn("launched_at", claim)

    def _launched_claim(self, allowed=("task-4.txt",)):
        baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"] = {
            "token": "drift-token",
            "generation": 0,
            "owner": "test-owner",
            "state": "launched",
            "task_id": "task-4",
            "policy_token": {"token": "policy", "repo_root": str(self.root), "allowed_paths": list(allowed), "operation_kind": "repository-task", "network": False, "generation": 0},
            "baseline_revision": baseline,
            "launched_at": 111.5,
            "launch_record": {"baseline_revision": baseline, "generation": 0, "launched_at": 111.5},
        }
        runtime._safe_write_json(self.state_path, state)
        return baseline

    def test_baseline_or_generation_change_maps_to_stale_claim(self):
        driver = self.driver()
        for mutate in ("erase", "change", "replace-generation"):
            with self.subTest(mutate=mutate):
                baseline = self._launched_claim()
                state = runtime.load_manifest(self.state_path)
                if mutate == "erase":
                    state["claims"]["task-4"]["baseline_revision"] = ""
                elif mutate == "change":
                    state["claims"]["task-4"]["baseline_revision"] = "0f1e2d3c4b5a6978869deadbeef0000000000001"
                else:
                    state["claims"]["task-4"]["generation"] = 9
                runtime._safe_write_json(self.state_path, state)
                generation = 9 if mutate == "replace-generation" else 0
                result = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=generation))
                self.assertEqual(result["status"], "blocked", mutate)
                self.assertEqual(result["reason_code"], "stale-claim", mutate)
                self.assertTrue(result["resume_allowed"], mutate)
                after = runtime.load_manifest(self.state_path)
                self.assertEqual(after["tasks"]["task-4"]["status"], "pending", mutate)
                self.assertFalse(any(event.get("event") == "done-commit" for event in after["history"]), mutate)

        # Done-boundary witness: drift after a legitimate checkpoint surfaces
        # stale-claim before any commit handoff.
        baseline = self._launched_claim()
        driver = self.driver()
        self.assertEqual(driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["baseline_revision"] = "0f1e2d3c4b5a6978869deadbeef0000000000001"
        runtime._safe_write_json(self.state_path, state)
        commit = self.commit_file("task-4.txt")
        done = driver.record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "stale-claim")
        self.assertTrue(done["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

        # Legitimate checkpoints and checkbox bookkeeping keep the snapshot
        # valid and both witnesses green.
        self._launched_claim()
        driver = self.driver()
        self.assertEqual(driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        state["history"].append({"event": "checkbox-update", "task_id": "task-4"})
        runtime._safe_write_json(self.state_path, state)
        manifest = runtime.load_manifest(self.state_path)
        self.assertIsNone(driver._claim_drift_outcome(manifest, manifest["claims"]["task-4"], "repository-task", "task-4:worker"))
        commit = self.commit_file("task-4.txt", content="legitimate checkpoint change\n")
        done = driver.record_done(self.done(task="task-4", generation=0, commit_identity=commit))
        self.assertEqual(done["status"], "success")

    def test_pre_launch_claim_has_no_drift_checks(self):
        driver = self.driver()
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"] = {"token": "pre-token", "generation": 0, "owner": "test-owner", "state": "claimed", "task_id": "task-4"}
        state["tasks"]["task-4"]["status"] = "claimed"
        runtime._safe_write_json(self.state_path, state)
        manifest = runtime.load_manifest(self.state_path)
        self.assertIsNone(driver._claim_drift_outcome(manifest, manifest["claims"]["task-4"], "repository-task", "task-4:worker"))

        # Recorded checkpoints without a launch record: demonstrably launched.
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"].update({"state": "launched", "token": "post-token"})
        state["tasks"]["task-4"]["status"] = "done-pending"
        state["checkpoints"]["task-4:worker"] = {"result": {"status": "success"}, "task_id": "task-4"}
        runtime._safe_write_json(self.state_path, state)
        manifest = runtime.load_manifest(self.state_path)
        outcome = driver._claim_drift_outcome(manifest, manifest["claims"]["task-4"], "repository-task", "task-4:worker")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])

        # Non-pending task status without checkpoints also proves launch; the
        # done boundary surfaces the same resumable outcome.
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"] = {"token": "post-token", "generation": 0, "owner": "test-owner", "state": "launched", "task_id": "task-4"}
        state["tasks"]["task-4"]["status"] = "done-pending"
        state["checkpoints"] = {}
        runtime._safe_write_json(self.state_path, state)
        done = driver.record_done(self.done(task="task-4", generation=0))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "stale-claim")
        self.assertTrue(done["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

    def test_retry_relaunch_timeout_persists_resumable_receipt(self):
        # A retry relaunch failure must persist the arm's real reason code
        # (with the failed attempt recorded under its ordinal), never surface
        # owner-mismatch from a receipt that lost its claim fencing. Every
        # launch-error arm is covered: raised TimeoutError/TypeError/
        # RuntimeError, a non-mapping return, and a mapping return without
        # claim_token (backfilled by the driver before the recursive
        # checkpoint).
        arms = [
            ("timeout", TimeoutError("deadline exceeded"), "timeout", "blocked", True),
            ("type-error", TypeError("policy token rejected"), "runtime-policy-unavailable", "blocked", False),
            ("runtime-error", RuntimeError("boom"), "runtime-error", "error", False),
            ("non-mapping", "not-a-mapping-result", "malformed-result", "blocked", False),
        ]

        def arm_launch(behavior):
            def launch(task, _prompt, generation, deadline_seconds=None, policy_token=None):
                if isinstance(behavior, BaseException):
                    raise behavior
                return behavior
            return launch

        failure_receipt = {
            "status": "error",
            "reason_code": "runtime-error",
            "evidence": ["boom"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker",
            "generation": 0,
            "retry_policy": {"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1},
        }
        for label, behavior, reason, result_status, resumable in arms:
            with self.subTest(arm=label):
                self.seed_claim(task="task-4", token="seed-task-4")
                driver = self.driver(adapter=FakeAdapter(arm_launch(behavior)), seed_task3=False)
                result = driver.record_worker_checkpoint({**failure_receipt, "claim_token": "seed-task-4"})
                self.assertEqual(result["status"], result_status, label)
                self.assertEqual(result["reason_code"], reason, label)
                self.assertNotEqual(result["reason_code"], "owner-mismatch", label)
                self.assertEqual(result["resume_allowed"], resumable, label)
                state = runtime.load_manifest(self.state_path)
                self.assertIn("task-4:worker#attempt-1", state["checkpoints"], label)
                self.assertEqual(state["tasks"]["task-4"]["status"], "blocked", label)
                self.assertEqual(state["tasks"]["task-4"]["blocked_receipt"]["reason_code"], reason, label)

        # Mapping-without-claim_token arm: the driver backfills the token, so
        # the success receipt lands done-pending instead of owner-mismatch.
        with self.subTest(arm="mapping-without-claim-token"):
            self.seed_claim(task="task-4", token="seed-task-4")

            def success_without_token(task, _prompt, generation, deadline_seconds=None, policy_token=None):
                receipt = self.worker_checkpoint(task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker")
                receipt.pop("claim_token", None)
                return receipt

            driver = self.driver(adapter=FakeAdapter(success_without_token), seed_task3=False)
            result = driver.record_worker_checkpoint({**failure_receipt, "claim_token": "seed-task-4"})
            self.assertEqual(result["state"], "done-pending")
            self.assertEqual(result["reason_code"], "completed")
            self.assertNotEqual(result["reason_code"], "owner-mismatch")
            state = runtime.load_manifest(self.state_path)
            self.assertIn("task-4:worker#attempt-1", state["checkpoints"])
            self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")

    def test_second_retry_persists_distinct_attempt_record(self):
        self.seed_claim(task="task-4", token="seed-task-4")
        launches = []

        def flaky(task, _prompt, generation, _deadline, _token):
            remaining = 2 - len(launches)
            launches.append(remaining)
            return {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": [f"failure {remaining}"],
                "action_scope": "repository-task",
                "checkpoint_identity": f"{task['id']}:worker",
                "generation": generation,
                "retry_policy": {"mode": "bounded", "max_attempts": 2, "attempts_remaining": remaining},
            }

        driver = self.driver(adapter=FakeAdapter(flaky))
        result = driver.record_worker_checkpoint(
            {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["failure 2"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-4:worker",
                "generation": 0,
                "claim_token": "seed-task-4",
                "retry_policy": {"mode": "bounded", "max_attempts": 2, "attempts_remaining": 2},
            }
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(launches), 2)
        state = runtime.load_manifest(self.state_path)
        # Two consecutive error checkpoints under retry budget 2 persist two
        # distinct durable attempt records under derived ordinals; the fixed
        # #attempt-initial key never overwrites the first attempt.
        attempts = sorted(key for key in state["checkpoints"] if key.startswith("task-4:worker#attempt-"))
        self.assertEqual(len(attempts), 2)
        self.assertNotIn("task-4:worker#attempt-initial", state["checkpoints"])
        for key in attempts:
            record = state["checkpoints"][key]
            self.assertEqual(record["task_id"], "task-4")
            self.assertEqual(record["result"]["status"], "error")

    def test_owner_resolved_under_lock(self):
        # Two first constructions on a fresh manifest with a deterministic
        # interleaving: the competing construction runs between the loser's
        # manifest read and its write, injected through the manifest loader
        # (the same injection point the loader-counting witness uses). The
        # loser must adopt the committed owner identity under the manifest
        # lock, never keep a private identity that silently fails every later
        # owner fence.
        fresh = self.root / "fresh_state.json"
        runtime.create_manifest(fresh, "fixture-plan", [{"id": "task-4", "number": 4, "status": "pending", "checkbox": False}])
        original = runtime.load_manifest
        interleave = {"armed": True}
        winner_holder = {}

        def loader(path):
            if interleave["armed"]:
                interleave["armed"] = False
                # The loser reads first, the competing construction commits
                # its owner, and only then does the loser's read return the
                # pre-competition snapshot.
                snapshot = original(path)
                winner_holder["winner"] = runtime.RuntimeDriver(
                    fresh, plan_slug="fixture-plan", repo_root=self.root, commit_lookup=lambda _commit: True
                )
                return snapshot
            return original(path)

        with mock.patch.object(runtime, "load_manifest", side_effect=loader):
            loser = runtime.RuntimeDriver(fresh, plan_slug="fixture-plan", repo_root=self.root, commit_lookup=lambda _commit: True)
        winner = winner_holder["winner"]
        committed = runtime.load_manifest(fresh).get("owner")
        self.assertTrue(isinstance(committed, str) and committed.strip())
        self.assertEqual(winner.owner, committed)
        self.assertEqual(loser.owner, committed)

    def test_owner_resolution_on_contended_construction_adopts_or_fails_closed(self):
        # Deterministic interleaving for the contended-at-construction branch:
        # the lock is held across the whole construction, so the driver hits
        # `not acquired` in _resolve_owner_and_receipts.
        fresh = self.root / "contended_state.json"
        runtime.create_manifest(fresh, "fixture-plan", [{"id": "task-4", "number": 4, "status": "pending", "checkbox": False}])
        # No committed owner: fail closed naming the contention instead of
        # silently keeping a provisional random identity that would miss every
        # later owner fence.
        with runtime._manifest_lock(fresh, "blocking-owner"):
            with self.assertRaises(ValueError) as raised:
                runtime.RuntimeDriver(fresh, plan_slug="fixture-plan", repo_root=self.root, commit_lookup=lambda _commit: True)
            self.assertIn("manifest lock contended at construction", str(raised.exception))
            self.assertIn("no committed owner to adopt", str(raised.exception))
        # A committed owner is adopted through the best-effort unlocked
        # re-read, converging the contender onto the winner's identity.
        state = runtime.load_manifest(fresh)
        state["owner"] = "committed-owner"
        runtime._safe_write_json(fresh, state)
        with runtime._manifest_lock(fresh, "blocking-owner"):
            contender = runtime.RuntimeDriver(fresh, plan_slug="fixture-plan", repo_root=self.root, commit_lookup=lambda _commit: True)
        self.assertEqual(contender.owner, "committed-owner")
        # An explicit owner is not provisional: contention is tolerated
        # without adoption.
        with runtime._manifest_lock(fresh, "blocking-owner"):
            explicit = runtime.RuntimeDriver(fresh, plan_slug="fixture-plan", owner="explicit-owner", repo_root=self.root, commit_lookup=lambda _commit: True)
        self.assertEqual(explicit.owner, "explicit-owner")

    def _resume_blocked_claim(self):
        baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        state = runtime.load_manifest(self.state_path)
        # Reset durable checkpoint records so each adapter-window witness
        # proves its own competing-writer transition instead of hitting the
        # duplicate-success no-persist branch on a prior witness's residue.
        state["checkpoints"] = {}
        state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": True, "session_id": "session-task-4"})
        state["claims"]["task-4"] = {
            "token": "resume-token",
            "generation": 1,
            "owner": "test-owner",
            "state": "blocked",
            "task_id": "task-4",
            "baseline_revision": baseline,
            "launch_record": {"baseline_revision": baseline, "generation": 1, "launched_at": 111.0},
            "policy_token": {"token": "policy", "repo_root": str(self.root), "allowed_paths": ["task-4.txt"], "operation_kind": "repository-task", "network": False, "generation": 1},
        }
        runtime._safe_write_json(self.state_path, state)
        return baseline

    def test_resume_runs_adapter_io_outside_manifest_lock(self):
        state_path = self.state_path
        self._resume_blocked_claim()
        events = {}

        class SlowResumeAdapter:
            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                # Inside the adapter window the manifest flock must be
                # released: a probe acquisition in the same thread succeeds.
                with runtime._manifest_lock(state_path, "probe-owner") as acquired:
                    events["probe_acquired"] = acquired
                return {
                    "status": "success",
                    "reason_code": "completed",
                    "evidence": ["resumed"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": "task-4:worker",
                    "generation": generation,
                }

        driver = self.driver(adapter=SlowResumeAdapter(), seed_task3=False)
        result = driver.resume()
        self.assertTrue(events.get("probe_acquired"))
        # No spurious blocked or stale-claim outcome for the probe window.
        self.assertEqual(result["state"], "done-pending")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")

        # A competing writer injected during the adapter window is detected on
        # re-acquisition: the nested checkpoint write fails closed with the
        # resumable stale-claim outcome; a stale in-memory snapshot is never
        # written back over the rewritten claim.
        self._resume_blocked_claim()

        class TamperingResumeAdapter:
            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                state = runtime.load_manifest(state_path)
                state["claims"]["task-4"]["generation"] = 9
                runtime._safe_write_json(state_path, state)
                return {
                    "status": "success",
                    "reason_code": "completed",
                    "evidence": ["resumed"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": "task-4:worker",
                    "generation": generation,
                }

        driver = self.driver(adapter=TamperingResumeAdapter(), seed_task3=False)
        drifted = driver.resume()
        self.assertEqual(drifted["status"], "blocked")
        self.assertEqual(drifted["reason_code"], "stale-claim")
        self.assertTrue(drifted["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["claims"]["task-4"]["generation"], 9)

    def test_stale_blocked_receipt_does_not_regress_done_pending(self):
        # Deterministic interleaving mirroring the adapter-window witness
        # above: a competing writer lands a success checkpoint inside the
        # resume adapter window; the stale non-success resume receipt must
        # surface the resumable stale-claim outcome and never regress the
        # task below done-pending.
        state_path = self.state_path
        self._resume_blocked_claim()
        case = self

        class StaleErrorResumeAdapter:
            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                competing = case.driver(seed_task3=False)
                landed = competing.record_worker_checkpoint(
                    {
                        "status": "success",
                        "reason_code": "completed",
                        "evidence": ["competing writer"],
                        "action_scope": "repository-task",
                        "checkpoint_identity": "task-4:worker",
                        "generation": generation,
                        "claim_token": "resume-token",
                    }
                )
                assert landed["state"] == "done-pending", landed
                return {
                    "status": "error",
                    "reason_code": "runtime-error",
                    "evidence": ["stale failure"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": "task-4:resume",
                    "generation": generation,
                    "retry_policy": {"mode": "none", "max_attempts": 0, "attempts_remaining": 0},
                }

        driver = self.driver(adapter=StaleErrorResumeAdapter(), seed_task3=False)
        result = driver.resume()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        self.assertTrue(result["resume_allowed"])
        after = runtime.load_manifest(state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertEqual(after["checkpoints"]["task-4:worker"]["result"]["status"], "success")

    def test_abort_then_retryable_receipt_does_not_relaunch(self):
        # F-r3-1 witness (i): an explicit abort wins over an in-flight
        # retryable receipt. No relaunch, no durable attempt record, the
        # aborted state is never un-aborted by the late receipt.
        self.seed_claim(task="task-4", token="seed-task-4")
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker")
        )
        driver = self.driver(adapter=adapter, seed_task3=False)
        aborter = self.driver(seed_task3=False)
        aborted = aborter.abort("task-4", "seed-task-4")
        self.assertEqual(aborted["status"], "aborted")
        receipt = {
            "status": "error",
            "reason_code": "runtime-error",
            "evidence": ["late failure"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker",
            "generation": 0,
            "claim_token": "seed-task-4",
            "retry_policy": {"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1},
        }
        result = driver.record_worker_checkpoint(receipt)
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(result["reason_code"], "explicit-abort")
        self.assertFalse(result["resume_allowed"])
        self.assertEqual(adapter.launches, [])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["workflow_state"], "aborted")
        self.assertEqual(after["tasks"]["task-4"]["status"], "aborted")
        self.assertEqual(after["claims"]["task-4"]["state"], "aborted")
        self.assertNotIn("task-4:worker#attempt-1", after["checkpoints"])

    def test_resume_after_abort_is_explicit_abort(self):
        # F-r3-1 witness (ii): resume() on an aborted workflow surfaces the
        # explicit-abort outcome (never auto-resumed), mirroring continue_parent.
        self._resume_blocked_claim()
        aborted = self.driver(seed_task3=False).abort("task-4", "resume-token")
        self.assertEqual(aborted["status"], "aborted")
        result = self.driver(seed_task3=False).resume()
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(result["reason_code"], "explicit-abort")
        self.assertFalse(result["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["workflow_state"], "aborted")
        self.assertEqual(after["claims"]["task-4"]["state"], "aborted")

    def test_abort_refuses_progressed_claim(self):
        # F-r4-1 witness: after a success checkpoint lands done-pending, an
        # explicit abort with the still-current token is the progression
        # refusal; the task, claim, and workflow state stay untouched.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertEqual(after["workflow_state"], "active")
        # The done handoff still runs after the refused abort.
        self.assertEqual(driver.record_done(self.done(task="task-4"))["status"], "success")

    def test_claim_refuses_aborted_workflow_without_mutation(self):
        # F-r4-2 witness: an explicitly aborted workflow never hands out a new
        # claim; no generation bump, no claimed residue.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        driver.abort("task-4", "seed-task-4")
        before = runtime.load_manifest(self.state_path)
        result = driver.claim_next_task()
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(result["reason_code"], "explicit-abort")
        self.assertFalse(result["resume_allowed"])
        self.assertFalse(result.get("claimed", False))
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_mark_commit_pending_refuses_aborted_workflow(self):
        # F-r4-4 witness (a): a stale commit-pending write must never
        # overwrite an aborted workflow or its aborted task.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        driver.abort("task-4", "seed-task-4")
        outcome = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["workflow_state"], "aborted")
        self.assertEqual(after["tasks"]["task-4"]["status"], "aborted")

    def test_mark_commit_pending_refuses_checkpointed_task(self):
        # F-r4-4 witness (b): after record_done closes the claim and
        # checkpoints the task, a stale commit-pending write is refused
        # instead of regressing the completed state.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(driver.record_done(self.done(task="task-4"))["status"], "success")
        outcome = driver.mark_commit_pending("task-4", "dd33ee44ff55", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "checkpointed")
        self.assertEqual(after["claims"]["task-4"]["state"], "closed")
        self.assertNotEqual(after["tasks"]["task-4"]["commit_identity"], "dd33ee44ff55")

    def test_stale_retryable_receipt_does_not_regress_done_pending(self):
        # F-r3-2 witness: mirrors test_stale_blocked_receipt_... but the late
        # receipt is retryable (attempts remaining > 0) under both retry
        # shapes: bounded error retries and rewrite-and-retry contract
        # violations. The retry branch is suppressed for a progressed task;
        # the resumable stale-claim outcome surfaces instead of a relaunch.
        self._resume_blocked_claim()
        case = self

        class StaleRetryableResumeAdapter:
            def __init__(self, receipt):
                self.receipt = receipt
                self.launches = []

            def launch(self, *args, **kwargs):
                self.launches.append(args)
                raise AssertionError("stale retryable receipt must not relaunch")

            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                competing = case.driver(seed_task3=False)
                landed = competing.record_worker_checkpoint(
                    {
                        "status": "success",
                        "reason_code": "completed",
                        "evidence": ["competing writer"],
                        "action_scope": "repository-task",
                        "checkpoint_identity": "task-4:worker",
                        "generation": generation,
                        "claim_token": "resume-token",
                    }
                )
                assert landed["state"] == "done-pending", landed
                receipt = dict(self.receipt)
                receipt["generation"] = generation
                return receipt

        arms = [
            {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["stale retryable failure"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-4:resume",
                "claim_token": "resume-token",
                "retry_policy": {"mode": "bounded", "max_attempts": 2, "attempts_remaining": 2},
            },
            {
                "status": "contract-violation",
                "reason_code": "contract-violation",
                "evidence": ["stale contract violation"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-4:resume",
                "claim_token": "resume-token",
                "contract_rule": "stale rewrite-and-retry receipt",
                "retry_policy": {"mode": "rewrite-and-retry", "max_attempts": 2, "attempts_remaining": 2},
            },
        ]
        for receipt in arms:
            with self.subTest(receipt=f"{receipt['status']}:{receipt['retry_policy']['mode']}"):
                self._resume_blocked_claim()
                adapter = StaleRetryableResumeAdapter(receipt)
                result = self.driver(adapter=adapter, seed_task3=False).resume()
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "stale-claim")
                self.assertTrue(result["resume_allowed"])
                self.assertEqual(adapter.launches, [])
                after = runtime.load_manifest(self.state_path)
                self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
                self.assertNotIn("task-4:resume#attempt-1", after["checkpoints"])

    def test_stale_receipt_after_competing_done_handoff_refuses_persist(self):
        # F-r3-8 adapter-window witness: a competing writer completes the full
        # done handoff inside the resume adapter window; the subsequent
        # malformed resume result is refused at the persist site (stale-claim)
        # and never regresses the closed, checkpointed task.
        self._resume_blocked_claim()
        state = runtime.load_manifest(self.state_path)
        # Empty the launch-record baseline so the fixture commit handoff
        # passes the done boundary with the inert git witnesses.
        state["claims"]["task-4"]["baseline_revision"] = ""
        state["claims"]["task-4"]["launch_record"] = {"baseline_revision": "", "generation": 1, "launched_at": 111.0}
        runtime._safe_write_json(self.state_path, state)
        case = self

        class DoneHandoffResumeAdapter:
            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                competing = case.driver(seed_task3=False)
                landed = competing.record_worker_checkpoint(
                    {
                        "status": "success",
                        "reason_code": "completed",
                        "evidence": ["competing writer"],
                        "action_scope": "repository-task",
                        "checkpoint_identity": "task-4:worker",
                        "generation": generation,
                        "claim_token": "resume-token",
                    }
                )
                assert landed["state"] == "done-pending", landed
                done = competing.record_done(case.done(task="task-4", generation=generation, claim_token="resume-token"))
                assert done["status"] == "success", done
                return None

        result = self.driver(adapter=DoneHandoffResumeAdapter(), seed_task3=False).resume()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "checkpointed")
        self.assertEqual(after["claims"]["task-4"]["state"], "closed")

    def test_claim_progressed_past_receipt_include_terminal_matrix(self):
        # F-r3-8 predicate-level witness: the include_terminal flag gates only
        # checkpointed/complete; the core statuses (done-pending,
        # commit-pending, aborted) and a closed claim always progress.
        live_claim = {"state": "launched"}
        for status in ("pending", "claimed", "launched", "blocked"):
            task = {"status": status}
            self.assertFalse(runtime._claim_progressed_past_receipt(task, live_claim))
            self.assertFalse(runtime._claim_progressed_past_receipt(task, live_claim, include_terminal=True), status)
        for status in ("done-pending", "commit-pending", "aborted"):
            task = {"status": status}
            self.assertTrue(runtime._claim_progressed_past_receipt(task, live_claim), status)
            self.assertTrue(runtime._claim_progressed_past_receipt(task, live_claim, include_terminal=True), status)
        for status in ("checkpointed", "complete"):
            task = {"status": status}
            self.assertFalse(runtime._claim_progressed_past_receipt(task, live_claim), status)
            self.assertTrue(runtime._claim_progressed_past_receipt(task, live_claim, include_terminal=True), status)
        self.assertTrue(runtime._claim_progressed_past_receipt({"status": "launched"}, {"state": "closed"}))
        self.assertTrue(runtime._claim_progressed_past_receipt(None, {"state": "closed"}))
        self.assertFalse(runtime._claim_progressed_past_receipt(None, live_claim))

    def test_blocked_claim_with_launch_record_and_ambient_noise_blocks_hard(self):
        # F-r3-4 witness: a blocked claim that already launched (it carries a
        # launch record) plus ambient-shaped dirt keeps the non-resumable
        # dirty-worktree block; the resumable cleanup-required hoist fires only
        # when no claim carries launch evidence.
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": True})
        state["claims"]["task-4"] = {
            "token": "blocked-launched",
            "generation": 1,
            "owner": "test-owner",
            "state": "blocked",
            "task_id": "task-4",
            "launch_record": {"baseline_revision": "", "generation": 1, "launched_at": 111.0},
        }
        runtime._safe_write_json(self.state_path, state)
        (self.root / ".DS_Store").write_bytes(b"junk")
        result = self.driver(seed_task3=False).reconcile_startup()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "dirty-worktree")
        self.assertFalse(result["resume_allowed"])

    def test_startup_dirty_gate_fires_for_completed_launch_claims(self):
        # F-r4-9 witness: legacy-style manifest whose only launch-evidence
        # claim sits on a completed task; the per-claim loop would skip it, so
        # the hoisted pre-loop dirty gate must fire. The ambient discriminator
        # still picks the outcome: a claim with a launch record keeps the hard
        # dirty-worktree block, a legacy claim without one keeps the resumable
        # cleanup-required outcome.
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                state = runtime.load_manifest(self.state_path)
                claim = {
                    "token": "legacy-launched",
                    "generation": 0,
                    "owner": "test-owner",
                    "state": "launched",
                    "task_id": "task-3",
                }
                if not legacy:
                    claim["launch_record"] = {"baseline_revision": "", "generation": 0, "launched_at": 111.0}
                state["claims"]["task-3"] = claim
                runtime._safe_write_json(self.state_path, state)
                (self.root / ".DS_Store").write_bytes(b"junk")
                result = self.driver().reconcile_startup()
                self.assertEqual(result["status"], "blocked")
                if legacy:
                    self.assertEqual(result["reason_code"], "cleanup-required")
                    self.assertTrue(result["resume_allowed"])
                else:
                    self.assertEqual(result["reason_code"], "dirty-worktree")
                    self.assertFalse(result["resume_allowed"])

    def test_continue_parent_does_not_relaunch_done_pending_claim(self):
        # F-r3-5 witness: after a crash between checkpoint and done handoff, a
        # launched claim over a done-pending task surfaces the done-pending
        # outcome; no fresh launch, no launch-record overwrite.
        self.seed_claim(task="task-4", token="seed-task-4")

        class NoLaunchAdapter:
            def launch(self, *args, **kwargs):
                raise AssertionError("done-pending task must not be relaunched")

        driver = self.driver(adapter=NoLaunchAdapter(), seed_task3=False)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        before = runtime.load_manifest(self.state_path)["claims"]["task-4"]["launch_record"]
        result = driver.continue_parent()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(after["claims"]["task-4"]["launch_record"], before)

    def test_activation_receipt_fence_refuses_aborted_workflow(self):
        # F-r3-6 witness: the activation-receipt write is fenced against an
        # aborted workflow and a claim that is no longer live; no write lands.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        claim = {"token": "seed-task-4", "generation": 0, "task_id": "task-4"}
        self.driver(seed_task3=False).abort("task-4", "seed-task-4")
        outcome = driver._record_activation_receipt(claim, "task-4", {"status": "success"})
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertNotIn("activation_receipt", runtime.load_manifest(self.state_path)["claims"]["task-4"])

        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "active"
        state["claims"]["task-4"]["state"] = "blocked"
        runtime._safe_write_json(self.state_path, state)
        outcome = driver._record_activation_receipt(claim, "task-4", {"status": "success"})
        # F-r4-3 tightening: a claim that left the live set on an active
        # workflow is the stale-claim family, distinct from explicit-abort.
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        self.assertNotIn("activation_receipt", runtime.load_manifest(self.state_path)["claims"]["task-4"])

    def test_profile_less_invocation_preserves_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "runtime_state.json"
            runtime.create_manifest(state_path, "receipt-plan", [{"id": "task-1", "number": 1, "status": "pending"}])
            receipt = root / "approval.json"
            config = root / "config.toml"
            config.write_text('approval_policy = "never"\n', encoding="utf-8")
            write_approval_receipt(receipt, config, {})

            def cli(*extra):
                command = [sys.executable, str(ROOT / "scripts/execute_plan_runtime.py"), "--manifest", str(state_path), "--operation", "claim", *extra]
                return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)

            profiled = cli("--runtime", "codex", "--approval-receipt", str(receipt))
            self.assertEqual(profiled.returncode, 0, profiled.stderr)
            before = runtime.load_manifest(state_path)["capabilities"]
            self.assertNotEqual(before["resume"]["state"], "unsupported")
            # A CLI construction without a runtime profile must leave the
            # durable capability receipts unchanged; no silent downgrade to
            # unsupported.
            plain = cli()
            self.assertEqual(plain.returncode, 0, plain.stderr)
            after = runtime.load_manifest(state_path)["capabilities"]
            self.assertEqual(after, before)

    def test_record_done_has_single_commit_pending_transition(self):
        token = self.seed_claim()
        driver = self.driver()
        # Same fixture pin as test_commit_before_checkpoint_reconciles: the
        # F-r4-4 fence refuses commit-pending writes onto a complete task.
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-3"]["status"] = "launched"
        runtime._safe_write_json(self.state_path, state)
        original_save = driver._save
        snapshots = []
        seen_events = 0

        def recording_save(manifest):
            nonlocal seen_events
            new_events = [dict(event) for event in manifest["history"][seen_events:]]
            seen_events = len(manifest["history"])
            snapshots.append(
                {
                    "tasks": {task_id: task.get("status") for task_id, task in manifest["tasks"].items()},
                    "new_events": new_events,
                }
            )
            original_save(manifest)

        with mock.patch.object(driver, "_save", side_effect=recording_save):
            # commit-pending is owned solely by mark_commit_pending.
            driver.mark_commit_pending("task-3", "aa11bb22cc33", ["done-log:task-3"], claim_token=token, generation=0)
        self.seed_claim(task="task-4", token="seed-task-4")
        with mock.patch.object(driver, "_save", side_effect=recording_save):
            # Full record_done cycle: the done handoff must not write its own
            # dead commit-pending transition.
            driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
            done = driver.record_done(self.done(task="task-4", generation=0))
        self.assertEqual(done["status"], "success")

        def marks_commit_pending(snapshot):
            return any(event.get("event") == "commit-pending" for event in snapshot["new_events"])

        marking = [index for index, snapshot in enumerate(snapshots) if marks_commit_pending(snapshot)]
        self.assertEqual(len(marking), 1, snapshots)
        # Nothing rewrites that transition afterwards.
        self.assertFalse(any(marks_commit_pending(snapshot) for snapshot in snapshots[marking[0] + 1 :]))
        self.assertIn("done-commit", [event.get("event") for event in snapshots[-1]["new_events"]])
        self.assertEqual(snapshots[-1]["tasks"]["task-4"], "checkpointed")

    def test_record_done_launches_next_task_after_released_lock(self):
        self.seed_claim()
        driver = self.driver()
        driver.record_worker_checkpoint(self.worker_checkpoint())
        outcome = driver.record_done(self.done())
        # The next-claim transition runs after the locked region ends: the
        # driver returns the launch-task action, never stale-claim from a
        # nested claim_next_task acquisition under the non-reentrant lock.
        self.assertEqual(outcome["status"], "success")
        self.assertNotEqual(outcome["reason_code"], "stale-claim")
        self.assertEqual([action["type"] for action in outcome["actions"]], ["launch-task"])
        self.assertEqual(outcome["actions"][0]["task_id"], "task-4")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "claimed")

    def test_blocked_persist_keeps_contract_violation_receipt(self):
        self._scope_claim(allowed=("allowed.txt",))
        (self.root / "outside-policy.txt").write_text("worker escape\n", encoding="utf-8")
        subprocess.run(["git", "add", "-N", "outside-policy.txt"], cwd=self.root, check=True)
        # Under the non-reentrant lock the blocked persist runs inside the
        # checkpoint's locked region: the scope violation must keep its
        # contract-violation receipt, never an owner-mismatch misdiagnosis
        # from a failed nested lock acquisition.
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        self.assertFalse(result["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "blocked")

    def test_authorize_action_reuses_loaded_manifest(self):
        driver = self.driver()
        loads = []
        original = runtime.load_manifest

        def counting(path):
            loads.append(str(path))
            return original(path)

        raw = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["worker"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker",
            "generation": 1,
            "actions": [
                {"operation": "repository-write", "target": "allowed-1.txt"},
                {"operation": "repository-write", "target": "allowed-2.txt"},
            ],
        }
        with mock.patch.object(runtime, "load_manifest", side_effect=counting):
            driver.validate_adapter_result(raw)
        # Several authorize_action calls inside one checkpoint cycle trigger
        # no per-call manifest re-read: the already-loaded manifest passes
        # through the authorization path.
        self.assertEqual(len(loads), 1)

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
                    [
                        sys.executable,
                        "-c",
                        "import json, os; print(json.dumps({'cwd': os.getcwd(), 'HOME': os.environ.get('HOME'), 'TZ': os.environ.get('TZ'), 'LANG': os.environ.get('LANG'), 'LC_ALL': os.environ.get('LC_ALL')}))",
                    ],
                    cwd=root,
                    env=dict(os.environ),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                observed = json.loads(process.stdout)
                self.assertEqual(
                    [str(Path(observed[key]).resolve()) for key in ("cwd", "HOME")],
                    [str(root.resolve()), str((root / "home").resolve())],
                )
                # Locale and clock env must take effect in the child too, not
                # only cwd and HOME.
                self.assertEqual(
                    (observed["TZ"], observed["LANG"], observed["LC_ALL"]), ("UTC", "C", "C")
                )
                self.assertTrue(state_path.is_relative_to(root))
            finally:
                os.environ.clear()
                os.environ.update(original_env)
                os.chdir(original_cwd)

    def test_hermeticity_round_trip_asserts_locale_and_clock_env(self):
        original_cwd = Path.cwd()
        original_env = dict(os.environ)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                os.chdir(root)
                os.environ.clear()
                os.environ.update({"HOME": str(root / "home"), "PATH": "", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"})
                # Construct the replay fixture first so the pinned locale and
                # clock environment intersects the code under test (the driver
                # construction and authorization run inside the window), not
                # only the subprocess round-trip below.
                driver, state_path = self._replay_driver(root, [{"id": "task-1", "number": 1, "status": "pending"}])
                self.assertEqual(driver.authorize_action("repository-write", "inside.txt")["status"], "success")
                self.assertEqual(driver.authorize_action("network")["status"], "blocked")
                self.assertTrue(state_path.is_relative_to(root))
                process = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "import json, os; print(json.dumps({'cwd': os.getcwd(), 'HOME': os.environ.get('HOME'), 'TZ': os.environ.get('TZ'), 'LANG': os.environ.get('LANG'), 'LC_ALL': os.environ.get('LC_ALL')}))",
                    ],
                    cwd=root,
                    env=dict(os.environ),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                observed = json.loads(process.stdout)
                self.assertEqual(
                    [str(Path(observed[key]).resolve()) for key in ("cwd", "HOME")],
                    [str(root.resolve()), str((root / "home").resolve())],
                )
                self.assertEqual(
                    (observed["TZ"], observed["LANG"], observed["LC_ALL"]), ("UTC", "C", "C")
                )
            finally:
                os.environ.clear()
                os.environ.update(original_env)
                os.chdir(original_cwd)

    def test_patched_socket_window_drives_continue_parent(self):
        # The network guard must intersect the code under test, not stand
        # beside it: continue_parent runs to completion across a window where
        # any socket construction is denied (an attempted connection would
        # raise and fail this test), and the policy-level network guard fires
        # on a real guarded call inside the same window.
        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(
                task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker"
            )
        )
        driver = self.driver(adapter=adapter, seed_task3=False)
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network disabled")):
            guarded = driver.authorize_action("network")
            outcome = driver.continue_parent()
        self.assertEqual(guarded["status"], "blocked")
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-4"]["status"], "done-pending")


if __name__ == "__main__":
    unittest.main()
