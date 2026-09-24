#!/usr/bin/env python3
"""Pure in-memory manifest worker registry reducer.

The registry has no file, lock, adapter, or durable-history knowledge.
``RuntimeDriver`` owns those concerns and persists the reducer's manifest.
"""

from __future__ import annotations

import copy
import json
import time
from typing import Any, Mapping


REGISTRY_VERSION = 1
WORKER_STATES = {"active", "terminal", "quarantined"}
TERMINAL_EVENTS = {"terminal", "close", "not_found"}
UNPROVEN_EVENTS = {"timeout", "shutdown", "not_found"}
OBSERVATION_STATES = {"available", "terminal", "stale", "unavailable", "malformed", "timed-out", "unsupported"}
OBSERVATION_VERSION = 1


def validate_provider_observation(value: Any, *, now: float, expected_kind: str = "inventory") -> dict[str, Any]:
    """Validate the versioned neutral provider envelope and normalize failures."""
    if not isinstance(value, Mapping):
        return {"version": OBSERVATION_VERSION, "observation_kind": expected_kind, "state": "unavailable", "capacity_slot_effect": "quarantine"}
    state = value.get("state")
    kind = value.get("observation_kind")
    observed_at = value.get("observed_at")
    freshness = value.get("freshness_window")
    effect = value.get("capacity_slot_effect")
    if value.get("version") != OBSERVATION_VERSION or kind != expected_kind or state not in OBSERVATION_STATES:
        return {"version": OBSERVATION_VERSION, "observation_kind": expected_kind, "state": "malformed", "capacity_slot_effect": "quarantine"}
    if not isinstance(observed_at, (int, float)) or isinstance(observed_at, bool) or not isinstance(freshness, (int, float)) or isinstance(freshness, bool) or freshness <= 0:
        return {**dict(value), "state": "malformed", "capacity_slot_effect": "quarantine"}
    if state not in {"unsupported", "unavailable", "timed-out", "malformed"} and (observed_at > now or now - observed_at > freshness):
        return {**dict(value), "state": "stale", "capacity_slot_effect": "quarantine"}
    expected_effect = {"available": "retain", "terminal": "release"}.get(state, "quarantine")
    if effect != expected_effect:
        return {**dict(value), "state": "malformed", "capacity_slot_effect": "quarantine"}
    if state in {"available", "terminal"} and (not isinstance(value.get("inventory"), list)):
        return {**dict(value), "state": "malformed", "capacity_slot_effect": "quarantine"}
    return dict(value)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _nonnegative(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _process_identity(value: Any, name: str) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{name} must be a non-empty identity mapping")
    pid, start = value.get("pid"), value.get("start_time")
    if pid is not None or start is not None:
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            raise ValueError(f"{name} must contain a positive pid")
        if not isinstance(start, (str, int, float)) or isinstance(start, bool) or (isinstance(start, str) and not start.strip()):
            raise ValueError(f"{name} must contain a valid start_time")
        return
    if not all(isinstance(value.get(key), str) and value[key].strip() for key in ("provider", "session_id")):
        raise ValueError(f"{name} must contain a process or provider session identity")


def migrate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a detached manifest with the versioned registry sections seeded."""
    if not isinstance(manifest, Mapping):
        raise ValueError("runtime manifest must be a mapping")
    value = copy.deepcopy(dict(manifest))
    value.setdefault("workers", {})
    value.setdefault("capacity", {"version": REGISTRY_VERSION, "entries": {}})
    if not isinstance(value["workers"], dict):
        raise ValueError("manifest workers must be a mapping")
    if not isinstance(value["capacity"], dict):
        raise ValueError("manifest capacity must be a mapping")
    value["capacity"].setdefault("version", REGISTRY_VERSION)
    value["capacity"].setdefault("entries", {})
    return value


TERMINAL_BACKING_RECEIPT_EVENT = "done-pending-recovery"
CLOSED_CLAIM_STATES = {"closed", "replaced", "aborted"}


def _terminal_receipt_backed(value: Mapping[str, Any], worker: Mapping[str, Any]) -> bool:
    """True when a done-pending-recovery receipt backs this historical terminal record.

    The receipt must match the record's ORIGINAL claim identity (task id,
    claim token, launch generation) - the identity the worker was launched
    under - proving the record is the retired first attempt of a recovery
    requeue, not an orphan of an unrecorded claim rotation.
    """
    history = value.get("history")
    if not isinstance(history, list):
        return False
    for event in history:
        if (
            isinstance(event, Mapping)
            and event.get("event") == TERMINAL_BACKING_RECEIPT_EVENT
            and event.get("task_id") == worker.get("task_id")
            and event.get("token") == worker.get("claim_token")
            and event.get("generation") == worker.get("generation")
        ):
            return True
    return False


def validate_manifest_worker_schema(manifest_or_text: Mapping[str, Any] | str) -> dict[str, Any]:
    """Validate registry sections and cross-reference their claim identities."""
    value = migrate_manifest(json.loads(manifest_or_text) if isinstance(manifest_or_text, str) else manifest_or_text)
    if not isinstance(value, dict) or not isinstance(value.get("workers"), dict):
        raise ValueError("manifest workers must be a mapping")
    capacity = value.get("capacity")
    if not isinstance(capacity, Mapping) or capacity.get("version") != REGISTRY_VERSION or not isinstance(capacity.get("entries"), dict):
        raise ValueError("manifest capacity schema is invalid")
    claims = value.get("claims", {})
    if not isinstance(claims, Mapping):
        raise ValueError("manifest claims must be a mapping")
    sessions: set[str] = set()
    capacity_ids: set[str] = set()
    capacity_workers: set[str] = set()
    workers: dict[str, Mapping[str, Any]] = value["workers"]
    for worker_id, worker in workers.items():
        if not isinstance(worker, Mapping) or worker.get("worker_id") != worker_id:
            raise ValueError("worker identity does not match manifest key")
        for field in ("task_id", "claim_token", "claim_owner_id", "provider_session_id", "worker_id", "command_identity", "launch_id", "capacity_entry_id"):
            _text(worker.get(field), f"worker {worker_id}.{field}")
        _nonnegative(worker.get("generation"), f"worker {worker_id}.generation")
        if worker.get("state") not in WORKER_STATES:
            raise ValueError(f"unknown worker state: {worker.get('state')}")
        if worker["provider_session_id"] in sessions:
            raise ValueError("provider session identity collision")
        sessions.add(worker["provider_session_id"])
        if worker["capacity_entry_id"] in capacity_ids:
            raise ValueError("capacity entry identity collision")
        capacity_ids.add(worker["capacity_entry_id"])
        claim = claims.get(worker["task_id"])
        if not isinstance(claim, Mapping):
            raise ValueError("worker claim is missing")
        identity_matches = (
            claim.get("token", claim.get("claim_token")) == worker["claim_token"]
            and claim.get("generation") == worker["generation"]
            and claim.get("owner", claim.get("claim_owner_id")) == worker["claim_owner_id"]
        )
        if worker["state"] != "terminal" and not identity_matches:
            raise ValueError("worker claim identity does not match claim")
        _process_identity(worker.get("process_identity"), f"worker {worker_id}.process_identity")
        if worker["state"] == "terminal" and not worker.get("terminal_reason"):
            raise ValueError("terminal worker requires terminal reason")
        if worker["state"] == "terminal" and not isinstance(worker.get("last_receipt"), Mapping):
            raise ValueError("terminal worker requires last receipt")
        if worker["state"] == "terminal" and not isinstance(worker.get("receipt_metadata"), Mapping):
            raise ValueError("terminal worker requires receipt metadata")
        if worker["state"] == "terminal" and (not worker["receipt_metadata"].get("receipt_id") or not isinstance(worker["receipt_metadata"].get("observed_at"), (int, float)) or isinstance(worker["receipt_metadata"].get("observed_at"), bool) or not isinstance(worker["receipt_metadata"].get("proof"), Mapping)):
            raise ValueError("terminal receipt metadata is incomplete")
        if worker["state"] == "terminal" and any(
            worker["receipt_metadata"].get(receipt_field) != worker[worker_field]
            for receipt_field, worker_field in (
                ("task_id", "task_id"),
                ("claim_token", "claim_token"),
                ("claim_owner_id", "claim_owner_id"),
                ("generation", "generation"),
                ("worker_id", "worker_id"),
                ("provider_session_id", "provider_session_id"),
            )
        ):
            raise ValueError("terminal worker receipt identity does not match worker")
        if worker["state"] == "terminal" and worker["last_receipt"].get("receipt_id") != worker["receipt_metadata"].get("receipt_id"):
            raise ValueError("terminal worker receipt identity does not match worker")
        if worker["state"] == "terminal" and not identity_matches and not _terminal_receipt_backed(value, worker):
            # A historical terminal record whose identity no longer matches
            # its task's claim is accepted only when a done-pending-recovery
            # receipt backs the rotation (the exact closed-claim + receipt
            # tuple); without that receipt the manifest is the unusable
            # orphaned-record shape and the next launch must refuse it.
            raise ValueError("worker claim identity does not match claim")
        group_id = claim.get("group_id") if isinstance(claim, Mapping) else None
        if group_id is not None:
            groups = value.get("claim_groups", {})
            group = groups.get(group_id) if isinstance(groups, Mapping) else None
            if not isinstance(group, Mapping) or worker["task_id"] not in group.get("members", ()):
                raise ValueError("worker claim is not a member of its claim group")
        entry = capacity["entries"].get(worker["capacity_entry_id"])
        if not isinstance(entry, Mapping) or entry.get("worker_id") != worker_id:
            raise ValueError("worker capacity contribution is missing or mismatched")
        expected_capacity = {
            "active": (True, "live"),
            "terminal": (False, "released"),
            "quarantined": (True, "quarantined"),
        }[worker["state"]]
        if (entry.get("counts_toward_capacity"), entry.get("state")) != expected_capacity:
            raise ValueError("worker state and capacity contribution disagree")
    for entry_id, entry in capacity["entries"].items():
        if not isinstance(entry, Mapping) or entry.get("capacity_entry_id") != entry_id:
            raise ValueError("capacity entry identity does not match manifest key")
        _text(entry.get("worker_id"), f"capacity {entry_id}.worker_id")
        if entry["worker_id"] in capacity_workers:
            raise ValueError("worker has duplicate capacity contributions")
        capacity_workers.add(entry["worker_id"])
        if not isinstance(entry.get("counts_toward_capacity"), bool):
            raise ValueError("capacity contribution must be boolean")
        if entry["worker_id"] not in workers:
            raise ValueError("capacity entry references an unknown worker")
    return value


class WorkerRegistry:
    """In-memory reducer for worker and capacity manifest sections."""

    liveness_window = 900.0

    def __init__(self, manifest: Mapping[str, Any]):
        self.manifest = migrate_manifest(manifest)
        validate_manifest_worker_schema(self.manifest)

    def worker(self, worker_id: str) -> dict[str, Any]:
        return self.manifest["workers"][worker_id]

    def active_workers(self) -> list[dict[str, Any]]:
        return [worker for worker in self.manifest["workers"].values() if worker["state"] == "active"]

    def capacity_entry(self, entry_id: str) -> dict[str, Any]:
        return self.manifest["capacity"]["entries"][entry_id]

    def capacity_witness(self) -> dict[str, Any]:
        entries = self.manifest["capacity"]["entries"]
        live = sum(1 for entry in entries.values() if entry.get("counts_toward_capacity") and entry.get("state") == "live")
        quarantined = any(worker.get("state") == "quarantined" for worker in self.manifest["workers"].values())
        return {"version": REGISTRY_VERSION, "live_workers": live, "entries": copy.deepcopy(entries), "launch_available": live == 0 and not quarantined, "quarantined": quarantined}

    def transition_count(self, worker_id: str) -> int:
        return sum(1 for item in self.manifest.get("history", []) if item.get("worker_id") == worker_id and item.get("event") == "worker-terminal")

    def register_launch(self, **fields: Any) -> dict[str, Any]:
        try:
            required = ("task_id", "claim_token", "claim_owner_id", "provider_session_id", "worker_id", "command_identity", "launch_id", "capacity_entry_id")
            for name in required:
                _text(fields.get(name), name)
            generation = _nonnegative(fields.get("generation"), "generation")
            _process_identity(fields.get("process_identity"), "process_identity")
            if fields["worker_id"] in self.manifest["workers"]:
                return {"status": "refused", "reason": "identity-collision"}
            claim = self.manifest.get("claims", {}).get(fields["task_id"])
            if not isinstance(claim, Mapping):
                return {"status": "refused", "reason": "claim-fence"}
            if (
                claim.get("token", claim.get("claim_token")) != fields["claim_token"]
                or claim.get("generation") != generation
                or claim.get("owner", claim.get("claim_owner_id")) != fields["claim_owner_id"]
            ):
                return {"status": "refused", "reason": "claim-fence"}
            if any(worker.get("provider_session_id") == fields["provider_session_id"] for worker in self.manifest["workers"].values()):
                return {"status": "refused", "reason": "identity-collision"}
            if fields["capacity_entry_id"] in self.manifest["capacity"]["entries"]:
                return {"status": "refused", "reason": "identity-collision"}
            worker = {key: fields[key] for key in required} | {"process_identity": copy.deepcopy(fields["process_identity"]), "generation": generation, "state": "active", "started_at": fields.get("started_at", time.time()), "last_receipt": None, "terminal_reason": None, "reconciliation": {"status": "available"}}
            entry = {"capacity_entry_id": fields["capacity_entry_id"], "worker_id": fields["worker_id"], "counts_toward_capacity": True, "state": "live"}
            candidate = copy.deepcopy(self.manifest)
            candidate["workers"][fields["worker_id"]] = worker
            candidate["capacity"]["entries"][fields["capacity_entry_id"]] = entry
            validate_manifest_worker_schema(candidate)
            self.manifest = candidate
            return copy.deepcopy(worker)
        except (TypeError, ValueError, KeyError) as exc:
            return {"status": "refused", "reason": str(exc)}

    def _identity_matches(self, receipt: Mapping[str, Any], worker: Mapping[str, Any]) -> bool:
        return all(receipt.get(a) == worker.get(b) for a, b in (("task_id", "task_id"), ("claim_token", "claim_token"), ("claim_owner_id", "claim_owner_id"), ("generation", "generation"), ("worker_id", "worker_id"), ("provider_session_id", "provider_session_id")))

    def apply_terminal_receipt(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        return self.apply_lifecycle_event("terminal", receipt)

    def apply_close_result(self, receipt: Mapping[str, Any], outcome: str) -> dict[str, Any]:
        value = dict(receipt)
        value["outcome"] = outcome
        event = "close" if outcome != "not_found" else "not_found"
        value["event"] = event
        return self.apply_lifecycle_event(event, value)

    def apply_lifecycle_event(self, event: str, receipt: Mapping[str, Any]) -> dict[str, Any]:
        required = ("task_id", "claim_token", "claim_owner_id", "generation", "worker_id", "provider_session_id", "event", "observed_at", "reason")
        if event not in {"terminal", "timeout", "shutdown", "close", "not_found", "replay", "late"} or not isinstance(receipt, Mapping):
            return {"status": "refused", "outcome": "refused", "reason": "malformed-lifecycle-receipt"}
        if any(key not in receipt for key in required) or receipt.get("event") != event:
            return {"status": "refused", "outcome": "refused", "reason": "malformed-lifecycle-receipt"}
        try:
            _text(receipt.get("receipt_id"), "receipt_id")
            for key in ("task_id", "claim_token", "claim_owner_id", "worker_id", "provider_session_id", "reason"):
                _text(receipt.get(key), key)
            _nonnegative(receipt.get("generation"), "generation")
            observed_at = receipt.get("observed_at")
            if not isinstance(observed_at, (int, float)) or isinstance(observed_at, bool):
                raise ValueError("observed_at must be numeric")
        except (TypeError, ValueError):
            return {"status": "refused", "outcome": "refused", "reason": "malformed-lifecycle-receipt"}
        worker_id = receipt.get("worker_id")
        worker = self.manifest["workers"].get(worker_id)
        if not isinstance(worker, Mapping) or not self._identity_matches(receipt, worker):
            return {"status": "refused", "outcome": "refused", "reason": "identity-mismatch"}
        if worker["state"] == "terminal":
            if event == "replay":
                return {"status": "success", "outcome": "replayed", "receipt_id": receipt.get("receipt_id")}
            if receipt.get("receipt_id") == (worker.get("last_receipt") or {}).get("receipt_id"):
                return copy.deepcopy(worker["last_receipt"])
            return {"status": "success", "outcome": "already-closed", "receipt_id": receipt.get("receipt_id")}
        proof = receipt.get("proof")
        expected_proof_kind = {"terminal": "provider-terminal", "close": "provider-close"}.get(event)
        proven = (
            expected_proof_kind is not None
            and isinstance(proof, Mapping)
            and proof.get("verified") is True
            and proof.get("kind") == expected_proof_kind
        )
        if worker["state"] == "quarantined" and not proven:
            return {"status": "refused", "outcome": "quarantined", "reason": "cleanup-unverified"}
        if event == "late":
            worker["state"] = "quarantined"
            worker["reconciliation"] = {"status": "quarantined", "reason": "late-receipt"}
            self.capacity_entry(worker["capacity_entry_id"])["state"] = "quarantined"
            return {"status": "refused", "outcome": "quarantined", "reason": "late-receipt"}
        if event in {"terminal", "close"} and (not receipt.get("receipt_id") or not isinstance(receipt.get("observed_at"), (int, float)) or isinstance(receipt.get("observed_at"), bool)):
            return {"status": "refused", "outcome": "refused", "reason": "terminal-receipt-metadata-required"}
        if event not in {"terminal", "close"} or not proven:
            worker["state"] = "quarantined"
            worker["reconciliation"] = {"status": "quarantined", "reason": "cleanup-unverified"}
            self.manifest["capacity"]["entries"][worker["capacity_entry_id"]].update(counts_toward_capacity=True, state="quarantined")
            return {"status": "quarantined", "outcome": "quarantined", "reason": "cleanup-unverified"}
        result = {"status": "success", "outcome": "released", "receipt_id": receipt.get("receipt_id"), "event": event}
        worker["state"] = "terminal"
        worker["terminal_reason"] = receipt.get("reason") or event
        worker["last_receipt"] = copy.deepcopy(result)
        worker["receipt_metadata"] = copy.deepcopy(dict(receipt))
        worker["reconciliation"] = {"status": "terminal", "observed_at": receipt.get("observed_at")}
        self.manifest["capacity"]["entries"][worker["capacity_entry_id"]].update(counts_toward_capacity=False, state="released")
        self.manifest.setdefault("history", []).append({"event": "worker-terminal", "worker_id": worker_id, "reason": worker["terminal_reason"]})
        return result

    def reconcile(self, provider_inventory: Any, now: float | None = None, progress: Mapping[str, Any] | None = None) -> dict[str, Any]:
        def quarantine(reason: str) -> dict[str, Any]:
            for worker in self.active_workers():
                worker["state"] = "quarantined"
                worker["reconciliation"] = {"status": "unavailable", "reason": reason}
                self.capacity_entry(worker["capacity_entry_id"]).update(counts_toward_capacity=True, state="quarantined")
            return {"status": "quarantined", "reason": "capacity-unavailable"}

        if not isinstance(provider_inventory, list):
            return quarantine("capacity-unavailable")
        inventory = set()
        for item in provider_inventory:
            try:
                if not isinstance(item, Mapping) or not isinstance(item.get("provider_session_id"), str) or not item["provider_session_id"].strip():
                    raise ValueError
                _process_identity(item.get("process_identity"), "inventory.process_identity")
            except (TypeError, ValueError):
                return quarantine("capacity-unavailable")
            if item["provider_session_id"] in inventory:
                return quarantine("capacity-unavailable")
            inventory.add(item["provider_session_id"])
        for worker in self.manifest["workers"].values():
            if worker["state"] != "quarantined":
                continue
            proof = next((item for item in provider_inventory if isinstance(item, Mapping) and item.get("worker_id") == worker["worker_id"] and item.get("state") == "terminal" and isinstance(item.get("proof"), Mapping) and item["proof"].get("verified") is True), None)
            if proof is not None:
                self.apply_lifecycle_event("terminal", proof)
        timestamp = time.time() if now is None else now
        for worker in self.active_workers():
            observed = next((item for item in provider_inventory if item["provider_session_id"] == worker["provider_session_id"]), None)
            if observed is None:
                worker["state"] = "quarantined"
                worker["reconciliation"] = {"status": "stale", "reason": "stale-inventory"}
                self.capacity_entry(worker["capacity_entry_id"])["state"] = "quarantined"
            elif observed["process_identity"] != worker["process_identity"]:
                worker["state"] = "quarantined"
                worker["reconciliation"] = {"status": "stale", "reason": "process-identity-mismatch"}
                self.capacity_entry(worker["capacity_entry_id"])["state"] = "quarantined"
            elif timestamp - float(worker.get("started_at", timestamp)) > self.liveness_window and not (progress or {}).get(worker["worker_id"]):
                worker["state"] = "quarantined"
                worker["reconciliation"] = {"status": "stalled", "reason": "stalled"}
                self.capacity_entry(worker["capacity_entry_id"])["state"] = "quarantined"
        if any(worker["state"] == "quarantined" for worker in self.manifest["workers"].values()):
            reason = "stalled" if any(item.get("reconciliation", {}).get("status") == "stalled" for item in self.manifest["workers"].values()) else "stale-inventory"
            return {"status": "stalled" if reason == "stalled" else "quarantined", "reason": reason, "recovery_action": "recovery-receipt-or-relaunch" if reason == "stalled" else "reconcile-provider-inventory"}
        return {"status": "available", "reason": "reconciled"}

    def apply_observation(self, observation: Mapping[str, Any], *, now: float) -> dict[str, Any]:
        """Map one neutral observation to a safe capacity transition."""
        envelope = validate_provider_observation(observation, now=now)
        if envelope.get("state") == "available":
            return self.reconcile(envelope.get("inventory"), now=now)
        if envelope.get("state") == "terminal":
            released = []
            for item in envelope.get("inventory", []):
                if not isinstance(item, Mapping) or item.get("state") != "terminal" or not isinstance(item.get("proof"), Mapping) or item["proof"].get("verified") is not True:
                    continue
                result = self.apply_lifecycle_event("terminal", item)
                if result.get("outcome") == "released":
                    released.append(item.get("worker_id"))
            return {"status": "available" if released else "quarantined", "reason": "terminal-observation", "released_workers": released}
        reason = envelope.get("state", "malformed")
        for worker in self.active_workers():
            worker["state"] = "quarantined"
            worker["reconciliation"] = {"status": reason, "reason": reason}
            self.capacity_entry(worker["capacity_entry_id"]).update(counts_toward_capacity=True, state="quarantined")
        return {"status": "quarantined", "reason": reason}

    def checkpoint(self, task_id: str, *, claim_token: str, generation: int) -> dict[str, Any]:
        claim = self.manifest.get("claims", {}).get(task_id)
        if not isinstance(claim, Mapping) or claim.get("token", claim.get("claim_token")) != claim_token or claim.get("generation") != generation:
            return {"status": "refused", "reason": "claim-fence"}
        return {"status": "checkpointed", "task_id": task_id, "generation": generation}

    def resume(self, task_id: str, *, claim_token: str, generation: int) -> dict[str, Any]:
        result = self.checkpoint(task_id, claim_token=(claim_token), generation=generation)
        if result["status"] == "refused":
            return result
        return {"status": "resumable", "task_id": task_id, "generation": generation}
