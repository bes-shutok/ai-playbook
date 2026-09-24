#!/usr/bin/env python3
"""RED contract tests for the manifest-owned execute-plan worker registry."""

from __future__ import annotations

import itertools
import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "scripts/testdata/execute-plan"


class WorkerRegistryTest(unittest.TestCase):
    @staticmethod
    def worker_registry_class():
        # Keep collection independent of Task 2's not-yet-created module so
        # the complete RED surface is reported in one run.
        from execute_plan_worker_registry import WorkerRegistry

        return WorkerRegistry

    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def registry(self, manifest: dict | None = None):
        value = deepcopy(manifest or self.load_fixture("runtime_state.json"))
        value.setdefault("claims", {}).setdefault("task-4", {"token": "ct4", "owner": "owner-task-4", "generation": 1, "state": "claimed"})
        return self.worker_registry_class()(value)

    @staticmethod
    def launch_fields(**overrides):
        fields = {
            "task_id": "task-4",
            "claim_token": "ct4",
            "generation": 1,
            "claim_owner_id": "owner-task-4",
            "provider_session_id": "provider-session-task-4",
            "worker_id": "worker-task-4",
            "command_identity": "opaque-command-task-4",
            "process_identity": {"pid": 4711, "start_time": "start-4711"},
            "launch_id": "launch-task-4",
            "capacity_entry_id": "capacity-task-4",
            "started_at": 100.0,
        }
        fields.update(overrides)
        return fields

    @staticmethod
    def lifecycle_receipt(event="terminal", **overrides):
        receipt = {
            "receipt_id": f"{event}-task-4",
            "task_id": "task-4",
            "claim_token": "ct4",
            "claim_owner_id": "owner-task-4",
            "generation": 1,
            "worker_id": "worker-task-4",
            "provider_session_id": "provider-session-task-4",
            "event": event,
            "outcome": "exit",
            "reason": "completed",
            "proof": {"kind": "provider-terminal", "verified": True},
            "observed_at": 110.0,
        }
        event_fields = {
            "terminal": {
                "outcome": "exit",
                "reason": "completed",
                "proof": {"kind": "provider-terminal", "verified": True},
            },
            "timeout": {
                "outcome": "timeout",
                "reason": "deadline-exceeded",
                "proof": {"kind": "deadline", "verified": False},
            },
            "shutdown": {
                "outcome": "shutdown",
                "reason": "parent-shutdown",
                "proof": {"kind": "parent-shutdown", "verified": False},
            },
            "close": {
                "outcome": "closed",
                "reason": "provider-close-confirmed",
                "proof": {"kind": "provider-close", "verified": True},
            },
            "not_found": {
                "outcome": "not_found",
                "reason": "provider-not-found",
                "proof": {"kind": "provider-close", "verified": False},
            },
            "replay": {
                "receipt_id": "terminal-task-4",
                "outcome": "exit",
                "reason": "completed",
                "proof": {"kind": "provider-terminal", "verified": True},
                "replayed_receipt_id": "terminal-task-4",
            },
            "late": {
                "claim_token": "old",
                "generation": 0,
                "outcome": "exit",
                "reason": "late-receipt",
                "proof": {"kind": "provider-terminal", "verified": True},
            },
        }
        receipt.update(event_fields[event])
        receipt.update(overrides)
        return receipt

    @classmethod
    def terminal_receipt(cls, **overrides):
        return cls.lifecycle_receipt("terminal", **overrides)

    def test_launch_registers_claim_and_worker_identity(self):
        registry = self.registry()
        worker = registry.register_launch(**self.launch_fields())

        self.assertEqual(worker["claim_token"], "ct4")
        self.assertEqual(worker["generation"], 1)
        self.assertEqual(worker["task_id"], "task-4")
        self.assertEqual(worker["provider_session_id"], "provider-session-task-4")
        self.assertEqual(worker["worker_id"], "worker-task-4")
        self.assertEqual(worker["command_identity"], "opaque-command-task-4")
        self.assertEqual(worker["process_identity"]["start_time"], "start-4711")
        self.assertEqual(registry.capacity_witness()["live_workers"], 1)
        self.assertEqual(len(registry.capacity_witness()["entries"]), 1)

    def test_register_launch_accepts_matching_live_claim(self):
        registry = self.registry()

        worker = registry.register_launch(**self.launch_fields())

        self.assertEqual(worker["state"], "active")
        self.assertEqual(worker["claim_token"], registry.manifest["claims"]["task-4"]["token"])

    def test_register_launch_accepts_codex_provider_session_identity(self):
        registry = self.registry()
        worker = registry.register_launch(**self.launch_fields(process_identity={"provider": "codex", "session_id": "thread-123"}))

        self.assertEqual(worker["process_identity"], {"provider": "codex", "session_id": "thread-123"})
        self.assertEqual(registry.capacity_witness()["live_workers"], 1)

    def test_terminal_event_releases_capacity_idempotently(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())

        first = registry.apply_terminal_receipt(self.terminal_receipt())
        second = registry.apply_terminal_receipt(self.terminal_receipt())

        self.assertEqual(first["outcome"], "released")
        self.assertEqual(second, first)
        self.assertEqual(registry.capacity_witness()["live_workers"], 0)
        self.assertEqual(registry.transition_count("worker-task-4"), 1)

    def test_terminal_worker_keeps_original_identity_after_claim_rotation(self):
        from execute_plan_worker_registry import validate_manifest_worker_schema

        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.apply_terminal_receipt(self.terminal_receipt())
        registry.manifest["history"] = [{
            "event": "done-pending-recovery",
            "task_id": "task-4",
            "token": "ct4",
            "generation": 1,
            "disposition": "requeue",
        }]
        registry.manifest["claims"]["task-4"] = {
            "token": "ct4-requeued",
            "owner": "owner-task-4-requeued",
            "generation": 2,
            "state": "claimed",
        }

        validated = validate_manifest_worker_schema(registry.manifest)

        self.assertEqual(validated["workers"]["worker-task-4"]["claim_token"], "ct4")

    def test_terminal_worker_rotation_without_receipt_backing_is_refused(self):
        from execute_plan_worker_registry import validate_manifest_worker_schema

        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.apply_terminal_receipt(self.terminal_receipt())
        registry.manifest["claims"]["task-4"] = {
            "token": "ct4-requeued",
            "owner": "owner-task-4-requeued",
            "generation": 2,
            "state": "claimed",
        }

        with self.assertRaisesRegex(ValueError, "worker claim identity does not match claim"):
            validate_manifest_worker_schema(registry.manifest)

    def test_terminal_worker_requeue_receipt_must_match_original_identity(self):
        from execute_plan_worker_registry import validate_manifest_worker_schema

        for mutated in ({"token": "ct4-other"}, {"generation": 9}, {"task_id": "other-task"}):
            with self.subTest(mutated=mutated):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                registry.apply_terminal_receipt(self.terminal_receipt())
                registry.manifest["history"] = [{
                    "event": "done-pending-recovery",
                    "task_id": "task-4",
                    "token": "ct4",
                    "generation": 1,
                    "disposition": "requeue",
                    **mutated,
                }]
                registry.manifest["claims"]["task-4"] = {
                    "token": "ct4-requeued",
                    "owner": "owner-task-4-requeued",
                    "generation": 2,
                    "state": "claimed",
                }

                with self.assertRaisesRegex(ValueError, "worker claim identity does not match claim"):
                    validate_manifest_worker_schema(registry.manifest)

    def test_terminal_worker_requires_receipt_identity_to_match_original_worker(self):
        from execute_plan_worker_registry import validate_manifest_worker_schema

        identity_fields = {
            "task_id": "other-task",
            "claim_token": "other-token",
            "claim_owner_id": "other-owner",
            "generation": 9,
            "worker_id": "other-worker",
            "provider_session_id": "other-session",
        }
        for field, invalid_value in identity_fields.items():
            with self.subTest(field=field):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                registry.apply_terminal_receipt(self.terminal_receipt())
                registry.manifest["workers"]["worker-task-4"]["receipt_metadata"][field] = invalid_value
                registry.manifest["claims"]["task-4"] = {
                    "token": "ct4-requeued",
                    "owner": "owner-task-4-requeued",
                    "generation": 2,
                    "state": "claimed",
                }

                with self.assertRaisesRegex(ValueError, "terminal worker receipt identity does not match worker"):
                    validate_manifest_worker_schema(registry.manifest)

    def test_active_worker_must_match_current_claim_after_claim_rotation(self):
        from execute_plan_worker_registry import validate_manifest_worker_schema

        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.manifest["claims"]["task-4"] = {
            "token": "ct4-requeued",
            "owner": "owner-task-4-requeued",
            "generation": 2,
            "state": "claimed",
        }

        with self.assertRaisesRegex(ValueError, "worker claim identity does not match claim"):
            validate_manifest_worker_schema(registry.manifest)

    def test_terminal_and_close_require_verified_matching_proof_and_replay_idempotently(self):
        for event in ("terminal", "close"):
            valid = self.lifecycle_receipt(event)
            invalid_proofs = [
                {"kind": valid["proof"]["kind"], "verified": False},
                None,
                {"kind": valid["proof"]["kind"]},
                {"kind": valid["proof"]["kind"], "verified": "true"},
            ]
            for proof in invalid_proofs:
                with self.subTest(event=event, proof=proof):
                    registry = self.registry()
                    registry.register_launch(**self.launch_fields())
                    receipt = self.lifecycle_receipt(event)
                    if proof is None:
                        receipt.pop("proof")
                    else:
                        receipt["proof"] = proof

                    result = registry.apply_lifecycle_event(event, receipt)

                    self.assertEqual(result["outcome"], "quarantined")
                    self.assertEqual(registry.worker("worker-task-4")["state"], "quarantined")
                    self.assertTrue(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])

            registry = self.registry()
            registry.register_launch(**self.launch_fields())
            receipt = self.lifecycle_receipt(event)
            first = registry.apply_lifecycle_event(event, receipt)
            second = registry.apply_lifecycle_event(event, receipt)
            self.assertEqual(first["outcome"], "released")
            self.assertEqual(second, first)
            self.assertEqual(registry.worker("worker-task-4")["state"], "terminal")
            self.assertFalse(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])
            self.assertEqual(registry.transition_count("worker-task-4"), 1)

    def test_terminal_and_close_refuse_verified_proof_for_wrong_event(self):
        for event in ("terminal", "close"):
            with self.subTest(event=event):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                wrong_kind = "provider-close" if event == "terminal" else "provider-terminal"
                receipt = self.lifecycle_receipt(event, proof={"kind": wrong_kind, "verified": True})

                result = registry.apply_lifecycle_event(event, receipt)

                self.assertEqual(result["outcome"], "quarantined")
                self.assertEqual(registry.worker("worker-task-4")["state"], "quarantined")
                self.assertTrue(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])

    def test_not_found_after_terminal_is_already_closed(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.apply_terminal_receipt(self.terminal_receipt())
        before = registry.capacity_witness()

        result = registry.apply_close_result(
            self.terminal_receipt(receipt_id="close-task-4"), outcome="not_found"
        )

        self.assertEqual(result["outcome"], "already-closed")
        self.assertEqual(registry.capacity_witness(), before)

    def test_stale_inventory_is_quarantined_not_free_capacity(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())

        result = registry.reconcile(provider_inventory=[])

        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reason"], "stale-inventory")
        self.assertEqual(registry.capacity_witness()["live_workers"], 0)
        self.assertFalse(registry.capacity_witness()["launch_available"])

    def test_duplicate_capacity_contributions_for_one_worker_are_rejected(self):
        manifest = self.load_fixture("runtime_state.parallel.json")
        first = next(iter(manifest["capacity"]["entries"].values()))
        duplicate_id = "capacity-duplicate"
        manifest["capacity"]["entries"][duplicate_id] = {
            "capacity_entry_id": duplicate_id,
            "worker_id": first["worker_id"],
            "counts_toward_capacity": True,
            "state": "live",
        }

        with self.assertRaisesRegex(ValueError, "duplicate capacity contributions"):
            self.worker_registry_class()(manifest)

    def test_concurrent_close_and_completion_converge(self):
        for first, second in (("terminal", "close"), ("close", "terminal")):
            with self.subTest(first=first, second=second):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                for event in (first, second):
                    if event == "terminal":
                        result = registry.apply_terminal_receipt(self.terminal_receipt())
                    else:
                        result = registry.apply_close_result(
                            self.lifecycle_receipt("close", receipt_id="close-task-4"), outcome="closed"
                        )

                self.assertIn(result["outcome"], {"released", "already-closed"})
                self.assertEqual(registry.worker("worker-task-4")["state"], "terminal")
                self.assertEqual(registry.capacity_witness()["live_workers"], 0)
                self.assertEqual(registry.transition_count("worker-task-4"), 1)

    def test_quarantined_worker_recovers_only_from_matching_proven_terminal_receipt(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.apply_lifecycle_event("timeout", self.lifecycle_receipt("timeout"))
        before = deepcopy(registry.manifest)

        mismatch = self.lifecycle_receipt("terminal", claim_token="stale")
        refused = registry.apply_lifecycle_event("terminal", mismatch)
        self.assertEqual(refused["reason"], "identity-mismatch")
        self.assertEqual(registry.manifest, before)

        unproven = self.lifecycle_receipt("terminal", receipt_id="unproven", proof={"verified": False})
        retained = registry.apply_lifecycle_event("terminal", unproven)
        self.assertEqual(retained["outcome"], "quarantined")
        self.assertTrue(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])

        proven = self.lifecycle_receipt("terminal", receipt_id="recovery")
        released = registry.apply_lifecycle_event("terminal", proven)
        replayed = registry.apply_lifecycle_event("terminal", proven)
        self.assertEqual(released["outcome"], "released")
        self.assertEqual(replayed, released)
        self.assertEqual(registry.worker("worker-task-4")["state"], "terminal")
        self.assertFalse(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])

    def test_quarantined_worker_does_not_recover_from_wrong_proof_kind(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        registry.apply_lifecycle_event("timeout", self.lifecycle_receipt("timeout"))
        before = deepcopy(registry.manifest)
        wrong_proof = self.lifecycle_receipt("terminal", proof={"kind": "provider-close", "verified": True})

        result = registry.apply_lifecycle_event("terminal", wrong_proof)

        self.assertEqual(result["outcome"], "quarantined")
        self.assertEqual(registry.worker("worker-task-4")["state"], "quarantined")
        self.assertTrue(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])
        self.assertEqual(registry.manifest, before)

    def test_stalled_worker_requires_recovery_receipt(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields(started_at=10.0))

        result = registry.reconcile(
            provider_inventory=[{"provider_session_id": "provider-session-task-4", "process_identity": {"pid": 4711, "start_time": "start-4711"}}],
            now=10.0 + registry.liveness_window + 1,
            progress={},
        )

        self.assertEqual(result["status"], "stalled")
        self.assertEqual(result["recovery_action"], "recovery-receipt-or-relaunch")
        self.assertFalse(registry.capacity_witness()["launch_available"])

    def test_parallel_fixture_loads_several_distinct_agent_sessions(self):
        parallel = self.load_fixture("runtime_state.parallel.json")
        sequential = self.load_fixture("runtime_state.json")
        registry = self.registry(parallel)

        self.assertEqual(len(registry.active_workers()), 2)
        claims = list(parallel["claims"].values())
        workers = list(parallel["workers"].values())
        capacities = list(parallel["capacity"]["entries"].values())
        self.assertEqual(len({claim["claim_token"] for claim in claims}), 2)
        self.assertEqual(len({claim["owner"] for claim in claims}), 2)
        self.assertEqual(len({claim["generation"] for claim in claims}), 2)
        self.assertEqual(len({worker["provider_session_id"] for worker in workers}), 2)
        self.assertEqual(len({worker["worker_id"] for worker in workers}), 2)
        self.assertEqual(len({entry["capacity_entry_id"] for entry in capacities}), 2)
        self.assertNotIn("workers", sequential)
        self.assertNotIn("capacity", sequential)
        self.assertEqual(self.registry(sequential).capacity_witness()["live_workers"], 0)

    def test_parallel_member_transition_does_not_mutate_sibling_session(self):
        registry = self.registry(self.load_fixture("runtime_state.parallel.json"))
        before = deepcopy(registry.manifest)
        registry.apply_terminal_receipt(
            self.terminal_receipt(
                task_id="task-4a",
                claim_token="ct4a",
                generation=3,
                worker_id="worker-task-4a",
                provider_session_id="provider-session-task-4a",
                receipt_id="terminal-task-4a",
            )
        )

        sibling = registry.manifest["claims"]["task-4b"]
        self.assertEqual(sibling, before["claims"]["task-4b"])
        self.assertEqual(registry.worker("worker-task-4b")["state"], "active")
        self.assertTrue(registry.capacity_entry("capacity-task-4b")["counts_toward_capacity"])

    def test_two_drivers_interleave_without_cross_session_mutation(self):
        first = self.registry(self.load_fixture("runtime_state.parallel.json"))
        second = self.registry(self.load_fixture("runtime_state.parallel.json"))

        first.checkpoint("task-4a", claim_token="ct4a", generation=3)
        second.apply_terminal_receipt(
            self.terminal_receipt(
                task_id="task-4b",
                claim_token="ct4b",
                claim_owner_id="owner-task-4b",
                generation=4,
                worker_id="worker-task-4b",
                provider_session_id="provider-session-task-4b",
                receipt_id="terminal-task-4b",
            )
        )
        first.resume("task-4a", claim_token="ct4a", generation=3)

        self.assertEqual(first.worker("worker-task-4a")["provider_session_id"], "provider-session-task-4a")
        self.assertEqual(second.worker("worker-task-4b")["state"], "terminal")
        self.assertEqual(first.worker("worker-task-4b")["state"], "active")
        self.assertEqual(first.capacity_witness()["live_workers"], 2)

    def test_lifecycle_order_permutations_converge(self):
        events = ("terminal", "timeout", "shutdown", "close", "not_found", "replay", "late")
        proof_events = {"terminal", "close"}
        for first, second in itertools.permutations(events, 2):
            with self.subTest(first=first, second=second):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                first_receipt = self.lifecycle_receipt(
                    first,
                    **({"claim_token": "ct4", "generation": 1} if first == "late" else {}),
                )
                first_result = registry.apply_lifecycle_event(
                    first, first_receipt
                )
                second_receipt = self.lifecycle_receipt(
                    second,
                    **({"claim_token": "ct4", "generation": 1} if second == "late" else {}),
                )
                second_result = registry.apply_lifecycle_event(
                    second, second_receipt
                )
                worker = registry.worker("worker-task-4")
                witness = registry.capacity_witness()

                if first in proof_events or second in proof_events:
                    if first in proof_events:
                        self.assertEqual(first_result["outcome"], "released")
                    self.assertEqual(worker["state"], "terminal")
                    self.assertTrue(witness["launch_available"])
                    self.assertIn(second_result["outcome"], {"already-closed", "replayed", "refused", "released"})
                else:
                    self.assertIn(first_result["outcome"], {"quarantined", "refused"})
                    self.assertEqual(worker["state"], "quarantined")
                    self.assertFalse(witness["launch_available"])
                    self.assertIn(second_result["outcome"], {"quarantined", "refused", "already-closed"})

                self.assertLessEqual(registry.transition_count("worker-task-4"), 1)
                self.assertEqual(witness["live_workers"], 0)

    def test_lifecycle_outcomes_release_only_with_valid_proof(self):
        for event in ("terminal", "timeout", "shutdown", "close", "not_found", "replay", "late"):
            with self.subTest(event=event):
                registry = self.registry()
                registry.register_launch(**self.launch_fields())
                if event == "replay":
                    registry.apply_lifecycle_event("terminal", self.lifecycle_receipt("terminal"))
                receipt = self.lifecycle_receipt(
                    event,
                    **({"claim_token": "ct4", "generation": 1} if event == "late" else {}),
                )
                result = registry.apply_lifecycle_event(event, receipt)
                worker = registry.worker("worker-task-4")
                entry = registry.capacity_entry("capacity-task-4")
                if event in {"terminal", "close", "replay"}:
                    self.assertEqual(worker["state"], "terminal")
                    self.assertFalse(entry["counts_toward_capacity"])
                    self.assertEqual(registry.transition_count("worker-task-4"), 1)
                else:
                    self.assertEqual(worker["state"], "quarantined")
                    self.assertTrue(entry["counts_toward_capacity"])
                    self.assertEqual(registry.transition_count("worker-task-4"), 0)
                self.assertEqual(result["outcome"] in {"released", "replayed"}, event in {"terminal", "close", "replay"})

    def test_incomplete_lifecycle_envelope_is_refused_without_mutation(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        before = deepcopy(registry.manifest)
        for field in ("claim_owner_id", "event", "observed_at", "reason", "provider_session_id"):
            receipt = self.lifecycle_receipt()
            receipt.pop(field, None)
            self.assertEqual(registry.apply_lifecycle_event("terminal", receipt)["reason"], "malformed-lifecycle-receipt")
        self.assertEqual(registry.manifest, before)

    def test_late_receipt_validates_identity_before_quarantining(self):
        registry = self.registry()
        registry.register_launch(**self.launch_fields())
        receipt = self.lifecycle_receipt("late", claim_token="ct4", generation=1)
        before = json.dumps(registry.manifest, sort_keys=True, separators=(",", ":")).encode()

        mismatched = dict(receipt, claim_token="stale")
        result = registry.apply_lifecycle_event("late", mismatched)

        after = json.dumps(registry.manifest, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], "identity-mismatch")
        self.assertEqual(hashlib.sha256(after).digest(), hashlib.sha256(before).digest())
        self.assertEqual(after, before)

        matching_result = registry.apply_lifecycle_event("late", receipt)

        self.assertEqual(matching_result["outcome"], "quarantined")
        self.assertEqual(registry.worker("worker-task-4")["state"], "quarantined")
        self.assertTrue(registry.capacity_entry("capacity-task-4")["counts_toward_capacity"])
        self.assertEqual(registry.capacity_entry("capacity-task-4")["state"], "quarantined")

    def test_registry_migrates_legacy_manifest_in_memory(self):
        legacy = self.load_fixture("runtime_state.json")
        original = deepcopy(legacy)

        registry = self.registry(legacy)

        self.assertNotIn("workers", legacy)
        self.assertNotIn("capacity", legacy)
        self.assertEqual(legacy, original)
        self.assertEqual(registry.manifest["workers"], {})
        self.assertEqual(registry.manifest["capacity"], {"version": 1, "entries": {}})

    def test_registry_reducer_mutates_only_its_detached_manifest(self):
        legacy = self.load_fixture("runtime_state.json")
        original = deepcopy(legacy)
        registry = self.registry(legacy)

        registry.register_launch(**self.launch_fields())

        self.assertEqual(legacy, original)
        self.assertIn("worker-task-4", registry.manifest["workers"])
        self.assertIn("capacity-task-4", registry.manifest["capacity"]["entries"])

    def test_identity_collision_and_late_receipt_are_refused(self):
        registry = self.registry(self.load_fixture("runtime_state.parallel.json"))
        before = deepcopy(registry.manifest)
        for fields in (
            self.launch_fields(provider_session_id="provider-session-task-4a"),
            self.launch_fields(task_id="task-4b", claim_token="ct4b", generation=4),
        ):
            result = registry.register_launch(**fields)
            self.assertEqual(result["status"], "refused")
        late = registry.apply_terminal_receipt(
            self.terminal_receipt(
                claim_token="old", worker_id="worker-task-4a", receipt_id="late-old-owner"
            )
        )
        self.assertEqual(late["status"], "refused")
        self.assertEqual(registry.manifest["claims"]["task-4b"], before["claims"]["task-4b"])
        self.assertEqual(registry.capacity_witness()["live_workers"], 2)

if __name__ == "__main__":
    unittest.main()
