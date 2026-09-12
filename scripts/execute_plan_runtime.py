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
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator, Mapping, Sequence

import runtime_capabilities as capabilities
from runtime_capabilities import bounded_evidence


STATUSES = {"success", "contract-violation", "blocked", "aborted", "error"}
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
# Ambient worktree noise tolerated only on the pre-launch startup path: a
# startup blocked purely by these untracked entries is resumable after
# cleanup. Post-launch paths never consult this list; launch-record presence,
# not file mtime, separates ambient noise from worker-caused changes there.
AMBIENT_NOISE_PATTERNS = (
    ".DS_Store",
    ".DS_Store?",
    "._.DS_Store",
    ".#*",  # editor interchange / lock files
    "#*#",
    "*.swp",
    "*.swo",
    "*.swpx",
    "*~",
)


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
    if value.endswith("/") or resolved.is_dir():
        # Directory prefix matching is explicitly out of scope: a
        # directory-valued entry silently never matches a file-level witness,
        # so fail closed with the entry named for actionable remediation.
        raise ValueError(f"allowed path names a directory; list files explicitly instead of a directory prefix: {value}")
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
        for name in sorted(capabilities.CAPABILITY_NAMES)
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
    """Use an advisory lock whose kernel lease survives stale lock files.

    The lock is deliberately non-reentrant: a same-thread nested acquisition
    yields ``acquired=False`` instead of silently extending a held lease, so
    every nested acquisition site must restructure around unlocked adapter
    I/O and freshly re-read manifests after re-acquisition.
    """

    lock_path = Path(f"{path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
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
        yield True
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _locked_mutation(method: Callable[..., Any]) -> Callable[..., Any]:
    """Fence a read-modify-write transition with the manifest lock."""

    def wrapped(self: "RuntimeDriver", *args: Any, **kwargs: Any) -> Any:
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "mutation:conflict")
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


@dataclass(frozen=True)
class _RetryRelaunch:
    """Marker: a retry launch must run after the manifest lock is released."""

    claim: Mapping[str, Any]
    task: Mapping[str, Any]
    retry_policy: Mapping[str, Any]


@dataclass(frozen=True)
class _AdapterWindow:
    """Marker: the adapter resume runs after the manifest lock is released."""

    task: Mapping[str, Any]
    claim: Mapping[str, Any]


@dataclass(frozen=True)
class _ContinueParent:
    """Marker: resume delegates to the parent-continuation path."""


@dataclass(frozen=True)
class _ReconcileCommit:
    """Marker: commit reconciliation runs after the manifest lock is released."""

    task_id: str
    commit_identity: str
    lookup: Callable[[str], bool]
    token: Any
    generation: Any


def _stale_claim_outcome(
    checkpoint_identity: Any,
    generation: Any,
    evidence: Any,
    action_scope: str = "repository-task",
    recovery_action: str = "preserve-and-reconcile",
) -> dict[str, Any]:
    """Shared resumable stale-claim outcome for contention and progression guards."""

    return _outcome(
        "blocked",
        "stale-claim",
        evidence,
        action_scope,
        str(checkpoint_identity),
        int(generation),
        recovery_action,
    )


def _abort_outcome(
    identity: Any,
    generation: Any,
    evidence: Any,
    action_scope: str = "repository-task",
    **extra: Any,
) -> dict[str, Any]:
    """Shared aborted/explicit-abort envelope: preserve-and-stop, never resumable."""

    return _outcome(
        "aborted",
        "explicit-abort",
        evidence,
        action_scope,
        str(identity),
        int(generation),
        "preserve-and-stop",
        **extra,
    )


def _claim_progressed_past_receipt(
    task: Mapping[str, Any] | None,
    claim: Mapping[str, Any] | None,
    *,
    include_terminal: bool = False,
) -> bool:
    """True when a stale non-success receipt must not regress the durable state.

    The core statuses (``done-pending``, ``commit-pending``, ``aborted``) and a
    closed claim are shared by every emission site: a receipt arriving for an
    aborted task or claim must never persist. ``include_terminal``
    additionally covers ``checkpointed``/``complete`` for the blocked-persist
    path, which must never overwrite a terminal task.
    """

    if (claim or {}).get("state") == "closed":
        return True
    statuses: set[str] = {"done-pending", "commit-pending", "aborted"}
    if include_terminal:
        statuses |= {"checkpointed", "complete"}
    return task is not None and task.get("status") in statuses


