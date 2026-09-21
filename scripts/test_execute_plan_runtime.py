#!/usr/bin/env python3
"""Hermetic tests for the durable execute-plan runtime driver."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from datetime import datetime, timezone
from unittest import mock
from pathlib import Path

import execute_plan_address_fanout as fanout
import execute_plan_runtime as runtime
import validate_review_staging as vrs
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
        # Hermetic git: neutralize host global/system config so hooks,
        # gpgsign, or aliases from the developer machine cannot leak into
        # the fixture repository; identity is set repo-locally below.
        self._git_env = dict(os.environ)
        self._git_env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        self._git_env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=self.root, check=True, env=self._git_env)
        (self.root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True, env=self._git_env)
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            [
                {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
                {"id": "task-4", "number": 4, "status": "pending", "checkbox": False, "allowed_paths": ["task-4.txt"]},
            ],
        )

    def _git(self, *args, cwd=None):
        # Hermetic git subprocess for fixture sites: the pinned _git_env
        # neutralizes host global/system config, and the asserted exit keeps
        # fixture setup failures loud. Returns the CompletedProcess.
        return subprocess.run(["git", *args], cwd=cwd or self.root, env=self._git_env, capture_output=True, text=True, check=True)

    def _git_stdout(self, *args, cwd=None):
        # Stripped-stdout form of the hermetic git helper for fixture assertions.
        completed = self._git(*args, cwd=cwd)
        return completed.stdout.strip()

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
        subprocess.run(["git", "add", name], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "commit", "-qm", f"fixture commit {name}"], cwd=self.root, check=True, env=self._git_env)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True, env=self._git_env).stdout.strip()

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

    def test_checkpoint_duplicate_short_circuit_requires_progressed_task(self):
        # A stale success record under the checkpoint identity on a task
        # whose durable status is still claimed must produce a real
        # completion write, never a phantom done-pending duplicate with
        # nothing persisted.
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: state["checkpoints"].update({
            "task-4:worker-seed": {"result": {"status": "success"}, "task_id": "task-4"},
        }))
        driver = self.driver()
        landed = driver.record_worker_checkpoint(
            self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-seed")
        )
        self.assertEqual(landed["status"], "success")
        self.assertIs(landed["duplicate"], False)
        self.assertEqual(landed["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")
        self.assertIn("recorded_at", state["checkpoints"]["task-4:worker-seed"])

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

    def test_claimed_launch_refuses_malformed_scalar_without_mutation(self):
        # A malformed launch receipt refuses read-only: the blocked malformed
        # outcome is returned, but the claim is never latched into blocked and
        # no worker-blocked event is appended, so the corrected relaunch or
        # resume proceeds under the live claim. The launch fence writes the
        # live launched state before the adapter window, so the no-mutation
        # witness is that pre-receipt live state (the same semantics the
        # checkpoint-path refusal pins: the refusal itself writes nothing).
        class ScalarAdapter(FakeAdapter):
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                self.launches.append((task["id"], generation, policy_token))
                return None

        adapter = ScalarAdapter()
        result = self.driver(adapter=adapter, seed_task3=False).launch_next_task()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "launched")
        self.assertEqual(state["claims"]["task-4"]["state"], "launched")
        self.assertNotIn("blocked_receipt", state["tasks"]["task-4"])
        self.assertNotIn("worker-blocked", [event.get("event") for event in state.get("history", [])])

    def test_claimed_launch_refuses_malformed_mapping_without_mutation(self):
        # Envelope-shaped failure (empty evidence on an otherwise
        # success-shaped mapping): the same read-only malformed refusal.
        class MalformedAdapter(FakeAdapter):
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                return {"status": "success", "evidence": []}

        result = self.driver(adapter=MalformedAdapter(), seed_task3=False).launch_next_task()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "launched")
        self.assertEqual(state["claims"]["task-4"]["state"], "launched")
        self.assertNotIn("blocked_receipt", state["tasks"]["task-4"])
        self.assertNotIn("worker-blocked", [event.get("event") for event in state.get("history", [])])

    def test_resume_non_mapping_refuses_without_mutation(self):
        # A malformed resume receipt refuses read-only: the seeded
        # receipt-permitting blocked claim keeps its exact durable state
        # (manifest byte-identical), so the corrected re-submission still
        # resumes it under the same token and generation.
        class MalformedResumeAdapter:
            def resume(self, *args, **kwargs):
                return None

        state = runtime.load_manifest(self.state_path)
        state["owner"] = "test-owner"
        state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": True, "session_id": "session-task-4"})
        state["claims"]["task-4"] = {
            "token": "resume-token",
            "generation": 1,
            "owner": "test-owner",
            "state": "blocked",
            "task_id": "task-4",
            "baseline_revision": self._git_stdout("rev-parse", "HEAD"),
            "launch_record": {"baseline_revision": self._git_stdout("rev-parse", "HEAD"), "generation": 1, "launched_at": 111.0},
            "policy_token": {"token": "policy", "repo_root": str(self.root), "allowed_paths": ["task.txt"], "operation_kind": "repository-task", "network": False, "generation": 1},
        }
        runtime._safe_write_json(self.state_path, state)
        seeded = runtime.load_manifest(self.state_path)
        result = self.driver(adapter=MalformedResumeAdapter(), seed_task3=False).resume()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "malformed-result")
        # The resume entrypoint's own outcome-independent bookkeeping writes
        # exactly two fields on EVERY resume() call: the construction/peer
        # stamps peer_resumed_at_epoch and updated_at. The refusal itself
        # writes nothing: the durable claim, task, receipt, checkpoint, and
        # history surfaces stay the seeded ones (the old persist arm failed
        # this pin on its worker-blocked history append and blocked_receipt
        # write).
        after = runtime.load_manifest(self.state_path)
        for stamped in ("peer_resumed_at_epoch", "updated_at"):
            after.pop(stamped, None)
            seeded.pop(stamped, None)
        self.assertEqual(after, seeded)

    def test_operational_launch_failure_still_persists_blocked(self):
        # Guard against over-broad interception: the operational timeout arm
        # manufactures the blocked outcome with explicit resume_allowed: true
        # and must keep latching the claim blocked through the persist arm.
        class TimeoutAdapter(FakeAdapter):
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                raise TimeoutError("deadline exceeded")

        result = self.driver(adapter=TimeoutAdapter(), seed_task3=False).launch_next_task()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "timeout")
        self.assertTrue(result["resume_allowed"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")
        self.assertTrue(state["tasks"]["task-4"]["resume_allowed"])
        self.assertEqual(state["tasks"]["task-4"]["blocked_receipt"]["reason_code"], "timeout")
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")
        self.assertIn("worker-blocked", [event.get("event") for event in state.get("history", [])])

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
        baseline = self._git_stdout("rev-parse", "HEAD")
        self.seed_claim(task="task-4", token="scope-token")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["policy_token"] = {"token": "policy", "repo_root": str(self.root), "allowed_paths": ["allowed.txt"], "operation_kind": "repository-task", "network": False, "generation": 0}
        state["claims"]["task-4"]["baseline_revision"] = baseline
        state["claims"]["task-4"]["launch_record"] = {"baseline_revision": baseline, "generation": 0, "launched_at": 111.0}
        runtime._safe_write_json(self.state_path, state)
        (self.root / "outside.txt").write_text("worker escaped scope\n", encoding="utf-8")
        self._git("add", "-N", "outside.txt")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "blocked")

    def _scope_claim(self, allowed):
        baseline = self._git_stdout("rev-parse", "HEAD")
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
        tree = self._git_stdout("rev-parse", "HEAD^{tree}")
        orphan = self._git_stdout("commit-tree", "-m", "orphan", tree)
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
        self._git("add", "link.txt")
        self._git("commit", "-qm", "committed symlink escape")
        commit = self._git_stdout("rev-parse", "HEAD")
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

    def test_post_claim_ambient_noise_downgrades_to_resumable_cleanup(self):
        # Ambient noise appearing after the claim's launch record is
        # host-generated and can never be a worker scope escape; when every
        # out-of-scope path is ambient-shaped the checkpoint witness
        # downgrades to the resumable cleanup-required envelope instead of
        # the terminal contract violation that hard-wedged the task.
        self._launched_claim(allowed=("task-4.txt",))
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        result = self.driver().record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "cleanup-required")
        self.assertTrue(result["resume_allowed"])
        self.assertIn(".DS_Store", result["evidence"][0])
        # The claim stays live: cleanup of the ambient file and a re-checkpoint
        # is the unwedge path (no relaunch, no terminal contract violation).
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-4"]["state"], "launched")

    def test_post_launch_mixed_ambient_and_escape_keeps_hard_block(self):
        # Hard arm: any non-ambient out-of-scope path next to the
        # ambient noise keeps the terminal contract violation.
        self._launched_claim(allowed=("task-4.txt",))
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        (self.root / "outside-policy.txt").write_text("worker escape\n", encoding="utf-8")
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

    def test_post_launch_tracked_ambient_name_stays_violation(self):
        # The ambient downgrade requires the porcelain-proven
        # untracked arm, not the name shape alone. A tracked out-of-scope
        # modification wearing an ambient name (.DS_Store) can carry
        # arbitrary worker content, so it keeps the terminal
        # contract-violation instead of the resumable cleanup envelope the
        # untracked arm gets (pinned by
        # test_post_claim_ambient_noise_downgrades_to_resumable_cleanup).
        self._launched_claim(allowed=("task-4.txt",))
        self.commit_file(".DS_Store", content="arbitrary content\n")
        driver = self.driver()
        result = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", generation=0))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "contract-violation")
        self.assertFalse(result["resume_allowed"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")

    def _prelaunch_claim(self, task="task-4"):
        state = runtime.load_manifest(self.state_path)
        state["claims"][task] = {"token": "pre-dirty-token", "generation": 0, "owner": "test-owner", "state": "claimed", "task_id": task}
        state["tasks"][task]["status"] = "claimed"
        runtime._safe_write_json(self.state_path, state)

    def test_startup_ambient_noise_is_resumable_cleanup_required(self):
        self._prelaunch_claim()
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        (self.root / ".DS_Store?").write_text("ambient\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "._.DS_Store").write_text("ambient\n", encoding="utf-8")
        driver = self.driver()
        startup = driver.reconcile_startup()
        self.assertEqual(startup["status"], "blocked")
        self.assertEqual(startup["reason_code"], "cleanup-required")
        self.assertTrue(startup["resume_allowed"])
        continued = driver.continue_parent()
        self.assertEqual(continued["reason_code"], "cleanup-required")
        self.assertTrue(continued["resume_allowed"])

        # Anything outside the allowlist keeps the hard dirty-worktree block,
        # and its evidence names the offending entry so the operator can
        # reconcile it explicitly.
        (docs / ".#notes.md").write_text("editor swap\n", encoding="utf-8")
        hard = driver.reconcile_startup()
        self.assertEqual(hard["reason_code"], "dirty-worktree")
        self.assertFalse(hard["resume_allowed"])
        self.assertIn("?? docs/.#notes.md", " ".join(hard["evidence"]))

        # Tracked modifications are never ambient noise on the same path.
        (docs / ".#notes.md").unlink()
        (self.root / ".DS_Store").unlink()
        (self.root / ".DS_Store?").unlink()
        (docs / "._.DS_Store").unlink()
        gitignore = self.root / ".gitignore"
        gitignore.write_text(gitignore.read_text(encoding="utf-8") + "# touched\n", encoding="utf-8")
        tracked = driver.reconcile_startup()
        self.assertEqual(tracked["reason_code"], "dirty-worktree")
        self.assertFalse(tracked["resume_allowed"])

    def test_startup_ambient_evidence_sanitizes_control_bytes(self):
        # The resumable cleanup-required evidence passes through the same
        # presentation sanitizer as the hard dirty-worktree block: a
        # control-byte directory name renders as its escaped form and the
        # raw ESC byte never reaches the evidence, while the classification
        # stays ambient (resumable cleanup-required, not a hard violation).
        self._prelaunch_claim()
        noisy = self.root / "we\x1bird dir"
        noisy.mkdir()
        (noisy / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        driver = self.driver()
        startup = driver.reconcile_startup()
        self.assertEqual(startup["status"], "blocked")
        self.assertEqual(startup["reason_code"], "cleanup-required")
        self.assertTrue(startup["resume_allowed"])
        evidence = " ".join(startup["evidence"])
        self.assertIn("?? we\\x1bird dir/.DS_Store", evidence)
        self.assertNotIn("\x1b", evidence)

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
        self.write_archived_plan(self.CHECKED_ARCHIVED_PLAN)
        self.seed_archive_gate()
        terminal = self.driver(adapter=adapter).mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
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
            self._git("init", "-q", cwd=root)
            self._git("config", "user.email", "test@example.invalid", cwd=root)
            self._git("config", "user.name", "Runtime Test", cwd=root)
            marker = root / "tracked.txt"
            marker.write_text("base\n", encoding="utf-8")
            self._git("add", "tracked.txt", cwd=root)
            self._git("commit", "-qm", "base", cwd=root)
            commit = self._git_stdout("rev-parse", "HEAD", cwd=root)
            # The manifest stays outside the fixture git repo so the
            # clean-worktree witness stays inert, but the name carries a uuid
            # suffix (the sibling fixtures' pattern) so concurrent suite
            # instances never clobber one shared fixed name in the parent of
            # the per-test temp dir; cleanups unlink the manifest and its
            # .lock sibling so no per-run litter survives in the shared dir.
            state_path = root.parent / f"runtime_state-{uuid.uuid4().hex[:8]}.json"
            self.addCleanup(state_path.unlink, missing_ok=True)
            self.addCleanup(Path(str(state_path) + ".lock").unlink, missing_ok=True)
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

    def test_reconcile_startup_survives_unicode_decode_on_dirty_probe(self):
        # Natural-path site 1: the pre-launch dirty probe itself hits a
        # filename byte invalid in the locale encoding; the fail-closed
        # witness outcome must replace the escaping exception.
        driver = self.driver()
        self.seed_claim(task="task-3")
        with mock.patch.object(driver, "_git_worktree_dirty", side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")):
            result = driver.reconcile_startup()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "worktree-witness-unavailable")
        self.assertFalse(result["resume_allowed"])

    def test_reconcile_startup_survives_unicode_decode_on_ambient_enumeration(self):
        # Natural-path site 2: dirt is witnessed, then the ambient
        # classification enumeration raises on an undecodable filename;
        # the same fail-closed witness outcome applies.
        driver = self.driver()
        self.seed_claim(task="task-3")
        with mock.patch.object(driver, "_git_worktree_dirty", return_value=True), \
                mock.patch.object(driver, "_git_worktree_entries", side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")):
            result = driver.reconcile_startup()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "worktree-witness-unavailable")
        self.assertFalse(result["resume_allowed"])

    def test_startup_dirty_witness_failure_degrades_evidence_not_block(self):
        # Degrade-direction witness (sibling of the git-witness failure test):
        # with the dirt already witnessed, a failing entry enumeration keeps
        # the hard dirty-worktree block and degrades the evidence to the bare
        # reconciliation line; the block itself never softens.
        self._prelaunch_claim()
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        driver = self.driver()
        with mock.patch.object(driver, "_git_worktree_entries", side_effect=RuntimeError("status failed")):
            result = driver.reconcile_startup(dirty_worktree=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "dirty-worktree")
        self.assertFalse(result["resume_allowed"])
        self.assertEqual(result["evidence"], ["uncommitted worktree requires explicit reconciliation"])

    def test_startup_dirty_evidence_truncates_with_tail(self):
        # r3 truncation witness: a 22-entry dirt set keeps the bare
        # reconciliation line plus the first 20 entries and delivers the
        # "... and 2 more entries" tail. The fill-in enumeration arm (the
        # injected dirty_worktree path) feeds the evidence. One entry
        # carries a control byte so the same witness pins the sanitizer:
        # the escaped rendering appears in evidence and the raw ESC byte
        # never does.
        self._prelaunch_claim()
        driver = self.driver()
        entries = [("??", f"f{i}.txt") for i in range(22)]
        entries[5] = ("??", "esc\x1b[31m.txt")
        with mock.patch.object(driver, "_git_worktree_entries", return_value=entries):
            result = driver.reconcile_startup(dirty_worktree=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "dirty-worktree")
        self.assertEqual(
            result["evidence"],
            ["uncommitted worktree requires explicit reconciliation"]
            + [f"?? f{i}.txt" for i in range(5)]
            + ["?? esc\\x1b[31m.txt"]
            + [f"?? f{i}.txt" for i in range(6, 20)]
            + ["... and 2 more entries"],
        )
        joined = " ".join(result["evidence"])
        self.assertIn("?? esc\\x1b[31m.txt", joined)
        self.assertNotIn("\x1b", joined)

    def test_cli_drives_claim_checkpoint_done_and_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git("init", "-q", cwd=root)
            self._git("config", "user.email", "test@example.invalid", cwd=root)
            self._git("config", "user.name", "Runtime Test", cwd=root)
            (root / "tracked.txt").write_text("base\n", encoding="utf-8")
            self._git("add", "tracked.txt", cwd=root)
            self._git("commit", "-qm", "base", cwd=root)
            commit = self._git_stdout("rev-parse", "HEAD", cwd=root)
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
            archived = root / "docs/plans/completed/cli-plan.md"
            archived.parent.mkdir(parents=True, exist_ok=True)
            archived.write_text("# cli plan\n\n### Task 1: first\n\n- [x] task-1\n", encoding="utf-8")
            # The final stage requires the pre-archive gate receipt: seed a
            # conforming one (declared destination equal to the archived CLI
            # path, digest over the archived bytes, source pointing at the
            # absent active path), mirroring seed_archive_gate semantics for
            # this CLI-driven fixture root.
            state = runtime.load_manifest(state_path)
            state["archive_gate"] = {
                "plan_path": "docs/plans/cli-plan.md",
                "declared_destination": "docs/plans/completed/cli-plan.md",
                "plan_digest": hashlib.sha256(archived.read_bytes()).hexdigest(),
                "last_commit_sha": commit,
                "phase5_checklist": ["tests"],
                "recorded_at": 1234.0,
            }
            runtime._safe_write_json(state_path, state)
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

    def test_create_operation_refuses_empty_task_list(self):
        # A zero-task manifest is never seeded: every later claim would
        # answer a silent success no-op while readiness and terminal refuse
        # the empty run, so create fails closed naming the missing tasks and
        # writes no manifest file.
        created_path = self.root / "created_empty.json"
        for empty in ([], {}):
            command = [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(created_path),
                "--repo-root", str(self.root),
                "--owner", "create-owner",
                "--plan-slug", "empty-plan",
                "--operation", "create",
                "--input", json.dumps({"tasks": empty}),
            ]
            with self.subTest(shape=type(empty).__name__):
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("create operation requires at least one task", completed.stderr)
                self.assertFalse(created_path.exists())

    def test_create_manifest_refuses_empty_task_list(self):
        # Library-level wedge guard: the CLI refusal alone left
        # create_manifest seeding the zero-task wedge for library callers,
        # so the seeding boundary itself now raises before writing any
        # manifest file.
        created_path = self.root / "created_empty_library.json"
        for empty in ([], {}):
            with self.subTest(shape=type(empty).__name__):
                with self.assertRaises(ValueError) as raised:
                    runtime.create_manifest(created_path, "empty-plan", empty)
                self.assertIn("create requires at least one task", str(raised.exception))
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
        self.write_archived_plan(self.CHECKED_ARCHIVED_PLAN)
        self.seed_archive_gate()
        driver.mark_terminal("docs/plans/completed/fixture-plan.md", "abcdef1", ["tests"])
        terminal = driver.terminal_result()
        self.assertEqual(terminal["status"], "success")
        self.assertEqual(terminal["workflow_state"], "complete")
        self.assertIn("phase5_checklist", terminal)
        self.assertIn("archived_plan_path", terminal)

    CHECKED_ARCHIVED_PLAN = "# fixture plan\n\n### Task 3: third\n### Task 4: fourth\n\n- [x] task-3\n- [x] task-4\n"
    ARCHIVED_PLAN_REL = "docs/plans/completed/fixture-plan.md"

    def complete_all_tasks(self) -> None:
        state = runtime.load_manifest(self.state_path)
        for task in state["tasks"].values():
            task.update({"status": "complete", "checkbox": True})
        runtime._safe_write_json(self.state_path, state)

    def write_archived_plan(self, text: str, rel: str = ARCHIVED_PLAN_REL) -> str:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return rel

    def seed_archive_gate(self, archived_rel: str = ARCHIVED_PLAN_REL, source_rel: str = "docs/plans/fixture-plan.md", commit: str = "abcdef1") -> str:
        """Seed a conforming ``archive_gate`` receipt for the final-stage fixtures.

        Conforming means: the declared destination equals the archived
        fixture path, the digest covers the archived bytes when the file
        exists (the canonical checked text otherwise, so the
        missing-archived-plan fixture still exercises the bounded-read
        refusal after the gate clauses pass), and the recorded source path
        points at the absent active path. Every final-stage ``mark_terminal``
        fixture seeds it before the call.
        """

        archived = self.root / archived_rel
        payload = archived.read_bytes() if archived.is_file() else self.CHECKED_ARCHIVED_PLAN.encode("utf-8")
        state = runtime.load_manifest(self.state_path)
        state["archive_gate"] = {
            "plan_path": source_rel,
            "declared_destination": archived_rel,
            "plan_digest": hashlib.sha256(payload).hexdigest(),
            "last_commit_sha": commit,
            "phase5_checklist": ["tests"],
            "recorded_at": 1234.0,
        }
        runtime._safe_write_json(self.state_path, state)
        return archived_rel

    def test_terminal_refuses_missing_archived_plan(self):
        # Under the staged final stage the conforming gate receipt is seeded
        # first, so the gate clauses (presence, exact destination, source
        # absence, digest) pass and the refusal is today's bounded-read
        # evidence for a missing path (the shared helper's exists gate):
        # without it the test cannot distinguish the missing-file refusal
        # from the over-limit or non-regular-file refusals.
        self.complete_all_tasks()
        self.seed_archive_gate()
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(
            any("archived plan is missing or unreadable" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        self.assertFalse(any("is not readable" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("exceeds the bounded read limit" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_refuses_empty_archived_plan(self):
        # A zero-byte archived plan makes the unchecked-checkbox predicate
        # vacuously true: the terminal gate refuses the empty
        # artifact instead of writing a receipt for it, and the manifest
        # stays non-terminal.
        self.complete_all_tasks()
        self.write_archived_plan("")
        self.seed_archive_gate()
        self.assertEqual((self.root / self.ARCHIVED_PLAN_REL).stat().st_size, 0)
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("archived plan is empty" in entry for entry in result["evidence"]), result["evidence"])
        # The empty refusal fires before the checkbox scan: no vacuous
        # zero-unchecked pass evidence may appear.
        self.assertFalse(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_refuses_whitespace_only_archived_plan(self):
        # Whitespace-only bytes are the empty artifact for the gate: the
        # emptiness predicate is strip-based (not plan_text.strip()), so a
        # plan of only spaces, tabs, and newlines is refused exactly like
        # the zero-byte plan (the unchecked-checkbox predicate would be
        # vacuously true over it). RED before the strip-based widening: the
        # truthy whitespace text used to pass the terminal gate.
        self.complete_all_tasks()
        self.write_archived_plan("   \n\t\n")
        self.seed_archive_gate()
        self.assertGreater((self.root / self.ARCHIVED_PLAN_REL).stat().st_size, 0)
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("archived plan is empty" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_refuses_archived_plan_without_task_sections(self):
        # At-least-one-task-heading requirement (mirroring the readiness
        # shape guard): a non-empty archived plan with zero recognizable
        # '### Task <N>:' headings makes the per-section scans vacuous and
        # proves the wrong file was archived, so the terminal gate refuses
        # it naming the missing task sections. RED before this task: the
        # sectionless plan used to pass the terminal gate.
        self.complete_all_tasks()
        self.write_archived_plan("# fixture plan\n\n- [x] all items\n\nNo task sections here.\n")
        self.seed_archive_gate()
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(
            any("archived plan carries no recognizable task sections" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        self.assertFalse(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_refuses_unchecked_plan_checkboxes(self):
        self.complete_all_tasks()
        self.write_archived_plan("# fixture plan\n### Task 4: fourth\n- [x] task-3\n- [ ] task-4\n")
        self.seed_archive_gate()
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("checkbox" in entry for entry in result["evidence"]), result["evidence"])
        # The evidence line number is computed during the scan: the first
        # unchecked line of this plan is line 4.
        self.assertTrue(any(entry.startswith("line 4:") for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_ignores_inline_checkbox_literals(self):
        self.complete_all_tasks()
        self.write_archived_plan(
            "# fixture plan\n\n### Task 3: third\n\nProse mentions the `- [ ]` marker mid-line and even a bare - [ ] fragment after words, "
            "but no line starts with an unchecked checkbox token.\n- [x] task-3\n- [x] task-4\n"
        )
        self.seed_archive_gate()
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(runtime.load_manifest(self.state_path)["workflow_state"], "complete")

    def test_terminal_refuses_unprovable_commit(self):
        self.complete_all_tasks()
        self.write_archived_plan(self.CHECKED_ARCHIVED_PLAN)
        self.seed_archive_gate()
        result = self.driver(commit_lookup=lambda _commit: False).mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("commit" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_accepts_verified_receipt(self):
        self.complete_all_tasks()
        rel = self.write_archived_plan(self.CHECKED_ARCHIVED_PLAN)
        self.seed_archive_gate(archived_rel=rel)
        result = self.driver().mark_terminal(rel, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "success")
        receipt = self.driver().terminal_result()
        self.assertEqual(receipt["workflow_state"], "complete")
        self.assertEqual(receipt["phase5_checklist"], ["tests"])
        self.assertEqual(receipt["archived_plan_path"], rel)
        self.assertEqual(receipt["last_commit_sha"], "abcdef1")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["workflow_state"], "complete")
        self.assertEqual(state["terminal_receipt"]["workflow_state"], "complete")

    def test_terminal_refuses_archived_plan_over_read_limit(self):
        # The terminal gate reads the archived plan under the shared bounded
        # read (open + read(LIMIT + 1), no stat size gate): a
        # plan whose read proves it over PLAN_READ_LIMIT is refused
        # outright (blocked done-pending) instead of scanning only its first
        # PLAN_READ_LIMIT bytes, so an unchecked line past the
        # bound can never slip through a prefix scan (the
        # previous prefix-scan acceptance here was fail-open on the gate's
        # core promise).
        self.complete_all_tasks()
        filler = "- [x] filler line\n" * 60_000  # 18-byte lines: 1,080,000 bytes
        self.write_archived_plan(filler + "- [ ] past the bounded prefix\n")
        self.seed_archive_gate()
        self.assertGreater(
            (self.root / self.ARCHIVED_PLAN_REL).stat().st_size,
            runtime.PLAN_READ_LIMIT,
        )
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        # The exact read-cap fragment: without it this refusal is
        # indistinguishable from the unreadable-file fallback.
        self.assertTrue(
            any("archived plan exceeds the bounded read limit" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_bounded_read_prefix_unchecked_still_blocks(self):
        # Mirror arm: the same over-limit shape with the unchecked line
        # inside what would have been the scanned prefix still refuses
        # terminal, and the evidence names the read cap rather than the
        # checkbox count: the bounded read refuses an over-limit plan
        # before any scan, so the terminal gate never prefix-scans an
        # over-limit plan (a reverted prefix-scan implementation would emit
        # the checkbox evidence instead).
        self.complete_all_tasks()
        filler = "- [x] filler line\n" * 60_000
        self.write_archived_plan("- [ ] inside the bounded prefix\n" + filler)
        self.seed_archive_gate()
        self.assertGreater(
            (self.root / self.ARCHIVED_PLAN_REL).stat().st_size,
            runtime.PLAN_READ_LIMIT,
        )
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("archived plan exceeds the bounded read limit" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_read_limit_boundary_pair_terminal(self):
        # Regression pin (classification already correct today): an archived
        # plan of exactly PLAN_READ_LIMIT bytes passes the
        # bounded-read gate (the +1-byte read window admits it whole, so the
        # terminal gate reaches the success receipt) while limit+1 is
        # refused with the over-limit evidence. A boundary drift in either
        # direction flips one arm.
        header = "# fixture plan\n\n### Task 4: fourth\n\n"
        for size, expect_success in ((runtime.PLAN_READ_LIMIT, True), (runtime.PLAN_READ_LIMIT + 1, False)):
            with self.subTest(size=size):
                self.complete_all_tasks()
                # Each arm starts from a non-terminal manifest: the accepted
                # arm writes a terminal receipt and workflow_state complete,
                # and that residue would leak into the refused arm's
                # non-terminal byte-identity assertions.
                self.rewrite_manifest(lambda state: (
                    state.pop("terminal_receipt", None),
                    state.__setitem__("workflow_state", "active"),
                ))
                text = header + "x" * (size - len(header))
                self.assertEqual(len(text.encode("utf-8")), size)
                rel = self.write_archived_plan(text, rel=f"docs/plans/completed/boundary-{size}.md")
                self.seed_archive_gate(archived_rel=rel)
                result = self.driver().mark_terminal(rel, "abcdef1", ["tests"])
                if expect_success:
                    self.assertEqual(result["status"], "success")
                    self.assertFalse(any("exceeds the bounded read limit" in entry for entry in result["evidence"]), result["evidence"])
                    self.assertEqual(runtime.load_manifest(self.state_path)["workflow_state"], "complete")
                else:
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "done-pending")
                    self.assertTrue(any("exceeds the bounded read limit" in entry for entry in result["evidence"]), result["evidence"])
                    state = runtime.load_manifest(self.state_path)
                    self.assertNotIn("terminal_receipt", state)
                    self.assertEqual(state["workflow_state"], "active")

    def test_terminal_refuses_empty_manifest(self):
        # A manifest with no tasks makes the completeness guard vacuously
        # true: the terminal gate refuses the empty run explicitly instead of
        # writing a terminal receipt for it. With the gate receipt seeded,
        # this fixture pins that the empty-manifest evidence still wins; the
        # dedicated completeness-before-gate ordering pin is
        # test_incomplete_gateless_manifest_refuses_on_completeness_before_gate
        # (the incomplete AND gateless fixture).
        self.rewrite_manifest(lambda state: state.update({"tasks": {}, "claims": {}}))
        self.write_archived_plan(self.CHECKED_ARCHIVED_PLAN)
        self.seed_archive_gate()
        result = self.driver().mark_terminal(self.ARCHIVED_PLAN_REL, "abcdef1", ["tests"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("manifest carries no tasks" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

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
                    self._git("init", "-q", cwd=root)
                    self._git("config", "user.email", "test@example.invalid", cwd=root)
                    self._git("config", "user.name", "Runtime Test", cwd=root)
                    (root / "seed.txt").write_text("base\n", encoding="utf-8")
                    self._git("add", "seed.txt", cwd=root)
                    self._git("commit", "-qm", "base", cwd=root)
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
        baseline = self._git_stdout("rev-parse", "HEAD")
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
        baseline = self._git_stdout("rev-parse", "HEAD")
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
        # RuntimeError, and a mapping return without claim_token (backfilled
        # by the driver before the recursive checkpoint).
        arms = [
            ("timeout", TimeoutError("deadline exceeded"), "timeout", "blocked", True),
            ("type-error", TypeError("policy token rejected"), "runtime-policy-unavailable", "blocked", False),
            ("runtime-error", RuntimeError("boom"), "runtime-error", "error", False),
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

        # Non-mapping relaunch arm: the manufactured malformed-result receipt
        # re-enters the checkpoint path, where the read-only interception
        # refuses it without mutation (the claim stays launched, no blocked
        # receipt is persisted); the failed attempt's ordinal record from the
        # retry itself stays in place, and the reason is never owner-mismatch.
        # This arm runs FIRST: the refusal writes nothing, so a later
        # position would expose the persisting arms' blocked_receipt residue
        # on the shared task record (seed_claim re-seeds the claim and the
        # checkpoint records, not the task record).
        with self.subTest(arm="non-mapping"):
            self.seed_claim(task="task-4", token="seed-task-4")
            driver = self.driver(adapter=FakeAdapter(arm_launch("not-a-mapping-result")), seed_task3=False)
            result = driver.record_worker_checkpoint({**failure_receipt, "claim_token": "seed-task-4"})
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason_code"], "malformed-result")
            self.assertNotEqual(result["reason_code"], "owner-mismatch")
            self.assertFalse(result["resume_allowed"])
            state = runtime.load_manifest(self.state_path)
            self.assertIn("task-4:worker#attempt-1", state["checkpoints"])
            self.assertEqual(state["tasks"]["task-4"]["status"], "launched")
            self.assertNotIn("blocked_receipt", state["tasks"]["task-4"])

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
        baseline = self._git_stdout("rev-parse", "HEAD")
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

    def test_success_checkpoint_refuses_aborted_workflow(self):
        # F-r5-1 witness (a): a late success checkpoint on an aborted
        # workflow is the explicit-abort envelope with no persist; the
        # manifest is byte-identical before and after the receipt.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        state = runtime.load_manifest(self.state_path)
        # Simulate an abort that landed elsewhere while this claim stayed
        # live: only the workflow state flips, never the claim or the task.
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = runtime.load_manifest(self.state_path)
        outcome = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertEqual(after["workflow_state"], "aborted")
        self.assertNotIn("task-4:worker-1", after["checkpoints"])
        self.assertEqual(after, before)
        # Duplicate-ordering arm: land the identical receipt while the
        # workflow is active, flip aborted, then replay it; the fence
        # precedes the duplicate short-circuit, so the replay is the
        # explicit-abort envelope, never the idempotent duplicate success,
        # and the manifest stays byte-identical.
        state["workflow_state"] = "active"
        runtime._safe_write_json(self.state_path, state)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        landed_state = runtime.load_manifest(self.state_path)
        self.assertEqual(landed_state["tasks"]["task-4"]["status"], "done-pending")
        landed_state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, landed_state)
        before = runtime.load_manifest(self.state_path)
        replay = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(replay["status"], "aborted")
        self.assertEqual(replay["reason_code"], "explicit-abort")
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_done_handoff_refuses_aborted_workflow(self):
        # F-r5-1 witness (b): the done handoff on an aborted workflow is the
        # explicit-abort envelope; no completion write lands.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = runtime.load_manifest(self.state_path)
        outcome = driver.record_done(self.done(task="task-4"))
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertNotIn("commit_identity", after["tasks"]["task-4"])
        self.assertFalse(after["tasks"]["task-4"].get("checkbox"))
        self.assertEqual(after, before)
        # Commit-lookup ordering arm: the aborted fence sits before the
        # commit lookup. With a driver whose commit lookup cannot find any
        # commit, the same landed done-pending task against the aborted
        # workflow still surfaces the explicit-abort envelope, never the
        # commit-pending block, and the manifest stays byte-identical.
        lookup_driver = self.driver(seed_task3=False, commit_lookup=lambda _c: False)
        before = runtime.load_manifest(self.state_path)
        outcome = lookup_driver.record_done(self.done(task="task-4"))
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
        self.assertEqual(runtime.load_manifest(self.state_path), before)
        # Duplicate-ordering arm: land the done handoff while the workflow
        # is active, flip aborted, then replay the identical handoff; the
        # fence sits before the duplicate short-circuit, so the replay is
        # the explicit-abort envelope, never the idempotent duplicate
        # success, and the manifest stays byte-identical.
        state["workflow_state"] = "active"
        runtime._safe_write_json(self.state_path, state)
        completed = driver.record_done(self.done(task="task-4"))
        self.assertEqual(completed["status"], "success")
        completed_state = runtime.load_manifest(self.state_path)
        self.assertEqual(completed_state["tasks"]["task-4"]["status"], "checkpointed")
        completed_state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, completed_state)
        before = runtime.load_manifest(self.state_path)
        replay = driver.record_done(self.done(task="task-4"))
        self.assertEqual(replay["status"], "aborted")
        self.assertEqual(replay["reason_code"], "explicit-abort")
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_commit_reconciliation_refuses_aborted_workflow(self):
        # F-r5-1 witness (c): commit reconciliation on an aborted workflow is
        # the explicit-abort envelope; no reconciliation write lands.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = runtime.load_manifest(self.state_path)
        outcome = driver.reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="seed-task-4", generation=0)
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        self.assertFalse(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "commit-pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertNotIn("task-4:commit", after["checkpoints"])
        self.assertEqual(after, before)
        # A replayed identical reconciliation after the abort keeps surfacing
        # the explicit-abort envelope; the manifest stays byte-identical.
        replay = driver.reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="seed-task-4", generation=0)
        self.assertEqual(replay["status"], "aborted")
        self.assertEqual(replay["reason_code"], "explicit-abort")
        self.assertEqual(runtime.load_manifest(self.state_path), before)
        # Duplicate-ordering pin: once the reconciliation has landed (the task
        # is checkpointed with the matching commit identity), a replay on the
        # aborted workflow returns the explicit-abort envelope, never the
        # idempotent duplicate success; the manifest stays byte-identical.
        state["workflow_state"] = "active"
        runtime._safe_write_json(self.state_path, state)
        landed = driver.reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="seed-task-4", generation=0)
        self.assertEqual(landed["status"], "success")
        landed_state = runtime.load_manifest(self.state_path)
        self.assertEqual(landed_state["tasks"]["task-4"]["status"], "checkpointed")
        landed_state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, landed_state)
        before = runtime.load_manifest(self.state_path)
        duplicate = driver.reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="seed-task-4", generation=0)
        self.assertEqual(duplicate["status"], "aborted")
        self.assertEqual(duplicate["reason_code"], "explicit-abort")
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_commit_reconciliation_foreign_token_keeps_owner_mismatch_before_fence(self):
        # r3 identity-before-fence witness (a): on an aborted workflow, a
        # reconciliation receipt carrying a foreign claim token fails the
        # identity check first and surfaces owner-mismatch, never the
        # explicit-abort fence; the manifest stays byte-identical.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = self.state_path.read_bytes()
        outcome = driver.reconcile_commit_before_checkpoint("task-4", "aa11bb22cc33", lambda _c: True, claim_token="wrong-token", generation=0)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "owner-mismatch")
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_success_checkpoint_foreign_token_keeps_owner_mismatch_before_fence(self):
        # r3 identity-before-fence witness (b): on an aborted workflow, a
        # success checkpoint with a foreign claim token fails the identity
        # check first (owner-mismatch), never the explicit-abort fence, and
        # nothing persists.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = self.state_path.read_bytes()
        outcome = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1", claim_token="wrong-token"))
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "owner-mismatch")
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_done_handoff_foreign_token_keeps_unfenced_block_before_fence(self):
        # r3 identity-before-fence witness (c): on an aborted workflow, a
        # done handoff with a foreign claim token fails the fence predicate
        # first and surfaces the missing-or-unfenced done evidence block,
        # never the explicit-abort envelope; nothing persists.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "aborted"
        runtime._safe_write_json(self.state_path, state)
        before = self.state_path.read_bytes()
        outcome = driver.record_done(self.done(task="task-4", claim_token="wrong-token"))
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "done-pending")
        self.assertIn("missing or unfenced done evidence", outcome["evidence"][0])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_abort_exits_wedged_commit_pending_claim(self):
        # F-r5-2 witness (a): a commit-pending claim whose recorded commit
        # provably does not exist is wedged (crash between the commit-pending
        # write and the commit itself); abort with the still-current token is
        # the preserve-and-stop runtime exit.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=lambda _commit: False)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "aborted")
        self.assertEqual(after["claims"]["task-4"]["state"], "aborted")
        self.assertEqual(after["workflow_state"], "aborted")

    def test_abort_exits_wedged_commit_pending_with_missing_identity(self):
        # Wedge-edge witness: a hand-corrupted commit-pending task whose
        # commit_identity field is missing routes through the wedge path too
        # (an empty identity fails the commit lookup, so the task is
        # unreconcilable), and the explicit stop with the still-current token
        # remains the runtime exit for task, claim, and workflow.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=lambda commit: bool(commit))
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].pop("commit_identity")
        runtime._safe_write_json(self.state_path, state)
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "aborted")
        self.assertEqual(after["claims"]["task-4"]["state"], "aborted")
        self.assertEqual(after["workflow_state"], "aborted")

    def test_abort_still_refuses_commit_pending_with_provable_commit(self):
        # F-r5-2 witness (b): when the recorded commit provably exists the
        # r4 progression refusal stands; the wedge exception is the only
        # unlock and the durable state stays untouched.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=lambda _commit: True)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "commit-pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertEqual(after["workflow_state"], "active")

    def test_abort_still_refuses_wedged_shaped_closed_claim(self):
        # Wedge-boundary witness: the wedge exception requires a live
        # (non-closed) claim. A hand-corrupted closed claim on a
        # commit-pending task with a missing commit_identity is wedged-shaped
        # but keeps the r4 progression refusal, and the durable state stays
        # untouched.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=lambda commit: bool(commit))
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["state"] = "closed"
        state["tasks"]["task-4"].pop("commit_identity")
        runtime._safe_write_json(self.state_path, state)
        before = runtime.load_manifest(self.state_path)
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["claims"]["task-4"]["state"], "closed")
        self.assertEqual(after["tasks"]["task-4"]["status"], "commit-pending")
        self.assertEqual(after["workflow_state"], "active")
        self.assertEqual(after, before)

    def test_abort_wedge_witness_failure_keeps_progression_refusal(self):
        # r3 wedge-degrade witness: when the commit witness raises, the
        # wedge exception degrades to not-wedged and the r4 progression
        # refusal stands; abort surfaces the resumable stale-claim outcome
        # and the manifest stays byte-identical. Both failure shapes are
        # pinned: RuntimeError from a failing git invocation and OSError
        # from an environment failure (git not found).
        def raising_lookup(_commit):
            raise RuntimeError("status failed")

        def oserror_lookup(_commit):
            raise OSError("git not found")

        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=raising_lookup)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        before = self.state_path.read_bytes()
        outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        self.assertEqual(self.state_path.read_bytes(), before)

        # OSError arm: the same degrade covers the environment-failure
        # shape; the refusal stands and the manifest stays byte-identical.
        degraded_driver = self.driver(seed_task3=False, commit_lookup=oserror_lookup)
        before = self.state_path.read_bytes()
        outcome = degraded_driver.abort("task-4", "seed-task-4")
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_abort_wedge_decision_revalidated_against_fresh_manifest_before_save(self):
        # r3 TOCTOU witness: a competing writer lands the task's completion
        # after abort computed its wedge decision but before its save; the
        # fresh-load re-validation refuses to clobber the completed state
        # and surfaces the resumable stale-claim outcome instead.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, commit_lookup=lambda _commit: False)
        pending = driver.mark_commit_pending("task-4", "aa11bb22cc33", ["done-log:task-4"], claim_token="seed-task-4", generation=0)
        self.assertEqual(pending["status"], "success")
        real_load = runtime.load_manifest
        loads = {"count": 0}

        def interleaved_load(path):
            manifest = real_load(path)
            loads["count"] += 1
            if loads["count"] == 2:
                # The competing writer runs between abort's decision
                # snapshot (first load) and its save: the task completes,
                # the claim closes.
                manifest["tasks"]["task-4"].update({"status": "checkpointed", "checkbox": True, "complete": True, "commit_identity": "aa11bb22cc33"})
                manifest["claims"]["task-4"]["state"] = "closed"
                runtime._safe_write_json(self.state_path, manifest)
            return manifest

        with mock.patch.object(runtime, "load_manifest", side_effect=interleaved_load):
            outcome = driver.abort("task-4", "seed-task-4")
        self.assertEqual(loads["count"], 2)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertTrue(outcome["resume_allowed"])
        self.assertEqual(outcome["evidence"], ["manifest changed during abort; wedge decision stale"])
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "checkpointed")
        self.assertTrue(after["tasks"]["task-4"]["complete"])
        self.assertEqual(after["claims"]["task-4"]["state"], "closed")
        self.assertEqual(after["workflow_state"], "active")

    def test_terminal_task_live_claim_surfaces_actionable_receipt(self):
        # F-r5-3 witness: a non-success receipt for a terminal (checkpointed)
        # task with a live claim surfaces the raw actionable receipt instead
        # of the stale-claim outcome; nothing regressed, so nothing persists.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"]["status"] = "checkpointed"
        state["tasks"]["task-4"]["complete"] = True
        runtime._safe_write_json(self.state_path, state)
        before = runtime.load_manifest(self.state_path)
        outcome = driver.record_worker_checkpoint(
            self.worker_checkpoint(
                task="task-4",
                checkpoint_identity="task-4:worker-1",
                status="approval-required",
                reason_code="approval-required",
                action_scope="external-write:publish",
                evidence=["approval-request:publish"],
            )
        )
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "approval-required")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "checkpointed")
        self.assertEqual(after["claims"]["task-4"]["state"], "launched")
        self.assertFalse(any(event["event"] in {"worker-retry", "worker-blocked"} for event in after["history"]))
        self.assertFalse(any(key.startswith("task-4:worker-1#attempt-") for key in after["checkpoints"]))
        self.assertEqual(after, before)

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
        # malformed resume result is refused read-only (malformed-result,
        # before the persist site) and never regresses the closed,
        # checkpointed task: the refusal writes nothing at all.
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
        self.assertEqual(result["reason_code"], "malformed-result")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "checkpointed")
        self.assertEqual(after["claims"]["task-4"]["state"], "closed")

    def test_claim_progressed_past_receipt_matrix(self):
        # F-r3-8 predicate-level witness: the base statuses (done-pending,
        # commit-pending, aborted, checkpointed, complete) and a closed claim
        # always progress; non-progressed statuses and a None task do not.
        live_claim = {"state": "launched"}
        for status in ("done-pending", "commit-pending", "aborted", "checkpointed", "complete"):
            task = {"status": status}
            self.assertTrue(runtime._claim_progressed_past_receipt(task, live_claim), status)
        for status in ("pending", "claimed", "launched", "blocked"):
            task = {"status": status}
            self.assertFalse(runtime._claim_progressed_past_receipt(task, live_claim), status)
        self.assertFalse(runtime._claim_progressed_past_receipt(None, live_claim))
        self.assertTrue(runtime._claim_progressed_past_receipt({"status": "launched"}, {"state": "closed"}))
        self.assertTrue(runtime._claim_progressed_past_receipt(None, {"state": "closed"}))

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

    def test_startup_routes_by_claim_key_not_task_id_field(self):
        # r3 claim-key routing witness: the claims-dict key, never the
        # claim's task_id field, names the task. A claim keyed "task-4"
        # whose task_id field disagrees ("task-3", a completed task) still
        # routes the dirty-worktree block to the task-4 claim: the outcome
        # carries that claim's own token, not the hoisted no-claim witness
        # identity.
        self.seed_claim(task="task-4", token="seed-task-4")
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-4"]["task_id"] = "task-3"
        runtime._safe_write_json(self.state_path, state)
        (self.root / "dirt.txt").write_text("real dirt\n", encoding="utf-8")
        result = self.driver(seed_task3=False).reconcile_startup()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "dirty-worktree")
        self.assertEqual(result["checkpoint_identity"], "seed-task-4")

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

    def test_continue_selects_first_incomplete_after_budget_pause_gap(self):
        # Characterization: a budget-paused run leaves completed tasks and no
        # claim in flight. continue_parent must advance to the first incomplete
        # task (task-3) without relaunching or re-checkpointing the completed
        # tasks; the blocked-claim resume operation is not the continuation
        # path because a pause leaves no blocked claim behind.
        state = runtime.load_manifest(self.state_path)
        state["tasks"] = {
            "task-1": {"id": "task-1", "number": 1, "status": "complete", "checkbox": True},
            "task-2": {"id": "task-2", "number": 2, "status": "complete", "checkbox": True},
            "task-3": {"id": "task-3", "number": 3, "status": "pending", "checkbox": False, "allowed_paths": ["task-3.txt"]},
        }
        state["claims"] = {}
        state["checkpoints"] = {}
        runtime._safe_write_json(self.state_path, state)

        adapter = FakeAdapter(
            lambda task, _prompt, generation, _deadline, _token: self.worker_checkpoint(
                task=task["id"], generation=generation, checkpoint_identity=f"{task['id']}:worker-1"
            )
        )
        driver = self.driver(adapter=adapter, seed_task3=False)

        # No blocked claim exists, so the resume operation has nothing to
        # resume; the continuation path is continue_parent, not resume.
        resume_probe = driver.resume()
        self.assertEqual(resume_probe["status"], "blocked")
        self.assertEqual(resume_probe["reason_code"], "stale-claim")
        self.assertEqual(adapter.launches, [])

        result = driver.continue_parent()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["state"], "done-pending")
        self.assertEqual([launch[0] for launch in adapter.launches], ["task-3"])

        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-1"]["status"], "complete")
        self.assertEqual(after["tasks"]["task-2"]["status"], "complete")
        self.assertEqual(after["tasks"]["task-3"]["status"], "done-pending")
        self.assertNotIn("task-1", after["claims"])
        self.assertNotIn("task-2", after["claims"])
        self.assertFalse(any(key.startswith(("task-1", "task-2")) for key in after["checkpoints"]))

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

    def test_activation_receipt_aborted_workflow_beats_token_mismatch(self):
        # r5-F6 witness: on an aborted workflow, a claim re-verification whose
        # token does not match the live claim surfaces the abort outcome, not
        # owner-mismatch; the abort check precedes the identity check exactly
        # as the launch fence orders them.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False)
        self.driver(seed_task3=False).abort("task-4", "seed-task-4")
        claim = {"token": "stale-token", "generation": 0, "task_id": "task-4"}
        outcome = driver._record_activation_receipt(claim, "task-4", {"status": "success"})
        self.assertEqual(outcome["status"], "aborted")
        self.assertEqual(outcome["reason_code"], "explicit-abort")
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
        self._git("add", "-N", "outside-policy.txt")
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


    def commit_message(self, message, name=None, content="predecessor work\n"):
        """Commit one file with an arbitrary message; return the commit sha."""
        target = name or f"predecessor-{uuid.uuid4().hex[:8]}.txt"
        (self.root / target).write_text(content, encoding="utf-8")
        self._git("add", target)
        self._git("commit", "-qm", message)
        return self._git_stdout("rev-parse", "HEAD")

    def orphan_commit(self):
        tree = self._git_stdout("rev-parse", "HEAD^{tree}")
        return self._git_stdout("commit-tree", "-m", "orphan", tree)

    def predecessors_file(self, document):
        path = self.root / f"predecessors-{uuid.uuid4().hex[:8]}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def verify(self, document):
        return runtime.verify_preconditions(self.root, document)

    def test_precondition_history_ref_verifies_rebased_history(self):
        base = self._git_stdout("rev-parse", "HEAD")
        self._git("checkout", "-q", "-b", "work")
        original = self.commit_message("CRM-1234 predecessor feature work")
        self._git("checkout", "-q", "--detach", base)
        newer = self.commit_message("newer base unrelated to the feature")
        self._git("checkout", "-q", "work")
        self._git("rebase", "-q", newer)
        rebased = self._git_stdout("rev-parse", "HEAD")
        self.assertNotEqual(rebased, original)
        result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "history-ref", "value": "CRM-1234"}]}]})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "completed")
        self.assertEqual(result["predecessors"][0]["ref"], "CRM-1234")
        self.assertTrue(result["predecessors"][0]["verified"])

    def test_precondition_history_ref_verifies_cherry_picked_history(self):
        self._git("checkout", "-q", "-b", "work")
        source = self.commit_message("CRM-1234 cherry-pick source work")
        self._git("checkout", "-q", "-")
        self.commit_message("divergent base commit")
        self._git("cherry-pick", source)
        picked = self._git_stdout("rev-parse", "HEAD")
        self.assertNotEqual(picked, source)
        result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "history-ref", "value": "CRM-1234"}]}]})
        self.assertEqual(result["status"], "success")

    def test_precondition_history_ref_verifies_squashed_history(self):
        base = self._git_stdout("rev-parse", "HEAD")
        self.commit_message("CRM-1234 first piece")
        self.commit_message("CRM-5678 second piece")
        self._git("reset", "-q", "--soft", base)
        self.commit_message("CRM-1234 CRM-5678 squashed predecessor work")
        for ref in ("CRM-1234", "CRM-5678"):
            result = self.verify({"predecessors": [{"ref": ref, "outcomes": [{"kind": "history-ref", "value": ref}]}]})
            self.assertEqual(result["status"], "success", ref)
            self.assertTrue(result["predecessors"][0]["verified"])

    def test_precondition_ancestry_outcome(self):
        ancestor = self.commit_message("ancestor base commit")
        self.commit_message("descendant commit")
        document = {"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "ancestry", "value": ancestor}]}]}
        verified = self.verify(document)
        self.assertEqual(verified["status"], "success")
        orphan = self.orphan_commit()
        unverified = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "ancestry", "value": orphan}]}]})
        self.assertEqual(unverified["status"], "blocked")
        self.assertEqual(unverified["reason_code"], "precondition-unverified")

    def test_precondition_artifact_outcome(self):
        probe = self.root / "scripts" / "quota_window_probe.py"
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("# probe\npause_decision = True\n", encoding="utf-8")
        document = {"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "artifact", "path": "scripts/quota_window_probe.py", "contains": "pause_decision"}]}]}
        verified = self.verify(document)
        self.assertEqual(verified["status"], "success")
        absent = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "artifact", "path": "scripts/quota_window_probe.py", "contains": "absent_span"}]}]})
        self.assertEqual(absent["status"], "blocked")
        self.assertEqual(absent["reason_code"], "precondition-unverified")

    def test_precondition_artifact_dotdot_path_refused(self):
        # A normalizing dotdot path that would resolve back INSIDE the repo
        # to a file carrying the pinned span must still be refused: the
        # artifact witness rejects any '..' component, not just escapes.
        probe = self.root / "scripts" / "quota_window_probe.py"
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("# probe\npause_decision = True\n", encoding="utf-8")
        result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "artifact", "path": "scripts/../scripts/quota_window_probe.py", "contains": "pause_decision"}]}]})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")

    def test_precondition_artifact_empty_contains_is_malformed(self):
        # A structurally-broken artifact declaration (empty contains) is a
        # malformed declaration, not an outcome that merely fails to verify.
        probe_path = self.root / "scripts" / "quota_window_probe.py"
        probe_path.parent.mkdir(parents=True, exist_ok=True)
        probe_path.write_text("# probe\npause_decision = True\n", encoding="utf-8")
        result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "artifact", "path": "scripts/quota_window_probe.py", "contains": ""}]}]})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        joined = " ".join(str(item) for item in result["evidence"])
        self.assertIn("(malformed declaration)", joined)

    def test_precondition_missing_repo_root_fails_closed(self):
        missing = self.root / f"missing-root-{uuid.uuid4().hex[:8]}"
        result = runtime.verify_preconditions(missing, {"predecessors": []})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        joined = " ".join(str(item) for item in result["evidence"])
        self.assertIn("repository root missing or not a directory", joined)
        self.assertIn(str(missing.resolve()), joined)
        self.assertTrue(result["resume_allowed"])

    def test_precondition_fails_closed_names_reference(self):
        self.commit_message("CRM-1234 present work")
        orphan = self.orphan_commit()
        outcomes = [
            {"kind": "history-ref", "value": "NOPE-9999"},
            {"kind": "ancestry", "value": orphan},
            {"kind": "artifact", "path": "scripts/missing_probe.py", "contains": "pause_decision"},
        ]
        result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": outcomes}]})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        self.assertTrue(result["resume_allowed"])
        joined = " ".join(str(item) for item in result["evidence"])
        self.assertIn("CRM-1234", joined)
        self.assertIn("NOPE-9999", joined)
        self.assertIn(orphan, joined)
        self.assertIn("scripts/missing_probe.py", joined)

    def test_precondition_malformed_declaration_fails_closed(self):
        cases = (
            {"ref": "CRM-1234", "outcomes": [{"kind": "time-travel", "value": "CRM-1234"}]},
            {"ref": "CRM-1234", "outcomes": []},
            {"outcomes": [{"kind": "history-ref", "value": "CRM-1234"}]},
        )
        for declaration in cases:
            with self.subTest(declaration=declaration):
                result = self.verify({"predecessors": [declaration]})
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "precondition-unverified")
                self.assertTrue(result["resume_allowed"])
                joined = " ".join(str(item) for item in result["evidence"]).lower()
                self.assertIn("malformed", joined)

    def test_precondition_any_outcome_verifies(self):
        self.commit_message("CRM-1234 present work")
        document = {"predecessors": [{"ref": "CRM-1234", "outcomes": [
            {"kind": "artifact", "path": "scripts/missing_probe.py", "contains": "pause_decision"},
            {"kind": "history-ref", "value": "CRM-1234"},
        ]}]}
        result = self.verify(document)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["predecessors"][0]["verified_by"]["kind"], "history-ref")

    def test_precondition_history_ref_fixed_string_no_regex_meta(self):
        self.commit_message("PROJ-123 fixed-string fixture commit")
        result = self.verify({"predecessors": [{"ref": "PROJ-1.3", "outcomes": [{"kind": "history-ref", "value": "PROJ-1.3"}]}]})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")

    def test_precondition_cli_without_manifest(self):
        self.commit_message("CRM-1234 cli fixture work")
        predecessors = self.predecessors_file({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "history-ref", "value": "CRM-1234"}]}]})
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--operation", "precondition",
                "--predecessors-file", str(predecessors),
                "--repo-root", str(self.root),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "completed")

    def test_precondition_malformed_document_fails_closed(self):
        cases = (
            {"predecessors": "CRM-1234"},
            {"predecessors": None},
            ["not", "a", "mapping"],
        )
        for document in cases:
            with self.subTest(document=document):
                result = self.verify(document)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "precondition-unverified")
                joined = " ".join(str(item) for item in result["evidence"]).lower()
                self.assertIn("malformed", joined)

    def test_precondition_absent_or_empty_predecessors_stays_success(self):
        for document in ({}, {"predecessors": []}):
            with self.subTest(document=document):
                result = self.verify(document)
                self.assertEqual(result["status"], "success")
                self.assertIn("no predecessors declared", result["evidence"])

    def test_precondition_cli_malformed_file_fails_closed(self):
        bad = self.root / "predecessors-broken.json"
        bad.write_text("{not json", encoding="utf-8")
        for target in (bad, self.root / "predecessors-absent.json"):
            with self.subTest(target=target.name):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/execute_plan_runtime.py"),
                        "--operation", "precondition",
                        "--predecessors-file", str(target),
                        "--repo-root", str(self.root),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result = json.loads(completed.stdout)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "precondition-unverified")
                self.assertIn(str(target), " ".join(str(item) for item in result["evidence"]))

    def test_precondition_artifact_path_escape_refused(self):
        # A decoy OUTSIDE the repo root carries the pinned span: a blocked
        # verdict proves the escape was refused, not that the span was missed.
        span = "pinned predecessor span {}".format(uuid.uuid4().hex[:8])
        decoy = self.root.parent / f"outside-decoy-{uuid.uuid4().hex[:8]}.txt"
        decoy.write_text(span, encoding="utf-8")
        self.addCleanup(decoy.unlink, missing_ok=True)
        document = {"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "artifact", "path": "../outside.txt", "contains": span}]}]}
        result = self.verify(document)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")

    def test_precondition_validator_only_outcome_blocks_without_malformed_label(self):
        document = {"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": "validator", "value": "scripts/check.py"}]}]}
        result = self.verify(document)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        joined = " ".join(str(item) for item in result["evidence"])
        self.assertIn("validator (orchestrator-run", joined)
        self.assertNotIn("malformed", joined.lower())

    def test_precondition_leading_dash_value_is_malformed_declaration(self):
        for kind in ("history-ref", "ancestry"):
            with self.subTest(kind=kind):
                result = self.verify({"predecessors": [{"ref": "CRM-1234", "outcomes": [{"kind": kind, "value": "--injected-option"}]}]})
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "precondition-unverified")
                joined = " ".join(str(item) for item in result["evidence"]).lower()
                self.assertIn("malformed declaration", joined)

    # ------------------------------------------------------------------
    # Readiness decision machinery (read-only; requires --plan on the CLI).
    # ------------------------------------------------------------------

    def write_plan(self, text, name="fixture-plan.md"):
        plan_path = self.root / name
        plan_path.write_text(text, encoding="utf-8")
        return plan_path

    def seed_fresh_pending_manifest(self, tasks=None):
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            tasks or [{"id": "task-1", "number": 1}, {"id": "task-2", "number": 2}],
        )

    def rewrite_manifest(self, mutate):
        state = runtime.load_manifest(self.state_path)
        mutate(state)
        runtime._safe_write_json(self.state_path, state)

    def test_readiness_direct_continuation_on_fresh_manifest(self):
        # A seeded active manifest with every task pending plus an agreeing
        # plan file: direct continuation on the provable first task.
        self.seed_fresh_pending_manifest()
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [ ] first item\n\n### Task 2: second\n- [ ] second item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["decision"], "direct-continuation")
        self.assertEqual(result["recovery_action"], "continue-parent")
        self.assertEqual(result["next_task_id"], "task-1")
        self.assertEqual(result["failed_conditions"], [])

    def test_readiness_observes_live_claim(self):
        # One launched claim: observe-worker names that task; the claim token,
        # generation, and task status stay byte-identical after the call.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: state["tasks"]["task-4"].update({"status": "launched"}))
        driver = self.driver()
        before = runtime.load_manifest(self.state_path)
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "observe-worker")
        # The observe arm's recovery action is pinned: a mutation to any
        # launch-flavored recovery action survives nothing here.
        self.assertEqual(result["recovery_action"], "observe-live-worker")
        self.assertEqual(result["next_task_id"], "task-4")
        self.assertTrue(any("task-4" in item for item in result["evidence"]))
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["claims"]["task-4"]["token"], "seed-task-4")
        self.assertEqual(after["claims"]["task-4"]["generation"], before["claims"]["task-4"]["generation"])
        self.assertEqual(after["tasks"]["task-4"]["status"], before["tasks"]["task-4"]["status"])
        self.assertEqual(after, before)

    def test_readiness_recovery_on_done_pending(self):
        # A task in done-pending is an unresolved done handoff: recovery.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [x] done item\n"
        )
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: state["tasks"]["task-4"].update({"status": "done-pending"}))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(any("unresolved done handoff" in item for item in result["failed_conditions"]))

    def test_readiness_recovery_on_plan_manifest_disagreement(self):
        # The manifest records task-3 complete while its plan section keeps
        # one unchecked line: plan-manifest disagreement, the manifest wins
        # per the seeding boundary, so the plan is corrected through the
        # skill-gated plan-edit step.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n- [ ] forgotten item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(any("plan-manifest disagreement" in item and "task-3" in item for item in result["failed_conditions"]))
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_agreement_reports_star_marker_disagreement(self):
        # GFM task-list widening witness: a progressed task whose plan
        # section keeps one unchecked '* [ ]' line disagrees exactly like
        # the dash form. RED before the widening: the dash-only predicate
        # read no disagreement for star lines, so this routed
        # direct-continuation. The readiness path emits count-only evidence
        # for its plan-manifest condition (line pins live on the terminal
        # and pre-archive scans), so no line-number fragment may appear.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n* [ ] forgotten star item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "plan-manifest disagreement" in item and "task-3" in item and "carries 1 unchecked" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertFalse(any("line " in item for item in result["failed_conditions"]), result["failed_conditions"])
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_mid_prose_mention_still_ignored(self):
        # Regression pin for the line-anchored reading under the widened
        # predicate: a mid-line prose mention of the asterisk or plus
        # marker form does not start its line and never counts, so the
        # progressed task's section agrees and the run continues directly.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\nProse mentions * [ ] mid-line and even a bare + [ ] fragment after words, but no line starts with an unchecked marker token.\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "direct-continuation")
        self.assertEqual(result["failed_conditions"], [])

    def test_readiness_recovery_on_blocked_state(self):
        # workflow_state blocked with no live claim: recovery naming the
        # machine state, across varying task statuses, including an
        # all-complete manifest that terminal-path would take on an active
        # workflow (a blocked workflow never routes to terminal-path).
        agreeing_plan = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [x] done item\n",
            name="plan-agreeing.md",
        )
        pending_plan = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n",
            name="plan-pending.md",
        )
        status_arms = (
            (
                "pending-tasks",
                [
                    {"id": "task-3", "number": 3, "status": "pending"},
                    {"id": "task-4", "number": 4, "status": "pending", "allowed_paths": ["task-4.txt"]},
                ],
            ),
            (
                "complete-and-checkpointed",
                [
                    {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
                    {"id": "task-4", "number": 4, "status": "checkpointed", "checkbox": True},
                ],
            ),
        )
        for plan_path in (pending_plan, agreeing_plan):
            for arm, tasks in status_arms:
                with self.subTest(plan=plan_path.name, tasks=arm):
                    self.seed_fresh_pending_manifest(tasks)
                    self.rewrite_manifest(lambda state: state.update({"workflow_state": "blocked"}))
                    driver = self.driver()
                    result = driver.readiness(plan_path)
                    self.assertEqual(result["decision"], "recovery")
                    self.assertTrue(any("workflow_state is 'blocked'" in item for item in result["failed_conditions"]))
                    self.assertEqual(result["recovery_action"], "stop-or-recovery")

    def test_readiness_refuses_aborted_workflow(self):
        # workflow_state aborted with otherwise clean pending tasks: recovery
        # naming the machine state with a stop-or-recovery action.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        self.rewrite_manifest(lambda state: state.update({"workflow_state": "aborted"}))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(any("workflow_state is 'aborted'" in item for item in result["failed_conditions"]))
        self.assertEqual(result["recovery_action"], "stop-or-recovery")

    def test_readiness_terminal_path_when_all_complete(self):
        # Every task complete: terminal-path whether workflow_state is
        # active, complete, or already terminal.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [x] done item\n\n### Task 2: second\n- [x] done item\n"
        )
        for workflow_state in ("active", "complete", "terminal"):
            with self.subTest(workflow_state=workflow_state):
                self.seed_fresh_pending_manifest(
                    [
                        {"id": "task-1", "number": 1, "status": "complete", "checkbox": True},
                        {"id": "task-2", "number": 2, "status": "checkpointed", "checkbox": True},
                    ]
                )
                if workflow_state != "active":
                    self.rewrite_manifest(lambda state: state.update({"workflow_state": workflow_state}))
                driver = self.driver()
                result = driver.readiness(plan_path)
                self.assertEqual(result["decision"], "terminal-path")
                self.assertEqual(result["recovery_action"], "continue-parent")
                self.assertEqual(result["failed_conditions"], [])

    def test_readiness_cli_requires_plan(self):
        # The CLI refuses --operation readiness without --plan: non-zero exit
        # and the manifest bytes stay untouched.
        before = self.state_path.read_bytes()
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(self.state_path),
                "--repo-root", str(self.root),
                "--owner", "cli-owner",
                "--operation", "readiness",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--plan is required", completed.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_readiness_missing_plan_file_fails_closed(self):
        # A nonexistent --plan path is the fail-closed precondition block:
        # blocked with reason precondition-unverified, the recovery decision,
        # no provable next task, and the manifest bytes untouched (branch
        # witness: without the named fields a caller could not route the
        # refusal).
        driver = self.driver()
        before = self.state_path.read_bytes()
        missing = self.root / "docs/plans/never-written.md"
        self.assertFalse(missing.exists())
        result = driver.readiness(missing)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        self.assertEqual(result["decision"], "recovery")
        self.assertIsNone(result["next_task_id"])
        self.assertTrue(any("plan file is missing or unreadable" in item for item in result["evidence"]), result["evidence"])
        self.assertTrue(any("plan file is missing or unreadable" in item for item in result["failed_conditions"]), result["failed_conditions"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_readiness_refuses_plan_over_read_limit(self):
        # The readiness plan read shares the terminal gate's bounded-read
        # helper (open + read(LIMIT + 1), no stat size gate):
        # a plan whose read proves it over PLAN_READ_LIMIT is
        # refused as precondition-unverified instead of being read whole,
        # and the manifest bytes stay untouched.
        driver = self.driver()
        before = self.state_path.read_bytes()
        huge = self.write_plan("# Fixture plan\n" + ("filler line\n" * 110_000), name="plan-huge.md")
        self.assertGreater(
            (self.root / "plan-huge.md").stat().st_size,
            runtime.PLAN_READ_LIMIT,
        )
        result = driver.readiness(huge)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        self.assertEqual(result["decision"], "recovery")
        self.assertIsNone(result["next_task_id"])
        self.assertTrue(any("plan file exceeds the bounded read limit" in item for item in result["evidence"]), result["evidence"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_read_limit_boundary_pair_readiness(self):
        # Regression pin (classification already correct today): the
        # readiness --plan read admits a plan of exactly
        # PLAN_READ_LIMIT bytes through the bounded-read gate (the
        # +1-byte read window) and refuses limit+1 with the over-limit
        # evidence. A boundary drift in either direction (an off-by-one
        # refusal at the limit, or a prefix scan at limit+1) flips one arm.
        self.seed_fresh_pending_manifest()
        driver = self.driver()
        header = "# Fixture plan\n\n### Task 1: first\n- [ ] only item\n\n"
        for size, expect_accepted in ((runtime.PLAN_READ_LIMIT, True), (runtime.PLAN_READ_LIMIT + 1, False)):
            with self.subTest(size=size):
                text = header + "x" * (size - len(header))
                self.assertEqual(len(text.encode("utf-8")), size)
                plan_path = self.root / f"plan-boundary-{size}.md"
                plan_path.write_text(text, encoding="utf-8")
                result = driver.readiness(plan_path)
                if expect_accepted:
                    self.assertNotIn("exceeds the bounded read limit", " ".join(result["evidence"]), result["evidence"])
                    self.assertEqual(result["decision"], "direct-continuation")
                else:
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "precondition-unverified")
                    self.assertTrue(any("plan file exceeds the bounded read limit" in item for item in result["evidence"]), result["evidence"])

    def test_readiness_refuses_non_regular_plan_file(self):
        # Regular-file gate witness: a plan path that is not a
        # regular file is refused before any open. A directory exercises the
        # same is_file() gate deterministically; a FIFO (os.mkfifo) is
        # refused through that identical gate and, unlike the directory, its
        # blocking read would hang forever because a FIFO's stat size is 0
        # and a size-only check cannot refuse it.
        driver = self.driver()
        before = self.state_path.read_bytes()
        directory = self.root / "plan-directory"
        directory.mkdir()
        result = driver.readiness(directory)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "precondition-unverified")
        self.assertEqual(result["decision"], "recovery")
        self.assertIsNone(result["next_task_id"])
        self.assertTrue(any("plan file is not a regular file" in item for item in result["evidence"]), result["evidence"])
        self.assertTrue(any("plan file is not a regular file" in item for item in result["failed_conditions"]), result["failed_conditions"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_read_plan_bounded_opens_nonblocking_and_fstats(self):
        # RED gate for the nonblocking open rewrite: the shared bounded read
        # must open with O_RDONLY | O_NONBLOCK | O_CLOEXEC, fstat the open
        # descriptor, require a regular file (stat.S_ISREG), and only then
        # wrap the descriptor and read. The nonblocking flag guarantees the
        # open itself cannot block on a FIFO with no writer, and classifying
        # the open descriptor removes the check-then-open window entirely
        # (no exists/is_file pre-check). The spies wrap the real primitives;
        # the read spy rides an fdopen seam instead of patching
        # io.BufferedReader.read because that type is immutable on modern
        # Pythons. The current Path.open implementation never calls the
        # patched os.open/os.fstat/os.fdopen or stat.S_ISREG, so the
        # ordering assertion fails pre-rewrite with an empty event log.
        plan_dir = self.root / "docs" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plan_dir / "spy-plan.md"
        plan_path.write_text("# spy plan\n", encoding="utf-8")
        events = []
        real_open, real_fstat, real_fdopen, real_isreg = os.open, os.fstat, os.fdopen, stat.S_ISREG

        def spy_open(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs)
            events.append(("open", os.fspath(path), flags, fd))
            return fd

        def spy_fstat(fd):
            result = real_fstat(fd)
            events.append(("fstat", fd))
            return result

        def spy_isreg(mode):
            events.append(("s-isreg",))
            return real_isreg(mode)

        class RecordingStream:
            # Minimal wrapper over the real buffered stream: it records the
            # read size and closes the underlying stream so the descriptor
            # ownership semantics of the code under test stay real.
            def __init__(self, stream):
                self._stream = stream

            def read(self, size=-1):
                events.append(("read", size))
                return self._stream.read(size)

            def close(self):
                self._stream.close()

        def spy_fdopen(fd, mode="r", *args, **kwargs):
            events.append(("fdopen", fd))
            return RecordingStream(real_fdopen(fd, mode, *args, **kwargs))

        with mock.patch.object(runtime.os, "open", side_effect=spy_open), \
                mock.patch.object(runtime.os, "fstat", side_effect=spy_fstat), \
                mock.patch.object(stat, "S_ISREG", side_effect=spy_isreg), \
                mock.patch.object(runtime.os, "fdopen", side_effect=spy_fdopen):
            text, error = runtime._read_plan_bounded(None, plan_path, require_safe_path=False)
        self.assertIsNone(error)
        # The helper strips the decoded text once (both empty-refusal sites
        # and the readiness decision consume the stripped form), so the
        # trailing newline of the file is gone from the returned text.
        self.assertEqual(text, "# spy plan")
        opens = [event for event in events if event[0] == "open"]
        self.assertEqual(len(opens), 1, events)
        _, opened_path, flags, fd = opens[0]
        self.assertEqual(opened_path, str(plan_path))
        self.assertEqual(flags, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        self.assertEqual([event for event in events if event[0] == "fstat"], [("fstat", fd)], events)
        self.assertEqual([event[0] for event in events], ["open", "fstat", "s-isreg", "fdopen", "read"], events)
        self.assertEqual(events[-1], ("read", runtime.PLAN_READ_LIMIT + 1), events)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "os.mkfifo is unavailable on this platform")
    def test_read_plan_bounded_refuses_fifo_without_open(self):
        # Refusal pin (green on the unfixed tree and must stay green after
        # the nonblocking rewrite): a FIFO is refused with the identical
        # not-a-regular-file fragment BEFORE any blocking read. The pre-open
        # is_file() gate refuses it today; the post-rewrite fstat S_ISREG
        # gate refuses it identically. A regression to a blocking read would
        # hang this test instead of passing it.
        fifo_dir = tempfile.mkdtemp()
        try:
            fifo_path = os.path.join(fifo_dir, "plan.fifo")
            os.mkfifo(fifo_path)
            text, error = runtime._read_plan_bounded(None, fifo_path, require_safe_path=False)
            self.assertIsNone(text)
            self.assertIsNotNone(error)
            self.assertIn("is not a regular file", error)
        finally:
            shutil.rmtree(fifo_dir, ignore_errors=True)

    def test_readiness_refuses_plan_without_task_sections(self):
        # A plan text with zero '### Task <N>:' headings cannot agree or
        # disagree per-section: the readiness decision fails the
        # plan-shape condition instead of returning a vacuous
        # direct-continuation for a wrong --plan file while no task has
        # progressed.
        self.seed_fresh_pending_manifest()
        plan_path = self.write_plan("# Not a plan\n\nNo task sections here.\n", name="plan-foreign.md")
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["decision"], "recovery")
        # The zero-section shape failure routes stop-or-recovery (the same
        # pairing the readiness decision emits for a finished workflow): the
        # wrong --plan file is not a resumable condition.
        self.assertEqual(result["recovery_action"], "stop-or-recovery")
        self.assertTrue(
            any("plan carries no recognizable task sections" in item for item in result["failed_conditions"]),
            result["failed_conditions"],
        )

    def test_readiness_blocked_while_manifest_lock_held(self):
        # Lock-contention witness: with another owner holding the
        # manifest lock at decision time, readiness returns the transient
        # contention envelope (blocked, decision recovery, recovery action
        # resumable-conflict) and the manifest bytes stay untouched.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()  # Construction (and its owner write) precedes the foreign lock.
        before = self.state_path.read_bytes()
        with runtime._manifest_lock(self.state_path, "blocking-owner") as acquired:
            self.assertTrue(acquired)
            result = driver.readiness(plan_path)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["decision"], "recovery")
        self.assertEqual(result["recovery_action"], "resumable-conflict")
        self.assertIn("manifest lock is held by another owner", result["failed_conditions"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_readiness_never_mutates_manifest(self):
        # Direct-continuation and recovery fixtures: the manifest file bytes
        # are byte-identical before and after each readiness call.
        driver = self.driver()
        self.seed_fresh_pending_manifest()
        plan_direct = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [ ] first item\n\n### Task 2: second\n- [ ] second item\n",
            name="plan-direct.md",
        )
        before = self.state_path.read_bytes()
        self.assertEqual(driver.readiness(plan_direct)["decision"], "direct-continuation")
        self.assertEqual(self.state_path.read_bytes(), before)
        self.seed_claim(task="task-2", token="seed-task-2")
        self.rewrite_manifest(lambda state: state["tasks"]["task-2"].update({"status": "done-pending"}))
        plan_recovery = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [x] done item\n\n### Task 2: second\n- [x] done item\n",
            name="plan-recovery.md",
        )
        before = self.state_path.read_bytes()
        self.assertEqual(driver.readiness(plan_recovery)["decision"], "recovery")
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_readiness_cli_manifest_bytes_identical_on_success(self):
        # CLI readiness on an owned manifest (success path): the read-only
        # driver construction plus the write-free decision keep the manifest
        # bytes identical across the whole operation.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        self.driver()  # First construction commits the owner identity.
        before = self.state_path.read_bytes()
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(self.state_path),
                "--repo-root", str(self.root),
                "--operation", "readiness",
                "--plan", str(plan_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["decision"], "direct-continuation")
        self.assertEqual(result["next_task_id"], "task-4")
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_readiness_recovery_on_blocked_claim(self):
        # A claim in state 'blocked' is a fenced claim: recovery naming it
        # (negative witness for the fenced-claim clause).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: (
            state["claims"]["task-4"].update({"state": "blocked"}),
            state["tasks"]["task-4"].update({"status": "blocked", "resume_allowed": False}),
        ))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(any("fenced claim in state 'blocked'" in item for item in result["failed_conditions"]))
        self.assertEqual(result["recovery_action"], "preserve-and-reconcile")

    def test_readiness_recovery_on_commit_pending(self):
        # A commit-pending task is an unresolved done handoff (negative
        # witness for the commit-pending clause, distinct from done-pending).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [x] done item\n"
        )
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: state["tasks"]["task-4"].update({
            "status": "commit-pending",
            "commit_identity": "aa11bb22cc33",
            "done_log_evidence": ["task-4-implement.log.md"],
        }))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any("unresolved done handoff" in item and "commit-pending" in item for item in result["failed_conditions"])
        )
        self.assertEqual(result["recovery_action"], "preserve-and-reconcile")

    def test_readiness_recovery_on_unprovable_next_task(self):
        # The first incomplete task in a non-claimable status is unprovable
        # (negative witness for the next-task clause); the rotated aborted
        # claim keeps observe-worker silent so recovery carries the failure.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [x] done item\n"
        )
        self.seed_claim(task="task-4", token="seed-task-4")
        self.rewrite_manifest(lambda state: (
            state["claims"]["task-4"].update({"state": "aborted"}),
            state["tasks"]["task-4"].update({"status": "aborted"}),
        ))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any("next incomplete task 'task-4' is not provable" in item for item in result["failed_conditions"])
        )
        self.assertEqual(result["recovery_action"], "preserve-and-reconcile")

    def test_readiness_empty_manifest_routes_to_recovery(self):
        # A manifest with no tasks continues nothing: recovery naming the
        # empty manifest, never a direct-continuation with next_task_id None.
        plan_path = self.write_plan("# Fixture plan\n")
        self.rewrite_manifest(lambda state: state.update({"tasks": {}, "claims": {}}))
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertIsNone(result["next_task_id"])
        self.assertTrue(any("carries no tasks" in item for item in result["failed_conditions"]))
        self.assertEqual(result["recovery_action"], "stop-or-recovery")

    def test_readiness_agreement_scan_spans_nested_subsections(self):
        # A nested '### Notes:' subsection belongs to the task section: an
        # unchecked line below a progressed task's checked boxes still
        # disagrees (the section scan stops only at '## ' or the next
        # '### Task <N>:' heading).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n### Notes:\n- [ ] follow-up hidden under notes\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any("plan-manifest disagreement" in item and "task-3" in item for item in result["failed_conditions"])
        )
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_readiness_agreement_scan_ignores_break_markers_inside_fence(self):
        # A fenced code block inside the task section must not truncate the
        # agreement scan: a '## ' line inside the fence is fenced content,
        # never a break marker, so the unchecked checkbox AFTER the fence is
        # still scanned and still disagrees (negative witness for the
        # fence-aware break handling).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n```text\n## not a heading\n```\n\n- [ ] hidden after the fence\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "plan-manifest disagreement" in item and "task-3" in item and "carries 1 unchecked" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_readiness_agreement_scan_keeps_pseudo_task_heading_inside_fence(self):
        # A literal '### Task 9:' line inside a fence is fenced content, not
        # a section break or a foreign heading: the unchecked box after it
        # stays inside task-3's scanned section and the disagreement names
        # task-3's own number, never a phantom task-9.
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n```markdown\n### Task 9: fake next task\n- [ ] example box inside the fence\n```\n\n### Task 4: fourth\n- [ ] pending item\n"
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "plan-manifest disagreement" in item and "task-3" in item and "carries 1 unchecked" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertFalse(any("task-9" in item for item in result["failed_conditions"]), result["failed_conditions"])
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_fence_map_tilde_fence_hides_break_marker(self):
        # CommonMark-grade fence map witness: a tilde-fenced block is a real
        # fence, so a '## ' line inside it is fenced content, never a break
        # marker, and the unchecked checkbox AFTER the block is still scanned
        # and still disagrees. RED before the fence map: the single-level
        # backtick parity toggle ignored tildes, so the tilde block's inner
        # '## ' line truncated task-3's section and the box after it was
        # missed (direct-continuation instead of recovery).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n~~~text\n## not a heading\n~~~\n\n- [ ] hidden after the tildes\n\n### Task 4: fourth\n- [ ] pending item\n",
            name="plan-tilde-fence.md",
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "plan-manifest disagreement" in item and "task-3" in item and "carries 1 unchecked" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_fence_map_nested_shorter_fence_does_not_close(self):
        # Nested-width witness: inside a four-backtick fence, a shorter
        # three-backtick line and a tilde line are fenced content; parity
        # holds until the matching four-backtick closer, so only the decoy
        # and the box after the closer are scanned and the next task heading
        # still breaks the section (no task-4 condition). RED before the
        # fence map: the single-level toggle closed the wide fence on the
        # inner three-backtick line and reopened on the wide closer, so
        # Task 4's heading was swallowed into task-3's section and its
        # pending box joined the disagreement (3 unchecked, not 2).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n````text\n```\n~~~ closer-looking line\n- [ ] decoy inside the wide fence\n````\n\n- [ ] hidden after the wide fence\n\n### Task 4: fourth\n- [ ] pending item\n",
            name="plan-nested-fence.md",
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "plan-manifest disagreement" in item and "task-3" in item and "carries 2 unchecked" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertFalse(any("task-4" in item for item in result["failed_conditions"]), result["failed_conditions"])
        self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_fence_map_unclosed_fence_fails_closed_for_later_sections(self):
        # Behavior pin for the fail-closed direction: an unclosed fence in
        # task-1's body stays open to end of file under whole-plan parity, so
        # Task 2's heading inside it binds no section and the readiness
        # condition fails closed naming task-2, never silently scanning the
        # fenced content as prose. RED before the fence map: the fence-blind
        # heading search bound the fenced heading and per-section parity
        # restarted closed, so the fenced pending box was scanned as prose
        # (a task-2 unchecked disagreement instead of the missing section).
        self.seed_fresh_pending_manifest()
        self.rewrite_manifest(lambda state: state["tasks"]["task-2"].update({"status": "checkpointed"}))
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [x] done item\n\n```text\nunclosed fence swallows the rest\n\n### Task 2: second\n- [ ] pending item\n",
            name="plan-unclosed-fence.md",
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "task-2" in item and "its plan section '### Task 2:' is missing" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertFalse(
            any("task-2" in item and "unchecked" in item for item in result["failed_conditions"]),
            result["failed_conditions"],
        )

    def test_fence_map_indent_tolerance(self):
        # Zero-to-three-space indent tolerance, both arms. Arm A: a fence
        # opener indented three spaces opens a real fence (its indented
        # '## ' content is fenced and the box after the closer is scanned);
        # this arm is green before the fence map because the pre-fix toggle
        # stripped indent too. Arm B (RED before the fence map): a
        # fence-lookalike line indented four spaces is literal text that
        # toggles nothing, so the REAL backtick fence after it still opens,
        # hides its inner '## ' line, and the box after it is scanned;
        # pre-fix the lookalike toggled the single-level parity, the real
        # opener mis-closed, and the inner '## ' line broke task-3's section
        # before the box (direct-continuation instead of recovery).
        plans = {
            "three-space-opener": (
                "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n   ```text\n   ## not a heading\n   ```\n\n- [ ] hidden after the indented fence\n\n### Task 4: fourth\n- [ ] pending item\n",
                "plan-indent-three.md",
            ),
            "four-space-lookalike": (
                "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n    ```text\n    literal lookalike, four spaces\n\n```text\n## not a heading\n```\n\n- [ ] hidden after the real fence\n\n### Task 4: fourth\n- [ ] pending item\n",
                "plan-indent-four.md",
            ),
        }
        for arm, (text, name) in plans.items():
            with self.subTest(arm=arm):
                plan_path = self.write_plan(text, name=name)
                driver = self.driver()
                result = driver.readiness(plan_path)
                self.assertEqual(result["decision"], "recovery")
                self.assertTrue(
                    any(
                        "plan-manifest disagreement" in item and "task-3" in item and "carries 1 unchecked" in item
                        for item in result["failed_conditions"]
                    ),
                    result["failed_conditions"],
                )
                self.assertEqual(result["recovery_action"], "correct-plan-through-skill-gated-plan-edit")

    def test_fence_map_whole_plan_parity_not_per_section(self):
        # Whole-plan parity witness: a fence opened in task-1's body and
        # closed after task-2's heading keeps task-2's heading fenced under
        # whole-plan parity (parity never restarts at a section start), so
        # task-2's extraction fails closed with the missing-section
        # condition. RED before the fence map: per-section parity restarted
        # closed at the fenced heading, the box after the closer was scanned
        # as prose, and the disagreement named task-2's unchecked box
        # instead of the missing section.
        self.seed_fresh_pending_manifest()
        self.rewrite_manifest(lambda state: state["tasks"]["task-2"].update({"status": "checkpointed"}))
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [x] done item\n\n```text\nfence opened in task 1\n\n### Task 2: second\n```\n- [ ] pending item\n",
            name="plan-whole-plan-parity.md",
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertTrue(
            any(
                "task-2" in item and "its plan section '### Task 2:' is missing" in item
                for item in result["failed_conditions"]
            ),
            result["failed_conditions"],
        )
        self.assertFalse(
            any("task-2" in item and "unchecked" in item for item in result["failed_conditions"]),
            result["failed_conditions"],
        )

    def test_fence_map_fenced_pseudo_heading_does_not_hijack(self):
        # The documented residual becomes fixed behavior: a fenced
        # pseudo-heading carrying a manifest-REAL task number ahead of the
        # real heading no longer hijacks the section start; the heading
        # search skips fenced lines and binds the real unfenced heading, so
        # task-3's scanned section is its own body (zero unchecked boxes)
        # and the decision is the plain direct continuation. Rewrites the
        # witness that pinned the hijack (the fenced fake heading started
        # the section, parity restarted closed, and the rest of the plan was
        # swallowed into a 2-unchecked disagreement).
        plan_path = self.write_plan(
            "# Fixture plan\n\n```text\n### Task 3: fake\n- [ ] decoy box inside the fence\n```\n\n### Task 3: third\n- [x] done item\n\n### Task 4: fourth\n- [ ] pending item\n",
            name="plan-fence-hijack.md",
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "direct-continuation")
        self.assertEqual(result["failed_conditions"], [])

    def test_readiness_task_heading_boundary_one_vs_ten(self):
        # The Task 1 / Task 10 heading-boundary contract: the heading match
        # pins the number against its terminating colon, so the Task 1
        # agreement scan never consumes Task 10's heading or content (and
        # vice versa).
        plan_path = self.write_plan(
            "# Fixture plan\n\n### Task 1: first\n- [x] done item\n\n### Task 10: tenth\n- [ ] pending item\n\n### Task 11: eleventh\n- [ ] pending item\n"
        )
        self.seed_fresh_pending_manifest(
            [
                {"id": "task-1", "number": 1, "status": "complete", "checkbox": True},
                {"id": "task-10", "number": 10, "status": "pending"},
                {"id": "task-11", "number": 11, "status": "pending"},
            ]
        )
        driver = self.driver()
        result = driver.readiness(plan_path)
        # Complete task-1's section is fully checked and both pending tasks'
        # unchecked boxes agree with the manifest: direct continuation.
        self.assertEqual(result["decision"], "direct-continuation")
        self.assertEqual(result["next_task_id"], "task-10")
        # The converse: a progressed Task 10 with an unchecked line is
        # reported under its own number, never attributed to Task 1 (the
        # still-pending Task 11 keeps terminal-path from firing first).
        self.rewrite_manifest(lambda state: state["tasks"]["task-10"].update({"status": "checkpointed", "checkbox": True}))
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        # The "carries 1 unchecked" discriminator: a number-pinning heading
        # regression (a first-digit capture) would report Task 10's section
        # as MISSING instead of scanning it, so the assertion must require
        # the section-scanned disagreement text, not the loose "task-10"
        # substring the missing-section message also contains.
        self.assertTrue(
            any("task-10" in item and "carries 1 unchecked" in item for item in result["failed_conditions"]),
            result["failed_conditions"],
        )
        self.assertFalse(any("task-1'" in item for item in result["failed_conditions"]), result["failed_conditions"])

    # ------------------------------------------------------------------
    # Interrupted-claim ownership recovery (lease-gated reclaim).
    # ------------------------------------------------------------------

    FIXED_NOW = 1_000_000.0

    def _expired_lease_timestamp(self):
        return self.FIXED_NOW - runtime.CLAIM_LEASE_SECONDS - 10.0

    def test_reclaim_blocked_before_lease_expiry(self):
        # A launched claim with a fresh timestamp is inside its lease: reclaim
        # is refused and the claim token, generation, and task status stay
        # byte-identical. The boundary arm is the mutation discriminator: at
        # elapsed exactly CLAIM_LEASE_SECONDS the lease has expired and the
        # reclaim succeeds (a `<` -> `<=` comparison regression would refuse
        # there too).
        for arm, timestamp, expect_success in (
            ("inside-lease", self.FIXED_NOW, False),
            ("exactly-at-lease-boundary", self.FIXED_NOW - runtime.CLAIM_LEASE_SECONDS, True),
        ):
            with self.subTest(lease=arm):
                self.seed_claim(task="task-4", token="seed-task-4", generation=0)
                self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": timestamp}))
                driver = self.driver(clock=lambda: self.FIXED_NOW)
                before = runtime.load_manifest(self.state_path)
                result = driver.reclaim("task-4")
                if expect_success:
                    self.assertEqual(result["status"], "success")
                    self.assertEqual(result["reason_code"], "reclaimed")
                else:
                    self.assertEqual(result["status"], "blocked")
                    self.assertEqual(result["reason_code"], "stale-claim")
                    self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_reclaim_releases_expired_claim(self):
        # Past the lease the reclaim recycles the claim (the resume path's
        # recycle pattern): task back to pending, old claim marked replaced
        # with a rotated token and generation, checkpoints preserved, every
        # other task and claim untouched. A subsequent claim takes the freed
        # task and the original token no longer passes claim-identity checks.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)

        def seed_expired(state):
            state["claims"]["task-4"]["timestamp"] = self._expired_lease_timestamp()
            state["checkpoints"]["task-4:worker-1"] = {"result": {"status": "success"}, "task_id": "task-4"}

        self.rewrite_manifest(seed_expired)
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        result = driver.reclaim("task-4")
        self.assertEqual(result["status"], "success")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "pending")
        replacement = after["claims"]["task-4"]
        self.assertEqual(replacement["state"], "replaced")
        self.assertNotEqual(replacement["token"], "seed-task-4")
        self.assertNotEqual(replacement["generation"], 0)
        self.assertEqual(after["generation"], replacement["generation"])
        self.assertEqual(after["checkpoints"]["task-4:worker-1"]["task_id"], "task-4")
        # The evidence-line composition lives in a pure helper,
        # and the pre-redaction label contract is asserted there directly:
        # the OLD claim token is carried under replaced_token and the NEW
        # rotated token under replacement_token, with distinct values, so a
        # label-swap mutation flips the helper pin (the driver's returned
        # envelope redacts both values and can only prove the labels exist).
        lines = runtime._reclaim_evidence_lines("task-4", "seed-old-token", "rotated-new-token", 5)
        self.assertIn("replaced_token=seed-old-token", lines)
        self.assertIn("replacement_token=rotated-new-token", lines)
        # Swap detector: the OLD token must never appear under the NEW
        # token's label, so a label-swap mutation flips this pin instead of
        # silently exchanging the two identities (the literal equality of
        # the two fixture tokens proves nothing and is deliberately absent).
        self.assertNotIn("replacement_token=seed-old-token", lines)
        self.assertIn(f"lease_seconds={runtime.CLAIM_LEASE_SECONDS}", lines)
        # The returned envelope redacts BOTH token values to <redacted>, and
        # this redaction must never change: the durable evidence can prove
        # the labels exist but must never carry a live token value.
        self.assertIn("replaced_token=<redacted>", result["evidence"])
        self.assertIn("replacement_token=<redacted>", result["evidence"])
        self.assertEqual(after["tasks"]["task-3"]["status"], "complete")
        self.assertNotIn("task-3", after["claims"])
        claim = driver.claim_next_task()
        self.assertTrue(claim["claimed"])
        self.assertEqual(claim["task_id"], "task-4")
        self.assertEqual(claim["generation"], replacement["generation"] + 1)
        self.assertNotEqual(claim["token"], "seed-task-4")
        late = driver.record_worker_checkpoint({
            "status": "success",
            "reason_code": "completed",
            "evidence": ["late-worker-log"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker-late",
            "generation": 0,
            "claim_token": "seed-task-4",
        })
        self.assertEqual(late["status"], "blocked")
        self.assertEqual(late["reason_code"], "owner-mismatch")

    def test_reclaim_unknown_task_fails_closed(self):
        # A missing task and a claimless pending task both fail closed as
        # stale-claim with the manifest bytes untouched.
        driver = self.driver()
        for task_id in ("task-99", "task-4"):
            with self.subTest(task_id=task_id):
                before = self.state_path.read_bytes()
                result = driver.reclaim(task_id)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "stale-claim")
                self.assertEqual(self.state_path.read_bytes(), before)

    def test_reclaim_refuses_progressed_task(self):
        # An expired claim on a done-pending task is the progression refusal:
        # the task status and the checkpoint records stay untouched.
        self.seed_claim(task="task-4", token="seed-task-4")
        driver = self.driver(seed_task3=False, clock=lambda: self.FIXED_NOW)
        landed = driver.record_worker_checkpoint(self.worker_checkpoint(task="task-4", checkpoint_identity="task-4:worker-1"))
        self.assertEqual(landed["state"], "done-pending")
        self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}))
        before = runtime.load_manifest(self.state_path)
        result = driver.reclaim("task-4")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(after["checkpoints"], before["checkpoints"])

    def test_reclaim_refuses_aborted_workflow(self):
        # An explicitly aborted workflow is never released, whatever the
        # lease state: the reclaim returns the explicit-abort
        # preserve-and-stop outcome and the manifest stays byte-identical.
        # The fresh-lease arm is the hoist discriminator: with the abort
        # fence below the lease check it would degrade to the stale-claim
        # lease refusal instead.
        for arm, timestamp in (("fresh-lease", self.FIXED_NOW), ("expired-lease", self._expired_lease_timestamp())):
            with self.subTest(lease=arm):
                self.seed_claim(task="task-4", token="seed-task-4", generation=0)
                self.rewrite_manifest(lambda state: (
                    state["claims"]["task-4"].update({"timestamp": timestamp}),
                    state.update({"workflow_state": "aborted"}),
                ))
                driver = self.driver(clock=lambda: self.FIXED_NOW)
                before = self.state_path.read_bytes()
                result = driver.reclaim("task-4")
                self.assertEqual(result["status"], "aborted")
                self.assertEqual(result["reason_code"], "explicit-abort")
                self.assertEqual(result["recovery_action"], "preserve-and-stop")
                self.assertFalse(result["resume_allowed"])
                self.assertEqual(self.state_path.read_bytes(), before)

    def test_reclaim_refused_under_complete_and_terminal_workflows(self):
        # The workflow-state fence covers the full closed non-active set:
        # an expired lease claim on a non-progressed task under a finished
        # workflow (complete, then terminal) is refused with the same
        # preserve-and-stop shape the abort fence returns, evidence naming
        # the finished state, and the manifest byte-identical. RED before
        # this task: the fence admitted only 'aborted', so a finished run's
        # claim was rotated by the reclaim.
        for arm in ("complete", "terminal"):
            with self.subTest(workflow=arm):
                self.seed_claim(task="task-4", token="seed-task-4", generation=0)
                self.rewrite_manifest(lambda state, name=arm: (
                    state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}),
                    state.update({"workflow_state": name}),
                ))
                driver = self.driver(clock=lambda: self.FIXED_NOW)
                before = self.state_path.read_bytes()
                result = driver.reclaim("task-4")
                self.assertEqual(result["status"], "aborted")
                self.assertEqual(result["recovery_action"], "preserve-and-stop")
                self.assertFalse(result["resume_allowed"])
                self.assertTrue(
                    any(f"workflow_state is '{arm}'" in entry for entry in result["evidence"]),
                    result["evidence"],
                )
                self.assertEqual(self.state_path.read_bytes(), before)
                after = runtime.load_manifest(self.state_path)
                self.assertEqual(after["claims"]["task-4"]["token"], "seed-task-4")
                self.assertEqual(after["claims"]["task-4"]["state"], "launched")

    def test_reclaim_preserves_other_claims(self):
        # Reclaiming an expired claim on one task leaves a live claim on
        # another task byte-identical.
        self.seed_fresh_pending_manifest()
        self.seed_claim(task="task-1", token="expired-task-1", generation=0)
        live_claim = {
            "token": "live-task-2",
            "generation": 0,
            "owner": "test-owner",
            "state": "launched",
            "task_id": "task-2",
            "timestamp": self.FIXED_NOW,
            "launch_record": {"baseline_revision": "", "generation": 0, "launched_at": self.FIXED_NOW},
        }
        self.rewrite_manifest(lambda state: state["claims"].update({"task-2": dict(live_claim)}))
        self.rewrite_manifest(lambda state: state["claims"]["task-1"].update({"timestamp": self._expired_lease_timestamp()}))
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        result = driver.reclaim("task-1")
        self.assertEqual(result["status"], "success")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["claims"]["task-2"], live_claim)
        self.assertEqual(after["claims"]["task-1"]["state"], "replaced")

    def test_reclaim_strips_dead_session_resume_fields(self):
        # The reclaim reset strips the previous session's resume fields: a
        # dead session_id, its resume_allowed flag, and the blocked receipt
        # must not survive on the freed task, or a later resume could route
        # into the dead session instead of a fresh claim.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)

        def seed_blocked(state):
            state["claims"]["task-4"].update({"state": "blocked", "timestamp": self._expired_lease_timestamp()})
            state["tasks"]["task-4"].update({
                "status": "blocked",
                "resume_allowed": True,
                "session_id": "dead-session",
                "blocked_receipt": {"status": "blocked", "reason_code": "timeout"},
            })

        self.rewrite_manifest(seed_blocked)
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        result = driver.reclaim("task-4")
        self.assertEqual(result["status"], "success")
        task = runtime.load_manifest(self.state_path)["tasks"]["task-4"]
        self.assertEqual(task["status"], "pending")
        for field in ("session_id", "resume_allowed", "blocked_receipt"):
            self.assertNotIn(field, task)

    def test_resume_recycle_strips_dead_session_resume_fields(self):
        # The resume-path claim recycle shares the rotation helper: with no
        # adapter, resuming a resumable blocked task recycles it to pending
        # through the same field-stripping reset, so the dead session's
        # session_id, resume_allowed flag, and blocked receipt never survive
        # (the replacement launch re-blocks on the missing adapter with its
        # own fresh receipt, not the dead session's).
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)

        def seed_resumable(state):
            state["claims"]["task-4"].update({
                "state": "blocked",
                "policy_token": {"generation": 0, "allowed_paths": ["task-4.txt"]},
            })
            state["tasks"]["task-4"].update({
                "status": "blocked",
                "resume_allowed": True,
                "session_id": "dead-session",
                "blocked_receipt": {"status": "blocked", "reason_code": "timeout"},
            })

        self.rewrite_manifest(seed_resumable)
        driver = self.driver()  # No adapter: the recycle path runs.
        result = driver.resume()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "runtime-policy-unavailable")
        state = runtime.load_manifest(self.state_path)
        # The recycle ran: the replaced seed claim was rotated for a fresh
        # claim (new token, bumped generation), which then launched and
        # re-blocked on the missing adapter.
        self.assertNotEqual(state["claims"]["task-4"]["token"], "seed-task-4")
        self.assertEqual(state["claims"]["task-4"]["generation"], 1)
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")
        task = state["tasks"]["task-4"]
        self.assertNotIn("session_id", task)
        self.assertIs(task.get("resume_allowed"), False)
        receipt = task.get("blocked_receipt", {})
        self.assertEqual(receipt.get("reason_code"), "runtime-policy-unavailable")
        self.assertNotIn("session_id", receipt if isinstance(receipt, dict) else {})

    def test_timeout_recovery_reconciles_without_duplicate_claim(self):
        # Regression pin (green before and after the deadline baseline
        # change): a session-less launch-deadline expiry (the worker died in
        # the launch window, so no session id exists anywhere) is reconciled
        # through the claim machinery exactly once. The resume recycle marks
        # the dead attempt's claim replaced and rotates the identity one
        # time; the recovery continuation re-claims the freed task as
        # exactly one live claim row (never a duplicate), and a late receipt
        # carrying the dead attempt's token fences as owner-mismatch instead
        # of resurrecting a second claim.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)

        def seed_dead_attempt(state):
            state["claims"]["task-4"].update({
                "state": "blocked",
                "policy_token": {"generation": 0, "allowed_paths": ["task-4.txt"]},
            })
            state["tasks"]["task-4"].update({
                "status": "blocked",
                "resume_allowed": True,
                "blocked_receipt": {"status": "blocked", "reason_code": "timeout", "evidence": ["launch deadline exceeded"]},
            })

        self.rewrite_manifest(seed_dead_attempt)

        def replacement_launch(task, prompt, generation, deadline_seconds=None, policy_token=None):
            return self.worker_checkpoint(
                task=task["id"],
                generation=generation,
                checkpoint_identity=f"{task['id']}:worker-replacement",
                evidence=["replacement-worker-log"],
            )

        driver = self.driver(adapter=FakeAdapter(result=replacement_launch))
        recovered = driver.resume()
        self.assertEqual(recovered["status"], "success", recovered)
        state = runtime.load_manifest(self.state_path)
        # Rotated exactly once: one fresh identity whose generation bumped
        # once from the dead attempt's generation 0, held by exactly one
        # claim row for the task.
        rows = [claim for claim in state["claims"].values() if claim.get("task_id") == "task-4"]
        self.assertEqual(len(rows), 1, state["claims"])
        replacement = rows[0]
        self.assertNotEqual(replacement["token"], "seed-task-4")
        self.assertEqual(replacement["generation"], 1)
        self.assertEqual(replacement["state"], "launched")
        # Exactly one resume rotation event and one replacement launch in
        # history: the dead attempt was never re-registered as a second
        # claim or a second launch record.
        self.assertEqual(len([item for item in state["history"] if item.get("event") == "resume"]), 1)
        self.assertEqual(len([item for item in state["history"] if item.get("event") == "started"]), 1)
        # The replacement worker's receipt landed on the freed task.
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")
        # The dead attempt's identity fences: its token claims nothing.
        late = self.worker_checkpoint(task="task-4", generation=0, checkpoint_identity="task-4:worker-dead", evidence=["dead-attempt-log"])
        late["claim_token"] = "seed-task-4"
        fenced = self.driver().record_worker_checkpoint(late)
        self.assertEqual(fenced["status"], "blocked")
        self.assertEqual(fenced["reason_code"], "owner-mismatch")
        state = runtime.load_manifest(self.state_path)
        rows = [claim for claim in state["claims"].values() if claim.get("task_id") == "task-4"]
        self.assertEqual(len(rows), 1, state["claims"])
        self.assertNotEqual(rows[0]["token"], "seed-task-4")

    def test_reclaim_then_continue_parent_succeeds(self):
        # Regression: reclaim success on a launched claim must not wedge
        # continuation. The replaced claim is reconciled by rotation, so
        # continue_parent after the reclaim claims the freed task and lands
        # the replacement worker's checkpoint instead of returning
        # owner-mismatch forever.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}))
        adapter = FakeAdapter(result=lambda task, prompt, generation, deadline_seconds=None, policy_token=None: {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["replacement-worker-log"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task['id']}:worker-replacement",
            "generation": generation,
        })
        driver = self.driver(clock=lambda: self.FIXED_NOW, adapter=adapter)
        self.assertEqual(driver.reclaim("task-4")["status"], "success")
        outcome = driver.continue_parent()
        self.assertEqual(outcome["status"], "success", outcome)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-4"]["state"], "launched")

    def test_reclaim_replaced_claim_reconciles_clean_startup(self):
        # Reclaim success must not wedge startup reconciliation: the replaced
        # claim (launch evidence retained) is reconciled by rotation, so a
        # clean-worktree reconcile_startup proceeds with no ambiguous claim
        # instead of quarantining the replaced claim as owner-mismatch.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}))
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        self.assertEqual(driver.reclaim("task-4")["status"], "success")
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"]["task-4"]["state"], "replaced")
        result = driver.reconcile_startup()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "completed")
        self.assertEqual(result["evidence"], ["no ambiguous claims"])

    def test_reclaim_replaced_claim_keeps_dirty_startup_blocked(self):
        # The dirty-worktree gate still applies after a reclaim: with the
        # replaced claim present (launch evidence retained), real untracked
        # dirt keeps the hard dirty-worktree block instead of rotating around
        # it.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}))
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        self.assertEqual(driver.reclaim("task-4")["status"], "success")
        (self.root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        result = driver.reconcile_startup()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "dirty-worktree")
        self.assertTrue(
            any("uncommitted worktree requires explicit reconciliation" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        # The replaced claim survived untouched (rotation, not quarantine).
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"]["task-4"]["state"], "replaced")

    def test_reclaim_cli_requires_task_id(self):
        # The CLI refuses --operation reclaim without --task-id before any
        # driver construction: non-zero exit and the manifest bytes stay
        # untouched.
        before = self.state_path.read_bytes()
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(self.state_path),
                "--repo-root", str(self.root),
                "--operation", "reclaim",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--task-id is required", completed.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_reclaim_cli_releases_expired_claim(self):
        # Happy-path CLI reclaim: the expired claim is rotated, the freed
        # task is pending again, and the JSON envelope reports the
        # replacement generation.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["claims"]["task-4"].update({"timestamp": self._expired_lease_timestamp()}))
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(self.state_path),
                "--repo-root", str(self.root),
                "--operation", "reclaim",
                "--task-id", "task-4",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "reclaimed")
        self.assertEqual(result["reclaimed_task"], "task-4")
        after = runtime.load_manifest(self.state_path)
        self.assertEqual(after["tasks"]["task-4"]["status"], "pending")
        self.assertEqual(after["claims"]["task-4"]["state"], "replaced")
        self.assertEqual(after["generation"], result["replacement_generation"])

    # ------------------------------------------------------------------
    # waiting-capacity durable state (capacity receipt parking).
    # ------------------------------------------------------------------

    WAITING_CAPACITY_PLAN = (
        "# Fixture plan\n\n### Task 3: third\n- [x] done item\n\n"
        "### Task 4: fourth\n- [ ] pending item\n"
    )

    def capacity_receipt(self, task="task-4", generation=0, **overrides):
        result = {
            "status": "blocked",
            "reason_code": "capacity-unavailable",
            "evidence": ["provider at capacity"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task}:worker-1",
            "generation": generation,
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def seed_parked_claim(self, task="task-4", token="seed-task-4", generation=0, timestamp=111.0):
        # Seed the durable parked shape directly: the claim state, the
        # standard bounded retry policy on the claim, and the blocked task
        # fields the parking branch writes.
        self.seed_claim(task=task, token=token, generation=generation)
        self.rewrite_manifest(lambda state: (
            state["claims"][task].update({
                "state": "waiting-capacity",
                "timestamp": timestamp,
                "retry_policy": {"mode": "bounded-resume", "max_attempts": 3, "attempts_remaining": 3},
            }),
            state["tasks"][task].update({
                "status": "blocked",
                "resume_allowed": False,
                "blocked_receipt": {"status": "blocked", "reason_code": "capacity-unavailable"},
            }),
        ))

    def test_capacity_receipt_parks_claim_waiting_capacity(self):
        # A capacity receipt on a single-task claim parks the claim in
        # waiting-capacity carrying the standard retry-policy shape; the
        # outcome carries the resume action in recovery_action (never a
        # next_action key) and history records the worker-blocked event with
        # the capacity reason code.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["tasks"]["task-4"].update({"status": "launched"}))
        outcome = self.driver().record_worker_checkpoint(self.capacity_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "capacity-unavailable")
        self.assertEqual(outcome["recovery_action"], "resume-same-claim")
        self.assertNotIn("next_action", outcome)
        state = runtime.load_manifest(self.state_path)
        claim = state["claims"]["task-4"]
        self.assertEqual(claim["state"], "waiting-capacity")
        self.assertEqual(claim["retry_policy"], {"mode": "bounded-resume", "max_attempts": 3, "attempts_remaining": 3})
        self.assertEqual(claim["token"], "seed-task-4")
        self.assertEqual(claim["generation"], 0)
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")
        self.assertEqual(state["tasks"]["task-4"]["resume_allowed"], False)
        self.assertEqual(state["tasks"]["task-4"]["blocked_receipt"]["reason_code"], "capacity-unavailable")
        blocked_events = [
            event for event in state["history"]
            if event.get("event") == "worker-blocked" and event.get("task_id") == "task-4"
        ]
        self.assertEqual([event.get("reason_code") for event in blocked_events], ["capacity-unavailable"])

    def test_waiting_capacity_claim_resumes_in_place(self):
        # A continue on a parked claim with retry budget remaining relaunches
        # the SAME claim: the new launch carries the same token and
        # generation, there is exactly one claim row, and no reclaim
        # rotation ran. The adapter returns another capacity receipt, so the
        # claim re-parks with one attempt consumed.
        self.seed_parked_claim()
        adapter = RecordingAdapter(launch_result={
            "status": "blocked",
            "reason_code": "capacity-unavailable",
            "evidence": ["provider at capacity"],
        })
        outcome = self.driver(adapter=adapter).continue_parent()
        self.assertEqual(outcome["reason_code"], "capacity-unavailable")
        self.assertEqual(outcome["recovery_action"], "resume-same-claim")
        self.assertEqual([call["generation"] for call in adapter.launch_calls], [0])
        state = runtime.load_manifest(self.state_path)
        claim = state["claims"]["task-4"]
        self.assertEqual(claim["state"], "waiting-capacity")
        self.assertEqual(claim["token"], "seed-task-4")
        self.assertEqual(claim["generation"], 0)
        self.assertEqual(claim["retry_policy"]["attempts_remaining"], 2)
        self.assertEqual(len(state["claims"]), 1)
        self.assertNotIn("claim-reclaimed", [event.get("event") for event in state["history"]])
        self.assertIn("started", [event.get("event") for event in state["history"]])

    def test_capacity_retry_exhaustion_moves_claim_to_blocked(self):
        # Successive capacity receipts consume the parked budget one attempt
        # at a time; the receipt that arrives once the budget is exhausted
        # transitions the claim to blocked, the existing reclaimable lease
        # state, under the same claim identity.
        self.seed_claim(task="task-4", token="seed-task-4", generation=0)
        self.rewrite_manifest(lambda state: state["tasks"]["task-4"].update({"status": "launched"}))
        driver = self.driver()
        driver.record_worker_checkpoint(self.capacity_receipt())
        for expected_remaining in (2, 1, 0):
            driver.record_worker_checkpoint(self.capacity_receipt())
            claim = runtime.load_manifest(self.state_path)["claims"]["task-4"]
            self.assertEqual(claim["state"], "waiting-capacity")
            self.assertEqual(claim["retry_policy"]["attempts_remaining"], expected_remaining)
        driver.record_worker_checkpoint(self.capacity_receipt())
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-4"]["state"], "blocked")
        self.assertIn(state["claims"]["task-4"]["state"], runtime.RECLAIMABLE_CLAIM_STATES)
        self.assertEqual(state["claims"]["task-4"]["token"], "seed-task-4")
        self.assertEqual(state["tasks"]["task-4"]["status"], "blocked")

    def test_waiting_capacity_claim_refuses_lease_reclaim(self):
        # A parked claim older than the claim lease is still refused: the
        # state is deliberately outside RECLAIMABLE_CLAIM_STATES while its
        # retry policy is live, the refusal names waiting-capacity, and the
        # manifest stays byte-identical.
        self.seed_parked_claim(timestamp=self._expired_lease_timestamp())
        driver = self.driver(clock=lambda: self.FIXED_NOW)
        before = runtime.load_manifest(self.state_path)
        result = driver.reclaim("task-4")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        self.assertTrue(any("waiting-capacity" in item for item in result["evidence"]))
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_manifest_validator_accepts_waiting_capacity_state(self):
        # The manifest validator's claim-state set includes waiting-capacity:
        # a parked claim passes schema validation instead of failing it.
        self.seed_parked_claim()
        validated = self.driver().refresh_manifest()
        self.assertEqual(validated["claims"]["task-4"]["state"], "waiting-capacity")

    def test_group_member_capacity_receipt_keeps_blocked_shape(self):
        # A capacity receipt on a live batch-group member never parks: the
        # member's claim takes the existing blocked shape with the capacity
        # reason code recorded on the group, and the group stays active (the
        # group path owns member recovery and the group fences stay
        # untouched). The receipt rides the member launch, mirroring the
        # batch timeout shape.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter(launch_result={
            "status": "blocked",
            "reason_code": "capacity-unavailable",
            "evidence": ["provider at capacity"],
        })
        driver = self.batch_driver(adapter=adapter)
        launch = driver.launch_next_task(batch=True)
        self.assertEqual(launch["reason_code"], "capacity-unavailable")
        state = runtime.load_manifest(self.state_path)
        claim = state["claims"]["task-1"]
        self.assertEqual(claim["state"], "blocked")
        self.assertNotEqual(claim.get("retry_policy", {}).get("mode"), "bounded-resume")
        group = self.live_group(state)
        self.assertEqual(group["state"], "active")
        self.assertEqual(group["member_attempts"]["task-1"]["receipt"]["reason_code"], "capacity-unavailable")
        blocked_events = [
            event for event in state["history"]
            if event.get("event") == "worker-blocked" and event.get("task_id") == "task-1"
        ]
        self.assertEqual([event.get("reason_code") for event in blocked_events], ["capacity-unavailable"])

    def test_readiness_routes_waiting_capacity_to_recovery(self):
        # A parked claim at the queue head is an unprovable next task: the
        # readiness decision is recovery with preserve-and-reconcile through
        # the existing unprovable-next-task condition, and the read-only
        # decision leaves the manifest byte-identical.
        self.seed_parked_claim()
        plan_path = self.write_plan(self.WAITING_CAPACITY_PLAN)
        driver = self.driver()
        before = runtime.load_manifest(self.state_path)
        result = driver.readiness(plan_path)
        self.assertEqual(result["decision"], "recovery")
        self.assertEqual(result["recovery_action"], "preserve-and-reconcile")
        self.assertTrue(
            any("next incomplete task 'task-4' is not provable" in item for item in result["failed_conditions"])
        )
        self.assertEqual(result["next_task_id"], "task-4")
        self.assertEqual(runtime.load_manifest(self.state_path), before)

    def test_changed_paths_delegates_to_worktree_entries(self):
        baseline = self.commit_file()
        # A second commit after the baseline keeps the worktree clean in the
        # status witness while still producing a tracked entry in
        # ``git diff --name-only <baseline>`` (the diff half of the union).
        self.commit_file(content="second committed change\n")
        (self.root / "notes.txt").write_text("untracked note\n", encoding="utf-8")
        (self.root / "t.txt").write_text("tracked edit\n", encoding="utf-8")
        driver = self.driver()
        original = driver._git_worktree_entries
        calls = []

        def counting_wrapper():
            calls.append(1)
            return original()

        driver._git_worktree_entries = counting_wrapper
        self.assertEqual(driver._git_changed_paths(baseline), ["notes.txt", "t.txt", "task-4.txt"])
        self.assertEqual(len(calls), 1)

    def test_address_fanout_state_round_trip_and_projection_fence(self):
        """runtime_state.json.address_fanout is the only live fan-out authority.

        Drives the real parent driver API through a reload: lifecycle
        transitions persist under the manifest lock, a stale attempt or
        projection generation cannot authorize a retry, patch application,
        or commit, and a lock-held finalization renders the manifest and
        sidecar projections from one current machine-state snapshot.
        """

        secret = "round-trip-secret"
        round_id = "r1"
        tokens = {
            worker: fanout.issue_scope_token(round_id, worker, "a1", secret)
            for worker in ("w1", "w2")
        }
        digests = {worker: fanout.token_digest(token) for worker, token in tokens.items()}
        grouping = [
            {"worker": "w1", "findings": [1, 2], "files": ["a.txt", "b.txt"]},
            {"worker": "w2", "findings": [3], "files": ["c.txt"]},
        ]
        workers = [
            {
                "worker": "w1",
                "attempt": "a1",
                "token_digest": digests["w1"],
                "findings": [1, 2],
                "files": ["a.txt", "b.txt"],
                "expected_paths": ["a.txt", "b.txt"],
                "log": "review-r1-receiving-review-w1.log.md",
            },
            {
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w2"],
                "findings": [3],
                "files": ["c.txt"],
                "expected_paths": ["c.txt"],
                "log": "review-r1-receiving-review-w2.log.md",
            },
        ]

        driver = self.driver()
        started = driver.record_address_fanout(
            {
                "kind": "start",
                "round": round_id,
                "baseline": "head",
                "grouping": grouping,
                "finding_files": [
                    {"id": 1, "files": ["a.txt"]},
                    {"id": 2, "files": ["a.txt", "b.txt"]},
                    {"id": 3, "files": ["c.txt"]},
                ],
                "workers": workers,
            }
        )
        self.assertEqual(started["status"], "success")
        self.assertEqual(started["address_fanout_generation"], 1)
        persisted = runtime.load_manifest(self.state_path)["address_fanout"]
        self.assertEqual(persisted["round"], round_id)
        self.assertEqual(persisted["status"], "active")
        self.assertEqual(persisted["workers"]["w1"]["expected_paths"], ["a.txt", "b.txt"])

        # Reload: a freshly constructed driver sees the same live record and
        # records the launches through the real parent driver API.
        reloaded = self.driver()
        reloaded.refresh_manifest()
        for worker in ("w1", "w2"):
            launched = reloaded.record_address_fanout(
                {
                    "kind": "attempt",
                    "round": round_id,
                    "worker": worker,
                    "attempt": "a1",
                    "token_digest": digests[worker],
                    "generation": 1,
                    "event": "launched",
                }
            )
            self.assertEqual(launched["status"], "success")

        # Active-attempt compare-and-swap: an accepted patch receipt must
        # name the worker, round, attempt, token digest, and generation.
        accepted = reloaded.record_address_fanout(
            {
                "kind": "accept",
                "round": round_id,
                "worker": "w1",
                "attempt": "a1",
                "token_digest": digests["w1"],
                "generation": 1,
                "changed_paths": ["a.txt"],
                "patch_digest": "d" * 64,
                "counts": {"fixed": 2, "dropped": 0, "deferred": 0, "pending": 0},
            }
        )
        self.assertEqual(accepted["status"], "success")
        self.assertEqual(
            runtime.load_manifest(self.state_path)["address_fanout"]["workers"]["w1"]["accepted"]["attempt"],
            "a1",
        )

        snapshot = runtime.load_manifest(self.state_path)
        # A forged token digest is quarantined and cannot mutate machine state.
        forged = reloaded.record_address_fanout(
            {
                "kind": "accept",
                "round": round_id,
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w1"],
                "generation": 1,
                "changed_paths": ["c.txt"],
                "patch_digest": "e" * 64,
            }
        )
        self.assertEqual(forged["status"], "blocked")
        self.assertTrue(forged["quarantined"])
        self.assertEqual(forged["reason_code"], fanout.REASON_STALE_ATTEMPT)
        self.assertEqual(runtime.load_manifest(self.state_path), snapshot)
        # A stale parent generation is quarantined the same way.
        stale_generation = reloaded.record_address_fanout(
            {
                "kind": "accept",
                "round": round_id,
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w2"],
                "generation": 99,
                "changed_paths": ["c.txt"],
                "patch_digest": "f" * 64,
            }
        )
        self.assertEqual(stale_generation["status"], "blocked")
        self.assertTrue(stale_generation["quarantined"])
        self.assertEqual(runtime.load_manifest(self.state_path), snapshot)

        # Lock-held finalization renders BOTH projections from one current
        # snapshot with the same generation and authorizes the round's
        # single address commit. Production run_address_fanout terminalizes
        # every attempt before finalize; the parent cancels w2's active
        # attempt first so the projection carries closed-enum rows only.
        w2_cancelled = reloaded.record_address_fanout(
            {
                "kind": "attempt",
                "round": round_id,
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w2"],
                "generation": 1,
                "event": "cancelled-verified",
                "reason_code": fanout.REASON_SUPERSEDED,
            }
        )
        self.assertEqual(w2_cancelled["status"], "success")
        manifest_projection = self.root / "manifest-projection.md"
        sidecar = self.root / "stats.json"
        finalized = reloaded.finalize_address_fanout(round_id, 1, manifest_projection, sidecar)
        self.assertEqual(finalized["status"], "success")
        self.assertTrue(finalized["commit_authorized"])
        self.assertEqual(finalized["address_fanout_generation"], 1)
        self.assertIn("round: r1", manifest_projection.read_text(encoding="utf-8"))
        rendered = json.loads(sidecar.read_text(encoding="utf-8"))["extensions"]["address_fanout"]
        # The sidecar projection is the closed three-key spec; the
        # generation and terminal map stay in machine state.
        self.assertEqual(set(rendered), {"round", "finding_files", "workers"})
        self.assertEqual(rendered["round"], "r1")
        self.assertEqual([worker["id"] for worker in rendered["workers"]], ["w1", "w2"])
        for worker in rendered["workers"]:
            for attempt in worker["attempts"]:
                self.assertIn(attempt["status"], ("success", "blocked", "cancelled"))
                self.assertIn(attempt["reason_code"], vrs.ADDRESS_FANOUT_REASON_CODES)

        # Post-finalization the record is closed: a retry attempt is refused,
        # and re-finalizing cannot advertise completion a second time.
        post_finalize = reloaded.record_address_fanout(
            {
                "kind": "attempt",
                "round": round_id,
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w2"],
                "generation": 1,
                "event": "launched",
            }
        )
        self.assertEqual(post_finalize["status"], "blocked")
        finalized_snapshot = runtime.load_manifest(self.state_path)
        again = reloaded.finalize_address_fanout(round_id, 1, manifest_projection, sidecar)
        self.assertEqual(again["status"], "blocked")
        self.assertFalse(again["commit_authorized"])
        self.assertEqual(runtime.load_manifest(self.state_path), finalized_snapshot)

        # A tampered sidecar projection authorizes nothing: the machine state
        # stays the sole live authority.
        tampered = json.loads(sidecar.read_text(encoding="utf-8"))
        tampered["extensions"]["address_fanout"]["round"] = "rX"
        sidecar.write_text(json.dumps(tampered), encoding="utf-8")
        spoofed = reloaded.record_address_fanout(
            {
                "kind": "attempt",
                "round": round_id,
                "worker": "w2",
                "attempt": "a1",
                "token_digest": digests["w2"],
                "generation": 99,
                "event": "launched",
            }
        )
        self.assertEqual(spoofed["status"], "blocked")
        self.assertEqual(runtime.load_manifest(self.state_path), finalized_snapshot)
        spoofed_finalize = reloaded.finalize_address_fanout(round_id, 99, manifest_projection, sidecar)
        self.assertEqual(spoofed_finalize["status"], "blocked")
        self.assertFalse(spoofed_finalize["commit_authorized"])

        # A new round supersedes with a monotonic fan-out generation, and a
        # projection-writer failure refuses to advertise completion.
        superseding = reloaded.record_address_fanout(
            {
                "kind": "start",
                "round": "r2",
                "baseline": "head2",
                "grouping": grouping,
                "workers": workers,
            }
        )
        self.assertEqual(superseding["status"], "success")
        self.assertEqual(superseding["address_fanout_generation"], 2)
        self.assertEqual(superseding["address_fanout"]["predecessor_generation"], 1)
        broken = reloaded.finalize_address_fanout(
            "r2",
            2,
            manifest_projection,
            sidecar,
            projection_writer=lambda path, text: (_ for _ in ()).throw(OSError("disk full")),
        )
        self.assertEqual(broken["status"], "blocked")
        self.assertEqual(broken["reason_code"], "projection-failed")
        self.assertFalse(broken["commit_authorized"])
        self.assertEqual(runtime.load_manifest(self.state_path)["address_fanout"]["status"], "active")
        good = reloaded.finalize_address_fanout("r2", 2, manifest_projection, sidecar)
        self.assertEqual(good["status"], "success")
        self.assertTrue(good["commit_authorized"])
        self.assertEqual(json.loads(sidecar.read_text(encoding="utf-8"))["extensions"]["address_fanout"]["round"], "r2")

    def test_changed_paths_returns_none_when_status_witness_raises(self):
        baseline = self.commit_file()
        driver = self.driver()
        def failing_witness():
            raise RuntimeError("git status witness failed")

        driver._git_worktree_entries = failing_witness
        self.assertIsNone(driver._git_changed_paths(baseline))

    def test_changed_paths_returns_none_when_diff_witness_fails(self):
        self.commit_file()
        driver = self.driver()
        # An unknown baseline revision makes ``git diff --name-only <baseline>``
        # exit non-zero; the method must fail closed to None, not raise.
        self.assertIsNone(driver._git_changed_paths("0" * 40))


    # ------------------------------------------------------------------
    # Batch implement launch claim groups (Step 1.2 batch contract)
    # ------------------------------------------------------------------

    def batch_manifest(self, tasks):
        # Re-seed the gitignored runtime_state.json with the given pending
        # task list; canonicalization persists through the real create path.
        runtime.create_manifest(self.state_path, "fixture-plan", tasks, repo_root=self.root)
        return self.state_path

    def batch_driver(self, adapter=None, **kwargs):
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="fixture-plan",
            owner=kwargs.pop("owner", "test-owner"),
            repo_root=self.root,
            commit_lookup=lambda _commit: True,
            adapter=adapter,
            **kwargs,
        )

    def disjoint_tasks(self, count, files_per_task=1, prefix="t"):
        tasks = []
        for n in range(1, count + 1):
            paths = [f"./{prefix}{n}-{k}.txt" for k in range(1, files_per_task + 1)]
            tasks.append({"id": f"task-{n}", "number": n, "status": "pending", "checkbox": False, "allowed_paths": paths})
        return tasks

    def commit_files(self, *names):
        # Content carries a per-call revision so re-committing a previously
        # committed file always produces a real (non-empty) commit.
        self._commit_revision = getattr(self, "_commit_revision", 0) + 1
        for name in names:
            (self.root / name).write_text(f"committed change {name} r{self._commit_revision}\n", encoding="utf-8")
        subprocess.run(["git", "add", *names], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "commit", "-qm", f"fixture commit {' '.join(names)} r{self._commit_revision}"], cwd=self.root, check=True, env=self._git_env)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=True, env=self._git_env).stdout.strip()

    def live_group(self, manifest):
        groups = [group for group in manifest.get("claim_groups", {}).values() if isinstance(group, dict)]
        self.assertEqual(len(groups), 1)
        return groups[0]

    def member_receipt(self, task, ordinal, generation, **overrides):
        result = {
            "status": "success",
            "reason_code": "completed",
            "evidence": [f"worker-log:{task}"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task}:worker",
            "generation": generation,
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def member_done(self, task, ordinal, commit, generation=1, **overrides):
        result = {
            "status": "success",
            "reason_code": "completed",
            "evidence": [f"done-log:{task}"],
            "action_scope": "done-handoff",
            "checkpoint_identity": f"{task}:done",
            "generation": generation,
            "task_id": task,
            "commit_identity": commit,
            "checkbox": True,
            "clean_state": True,
            "log_evidence": [f"task-{ordinal}-implement.log.md"],
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def test_batch_claim_assembles_canonical_disjoint_prefix(self):
        # given: three consecutive pending tasks whose manifest-seeded
        # canonical allowed_paths are disjoint.
        self.batch_manifest(self.disjoint_tasks(3))
        result = self.batch_driver().claim_next_task(batch=True)
        # expects: one group with ordered members, explicit ordinals, one
        # generation bump, and member claims referencing that group.
        self.assertTrue(result["claimed"])
        self.assertEqual(result["members"], ["task-1", "task-2", "task-3"])
        self.assertEqual(result["member_ordinals"], {"task-1": 1, "task-2": 2, "task-3": 3})
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["generation"], 1)
        group = self.live_group(manifest)
        self.assertEqual(group["group_id"], result["group_id"])
        self.assertEqual(group["anchor"], "task-1")
        self.assertEqual(group["members"], ["task-1", "task-2", "task-3"])
        self.assertEqual(group["active_member"], "task-1")
        self.assertEqual(group["generation"], 1)
        self.assertEqual(group["state"], "active")
        for member, ordinal in result["member_ordinals"].items():
            claim = manifest["claims"][member]
            self.assertEqual(claim["group_id"], result["group_id"])
            self.assertEqual(claim["member_ordinal"], ordinal)
            self.assertEqual(claim["allowed_paths"], [f"t{ordinal}-1.txt"])
        self.assertEqual(manifest["tasks"]["task-1"]["status"], "claimed")
        self.assertEqual(manifest["tasks"]["task-2"]["status"], "pending")
        self.assertEqual(manifest["tasks"]["task-3"]["status"], "pending")

    def test_manifest_create_persists_canonical_paths_and_document_ordinals(self):
        (self.root / "a.txt").write_text("target\n", encoding="utf-8")
        (self.root / "link.txt").symlink_to("a.txt")
        # within-task duplicate after lexical alias resolution is rejected
        with self.assertRaises(ValueError):
            runtime.create_manifest(
                self.root / "dup_lexical.json",
                "fixture-plan",
                [{"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./a.txt", "a.txt"]}],
                repo_root=self.root,
            )
        # within-task duplicate after in-repository symlink resolution is rejected
        with self.assertRaises(ValueError):
            runtime.create_manifest(
                self.root / "dup_symlink.json",
                "fixture-plan",
                [{"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["link.txt", "a.txt"]}],
                repo_root=self.root,
            )
        for candidate in ("dup_lexical.json", "dup_symlink.json"):
            self.assertFalse((self.root / candidate).exists())
        # canonical paths and document ordinals persist; cross-task overlap
        # is retained for queue stopping rather than silently rewritten.
        self.batch_manifest([
            {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./t1.txt"]},
            {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["t2.txt"]},
            {"id": "task-3", "number": 3, "status": "pending", "allowed_paths": ["t1.txt"]},
        ])
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["tasks"]["task-1"]["allowed_paths"], ["t1.txt"])
        self.assertEqual(manifest["tasks"]["task-2"]["allowed_paths"], ["t2.txt"])
        self.assertEqual(manifest["tasks"]["task-3"]["allowed_paths"], ["t1.txt"])
        self.assertEqual([manifest["tasks"][f"task-{n}"]["ordinal"] for n in (1, 2, 3)], [0, 1, 2])
        # ordinals survive reload through real validation
        driver = self.batch_driver()
        validated = driver.validate_manifest()
        self.assertEqual(validated["tasks"]["task-2"]["ordinal"], 1)
        # the CLI create operation persists canonical paths too
        created = self.root / "cli_created.json"
        command = [
            sys.executable,
            str(ROOT / "scripts/execute_plan_runtime.py"),
            "--manifest", str(created),
            "--repo-root", str(self.root),
            "--owner", "create-owner",
            "--plan-slug", "cli-plan",
            "--operation", "create",
            "--input", json.dumps({"tasks": [{"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./c1.txt"]}]}),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(runtime.load_manifest(created)["tasks"]["task-1"]["allowed_paths"], ["c1.txt"])

    def test_batch_claim_stops_at_canonical_alias_overlap(self):
        # lexical alias fixture: ./t1.txt and t1.txt resolve to one canonical path
        self.batch_manifest([
            {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./t1.txt"]},
            {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["t1.txt"]},
            {"id": "task-3", "number": 3, "status": "pending", "allowed_paths": ["t3.txt"]},
        ])
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["tasks"]["task-1"]["allowed_paths"], ["t1.txt"])
        self.assertEqual(manifest["tasks"]["task-2"]["allowed_paths"], ["t1.txt"])
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(result["claimed"])
        self.assertNotIn("group_id", result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(set(manifest["claims"]), {"task-1"})
        # symlink alias fixture: an in-repository link resolves to its target
        (self.root / "real.txt").write_text("target\n", encoding="utf-8")
        (self.root / "alias.txt").symlink_to("real.txt")
        self.batch_manifest([
            {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["alias.txt"]},
            {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["real.txt"]},
        ])
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["tasks"]["task-1"]["allowed_paths"], ["real.txt"])
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(result["claimed"])
        self.assertNotIn("group_id", result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(set(manifest["claims"]), {"task-1"})

    def test_batch_claim_stops_at_overlap_and_caps(self):
        # an overlapping second task stops the maximal prefix before it even
        # though six later tasks are disjoint: no skipping past overlap.
        tasks = [
            {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["a.txt"]},
            {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["a.txt"]},
        ]
        tasks.extend({"id": f"task-{n}", "number": n, "status": "pending", "allowed_paths": [f"x{n}.txt"]} for n in range(3, 9))
        self.batch_manifest(tasks)
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(result["claimed"])
        self.assertNotIn("group_id", result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        # six disjoint tasks cap the prefix at four members
        self.batch_manifest(self.disjoint_tasks(6))
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertEqual(result["members"], ["task-1", "task-2", "task-3", "task-4"])
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        self.assertEqual(group["members"], ["task-1", "task-2", "task-3", "task-4"])
        self.assertEqual(manifest["tasks"]["task-5"]["status"], "pending")
        # combined canonical files cap at eight: 3 + 3 stops, a third 3-file
        # member would reach nine
        self.batch_manifest(self.disjoint_tasks(3, files_per_task=3))
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertEqual(result["members"], ["task-1", "task-2"])
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        combined = sum(len(paths) for paths in group["member_paths"].values())
        self.assertEqual(combined, 6)
        self.assertEqual(manifest["tasks"]["task-3"]["status"], "pending")

    def test_batch_claim_single_task_and_no_opt_in_are_field_free(self):
        # one pending task: the batch opt-in still yields today's single-task
        # result with no batch fields
        self.batch_manifest(self.disjoint_tasks(1))
        result = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(result["claimed"])
        for field in ("group_id", "members", "member_ordinals", "batch"):
            self.assertNotIn(field, result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        # a no-flag claim keeps today's single-task result field-free
        self.batch_manifest(self.disjoint_tasks(3))
        result = self.batch_driver().claim_next_task()
        self.assertTrue(result["claimed"])
        self.assertEqual(result["task_id"], "task-1")
        for field in ("group_id", "members", "member_ordinals", "batch"):
            self.assertNotIn(field, result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(len(manifest["claims"]), 1)

    def test_batch_group_has_one_anchor_launch_record(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        claim = driver.claim_next_task(batch=True)
        self.assertTrue(claim["claimed"])
        result = driver.launch_next_task(batch=True)
        self.assertEqual(result["status"], "success")
        group_id = claim["group_id"]
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        self.assertEqual(group["anchor"], "task-1")
        self.assertEqual(group["active_member"], "task-1")
        self.assertEqual(group["state"], "active")
        self.assertEqual(group["generation"], 1)
        self.assertIsInstance(group["launch_record"], dict)
        self.assertEqual(group["launch_record"]["generation"], group["generation"])
        self.assertTrue(group["launch_record"]["baseline_revision"])
        self.assertEqual(group["anchor_session"], adapter.session_id)
        # exactly one launch-record slot lives on the group
        record_holders = [g["group_id"] for g in manifest["claim_groups"].values() if isinstance(g.get("launch_record"), dict)]
        self.assertEqual(record_holders, [group_id])
        for member in group["members"]:
            self.assertNotIn("launch_record", manifest["claims"][member])
        # member claims hold only their own canonical paths, member token,
        # ordinal, and group reference
        anchor_claim = manifest["claims"]["task-1"]
        self.assertEqual(anchor_claim["allowed_paths"], ["t1-1.txt"])
        self.assertEqual(anchor_claim["policy_token"]["allowed_paths"], ["t1-1.txt"])
        self.assertEqual(anchor_claim["group_id"], group_id)
        self.assertEqual(anchor_claim["member_ordinal"], 1)
        self.assertEqual(anchor_claim["baseline_revision"], group["launch_record"]["baseline_revision"])
        for member, path in (("task-2", "t2-1.txt"), ("task-3", "t3-1.txt")):
            staged = manifest["claims"][member]
            self.assertEqual(staged["state"], "staged")
            self.assertEqual(staged["allowed_paths"], [path])
            self.assertEqual(staged["group_id"], group_id)
            self.assertNotIn("policy_token", staged)
            self.assertNotIn("baseline_revision", staged)

    def state_fingerprint(self):
        # Driver construction refreshes updated_at under the manifest lock,
        # so no-mutation witnesses compare state with updated_at removed.
        state = runtime.load_manifest(self.state_path)
        state.pop("updated_at", None)
        return state

    def test_batch_member_policy_is_scoped(self):
        # checkpoint arm: member 1's launch hits a timeout, then its resume
        # receipt claims success while member 2's file changed in the
        # worktree
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter(launch_result={"status": "blocked", "reason_code": "timeout", "evidence": ["deadline exceeded"], "resume_allowed": True})
        driver = self.batch_driver(adapter=adapter)
        driver.claim_next_task(batch=True)
        launch = driver.launch_next_task(batch=True)
        self.assertEqual(launch["status"], "blocked")
        self.assertEqual(launch["reason_code"], "timeout")
        (self.root / "t2-1.txt").write_text("foreign change\n", encoding="utf-8")
        driver = self.batch_driver(adapter=RecordingAdapter())
        resumed = driver.resume()
        self.assertEqual(resumed["status"], "blocked")
        self.assertEqual(resumed["reason_code"], "contract-violation")
        self.assertTrue(any("t2-1.txt" in item for item in resumed["evidence"]))
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        # the witness-only union stayed on the group record and never
        # authorized the foreign path
        self.assertEqual(group["member_paths"], {"task-1": ["t1-1.txt"], "task-2": ["t2-1.txt"]})
        self.assertEqual(group["member_paths"]["task-2"], ["t2-1.txt"])
        (self.root / "t2-1.txt").unlink()
        # done boundary arm: member 1's commit touches member 2's file
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        receipt = self.member_receipt("task-1", 1, 1)
        self.assertEqual(driver.record_worker_checkpoint(receipt)["status"], "success")
        commit = self.commit_files("t1-1.txt", "t2-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit))
        self.assertEqual(done["status"], "blocked")
        self.assertEqual(done["reason_code"], "commit-pending")
        self.assertTrue(any("t2-1.txt" in item for item in done["evidence"]))
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["claims"]["task-1"]["state"], "launched")

    def test_batch_member_progress_resumes_anchor_session(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        group_id = group["group_id"]
        first_record = dict(group["launch_record"])
        anchor_session = group["anchor_session"]
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        action = done["actions"][0]
        self.assertEqual(action["type"], "resume_member")
        self.assertEqual(action["group_id"], group_id)
        self.assertEqual(action["task_id"], "task-2")
        self.assertEqual(action["member_ordinal"], 2)
        self.assertEqual(action["session_id"], anchor_session)
        self.assertEqual(action["baseline_revision"], commit1)
        manifest = runtime.load_manifest(self.state_path)
        group = manifest["claim_groups"][group_id]
        self.assertEqual(group["active_member"], "task-2")
        self.assertEqual(group["launch_record"], first_record)
        self.assertEqual(group["anchor_session"], anchor_session)
        attempt = group["member_attempts"]["task-2"]
        self.assertEqual(attempt["baseline_revision"], commit1)
        claim1 = manifest["claims"]["task-1"]
        claim2 = manifest["claims"]["task-2"]
        self.assertNotEqual(claim2["policy_token"]["token"], claim1["policy_token"]["token"])
        self.assertEqual(claim2["policy_token"]["allowed_paths"], ["t2-1.txt"])
        self.assertEqual(claim2["baseline_revision"], commit1)
        # resume without a second launch record: the anchor session is
        # reused with member 2's own token
        fresh = self.batch_driver(adapter=adapter)
        resumed = fresh.continue_parent(batch=True)
        self.assertEqual(resumed["status"], "success")
        self.assertEqual(len(adapter.launch_calls), 1)
        self.assertEqual(adapter.resume_calls[0]["session_id"], anchor_session)
        self.assertEqual(adapter.resume_calls[0]["task_id"], "task-2")
        self.assertEqual(adapter.resume_calls[0]["policy_token"]["allowed_paths"], ["t2-1.txt"])
        manifest = runtime.load_manifest(self.state_path)
        holders = [g["group_id"] for g in manifest["claim_groups"].values() if isinstance(g.get("launch_record"), dict)]
        self.assertEqual(holders, [group_id])
        self.assertEqual(manifest["claim_groups"][group_id]["launch_record"], first_record)

    def test_batch_done_returns_typed_resume_member_action(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        self.assertEqual(len(adapter.launch_calls), 1)
        self.assertEqual(adapter.launch_calls[0]["task_id"], "task-1")
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        self.assertEqual(done["actions"][0]["type"], "resume_member")
        # generic next-claim is suppressed while the group is live
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(set(manifest["claims"]), {"task-1", "task-2", "task-3"})
        self.assertEqual(manifest["tasks"]["task-3"]["status"], "pending")
        # member 2 advances only through resume, never a second launch
        driver = self.batch_driver(adapter=adapter)
        resumed = driver.continue_parent(batch=True)
        self.assertEqual(resumed["status"], "success")
        self.assertEqual(len(adapter.launch_calls), 1)
        commit2 = self.commit_files("t2-1.txt")
        done2 = driver.record_done(self.member_done("task-2", 2, commit2))
        self.assertEqual(done2["status"], "success")
        self.assertEqual(done2["actions"][0]["type"], "resume_member")
        self.assertEqual(done2["actions"][0]["member_ordinal"], 3)
        self.assertEqual(len(adapter.launch_calls), 1)

    def test_batch_member2_witnesses_from_member1_done(self):
        self.batch_manifest(self.disjoint_tasks(4))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commits = {}
        for ordinal, task in enumerate(("task-1", "task-2", "task-3", "task-4"), start=1):
            if ordinal > 1:
                driver = self.batch_driver(adapter=adapter)
                advanced = driver.continue_parent(batch=True)
                self.assertEqual(advanced["status"], "success")
            if ordinal == 3:
                # stale predecessor: member 3 cannot close over member 1's
                # commit; it is not new work on member 2's baseline
                stale = driver.record_done(self.member_done(task, ordinal, commits["task-1"]))
                self.assertEqual(stale["status"], "blocked")
                self.assertEqual(stale["reason_code"], "commit-pending")
                self.assertTrue(any("not new work" in item for item in stale["evidence"]))
            commits[task] = self.commit_files(f"t{ordinal}-1.txt")
            done = driver.record_done(self.member_done(task, ordinal, commits[task]))
            self.assertEqual(done["status"], "success")
            manifest = runtime.load_manifest(self.state_path)
            self.assertEqual(manifest["claims"][task]["state"], "closed")
        # foreign path rejection in a fresh two-member fixture: a member's
        # done commit may only touch its own canonical paths (a foreign
        # commit inside a member window would poison every later diff, so
        # this arm gets its own group)
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        self.assertEqual(driver.record_done(self.member_done("task-1", 1, commit1))["status"], "success")
        driver = self.batch_driver(adapter=RecordingAdapter())
        self.assertEqual(driver.continue_parent(batch=True)["status"], "success")
        foreign = self.commit_files("t1-1.txt")
        rejected = driver.record_done(self.member_done("task-2", 2, foreign))
        self.assertEqual(rejected["status"], "blocked")
        self.assertEqual(rejected["reason_code"], "commit-pending")
        self.assertTrue(any("out-of-scope committed change: t1-1.txt" in item for item in rejected["evidence"]))

    def test_batch_mid_member_failure_preserves_prefix_and_suffix(self):
        self.batch_manifest(self.disjoint_tasks(4))
        adapter = RecordingAdapter(resume_result={"status": "blocked", "reason_code": "timeout", "evidence": ["resume deadline exceeded"], "resume_allowed": True})
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        anchor_session = group["anchor_session"]
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["actions"][0]["type"], "resume_member")
        fresh = self.batch_driver(adapter=adapter)
        resumed = fresh.continue_parent(batch=True)
        self.assertEqual(resumed["status"], "blocked")
        self.assertEqual(resumed["reason_code"], "timeout")
        manifest = runtime.load_manifest(self.state_path)
        group = manifest["claim_groups"][done["actions"][0]["group_id"]]
        # member 1 closed, member 2 blocked with its attempt receipt, later
        # members pending
        self.assertEqual(manifest["claims"]["task-1"]["state"], "closed")
        self.assertEqual(manifest["claims"]["task-2"]["state"], "blocked")
        self.assertEqual(manifest["tasks"]["task-2"]["status"], "blocked")
        self.assertEqual(manifest["tasks"]["task-3"]["status"], "pending")
        self.assertEqual(manifest["tasks"]["task-4"]["status"], "pending")
        self.assertEqual(manifest["claims"]["task-3"]["state"], "staged")
        self.assertEqual(manifest["claims"]["task-4"]["state"], "staged")
        attempt = group["member_attempts"]["task-2"]
        self.assertEqual(attempt["receipt"]["reason_code"], "timeout")
        self.assertEqual(group["active_member"], "task-2")
        # resume selects only the first unfinished member through the anchor
        # session
        resume_adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=resume_adapter)
        result = driver.resume()
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(resume_adapter.resume_calls), 1)
        self.assertEqual(resume_adapter.resume_calls[0]["session_id"], anchor_session)
        self.assertEqual(resume_adapter.resume_calls[0]["task_id"], "task-2")
        self.assertEqual(resume_adapter.resume_calls[0]["policy_token"]["allowed_paths"], ["t2-1.txt"])
        self.assertEqual(len(resume_adapter.launch_calls), 0)

    def test_batch_done_closes_members_individually(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        for ordinal, task in enumerate(("task-1", "task-2", "task-3"), start=1):
            if ordinal > 1:
                driver = self.batch_driver(adapter=adapter)
                advanced = driver.continue_parent(batch=True)
                self.assertEqual(advanced["status"], "success")
            commit = self.commit_files(f"t{ordinal}-1.txt")
            done = driver.record_done(self.member_done(task, ordinal, commit))
            self.assertEqual(done["status"], "success")
            manifest = runtime.load_manifest(self.state_path)
            self.assertEqual(manifest["claims"][task]["state"], "closed")
            group = self.live_group(manifest)
            if ordinal < 3:
                self.assertEqual(group["state"], "active")
            else:
                self.assertEqual(group["state"], "closed")
                self.assertIsNone(group["active_member"])

    def test_batch_late_receipt_is_rejected(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]
        closed = runtime.load_manifest(self.state_path)["claims"]["task-1"]
        late_success = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["late"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1:worker",
            "generation": 1,
            "claim_token": closed["token"],
        }
        late_error = dict(late_success, status="error", reason_code="runtime-error", evidence=["late failure"])
        late_done = self.member_done("task-1", 1, commit1)
        before = self.state_fingerprint()
        # success, error, and done receipts for a closed member are late
        for label, receipt in (("success", late_success), ("error", late_error)):
            outcome = self.batch_driver().record_worker_checkpoint(receipt)
            self.assertEqual(outcome["status"], "blocked", label)
            self.assertEqual(outcome["reason_code"], "stale-claim", label)
            self.assertEqual(self.state_fingerprint(), before, label)
        outcome = self.batch_driver().record_done(late_done)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertEqual(self.state_fingerprint(), before)
        # old-attempt receipt: the batch progress attempt does not match the
        # live member attempt
        active = runtime.load_manifest(self.state_path)["claims"]["task-2"]
        old_attempt = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["stale attempt"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-2:worker",
            "generation": 1,
            "claim_token": active["token"],
            "batch_progress": {"batch_id": group_id, "member_id": "task-2", "member_ordinal": 2, "attempt": 3, "session_id": anchor_session},
        }
        outcome = self.batch_driver().record_worker_checkpoint(old_attempt)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertEqual(self.state_fingerprint(), before)
        # superseded member: a replaced claim is refused the same way
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-2"]["state"] = "replaced"
        runtime._safe_write_json(self.state_path, state)
        superseded_receipt = dict(old_attempt)
        superseded_receipt["batch_progress"] = {"batch_id": group_id, "member_id": "task-2", "member_ordinal": 2, "attempt": 1, "session_id": anchor_session}
        superseded_before = self.state_fingerprint()
        outcome = self.batch_driver().record_worker_checkpoint(superseded_receipt)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertEqual(self.state_fingerprint(), superseded_before)
        # aborted member: the receipt is a late receipt for an aborted member
        # and fails closed as stale-claim with no state mutation
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter(launch_result={"status": "blocked", "reason_code": "timeout", "evidence": ["deadline exceeded"], "resume_allowed": True}))
        claimed = driver.claim_next_task(batch=True)
        driver.launch_next_task(batch=True)
        driver.abort("task-1", claimed["token"])
        aborted_before = self.state_fingerprint()
        receipt = self.member_receipt("task-1", 1, 1, claim_token=claimed["token"])
        outcome = self.batch_driver().record_worker_checkpoint(receipt)
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "stale-claim")
        self.assertEqual(self.state_fingerprint(), aborted_before)

    def test_batch_member_envelope_checkpoint_passes_member_fence(self):
        # A live member checkpoint carrying the documented
        # batch_progress envelope (the normalized shape the codex adapter
        # emits: batch_id, member_id, member_ordinal, attempt, session_id,
        # and no claim token inside the envelope) passes the member receipt
        # fence and checkpoints. Pre-fix, the fence demanded claim_token
        # inside the normalized envelope, which it can never carry, so every
        # conforming member checkpoint was fenced stale-claim.
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]
        active = runtime.load_manifest(self.state_path)["claims"]["task-2"]
        receipt = self.member_receipt("task-2", 2, active["generation"])
        receipt["batch_progress"] = {
            "batch_id": group_id,
            "member_id": "task-2",
            "member_ordinal": 2,
            "attempt": 1,
            "session_id": anchor_session,
        }
        outcome = self.batch_driver().record_worker_checkpoint(receipt)
        self.assertEqual(outcome["status"], "success", outcome)
        self.assertEqual(outcome["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertIn("task-2:worker", state["checkpoints"])

    def test_batch_sessionless_timeout_wedge_recovers_through_launch(self):
        # A launch-window timeout before the first receipt leaves the
        # active member blocked with no session anywhere (no task session,
        # no anchor session). Pre-fix, resume and continue returned
        # stale-claim forever and only a manual abort ended the run,
        # stranding later members. Post-fix, the member recycles through a
        # rotated identity into a fresh launch, the group advances, and a
        # late receipt carrying the dead attempt's claim token fences shut.
        self.batch_manifest(self.disjoint_tasks(2))

        class TimeoutAdapter:
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                raise TimeoutError("launch deadline exceeded")

        driver = self.batch_driver(adapter=TimeoutAdapter())
        driver.claim_next_task(batch=True)
        blocked = driver.launch_next_task(batch=True)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["reason_code"], "timeout")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-1"]["status"], "blocked")
        self.assertTrue(state["tasks"]["task-1"]["resume_allowed"])
        self.assertIsNone(state["tasks"]["task-1"].get("session_id"))
        self.assertIsNone(self.live_group(state).get("anchor_session"))
        dead_token = state["claims"]["task-1"]["token"]

        # The wedge: resume (and continue) must not answer stale-claim
        # forever; the session-less blocked member recycles into a fresh
        # launch through the rotated identity.
        driver = self.batch_driver(adapter=RecordingAdapter())
        recovered = driver.resume()
        self.assertEqual(recovered["status"], "success", recovered)
        state = runtime.load_manifest(self.state_path)
        self.assertNotEqual(state["claims"]["task-1"]["token"], dead_token)
        self.assertEqual(state["claims"]["task-1"]["attempt"], 2)
        self.assertEqual(state["claims"]["task-1"]["state"], "launched")
        self.assertEqual(self.live_group(state)["member_attempts"]["task-1"]["attempt"], 2)
        self.assertIsNotNone(self.live_group(state)["anchor_session"])

        # A late receipt from the dead attempt fences on the rotated identity.
        late = self.member_receipt("task-1", 1, state["claims"]["task-1"]["generation"])
        late["claim_token"] = dead_token
        fenced = self.batch_driver().record_worker_checkpoint(late)
        self.assertEqual(fenced["status"], "blocked")
        self.assertEqual(fenced["reason_code"], "owner-mismatch")

        # The recovered member completes and the group advances to member 2:
        # the standard fix path, not a wedged batch.
        fresh = self.batch_driver(adapter=RecordingAdapter())
        commit1 = self.commit_files("t1-1.txt")
        done = fresh.record_done(self.member_done("task-1", 1, commit1, generation=state["claims"]["task-1"]["generation"]))
        self.assertEqual(done["status"], "success", done)
        self.assertEqual(done["actions"][0]["type"], "resume_member")
        self.assertEqual(done["actions"][0]["task_id"], "task-2")

    def test_batch_member_session_fence_refuses_wrong_outer_session(self):
        # The anchor-session comparison in the member receipt fence
        # had zero coverage (deleting the comparison passed the whole suite).
        # Negative arm: a member receipt whose translated top-level
        # session_id (what the codex adapter copies from the worker
        # envelope) differs from the group's anchor session is a blocked
        # stale-claim with a byte-identical manifest; control arm: the
        # matching anchor session checkpoints through.
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]
        active = runtime.load_manifest(self.state_path)["claims"]["task-2"]
        before = self.state_path.read_bytes()
        wrong = self.member_receipt("task-2", 2, active["generation"], session_id="sess-rogue-9")
        # The same driver instance: a fresh construction persists its
        # updated_at backfill, which would swamp the byte-identical
        # fingerprint the refused receipt must leave.
        refused = driver.record_worker_checkpoint(wrong)
        self.assertEqual(refused["status"], "blocked")
        self.assertEqual(refused["reason_code"], "stale-claim")
        self.assertEqual(self.state_path.read_bytes(), before)
        match = self.member_receipt("task-2", 2, active["generation"], session_id=anchor_session)
        outcome = self.batch_driver().record_worker_checkpoint(match)
        self.assertEqual(outcome["status"], "success", outcome)

    def test_claim_blocked_while_batch_live(self):
        self.batch_manifest(self.disjoint_tasks(3))
        first = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(first["claimed"])
        # a second group claim retains today's blocked stale-claim outcome
        second = self.batch_driver(owner="other-owner").claim_next_task(batch=True)
        self.assertEqual(second["status"], "blocked")
        self.assertEqual(second["reason_code"], "stale-claim")
        self.assertFalse(second["claimed"])
        self.assertEqual(second["evidence"], ["another task is already claimed"])
        # the no-flag claim is blocked by the same single-claim invariant
        third = self.batch_driver().claim_next_task()
        self.assertEqual(third["status"], "blocked")
        self.assertEqual(third["reason_code"], "stale-claim")

    def test_cli_batch_opt_in_and_no_flag_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def create_cli(manifest_name):
                path = root / manifest_name
                command = [
                    sys.executable,
                    str(ROOT / "scripts/execute_plan_runtime.py"),
                    "--manifest", str(path),
                    "--repo-root", str(root),
                    "--owner", "cli-owner",
                    "--plan-slug", "cli-batch",
                    "--operation", "create",
                    "--input", json.dumps({"tasks": [
                        {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./b1.txt"]},
                        {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["b2.txt"]},
                        {"id": "task-3", "number": 3, "status": "pending", "allowed_paths": ["b3.txt"]},
                    ]}),
                ]
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(completed.stdout)["status"], "success")
                return path

            def claim_cli(manifest_path, *extra):
                command = [
                    sys.executable,
                    str(ROOT / "scripts/execute_plan_runtime.py"),
                    "--manifest", str(manifest_path),
                    "--repo-root", str(root),
                    "--owner", "cli-owner",
                    "--operation", "claim",
                    *extra,
                ]
                return json.loads(subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout)

            batch_manifest = create_cli("batch_state.json")
            result = claim_cli(batch_manifest, "--batch")
            self.assertTrue(result["claimed"])
            self.assertEqual(result["members"], ["task-1", "task-2", "task-3"])
            manifest = runtime.load_manifest(batch_manifest)
            self.assertEqual(len(manifest["claim_groups"]), 1)
            self.assertEqual(manifest["generation"], 1)
            group = next(iter(manifest["claim_groups"].values()))
            self.assertEqual(group["member_ordinals"], {"task-1": 1, "task-2": 2, "task-3": 3})
            self.assertEqual(manifest["tasks"]["task-1"]["allowed_paths"], ["b1.txt"])
            # the no-flag entrypoint persists one task only
            single_manifest = create_cli("single_state.json")
            result = claim_cli(single_manifest)
            self.assertTrue(result["claimed"])
            self.assertNotIn("group_id", result)
            manifest = runtime.load_manifest(single_manifest)
            self.assertEqual(manifest.get("claim_groups"), {})
            self.assertEqual(len(manifest["claims"]), 1)
            self.assertEqual(manifest["generation"], 1)

    def test_batch_wrapper_opt_in_and_no_flag_control(self):
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        # launch_next_task(batch=True) claims and launches the group
        result = self.batch_driver(adapter=adapter).launch_next_task(batch=True)
        self.assertEqual(result["status"], "success")
        manifest = runtime.load_manifest(self.state_path)
        group_id = self.live_group(manifest)["group_id"]
        commit1 = self.commit_files("t1-1.txt")
        done = self.batch_driver().record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["actions"][0]["type"], "resume_member")
        # continue_parent(batch=True) resumes the group's active member
        resumed = self.batch_driver(adapter=adapter).continue_parent(batch=True)
        self.assertEqual(resumed["status"], "success")
        self.assertEqual(adapter.resume_calls[0]["task_id"], "task-2")
        manifest = runtime.load_manifest(self.state_path)
        self.assertIn(group_id, manifest["claim_groups"])
        # both no-flag calls preserve today's single-task behavior
        self.batch_manifest(self.disjoint_tasks(2))
        single = RecordingAdapter()
        single_result = self.batch_driver(adapter=single).launch_next_task()
        self.assertEqual(single_result["status"], "success")
        self.assertNotIn("group_id", single_result)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(single.launch_calls[0]["task_id"], "task-1")
        continued = self.batch_driver(adapter=single).continue_parent()
        self.assertEqual(continued["status"], "blocked")
        self.assertEqual(continued["reason_code"], "done-pending")
        self.assertTrue(any("awaiting the done handoff" in item for item in continued["evidence"]))
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})

    def test_cli_continue_batch_opt_in_and_no_flag_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git("init", "-q", cwd=root)
            self._git("config", "user.email", "test@example.invalid", cwd=root)
            self._git("config", "user.name", "Runtime Test", cwd=root)
            (root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
            self._git("add", ".gitignore", cwd=root)
            self._git("commit", "-qm", "base", cwd=root)
            state = root / "runtime_state.json"
            runtime.create_manifest(state, "cli-batch", [
                {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["c1.txt"]},
                {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["c2.txt"]},
            ], repo_root=root)
            adapter = RecordingAdapter(session_id="sess-cli-anchor")
            driver = runtime.RuntimeDriver(state, plan_slug="cli-batch", owner="cli-owner", repo_root=root, commit_lookup=lambda _commit: True, adapter=adapter)
            driver.launch_next_task(batch=True)
            (root / "c1.txt").write_text("one\n", encoding="utf-8")
            commit1 = subprocess.run(["git", "add", "c1.txt"], cwd=root, env=self._git_env, check=True).returncode
            self.assertEqual(commit1, 0)
            subprocess.run(["git", "commit", "-qm", "member one"], cwd=root, env=self._git_env, check=True)
            commit1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True, env=self._git_env).stdout.strip()
            done = driver.record_done({
                "status": "success",
                "reason_code": "completed",
                "evidence": ["done-log:task-1"],
                "action_scope": "done-handoff",
                "checkpoint_identity": "task-1:done",
                "generation": 1,
                "task_id": "task-1",
                "claim_token": runtime.load_manifest(state)["claims"]["task-1"]["token"],
                "commit_identity": commit1,
                "checkbox": True,
                "clean_state": True,
                "log_evidence": ["task-1-implement.log.md"],
            })
            anchor_session = done["actions"][0]["session_id"]
            self.assertEqual(anchor_session, "sess-cli-anchor")

            def continue_cli(*extra):
                command = [
                    sys.executable,
                    str(ROOT / "scripts/execute_plan_runtime.py"),
                    "--manifest", str(state),
                    "--repo-root", str(root),
                    "--operation", "continue",
                    *extra,
                ]
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
                return json.loads(completed.stdout)

            # the real --batch entrypoint resolves the active member and the
            # anchor session; with no adapter configured it fails closed
            # naming both instead of relaunching
            result = continue_cli("--batch")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["active_member"], "task-2")
            self.assertEqual(result["anchor_session"], anchor_session)
            manifest = runtime.load_manifest(state)
            self.assertEqual(manifest["claims"]["task-2"]["state"], "claimed")
            self.assertEqual(manifest["claim_groups"][done["actions"][0]["group_id"]]["anchor_session"], anchor_session)
            # the no-flag entrypoint keeps the single-task continuation and
            # never names the anchor session
            control = continue_cli()
            self.assertEqual(control["status"], "blocked")
            self.assertNotIn("anchor_session", control)
            self.assertNotIn("active_member", control)
            self.assertTrue(any("resume" in item for item in control["evidence"]))
            manifest = runtime.load_manifest(state)
            self.assertEqual(manifest["claims"]["task-2"]["state"], "claimed")

    def test_reclaim_refuses_live_group_member_and_non_member_still_reclaims(self):
        # An expired claim on a member of a live batch group is
        # refused with the resumable stale-claim outcome naming the group,
        # whatever its lease state (a group parked at a budget pause is
        # EXPECTED to be lease-expired, so the refusal precedes lease
        # accounting); the manifest stays byte-identical because the group
        # protocol owns the member. The control arm proves reclaim still
        # works for a non-member expired claim, and the recovery arm proves
        # the group path the refusal points at actually advances the group.
        self.batch_manifest(self.disjoint_tasks(5))
        # The batch cap packs task-1..task-4 into the group; task-5 stays
        # pending with no claim.
        claim = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(claim["claimed"])
        group_id = claim["group_id"]
        expired = self.FIXED_NOW - runtime.CLAIM_LEASE_SECONDS - 10.0

        def expire_members(state):
            for member in claim["members"]:
                state["claims"][member]["timestamp"] = expired

        self.rewrite_manifest(expire_members)
        driver = self.batch_driver(clock=lambda: self.FIXED_NOW)
        before = self.state_path.read_bytes()
        refused = driver.reclaim("task-1")
        self.assertEqual(refused["status"], "blocked")
        self.assertEqual(refused["reason_code"], "stale-claim")
        self.assertTrue(any(group_id in item for item in refused["evidence"]), refused["evidence"])
        self.assertTrue(any("continue --batch" in item for item in refused["evidence"]))
        self.assertEqual(self.state_path.read_bytes(), before)
        # A fresh lease on the same member refuses through the same fence.
        self.rewrite_manifest(lambda state: state["claims"]["task-1"].update({"timestamp": self.FIXED_NOW}))
        fresh = self.batch_driver(clock=lambda: self.FIXED_NOW).reclaim("task-1")
        self.assertEqual(fresh["reason_code"], "stale-claim")
        self.assertTrue(any(group_id in item for item in fresh["evidence"]))
        # Control arm: an expired non-member claim reclaims normally.
        def seed_expired_non_member(state):
            state["claims"]["task-5"] = {
                "token": "seed-task-5",
                "generation": 0,
                "owner": "test-owner",
                "timestamp": expired,
                "state": "launched",
                "task_id": "task-5",
            }

        self.rewrite_manifest(seed_expired_non_member)
        released = self.batch_driver(clock=lambda: self.FIXED_NOW).reclaim("task-5")
        self.assertEqual(released["status"], "success")
        self.assertEqual(released["reason_code"], "reclaimed")
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"]["task-5"]["state"], "replaced")
        # Recovery arm: the group path the refusal names still advances the
        # group (the active member launches through the anchor protocol).
        adapter = RecordingAdapter()
        recovered = self.batch_driver(adapter=adapter).continue_parent(batch=True)
        self.assertEqual(recovered["status"], "success", recovered)
        self.assertEqual(adapter.launch_calls[0]["task_id"], "task-1")

    def test_batch_member_lease_refreshes_at_activation(self):
        # The member lease timestamp measures liveness from the
        # moment the member became active, not from the group claim: the
        # anchor launch refreshes it, and a later member's activation at
        # the done boundary refreshes it again, so a group parked past the
        # lease never carries claim-time-frozen leases that invite reclaim.
        now = {"value": self.FIXED_NOW}

        def clock():
            return now["value"]

        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(clock=clock, adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"]["task-1"]["timestamp"], now["value"])
        now["value"] += runtime.CLAIM_LEASE_SECONDS + 60
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success", done)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-2"]["timestamp"], now["value"])
        self.assertEqual(state["claims"]["task-1"]["timestamp"], self.FIXED_NOW)

    def test_continue_batch_refuses_non_resumable_blocked_member(self):
        # A blocked member whose receipt forbids continuation (a
        # foreign-path contract violation, resume_allowed=False) is refused
        # by BOTH group recovery entries exactly like resume() hard-filters
        # it; resuming it through the batch continuation would give the
        # caught scope violator a second turn that launders the violation
        # into an acceptance. The control arm proves resume_allowed=True
        # still resumes through the anchor session.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]

        def block_member2(resume_allowed):
            def mutate(state):
                state["claims"]["task-2"]["state"] = "blocked"
                state["tasks"]["task-2"]["status"] = "blocked"
                state["tasks"]["task-2"]["resume_allowed"] = resume_allowed
                state["tasks"]["task-2"]["session_id"] = anchor_session
            return mutate

        self.rewrite_manifest(block_member2(False))
        blocked_driver = self.batch_driver(adapter=RecordingAdapter())
        refused = blocked_driver.continue_parent(batch=True)
        self.assertEqual(refused["status"], "blocked")
        self.assertEqual(refused["reason_code"], "stale-claim")
        self.assertTrue(any("not resumable" in item for item in refused["evidence"]), refused["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertFalse(state["tasks"]["task-2"]["resume_allowed"])
        self.assertEqual(state["claims"]["task-2"]["state"], "blocked")
        # resume() refuses the same member (the entry points agree).
        resume_refused = self.batch_driver(adapter=RecordingAdapter()).resume()
        self.assertEqual(resume_refused["status"], "blocked")
        self.assertEqual(resume_refused["reason_code"], "stale-claim")
        self.assertTrue(any("no resumable blocked task" in item for item in resume_refused["evidence"]))
        # Control arm: resume_allowed=True resumes through the anchor.
        self.rewrite_manifest(block_member2(True))
        control_adapter = RecordingAdapter()
        resumed = self.batch_driver(adapter=control_adapter).continue_parent(batch=True)
        self.assertEqual(resumed["status"], "success", resumed)
        self.assertEqual(control_adapter.resume_calls[0]["task_id"], "task-2")
        self.assertEqual(control_adapter.resume_calls[0]["session_id"], anchor_session)

    def test_batch_member_retryable_error_lands_through_anchor_resume(self):
        # Blocking arm: a batch member's retryable error receipt never
        # takes the plain driver relaunch - that launch bypasses the group
        # fences and its fresh session then always fails the member receipt
        # fence's session pin (the group anchor is already captured), so the
        # group livelocks on contradictory durable state. The member retry
        # is the group's own continuation primitive instead: an
        # anchor-session resume whose receipt re-enters every member fence
        # and lands. tasks[].status never disagrees with claims[].state
        # across the retry window, the anchor identity never changes, and
        # the driver-owned retry budget decrements exactly once.
        self.batch_manifest(self.disjoint_tasks(2))

        class ScriptedAdapter:
            """Two-call resume script: first receipt errors, retry lands."""

            def __init__(self):
                self.launch_calls = []
                self.resume_calls = []

            @staticmethod
            def _receipt(task_id, generation, session_id, status, remaining=None):
                result = {
                    "status": status,
                    "reason_code": "completed" if status == "success" else "runtime-error",
                    "evidence": ["batch-worker-log"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": f"{task_id}:worker",
                    "generation": generation,
                    "session_id": session_id,
                }
                if remaining is not None:
                    result["retry_policy"] = {"mode": "bounded", "max_attempts": 1, "attempts_remaining": remaining}
                return result

            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                self.launch_calls.append(task["id"])
                return self._receipt(task["id"], generation, "sess-anchor-1", "success")

            def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
                self.resume_calls.append({"session_id": session_id, "task_id": task_id})
                if len(self.resume_calls) == 1:
                    return self._receipt(task_id, generation, session_id, "error", remaining=1)
                return self._receipt(task_id, generation, session_id, "success")

        adapter = ScriptedAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]

        advanced = driver.continue_parent(batch=True)
        self.assertEqual(advanced["status"], "success", advanced)
        self.assertEqual(advanced["state"], "done-pending")
        # No driver relaunch: the anchor's launch stays the only one, and
        # both member resumes carried the anchor session (the retry
        # re-entered the member fences instead of fencing forever).
        self.assertEqual(adapter.launch_calls, ["task-1"])
        self.assertEqual([call["session_id"] for call in adapter.resume_calls], [anchor_session, anchor_session])
        self.assertEqual([call["task_id"] for call in adapter.resume_calls], ["task-2", "task-2"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-2"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-2"]["state"], "launched")
        self.assertEqual(state["claim_groups"][group_id]["anchor_session"], anchor_session)
        self.assertIn("task-2:worker#attempt-1", state["checkpoints"])
        self.assertTrue(any(
            entry.get("event") == "worker-retry" and entry.get("task_id") == "task-2"
            for entry in state["history"]
        ))

    def test_batch_member_retry_budget_exhaustion_blocks_consistently(self):
        # Recovery arm: with the retry budget spent the member
        # converges to a consistent blocked state through the same
        # anchor-session resume - exactly two resumes (the window and the
        # one budgeted retry), no livelock, no driver relaunch, and
        # tasks[].status agrees with claims[].state for every task.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter(
            resume_result={
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["persistent worker error"],
                "action_scope": "repository-task",
                "retry_policy": {"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1},
            }
        )
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]

        advanced = driver.continue_parent(batch=True)
        self.assertEqual(advanced["status"], "error", advanced)
        self.assertEqual(len(adapter.resume_calls), 2)
        self.assertEqual([call["session_id"] for call in adapter.resume_calls], [anchor_session, anchor_session])
        self.assertEqual(len(adapter.launch_calls), 1)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-2"]["state"], "blocked")
        self.assertTrue(state["tasks"]["task-2"]["resume_allowed"])
        self.assertEqual(state["tasks"]["task-2"]["session_id"], anchor_session)
        self.assertEqual(state["claim_groups"][group_id]["state"], "active")
        self.assertEqual(state["tasks"]["task-1"]["status"], "checkpointed")
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")

    def test_batch_member_retry_without_session_persists_blocked(self):
        # The no-session arm of the member-retry primitive. A
        # retryable member receipt with NO session anywhere (the member's own
        # task record and the group anchor both carry none) has nothing to
        # resume and no legal member launch, so the receipt persists as the
        # member's blocked state: no retry window, no budget spend, no
        # relaunch, and the operator recovers through the group path.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        group_id = done["actions"][0]["group_id"]

        def strip_sessions(state):
            # Drift shape: a manifest written before the session contract
            # carries no anchor session and no member task session.
            state["claim_groups"][group_id]["anchor_session"] = None
            state["tasks"]["task-2"].pop("session_id", None)

        self.rewrite_manifest(strip_sessions)
        state = runtime.load_manifest(self.state_path)
        claim2 = state["claims"]["task-2"]
        error_receipt = {
            "status": "error",
            "reason_code": "runtime-error",
            "evidence": ["persistent member error"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-2:worker",
            "generation": claim2["generation"],
            "claim_token": claim2["token"],
            "retry_policy": {"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1},
        }
        result = driver.record_worker_checkpoint(error_receipt)
        self.assertEqual(result["status"], "error", result)
        # Persisted, not retried: no adapter window opened and the retry
        # budget was not spent.
        self.assertEqual(adapter.resume_calls, [])
        self.assertEqual([call["task_id"] for call in adapter.launch_calls], ["task-1"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-2"]["state"], "blocked")
        self.assertTrue(state["tasks"]["task-2"]["resume_allowed"])
        self.assertFalse(any(key.startswith("task-2:worker#attempt-") for key in state["checkpoints"]))
        self.assertFalse(any(
            entry.get("event") == "worker-retry" and entry.get("task_id") == "task-2"
            for entry in state["history"]
        ))

    def test_batch_claim_refuses_unauthorizable_members_up_front(self):
        # A member whose envelope can never be authorized (a network
        # flag, or zero scope) is excluded from the batch prefix, so the
        # batch claim refuses up front - the reproduced two-member
        # network:true scenario ends in a single-task fallback instead of a
        # group wedged at its advance.
        tasks = self.disjoint_tasks(2)
        tasks[1]["network"] = True
        self.batch_manifest(tasks)
        adapter = RecordingAdapter()
        launched = self.batch_driver(adapter=adapter).launch_next_task(batch=True)
        # The prefix ends at the network-flagged member: no group exists,
        # and the claim fell back to the single-task path, which launched
        # the authorizable anchor task.
        manifest = runtime.load_manifest(self.state_path)
        self.assertFalse(manifest.get("claim_groups"), manifest.get("claim_groups"))
        self.assertNotIn("batch", launched)
        self.assertEqual(launched["status"], "success", launched)
        self.assertEqual([call["task_id"] for call in adapter.launch_calls], ["task-1"])
        self.assertEqual(manifest["tasks"]["task-2"]["status"], "pending")

        # A network-flagged FIRST member empties the prefix entirely: the
        # single-task claim takes it and its launch path owns the refusal.
        tasks = self.disjoint_tasks(2)
        tasks[0]["network"] = True
        self.batch_manifest(tasks)
        blocked = self.batch_driver(adapter=RecordingAdapter()).launch_next_task(batch=True)
        self.assertEqual(blocked["status"], "blocked", blocked)
        self.assertEqual(blocked["reason_code"], "approval-required")
        self.assertFalse(runtime.load_manifest(self.state_path).get("claim_groups"))

        # A zero-scope member is excluded the same way.
        tasks = self.disjoint_tasks(2)
        tasks[1]["allowed_paths"] = []
        self.batch_manifest(tasks)
        launched = self.batch_driver(adapter=RecordingAdapter()).launch_next_task(batch=True)
        self.assertFalse(runtime.load_manifest(self.state_path).get("claim_groups"))
        self.assertEqual(launched["status"], "success", launched)

    def test_batch_advance_authorization_failure_fails_group_and_completes_done(self):
        # Authorization belt: when the NEXT member's envelope cannot be authorized
        # at the advance (here the task is drifted to network:true after the
        # claim-time authorization passed), the group fails atomically in
        # the done handoff's locked save and the completed member's done
        # lands. The pre-fix behavior returned the authorization outcome as
        # the done's blocked result, so the done was refused forever - every
        # retry re-failed the same authorization - and the group wedged
        # with no exit.
        self.batch_manifest(self.disjoint_tasks(2))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")

        def drift_network(state):
            state["tasks"]["task-2"]["network"] = True

        self.rewrite_manifest(drift_network)
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success", done)
        state = runtime.load_manifest(self.state_path)
        group = self.live_group(state)
        self.assertEqual(group["state"], "failed")
        self.assertIsNone(group["active_member"])
        self.assertEqual(state["tasks"]["task-1"]["status"], "checkpointed")
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")
        # The staged member's claim was released (the history event names
        # it) and its task re-entered the individual queue: the done's
        # attached generic next-claim already took it as a fresh individual
        # claim with no group reference.
        self.assertTrue(any(
            entry.get("event") == "batch-group-failed" and entry.get("member") == "task-2"
            and "task-2" in (entry.get("released_members") or [])
            for entry in state["history"]
        ))
        self.assertEqual(state["tasks"]["task-2"]["status"], "claimed")
        self.assertTrue(any(
            action.get("type") == "launch-task" and action.get("task_id") == "task-2"
            for action in done.get("actions", [])
        ), done.get("actions"))
        # The released member's fresh individual claim has no group
        # reference, and its single-task launch path owns the authorization
        # refusal (blocked, persisted) instead of any group wedge.
        fresh_claim = runtime.load_manifest(self.state_path)["claims"]["task-2"]
        self.assertNotIn("group_id", fresh_claim)
        refused = driver._launch_claimed_task(fresh_claim, "continue execute-plan", None)
        self.assertEqual(refused["status"], "blocked", refused)
        self.assertEqual(refused["reason_code"], "approval-required")
        self.assertEqual(runtime.load_manifest(self.state_path)["tasks"]["task-2"]["status"], "blocked")

    def test_reclaim_non_resumable_member_fails_group_and_releases_staged(self):
        # Wedge + exit: a blocked member whose receipt forbids
        # continuation has no group path left (continue --batch and resume
        # both refuse it and nothing else closes a group), and before the
        # exit its reclaim was refused too, so only a hand edit could
        # recover the run. The exit: reclaiming that member is allowed
        # through (no lease wait: the durable non-resumable receipt is
        # terminal) and atomically fails the group in the same locked CAS -
        # the member rotates back to pending, the staged members close back
        # onto the pending queue, and a fresh individual claim proceeds.
        self.batch_manifest(self.disjoint_tasks(3))
        driver = self.batch_driver(adapter=RecordingAdapter())
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done["status"], "success")
        group_id = done["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]

        def wedge_member2(state):
            state["claims"]["task-2"]["state"] = "blocked"
            state["tasks"]["task-2"]["status"] = "blocked"
            state["tasks"]["task-2"]["resume_allowed"] = False
            state["tasks"]["task-2"]["session_id"] = anchor_session

        self.rewrite_manifest(wedge_member2)
        # The wedge: both group recovery entries refuse the member forever.
        refused_continue = self.batch_driver(adapter=RecordingAdapter()).continue_parent(batch=True)
        self.assertEqual(refused_continue["status"], "blocked")
        self.assertTrue(any("not resumable" in item for item in refused_continue["evidence"]), refused_continue["evidence"])
        refused_resume = self.batch_driver(adapter=RecordingAdapter()).resume()
        self.assertEqual(refused_resume["status"], "blocked")
        # The exit: reclaiming the wedged member succeeds and fails the
        # group in the same CAS.
        released = self.batch_driver(adapter=RecordingAdapter()).reclaim("task-2")
        self.assertEqual(released["status"], "success", released)
        self.assertEqual(released["reason_code"], "reclaimed")
        self.assertTrue(any(f"group_failed={group_id}" in item for item in released["evidence"]), released["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claim_groups"][group_id]["state"], "failed")
        self.assertIsNone(state["claim_groups"][group_id]["active_member"])
        self.assertEqual(state["claims"]["task-2"]["state"], "replaced")
        self.assertEqual(state["tasks"]["task-2"]["status"], "pending")
        self.assertNotIn("resume_allowed", state["tasks"]["task-2"])
        self.assertNotIn("session_id", state["tasks"]["task-2"])
        self.assertEqual(state["claims"]["task-3"]["state"], "closed")
        self.assertEqual(state["tasks"]["task-3"]["status"], "pending")
        self.assertTrue(any(entry.get("event") == "batch-group-failed" for entry in state["history"]))
        # Round-trip: the failed group state must survive the
        # authoritative validator and a full validating continuation. The
        # original witness read the state with a bare load_manifest, which
        # masked the defect where validate_manifest (active/closed only)
        # raised ValueError on every validating entrypoint after the exit.
        reread = self.batch_driver(adapter=RecordingAdapter()).refresh_manifest()
        self.assertEqual(reread["claim_groups"][group_id]["state"], "failed")
        # The continuation claims and launches the released member itself,
        # so the post-exit snapshot is restored afterwards and the next
        # witness re-runs on the same durable state.
        post_exit = runtime.load_manifest(self.state_path)
        continued = self.batch_driver(adapter=RecordingAdapter()).continue_parent()
        self.assertEqual(continued["status"], "success", continued)
        self.rewrite_manifest(lambda state: state.update(post_exit))
        # The queue moved on: a fresh individual claim proceeds past the
        # failed group.
        next_claim = self.batch_driver(adapter=RecordingAdapter()).claim_next_task()
        self.assertTrue(next_claim["claimed"], next_claim)

    # ------------------------------------------------------------------
    # Parallel implement groups (Step 1.2 parallel-group contract)
    # ------------------------------------------------------------------

    def test_parallel_group_claim_refuses_overlap(self):
        # given: a parallel-group claim whose members share a canonical file
        # (the lexical alias ./t1.txt and t1.txt canonicalizes to one path).
        self.batch_manifest([
            {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["./t1.txt"]},
            {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["t1.txt"]},
        ])
        driver = self.batch_driver()
        before = self.state_path.read_bytes()
        result = driver.claim_parallel_group(["task-1", "task-2"])
        # expects: refusal with stale-claim evidence naming the shared path
        # and both members.
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        self.assertTrue(any("t1.txt" in item for item in result["evidence"]), result["evidence"])
        self.assertTrue(any("task-1" in item and "task-2" in item for item in result["evidence"]), result["evidence"])
        # no mutation: no claims, no group record, no generation bump.
        self.assertEqual(self.state_path.read_bytes(), before)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(manifest["claims"], {})

    def test_parallel_group_claim_accepts_disjoint(self):
        # boundary arm: a one-member request is refused; a parallel group
        # needs at least two members.
        self.batch_manifest(self.disjoint_tasks(1))
        driver = self.batch_driver()
        solo = driver.claim_parallel_group(["task-1"])
        self.assertEqual(solo["status"], "blocked")
        self.assertEqual(solo["reason_code"], "stale-claim")
        self.assertTrue(any("at least two" in item for item in solo["evidence"]), solo["evidence"])
        self.assertEqual(runtime.load_manifest(self.state_path)["claims"], {})
        # given: K pairwise-disjoint member tasks in canonical document order
        # (the request order is scrambled; membership lands canonical).
        self.batch_manifest(self.disjoint_tasks(3))
        driver = self.batch_driver()
        result = driver.claim_parallel_group(["task-3", "task-1", "task-2"])
        # expects: the claim accepted...
        self.assertTrue(result["claimed"], result)
        self.assertTrue(result["parallel"])
        self.assertEqual(result["members"], ["task-1", "task-2", "task-3"])
        self.assertEqual(result["member_ordinals"], {"task-1": 1, "task-2": 2, "task-3": 3})
        # ...the group recorded in the machine manifest with members and
        # state active, no anchor identity and no active-member ordinal gate...
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest["generation"], 1)
        group = self.live_group(manifest)
        self.assertEqual(group["group_id"], result["group_id"])
        self.assertEqual(group["kind"], "parallel")
        self.assertEqual(group["state"], "active")
        self.assertIsNone(group["active_member"])
        self.assertEqual(group["members"], ["task-1", "task-2", "task-3"])
        self.assertNotIn("anchor", group)
        self.assertNotIn("launch_record", group)
        self.assertNotIn("anchor_session", group)
        # ...and each member holding an ordinary live claim bound to the
        # group id (no staged members: all members are concurrent).
        for member, ordinal in result["member_ordinals"].items():
            claim = manifest["claims"][member]
            self.assertEqual(claim["state"], "claimed")
            self.assertEqual(claim["group_id"], result["group_id"])
            self.assertEqual(claim["member_ordinal"], ordinal)
            self.assertEqual(claim["allowed_paths"], [f"t{ordinal}-1.txt"])
            self.assertEqual(manifest["tasks"][member]["status"], "claimed")

    def test_parallel_group_closes_on_last_member_commit(self):
        # given: a claimed and launched parallel group whose three members
        # all landed (their changes sit uncommitted in the shared worktree),
        # then per-member done in document order.
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        claimed = driver.claim_parallel_group(["task-1", "task-2", "task-3"])
        self.assertTrue(claimed["claimed"], claimed)
        group_id = claimed["group_id"]
        for n in (1, 2, 3):
            (self.root / f"t{n}-1.txt").write_text(f"member {n} change\n", encoding="utf-8")
        for member in claimed["members"]:
            launched = driver.launch_member_task(member)
            self.assertEqual(launched["status"], "success", launched)
        state = runtime.load_manifest(self.state_path)
        for member in claimed["members"]:
            self.assertEqual(state["tasks"][member]["status"], "done-pending")
        group = state["claim_groups"][group_id]
        # concurrent members keep their own launch records and sessions; the
        # group carries no shared anchor identity.
        self.assertNotIn("launch_record", group)
        self.assertNotIn("anchor_session", group)
        for member in claimed["members"]:
            self.assertIsInstance(state["claims"][member].get("launch_record"), dict)
        # expects: the last member commit closes the group and leaves no
        # lingering claim; sibling members' uncommitted files never block a
        # member's receipt witnesses.
        for ordinal, task in enumerate(("task-1", "task-2", "task-3"), start=1):
            commit = self.commit_files(f"t{ordinal}-1.txt")
            done = driver.record_done(self.member_done(task, ordinal, commit))
            self.assertEqual(done["status"], "success", done)
            state = runtime.load_manifest(self.state_path)
            self.assertEqual(state["claims"][task]["state"], "closed")
            group = state["claim_groups"][group_id]
            if ordinal < 3:
                self.assertEqual(group["state"], "active")
            else:
                self.assertEqual(group["state"], "closed")
                self.assertIsNone(group["active_member"])
        live = [
            task_id
            for task_id, claim in state["claims"].items()
            if claim.get("state") in {"claimed", "launched", "blocked", "waiting-capacity", "staged"}
        ]
        self.assertEqual(live, [])
        self.assertTrue(any(entry.get("event") == "parallel-group-closed" for entry in state["history"]))
        # the closed group releases the generic next-claim.
        next_claim = self.batch_driver(adapter=RecordingAdapter()).claim_next_task()
        self.assertEqual(next_claim["status"], "success")
        self.assertFalse(next_claim["claimed"])

    def test_parallel_group_failed_member_isolation(self):
        # given: one member of an active parallel group holds a terminal
        # blocked receipt (a non-resumable contract violation) while its
        # sibling lands normally.
        self.batch_manifest(self.disjoint_tasks(2))

        class TerminalMemberAdapter:
            def __init__(self):
                self.launch_calls = []

            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                self.launch_calls.append(task["id"])
                if task["id"] == "task-2":
                    return {
                        "status": "blocked",
                        "reason_code": "contract-violation",
                        "evidence": ["out-of-scope change: foreign.txt"],
                        "action_scope": "repository-task",
                        "checkpoint_identity": "task-2:worker",
                        "generation": generation,
                        "session_id": "sess-task-2",
                    }
                return {
                    "status": "success",
                    "reason_code": "completed",
                    "evidence": [f"worker-log:{task['id']}"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": f"{task['id']}:worker",
                    "generation": generation,
                    "session_id": f"sess-{task['id']}",
                }

        adapter = TerminalMemberAdapter()
        driver = self.batch_driver(adapter=adapter)
        claimed = driver.claim_parallel_group(["task-1", "task-2"])
        self.assertTrue(claimed["claimed"], claimed)
        group_id = claimed["group_id"]
        self.assertEqual(driver.launch_member_task("task-1")["status"], "success")
        blocked_launch = driver.launch_member_task("task-2")
        self.assertEqual(blocked_launch["status"], "blocked")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-1"]["status"], "done-pending")
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertIs(state["tasks"]["task-2"]["resume_allowed"], False)
        # the terminal-receipt executable exit: reclaim releases ONLY that
        # member; the group stays active and the sibling is untouched.
        released = self.batch_driver().reclaim("task-2")
        self.assertEqual(released["status"], "success", released)
        self.assertEqual(released["reason_code"], "reclaimed")
        self.assertTrue(any("task-2" in item for item in released["evidence"]), released["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-2"]["state"], "replaced")
        self.assertEqual(state["tasks"]["task-2"]["status"], "pending")
        self.assertNotIn("resume_allowed", state["tasks"]["task-2"])
        self.assertEqual(state["claims"]["task-1"]["state"], "launched")
        self.assertEqual(state["tasks"]["task-1"]["status"], "done-pending")
        self.assertEqual(state["claim_groups"][group_id]["state"], "active")
        self.assertTrue(any(entry.get("event") == "parallel-member-reclaimed" for entry in state["history"]))
        self.assertFalse(any(entry.get("event") == "batch-group-failed" for entry in state["history"]))
        # control arm: a member whose receipt still permits continuation has
        # a recovery path left, so its reclaim is refused naming the group;
        # the manifest stays byte-identical.
        def resumable_member1(state):
            state["claims"]["task-1"]["state"] = "blocked"
            state["tasks"]["task-1"]["status"] = "blocked"
            state["tasks"]["task-1"]["resume_allowed"] = True

        self.rewrite_manifest(resumable_member1)
        refused_driver = self.batch_driver()
        before = self.state_path.read_bytes()
        refused = refused_driver.reclaim("task-1")
        self.assertEqual(refused["status"], "blocked")
        self.assertEqual(refused["reason_code"], "stale-claim")
        self.assertTrue(any(group_id in item for item in refused["evidence"]), refused["evidence"])
        self.assertEqual(self.state_path.read_bytes(), before)
        # the released member never wedges the group: once the sibling's
        # done lands, the group closes with the released member replaced.
        self.rewrite_manifest(lambda state: state["claims"]["task-1"].update({"state": "launched"}))
        self.rewrite_manifest(lambda state: state["tasks"]["task-1"].update({"status": "done-pending"}))
        commit = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit))
        self.assertEqual(done["status"], "success", done)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claim_groups"][group_id]["state"], "closed")
        self.assertIsNone(state["claim_groups"][group_id]["active_member"])
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")

    def test_parallel_group_sessionless_resume_release_closes_group(self):
        # Regression (panel phase 3, blocking wedge): a 2-member parallel
        # group whose member A is done and whose member B is blocked with no
        # session anywhere takes the session-less resume release, which
        # replaces B's claim. The release is a terminal member transition,
        # so the group must close with it. Before the fix the release ran no
        # group-close check: the group stayed active with zero live members,
        # every future claim was refused forever ("another task is already
        # claimed"), and reclaim cannot touch a replaced claim - a wedge no
        # entrypoint could leave.
        self.batch_manifest(self.disjoint_tasks(2))

        class ResumableSessionlessBlockAdapter:
            # Member A launches clean; member B's launch blocks with a
            # resumable receipt that carries no session id at all (the
            # dead-session shape the session-less release exists for).
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                if task["id"] == "task-2":
                    return {
                        "status": "blocked",
                        "reason_code": "timeout",
                        "evidence": ["launch deadline exceeded"],
                        "action_scope": "repository-task",
                        "checkpoint_identity": "task-2:worker",
                        "generation": generation,
                        "resume_allowed": True,
                    }
                return {
                    "status": "success",
                    "reason_code": "completed",
                    "evidence": [f"worker-log:{task['id']}"],
                    "action_scope": "repository-task",
                    "checkpoint_identity": f"{task['id']}:worker",
                    "generation": generation,
                    "session_id": f"sess-{task['id']}",
                }

        driver = self.batch_driver(adapter=ResumableSessionlessBlockAdapter())
        claimed = driver.claim_parallel_group(["task-1", "task-2"])
        self.assertTrue(claimed["claimed"], claimed)
        group_id = claimed["group_id"]
        self.assertEqual(driver.launch_member_task("task-1")["status"], "success")
        blocked_launch = driver.launch_member_task("task-2")
        self.assertEqual(blocked_launch["status"], "blocked")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-1"]["status"], "done-pending")
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertIs(state["tasks"]["task-2"]["resume_allowed"], True)
        self.assertNotIn("session_id", state["tasks"]["task-2"])
        # Member A's done lands; the group stays active pending B.
        commit = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit))
        self.assertEqual(done["status"], "success", done)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")
        self.assertEqual(state["claim_groups"][group_id]["state"], "active")
        # The session-less resume release: B resumes on its own session, has
        # none anywhere, and takes the release arm (the noop continuation
        # freezes the manifest at the exact post-release state).
        release_driver = self.batch_driver()
        release_driver.continue_parent = lambda *args, **kwargs: {"status": "blocked", "reason_code": "test-noop"}
        resumed = release_driver.resume()
        self.assertEqual(resumed["reason_code"], "test-noop", resumed)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-2"]["state"], "replaced")
        self.assertEqual(state["tasks"]["task-2"]["status"], "pending")
        self.assertTrue(any(
            entry.get("event") == "parallel-member-released" and entry.get("member") == "task-2"
            for entry in state["history"]
        ), state["history"])
        # The fix: the release itself closes the group - zero live members
        # left, so the live group can never wedge on a terminal membership.
        self.assertEqual(state["claim_groups"][group_id]["state"], "closed")
        self.assertIsNone(state["claim_groups"][group_id]["active_member"])
        self.assertTrue(any(
            entry.get("event") == "parallel-group-closed" and entry.get("last_member") == "task-2"
            for entry in state["history"]
        ), state["history"])
        # The replaced claim is outside the reclaimable set (the release is
        # the only recovery), so reclaim stays refused after the fix too.
        refused_reclaim = self.batch_driver().reclaim("task-2")
        self.assertEqual(refused_reclaim["status"], "blocked", refused_reclaim)
        self.assertEqual(refused_reclaim["reason_code"], "stale-claim")
        # And the queue is live again: the released task is claimable.
        next_claim = self.batch_driver().claim_next_task()
        self.assertEqual(next_claim["status"], "success", next_claim)
        self.assertTrue(next_claim["claimed"], next_claim)
        self.assertEqual(next_claim["task_id"], "task-2")

    def test_parallel_group_claim_refuses_combined_file_cap(self):
        # given: 3 pairwise-disjoint eligible members (at or under the member
        # cap) whose combined canonical file count crosses the file cap on
        # the third member: 4 + 4 + 4 = 12 > 8.
        self.batch_manifest(self.disjoint_tasks(3, files_per_task=4))
        driver = self.batch_driver()
        before = self.state_path.read_bytes()
        result = driver.claim_parallel_group(["task-1", "task-2", "task-3"])
        # expects: refusal citing the combined member file cap with the batch
        # numeric caps carried verbatim (4 members, 8 combined member files).
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        self.assertTrue(any("combined member file cap" in item for item in result["evidence"]), result["evidence"])
        evidence = " ".join(result["evidence"])
        self.assertIn("12", evidence)
        self.assertIn("8", evidence)
        self.assertIn("4", evidence)
        # no mutation.
        self.assertEqual(self.state_path.read_bytes(), before)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(manifest["claims"], {})
        # the shared cap is the batch prefix's too (one source of truth):
        # 4 + 4 members fit exactly at the cap, the third 4-file member ends
        # the prefix, and the surviving pair claims as one batch group.
        self.batch_manifest(self.disjoint_tasks(3, files_per_task=4))
        batched = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(batched["claimed"], batched)
        self.assertEqual(batched["members"], ["task-1", "task-2"])
        manifest = runtime.load_manifest(self.state_path)
        group = self.live_group(manifest)
        self.assertEqual(sum(len(paths) for paths in group["member_paths"].values()), 8)
        self.assertEqual(manifest["tasks"]["task-3"]["status"], "pending")

    def test_parallel_group_claim_refuses_over_cap(self):
        # given: 5 pairwise-disjoint eligible tasks requested as one
        # parallel group.
        self.batch_manifest(self.disjoint_tasks(5))
        driver = self.batch_driver()
        before = self.state_path.read_bytes()
        result = driver.claim_parallel_group([f"task-{n}" for n in range(1, 6)])
        # expects: refusal citing the member cap, the batch numeric caps
        # carried verbatim (4 members, 8 combined member files).
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "stale-claim")
        self.assertTrue(any("member cap" in item for item in result["evidence"]), result["evidence"])
        evidence = " ".join(result["evidence"])
        self.assertIn("4", evidence)
        self.assertIn("8", evidence)
        # no mutation.
        self.assertEqual(self.state_path.read_bytes(), before)
        manifest = runtime.load_manifest(self.state_path)
        self.assertEqual(manifest.get("claim_groups"), {})
        self.assertEqual(manifest["claims"], {})

    def test_batch_group_lifecycle_transition_table_is_exhaustive(self):
        # G1 reconciliation: the group state x operation table is normative in
        # the runtime contract's batch claim groups section, and this test
        # drives it cell by cell. Every operation runs from every group state
        # ({active, closed, failed}); every cell has a defined outcome (no
        # state is wedged: active always keeps an executable group action or
        # the reclaim exit, closed and failed are documented terminals whose
        # only forward motion is the individual queue), and after every
        # operation every task status agrees with its claim state.
        AGREEMENT = {
            # task status -> claim states that agree with it. `pending`
            # admits the staged member shape plus the documented release
            # shapes (closed staged claims and the replaced claim of a
            # reclaimed member) whose tasks re-enter the individual queue.
            "pending": {"staged", "closed", "replaced"},
            "claimed": {"claimed"},
            "launched": {"launched"},
            "blocked": {"blocked"},
            "done-pending": {"launched"},
            "commit-pending": {"launched"},
            "checkpointed": {"closed"},
            "complete": {"closed"},
            "aborted": {"aborted"},
        }

        def assert_agreement():
            state = runtime.load_manifest(self.state_path)
            for task_id, task in state["tasks"].items():
                claim = state["claims"].get(task_id)
                if claim is None:
                    self.assertEqual(task["status"], "pending", task_id)
                    continue
                self.assertIn(
                    claim["state"],
                    AGREEMENT.get(task["status"], set()),
                    (task_id, task["status"], claim["state"]),
                )

        def group_record():
            state = runtime.load_manifest(self.state_path)
            groups = [g for g in state.get("claim_groups", {}).values() if isinstance(g, dict)]
            if not groups:
                return None
            self.assertEqual(len(groups), 1)
            return groups[0]

        def assert_group_state(expected_state):
            group = group_record()
            self.assertIsNotNone(group)
            self.assertEqual(group["state"], expected_state)
            self.assertIn(group["state"], runtime.BATCH_GROUP_STATES)

        def block_member(member, anchor_session, resume_allowed, expired=False):
            def mutate(state):
                state["claims"][member]["state"] = "blocked"
                if expired:
                    state["claims"][member]["timestamp"] = self.FIXED_NOW - runtime.CLAIM_LEASE_SECONDS - 10.0
                state["tasks"][member]["status"] = "blocked"
                state["tasks"][member]["resume_allowed"] = resume_allowed
                state["tasks"][member]["session_id"] = anchor_session
            return mutate

        def reactivate_member(member):
            # Rewind a member the previous arm parked at done-pending or
            # blocked back to the live claimed seat, so the next arm drives
            # the same active state from a fresh start.
            def mutate(state):
                state["claims"][member]["state"] = "claimed"
                state["tasks"][member]["status"] = "claimed"
                state["tasks"][member]["resume_allowed"] = True
            return mutate

        def late_member_receipt(member, **overrides):
            # A late receipt carries the closed member's own (stale) token.
            receipt = self.member_receipt(member, 1, 1)
            receipt.update(overrides)
            return receipt

        LATE_RECEIPT_ARMS = (
            {},
            {"status": "blocked", "reason_code": "approval-required"},
            {"status": "error", "reason_code": "runtime-error", "retry_policy": {"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1}},
        )

        # ------------------------------------------------------------------
        # active: every operation has a defined, executable outcome.
        # ------------------------------------------------------------------

        # claim from active: blocked stale-claim, the group holds the launch.
        self.batch_manifest(self.disjoint_tasks(3))
        self.batch_driver().claim_next_task(batch=True)
        refused_claim = self.batch_driver().claim_next_task()
        self.assertEqual(refused_claim["status"], "blocked")
        self.assertEqual(refused_claim["reason_code"], "stale-claim")
        self.assertFalse(refused_claim["claimed"])

        # launch from active (unlaunched): the anchor's first launch through
        # the group path arms the ONE group launch record; with the anchor
        # already at its done boundary the same call routes to the member
        # continuation instead of a second launch.
        self.batch_manifest(self.disjoint_tasks(3))
        launch_adapter = RecordingAdapter()
        launch_driver = self.batch_driver(adapter=launch_adapter)
        launch_driver.claim_next_task(batch=True)
        launched = launch_driver.launch_next_task(batch=True)
        self.assertEqual(launched["status"], "success", launched)
        self.assertEqual(launch_adapter.launch_calls[0]["task_id"], "task-1")
        self.assertIsInstance(group_record()["launch_record"], dict)
        launch_commit1 = self.commit_files("t1-1.txt")
        self.assertEqual(launch_driver.record_done(self.member_done("task-1", 1, launch_commit1))["status"], "success")
        relaunch_adapter = RecordingAdapter()
        relaunched = self.batch_driver(adapter=relaunch_adapter).launch_next_task(batch=True)
        self.assertEqual(relaunched["status"], "success", relaunched)
        self.assertEqual(relaunch_adapter.resume_calls[0]["task_id"], "task-2")
        assert_group_state("active")
        assert_agreement()

        # Main fixture: the anchor landed (auto-checkpoint at launch), its
        # done advanced the group, and member-2 is the active seat (claimed).
        self.batch_manifest(self.disjoint_tasks(3))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done1 = driver.record_done(self.member_done("task-1", 1, commit1))
        self.assertEqual(done1["actions"][0]["type"], "resume_member")
        group_id = done1["actions"][0]["group_id"]
        anchor_session = runtime.load_manifest(self.state_path)["claim_groups"][group_id]["anchor_session"]
        assert_group_state("active")
        self.assertEqual(group_record()["active_member"], "task-2")
        assert_agreement()

        # checkpoint success from active: the named active member lands
        # done-pending; the group is unchanged.
        receipt = self.member_receipt("task-2", 2, 1, session_id=anchor_session)
        landed = driver.record_worker_checkpoint(receipt)
        self.assertEqual(landed["status"], "success", landed)
        self.assertEqual(landed["state"], "done-pending")
        assert_group_state("active")
        self.assertEqual(group_record()["active_member"], "task-2")
        assert_agreement()

        # checkpoint blocked from active: the member persists blocked through
        # the shared blocked-persist tail; the group stays active.
        self.rewrite_manifest(reactivate_member("task-2"))
        blocked_receipt = self.member_receipt(
            "task-2", 2, 1, session_id=anchor_session,
            status="blocked", reason_code="approval-required",
        )
        blocked = driver.record_worker_checkpoint(blocked_receipt)
        self.assertEqual(blocked["status"], "blocked", blocked)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-2"]["status"], "blocked")
        self.assertEqual(state["claims"]["task-2"]["state"], "blocked")
        assert_group_state("active")
        assert_agreement()

        # retryable-error receipt from active: the member retry runs through
        # the group's own continuation primitive (the anchor-session window),
        # never the plain driver relaunch, and the retry receipt lands.
        self.rewrite_manifest(reactivate_member("task-2"))
        retry_receipt = self.member_receipt(
            "task-2", 2, 1, session_id=anchor_session,
            status="error", reason_code="runtime-error",
            retry_policy={"mode": "bounded", "max_attempts": 1, "attempts_remaining": 1},
        )
        retry_adapter = RecordingAdapter()
        retried = self.batch_driver(adapter=retry_adapter).record_worker_checkpoint(retry_receipt)
        self.assertEqual(retried["status"], "success", retried)
        self.assertEqual([call["task_id"] for call in retry_adapter.resume_calls], ["task-2"])
        self.assertEqual([call["session_id"] for call in retry_adapter.resume_calls], [anchor_session])
        # No plain driver relaunch: the fresh adapter records no launch call.
        self.assertEqual(retry_adapter.launch_calls, [])
        assert_group_state("active")
        assert_agreement()

        # done from active: the member closes and the group advances to the
        # next member under the same lock.
        commit2 = self.commit_files("t2-1.txt")
        done2 = driver.record_done(self.member_done("task-2", 2, commit2))
        self.assertEqual(done2["status"], "success", done2)
        self.assertEqual(done2["actions"][0]["type"], "resume_member")
        self.assertEqual(done2["actions"][0]["task_id"], "task-3")
        assert_group_state("active")
        self.assertEqual(group_record()["active_member"], "task-3")
        assert_agreement()

        # done from active, session-less cell: an
        # adapter whose receipts carry no session id anywhere reaches the
        # same cell, so the exhaustiveness claim must cover it. The advance
        # fails the group atomically (the release shape), the done
        # lands, and the released staged member is re-claimed individually:
        # a state from which an entrypoint proceeds, never a wedge.
        main_fixture = json.loads(self.state_path.read_text(encoding="utf-8"))
        main_head = self._git_stdout("rev-parse", "HEAD")
        self.batch_manifest(self.disjoint_tasks(2))
        sessionless_driver = self.batch_driver(adapter=SessionlessRecordingAdapter())
        sessionless_driver.launch_next_task(batch=True)
        sessionless_commit = self.commit_files("t1-1.txt")
        sessionless_done = sessionless_driver.record_done(self.member_done("task-1", 1, sessionless_commit))
        self.assertEqual(sessionless_done["status"], "success", sessionless_done)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(self.live_group(state)["state"], "failed")
        self.assertIsNone(self.live_group(state)["active_member"])
        self.assertEqual(state["tasks"]["task-1"]["status"], "checkpointed")
        self.assertEqual(state["claims"]["task-2"]["state"], "claimed")
        self.assertNotIn("group_id", state["claims"]["task-2"])
        assert_agreement()
        # Restore the main fixture - manifest and git HEAD together, so the
        # next arm's done-boundary witnesses diff against the baselines the
        # fixture recorded - and it drives the same active seat (task-3)
        # the earlier arms left.
        self._git("reset", "-q", "--hard", main_head)
        self.rewrite_manifest(lambda state: state.update(main_fixture))
        assert_group_state("active")
        self.assertEqual(group_record()["active_member"], "task-3")

        # resume from active: selects only the active member and resumes the
        # anchor session.
        self.rewrite_manifest(block_member("task-3", anchor_session, resume_allowed=True))
        resume_adapter = RecordingAdapter()
        resumed = self.batch_driver(adapter=resume_adapter).resume()
        self.assertEqual(resumed["status"], "success", resumed)
        self.assertEqual(resume_adapter.resume_calls[0]["task_id"], "task-3")
        self.assertEqual(resume_adapter.resume_calls[0]["session_id"], anchor_session)
        assert_group_state("active")
        assert_agreement()

        # continue --batch from active: advances through the active member.
        self.rewrite_manifest(reactivate_member("task-3"))
        continue_adapter = RecordingAdapter()
        continued = self.batch_driver(adapter=continue_adapter).continue_parent(batch=True)
        self.assertEqual(continued["status"], "success", continued)
        self.assertEqual(continue_adapter.resume_calls[0]["task_id"], "task-3")
        assert_group_state("active")
        assert_agreement()

        # reclaim (resumable member) from active: refused naming the group,
        # whatever the lease state; the manifest stays byte-identical.
        self.rewrite_manifest(block_member("task-3", anchor_session, resume_allowed=True, expired=True))
        reclaim_driver = self.batch_driver(clock=lambda: self.FIXED_NOW)
        before = self.state_path.read_bytes()
        reclaim_refused = reclaim_driver.reclaim("task-3")
        self.assertEqual(reclaim_refused["status"], "blocked")
        self.assertEqual(reclaim_refused["reason_code"], "stale-claim")
        self.assertTrue(any(group_id in item for item in reclaim_refused["evidence"]), reclaim_refused["evidence"])
        self.assertTrue(any("continue --batch" in item for item in reclaim_refused["evidence"]))
        self.assertEqual(self.state_path.read_bytes(), before)
        assert_agreement()

        # reclaim (non-resumable member) from active: the one executable
        # exit - the member rotates back to pending and the group fails
        # atomically in the same locked compare-and-swap. Already-closed
        # members stay closed history; no staged member remains here.
        self.rewrite_manifest(block_member("task-3", anchor_session, resume_allowed=False))
        released = self.batch_driver(clock=lambda: self.FIXED_NOW).reclaim("task-3")
        self.assertEqual(released["status"], "success", released)
        self.assertTrue(any(f"group_failed={group_id}" in item for item in released["evidence"]), released["evidence"])
        assert_group_state("failed")
        self.assertIsNone(group_record()["active_member"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-3"]["state"], "replaced")
        self.assertEqual(state["tasks"]["task-3"]["status"], "pending")
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")
        self.assertEqual(state["claims"]["task-2"]["state"], "closed")
        assert_agreement()

        # group release from active: reached only through the exit above or
        # the advance-time authorization belt; both are covered here and by
        # test_batch_advance_authorization_failure_fails_group_and_completes_done.

        # ------------------------------------------------------------------
        # closed: the documented terminal; every operation has a defined
        # no-mutation or queue-continuation outcome.
        # ------------------------------------------------------------------
        self.batch_manifest(self.disjoint_tasks(3))
        close_adapter = RecordingAdapter()
        close_driver = self.batch_driver(adapter=close_adapter)
        close_driver.launch_next_task(batch=True)
        closed_commit1 = self.commit_files("t1-1.txt")
        self.assertEqual(close_driver.record_done(self.member_done("task-1", 1, closed_commit1))["status"], "success")
        self.assertEqual(close_driver.continue_parent(batch=True)["status"], "success")
        closed_commit2 = self.commit_files("t2-1.txt")
        self.assertEqual(close_driver.record_done(self.member_done("task-2", 2, closed_commit2))["status"], "success")
        self.assertEqual(close_driver.continue_parent(batch=True)["status"], "success")
        closed_commit3 = self.commit_files("t3-1.txt")
        self.assertEqual(close_driver.record_done(self.member_done("task-3", 3, closed_commit3))["status"], "success")
        assert_group_state("closed")
        self.assertIsNone(group_record()["active_member"])
        assert_agreement()
        closed_snapshot = json.loads(self.state_path.read_text(encoding="utf-8"))

        def rewind_closed():
            self.rewrite_manifest(lambda state: state.update(json.loads(json.dumps(closed_snapshot))))

        # claim from closed: the queue is drained (defined claimed: false).
        drained = self.batch_driver().claim_next_task()
        self.assertEqual(drained["status"], "success")
        self.assertFalse(drained["claimed"])
        assert_agreement()

        # launch from closed: no live group and a drained queue: the defined
        # claimed-false envelope, never an undefined error.
        end_drained = self.batch_driver(adapter=RecordingAdapter()).launch_next_task(batch=True)
        self.assertEqual(end_drained["status"], "success")
        self.assertFalse(end_drained["claimed"])
        assert_agreement()

        # checkpoint success/blocked/retryable from closed: late member
        # receipts fence as stale-claim with no mutation.
        for overrides in LATE_RECEIPT_ARMS:
            rewind_closed()
            fence_driver = self.batch_driver(adapter=RecordingAdapter())
            before_closed = self.state_path.read_bytes()
            fenced = fence_driver.record_worker_checkpoint(late_member_receipt("task-1", **overrides))
            self.assertEqual(fenced["status"], "blocked", (overrides, fenced))
            self.assertEqual(fenced["reason_code"], "stale-claim")
            self.assertEqual(self.state_path.read_bytes(), before_closed)
        assert_agreement()

        # done from closed: a late done replay is unfenced done evidence.
        rewind_closed()
        done_driver = self.batch_driver()
        before_closed = self.state_path.read_bytes()
        late_done = done_driver.record_done(self.member_done("task-1", 1, closed_commit1))
        self.assertEqual(late_done["status"], "blocked")
        # The member fence refuses before any commit work: a terminal group
        # routes no member action.
        self.assertEqual(late_done["reason_code"], "stale-claim")
        self.assertEqual(self.state_path.read_bytes(), before_closed)
        assert_agreement()

        # resume from closed: no resumable blocked task (defined block).
        no_resume = self.batch_driver(adapter=RecordingAdapter()).resume()
        self.assertEqual(no_resume["status"], "blocked")
        self.assertEqual(no_resume["reason_code"], "stale-claim")
        assert_agreement()

        # continue --batch from closed: no live group; the defined
        # terminal-evidence block (the run is at its documented end).
        closed_continued = self.batch_driver(adapter=RecordingAdapter()).continue_parent(batch=True)
        self.assertEqual(closed_continued["status"], "blocked")
        self.assertEqual(closed_continued["reason_code"], "done-pending")
        assert_agreement()

        # reclaim (either member shape) from closed: closed claims are
        # outside the reclaimable set; refused, no mutation.
        for member in ("task-1", "task-2"):
            rewind_closed()
            reclaim_driver = self.batch_driver(clock=lambda: self.FIXED_NOW)
            before_closed = self.state_path.read_bytes()
            reclaim_closed = reclaim_driver.reclaim(member)
            self.assertEqual(reclaim_closed["status"], "blocked")
            self.assertEqual(reclaim_closed["reason_code"], "stale-claim")
            self.assertEqual(self.state_path.read_bytes(), before_closed)
        assert_agreement()

        # group release from closed: not reachable (both release arms are
        # guarded by the live-group fence); no operation above mutated the
        # terminal record.

        # ------------------------------------------------------------------
        # failed: the documented terminal whose forward motion is the
        # released individual queue.
        # ------------------------------------------------------------------
        self.batch_manifest(self.disjoint_tasks(3))
        fail_driver = self.batch_driver(adapter=RecordingAdapter())
        fail_driver.launch_next_task(batch=True)
        failed_commit1 = self.commit_files("t1-1.txt")
        self.assertEqual(fail_driver.record_done(self.member_done("task-1", 1, failed_commit1))["status"], "success")
        failed_group_id = runtime.load_manifest(self.state_path)["claims"]["task-2"]["group_id"]
        failed_anchor = runtime.load_manifest(self.state_path)["claim_groups"][failed_group_id]["anchor_session"]
        self.rewrite_manifest(block_member("task-2", failed_anchor, resume_allowed=False))
        exit_outcome = self.batch_driver(clock=lambda: self.FIXED_NOW).reclaim("task-2")
        self.assertEqual(exit_outcome["status"], "success", exit_outcome)
        assert_group_state("failed")
        assert_agreement()
        failed_snapshot = json.loads(self.state_path.read_text(encoding="utf-8"))

        def rewind_failed():
            self.rewrite_manifest(lambda state: state.update(json.loads(json.dumps(failed_snapshot))))

        # claim from failed: the queue re-took a released task individually.
        retook = self.batch_driver().claim_next_task()
        self.assertTrue(retook["claimed"], retook)
        self.assertNotIn("group_id", retook)
        fresh = runtime.load_manifest(self.state_path)["claims"][retook["task_id"]]
        self.assertNotIn("group_id", fresh)
        assert_agreement()

        # launch from failed: the individual claim launches through the
        # single-task path, no batch fields, no member action. task-1 is
        # complete history; the released queue re-enters at task-2.
        rewind_failed()
        relaunch_adapter = RecordingAdapter()
        relaunched = self.batch_driver(adapter=relaunch_adapter).launch_next_task()
        self.assertEqual(relaunched["status"], "success", relaunched)
        self.assertNotIn("batch", relaunched)
        self.assertEqual(relaunch_adapter.launch_calls[0]["task_id"], "task-2")
        assert_agreement()

        # continue --batch from failed: no live group routes the continuation,
        # so the fresh batch opt-in may assemble a NEW group from the
        # released tasks; the failed record stays terminal, never revived.
        rewind_failed()
        rebatch_adapter = RecordingAdapter()
        rebatched = self.batch_driver(adapter=rebatch_adapter).continue_parent(batch=True)
        self.assertEqual(rebatched["status"], "success", rebatched)
        self.assertEqual(rebatch_adapter.launch_calls[0]["task_id"], "task-2")
        state = runtime.load_manifest(self.state_path)
        states_seen = [g["state"] for g in state.get("claim_groups", {}).values() if isinstance(g, dict)]
        self.assertEqual(states_seen.count("failed"), 1, states_seen)
        self.assertEqual(states_seen.count("active"), 1, states_seen)
        assert_agreement()

        # checkpoint success/blocked/retryable from failed: late member
        # receipts fence as stale-claim with no mutation.
        for overrides in LATE_RECEIPT_ARMS:
            rewind_failed()
            fence_driver = self.batch_driver(adapter=RecordingAdapter())
            before_failed = self.state_path.read_bytes()
            fenced = fence_driver.record_worker_checkpoint(late_member_receipt("task-3", **overrides))
            self.assertEqual(fenced["status"], "blocked", (overrides, fenced))
            self.assertEqual(fenced["reason_code"], "stale-claim")
            self.assertEqual(self.state_path.read_bytes(), before_failed)
        assert_agreement()

        # done from failed: a late done replay from the released
        # never-launched staged member (claim closed) is unfenced done
        # evidence; a late replay from the progressed member (checkpointed,
        # its own closed claim) is fenced by the member receipt fence.
        for member, expected_reason in (("task-3", "done-pending"), ("task-1", "stale-claim")):
            rewind_failed()
            done_driver = self.batch_driver()
            before_failed = self.state_path.read_bytes()
            failed_done = done_driver.record_done(self.member_done(member, 3, failed_commit1))
            self.assertEqual(failed_done["status"], "blocked")
            self.assertEqual(failed_done["reason_code"], expected_reason, (member, failed_done))
            self.assertEqual(self.state_path.read_bytes(), before_failed)
        assert_agreement()

        # resume from failed: the released members sit pending or closed, so
        # the defined no-resumable-task block stands.
        rewind_failed()
        failed_resume = self.batch_driver(adapter=RecordingAdapter()).resume()
        self.assertEqual(failed_resume["status"], "blocked")
        self.assertEqual(failed_resume["reason_code"], "stale-claim")
        assert_agreement()

        # reclaim (either member shape) from failed: the exit already ran
        # (the member claim is replaced, the staged claims closed); refused,
        # no mutation.
        for member in ("task-2", "task-3"):
            rewind_failed()
            reclaim_driver = self.batch_driver(clock=lambda: self.FIXED_NOW)
            before_failed = self.state_path.read_bytes()
            reclaim_failed = reclaim_driver.reclaim(member)
            self.assertEqual(reclaim_failed["status"], "blocked")
            self.assertEqual(reclaim_failed["reason_code"], "stale-claim")
            self.assertEqual(self.state_path.read_bytes(), before_failed)
        assert_agreement()

        # group release from failed: not reachable; `failed` is terminal and
        # no operation above re-released or revived the group record.

    def test_group_state_writes_route_through_the_single_choke_point(self):
        # The group-lifecycle analog of the G2 receipt-identity
        # structural pin: the contract's single choke point invariant ("no
        # site other than the primitive writes group state") is pinned by an
        # AST walk over the driver source, so a future direct
        # claim_groups-record write ships red instead of green. Claim-record
        # writes (a claim variable, or a subscript chain through
        # manifest["claims"]) and the authoritative top-level
        # manifest["progress_revision"] counter stay outside the invariant;
        # a direct claim_groups-record write or a bare group-record variable
        # written anywhere but _set_group_state fails.
        source = (ROOT / "scripts/execute_plan_runtime.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def enclosing_function(node):
            while node is not None:
                node = parents.get(node)
                if isinstance(node, ast.FunctionDef):
                    return node
            return None

        def base_of(target):
            # Strip nested subscripts off the store target's base: return
            # the constant keys seen on the way and the root expression.
            keys = []
            value = target
            while isinstance(value, ast.Subscript):
                if isinstance(value.slice, ast.Constant):
                    keys.append(value.slice.value)
                value = value.value
            return keys, value

        GROUP_KEYS = {"state", "active_member", "progress_revision"}
        choke_writes = []
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            else:
                continue
            for target in targets:
                if not isinstance(target, ast.Subscript) or not isinstance(target.slice, ast.Constant):
                    continue
                if target.slice.value not in GROUP_KEYS:
                    continue
                keys, root = base_of(target.value)
                owner = enclosing_function(node)
                owner_name = owner.name if owner is not None else "<module>"
                if "claim_groups" in keys:
                    # A direct claim_groups-record write: never allowed,
                    # not even inside the primitive (which writes through
                    # its own group reference).
                    offenders.append((owner_name, target.slice.value, "direct claim_groups write"))
                elif "claims" in keys:
                    # A claim-record write through the claims collection:
                    # claim state is not group state.
                    pass
                elif isinstance(root, ast.Name) and root.id not in {"claim", "manifest"}:
                    # A bare group-record variable write.
                    if owner_name == "_set_group_state":
                        choke_writes.append((owner_name, target.slice.value))
                    else:
                        offenders.append((owner_name, target.slice.value, "bare group-record write"))
        self.assertEqual(
            sorted(choke_writes),
            sorted([
                ("_set_group_state", "state"),
                ("_set_group_state", "active_member"),
                ("_set_group_state", "progress_revision"),
            ]),
            choke_writes,
        )
        self.assertEqual(offenders, [], offenders)

    def test_startup_group_member_launch_evidence_resolves_through_group(self):
        # Member claims never carry launch records (the ONE record
        # lives on the group), so the ambient discriminator that classifies
        # pre-launch versus launched claims must resolve member evidence
        # through claim_groups[group_id]['launch_record']. A launched
        # member wearing ambient dirt keeps the hard dirty-worktree block
        # (post-launch dirt is worker-shaped); a merely-claimed group keeps
        # the resumable cleanup-required classification.
        self.batch_manifest(self.disjoint_tasks(2))
        self.batch_driver(adapter=RecordingAdapter()).launch_next_task(batch=True)
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        launched = self.batch_driver().reconcile_startup()
        self.assertEqual(launched["reason_code"], "dirty-worktree")
        self.assertFalse(launched["resume_allowed"])

        self.batch_manifest(self.disjoint_tasks(2))
        self.batch_driver().claim_next_task(batch=True)
        (self.root / ".DS_Store").write_text("ambient\n", encoding="utf-8")
        claimed = self.batch_driver().reconcile_startup()
        self.assertEqual(claimed["reason_code"], "cleanup-required")
        self.assertTrue(claimed["resume_allowed"])

    def _ordinal_tasks(self, count):
        # Non-lexicographic probe: ids task-1..task-12 with NO number field;
        # only the persisted document ordinal carries the plan order, so a
        # number-based sort degenerates to lexicographic order
        # (task-1, task-10, task-11, ...).
        return [
            {"id": f"task-{n}", "status": "pending", "checkbox": False, "allowed_paths": [f"./o{n}.txt"]}
            for n in range(1, count + 1)
        ]

    def test_document_order_ordinal_selection_across_claim_batch_and_readiness(self):
        # The persisted document ordinal is the canonical queue order
        # and every selection site consumes it - single claims walk the plan
        # in document order (never lexicographic id order), the batch prefix
        # assembles in document order so member ordinals agree with the
        # plan, and the readiness decision names the provable next task in
        # document order.
        document_order = [f"task-{n}" for n in range(1, 13)]
        self.batch_manifest(self._ordinal_tasks(12))
        driver = self.batch_driver()
        claimed_order = []
        for _ in document_order:
            claim = driver.claim_next_task()
            self.assertTrue(claim["claimed"])
            claimed_order.append(claim["task_id"])

            def close_claim(task_id):
                def mutate(state):
                    state["claims"].pop(task_id, None)
                    state["tasks"][task_id]["status"] = "complete"
                    state["tasks"][task_id]["checkbox"] = True
                return mutate

            self.rewrite_manifest(close_claim(claim["task_id"]))
        self.assertEqual(claimed_order, document_order)

        # The batch prefix inherits document order.
        self.batch_manifest(self._ordinal_tasks(12))
        batch = self.batch_driver().claim_next_task(batch=True)
        self.assertTrue(batch["claimed"])
        self.assertEqual(batch["members"], document_order[:4])
        self.assertEqual(batch["member_ordinals"], {f"task-{n}": n for n in range(1, 5)})

        # The readiness decision's provable next task follows document
        # order: with task-1 complete, the next task is task-2, never the
        # lexicographic task-10.
        self.batch_manifest(self._ordinal_tasks(12))
        self.rewrite_manifest(lambda state: (
            state["tasks"]["task-1"].update({"status": "complete", "checkbox": True}),
        ))
        plan_path = self.write_plan(
            "# Fixture plan\n\n"
            + "".join(f"### Task {n}: title\n- [ ] item {n}\n\n" for n in range(1, 13))
        )
        readiness = self.batch_driver().readiness(plan_path)
        self.assertEqual(readiness["next_task_id"], "task-2", readiness["failed_conditions"])

    def test_batch_member_done_without_anchor_session_falls_back_to_task_session(self):
        # The anchor capture is receipt-driven, so a group whose
        # receipts never captured the anchor wedged at the first member
        # done: the advance refused for the missing anchor session, the
        # done-pending member refused relaunch, and a later done failed on
        # the same missing session. The advance now falls back to the
        # completed task's own session and captures it; only when no
        # session exists anywhere does the refusal stand.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = RecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        group_id = done["actions"][0]["group_id"]
        task_session = runtime.load_manifest(self.state_path)["tasks"]["task-1"]["session_id"]
        self.assertTrue(task_session)

        # Strip the captured anchor: the group has no anchor session, the
        # done envelope carries none, and only the task still holds one.
        def strip_anchor(state):
            state["claim_groups"][group_id]["anchor_session"] = None
            state["tasks"]["task-2"]["status"] = "done-pending"  # undone below
        self.rewrite_manifest(strip_anchor)
        # Redo the advance for real: member-1 is already checkpointed and
        # its done was consumed, so re-drive the wedge by reverting member-1
        # to done-pending with its claim live and re-running the handoff.
        def rewind_to_done_pending(state):
            group = state["claim_groups"][group_id]
            group["active_member"] = "task-1"
            group["state"] = "active"
            state["tasks"]["task-1"]["status"] = "done-pending"
            state["tasks"]["task-1"].pop("complete", None)
            state["claims"]["task-1"]["state"] = "launched"
            # task-2 stays a staged pending member with its claim.
            state["tasks"]["task-2"]["status"] = "pending"
            state["claims"]["task-2"].pop("policy_token", None)
            state["checkpoints"].pop("task-1:done", None)

        self.rewrite_manifest(rewind_to_done_pending)
        wedged_driver = self.batch_driver(adapter=adapter)
        commit1b = self.commit_files("t1-1.txt")
        retried = wedged_driver.record_done(self.member_done("task-1", 1, commit1b))
        self.assertEqual(retried["status"], "success", retried)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claim_groups"][group_id]["anchor_session"], task_session)
        self.assertEqual(retried["actions"][0]["type"], "resume_member")
        self.assertEqual(retried["actions"][0]["session_id"], task_session)
        # The captured anchor pins the fence: a member receipt whose
        # session matches neither the anchor nor the task session is fenced.
        active = state["claims"]["task-2"]
        wrong = self.member_receipt("task-2", 2, active["generation"], session_id="sess-rogue")
        fenced = self.batch_driver().record_worker_checkpoint(wrong)
        self.assertEqual(fenced["status"], "blocked")
        self.assertEqual(fenced["reason_code"], "stale-claim")

    def test_batch_sessionless_advance_fails_group_and_lands_done(self):
        # The schema-legal success adapter whose receipts carry
        # no session id anywhere leaves the group without an anchor session,
        # and the advance-time capture used to refuse the done forever
        # (blocked done-pending). That wedged the group with no exit: done
        # replay, continue --batch, resume, reclaim (done-pending is a
        # progressed status), and claim_next_task (live group) all refuse.
        # The advance now fails the group atomically in the release
        # shape: the completed member's done lands, the staged member is
        # released to the pending queue, and the generic next-claim proceeds
        # from the failed terminal.
        self.batch_manifest(self.disjoint_tasks(2))
        adapter = SessionlessRecordingAdapter()
        driver = self.batch_driver(adapter=adapter)
        driver.launch_next_task(batch=True)
        state = runtime.load_manifest(self.state_path)
        self.assertIsNone(self.live_group(state)["anchor_session"])
        self.assertNotIn("session_id", state["tasks"]["task-1"])
        commit1 = self.commit_files("t1-1.txt")
        done = driver.record_done(self.member_done("task-1", 1, commit1))
        # The done itself lands (pre-fix: blocked done-pending, the wedge).
        self.assertEqual(done["status"], "success", done)
        state = runtime.load_manifest(self.state_path)
        # Exactly one group record remains and it is the failed terminal.
        self.assertEqual(self.live_group(state)["state"], "failed")
        failed = self.live_group(state)
        self.assertIsNone(failed["active_member"])
        self.assertTrue(any(
            entry.get("event") == "batch-group-failed"
            and entry.get("member") == "task-2"
            and "session" in str(entry.get("reason", ""))
            and "task-2" in (entry.get("released_members") or [])
            for entry in state["history"]
        ), state["history"][-3:])
        self.assertEqual(state["tasks"]["task-1"]["status"], "checkpointed")
        self.assertEqual(state["claims"]["task-1"]["state"], "closed")
        # The group reached a state from which an entrypoint proceeds: the
        # released staged member re-entered the queue and the done's
        # attached generic next-claim already took it as a fresh individual
        # claim with no group reference.
        self.assertTrue(any(
            action.get("type") == "launch-task" and action.get("task_id") == "task-2"
            for action in done.get("actions", [])
        ), done.get("actions"))
        fresh_claim = state["claims"]["task-2"]
        self.assertEqual(fresh_claim["state"], "claimed")
        self.assertNotIn("group_id", fresh_claim)
        self.assertEqual(state["tasks"]["task-2"]["status"], "claimed")

    def test_batch_sessionless_timeout_wedge_recovers_through_continue(self):
        # The recovery arm's continue entry: the
        # session-less blocked anchor wedge recovers through
        # continue_parent(batch=True) as well as resume(): exactly one
        # launch call rotates the member to attempt 2, the group attempt
        # record re-arms, and a late receipt carrying the dead attempt's
        # claim token fences as owner-mismatch.
        self.batch_manifest(self.disjoint_tasks(2))

        class TimeoutAdapter:
            def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
                raise TimeoutError("launch deadline exceeded")

        driver = self.batch_driver(adapter=TimeoutAdapter())
        driver.claim_next_task(batch=True)
        blocked = driver.launch_next_task(batch=True)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["reason_code"], "timeout")
        state = runtime.load_manifest(self.state_path)
        dead_token = state["claims"]["task-1"]["token"]

        recovery_adapter = RecordingAdapter()
        recovered = self.batch_driver(adapter=recovery_adapter).continue_parent(batch=True)
        self.assertEqual(recovered["status"], "success", recovered)
        self.assertEqual(len(recovery_adapter.launch_calls), 1)
        self.assertEqual(recovery_adapter.launch_calls[0]["task_id"], "task-1")
        state = runtime.load_manifest(self.state_path)
        self.assertNotEqual(state["claims"]["task-1"]["token"], dead_token)
        self.assertEqual(state["claims"]["task-1"]["attempt"], 2)
        self.assertEqual(self.live_group(state)["member_attempts"]["task-1"]["attempt"], 2)
        late = self.member_receipt("task-1", 1, state["claims"]["task-1"]["generation"])
        late["claim_token"] = dead_token
        fenced = self.batch_driver().record_worker_checkpoint(late)
        self.assertEqual(fenced["status"], "blocked")
        self.assertEqual(fenced["reason_code"], "owner-mismatch")


class ArchiveGateFixtureBase(unittest.TestCase):
    """Shared fixture scaffolding for the archive/terminal gate classes (fixture scaffolding dedup origin).

    Owns exactly the members the four-class helper inventory proves shared:
    the fixture plan text and shared path constants, the TOML-fence facts
    writer, the completed-directory mkdir, the manifest seed from the
    class-level task-row list, the active-plan writer, the sidecar writer
    and clean-sidecar payload, the pre-archive stage call, and the driver
    constructor. Single-class helpers stay local to their classes
    (``_git``, ``complete_all_tasks``, ``seed_gate``, ``write_archived_plan``,
    the residual helpers, the clock). The hermetic git setup is gated behind
    ``requires_git`` so the mixin never silently grants git init to classes
    that never prove real ancestry: only ``ArchiveGatePreArchiveTest`` opts
    in, because its success arm proves a real ancestor-or-self commit.
    """

    # Fixture plan text every archive fixture writes; the checkboxes are
    # complete so plan-file evidence never fires unless a test overrides the
    # plan or the manifest rows.
    PLAN_TEXT = "# fixture plan\n\n### Task 3: third\n### Task 4: fourth\n\n- [x] task-3\n- [x] task-4\n"
    ACTIVE_PLAN_REL = "docs/plans/fixture-plan.md"
    SIDECAR_REL = "docs/reviews/fixture-r3.stats.json"
    PLAN_SLUG = "fixture-plan"
    # Manifest task rows seeded by ``seed_manifest``; a class overrides this
    # to seed a differing completion shape (ArchiveGatePreArchiveTest seeds
    # task-4 pending so its incompleteness refusal arms have a target).
    TASK_ROWS = [
        {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
        {"id": "task-4", "number": 4, "status": "complete", "checkbox": True},
    ]
    # Hermetic git is opt-in; each class also pins its own owner identity.
    requires_git = False
    OWNER: str

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        if self.requires_git:
            # Hermetic git: neutralize host global/system config so hooks,
            # gpgsign, or aliases from the developer machine cannot leak into
            # the fixture repository; identity is set repo-locally below.
            self._git_env = dict(os.environ)
            self._git_env["GIT_CONFIG_GLOBAL"] = "/dev/null"
            self._git_env["GIT_CONFIG_SYSTEM"] = "/dev/null"
            subprocess.run(["git", "init", "-q"], cwd=self.root, check=True, env=self._git_env)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True, env=self._git_env)
            subprocess.run(["git", "config", "user.name", "Archive Gate Test"], cwd=self.root, check=True, env=self._git_env)
            (self.root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore"], cwd=self.root, check=True, env=self._git_env)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True, env=self._git_env)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_facts(self) -> None:
        # The real TOML-fence facts format (this fence is the only place the
        # directory keys live; the markdown table-row parser cannot read
        # them), resolving the plans directory and its completed sibling
        # exactly like the production facts file.
        facts = self.root / ".ai-playbook" / "facts.md"
        facts.parent.mkdir(parents=True, exist_ok=True)
        facts.write_text(
            "```toml\n"
            "plans_dir = \"docs/plans/\"\n"
            "plans_completed_dir = \"docs/plans/completed/\"\n"
            "```\n",
            encoding="utf-8",
        )

    def make_completed_dir(self) -> None:
        # The resolved destination directory exists on disk, so the
        # lookalike-candidate refusal proves the candidate-mismatch arm and
        # the success arm passes the destination-existence check.
        (self.root / "docs/plans/completed").mkdir(parents=True, exist_ok=True)

    def seed_manifest(self) -> None:
        runtime.create_manifest(self.state_path, self.PLAN_SLUG, self.TASK_ROWS)

    def write_active_plan(self, text: str | None = None, rel: str | None = None) -> str:
        rel = rel or self.ACTIVE_PLAN_REL
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if text is not None else self.PLAN_TEXT, encoding="utf-8")
        return rel

    def write_sidecar(self, payload: dict) -> str:
        path = self.root / self.SIDECAR_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return self.SIDECAR_REL

    @staticmethod
    def clean_sidecar(**overrides) -> dict:
        payload = {"schema_version": 1, "source_kind": "code", "verdict": "yes", "findings": []}
        payload.update(overrides)
        return payload

    def driver(self, **kwargs):
        kwargs.setdefault("commit_lookup", lambda _commit: True)
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug=self.PLAN_SLUG,
            owner=self.OWNER,
            repo_root=self.root,
            **kwargs,
        )

    def assert_refusal_preserves_manifest(self, before: bytes, context: str = "") -> None:
        """A terminal refusal may append only its terminal-refused event.

        The refusal tail's history append is the one allowed evidence write
        after a refusal (the outcome is composed first and the append never
        changes it), so this pin holds every manifest field outside the
        appended history tail and the write timestamp byte-stable, requires
        each appended event to be exactly a terminal-refused record, and
        requires the timestamp to have advanced with the save.
        """

        before_state = json.loads(before)
        after_state = json.loads(self.state_path.read_bytes())
        before_stamp = before_state.pop("updated_at")
        after_stamp = after_state.pop("updated_at")
        self.assertIsInstance(after_stamp, (int, float), context)
        self.assertGreaterEqual(after_stamp, before_stamp, context)
        prefix = before_state.pop("history", [])
        suffix = after_state.pop("history", [])
        self.assertEqual(suffix[: len(prefix)], prefix, context)
        for event in suffix[len(prefix):]:
            self.assertEqual(event.get("event"), "terminal-refused", context)
        self.assertEqual(after_state, before_state, context)

    def pre_archive(self, driver, **overrides) -> dict:
        payload = {
            "plan_path": self.ACTIVE_PLAN_REL,
            "destination": "",
            "review_sidecar": "",
            "last_commit_sha": "abcdef1",
            "phase5_checklist": ["tests"],
            "residual_policy": None,
        }
        payload.update(overrides)
        if not payload["review_sidecar"]:
            # Default clean sidecar, written only when the caller did not
            # supply one: a supplied path is never clobbered by a rewrite.
            payload["review_sidecar"] = self.write_sidecar(self.clean_sidecar())
        return driver.mark_terminal(
            stage="pre-archive",
            plan_path=payload["plan_path"],
            destination=payload["destination"],
            review_sidecar=payload["review_sidecar"],
            last_commit_sha=payload["last_commit_sha"],
            phase5_checklist=payload["phase5_checklist"],
            residual_policy=payload["residual_policy"],
        )


class ArchiveGatePreArchiveTest(ArchiveGateFixtureBase):
    """Terminal pre-archive eligibility stage (archive origin fixtures 1, 2, 3, and the pre-move half of fixture 5).

    The driver's terminal operation gains a staged shape: the pre-archive
    stage evaluates one fixed-order eligibility predicate and either refuses
    with the first failed condition (blocked ``done-pending``, the machine
    manifest byte-identical, the active plan still in place) or records the
    ``archive_gate`` receipt without touching ``workflow_state`` or writing a
    ``terminal_receipt``. The class also owns the sanctioned
    residual-acceptance exit fixtures (origin D): an optional structured
    ``residual_policy`` input (the named finding ids, the grant source, and
    the recorded-at epoch) opens an OR-branch in the clean-round sidecar
    predicate that additionally accepts the focused verification-round
    sidecar when the policy's recorded-at predates that round's date and no
    findings row is both ``blocking: true`` and a member of the policy's
    finding ids; blocking rows outside the set are the backlogged residuals
    and are permitted, a blocking row inside the set still refuses, a
    blocking row whose id is not an integer refuses (membership against the
    policy's integer finding ids cannot prove such a row outside the named
    set), a present verdict must be ``yes`` or ``no`` (the sidecar verdict
    may be ``no`` precisely because the out-of-set residuals are staged;
    any other value refuses), and the membership rule replaces the
    zero-blocking rule.
    """

    # task-4 stays pending so the machine-completeness refusal arms have a
    # target; every arm that needs a complete manifest calls
    # complete_all_tasks() first.
    TASK_ROWS = [
        {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
        {"id": "task-4", "number": 4, "status": "pending", "checkbox": False},
    ]
    ROUND_DATE = "2026-09-18"
    ROUND_DAY_EPOCH = datetime(2026, 9, 18, tzinfo=timezone.utc).timestamp()
    # The success arm proves a real ancestor-or-self commit, so this class
    # alone initializes the hermetic fixture repository.
    requires_git = True
    OWNER = "archive-gate-owner"

    def setUp(self) -> None:
        super().setUp()
        self.write_facts()
        self.make_completed_dir()
        self.seed_manifest()
        self.write_active_plan()

    def _git(self, *args) -> str:
        completed = subprocess.run(["git", *args], cwd=self.root, env=self._git_env, capture_output=True, text=True, check=True)
        return completed.stdout.strip()

    def complete_all_tasks(self) -> None:
        state = runtime.load_manifest(self.state_path)
        for task in state["tasks"].values():
            task.update({"status": "complete", "checkbox": True})
        runtime._safe_write_json(self.state_path, state)

    def test_refuses_lookalike_destination(self):
        # Fixture 1: a complete plan whose candidate destination is the bare
        # lookalike folder name is refused by the fail-closed safe-path
        # guard, which rejects directory and trailing-slash destination
        # forms before any candidate equality runs; the manifest bytes plus
        # the active plan file stay exactly where they were.
        self.complete_all_tasks()
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, destination="plans_completed/")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unsupported archive destination" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)
        self.assertTrue((self.root / self.ACTIVE_PLAN_REL).is_file())

    def test_accepts_declared_full_path_destination(self):
        # Destination-candidate equality, accept arm: passing the echoed
        # declared full-file path (resolved completed directory plus the
        # plan filename) satisfies the candidate equality exactly and the
        # gate records that same declared destination.
        self.complete_all_tasks()
        result = self.pre_archive(self.driver(), destination="docs/plans/completed/fixture-plan.md")
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["archive_gate"]["declared_destination"], "docs/plans/completed/fixture-plan.md")
        self.assertEqual(state["workflow_state"], "active")

    def test_refuses_resolved_directory_form_destination(self):
        # Directory-form refuse arm: the resolved completed directory alone
        # (without the plan filename) is rejected by the fail-closed
        # safe-path guard, which refuses directory and trailing-slash
        # destination forms before any candidate equality runs, naming
        # unsupported archive destination, with the manifest untouched.
        self.complete_all_tasks()
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, destination="docs/plans/completed/")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unsupported archive destination" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("docs/plans/completed/" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_non_equal_file_destination(self):
        # Destination-candidate equality, file-valued refuse arm: a safe
        # repository-relative file path that is simply not the declared
        # destination refuses naming the facts-resolved destination, with
        # the manifest bytes untouched.
        self.complete_all_tasks()
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, destination="docs/plans/completed/other-plan.md")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unsupported archive destination" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("the facts-resolved destination is docs/plans/completed/fixture-plan.md" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_unchecked_plan_checkbox(self):
        # Fixture 2: the machine tasks are all complete but the active plan
        # still carries one unchecked line; the refusal names the checkbox
        # and its line number, and the manifest stays byte-identical.
        self.complete_all_tasks()
        self.write_active_plan("# fixture plan\n\n- [x] task-3\n- [ ] task-4\n")
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any(entry.startswith("line 4:") for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_incomplete_machine_tasks(self):
        # Fixture 2, machine half: one task still pending is refused first,
        # naming the incomplete task, before any plan-file or destination
        # evidence can run (machine completeness precedes them in the fixed
        # order).
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("task-4" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unsupported archive" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unchecked checkbox" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_open_claim_record(self):
        # Machine completeness, claims arm: every task complete but a claim
        # record not in the closed state refuses naming the open claim,
        # before any plan-file or destination evidence can run, with the
        # manifest byte-identical. Both row shapes refuse: a Mapping row
        # whose state is not closed and a row that is not a Mapping at all
        # (fail-closed on the malformed shape).
        self.complete_all_tasks()
        for claims in ({"task-4": {"state": "open"}}, {"task-4": "open"}):
            with self.subTest(claims=claims):
                state = runtime.load_manifest(self.state_path)
                state["claims"] = claims
                runtime._safe_write_json(self.state_path, state)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("claim records must be closed before archival" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any("task-4" in entry for entry in result["evidence"]), result["evidence"])
                self.assertFalse(any("unchecked checkbox" in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_refuses_pending_done_handoff(self):
        # Machine completeness, handoff arm: a task whose checkbox is true
        # but whose status is still a pending handoff value passes the
        # completeness helper (the checkbox counts) and reaches the handoff
        # arm, which refuses naming the pending done handoff, with the
        # manifest byte-identical. Both pending sub-values refuse:
        # done-pending and commit-pending.
        for status in ("done-pending", "commit-pending"):
            with self.subTest(status=status):
                state = runtime.load_manifest(self.state_path)
                state["tasks"]["task-4"]["status"] = status
                state["tasks"]["task-4"]["checkbox"] = True
                runtime._safe_write_json(self.state_path, state)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("pending done handoff must land before archival" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any("task-4" in entry for entry in result["evidence"]), result["evidence"])
                self.assertFalse(any("incomplete tasks" in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_refuses_foreign_plan_path(self):
        # Backlog origin Required behavior 1, source-binding guard: a
        # complete, checkbox-clean plan sitting under the resolved plans
        # directory but named for another run is refused on the plan identity
        # mismatch with the manifest plan_slug.
        self.complete_all_tasks()
        foreign = self.write_active_plan(self.PLAN_TEXT, rel="docs/plans/other-plan.md")
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, plan_path=foreign)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("identity mismatch" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("fixture-plan" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unsupported archive destination" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_mismatched_watcher_plan_path(self):
        # The resume watcher's recorded canonical plan path is part of the
        # plan identity: a watcher record naming a different path refuses
        # with the identity-mismatch evidence even though the filename
        # matches the manifest plan_slug, and the manifest stays
        # byte-identical.
        self.complete_all_tasks()
        state = runtime.load_manifest(self.state_path)
        state["resume_watcher"] = {"plan_path": "docs/plans/other-plan.md"}
        runtime._safe_write_json(self.state_path, state)
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("identity mismatch" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("resume watcher" in entry for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any("unsupported archive destination" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_accepts_conforming_watcher_plan_path(self):
        # Mirror arm: a watcher record whose canonical plan path equals the
        # supplied active plan path passes the identity clause, and the
        # recorded gate receipt names the same plan path while the run
        # stays active; both path forms pass, the relative form and the
        # absolute form (the driver canonicalizes the recorded path against
        # the repository root before comparing).
        self.complete_all_tasks()
        for watcher_plan in (
            self.ACTIVE_PLAN_REL,
            str((self.root / self.ACTIVE_PLAN_REL).resolve()),
        ):
            with self.subTest(watcher_plan=watcher_plan):
                state = runtime.load_manifest(self.state_path)
                state["resume_watcher"] = {"plan_path": watcher_plan}
                runtime._safe_write_json(self.state_path, state)
                result = self.pre_archive(self.driver())
                self.assertEqual(result["status"], "success")
                state = runtime.load_manifest(self.state_path)
                self.assertEqual(state["archive_gate"]["plan_path"], self.ACTIVE_PLAN_REL)
                self.assertEqual(state["workflow_state"], "active")

    def test_refuses_missing_or_unclean_review_sidecar(self):
        # Fixture 3: ten unclean-sidecar shapes, all refused with the
        # clean-round review sidecar evidence condition named and the manifest
        # byte-identical: a missing sidecar path, a present non-"yes" verdict
        # ("no" and "maybe"), a blocking findings row, a version-1 sidecar of
        # the plan-review sibling kind, the missing-key shape (no
        # schema_version; an absent verdict is not a refusal, it falls
        # through to the blocking-rows check and is covered by the
        # verdict-absent accept test), a payload without the required
        # findings key, a findings row whose blocking value is present but
        # not a boolean, and a findings row without a blocking key at all
        # (fail-closed on the malformed row; blocking is required per row,
        # unlike the verdict); the malformed shape pins its evidence in
        # three arms, a truthy string, a falsy 0 row, and a row with no
        # blocking key.
        self.complete_all_tasks()
        driver = self.driver()
        cases = (
            ("missing", None, None),
            ("verdict-no", self.clean_sidecar(verdict="no"), None),
            ("verdict-maybe", self.clean_sidecar(verdict="maybe"), None),
            ("blocking-finding", self.clean_sidecar(findings=[{"id": "R1", "blocking": True}]), None),
            ("plan-source-kind", self.clean_sidecar(source_kind="plan"), None),
            ("missing-schema-version", {"source_kind": "code", "verdict": "yes", "findings": []}, None),
            ("missing-findings", {"schema_version": 1, "source_kind": "code", "verdict": "yes"}, "missing the required findings array"),
            ("non-boolean-blocking", self.clean_sidecar(findings=[{"id": "R9", "blocking": "yes"}]), "non-boolean blocking value"),
            ("falsy-non-boolean-blocking", self.clean_sidecar(findings=[{"id": "R10", "blocking": 0}]), "first malformed finding: R10"),
            ("absent-blocking-key", self.clean_sidecar(findings=[{"id": "R11"}]), "first malformed finding: R11"),
        )
        for label, payload, evidence_fragment in cases:
            with self.subTest(case=label):
                if payload is None:
                    sidecar = "docs/reviews/absent-round.stats.json"
                else:
                    sidecar = self.write_sidecar(payload)
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("clean-round review sidecar" in entry for entry in result["evidence"]), result["evidence"])
                if evidence_fragment is not None:
                    self.assertTrue(any(evidence_fragment in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_pre_archive_refuses_environment_and_shape_arms(self):
        # Refusal-arm witnesses for the environment and input-shape arms the
        # fixed-order predicate owned unwitnessed: (a) facts without the
        # completed-directory key, (b) the resolved destination directory
        # removed from disk, (c) facts resolving the destination outside the
        # repository root, (d) a review sidecar path escaping the repository
        # root, (e) a sidecar file of raw non-JSON text, and (f) the input
        # shape guard over three malformed shapes. Every arm refuses blocked
        # done-pending naming its condition and leaves the manifest
        # byte-identical. The facts rewrites assemble the completed key from
        # parts so the mixin's write_facts keeps the file's only TOML
        # literal (test_mixin_membership pins that count).
        self.complete_all_tasks()
        driver = self.driver()
        escape_dir = self.root.parent / f"{self.root.name}-escape-completed"
        escape_dir.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, escape_dir, ignore_errors=True)
        raw_sidecar_rel = "docs/reviews/raw-prose-r3.stats.json"

        def write_plain_facts(body: str) -> None:
            facts = self.root / ".ai-playbook" / "facts.md"
            facts.write_text("```toml\n" + body + "```\n", encoding="utf-8")

        def reset_standard_environment() -> None:
            # Every case seeds from the standard setUp environment so the
            # cases stay order-independent despite their mutations.
            self.write_facts()
            self.make_completed_dir()

        def seed_missing_completed_key() -> None:
            reset_standard_environment()
            write_plain_facts('plans_dir = "docs/plans/"\n')

        def seed_removed_completed_dir() -> None:
            reset_standard_environment()
            shutil.rmtree(self.root / "docs/plans/completed")

        def seed_escaping_completed_dir() -> None:
            reset_standard_environment()
            completed_key = "plans_completed_dir"
            escape_value = f"../{self.root.name}-escape-completed"
            write_plain_facts('plans_dir = "docs/plans/"\n' + completed_key + ' = "' + escape_value + '"\n')

        def seed_raw_text_sidecar() -> None:
            reset_standard_environment()
            path = self.root / raw_sidecar_rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("review prose, not JSON", encoding="utf-8")

        cases = (
            ("missing-facts-key", seed_missing_completed_key, {}, ("the facts TOML-fence key plans_completed_dir is missing or unresolvable",)),
            ("completed-dir-removed", seed_removed_completed_dir, {}, ("the resolved destination directory does not exist",)),
            ("completed-dir-escapes-root", seed_escaping_completed_dir, {}, ("the resolved destination escapes the repository root",)),
            ("sidecar-escapes-root", reset_standard_environment, {"review_sidecar": "../escape-round.stats.json"}, ("clean-round review sidecar", "is not a safe repository-relative path under the repository root", "../escape-round.stats.json")),
            ("sidecar-unreadable-or-invalid-json", seed_raw_text_sidecar, {"review_sidecar": raw_sidecar_rel}, ("clean-round review sidecar is unreadable or invalid JSON",)),
        )
        for label, seed_environment, overrides, fragments in cases:
            with self.subTest(case=label):
                seed_environment()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, **overrides)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                for fragment in fragments:
                    self.assertTrue(any(fragment in entry for entry in result["evidence"]), (fragment, result["evidence"]))
                self.assert_refusal_preserves_manifest(before)

        # The input shape guard: a non-string plan path, a non-sha commit
        # identity, and an empty Phase 5 checklist all refuse with the same
        # required-inputs evidence before any filesystem work runs.
        reset_standard_environment()
        shape_cases = (
            ("non-string-plan-path", {"plan_path": 123}),
            ("non-sha-commit-identity", {"last_commit_sha": "nothex"}),
            ("empty-phase5-checklist", {"phase5_checklist": []}),
        )
        with self.subTest(case="required-inputs-shape-guard"):
            for shape, shape_overrides in shape_cases:
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, **shape_overrides)
                self.assertEqual(result["status"], "blocked", shape)
                self.assertEqual(result["reason_code"], "done-pending", shape)
                self.assertTrue(
                    any("active plan path, review sidecar, commit identity, and Phase 5 checklist are required" in entry for entry in result["evidence"]),
                    (shape, result["evidence"]),
                )
                self.assert_refusal_preserves_manifest(before, shape)

    def test_accepts_sidecar_without_verdict_key(self):
        # Fixture 3, verdict-absent accept arm: the review-staging schema
        # makes `verdict` optional, so a code sidecar carrying schema
        # version 1, source_kind "code", and zero blocking findings but no
        # verdict key is a clean round: the verdict clause refuses only a
        # present non-"yes" verdict, an absent verdict falls through to the
        # blocking-rows check, and the empty findings list passes it; the
        # gate records and the run stays active.
        self.complete_all_tasks()
        sidecar = self.write_sidecar({"schema_version": 1, "source_kind": "code", "findings": []})
        result = self.pre_archive(self.driver(), review_sidecar=sidecar)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertIn("archive_gate", state)
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)

    def _write_padded_sidecar(self, total_bytes: int) -> str:
        # A clean sidecar padded with JSON whitespace to exactly
        # total_bytes bytes, so the bounded-read size arms vary only the
        # byte count and never the payload shape.
        text = json.dumps(self.clean_sidecar())
        padded = text[:-1] + " " * (total_bytes - len(text)) + "}"
        path = self.root / self.SIDECAR_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(padded, encoding="utf-8")
        return self.SIDECAR_REL

    def test_sidecar_read_bounded_refuses_oversize(self):
        # Bounded sidecar read, oversize refuse arm: a valid-shape clean
        # sidecar padded to PLAN_READ_LIMIT + 1 bytes refuses as
        # clean-round evidence failure naming the bounded-read limit, with
        # the manifest byte-identical; the gate reads the sidecar through
        # the same LIMIT + 1 byte-capped policy as the plan read, so an
        # over-limit sidecar is never parsed.
        self.complete_all_tasks()
        sidecar = self._write_padded_sidecar(runtime.PLAN_READ_LIMIT + 1)
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, review_sidecar=sidecar)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("clean-round review sidecar exceeds the bounded read limit" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_sidecar_read_bounded_accepts_at_limit(self):
        # Bounded sidecar read, at-limit accept arm: the same clean sidecar
        # sized to exactly PLAN_READ_LIMIT bytes passes the cap
        # (len(data) == LIMIT is not over it), the gate records, and the
        # run stays active; this pins the boundary so the refusal stays
        # strictly over the limit.
        self.complete_all_tasks()
        sidecar = self._write_padded_sidecar(runtime.PLAN_READ_LIMIT)
        result = self.pre_archive(self.driver(), review_sidecar=sidecar)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertIn("archive_gate", state)
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)

    def test_refuses_stale_last_fix_commit(self):
        # Fixture 3, freshness half: a clean sidecar whose last_fix_commit is
        # not an ancestor-or-self of HEAD refuses with the review freshness
        # condition; the ancestry check runs through an injectable seam so a
        # fixture root without a git repository can stub it.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.clean_sidecar(last_fix_commit="1234567890abcdef"))
        driver = self.driver(commit_ancestry=lambda _commit: False)
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, review_sidecar=sidecar)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("last_fix_commit" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("ancestor-or-self of HEAD" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_success_writes_gate_receipt_and_stays_active(self):
        # Fixture 5, pre-move half: the passing predicate records archive_gate
        # with the facts-resolved declared destination, the plan sha256
        # digest, the commit identity, the checklist, and a timestamp, while
        # workflow_state stays active and no terminal receipt exists yet.
        self.complete_all_tasks()
        head = self._git("rev-parse", "HEAD")
        sidecar = self.write_sidecar(self.clean_sidecar(last_fix_commit=head))
        driver = self.driver()
        result = self.pre_archive(driver, last_commit_sha="abcdef1", review_sidecar=sidecar)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        gate = state["archive_gate"]
        self.assertEqual(gate["plan_path"], self.ACTIVE_PLAN_REL)
        self.assertEqual(gate["declared_destination"], "docs/plans/completed/fixture-plan.md")
        self.assertEqual(gate["plan_digest"], hashlib.sha256((self.root / self.ACTIVE_PLAN_REL).read_bytes()).hexdigest())
        self.assertEqual(gate["last_commit_sha"], "abcdef1")
        self.assertEqual(gate["phase5_checklist"], ["tests"])
        self.assertIn("recorded_at", gate)
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)


    def residual_sidecar(self, **overrides) -> dict:
        # The focused verification-round sidecar: verdict "no" precisely
        # because the out-of-set residuals are staged, one out-of-set
        # blocking row carrying the backlogged residual, and the round date
        # the ordering proof reads.
        payload = {
            "schema_version": 1,
            "source_kind": "code",
            "verdict": "no",
            "date": self.ROUND_DATE,
            "findings": [
                {"id": 1, "blocking": False},
                {"id": 2, "blocking": True},
            ],
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def residual_policy(recorded_at: float, finding_ids: list[int] | None = None) -> dict:
        return {
            "finding_ids": [3, 7] if finding_ids is None else finding_ids,
            "grant_source": "user standing instruction recorded in manifest.md",
            "recorded_at": recorded_at,
        }

    def test_accepts_residual_policy_exit(self):
        # Residual-acceptance exit, accept arm: the focused-round sidecar
        # with verdict "no" and one out-of-set blocking row, plus the policy
        # input whose recorded-at predates the round date, archives: the
        # OR-branch applies, the verdict sub-check does not, and the
        # membership rule permits the out-of-set blocking row as the
        # backlogged residual; the gate records and the run stays active
        # with no terminal receipt yet.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar())
        policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400)
        result = self.pre_archive(self.driver(), review_sidecar=sidecar, residual_policy=policy)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertIn("archive_gate", state)
        self.assertEqual(state["archive_gate"]["declared_destination"], "docs/plans/completed/fixture-plan.md")
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)

    def test_refuses_residual_sidecar_without_policy_input(self):
        # Input-gated refuse arm: the same focused-round sidecar without the
        # residual_policy input still refuses, so the exit cannot ride an
        # unrecorded policy; the landed verdict sub-check fires on the
        # present "no" verdict and the manifest stays byte-identical.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar())
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, review_sidecar=sidecar)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any('verdict must be "yes" when present' in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_blocking_finding_inside_residual_set(self):
        # Membership refuse arm: a blocking row whose integer id is a member
        # of the policy's finding_ids refuses even under the recorded policy,
        # because the named set must reach fixed or dropped before the exit;
        # the refusal names the in-set finding and leaves the manifest
        # byte-identical.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar(findings=[{"id": 3, "blocking": True}]))
        policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400, finding_ids=[3, 7])
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("inside the recorded residual policy set" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any("first in-set blocking finding: 3" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_refuses_policy_recorded_after_verification_round(self):
        # Ordering refuse arm: a policy whose recorded-at postdates the
        # sidecar's round date refuses, because the policy must be recorded
        # BEFORE the verification round runs; the day-precision proof is
        # strict, so a policy recorded exactly at the round-day boundary is
        # not predating either and refuses the same way.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar())
        for recorded_at in (self.ROUND_DAY_EPOCH + 86400, self.ROUND_DAY_EPOCH):
            with self.subTest(recorded_at=recorded_at):
                policy = self.residual_policy(recorded_at=recorded_at)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("does not predate" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any(self.ROUND_DATE in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_refuses_nonfinite_recorded_at_policy(self):
        # Shape-guard refuse arm: JSON parses NaN and the infinities
        # as numbers, but a non-finite recorded-at poisons the ordering
        # proof (NaN compares False against every round-day epoch, so a NaN
        # policy would "predate" every round); the shape guard refuses the
        # policy before any filesystem work and the manifest stays
        # byte-identical (nothing archives).
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar())
        for recorded_at in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(recorded_at=recorded_at):
                policy = self.residual_policy(recorded_at=recorded_at)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("residual_policy.recorded_at must be a finite epoch timestamp" in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_refuses_non_integer_blocking_id_under_policy(self):
        # Membership refuse arm: a blocking row whose id is not an
        # integer can never prove itself outside the policy's named integer
        # set, so under the branch it refuses instead of silently
        # reclassifying as a permitted out-of-set residual; the evidence
        # names the row and the integer-id requirement and the manifest
        # stays byte-identical.
        self.complete_all_tasks()
        for row_id in ("3", 3.0):
            with self.subTest(row_id=row_id):
                sidecar = self.write_sidecar(self.residual_sidecar(findings=[{"id": row_id, "blocking": True}]))
                policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400, finding_ids=[3, 7])
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("whose id is not an integer under the residual policy branch" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any(f"first non-integer blocking id: {row_id!r}" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any("requires an integer id matching the policy's integer finding ids" in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_refuses_junk_verdict_under_policy(self):
        # Verdict-slot refuse arm: under the branch the verdict slot
        # narrows to the yes/no pair instead of applying the landed
        # clean-round sub-check; "no" is legitimate because the out-of-set
        # residuals are staged, and any other present value (a junk verdict
        # such as "maybe", or an empty string) refuses with the branch's
        # evidence naming the accepted pair.
        self.complete_all_tasks()
        for verdict in ("maybe", ""):
            with self.subTest(verdict=verdict):
                sidecar = self.write_sidecar(self.residual_sidecar(verdict=verdict))
                policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any('verdict under the residual policy branch must be "yes" or "no" when present' in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any(f"supplied {verdict!r}" in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)

    def test_accepts_in_set_non_blocking_row_under_policy(self):
        # Fixed-member accept arm: a row whose integer id IS a
        # member of the policy set but carries blocking false (the finding
        # was fixed or dropped) archives, pinning the blocking conjunct of
        # the membership rule: membership refuses only blocking rows, so a
        # fixed member never wedges the sanctioned exit; the gate records
        # and the run stays active.
        self.complete_all_tasks()
        sidecar = self.write_sidecar(self.residual_sidecar(findings=[{"id": 3, "blocking": False}]))
        policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400, finding_ids=[3, 7])
        result = self.pre_archive(self.driver(), review_sidecar=sidecar, residual_policy=policy)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertIn("archive_gate", state)
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)

    def test_normalize_residual_policy_malformed_inputs_refuse(self):
        # Shape-guard refusal coverage: every fail-closed branch of
        # the policy normalizer keeps its documented evidence string, and
        # the one valid shape still normalizes (grant source trimmed).
        cases = (
            ("non-mapping", "policy", "residual_policy must be a JSON object when present"),
            ("empty-finding-ids", {"finding_ids": [], "grant_source": "user grant", "recorded_at": 1.0}, "residual_policy.finding_ids must be a non-empty list"),
            ("non-int-member", {"finding_ids": [3, "7"], "grant_source": "user grant", "recorded_at": 1.0}, "residual_policy.finding_ids must be integers matching the sidecar's integer finding ids"),
            ("bool-member", {"finding_ids": [3, True], "grant_source": "user grant", "recorded_at": 1.0}, "residual_policy.finding_ids must be integers matching the sidecar's integer finding ids"),
            ("empty-grant-source", {"finding_ids": [3], "grant_source": "   ", "recorded_at": 1.0}, "residual_policy.grant_source must be a non-empty string"),
            ("bool-grant-source", {"finding_ids": [3], "grant_source": True, "recorded_at": 1.0}, "residual_policy.grant_source must be a non-empty string"),
            ("missing-recorded-at", {"finding_ids": [3], "grant_source": "user grant"}, "residual_policy.recorded_at must be an epoch timestamp"),
            ("bool-recorded-at", {"finding_ids": [3], "grant_source": "user grant", "recorded_at": True}, "residual_policy.recorded_at must be an epoch timestamp"),
            ("nan-recorded-at", {"finding_ids": [3], "grant_source": "user grant", "recorded_at": float("nan")}, "residual_policy.recorded_at must be a finite epoch timestamp"),
        )
        for label, policy, expected_fragment in cases:
            with self.subTest(case=label):
                normalized, error = runtime._normalize_residual_policy(policy)
                self.assertIsNone(normalized)
                self.assertIsNotNone(error)
                self.assertIn(expected_fragment, error)
        normalized, error = runtime._normalize_residual_policy({"finding_ids": [3, 7], "grant_source": "  user grant  ", "recorded_at": 5.0})
        self.assertIsNone(error)
        self.assertEqual(normalized["finding_ids"], [3, 7])
        self.assertEqual(normalized["grant_source"], "user grant")
        self.assertEqual(normalized["recorded_at"], 5.0)

    def test_refuses_residual_sidecar_missing_or_malformed_round_date(self):
        # Round-date guard refuse arms: under the branch the
        # ordering proof reads the sidecar date, so a sidecar without a
        # usable date value refuses with the missing-date evidence and a
        # non-ISO date refuses with the format evidence; the manifest stays
        # byte-identical in both.
        self.complete_all_tasks()
        missing = self.residual_sidecar()
        missing.pop("date")
        malformed = self.residual_sidecar(date="18-09-2026")
        policy = self.residual_policy(recorded_at=self.ROUND_DAY_EPOCH - 86400)
        for label, payload, evidence_fragment in (
            ("missing-date", missing, "missing the round date the residual policy ordering proof requires"),
            ("malformed-date", malformed, "round date is not an ISO YYYY-MM-DD date: 18-09-2026"),
        ):
            with self.subTest(case=label):
                sidecar = self.write_sidecar(payload)
                driver = self.driver()
                before = self.state_path.read_bytes()
                result = self.pre_archive(driver, review_sidecar=sidecar, residual_policy=policy)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any(evidence_fragment in entry for entry in result["evidence"]), result["evidence"])
                self.assert_refusal_preserves_manifest(before)


class TerminalFinalStageTest(ArchiveGateFixtureBase):
    """Terminal final-stage archive safety (archive origin fixture 4 and the post-move half of fixture 5).

    The final terminal stage is the second half of the staged protocol: it
    refuses as blocked ``done-pending`` unless the ``archive_gate`` receipt
    exists, the supplied archived path equals the gate's
    ``declared_destination`` exactly, the gate-recorded source plan path is
    absent from the filesystem, and the archived bytes still hash to the
    gate's ``plan_digest``; only then do today's archived-plan checks run
    and the terminal receipt gain the gate digest. Every refusal preserves
    the machine state.
    """

    ARCHIVED_REL = "docs/plans/completed/fixture-plan.md"
    SOURCE_REL = "docs/plans/fixture-plan.md"
    OWNER = "terminal-final-owner"

    def setUp(self) -> None:
        super().setUp()
        self.seed_manifest()
        self.write_archived_plan(self.PLAN_TEXT)

    def write_archived_plan(self, text: str, rel: str | None = None) -> str:
        rel = rel or self.ARCHIVED_REL
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return rel

    def seed_gate(self, **overrides) -> dict:
        """Seed a conforming ``archive_gate`` receipt; overrides replace fields.

        Conforming means: the declared destination equals the archived
        fixture path, the digest covers the archived bytes, and the recorded
        source plan path is the absent active path.
        """

        state = runtime.load_manifest(self.state_path)
        gate = {
            "plan_path": self.SOURCE_REL,
            "declared_destination": self.ARCHIVED_REL,
            "plan_digest": hashlib.sha256((self.root / self.ARCHIVED_REL).read_bytes()).hexdigest(),
            "last_commit_sha": "abcdef1",
            "phase5_checklist": ["tests"],
            "recorded_at": 1234.0,
        }
        gate.update(overrides)
        state["archive_gate"] = gate
        runtime._safe_write_json(self.state_path, state)
        return gate

    def mark_terminal(self, driver, **overrides) -> dict:
        payload = {"archived_plan_path": self.ARCHIVED_REL, "last_commit_sha": "abcdef1", "phase5_checklist": ["tests"]}
        payload.update(overrides)
        return driver.mark_terminal(payload["archived_plan_path"], payload["last_commit_sha"], payload["phase5_checklist"])

    def test_refuses_without_gate_receipt(self):
        # Fixture 4: the plan already sits at the destination but no
        # archive_gate receipt exists (the move happened without the
        # pre-archive stage); the final stage refuses naming the missing
        # pre-archive gate and the run stays active for recovery.
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("pre-archive gate" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_refuses_archived_path_mismatch(self):
        # The supplied archived path must equal the gate's declared
        # destination exactly: a plan parked at any other path is refused
        # naming the destination mismatch, never terminal.
        self.seed_gate(declared_destination="docs/plans/completed/other-plan.md")
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(
            any("does not equal" in entry and "declared_destination" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_refuses_source_still_present(self):
        # Fixture 5, post-move half: the gate-recorded source plan path is
        # still on the filesystem after the supposed move, so the archive
        # move never happened; the final stage refuses naming the
        # source-present condition with the recorded path.
        self.write_archived_plan(self.PLAN_TEXT, rel=self.SOURCE_REL)
        self.seed_gate()
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("still present" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any(self.SOURCE_REL in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_refuses_archived_content_drift(self):
        # The archived bytes must still hash to the gate's plan digest: a
        # drifted archive is refused done-pending naming the digest mismatch
        # and the manifest bytes stay exactly as they were.
        self.seed_gate(plan_digest=hashlib.sha256(b"drifted plan bytes").hexdigest())
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("digest mismatch" in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)

    def test_terminal_refuses_star_and_plus_markers(self):
        # GFM task-list widening witness for the terminal predicate: an
        # archived plan whose unchecked line uses the '*' marker and then
        # one using the '+' marker are refused exactly like the dash form,
        # each with the line-anchored 'line <N>:' evidence for the marker
        # line. RED before the widening: the dash-only predicate ignored
        # both marker lines, so the gate wrote the terminal receipt.
        for marker in ("*", "+"):
            with self.subTest(marker=marker):
                self.write_archived_plan(f"# fixture plan\n### Task 4: fourth\n- [x] task-3\n{marker} [ ] task-4\n")
                self.seed_gate()
                driver = self.driver()
                result = self.mark_terminal(driver)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "done-pending")
                self.assertTrue(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
                self.assertTrue(any(entry.startswith("line 4:") for entry in result["evidence"]), result["evidence"])
                state = runtime.load_manifest(self.state_path)
                self.assertNotIn("terminal_receipt", state)
                self.assertEqual(state["workflow_state"], "active")

    def test_widened_marker_evidence_line_numbers_stable(self):
        # Evidence-pin stability under the widened predicate: the first
        # unchecked marker of this fixture is the '* [ ]' line at line 5
        # (the dash-only predicate ignored it, so pre-widening the first
        # pinned line was the dash line at line 6); the pin carries the
        # unchanged 'line <N>:' prefix form, numbered by the scan helper's
        # walk, and the later dash line never displaces the first pin.
        self.write_archived_plan(
            "# fixture plan\n\n### Task 4: fourth\n- [x] task-3\n* [ ] first unchecked star line\n- [ ] later dash line\n"
        )
        self.seed_gate()
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any(entry.startswith("line 5:") for entry in result["evidence"]), result["evidence"])
        self.assertFalse(any(entry.startswith("line 6:") for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_terminal_backstop_stays_fence_blind(self):
        # Regression pin for the terminal backstop's fence-blind spec: an
        # unchecked checkbox inside a fenced block in the archived plan still
        # refuses terminal with the line-anchored evidence (the readiness
        # fence map is scoped to the section extractor and the heading
        # search; the terminal whole-file scan never consumes it). Green
        # before and after the fence map by spec.
        self.write_archived_plan(
            "# fixture plan\n\n### Task 3: third\n### Task 4: fourth\n\n```text\n- [ ] fenced unchecked box\n```\n\n- [x] task-3\n- [x] task-4\n"
        )
        self.seed_gate()
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unchecked checkbox line" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any(entry.startswith("line 7:") for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_refuses_unknown_terminal_stage(self):
        # The staged terminal dispatcher owns exactly two stages: a stage
        # that is neither ``pre-archive`` nor ``final`` refuses blocked
        # done-pending naming the unsupported stage, with the manifest
        # byte-identical, no terminal receipt, and the run left active.
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = driver.mark_terminal(stage="mid-archive")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unsupported terminal stage: mid-archive" in entry for entry in result["evidence"]), result["evidence"])
        self.assertEqual(self.state_path.read_bytes(), before)
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")

    def test_success_records_exact_destination_and_digest(self):
        # Fixture 5: the full happy path completes the run; the receipt's
        # archived_plan_path equals the gate's declared_destination and the
        # receipt carries the gate digest, but only after the final stage
        # re-verified the archived bytes hash to it.
        gate = self.seed_gate()
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "success")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["workflow_state"], "complete")
        receipt = state["terminal_receipt"]
        self.assertEqual(receipt["archived_plan_path"], gate["declared_destination"])
        self.assertEqual(receipt["plan_digest"], gate["plan_digest"])
        reread = self.driver().terminal_result()
        self.assertEqual(reread["status"], "success")
        self.assertEqual(reread["plan_digest"], gate["plan_digest"])

    def test_incomplete_gateless_manifest_refuses_on_completeness_before_gate(self):
        # Ordering pin for the migrated fixtures: an incomplete AND gateless
        # manifest is refused with the machine-completeness evidence before
        # any gate clause, so the prescribed order cannot be silently
        # inverted (gate checks hoisted above completeness) to keep the old
        # refusal assertions green.
        state = runtime.load_manifest(self.state_path)
        state["tasks"]["task-4"].update({"status": "pending", "checkbox": False})
        runtime._safe_write_json(self.state_path, state)
        self.assertNotIn("archive_gate", runtime.load_manifest(self.state_path))
        driver = self.driver()
        result = self.mark_terminal(driver)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(
            any("all tasks must be complete before terminal state" in entry for entry in result["evidence"]),
            result["evidence"],
        )
        self.assertFalse(any("gate" in entry for entry in result["evidence"]), result["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertNotIn("terminal_receipt", state)
        self.assertEqual(state["workflow_state"], "active")


class ArchiveLocationTest(ArchiveGateFixtureBase):
    """Pre-archive relocation detection (archive origin fixture 7).

    A plan relocated under a completed-folder-like sibling that is neither
    the resolved plans directory nor the resolved completed directory is
    refused by the pre-archive stage naming ``unsupported archive location``
    with the offending path, leaving the machine manifest untouched and the
    relocated file in place for recovery.
    """

    SIBLING_PLAN_REL = "docs/plans_completed/fixture-plan.md"
    OWNER = "archive-location-owner"

    def setUp(self) -> None:
        super().setUp()
        self.write_facts()
        self.make_completed_dir()
        self.seed_manifest()
        # The relocated plan sits under neither resolved directory.
        self.write_active_plan(self.PLAN_TEXT, rel=self.SIBLING_PLAN_REL)

    def test_reports_unsupported_sibling_location(self):
        # Fixture 7: the sibling directory sits outside the resolved plans
        # directory, so the containment clause refuses before any identity,
        # destination, or sidecar evidence; the offending path is named and
        # nothing moves.
        sidecar = self.write_sidecar(self.clean_sidecar())
        driver = self.driver()
        before = self.state_path.read_bytes()
        result = driver.mark_terminal(
            stage="pre-archive",
            plan_path=self.SIBLING_PLAN_REL,
            destination="",
            review_sidecar=sidecar,
            last_commit_sha="abcdef1",
            phase5_checklist=["tests"],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason_code"], "done-pending")
        self.assertTrue(any("unsupported archive location" in entry for entry in result["evidence"]), result["evidence"])
        self.assertTrue(any(self.SIBLING_PLAN_REL in entry for entry in result["evidence"]), result["evidence"])
        self.assert_refusal_preserves_manifest(before)
        self.assertTrue((self.root / self.SIBLING_PLAN_REL).is_file())


class TerminalResumeTest(ArchiveGateFixtureBase):
    """Interrupted archive run resumes without double archive (fixture 6).

    A run that recorded its ``archive_gate`` receipt and was interrupted
    before the move stays active with its claims intact; the resumed
    process re-runs the pre-archive stage and the receipt is overwritten in
    place with the identity fields stable while ``recorded_at`` advances.
    """

    OWNER = "terminal-resume-owner"

    def setUp(self) -> None:
        super().setUp()
        self.write_facts()
        self.make_completed_dir()
        self.seed_manifest()
        self.write_active_plan()
        # One closed claim record: the interruption happened after the work
        # landed, and the resume must leave the record exactly intact.
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-3"] = {
            "token": "resume-token",
            "generation": 0,
            "owner": "resume-owner",
            "state": "closed",
            "task_id": "task-3",
        }
        runtime._safe_write_json(self.state_path, state)
        self.clock_values = [1000.0]

    def advance_clock(self) -> None:
        self.clock_values.append(self.clock_values[-1] + 1.0)

    def test_interrupted_run_resumes_without_double_archive(self):
        # Fixture 6: gate recorded, no move performed. The resumed process
        # (a fresh driver over the same manifest) finds workflow_state still
        # active with the closed claim record intact, and its repeated
        # pre-archive call overwrites the gate in place: identity fields
        # stable, recorded_at advanced, no terminal receipt, and the active
        # plan still in place, so no second archive transition exists.
        first = self.driver(clock=lambda: self.clock_values[-1])
        outcome = self.pre_archive(first)
        self.assertEqual(outcome["status"], "success")
        state = runtime.load_manifest(self.state_path)
        gate_before = state["archive_gate"]
        self.assertEqual(state["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state)
        self.advance_clock()
        resumed = self.driver(clock=lambda: self.clock_values[-1])
        repeat = self.pre_archive(resumed)
        self.assertEqual(repeat["status"], "success")
        state_after = runtime.load_manifest(self.state_path)
        gate_after = state_after["archive_gate"]
        self.assertEqual(gate_after["plan_path"], gate_before["plan_path"])
        self.assertEqual(gate_after["declared_destination"], gate_before["declared_destination"])
        self.assertEqual(gate_after["plan_digest"], gate_before["plan_digest"])
        self.assertEqual(gate_after["last_commit_sha"], gate_before["last_commit_sha"])
        self.assertEqual(gate_after["phase5_checklist"], gate_before["phase5_checklist"])
        self.assertGreater(gate_after["recorded_at"], gate_before["recorded_at"])
        self.assertEqual(state_after["workflow_state"], "active")
        self.assertNotIn("terminal_receipt", state_after)
        self.assertEqual(state_after["claims"]["task-3"]["state"], "closed")
        self.assertTrue((self.root / self.ACTIVE_PLAN_REL).is_file())


class TestArchiveGateFixtureBase(unittest.TestCase):
    """Structural witness for the ArchiveGateFixtureBase extraction (fixture scaffolding dedup origin).

    The dedup contract: the mixin owns the shared archive/terminal fixture
    scaffolding exactly once, the four rebased classes keep no local copy of
    a mixin-owned member, and the hermetic git setup stays gated behind
    ``requires_git`` on the single class whose success arm proves real
    ancestor-or-self ancestry.
    """

    def test_mixin_membership(self):
        # Given the four rebased classes, each defines no local copy of a
        # mixin-owned member (helpers and shared constants alike), every
        # listed member really exists on the mixin, the requires_git gate
        # defaults off and is opted in by the pre-archive class alone, and
        # the facts TOML literal occurs exactly once in the file (owned by
        # the mixin's write_facts; no inline copy survives anywhere else).
        mixin_owned = (
            "PLAN_TEXT",
            "ACTIVE_PLAN_REL",
            "SIDECAR_REL",
            "write_facts",
            "make_completed_dir",
            "seed_manifest",
            "write_active_plan",
            "write_sidecar",
            "clean_sidecar",
            "pre_archive",
            "driver",
        )
        for name in mixin_owned:
            self.assertTrue(hasattr(ArchiveGateFixtureBase, name), f"mixin lost member {name}")
        rebased = (ArchiveGatePreArchiveTest, TerminalFinalStageTest, ArchiveLocationTest, TerminalResumeTest)
        for cls in rebased:
            self.assertTrue(issubclass(cls, ArchiveGateFixtureBase), f"{cls.__name__} is not rebased on the mixin")
            for name in mixin_owned:
                self.assertNotIn(name, vars(cls), f"{cls.__name__} keeps a local copy of mixin-owned {name}")
        # Hermeticity: git init is opt-in, and only the class that proves a
        # real ancestor-or-self commit initializes the fixture repository.
        self.assertIs(ArchiveGateFixtureBase.requires_git, False)
        self.assertIs(ArchiveGatePreArchiveTest.requires_git, True)
        for cls in (TerminalFinalStageTest, ArchiveLocationTest, TerminalResumeTest):
            self.assertIs(cls.requires_git, False, f"{cls.__name__} must not grant itself git init")
        source = Path(__file__).read_text(encoding="utf-8")
        # Needle assembled from parts so this assertion's own source text
        # cannot match it; the mixin's write_facts owns the only occurrence.
        toml_row = "plans_completed_dir " + "= "
        self.assertEqual(source.count(toml_row), 1, "facts TOML literal must occur exactly once in the file")


    def test_terminal_resume_driver_sites_inject_clock(self):
        import inspect
        src = inspect.getsource(TerminalResumeTest)
        self.assertNotIn(
            "self.driver()",
            src,
            "driver constructions in TerminalResumeTest must inject the fixture clock; "
            "ambient time makes the recorded_at assertion order-dependent",
        )

class ClaimsContainerShapeTest(unittest.TestCase):
    """Claims-container shape refusal at the load boundary (claims-container shape refusal origin).

    ``load_manifest`` validated only ``schema_version`` and ``tasks``, so a
    malformed claims container (null, a list, a string) sailed through to
    the first consumer that iterates it (the open-claims completeness
    comprehension of ``_pre_archive_gate``'s arm (1), the first
    ``.items()`` iteration over the claims container, which runs before
    any residual handling and fires without ``residual_policy``) and
    crashed there with ``AttributeError`` the CLI top-level handler does
    not catch: the operator saw a traceback instead of a failure line.
    These canaries pin the load-time refusal for every
    non-mapping shape and the CLI surface that must name the claims shape
    before any driver work runs, leaving the manifest byte-identical.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_manifest_with_claims(self, claims):
        # create_manifest cannot produce a malformed container, so the
        # fixture seeds a producer-valid manifest and swaps the claims key
        # by hand; every other container stays producer-valid so the canary
        # pins the claims shape alone. Tasks are completed so the CLI
        # pre-archive gate passes the completeness check and reaches the
        # claims container iteration (the origin-recorded crash site).
        manifest = runtime.create_manifest(self.state_path, "claims-shape", [{"id": "task-1", "number": 1, "status": "complete", "checkbox": True}])
        manifest["claims"] = claims
        self.state_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_load_manifest_refuses_non_mapping_claims(self):
        for claims_shape in (None, ["task-1"], "task-1"):
            with self.subTest(claims_shape=claims_shape):
                self._seed_manifest_with_claims(claims_shape)
                with self.assertRaises(ValueError) as ctx:
                    runtime.load_manifest(self.state_path)
                self.assertIn("claims must be a mapping", str(ctx.exception))

    def test_cli_refuses_claims_container_before_driver_work(self):
        self._seed_manifest_with_claims(None)
        before = self.state_path.read_bytes()
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/execute_plan_runtime.py"),
                "--manifest", str(self.state_path),
                "--repo-root", str(self.root),
                "--owner", "claims-shape-owner",
                "--operation", "terminal",
                "--input", json.dumps(
                    {
                        "stage": "pre-archive",
                        "plan_path": "docs/plans/claims-shape.md",
                        "destination": "",
                        "review_sidecar": "",
                        "last_commit_sha": "abcdef1",
                        "phase5_checklist": ["tests"],
                    }
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("claims must be a mapping", completed.stderr)
        self.assertEqual(completed.stdout.strip(), "")
        self.assertEqual(self.state_path.read_bytes(), before)


class CheckpointRecoveryTest(unittest.TestCase):
    """Recovery pins for the checkpoint caller envelope (blocked-claim wedge origin).

    A first checkpoint whose worker-result envelope is malformed (missing
    ``reason_code``) is refused as a read-only blocked ``malformed-result``
    outcome: the interception returns before the claim fence, before any
    latch, history append, or checkpoint record write, so the manifest is
    untouched and the latched-wedge precondition this class once
    characterized no longer exists. These pins document the recovery
    boundary the runtime contract's "Checkpoint caller envelope" section
    states: recovery is the corrected re-submission itself, under the same
    live claim token and generation, with no lease expiry, claim
    replacement, or manifest recreation, while a post-launch claim without
    a launch record refuses the corrected receipt as the drift guard's
    resumable stale-claim outcome by design (anti-tamper; never bypassed or
    weakened here).
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        runtime.create_manifest(
            self.state_path,
            "checkpoint-recovery",
            [{"id": "task-1", "number": 1, "status": "pending"}],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _driver(self):
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="checkpoint-recovery",
            owner="recovery-owner",
            repo_root=self.root,
            commit_lookup=lambda _commit: True,
        )

    def _seed_claim(self, *, launch_record=True, blocked=False):
        # Seed 0: the claim generation equals the manifest generation (the
        # create_manifest seed default), which is what lets the corrected
        # receipt pass the _record_checkpoint_locked fence under the same
        # generation; the malformed refusal never reaches the fence at all
        # (the interception precedes it), so the seed shape pins the
        # post-refusal recovery path, not the fence.
        state = runtime.load_manifest(self.state_path)
        claim = {
            "token": "seed-token",
            "generation": 0,
            "owner": "recovery-owner",
            "state": "blocked" if blocked else "launched",
            "task_id": "task-1",
            "launched_at": 111.0,
        }
        if launch_record:
            claim["launch_record"] = {"baseline_revision": "", "generation": 0, "launched_at": 111.0}
        state["claims"]["task-1"] = claim
        if blocked:
            state["tasks"]["task-1"].update({"status": "blocked", "resume_allowed": False})
        runtime._safe_write_json(self.state_path, state)

    def _envelope(self):
        # The caller-facing checkpoint envelope the runtime contract
        # documents; generation is the claim generation (0 at this seed).
        return {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["worker-log: task complete"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1:worker-1",
            "generation": 0,
            "claim_token": "seed-token",
        }

    def test_corrected_checkpoint_after_malformed_receipt_recovers(self):
        driver = self._driver()
        self._seed_claim()
        seeded = runtime.load_manifest(self.state_path)
        malformed = self._envelope()
        del malformed["reason_code"]
        before = self.state_path.read_bytes()
        receipt = driver.record_worker_checkpoint(malformed)
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["reason_code"], "malformed-result")
        self.assertFalse(receipt["resume_allowed"])
        # Read-only refusal: the manifest is byte-identical to the seeded
        # document (no latch, no history append, no checkpoint record).
        self.assertEqual(self.state_path.read_bytes(), before)
        refused = runtime.load_manifest(self.state_path)
        self.assertEqual(refused["claims"]["task-1"]["state"], "launched")
        self.assertEqual(refused["tasks"]["task-1"]["status"], "pending")
        self.assertNotIn("blocked_receipt", refused["tasks"]["task-1"])
        self.assertNotIn("worker-blocked", [event.get("event") for event in refused["history"]])
        self.assertNotIn("task-1:worker-1", refused["checkpoints"])
        corrected = self._envelope()
        recovered = driver.record_worker_checkpoint(corrected)
        self.assertEqual(recovered["status"], "success")
        self.assertEqual(recovered["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-1"]["status"], "done-pending")
        self.assertIn("task-1:worker-1", state["checkpoints"])
        # In-place recovery under the same live claim: the token and
        # generation survive (no reclaim, no replaced claim), the lease
        # timestamp is never rotated, and the seeded manifest document is
        # still the one serving the run (no recreation, no generation bump).
        self.assertEqual(state["claims"]["task-1"]["token"], "seed-token")
        self.assertEqual(state["claims"]["task-1"]["generation"], seeded["claims"]["task-1"]["generation"])
        self.assertEqual(state["claims"]["task-1"]["state"], "launched")
        self.assertEqual(state["claims"]["task-1"]["launched_at"], seeded["claims"]["task-1"]["launched_at"])
        self.assertEqual(state["generation"], seeded["generation"])
        self.assertEqual(state["plan_slug"], seeded["plan_slug"])

    def test_drift_guard_refuses_post_launch_claim_without_launch_record(self):
        driver = self._driver()
        self._seed_claim(launch_record=False, blocked=True)
        receipt = driver.record_worker_checkpoint(self._envelope())
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["reason_code"], "stale-claim")
        self.assertTrue(receipt["resume_allowed"])
        self.assertIn("claim is in a post-launch state but has no launch record", receipt["evidence"])
        state = runtime.load_manifest(self.state_path)
        # The refusal preserves the manifest: the task stays latched, the
        # corrected checkpoint is not persisted, and no launch record is
        # backfilled behind the guard.
        self.assertEqual(state["tasks"]["task-1"]["status"], "blocked")
        self.assertNotIn("task-1:worker-1", state["checkpoints"])
        self.assertNotIn("launch_record", state["claims"]["task-1"])


class CheckpointMalformedNoMutationTest(unittest.TestCase):
    """No-mutation pins for the malformed checkpoint interception.

    The interception precedes the claim fence: a malformed envelope is
    refused read-only with the blocked ``malformed-result`` outcome even
    when the claim's generation differs from the manifest generation (where
    the fence alone would answer ``owner-mismatch``), and a well-formed
    failure receipt keeps the existing latch so the interception never
    swallows a real worker failure.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        runtime.create_manifest(
            self.state_path,
            "checkpoint-recovery",
            [{"id": "task-1", "number": 1, "status": "pending"}],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _driver(self):
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="checkpoint-recovery",
            owner="recovery-owner",
            repo_root=self.root,
            commit_lookup=lambda _commit: True,
        )

    def _seed_claim(self, *, claim_generation=0):
        state = runtime.load_manifest(self.state_path)
        state["claims"]["task-1"] = {
            "token": "seed-token",
            "generation": claim_generation,
            "owner": "recovery-owner",
            "state": "launched",
            "task_id": "task-1",
            "launched_at": 111.0,
            "launch_record": {"baseline_revision": "", "generation": claim_generation, "launched_at": 111.0},
        }
        runtime._safe_write_json(self.state_path, state)

    def _envelope(self, *, status="success", reason_code="completed"):
        return {
            "status": status,
            "reason_code": reason_code,
            "evidence": [f"worker-log: {reason_code}"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1:worker-1",
            "generation": 0,
            "claim_token": "seed-token",
        }

    def test_malformed_checkpoint_with_stale_fence_refuses_read_only(self):
        driver = self._driver()
        # The claim generation differs from the manifest generation (0), so
        # the fence alone would refuse this receipt as owner-mismatch; the
        # malformed interception must precede the fence and answer
        # malformed-result instead.
        self._seed_claim(claim_generation=1)
        malformed = self._envelope()
        del malformed["reason_code"]
        before = self.state_path.read_bytes()
        receipt = driver.record_worker_checkpoint(malformed)
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(receipt["reason_code"], "malformed-result")
        self.assertNotEqual(receipt["reason_code"], "owner-mismatch")
        self.assertFalse(receipt["resume_allowed"])
        # Read-only refusal: the manifest is byte-identical to the seeded
        # document (no latch, no history append, no checkpoint record).
        self.assertEqual(self.state_path.read_bytes(), before)
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["claims"]["task-1"]["state"], "launched")
        self.assertEqual(state["claims"]["task-1"]["generation"], 1)
        self.assertEqual(state["tasks"]["task-1"]["status"], "pending")
        self.assertNotIn("blocked_receipt", state["tasks"]["task-1"])
        self.assertNotIn("worker-blocked", [event.get("event") for event in state["history"]])
        self.assertNotIn("task-1:worker-1", state["checkpoints"])

    def test_well_formed_failure_receipt_still_latches(self):
        driver = self._driver()
        self._seed_claim()
        receipt = driver.record_worker_checkpoint(self._envelope(status="error", reason_code="runtime-error"))
        self.assertEqual(receipt["status"], "error")
        self.assertEqual(receipt["reason_code"], "runtime-error")
        state = runtime.load_manifest(self.state_path)
        # The existing latch is unchanged: runtime-error is a resumable
        # reason, so the claim and task latch blocked with
        # resume_allowed: true and the standard blocked-receipt machinery
        # (blocked_receipt, worker-blocked history event) applies.
        self.assertEqual(state["claims"]["task-1"]["state"], "blocked")
        self.assertEqual(state["tasks"]["task-1"]["status"], "blocked")
        self.assertTrue(state["tasks"]["task-1"]["resume_allowed"])
        self.assertEqual(state["tasks"]["task-1"]["blocked_receipt"]["reason_code"], "runtime-error")
        self.assertIn("worker-blocked", [event.get("event") for event in state["history"]])


class DoneBoundaryNoCommitTest(unittest.TestCase):
    """Done-boundary pins for the none no-commit justification (done-boundary commits origin).

    The done receipt accepts ``commit_identity`` set to the exact literal
    ``none`` (after stripping) for a task whose plan section carries no
    ``Commit:`` line (a read-only verification gate with nothing to commit).
    The driver never consults the commit lookup for ``none``; it proves the
    state itself: a dirty entry inside the claim's allowed paths refuses as
    ``commit-pending``, a tracked Markdown entry outside them is tolerated
    only when its working-tree diff is checkbox-marker-only with paired-line
    identity (the Step 1.3 plan-file flip is the sanctioned case; a content
    rewrite never satisfies the shape), every other dirty entry refuses with
    the clean-state evidence, and when the claim carries a baseline revision
    HEAD must equal it, so a committing worker cannot report ``none`` past
    its baseline. The group advance hands the next member the current HEAD
    revision as its baseline exactly as if a real commit had landed, the
    riding flip stays tolerated at the checkpoint scope witness, the
    real-identity done tail, and the startup reconciliation dirty gate, and
    the reconciliation completion recovery accepts a recorded ``none``
    without any git lookup.
    """

    NONE_EVIDENCE_LINE = "no-commit justification, checkbox, clean-state, and log evidence recorded"
    REAL_EVIDENCE_LINE = "done commit, checkbox, clean-state, and log evidence recorded"

    def setUp(self) -> None:
        # Pin ambient execute-plan env inputs so an exported variable cannot
        # silently redirect the code under test to a foreign registry.
        self._saved_env = {key: os.environ.pop(key) for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST") if key in os.environ}
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        # Hermetic git: neutralize host global/system config so hooks,
        # gpgsign, or aliases from the developer machine cannot leak into
        # the fixture repository; identity is set repo-locally below.
        self._git_env = dict(os.environ)
        self._git_env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        self._git_env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=self.root, check=True, env=self._git_env)
        (self.root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore"], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True, env=self._git_env)
        # The committed minimal plan Markdown: the sanctioned Step 1.3 flip
        # rides on this tracked file, which sits outside every task's
        # allowed paths so the tolerated-entry classification stays
        # content-based (no plan-path pin anywhere in the driver).
        self.plan_file = "fixture-plan.md"
        (self.root / self.plan_file).write_text(
            "# Fixture Plan\n"
            "\n"
            "### Task 3: verification gate\n"
            "\n"
            "- [ ] step one\n"
            "- [ ] step two\n"
            "\n"
            "### Task 4: content task\n"
            "\n"
            "- [ ] step three\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", self.plan_file], cwd=self.root, check=True, env=self._git_env)
        subprocess.run(["git", "commit", "-qm", "fixture plan"], cwd=self.root, check=True, env=self._git_env)
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            [
                {"id": "task-3", "number": 3, "status": "pending", "checkbox": False, "allowed_paths": ["task-3.txt"]},
                {"id": "task-4", "number": 4, "status": "pending", "checkbox": False, "allowed_paths": ["task-4.txt"]},
            ],
            repo_root=self.root,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.update(self._saved_env)
        for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST"):
            if key not in self._saved_env:
                os.environ.pop(key, None)

    def _git(self, *args, cwd=None):
        # Hermetic git subprocess for fixture sites: the pinned _git_env
        # neutralizes host global/system config, and the asserted exit keeps
        # fixture setup failures loud. Returns the CompletedProcess.
        return subprocess.run(["git", *args], cwd=cwd or self.root, env=self._git_env, capture_output=True, text=True, check=True)

    def _git_stdout(self, *args, cwd=None):
        completed = self._git(*args, cwd=cwd)
        return completed.stdout.strip()

    def recording_lookup(self):
        """A commit_lookup stub that answers False and records every call."""

        def lookup(commit):
            lookup.calls.append(commit)
            return False

        lookup.calls = []
        return lookup

    def driver(self, commit_lookup=None, **kwargs):
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="fixture-plan",
            owner="done-owner",
            repo_root=self.root,
            commit_lookup=commit_lookup if commit_lookup is not None else self.recording_lookup(),
            **kwargs,
        )

    def seed_done_pending(self, task="task-3", *, status="done-pending", allowed=None):
        # Seed a fenced launched claim whose baseline_revision is the fixture
        # HEAD captured at seed time, with a policy-token scope and the
        # matching launch-record snapshot; the task sits at its done
        # boundary (or in flight for the follow-on consumers).
        head = self._git_stdout("rev-parse", "HEAD")
        state = runtime.load_manifest(self.state_path)
        state["checkpoints"] = {}
        allowed_paths = list(allowed or [f"{task}.txt"])
        state["claims"][task] = {
            "token": f"seed-{task}",
            "generation": 0,
            "owner": "done-owner",
            "state": "launched",
            "task_id": task,
            "allowed_paths": allowed_paths,
            "launched_at": 111.0,
            "baseline_revision": head,
            "policy_token": {"allowed_paths": allowed_paths},
            "launch_record": {"baseline_revision": head, "generation": 0, "launched_at": 111.0},
        }
        state["tasks"][task]["status"] = status
        runtime._safe_write_json(self.state_path, state)
        return state["claims"][task]["token"], head

    def flip_plan_checkbox(self):
        # The sanctioned Step 1.3 flip: one pre-existing unchecked plan
        # checkbox line flipped to checked, left uncommitted.
        text = (self.root / self.plan_file).read_text(encoding="utf-8")
        flipped = text.replace("- [ ] step one", "- [x] step one", 1)
        self.assertNotEqual(text, flipped)
        (self.root / self.plan_file).write_text(flipped, encoding="utf-8")

    def done_receipt(self, task="task-3", generation=0, **overrides):
        result = {
            "status": "success",
            "reason_code": "completed",
            "evidence": [f"done-log:{task}"],
            "action_scope": "done-handoff",
            "checkpoint_identity": f"{task}:done-1",
            "generation": generation,
            "task_id": task,
            "commit_identity": "none",
            "checkbox": True,
            "clean_state": True,
            "log_evidence": [f"{task}-implement.log.md"],
        }
        result.update(overrides)
        claim = runtime.load_manifest(self.state_path).get("claims", {}).get(task)
        if claim:
            result.setdefault("claim_token", claim["token"])
        return result

    def test_none_identity_clean_worktree_completes(self):
        lookup = self.recording_lookup()
        driver = self.driver(commit_lookup=lookup)
        self.seed_done_pending()
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(outcome["reason_code"], "completed")
        self.assertIn(self.NONE_EVIDENCE_LINE, outcome["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "checkpointed")
        self.assertEqual(state["tasks"]["task-3"]["commit_identity"], "none")
        self.assertIn({"event": "done-commit", "task_id": "task-3", "commit_identity": "none"}, state["history"])
        self.assertEqual(state["claims"]["task-3"]["state"], "closed")
        # The driver never consults the commit lookup for the none receipt.
        self.assertEqual(lookup.calls, [])

    def test_none_identity_tolerates_plan_checkbox_flip(self):
        driver = self.driver()
        self.seed_done_pending()
        # The Step 1.3 flip rides uncommitted at the done receipt; the
        # outcome shape matches the clean case.
        self.flip_plan_checkbox()
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(outcome["reason_code"], "completed")
        self.assertIn(self.NONE_EVIDENCE_LINE, outcome["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "checkpointed")
        self.assertEqual(state["tasks"]["task-3"]["commit_identity"], "none")
        self.assertIn({"event": "done-commit", "task_id": "task-3", "commit_identity": "none"}, state["history"])

    def test_none_identity_refuses_untracked_dirt(self):
        driver = self.driver()
        self.seed_done_pending()
        (self.root / "stray-notes.txt").write_text("untracked dirt\n", encoding="utf-8")
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertTrue(any("worktree is not clean at the done boundary" in item for item in outcome["evidence"]))
        self.assertTrue(any("stray-notes.txt" in item for item in outcome["evidence"]))
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-3"]["state"], "launched")
        self.assertIsNone(state["tasks"]["task-3"].get("commit_identity"))

    def test_none_identity_refuses_tracked_content_dirt(self):
        driver = self.driver()
        self.seed_done_pending()
        # A committed fixture file edited with non-checkbox content: the
        # appended prose line has no removed counterpart, so the paired-line
        # shape never holds.
        with (self.root / self.plan_file).open("a", encoding="utf-8") as handle:
            handle.write("prose appendix, not a checkbox line\n")
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertTrue(any("worktree is not clean at the done boundary" in item for item in outcome["evidence"]))
        self.assertTrue(any(self.plan_file in item for item in outcome["evidence"]))
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-3"]["state"], "launched")

    def test_none_identity_refuses_in_scope_dirt(self):
        driver = self.driver()
        self.seed_done_pending(allowed=["task-3.txt", self.plan_file])
        # Checkbox-marker-only diff shape, but the file sits inside the
        # claim's allowed paths: in-scope dirt is the claim's own work to
        # commit, so the tolerance never reaches it.
        self.flip_plan_checkbox()
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertTrue(any("worktree is not clean at the done boundary" in item for item in outcome["evidence"]))
        self.assertTrue(any(self.plan_file in item for item in outcome["evidence"]))
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")

    def test_none_identity_refuses_when_head_moved_past_baseline(self):
        driver = self.driver()
        self.seed_done_pending()
        # One extra commit after the seeded baseline: a committing worker
        # cannot masquerade as verification-only.
        (self.root / "late.txt").write_text("late work\n", encoding="utf-8")
        self._git("add", "late.txt")
        self._git("commit", "-qm", "post-baseline work")
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertTrue(any("HEAD moved past the claim baseline" in item for item in outcome["evidence"]))
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")

    def test_real_commit_path_unchanged(self):
        driver = self.driver(commit_lookup=lambda _commit: False)
        self.seed_done_pending()
        outcome = driver.record_done(self.done_receipt(commit_identity="aa11bb22cc33"))
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertIn("commit not found: aa11bb22cc33", outcome["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-3"]["state"], "launched")

    def test_group_advance_none_hands_off_head_baseline(self):
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            [
                {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["t1-1.txt"]},
                {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["t2-1.txt"]},
            ],
            repo_root=self.root,
        )
        driver = self.driver(adapter=RecordingAdapter())
        driver.claim_next_task(batch=True)
        driver.launch_next_task(batch=True)
        head_before = self._git_stdout("rev-parse", "HEAD")
        done = driver.record_done(self.done_receipt("task-1", generation=1, checkpoint_identity="task-1:done"))
        self.assertEqual(done["status"], "success")
        self.assertEqual(done["actions"][0]["type"], "resume_member")
        manifest = runtime.load_manifest(self.state_path)
        group = next(group for group in manifest.get("claim_groups", {}).values() if isinstance(group, dict))
        attempt = group["member_attempts"]["task-2"]
        # Every hand-off site carries the fixture HEAD captured before the
        # done, exactly as if a real commit had landed.
        self.assertEqual(manifest["claims"]["task-2"]["baseline_revision"], head_before)
        self.assertEqual(attempt["baseline_revision"], head_before)
        self.assertEqual(attempt["initialized_from"], head_before)
        self.assertEqual(done["actions"][0]["baseline_revision"], head_before)

    def test_reconcile_accepts_recorded_none_identity(self):
        lookup = self.recording_lookup()
        driver = self.driver(commit_lookup=lookup)
        self.seed_done_pending()
        # The flip rides uncommitted at the none completion, exactly as in
        # the sanctioned flow.
        self.flip_plan_checkbox()
        done = driver.record_done(self.done_receipt())
        self.assertEqual(done["status"], "success")
        # Hand-corruption seeding: the atomic done flow closes the claim in
        # the same write as the completion, so a checkpointed task with a
        # still-launched claim is unreachable through the flow itself. The
        # done's auto next-claim is pruned so the fixture isolates the
        # corrupt claim.
        state = runtime.load_manifest(self.state_path)
        state["claims"] = {"task-3": state["claims"]["task-3"]}
        state["claims"]["task-3"]["state"] = "launched"
        runtime._safe_write_json(self.state_path, state)
        result = driver.reconcile_startup(commit_lookup=lookup)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["reason_code"], "completed")
        # The recovery completes without any git lookup refusal.
        self.assertEqual(lookup.calls, [])

    def test_none_completion_then_next_checkpoint_succeeds(self):
        driver = self.driver()
        self.seed_done_pending()
        self.flip_plan_checkbox()
        done = driver.record_done(self.done_receipt())
        self.assertEqual(done["status"], "success")
        token, _head = self.seed_done_pending(task="task-4", status="launched")
        checkpoint = {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["worker-log:task-4"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-4:worker-1",
            "generation": 0,
            "claim_token": token,
        }
        outcome = driver.record_worker_checkpoint(checkpoint)
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(outcome["state"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-4"]["state"], "launched")
        self.assertNotIn("worker-blocked", [event.get("event") for event in state["history"]])
        self.assertNotEqual(state["claims"]["task-4"].get("state"), "blocked")

    def test_none_completion_then_real_commit_done_succeeds(self):
        driver = self.driver()
        self.seed_done_pending()
        self.flip_plan_checkbox()
        done = driver.record_done(self.done_receipt())
        self.assertEqual(done["status"], "success")
        self.seed_done_pending(task="task-4", status="done-pending")
        (self.root / "task-4.txt").write_text("content change\n", encoding="utf-8")
        self._git("add", "task-4.txt")
        self._git("commit", "-qm", "task-4 content work")
        commit = self._git_stdout("rev-parse", "HEAD")
        # The real-identity done tail tolerates the riding flip while the
        # full witness chain keeps verifying the commit itself.
        outcome = self.driver(commit_lookup=lambda identity: identity == commit).record_done(
            self.done_receipt("task-4", commit_identity=commit)
        )
        self.assertEqual(outcome["status"], "success")
        self.assertEqual(outcome["reason_code"], "completed")
        self.assertIn(self.REAL_EVIDENCE_LINE, outcome["evidence"])
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-4"]["status"], "checkpointed")
        self.assertEqual(state["tasks"]["task-4"]["commit_identity"], commit)

    def test_reconcile_after_none_completion_not_blocked(self):
        driver = self.driver()
        self.seed_done_pending()
        self.flip_plan_checkbox()
        done = driver.record_done(self.done_receipt())
        self.assertEqual(done["status"], "success")
        self.seed_done_pending(task="task-4", status="launched")
        result = driver.reconcile_startup()
        self.assertNotIn(result["reason_code"], {"dirty-worktree", "cleanup-required"})

    def test_flip_shaped_content_rewrite_refuses(self):
        driver = self.driver()
        self.seed_done_pending()
        # Paired-line identity violated: the real checklist lines are
        # deleted and fabricated checked lines are inserted, so the diff is
        # not a marker flip of pre-existing lines even though the changed
        # line counts still pair one-to-one.
        text = (self.root / self.plan_file).read_text(encoding="utf-8")
        rewritten = text.replace("- [ ] step one\n- [ ] step two", "- [x] fabricated one\n- [x] fabricated two")
        self.assertNotEqual(text, rewritten)
        (self.root / self.plan_file).write_text(rewritten, encoding="utf-8")
        outcome = driver.record_done(self.done_receipt())
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["reason_code"], "commit-pending")
        self.assertTrue(any("worktree is not clean at the done boundary" in item for item in outcome["evidence"]))
        self.assertTrue(any(self.plan_file in item for item in outcome["evidence"]))
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["tasks"]["task-3"]["status"], "done-pending")
        self.assertEqual(state["claims"]["task-3"]["state"], "launched")


class DiagnoseOperationTest(unittest.TestCase):
    """Witnesses for the read-only first-failed-transition diagnose operation.

    The fixtures hand-write the history events the classifier keys on, with
    one exception: the terminal-gate witness drives a real final-stage
    terminal refusal so the terminal-refused producer is proven end to end.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "runtime_state.json"
        self.seed_manifest()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def seed_manifest(self) -> None:
        runtime.create_manifest(
            self.state_path,
            "fixture-plan",
            [
                {"id": "task-3", "number": 3, "status": "complete", "checkbox": True},
                {"id": "task-4", "number": 4, "status": "pending", "checkbox": False, "allowed_paths": ["task-4.txt"]},
            ],
        )

    def diagnose_driver(self) -> runtime.RuntimeDriver:
        # persist_construction=False mirrors the CLI diagnose construction:
        # no owner backfill or receipt write may precede a read-only report.
        return runtime.RuntimeDriver(
            self.state_path,
            plan_slug="fixture-plan",
            owner="test-owner",
            repo_root=self.root,
            persist_construction=False,
        )

    def append_history(self, events) -> None:
        state = runtime.load_manifest(self.state_path)
        state.setdefault("history", []).extend(events)
        runtime._safe_write_json(self.state_path, state)

    def seed_terminal_receipt(self) -> None:
        state = runtime.load_manifest(self.state_path)
        state["workflow_state"] = "complete"
        state["terminal_receipt"] = {
            "workflow_state": "complete",
            "phase5_checklist": ["phase 5 complete"],
            "archived_plan_path": "docs/plans/completed/fixture-plan.md",
            "last_commit_sha": "a" * 40,
            "plan_digest": "b" * 64,
        }
        runtime._safe_write_json(self.state_path, state)

    def test_diagnose_names_first_failed_timeout(self):
        self.append_history([
            {"event": "started", "task_id": "task-4", "generation": 0},
            {"event": "worker-blocked", "task_id": "task-4", "reason_code": "timeout"},
        ])
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["status"], "blocked")
        self.assertEqual(outcome["classification"], "timeout")
        self.assertEqual(
            outcome["first_failed_transition"],
            {"event": "worker-blocked", "task_id": "task-4", "reason_code": "timeout"},
        )

    def test_diagnose_classifies_capacity(self):
        self.append_history([
            {"event": "started", "task_id": "task-4", "generation": 0},
            {"event": "worker-blocked", "task_id": "task-4", "reason_code": "capacity-unavailable"},
        ])
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["classification"], "capacity-unavailable")
        self.assertEqual(outcome["first_failed_transition"]["event"], "worker-blocked")

    def test_diagnose_classifies_worker_failure_and_stale_evidence(self):
        # malformed-result and cleanup-unverified (the adapter's
        # non-resumable unverified-kill arm) classify worker-failure;
        # stale-claim classifies stale-evidence.
        for reason, expected in (
            ("malformed-result", "worker-failure"),
            ("stale-claim", "stale-evidence"),
            ("cleanup-unverified", "worker-failure"),
        ):
            with self.subTest(reason_code=reason):
                self.state_path.unlink(missing_ok=True)
                self.seed_manifest()
                self.append_history([
                    {"event": "started", "task_id": "task-4", "generation": 0},
                    {"event": "worker-blocked", "task_id": "task-4", "reason_code": reason},
                ])
                outcome = self.diagnose_driver().diagnose()
                self.assertEqual(outcome["classification"], expected)
                self.assertEqual(outcome["first_failed_transition"]["reason_code"], reason)

    def test_diagnose_classifies_inclusion(self):
        self.append_history([
            {"event": "started", "task_id": "task-4", "generation": 0},
            {"event": "worker-blocked", "task_id": "task-4", "reason_code": "precondition-unverified"},
        ])
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["classification"], "inclusion")
        self.assertEqual(outcome["first_failed_transition"]["reason_code"], "precondition-unverified")

    def test_diagnose_classifies_terminal_gate(self):
        driver = self.diagnose_driver()
        refusal = driver.mark_terminal(
            archived_plan_path="docs/plans/completed/fixture-plan.md",
            last_commit_sha="a" * 40,
            phase5_checklist=["phase 5 complete"],
        )
        # The final stage refuses on machine completeness (task-4 is
        # pending) before any gate or filesystem clause.
        self.assertEqual(refusal["status"], "blocked")
        self.assertEqual(refusal["reason_code"], "done-pending")
        state = runtime.load_manifest(self.state_path)
        self.assertEqual(state["workflow_state"], "active")
        refused = [event for event in state["history"] if event.get("event") == "terminal-refused"]
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]["stage"], "final")
        # The appended evidence is the composed refusal's evidence: the
        # append never changes the outcome.
        self.assertEqual(refused[0]["evidence"], refusal["evidence"])
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["classification"], "terminal-gate")
        self.assertEqual(outcome["first_failed_transition"], refused[0])

    def test_diagnose_classifies_user_interruption(self):
        # task-3 is complete, so its earlier timeout failure has since
        # reached the progressed terminal state and must be skipped: the
        # user-interrupt-recorded event is the earliest uncompleted failure.
        self.append_history([
            {"event": "started", "task_id": "task-3", "generation": 0},
            {"event": "worker-blocked", "task_id": "task-3", "reason_code": "timeout"},
            {"event": "user-interrupt-recorded", "user_interrupt": "2026-09-20T10:00:00+00:00"},
        ])
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["classification"], "user-interruption")
        self.assertEqual(
            outcome["first_failed_transition"],
            {"event": "user-interrupt-recorded", "user_interrupt": "2026-09-20T10:00:00+00:00"},
        )

    def test_diagnose_clean_terminal_reports_none(self):
        self.seed_terminal_receipt()
        outcome = self.diagnose_driver().diagnose()
        self.assertEqual(outcome["status"], "success")
        self.assertIsNone(outcome["first_failed_transition"])
        self.assertEqual(outcome["classification"], "none")

    def test_diagnose_is_read_only(self):
        self.append_history([
            {"event": "worker-blocked", "task_id": "task-4", "reason_code": "runtime-error"},
        ])
        before = hashlib.sha256(self.state_path.read_bytes()).hexdigest()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = runtime.main([
                "--manifest", str(self.state_path),
                "--operation", "diagnose",
                "--plan-slug", "fixture-plan",
                "--owner", "test-owner",
                "--repo-root", str(self.root),
            ])
        self.assertEqual(exit_code, 0)
        outcome = json.loads(buffer.getvalue().strip().splitlines()[-1])
        self.assertEqual(outcome["classification"], "worker-failure")
        self.assertEqual(hashlib.sha256(self.state_path.read_bytes()).hexdigest(), before)


class RecordingAdapter:
    """Batch-aware fake adapter recording launch and resume calls."""

    def __init__(self, launch_result=None, resume_result=None, session_id="sess-anchor-1"):
        self.launch_calls = []
        self.resume_calls = []
        self.session_id = session_id
        self.launch_result = dict(launch_result or {})
        self.resume_result = dict(resume_result or {})

    def _base(self, task_id, generation):
        return {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["batch-worker-log"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task_id}:worker",
            "generation": generation,
            "session_id": self.session_id,
        }

    def launch(self, task, prompt, generation, deadline_seconds=None, policy_token=None):
        self.launch_calls.append({"task_id": task["id"], "generation": generation, "prompt": prompt, "policy_token": policy_token})
        result = self._base(task["id"], generation)
        result.update(self.launch_result)
        return result

    def resume(self, session_id, prompt, generation, task_id=None, deadline_seconds=None, policy_token=None):
        self.resume_calls.append({"session_id": session_id, "task_id": task_id, "generation": generation, "prompt": prompt, "policy_token": policy_token})
        result = self._base(task_id or "unknown", generation)
        result.update(self.resume_result)
        return result


class SessionlessRecordingAdapter(RecordingAdapter):
    """Schema-legal success receipts that carry no
    session id at all (the codex adapter sets the field only when the
    envelope has one), so no anchor session is ever captured."""

    def _base(self, task_id, generation):
        result = super()._base(task_id, generation)
        result.pop("session_id", None)
        return result


class ContractContentParityTest(unittest.TestCase):
    """Durable probes for the runtime contract's documented obligations.

    Reads agents/skills/execute-plan/runtime-contract.md once and asserts
    each required content obligation as a whitespace-normalized fragment
    scoped to the paragraph block that anchors it, so deleting the span
    fails the probe even when the same words survive elsewhere in the file.
    """

    CONTRACT = ROOT / "agents/skills/execute-plan/runtime-contract.md"

    @classmethod
    def setUpClass(cls):
        cls.raw = cls.CONTRACT.read_text(encoding="utf-8")
        cls.blocks = [" ".join(block.split()) for block in cls.raw.split("\n\n")]

    def block_containing(self, *anchors):
        matches = [block for block in self.blocks if all(anchor in block for anchor in anchors)]
        self.assertTrue(
            matches,
            "no runtime-contract paragraph contains all anchors: " + " | ".join(anchors),
        )
        return matches[0]

    def test_contention_envelope_pairs_stale_claim_with_resumable_conflict(self):
        block = self.block_containing("resumable-conflict")
        self.assertIn("reason code `stale-claim` with recovery action `resumable-conflict`", block)
        self.assertIn("the decision itself is carried in the outcome's `decision` field", block)

    def test_terminal_path_bullet_requires_at_least_one_task(self):
        block = self.block_containing("`terminal-path` fires only when")
        self.assertIn("carries at least one task, every task is complete or checkpointed", block)

    def test_stop_or_recovery_covers_zero_task_sections(self):
        block = self.block_containing("`stop-or-recovery` for a machine state that is not `active`")
        self.assertIn("for a plan with zero recognizable task sections", block)

    def test_transition_preamble_names_exactly_one_next_action(self):
        block = self.block_containing("Each outcome in the table names exactly one next action")
        self.assertIn("take that one action, then re-classify the state", block)

    def test_transition_table_pins_capacity_unavailable_and_reclaimed_rows(self):
        table = self.block_containing(
            "Claim parks `waiting-capacity` keeping token, generation, and launch record",
            "a finished-workflow reclaim is refused with the `explicit-abort` preserve-and-stop envelope before any lease accounting",
        )
        self.assertIn("bounded-resume (`attempts_remaining: 3`)", table)
        self.assertIn(
            "Resume the same claim with `continue` (same token and generation, no second claim row)",
            table,
        )
        self.assertIn("the machine `workflow_state` outside the closed non-active set", table)
        self.assertIn(
            "a workflow in the closed non-active set returns `explicit-abort` (preserve-and-stop; the evidence names the finished state)",
            table,
        )

    def test_terminal_predicate_names_three_markers_whitespace_and_headings(self):
        block = self.block_containing(
            "empty or whitespace-only plan is refused as empty",
            "task headings is refused naming the missing task sections",
        )
        self.assertIn("one of `- [ ]`, `* [ ]`, or `+ [ ]`", block)

    def test_readiness_condition4_names_three_markers(self):
        block = self.block_containing("Plan-manifest agreement")
        self.assertIn("one of `- [ ]`, `* [ ]`, or `+ [ ]`", block)

    def test_readiness_fence_paragraph_names_fence_rules(self):
        block = self.block_containing("CommonMark-grade fence map")
        self.assertIn("backtick and tilde fences", block)
        self.assertIn("zero-to-three-space indent tolerance", block)
        self.assertIn("keep parity until the matching closer", block)
        self.assertIn("unclosed fence stays open to end of file", block)

    def test_stale_scanner_reference_is_gone(self):
        self.assertNotIn("2026-09-17-fence-robust-checkbox-scanning", self.raw)

    def test_waiting_capacity_paragraph_carries_retry_resume_and_group_shape(self):
        block = self.block_containing("parks a single-task claim in the `waiting-capacity` state")
        self.assertIn("`mode: bounded-resume`, `max_attempts: 3`, `attempts_remaining: 3`", block)
        self.assertIn("the receipt that arrives with the budget exhausted transitions the claim to `blocked`", block)
        self.assertIn("recovery is the in-place resume", block)
        self.assertIn("A capacity receipt on a live batch-group member never parks", block)

    def test_reason_code_list_contains_capacity_unavailable(self):
        block = self.block_containing("The standard reason codes are")
        self.assertIn("`capacity-unavailable`", block)

    def test_diagnose_subsection_names_enum_and_read_only_rule(self):
        enum_block = self.block_containing("The classification enum is fixed")
        for code in (
            "timeout",
            "capacity-unavailable",
            "worker-failure",
            "stale-evidence",
            "inclusion",
            "terminal-gate",
            "user-interruption",
            "none",
        ):
            self.assertIn(f"`{code}`", enum_block)
        read_only = self.block_containing("The `diagnose` operation is the read-only first-failed-transition report")
        self.assertIn("returns without any write path", read_only)

    def test_deadline_paragraph_names_both_baselines(self):
        # The neutral contract keeps deadlines out; the baseline lives in
        # the codex adapter profile (and the shipped package manifest).
        profile_blocks = [
            " ".join(block.split())
            for block in (ROOT / "agents/skills/execute-plan/runtime-adapters/codex.md")
            .read_text(encoding="utf-8")
            .split("\n\n")
        ]
        matches = [b for b in profile_blocks if "cross-runtime deadline baseline" in b]
        self.assertTrue(
            matches,
            "no codex adapter profile paragraph names the cross-runtime deadline baseline",
        )
        self.assertIn("`launch_deadline_seconds = 900` and `wait_deadline_seconds = 1500`", matches[0])

    def test_reclaim_finished_workflow_fence_is_documented(self):
        block = self.block_containing("workflow was explicitly aborted before")
        self.assertIn("a machine `workflow_state` of `aborted`, `complete`, or `terminal`", block)
        self.assertIn("the envelope reason code is `explicit-abort` for all three closed states", block)
        self.assertIn("the evidence names the finished state", block)
        self.assertIn("\"workflow_state is '<state>'; the workflow already finished\" under `complete` and `terminal`", block)


class PlansWatcherScheduleContractTest(unittest.TestCase):
    """Witnesses for the plans-watcher-schedule full-probe-report contract.

    The boundary classifier reads `status`, `binding`, `pause_decision`,
    and the binding window's `reset_at_epoch` from the matching `limits[]`
    entry. The two witnesses pin both contract ends: a full probe report
    at a known continue with a trusted epoch installs the watcher, and a
    subset payload (flat `reset_at_epoch`, no `limits[]`) classifies
    unknown and degrades to the report-only supersede. On the clean tree
    they pin existing classifier behavior; they go RED only under the
    plan's mutation probes.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_path = self.root / "plan-requirements-contract-fixture.json"
        self.plan_path = self.root / "contract-fixture-plan.md"
        self.plan_path.write_text("# contract fixture plan\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _hermetic_launchd(self, bootstrap_calls: list[str]) -> None:
        # The schedule arm's launchd link must never reach the real gui
        # domain from a test: patch the bootstrap and prove it consumed.
        import execute_plan_resume_watcher as watcher

        def fake_bootstrap(job):
            bootstrap_calls.append(str(job))
            return True, ""

        patcher = mock.patch.object(watcher, "launchctl_bootstrap", fake_bootstrap)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _full_probe_report(self, reset_at_epoch: int) -> dict:
        return {
            "status": "ok",
            "binding": "5h",
            "pause_decision": "continue",
            "limits": [{"kind": "5h", "reset_at_epoch": reset_at_epoch}],
        }

    def _schedule(self, probe_report: dict) -> tuple[dict, list[str]]:
        bootstrap_calls: list[str] = []
        self._hermetic_launchd(bootstrap_calls)
        payload = {
            "state_path": str(self.state_path),
            "plan_path": str(self.plan_path),
            "plan_slug": "contract-fixture",
            "job_dir": str(self.root / "launchd"),
            "sentinel_path": str(self.root / "budget-resume.sentinel"),
            "probe_report": probe_report,
        }
        outcome = runtime._plans_watcher_operation("plans-watcher-schedule", payload, self.root)
        return outcome, bootstrap_calls

    def test_trusted_epoch_continue_installs_watcher(self) -> None:
        reset_at_epoch = int(datetime.now().timestamp()) + 3600
        outcome, bootstrap_calls = self._schedule(self._full_probe_report(reset_at_epoch))
        self.assertEqual(outcome["status"], "success", outcome)
        self.assertEqual(outcome["reason_code"], "resume-watcher-scheduled", outcome)
        receipt = outcome.get("resume_watcher")
        self.assertIsNotNone(receipt, outcome)
        self.assertEqual(int(receipt["reset_at_epoch"]), reset_at_epoch, outcome)
        scheduling = outcome.get("scheduling")
        self.assertIsNotNone(scheduling, outcome)
        self.assertTrue(scheduling.get("scheduled"), outcome)
        self.assertTrue(
            bootstrap_calls,
            "launchd bootstrap fake was never invoked; the install witness would be mutating the real gui domain",
        )

    def test_probe_subset_degrades_report_only(self) -> None:
        reset_at_epoch = int(datetime.now().timestamp()) + 3600
        subset = {"status": "ok", "binding": "5h", "reset_at_epoch": reset_at_epoch}
        outcome, bootstrap_calls = self._schedule(subset)
        self.assertEqual(outcome["status"], "blocked", outcome)
        self.assertEqual(outcome["reason_code"], "resume-watcher-superseded", outcome)
        evidence = " | ".join(str(item) for item in (outcome.get("evidence") or ()))
        self.assertIn("classification=unknown", evidence)
        self.assertIsNone(outcome.get("scheduling"), outcome)
        self.assertIsNone(outcome.get("resume_watcher"), outcome)
        self.assertEqual(bootstrap_calls, [], "the degraded boundary must arm nothing")


if __name__ == "__main__":
    unittest.main()
