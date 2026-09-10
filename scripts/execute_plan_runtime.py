#!/usr/bin/env python3
"""Durable, provider-neutral continuation driver for execute-plan.

The driver owns the file-backed state machine and policy boundary. Host-specific
process and session handling belongs in an adapter such as
``execute_plan_runtime_codex``.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

import runtime_capabilities as capabilities


STATUSES = {"success", "contract-violation", "blocked", "aborted", "error"}
MAX_EVIDENCE_BYTES = 4096
MAX_EVIDENCE_ITEM_BYTES = 512
SCHEMA_VERSION = 1
ALLOWED_OPERATION_KINDS = {
    "repository-task",
    "repository-read",
    "repository-write",
    "done-handoff",
    "checkpoint",
}
GATED_OPERATION_KINDS = {
    "access-change",
    "deploy",
    "external-communication",
    "merge",
    "push",
}
SHELL_MARKERS = (";", "&&", "||", "|", "`", "$(", "${", "\n", "\r")
_LOCK_LOCAL = threading.local()


@dataclass(frozen=True)
class ActionEnvelope:
    """Typed policy input issued to an adapter for one repository operation."""

    repo_root: str
    allowed_paths: tuple[str, ...]
    operation_kind: str
    network: bool
    evidence: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ActionEnvelope":
        if not isinstance(value, Mapping):
            raise ValueError("action envelope must be a mapping")
        allowed_paths = value.get("allowed_paths", ())
        evidence = value.get("evidence", ())
        if isinstance(allowed_paths, str) or not isinstance(allowed_paths, (list, tuple)):
            raise ValueError("action envelope allowed_paths must be a sequence")
        if isinstance(evidence, str) or not isinstance(evidence, (list, tuple)):
            raise ValueError("action envelope evidence must be a sequence")
        if not isinstance(value.get("network"), bool):
            raise ValueError("action envelope network must be boolean")
        return cls(
            repo_root=str(value.get("repo_root", "")),
            allowed_paths=tuple(str(path) for path in allowed_paths),
            operation_kind=str(value.get("operation_kind", "")),
            network=value.get("network") is True,
            evidence=tuple(str(item) for item in evidence),
        )


def _safe_relative_path(repo_root: Path, value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("path must be non-empty and NUL-free")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("path escapes repository root")
    if any(marker in value for marker in SHELL_MARKERS) or value.startswith(("~", "-")):
        raise ValueError("path contains an unsafe shell or option marker")
    resolved = (repo_root / candidate).resolve()
    if resolved != repo_root and repo_root not in resolved.parents:
        raise ValueError("path escapes repository root")
    return resolved.relative_to(repo_root).as_posix()


def validate_action_envelope(
    envelope: ActionEnvelope | Mapping[str, Any], expected_repo_root: Path | str
) -> ActionEnvelope:
    """Canonicalize a typed envelope and reject unsafe policy inputs."""

    value = envelope if isinstance(envelope, ActionEnvelope) else ActionEnvelope.from_mapping(envelope)
    repo_root = Path(expected_repo_root).resolve()
    declared_root = Path(value.repo_root).resolve()
    if declared_root != repo_root:
        raise ValueError("action envelope repository root is not canonical")
    if value.operation_kind not in ALLOWED_OPERATION_KINDS:
        raise ValueError("operation kind is not repository-scoped")
    if value.network:
        raise ValueError("network actions are denied by default")
    if not value.evidence or any(not item.strip() for item in value.evidence):
        raise ValueError("action envelope needs non-empty evidence")
    paths = tuple(_safe_relative_path(repo_root, path) for path in value.allowed_paths)
    if not paths:
        # Empty scope is the widest possible scope; fail closed instead of
        # authorizing a task whose witness can never be satisfied.
        raise ValueError("action envelope requires non-empty allowed_paths")
    return ActionEnvelope(str(repo_root), paths, value.operation_kind, False, value.evidence)


def _now() -> float:
    return time.time()


def _redact(value: str) -> str:
    value = re.sub(r"(?i)(token|password|secret|api[_-]?key)[\"']?\s*[:=]\s*[\"']?([^\s,;\"'}]+)", r"\1=<redacted>", value)
    value = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer <redacted>", value)
    return value


def bounded_evidence(items: Any, limit: int = MAX_EVIDENCE_BYTES) -> list[str]:
    """Return bounded, redacted evidence suitable for durable state."""

    if isinstance(items, str):
        items = [items]
    if not isinstance(items, (list, tuple)):
        items = [repr(items)]
    result: list[str] = []
    used = 0
    for item in items:
        text = _redact(str(item))[:MAX_EVIDENCE_ITEM_BYTES]
        remaining = limit - used
        if remaining <= 0:
            break
        text = text[:remaining]
        if text:
            result.append(text)
            used += len(text)
    return result or ["evidence unavailable"]


def _safe_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_manifest(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    with manifest_path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported runtime manifest")
    if not isinstance(value.get("tasks"), dict):
        raise ValueError("runtime manifest tasks must be a mapping")
    return value


def create_manifest(
    path: Path | str,
    plan_slug: str,
    tasks: list[Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
    profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the authoritative machine manifest with restrictive permissions."""

    if isinstance(tasks, Mapping):
        task_items = tasks.items()
    else:
        task_items = ((str(task["id"]), task) for task in tasks)
    task_map: dict[str, dict[str, Any]] = {}
    for task_id, task in task_items:
        item = dict(task)
        item.setdefault("id", task_id)
        item.setdefault("status", "pending")
        item.setdefault("checkbox", item["status"] == "complete")
        task_map[str(task_id)] = item
    profile = profile or {}
    capabilities_data = dict(profile.get("capabilities", {}))
    capability_receipts = {
        name: {
            "state": capabilities_data.get(name, "unsupported"),
            "fallback": profile.get("fallback", "No runtime profile was selected; use explicit operator recovery."),
        }
        for name in ("parent_continuation", "final_response", "resume")
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "plan_slug": plan_slug,
        "generation": 0,
        "workflow_state": "active",
        "created_at": _now(),
        "updated_at": _now(),
        "tasks": task_map,
        "claims": {},
        "checkpoints": {},
        "capabilities": capability_receipts,
        "history": [],
    }
    _safe_write_json(Path(path), manifest)
    return manifest