def _mutation_unavailable(driver: "RuntimeDriver", checkpoint_identity: str, action_scope: str = "repository-task") -> dict[str, Any]:
    manifest = load_manifest(driver.manifest_path)
    return _stale_claim_outcome(
        checkpoint_identity,
        manifest.get("generation", 0),
        ["manifest mutation is held by another owner"],
        action_scope,
        "resumable-conflict",
    )


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
        self._explicit_owner = owner is not None
        if owner is not None:
            self.owner = owner
        elif isinstance(manifest_owner, str) and manifest_owner.strip():
            # Derive the owner from the machine manifest so separate driver
            # processes sharing one manifest also share one owner identity.
            # Provisional: re-resolved under the manifest lock below so two
            # first constructions on a fresh manifest commit exactly one
            # owner identity.
            self.owner = manifest_owner
        else:
            self.owner = f"runtime-{uuid.uuid4().hex}"
        if plan_slug and manifest.get("plan_slug") != plan_slug:
            raise ValueError("manifest plan slug mismatch")
        self.plan_slug = str(manifest["plan_slug"])
        self._resolve_owner_and_receipts()

    def _resolve_owner_and_receipts(self) -> None:
        """Commit owner identity and capability receipts under the manifest lock.

        Owner resolution and the receipt refresh run inside the locked
        section: when two first constructions race on a fresh manifest, the
        loser re-reads the manifest under the lock and adopts the winner's
        committed owner instead of silently failing every later owner fence.
        When the lock is contended at construction, the driver makes one
        best-effort unlocked re-read and adopts a committed owner if present;
        a manifest with no committed owner (or a failed re-read) is a
        fail-closed construction error naming the contention, never a
        silently kept provisional identity that would miss every later owner
        fence. A profile-less construction (for example a CLI invocation
        without ``--runtime``) skips the receipt write so durable capability
        receipts are never downgraded to ``unsupported``, while the locked
        owner initialization still persists ``manifest["owner"]``.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                # Adoption or fail-closed: an unlocked read is safe here
                # because nothing is written and the adopted value only ever
                # converges two racers onto the winner's committed identity.
                if self._explicit_owner:
                    return
                contention_error: Exception | None = None
                try:
                    contended = load_manifest(self.manifest_path)
                except (OSError, ValueError) as exc:
                    contention_error = exc
                    contended = None
                committed = contended.get("owner") if contended else None
                if not (isinstance(committed, str) and committed.strip()):
                    raise ValueError(f"manifest lock contended at construction; no committed owner to adopt: {self.manifest_path}") from contention_error
                self.owner = committed
                return
            manifest = load_manifest(self.manifest_path)
            committed_owner = manifest.get("owner")
            if not self._explicit_owner and isinstance(committed_owner, str) and committed_owner.strip():
                self.owner = committed_owner
            else:
                manifest.setdefault("owner", self.owner)
            if self.profile:
                capabilities_data = dict(self.profile.get("capabilities", {}))
                receipts = manifest.setdefault("capabilities", {})
                fallback = self.profile.get("fallback", "Use the durable receipt and parent continuation.")
                for name in sorted(capabilities.CAPABILITY_NAMES):
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

    def authorize_action(self, action_scope: str, path: str | None = None, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Default-deny operations outside repository-local continuation.

        Callers inside an already-loaded checkpoint cycle pass the loaded
        manifest through so authorization triggers no per-call manifest
        re-read.
        """

        scope = str(action_scope or "")
        lowered = scope.lower()
        if manifest is not None:
            generation = manifest.get("generation", 0)
        else:
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
            if result["action_scope"].startswith("external") or not self.authorize_action(result["action_scope"], manifest=manifest)["status"] == "success":
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
                if self.authorize_action(operation, target or None, manifest=manifest)["status"] != "success":
                    return _outcome("blocked", "contract-violation", [f"post-launch action={operation}"], operation or "unknown", result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
            return result
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            checkpoint = str(raw.get("checkpoint_identity") or "runtime:malformed")
            return self._result_error(str(exc), generation, checkpoint_identity=checkpoint)

    def _launch_record(self, claim: Mapping[str, Any], baseline_revision: str) -> dict[str, Any]:
        """Snapshot a claim's launch identity for later drift checks."""

        return {
            "baseline_revision": str(baseline_revision or ""),
            "generation": claim.get("generation"),
            "launched_at": self.clock(),
        }

    def _persist_blocked_claim(
        self,
        claim: Mapping[str, Any],
        result: Mapping[str, Any],
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Locking wrapper for unlocked call sites (launch and resume paths)."""

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, str(claim.get("token", "claim")))
            manifest = load_manifest(self.manifest_path)
            return self._persist_blocked_claim_locked(claim, result, task_id, manifest)

    @staticmethod
    def _apply_blocked(
        manifest: dict[str, Any],
        task_id: str,
        result: Mapping[str, Any],
        *,
        resume_allowed: Any,
        session_id: Any,
    ) -> None:
        """Shared blocked-persist mutation tail for both persist sites."""

        task = manifest["tasks"].get(task_id)
        if task is not None:
            task["status"] = "blocked"
            task["resume_allowed"] = bool(resume_allowed)
            task["blocked_receipt"] = dict(result)
            if session_id:
                task["session_id"] = str(session_id)
        manifest["claims"][task_id]["state"] = "blocked"
        manifest["history"].append({"event": "worker-blocked", "task_id": task_id, "reason_code": result.get("reason_code", "malformed-result")})

    def _persist_blocked_claim_locked(
        self,
        claim: Mapping[str, Any],
        result: Mapping[str, Any],
        task_id: str | None,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist a blocked claim; the caller already holds the manifest lock."""

        task_id = task_id or str(claim.get("task_id", ""))
        current_claim = manifest.get("claims", {}).get(task_id)
        if not current_claim or current_claim.get("token") != claim.get("token") or current_claim.get("generation") != claim.get("generation"):
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
        if manifest.get("workflow_state") == "aborted":
            # An aborted workflow is never resurrected by a late receipt.
            return _abort_outcome(
                claim.get("token", "claim"),
                claim.get("generation", manifest.get("generation", 0)),
                ["workflow was explicitly aborted before this receipt"],
            )
        if _claim_progressed_past_receipt(task, current_claim, include_terminal=True):
            # A blocked receipt that arrives after the task already progressed
            # (for example across a resume adapter window) must never regress
            # the durable state; surface the resumable stale-claim outcome.
            return _stale_claim_outcome(
                claim.get("token", "claim"),
                claim.get("generation", manifest.get("generation", 0)),
                ["claim already progressed past this receipt"],
            )
        self._apply_blocked(manifest, task_id, result, resume_allowed=result.get("resume_allowed", False), session_id=result.get("session_id"))
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
            return _outcome("blocked", "timeout", ["launch deadline exceeded"], "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile", resume_allowed=True, claim_token=claim["token"])
        except TypeError as exc:
            return _outcome("blocked", "runtime-policy-unavailable", [f"adapter rejected policy token: {exc}"], "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile", claim_token=claim["token"])
        except Exception as exc:
            return _outcome("error", "runtime-error", [type(exc).__name__], "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile", claim_token=claim["token"])
        if not isinstance(raw, Mapping):
            return _outcome("blocked", "malformed-result", ["adapter returned a non-mapping result"], "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile", claim_token=claim["token"])
        raw = dict(raw)
        raw["claim_token"] = claim["token"]
        return raw

    def record_worker_checkpoint(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Commit a checkpoint receipt; retry adapter I/O runs outside the lock.

        The receipt validation, retry accounting, and state transitions run
        under the manifest lock. When a retry launch is warranted the locked
        region ends first: the adapter call runs unlocked (mirroring the
        launch pattern) and the recursive checkpoint re-acquires the lock
        against a freshly read manifest.
        """

        outcome: dict[str, Any] | _RetryRelaunch
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "mutation:conflict")
            outcome = self._record_checkpoint_locked(raw)
        if isinstance(outcome, _RetryRelaunch):
            retry_raw = self._invoke_adapter_launch(
                outcome.claim,
                outcome.task,
                "Rewrite the authorized repository task and return a structured result.",
                None,
                outcome.claim.get("policy_token", {}),
            )
            # The driver owns the retry budget: override any worker- or
            # adapter-supplied policy with the decremented budget so a
            # hostile envelope cannot re-supply attempts each round.
            retry_raw["retry_policy"] = outcome.retry_policy
            # Every launch return path carries the claim token, but a
            # hand-rolled runner result could still omit it: without the
            # token the recursive checkpoint would misdiagnose owner-mismatch
            # instead of persisting the attempt receipt.
            retry_raw.setdefault("claim_token", outcome.claim["token"])
            return self.record_worker_checkpoint(retry_raw)
        return outcome

    def _record_checkpoint_locked(self, raw: Mapping[str, Any]) -> dict[str, Any] | _RetryRelaunch:
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
            return self._checkpoint_retry_or_blocked(result, raw, manifest, task_id, claim)
        return self._checkpoint_success_commit(result, raw, manifest, task_id, claim_token)

    def _checkpoint_retry_or_blocked(self, result: dict[str, Any], raw: Mapping[str, Any], manifest: dict[str, Any], task_id: str, claim: Mapping[str, Any]) -> dict[str, Any] | _RetryRelaunch:
        """Handle a non-success checkpoint receipt: bounded retries and blocked claims.

        Owns retry budget accounting and the durable attempt records; returns
        either the receipt to surface to the caller or a ``_RetryRelaunch``
        marker telling the caller to relaunch after the lock is released.
        """

        if result["reason_code"] == "worker-hesitation":
            result["recovery_action"] = "rewrite-and-retry"
            result["contract_rule"] = "worker must not ask conversational permission for authorized repository work"
        elif result["status"] == "contract-violation":
            result["contract_rule"] = str(raw.get("contract_rule") or "adapter result violated the typed action contract")
        if manifest.get("workflow_state") == "aborted":
            # An explicit abort wins over any in-flight receipt, retryable or
            # not: never persist, never relaunch, never un-abort.
            return _abort_outcome(
                result["checkpoint_identity"],
                result["generation"],
                ["workflow was explicitly aborted before this receipt"],
            )
        task = manifest["tasks"].get(task_id)
        retry = result.get("retry_policy", {})
        retryable = (
            result["status"] == "contract-violation" and retry.get("mode") == "rewrite-and-retry"
        ) or (result["status"] == "error" and retry.get("mode") == "bounded")
        # The progression guard is a conjunct of the retry decision and of the
        # non-success receipt guard below: a stale retryable receipt (for
        # example one landing after a competing writer completed a success
        # checkpoint inside a resume adapter window) must never relaunch a
        # done-pending, commit-pending, checkpointed, complete, or aborted
        # task. The receipt guard keeps one distinction: a terminal
        # (checkpointed/complete) task with a live claim surfaces the receipt
        # itself rather than stale-claim, because nothing regressed and the
        # reason code (for example approval-required) stays actionable.
        progressed = _claim_progressed_past_receipt(task, claim, include_terminal=True)
        if retryable and progressed:
            retryable = False
        if retryable and retry.get("attempts_remaining", 0) > 0 and self.adapter is not None and task is not None:
            retry["attempts_remaining"] = int(retry["attempts_remaining"]) - 1
            # A failed attempt must not poison the stable checkpoint
            # identity: record it under a distinct attempt identity so the
            # retry can still land the real checkpoint. The ordinal derives
            # from the existing checkpoint history so consecutive errors
            # persist distinct durable records instead of overwriting one
            # fixed key.
            identity = result["checkpoint_identity"]
            prior_ordinals = sorted(
                int(key.rsplit("#attempt-", 1)[1])
                for key in manifest["checkpoints"]
                if key.startswith(f"{identity}#attempt-") and key.rsplit("#attempt-", 1)[-1].isdigit()
            )
            ordinal = (prior_ordinals[-1] + 1) if prior_ordinals else 1
            manifest["checkpoints"][f"{identity}#attempt-{ordinal}"] = {"result": result, "task_id": task_id, "attempt": ordinal}
            manifest["history"].append({"event": "worker-retry", "task_id": task_id, "generation": result["generation"], "reason_code": result["reason_code"], "attempt": ordinal, "attempts_remaining": retry["attempts_remaining"]})
            task["status"] = "launched"
            if not isinstance(claim.get("launch_record"), Mapping):
                # A driver-owned relaunch is a launch: snapshot the record for
                # claims whose manifest predates launch records, so drift
                # detection stays armed for the retry result.
                manifest["claims"][task_id]["launch_record"] = self._launch_record(claim, claim.get("baseline_revision"))
            self._save(manifest)
            return _RetryRelaunch(claim=dict(manifest["claims"][task_id]), task=task, retry_policy=retry)
        if progressed and (task is None or not self._task_complete(task)):
            # A stale non-success receipt (for example one landing after a
            # competing writer completed a success checkpoint inside a resume
            # adapter window) must not regress done-pending; surface the
            # resumable stale-claim outcome instead.
            return _stale_claim_outcome(
                result["checkpoint_identity"],
                result["generation"],
                ["claim already progressed past this receipt"],
            )
        if task and not self._task_complete(task):
            self._apply_blocked(manifest, task_id, result, resume_allowed=result["reason_code"] in capabilities.RESUMABLE_REASONS, session_id=raw.get("session_id"))
            self._save(manifest)
        return result

    def _checkpoint_success_commit(self, result: dict[str, Any], raw: Mapping[str, Any], manifest: dict[str, Any], task_id: str, claim_token: Any) -> dict[str, Any]:
        """Commit a successful checkpoint receipt and transition the task to done-pending.

        Runs inside the caller's held manifest lock; the locked snapshot is
        passed in, so no manifest reload is needed here.
        """

        identity = result["checkpoint_identity"]
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id)
        prior = manifest["checkpoints"].get(identity)
        if prior is not None and prior.get("result", {}).get("status") == "success":
            return {**result, "state": "done-pending", "duplicate": True, "actions": []}
        if task is None:
            return self._result_error(f"unknown checkpoint task: {task_id}", result["generation"])
        if claim.get("state") not in {"claimed", "launched", "blocked"}:
            return _outcome("blocked", "owner-mismatch", ["checkpoint claim is not live"], "repository-task", identity, result["generation"], "preserve-and-reconcile")
        drift = self._claim_drift_outcome(manifest, claim, "repository-task", identity)
        if drift is not None:
            return drift
        verdict, unexpected = self._worktree_scope_violation(claim)
        if verdict == "unavailable":
            return _outcome("blocked", "worktree-witness-unavailable", ["git diff scope witness failed"], "repository-task", identity, result["generation"], "preserve-and-reconcile", resume_allowed=False)
        if verdict == "violation":
            violation = _outcome("blocked", "contract-violation", [f"out-of-scope change: {path}" for path in unexpected], "repository-task", identity, result["generation"], "preserve-and-reconcile", resume_allowed=False)
            # The checkpoint's locked region is still held: use the unlocked
            # inner helper so the contract-violation receipt is persisted
            # without a nested lock acquisition (which the non-reentrant
            # lock would refuse and misdiagnose as owner-mismatch).
            return self._persist_blocked_claim_locked(claim, violation, task_id, manifest)
        completion: dict[str, Any] = {"status": "done-pending", "checkpoint_identity": identity}
        if raw.get("session_id"):
            completion["session_id"] = str(raw["session_id"])
        if not isinstance(claim.get("launch_record"), Mapping):
            # A fenced checkpoint proves the claim launched even when the
            # launch record was never written (manifests from before the
            # launch record existed); snapshot the claim's own live fields now
            # so later done-boundary drift checks stay armed.
            manifest["claims"][task_id]["launch_record"] = self._launch_record(claim, claim.get("baseline_revision"))
        self._complete_and_persist(
            manifest,
            task_id,
            completion=completion,
            history=[{"event": "worker-checkpoint", "task_id": task_id, "generation": result["generation"]}],
            checkpoint_record=(identity, {"result": result, "task_id": task_id, "recorded_at": self.clock()}),
            claim_state="launched",
        )
        refreshed = self.refresh_manifest()
        return {**result, "state": refreshed["tasks"][task_id]["status"], "duplicate": False, "actions": []}

    def record_done(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Record the done handoff; the next-claim transition runs after the lock.

        The verification and completion writes run under the manifest lock;
        the next-claim transition is deliberately outside the locked region
        so it never performs a nested (non-reentrant) lock acquisition.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "runtime:done", action_scope="done-handoff")
            outcome, claim_next = self._record_done_locked(raw)
        if claim_next:
            return self._attach_next_claim_action(outcome)
        return outcome

    def _attach_next_claim_action(self, outcome: dict[str, Any]) -> dict[str, Any]:
        """Claim the next task and attach the launch-task action to the outcome.

        Runs only after the caller's manifest lock is released: the claim
        transition acquires the (non-reentrant) lock itself.
        """

        claim = self.claim_next_task()
        if claim.get("claimed"):
            outcome["actions"] = [{"type": "launch-task", "task_id": claim["task_id"], "generation": claim["generation"]}]
        return outcome

    def _record_done_locked(self, raw: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        manifest = load_manifest(self.manifest_path)
        if not isinstance(raw, Mapping):
            return self._result_error("done handoff must be a mapping", action_scope="done-handoff"), False
        checkpoint_identity = raw.get("checkpoint_identity")
        if not isinstance(checkpoint_identity, str) or not checkpoint_identity.strip():
            return _outcome("blocked", "done-pending", ["checkpoint_identity is required before mutating state"], "done-handoff", "runtime:done", manifest.get("generation", 0), "preserve-and-reconcile"), False
        task_id = str(raw.get("task_id") or self._task_id_from_checkpoint(checkpoint_identity))
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id) if task else None
        if raw.get("status") != "success":
            return _outcome("blocked", "done-pending", ["successful done handoff required"], "done-handoff", str(raw.get("checkpoint_identity", f"{task_id}:done")), manifest.get("generation", 0), "preserve-and-reconcile"), False
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
            return _outcome("blocked", "done-pending", [f"missing or unfenced done evidence: {', '.join(required)}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile"), False
        if not self.commit_lookup(str(raw["commit_identity"])):
            return _outcome("blocked", "commit-pending", [f"commit not found: {raw['commit_identity']}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile"), False
        boundary = self._done_boundary_block(claim, str(raw["commit_identity"]), checkpoint_identity, manifest.get("generation", 0), manifest=manifest)
        if boundary is not None:
            return boundary, False
        if task.get("status") == "checkpointed" and task.get("commit_identity") == raw["commit_identity"]:
            return _outcome("success", "completed", ["duplicate done handoff"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[], duplicate=True), False
        self._complete_and_persist(
            manifest,
            task_id,
            completion={
                "status": "checkpointed",
                "checkbox": True,
                "complete": True,
                "commit_identity": str(raw["commit_identity"]),
                "done_log_evidence": bounded_evidence(raw["log_evidence"]),
            },
            # commit-pending is owned solely by mark_commit_pending; the done
            # handoff records only its own completion event.
            history=[
                {"event": "done-commit", "task_id": task_id, "commit_identity": str(raw["commit_identity"])},
            ],
            claim_state="closed",
        )
        return _outcome("success", "completed", ["done commit, checkbox, clean-state, and log evidence recorded"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[]), True

    def _done_boundary_block(self, claim: Mapping[str, Any] | None, commit_identity: str, checkpoint_identity: str, generation: int, manifest: Mapping[str, Any]) -> dict[str, Any] | None:
        """Verify the done boundary against the claim's launch baseline.

        The committed artifact is checked, not just attested. Only a claim with
        a recorded launch baseline can be verified; the launch path fails
        closed when no baseline is available, so a missing baseline skips
        verification here (preserving the launch-time failure). Returns None
        when verification passes, or a blocked outcome describing the failure.
        ``manifest`` is the locked-read snapshot supplied by the caller; every
        call site runs under the manifest lock, so the parameter is required.
        """

        # Drift first: a claim whose launch-record snapshot no longer matches
        # the live manifest (or is missing on a demonstrably launched claim)
        # must surface stale-claim before any commit handoff.
        drift = self._claim_drift_outcome(manifest, claim, "done-handoff", checkpoint_identity)
        if drift is not None:
            return drift
        baseline_revision = str((claim or {}).get("baseline_revision") or "").strip()
        if not baseline_revision:
            return None
        allowed = set((claim.get("policy_token") or {}).get("allowed_paths", ()))
        is_descendant, witness_ok = self._git_commit_is_descendant(baseline_revision, commit_identity)
        if not witness_ok or not allowed:
            return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary git witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        if not is_descendant:
            return _outcome("blocked", "commit-pending", [f"commit is not new work on the claim baseline: {commit_identity}"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        committed_paths = self._git_diff_paths(baseline_revision, commit_identity)
        if committed_paths is None:
            return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary git diff witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        out_of_scope = [path for path in committed_paths if path not in allowed]
        if out_of_scope:
            return _outcome("blocked", "commit-pending", [f"out-of-scope committed change: {path}" for path in out_of_scope], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        try:
            symlink_escapes = self._git_committed_symlink_escapes(commit_identity, [path for path in committed_paths if path in allowed])
        except (OSError, RuntimeError):
            return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary symlink witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        if symlink_escapes:
            return _outcome("blocked", "commit-pending", [f"committed symlink escapes repository: {path}" for path in symlink_escapes], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        try:
            actually_dirty = self._git_worktree_dirty()
        except (OSError, RuntimeError):
            return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary clean-state witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        if actually_dirty:
            return _outcome("blocked", "commit-pending", ["worktree is not clean at the done boundary"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        return None

    def _complete_and_persist(
        self,
        manifest: dict[str, Any],
        task_id: str,
        *,
        completion: Mapping[str, Any],
        history: Sequence[Mapping[str, Any]] = (),
        checkpoint_record: tuple[str, dict[str, Any]] | None = None,
        claim_state: str | None = None,
    ) -> None:
        """Apply a success-path completion and persist it under the held lock.

        Shared by the checkpoint success commit (task done-pending, claim
        stays live for the done handoff) and the done handoff (task
        checkpointed, claim closed). The next-claim transition is owned by
        the unlocked call sites, never performed here: this helper runs
        inside the caller's manifest lock and the lock is non-reentrant.
        """

        task = manifest["tasks"][task_id]
        task.update(completion)
        if checkpoint_record is not None:
            manifest["checkpoints"][checkpoint_record[0]] = checkpoint_record[1]
        for event in history:
            manifest["history"].append(event)
        if claim_state is not None and task_id in manifest["claims"]:
            manifest["claims"][task_id]["state"] = claim_state
        self._save(manifest)

    def claim_next_task(self) -> dict[str, Any]:
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            manifest = load_manifest(self.manifest_path)
            if not acquired:
                return _outcome("blocked", "stale-claim", ["manifest claim is held by another owner"], "repository-task", "claim:conflict", manifest.get("generation", 0), "resumable-conflict", claimed=False)
            if manifest.get("workflow_state") == "aborted":
                # An explicitly aborted workflow never hands out a new claim:
                # refuse before any generation bump or claim write so no
                # claimed residue is left behind for later reconciliation.
                return _abort_outcome(
                    "claim:aborted",
                    manifest.get("generation", 0),
                    ["workflow was explicitly aborted before claim"],
                    claimed=False,
                )
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
        if manifest.get("workflow_state") == "aborted":
            # An explicit abort racing the launch window is an abort outcome,
            # not an owner mismatch: the claim may still be live and owned.
            return _abort_outcome(claim["token"], claim["generation"], ["workflow was explicitly aborted before launch"])
        if (
            not current_claim
            or current_claim.get("token") != claim["token"]
            or current_claim.get("generation") != claim["generation"]
            or current_claim.get("state") not in {"claimed", "launched"}
        ):
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        baseline_revision = self._git_head_revision()
        if not baseline_revision:
            # A missing baseline would silently disable the scope witness at
            # every later checkpoint; fail closed at launch instead.
            return _outcome("blocked", "worktree-witness-unavailable", ["git baseline revision unavailable at launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=False)
        launch_record = self._launch_record(claim, baseline_revision)
        current_claim.update({"state": "launched", "policy_token": policy_token, "baseline_revision": baseline_revision, "launch_record": launch_record})
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
        if manifest.get("workflow_state") == "aborted":
            # Never write an activation receipt onto an aborted workflow.
            return _abort_outcome(claim["token"], claim["generation"], ["workflow was explicitly aborted before the activation receipt"])
        if current_claim.get("state") not in {"claimed", "launched"}:
            # A claim that left the live set on an active workflow is
            # contention or progression, not an abort: surface the resumable
            # stale-claim outcome instead of an explicit-abort envelope.
            return _stale_claim_outcome(claim["token"], claim["generation"], ["claim is no longer live; activation receipt refused"])
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
            return _abort_outcome("runtime:aborted", manifest.get("generation", 0), ["workflow was explicitly aborted"], action_scope="parent-continuation")
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
            if task.get("status") in {"done-pending", "commit-pending"}:
                # A task that already reached its commit boundary (for example
                # after a crash between checkpoint and done handoff) must not
                # be relaunched: the done handoff is the correct next step.
                return _outcome(
                    "blocked",
                    "done-pending",
                    ["claimed task is awaiting the done handoff; relaunch refused"],
                    "parent-continuation",
                    f"{task['id']}:done",
                    int(existing_claim.get("generation", 0)),
                    "preserve-and-reconcile",
                )
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

    def resume(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        """Resume only blocked tasks whose receipt permits continuation.

        Mirrors the launch pattern: the state selection and fence checks run
        under the manifest lock, the adapter resume call runs with the lock
        released, and the lock is re-acquired afterwards with the manifest
        re-read and checked for drift before any nested checkpoint write.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "runtime:resume", action_scope="parent-continuation")
            selection = self._resume_select_locked()
        if isinstance(selection, _AdapterWindow):
            task, claim = selection.task, selection.claim
            # Adapter I/O runs outside the manifest flock.
            try:
                raw = self.adapter.resume(task["session_id"], prompt, claim["generation"], task_id=task["id"], deadline_seconds=deadline_seconds, policy_token=claim.get("policy_token"))
            except Exception as exc:
                raw = _outcome("error", "runtime-error", [type(exc).__name__], "repository-task", f"{task['id']}:resume", claim["generation"], "preserve-and-reconcile")
            if isinstance(raw, Mapping):
                raw = dict(raw)
                raw["claim_token"] = claim["token"]
            else:
                raw = _outcome("blocked", "malformed-result", ["adapter resume returned a non-mapping result"], "repository-task", f"{task['id']}:resume", claim["generation"], "preserve-and-reconcile")
            # Re-acquire the lock and re-read the manifest: a competing writer
            # that rewrote the claim during the adapter window fails closed
            # with the resumable stale-claim outcome; a stale in-memory
            # snapshot is never written back.
            with _manifest_lock(self.manifest_path, self.owner) as reacquired:
                if not reacquired:
                    return _mutation_unavailable(self, f"{task['id']}:resume", action_scope="parent-continuation")
                fresh = load_manifest(self.manifest_path)
                live_claim = fresh.get("claims", {}).get(task["id"])
                drift = self._claim_drift_outcome(fresh, live_claim, "parent-continuation", f"{task['id']}:resume")
                if drift is not None:
                    return drift
            validated = self.validate_adapter_result(raw)
            if validated.get("reason_code") == "malformed-result":
                return self._persist_blocked_claim(claim, validated, task["id"])
            return self.record_worker_checkpoint(raw)
        if isinstance(selection, _ContinueParent):
            return self.continue_parent(prompt, deadline_seconds)
        return selection

    def _resume_select_locked(self) -> dict[str, Any] | _AdapterWindow | _ContinueParent:
        """Select the resume target under the held manifest lock.

        Returns the final outcome, an ``_AdapterWindow`` marker telling the
        caller to run the adapter resume with the lock released, or a
        ``_ContinueParent`` marker for the replacement path.
        """

        manifest = self.refresh_manifest()
        if manifest.get("workflow_state") == "aborted":
            # An explicitly aborted workflow is never auto-resumed; mirror
            # continue_parent's preserve-and-stop abort outcome.
            return _abort_outcome("runtime:aborted", manifest.get("generation", 0), ["workflow was explicitly aborted"], action_scope="parent-continuation")
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
            return _AdapterWindow(task=dict(task), claim=dict(claim))
        task["status"] = "pending"
        claim["state"] = "replaced"
        manifest["history"].append({"event": "resume", "tasks": [task["id"] for task in resumable]})
        self._save(manifest)
        return _ContinueParent()

    def reconcile_startup(
        self,
        commit_lookup: Callable[[str], bool] | None = None,
        dirty_worktree: bool = False,
        live_worker_owner: str | None = None,
    ) -> dict[str, Any]:
        """Recover only provable commits; quarantine ambiguous claims."""

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "worktree:witness")
            selection = self._reconcile_startup_locked(commit_lookup, dirty_worktree, live_worker_owner)
        if isinstance(selection, _ReconcileCommit):
            # Delegation runs after the lock releases: the commit
            # reconciliation acquires the (non-reentrant) lock itself.
            return self.reconcile_commit_before_checkpoint(
                selection.task_id,
                selection.commit_identity,
                selection.lookup,
                claim_token=selection.token,
                generation=selection.generation,
            )
        return selection

    def _reconcile_startup_locked(
        self,
        commit_lookup: Callable[[str], bool] | None,
        dirty_worktree: bool,
        live_worker_owner: str | None,
    ) -> dict[str, Any] | _ReconcileCommit:
        manifest = load_manifest(self.manifest_path)
        commit_lookup = commit_lookup or self.commit_lookup
        ambient_entries: list[tuple[str, str]] | None = None
        # Any claim carrying launch evidence (state claimed/launched or a
        # launch record) proves the worktree entered a launch window; the
        # dirty-worktree gate below must fire even when every such claim sits
        # on a completed task (legacy manifests), which the per-claim loop
        # would otherwise skip entirely.
        launch_evidence_claims = [
            claim for claim in manifest["claims"].values()
            if claim.get("state") in {"claimed", "launched"} or isinstance(claim.get("launch_record"), Mapping)
        ]
        if not dirty_worktree:
            try:
                dirty_worktree = self._git_worktree_dirty()
            except (OSError, RuntimeError) as exc:
                return _outcome("blocked", "worktree-witness-unavailable", [str(exc)], "repository-task", "worktree:witness", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            if dirty_worktree:
                # Only the pre-launch startup path consults the ambient-noise
                # allowlist: before launch nothing proves the noise was worker
                # caused, so a purely ambient dirty worktree blocks resumably
                # for cleanup instead of the non-resumable dirty-worktree gate.
                try:
                    entries = self._git_worktree_entries()
                except (OSError, RuntimeError) as exc:
                    return _outcome("blocked", "worktree-witness-unavailable", [str(exc)], "repository-task", "worktree:witness", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
                if entries and all(self._is_ambient_noise_entry(code, path) for code, path in entries):
                    ambient_entries = entries
        if ambient_entries is not None:

            def cleanup_outcome(token: Any, generation: Any) -> dict[str, Any]:
                return _outcome(
                    "blocked",
                    "cleanup-required",
                    [f"ambient worktree noise requires cleanup: {code} {path}" for code, path in ambient_entries],
                    "repository-task",
                    token,
                    generation,
                    "preserve-and-reconcile",
                )

            # Any claim carrying a launch record proves the worktree entered a
            # launch window (including a blocked claim that already launched):
            # ambient-shaped noise after launch is indistinguishable from
            # worker-caused dirt and keeps the hard block, so the resumable
            # hoisted return fires only when no claim has launch evidence.
            if not launch_evidence_claims:
                # Hoisted no-live-claim case: purely ambient noise on a
                # worktree with nothing in flight is the same resumable
                # cleanup condition as the claim-attached case below; without
                # this return the loop no-ops and startup silently proceeds.
                return cleanup_outcome("worktree:witness", manifest.get("generation", 0))
        if dirty_worktree and launch_evidence_claims:
            examined = [
                claim for claim in launch_evidence_claims
                if manifest["tasks"].get(str(claim.get("task_id")), {}).get("status")
                not in {"done-pending", "checkpointed", "complete"}
            ]
            if not examined:
                # Every launch-evidence claim sits on a task the per-claim
                # loop below skips (completed or at its commit boundary), so
                # the dirty gate is evaluated once here instead of being
                # silently skipped. The ambient discriminator still applies:
                # a launch-evidence claim without a launch record keeps the
                # resumable cleanup outcome; anything else keeps the hard
                # dirty-worktree block.
                if ambient_entries is not None:
                    prelaunch = next(
                        (claim for claim in launch_evidence_claims if not isinstance(claim.get("launch_record"), Mapping)),
                        None,
                    )
                    if prelaunch is not None:
                        return cleanup_outcome(prelaunch.get("token", "claim"), prelaunch.get("generation", 0))
                return _outcome("blocked", "dirty-worktree", ["uncommitted worktree requires explicit reconciliation"], "repository-task", "worktree:witness", manifest.get("generation", 0), "preserve-and-reconcile")
        for task_id, claim in manifest["claims"].items():
            if claim.get("state") not in {"claimed", "launched"} and not isinstance(claim.get("launch_record"), Mapping):
                continue
            task = manifest["tasks"].get(task_id, {})
            if task.get("status") in {"done-pending", "checkpointed", "complete"}:
                continue
            if dirty_worktree:
                # The resumable cleanup-required outcome requires a pre-launch
                # claim: once the launch record exists, ambient-shaped noise is
                # indistinguishable from worker-caused dirt and keeps the hard
                # dirty-worktree block (launch-record presence, not mtime, is
                # the discriminator).
                if ambient_entries is not None and not isinstance(claim.get("launch_record"), Mapping):
                    return cleanup_outcome(claim.get("token", "claim"), claim.get("generation", 0))
                return _outcome("blocked", "dirty-worktree", ["uncommitted worktree requires explicit reconciliation"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
            commit_identity = task.get("commit_identity")
            if commit_identity and task.get("done_log_evidence") and commit_lookup and commit_lookup(commit_identity):
                return _ReconcileCommit(task_id, commit_identity, commit_lookup, claim.get("token"), claim.get("generation"))
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

    @staticmethod
    def _parse_porcelain_z(output: str) -> list[tuple[str, str]]:
        """Parse NUL-delimited ``git status --porcelain -z`` records.

        With ``-z`` git emits literal paths (a double quote or non-ASCII byte
        in a name never becomes a C-quoted rendering), and rename or copy
        records carry the original path as a following NUL field instead of
        the ``orig -> new`` arrow. Malformed records surface with their raw
        text so callers treat them as real (never ambient, never allowed)
        paths.
        """

        entries: list[tuple[str, str]] = []
        fields = output.split("\0")
        index = 0
        while index < len(fields):
            record = fields[index]
            index += 1
            if not record:
                continue
            entries.append((record[:2], record[3:]))
            if record[:1] in {"R", "C"} and index < len(fields):
                entries.append((record[:2], fields[index]))
                index += 1
        return entries

    def _git_worktree_entries(self) -> list[tuple[str, str]]:
        """Enumerate worktree entries with the flagged porcelain -z witness."""

        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-z", "--untracked-files=all"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("git status witness failed")
        return self._parse_porcelain_z(completed.stdout)

    def _is_ambient_noise_entry(self, code: str, path: str) -> bool:
        """True only for untracked, in-repo entries matching the allowlist."""

        if code != "??":
            return False
        if not path or "\\" in path or "\x00" in path or path.startswith('"'):
            # A quoted or malformed rendering can never be proven ambient;
            # fail closed to the hard block.
            return False
        if self._path_escapes_repo(path):
            return False
        name = PurePosixPath(path).name
        return any(fnmatch.fnmatchcase(name, pattern) for pattern in AMBIENT_NOISE_PATTERNS)

    def _git_worktree_dirty(self) -> bool:
        return bool(self._git_worktree_entries())

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
        Both witnesses run with ``core.quotePath=false`` and the status witness
        uses the NUL-delimited ``-z`` form parsed by the shared porcelain
        helper, so names containing quotes or non-ASCII bytes stay comparable
        as literal posix paths. Returns ``None`` when either git witness
        fails.
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
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-z", "--untracked-files=all"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if status.returncode != 0:
            return None
        for _code, path in self._parse_porcelain_z(status.stdout):
            if path:
                paths.add(path)
        return sorted(paths)

    def _path_escapes_repo(self, path: str) -> bool:
        """True when an on-disk path resolves outside the repository root.

        A tracked in-scope path replaced by a symlink pointing outside the
        repository must count as a scope violation even though the diff lists
        only the (in-scope) name. A path whose resolution raises ``OSError``
        cannot be proven contained, so it fails closed as escaping.
        """

        try:
            resolved = (self.repo_root / path).resolve()
        except OSError:
            return True
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

    def _git_committed_symlink_escapes(self, commit: str, paths: Sequence[str]) -> list[str]:
        """Return committed symlink paths whose targets escape the repository.

        ``git diff --name-only`` lists only the (possibly in-scope) link name,
        so a committed symlink (blob mode 120000, checked via ``git ls-tree``)
        pointing outside the repository root is verified separately. Any
        witness failure counts the path as escaping (fail closed).
        """

        if not paths:
            return []
        tree = subprocess.run(
            ["git", "ls-tree", "-z", commit, "--", *paths],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if tree.returncode != 0:
            raise RuntimeError("git ls-tree witness failed")
        escapes: list[str] = []
        for record in tree.stdout.split("\0"):
            if not record:
                continue
            meta, _, path = record.partition("\t")
            parts = meta.split()
            if len(parts) != 3 or parts[0] != "120000" or parts[1] != "blob":
                continue
            target = subprocess.run(
                ["git", "cat-file", "blob", f"{commit}:{path}"],
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
            if target.returncode != 0:
                escapes.append(path)
                continue
            candidate = Path(target.stdout)
            if candidate.is_absolute():
                escapes.append(path)
                continue
            try:
                resolved = (self.repo_root / candidate).resolve()
            except OSError:
                escapes.append(path)
                continue
            if resolved != self.repo_root and self.repo_root not in resolved.parents:
                escapes.append(path)
        return escapes

    def _claim_drift_outcome(
        self,
        manifest: Mapping[str, Any],
        claim: Mapping[str, Any] | None,
        action_scope: str,
        checkpoint_identity: str,
    ) -> dict[str, Any] | None:
        """Compare the live manifest against the claim's launch-record snapshot.

        Callers must pass a manifest snapshot read under the manifest lock,
        never an ambient unlocked read. The launch record (``baseline_revision``,
        ``generation``, ``launched_at``) is written atomically with the claim
        transition on the launch path; a genuinely pre-launch claim (no launch
        record, no recorded checkpoints, pending or claimed task status (or a
        commit-pending status recorded by the parent before any launch), claim
        state ``claimed``) undergoes no drift checks. When a record exists, the
        live claim drifts when its ``baseline_revision`` or ``generation`` no
        longer matches the snapshot, and a claim in any post-launch state whose
        record is missing also maps to ``stale-claim`` so record absence never
        disarms drift detection (covering manifests written across the
        re-activation or rollback window). A legacy claim carrying only a
        hand-written ``baseline_revision`` counts as its own snapshot. Returns
        ``None`` when the snapshot is valid or exempt, else the resumable
        ``stale-claim`` outcome.
        """

        task_id = str((claim or {}).get("task_id") or self._task_id_from_checkpoint(checkpoint_identity))
        task = manifest.get("tasks", {}).get(task_id, {})
        record = (claim or {}).get("launch_record")
        if not isinstance(record, Mapping):
            checkpoints_recorded = any(
                isinstance(entry, Mapping) and entry.get("task_id") == task_id
                for entry in manifest.get("checkpoints", {}).values()
            )
            pre_launch = (
                not checkpoints_recorded
                and task.get("status") in {"pending", "claimed", "commit-pending"}
                and (claim or {}).get("state") == "claimed"
            )
            has_legacy_baseline = bool(str((claim or {}).get("baseline_revision") or "").strip())
            if pre_launch or has_legacy_baseline:
                return None
            return _outcome(
                "blocked",
                "stale-claim",
                ["claim is in a post-launch state but has no launch record"],
                action_scope,
                checkpoint_identity,
                manifest.get("generation", 0),
                "preserve-and-reconcile",
            )
        drifted = (
            str((claim or {}).get("baseline_revision") or "") != str(record.get("baseline_revision") or "")
            or (claim or {}).get("generation") != record.get("generation")
        )
        if drifted:
            return _outcome(
                "blocked",
                "stale-claim",
                ["claim baseline or generation no longer matches the launch record"],
                action_scope,
                checkpoint_identity,
                manifest.get("generation", 0),
                "preserve-and-reconcile",
            )
        return None

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
        task = manifest["tasks"].get(task_id)
        if _claim_progressed_past_receipt(task, claim, include_terminal=True):
            # An explicit abort must not regress a task that already reached
            # its receipt boundary (done-pending, checkpointed, complete,
            # aborted) or a closed claim: the durable state stays untouched
            # and the resumable stale-claim outcome surfaces instead.
            return _stale_claim_outcome(
                token,
                claim.get("generation", manifest.get("generation", 0)),
                ["claim already progressed past the abort receipt"],
            )
        manifest["tasks"][task_id]["status"] = "aborted"
        claim["state"] = "aborted"
        manifest["workflow_state"] = "aborted"
        self._save(manifest)
        return _abort_outcome(token, claim.get("generation", 0), [f"task={task_id}"])

    @_locked_mutation
    def mark_commit_pending(self, task_id: str, commit_identity: str, log_evidence: Any = (), claim_token: str | None = None, generation: int | None = None) -> dict[str, Any]:
        """Persist the commit boundary before checkpoint completion."""

        manifest = self.refresh_manifest()
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id) if task else None
        if task is None or claim is None or claim.get("owner") != self.owner or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
            return _outcome("blocked", "owner-mismatch", [f"task={task_id}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile")
        if manifest.get("workflow_state") == "aborted":
            # A stale commit-pending write must never resurrect an aborted
            # workflow or overwrite its aborted task.
            return _abort_outcome(f"{task_id}:commit", manifest.get("generation", 0), ["workflow was explicitly aborted before the commit-pending write"], action_scope="done-handoff")
        if claim.get("state") == "closed" or task.get("status") in {"aborted", "checkpointed", "complete"}:
            # Progression fence: the commit boundary is owned by the live
            # launch window; a closed claim or a task that already reached a
            # later boundary (aborted, checkpointed, complete) is never
            # rewritten to commit-pending.
            return _stale_claim_outcome(
                f"{task_id}:commit",
                claim.get("generation", manifest.get("generation", 0)),
                ["claim already progressed past the commit-pending write"],
                action_scope="done-handoff",
            )
        task.update({"status": "commit-pending", "commit_identity": str(commit_identity), "done_log_evidence": bounded_evidence(log_evidence)})
        manifest["history"].append({"event": "commit-pending", "task_id": task_id, "commit_identity": str(commit_identity)})
        self._save(manifest)
        return _outcome("success", "commit-pending", [f"task={task_id}", f"commit={commit_identity}"], "done-handoff", f"{task_id}:commit", claim.get("generation", 0), "preserve-and-reconcile")

    def reconcile_commit_before_checkpoint(self, task_id: str, commit_identity: str, commit_lookup: Callable[[str], bool], claim_token: str | None = None, generation: int | None = None) -> dict[str, Any]:
        """Reconcile a provable commit; the next claim runs after the lock."""

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, f"{task_id}:commit", action_scope="done-handoff")
            outcome, claim_next = self._reconcile_commit_locked(task_id, commit_identity, commit_lookup, claim_token, generation)
        if claim_next:
            return self._attach_next_claim_action(outcome)
        return outcome

    def _reconcile_commit_locked(self, task_id: str, commit_identity: str, commit_lookup: Callable[[str], bool], claim_token: str | None, generation: int | None) -> tuple[dict[str, Any], bool]:
        manifest = load_manifest(self.manifest_path)
        task = manifest["tasks"].get(task_id)
        if task is None:
            return self._result_error(f"unknown task: {task_id}"), False
        if task.get("status") == "checkpointed" and task.get("commit_identity") == commit_identity:
            return _outcome("success", "completed", ["commit already reconciled"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[]), False
        claim = manifest["claims"].get(task_id)
        if not claim or claim.get("owner") != self.owner or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
            return _outcome("blocked", "owner-mismatch", ["commit recovery receipt does not match the live claim"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile"), False
        if task.get("commit_identity") != commit_identity or not task.get("done_log_evidence"):
            return _outcome("blocked", "commit-pending", ["matching done-log evidence and commit identity are required"], "done-handoff", f"{task_id}:commit", claim.get("generation", manifest.get("generation", 0)), "preserve-and-reconcile"), False
        if not commit_lookup(commit_identity):
            return _outcome("blocked", "commit-pending", [f"commit not found: {commit_identity}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile"), False
        # The committed artifact is verified exactly as the done handoff would
        # verify it: an out-of-scope or escaping commit is never reconciled
        # into a completed checkpoint. The drift snapshot check runs on the
        # same locked manifest the done handoff uses, so a claim whose launch
        # record drifted between quarantine and reconciliation surfaces
        # stale-claim here too.
        boundary = self._done_boundary_block(claim, commit_identity, f"{task_id}:commit", manifest.get("generation", 0), manifest=manifest)
        if boundary is not None:
            return boundary, False
        task.update({"status": "checkpointed", "checkbox": True, "complete": True, "commit_identity": commit_identity})
        manifest["checkpoints"][f"{task_id}:commit"] = {"task_id": task_id, "commit_identity": commit_identity, "reconciled": True}
        if task_id in manifest["claims"]:
            manifest["claims"][task_id]["state"] = "closed"
        self._save(manifest)
        return _outcome("success", "completed", [f"reconciled commit={commit_identity}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[]), True

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


def _operation_create(args: argparse.Namespace, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Seed the machine manifest from a plan task list.

    This is the only documented path that translates plan checkboxes into
    machine manifest state: it wraps ``create_manifest`` (the same seeding
    routine ``--selftest`` uses), validates every task's allowed-path entries
    against the same fail-closed path policy the launch envelope enforces,
    and refuses to overwrite an existing manifest.
    """

    if args.manifest is None:
        raise ValueError("--manifest is required")
    manifest_path = Path(args.manifest)
    tasks = payload.get("tasks")
    if isinstance(tasks, str) or not isinstance(tasks, (list, tuple, Mapping)):
        raise ValueError("create operation requires a task list under payload key 'tasks'")
    plan_slug = str(args.plan_slug or payload.get("plan_slug") or "")
    if not plan_slug.strip():
        raise ValueError("create operation requires --plan-slug (or payload plan_slug)")
    repo_root = Path(args.repo_root or Path.cwd()).resolve()
    for task in tasks.values() if isinstance(tasks, Mapping) else tasks:
        # Validate the item shape before any subscripting: a malformed list
        # item must raise the fail-closed ValueError, not a raw TypeError. A
        # mapping-valued input derives each id from its key, so the string-id
        # check applies only to list items.
        if not isinstance(task, Mapping) or (
            not isinstance(tasks, Mapping) and not isinstance(task.get("id"), str)
        ):
            raise ValueError("create operation tasks must be mappings with a string id")
        for entry in task.get("allowed_paths", task.get("files", ())):
            _safe_relative_path(repo_root, str(entry))
    # The lock lease is independent of manifest existence: fencing the
    # exists-check, create, and owner write inside _manifest_lock makes a
    # concurrent create fail closed instead of last-writer-wins.
    with _manifest_lock(manifest_path, str(args.owner or f"create-{uuid.uuid4().hex}")) as acquired:
        if not acquired:
            raise ValueError(f"manifest creation is held by another owner: {manifest_path}")
        if manifest_path.exists():
            raise ValueError(f"manifest already exists; create refuses to overwrite: {manifest_path}")
        manifest = create_manifest(manifest_path, plan_slug, tasks)
        if args.owner:
            manifest["owner"] = args.owner
            _safe_write_json(manifest_path, manifest)
    return _outcome(
        "success",
        "created",
        [f"manifest={manifest_path}", f"tasks={len(manifest['tasks'])}", f"plan={plan_slug}"],
        "repository-task",
        f"create:{plan_slug}",
        manifest["generation"],
        "continue-parent",
        actions=[],
    )


def _git_commit_matching_reference(repo_root: Path, reference: str) -> bool:
    """True when a HEAD-reachable commit message contains the fixed string.

    ``git log -F --grep`` pins the reference to a fixed-string match: a
    ``.`` inside a reference must never act as a basic-regex wildcard. Any
    witness failure counts as no match (fail closed).
    """

    completed = subprocess.run(
        ["git", "log", "-F", "--format=%H", f"--grep={reference}", "HEAD"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def verify_preconditions(repo_root: Path | str, document: Mapping[str, Any]) -> dict[str, Any]:
    """Verify declared predecessor work repository-locally; manifest-free.

    Reads a predecessors JSON document (``{"predecessors": [...]}``) plus the
    repository root; no machine manifest is loaded or required. Each
    predecessor's outcomes are OR-combined per reference. The driver evaluates
    only the repository-local kinds ``history-ref``, ``ancestry``, and
    ``artifact``; the plan-declared ``validator`` kind is orchestrator-run
    (exit evidence lives in ``manifest.md``) and never executes here. Any
    malformed declaration, malformed document-level shape (non-mapping
    document, or a ``predecessors`` value present but not a list), or
    all-outcomes-fail predecessor returns the fail-closed blocked outcome with
    a diagnostic naming the reference and every outcome tried.
    """

    root = Path(repo_root).resolve()

    def _malformed_document(diagnostic: str) -> dict[str, Any]:
        return _outcome(
            "blocked",
            "precondition-unverified",
            [diagnostic],
            "repository-read",
            "precondition:verify",
            0,
            "preserve-and-reconcile",
            resume_allowed=True,
            predecessors=[],
        )

    if not root.is_dir():
        # A missing or non-directory root would otherwise crash the git
        # witnesses below with a traceback; fail closed instead.
        return _malformed_document(
            "repository root missing or not a directory: {}".format(root)
        )

    # Reuse the driver's existing git witnesses without constructing a driver:
    # construction would load a machine manifest, which this manifest-free
    # operation must never do.
    witness = RuntimeDriver.__new__(RuntimeDriver)
    witness.repo_root = root
    head = witness._git_head_revision()

    # Document-level shape fails closed: a missing key (or empty list) is the
    # plan-without-predecessors success path, but a present-yet-non-list
    # `predecessors` value (including null) must never degrade to [] and pass.
    if not isinstance(document, Mapping):
        return _malformed_document("malformed predecessors document: expected a JSON object mapping")
    if "predecessors" in document:
        predecessors = document["predecessors"]
        if not isinstance(predecessors, (list, tuple)):
            return _malformed_document("malformed predecessors document: 'predecessors' must be a list")
    else:
        predecessors = []
    evidence: list[str] = []
    diagnostics: list[str] = []
    per_predecessor: list[dict[str, Any]] = []

    def evaluate(outcome: Mapping[str, Any]) -> bool:
        kind = str(outcome.get("kind", ""))
        if kind == "history-ref":
            value = outcome.get("value")
            return isinstance(value, str) and bool(value.strip()) and _git_commit_matching_reference(root, value)
        if kind == "ancestry":
            value = outcome.get("value")
            if not isinstance(value, str) or not value.strip() or not head:
                return False
            is_descendant, witness_ok = witness._git_commit_is_descendant(value, head)
            return witness_ok and is_descendant
        if kind == "artifact":
            path = outcome.get("path")
            contains = outcome.get("contains")
            if not isinstance(path, str) or not isinstance(contains, str) or not contains:
                return False
            try:
                resolved = _safe_relative_path(root, path)
                text = (root / resolved).read_text(encoding="utf-8")
            except (OSError, ValueError):
                return False
            return contains in text
        return False

    for declaration in predecessors:
        ref = declaration.get("ref") if isinstance(declaration, Mapping) else None
        ref_label = ref if isinstance(ref, str) and ref.strip() else "<missing>"
        outcomes = declaration.get("outcomes") if isinstance(declaration, Mapping) else None
        if (
            not isinstance(declaration, Mapping)
            or not isinstance(ref, str)
            or not ref.strip()
            or not isinstance(outcomes, (list, tuple))
            or not outcomes
        ):
            diagnostics.append(f"malformed predecessor declaration: ref={ref_label} requires a non-empty ref and a non-empty outcomes list")
            per_predecessor.append({"ref": ref_label, "verified": False, "verified_by": None})
            continue
        verified_by: dict[str, Any] | None = None
        attempted: list[str] = []
        malformed = False
        for outcome in outcomes:
            if not isinstance(outcome, Mapping):
                malformed = True
                attempted.append("malformed-outcome")
                continue
            kind = str(outcome.get("kind", ""))
            if kind not in {"history-ref", "ancestry", "artifact", "validator"}:
                malformed = True
                attempted.append(f"unknown-kind {kind or '<missing>'}")
                continue
            if kind == "validator":
                # Orchestrator-run outcome: the driver never executes
                # plan-declared commands; it contributes no verification here.
                attempted.append("validator (orchestrator-run; exit evidence in manifest.md)")
                continue
            raw_target = outcome.get("value") or outcome.get("path")
            detail = str(raw_target or "<missing>")
            if kind in {"history-ref", "ancestry"} and isinstance(raw_target, str) and raw_target.startswith("-"):
                # A leading dash can never be a valid work-item reference; it
                # is a malformed declaration, not an outcome that merely fails.
                malformed = True
                attempted.append(f"{kind} {detail} (malformed declaration: leading-dash value)")
                continue
            if kind == "artifact" and (
                not isinstance(outcome.get("path"), str)
                or not isinstance(outcome.get("contains"), str)
                or not outcome.get("contains")
            ):
                # A structurally-broken artifact declaration (missing or
                # non-string path; missing, empty, or non-string contains)
                # cannot be evaluated at all — malformed, not merely failed.
                malformed = True
                attempted.append(f"artifact {detail} (malformed declaration)")
                continue
            attempted.append(f"{kind} {detail}")
            if verified_by is None and evaluate(outcome):
                verified_by = {"kind": kind, "target": str(raw_target or "")}
        per_predecessor.append({"ref": ref, "verified": verified_by is not None, "verified_by": verified_by})
        if verified_by is not None:
            evidence.append(f"ref={ref} verified by {verified_by['kind']}")
        else:
            note = " (malformed declaration)" if malformed else ""
            diagnostics.append(f"predecessor ref={ref} unverified{note}; outcomes tried: {', '.join(attempted)}")
    if diagnostics:
        return _outcome(
            "blocked",
            "precondition-unverified",
            diagnostics,
            "repository-read",
            "precondition:verify",
            0,
            "preserve-and-reconcile",
            resume_allowed=True,
            predecessors=per_predecessor,
        )
    return _outcome(
        "success",
        "completed",
        evidence or ["no predecessors declared"],
        "repository-read",
        "precondition:verify",
        0,
        "continue-parent",
        predecessors=per_predecessor,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--operation", choices=("create", "claim", "checkpoint", "done", "resume", "continue", "terminal", "precondition"))
    parser.add_argument("--predecessors-file", type=Path, help="predecessors JSON document for the manifest-free precondition operation")
    parser.add_argument("--input", help="JSON object for create, checkpoint, or done")
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
        if args.operation == "precondition":
            # Manifest-free end to end: the precondition operation runs from a
            # predecessors document and the repository root alone.
            if args.predecessors_file is None:
                parser.error("--predecessors-file is required for --operation precondition")
        elif args.manifest is None or args.operation is None:
            parser.error("--manifest and --operation are required unless --selftest is used (or --operation precondition with --predecessors-file)")
        profile = capabilities.load_profiles().get(capabilities.canonicalize_runtime_id(args.runtime)) if args.runtime else None
        adapter_kwargs = {}
        if args.approval_receipt is not None:
            receipt = capabilities.load_approval_receipt(args.approval_receipt)
            if args.runtime and capabilities.canonicalize_runtime_id(args.runtime) != receipt["runtime"]:
                raise ValueError("approval receipt runtime does not match --runtime")
            adapter_kwargs["approval_receipt"] = args.approval_receipt
        adapter = capabilities.resolve_adapter(args.runtime, args.repo_root or Path.cwd(), **adapter_kwargs) if args.runtime else None
        payload = json.loads(args.input) if args.input else {}
        if args.operation == "create":
            # The manifest does not exist yet: create runs before any driver
            # construction and owns the seeding boundary itself.
            result = _operation_create(args, payload)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.operation == "precondition":
            # Manifest-free: no driver is constructed and no manifest loaded;
            # the repository root resolves from --repo-root or the cwd. An
            # unreadable or unparsable predecessors file fails closed as a
            # malformed document naming the file, never as a traceback.
            try:
                with Path(args.predecessors_file).open(encoding="utf-8") as stream:
                    document = json.load(stream)
            except (OSError, ValueError) as exc:
                result = _outcome(
                    "blocked",
                    "precondition-unverified",
                    [f"malformed predecessors document {args.predecessors_file}: {exc}"],
                    "repository-read",
                    "precondition:verify",
                    0,
                    "preserve-and-reconcile",
                    resume_allowed=True,
                    predecessors=[],
                )
                print(json.dumps(result, sort_keys=True))
                return 0
            result = verify_preconditions(Path(args.repo_root or Path.cwd()).resolve(), document)
            print(json.dumps(result, sort_keys=True))
            return 0
        driver = RuntimeDriver(
            args.manifest,
            plan_slug=args.plan_slug,
            adapter=adapter,
            profile=profile,
            owner=args.owner,
            repo_root=args.repo_root,
        )
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