@contextlib.contextmanager
def _manifest_lock(path: Path, owner: str) -> Iterator[bool]:
    """Use an advisory lock whose kernel lease survives stale lock files."""

    lock_path = Path(f"{path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    held = getattr(_LOCK_LOCAL, "held", set())
    if key in held:
        yield True
        return
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            yield False
            return
        os.ftruncate(fd, 0)
        os.write(fd, f"{owner}\n".encode())
        os.fsync(fd)
        held.add(key)
        _LOCK_LOCAL.held = held
        yield True
    finally:
        if acquired:
            held.discard(key)
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _locked_mutation(method: Callable[..., Any]) -> Callable[..., Any]:
    """Fence a read-modify-write transition with the manifest lock."""

    def wrapped(self: "RuntimeDriver", *args: Any, **kwargs: Any) -> Any:
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                manifest = load_manifest(self.manifest_path)
                return _outcome("blocked", "stale-claim", ["manifest mutation is held by another owner"], "repository-task", "mutation:conflict", manifest.get("generation", 0), "resumable-conflict")
            return method(self, *args, **kwargs)

    wrapped.__name__ = method.__name__
    return wrapped


def _outcome(
    status: str,
    reason_code: str,
    evidence: Any,
    action_scope: str,
    checkpoint_identity: str,
    generation: int,
    recovery_action: str,
    retry_policy: Mapping[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"invalid runtime status: {status}")
    default_resume = status == "blocked" and reason_code in capabilities.RESUMABLE_REASONS
    return {
        "status": status,
        "reason_code": reason_code,
        "evidence": bounded_evidence(evidence),
        "action_scope": action_scope,
        "checkpoint_identity": checkpoint_identity,
        "generation": generation,
        "retry_policy": dict(retry_policy or {"mode": "none", "max_attempts": 0, "attempts_remaining": 0}),
        "recovery_action": recovery_action,
        "resume_allowed": bool(extra.pop("resume_allowed", default_resume)),
        **extra,
    }


class RuntimeDriver:
    """Own durable task transitions; never owns commits."""

    def __init__(
        self,
        manifest_path: Path | str,
        plan_slug: str | None = None,
        adapter: Any | None = None,
        profile: Mapping[str, Any] | None = None,
        owner: str | None = None,
        repo_root: Path | str | None = None,
        commit_lookup: Callable[[str], bool] | None = None,
        clock: Callable[[], float] = _now,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.adapter = adapter
        self.profile = profile or {}
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.commit_lookup = commit_lookup or self._git_commit_exists
        self.clock = clock
        manifest = load_manifest(self.manifest_path)
        manifest_owner = manifest.get("owner")
        if owner is not None:
            self.owner = owner
        elif isinstance(manifest_owner, str) and manifest_owner.strip():
            # Derive the owner from the machine manifest so separate driver
            # processes sharing one manifest also share one owner identity.
            self.owner = manifest_owner
        else:
            self.owner = f"runtime-{uuid.uuid4().hex}"
        if plan_slug and manifest.get("plan_slug") != plan_slug:
            raise ValueError("manifest plan slug mismatch")
        self.plan_slug = str(manifest["plan_slug"])
        self._refresh_capability_receipts()

    def _refresh_capability_receipts(self) -> None:
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return
            manifest = load_manifest(self.manifest_path)
            manifest.setdefault("owner", self.owner)
            capabilities_data = dict(self.profile.get("capabilities", {}))
            receipts = manifest.setdefault("capabilities", {})
            fallback = self.profile.get("fallback", "Use the durable receipt and parent continuation.")
            for name in ("parent_continuation", "final_response", "resume"):
                state = capabilities_data.get(name, "unsupported")
                receipts[name] = {"state": state, "fallback": fallback}
            self._save(manifest)

    def _save(self, manifest: dict[str, Any]) -> None:
        manifest["updated_at"] = self.clock()
        _safe_write_json(self.manifest_path, manifest)

    @staticmethod
    def _task_id_from_checkpoint(identity: str) -> str:
        return identity.split(":", 1)[0]

    @staticmethod
    def _task_complete(task: Mapping[str, Any]) -> bool:
        return task.get("status") in {"complete", "checkpointed"} or bool(task.get("checkbox"))

    def _result_error(self, message: str, generation: int | None = None, action_scope: str = "runtime", checkpoint_identity: str = "runtime:malformed") -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        return _outcome("blocked", "malformed-result", [message], action_scope, checkpoint_identity, manifest.get("generation", 0) if generation is None else generation, "preserve-and-reconcile")

    def validate_manifest(self, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Validate the authoritative machine state before selecting work."""

        value = dict(manifest or load_manifest(self.manifest_path))
        if value.get("workflow_state") not in {"active", "blocked", "complete", "terminal", "aborted"}:
            raise ValueError("invalid workflow state")
        if not isinstance(value.get("generation"), int) or value["generation"] < 0:
            raise ValueError("manifest generation must be non-negative")
        task_states = {"pending", "claimed", "launched", "blocked", "done-pending", "commit-pending", "checkpointed", "complete", "aborted"}
        claim_states = {"claimed", "launched", "blocked", "closed", "aborted", "replaced"}
        for task_id, task in value["tasks"].items():
            if not isinstance(task, Mapping) or task.get("id", task_id) != task_id:
                raise ValueError("task identity does not match manifest key")
            if task.get("status") not in task_states:
                raise ValueError(f"unknown task status: {task.get('status')}")
        if not isinstance(value.get("claims"), dict) or not isinstance(value.get("checkpoints"), dict):
            raise ValueError("manifest claims and checkpoints must be mappings")
        for task_id, claim in value["claims"].items():
            if not isinstance(claim, Mapping) or claim.get("task_id") != task_id:
                raise ValueError("claim identity does not match manifest key")
            if claim.get("state") not in claim_states:
                raise ValueError(f"unknown claim state: {claim.get('state')}")
            for field in ("token", "owner"):
                if not isinstance(claim.get(field), str) or not claim[field].strip():
                    raise ValueError(f"claim {field} is required")
            if not isinstance(claim.get("generation"), int) or claim["generation"] < 0:
                raise ValueError("claim generation must be non-negative")
            if task_id not in value["tasks"]:
                raise ValueError("claim references an unknown task")
        return value

    def refresh_manifest(self) -> dict[str, Any]:
        """Reload and validate machine state after every parent checkpoint."""

        return self.validate_manifest(load_manifest(self.manifest_path))

    def _policy_block(self, reason: str, evidence: list[str], generation: int) -> dict[str, Any]:
        return _outcome(
            "blocked",
            reason,
            evidence,
            "repository-task",
            "policy:authorization",
            generation,
            "preserve-and-reconcile" if reason != "approval-required" else "preserve-and-await-approval",
        )

    def authorize_envelope(
        self, envelope: ActionEnvelope | Mapping[str, Any], generation: int
    ) -> dict[str, Any]:
        """Issue an opaque adapter token only for a validated local operation."""

        try:
            normalized = validate_action_envelope(envelope, self.repo_root)
        except (TypeError, ValueError) as exc:
            return self._policy_block("approval-required", [str(exc)], generation)
        token = {
            "token": uuid.uuid4().hex,
            "repo_root": normalized.repo_root,
            "allowed_paths": list(normalized.allowed_paths),
            "operation_kind": normalized.operation_kind,
            "network": normalized.network,
            "evidence": list(normalized.evidence),
            "generation": generation,
        }
        return _outcome(
            "success",
            "authorized",
            list(normalized.evidence),
            normalized.operation_kind,
            "policy:authorization",
            generation,
            "continue-parent",
            policy_token=token,
        )

    def authorize_action(self, action_scope: str, path: str | None = None) -> dict[str, Any]:
        """Default-deny operations outside repository-local continuation."""

        scope = str(action_scope or "")
        lowered = scope.lower()
        generation = load_manifest(self.manifest_path).get("generation", 0)
        if scope in GATED_OPERATION_KINDS or any(term in lowered for term in GATED_OPERATION_KINDS):
            return self._policy_block("approval-required", [f"action_scope={scope}"], generation)
        if scope not in ALLOWED_OPERATION_KINDS and not scope.startswith("repository-task:"):
            return self._policy_block("approval-required", [f"action_scope={scope}"], generation)
        if path is None:
            # Scope-class check only: no concrete target means there is no
            # path-level scope to authorize, and an empty allowed_paths
            # envelope would fail closed by design.
            return _outcome("success", "authorized", [f"action_scope={scope}"], scope, "policy:authorization", generation, "continue-parent")
        envelope = ActionEnvelope(
            str(self.repo_root),
            (path,) if path else (),
            "repository-task" if scope.startswith("repository-task:") else scope,
            False,
            (f"action_scope={scope}",),
        )
        result = self.authorize_envelope(envelope, generation)
        result["action_scope"] = scope
        return result

    def validate_adapter_result(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            return self._result_error("adapter result must be a mapping")
        manifest = load_manifest(self.manifest_path)
        generation = manifest.get("generation", 0)
        try:
            if raw.get("adapter_version") not in (None, self.profile.get("adapter_version", "1.0")):
                return self._result_error("incompatible adapter version", generation)
            result = capabilities.normalize_result(raw, int(self.profile.get("retry_budget", 2)))
            result["evidence"] = bounded_evidence(result["evidence"])
            result["resume_allowed"] = bool(result["resume_allowed"])
            if result["action_scope"].startswith("external") or not self.authorize_action(result["action_scope"])["status"] == "success":
                return _outcome("blocked", "approval-required", result["evidence"] + [result["action_scope"], f"action_scope={result['action_scope']}"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-await-approval")
            task_id = self._task_id_from_checkpoint(result["checkpoint_identity"])
            claim = manifest.get("claims", {}).get(task_id, {})
            policy_token = claim.get("policy_token", {})
            allowed_paths = set(policy_token.get("allowed_paths", []))
            for action in raw.get("actions", []):
                if not isinstance(action, Mapping):
                    return _outcome("blocked", "contract-violation", ["adapter action must be a mapping"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
                operation = str(action.get("operation", ""))
                target = str(action.get("target", action.get("path", "")))
                lowered = f"{operation} {target}".lower()
                if operation in {"shell", "command", "exec", "network", "push", "deploy", "merge"} or any(marker in lowered for marker in SHELL_MARKERS):
                    return _outcome("blocked", "contract-violation", [f"post-launch action={operation}", f"target={target}"], operation or "unknown", result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
                if target:
                    try:
                        normalized_target = _safe_relative_path(self.repo_root, target)
                    except ValueError as exc:
                        return _outcome("blocked", "contract-violation", [str(exc), f"target={target}"], operation or "unknown", result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
                    if not allowed_paths or normalized_target not in allowed_paths:
                        return _outcome("blocked", "contract-violation", [f"unlisted path={normalized_target}"], operation or "unknown", result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
                if self.authorize_action(operation, target or None)["status"] != "success":
                    return _outcome("blocked", "contract-violation", [f"post-launch action={operation}"], operation or "unknown", result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
            return result
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            checkpoint = str(raw.get("checkpoint_identity") or "runtime:malformed")
            return self._result_error(str(exc), generation, checkpoint_identity=checkpoint)

    def _persist_blocked_claim(
        self,
        claim: Mapping[str, Any],
        result: Mapping[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        task_id = task_id or str(claim.get("task_id", ""))
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            manifest = load_manifest(self.manifest_path)
            current_claim = manifest.get("claims", {}).get(task_id)
            if not acquired or not current_claim or current_claim.get("token") != claim.get("token") or current_claim.get("generation") != claim.get("generation"):
                return _outcome(
                    "blocked",
                    "owner-mismatch",
                    ["claim changed before blocked receipt"],
                    "repository-task",
                    str(claim.get("token", "claim")),
                    int(claim.get("generation", manifest.get("generation", 0))),
                    "preserve-and-reconcile",
                )
            task = manifest.get("tasks", {}).get(task_id)
            if task is not None:
                task["status"] = "blocked"
                task["resume_allowed"] = bool(result.get("resume_allowed", False))
                task["blocked_receipt"] = dict(result)
                if result.get("session_id"):
                    task["session_id"] = str(result["session_id"])
            current_claim["state"] = "blocked"
            manifest["history"].append({"event": "worker-blocked", "task_id": task_id, "reason_code": result.get("reason_code", "malformed-result")})
            self._save(manifest)
        return dict(result)

    def _invoke_adapter_launch(
        self,
        claim: Mapping[str, Any],
        task: Mapping[str, Any],
        prompt: str,
        deadline_seconds: float | None,
        policy_token: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            raw = self.adapter.launch(
                task,
                prompt,
                claim["generation"],
                deadline_seconds=deadline_seconds,
                policy_token=policy_token,
            )
        except TimeoutError:
            return _outcome("blocked", "timeout", ["launch deadline exceeded"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=True)
        except TypeError as exc:
            return _outcome("blocked", "runtime-policy-unavailable", [f"adapter rejected policy token: {exc}"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        except Exception as exc:
            return _outcome("error", "runtime-error", [type(exc).__name__], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        if not isinstance(raw, Mapping):
            return _outcome("blocked", "malformed-result", ["adapter returned a non-mapping result"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        raw = dict(raw)
        raw["claim_token"] = claim["token"]
        return raw

    @_locked_mutation
    def record_worker_checkpoint(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        result = self.validate_adapter_result(raw)
        manifest = load_manifest(self.manifest_path)
        task_id = self._task_id_from_checkpoint(result["checkpoint_identity"])
        claim = manifest.get("claims", {}).get(task_id)
        claim_token = raw.get("claim_token")
        if not claim or claim.get("owner") != self.owner or claim.get("token") != claim_token or claim.get("generation") != result["generation"]:
            return _outcome(
                "blocked",
                "owner-mismatch",
                ["checkpoint receipt does not match a live claim"],
                "repository-task",
                result["checkpoint_identity"],
                result["generation"],
                "preserve-and-reconcile",
            )
        if result["status"] != "success":
            if result["reason_code"] == "worker-hesitation":
                result["recovery_action"] = "rewrite-and-retry"
                result["contract_rule"] = "worker must not ask conversational permission for authorized repository work"
            elif result["status"] == "contract-violation":
                result["contract_rule"] = str(raw.get("contract_rule") or "adapter result violated the typed action contract")
            task = manifest["tasks"].get(task_id)
            retry = result.get("retry_policy", {})
            retryable = (
                result["status"] == "contract-violation" and retry.get("mode") == "rewrite-and-retry"
            ) or (result["status"] == "error" and retry.get("mode") == "bounded")
            if retryable and retry.get("attempts_remaining", 0) > 0 and self.adapter is not None:
                retry["attempts_remaining"] = int(retry["attempts_remaining"]) - 1
                # A failed attempt must not poison the stable checkpoint
                # identity: record it under a distinct attempt identity so the
                # retry can still land the real checkpoint.
                manifest["checkpoints"][f"{result['checkpoint_identity']}#attempt-initial"] = {"result": result, "task_id": task_id, "attempt": "initial"}
                manifest["history"].append({"event": "worker-retry", "task_id": task_id, "generation": result["generation"], "reason_code": result["reason_code"], "attempts_remaining": retry["attempts_remaining"]})
                task["status"] = "launched"
                self._save(manifest)
                retry_raw = self._invoke_adapter_launch(
                    claim,
                    task,
                    "Rewrite the authorized repository task and return a structured result.",
                    None,
                    claim.get("policy_token", {}),
                )
                # The driver owns the retry budget: override any worker- or
                # adapter-supplied policy with the decremented budget so a
                # hostile envelope cannot re-supply attempts each round.
                retry_raw["retry_policy"] = retry
                return self.record_worker_checkpoint(retry_raw)
            if task and not self._task_complete(task):
                task["status"] = "blocked"
                task["resume_allowed"] = result["reason_code"] in capabilities.RESUMABLE_REASONS
                task["blocked_receipt"] = result
                if raw.get("session_id"):
                    task["session_id"] = str(raw["session_id"])
                claim["state"] = "blocked"
                manifest["history"].append({"event": "worker-blocked", "task_id": task_id, "reason_code": result["reason_code"]})
                self._save(manifest)
            return result
        manifest = load_manifest(self.manifest_path)
        # Re-fetch task and claim from the freshly loaded snapshot: objects
        # fetched before this reload belong to a stale manifest and writes to
        # them would be silently lost on save.
        identity = result["checkpoint_identity"]
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id)
        if claim is None or claim.get("owner") != self.owner or claim.get("token") != claim_token or claim.get("generation") != result["generation"]:
            return _outcome("blocked", "owner-mismatch", ["checkpoint receipt does not match a live claim"], "repository-task", identity, result["generation"], "preserve-and-reconcile")
        prior = manifest["checkpoints"].get(identity)
        if prior is not None and prior.get("result", {}).get("status") == "success":
            return {**result, "state": "done-pending", "duplicate": True, "actions": []}
        if task is None:
            return self._result_error(f"unknown checkpoint task: {task_id}", result["generation"])
        if claim.get("state") not in {"claimed", "launched", "blocked"}:
            return _outcome("blocked", "owner-mismatch", ["checkpoint claim is not live"], "repository-task", identity, result["generation"], "preserve-and-reconcile")
        verdict, unexpected = self._worktree_scope_violation(claim)
        if verdict == "unavailable":
            return _outcome("blocked", "worktree-witness-unavailable", ["git diff scope witness failed"], "repository-task", identity, result["generation"], "preserve-and-reconcile", resume_allowed=False)
        if verdict == "violation":
            violation = _outcome("blocked", "contract-violation", [f"out-of-scope change: {path}" for path in unexpected], "repository-task", identity, result["generation"], "preserve-and-reconcile", resume_allowed=False)
            return self._persist_blocked_claim(claim, violation, task_id)
        task["status"] = "done-pending"
        task["checkpoint_identity"] = identity
        if raw.get("session_id"):
            task["session_id"] = str(raw["session_id"])
        if claim:
            claim["state"] = "launched"
        manifest["checkpoints"][identity] = {"result": result, "task_id": task_id, "recorded_at": self.clock()}
        manifest["history"].append({"event": "worker-checkpoint", "task_id": task_id, "generation": result["generation"]})
        self._save(manifest)
        refreshed = self.refresh_manifest()
        return {**result, "state": refreshed["tasks"][task_id]["status"], "duplicate": False, "actions": []}

    @_locked_mutation
    def record_done(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        if not isinstance(raw, Mapping):
            return self._result_error("done handoff must be a mapping", action_scope="done-handoff")
        checkpoint_identity = raw.get("checkpoint_identity")
        if not isinstance(checkpoint_identity, str) or not checkpoint_identity.strip():
            return _outcome("blocked", "done-pending", ["checkpoint_identity is required before mutating state"], "done-handoff", "runtime:done", manifest.get("generation", 0), "preserve-and-reconcile")
        task_id = str(raw.get("task_id") or self._task_id_from_checkpoint(checkpoint_identity))
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id) if task else None
        if raw.get("status") != "success":
            return _outcome("blocked", "done-pending", ["successful done handoff required"], "done-handoff", str(raw.get("checkpoint_identity", f"{task_id}:done")), manifest.get("generation", 0), "preserve-and-reconcile")
        required = ("commit_identity", "log_evidence")
        valid_log = isinstance(raw.get("log_evidence"), (list, tuple)) and bool(raw.get("log_evidence")) and all(isinstance(item, str) and item.strip() for item in raw["log_evidence"])
        fenced = claim and claim.get("owner") == self.owner and claim.get("token") == raw.get("claim_token") and claim.get("generation") == raw.get("generation")
        valid = (
            task is not None
            and task.get("status") in {"done-pending", "checkpointed"}
            and fenced
            and raw.get("action_scope") == "done-handoff"
            and raw.get("checkbox") is True
            and raw.get("clean_state") is True
            and isinstance(raw.get("commit_identity"), str) and raw["commit_identity"].strip()
            and valid_log
            and len(str(raw["commit_identity"])) <= 128
            and self._task_id_from_checkpoint(checkpoint_identity) == task_id
        )
        if not valid:
            return _outcome("blocked", "done-pending", [f"missing or unfenced done evidence: {', '.join(required)}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile")
        if not self.commit_lookup(str(raw["commit_identity"])):
            return _outcome("blocked", "commit-pending", [f"commit not found: {raw['commit_identity']}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile")
        # Done-boundary verification: the committed artifact is checked, not
        # just attested. Only a claim with a recorded launch baseline can be
        # verified; the launch path fails closed when no baseline is available.
        baseline_revision = str((claim or {}).get("baseline_revision") or "").strip()
        if baseline_revision:
            commit_identity = str(raw["commit_identity"])
            allowed = set((claim.get("policy_token") or {}).get("allowed_paths", ()))
            is_descendant, witness_ok = self._git_commit_is_descendant(baseline_revision, commit_identity)
            if not witness_ok or not allowed:
                return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary git witness failed"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            if not is_descendant:
                return _outcome("blocked", "commit-pending", [f"commit is not new work on the claim baseline: {commit_identity}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            committed_paths = self._git_diff_paths(baseline_revision, commit_identity)
            if committed_paths is None:
                return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary git diff witness failed"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            out_of_scope = [path for path in committed_paths if path not in allowed]
            if out_of_scope:
                return _outcome("blocked", "commit-pending", [f"out-of-scope committed change: {path}" for path in out_of_scope], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            try:
                actually_dirty = self._git_worktree_dirty()
            except (OSError, RuntimeError):
                return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary clean-state witness failed"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            if actually_dirty:
                return _outcome("blocked", "commit-pending", ["worktree is not clean at the done boundary"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        if task.get("status") == "checkpointed" and task.get("commit_identity") == raw["commit_identity"]:
            return _outcome("success", "completed", ["duplicate done handoff"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[], duplicate=True)
        task.update({"status": "commit-pending", "commit_identity": str(raw["commit_identity"]), "done_log_evidence": bounded_evidence(raw["log_evidence"])})
        manifest["history"].append({"event": "commit-pending", "task_id": task_id, "commit_identity": str(raw["commit_identity"])})
        task.update({"status": "checkpointed", "checkbox": True, "complete": True})
        claim["state"] = "closed"
        manifest["history"].append({"event": "done-commit", "task_id": task_id, "commit_identity": str(raw["commit_identity"])})
        self._save(manifest)
        claim = self.claim_next_task()
        actions = [{"type": "launch-task", "task_id": claim["task_id"], "generation": claim["generation"]}] if claim.get("claimed") else []
        return _outcome("success", "completed", ["done commit, checkbox, clean-state, and log evidence recorded"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=actions)

    def claim_next_task(self) -> dict[str, Any]:
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            manifest = load_manifest(self.manifest_path)
            if not acquired:
                return _outcome("blocked", "stale-claim", ["manifest claim is held by another owner"], "repository-task", "claim:conflict", manifest.get("generation", 0), "resumable-conflict", claimed=False)
            pending = [task for task in manifest["tasks"].values() if not self._task_complete(task) and task.get("status") == "pending"]
            pending.sort(key=lambda task: (task.get("number", 0), task.get("id", "")))
            if not pending:
                return {"status": "success", "claimed": False, "actions": [], "generation": manifest.get("generation", 0)}
            existing_claim = next((claim for claim in manifest["claims"].values() if claim.get("state") in {"claimed", "launched"}), None)
            if existing_claim:
                return _outcome("blocked", "stale-claim", ["another task is already claimed"], "repository-task", existing_claim.get("token", "claim"), manifest.get("generation", 0), "resumable-conflict", claimed=False)
            task = pending[0]
            manifest["generation"] = int(manifest.get("generation", 0)) + 1
            token = uuid.uuid4().hex
            claim = {"token": token, "generation": manifest["generation"], "owner": self.owner, "timestamp": self.clock(), "state": "claimed", "task_id": task["id"]}
            manifest["claims"][task["id"]] = claim
            task["status"] = "claimed"
            self._save(manifest)
            return {"status": "success", "claimed": True, "task_id": task["id"], "generation": manifest["generation"], "token": token, "actions": []}

    @_locked_mutation
    def _mark_claim_launched(self, claim: Mapping[str, Any], task_id: str, policy_token: Mapping[str, Any]) -> dict[str, Any] | None:
        """Fence the claim-launched write; re-verify the claim under the lock."""

        manifest = load_manifest(self.manifest_path)
        current_claim = manifest["claims"].get(task_id)
        if (
            not current_claim
            or current_claim.get("token") != claim["token"]
            or current_claim.get("generation") != claim["generation"]
            or current_claim.get("state") not in {"claimed", "launched"}
            or manifest.get("workflow_state") == "aborted"
        ):
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        baseline_revision = self._git_head_revision()
        if not baseline_revision:
            # A missing baseline would silently disable the scope witness at
            # every later checkpoint; fail closed at launch instead.
            return _outcome("blocked", "worktree-witness-unavailable", ["git baseline revision unavailable at launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=False)
        current_claim.update({"state": "launched", "policy_token": policy_token, "baseline_revision": baseline_revision})
        # Re-fetch the task from this live snapshot; a task object captured
        # from an earlier manifest snapshot would be silently dropped on save.
        manifest["tasks"][task_id]["status"] = "launched"
        manifest["history"].append({"event": "started", "task_id": task_id, "generation": claim["generation"]})
        self._save(manifest)
        return None

    @_locked_mutation
    def _record_activation_receipt(self, claim: Mapping[str, Any], task_id: str, activation: Mapping[str, Any]) -> dict[str, Any] | None:
        """Fence the activation-receipt write; re-verify the claim under the lock."""

        manifest = load_manifest(self.manifest_path)
        current_claim = manifest["claims"].get(task_id)
        if not current_claim or current_claim.get("token") != claim["token"] or current_claim.get("generation") != claim["generation"]:
            return _outcome("blocked", "owner-mismatch", ["claim changed before activation receipt"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        current_claim["activation_receipt"] = getattr(self.adapter, "activation_receipt", dict(activation))
        self._save(manifest)
        return None

    def _launch_claimed_task(self, claim: Mapping[str, Any], prompt: str, deadline_seconds: float | None) -> dict[str, Any]:
        task_id = str(claim["task_id"])
        task = load_manifest(self.manifest_path)["tasks"][task_id]
        operation_kind = str(task.get("operation_kind", "repository-task"))
        allowed_paths = task.get("allowed_paths", task.get("files", ()))
        envelope = ActionEnvelope(
            str(self.repo_root),
            tuple(str(path) for path in allowed_paths),
            operation_kind,
            task.get("network") is True,
            (f"task={task_id}", f"plan={self.plan_slug}"),
        )
        authorization = self.authorize_envelope(envelope, int(claim["generation"]))
        if authorization["status"] != "success":
            return self._persist_blocked_claim(claim, authorization, task_id)
        fencing = self._mark_claim_launched(claim, task_id, authorization["policy_token"])
        if fencing is not None:
            return fencing
        if self.adapter is None:
            return self._persist_blocked_claim(
                claim,
                _outcome("blocked", "runtime-policy-unavailable", ["no adapter configured"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile"),
            )
        activation_check = getattr(self.adapter, "activation_check", None)
        if callable(activation_check):
            activation = activation_check()
            if not isinstance(activation, Mapping) or activation.get("status") != "success":
                activation_evidence = activation.get("evidence", ["adapter activation was not verified"]) if isinstance(activation, Mapping) else ["adapter activation returned a malformed receipt"]
                return self._persist_blocked_claim(
                    claim,
                    _outcome("blocked", "runtime-policy-unavailable", bounded_evidence(activation_evidence), "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile"),
                )
            fencing = self._record_activation_receipt(claim, task_id, activation)
            if fencing is not None:
                return fencing
        raw = self._invoke_adapter_launch(claim, task, prompt, deadline_seconds, authorization["policy_token"])
        if raw.get("status") != "success" and raw.get("reason_code") in {"malformed-result", "runtime-policy-unavailable", "runtime-error", "timeout"}:
            return self._persist_blocked_claim(claim, raw, task_id)
        validated = self.validate_adapter_result(raw)
        if validated.get("reason_code") == "malformed-result":
            return self._persist_blocked_claim(claim, validated, task_id)
        return self.record_worker_checkpoint(raw)

    def launch_next_task(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        claim = self.claim_next_task()
        if not claim.get("claimed"):
            return claim
        return self._launch_claimed_task(claim, prompt, deadline_seconds)

    def continue_parent(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        """Reload state, reconcile safely, and advance one defined step."""

        manifest = self.refresh_manifest()
        if manifest.get("workflow_state") == "aborted":
            return _outcome("aborted", "explicit-abort", ["workflow was explicitly aborted"], "parent-continuation", "runtime:aborted", manifest.get("generation", 0), "preserve-and-stop")
        if manifest.get("workflow_state") in {"terminal", "complete"}:
            return self.terminal_result() or self._result_error("terminal receipt disappeared")
        reconciliation = self.reconcile_startup()
        if reconciliation["status"] != "success":
            return reconciliation
        manifest = self.refresh_manifest()
        if manifest.get("workflow_state") in {"terminal", "complete"}:
            return self.terminal_result() or self._result_error("terminal receipt disappeared")
        existing_claim = next(
            (claim for claim in manifest["claims"].values() if claim.get("state") in {"claimed", "launched"}),
            None,
        )
        if existing_claim:
            if existing_claim.get("owner") != self.owner:
                return _outcome("blocked", "stale-claim", ["another owner holds the next task claim"], "parent-continuation", str(existing_claim.get("token", "claim")), int(existing_claim.get("generation", 0)), "preserve-and-reconcile")
            task = manifest["tasks"].get(existing_claim.get("task_id"))
            if task is None:
                return self._result_error("claimed task is absent from manifest")
            result = self._launch_claimed_task(existing_claim, prompt, deadline_seconds)
            self.refresh_manifest()
            return result
        claim = self.claim_next_task()
        if not claim.get("claimed"):
            if all(self._task_complete(item) for item in manifest["tasks"].values()):
                return _outcome("blocked", "done-pending", ["terminal receipt evidence is required"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
            return claim
        result = self._launch_claimed_task(claim, prompt, deadline_seconds)
        self.refresh_manifest()
        return result

    @_locked_mutation
    def resume(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        """Resume only blocked tasks whose receipt permits continuation."""

        manifest = self.refresh_manifest()
        if manifest.get("workflow_state") in {"terminal", "complete"}:
            return self.terminal_result() or self._result_error("terminal receipt disappeared")
        resumable = [
            task for task in manifest["tasks"].values()
            if task.get("status") == "blocked" and task.get("resume_allowed") is True
        ]
        if not resumable:
            return _outcome(
                "blocked",
                "stale-claim",
                ["no resumable blocked task"],
                "parent-continuation",
                "runtime:resume",
                manifest.get("generation", 0),
                "preserve-and-reconcile",
            )
        task = sorted(resumable, key=lambda item: (item.get("number", 0), item.get("id", "")))[0]
        claim = manifest["claims"].get(task["id"])
        if not isinstance(claim, Mapping):
            return _outcome("blocked", "owner-mismatch", ["blocked task has no claim"], "parent-continuation", f"{task['id']}:resume", manifest.get("generation", 0), "preserve-and-reconcile")
        if claim.get("owner") != self.owner or claim.get("state") != "blocked":
            return _outcome("blocked", "owner-mismatch", ["resume claim is not owned and blocked"], "parent-continuation", str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), "preserve-and-reconcile")
        if not isinstance(claim.get("policy_token"), Mapping) or claim["policy_token"].get("generation") != claim.get("generation"):
            return _outcome("blocked", "runtime-policy-unavailable", ["resume policy token is missing or stale"], "parent-continuation", str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), "preserve-and-reconcile")
        if self.adapter is not None and task.get("session_id") and claim:
            try:
                raw = self.adapter.resume(task["session_id"], prompt, claim["generation"], task_id=task["id"], deadline_seconds=deadline_seconds, policy_token=claim.get("policy_token"))
            except Exception as exc:
                raw = _outcome("error", "runtime-error", [type(exc).__name__], "repository-task", f"{task['id']}:resume", claim["generation"], "preserve-and-reconcile")
            if isinstance(raw, Mapping):
                raw = dict(raw)
                raw["claim_token"] = claim["token"]
            else:
                raw = _outcome("blocked", "malformed-result", ["adapter resume returned a non-mapping result"], "repository-task", f"{task['id']}:resume", claim["generation"], "preserve-and-reconcile")
            validated = self.validate_adapter_result(raw)
            if validated.get("reason_code") == "malformed-result":
                return self._persist_blocked_claim(claim, validated, task["id"])
            return self.record_worker_checkpoint(raw)
        task["status"] = "pending"
        claim["state"] = "replaced"
        manifest["history"].append({"event": "resume", "tasks": [task["id"] for task in resumable]})
        self._save(manifest)
        return self.continue_parent(prompt, deadline_seconds)

    @_locked_mutation
    def reconcile_startup(
        self,
        commit_lookup: Callable[[str], bool] | None = None,
        dirty_worktree: bool = False,
        live_worker_owner: str | None = None,
    ) -> dict[str, Any]:
        """Recover only provable commits; quarantine ambiguous claims."""

        manifest = load_manifest(self.manifest_path)
        commit_lookup = commit_lookup or self.commit_lookup
        if not dirty_worktree:
            try:
                dirty_worktree = self._git_worktree_dirty()
            except (OSError, RuntimeError) as exc:
                return _outcome("blocked", "worktree-witness-unavailable", [str(exc)], "repository-task", "worktree:witness", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        for task_id, claim in manifest["claims"].items():
            if claim.get("state") not in {"claimed", "launched"}:
                continue
            task = manifest["tasks"].get(task_id, {})
            if task.get("status") in {"done-pending", "checkpointed", "complete"}:
                continue
            if dirty_worktree:
                return _outcome("blocked", "dirty-worktree", ["uncommitted worktree requires explicit reconciliation"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
            commit_identity = task.get("commit_identity")
            if commit_identity and task.get("done_log_evidence") and commit_lookup and commit_lookup(commit_identity):
                return self.reconcile_commit_before_checkpoint(
                    task_id,
                    commit_identity,
                    commit_lookup,
                    claim_token=claim.get("token"),
                    generation=claim.get("generation"),
                )
            if live_worker_owner and live_worker_owner == claim.get("owner"):
                return _outcome("blocked", "stale-claim", ["ambiguous live worker claim"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
            return _outcome("blocked", "owner-mismatch", ["claim owner or generation cannot be proven safe"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
        return {"status": "success", "reason_code": "completed", "evidence": ["no ambiguous claims"], "actions": [], "generation": manifest.get("generation", 0)}

    def _git_commit_exists(self, commit_identity: str) -> bool:
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", str(commit_identity)):
            return False
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{commit_identity}^{{commit}}"],
            cwd=self.repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return completed.returncode == 0

    def _git_worktree_dirty(self) -> bool:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("git status witness failed")
        return bool(completed.stdout.strip())

    def _git_head_revision(self) -> str:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return ""
        return completed.stdout.strip()

    def _git_changed_paths(self, baseline: str) -> list[str] | None:
        """Union of tracked diffs and untracked files relative to a baseline.

        ``git diff`` alone is blind to untracked files (the primary write form
        in this workflow), so untracked entries from ``git status`` are added.
        ``core.quotePath=false`` keeps names comparable as literal posix paths.
        Returns ``None`` when either git witness fails.
        """

        diff = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "--name-only", baseline],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if diff.returncode != 0:
            return None
        paths = {line.strip() for line in diff.stdout.splitlines() if line.strip()}
        status = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if status.returncode != 0:
            return None
        for line in status.stdout.splitlines():
            if len(line) < 4:
                continue
            for part in line[3:].split(" -> "):
                path = part.strip().strip('"')
                if path:
                    paths.add(path)
        return sorted(paths)

    def _path_escapes_repo(self, path: str) -> bool:
        """True when an on-disk path resolves outside the repository root.

        A tracked in-scope path replaced by a symlink pointing outside the
        repository must count as a scope violation even though the diff lists
        only the (in-scope) name.
        """

        try:
            resolved = (self.repo_root / path).resolve()
        except OSError:
            return False
        return resolved != self.repo_root and self.repo_root not in resolved.parents

    def _git_commit_is_descendant(self, baseline: str, commit: str) -> tuple[bool, bool]:
        """Return ``(is_descendant, witness_ok)`` for a claimed commit."""

        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "merge-base", "--is-ancestor", baseline, commit],
            cwd=self.repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode == 0:
            return True, True
        if completed.returncode == 1:
            return False, True
        return False, False

    def _git_diff_paths(self, baseline: str, commit: str) -> list[str] | None:
        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "--name-only", baseline, commit],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        return [line.strip() for line in completed.stdout.splitlines() if line.strip()]

    def _worktree_scope_violation(self, claim: Mapping[str, Any]) -> tuple[str, list[str]]:
        """Enforce the claim's allowed-path boundary with a git witness.

        Returns ``(verdict, paths)`` where verdict is ``ok``, ``violation``,
        or ``unavailable``. A claim without a recorded baseline revision
        (for example a seeded test claim) has no witness and stays ``ok``;
        a recorded baseline with an empty scope, or a broken witness, fails
        closed.
        """

        baseline = str(claim.get("baseline_revision") or "").strip()
        if not baseline:
            return "ok", []
        allowed = set((claim.get("policy_token") or {}).get("allowed_paths", ()))
        if not allowed:
            return "unavailable", []
        changed = self._git_changed_paths(baseline)
        if changed is None:
            return "unavailable", []
        unexpected = [path for path in changed if path not in allowed or self._path_escapes_repo(path)]
        if unexpected:
            return "violation", unexpected
        return "ok", []

    @_locked_mutation
    def abort(self, task_id: str, token: str) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        claim = manifest["claims"].get(task_id)
        if not claim or claim.get("token") != token or claim.get("owner") != self.owner:
            return _outcome("blocked", "owner-mismatch", ["abort receipt does not match claim owner"], "repository-task", token, manifest.get("generation", 0), "preserve-and-reconcile")
        manifest["tasks"][task_id]["status"] = "aborted"
        claim["state"] = "aborted"
        manifest["workflow_state"] = "aborted"
        self._save(manifest)
        return _outcome("aborted", "explicit-abort", [f"task={task_id}"], "repository-task", token, claim.get("generation", 0), "preserve-and-stop")

    @_locked_mutation
    def mark_commit_pending(self, task_id: str, commit_identity: str, log_evidence: Any = (), claim_token: str | None = None, generation: int | None = None) -> dict[str, Any]:
        """Persist the commit boundary before checkpoint completion."""

        manifest = self.refresh_manifest()
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id) if task else None
        if task is None or claim is None or claim.get("owner") != self.owner or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
            return _outcome("blocked", "owner-mismatch", [f"task={task_id}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile")
        task.update({"status": "commit-pending", "commit_identity": str(commit_identity), "done_log_evidence": bounded_evidence(log_evidence)})
        manifest["history"].append({"event": "commit-pending", "task_id": task_id, "commit_identity": str(commit_identity)})
        self._save(manifest)
        return _outcome("success", "commit-pending", [f"task={task_id}", f"commit={commit_identity}"], "done-handoff", f"{task_id}:commit", claim.get("generation", 0), "preserve-and-reconcile")

    @_locked_mutation
    def reconcile_commit_before_checkpoint(self, task_id: str, commit_identity: str, commit_lookup: Callable[[str], bool], claim_token: str | None = None, generation: int | None = None) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        task = manifest["tasks"].get(task_id)
        if task is None:
            return self._result_error(f"unknown task: {task_id}")
        if task.get("status") == "checkpointed" and task.get("commit_identity") == commit_identity:
            return _outcome("success", "completed", ["commit already reconciled"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[])
        claim = manifest["claims"].get(task_id)
        if not claim or claim.get("owner") != self.owner or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
            return _outcome("blocked", "owner-mismatch", ["commit recovery receipt does not match the live claim"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile")
        if task.get("commit_identity") != commit_identity or not task.get("done_log_evidence"):
            return _outcome("blocked", "commit-pending", ["matching done-log evidence and commit identity are required"], "done-handoff", f"{task_id}:commit", claim.get("generation", manifest.get("generation", 0)), "preserve-and-reconcile")
        if not commit_lookup(commit_identity):
            return _outcome("blocked", "commit-pending", [f"commit not found: {commit_identity}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile")
        task.update({"status": "checkpointed", "checkbox": True, "complete": True, "commit_identity": commit_identity})
        manifest["checkpoints"][f"{task_id}:commit"] = {"task_id": task_id, "commit_identity": commit_identity, "reconciled": True}
        if task_id in manifest["claims"]:
            manifest["claims"][task_id]["state"] = "closed"
        self._save(manifest)
        claim = self.claim_next_task()
        actions = [{"type": "launch-task", "task_id": claim["task_id"], "generation": claim["generation"]}] if claim.get("claimed") else []
        return _outcome("success", "completed", [f"reconciled commit={commit_identity}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=actions)

    def parent_continuation_available(self) -> bool:
        return self.profile.get("capabilities", {}).get("parent_continuation", "unsupported") != "unsupported"

    @_locked_mutation
    def mark_terminal(self, archived_plan_path: str = "", last_commit_sha: str = "", phase5_checklist: list[str] | None = None) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        if not all(self._task_complete(task) for task in manifest["tasks"].values()):
            return _outcome("blocked", "done-pending", ["all tasks must be complete before terminal state"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
        if (
            not isinstance(archived_plan_path, str)
            or not archived_plan_path.strip()
            or not isinstance(last_commit_sha, str)
            or not re.fullmatch(r"[0-9a-fA-F]{7,64}", last_commit_sha.strip())
            or not isinstance(phase5_checklist, list)
            or not phase5_checklist
            or not all(isinstance(item, str) and item.strip() for item in phase5_checklist)
        ):
            return _outcome("blocked", "done-pending", ["archived plan, commit identity, and Phase 5 checklist are required"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
        manifest["workflow_state"] = "complete"
        manifest["terminal_receipt"] = {
            "workflow_state": "complete",
            "phase5_checklist": list(phase5_checklist),
            "archived_plan_path": archived_plan_path,
            "last_commit_sha": last_commit_sha,
        }
        self._save(manifest)
        return _outcome("success", "completed", ["validated complete manifest"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "continue-parent")

    def terminal_result(self) -> dict[str, Any] | None:
        manifest = load_manifest(self.manifest_path)
        if manifest.get("workflow_state") not in {"terminal", "complete"}:
            return None
        receipt = manifest.get("terminal_receipt", {})
        if (
            receipt.get("workflow_state") != "complete"
            or not isinstance(receipt.get("phase5_checklist"), list)
            or not receipt["phase5_checklist"]
            or not isinstance(receipt.get("archived_plan_path"), str)
            or not receipt["archived_plan_path"].strip()
            or not isinstance(receipt.get("last_commit_sha"), str)
            or not re.fullmatch(r"[0-9a-fA-F]{7,64}", receipt["last_commit_sha"].strip())
        ):
            return None
        return _outcome("success", "completed", ["machine manifest is complete"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "continue-parent", workflow_state="complete", phase5_checklist=receipt.get("phase5_checklist", []), archived_plan_path=receipt.get("archived_plan_path", ""), last_commit_sha=receipt.get("last_commit_sha", ""))

    def selftest(self) -> None:
        manifest = load_manifest(self.manifest_path)
        if manifest["workflow_state"] not in {"active", "terminal", "complete", "blocked", "aborted"}:
            raise AssertionError("invalid workflow state")
        self.authorize_action("push")


def selftest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "runtime_state.json"
        create_manifest(path, "selftest", [{"id": "task-1", "number": 1, "status": "pending"}])
        driver = RuntimeDriver(path, plan_slug="selftest", repo_root=directory, commit_lookup=lambda _commit: True)
        claim = driver.claim_next_task()
        assert claim["claimed"]
        result = driver.record_worker_checkpoint({"status": "success", "reason_code": "completed", "evidence": ["selftest"], "action_scope": "repository-task", "checkpoint_identity": "task-1:worker", "generation": claim["generation"], "claim_token": claim["token"]})
        assert result["state"] == "done-pending"
        done = driver.record_done({"status": "success", "checkpoint_identity": "task-1:done", "task_id": "task-1", "generation": claim["generation"], "claim_token": claim["token"], "action_scope": "done-handoff", "evidence": ["selftest"], "commit_identity": "selftest-commit", "checkbox": True, "clean_state": True, "log_evidence": ["selftest-log"]})
        assert done["status"] == "success"
        terminal = driver.mark_terminal("docs/plans/completed/selftest.md", "abcdef1", ["selftest"])
        assert terminal["status"] == "success"
        assert driver.terminal_result()["status"] == "success"
    print("execute-plan runtime selftest: durable claim, checkpoint, and done boundary passed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--operation", choices=("claim", "checkpoint", "done", "resume", "continue", "terminal"))
    parser.add_argument("--input", help="JSON object for checkpoint or done")
    parser.add_argument("--plan-slug")
    parser.add_argument("--owner")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--runtime")
    parser.add_argument("--approval-receipt", type=Path, help="auditable activation receipt proving a verified non-interactive host approval policy")
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            selftest()
            return 0
        if args.manifest is None or args.operation is None:
            parser.error("--manifest and --operation are required unless --selftest is used")
        profile = capabilities.load_profiles().get(capabilities.canonicalize_runtime_id(args.runtime)) if args.runtime else None
        adapter_kwargs = {}
        if args.approval_receipt is not None:
            receipt = capabilities.load_approval_receipt(args.approval_receipt)
            if args.runtime and capabilities.canonicalize_runtime_id(args.runtime) != receipt["runtime"]:
                raise ValueError("approval receipt runtime does not match --runtime")
            adapter_kwargs["approval_receipt"] = args.approval_receipt
        adapter = capabilities.resolve_adapter(args.runtime, args.repo_root or Path.cwd(), **adapter_kwargs) if args.runtime else None
        driver = RuntimeDriver(
            args.manifest,
            plan_slug=args.plan_slug,
            adapter=adapter,
            profile=profile,
            owner=args.owner,
            repo_root=args.repo_root,
        )
        payload = json.loads(args.input) if args.input else {}
        if args.operation == "claim":
            result = driver.claim_next_task()
        elif args.operation == "checkpoint":
            result = driver.record_worker_checkpoint(payload)
        elif args.operation == "done":
            result = driver.record_done(payload)
        elif args.operation == "resume":
            result = driver.resume()
        elif args.operation == "continue":
            result = driver.continue_parent()
        else:
            result = driver.mark_terminal(
                archived_plan_path=str(payload.get("archived_plan_path", "")),
                last_commit_sha=str(payload.get("last_commit_sha", "")),
                phase5_checklist=payload.get("phase5_checklist"),
            )
        print(json.dumps(result, sort_keys=True))
    except (AssertionError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        label = "selftest" if args.selftest else "operation"
        print(f"execute-plan runtime {label} failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
