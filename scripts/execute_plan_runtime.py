#!/usr/bin/env python3
"""Durable, provider-neutral continuation driver for execute-plan.

The driver owns the file-backed state machine and policy boundary. Host-specific
process and session handling belongs in an adapter such as
``execute_plan_runtime_codex``.
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import fcntl
import fnmatch
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

import runtime_capabilities as capabilities
from execute_plan_worker_registry import WorkerRegistry, validate_manifest_worker_schema, validate_provider_observation
from runtime_capabilities import bounded_evidence


STATUSES = {"success", "contract-violation", "blocked", "aborted", "error"}
SCHEMA_VERSION = 1

# Standing resume watcher receipt schema: the workflow-neutral watcher module
# owns it (dependency direction runtime -> watcher, never reverse).
# The names below re-point there lazily so a layout staged without the
# watcher module keeps importing this driver.
WORKFLOW_STATES = {"active", "blocked", "complete", "terminal", "aborted"}
# The progressed set: once a task reaches one of these statuses its plan
# checkboxes must agree with the manifest (the manifest wins per the seeding
# boundary). Shared by the readiness decision and the reclaim progression
# guard.
PROGRESSED_TASK_STATUSES = {"done-pending", "commit-pending", "checkpointed", "complete"}
# The closed recovery-disposition set for the done-pending recovery
# transition (``recover_done_pending``): the operator's durable choice for
# the recovered task. ``requeue`` returns the task to pending under a newly
# authorized generation; ``defer`` marks the task ``deferred`` with linked
# backlog evidence; ``abort`` ends the run.
RECOVERY_DISPOSITIONS = ("requeue", "defer", "abort")
# The append-only history event recording one done-pending recovery. Its
# identity (task id plus claim token plus claim generation) fences duplicate
# receipts: a second recovery of the same wedged claim identity is refused.
DONE_PENDING_RECOVERY_EVENT = "done-pending-recovery"
# Claim lease for the reclaim operation: the claim `timestamp` is written once
# at claim time and never renewed, so a claim is reclaimable only after this
# many seconds. 14400 (four hours) is an order of magnitude above the
# execute-plan 20-minute per-worker timeout, so a live worker's task normally
# completes well inside the lease; a task still running past the lease has its
# post-reclaim checkpoint fail fenced as owner-mismatch rather than corrupting
# state. Driver-owned code: no environment variable or CLI flag overrides it.
CLAIM_LEASE_SECONDS = 14400
# Claim states the reclaim operation admits (the live set plus a claim fenced
# by a blocked receipt whose worker is gone).
RECLAIMABLE_CLAIM_STATES = {"claimed", "launched", "blocked"}
# Budget of the waiting-capacity parking policy: a capacity receipt parks a
# single-task claim with this many resumptions on the claim's retry policy,
# each successive capacity receipt consumes one, and the receipt that arrives
# with the budget at zero moves the claim to `blocked`. Driver-owned code: no
# environment variable or CLI flag overrides it.
WAITING_CAPACITY_RETRY_ATTEMPTS = 3
# The closed batch claim-group state set (the manifest validator and the
# group-state mutation primitive share it): `failed` is the terminal state the
# reclaim-time group release and the advance-time group-failure belt
# write; every consumer keys on == "active", so a failed group routes
# no member action.
BATCH_GROUP_STATES = {"active", "closed", "failed"}
HANDOFF_STATES = {"prepared", "launching", "launched", "receipt-persisted", "failed", "ambiguous"}
HANDOFF_TRANSITIONS = {
    "prepared": {"launching", "failed"},
    "launching": {"launched", "failed", "ambiguous"},
    "launched": {"receipt-persisted", "ambiguous"},
    "receipt-persisted": set(),
    "failed": set(),
    "ambiguous": {"failed"},
}
# The group-kind discriminator in the manifest group record. `batch` is the
# pre-existing one-worker sequential protocol (also the reading for legacy
# records written before the field existed); `parallel` is the concurrent
# single-task-worker protocol: members launch together, each on its own
# session, claim, policy token, and log path, with no anchor session and no
# active-member ordinal gate. Every group-protocol branch reads the kind
# through `_claim_group_kind` so a missing field can never change batch
# behavior.
GROUP_KIND_BATCH = "batch"
GROUP_KIND_PARALLEL = "parallel"
# The batch numeric caps: the one source of truth shared by the batch prefix
# computation and the parallel-group claim refusals (a parallel implement
# group never exceeds the batch contract's known-safe size - 4 members, 8
# combined canonical member files). Driver-owned code: the caps are contract
# constants, never environment-tunable.
PARALLEL_GROUP_MEMBER_CAP = 4
PARALLEL_GROUP_COMBINED_FILE_CAP = 8
# Claim states a parallel-group member's claim may hold when its group
# closes: `closed` (the member's done landed), `replaced` (released by the
# per-member reclaim exit or the session-less resume release), or `aborted`
# (explicitly stopped). Close = the last member reaching one of these; a
# released or stopped member never wedges an otherwise complete group.
PARALLEL_MEMBER_TERMINAL_CLAIM_STATES = {"closed", "replaced", "aborted"}
# The terminal gate bounds its archived-plan read at 1,000,000 bytes: a plan
# at or under the bound is read whole (the unchecked-checkbox scan covers the
# entire file), and a plan over the bound is refused outright instead of
# prefix-scanned. The readiness operation applies the same bound to its plan
# read.
PLAN_READ_LIMIT = 1_000_000
# The diagnose classification map: the fixed, closed mapping from a history
# failure event to the first-failed-transition classification. The worker-failure
# class covers the whole non-resumable worker-failure family including
# cleanup-unverified; stale-claim receipts are stale evidence, and
# precondition-unverified receipts are inclusion failures. Cancellation is
# deliberately absent as a class: a cancelled worker's receipts already carry
# the timeout, malformed-result, or cleanup-unverified codes and classify under
# those. Driver-owned code: a new recurring gate is a backlog decision, never a
# silent extension of this table.
DIAGNOSE_REASON_CLASSIFICATIONS = {
    "timeout": "timeout",
    "capacity-unavailable": "capacity-unavailable",
    "malformed-result": "worker-failure",
    "runtime-error": "worker-failure",
    "runtime-policy-unavailable": "worker-failure",
    "cleanup-unverified": "worker-failure",
    "stale-claim": "stale-evidence",
    "precondition-unverified": "inclusion",
}
# Workflow-scoped failure events that carry no reason code: the terminal
# refusal tail's evidence write and the user interruption fence.
DIAGNOSE_EVENT_CLASSIFICATIONS = {
    "terminal-refused": "terminal-gate",
    "user-interrupt-recorded": "user-interruption",
}


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
# Ambient worktree noise tolerated by name shape: pre-launch (nothing proves
# the noise was worker-caused) a purely ambient dirty worktree blocks
# resumably for cleanup; post-launch, the worktree scope witness consults
# the same allowlist only to DOWNGRADE its verdict (untracked arm
# tightened by the later review): when every out-of-scope path is porcelain-proven
# untracked AND ambient-shaped the blocked outcome is the resumable
# cleanup-required envelope, and any tracked out-of-scope modification or
# non-ambient out-of-scope path keeps the terminal contract-violation. A
# tracked in-scope change is never affected: only out-of-scope paths reach
# the ambient discriminator.
AMBIENT_NOISE_PATTERNS = (
    ".DS_Store",
    ".DS_Store?",
    "._.DS_Store",
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


def _read_plan_bounded(
    repo_root: Path | None,
    path: Path | str,
    require_safe_path: bool,
) -> tuple[str | None, str | None]:
    """Read a plan file under one shared bounded-read policy.

    Returns ``(text, error)`` with exactly one of the two ``None``; each
    error is a predicate fragment the caller prefixes with its own subject
    ("archived plan" / "plan file") to build its refusal envelope. The
    policy is identical for every call site (terminal gate, pre-archive
    mirror, and readiness):

    - with ``require_safe_path`` (terminal gate and pre-archive mirror) the
      path must first resolve through the fail-closed path policy
      (repository-relative, non-escaping, shell-marker-free) under
      ``repo_root``;
    - the target must be a regular file, proven on the open descriptor
      itself: the file is opened with
      ``os.open(O_RDONLY | O_NONBLOCK | O_CLOEXEC)`` (the nonblocking flag
      makes the open itself unable to block on a FIFO with no writer) and
      ``os.fstat`` classifies that descriptor through ``stat.S_ISREG``
      before any byte is read. There is no check-then-open window at all:
      the file cannot be swapped between a pre-open classification and the
      read, because the classified object IS the read object. A named pipe
      (whose stat size is 0 and whose blocking read would hang forever),
      a device, and a directory are all refused through this one gate;
    - the read is bounded without any stat size gate (a stat-then-read
      window lets the file grow past the checked size): the descriptor is
      wrapped with ``os.fdopen`` and the stream reads at most
      ``PLAN_READ_LIMIT + 1`` bytes and ``len(data)`` over
      ``PLAN_READ_LIMIT`` refuses the plan outright, so the
      whole-file scan promise is proven at read time and an over-limit plan
      is never prefix-scanned.

    Decoding uses ``errors="replace"`` so hostile bytes cannot crash a gate.
    The decoded text is stripped here, once, so every consumer (the two
    empty-refusal sites and the readiness decision) shares one text and an
    empty-or-whitespace-only artifact is a plain falsy check downstream;
    callers that split the text into lines number them from the stripped
    form, so leading or trailing blank lines shift no interior number.
    """

    if require_safe_path:
        try:
            if repo_root is None:
                return None, "is not resolvable: no repository root is configured"
            relative = _safe_relative_path(repo_root, str(path).strip())
        except ValueError:
            return None, "is not a safe repository-relative path under the repository root"
        plan_path = repo_root / relative
    else:
        plan_path = Path(path)
    try:
        fd = os.open(plan_path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as exc:
        return None, f"is missing or unreadable: {plan_path}: {exc}"
    stream = None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            # Regular-file gate on the open descriptor: a FIFO passes every
            # size check (its stat size is 0) and would hang a blocking read
            # forever; O_NONBLOCK already made the open itself non-blocking,
            # and S_ISREG refuses FIFOs, devices, and directories before any
            # byte is read. The classification is of the very descriptor the
            # read would consume, so nothing can slip in between the check
            # and the open.
            return None, f"is not a regular file: {plan_path}"
        stream = os.fdopen(fd, "rb")
        data = stream.read(PLAN_READ_LIMIT + 1)
    except OSError as exc:
        return None, f"is missing or unreadable: {plan_path}: {exc}"
    finally:
        # The descriptor has exactly one closer: before os.fdopen succeeds
        # the raw fd is ours to close; afterwards the stream owns it, and
        # closing the stream closes the fd. Either way the descriptor never
        # leaks on a refusal or a read error.
        if stream is None:
            os.close(fd)
        else:
            stream.close()
    if len(data) > PLAN_READ_LIMIT:
        # The +1 read replaces a stat size gate: len(data) over the limit
        # proves, at read time and without any stat-then-read window, that
        # the whole-file scan promise cannot be kept.
        return None, f"exceeds the bounded read limit: over {PLAN_READ_LIMIT} bytes"
    # Strip once here so every consumer shares one text: the empty-refusal
    # sites check plain falsiness, and the readiness decision scans the same
    # stripped form the refusal sites saw. A checkbox line is never
    # whitespace, so the strip can only drop blank edge lines, never a
    # scannable marker line.
    return data.decode("utf-8", errors="replace").strip(), None


def _resolved_facts_dir(repo_root: Path, key: str) -> Path | None:
    """Resolve a facts TOML-fence directory key anchored at the repository root.

    The archive gate resolves its directory keys through the SINGLE
    TOML-fence parser (``facts_paths.resolve_toml_key_raw``): this
    repository's facts file stores the keys inside the ```toml fence, which
    the markdown table-row parser cannot read. The raw value is anchored at
    the driver's repository root (never the process CWD, which a relative
    value would otherwise resolve against). A missing facts file, a missing
    key, or a sibling ``facts_paths`` module returns ``None`` and the caller
    refuses: fail closed, because the gate has no default destination.
    """

    try:
        import facts_paths
    except ImportError:
        return None
    try:
        raw = facts_paths.resolve_toml_key_raw(repo_root, key)
    except AttributeError:
        # A shadowing ``facts_paths`` module without the resolver must fail
        # closed exactly like the missing-module case: the caller refuses
        # with the missing-key evidence instead of surfacing a traceback.
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _sha256_capped(path: Path) -> tuple[str | None, str | None]:
    """sha256 digest over at most ``PLAN_READ_LIMIT`` bytes.

    Returns ``(digest, error)`` with exactly one of the two ``None``. The
    byte digest, not a digest over the decoded text, is what the staged
    terminal contract recomputes over the archived bytes, so the recorded
    ``plan_digest`` always refers to the file bytes.
    """

    try:
        with path.open("rb") as stream:
            data = stream.read(PLAN_READ_LIMIT + 1)
    except OSError:
        return None, "is unreadable"
    if len(data) > PLAN_READ_LIMIT:
        return None, "exceeds the bounded read limit"
    return hashlib.sha256(data).hexdigest(), None


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


def _normalize_residual_policy(residual_policy: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Validate the optional structured ``residual_policy`` pre-archive input.

    The sanctioned residual-acceptance exit (origin D) supplies the named
    finding set as integers matching the version-1 sidecar's integer
    finding ids, the grant's source, and the recorded-at epoch. The input
    is optional: ``None`` means no policy was recorded and the gate keeps
    its landed clean-round reading. A present policy is validated
    fail-closed and returns ``(policy, None)`` only when every field
    carries its documented shape; any malformed field returns
    ``(None, error)`` with the evidence string the gate refuses on.
    """

    if residual_policy is None:
        return None, None
    if not isinstance(residual_policy, Mapping):
        return None, "residual_policy must be a JSON object when present"
    finding_ids = residual_policy.get("finding_ids")
    if not isinstance(finding_ids, list) or not finding_ids:
        return None, "residual_policy.finding_ids must be a non-empty list when residual_policy is present"
    if any(isinstance(finding_id, bool) or not isinstance(finding_id, int) for finding_id in finding_ids):
        return None, "residual_policy.finding_ids must be integers matching the sidecar's integer finding ids"
    grant_source = residual_policy.get("grant_source")
    if not isinstance(grant_source, str) or not grant_source.strip():
        return None, "residual_policy.grant_source must be a non-empty string when residual_policy is present"
    recorded_at = residual_policy.get("recorded_at")
    if isinstance(recorded_at, bool) or not isinstance(recorded_at, (int, float)):
        return None, "residual_policy.recorded_at must be an epoch timestamp when residual_policy is present"
    if not math.isfinite(recorded_at):
        # NaN and the infinities parse as JSON numbers but poison the
        # ordering proof (NaN compares False against every round-day
        # epoch, so a NaN policy would "predate" every round); refuse
        # them here so the proof stays total over the values it admits.
        return None, f"residual_policy.recorded_at must be a finite epoch timestamp; supplied {recorded_at!r} cannot order the policy against the sidecar round date"
    return {"finding_ids": list(finding_ids), "grant_source": grant_source.strip(), "recorded_at": recorded_at}, None


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
    if "claims" in value and not isinstance(value["claims"], dict):
        # Claims-container shape refusal: consumer sites split two ways.
        # Some read the container through ``.get("claims", {})``, which
        # treats an absent key as no open claims; others index the
        # container directly (``manifest["claims"]``), where an absent key
        # raises ``KeyError`` that the CLI top-level handler catches and
        # prints as a failure line. Neither rescues a present-but-
        # non-mapping value, so a malformed shape used to crash the first
        # iterating consumer (``_pre_archive_gate``) with an
        # ``AttributeError`` the CLI top-level handler does not catch.
        # Refuse here, beside the ``tasks`` check, so the operator sees the
        # failure line; an absent key stays legal (both consumer shapes
        # already tolerate it).
        raise ValueError("runtime manifest claims must be a mapping")
    # Legacy manifests are accepted and migrated in memory.  The driver adds
    # the sections to the next valid locked mutation; the registry remains a
    # pure reducer over the detached manifest.
    # Validation returns the detached migrated document.  Returning the
    # original value here discarded legacy workers/capacity sections and made
    # migration persistence dependent on a caller remembering to migrate it.
    return validate_manifest_worker_schema(value)


def create_manifest(
    path: Path | str,
    plan_slug: str,
    tasks: list[Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
    profile: Mapping[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Create the authoritative machine manifest with restrictive permissions.

    When ``repo_root`` is supplied, every task's raw ``Files:`` entries are
    canonicalized through the same fail-closed path policy the launch
    envelope enforces and persisted as canonical ``allowed_paths``;
    within-task entries that resolve to one canonical path (lexical aliases
    such as ``./a`` versus ``a``, or an in-repository symlink and its
    target) are rejected. Each task also gains a persisted document
    ``ordinal`` (its document position), which claim selection, pending
    selection, and batch member advancement consume. Cross-task canonical
    overlap is retained, never rewritten: queue stopping needs to see it.
    """

    if isinstance(tasks, Mapping):
        task_items = list(tasks.items())
    else:
        task_items = [(str(task["id"]), task) for task in tasks]
    if not task_items:
        # Library-callers wedge guard: a zero-task manifest would
        # answer every later claim with a silent success no-op while
        # readiness and terminal refuse the empty run, so the seeding
        # boundary itself refuses it (the CLI create operation refuses
        # earlier with its own message).
        raise ValueError("create requires at least one task")
    canonical_root = Path(repo_root).resolve() if repo_root is not None else None
    task_map: dict[str, dict[str, Any]] = {}
    for position, (task_id, task) in enumerate(task_items):
        item = dict(task)
        item.setdefault("id", task_id)
        item.setdefault("status", "pending")
        item.setdefault("checkbox", item["status"] == "complete")
        item.setdefault("ordinal", position)
        raw_paths = item.get("allowed_paths", item.get("files"))
        if canonical_root is not None and raw_paths is not None:
            canonical_paths: list[str] = []
            seen: set[str] = set()
            for entry in raw_paths:
                resolved = _safe_relative_path(canonical_root, str(entry))
                if resolved in seen:
                    raise ValueError(
                        f"task {task_id} lists duplicate canonical allowed path after alias resolution: {entry} -> {resolved}"
                    )
                seen.add(resolved)
                canonical_paths.append(resolved)
            item["allowed_paths"] = canonical_paths
            item.pop("files", None)
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
        # Budget-boundary watcher authority: the monotonic semantic progress
        # revision plus the fenced resume-watcher receipt (null when no
        # watcher is pending). See execute_plan_resume_watcher.
        "progress_revision": 0,
        "boundary_generation": 0,
        "resume_watcher": None,
        "user_interrupt": None,
        "tasks": task_map,
        "evidence_contract_digest": capabilities.evidence_contract_digest(task_map),
        "evidence_enforcement": False,
        "claims": {},
        "workers": {},
        "capacity": {"version": 1, "entries": {}, "reservations": {}},
        # Authoritative batch implement launch groups (Step 1.2 batch
        # contract); empty for the default-off single-task path.
        "claim_groups": {},
        "handoff_intents": {},
        "checkpoints": {},
        "verification_evidence": {},
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
    """Marker: the adapter resume runs after the manifest lock is released.

    ``retry_policy`` rides only on the batch-member retry window:
    the driver-owned decremented budget the resumed receipt is forced to,
    so a hostile envelope cannot re-supply attempts each round. The plain
    resume-selection window leaves it None.
    """

    task: Mapping[str, Any]
    claim: Mapping[str, Any]
    retry_policy: Mapping[str, Any] | None = None


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


def _reclaim_evidence_lines(task_id: str, replaced_token: str, replacement_token: str, replaced_generation: int) -> list[str]:
    """Compose the reclaim success evidence lines (pure; no I/O).

    Pins the pre-redaction label contract: the OLD claim token is
    carried under ``replaced_token=`` and the NEW rotated token under
    ``replacement_token=``. The durable envelope redacts both values, so the
    returned evidence alone cannot prove which token each label carries;
    this helper is the pinned source of that mapping and is asserted
    directly with distinct values in the suite.
    """

    return [
        f"task={task_id}",
        f"replaced_token={replaced_token}",
        f"replacement_token={replacement_token}",
        f"generation={replaced_generation}",
        f"lease_seconds={CLAIM_LEASE_SECONDS}",
    ]


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
) -> bool:
    """True when a stale non-success receipt must not regress the durable state.

    Every progressed status (``done-pending``, ``commit-pending``,
    ``checkpointed``, ``complete``, ``aborted``) and a closed claim are shared
    by every emission site: a receipt arriving for an aborted task or claim
    must never persist.
    """

    if (claim or {}).get("state") == "closed":
        return True
    # The progressed set plus the one delta this guard owns: an ``aborted``
    # task must never regress either, so deriving from
    # PROGRESSED_TASK_STATUSES keeps the receipt guard in lockstep with the
    # reclaim and readiness progression guards by construction.
    statuses = PROGRESSED_TASK_STATUSES | {"aborted"}
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


def _printable_evidence(text: str) -> str:
    """Presentation-only control-character escape for operator-facing evidence.

    Control bytes (tabs, newlines, ESC, and other non-printables) become
    literal ``\\xNN`` escapes, or ``\\uNNNN`` for non-printables above
    U+00FF, so a hostile path cannot smuggle them into console, log, or
    durable-JSON rendering of evidence; printable text, including
    non-ASCII, passes through unchanged.
    """

    return "".join(
        ch if ch.isprintable() else ("\\x" + format(ord(ch), "02x") if ord(ch) <= 0xFF else "\\u" + format(ord(ch), "04x"))
        for ch in text
    )


_TASK_SECTION_HEADING = re.compile(r"^### Task (\d+):")


def _pending_sort_key(task: Mapping[str, Any]) -> tuple[int, str]:
    """The canonical queue order key shared by claim, resume, readiness, and
    the batch prefix.

    The persisted document ordinal (``create_manifest`` seeds it) is the
    canonical queue order; ``number`` then ``id`` remain the legacy fallback
    for manifests that predate ordinals. One owner for the key: a
    divergent or number-based key at any selection site breaks document
    order on ordinary 10+ task plans (ids sort lexicographically) and makes
    the batch member ordinals disagree with the plan.
    """

    ordinal = task.get("ordinal", task.get("number", 0))
    if isinstance(ordinal, bool) or not isinstance(ordinal, int):
        ordinal = 0
    return ordinal, str(task.get("id", ""))


def _plan_task_number(task_id: str) -> int | None:
    """Return the plan number from a canonical or legacy numeric task ID."""

    if task_id.isdigit():
        return int(task_id)
    prefix = "task-"
    if not task_id.startswith(prefix):
        return None
    suffix = task_id[len(prefix):]
    return int(suffix) if suffix.isdigit() else None


def _plan_fence_opener(line: str) -> tuple[str, int] | None:
    """The ``(character, width)`` fence opener when the line opens a fence.

    CommonMark opening rule: zero to three leading spaces, then a run of
    three or more backticks or tildes, then an optional info string; a
    backtick opener's info string carries no backtick, so a line like
    `` ```a`b `` opens nothing. Indent beyond three spaces (including a
    leading tab) makes the line literal text, never a fence.
    """

    indent = len(line) - len(line.lstrip(" "))
    if indent > 3:
        return None
    body = line[indent:]
    for character in ("`", "~"):
        width = 0
        while width < len(body) and body[width] == character:
            width += 1
        if width >= 3:
            if character == "`" and "`" in body[width:]:
                return None
            return character, width
    return None


def _plan_fence_map(lines: Sequence[str]) -> list[bool]:
    """Per-line fence-state table over the WHOLE plan's lines (pure; no I/O).

    ``fenced[i]`` is True when ``lines[i]`` belongs to a fenced code block:
    its opener line, its content lines, and its closer line. CommonMark
    rules: an opener is ``_plan_fence_opener``'s run of three or more
    backticks or tildes with an optional info string; a closing line uses
    the same character at an equal or greater width and is bare (zero to
    three leading spaces, nothing after the run); nested fences of
    different widths do not close a wider fence early; an unclosed fence
    stays open to end of file. The map is computed once over the whole
    plan's lines, so fence parity never restarts at a section boundary: a
    fence opened in one task's body keeps every later heading inside it
    fenced until its matching closer appears.
    """

    fenced: list[bool] = []
    open_character = ""
    open_width = 0
    for line in lines:
        if open_character:
            fenced.append(True)
            indent = len(line) - len(line.lstrip(" "))
            body = line[indent:] if indent <= 3 else ""
            if len(body) >= open_width and body == open_character * len(body):
                open_character, open_width = "", 0
            continue
        opener = _plan_fence_opener(line)
        if opener is not None:
            open_character, open_width = opener
            fenced.append(True)
        else:
            fenced.append(False)
    return fenced


def _plan_task_section_lines(lines: Sequence[str], number: int) -> list[str] | None:
    """Extract one plan task section from pre-split plan lines.

    The heading match pins the task number against its terminating colon, so
    the Task 1 section never scans Task 10's heading or content. The section
    spans from its heading line to the next ``## `` heading line or the next
    ``### Task <N>:`` heading line, or end of file. A nested ``###`` subsection
    (for example ``### Notes:``) belongs to the task section, so lower
    unchecked checkboxes stay visible to the agreement scan. Both the heading
    search and the section walk consume ``_plan_fence_map`` computed once over
    the whole plan's lines: a fenced ``## `` or ``### Task <N>:`` line is
    fenced content, never a heading or a break marker, so a fenced example
    cannot truncate the section or hijack the section start; parity never
    restarts at the section start, and an unclosed fence keeps every later
    heading unfound so the caller fails closed on the missing section.
    Returns None when the lines carry no unfenced section for ``number``.
    """

    fenced = _plan_fence_map(lines)
    start: int | None = None
    for index, line in enumerate(lines):
        if fenced[index]:
            continue
        match = _TASK_SECTION_HEADING.match(line)
        if match is not None and int(match.group(1)) == number:
            start = index + 1
            break
    if start is None:
        return None
    section: list[str] = []
    for index in range(start, len(lines)):
        line = lines[index]
        if not fenced[index] and (line.startswith("## ") or _TASK_SECTION_HEADING.match(line)):
            break
        section.append(line)
    return section


def _unchecked_checkbox_pairs(lines: Sequence[str]) -> list[tuple[int, str]]:
    """``(1-based line number, line)`` pairs for unchecked checkbox lines.

    The line-anchored reading: a line counts only when its first
    non-whitespace token is an unchecked GFM task-list marker, one of
    ``- [ ]``, ``* [ ]``, or ``+ [ ]``; a mid-prose mention of the marker
    does not start its line and never counts. One scan computes the number
    during the walk, so a duplicated line is never resolved through an
    ambiguous text search and the helper has no dead no-match path.
    Evidence line numbers are positions in the sequence the caller passes,
    which is always ``str.splitlines()`` output: they count ``splitlines()``
    boundaries, which differ from a plain ``\\n`` split where Unicode line
    separators (``\\u2028``, ``\\u2029``, ``\\x85``, ``\\v``, ``\\f``) occur.
    """

    return [
        (index, line)
        for index, line in enumerate(lines, start=1)
        if line.strip().startswith(("- [ ]", "* [ ]", "+ [ ]"))
    ]


def _unchecked_checkbox_lines(lines: Sequence[str]) -> list[str]:
    """Lines whose first non-whitespace token is an unchecked checkbox
    (``- [ ]``, ``* [ ]``, or ``+ [ ]``)."""

    return [line for _number, line in _unchecked_checkbox_pairs(lines)]


def _checkbox_flip_identity(content: str, *, checked: bool) -> str | None:
    """Identity of a checkbox line after its ``- [ ]`` / ``- [x]`` marker.

    Returns the line text with the marker (and one following space) stripped,
    or None when the line does not carry that exact marker shape: only lines
    that are a checkbox marker before and after the change can pair.
    """

    marker = "- [x]" if checked else "- [ ]"
    if not content.startswith(marker):
        return None
    rest = content[len(marker):]
    return rest[1:] if rest.startswith(" ") else rest


def _diff_is_checkbox_marker_only(diff_text: str) -> bool:
    """True when a unified diff flips pre-existing checkbox markers only.

    The paired-line identity the tolerated dirty-entry shape requires: hunk
    and file headers are ignored, every removed line must carry the unchecked
    marker, every added line the checked marker, and the two sides must pair
    one-to-one on the identity after the markers. Only unchecked-to-checked
    flips of pre-existing checkbox lines satisfy the shape; a content
    rewrite, an inserted or deleted line, and any non-checkbox changed line
    never do. An empty diff is never marker-only: nothing is proven there,
    and the caller refuses.
    """

    removed: list[str] = []
    added: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            identity = _checkbox_flip_identity(line[1:], checked=False)
            if identity is None:
                return False
            removed.append(identity)
        elif line.startswith("+") and not line.startswith("+++"):
            identity = _checkbox_flip_identity(line[1:], checked=True)
            if identity is None:
                return False
            added.append(identity)
    if not removed and not added:
        return False
    return sorted(removed) == sorted(added)


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
        commit_ancestry: Callable[[str], bool] | None = None,
        clock: Callable[[], float] = _now,
        persist_construction: bool = True,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.adapter = adapter
        self.profile = profile or {}
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.commit_lookup = commit_lookup or self._git_commit_exists
        # The staged terminal gate's freshness seam: True only when a commit
        # is proven ancestor-or-self of HEAD. Injectable beside commit_lookup
        # so a fixture root without a git repository can stub it.
        self.commit_ancestry = commit_ancestry or self._git_commit_ancestor_or_self
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
        # Construction-only policy, passed through and never stored: no
        # long-lived driver attribute outlives the construction writes it
        # governs.
        self._resolve_owner_and_receipts(persist_construction=bool(persist_construction))

    def _resolve_owner_and_receipts(self, persist_construction: bool) -> None:
        """Commit the construction-time manifest writes under the manifest lock.

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
        owner initialization still persists ``manifest["owner"]``. With
        ``persist_construction=False`` (the CLI ``readiness`` and ``reclaim``
        operations) construction resolves the owner identity only: the
        backfill, receipt, and save writes below never run. This method owns
        the construction-time writes only; reclaim performs its own
        compare-and-swap manifest write, and readiness never writes.
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
            if not persist_construction:
                # Construction without persistence: the resolved identity
                # above is enough for lock fencing and owner checks; nothing
                # is written, so an already-owned manifest stays
                # byte-identical across the whole operation.
                return
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

    def _persist_recovery_transition(self, manifest: dict[str, Any], transition: str) -> str | None:
        """Validate the post-transition manifest through the same worker-schema
        validation the next launch runs, BEFORE persistence.

        Returns None when the manifest was saved. On validation failure the
        caller receives the refusal text and nothing is persisted: the
        manifest file stays byte-identical to its pre-transition bytes, so a
        recovery can never succeed into a manifest the next launch refuses.
        """
        try:
            validate_manifest_worker_schema(manifest)
        except ValueError as error:
            return (
                f"recovery post-transition validation failed ({transition}); "
                f"nothing was persisted: {error}"
            )
        self._save(manifest)
        return None

    def _claim_owned_by_driver(self, claim: Mapping[str, Any] | None) -> bool:
        """Match a claim to this stable manifest writer, including handoffs."""
        if not isinstance(claim, Mapping):
            return False
        return claim.get("run_writer_id", claim.get("owner")) == self.owner

    @staticmethod
    def _transition_handoff(intent: dict[str, Any], state: str) -> None:
        """Apply one declared split-phase handoff transition."""
        current = intent.get("state")
        if current not in HANDOFF_STATES or state not in HANDOFF_TRANSITIONS.get(current, set()):
            raise ValueError(f"invalid handoff transition: {current} -> {state}")
        intent.update({"state": state})

    def _prepare_handoff_locked(self, manifest: dict[str, Any], prior_task_id: str, checkpoint_identity: str) -> dict[str, Any] | None:
        """Atomically create one successor claim and durable handoff intent.

        The caller holds the manifest lock and has already validated the
        terminal receipt. External adapter I/O is deliberately deferred to
        the continuation path after this intent is durable.
        """
        intents = manifest.setdefault("handoff_intents", {})
        intent_key = f"{prior_task_id}:{checkpoint_identity}"
        existing = intents.get(intent_key)
        if isinstance(existing, Mapping):
            return dict(existing)
        live = any(
            isinstance(claim, Mapping)
            and claim.get("state") in {"claimed", "launched", "waiting-capacity", "blocked"}
            for task_id, claim in manifest.get("claims", {}).items()
            if task_id != prior_task_id
        )
        if live or self._live_group(manifest) is not None:
            return None
        pending = [task for task in manifest["tasks"].values() if not self._task_complete(task) and task.get("status") == "pending"]
        pending.sort(key=_pending_sort_key)
        if not pending:
            return None
        manifest["run_writer_id"] = manifest.get("run_writer_id") or self.owner
        successor = pending[0]
        task_id = str(successor["id"])
        generation = max(
            int(manifest.get("generation", 0)),
            int((manifest.get("claims", {}).get(prior_task_id) or {}).get("generation", 0)),
        ) + 1
        claim_secret = uuid.uuid4().hex
        owner = uuid.uuid4().hex
        launch_id = uuid.uuid4().hex
        manifest["generation"] = generation
        claim = {
            "token": claim_secret,
            "generation": generation,
            "owner": owner,
            "claim_owner_id": owner,
            "run_writer_id": manifest.get("run_writer_id") or self.owner,
            "launch_id": launch_id,
            "handoff_intent_key": intent_key,
            "timestamp": self.clock(),
            "state": "claimed",
            "task_id": task_id,
        }
        manifest["claims"][task_id] = claim
        successor["status"] = "claimed"
        intent = {
            "intent_id": uuid.uuid4().hex,
            "idempotency_key": f"{self.plan_slug}:{checkpoint_identity}:{launch_id}",
            "state": "prepared",
            "prior": {
                "task_id": prior_task_id,
                "checkpoint_identity": checkpoint_identity,
                "claim_owner_id": (manifest.get("claims", {}).get(prior_task_id) or {}).get("claim_owner_id", self.owner),
                "claim_token": (manifest.get("claims", {}).get(prior_task_id) or {}).get("token"),
                "generation": (manifest.get("claims", {}).get(prior_task_id) or {}).get("generation"),
            },
            "successor": {"task_id": task_id, "claim_owner_id": owner, "claim_token": claim_secret, "generation": generation, "launch_id": launch_id},
            "outcome_action": {"type": "launch-task", "task_id": task_id, "claim_owner_id": owner, "claim_token": claim_secret, "generation": generation, "launch_id": launch_id, "idempotency_key": f"{self.plan_slug}:{checkpoint_identity}:{launch_id}"},
            "prelaunch_binding": {
                "run_writer_id": manifest.get("run_writer_id") or self.owner,
                "parent_session_id": None,
                "turn_id": None,
                "tool_use_id": None,
                "claim_owner_id": owner,
                "claim_token": claim_secret,
                "generation": generation,
                "launch_id": launch_id,
                "expected_model": None,
                "worker_identity": None,
                "consumed": False,
            },
            "launch_receipt": None,
        }
        intents[intent_key] = intent
        manifest.setdefault("history", []).append({"event": "handoff-prepared", "intent_id": intent["intent_id"], "from": prior_task_id, "to": task_id, "generation": generation})
        return intent

    @staticmethod
    def _claim_receipt_owner_matches(claim: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
        """Validate an optional rotating claim-owner field on legacy receipts."""
        claim_owner = claim.get("claim_owner_id")
        return claim_owner is None or receipt.get("claim_owner_id") == claim_owner

    def worker_registry(self, manifest: Mapping[str, Any] | None = None) -> WorkerRegistry:
        """Build the detached reducer view for the current manifest."""
        return WorkerRegistry(manifest or load_manifest(self.manifest_path))

    def reconcile_worker_capacity(self, manifest: dict[str, Any], *, now: float | None = None) -> dict[str, Any]:
        """Reconcile provider inventory before a capacity-sensitive action.

        Provider observations are advisory until this driver validates and
        records them.  An adapter without the neutral inventory port is
        unavailable, never an implicit empty inventory.
        """
        observe = getattr(self.adapter, "observe_inventory", None)
        try:
            observation = observe() if callable(observe) else None
        except (OSError, TypeError, ValueError, TimeoutError):
            observation = None
        inventory = None
        timestamp = time.monotonic() if now is None else now
        envelope = validate_provider_observation(observation, now=timestamp)
        if envelope.get("state") == "available":
            items = envelope["inventory"]
            if all(
                    isinstance(item, Mapping)
                    and isinstance(item.get("provider_session_id"), str) and bool(item["provider_session_id"].strip())
                    and isinstance(item.get("process_identity"), Mapping) and bool(item["process_identity"])
                    and (
                        (isinstance(item["process_identity"].get("pid"), int) and not isinstance(item["process_identity"].get("pid"), bool)
                         and item["process_identity"]["pid"] > 0
                         and isinstance(item["process_identity"].get("start_time"), (str, int, float)))
                        or (isinstance(item["process_identity"].get("provider"), str) and bool(item["process_identity"]["provider"].strip())
                            and isinstance(item["process_identity"].get("session_id"), str) and bool(item["process_identity"]["session_id"].strip()))
                    )
                    for item in items
                ) and len({item["provider_session_id"] for item in items}) == len(items):
                inventory = items
        registry = WorkerRegistry(manifest)
        launch_reservations = manifest.get("capacity", {}).get("reservations", {})
        result = registry.apply_observation(envelope, now=timestamp)
        reservations = launch_reservations
        if result.get("status") == "available" and reservations:
            result = {"status": "unavailable", "reason": "launch-reservation"}
        if result.get("status") == "available" and inventory is not None and envelope.get("state") == "available":
            registered_sessions = {
                worker.get("provider_session_id")
                for worker in registry.manifest["workers"].values()
                if worker.get("state") in {"active", "quarantined"}
            }
            registered_processes = {
                json.dumps(worker.get("process_identity", {}), sort_keys=True)
                for worker in registry.manifest["workers"].values()
                if worker.get("state") in {"active", "quarantined"} and isinstance(worker.get("process_identity"), Mapping)
            }
            if any(
                item.get("provider_session_id") not in registered_sessions
                and json.dumps(item.get("process_identity", {}), sort_keys=True) not in registered_processes
                for item in inventory
            ):
                result = {"status": "unavailable", "reason": "capacity-live"}
        if result.get("status") == "available" and not registry.capacity_witness()["launch_available"]:
            result = {"status": "unavailable", "reason": "capacity-live"}
        manifest["workers"] = registry.manifest["workers"]
        manifest["capacity"] = registry.manifest["capacity"]
        manifest["capacity"]["reservations"] = reservations
        manifest["capacity"]["last_reconciliation"] = {
            "status": envelope.get("state"),
            "reason": result.get("reason", envelope.get("state")),
            "observed_at": envelope.get("observed_at"),
            "checked_at": timestamp,
        }
        manifest.setdefault("history", []).append({"event": "worker-reconciled", "status": result.get("status"), "reason": result.get("reason"), "recovery_action": result.get("recovery_action"), "observation_state": envelope.get("state")})
        return result

    def _capacity_transition(self, claim: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Reconcile and durably record capacity under the manifest lock."""
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return {"status": "unavailable", "reason": "capacity-unavailable"}
            manifest = load_manifest(self.manifest_path)
            reservations = manifest.get("capacity", {}).get("reservations", {})
            claim_launch_id = claim.get("launch_id") if claim else None
            if claim and not claim_launch_id and claim.get("group_id"):
                claim_launch_id = claim.get("group_id")
            own_id = f"{claim.get('task_id')}:{claim.get('generation')}:{claim_launch_id}" if claim else None
            if any(key != own_id for key in reservations):
                return {"status": "unavailable", "reason": "launch-reservation"}
            if own_id in reservations:
                # A continuation of this exact durable launch already owns
                # the reserved slot. Reuse that reservation instead of
                # treating it as free capacity or requiring a second slot.
                return {"status": "available", "reason": "claim-launch-reservation"}
            before = json.dumps(manifest, sort_keys=True)
            result = self.reconcile_worker_capacity(manifest)
            if result.get("reason") == "capacity-live" and claim and claim.get("group_id") and self._claim_group_kind(manifest, claim) == GROUP_KIND_PARALLEL:
                group = manifest.get("claim_groups", {}).get(claim.get("group_id"), {})
                members = set(str(item) for item in group.get("members", ())) if isinstance(group, Mapping) else set()
                workers = manifest.get("workers", {}).values()
                if group.get("state") == "active" and all(worker.get("task_id") in members for worker in workers if worker.get("state") in {"active", "quarantined"}):
                    result = {"status": "available", "reason": "parallel-group-capacity"}
            if json.dumps(manifest, sort_keys=True) != before:
                self._save(manifest)
            return result

    @_locked_mutation
    def _release_launch_reservation(self, claim: Mapping[str, Any]) -> None:
        manifest = load_manifest(self.manifest_path)
        reservations = manifest.get("capacity", {}).get("reservations", {})
        if isinstance(reservations, Mapping):
            for key, reservation in list(reservations.items()):
                if isinstance(reservation, Mapping) and reservation.get("task_id") == claim.get("task_id") and reservation.get("claim_token") == claim.get("token") and reservation.get("generation") == claim.get("generation"):
                    reservations.pop(key, None)
            self._save(manifest)

    @_locked_mutation
    def apply_worker_lifecycle_receipt(self, event: str, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Persist a validated provider lifecycle transition under the manifest lock."""
        manifest = load_manifest(self.manifest_path)
        registry = WorkerRegistry(manifest)
        result = registry.apply_lifecycle_event(event, receipt)
        if result.get("outcome") not in {"refused"}:
            manifest["workers"] = registry.manifest["workers"]
            manifest["capacity"] = registry.manifest["capacity"]
            manifest.setdefault("history", []).append({"event": "worker-lifecycle-receipt", "worker_id": receipt.get("worker_id"), "lifecycle_event": event, "outcome": result.get("outcome"), "receipt_id": receipt.get("receipt_id")})
            self._save(manifest)
        return result

    @staticmethod
    def _task_id_from_checkpoint(identity: str) -> str:
        return identity.split(":", 1)[0]

    @staticmethod
    def _task_complete(task: Mapping[str, Any]) -> bool:
        """True when the task is out of the incomplete selection set.

        ``complete`` and ``checkpointed`` are the done statuses; a truthy
        ``checkbox`` means the plan itself marks the work done (the seeding
        boundary). ``deferred`` is complete-for-selection: the done-pending
        recovery's defer disposition retires the task from the queue and it
        is never relaunched, so no selection site may pick it up again.
        ``deferred`` deliberately stays out of PROGRESSED_TASK_STATUSES so
        readiness condition (c) plan-manifest agreement never demands
        unchecked-checkbox closure for a task the operator chose not to
        complete - the recorded recovery receipt, not plan checkboxes, is
        the deferred task's evidence.
        """

        return task.get("status") in {"complete", "checkpointed", "deferred"} or bool(task.get("checkbox"))

    @staticmethod
    def _interruption_reconciliation_payload(manifest: Mapping[str, Any], prefix: str) -> dict[str, Any] | None:
        task = next((item for item in manifest.get("tasks", {}).values()
                     if item.get("status") == "blocked" and item.get("resume_allowed") is False
                     and isinstance(item.get("blocked_receipt"), Mapping)
                     and item["blocked_receipt"].get("reason_code") in {"timeout", "parent-shutdown", "session-interrupted", "user-interruption"}), None)
        if task is None:
            return None
        task_id = str(task.get("id", ""))
        claim = manifest.get("claims", {}).get(task_id)
        if not isinstance(claim, Mapping):
            return {"task_id": task_id, "missing_claim": True}
        return {
            "idempotency_key": f"{prefix}:{task_id}:{claim.get('generation')}:{claim.get('token')}",
            "task_id": task_id,
            "claim_token": claim.get("token"),
            "generation": claim.get("generation"),
        }

    def _result_error(self, message: str, generation: int | None = None, action_scope: str = "runtime", checkpoint_identity: str = "runtime:malformed") -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        return _outcome("blocked", "malformed-result", [message], action_scope, checkpoint_identity, manifest.get("generation", 0) if generation is None else generation, "preserve-and-reconcile")

    def validate_manifest(self, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Validate the authoritative machine state before selecting work."""

        value = dict(manifest or load_manifest(self.manifest_path))
        validate_manifest_worker_schema(value)
        if value.get("workflow_state") not in WORKFLOW_STATES:
            raise ValueError("invalid workflow state")
        # Watcher-authority fields tolerate absence (state written before the
        # watcher contract) but never tolerate a wrong type when present.
        for field in ("progress_revision", "boundary_generation"):
            if field in value and (isinstance(value[field], bool) or not isinstance(value[field], int) or value[field] < 0):
                raise ValueError(f"manifest {field} must be a non-negative integer")
        if "resume_watcher" in value and value["resume_watcher"] is not None:
            # Schema owner: execute_plan_resume_watcher. A layout
            # missing that module fails closed as a ValueError, never an
            # uncaught ImportError.
            try:
                import execute_plan_resume_watcher

                execute_plan_resume_watcher.validate_resume_watcher_receipt(value["resume_watcher"])
            except ImportError as exc:
                raise ValueError(f"resume watcher schema module unavailable: {exc}") from exc
        if "user_interrupt" in value and value["user_interrupt"] is not None and not isinstance(value["user_interrupt"], str):
            raise ValueError("manifest user_interrupt must be an ISO-8601 string or null")
        if not isinstance(value.get("generation"), int) or value["generation"] < 0:
            raise ValueError("manifest generation must be non-negative")
        # `deferred` (the done-pending recovery disposition status) is admitted
        # here so readiness, diagnose, and every refresh_manifest caller keep
        # validating a post-defer manifest instead of re-wedging the run.
        task_states = {"pending", "claimed", "launched", "blocked", "done-pending", "commit-pending", "checkpointed", "complete", "deferred", "aborted"}
        claim_states = {"claimed", "launched", "blocked", "waiting-capacity", "closed", "aborted", "replaced", "staged"}
        for task_id, task in value["tasks"].items():
            if not isinstance(task, Mapping) or task.get("id", task_id) != task_id:
                raise ValueError("task identity does not match manifest key")
            if task.get("status") not in task_states:
                raise ValueError(f"unknown task status: {task.get('status')}")
            if "ordinal" in task and (isinstance(task["ordinal"], bool) or not isinstance(task["ordinal"], int) or task["ordinal"] < 0):
                raise ValueError("task ordinal must be a non-negative integer")
        evidence_digest = value.get("evidence_contract_digest")
        if evidence_digest is not None and evidence_digest != capabilities.evidence_contract_digest(value["tasks"]):
            raise ValueError("manifest evidence contract digest does not match task criteria and allowlists")
        if "evidence_enforcement" in value and not isinstance(value["evidence_enforcement"], bool):
            raise ValueError("manifest evidence_enforcement must be boolean")
        if value.get("evidence_enforcement") is True and any(not task.get("required_criteria") or not task.get("verification_commands") for task in value["tasks"].values()):
            raise ValueError("manifest evidence enforcement requires criteria and verification commands for every task")
        if not isinstance(value.get("claims"), dict) or not isinstance(value.get("checkpoints"), dict):
            raise ValueError("manifest claims and checkpoints must be mappings")
        groups = value.get("claim_groups")
        if groups is not None:
            if not isinstance(groups, dict):
                raise ValueError("manifest claim_groups must be a mapping")
            for group_id, group in groups.items():
                if not isinstance(group, Mapping) or str(group.get("group_id", group_id)) != group_id:
                    raise ValueError("batch group identity does not match manifest key")
                # `failed` is the terminal state documented in
                # BATCH_GROUP_STATES; refusing it here used to make every
                # validating entrypoint raise after the exit.
                if group.get("state") not in BATCH_GROUP_STATES:
                    raise ValueError(f"unknown batch group state: {group.get('state')}")
                members = group.get("members")
                if not isinstance(members, list) or not members or not all(isinstance(member, str) and member for member in members):
                    raise ValueError("batch group members must be a non-empty ordered list")
                kind = str(group.get("kind") or GROUP_KIND_BATCH)
                if kind not in (GROUP_KIND_BATCH, GROUP_KIND_PARALLEL):
                    raise ValueError(f"unknown claim group kind: {group.get('kind')}")
                if kind == GROUP_KIND_PARALLEL:
                    # Concurrent members carry no anchor identity and no
                    # active-member ordinal gate; both must be absent so a
                    # batch-shaped record can never masquerade as parallel.
                    if group.get("anchor") is not None:
                        raise ValueError("parallel group must not carry a batch anchor")
                    if group.get("active_member") is not None:
                        raise ValueError("parallel group must not carry an active member")
                else:
                    if group.get("anchor") not in members:
                        raise ValueError("batch group anchor must be a member")
                    if group.get("active_member") is not None and group.get("active_member") not in members:
                        raise ValueError("batch group active member must be a member")
                if isinstance(group.get("generation"), bool) or not isinstance(group.get("generation"), int) or group["generation"] < 0:
                    raise ValueError("batch group generation must be non-negative")
                for member in members:
                    if member not in value["tasks"]:
                        raise ValueError("batch group references an unknown task")
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
            if claim.get("group_id") is not None and claim.get("group_id") not in (groups or {}):
                raise ValueError("claim references an unknown batch group")
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

    def capture_verification_evidence(self, task_id: str, command_id: str, timeout_seconds: float = 900.0) -> dict[str, Any]:
        """Run one task-declared verification command and bind its output to the live claim."""
        manifest = load_manifest(self.manifest_path)
        task = manifest.get("tasks", {}).get(str(task_id))
        claim = manifest.get("claims", {}).get(str(task_id))
        if not isinstance(task, Mapping) or not isinstance(claim, Mapping) or claim.get("state") != "launched":
            return _outcome("blocked", "stale-claim", ["verification requires the launched task's live claim"], "repository-task", f"{task_id}:verify", manifest.get("generation", 0), "preserve-and-reconcile")
        declaration = next((item for item in task.get("verification_commands", ()) if isinstance(item, Mapping) and item.get("id") == command_id), None)
        if declaration is None:
            return _outcome("blocked", "malformed-result", ["verification command is not in the immutable task contract"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile")
        argv = declaration.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(value, str) or not value for value in argv):
            return _outcome("blocked", "malformed-result", ["task verification command has an invalid argv"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile")
        try:
            completed = subprocess.run(argv, cwd=self.repo_root, capture_output=True, timeout=timeout_seconds, check=False)
            output_digest = "sha256:" + hashlib.sha256(completed.stdout + b"\0" + completed.stderr).hexdigest()
        except (OSError, subprocess.SubprocessError) as exc:
            return _outcome("blocked", "worktree-witness-unavailable", [f"verification command could not be witnessed: {type(exc).__name__}"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        allowed = sorted(str(path) for path in claim.get("allowed_paths", task.get("allowed_paths", ())))
        try:
            source_digest = self._task_source_digest(allowed)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return _outcome("blocked", "worktree-witness-unavailable", [f"task source snapshot could not be witnessed: {type(exc).__name__}"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        baseline_paths = []
        changed = []
        baseline = str(claim.get("baseline_revision") or "")
        if baseline:
            try:
                names = subprocess.run(["git", "diff", "--name-only", "-z", baseline, "HEAD"], cwd=self.repo_root, capture_output=True, timeout=10, check=True).stdout
                changed = [name.decode("utf-8", errors="replace") for name in names.split(b"\0") if name]
                tree = subprocess.run(["git", "ls-tree", "-r", "--name-only", "-z", baseline], cwd=self.repo_root, capture_output=True, timeout=10, check=True).stdout
                allowed_set = set(claim.get("allowed_paths", task.get("allowed_paths", ())))
                baseline_paths = [name.decode("utf-8", errors="replace") for name in tree.split(b"\0") if name and name.decode("utf-8", errors="replace") in allowed_set]
            except (OSError, subprocess.SubprocessError):
                changed = ["path-observation-unavailable"]
                baseline_paths = []
        if completed.returncode != 0:
            return _outcome("blocked", "contract-violation", [f"required verification command failed: {command_id}", f"exit_status={completed.returncode}"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile")
        envelope = capabilities.normalize_evidence_envelope({
            "version": 1, "command": argv, "working_directory": str(self.repo_root), "exit_status": completed.returncode,
            "output_digest": output_digest, "selected_tests": declaration.get("selected_tests", [command_id]),
            "stdout_digest": "sha256:" + hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_digest": "sha256:" + hashlib.sha256(completed.stderr).hexdigest(),
            "baseline_paths": baseline_paths, "changed_paths": changed, "allowed_paths": allowed,
            "criteria": declaration.get("criteria", []), "verified_by": "runtime-driver", "task_id": str(task_id),
            "claim_token": str(claim["token"]), "generation": int(claim["generation"]), "launch_id": str(claim["launch_id"]),
            "evidence_contract_digest": str(manifest.get("evidence_contract_digest", "")), "source_digest": source_digest,
        })
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, f"{task_id}:verify")
            current = load_manifest(self.manifest_path)
            current_claim = current.get("claims", {}).get(str(task_id), {})
            if any(current_claim.get(key) != claim.get(key) for key in ("token", "generation", "launch_id")):
                return _outcome("blocked", "owner-mismatch", ["claim changed while verification command ran"], "repository-task", f"{task_id}:verify", claim.get("generation", 0), "preserve-and-reconcile")
            current.setdefault("verification_evidence", {}).setdefault(str(task_id), {})[str(command_id)] = envelope
            self._save(current)
        return {"status": "success", "reason_code": "completed", "evidence": [f"verification={command_id}", f"output={output_digest}"], "envelope": envelope}

    def _task_source_digest(self, allowed_paths: Sequence[str], revision: str | None = None) -> str:
        """Digest only allowlisted file contents, from the worktree or a commit."""
        root = self.repo_root.resolve()
        entries: dict[str, str] = {}
        if revision:
            listed = subprocess.run(["git", "ls-tree", "-r", "-z", revision], cwd=root, capture_output=True, check=True).stdout
            for record in listed.split(b"\0"):
                if not record:
                    continue
                header, raw_path = record.split(b"\t", 1)
                path = raw_path.decode("utf-8", errors="strict")
                if not any(path == allowed or path.startswith(allowed.rstrip("/") + "/") for allowed in allowed_paths):
                    continue
                blob = header.split(b" ")[-1].decode("ascii")
                content = subprocess.run(["git", "cat-file", "blob", blob], cwd=root, capture_output=True, check=True).stdout
                entries[path] = hashlib.sha256(content).hexdigest()
        else:
            for allowed in allowed_paths:
                normalized = _safe_relative_path(root, allowed)
                target = root / normalized
                if target.is_symlink() or target.is_file():
                    candidates = [target]
                elif target.is_dir():
                    candidates = sorted(item for item in target.rglob("*") if item.is_file() or item.is_symlink())
                else:
                    entries[normalized] = "missing"
                    continue
                for item in candidates:
                    relative = item.relative_to(root).as_posix()
                    content = os.fsencode(os.readlink(item)) if item.is_symlink() else item.read_bytes()
                    entries[relative] = hashlib.sha256(content).hexdigest()
        encoded = json.dumps(sorted(entries.items()), separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

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
            task = manifest.get("tasks", {}).get(task_id, {})
            required_criteria = set(task.get("required_criteria", ())) if isinstance(task, Mapping) else set()
            if manifest.get("evidence_enforcement") is True and not required_criteria:
                return _outcome("blocked", "malformed-result", ["task has no immutable verification criteria; recreate the run with verification requirements"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
            if result["status"] == "success" and required_criteria:
                if not isinstance(claim, Mapping) or raw.get("claim_token") != claim.get("token") or claim.get("state") != "launched":
                    return _outcome("blocked", "owner-mismatch", ["successful result is not bound to the active launched claim"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
                receipts = manifest.get("verification_evidence", {}).get(task_id, {})
                covered: set[str] = set()
                commands = {item.get("id"): item for item in task.get("verification_commands", ()) if isinstance(item, Mapping)}
                allowed_for_task = sorted(str(path) for path in claim.get("allowed_paths", task.get("allowed_paths", ())))
                try:
                    current_source_digest = self._task_source_digest(allowed_for_task)
                except (OSError, subprocess.SubprocessError, ValueError) as exc:
                    return _outcome("blocked", "worktree-witness-unavailable", [f"task source snapshot could not be verified: {type(exc).__name__}"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-reconcile", resume_allowed=False)
                for command_id, envelope in receipts.items() if isinstance(receipts, Mapping) else ():
                    try:
                        normalized_evidence = capabilities.normalize_evidence_envelope(envelope)
                    except ValueError as exc:
                        return self._result_error(str(exc), result["generation"], result["action_scope"], result["checkpoint_identity"])
                    declaration = commands.get(command_id)
                    if not isinstance(declaration, Mapping) or normalized_evidence["command"] != declaration.get("argv") or normalized_evidence["criteria"] != sorted(declaration.get("criteria", ())):
                        continue
                    if any(normalized_evidence.get(field) != claim.get(claim_field) for field, claim_field in (("task_id", "task_id"), ("claim_token", "token"), ("generation", "generation"), ("launch_id", "launch_id"))) or normalized_evidence.get("evidence_contract_digest") != manifest.get("evidence_contract_digest"):
                        continue
                    if normalized_evidence["source_digest"] != current_source_digest:
                        continue
                    if normalized_evidence["exit_status"] == 0 and normalized_evidence["working_directory"] == str(self.repo_root):
                        covered.update(normalized_evidence["criteria"])
                if not required_criteria.issubset(covered):
                    missing = sorted(required_criteria - covered)
                    return _outcome("blocked", "malformed-result", [f"required verification criteria missing: {', '.join(missing)}", "run the driver-owned verification command and retry"], result["action_scope"], result["checkpoint_identity"], result["generation"], "preserve-and-reconcile")
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
        claim = manifest["claims"][task_id]
        claim["state"] = "blocked"
        if claim.get("group_id"):
            # Batch members persist the attempt receipt on the group and
            # capture the anchor session from the first member receipt that
            # carries one. Parallel members keep neither: each member owns
            # its session on its own task record, and the blocked receipt
            # stays on the task (the reclaim exit reads it there).
            group = manifest.get("claim_groups", {}).get(claim["group_id"])
            if isinstance(group, Mapping) and RuntimeDriver._claim_group_kind(manifest, claim, group) == GROUP_KIND_BATCH:
                if session_id and not group.get("anchor_session"):
                    group["anchor_session"] = str(session_id)
                attempts = group.setdefault("member_attempts", {})
                record = attempts.setdefault(task_id, {})
                record["attempt"] = int(claim.get("attempt") or record.get("attempt") or 1)
                record["receipt"] = dict(result)
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
        if _claim_progressed_past_receipt(task, current_claim):
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
        live = self.refresh_manifest().get("claims", {}).get(str(task.get("id")))
        if (
            not isinstance(live, Mapping)
            or not self._claim_owned_by_driver(live)
            or live.get("token") != claim.get("token")
            or live.get("generation") != claim.get("generation")
            or live.get("owner") != claim.get("owner")
            or live.get("launch_id") != claim.get("launch_id")
        ):
            return _outcome("blocked", "owner-mismatch", ["stale handoff identity refused before adapter launch"], "repository-task", f"{task['id']}:launch", int(claim.get("generation", 0)), "preserve-and-reconcile")
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
        if claim.get("claim_owner_id"):
            if raw.get("claim_owner_id") not in (None, claim.get("claim_owner_id")):
                return _outcome("blocked", "owner-mismatch", ["adapter launch receipt carries a stale claim owner"], "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile")
            raw["claim_owner_id"] = claim["claim_owner_id"]
        lifecycle_event = raw.get("lifecycle_event", raw.get("event"))
        if lifecycle_event in {"shutdown", "close", "not_found", "timeout"}:
            adapter_proof = raw.get("proof")
            self._apply_adapter_lifecycle(claim, task, raw, str(lifecycle_event), proof=adapter_proof if isinstance(adapter_proof, Mapping) else False)
        elif raw.get("status") == "success" and raw.get("provider_session_id"):
            recording = self._record_worker_launch(claim, task, raw)
            if isinstance(recording, Mapping) and recording.get("status") == "refused":
                return _outcome(
                    "blocked", "worker-registry-refused", [str(recording.get("reason", "worker launch was not recorded"))],
                    "repository-task", f"{task['id']}:launch", int(claim["generation"]), "preserve-and-reconcile",
                    claim_token=claim["token"],
                )
        elif raw.get("reason_code") in {"timeout", "cleanup-unverified"}:
            self._apply_adapter_lifecycle(claim, task, raw, "timeout", proof=False)
        raw.setdefault("claim_token", claim["token"])
        return raw

    def _apply_adapter_lifecycle(self, claim: Mapping[str, Any], task: Mapping[str, Any], result: Mapping[str, Any], event: str, *, proof: Mapping[str, Any] | bool) -> dict[str, Any] | None:
        manifest = load_manifest(self.manifest_path)
        worker = next((item for item in manifest.get("workers", {}).values() if item.get("task_id") == task["id"] and item.get("claim_token") == claim.get("token") and item.get("generation") == claim.get("generation")), None)
        if not isinstance(worker, Mapping):
            return {"status": "refused", "outcome": "refused", "reason": "identity-mismatch"}
        identity = {
            "task_id": task["id"],
            "claim_token": claim["token"],
            "claim_owner_id": claim.get("claim_owner_id", claim.get("owner", self.owner)),
            "generation": claim["generation"],
            "worker_id": worker["worker_id"],
            "provider_session_id": worker["provider_session_id"],
        }
        if any(key not in result for key in identity):
            return {"status": "refused", "outcome": "refused", "reason": "malformed-lifecycle-identity"}
        if any(result.get(key) != value for key, value in identity.items()):
            return {"status": "refused", "outcome": "refused", "reason": "identity-mismatch"}
        adapter_proof = result.get("proof")
        if not isinstance(adapter_proof, Mapping) and isinstance(proof, Mapping):
            adapter_proof = proof
        if not isinstance(adapter_proof, Mapping):
            adapter_proof = {"verified": False, "reason": result.get("reason_code", event)}
        receipt = {
            "receipt_id": str(result.get("receipt_id") or f"{event}-{task['id']}-{claim['generation']}-{result.get('reason_code', 'result')}"),
            **{key: result[key] for key in identity},
            "event": event,
            "proof": dict(adapter_proof),
            "observed_at": result.get("observed_at", self.clock()),
            "reason": result.get("reason_code", event),
        }
        return self.apply_worker_lifecycle_receipt(event, receipt)

    @_locked_mutation
    def _record_worker_launch(self, claim: Mapping[str, Any], task: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Persist one adapter-provided worker identity under the driver lock."""
        manifest = load_manifest(self.manifest_path)
        current = manifest.get("claims", {}).get(str(task["id"]))
        if not isinstance(current, Mapping) or current.get("token") != claim.get("token") or current.get("generation") != claim.get("generation") or current.get("owner") != claim.get("owner") or current.get("launch_id") != claim.get("launch_id"):
            return {"status": "refused", "reason": "claim-fence"}
        intent_key = current.get("handoff_intent_key")
        intent = manifest.get("handoff_intents", {}).get(intent_key) if intent_key else None
        if isinstance(intent, Mapping):
            if intent.get("state") == "launched":
                recorded = intent.get("launch_receipt") or {}
                if recorded.get("provider_session_id") == receipt.get("provider_session_id") and recorded.get("worker_id") == (receipt.get("worker_id") or f"worker-{task['id']}-{receipt.get('provider_session_id')}"):
                    return {"status": "replayed", "reason": "matching handoff launch receipt already persisted"}
                return {"status": "refused", "reason": "handoff-launch-already-consumed"}
            if intent.get("state") != "launching":
                return {"status": "refused", "reason": "handoff-intent-state"}
        registry = WorkerRegistry(manifest)
        session = str(receipt["provider_session_id"])
        process_identity = receipt.get("process_identity")
        if not process_identity:
            adapter = self.adapter
            provider = next((getattr(adapter, name, None) for name in ("provider_name", "name") if isinstance(getattr(adapter, name, None), str) and getattr(adapter, name).strip()), None)
            if provider is None:
                provider = type(adapter).__name__.lower() if adapter is not None else "runtime"
            process_identity = {"provider": provider, "session_id": session}
        elif isinstance(process_identity, Mapping) and process_identity.get("session_id") is not None and process_identity.get("session_id") != session:
            return {"status": "refused", "reason": "provider-session-identity-mismatch"}
        result = registry.register_launch(
            task_id=str(task["id"]),
            claim_token=str(claim["token"]),
            generation=int(claim["generation"]),
            claim_owner_id=str(claim.get("claim_owner_id", claim.get("owner", self.owner))),
            provider_session_id=session,
            worker_id=str(receipt.get("worker_id") or f"worker-{task['id']}-{session}"),
            command_identity=str(receipt.get("command_identity") or f"adapter:{task['id']}"),
            process_identity=process_identity,
            launch_id=str(claim.get("launch_id") or receipt.get("launch_id") or f"launch-{task['id']}-{session}"),
            capacity_entry_id=str(receipt.get("capacity_entry_id") or f"capacity-{task['id']}-{session}"),
            started_at=receipt.get("observed_at", self.clock()),
        )
        if result.get("status") == "refused":
            return result
        manifest["workers"] = registry.manifest["workers"]
        manifest["capacity"] = registry.manifest["capacity"]
        manifest.setdefault("history", []).append({"event": "worker-launched", "task_id": task["id"], "worker_id": result["worker_id"]})
        if isinstance(intent, dict):
            self._transition_handoff(intent, "launched")
            intent["launch_receipt"] = {"worker_id": result["worker_id"], "provider_session_id": session, "observed_at": receipt.get("observed_at", self.clock())}
            binding = intent.get("prelaunch_binding")
            if isinstance(binding, dict):
                worker_identity = {"worker_id": result["worker_id"], "provider_session_id": session}
                if binding.get("consumed") and binding.get("worker_identity") != worker_identity:
                    return {"status": "refused", "reason": "worker-start-identity-mismatch"}
                binding["worker_identity"] = {"worker_id": result["worker_id"], "provider_session_id": session}
                binding["provider_launch_id"] = receipt.get("launch_id")
        self._save(manifest)
        return result

    @_locked_mutation
    def record_worker_start(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        """Consume a handoff binding only after its matching worker-start event."""
        if not isinstance(receipt, Mapping):
            return _outcome("blocked", "malformed-result", ["worker-start receipt must be a mapping"], "repository-task", "runtime:worker-start", 0, "preserve-and-reconcile")
        required = (
            "task_id", "run_writer_id", "parent_session_id", "turn_id", "tool_use_id",
            "claim_owner_id", "claim_token", "generation", "launch_id", "expected_model",
            "worker_id", "provider_session_id", "agent_type", "model", "repo_root", "manifest_path",
        )
        if any(key not in receipt for key in required) or any(not isinstance(receipt.get(key), str) or not receipt.get(key).strip() for key in ("agent_type", "model", "repo_root", "manifest_path")):
            return _outcome("blocked", "malformed-result", ["worker-start receipt is missing a required identity field"], "repository-task", "runtime:worker-start", 0, "preserve-and-reconcile")
        if Path(str(receipt["repo_root"])).resolve() != self.repo_root or Path(str(receipt["manifest_path"])).resolve() != self.manifest_path.resolve():
            return _outcome("blocked", "owner-mismatch", ["worker-start receipt repository or manifest path does not match this runtime"], "repository-task", "runtime:worker-start", 0, "preserve-and-reconcile")
        task_id = str(receipt["task_id"])
        manifest = load_manifest(self.manifest_path)
        claim = manifest.get("claims", {}).get(task_id)
        if not isinstance(claim, Mapping) or (
            claim.get("run_writer_id") != receipt.get("run_writer_id")
            or claim.get("claim_owner_id") != receipt.get("claim_owner_id")
            or claim.get("token") != receipt.get("claim_token")
            or claim.get("generation") != receipt.get("generation")
            or claim.get("launch_id") != receipt.get("launch_id")
            or not self._claim_owned_by_driver(claim)
        ):
            return _outcome("blocked", "owner-mismatch", ["worker-start receipt does not match the live claim identity"], "repository-task", f"{task_id}:worker-start", manifest.get("generation", 0), "preserve-and-reconcile")
        intent_key = claim.get("handoff_intent_key")
        intent = manifest.get("handoff_intents", {}).get(intent_key) if intent_key else None
        binding = intent.get("prelaunch_binding") if isinstance(intent, Mapping) else None
        if not isinstance(intent, Mapping) or not isinstance(binding, dict) or intent.get("state") not in {"launching", "launched"}:
            return _outcome("blocked", "owner-mismatch", ["worker-start receipt has no active handoff binding"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "preserve-and-reconcile")
        binding_fields = ("run_writer_id", "parent_session_id", "turn_id", "tool_use_id", "claim_owner_id", "claim_token", "generation", "launch_id", "expected_model")
        if any(receipt.get(key) != binding.get(key) for key in binding_fields):
            return _outcome("blocked", "owner-mismatch", ["worker-start receipt does not match the prelaunch binding"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "preserve-and-reconcile")
        worker_identity = {"worker_id": receipt["worker_id"], "provider_session_id": receipt["provider_session_id"]}
        if binding.get("worker_identity") not in (None, worker_identity):
            return _outcome("blocked", "owner-mismatch", ["worker-start identity differs from the recorded launch receipt"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "preserve-and-reconcile")
        if isinstance(intent.get("launch_receipt"), Mapping):
            launch = intent["launch_receipt"]
            if launch.get("worker_id") != worker_identity["worker_id"] or launch.get("provider_session_id") != worker_identity["provider_session_id"]:
                return _outcome("blocked", "owner-mismatch", ["worker-start receipt differs from the durable provider launch receipt"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "preserve-and-reconcile")
        receipt_identity = {key: receipt.get(key) for key in required}
        existing = binding.get("worker_start_receipt")
        if binding.get("consumed"):
            if existing == receipt_identity:
                return _outcome("success", "completed", ["matching worker-start receipt already consumed"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "continue-parent", duplicate=True)
            return _outcome("blocked", "owner-mismatch", ["prelaunch binding was consumed by a different worker-start receipt"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "preserve-and-reconcile")
        binding["worker_identity"] = worker_identity
        binding["worker_start_receipt"] = receipt_identity
        binding["consumed"] = True
        self._save(manifest)
        return _outcome("success", "completed", ["matching worker-start receipt consumed prelaunch binding"], "repository-task", f"{task_id}:worker-start", claim.get("generation", 0), "continue-parent")

    @_locked_mutation
    def reserve_continuation(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Atomically reserve one of three recoverable stop continuations per claim generation."""
        if not isinstance(request, Mapping):
            return {"status": "blocked", "reason_code": "malformed-result"}
        required = ("task_id", "claim_token", "generation", "event_id", "parent_session_id", "event")
        if any(not isinstance(request.get(key), (str, int)) or request.get(key) == "" for key in required):
            return {"status": "blocked", "reason_code": "malformed-result"}
        manifest = load_manifest(self.manifest_path)
        task_id = str(request["task_id"])
        claim = manifest.get("claims", {}).get(task_id)
        task = manifest.get("tasks", {}).get(task_id)
        if not isinstance(claim, Mapping) or not isinstance(task, Mapping) or (
            claim.get("token") != request["claim_token"] or claim.get("generation") != request["generation"]
        ):
            return {"status": "blocked", "reason_code": "stale-claim"}
        reservations = manifest.setdefault("continuation_reservations", {})
        identity = f"{task_id}:{request['generation']}:{request['event']}:{request['parent_session_id']}:{request['event_id']}"
        if identity in reservations:
            return dict(reservations[identity]) | {"replayed": True}
        blocked_receipt = task.get("blocked_receipt")
        reason = blocked_receipt.get("reason_code") if isinstance(blocked_receipt, Mapping) else None
        hard_blocks = {"approval-required", "runtime-policy-unavailable", "cleanup-unverified", "malformed-result", "owner-mismatch", "stale-claim", "ambiguous"}
        if request.get("stop_hook_active") or task.get("status") in {"completed", "complete", "checkpointed", "done"} or task.get("checkbox") is True or task.get("resume_allowed") is False or reason in hard_blocks:
            return {"status": "refused", "reason_code": "continuation-not-allowed"}
        key = f"{task_id}:{request['generation']}"
        used = sum(1 for row in reservations.values() if isinstance(row, Mapping) and row.get("budget_key") == key and row.get("status") == "reserved")
        if used >= 3:
            return {"status": "refused", "reason_code": "continuation-budget-exhausted"}
        outcome = {"status": "reserved", "reason_code": "continuation-reserved", "budget_key": key, "ordinal": used + 1,
                   "task_id": task_id, "generation": request["generation"], "event_id": str(request["event_id"]),
                   "parent_session_id": str(request["parent_session_id"]), "event": str(request["event"])}
        reservations[identity] = outcome
        manifest.setdefault("history", []).append({"event": "continuation-reserved", "task_id": task_id, "generation": request["generation"], "event_id": str(request["event_id"]), "ordinal": used + 1})
        self._save(manifest)
        return outcome

    @_locked_mutation
    def recover_ambiguous_handoff(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Close an ambiguous launch fence only with exact provider terminal evidence."""
        if not isinstance(request, Mapping):
            return _outcome("blocked", "malformed-result", ["handoff recovery request must be a mapping"], "repository-task", "runtime:handoff-recovery", 0, "preserve-and-reconcile")
        manifest = load_manifest(self.manifest_path)
        intent_key = request.get("intent_key")
        intent = manifest.get("handoff_intents", {}).get(intent_key) if isinstance(intent_key, str) else None
        evidence = request.get("provider_evidence")
        if not isinstance(intent, dict) or intent.get("state") != "ambiguous" or not isinstance(evidence, Mapping):
            return _outcome("blocked", "ambiguous", ["handoff is not recoverable from the supplied provider evidence"], "repository-task", str(intent_key or "handoff"), manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        successor = intent.get("successor")
        if not isinstance(successor, Mapping) or (
            evidence.get("source") != "provider-lifecycle"
            or evidence.get("state") != "terminal"
            or evidence.get("intent_id") != intent.get("intent_id")
            or evidence.get("launch_id") != successor.get("launch_id")
            or not isinstance(evidence.get("provider_session_id"), str) or not evidence.get("provider_session_id")
        ):
            return _outcome("blocked", "ambiguous", ["provider terminal evidence does not uniquely match the exact handoff intent and launch identity"], "repository-task", str(intent_key), manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        task_id = str(successor.get("task_id", ""))
        claim = manifest.get("claims", {}).get(task_id)
        task = manifest.get("tasks", {}).get(task_id)
        if not isinstance(claim, dict) or not isinstance(task, dict) or claim.get("token") != successor.get("claim_token") or claim.get("generation") != successor.get("generation") or claim.get("launch_id") != successor.get("launch_id"):
            return _outcome("blocked", "stale-claim", ["handoff claim identity changed; recovery refused"], "repository-task", str(intent_key), manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        self._transition_handoff(intent, "failed")
        intent["terminal_recovery_evidence"] = dict(evidence)
        claim.update({"state": "replaced", "replaced_at": self.clock(), "recovery_reason": "provider-terminal-handoff-proof"})
        task.update({"status": "pending", "resume_allowed": False})
        manifest["generation"] = int(manifest.get("generation", 0)) + 1
        manifest.setdefault("history", []).append({"event": "ambiguous-handoff-recovered", "intent_id": intent.get("intent_id"), "task_id": task_id, "provider_session_id": evidence["provider_session_id"]})
        failure = self._persist_recovery_transition(manifest, "recover-ambiguous-handoff")
        if failure is not None:
            return _outcome("blocked", "recovery-postvalidation-failed", [failure], "repository-task", str(intent_key), manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        return _outcome("success", "handoff-recovered", ["exact provider terminal evidence closed the ambiguous launch fence"], "repository-task", str(intent_key), manifest["generation"], "continue-parent", task_id=task_id)

    def _member_receipt_fence(
        self,
        manifest: Mapping[str, Any],
        task_id: str,
        claim: Mapping[str, Any] | None,
        raw: Mapping[str, Any] | None,
        action_scope: str,
        checkpoint_identity: str,
    ) -> dict[str, Any] | None:
        """Fail closed on late batch-member receipts; None when the member may act.

        A closed, superseded, or aborted member receipt, a receipt that does
        not name the live group's active member, and an old-attempt or
        mismatched batch-progress envelope are each a blocked ``stale-claim``
        outcome with no state mutation. The member-scoped claim token stays
        the only authorization input; the group's diagnostic path union never
        authorizes anything.
        """

        group_id = (claim or {}).get("group_id")
        if not group_id:
            return None

        def stale(evidence: list[str]) -> dict[str, Any]:
            return _stale_claim_outcome(checkpoint_identity, int((claim or {}).get("generation", manifest.get("generation", 0))), evidence, action_scope)

        group = manifest.get("claim_groups", {}).get(group_id)
        if not isinstance(group, Mapping):
            return stale(["member claim references an unknown batch group"])
        if (claim or {}).get("state") not in {"claimed", "launched", "blocked"}:
            return stale(["receipt names a closed or superseded batch member"])
        if RuntimeDriver._claim_group_kind(manifest, claim, group) == GROUP_KIND_PARALLEL:
            # Concurrent members: the fence accepts any live member's receipt
            # at any time. No active-member ordinal gate exists (all members
            # are live together), no group attempt record is consulted (each
            # member launches through its own ordinary launch record), and no
            # shared anchor session is pinned: a receipt carrying a session
            # that disagrees with the member's OWN task session is fenced.
            if group.get("state") != "active":
                return stale(["receipt names a member of an inactive parallel group"])
            task = manifest.get("tasks", {}).get(task_id) or {}
            own_session = task.get("session_id")
            session_id = raw.get("session_id") if isinstance(raw, Mapping) else None
            if session_id and own_session and str(session_id) != str(own_session):
                return stale(["receipt session does not match the member's own session"])
            return None
        if group.get("state") != "active" or group.get("active_member") != task_id:
            return stale(["receipt does not name the active batch member"])
        attempt_record = (group.get("member_attempts") or {}).get(task_id) or {}
        live_attempt = int((claim or {}).get("attempt") or 0)
        if live_attempt != int(attempt_record.get("attempt", live_attempt)):
            return stale(["member attempt does not match the group attempt record"])
        progress = raw.get("batch_progress") if isinstance(raw, Mapping) else None
        if progress is not None:
            # The normalized envelope carries no credential: the
            # outer receipt's claim token was already verified against the
            # live claim before this fence ran, so the envelope check pins
            # only the identity fields it can actually carry.
            expected = {
                "batch_id": group_id,
                "member_id": task_id,
                "member_ordinal": (claim or {}).get("member_ordinal"),
                "attempt": (claim or {}).get("attempt"),
            }
            if not capabilities.validate_member_receipt(progress, expected):
                return stale(["batch member receipt does not match active group state"])
        # The session pin resolves the expected session through the
        # group anchor first, then the member's own task session: a receipt
        # carrying a session that matches neither the anchor nor the live
        # task session is fenced even when the anchor has not been captured
        # yet (the capture is receipt-driven and can lag one receipt).
        session_id = raw.get("session_id") if isinstance(raw, Mapping) else None
        anchor_session = self._member_session(manifest, manifest.get("tasks", {}).get(task_id) or {}, claim, anchor_first=True)
        if session_id and anchor_session and str(session_id) != str(anchor_session):
            return stale(["receipt session does not match the group anchor session"])
        return None

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
        if isinstance(outcome, _AdapterWindow):
            # A batch-member retry: the relaunch is the group's own
            # continuation primitive - an anchor-session resume through the
            # shared member window. The resume runs outside the lock and its
            # receipt re-enters record_worker_checkpoint, where the
            # driver-owned retry policy below keeps the budget converging.
            return self._resume_member_window(
                outcome.task,
                outcome.claim,
                "Rewrite the authorized repository task and return a structured result.",
                None,
                retry_policy=outcome.retry_policy,
            )
        return outcome

    def _record_checkpoint_locked(self, raw: Mapping[str, Any]) -> dict[str, Any] | _RetryRelaunch:
        result = self.validate_adapter_result(raw)
        if result.get("reason_code") == "malformed-result":
            # A malformed envelope refuses read-only: return before the
            # fence, before any claim lookup, latch, history append, or
            # checkpoint record write, so a self-inflicted malformed receipt
            # never converts a healthy claim into a blocked state; the
            # corrected re-submission under the same live claim token and
            # generation succeeds immediately.
            return result
        manifest = load_manifest(self.manifest_path)
        task_id = self._task_id_from_checkpoint(result["checkpoint_identity"])
        claim = manifest.get("claims", {}).get(task_id)
        claim_token = raw.get("claim_token")
        if not claim or not self._claim_owned_by_driver(claim) or not self._claim_receipt_owner_matches(claim, raw) or claim.get("token") != claim_token or claim.get("generation") != result["generation"]:
            return _outcome(
                "blocked",
                "owner-mismatch",
                ["checkpoint receipt does not match a live claim"],
                "repository-task",
                result["checkpoint_identity"],
                result["generation"],
                "preserve-and-reconcile",
            )
        member_fence = self._member_receipt_fence(manifest, task_id, claim, raw, "repository-task", result["checkpoint_identity"])
        if member_fence is not None:
            return member_fence
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
        progressed = _claim_progressed_past_receipt(task, claim)
        if retryable and progressed:
            retryable = False
        member_retry_session: str | None = None
        claim_group_kind = self._claim_group_kind(manifest, claim)
        if retryable and retry.get("attempts_remaining", 0) > 0 and self.adapter is not None and task is not None:
            if claim_group_kind == GROUP_KIND_BATCH:
                # A batch member never takes the plain driver relaunch.
                # That relaunch bypasses the group fences (launch refusal,
                # attempt rotation, member_attempts re-arm), and its fresh
                # session then always fails ``_member_receipt_fence``'s
                # session pin because the group anchor is already captured,
                # so every retry receipt fences and the group livelocks on
                # contradictory durable state. The member retry runs through
                # the group's own continuation primitive instead: with a
                # session anywhere (the member's own or the group anchor) the
                # retry is an anchor-session resume whose receipt re-enters
                # every member fence; with no session anywhere there is
                # nothing to resume and no legal member launch
                # (``_member_launch_refusal`` refuses a launched member), so
                # the receipt persists as the member's blocked state and the
                # operator recovers through the group path
                # (``continue --batch``; the recycle shape for the
                # anchor).
                member_retry_session = self._member_session(manifest, task, claim, anchor_first=False)
            # A parallel member has no anchor session to protect and carries
            # its own launch record, so its retryable receipt takes the plain
            # in-place relaunch exactly like a single-task claim; the member
            # fence's own-session pin still judges every retry receipt.
            if member_retry_session is not None or claim_group_kind != GROUP_KIND_BATCH:
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
                if member_retry_session is not None:
                    # The member keeps its pre-receipt task status: the
                    # resumed receipt owns the next transition exactly like
                    # every other member resume, so tasks[].status never
                    # disagrees with claims[].state across the retry window.
                    self._save(manifest)
                    return _AdapterWindow(task=dict(task, session_id=member_retry_session), claim=dict(claim), retry_policy=retry)
                task["status"] = "launched"
                if not isinstance(claim.get("launch_record"), Mapping) and not claim.get("group_id"):
                    # A driver-owned relaunch is a launch: snapshot the record for
                    # claims whose manifest predates launch records, so drift
                    # detection stays armed for the retry result. Group members
                    # never carry launch records; the group holds the one record.
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
        if (
            task is not None
            and not self._task_complete(task)
            and result["reason_code"] == "capacity-unavailable"
            and not claim.get("group_id")
        ):
            # A capacity receipt proves the worker never ran, so a
            # single-task claim parks in place instead of taking the blocked
            # shape: parking keeps the claim identity live for the in-place
            # resume. A group member never parks here (the group path owns
            # member recovery) and falls through to the shared persist below.
            return self._park_waiting_capacity_locked(manifest, task_id, claim, result, raw)
        if task and not self._task_complete(task):
            self._apply_blocked(manifest, task_id, result, resume_allowed=result["reason_code"] in capabilities.RESUMABLE_REASONS, session_id=raw.get("session_id"))
            self._save(manifest)
        return result

    def _park_waiting_capacity_locked(
        self,
        manifest: dict[str, Any],
        task_id: str,
        claim: Mapping[str, Any],
        result: dict[str, Any],
        raw: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Park a single-task claim in ``waiting-capacity`` under a bounded retry policy.

        Caller holds the manifest lock. A capacity receipt proves the worker
        never ran, so there is no dead session to fence and no rotation to
        pay: the claim keeps its token, generation, and launch record and
        carries the standard-shape bounded retry policy. The first capacity
        receipt parks with the full budget; each successive capacity receipt
        consumes one attempt; the receipt that arrives with the budget at
        zero ends the parked state through the shared blocked-persist tail
        (claim ``blocked``, the reclaimable lease state). The budget lives on
        the claim and is driver-owned: a worker- or adapter-supplied policy
        never re-supplies attempts.
        """

        prior = claim.get("retry_policy")
        if isinstance(prior, Mapping) and prior.get("mode") == "bounded-resume":
            remaining = int(prior.get("attempts_remaining", 0))
            if remaining <= 0:
                # Budget exhausted: the parked state ends and the claim takes
                # the existing blocked shape, whose standard recovery
                # machinery (resume fencing, lease-gated reclaim) applies.
                self._apply_blocked(manifest, task_id, result, resume_allowed=result["reason_code"] in capabilities.RESUMABLE_REASONS, session_id=raw.get("session_id"))
                self._save(manifest)
                return result
            policy = {
                "mode": "bounded-resume",
                "max_attempts": int(prior.get("max_attempts", WAITING_CAPACITY_RETRY_ATTEMPTS)),
                "attempts_remaining": remaining - 1,
            }
        else:
            policy = {
                "mode": "bounded-resume",
                "max_attempts": WAITING_CAPACITY_RETRY_ATTEMPTS,
                "attempts_remaining": WAITING_CAPACITY_RETRY_ATTEMPTS,
            }
        task = manifest["tasks"].get(task_id)
        result["recovery_action"] = "resume-same-claim"
        if task is not None:
            task["status"] = "blocked"
            task["resume_allowed"] = False
            task["blocked_receipt"] = dict(result)
            session_id = raw.get("session_id")
            if session_id:
                task["session_id"] = str(session_id)
        claim["state"] = "waiting-capacity"
        claim["retry_policy"] = policy
        manifest["history"].append({"event": "worker-blocked", "task_id": task_id, "reason_code": result.get("reason_code", "malformed-result")})
        self._save(manifest)
        return result

    @staticmethod
    def _member_session(
        manifest: Mapping[str, Any],
        task: Mapping[str, Any],
        claim: Mapping[str, Any] | None,
        *,
        anchor_first: bool,
    ) -> str | None:
        """The one member-session resolution, two explicit orders.

        Consolidates the four former spellings. Both precedence orders are
        semantic, not accidental:

        - ``anchor_first=True`` (the receipt fence's session pin and the
          advance capture) prefers the group's captured anchor session: a
          member's receipts pin to the group session even before the
          member's own task record carries it, and the advance must not
          re-derive a different session once one is captured.
        - ``anchor_first=False`` (the member retry and both group recovery
          entries) prefers the member's own task session: it is the session
          the member's live window actually runs in, with the anchor
          session as the fallback when the task record has none.

        Returns ``None`` when neither source carries a session (no legal
        member retry exists; nothing to resume).
        """

        group = manifest.get("claim_groups", {}).get(str((claim or {}).get("group_id") or ""))
        anchor_session = group.get("anchor_session") if isinstance(group, Mapping) else None
        task_session = task.get("session_id")
        session = (anchor_session or task_session) if anchor_first else (task_session or anchor_session)
        return str(session) if session else None

    def _checkpoint_success_commit(self, result: dict[str, Any], raw: Mapping[str, Any], manifest: dict[str, Any], task_id: str, claim_token: Any) -> dict[str, Any]:
        """Commit a successful checkpoint receipt and transition the task to done-pending.

        Runs inside the caller's held manifest lock; the locked snapshot is
        passed in, so no manifest reload is needed here.
        """

        # The same global fence the sibling receipt paths enforce: an
        # aborted workflow is never resurrected by a late success receipt.
        # The fence sits before the duplicate short-circuit (mirroring the
        # retry path's fence ordering) because the caller's identity check
        # has already matched the live claim.
        if manifest.get("workflow_state") == "aborted":
            return _abort_outcome(result["checkpoint_identity"], result["generation"], ["workflow was explicitly aborted before the success checkpoint"])
        identity = result["checkpoint_identity"]
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id)
        prior = manifest["checkpoints"].get(identity)
        if task is None:
            return self._result_error(f"unknown checkpoint task: {task_id}", result["generation"])
        if (
            prior is not None
            and prior.get("result", {}).get("status") == "success"
            and task.get("status") in PROGRESSED_TASK_STATUSES
        ):
            # The duplicate short-circuit is honored only when the durable
            # task status actually progressed: a stale success record under
            # the identity (for example one left by an interrupted predecessor
            # on a claimed task) must produce a real completion write, never
            # a phantom done-pending report with nothing persisted.
            return {**result, "state": "done-pending", "duplicate": True, "actions": []}
        if claim.get("state") not in {"claimed", "launched", "blocked"}:
            return _outcome("blocked", "owner-mismatch", ["checkpoint claim is not live"], "repository-task", identity, result["generation"], "preserve-and-reconcile")
        if claim.get("group_id") and self._claim_group_kind(manifest, claim) == GROUP_KIND_BATCH:
            # The anchor session is captured once from the first member
            # receipt that carries one; every later member resume reuses it.
            # Parallel members capture no group session: each member keeps
            # its own session on its own task record.
            group = manifest.get("claim_groups", {}).get(claim["group_id"])
            if isinstance(group, Mapping) and raw.get("session_id") and not group.get("anchor_session"):
                group["anchor_session"] = str(raw["session_id"])
        drift = self._claim_drift_outcome(manifest, claim, "repository-task", identity)
        if drift is not None:
            return drift
        # Uncommitted worktree contents do not determine checkpoint success.
        # The done boundary verifies the task's actual commit paths, while
        # path-limited staging and commits leave unrelated dirty paths out.
        completion: dict[str, Any] = {"status": "done-pending", "checkpoint_identity": identity}
        if raw.get("session_id"):
            completion["session_id"] = str(raw["session_id"])
        handoff_key = claim.get("handoff_intent_key")
        handoff_intent = manifest.get("handoff_intents", {}).get(handoff_key) if handoff_key else None
        if isinstance(handoff_intent, dict):
            if handoff_intent.get("state") != "launched" or not (handoff_intent.get("prelaunch_binding") or {}).get("consumed"):
                return _outcome("blocked", "owner-mismatch", ["successor checkpoint has no consumed matching launch binding"], "repository-task", identity, result["generation"], "preserve-and-reconcile", resume_allowed=False)
            self._transition_handoff(handoff_intent, "receipt-persisted")
            handoff_intent["checkpoint_identity"] = identity
        if not isinstance(claim.get("launch_record"), Mapping) and not claim.get("group_id"):
            # A fenced checkpoint proves the claim launched even when the
            # launch record was never written (manifests from before the
            # launch record existed); snapshot the claim's own live fields now
            # so later done-boundary drift checks stay armed. Group members
            # never carry launch records; the group holds the one record.
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
        fenced = claim and self._claim_owned_by_driver(claim) and self._claim_receipt_owner_matches(claim, raw) and claim.get("token") == raw.get("claim_token") and claim.get("generation") == raw.get("generation")
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
        if manifest.get("workflow_state") == "aborted":
            # The same global fence the sibling receipt paths enforce: an
            # aborted workflow is never completed by a late done handoff.
            return _abort_outcome(checkpoint_identity, manifest.get("generation", 0), ["workflow was explicitly aborted before the done handoff"], action_scope="done-handoff"), False
        member_fence = self._member_receipt_fence(manifest, task_id, claim, raw, "done-handoff", checkpoint_identity)
        if member_fence is not None:
            return member_fence, False
        stripped_identity = str(raw["commit_identity"]).strip()
        none_receipt = stripped_identity == "none"
        if not none_receipt and not self.commit_lookup(str(raw["commit_identity"])):
            return _outcome("blocked", "commit-pending", [f"commit not found: {raw['commit_identity']}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile"), False
        # The none receipt skips the commit lookup: the boundary witnesses
        # below prove the clean state themselves, and the recorded identity
        # is the justification literal, never a manufactured commit.
        boundary = self._done_boundary_block(claim, str(raw["commit_identity"]), checkpoint_identity, manifest.get("generation", 0), manifest=manifest)
        if boundary is not None:
            return boundary, False
        if task.get("status") == "checkpointed" and task.get("commit_identity") == raw["commit_identity"]:
            existing_intent = manifest.get("handoff_intents", {}).get(f"{task_id}:{checkpoint_identity}")
            actions = []
            if isinstance(existing_intent, Mapping) and isinstance(existing_intent.get("outcome_action"), Mapping):
                actions = [dict(existing_intent["outcome_action"])]
            return _outcome("success", "completed", ["duplicate done handoff"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=actions, duplicate=True), False
        stored_identity = stripped_identity if none_receipt else str(raw["commit_identity"])
        resume_action, claim_next, advance_blocked = self._advance_group_locked(manifest, task_id, stored_identity, checkpoint_identity)
        if advance_blocked is not None:
            return advance_blocked, False
        handoff_intent = None
        if resume_action is None and claim_next:
            handoff_intent = self._prepare_handoff_locked(manifest, task_id, checkpoint_identity)
        self._complete_and_persist(
            manifest,
            task_id,
            completion={
                "status": "checkpointed",
                "checkbox": True,
                "complete": True,
                "commit_identity": stored_identity,
                "done_log_evidence": bounded_evidence(raw["log_evidence"]),
            },
            # commit-pending is owned solely by mark_commit_pending; the done
            # handoff records only its own completion event.
            history=[
                {"event": "done-commit", "task_id": task_id, "commit_identity": stored_identity},
            ],
            claim_state="closed",
        )
        done_evidence = (
            "no-commit justification, checkbox, clean-state, and log evidence recorded"
            if none_receipt
            else "done commit, checkbox, clean-state, and log evidence recorded"
        )
        if resume_action is not None:
            # A member done advances the group under this manifest lock and
            # suppresses the generic next-claim: the parent resumes the next
            # member on the anchor session instead of launching a new task.
            return _outcome("success", "completed", [done_evidence], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[resume_action]), claim_next
        if handoff_intent is not None:
            action = dict(handoff_intent["outcome_action"])
            return _outcome("success", "completed", [done_evidence, f"handoff_intent={handoff_intent['intent_id']}"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[action]), False
        return _outcome("success", "completed", [done_evidence], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "continue-parent", actions=[]), claim_next

    def _advance_group_locked(self, manifest: dict[str, Any], task_id: str, commit_identity: str, checkpoint_identity: str) -> tuple[dict[str, Any] | None, bool, dict[str, Any] | None]:
        """Advance a live group after one member closed; caller holds the lock.

        Returns ``(resume_action, claim_next, blocked)``. The next member is
        initialized from the completed member commit (the moving baseline)
        with a freshly authorized member-scoped policy token under the same
        manifest lock that closes the completed member; the group's progress
        revision mirrors the authoritative manifest revision (no second
        counter). The last member closes the group and returns
        ``claim_next=True`` so the generic next-claim resumes only after the
        lock is released. Non-member claims pass through unchanged.

        Parallel-kind groups take the concurrent branch instead: there is no
        anchor session to capture and no next member to activate (all members
        run together), so a member done only re-derives the close rule
        (close = the last member reaching a terminal claim state) and always
        returns ``claim_next=True``.
        """

        claim = manifest["claims"].get(task_id) or {}
        group_id = claim.get("group_id")
        group = manifest.get("claim_groups", {}).get(group_id) if group_id else None
        if not isinstance(group, Mapping):
            return None, True, None
        members = list(group.get("members") or ())
        if self._claim_group_kind(manifest, claim, group) == GROUP_KIND_PARALLEL:
            if group.get("state") == "active" and task_id in members:
                # The done close runs the one terminal-membership predicate
                # shared with the reclaim and resume-release exits below:
                # every terminal transition of a parallel member re-derives
                # the close rule, so no release path can leave the group
                # active with zero live members.
                self._close_parallel_group_when_terminal_locked(manifest, group_id, task_id, group)
            return None, True, None
        if group.get("state") == "active" and task_id in members:
            index = members.index(task_id)
            if index + 1 < len(members):
                # The advance baseline is computed once for every hand-off
                # site below: a none done hands the driver's current HEAD
                # revision to the next member exactly as if a real commit
                # had landed, any other identity advances on itself. An
                # unreadable HEAD under a none done refuses the done as
                # commit-pending (fail closed) instead of seeding an empty
                # baseline the done-boundary witnesses cannot consume.
                advance_revision = self._git_head_revision() if str(commit_identity).strip() == "none" else str(commit_identity)
                if not advance_revision:
                    return None, False, _outcome("blocked", "commit-pending", ["no-commit advance baseline unavailable: HEAD revision could not be read"], "done-handoff", checkpoint_identity, manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
                # Anchor-session resolution: the anchor capture is
                # receipt-driven, so a member whose receipts carried no
                # session id leaves the group without one and the advance
                # could not resume the next member. Fall back to the
                # completed task's own session and capture it before giving
                # up; only when no session exists anywhere does the
                # release below stand.
                completed_task = manifest["tasks"].get(task_id) or {}
                anchor_session = self._member_session(manifest, completed_task, claim, anchor_first=True)
                if anchor_session and not group.get("anchor_session"):
                    group["anchor_session"] = str(anchor_session)
                    manifest.setdefault("history", []).append({
                        "event": "batch-anchor-session-captured",
                        "group_id": group_id,
                        "from": task_id,
                    })
                next_id = members[index + 1]
                if not anchor_session:
                    # No session exists anywhere (a schema-legal
                    # adapter whose receipts carry none). Refusing the done
                    # instead wedged the group forever: done replay,
                    # continue --batch, resume, and reclaim all refuse a
                    # done-pending member of a live group, so no entrypoint
                    # could ever leave the state. Fail the group atomically
                    # in the same release shape the authorization
                    # belt uses: the completed member's done lands below
                    # and the staged members re-enter the individual queue.
                    self._fail_group_release_locked(
                        manifest,
                        str(group_id),
                        task_id,
                        next_id,
                        members,
                        "no member session is available for the batch advance (r6 F1)",
                    )
                    return None, True, None
                next_claim = manifest["claims"].get(next_id)
                next_task = manifest["tasks"].get(next_id) or {}
                if not isinstance(next_claim, Mapping):
                    return None, False, self._result_error(f"batch member claim is absent: {next_id}", manifest.get("generation", 0), action_scope="done-handoff", checkpoint_identity=checkpoint_identity)
                envelope = ActionEnvelope(
                    str(self.repo_root),
                    tuple(str(path) for path in (next_claim.get("allowed_paths") or self._task_allowed_paths(next_task))),
                    str(next_task.get("operation_kind", "repository-task")),
                    next_task.get("network") is True,
                    (f"task={next_id}", f"plan={self.plan_slug}", f"group={group_id}"),
                )
                authorization = self.authorize_envelope(envelope, int(group.get("generation", 0)))
                if authorization["status"] != "success":
                    # Authorization belt: claim-time authorization and the prefix
                    # exclusion make this arm unreachable for a well-formed
                    # group, so it fires only on drifted state. Failing the
                    # group atomically here (the release shape) lets
                    # the completed member's done land and releases the
                    # staged members back to the individual queue; refusing
                    # the done instead would wedge the group forever, because
                    # every retry re-fails the same authorization. The
                    # released next member's task is claimed individually
                    # afterwards, where its launch path owns the refusal.
                    self._fail_group_release_locked(
                        manifest,
                        str(group_id),
                        task_id,
                        next_id,
                        members,
                        "next-member envelope authorization failed",
                    )
                    return None, True, None
                policy_token = authorization["policy_token"]
                # The lease timestamp refreshes at activation: the
                # claim lease measures member liveness from the moment the
                # member became active, so a group parked at a budget pause
                # does not age into reclaimable-looking leases (reclaim
                # refuses live-group members regardless, but the lease
                # field stays an honest activation timestamp).
                next_claim.update({"state": "claimed", "attempt": 1, "policy_token": policy_token, "baseline_revision": advance_revision, "timestamp": self.clock()})
                manifest["tasks"][next_id]["status"] = "claimed"
                self._set_group_state(manifest, str(group_id), "active", next_id)
                group.setdefault("member_attempts", {})[next_id] = {
                    "attempt": 1,
                    "token": next_claim["token"],
                    "baseline_revision": advance_revision,
                    "initialized_from": advance_revision,
                    "launched_at": self.clock(),
                }
                manifest["history"].append({"event": "batch-member-advanced", "group_id": group_id, "from": task_id, "to": next_id, "member_ordinal": next_claim.get("member_ordinal")})
                action = {
                    "type": "resume_member",
                    "group_id": group_id,
                    "task_id": next_id,
                    "member_ordinal": next_claim.get("member_ordinal"),
                    "session_id": group.get("anchor_session"),
                    "policy_token": policy_token,
                    "baseline_revision": advance_revision,
                }
                return action, False, None
            self._set_group_state(manifest, str(group_id), "closed", None)
            manifest["history"].append({"event": "batch-group-closed", "group_id": group_id})
        return None, True, None

    def _close_parallel_group_when_terminal_locked(
        self,
        manifest: dict[str, Any],
        group_id: Any,
        last_member: str,
        group: Mapping[str, Any],
    ) -> bool:
        """The ONE parallel-group terminal-membership close predicate.

        Caller holds the manifest lock. Close = the group is active, the
        transitioning member holds its seat, and every member claim is at a
        terminal claim state (the just-transitioned member is exempt: the
        caller records its own transition and the done handoff closes its
        claim only afterwards). Invoked at EVERY terminal transition of a
        parallel member - the done-handoff advance close, the per-member
        reclaim exit, and the session-less resume release - so no release
        path can leave the group active with zero live members (the wedge
        where every later claim is refused forever and reclaim cannot touch
        a terminal claim). Writes the closed state through the one group
        primitive and appends the ``parallel-group-closed`` history event.
        Returns True when the group closed here.
        """

        members = [str(member) for member in (group.get("members") or ())]
        if group.get("state") != "active" or last_member not in members:
            return False
        if not all(
            member == last_member
            or (manifest["claims"].get(member) or {}).get("state") in PARALLEL_MEMBER_TERMINAL_CLAIM_STATES
            for member in members
        ):
            return False
        self._set_group_state(manifest, str(group_id), "closed", None)
        manifest.setdefault("history", []).append({
            "event": "parallel-group-closed",
            "group_id": group_id,
            "last_member": last_member,
        })
        return True

    def _done_boundary_block(self, claim: Mapping[str, Any] | None, commit_identity: str, checkpoint_identity: str, generation: int, manifest: Mapping[str, Any]) -> dict[str, Any] | None:
        """Verify the done boundary against the claim's launch baseline.

        The committed artifact is checked, not just attested. Only a claim with
        a recorded launch baseline can be verified; the launch path fails
        closed when no baseline is available, so a missing baseline skips
        verification here (preserving the launch-time failure). Returns None
        when verification passes, or a blocked outcome describing the failure.
        ``manifest`` is the locked-read snapshot supplied by the caller; every
        call site runs under the manifest lock, so the parameter is required.

        A no-commit justification does not require a clean worktree or an
        unchanged HEAD: unrelated work may coexist with this task. A real
        commit is checked by its own first-parent path set, so peer commits
        made after the task baseline are not attributed to this task.
        """

        # Drift first: a claim whose launch-record snapshot no longer matches
        # the live manifest (or is missing on a demonstrably launched claim)
        # must surface stale-claim before any commit handoff.
        drift = self._claim_drift_outcome(manifest, claim, "done-handoff", checkpoint_identity)
        if drift is not None:
            return drift
        allowed = set((claim.get("policy_token") or {}).get("allowed_paths", ()))
        if str(commit_identity).strip() == "none":
            return None
        baseline_revision = str((claim or {}).get("baseline_revision") or "").strip()
        if not baseline_revision:
            return None
        is_descendant, witness_ok = self._git_commit_is_descendant(baseline_revision, commit_identity)
        if not witness_ok or not allowed:
            return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary git witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        if not is_descendant:
            shares_history, history_witness_ok = self._git_commits_share_history(baseline_revision, commit_identity)
            if not history_witness_ok:
                return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary shared-history witness failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
            if not shares_history:
                return _outcome("blocked", "commit-pending", [f"commit is not new work on the claim baseline: {commit_identity}"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
        # A parallel member's committed-paths witness measures the done
        # commit's OWN change set (first-parent diff), not the cumulative
        # diff since its launch baseline: per-member done runs after all
        # members land, so the member's commit sits on top of its siblings'
        # commits and a baseline-cumulative diff would name the siblings'
        # committed files as this member's scope escape. The descendant check
        # above still pins the commit to the claim's recorded baseline.
        committed_paths = self._git_commit_own_paths(commit_identity)
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
        task_id = self._task_id_from_checkpoint(checkpoint_identity)
        task = manifest.get("tasks", {}).get(task_id, {})
        if manifest.get("evidence_enforcement") is True and task.get("required_criteria"):
            receipts = manifest.get("verification_evidence", {}).get(task_id, {})
            expected = {envelope.get("source_digest") for envelope in receipts.values() if isinstance(envelope, Mapping)} if isinstance(receipts, Mapping) else set()
            try:
                committed_source_digest = self._task_source_digest(sorted(allowed), revision=commit_identity)
            except (OSError, subprocess.SubprocessError, ValueError):
                return _outcome("blocked", "worktree-witness-unavailable", ["done-boundary verification source snapshot failed"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
            if committed_source_digest not in expected:
                return _outcome("blocked", "commit-pending", ["task commit contents do not match driver-captured verification evidence"], "done-handoff", checkpoint_identity, generation, "preserve-and-reconcile", resume_allowed=False)
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

    @staticmethod
    def _task_allowed_paths(task: Mapping[str, Any]) -> tuple[str, ...]:
        """A task's persisted allowed paths (canonical when create seeded them)."""

        paths = task.get("allowed_paths", task.get("files", ()))
        if isinstance(paths, str) or not isinstance(paths, (list, tuple)):
            return ()
        return tuple(str(path) for path in paths)

    @staticmethod
    def _live_group(manifest: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """The one authoritative live claim group, or None."""

        groups = manifest.get("claim_groups")
        if not isinstance(groups, Mapping):
            return None
        for group in groups.values():
            if isinstance(group, Mapping) and group.get("state") == "active":
                return group
        return None

    @staticmethod
    def _claim_group_kind(manifest: Mapping[str, Any], claim: Mapping[str, Any] | None, group: Mapping[str, Any] | None = None) -> str:
        """The one group-kind discriminator read every group-protocol branch shares.

        Returns ``GROUP_KIND_PARALLEL`` or ``GROUP_KIND_BATCH`` for a claimed
        member (a legacy record with no ``kind`` field reads as batch, so
        pre-parallel manifests behave byte-identically), and ``"none"`` when
        the claim carries no group reference. A pre-resolved group record may
        be passed by callers that already hold it.
        """

        if group is None:
            group_id = (claim or {}).get("group_id")
            if not group_id:
                return "none"
            group = (manifest.get("claim_groups") or {}).get(str(group_id))
        if not isinstance(group, Mapping):
            return GROUP_KIND_BATCH
        return str(group.get("kind") or GROUP_KIND_BATCH)

    @staticmethod
    def _parallel_sibling_paths(manifest: Mapping[str, Any], claim: Mapping[str, Any] | None) -> frozenset[str]:
        """Allowed-path union of a parallel member's siblings, or empty.

        A member of an ACTIVE parallel group works in the shared worktree at
        the same time as its siblings, so the siblings' claimed files sit
        changed-but-uncommitted while this member's receipts run. They are
        the group's claimed in-flight work, never foreign changes, and both
        member-scoped path witnesses (the checkpoint scope witness and the
        done-boundary clean-state witness) subtract this set before judging.
        Every path outside it keeps the full witness force. Batch members
        never qualify: their protocol is sequential in one session with a
        moving baseline, so no sibling files exist while a batch member runs.
        """

        if RuntimeDriver._claim_group_kind(manifest, claim) != GROUP_KIND_PARALLEL:
            return frozenset()
        group_id = str((claim or {}).get("group_id") or "")
        group = (manifest.get("claim_groups") or {}).get(group_id)
        if not isinstance(group, Mapping) or group.get("state") != "active":
            return frozenset()
        task_id = str((claim or {}).get("task_id") or "")
        siblings: set[str] = set()
        for member in group.get("members") or ():
            member = str(member)
            if member == task_id:
                continue
            member_claim = manifest.get("claims", {}).get(member) or {}
            paths = member_claim.get("allowed_paths")
            if not paths:
                paths = (manifest.get("tasks", {}).get(member) or {}).get("allowed_paths", ())
            if isinstance(paths, str) or not isinstance(paths, (list, tuple)):
                continue
            siblings.update(str(path) for path in paths)
        return frozenset(siblings)

    @staticmethod
    def _set_group_state(
        manifest: dict[str, Any],
        group_id: str,
        state: str,
        active_member: str | None,
    ) -> Mapping[str, Any] | None:
        """The ONE batch claim-group state mutation primitive (single choke point).

        Every group lifecycle transition routes through this helper and no
        other site writes ``claim_groups[group_id]["state"]`` or
        ``active_member``: activate (claim creation and the anchor launch
        re-arm), advance (member done handoff), fail (the reclaim-time
        release and the advance-time belt), and close (the last
        member's done). The semantic progress revision mirror rides every
        transition so the group never carries a second progress counter.
        Unknown states fail closed; a missing group record returns None and
        leaves the refusal to the caller's existing group guard. The total
        group state x operation table this primitive serves is normative in
        the runtime contract's batch claim groups section and pinned cell by
        cell by the exhaustiveness test.
        """

        if state not in BATCH_GROUP_STATES:
            raise ValueError(f"unknown batch group state: {state}")
        group = (manifest.get("claim_groups") or {}).get(group_id)
        if not isinstance(group, dict):
            return None
        group["state"] = state
        group["active_member"] = active_member
        group["progress_revision"] = int(manifest.get("progress_revision", 0))
        return group

    def _fail_group_release_locked(
        self,
        manifest: dict[str, Any],
        group_id: str,
        completed_member: str,
        blocked_member: str,
        members: Sequence[str],
        reason: str,
    ) -> list[str]:
        """The advance-time group release, one shape shared by its arms.

        Caller holds the manifest lock and the group is live with the
        completed member still holding its seat. One save shape: the
        still-staged member claims (every member but the completed one,
        whose live claim the caller's done closes next) close so their
        pending tasks re-enter the queue as individual claims, the group
        terminal state is written through the one choke-point primitive
        (``failed``, active member cleared), and the ``batch-group-failed``
        history event names the member whose activation was blocked, the
        released claims, and the reason. Refusing the done instead would
        wedge the group forever. Arms: the next member's envelope
        authorization failing (a state drift) and no member session existing
        anywhere for the anchor resume.
        """

        released = [
            member
            for member in members
            if member != completed_member and (manifest["claims"].get(member) or {}).get("state") == "staged"
        ]
        for member in released:
            manifest["claims"][member]["state"] = "closed"
        self._set_group_state(manifest, str(group_id), "failed", None)
        manifest.setdefault("history", []).append({
            "event": "batch-group-failed",
            "group_id": group_id,
            "member": blocked_member,
            "released_members": released,
            "reason": reason,
        })
        return released

    def _compute_batch_prefix(self, pending: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        """Maximal file-disjoint prefix of the pending queue for one batch.

        Canonical document order (the persisted ordinal; the prefix is
        re-sorted so a caller's ordering can never leak task-number order
        into the batch queue), no skipping past an overlapping task, the
        shared parallel-group numeric caps (``PARALLEL_GROUP_MEMBER_CAP``,
        ``PARALLEL_GROUP_COMBINED_FILE_CAP`` - the one source of truth for
        both the batch prefix and the parallel-group claim refusals). A
        zero-scope or network-flagged pending task ends the prefix: its
        envelope can never be authorized, so the batch contract never stages
        it as a member and its single-task launch path owns the
        authorization refusal.
        """

        ordered = sorted(pending, key=_pending_sort_key)
        members: list[Mapping[str, Any]] = []
        member_paths: list[set[str]] = []
        combined = 0
        for task in ordered:
            if len(members) >= PARALLEL_GROUP_MEMBER_CAP:
                break
            paths = set(self._task_allowed_paths(task))
            if not paths or task.get("network") is True:
                # A member whose envelope is guaranteed to fail authorization
                # would wedge the group at its advance (the previous member's
                # done handoff authorizes the next member's envelope), so the
                # task ends the prefix and stays in the individual queue.
                break
            if members:
                if combined + len(paths) > PARALLEL_GROUP_COMBINED_FILE_CAP:
                    break
                if any(paths & prior for prior in member_paths):
                    break
            members.append(task)
            member_paths.append(paths)
            combined += len(paths)
        return members

    def _claim_batch_locked(self, manifest: dict[str, Any], prefix: list[Mapping[str, Any]]) -> dict[str, Any]:
        """Create one claim group with ordered member claims; caller holds the lock.

        One generation bump covers the whole group. Every member claim
        carries that generation, its own canonical allowed paths, its
        explicit ordinal, and the group reference; only the anchor claim
        starts live and later members stay staged (tasks pending) until the
        group advances to them. The group's policy union is recorded for
        diagnostics only; it never authorizes actions. Every member's
        envelope is authorized here, before any state write: a
        member whose envelope cannot be authorized refuses the batch claim
        cheaply and leaves the manifest untouched, instead of staging a
        member whose advance-time authorization is guaranteed to fail and
        wedging the group on the previous member's done handoff.
        """

        manifest["generation"] = int(manifest.get("generation", 0)) + 1
        generation = manifest["generation"]
        group_id = f"group-{generation}"
        member_ids = [str(task["id"]) for task in prefix]
        for member_id, task in zip(member_ids, prefix):
            envelope = ActionEnvelope(
                str(self.repo_root),
                tuple(str(path) for path in self._task_allowed_paths(task)),
                str(task.get("operation_kind", "repository-task")),
                task.get("network") is True,
                (f"task={member_id}", f"plan={self.plan_slug}", f"group={group_id}"),
            )
            authorization = self.authorize_envelope(envelope, generation)
            if authorization["status"] != "success":
                # Nothing was persisted: the in-memory generation bump is
                # discarded with the unsaved manifest snapshot.
                return authorization
        member_ordinals = {member_id: ordinal for ordinal, member_id in enumerate(member_ids, start=1)}
        member_paths = {member_id: list(self._task_allowed_paths(task)) for member_id, task in zip(member_ids, prefix)}
        timestamp = self.clock()
        for position, member_id in enumerate(member_ids):
            active = position == 0
            manifest["claims"][member_id] = {
                "token": uuid.uuid4().hex,
                "generation": generation,
                "owner": self.owner,
                "timestamp": timestamp,
                "state": "claimed" if active else "staged",
                "task_id": member_id,
                "group_id": group_id,
                "member_ordinal": member_ordinals[member_id],
                "attempt": 1 if active else 0,
                "allowed_paths": member_paths[member_id],
            }
            manifest["tasks"][member_id]["status"] = "claimed" if active else "pending"
        manifest.setdefault("claim_groups", {})[group_id] = {
            "group_id": group_id,
            "anchor": member_ids[0],
            "members": member_ids,
            "member_ordinals": member_ordinals,
            "member_paths": member_paths,
            "generation": generation,
            "launch_record": None,
            "anchor_session": None,
            "member_attempts": {},
        }
        # Activate through the one primitive: state, active member, and the
        # progress-revision mirror are lifecycle writes like any other.
        self._set_group_state(manifest, group_id, "active", member_ids[0])
        self._save(manifest)
        return {
            "status": "success",
            "claimed": True,
            "task_id": member_ids[0],
            "generation": generation,
            "token": manifest["claims"][member_ids[0]]["token"],
            "actions": [],
            "batch": True,
            "group_id": group_id,
            "members": member_ids,
            "member_ordinals": member_ordinals,
        }

    def claim_next_task(self, batch: bool = False) -> dict[str, Any]:
        """Claim the next pending task; ``batch`` opts in to a claim group.

        This is the default-off `batch` opt-in on claim: a no-flag claim is
        exactly the single-task claim. An opted-in claim assembles the maximal
        file-disjoint prefix of the pending queue and claims it as one group
        with one generation bump; a one-member prefix falls back to the
        single-task claim with no batch fields.
        """

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
            pending_handoff = next((
                (intent_key, intent) for intent_key, intent in manifest.get("handoff_intents", {}).items()
                if isinstance(intent, Mapping) and intent.get("state") in {"prepared", "launching", "launched", "ambiguous"}
            ), None)
            if pending_handoff is not None:
                intent_key, intent = pending_handoff
                if intent.get("state") == "prepared":
                    successor = intent.get("successor") or {}
                    task_id = str(successor.get("task_id", "")) if isinstance(successor, Mapping) else ""
                    task = manifest.get("tasks", {}).get(task_id)
                    claim = manifest.get("claims", {}).get(task_id)
                    if (
                        intent.get("launch_receipt") is None
                        and isinstance(task, Mapping) and task.get("status") == "pending"
                        and isinstance(claim, Mapping) and claim.get("state") == "replaced"
                        and claim.get("handoff_intent_key") == intent_key
                        and claim.get("launch_record") is None
                    ):
                        self._transition_handoff(intent, "failed")
                        intent["failure_reason"] = "prepared successor claim was replaced before launch"
                        intent["failed_at"] = self.clock()
                    else:
                        return {"status": "success", "claimed": True, **dict(successor), "actions": [], "adopted_handoff": intent.get("intent_id")}
                else:
                    return _outcome("blocked", "ambiguous", [f"handoff intent {intent.get('intent_id')} is {intent.get('state')}; reconcile it before another claim"], "repository-task", str(intent.get("idempotency_key", "handoff")), manifest.get("generation", 0), "preserve-and-reconcile", claimed=False, resume_allowed=False)
            pending = [task for task in manifest["tasks"].values() if not self._task_complete(task) and task.get("status") == "pending"]
            pending.sort(key=_pending_sort_key)
            if not pending:
                return {"status": "success", "claimed": False, "actions": [], "generation": manifest.get("generation", 0)}
            existing_claim = next((claim for claim in manifest["claims"].values() if claim.get("state") in {"claimed", "launched", "waiting-capacity"}), None)
            if existing_claim:
                return _outcome("blocked", "stale-claim", ["another task is already claimed"], "repository-task", existing_claim.get("token", "claim"), manifest.get("generation", 0), "resumable-conflict", claimed=False)
            live_group = self._live_group(manifest)
            if live_group is not None:
                # A live batch group holds the one implement launch; a second
                # claim (flagged or not) keeps the blocked stale-claim
                # outcome until the group closes.
                return _outcome("blocked", "stale-claim", ["another task is already claimed"], "repository-task", str(live_group.get("active_member") or live_group.get("anchor") or live_group.get("group_id", "claim")), manifest.get("generation", 0), "resumable-conflict", claimed=False)
            if batch:
                prefix = self._compute_batch_prefix(pending)
                if len(prefix) > 1:
                    return self._claim_batch_locked(manifest, prefix)
                # A one-member prefix falls back to the single-task claim.
            task = pending[0]
            manifest["generation"] = int(manifest.get("generation", 0)) + 1
            token = uuid.uuid4().hex
            launch_id = uuid.uuid4().hex
            claim = {"token": token, "generation": manifest["generation"], "owner": self.owner, "timestamp": self.clock(), "state": "claimed", "task_id": task["id"], "launch_id": launch_id}
            manifest["claims"][task["id"]] = claim
            task["status"] = "claimed"
            self._save(manifest)
            return {"status": "success", "claimed": True, "task_id": task["id"], "generation": manifest["generation"], "token": token, "launch_id": launch_id, "actions": []}

    def claim_parallel_group(self, member_ids: Sequence[str]) -> dict[str, Any]:
        """Claim the requested tasks as one parallel implement group.

        The parallel-group operation on the claim path: the orchestrator
        selects the next K unchecked tasks in canonical document order and
        requests them by id; the driver trusts nothing and re-derives every
        membership condition from the manifest before any state write. The
        membership disjointness computation is the batch prefix's (pairwise
        disjoint canonical ``Files:`` sets over the manifest's canonical
        allowed paths, canonical document order, no ineligible member), but
        evaluated per requested member with a refusal instead of a prefix
        stop, and the batch numeric caps are carried verbatim as the
        known-safe envelope (4 members, 8 combined canonical member files):
        an overlapping or over-cap request refuses at claim time with
        stale-claim evidence naming the violation, never truncates silently.
        The requested set must also be exactly the next pending tasks of the
        canonical queue (no skipping past a pending task).

        Divergence points threaded from the batch protocol, which otherwise
        stays untouched: the group record carries the ``kind: parallel``
        discriminator; all members claim live together (no staged members,
        no anchor, no active-member ordinal gate); each member keeps its own
        session, claim, policy token, and log path; reclaim is per member
        (the terminal-receipt exit releases only that member); close = the
        last member reaching a terminal claim state. One generation bump
        covers the whole group, and every member's envelope is authorized
        before any state write (a member whose envelope cannot be authorized
        refuses the claim cheaply, leaving the manifest untouched).
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            manifest = load_manifest(self.manifest_path)
            if not acquired:
                return _outcome("blocked", "stale-claim", ["manifest claim is held by another owner"], "repository-task", "claim:conflict", manifest.get("generation", 0), "resumable-conflict", claimed=False)
            if manifest.get("workflow_state") == "aborted":
                # An explicitly aborted workflow never hands out a new claim.
                return _abort_outcome(
                    "claim:aborted",
                    manifest.get("generation", 0),
                    ["workflow was explicitly aborted before claim"],
                    claimed=False,
                )

            def refuse(evidence: list[str]) -> dict[str, Any]:
                return _outcome("blocked", "stale-claim", evidence, "repository-task", "claim:parallel-group", manifest.get("generation", 0), "resumable-conflict", claimed=False)

            requested = [str(member) for member in member_ids]
            if len(set(requested)) != len(requested):
                return refuse(["parallel group membership names a task twice"])
            if len(requested) < 2:
                return refuse([f"a parallel group requires at least two members; {len(requested)} requested"])
            unknown = [member for member in requested if member not in manifest["tasks"]]
            if unknown:
                return refuse([f"parallel group names unknown task '{member}'" for member in unknown])
            pending = [task for task in manifest["tasks"].values() if not self._task_complete(task) and task.get("status") == "pending"]
            pending.sort(key=_pending_sort_key)
            pending_ids = [str(task["id"]) for task in pending]
            requested_set = set(requested)
            not_pending = [member for member in requested if member not in pending_ids]
            if not_pending:
                return refuse([
                    f"parallel group member '{member}' is not pending (status: {manifest['tasks'][member].get('status')})"
                    for member in not_pending
                ])
            # Canonical document-order prefix: the requested set is exactly
            # the next len(requested) pending tasks, so a parallel group can
            # never skip past a pending task the way the batch prefix never
            # skips past an overlapping one.
            expected = pending_ids[:len(requested)]
            if set(expected) != requested_set:
                skipped = next((member for member in expected if member not in requested_set), expected[-1] if expected else "unknown")
                return refuse([f"parallel group membership must be the next pending tasks in canonical document order; '{skipped}' precedes the requested set"])
            existing_claim = next((claim for claim in manifest["claims"].values() if claim.get("state") in {"claimed", "launched", "waiting-capacity"}), None)
            if existing_claim:
                return _outcome("blocked", "stale-claim", ["another task is already claimed"], "repository-task", existing_claim.get("token", "claim"), manifest.get("generation", 0), "resumable-conflict", claimed=False)
            if self._live_group(manifest) is not None:
                return _outcome("blocked", "stale-claim", ["another task is already claimed"], "repository-task", "claim:parallel-group", manifest.get("generation", 0), "resumable-conflict", claimed=False)
            members = [task for task in pending if str(task["id"]) in requested_set]
            # The batch membership disjointness computation, evaluated per
            # requested member with refusal instead of a prefix stop.
            member_path_sets: list[set[str]] = []
            combined = 0
            for task in members:
                member_id = str(task["id"])
                paths = set(self._task_allowed_paths(task))
                if not paths or task.get("network") is True:
                    return refuse([f"parallel member '{member_id}' has no authorizable envelope (empty scope or network flag); its single-task launch path owns the authorization refusal"])
                if member_path_sets:
                    if combined + len(paths) > PARALLEL_GROUP_COMBINED_FILE_CAP:
                        return refuse([f"parallel group exceeds the combined member file cap: {combined + len(paths)} combined canonical files exceeds the batch cap of {PARALLEL_GROUP_COMBINED_FILE_CAP} (batch numeric caps carried verbatim: {PARALLEL_GROUP_MEMBER_CAP} members, {PARALLEL_GROUP_COMBINED_FILE_CAP} combined member files)"])
                    for prior_position, prior_paths in enumerate(member_path_sets):
                        shared = paths & prior_paths
                        if shared:
                            prior_id = str(members[prior_position]["id"])
                            return refuse([f"parallel group members {prior_id} and {member_id} share canonical file(s): {', '.join(sorted(shared))}"])
                member_path_sets.append(paths)
                combined += len(paths)
            if len(members) > PARALLEL_GROUP_MEMBER_CAP:
                return refuse([f"parallel group exceeds the member cap: {len(members)} requested members exceeds the batch cap of {PARALLEL_GROUP_MEMBER_CAP} (batch numeric caps carried verbatim: {PARALLEL_GROUP_MEMBER_CAP} members, {PARALLEL_GROUP_COMBINED_FILE_CAP} combined member files)"])
            manifest["generation"] = int(manifest.get("generation", 0)) + 1
            generation = manifest["generation"]
            group_id = f"group-{generation}"
            for task in members:
                member_id = str(task["id"])
                envelope = ActionEnvelope(
                    str(self.repo_root),
                    tuple(str(path) for path in self._task_allowed_paths(task)),
                    str(task.get("operation_kind", "repository-task")),
                    task.get("network") is True,
                    (f"task={member_id}", f"plan={self.plan_slug}", f"group={group_id}"),
                )
                authorization = self.authorize_envelope(envelope, generation)
                if authorization["status"] != "success":
                    # Nothing was persisted: the in-memory generation bump is
                    # discarded with the unsaved manifest snapshot.
                    return authorization
            member_ids_canonical = [str(task["id"]) for task in members]
            member_ordinals = {member_id: ordinal for ordinal, member_id in enumerate(member_ids_canonical, start=1)}
            member_paths = {member_id: list(self._task_allowed_paths(task)) for member_id, task in zip(member_ids_canonical, members)}
            timestamp = self.clock()
            for member_id in member_ids_canonical:
                # Every member claims live together: an ordinary claim (own
                # token, own canonical paths, own ordinal) bound to the group,
                # with no staged state and no anchor.
                manifest["claims"][member_id] = {
                    "token": uuid.uuid4().hex,
                    "generation": generation,
                    "owner": self.owner,
                    "timestamp": timestamp,
                "state": "claimed",
                "task_id": member_id,
                "launch_id": uuid.uuid4().hex,
                "group_id": group_id,
                    "member_ordinal": member_ordinals[member_id],
                    "allowed_paths": member_paths[member_id],
                }
                manifest["tasks"][member_id]["status"] = "claimed"
            manifest.setdefault("claim_groups", {})[group_id] = {
                "group_id": group_id,
                "kind": GROUP_KIND_PARALLEL,
                "members": member_ids_canonical,
                "member_ordinals": member_ordinals,
                "member_paths": member_paths,
                "generation": generation,
            }
            # Activate through the one primitive: state active, no active
            # member (concurrent members have no ordinal gate), and the
            # progress-revision mirror ride every lifecycle transition.
            self._set_group_state(manifest, group_id, "active", None)
            self._save(manifest)
            return {
                "status": "success",
                "claimed": True,
                "parallel": True,
                "generation": generation,
                "group_id": group_id,
                "members": member_ids_canonical,
                "member_ordinals": member_ordinals,
                "actions": [],
            }

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
            or current_claim.get("owner") != claim.get("owner")
            or current_claim.get("claim_owner_id") != claim.get("claim_owner_id")
            or not self._claim_owned_by_driver(current_claim)
            or current_claim.get("launch_id") != claim.get("launch_id")
            or current_claim.get("state") not in {"claimed", "launched", "waiting-capacity"}
        ):
            # The launch fence also admits a parked claim: the capacity
            # resume relaunches the SAME claim in place (token and generation
            # unchanged, no second claim row, no reclaim rotation).
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        intent_key = current_claim.get("handoff_intent_key")
        intent = manifest.get("handoff_intents", {}).get(intent_key) if intent_key else None
        if isinstance(intent, Mapping):
            if intent.get("state") != "prepared":
                return _outcome("blocked", "ambiguous", [f"handoff intent is {intent.get('state')}; external launch outcome is not safe to repeat"], "parent-continuation", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=False)
            self._transition_handoff(intent, "launching")
        launch_id = current_claim.get("launch_id") or claim.get("launch_id") or uuid.uuid4().hex
        current_claim["launch_id"] = launch_id
        reservations = manifest.setdefault("capacity", {}).setdefault("reservations", {})
        reservation_id = f"{task_id}:{claim['generation']}:{launch_id}"
        if any(key != reservation_id for key in reservations):
            return _outcome("blocked", "capacity-unavailable", ["another task holds a durable adapter launch reservation"], "parent-continuation", f"{task_id}:launch", int(claim["generation"]), "preserve-and-reconcile", claim_token=claim["token"])
        baseline_revision = self._git_head_revision()
        if not baseline_revision:
            # A missing baseline would silently disable the scope witness at
            # every later checkpoint; fail closed at launch instead.
            return _outcome("blocked", "worktree-witness-unavailable", ["git baseline revision unavailable at launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=False)
        launch_record = self._launch_record({**claim, "launch_id": launch_id}, baseline_revision)
        current_claim.update({"state": "launched", "policy_token": policy_token, "baseline_revision": baseline_revision, "launch_record": launch_record})
        reservations[reservation_id] = {"task_id": task_id, "claim_token": claim["token"], "generation": claim["generation"], "launch_id": launch_id, "reserved_at": self.clock()}
        # Re-fetch the task from this live snapshot; a task object captured
        # from an earlier manifest snapshot would be silently dropped on save.
        manifest["tasks"][task_id]["status"] = "launched"
        manifest["history"].append({"event": "started", "task_id": task_id, "generation": claim["generation"]})
        self._save(manifest)
        return None

    @_locked_mutation
    def _mark_group_launched(self, claim: Mapping[str, Any], task_id: str, policy_token: Mapping[str, Any]) -> dict[str, Any] | None:
        """Fence the group anchor launch; ONE launch record lives on the group.

        The group's launch record is the immutable launch identity for every
        member: the baseline revision is snapshotted exactly once, member
        claims carry no launch records of their own, and later members
        resume the same anchor session without a second launch record.
        """

        manifest = load_manifest(self.manifest_path)
        current_claim = manifest["claims"].get(task_id)
        group = manifest.get("claim_groups", {}).get(claim.get("group_id"))
        if manifest.get("workflow_state") == "aborted":
            # An explicit abort racing the launch window is an abort outcome,
            # not an owner mismatch: the claim may still be live and owned.
            return _abort_outcome(claim["token"], claim["generation"], ["workflow was explicitly aborted before launch"])
        if (
            not current_claim
            or current_claim.get("token") != claim["token"]
            or current_claim.get("generation") != claim["generation"]
            or current_claim.get("state") not in {"claimed", "launched"}
            or not isinstance(group, Mapping)
            or group.get("state") != "active"
            or group.get("active_member") != task_id
        ):
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        baseline_revision = self._git_head_revision()
        if not baseline_revision:
            return _outcome("blocked", "worktree-witness-unavailable", ["git baseline revision unavailable at launch"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile", resume_allowed=False)
        if not isinstance(group.get("launch_record"), Mapping):
            group["launch_record"] = self._launch_record({"generation": group.get("generation")}, baseline_revision)
        reservations = manifest.setdefault("capacity", {}).setdefault("reservations", {})
        reservation_id = f"{task_id}:{claim['generation']}:{claim.get('launch_id', group.get('group_id'))}"
        if any(key != reservation_id for key in reservations):
            return _outcome("blocked", "capacity-unavailable", ["another task holds a durable adapter launch reservation"], "parent-continuation", f"{task_id}:launch", int(claim["generation"]), "preserve-and-reconcile", claim_token=claim["token"])
        reservations[reservation_id] = {"task_id": task_id, "claim_token": claim["token"], "generation": claim["generation"], "launch_id": claim.get("launch_id", group.get("group_id")), "reserved_at": self.clock()}
        # Re-assert the active group state through the one primitive: the
        # launch fence above already proved state == "active" and
        # active_member == task_id, so this write is the activation record.
        self._set_group_state(manifest, str(claim.get("group_id")), "active", task_id)
        attempt = int(current_claim.get("attempt") or 1)
        group.setdefault("member_attempts", {})[task_id] = {
            "attempt": attempt,
            "token": current_claim["token"],
            "baseline_revision": baseline_revision,
            "launched_at": self.clock(),
        }
        # The lease timestamp refreshes at activation: the anchor
        # claim's lease measures liveness from the launch, not the claim.
        current_claim.update({"state": "launched", "policy_token": policy_token, "baseline_revision": baseline_revision, "timestamp": self.clock()})
        manifest["tasks"][task_id]["status"] = "launched"
        manifest["history"].append({"event": "started", "task_id": task_id, "generation": claim["generation"], "group_id": claim.get("group_id")})
        self._save(manifest)
        return None

    @_locked_mutation
    def _record_activation_receipt(self, claim: Mapping[str, Any], task_id: str, activation: Mapping[str, Any]) -> dict[str, Any] | None:
        """Fence the activation-receipt write; re-verify the claim under the lock."""

        manifest = load_manifest(self.manifest_path)
        current_claim = manifest["claims"].get(task_id)
        if manifest.get("workflow_state") == "aborted":
            # An explicit abort racing the activation window is an abort
            # outcome, not an owner mismatch: the claim may still be live
            # and owned.
            return _abort_outcome(claim["token"], claim["generation"], ["workflow was explicitly aborted before the activation receipt"])
        if not current_claim or current_claim.get("token") != claim["token"] or current_claim.get("generation") != claim["generation"]:
            return _outcome("blocked", "owner-mismatch", ["claim changed before activation receipt"], "repository-task", str(claim["token"]), int(claim["generation"]), "preserve-and-reconcile")
        if current_claim.get("state") not in {"claimed", "launched"}:
            # A claim that left the live set on an active workflow is
            # contention or progression, not an abort: surface the resumable
            # stale-claim outcome instead of an explicit-abort envelope.
            return _stale_claim_outcome(claim["token"], claim["generation"], ["claim is no longer live; activation receipt refused"])
        current_claim["activation_receipt"] = getattr(self.adapter, "activation_receipt", dict(activation))
        self._save(manifest)
        return None

    def _member_launch_refusal(self, claim: Mapping[str, Any], task_id: str) -> dict[str, Any] | None:
        """Refuse a launch that would bypass the group session protocol.

        Batch groups: only the anchor's initial launch (live group, no anchor
        session yet) is a launch; later batch members resume the anchor
        session, so any other member launch attempt fails closed as
        stale-claim. Parallel groups: every member's initial launch IS an
        ordinary launch on its own session, so the only gate is that the
        member is a claimed member of the still-active group.
        """

        manifest = load_manifest(self.manifest_path)
        group = manifest.get("claim_groups", {}).get(claim.get("group_id"))
        current_claim = manifest.get("claims", {}).get(task_id) or {}
        if isinstance(group, Mapping) and str(group.get("kind") or GROUP_KIND_BATCH) == GROUP_KIND_PARALLEL:
            if group.get("state") != "active" or current_claim.get("state") != "claimed":
                return _stale_claim_outcome(str(claim.get("token", task_id)), int(claim.get("generation", 0)), ["parallel member launch does not name a claimed member of the active group"])
            return None
        if not isinstance(group, Mapping) or group.get("state") != "active":
            return _stale_claim_outcome(str(claim.get("token", task_id)), int(claim.get("generation", 0)), ["member claim references an unknown or closed batch group"])
        if group.get("anchor") != task_id or group.get("anchor_session") is not None or current_claim.get("state") != "claimed":
            return _stale_claim_outcome(str(claim.get("token", task_id)), int(claim.get("generation", 0)), ["later batch members resume the anchor session; launch refused"])
        return None

    def _launch_claimed_task(self, claim: Mapping[str, Any], prompt: str, deadline_seconds: float | None) -> dict[str, Any]:
        task_id = str(claim.get("task_id") or "")
        current_claim = self.refresh_manifest().get("claims", {}).get(task_id)
        if not isinstance(current_claim, Mapping):
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim.get("token", "claim")), int(claim.get("generation", 0)), "preserve-and-reconcile")
        for field in ("token", "generation", "owner", "claim_owner_id", "launch_id"):
            if field in claim and claim.get(field) != current_claim.get(field):
                return _outcome("blocked", "owner-mismatch", ["stale handoff identity refused before adapter launch"], "repository-task", str(claim.get("token", "claim")), int(claim.get("generation", 0)), "preserve-and-reconcile")
        if not self._claim_owned_by_driver(current_claim):
            return _outcome("blocked", "owner-mismatch", ["claim is not owned by this run writer"], "repository-task", str(claim.get("token", "claim")), int(claim.get("generation", 0)), "preserve-and-reconcile")
        claim = current_claim
        task_id = str(claim["task_id"])
        group_kind = "none"
        if claim.get("group_id"):
            group_kind = self._claim_group_kind(load_manifest(self.manifest_path), claim)
            refusal = self._member_launch_refusal(claim, task_id)
            if refusal is not None:
                return refusal
        task = load_manifest(self.manifest_path)["tasks"][task_id]
        operation_kind = str(task.get("operation_kind", "repository-task"))
        # Member claims authorize their own canonical paths, never a
        # group-wide union.
        allowed_paths = claim.get("allowed_paths") or task.get("allowed_paths", task.get("files", ()))
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
        capacity = self._capacity_transition(claim=claim)
        if capacity.get("status") != "available":
            recovery_action = "resume-same-claim" if claim.get("state") == "waiting-capacity" else "preserve-and-reconcile"
            return _outcome("blocked", "capacity-unavailable", [str(capacity.get("reason", "capacity unavailable"))], "parent-continuation", f"{task_id}:launch", int(claim.get("generation", 0)), recovery_action, claim_token=(claim.get("token")))
        if group_kind == GROUP_KIND_BATCH:
            fencing = self._mark_group_launched(claim, task_id, authorization["policy_token"])
        else:
            fencing = self._mark_claim_launched(claim, task_id, authorization["policy_token"])
        if fencing is not None:
            return fencing
        claim = self.refresh_manifest().get("claims", {}).get(task_id, claim)
        policy_token = dict(authorization["policy_token"])
        if group_kind == GROUP_KIND_PARALLEL:
            manifest = load_manifest(self.manifest_path)
            members = set(str(item) for item in manifest.get("claim_groups", {}).get(claim.get("group_id"), {}).get("members", ()))
            policy_token["parallel_member_processes"] = [
                dict(worker.get("process_identity", {}))
                for worker in manifest.get("workers", {}).values()
                if isinstance(worker, Mapping) and worker.get("task_id") in members
                and worker.get("state") in {"active", "quarantined"}
                and isinstance(worker.get("process_identity"), Mapping)
                and worker.get("process_identity", {}).get("pid") is not None
            ]
        raw = self._invoke_adapter_launch(claim, task, prompt, deadline_seconds, policy_token)
        if raw.get("reason_code") == "malformed-result":
            # A malformed launch receipt refuses read-only: return before the
            # blocked-persist arm, so a self-inflicted malformed receipt never
            # latches the claim into a blocked state that only a lease expiry
            # or hand edit can undo; the corrected relaunch or resume proceeds
            # under the live claim token and generation.
            return raw
        if raw.get("status") != "success" and raw.get("reason_code") in {"runtime-policy-unavailable", "runtime-error", "timeout"}:
            return self._persist_blocked_claim(claim, raw, task_id)
        validated = self.validate_adapter_result(raw)
        lifecycle_event = "timeout" if validated.get("reason_code") in {"timeout", "cleanup-unverified"} else None
        if lifecycle_event is not None:
            lifecycle = self._apply_adapter_lifecycle(claim, task, validated, lifecycle_event, proof=lifecycle_event == "terminal")
            if isinstance(lifecycle, Mapping) and lifecycle.get("outcome") == "released":
                self._release_launch_reservation(claim)
        if validated.get("reason_code") == "malformed-result":
            # An envelope-shaped failure validated to malformed-result is the
            # same read-only refusal: return it without persisting.
            return validated
        if validated.get("status") == "success":
            # A reservation is released only after the adapter result has
            # passed the driver-owned identity and evidence checks.
            self._release_launch_reservation(claim)
        return self.record_worker_checkpoint(raw)

    def launch_next_task(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None, batch: bool = False) -> dict[str, Any]:
        if batch and self._live_group(self.refresh_manifest()) is not None:
            # An already-claimed live group is launched or resumed through
            # the member continuation path, never through a second claim.
            return self.continue_parent(prompt, deadline_seconds, batch=True)
        claim = self.claim_next_task(batch=batch)
        if not claim.get("claimed"):
            return claim
        live_claim = self.refresh_manifest().get("claims", {}).get(str(claim.get("task_id")))
        if not isinstance(live_claim, Mapping) or live_claim.get("token") != claim.get("token") or live_claim.get("generation") != claim.get("generation"):
            return _outcome("blocked", "owner-mismatch", ["claim changed before launch"], "repository-task", str(claim.get("token", "claim")), int(claim.get("generation", 0)), "preserve-and-reconcile")
        return self._launch_claimed_task(live_claim, prompt, deadline_seconds)

    def launch_member_task(self, task_id: str, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        """Launch one claimed member of a live parallel implement group.

        The parallel-group launch entry: after ``claim_parallel_group``
        claims every member, the orchestrator launches the members
        concurrently through this operation, one call per member. Each
        member is an ordinary launch (own authorized envelope, own launch
        record and baseline, own policy token and session); the group's
        only gates are that the group is still active and the target is a
        claimed member of it. A group that is not a live parallel group
        refuses: batch members launch through the group continuation, not
        this path.
        """

        manifest = self.refresh_manifest()
        claim = manifest.get("claims", {}).get(str(task_id))
        if not isinstance(claim, Mapping) or not self._claim_owned_by_driver(claim) or claim.get("state") not in {"claimed", "launched", "waiting-capacity"}:
            return _outcome("blocked", "stale-claim", [f"launch does not name an owned live claim: {task_id}"], "parent-continuation", f"{task_id}:launch", manifest.get("generation", 0), "preserve-and-reconcile")
        if self._claim_group_kind(manifest, claim) != GROUP_KIND_PARALLEL:
            return _outcome("blocked", "stale-claim", [f"launch does not name a parallel group member: {task_id}"], "parent-continuation", f"{task_id}:launch", manifest.get("generation", 0), "preserve-and-reconcile")
        group = manifest.get("claim_groups", {}).get(str(claim.get("group_id") or ""))
        if not isinstance(group, Mapping) or group.get("state") != "active" or str(task_id) not in [str(member) for member in (group.get("members") or ())]:
            return _stale_claim_outcome(str(claim.get("token", f"{task_id}:launch")), int(claim.get("generation", 0)), ["parallel member launch does not name the active group"])
        return self._launch_claimed_task(claim, prompt, deadline_seconds)

    def continue_parent(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None, batch: bool = False) -> dict[str, Any]:
        """Reload state, reconcile safely, and advance one defined step.

        ``batch`` opts the continuation into the claim-group protocol: a
        live group advances through its active member by resuming the anchor
        session with that member's own policy token, never through a generic
        next-claim. The no-flag call is the unchanged single-task
        continuation.
        """

        # Resume-path re-entry: a scheduled watcher stands down on this
        # (the peer fence).
        self._mark_peer_resumed()
        manifest = self.refresh_manifest()
        if manifest.get("workflow_state") == "aborted":
            return _abort_outcome("runtime:aborted", manifest.get("generation", 0), ["workflow was explicitly aborted"], action_scope="parent-continuation")
        if manifest.get("workflow_state") in {"terminal", "complete"}:
            return self.terminal_result() or self._result_error("terminal receipt disappeared")
        reconciliation_payload = self._interruption_reconciliation_payload(manifest, "continue")
        if reconciliation_payload is not None:
            if reconciliation_payload.get("missing_claim"):
                return _outcome("blocked", "stale-claim", ["interrupted task has no durable claim to reconcile"], "parent-continuation", f"{reconciliation_payload['task_id']}:reconcile-interruption", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            reconciled = self.reconcile_interruption(reconciliation_payload)
            if reconciled.get("status") != "success":
                return reconciled
            manifest = self.refresh_manifest()
        reconciliation = self.reconcile_startup()
        if reconciliation["status"] != "success":
            return reconciliation
        manifest = self.refresh_manifest()
        # A lease reclaim can rotate a successor claim while its prepared
        # handoff is still queued. Prepared proves adapter I/O has not begun;
        # close only that now-stale intent so it cannot dispatch the replaced
        # identity again.
        stale_prepared = False
        for intent in manifest.get("handoff_intents", {}).values():
            if not isinstance(intent, dict) or intent.get("state") != "prepared" or intent.get("launch_receipt") is not None:
                continue
            successor = intent.get("successor") or {}
            current = manifest.get("claims", {}).get(str(successor.get("task_id"))) or {}
            if current.get("state") == "replaced":
                self._transition_handoff(intent, "failed")
                intent["failure_reason"] = "successor claim was replaced before adapter launch"
                stale_prepared = True
        if stale_prepared:
            self._save(manifest)
        if manifest.get("workflow_state") in {"terminal", "complete"}:
            return self.terminal_result() or self._result_error("terminal receipt disappeared")
        if batch:
            group = self._live_group(manifest)
            if group is not None:
                return self._continue_group_member(manifest, group, prompt, deadline_seconds)
        existing_claim = next(
            (claim for claim in manifest["claims"].values() if claim.get("state") in {"claimed", "launched", "waiting-capacity"}),
            None,
        )
        if existing_claim:
            if not self._claim_owned_by_driver(existing_claim):
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
            # A parked claim reaches the same relaunch as a live one: the
            # launch fence relaunches it in place (the capacity resume), so
            # the parked state never routes to a second claim.
            result = self._launch_claimed_task(existing_claim, prompt, deadline_seconds)
            self.refresh_manifest()
            return result
        claim = self.claim_next_task(batch=batch)
        if not claim.get("claimed"):
            if all(self._task_complete(item) for item in manifest["tasks"].values()):
                return _outcome("blocked", "done-pending", ["terminal receipt evidence is required"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
            return claim
        result = self._launch_claimed_task(claim, prompt, deadline_seconds)
        self.refresh_manifest()
        return result

    def _continue_group_member(self, manifest: Mapping[str, Any], group: Mapping[str, Any], prompt: str, deadline_seconds: float | None) -> dict[str, Any]:
        """Advance a live group through its active member (reload-resolved).

        The active member and the anchor session are resolved from the
        group record reloaded from the manifest, never from in-memory state.
        With no anchor session yet, only the anchor's initial launch is
        legal; later members resume the anchor session, and a missing
        adapter fails closed naming the resolved member and session instead
        of relaunching.
        """

        active_id = group.get("active_member")
        task = manifest["tasks"].get(active_id) if isinstance(active_id, str) else None
        claim = manifest["claims"].get(active_id) if isinstance(active_id, str) else None
        if task is None or not isinstance(claim, Mapping):
            return self._result_error("live batch group has no active member claim")
        if task.get("status") in {"done-pending", "commit-pending"}:
            return _outcome(
                "blocked",
                "done-pending",
                [f"batch member {active_id} is awaiting the done handoff; relaunch refused"],
                "parent-continuation",
                f"{active_id}:done",
                int(claim.get("generation", 0)),
                "preserve-and-reconcile",
                active_member=active_id,
                group_id=group.get("group_id"),
            )
        if not self._claim_owned_by_driver(claim):
            return _outcome("blocked", "stale-claim", ["another owner holds the active batch member"], "parent-continuation", str(claim.get("token", "claim")), int(claim.get("generation", 0)), "preserve-and-reconcile")
        if claim.get("state") not in {"claimed", "launched", "blocked"}:
            return _stale_claim_outcome(str(claim.get("token", active_id)), int(claim.get("generation", 0)), ["active batch member claim is not live"])
        if claim.get("state") == "blocked" and task.get("resume_allowed") is not True:
            # resume_allowed conjunct on the session branch: a
            # blocked member whose receipt forbids continuation (a foreign-
            # path contract violation) is refused on both group recovery
            # entries exactly like resume() hard-filters it; resuming it
            # here would give the caught scope violator a second turn that
            # launders the violation into an acceptance.
            return _stale_claim_outcome(str(claim.get("token", active_id)), int(claim.get("generation", 0)), ["blocked batch member receipt is not resumable; continuation refused"])
        session_id = self._member_session(manifest, task, claim, anchor_first=False)
        if session_id:
            if self.adapter is None:
                return _outcome(
                    "blocked",
                    "runtime-policy-unavailable",
                    [
                        "no adapter configured for the batch member resume",
                        f"active_member={active_id}",
                        f"anchor_session={session_id}",
                    ],
                    "parent-continuation",
                    str(claim.get("token", active_id)),
                    int(claim.get("generation", 0)),
                    "preserve-and-reconcile",
                    active_member=active_id,
                    anchor_session=str(session_id),
                    group_id=group.get("group_id"),
                )
            return self._resume_member_window(dict(task, session_id=str(session_id)), dict(claim), prompt, deadline_seconds)
        # No anchor session yet: only the anchor's initial launch is legal.
        # A session-less blocked member (a launch-window timeout, launch
        # exception, or activation failure before the first receipt)
        # recovers through the same initial-launch branch with a rotated
        # member identity instead of wedging the group on a permanent
        # stale-claim loop: there is no session to resume, the dead
        # attempt's identity is rotated away (late receipts fence as
        # stale), and the relaunch re-fences through the standard launch
        # path (_member_launch_refusal then _mark_group_launched). The
        # single-task path already recovers this exact shape by recycling
        # the claim; the group path now matches it. A non-resumable
        # blocked receipt (contract violation) never relaunches.
        if group.get("anchor") == active_id and group.get("anchor_session") is None and not task.get("session_id"):
            if claim.get("state") == "claimed":
                result = self._launch_claimed_task(claim, prompt, deadline_seconds)
                self.refresh_manifest()
                return result
            if self._sessionless_member_recycle_shape(group, task, claim, active_id):
                released = self._release_blocked_member_for_launch(claim, active_id)
                if released is not None:
                    return released
                fresh_claim = load_manifest(self.manifest_path)["claims"][active_id]
                result = self._launch_claimed_task(fresh_claim, prompt, deadline_seconds)
                self.refresh_manifest()
                return result
        return _stale_claim_outcome(str(claim.get("token", active_id)), int(claim.get("generation", 0)), ["batch group has no anchor session to resume"])

    @staticmethod
    def _sessionless_member_recycle_shape(group: Mapping[str, Any], task: Mapping[str, Any], claim: Mapping[str, Any], task_id: str) -> bool:
        """The wedge shape shared by both group recovery entries.

        A live group's ANCHOR member is blocked with no session anywhere
        (no task session, no anchor session) and its receipt permits
        continuation: nothing exists to resume, so both entries (``resume``
        selection and the batch continuation) recycle the member into a
        fresh launch through a rotated identity instead of wedging the
        group on a permanent stale-claim loop. One spelling lives here; a
        non-resumable blocked receipt (contract violation) never matches.
        """

        return (
            isinstance(group, Mapping)
            and group.get("state") == "active"
            and group.get("anchor") == task_id
            and group.get("anchor_session") is None
            and not task.get("session_id")
            and claim.get("state") == "blocked"
            and task.get("resume_allowed") is not False
        )

    @_locked_mutation
    def _release_blocked_member_for_launch(self, claim: Mapping[str, Any], task_id: str) -> dict[str, Any] | None:
        """Recycle a session-less blocked member for a fresh launch.

        The launch window timed out, the launch raised, or activation
        failed before the worker produced a receipt, so the claim is
        blocked with no session anywhere (no task session, no group anchor
        session): nothing exists to resume. Under the manifest lock the
        helper re-verifies the exact wedge shape and rotates the member
        identity through :meth:`_rotate_member_identity_locked` (fresh
        token and bumped attempt, so any late receipt from the dead
        attempt fences as owner-mismatch), then persists. Every other
        shape refuses without mutation.
        """

        manifest = load_manifest(self.manifest_path)
        group = manifest.get("claim_groups", {}).get(str(claim.get("group_id") or ""))
        if (
            not isinstance(group, Mapping)
            or group.get("state") != "active"
            or group.get("anchor") != task_id
            or group.get("anchor_session") is not None
            or self._rotate_member_identity_locked(manifest, task_id, claim) is None
        ):
            return _stale_claim_outcome(str(claim.get("token", task_id)), int(claim.get("generation", 0)), ["batch member changed before the blocked-launch release"])
        self._save(manifest)
        return None

    @staticmethod
    def _rotate_member_identity_locked(manifest: dict[str, Any], task_id: str, claim: Mapping[str, Any]) -> int | None:
        """Rotate a session-less blocked member's identity for relaunch.

        Callers hold the manifest lock and have verified the wedge shape
        (live group, anchor member, no anchor session, resumable blocked
        receipt). Mutates the passed manifest in place: fresh claim token
        and a bumped member attempt (fencing late receipts from the dead
        attempt), and the task's blocked-receipt fields stripped. The
        generation is deliberately unchanged: the group's ONE launch
        record is generation-keyed and the member drift fence compares
        against it. Returns the new attempt, or None on any residual
        mismatch, in which case nothing mutated.
        """

        current = manifest["claims"].get(task_id)
        if (
            not current
            or current.get("token") != claim.get("token")
            or current.get("generation") != claim.get("generation")
            or current.get("state") != "blocked"
        ):
            return None
        task = manifest["tasks"].get(task_id)
        if task is None or task.get("session_id") or task.get("resume_allowed") is False:
            return None
        # Token and attempt rotate; the generation deliberately does not:
        # the group's ONE launch record is generation-keyed (the member
        # drift fence compares the claim generation against it), and the
        # fresh token alone fences any late receipt from the dead attempt
        # as owner-mismatch. _mark_group_launched re-arms the group's
        # attempt record with the bumped attempt at the relaunch.
        manifest["claims"][task_id] = {
            **claim,
            "token": uuid.uuid4().hex,
            "state": "claimed",
            "attempt": int(claim.get("attempt") or 1) + 1,
        }
        for field in ("session_id", "resume_allowed", "blocked_receipt"):
            task.pop(field, None)
        manifest.setdefault("history", []).append({
            "event": "blocked-member-released-for-launch",
            "task_id": task_id,
            "attempt": manifest["claims"][task_id]["attempt"],
        })
        return manifest["claims"][task_id]["attempt"]

    def resume(self, prompt: str = "continue execute-plan", deadline_seconds: float | None = None) -> dict[str, Any]:
        """Resume only blocked tasks whose receipt permits continuation.

        Mirrors the launch pattern: the state selection and fence checks run
        under the manifest lock, the adapter resume call runs with the lock
        released, and the lock is re-acquired afterwards with the manifest
        re-read and checked for drift before any nested checkpoint write.
        """

        # Resume-path re-entry: a scheduled watcher stands down on this
        # (the peer fence).
        self._mark_peer_resumed()
        snapshot = self.refresh_manifest()
        reconciliation_payload = self._interruption_reconciliation_payload(snapshot, "resume")
        if reconciliation_payload is not None:
            if reconciliation_payload.get("missing_claim"):
                return _outcome("blocked", "stale-claim", ["interrupted task has no durable claim to reconcile"], "parent-continuation", f"{reconciliation_payload['task_id']}:reconcile-interruption", snapshot.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            reconciled = self.reconcile_interruption(reconciliation_payload)
            if reconciled.get("status") != "success":
                return reconciled
            return self.continue_parent(prompt, deadline_seconds)
        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "runtime:resume", action_scope="parent-continuation")
            selection = self._resume_select_locked()
        if isinstance(selection, _AdapterWindow):
            task, claim = selection.task, selection.claim
            return self._resume_member_window(task, claim, prompt, deadline_seconds)
        if isinstance(selection, _ContinueParent):
            return self.continue_parent(prompt, deadline_seconds)
        return selection

    def _resume_member_window(self, task: Mapping[str, Any], claim: Mapping[str, Any], prompt: str, deadline_seconds: float | None, retry_policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Run one adapter resume outside the lock, then re-fence and checkpoint.

        Shared by the blocked-task resume path and the batch member
        continuation: the adapter call runs with the manifest lock released,
        the lock is re-acquired afterwards with the manifest re-read and
        checked for drift before any nested checkpoint write. A member retry
        window passes the driver-owned decremented ``retry_policy``
        the resumed receipt is forced to, mirroring the plain relaunch arm's
        budget override.
        """

        # Recheck the selected claim before consulting inventory so a stale
        # selection keeps precedence over the capacity outcome.
        with _manifest_lock(self.manifest_path, self.owner) as preflight_acquired:
            if not preflight_acquired:
                return _mutation_unavailable(self, f"{task['id']}:resume", action_scope="parent-continuation")
            preflight = load_manifest(self.manifest_path)
            current = preflight.get("claims", {}).get(task["id"])
            drift = self._claim_drift_outcome(preflight, current, "parent-continuation", f"{task['id']}:resume")
            if drift is not None:
                return drift
        capacity = self._capacity_transition(claim=claim)
        if capacity.get("status") != "available":
            return _outcome(
                "blocked", "capacity-unavailable", [str(capacity.get("reason", "capacity unavailable"))],
                "parent-continuation", f"{task['id']}:resume", int(claim["generation"]),
                "resume-same-claim", claim_token=claim["token"],
            )
        # Adapter I/O runs outside the manifest flock.
        try:
            raw = self.adapter.resume(task["session_id"], prompt, claim["generation"], task_id=task["id"], deadline_seconds=deadline_seconds, policy_token=claim.get("policy_token"))
        except Exception as exc:
            raw = _outcome("error", "runtime-error", [type(exc).__name__], "repository-task", f"{task['id']}:resume", claim["generation"], "preserve-and-reconcile")
        if isinstance(raw, Mapping):
            raw = dict(raw)
            raw["claim_token"] = claim["token"]
            if retry_policy is not None:
                raw["retry_policy"] = dict(retry_policy)
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
            # A malformed resume receipt refuses read-only: the seeded
            # receipt-permitting claim keeps its durable state instead of
            # being latched non-resumable, so the corrected re-submission
            # still resumes it under the same token and generation.
            return validated
        return self.record_worker_checkpoint(raw)

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
        task = sorted(resumable, key=_pending_sort_key)[0]
        claim = manifest["claims"].get(task["id"])
        if not isinstance(claim, Mapping):
            return _outcome("blocked", "owner-mismatch", ["blocked task has no claim"], "parent-continuation", f"{task['id']}:resume", manifest.get("generation", 0), "preserve-and-reconcile")
        if not self._claim_owned_by_driver(claim) or claim.get("state") != "blocked":
            return _outcome("blocked", "owner-mismatch", ["resume claim is not owned and blocked"], "parent-continuation", str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), "preserve-and-reconcile")
        if not isinstance(claim.get("policy_token"), Mapping) or claim["policy_token"].get("generation") != claim.get("generation"):
            return _outcome("blocked", "runtime-policy-unavailable", ["resume policy token is missing or stale"], "parent-continuation", str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), "preserve-and-reconcile")
        session_id = task.get("session_id")
        if claim.get("group_id") and self._claim_group_kind(manifest, claim) == GROUP_KIND_PARALLEL:
            # A parallel member resumes on its OWN session (concurrent
            # members share no anchor session and there is no active-member
            # gate to satisfy). With no session anywhere the member takes
            # the standard single-task release: its identity rotates and its
            # task re-enters the queue once the group closes (the replaced
            # claim is terminal for the group's close rule).
            group = manifest.get("claim_groups", {}).get(claim["group_id"])
            if not isinstance(group, Mapping) or group.get("state") != "active":
                return _stale_claim_outcome(str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), ["resume does not name a live parallel group member"])
            if not session_id:
                self._reset_task_to_pending(task)
                claim["state"] = "replaced"
                manifest.setdefault("history", []).append({
                    "event": "parallel-member-released",
                    "group_id": claim["group_id"],
                    "member": task["id"],
                    "reason": "resume has no member session",
                })
                # The release is a terminal member transition, so it runs the
                # one terminal-membership close predicate (shared with the
                # advance close and the per-member reclaim exit). Without it
                # a released last live member left the group active with zero
                # live members: every later claim refused forever ("another
                # task is already claimed") and reclaim cannot touch a
                # replaced claim - the wedge.
                self._close_parallel_group_when_terminal_locked(manifest, claim["group_id"], task["id"], group)
                self._save(manifest)
                return _ContinueParent()
        elif claim.get("group_id"):
            # Resume selects only the live group's active member, through the
            # group's anchor session when the task carries no session of its
            # own; a member is never replaced onto the pending queue.
            group = manifest.get("claim_groups", {}).get(claim["group_id"])
            if not isinstance(group, Mapping) or group.get("state") != "active" or group.get("active_member") != task["id"]:
                return _stale_claim_outcome(str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), ["resume does not name the active batch member"])
            session_id = self._member_session(manifest, task, claim, anchor_first=False)
            if not session_id:
                # A session-less blocked anchor member (a launch-window
                # timeout, launch exception, or activation failure before the
                # first receipt) recycles into a fresh launch instead of
                # wedging the group forever: the identity rotation fences the
                # dead attempt, the returned continuation relaunches the
                # member through the standard launch fences, and later
                # members run. The wedge shape is the one shared predicate
                # also used by the batch continuation; non-resumable
                # receipts (contract violations) and non-anchor shapes keep
                # the refusal.
                if (
                    self._sessionless_member_recycle_shape(group, task, claim, task["id"])
                    and self._rotate_member_identity_locked(manifest, task["id"], claim) is not None
                ):
                    self._save(manifest)
                    return _ContinueParent()
                return _outcome("blocked", "stale-claim", ["batch member has no anchor session to resume"], "parent-continuation", str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), "preserve-and-reconcile")
        if self.adapter is not None and session_id and claim:
            return _AdapterWindow(task=dict(task, session_id=str(session_id)), claim=dict(claim))
        if claim.get("group_id"):
            return _stale_claim_outcome(str(claim.get("token", f"{task['id']}:resume")), int(claim.get("generation", manifest.get("generation", 0))), ["batch member resume requires a configured adapter"])
        self._reset_task_to_pending(task)
        claim["state"] = "replaced"
        manifest["history"].append({"event": "resume", "tasks": [task["id"] for task in resumable]})
        self._save(manifest)
        return _ContinueParent()

    @staticmethod
    def _reset_task_to_pending(task: Mapping[str, Any]) -> None:
        """Return a task to ``pending``, stripping dead-session resume fields.

        ``session_id``, ``resume_allowed``, and ``blocked_receipt`` describe
        the previous worker's session and receipt; once the task is claimable
        again they are stale inputs a later resume must never consume (a
        dead session id would route the next resume into a dead adapter
        session instead of a fresh claim). Shared by the reclaim release and
        the resume-path claim recycle, the two task-to-pending rotation
        sites.
        """

        task["status"] = "pending"
        for field in ("session_id", "resume_allowed", "blocked_receipt"):
            task.pop(field, None)

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
        # Claims are carried with their dictionary key, which is the
        # authoritative task identity for recovery.
        launch_evidence_claims = [
            (task_id, claim) for task_id, claim in manifest["claims"].items()
            if (
                claim.get("state") in {"claimed", "launched"}
                or self._claim_launch_evidence(manifest, claim) is not None
            ) and not self._claim_requeued_by_done_recovery(manifest, task_id, claim)
        ]
        examined = [
            (task_id, claim) for task_id, claim in launch_evidence_claims
            if claim.get("state") not in {"replaced", "waiting-capacity"}
            and manifest["tasks"].get(task_id, {}).get("status")
            not in {"done-pending", "checkpointed", "complete"}
            and not self._claim_owned_by_live_group(manifest, claim)
            and not self._claim_released_by_failed_group(manifest, claim)
        ]
        for task_id, claim in examined:
            task = manifest["tasks"].get(task_id, {})
            commit_identity = task.get("commit_identity")
            if commit_identity and task.get("done_log_evidence"):
                # A recorded none identity is a valid completion on its own:
                # the done flow proved the clean state before recording it,
                # so the recovery completes without any git lookup.
                if str(commit_identity).strip() == "none" or (commit_lookup and commit_lookup(commit_identity)):
                    return _ReconcileCommit(task_id, str(commit_identity), commit_lookup, claim.get("token"), claim.get("generation"))
            handoff_key = claim.get("handoff_intent_key")
            handoff = manifest.get("handoff_intents", {}).get(handoff_key) if handoff_key else None
            task_reservations = manifest.get("capacity", {}).get("reservations", {})
            task_workers = manifest.get("workers", {})
            if (
                claim.get("state") == "claimed"
                and task.get("status") == "claimed"
                and claim.get("owner") == self.owner
                and claim.get("launch_record") is None
                and not any(isinstance(item, Mapping) and item.get("task_id") == task_id for item in task_reservations.values())
                and not any(
                    isinstance(item, Mapping)
                    and item.get("task_id") == task_id
                    and item.get("state") != "terminal"
                    for item in task_workers.values()
                )
                and (not isinstance(handoff, Mapping) or handoff.get("state") == "failed")
            ):
                return _outcome("success", "prelaunch-claim-reconciled", ["owned claim is claimed but has no launch record, reservation, worker, or active handoff"], "parent-continuation", f"{task_id}:launch", claim.get("generation", manifest.get("generation", 0)), "continue-parent")
            if isinstance(handoff, Mapping) and claim.get("run_writer_id") == self.owner:
                if handoff.get("state") == "prepared":
                    return _outcome("success", "completed", [f"adopted prepared handoff intent={handoff.get('intent_id')}"], "parent-continuation", f"{task_id}:launch", claim.get("generation", manifest.get("generation", 0)), "continue-parent")
                if handoff.get("state") in {"launching", "launched", "ambiguous"}:
                    return _outcome("blocked", "ambiguous", [f"handoff intent {handoff.get('intent_id')} is {handoff.get('state')}; reconcile provider result before retry"], "parent-continuation", f"{task_id}:launch", claim.get("generation", manifest.get("generation", 0)), "preserve-and-reconcile", resume_allowed=False)
            if live_worker_owner and live_worker_owner == claim.get("owner"):
                return _outcome("blocked", "stale-claim", ["ambiguous live worker claim"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
            return _outcome("blocked", "owner-mismatch", ["claim owner or generation cannot be proven safe"], "repository-task", claim.get("token", "claim"), claim.get("generation", 0), "preserve-and-reconcile")
        return {"status": "success", "reason_code": "completed", "evidence": ["no ambiguous claims"], "actions": [], "generation": manifest.get("generation", 0)}

    @staticmethod
    def _claim_owned_by_live_group(manifest: Mapping[str, Any], claim: Mapping[str, Any]) -> bool:
        """True when the claim belongs to an active (live) claim group.

        The group protocol owns every member claim, not only the active
        member: startup reconciliation never quarantines any of
        them as an ambiguous live worker (the dirty-worktree gates above
        still fire through the launch-evidence list, discriminated by the
        group-resolved launch record), and the batch continuation resolves
        the active member through the anchor session.
        """

        group_id = (claim or {}).get("group_id")
        if not group_id:
            return False
        group = (manifest.get("claim_groups") or {}).get(group_id)
        return isinstance(group, Mapping) and group.get("state") == "active"

    @staticmethod
    def _claim_released_by_failed_group(manifest: Mapping[str, Any], claim: Mapping[str, Any]) -> bool:
        """True when the claim's group is terminally failed.

        A failed group owns no live work: its member claims were closed by
        the release itself (the reclaim-time release or the
        advance-time group failure), and late receipts fence as stale
        against those closed or rotated identities. Their launch evidence
        still resolves through the group record, so without this predicate
        startup reconciliation would quarantine every released member as an
        ambiguous live worker and wedge the run the release just freed -
        the release's whole point is that their tasks re-enter the queue as
        individual claims.
        """

        group_id = (claim or {}).get("group_id")
        if not group_id:
            return False
        group = (manifest.get("claim_groups") or {}).get(group_id)
        return isinstance(group, Mapping) and group.get("state") == "failed"

    @staticmethod
    def _claim_requeued_by_done_recovery(
        manifest: Mapping[str, Any], task_id: str, claim: Mapping[str, Any]
    ) -> bool:
        """Identify a closed historical claim retired by an exact requeue receipt.

        Its launch record remains useful audit evidence, but must not make
        startup reconciliation treat the newly pending task as still owned
        by that old launch generation.
        """

        if claim.get("state") != "closed":
            return False
        task = (manifest.get("tasks") or {}).get(task_id)
        if not isinstance(task, Mapping) or task.get("status") != "pending":
            return False
        return any(
            isinstance(event, Mapping)
            and event.get("event") == DONE_PENDING_RECOVERY_EVENT
            and event.get("task_id") == task_id
            and event.get("token") == str(claim.get("token"))
            and event.get("generation") == claim.get("generation")
            and event.get("disposition") == "requeue"
            for event in manifest.get("history", [])
        )

    @staticmethod
    def _claim_launch_evidence(manifest: Mapping[str, Any], claim: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """A claim's launch record, resolved through its group for members.

        Group member claims never carry launch records of their own:
        the ONE launch record lives on the group, so the ambient-dirt
        discriminator that classifies pre-launch versus launched claims must
        resolve member evidence through ``claim_groups[group_id]
        ['launch_record']`` or every launched member is misclassified as
        pre-launch. Single-task claims use their own record.
        """

        record = (claim or {}).get("launch_record")
        if isinstance(record, Mapping):
            return record
        group_id = (claim or {}).get("group_id")
        if group_id:
            group = (manifest.get("claim_groups") or {}).get(group_id)
            if isinstance(group, Mapping):
                record = group.get("launch_record")
                if isinstance(record, Mapping):
                    return record
        return None

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

    def _git_commit_ancestor_or_self(self, commit: str) -> bool:
        """True only when ``commit`` is proven ancestor-or-self of HEAD.

        The default witness behind the injectable ``commit_ancestry`` seam
        (``git merge-base --is-ancestor`` exits 0 for an ancestor including
        HEAD itself). Any other exit code is a witness failure, not a
        negative answer, and fails closed to False.
        """

        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", str(commit)):
            return False
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", str(commit), "HEAD"],
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
        return self._is_ambient_noise_path(path)

    def _is_ambient_noise_path(self, path: str) -> bool:
        """True when a path's file name matches the ambient allowlist shape."""

        name = PurePosixPath(path).name
        return any(fnmatch.fnmatchcase(name, pattern) for pattern in AMBIENT_NOISE_PATTERNS)

    def _git_worktree_dirty(self) -> bool:
        return bool(self._git_worktree_entries())

    def _entry_is_tolerated_checkbox_flip(self, path: str, code: str) -> bool:
        """True for the one tolerated dirty entry: the sanctioned flip shape.

        A tracked Markdown file whose working-tree diff over HEAD is
        checkbox-marker-only with paired-line identity (the Step 1.3
        plan-file checkbox flip). Untracked entries, non-Markdown files,
        repository-escaping paths, and any witness failure refuse (fail
        closed): the tolerance is an allowance for the riding plan flip,
        never a laundering channel for content changes.
        """

        if not path or code == "??":
            # Untracked entries carry no tracked diff to prove anything
            # about; an empty diff must never read as a tolerated flip.
            return False
        if PurePosixPath(path).suffix.lower() != ".md":
            return False
        if self._path_escapes_repo(path):
            return False
        try:
            completed = subprocess.run(
                ["git", "-c", "core.quotePath=false", "diff", "HEAD", "--", path],
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
        except (OSError, RuntimeError, UnicodeDecodeError):
            return False
        if completed.returncode != 0:
            return False
        return _diff_is_checkbox_marker_only(completed.stdout)

    def _classify_dirty_entries(
        self,
        allowed_paths: Iterable[str],
        exempt_paths: Iterable[str] = frozenset(),
        entries: list[tuple[str, str]] | None = None,
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]] | None:
        """Partition worktree entries into (refused, tolerated) for one scope.

        The one dirty-entry classifier every dirty-tree consumer shares (the
        done boundary's none arm and real-identity clean tail, the checkpoint
        scope witness, and the startup reconciliation dirty gate): a dirty
        entry inside ``allowed_paths`` refuses; a tracked Markdown entry
        outside them is tolerated only when its working-tree diff is
        checkbox-marker-only with paired-line identity; every other dirty
        entry refuses. ``exempt_paths`` (a parallel member's siblings) are
        in-flight by contract and are neither refused nor tolerated. Callers
        that already hold an enumeration pass it as ``entries`` so the gate
        never takes a second witness snapshot; otherwise the worktree is
        enumerated here. Returns None when the git witness fails so every
        caller fails closed.
        """

        if entries is None:
            try:
                entries = self._git_worktree_entries()
            except (OSError, RuntimeError):
                return None
        allowed = set(allowed_paths)
        exempt = set(exempt_paths)
        refused: list[tuple[str, str]] = []
        tolerated: list[tuple[str, str]] = []
        for code, path in entries:
            if not path or path in exempt:
                continue
            if path in allowed or not self._entry_is_tolerated_checkbox_flip(path, code):
                refused.append((code, path))
            else:
                tolerated.append((code, path))
        return refused, tolerated

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
        try:
            entries = self._git_worktree_entries()
        except RuntimeError:
            return None
        for _code, path in entries:
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

    def _git_commits_share_history(self, first: str, second: str) -> tuple[bool, bool]:
        """Return whether two commits have a merge base and whether Git proved it."""

        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "merge-base", first, second],
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

    def _git_commit_own_paths(self, commit: str) -> list[str] | None:
        """The done commit's own change set (first-parent diff).

        The parallel-member done-boundary measure: per-member done runs after
        all members land, so the member's commit sits on top of its siblings'
        commits and the baseline-cumulative diff would count the siblings'
        committed files as this member's scope escape. A root-commit target
        (no first parent) fails the witness (None, fail closed).
        """

        completed = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"{commit}^", commit],
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
        group_id = (claim or {}).get("group_id")
        if group_id and self._claim_group_kind(manifest, claim) == GROUP_KIND_BATCH:
            # Batch member claims drift against the group's single launch
            # record and their own attempt baseline; they never carry launch
            # records of their own. Parallel members are ordinary launches:
            # they fall through to their own launch-record snapshot below.
            group = manifest.get("claim_groups", {}).get(group_id)
            record = group.get("launch_record") if isinstance(group, Mapping) else None
            if not isinstance(record, Mapping):
                return _outcome(
                    "blocked",
                    "stale-claim",
                    ["member claim has no group launch record"],
                    action_scope,
                    checkpoint_identity,
                    manifest.get("generation", 0),
                    "preserve-and-reconcile",
                )
            attempt_record = (group.get("member_attempts") or {}).get(task_id) or {}
            member_drifted = (
                (claim or {}).get("generation") != record.get("generation")
                or str((claim or {}).get("baseline_revision") or "") != str(attempt_record.get("baseline_revision", (claim or {}).get("baseline_revision") or ""))
            )
            if member_drifted:
                return _outcome(
                    "blocked",
                    "stale-claim",
                    ["member baseline or generation no longer matches the group launch identity"],
                    action_scope,
                    checkpoint_identity,
                    manifest.get("generation", 0),
                    "preserve-and-reconcile",
                )
            return None
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

    def _worktree_scope_violation(self, claim: Mapping[str, Any], sibling_paths: frozenset[str] = frozenset()) -> tuple[str, list[str]]:
        """Enforce the claim's allowed-path boundary with a git witness.

        Returns ``(verdict, paths)`` where verdict is ``ok``, ``violation``,
        ``cleanup``, or ``unavailable``. A claim without a recorded baseline
        revision (for example a seeded test claim) has no witness and stays
        ``ok``; a recorded baseline with an empty scope, or a broken witness,
        fails closed. When every out-of-scope path is porcelain-proven
        untracked AND ambient-shaped (the ``AMBIENT_NOISE_PATTERNS``
        allowlist, tightened by the later review), the verdict is the resumable
        ``cleanup`` envelope instead of the terminal ``violation`` that
        would hard-wedge the task on host-generated untracked noise; any
        tracked out-of-scope modification, even one wearing an ambient
        name, keeps the hard block. The one exception is the tolerated
        dirty-entry shape from the shared classifier: a tracked Markdown
        out-of-scope path whose working-tree diff is checkbox-marker-only
        with paired-line identity (the Step 1.3 plan-file flip riding
        uncommitted after a none completion) is not ``unexpected``, so the
        next task's checkpoint after a none completion never persists a
        non-resumable ``contract-violation``.

        ``sibling_paths`` is the parallel-group carve-out: the claimed files
        of this member's concurrently running siblings (see
        ``_parallel_sibling_paths``) are subtracted before judging, so a
        sibling's in-flight work never reads as this member's scope escape.
        Every path outside the member's scope AND the sibling set keeps the
        full witness force, including the on-disk escape probe.
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
        unexpected = [
            path
            for path in changed
            if path not in sibling_paths and (path not in allowed or self._path_escapes_repo(path))
        ]
        if unexpected:
            if self._ambient_untracked_witness(unexpected):
                return "cleanup", unexpected
            # The tolerated-entry carve-out runs after the ambient arm: an
            # untracked entry can never satisfy the flip shape (no tracked
            # diff), so the two allowances never overlap. A classifier
            # witness failure keeps the hard block (fail closed).
            try:
                classified = self._classify_dirty_entries(allowed, exempt_paths=sibling_paths)
            except (OSError, RuntimeError, UnicodeDecodeError):
                classified = None
            if classified is not None:
                tolerated_paths = {path for _code, path in classified[1]}
                unexpected = [path for path in unexpected if path not in tolerated_paths]
                if not unexpected:
                    return "ok", []
            return "violation", unexpected
        return "ok", []

    def _ambient_untracked_witness(self, paths: Sequence[str]) -> bool:
        """True when every path is proven untracked-and-ambient by porcelain.

        The post-launch ambient downgrade needs the untracked arm,
        not just the name shape. A tracked out-of-scope modification can
        wear an ambient name (``.DS_Store``), and the name check alone
        would downgrade an arbitrary content escape to a resumable
        cleanup; the porcelain witness (``??`` status, same discriminator
        as the pre-launch startup path) must prove every path untracked.
        Any witness failure, quoted or malformed rendering, escaping path,
        or tracked status keeps the hard block.
        """

        try:
            entries = self._git_worktree_entries()
        except (OSError, RuntimeError):
            return False
        statuses: dict[str, str] = {}
        for code, path in entries:
            if path:
                statuses.setdefault(path, code)
        return all(self._is_ambient_noise_entry(statuses.get(path, ""), path) for path in paths)

    @_locked_mutation
    def abort(self, task_id: str, token: str) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        claim = manifest["claims"].get(task_id)
        if not claim or claim.get("token") != token or not self._claim_owned_by_driver(claim):
            return _outcome("blocked", "owner-mismatch", ["abort receipt does not match claim owner"], "repository-task", token, manifest.get("generation", 0), "preserve-and-reconcile")
        handoff_key = claim.get("handoff_intent_key")
        handoff = manifest.get("handoff_intents", {}).get(handoff_key) if handoff_key else None
        if isinstance(handoff, Mapping) and handoff.get("state") == "launching":
            return _outcome("blocked", "stale-claim", ["handoff adapter dispatch is in flight; abort was not recorded"], "repository-task", token, claim.get("generation", manifest.get("generation", 0)), "preserve-and-reconcile", resume_allowed=False)
        task = manifest["tasks"].get(task_id)
        # Wedge exception (r5-F2): a commit-pending claim whose recorded
        # commit provably does not exist is wedged; no receipt path can
        # reconcile it, so the explicit stop with the still-current token
        # is the only runtime exit. A missing or empty commit_identity on
        # a hand-corrupted task routes through the wedge path too: an
        # empty identity fails the commit lookup. A hand-corrupted closed
        # claim never routes through the wedge path: the closed state keeps
        # the r4 progression refusal (not wedged).
        wedged = False
        if task is not None and task.get("status") == "commit-pending" and claim.get("state") != "closed":
            try:
                wedged = not self.commit_lookup(str(task.get("commit_identity") or ""))
            except (OSError, RuntimeError):
                # Witness failure degrades to not-wedged: the refusal stands.
                pass
        if not wedged and _claim_progressed_past_receipt(task, claim):
            # An explicit abort must not regress a task that already reached
            # its receipt boundary (done-pending, commit-pending,
            # checkpointed, complete, aborted) or a closed claim: the
            # durable state stays untouched unless the claim is wedged (a
            # commit-pending task with a provably missing commit), where
            # the explicit stop is the only runtime exit.
            return _stale_claim_outcome(
                token,
                claim.get("generation", manifest.get("generation", 0)),
                ["claim already progressed past the abort receipt"],
            )
        if wedged:
            # TOCTOU guard (r3, guarantee wording corrected r4): the wedge
            # decision above was computed from the locked snapshot; a
            # competing writer may have landed the task's completion
            # between that decision and this save. Compare the snapshot
            # against a fresh load before persisting: all runtime writers
            # hold the manifest lock for their whole body, so the re-read
            # detects out-of-band manifest edits, but edits to fields
            # other than the task, the claim, and the workflow state are
            # not detected. When the comparison passes, the abort writes
            # rebase on the fresh object so the persisted state is built
            # from what was just re-verified, never the stale snapshot.
            fresh = load_manifest(self.manifest_path)
            if (
                fresh["tasks"].get(task_id) != task
                or fresh["claims"].get(task_id) != claim
                or fresh.get("workflow_state") != manifest.get("workflow_state")
            ):
                return _outcome("blocked", "stale-claim", ["manifest changed during abort; wedge decision stale"], "repository-task", token, manifest.get("generation", 0), "preserve-and-reconcile")
            fresh["tasks"][task_id]["status"] = "aborted"
            fresh["claims"][task_id]["state"] = "aborted"
            fresh["workflow_state"] = "aborted"
            self._save(fresh)
            return _abort_outcome(token, fresh["claims"][task_id].get("generation", 0), [f"task={task_id}"])
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
        if task is None or claim is None or not self._claim_owned_by_driver(claim) or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
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
        claim = manifest["claims"].get(task_id)
        if not claim or not self._claim_owned_by_driver(claim) or (claim_token is not None and claim.get("token") != claim_token) or (generation is not None and claim.get("generation") != generation):
            return _outcome("blocked", "owner-mismatch", ["commit recovery receipt does not match the live claim"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "preserve-and-reconcile"), False
        if manifest.get("workflow_state") == "aborted":
            # The same global fence the sibling receipt paths enforce: an
            # aborted workflow is never reconciled by a late commit receipt.
            # The fence sits above the duplicate short-circuit (mirroring the
            # success-checkpoint path's fence ordering) so a replayed
            # reconciliation cannot return the idempotent duplicate success
            # on an aborted workflow; the identity check still precedes it,
            # so a foreign claim keeps owner-mismatch.
            return _abort_outcome(f"{task_id}:commit", manifest.get("generation", 0), ["workflow was explicitly aborted before the commit reconciliation"], action_scope="done-handoff"), False
        if task.get("status") == "checkpointed" and task.get("commit_identity") == commit_identity:
            return _outcome("success", "completed", ["commit already reconciled"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[]), False
        if task.get("commit_identity") != commit_identity or not task.get("done_log_evidence"):
            return _outcome("blocked", "commit-pending", ["matching done-log evidence and commit identity are required"], "done-handoff", f"{task_id}:commit", claim.get("generation", manifest.get("generation", 0)), "preserve-and-reconcile"), False
        # The none identity never consults the lookup: the boundary witnesses
        # below (the none arm of the done boundary) prove the state instead.
        if str(commit_identity).strip() != "none" and not commit_lookup(commit_identity):
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
        # A reconciled member commit advances the group exactly as its done
        # handoff would; the mutation lands in this same locked save.
        resume_action, claim_next, advance_blocked = self._advance_group_locked(manifest, task_id, commit_identity, f"{task_id}:commit")
        if advance_blocked is not None:
            return advance_blocked, False
        handoff_intent = None
        if resume_action is None and claim_next:
            handoff_intent = self._prepare_handoff_locked(manifest, task_id, f"{task_id}:commit")
        self._save(manifest)
        if handoff_intent is not None:
            outcome = _outcome("success", "completed", [f"reconciled commit={commit_identity}", f"handoff_intent={handoff_intent['intent_id']}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[dict(handoff_intent["outcome_action"])])
            return outcome, False
        return _outcome("success", "completed", [f"reconciled commit={commit_identity}"], "done-handoff", f"{task_id}:commit", manifest.get("generation", 0), "continue-parent", actions=[resume_action] if resume_action else []), claim_next

    def parent_continuation_available(self) -> bool:
        return self.profile.get("capabilities", {}).get("parent_continuation", "unsupported") != "unsupported"

    @_locked_mutation
    def mark_terminal(
        self,
        archived_plan_path: str = "",
        last_commit_sha: str = "",
        phase5_checklist: list[str] | None = None,
        stage: str = "final",
        plan_path: str = "",
        destination: str = "",
        review_sidecar: str = "",
        residual_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Dispatch the staged terminal operation; each stage owns its checks.

        ``stage`` selects the stage and defaults to ``final``, which preserves
        today's input contract unchanged (the archived plan path, commit
        identity, and Phase 5 checklist). ``pre-archive`` carries the active
        ``plan_path``, an optional candidate ``destination``, the
        ``review_sidecar`` path, ``last_commit_sha``, the
        ``phase5_checklist``, and an optional structured ``residual_policy``
        (finding ids, grant source, recorded-at epoch), evaluates the
        fixed-order eligibility predicate (``_pre_archive_gate``), and on
        success records the ``archive_gate`` receipt without touching
        ``workflow_state`` or writing a ``terminal_receipt``. The final-stage
        checks live in ``_final_terminal_stage``, keeping this operation a
        small dispatcher. An unknown stage refuses as blocked ``done-pending``.
        Each stage refusal composes its blocked outcome first and then appends
        one ``terminal-refused`` evidence event to the append-only history (the
        append never changes the outcome); the unknown-stage dispatch refusal
        writes no event because no stage ran to refuse.
        """

        manifest = load_manifest(self.manifest_path)
        if stage == "pre-archive":
            return self._pre_archive_gate(
                manifest,
                plan_path=plan_path,
                destination=destination,
                review_sidecar=review_sidecar,
                last_commit_sha=last_commit_sha,
                phase5_checklist=phase5_checklist,
                residual_policy=residual_policy,
            )
        if stage != "final":
            return _outcome("blocked", "done-pending", [f"unsupported terminal stage: {stage}"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
        return self._final_terminal_stage(manifest, archived_plan_path=archived_plan_path, last_commit_sha=last_commit_sha, phase5_checklist=phase5_checklist)

    def _terminal_refusal_tail(self, manifest: dict[str, Any], stage: str, evidence: list[str]) -> dict[str, Any]:
        """Compose the stage refusal, then append its terminal-refused event.

        The blocked outcome is composed FIRST and the history append never
        changes it: this is the one evidence write allowed after a refusal,
        and it is ordered strictly after the outcome exists. The caller
        already holds the manifest lock (the terminal operation is a locked
        mutation), and history stays append-only: the event records the
        refusal, it never rewrites one. This event is the history producer
        the diagnose operation's terminal-gate class keys on.
        """

        outcome = _outcome("blocked", "done-pending", evidence, "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "preserve-and-reconcile")
        manifest.setdefault("history", []).append(
            {
                "event": "terminal-refused",
                "stage": stage,
                "evidence": bounded_evidence(list(outcome["evidence"])),
            }
        )
        self._save(manifest)
        return outcome

    def _final_terminal_stage(
        self,
        manifest: dict[str, Any],
        archived_plan_path: str = "",
        last_commit_sha: str = "",
        phase5_checklist: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record the terminal receipt only after the machine terminal predicate.

        The final stage is the second half of the staged terminal protocol:
        it first requires the pre-archive gate receipt, then runs the
        archived-plan checks in a fixed order. The order is:

        (1) machine completeness (a non-empty task map, every task complete
        through the existing completeness helper), which precedes every gate
        clause so an incomplete run is never refused on gate evidence; (2)
        the gate clauses: the ``archive_gate`` receipt must be present (the
        pre-archive stage wrote it before the move), the supplied archived
        path must equal ``archive_gate.declared_destination`` exactly, and
        the gate-recorded source plan path (``archive_gate.plan_path``) must
        be absent from the filesystem; (3) today's archived-plan checks in
        order: the shape guard, the fail-closed bounded read (the shared
        ``_read_plan_bounded`` policy; see that helper's docstring), the
        digest recompute over the archived bytes
        against ``archive_gate.plan_digest``, the empty-plan refusal (an
        empty or whitespace-only plan makes the unchecked-checkbox
        predicate vacuously true), the at-least-one-task-heading
        requirement (a plan with zero recognizable '### Task <N>:' headings
        mirrors the readiness plan-shape guard and proves the wrong file
        was archived), zero line-anchored unchecked
        checkboxes over the whole file, and ``commit_lookup`` proving the
        supplied commit identity. The terminal receipt gains ``plan_digest``
        from the gate record only after the digest equality held. Any miss
        returns the retriable ``done-pending`` block with evidence naming
        the failed check; the refusal composes first and then appends one
        ``terminal-refused`` history evidence event (the append never
        changes the outcome), and apart from that append-only event the
        manifest stays untouched (non-terminal).
        """

        if not manifest["tasks"]:
            return self._terminal_refusal_tail(manifest, "final", ["manifest carries no tasks"])
        if not all(self._task_complete(task) for task in manifest["tasks"].values()):
            return self._terminal_refusal_tail(manifest, "final", ["all tasks must be complete before terminal state"])
        # (2) The pre-archive gate receipt is the prerequisite of the final
        # stage: no archive without the pre-move eligibility proof, the
        # archived plan exactly at the declared destination, the source gone,
        # and the archived bytes still hashing to the recorded digest.
        gate = manifest.get("archive_gate")
        if not isinstance(gate, Mapping):
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [
                    "pre-archive gate receipt is required before the final terminal stage",
                    "no archive_gate record is present; run the terminal pre-archive stage before the move",
                ],
            )
        declared_destination = gate.get("declared_destination")
        supplied_path = archived_plan_path.strip() if isinstance(archived_plan_path, str) else archived_plan_path
        if not isinstance(declared_destination, str) or not declared_destination or supplied_path != declared_destination:
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"archived plan path {archived_plan_path!r} does not equal the archive gate declared_destination {declared_destination!r}; the move must land exactly at the declared destination"],
            )
        recorded_source = gate.get("plan_path")
        if not isinstance(recorded_source, str) or not recorded_source.strip():
            return self._terminal_refusal_tail(
                manifest,
                "final",
                ["archive gate receipt does not record a source plan path"],
            )
        try:
            source_relative = _safe_relative_path(self.repo_root, recorded_source.strip())
        except ValueError:
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"archive gate receipt records an unsafe source plan path: {recorded_source.strip()}"],
            )
        if (self.repo_root / source_relative).exists():
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"gate-recorded source plan path {recorded_source.strip()} is still present; the archive move did not happen"],
            )
        if (
            not isinstance(archived_plan_path, str)
            or not archived_plan_path.strip()
            or not isinstance(last_commit_sha, str)
            or not re.fullmatch(r"[0-9a-fA-F]{7,64}", last_commit_sha.strip())
            or not isinstance(phase5_checklist, list)
            or not phase5_checklist
            or not all(isinstance(item, str) and item.strip() for item in phase5_checklist)
        ):
            return self._terminal_refusal_tail(manifest, "final", ["archived plan, commit identity, and Phase 5 checklist are required"])
        plan_text, plan_error = _read_plan_bounded(self.repo_root, archived_plan_path.strip(), require_safe_path=True)
        if plan_error is not None:
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"archived plan {plan_error}"],
            )
        # The archived bytes must still hash to the gate's recorded digest:
        # the recompute runs through the same bounded byte policy over the
        # exact path the bounded read just proved, and only equality lets
        # the receipt carry the gate digest.
        try:
            archived_relative = _safe_relative_path(self.repo_root, archived_plan_path.strip())
            archived_digest, digest_error = _sha256_capped(self.repo_root / archived_relative)
        except ValueError:
            archived_digest, digest_error = None, "is not a safe repository-relative path under the repository root"
        if digest_error is not None:
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"archived plan digest mismatch: the archived bytes could not be re-hashed ({digest_error})"],
            )
        if archived_digest != gate.get("plan_digest"):
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [f"archived plan digest mismatch: recomputed sha256 {archived_digest} does not equal the gate receipt plan_digest {gate.get('plan_digest')}"],
            )
        if not plan_text:
            # An empty plan (the helper already stripped whitespace-only
            # bytes) makes the unchecked-checkbox predicate vacuously true:
            # refuse the empty artifact instead of letting it pass the
            # terminal gate.
            return self._terminal_refusal_tail(
                manifest,
                "final",
                ["archived plan is empty"],
            )
        plan_lines = plan_text.splitlines()
        if not any(_TASK_SECTION_HEADING.match(line) for line in plan_lines):
            # At-least-one-task-heading requirement, mirroring the readiness
            # plan-shape guard: a non-empty plan with zero recognizable
            # '### Task <N>:' headings makes every per-section scan vacuous
            # and proves the wrong file was archived, so the terminal gate
            # refuses it instead of accepting a sectionless artifact.
            return self._terminal_refusal_tail(
                manifest,
                "final",
                ["archived plan carries no recognizable task sections"],
            )
        unchecked = _unchecked_checkbox_pairs(plan_lines)
        if unchecked:
            # The evidence line number comes from the scan helper, never
            # from re-searching the line text: a duplicated line would make
            # a text search ambiguous.
            first_number, first = unchecked[0]
            return self._terminal_refusal_tail(
                manifest,
                "final",
                [
                    f"archived plan still has {len(unchecked)} unchecked checkbox line(s)",
                    f"line {first_number}: {first.strip()}",
                ],
            )
        if not self.commit_lookup(last_commit_sha.strip()):
            return self._terminal_refusal_tail(manifest, "final", [f"commit identity is not provable: {last_commit_sha.strip()}"])
        manifest["workflow_state"] = "complete"
        manifest["terminal_receipt"] = {
            "workflow_state": "complete",
            "phase5_checklist": list(phase5_checklist),
            "archived_plan_path": archived_plan_path,
            "last_commit_sha": last_commit_sha,
            # The gate digest is copied only here, after the recompute above
            # proved the archived bytes still hash to it.
            "plan_digest": gate.get("plan_digest"),
        }
        self._save(manifest)
        return _outcome("success", "completed", ["validated complete manifest"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "continue-parent")

    def _pre_archive_gate(
        self,
        manifest: dict[str, Any],
        plan_path: str = "",
        destination: str = "",
        review_sidecar: str = "",
        last_commit_sha: str = "",
        phase5_checklist: list[str] | None = None,
        residual_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate the pre-archive eligibility predicate in one fixed order.

        The predicate owns the archive origin's gate-before-move ordering and
        returns exactly the FIRST failed condition as a blocked
        ``done-pending`` outcome; every refusal evidence names its condition.
        The refusal composes first and then appends one ``terminal-refused``
        history evidence event (the append never changes the outcome); apart
        from that append-only event the manifest stays untouched:

        (1) machine completeness: a non-empty task map, every task complete
        through the existing completeness helper, every claim record closed,
        and no pending done handoff; (2) active-plan integrity and identity:
        the plan path resolves under the resolved plans directory through the
        fail-closed path policy, its filename matches the manifest
        ``plan_slug`` (and the resume watcher's recorded plan path when one
        exists), and the file reads under the shared ``_read_plan_bounded``
        policy (see that helper's docstring) with zero line-anchored
        unchecked checkbox lines; a path under any other
        directory refuses as ``unsupported archive location``; a present
        ``residual_policy`` input must be well-formed here (non-empty
        integer finding ids, a non-empty grant source, a finite numeric
        recorded-at epoch) and refuses before any filesystem work when it
        is not; (3)
        destination: the completed directory resolves only from the facts
        TOML-fence key (never the table-row parser, never a folder name), a
        missing key or non-existent directory refuses, and a supplied
        candidate that differs from the resolved destination refuses as
        ``unsupported archive destination``; (4) clean-round sidecar: the
        sidecar path resolves through the same fail-closed path policy
        before any open, then reads through the same bounded byte-capped
        policy as the plan read (an over-limit sidecar refuses with
        evidence naming ``clean-round review sidecar exceeds the bounded
        read limit``), then schema version 1, ``source_kind``
        ``code``, a present
        verdict must be ``yes`` (the verdict is the only field whose absence falls through, and ``last_fix_commit`` is nullable (absent or null skips the ancestry check); an absent verdict
        falls through to the blocking-rows check), the findings array is
        required and every findings row must carry a boolean ``blocking``
        flag, zero findings rows with ``blocking`` true, and a
        ``last_fix_commit`` ancestor-or-self of HEAD when non-null, the
        ancestry check running through the injectable ``commit_ancestry``
        seam; when the input carries a well-formed ``residual_policy``, an
        OR-branch applies inside this clause: it additionally accepts the
        focused verification-round sidecar when the policy's recorded-at
        predates the sidecar's round date (the proof is strict at day
        precision against the sidecar ``date`` field, so a policy recorded
        at or after the round day refuses), a blocking findings row whose
        id is not an integer refuses (membership against the policy's
        integer finding ids cannot prove such a row outside the named
        set), no findings row is both ``blocking: true`` and a member of
        the policy's finding ids, and a present ``verdict`` must be
        ``yes`` or ``no``; blocking rows outside the set are the
        backlogged residuals and are permitted, a blocking row inside the
        set still refuses, and the sidecar's verdict may be ``no``
        precisely because the out-of-set residuals are staged (the landed
        ``verdict`` sub-check narrows to the ``yes``/``no`` pair instead
        of applying), the membership rule replacing the
        zero-blocking rule; (5) commit identity via the existing
        ``commit_lookup``.

        On success the ``archive_gate`` receipt (source plan path, declared
        destination, plan digest, commit identity, checklist, timestamp) is
        written under the manifest lock; re-running overwrites the receipt in
        place with the identity fields stable and ``recorded_at`` refreshed.
        This stage never sets ``workflow_state`` and never writes a
        ``terminal_receipt``: the final stage owns those after the move.
        """

        def blocked(evidence: list[str]) -> dict[str, Any]:
            return self._terminal_refusal_tail(manifest, "pre-archive", evidence)

        # (1) Machine completeness, before any filesystem or destination work.
        tasks: Mapping[str, Any] = manifest["tasks"]
        if not tasks:
            return blocked(["manifest carries no tasks"])
        incomplete = sorted(task_id for task_id, task in tasks.items() if not self._task_complete(task))
        if incomplete:
            return blocked([f"tasks must be complete before archival; incomplete tasks: {', '.join(incomplete)}"])
        open_claims = sorted(
            claim_id
            for claim_id, claim in manifest.get("claims", {}).items()
            if not isinstance(claim, Mapping) or claim.get("state") != "closed"
        )
        if open_claims:
            return blocked([f"claim records must be closed before archival; open claims: {', '.join(open_claims)}"])
        pending_handoff = sorted(
            task_id for task_id, task in tasks.items() if task.get("status") in {"done-pending", "commit-pending"}
        )
        if pending_handoff:
            return blocked([f"pending done handoff must land before archival: {', '.join(pending_handoff)}"])

        # (2) Active-plan integrity and identity.
        if (
            not isinstance(plan_path, str)
            or not plan_path.strip()
            or not isinstance(destination, str)
            or not isinstance(review_sidecar, str)
            or not review_sidecar.strip()
            or not isinstance(last_commit_sha, str)
            or not re.fullmatch(r"[0-9a-fA-F]{7,64}", last_commit_sha.strip())
            or not isinstance(phase5_checklist, list)
            or not phase5_checklist
            or not all(isinstance(item, str) and item.strip() for item in phase5_checklist)
        ):
            return blocked(["active plan path, review sidecar, commit identity, and Phase 5 checklist are required"])
        # The optional structured residual_policy is part of the input shape
        # guard: a present but malformed policy refuses before any
        # filesystem work, so a half-recorded exit can never reach the
        # sidecar predicate.
        residual_policy, residual_policy_error = _normalize_residual_policy(residual_policy)
        if residual_policy_error is not None:
            return blocked([residual_policy_error])
        try:
            plan_relative = _safe_relative_path(self.repo_root, plan_path.strip())
        except ValueError:
            return blocked([f"unsupported archive location: {plan_path.strip()}", "the path is not a safe repository-relative path under the repository root"])
        plan_file = (self.repo_root / plan_relative).resolve()
        plans_dir = _resolved_facts_dir(self.repo_root, "plans_dir")
        if plans_dir is None or plans_dir not in (plan_file, *plan_file.parents):
            return blocked([f"unsupported archive location: {plan_path.strip()}", f"the active plan must sit under the resolved plans directory{'' if plans_dir is None else f': {plans_dir}'}"])
        expected_name = f"{self.plan_slug}.md"
        if plan_file.name != expected_name:
            return blocked([f"plan identity mismatch: filename {plan_file.name} does not match the manifest plan_slug '{self.plan_slug}' (expected {expected_name})"])
        watcher = manifest.get("resume_watcher")
        if isinstance(watcher, Mapping):
            watcher_plan = watcher.get("plan_path")
            if isinstance(watcher_plan, str) and watcher_plan.strip():
                watcher_path = Path(watcher_plan)
                if not watcher_path.is_absolute():
                    watcher_path = self.repo_root / watcher_path
                if watcher_path.resolve() != plan_file:
                    return blocked([f"plan identity mismatch: {plan_path.strip()} does not equal the resume watcher's recorded plan path {watcher_plan.strip()}"])
        plan_text, plan_error = _read_plan_bounded(self.repo_root, plan_relative, require_safe_path=True)
        if plan_error is not None:
            return blocked([f"active plan {plan_error}"])
        if not plan_text:
            # Same empty-artifact refusal as the final gate: an empty plan
            # (the shared helper already stripped whitespace-only bytes)
            # makes the unchecked-checkbox predicate vacuously true.
            return blocked(["active plan is empty"])
        unchecked = _unchecked_checkbox_pairs(plan_text.splitlines())
        if unchecked:
            first_number, first = unchecked[0]
            return blocked(
                [
                    f"active plan still has {len(unchecked)} unchecked checkbox line(s)",
                    f"line {first_number}: {first.strip()}",
                ]
            )

        # (3) Destination: facts-key resolution only, never a folder name.
        completed_dir = _resolved_facts_dir(self.repo_root, "plans_completed_dir")
        if completed_dir is None:
            return blocked(["unsupported archive destination: the facts TOML-fence key plans_completed_dir is missing or unresolvable"])
        if not completed_dir.is_dir():
            return blocked([f"unsupported archive destination: the resolved destination directory does not exist: {completed_dir}"])
        try:
            declared_relative = (completed_dir / plan_file.name).relative_to(self.repo_root)
        except ValueError:
            return blocked([f"unsupported archive destination: the resolved destination escapes the repository root: {completed_dir}"])
        if destination.strip():
            try:
                candidate = (self.repo_root / _safe_relative_path(self.repo_root, destination.strip())).resolve()
            except ValueError:
                return blocked([f"unsupported archive destination: {destination.strip()}", "the candidate destination is not a safe repository-relative path under the repository root"])
            if candidate != (self.repo_root / declared_relative):
                return blocked([f"unsupported archive destination: {destination.strip()}", f"the facts-resolved destination is {declared_relative.as_posix()}"])

        # (4) Clean-round sidecar, resolved through the same path policy
        # before any open.
        try:
            sidecar_relative = _safe_relative_path(self.repo_root, review_sidecar.strip())
        except ValueError:
            return blocked([f"clean-round review sidecar {review_sidecar.strip()} is not a safe repository-relative path under the repository root"])
        sidecar_path = self.repo_root / sidecar_relative
        if not sidecar_path.is_file():
            return blocked([f"clean-round review sidecar is missing or unreadable: {review_sidecar.strip()}"])
        try:
            # Same bounded byte-capped read as the plan read: read at most
            # PLAN_READ_LIMIT + 1 bytes and refuse len(data) over
            # PLAN_READ_LIMIT outright, so an over-limit sidecar is
            # never parsed; a decode failure is a ValueError subclass and
            # keeps the existing unreadable-or-invalid-JSON refusal.
            with sidecar_path.open("rb") as stream:
                data = stream.read(PLAN_READ_LIMIT + 1)
            if len(data) > PLAN_READ_LIMIT:
                return blocked([f"clean-round review sidecar exceeds the bounded read limit: over {PLAN_READ_LIMIT} bytes"])
            payload = json.loads(data.decode("utf-8"))
        except (OSError, ValueError):
            return blocked([f"clean-round review sidecar is unreadable or invalid JSON: {review_sidecar.strip()}"])
        if not isinstance(payload, Mapping):
            return blocked([f"clean-round review sidecar must be a JSON object: {review_sidecar.strip()}"])
        schema_version = payload.get("schema_version")
        if isinstance(schema_version, bool) or schema_version != 1:
            return blocked(["clean-round review sidecar must carry schema_version 1"])
        if payload.get("source_kind") != "code":
            return blocked([f"clean-round review sidecar must carry source_kind \"code\"; supplied {payload.get('source_kind')!r}"])
        # The review-staging schema makes the verdict optional: an ABSENT
        # verdict falls through to the blocking-rows check (which carries the
        # cleanliness evidence on its own), so only a PRESENT non-"yes"
        # verdict refuses here. Under the residual-policy OR-branch the
        # verdict sub-check narrows instead of applying: the focused
        # verification-round sidecar's verdict may be "no" precisely because
        # the out-of-set residuals are staged, "yes" is the ordinary clean
        # round, and any other value is a junk verdict the branch refuses.
        residual_exit = residual_policy is not None
        if residual_exit:
            round_date = payload.get("date")
            if not isinstance(round_date, str) or not round_date.strip():
                return blocked(["clean-round review sidecar is missing the round date the residual policy ordering proof requires"])
            try:
                round_day_epoch = datetime.strptime(round_date.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                return blocked([f"clean-round review sidecar round date is not an ISO YYYY-MM-DD date: {round_date.strip()}"])
            if float(residual_policy["recorded_at"]) >= round_day_epoch:
                return blocked([
                    f"residual policy recorded_at {residual_policy['recorded_at']} does not predate the sidecar round date {round_date.strip()}; the policy must be recorded in the manifest before the verification round runs",
                ])
            if "verdict" in payload and payload.get("verdict") not in ("yes", "no"):
                return blocked([f"clean-round review sidecar verdict under the residual policy branch must be \"yes\" or \"no\" when present; supplied {payload.get('verdict')!r}"])
        elif "verdict" in payload and payload.get("verdict") != "yes":
            return blocked([f"clean-round review sidecar verdict must be \"yes\" when present; an absent verdict falls through to the blocking-rows check; supplied {payload.get('verdict')!r}"])
        if "findings" not in payload:
            return blocked(["clean-round review sidecar is missing the required findings array"])
        findings = payload["findings"]
        if not isinstance(findings, (list, tuple)):
            return blocked(["clean-round review sidecar findings must be a list"])
        if any(not isinstance(row, Mapping) for row in findings):
            return blocked(["clean-round review sidecar findings rows must be JSON objects"])
        # Fail closed on malformed rows: every findings row must carry a
        # boolean blocking flag (unlike the verdict, blocking is required
        # per row with no fall-through), so a truthy string, a number, or
        # an absent key must never read as a clean row.
        malformed_blocking = [row for row in findings if not isinstance(row.get("blocking"), bool)]
        if malformed_blocking:
            first_row = malformed_blocking[0]
            named = first_row.get("id") if isinstance(first_row.get("id"), str) and first_row["id"].strip() else "<unidentified>"
            return blocked([f"clean-round review sidecar carries {len(malformed_blocking)} findings row(s) with a missing or non-boolean blocking value", f"first malformed finding: {named}"])
        blocking = [row for row in findings if row.get("blocking") is True]
        if residual_exit:
            # Membership rule replaces the zero-blocking rule: blocking rows
            # outside the policy's named finding set are the backlogged
            # residuals and are permitted, while a blocking row inside the
            # set still refuses because the named set must reach fixed or
            # dropped before the exit. Membership needs an integer row id
            # equal to a policy finding id, so a blocking row whose id is
            # not an integer refuses instead of silently reclassifying as
            # a permitted out-of-set residual.
            non_integer_ids = [
                row for row in blocking
                if isinstance(row.get("id"), bool) or not isinstance(row.get("id"), int)
            ]
            if non_integer_ids:
                first_row = non_integer_ids[0]
                return blocked([
                    f"clean-round review sidecar carries {len(non_integer_ids)} blocking finding(s) whose id is not an integer under the residual policy branch",
                    f"first non-integer blocking id: {first_row.get('id')!r}; membership against the policy set requires an integer id matching the policy's integer finding ids",
                ])
            policy_ids = set(residual_policy["finding_ids"])
            in_set = [row for row in blocking if row["id"] in policy_ids]
            if in_set:
                first_row = in_set[0]
                return blocked([
                    f"clean-round review sidecar carries {len(in_set)} blocking finding(s) inside the recorded residual policy set",
                    f"first in-set blocking finding: {first_row.get('id')}",
                ])
        elif blocking:
            first_row = blocking[0]
            named = first_row.get("id") if isinstance(first_row.get("id"), str) and first_row["id"].strip() else "<unidentified>"
            return blocked([f"clean-round review sidecar still carries {len(blocking)} blocking finding(s)", f"first blocking finding: {named}"])
        last_fix = payload.get("last_fix_commit")
        if last_fix is not None:
            if not isinstance(last_fix, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", last_fix.strip()):
                return blocked(["clean-round review sidecar last_fix_commit is not a commit identity"])
            if not self.commit_ancestry(last_fix.strip()):
                return blocked([f"clean-round review sidecar last_fix_commit {last_fix.strip()} is not an ancestor-or-self of HEAD; the clean round predates the current fix state"])

        # (5) Commit identity via the existing seam.
        if not self.commit_lookup(last_commit_sha.strip()):
            return blocked([f"commit identity is not provable: {last_commit_sha.strip()}"])

        digest, digest_error = _sha256_capped(plan_file)
        if digest is None:
            return blocked([f"active plan {digest_error}"])
        gate = {
            "plan_path": plan_path.strip(),
            "declared_destination": declared_relative.as_posix(),
            "plan_digest": digest,
            "last_commit_sha": last_commit_sha.strip(),
            "phase5_checklist": list(phase5_checklist),
            "recorded_at": self.clock(),
        }
        # Overwrite-in-place semantics: a re-run recomputes the identity
        # fields from the same proven inputs (stable) while recorded_at
        # advances. workflow_state and terminal_receipt are never written
        # here; the final stage owns them after the move.
        manifest["archive_gate"] = gate
        self._save(manifest)
        return _outcome(
            "success",
            "completed",
            [f"archive gate recorded; declared destination {declared_relative.as_posix()}"],
            "parent-continuation",
            "runtime:terminal",
            manifest.get("generation", 0),
            "continue-parent",
            archive_gate=dict(gate),
            declared_destination=declared_relative.as_posix(),
        )

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
        return _outcome("success", "completed", ["machine manifest is complete"], "parent-continuation", "runtime:terminal", manifest.get("generation", 0), "continue-parent", workflow_state="complete", phase5_checklist=receipt.get("phase5_checklist", []), archived_plan_path=receipt.get("archived_plan_path", ""), last_commit_sha=receipt.get("last_commit_sha", ""), plan_digest=receipt.get("plan_digest", ""))

    def diagnose(self) -> dict[str, Any]:
        """Report the first failed transition from one locked manifest snapshot.

        Read-only by construction: the manifest is loaded and validated under
        the manifest lock, the lock is released before the classification
        returns, and the method contains no write path. The CLI operation
        constructs its driver with ``persist_construction=False`` (like
        readiness), so construction persists no owner backfill or receipt
        write either and the manifest is byte-identical across the whole
        operation. The walk takes the EARLIEST classifiable failure event in
        history order whose subject has not since reached the progressed
        terminal state (a task-scoped event's task status ``complete``; a
        workflow-scoped event's ``workflow_state`` ``complete`` or
        ``terminal``) and classifies it through the fixed
        ``DIAGNOSE_REASON_CLASSIFICATIONS`` and
        ``DIAGNOSE_EVENT_CLASSIFICATIONS`` maps:

        - ``timeout`` and ``capacity-unavailable``: the same-named classes
          over their ``worker-blocked`` receipts.
        - ``worker-failure``: ``malformed-result``, ``runtime-error``,
          ``runtime-policy-unavailable``, and ``cleanup-unverified``
          receipts (the adapter's non-resumable unverified-kill arm
          included).
        - ``stale-evidence``: ``stale-claim`` receipts.
        - ``inclusion``: ``precondition-unverified`` receipts.
        - ``terminal-gate``: the ``terminal-refused`` event the terminal
          refusal tail appends.
        - ``user-interruption``: the ``user-interrupt-recorded`` event.
        - ``none``: no classifiable failure survives the filter;
          ``first_failed_transition`` is null.

        Cancellation is not a separate class: a cancelled worker's receipts
        already carry the ``timeout``, ``malformed-result``, or
        ``cleanup-unverified`` codes and classify under those, and unverified
        cleanup classifies under its receipt's ``worker-failure`` code. The
        classification enum is a fixed map; a new recurring gate is a backlog
        decision, never a silent extension of the table. A ``none`` report is
        a ``success`` outcome; a named failure is a ``blocked`` outcome with
        recovery action ``preserve-and-reconcile`` whose
        ``first_failed_transition`` carries the named history event.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                outcome = _mutation_unavailable(self, "runtime:diagnose", action_scope="parent-continuation")
                outcome["first_failed_transition"] = None
                outcome["classification"] = "none"
                return outcome
            manifest = self.validate_manifest(load_manifest(self.manifest_path))
        event, classification, index = self._first_failed_transition(manifest)
        if event is None:
            return _outcome(
                "success",
                "none",
                ["no classifiable failure event in manifest history"],
                "parent-continuation",
                "runtime:diagnose",
                manifest.get("generation", 0),
                "continue-parent",
                first_failed_transition=None,
                classification="none",
            )
        label = f"history[{index}] {event.get('event')}"
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            label += f" task={task_id}"
        reason_code = event.get("reason_code")
        if isinstance(reason_code, str) and reason_code:
            label += f" reason_code={reason_code}"
        return _outcome(
            "blocked",
            classification,
            [f"first failed transition: {label}", f"classification: {classification}"],
            "parent-continuation",
            "runtime:diagnose",
            manifest.get("generation", 0),
            "preserve-and-reconcile",
            first_failed_transition=event,
            classification=classification,
        )

    def _first_failed_transition(self, manifest: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str, int]:
        """Walk history in order and return the earliest live failure.

        Returns ``(event, classification, index)`` with a copied event
        mapping, or ``(None, "none", -1)`` when no classifiable failure
        survives the progressed-terminal filter. Never mutates the manifest.
        """

        workflow_terminal = manifest.get("workflow_state") in {"complete", "terminal"}
        for index, event in enumerate(manifest.get("history") or ()):
            if not isinstance(event, Mapping):
                continue
            classification = self._diagnose_classification(event)
            if classification is None or self._diagnose_event_superseded(manifest, event, workflow_terminal):
                continue
            return dict(event), classification, index
        return None, "none", -1

    @staticmethod
    def _diagnose_classification(event: Mapping[str, Any]) -> str | None:
        """Fixed-map classification for one history event; None when the event carries no classifiable failure evidence."""

        event_type = str(event.get("event", ""))
        if event_type == "worker-blocked":
            return DIAGNOSE_REASON_CLASSIFICATIONS.get(str(event.get("reason_code", "")))
        return DIAGNOSE_EVENT_CLASSIFICATIONS.get(event_type)

    @staticmethod
    def _diagnose_event_superseded(manifest: Mapping[str, Any], event: Mapping[str, Any], workflow_terminal: bool) -> bool:
        """True when the event's subject has since reached the progressed terminal state."""

        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id:
            task = manifest.get("tasks", {}).get(task_id)
            return task is not None and task.get("status") == "complete"
        return workflow_terminal

    _PLAN_PATH_TOKEN = re.compile(r"`([^`\n]+?)`")

    def preflight(self, plan_path: str | Path) -> dict[str, Any]:
        """Read-only pre-launch preflight (never mutates state).

        Run before a claim is created or rotated, the preflight proves the
        next task can be claimed, launched, completed, committed, and
        resumed, and reports plan-versus-claim scope drift BEFORE any claim
        is consumed. Checks, in fixed order, each named in the result's
        ``checks`` list: (1) the post-recovery worker-registry schema
        validation the next launch runs (``validate_manifest_worker_schema``);
        (2) plan readability through the shared bounded-read policy; (3) the
        whole-plan readiness decision (claimability, workflow state, live
        worker observation) reused verbatim from the readiness operation;
        (4) plan-versus-claim scope drift for the next provable incomplete
        task: the plan section's backticked path tokens are compared with the
        machine-seeded ``allowed_paths`` of that task's claim scope and every
        uncovered path is reported side by side with the seeded scope;
        (5) the recorded approval receipt, where the manifest records one,
        re-loaded and re-fingerprinted through the shared receipt loader.
        The CLI constructs the driver with ``persist_construction=False`` and
        the method contains no write path: a failing preflight leaves the
        manifest byte-identical and every claim and handoff retryable. The
        result carries one canonical continuation command built from the
        verified local configuration, so a resume run never hand-assembles
        runtime inputs.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                outcome = _mutation_unavailable(self, "runtime:preflight", action_scope="parent-continuation")
                outcome["preflight"] = {"status": "blocked", "checks": [], "drift": [], "continuation_command": None}
                return outcome
            manifest = load_manifest(self.manifest_path)
        checks: list[str] = []
        problems: list[str] = []
        try:
            validate_manifest_worker_schema(manifest)
            checks.append("worker-registry schema: valid")
        except ValueError as error:
            problems.append(f"worker-registry schema: {error}")
        plan_text, plan_error = _read_plan_bounded(None, plan_path, require_safe_path=False)
        if plan_error is not None:
            problems.append(f"plan file {plan_error}")
            plan_text = ""
        else:
            checks.append("plan file: readable")
        decision, failed_conditions, next_task_id, recovery_action = (
            self._readiness_decision(manifest, plan_text) if plan_text else ("recovery", ["plan unreadable"], None, "preserve-and-reconcile")
        )
        checks.append(f"readiness decision: {decision}")
        if failed_conditions:
            problems.extend(f"readiness: {condition}" for condition in failed_conditions)
        drift: list[dict[str, Any]] = []
        if plan_text and next_task_id is not None:
            seeded = manifest.get("tasks", {}).get(next_task_id, {})
            allowed = list(seeded.get("allowed_paths", ())) if isinstance(seeded, Mapping) else []
            section = self._plan_task_section(plan_text, next_task_id)
            if section is not None:
                claimed_paths = [token for token in self._PLAN_PATH_TOKEN.findall(section) if ("/" in token or token.endswith((".py", ".md", ".sh", ".json", ".toml"))) and not token.startswith(("http", "git "))]
                uncovered = sorted({path for path in claimed_paths if not any(path == scope or path.startswith(scope) for scope in allowed)})
                if uncovered:
                    drift.append({"task_id": next_task_id, "plan_paths": uncovered, "seeded_allowed_paths": allowed})
                    problems.append(f"scope drift on task '{next_task_id}': {len(uncovered)} plan path(s) outside the seeded scope")
                else:
                    checks.append(f"plan-versus-claim scope on '{next_task_id}': paths covered by the seeded scope")
        if plan_text and next_task_id is not None:
            recorded_digest = manifest.get("plan_digest")
            if isinstance(recorded_digest, str) and recorded_digest.strip():
                actual = hashlib.sha256(Path(plan_path).read_bytes()).hexdigest()
                if actual != recorded_digest:
                    problems.append(f"plan digest mismatch: file sha256 {actual} does not equal the manifest's recorded plan_digest")
                else:
                    checks.append("plan digest: matches the manifest's recorded plan_digest")
            else:
                checks.append("plan digest: not recorded in the manifest (delegated to the Step 0.5 validator)")
            task_state = manifest.get("tasks", {}).get(next_task_id, {})
            section = self._plan_task_section(plan_text, next_task_id)
            if section is not None:
                unchecked = section.count("- [ ]")
                complete = bool(task_state.get("checkbox")) if isinstance(task_state, Mapping) else False
                if complete and unchecked:
                    problems.append(f"checklist ownership: task '{next_task_id}' is complete but its plan section still has {unchecked} unchecked box(es)")
                elif not complete and not unchecked:
                    problems.append(f"checklist ownership: task '{next_task_id}' is incomplete but its plan section has no unchecked box to own the work")
                else:
                    checks.append(f"checklist ownership on '{next_task_id}': plan section checkbox state agrees with the manifest")
        live_claims = [
            claim
            for claim in manifest.get("claims", {}).values()
            if isinstance(claim, Mapping) and claim.get("state") in ("claimed", "launched", "blocked")
        ]
        missing_activation = [
            str(claim.get("task_id", "?"))
            for claim in live_claims
            if not isinstance(claim.get("launch_record"), Mapping) and self._claim_launch_evidence(manifest, claim) is None
        ]
        if missing_activation:
            problems.append(f"activation evidence missing or stale for live claim(s): {', '.join(missing_activation)}; the claim and handoff stay retryable")
        else:
            checks.append("activation evidence: every live claim carries its launch record")
        try:
            from execute_plan_worker_registry import WorkerRegistry

            witness = WorkerRegistry(manifest).capacity_witness()
            witness_state = "live" if witness.get("live_workers") else witness.get("state") or "released"
            checks.append(f"capacity evidence: witness {witness_state}")
        except ValueError as error:
            problems.append(f"capacity evidence: {error}")
        approval_receipt = manifest.get("approval_receipt")
        if isinstance(approval_receipt, Mapping) and approval_receipt.get("path"):
            from runtime_capabilities import load_approval_receipt

            try:
                load_approval_receipt(approval_receipt["path"], config_root=self.repo_root)
                checks.append("approval receipt: valid")
            except (OSError, ValueError, KeyError) as error:
                problems.append(f"approval receipt: {error}")
        continuation = (
            f"python3 scripts/execute_plan_runtime.py --manifest {self.manifest_path} --operation continue"
            if decision == "direct-continuation"
            else None
        )
        return _outcome(
            "blocked" if problems else "success",
            "preflight-passed" if not problems else "preflight-failed",
            checks + problems,
            "parent-continuation",
            "runtime:preflight",
            manifest.get("generation", 0),
            "preserve-and-reconcile" if problems else "continue-parent",
            preflight={"status": "passed" if not problems else "failed", "checks": checks, "problems": problems, "drift": drift, "next_task_id": next_task_id, "continuation_command": continuation},
        )

    def _plan_task_section(self, plan_text: str, task_id: str) -> str | None:
        """Extract the plan section of the task whose id encodes its ordinal.

        Machine task ids are seeded in plan order (``task-N``); the section
        is the ``### Task N`` heading span. A task id without a resolvable
        ordinal returns None and the drift check reports nothing for it.
        """
        match = re.fullmatch(r"task-(\d+)", str(task_id))
        if match is None:
            return None
        pattern = re.compile(rf"(?ms)^### Task {match.group(1)}:.*?(?=^### Task \d+:|^## |\Z)")
        found = pattern.search(plan_text)
        return found.group(0) if found else None

    def readiness(self, plan_path: str | Path) -> dict[str, Any]:
        """Decide continuation readiness from one locked manifest snapshot.

        Read-only by construction: the manifest is loaded and validated under
        the manifest lock, the lock is released before the decision returns,
        and the method contains no write path. The CLI operation constructs
        its driver with ``persist_construction=False``, so construction
        persists no owner backfill or receipt write either and the manifest
        is byte-identical across the whole operation. All five machine-owned
        conditions are evaluated against exactly one manifest snapshot. The
        plan file is read through the shared ``_read_plan_bounded`` policy
        (``require_safe_path=False``); see that helper's docstring for the
        bounded-read policy. A missing, unreadable, or
        over-limit plan is a fail-closed blocked outcome with the recovery
        decision. The digest, review-scope, and
        unresolved-finding conditions stay delegated to the Step 0.5
        validator and the review artifacts; the driver never reads review
        sidecars.

        Returns the closed decision set {``direct-continuation``,
        ``observe-worker``, ``recovery``, ``terminal-path``} with named
        failed conditions and the provable next task id.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                outcome = _mutation_unavailable(self, "runtime:readiness", action_scope="parent-continuation")
                outcome["decision"] = "recovery"
                outcome["next_task_id"] = None
                outcome["failed_conditions"] = ["manifest lock is held by another owner"]
                return outcome
            manifest = self.validate_manifest(load_manifest(self.manifest_path))
        plan_text, plan_error = _read_plan_bounded(None, plan_path, require_safe_path=False)
        if plan_error is not None:
            return _outcome(
                "blocked",
                "precondition-unverified",
                [f"plan file {plan_error}"],
                "parent-continuation",
                "runtime:readiness",
                manifest.get("generation", 0),
                "preserve-and-reconcile",
                decision="recovery",
                next_task_id=None,
                failed_conditions=[f"plan file {plan_error}"],
            )
        decision, failed_conditions, next_task_id, recovery_action = self._readiness_decision(manifest, plan_text)
        evidence = list(failed_conditions)
        if decision == "observe-worker":
            evidence.insert(0, f"live claim on task '{next_task_id}'; observe the live worker before any launch")
        elif not evidence:
            evidence = [f"readiness decision: {decision}"]
        return _outcome(
            "blocked" if decision == "recovery" else "success",
            decision,
            evidence,
            "parent-continuation",
            "runtime:readiness",
            manifest.get("generation", 0),
            recovery_action,
            decision=decision,
            next_task_id=next_task_id,
            failed_conditions=failed_conditions,
        )

    def _readiness_decision(
        self, manifest: Mapping[str, Any], plan_text: str
    ) -> tuple[str, list[str], str | None, str]:
        """Evaluate the five machine-owned conditions; never mutates state.

        Returns ``(decision, failed_conditions, next_task_id,
        recovery_action)``. The decision order is fixed: terminal-path,
        observe-worker, recovery, direct-continuation.
        """

        tasks: Mapping[str, Any] = manifest["tasks"]
        claims: Mapping[str, Any] = manifest.get("claims", {})
        workflow_state = manifest.get("workflow_state")
        plan_lines = plan_text.splitlines()
        ordered_tasks = sorted(tasks.values(), key=_pending_sort_key)
        failed: list[tuple[str, str]] = []
        # (0) A manifest without tasks continues nothing: route to recovery
        # naming the empty manifest instead of falling through to a
        # direct-continuation decision whose next task is None.
        if not tasks:
            failed.append(
                (
                    "machine manifest carries no tasks; nothing to continue",
                    "stop-or-recovery",
                )
            )
        # (a) Machine ownership and state: only an active workflow continues
        # directly; blocked or aborted names the machine state with a
        # stop-or-recovery action. An already complete or terminal manifest
        # is handled first by the terminal-path decision below.
        if workflow_state != "active":
            failed.append(
                (
                    f"machine workflow_state is '{workflow_state}'; only an active workflow continues directly",
                    "stop-or-recovery",
                )
            )
        # (b) No unresolved handoff or fenced claim: no task in done-pending
        # or commit-pending, no claim in state blocked. The done-pending arm
        # names the driver-owned recovery operation: that wedge's single
        # sanctioned exit is the operator-invoked recover-done-pending
        # transition, and readiness only points at it (read-only naming,
        # never a mutation). The commit-pending arm keeps
        # preserve-and-reconcile: its wedge exception is the commit-witness
        # path, not the recovery transition.
        for task in ordered_tasks:
            if task.get("status") in {"done-pending", "commit-pending"}:
                recovery_action = (
                    "recover-done-pending"
                    if task.get("status") == "done-pending"
                    else "preserve-and-reconcile"
                )
                failed.append(
                    (
                        f"unresolved done handoff: task '{task['id']}' is in status '{task.get('status')}'",
                        recovery_action,
                    )
                )
        for claim in claims.values():
            if claim.get("state") == "blocked":
                failed.append(
                    (
                        f"fenced claim in state 'blocked' on task '{claim.get('task_id')}'",
                        "preserve-and-reconcile",
                    )
                )
        # (c) Plan-manifest agreement: for every task in the progressed set,
        # the plan's matching section carries no unchecked checkbox line. The
        # manifest wins per the seeding boundary, so disagreement is corrected
        # in the plan through the skill-gated plan-edit step, never by
        # mutating the manifest. A pending task's unchecked boxes agree with
        # the manifest.
        # Plan shape first: a plan with zero recognizable
        # '### Task <N>:' headings cannot agree or disagree per-section;
        # failing it keeps a wrong --plan file from producing a vacuous
        # direct-continuation while no task has progressed.
        if not any(_TASK_SECTION_HEADING.match(line) for line in plan_lines):
            failed.append(
                (
                    "plan carries no recognizable task sections",
                    "stop-or-recovery",
                )
            )
        for task in ordered_tasks:
            if task.get("status") not in PROGRESSED_TASK_STATUSES:
                continue
            task_id = str(task["id"])
            number = _plan_task_number(task_id)
            section = None if number is None else _plan_task_section_lines(plan_lines, number)
            if section is None:
                label = number if number is not None else task_id
                failed.append(
                    (
                        f"plan-manifest disagreement: task '{task_id}' is '{task.get('status')}' in the manifest but its plan section '### Task {label}:' is missing",
                        "correct-plan-through-skill-gated-plan-edit",
                    )
                )
                continue
            unchecked = _unchecked_checkbox_lines(section)
            if unchecked:
                failed.append(
                    (
                        f"plan-manifest disagreement: task '{task_id}' is '{task.get('status')}' in the manifest but its plan section '### Task {number}:' carries {len(unchecked)} unchecked checkbox line(s); the manifest wins per the seeding boundary",
                        "correct-plan-through-skill-gated-plan-edit",
                    )
                )
        # (d) The next incomplete task is provable: claimable from pending.
        incomplete = [task for task in ordered_tasks if not self._task_complete(task)]
        next_task_id = str(incomplete[0]["id"]) if incomplete else None
        if incomplete and incomplete[0].get("status") != "pending":
            failed.append(
                (
                    f"next incomplete task '{next_task_id}' is not provable: status '{incomplete[0].get('status')}' is not claimable",
                    "preserve-and-reconcile",
                )
            )
        # Fixed decision order: terminal-path, observe-worker, recovery,
        # direct-continuation.
        if tasks and not incomplete and workflow_state in {"active", "complete", "terminal"}:
            return "terminal-path", [], None, "continue-parent"
        for claim in claims.values():
            claimed_task = tasks.get(claim.get("task_id"))
            if (
                claim.get("state") in {"claimed", "launched"}
                and claimed_task is not None
                and claimed_task.get("status") not in PROGRESSED_TASK_STATUSES
            ):
                return "observe-worker", [text for text, _ in failed], str(claim["task_id"]), "observe-live-worker"
        if failed:
            return "recovery", [text for text, _ in failed], next_task_id, failed[0][1]
        return "direct-continuation", [], next_task_id, "continue-parent"

    # ------------------------------------------------------------------
    # Interrupted-claim ownership recovery (lease-gated reclaim)
    # ------------------------------------------------------------------

    @staticmethod
    def _proven_prelaunch_activation_failure(
        manifest: Mapping[str, Any], task_id: str, task: Mapping[str, Any], claim: Mapping[str, Any]
    ) -> bool:
        """Prove a policy/activation refusal happened before any worker launch."""

        receipt = task.get("blocked_receipt")
        if (
            task.get("status") != "blocked"
            or task.get("resume_allowed") is not False
            or claim.get("state") != "blocked"
            or not isinstance(receipt, Mapping)
            or receipt.get("reason_code") != "runtime-policy-unavailable"
            or claim.get("launch_record") is not None
        ):
            return False
        intent_key = claim.get("handoff_intent_key")
        intents = manifest.get("handoff_intents")
        intent = intents.get(intent_key) if isinstance(intent_key, str) and isinstance(intents, Mapping) else None
        if not isinstance(intent, Mapping) or intent.get("state") != "prepared" or intent.get("launch_receipt") is not None:
            return False
        successor = intent.get("successor")
        if not isinstance(successor, Mapping) or any(
            successor.get(field) != claim.get(claim_field)
            for field, claim_field in (
                ("task_id", "task_id"),
                ("claim_token", "token"),
                ("generation", "generation"),
                ("claim_owner_id", "claim_owner_id"),
                ("launch_id", "launch_id"),
            )
        ):
            return False
        workers = manifest.get("workers")
        if not isinstance(workers, Mapping) or any(
            isinstance(worker, Mapping) and worker.get("task_id") == task_id
            for worker in workers.values()
        ):
            return False
        reservations = manifest.get("capacity", {}).get("reservations", {})
        if isinstance(reservations, Mapping) and any(
            isinstance(reservation, Mapping) and reservation.get("task_id") == task_id
            for reservation in reservations.values()
        ):
            return False
        return True

    @_locked_mutation
    def reclaim(self, task_id: str) -> dict[str, Any]:
        """Release one expired claim so its interrupted task can be re-claimed.

        The machine-provable precondition is lease expiry only: claim records
        carry token, generation, owner, and timestamp but no process identity,
        so process liveness cannot be proven. Under the manifest lock the
        operation admits only a claim in ``RECLAIMABLE_CLAIM_STATES`` on a task
        outside ``PROGRESSED_TASK_STATUSES`` whose ``timestamp`` is at least
        ``CLAIM_LEASE_SECONDS`` old (measured with the injectable clock); the
        compare-and-swap release then replaces the claim generation and token,
        marks the old claim ``replaced`` (the resume path's recycle pattern),
        resets the task to ``pending`` with the previous session's resume
        fields stripped, and preserves recorded checkpoints as evidence. The
        replaced claim is reconciled by rotation and never quarantined at
        startup. Every refusal (before expiry, unknown task, closed or
        replaced or aborted claim, parked ``waiting-capacity`` claim with a
        live retry policy or an exhausted retry budget, progressed task)
        fails closed with the
        resumable ``stale-claim`` outcome and never mutates the manifest;
        for a reclaimable claim on a task outside the progressed set, a
        workflow in the closed non-active set returns the preserve-and-stop
        outcome before any lease accounting instead of releasing anything
        (an explicitly aborted workflow keeps the ``explicit-abort``
        outcome; a complete or terminal workflow returns the same shape
        with evidence naming the finished state; a progressed-task refusal
        still returns ``stale-claim``). A claim that belongs to a live
        batch claim group
        is refused with the group named: the group protocol owns
        its members and reclaiming one rotates it away while the group
        stays active, wedging every entrypoint; batch members recover
        through the group path (``continue --batch``), never through
        reclaim - except the one executable exit: a member whose
        receipt is non-resumable (the task blocked with ``resume_allowed``
        False) has no group path left, so its reclaim is allowed through
        and atomically fails the group in the same locked CAS, releasing
        the staged members back to the pending queue as individuals.
        """

        manifest = self.refresh_manifest()
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id)
        if isinstance(claim, Mapping) and claim.get("state") == "waiting-capacity":
            # A parked claim is machine-proven durable state (its capacity
            # receipt landed under the manifest lock), never an ambiguous
            # live worker: it stays outside the reclaimable set while its
            # bounded retry policy is live, and recovery is the in-place
            # resume (continue relaunches the same claim), never a rotation.
            # In the exhausted window (attempts_remaining 0, before the next
            # capacity receipt lands the claim in blocked) the refusal names
            # the exhausted budget and the pending transition instead; an
            # absent or malformed retry_policy keeps the live-budget evidence
            # rather than crashing the branch.
            retry_policy = claim.get("retry_policy")
            attempts_remaining = (
                retry_policy.get("attempts_remaining")
                if isinstance(retry_policy, Mapping)
                else None
            )
            if (
                isinstance(attempts_remaining, int)
                and not isinstance(attempts_remaining, bool)
                and attempts_remaining <= 0
            ):
                evidence = [
                    "claim state 'waiting-capacity' is parked with its retry budget exhausted; reclaim refused",
                    "the next capacity receipt transitions the claim to blocked, whose recovery machinery applies",
                ]
            else:
                evidence = [
                    "claim state 'waiting-capacity' is parked on a live bounded retry policy; reclaim refused",
                    "resume in place with continue while attempts remain",
                ]
            return _stale_claim_outcome(
                str(claim.get("token", f"{task_id}:reclaim")),
                int(claim.get("generation", manifest.get("generation", 0))),
                evidence,
            )
        if task is None or not isinstance(claim, Mapping) or claim.get("state") not in RECLAIMABLE_CLAIM_STATES:
            state = claim.get("state") if isinstance(claim, Mapping) else "none"
            return _stale_claim_outcome(
                f"{task_id}:reclaim",
                manifest.get("generation", 0),
                [f"no reclaimable claim on task '{task_id}' (claim state: {state})"],
            )
        if task.get("status") in PROGRESSED_TASK_STATUSES:
            return _stale_claim_outcome(
                str(claim.get("token", f"{task_id}:reclaim")),
                int(claim.get("generation", manifest.get("generation", 0))),
                [f"task status '{task.get('status')}' is in the progressed set; reclaim refused"],
            )
        workflow_state = manifest.get("workflow_state")
        if workflow_state in {"aborted", "complete", "terminal"}:
            # The stronger fence first: the full closed non-active set is
            # never mutated by a reclaim of an expired lease claim, whatever
            # the lease state is, so this fence precedes the lease check. An
            # aborted workflow keeps the explicit-abort outcome; a complete
            # or terminal workflow returns the same preserve-and-stop shape
            # with evidence naming the finished state, because releasing a
            # claim under a finished run would rewrite a settled record.
            if workflow_state == "aborted":
                fence_evidence = ["workflow was explicitly aborted before the reclaim"]
            else:
                fence_evidence = [
                    f"workflow_state is '{workflow_state}'; the workflow already finished; reclaim refused",
                    "the finished run is preserved; reclaim cannot release claims under it",
                ]
            return _abort_outcome(
                str(claim.get("token", f"{task_id}:reclaim")),
                int(claim.get("generation", manifest.get("generation", 0))),
                fence_evidence,
            )
        group_id = claim.get("group_id")
        if group_id and self._claim_owned_by_live_group(manifest, claim):
            group = manifest.get("claim_groups", {}).get(group_id)
            if self._claim_group_kind(manifest, claim, group) == GROUP_KIND_PARALLEL:
                # Parallel groups have no group path to recover through
                # (members recover through the standard single-task path),
                # so the fence is only about who releases: a member whose
                # receipt still permits continuation has that recovery left,
                # so its reclaim is refused naming the group; a member with
                # a terminal (non-resumable) receipt has no path left, and
                # its reclaim is the executable exit that releases ONLY that
                # member - the group stays active and its siblings are never
                # touched (never an atomic group fail).
                if not (task.get("status") == "blocked" and task.get("resume_allowed") is False):
                    return _stale_claim_outcome(
                        str(claim.get("token", f"{task_id}:reclaim")),
                        int(claim.get("generation", manifest.get("generation", 0))),
                        [
                            f"claim is a member of live parallel group '{group_id}'; reclaim refused",
                            "recover the member through the standard single-task path (resume), not reclaim",
                        ],
                    )
                return self._reclaim_parallel_member_locked(manifest, task_id, claim, group_id, group)
            # Live-group fence with its one executable exit.
            # The lease check below is exactly the wedge trigger - a group
            # parked at a budget pause is EXPECTED to be lease-expired - so
            # the fence precedes any lease accounting and fires for a member
            # of an active group whatever its lease state. For a member
            # whose receipt still permits continuation the refusal is the
            # resumable stale-claim outcome naming the group: recovery is
            # the group path (continue --batch), never a reclaim that would
            # rotate the member away and dead-end every entrypoint. A member
            # whose receipt is NON-resumable has no group path left (both
            # group recovery entries refuse a non-resumable receipt and
            # nothing else closes a group), so its reclaim is the exit: the
            # locked CAS below rotates the member away AND fails the group
            # atomically, releasing the staged members back to the pending
            # queue as individuals. No lease wait is re-introduced for this
            # shape: the durable non-resumable receipt is machine-provable
            # and terminal (every continuation entry refuses it), so lease
            # freshness here only means the receipt just landed, never that
            # a worker is mid-flight.
            group = manifest.get("claim_groups", {}).get(group_id)
            if not (task.get("status") == "blocked" and task.get("resume_allowed") is False):
                return _stale_claim_outcome(
                    str(claim.get("token", f"{task_id}:reclaim")),
                    int(claim.get("generation", manifest.get("generation", 0))),
                    [
                        f"claim is a member of live batch claim group '{group_id}'; reclaim refused",
                        "recover the batch member through the group path (continue --batch), not reclaim",
                    ],
                )
            return self._reclaim_live_group_member_locked(manifest, task_id, claim, group_id, group)
        timestamp = claim.get("timestamp")
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            return _stale_claim_outcome(
                str(claim.get("token", f"{task_id}:reclaim")),
                int(claim.get("generation", manifest.get("generation", 0))),
                ["claim carries no lease timestamp; reclaim refused"],
            )
        elapsed = self.clock() - float(timestamp)
        prelaunch_recovery = self._proven_prelaunch_activation_failure(manifest, task_id, task, claim)
        if elapsed < CLAIM_LEASE_SECONDS and not prelaunch_recovery:
            return _stale_claim_outcome(
                str(claim.get("token", f"{task_id}:reclaim")),
                int(claim.get("generation", manifest.get("generation", 0))),
                [f"claim lease has not expired: {int(elapsed)}s elapsed of {CLAIM_LEASE_SECONDS}s"],
            )
        capacity = self.reconcile_worker_capacity(manifest)
        if capacity.get("status") != "available":
            self._save(manifest)
            return _outcome(
                "blocked", "capacity-unavailable", [str(capacity.get("reason", "capacity unavailable"))],
                "repository-task", f"{task_id}:reclaim", int(claim.get("generation", manifest.get("generation", 0))),
                "preserve-and-reconcile", claim_token=(claim.get("token")),
            )
        # Terminal workers no longer consume capacity, but their registry rows
        # still carry the old claim identity. Retire those rows with their
        # released capacity contributions before rotating the claim, so the
        # persisted manifest remains schema-valid. Active and quarantined
        # workers are retained and refused by the capacity gate above.
        workers = manifest.get("workers", {})
        capacity_entries = manifest.get("capacity", {}).get("entries", {})
        for worker_id, worker in list(workers.items()):
            if worker.get("task_id") == task_id and worker.get("state") == "terminal":
                capacity_entries.pop(worker.get("capacity_entry_id"), None)
                workers.pop(worker_id, None)
        # Compare-and-swap the release: rotate token and generation, mark the
        # old claim replaced, and return the task to pending. The old claim's
        # recorded checkpoints are deliberately preserved as evidence; the
        # rotated identity fences any late receipt from the replaced owner as
        # owner-mismatch.
        replaced_generation = int(manifest.get("generation", 0)) + 1
        replaced_token = uuid.uuid4().hex
        intent_key = claim.get("handoff_intent_key")
        intent = manifest.get("handoff_intents", {}).get(intent_key) if isinstance(intent_key, str) else None
        if prelaunch_recovery and isinstance(intent, Mapping) and intent.get("state") == "prepared":
            self._transition_handoff(intent, "failed")
            intent["failure_reason"] = "prepared successor claim was reclaimed before launch"
            intent["failed_at"] = self.clock()
        manifest["generation"] = replaced_generation
        manifest["claims"][task_id] = {
            **claim,
            "token": replaced_token,
            "generation": replaced_generation,
            "state": "replaced",
            "replaced_at": self.clock(),
        }
        # The reset strips the previous session's resume fields (the shared
        # rotation helper); the replaced claim itself keeps its launch record
        # and baseline as audit evidence, fenced by the rotated identity.
        self._reset_task_to_pending(task)
        manifest.setdefault("history", []).append({
            "event": "claim-reclaimed",
            "task_id": task_id,
            "replaced_generation": int(claim.get("generation", 0)),
            "generation": replaced_generation,
        })
        self._save(manifest)
        return _outcome(
            "success",
            "reclaimed",
            _reclaim_evidence_lines(
                task_id,
                str(claim.get("token", "claim")),
                replaced_token,
                replaced_generation,
            ) + (["recovery=proven-prelaunch-activation-failure", "launch_receipt=absent", "worker_identity=absent"] if prelaunch_recovery else []),
            "repository-task",
            f"{task_id}:reclaim",
            replaced_generation,
            "continue-parent",
            actions=[],
            claimed=False,
            reclaimed_task=task_id,
            replacement_generation=replaced_generation,
        )

    def _reclaim_live_group_member_locked(
        self,
        manifest: dict[str, Any],
        task_id: str,
        claim: Mapping[str, Any],
        group_id: str,
        group: Mapping[str, Any],
    ) -> dict[str, Any]:
        """The executable exit: reclaim a non-resumable member and fail its group.

        Caller holds the manifest lock; the fence has already proven the
        wedge shape (live group, member claim, task blocked with a receipt
        whose ``resume_allowed`` is False, so both group recovery entries
        refuse it forever). One save carries the whole release: the member
        identity rotates (fresh token and bumped generation, so any late
        receipt from the dead attempt fences as owner-mismatch), the task
        returns to pending with the dead session's resume fields stripped,
        the group is marked failed with its active member cleared so no
        entrypoint keeps routing through it, and the still-staged member
        claims close so their pending tasks re-enter the queue as
        individual claims. A torn release that left the group live with a
        reclaimed member would re-wedge every entrypoint.
        """

        replaced_generation = int(manifest.get("generation", 0)) + 1
        replaced_token = uuid.uuid4().hex
        manifest["generation"] = replaced_generation
        manifest["claims"][task_id] = {
            **claim,
            "token": replaced_token,
            "generation": replaced_generation,
            "state": "replaced",
            "replaced_at": self.clock(),
        }
        self._reset_task_to_pending(manifest["tasks"][task_id])
        released = [
            member
            for member in (str(item) for item in (group.get("members") or ()))
            if member != task_id and (manifest["claims"].get(member) or {}).get("state") == "staged"
        ]
        for member in released:
            manifest["claims"][member]["state"] = "closed"
        self._set_group_state(manifest, str(group_id), "failed", None)
        manifest.setdefault("history", []).append({
            "event": "claim-reclaimed",
            "task_id": task_id,
            "replaced_generation": int(claim.get("generation", 0)),
            "generation": replaced_generation,
        })
        manifest["history"].append({
            "event": "batch-group-failed",
            "group_id": group_id,
            "member": task_id,
            "released_members": released,
        })
        self._save(manifest)
        return _outcome(
            "success",
            "reclaimed",
            _reclaim_evidence_lines(
                task_id,
                str(claim.get("token", "claim")),
                replaced_token,
                replaced_generation,
            )
            + [
                f"group_failed={group_id}",
                f"released_members={','.join(released) if released else 'none'}",
            ],
            "repository-task",
            f"{task_id}:reclaim",
            replaced_generation,
            "continue-parent",
            actions=[],
            claimed=False,
            reclaimed_task=task_id,
            replacement_generation=replaced_generation,
            group_id=group_id,
            group_state="failed",
        )

    def _reclaim_parallel_member_locked(
        self,
        manifest: dict[str, Any],
        task_id: str,
        claim: Mapping[str, Any],
        group_id: str,
        group: Mapping[str, Any],
    ) -> dict[str, Any]:
        """The per-member executable exit: reclaim one parallel member only.

        Caller holds the manifest lock; the fence has already proven the
        terminal shape (live parallel group, member claim, task blocked with
        a receipt whose ``resume_allowed`` is False, so the standard
        single-task recovery refuses it forever). One save carries the whole
        release: the member identity rotates (fresh token and bumped
        generation, so any late receipt from the dead attempt fences as
        owner-mismatch) and the task returns to pending with the dead
        session's resume fields stripped. Unlike the batch exit this is
        never an atomic group fail: the group stays active, the siblings'
        claims are untouched, and the released member's task re-enters the
        queue once the group closes. When the release leaves every member at
        a terminal claim state the group closes too (the last commit may
        already have landed before the final member was released), so the
        live group can never wedge on a fully terminal membership.
        """

        replaced_generation = int(manifest.get("generation", 0)) + 1
        replaced_token = uuid.uuid4().hex
        manifest["generation"] = replaced_generation
        manifest["claims"][task_id] = {
            **claim,
            "token": replaced_token,
            "generation": replaced_generation,
            "state": "replaced",
            "replaced_at": self.clock(),
        }
        self._reset_task_to_pending(manifest["tasks"][task_id])
        manifest.setdefault("history", []).append({
            "event": "claim-reclaimed",
            "task_id": task_id,
            "replaced_generation": int(claim.get("generation", 0)),
            "generation": replaced_generation,
        })
        manifest["history"].append({
            "event": "parallel-member-reclaimed",
            "group_id": group_id,
            "member": task_id,
        })
        # The release is a terminal member transition, so it runs the one
        # terminal-membership close predicate (shared with the advance close
        # and the session-less resume release): when this release leaves
        # every member claim terminal the group closes too.
        self._close_parallel_group_when_terminal_locked(manifest, group_id, task_id, group)
        self._save(manifest)
        return _outcome(
            "success",
            "reclaimed",
            _reclaim_evidence_lines(
                task_id,
                str(claim.get("token", "claim")),
                replaced_token,
                replaced_generation,
            )
            + [
                f"group={group_id} stays active; only this member was released",
            ],
            "repository-task",
            f"{task_id}:reclaim",
            replaced_generation,
            "continue-parent",
            actions=[],
            claimed=False,
            reclaimed_task=task_id,
            replacement_generation=replaced_generation,
            group_id=group_id,
            group_state=str((manifest.get("claim_groups", {}).get(group_id) or {}).get("state", "active")),
        )

    @_locked_mutation
    def recover_done_pending(
        self,
        task_id: str,
        token: str,
        disposition: str,
        terminal_evidence: Any,
        backlog_evidence: Any = None,
    ) -> dict[str, Any]:
        """Recover a terminal worker's stuck done-pending claim under operator evidence.

        The single sanctioned exit from ``done-pending``. A terminal worker's
        claim can rest at the done boundary with no incomplete receipt path
        left: ``record_done`` refuses the incomplete done evidence, ``abort``
        refuses to regress a claim past its receipt boundary (the r5-F2 wedge
        exception stays commit-pending-only), and ``reclaim`` admits only
        tasks outside the progressed statuses behind the lease. This
        transition closes that deadlock class without any manual
        machine-manifest edit. Under the manifest lock it admits exactly one
        shape:

        - exact identity: the live claim's owner, token, and generation must
          match the call exactly (the shared ``_stale_claim_outcome`` fence);
        - the task status is ``done-pending``;
        - no live claim group owns the claim - parallel or batch alike,
          checked with the group-kind-agnostic ``_claim_owned_by_live_group``
          predicate; the refusal names the group and leaves the sibling
          members untouched;
        - the terminal evidence is a non-empty list of non-empty strings, at
          least one naming the claim's session or launch identity; per the
          reclaim liveness precedent (claim records carry no process
          identity), the transition runs no process-liveness probe and waits
          out no lease - the operator-supplied evidence is what proves the
          worker ended;
        - no ``done-pending-recovery`` receipt with the same task id, token,
          and generation is already recorded in history (the receipt identity
          fences duplicate receipts).

        The ``requeue`` disposition reuses the shared
        ``_reset_task_to_pending`` rotation (the dead session's
        ``session_id``/``resume_allowed``/``blocked_receipt`` fields
        stripped), closes the claim, bumps the manifest generation exactly
        once so the next claim mints a fresh policy token from the reconciled
        plan section through the seeding boundary (``allowed_paths`` is never
        edited here), appends the ``done-pending-recovery`` receipt carrying
        the bounded terminal evidence, and post-validates that the next
        provable incomplete task is pending or None before the save (the
        post-acceptance check; a failed check discards every in-memory
        mutation). No claim or launch action is returned: launching the
        requeued task is the ordinary claim path's job, never this
        transition's.

        The ``defer`` disposition marks the task ``deferred`` -
        complete-for-selection through ``_task_complete``, never relaunched,
        and deliberately outside PROGRESSED_TASK_STATUSES so readiness
        condition (c) plan-manifest agreement never demands unchecked-checkbox
        closure for a task the operator chose not to complete (the recorded
        receipt is the evidence). It requires backlog evidence: an existing
        repository-relative file under ``docs/history/backlog/`` (validated
        fail-closed through the shared ``_safe_relative_path`` path policy),
        recorded in the receipt. Dependency ordering is validated before any
        mutation: defer is valid only for the next provable incomplete task,
        the one machine-provable dependency signal the manifest carries. The
        claim is closed (a live claim on a non-progressed ``deferred`` task
        would flip readiness to ``observe-worker``), the receipt is appended,
        and the shared post-acceptance check runs; no generation bump (the
        requeued-task re-authorization does not apply to a retired task).

        The ``abort`` disposition ends the run: the same durable writes the
        wedged-abort path makes (task aborted, claim aborted,
        ``workflow_state`` aborted), the receipt appended, and the shared
        post-acceptance validation skipped - the run is terminal, there is no
        next provable task to prove. The envelope is the shared
        ``_abort_outcome`` shape (status ``aborted``, reason ``explicit-abort``,
        recovery action ``preserve-and-stop``) carrying the recovery receipt
        identity and the abort evidence.
        """

        manifest = self.refresh_manifest()
        identity = f"{task_id}:recovery"
        task = manifest["tasks"].get(task_id)
        claim = manifest["claims"].get(task_id)
        claim_generation = int(claim.get("generation", manifest.get("generation", 0))) if isinstance(claim, Mapping) else int(manifest.get("generation", 0))
        # (1) Exact-identity fence: owner, token, and generation must match
        # the live claim exactly. Any mismatch (including no live claim at
        # all) is the resumable stale-claim refusal, and nothing is mutated.
        mismatched: list[str] = []
        if not isinstance(claim, Mapping):
            mismatched.append("claim")
        else:
            if claim.get("owner") != self.owner:
                mismatched.append("owner")
            if claim.get("token") != token:
                mismatched.append("token")
            if claim.get("generation") != manifest.get("generation"):
                mismatched.append("generation")
        if mismatched:
            return _stale_claim_outcome(
                identity,
                claim_generation,
                [
                    f"recovery refused: claim identity does not match the live claim on task '{task_id}'; exact owner, token, and generation identity is required",
                    f"identity mismatch: {', '.join(mismatched)}",
                ],
            )
        # (2) Done-pending precondition: the transition exits exactly the
        # done-pending wedge, never a live claim on a task still in flight.
        if task is None or task.get("status") != "done-pending":
            status = str(task.get("status")) if isinstance(task, Mapping) else "unknown"
            return _stale_claim_outcome(
                identity,
                claim_generation,
                [f"recovery requires task status 'done-pending'; task '{task_id}' is '{status}'"],
            )
        # (3) Live-claim-group refusal, group-kind-agnostic: a parallel or
        # batch group owns its member claims, so a member's recovery would
        # fight the group protocol; the wedge exception is named for the
        # operator and the siblings are untouched.
        group_id = claim.get("group_id")
        if group_id and self._claim_owned_by_live_group(manifest, claim):
            return _stale_claim_outcome(
                identity,
                claim_generation,
                [
                    f"claim is owned by live claim group '{group_id}'; recovery refused",
                    "the group protocol owns the claim; sibling members are untouched",
                ],
            )
        # (4) Terminal-evidence gate: non-empty bounded strings, at least one
        # naming the claim's session or launch identity. No liveness probe
        # and no lease wait: the evidence is the proof.
        if isinstance(terminal_evidence, str):
            supplied: list[Any] = [terminal_evidence]
        elif isinstance(terminal_evidence, (list, tuple)):
            supplied = list(terminal_evidence)
        else:
            supplied = []
        if not supplied or any(not isinstance(item, str) or not item.strip() for item in supplied):
            return _outcome(
                "blocked",
                "precondition-unverified",
                ["terminal evidence is required: a non-empty list of non-empty strings naming the claim's session or launch identity and the observed termination"],
                "repository-task",
                identity,
                claim_generation,
                "preserve-and-reconcile",
            )
        terminal = bounded_evidence(supplied)
        identity_anchors: list[str] = []
        for candidate in (task.get("session_id"), claim.get("session_id")):
            session = str(candidate or "").strip()
            if session and session not in identity_anchors:
                identity_anchors.append(session)
        launch_record = self._claim_launch_evidence(manifest, claim)
        if isinstance(launch_record, Mapping):
            baseline = str(launch_record.get("baseline_revision") or "").strip()
            if baseline and baseline not in identity_anchors:
                identity_anchors.append(baseline)
        if not identity_anchors or not any(anchor in item for item in terminal for anchor in identity_anchors):
            return _outcome(
                "blocked",
                "precondition-unverified",
                ["terminal evidence must name the claim's session or launch identity and the observed termination"],
                "repository-task",
                identity,
                claim_generation,
                "preserve-and-reconcile",
            )
        # (5) Duplicate-receipt fence: the receipt identity (task id, claim
        # token, claim generation) is recorded exactly once in history. The
        # token comparison normalizes through str() because the receipt
        # stores the string form: a replay with the same non-string token
        # argument must still match its own recorded receipt.
        for event in manifest.get("history", []):
            if (
                isinstance(event, Mapping)
                and event.get("event") == DONE_PENDING_RECOVERY_EVENT
                and event.get("task_id") == task_id
                and event.get("token") == str(token)
                and event.get("generation") == claim.get("generation")
            ):
                return _outcome(
                    "blocked",
                    "precondition-unverified",
                    [
                        "duplicate done-pending-recovery receipt refused: a receipt with the same task id, token, and generation is already recorded",
                    ],
                    "repository-task",
                    identity,
                    claim_generation,
                    "preserve-and-reconcile",
                )
        # (6) Disposition dispatch: the closed disposition set. An unknown
        # disposition is refused naming the valid set.
        if disposition not in RECOVERY_DISPOSITIONS:
            return _outcome(
                "blocked",
                "precondition-unverified",
                [
                    f"unknown recovery disposition '{disposition}'",
                    f"valid dispositions: {', '.join(RECOVERY_DISPOSITIONS)}",
                ],
                "repository-task",
                identity,
                claim_generation,
                "preserve-and-reconcile",
            )
        retirement_conflict = self._retire_recovered_workers(manifest, task_id, claim, terminal)
        if retirement_conflict:
            return _outcome(
                "blocked",
                "precondition-unverified",
                retirement_conflict,
                "repository-task",
                identity,
                claim_generation,
                "preserve-and-reconcile",
            )
        if disposition == "defer":
            # The defer arm's gates run before any mutation: a refused defer
            # leaves the manifest byte-identical. (7) Backlog evidence: an
            # existing repository-relative file under the backlog directory,
            # normalized fail-closed through the shared path policy.
            backlog_value = backlog_evidence if isinstance(backlog_evidence, str) else None
            normalized_backlog = None
            if backlog_value and backlog_value.strip():
                try:
                    candidate = _safe_relative_path(self.repo_root, backlog_value)
                except ValueError:
                    candidate = None
                if candidate is not None and candidate.startswith("docs/history/backlog/") and (self.repo_root / candidate).is_file():
                    normalized_backlog = candidate
            if normalized_backlog is None:
                evidence = [
                    "defer requires backlog evidence: an existing repository-relative path under docs/history/backlog/ recording the deferred task's follow-up",
                ]
                if backlog_value:
                    evidence.append(
                        f"backlog evidence refused: '{backlog_value}' is not an existing repository-relative path under docs/history/backlog/"
                    )
                return _outcome(
                    "blocked",
                    "precondition-unverified",
                    evidence,
                    "repository-task",
                    identity,
                    claim_generation,
                    "preserve-and-reconcile",
                )
            # (8) Dependency ordering: defer is valid only for the next
            # provable incomplete task - the ordinal queue order is the only
            # machine-provable dependency signal in the manifest, and skipping
            # a provably incomplete predecessor would strand it behind a
            # terminal-ish status it can never recover from.
            incomplete = [candidate for candidate in sorted(manifest["tasks"].values(), key=_pending_sort_key) if not self._task_complete(candidate)]
            if not incomplete or incomplete[0].get("id") != task_id:
                ahead = str(incomplete[0].get("id")) if incomplete else "none"
                return _outcome(
                    "blocked",
                    "precondition-unverified",
                    [
                        f"defer refused: task '{task_id}' is not the next provable incomplete task",
                        f"dependency ordering: defer is valid only for the next provable incomplete task; task '{ahead}' is ahead of it in queue order",
                    ],
                    "repository-task",
                    identity,
                    claim_generation,
                    "preserve-and-reconcile",
                )
            # The defer mutations: the task is retired from the queue
            # (complete-for-selection, never relaunched) and the claim is
            # closed - a live claim on a non-progressed `deferred` task would
            # flip readiness to observe-worker. No generation bump: the
            # requeued-task re-authorization does not apply to a retired task.
            task["status"] = "deferred"
            claim["state"] = "closed"
            manifest.setdefault("history", []).append({
                "event": DONE_PENDING_RECOVERY_EVENT,
                "task_id": task_id,
                "token": str(token),
                "generation": claim.get("generation"),
                "disposition": disposition,
                "terminal_evidence": terminal,
                "backlog_evidence": bounded_evidence([normalized_backlog]),
            })
            # Shared post-acceptance check (the same discard-on-failure
            # discipline as the requeue arm): after the defer, the next
            # provable incomplete task in queue order is pending or None.
            incomplete = [candidate for candidate in sorted(manifest["tasks"].values(), key=_pending_sort_key) if not self._task_complete(candidate)]
            if incomplete and incomplete[0].get("status") != "pending":
                return _stale_claim_outcome(
                    identity,
                    claim_generation,
                    [
                        "recovery post-condition failed: the next provable incomplete task "
                        f"'{incomplete[0].get('id')}' is not pending after the defer; nothing was persisted",
                    ],
                )
            failure = self._persist_recovery_transition(manifest, "recover-done-pending defer")
            if failure is not None:
                return _stale_claim_outcome(identity, claim_generation, [failure])
            return _outcome(
                "success",
                "deferred",
                [
                    f"task={task_id}",
                    f"disposition={disposition}",
                    f"backlog_evidence={normalized_backlog}",
                    "done-pending-recovery receipt recorded with the bounded terminal evidence and the backlog evidence",
                    "task deferred: excluded from the incomplete selection, never relaunched; the run continues with the next provable task",
                ],
                "repository-task",
                identity,
                claim_generation,
                "continue-parent",
                actions=[],
                recovered_task=task_id,
                disposition=disposition,
            )
        if disposition == "abort":
            # The abort arm: the run ends. The same durable writes the
            # wedged-abort path makes (task aborted, claim aborted,
            # workflow_state aborted), the receipt appended, and the shared
            # post-acceptance validation skipped - the run is terminal, there
            # is no next provable task to prove. No generation bump.
            task["status"] = "aborted"
            claim["state"] = "aborted"
            manifest["workflow_state"] = "aborted"
            manifest.setdefault("history", []).append({
                "event": DONE_PENDING_RECOVERY_EVENT,
                "task_id": task_id,
                "token": str(token),
                "generation": claim.get("generation"),
                "disposition": disposition,
                "terminal_evidence": terminal,
            })
            failure = self._persist_recovery_transition(manifest, "recover-done-pending abort")
            if failure is not None:
                return _stale_claim_outcome(identity, claim_generation, [failure])
            return _abort_outcome(
                identity,
                claim_generation,
                [
                    f"task={task_id}",
                    f"disposition={disposition}",
                    "done-pending-recovery receipt recorded with the bounded terminal evidence",
                    "workflow aborted by the operator's explicit recovery disposition; preserve-and-stop",
                ],
                action_scope="repository-task",
                actions=[],
                recovered_task=task_id,
                disposition=disposition,
            )
        # The requeue arm: the shared task-to-pending rotation (dead-session
        # resume fields stripped), the claim closed, one generation bump so
        # the next claim mints a fresh policy token from the reconciled plan
        # section, and the immutable receipt. allowed_paths is never edited.
        self._reset_task_to_pending(task)
        claim["state"] = "closed"
        requeue_generation = int(manifest.get("generation", 0)) + 1
        manifest["generation"] = requeue_generation
        receipt: dict[str, Any] = {
            "event": DONE_PENDING_RECOVERY_EVENT,
            "task_id": task_id,
            "token": str(token),
            "generation": claim.get("generation"),
            "disposition": disposition,
            "terminal_evidence": terminal,
        }
        if backlog_evidence:
            # F1 fold: the requeue receipt carries backlog evidence only
            # through the same gate the defer arm uses - an existing
            # repository-relative path under docs/history/backlog/.
            normalized_requeue_backlog = None
            if isinstance(backlog_evidence, str) and backlog_evidence.strip():
                try:
                    candidate = _safe_relative_path(self.repo_root, backlog_evidence)
                except ValueError:
                    candidate = None
                if candidate is not None and candidate.startswith("docs/history/backlog/") and (self.repo_root / candidate).is_file():
                    normalized_requeue_backlog = candidate
            if normalized_requeue_backlog is None:
                return _outcome(
                    "blocked",
                    "precondition-unverified",
                    [
                        "requeue backlog_evidence refused: it must be an existing repository-relative path under docs/history/backlog/",
                    ],
                    "repository-task",
                    identity,
                    claim_generation,
                    "preserve-and-reconcile",
                )
            receipt["backlog_evidence"] = bounded_evidence(normalized_requeue_backlog)
        manifest.setdefault("history", []).append(receipt)
        # Post-acceptance check: the requeued state must be provable before
        # it persists - the next incomplete task in queue order is pending
        # (ours) or None (the run is otherwise complete). A failed check
        # discards every in-memory mutation: nothing is saved.
        incomplete = [candidate for candidate in sorted(manifest["tasks"].values(), key=_pending_sort_key) if not self._task_complete(candidate)]
        if incomplete and incomplete[0].get("status") != "pending":
            return _stale_claim_outcome(
                identity,
                claim_generation,
                [
                    "recovery post-condition failed: the next provable incomplete task "
                    f"'{incomplete[0].get('id')}' is not pending after the requeue; nothing was persisted",
                ],
            )
        failure = self._persist_recovery_transition(manifest, "recover-done-pending requeue")
        if failure is not None:
            return _stale_claim_outcome(identity, claim_generation, [failure])
        return _outcome(
            "success",
            "requeued",
            [
                f"task={task_id}",
                f"disposition={disposition}",
                f"generation={requeue_generation}",
                "done-pending-recovery receipt recorded with the bounded terminal evidence",
                "task requeued to pending; the next claim mints a fresh policy token from the reconciled plan section",
            ],
            "repository-task",
            identity,
            requeue_generation,
            "continue-parent",
            actions=[],
            recovered_task=task_id,
            disposition=disposition,
        )

    def _retire_recovered_workers(
        self,
        manifest: dict[str, Any],
        task_id: str,
        claim: Mapping[str, Any],
        terminal_evidence: list[str],
    ) -> list[str] | None:
        """Retire only workers whose immutable identity is the recovered claim."""
        claim_identity = (task_id, str(claim.get("token")), claim.get("generation"), claim.get("owner"))
        matched: list[dict[str, Any]] = []
        for worker in manifest.get("workers", {}).values():
            if not isinstance(worker, dict) or worker.get("task_id") != task_id or worker.get("state") == "terminal":
                continue
            worker_identity = (
                worker.get("task_id"),
                str(worker.get("claim_token")),
                worker.get("generation"),
                worker.get("claim_owner_id"),
            )
            if worker_identity != claim_identity:
                return [
                    f"recovery refused: non-terminal worker '{worker.get('worker_id')}' does not match the exact done-pending claim identity",
                ]
            matched.append(worker)
        observed_at = self.clock()
        for worker in matched:
            receipt_id = "done-pending-recovery-terminal-" + hashlib.sha256(
                f"{task_id}:{claim.get('token')}:{claim.get('generation')}:{worker.get('worker_id')}".encode("utf-8")
            ).hexdigest()[:20]
            receipt = {
                "receipt_id": receipt_id,
                "task_id": task_id,
                "claim_token": str(claim.get("token")),
                "claim_owner_id": str(claim.get("owner")),
                "generation": claim.get("generation"),
                "worker_id": worker.get("worker_id"),
                "provider_session_id": worker.get("provider_session_id"),
                "event": "terminal",
                "reason": "done-pending-recovery",
                "proof": {"kind": "operator-terminal-evidence", "verified": True, "evidence": terminal_evidence},
                "observed_at": observed_at,
            }
            worker.update(
                {
                    "state": "terminal",
                    "terminal_reason": "done-pending-recovery",
                    "last_receipt": {"status": "success", "outcome": "released", "event": "terminal", "receipt_id": receipt_id},
                    "receipt_metadata": receipt,
                    "reconciliation": {"status": "terminal", "observed_at": observed_at},
                }
            )
            capacity_entry = manifest.get("capacity", {}).get("entries", {}).get(worker.get("capacity_entry_id"))
            if isinstance(capacity_entry, dict):
                capacity_entry.update({"counts_toward_capacity": False, "state": "released"})
        return None

    def selftest(self) -> None:
        manifest = load_manifest(self.manifest_path)
        if manifest["workflow_state"] not in {"active", "terminal", "complete", "blocked", "aborted"}:
            raise AssertionError("invalid workflow state")
        self.authorize_action("push")

    # ------------------------------------------------------------------
    # Address fan-out authority (Step 3.3 file-affinity contract)
    # ------------------------------------------------------------------

    def record_address_fanout(self, transition: Mapping[str, Any]) -> dict[str, Any]:
        """Persist one address fan-out lifecycle transition under the manifest lock.

        ``runtime_state.json.address_fanout`` is the one authoritative live
        fan-out record: every launch, cancellation, acceptance, quarantine,
        and terminal subset outcome flows through this lock-held transition
        writer, which owns the monotonically increasing fan-out generation.
        The transition semantics are the pure reducer in
        ``execute_plan_address_fanout``; a quarantined receipt (closed,
        cancelled, superseded, aborted, or replaced attempt) never mutates
        machine state. Projections (``manifest.md`` and the sidecar
        ``extensions.address_fanout``) are rendered only by
        :meth:`finalize_address_fanout` from one lock-held snapshot.
        """

        # The fan-out helper is imported lazily so the driver keeps working
        # when staged alone by the activation path, which copies only the
        # three core runtime scripts into the loaded runtime directory.
        import execute_plan_address_fanout

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "address-fanout:conflict", action_scope="repository-write")
            return self._record_address_fanout_locked(execute_plan_address_fanout, transition)

    def _record_address_fanout_locked(self, address_fanout: Any, transition: Mapping[str, Any]) -> dict[str, Any]:
        manifest = load_manifest(self.manifest_path)
        record = manifest.get("address_fanout")
        generation = manifest.get("generation", 0)
        try:
            next_record, fanout_outcome = address_fanout.apply_transition(record, transition, clock=self.clock)
        except (TypeError, ValueError) as exc:
            return _outcome(
                "blocked",
                "malformed-result",
                [f"address fan-out transition rejected: {exc}"],
                "repository-write",
                "address-fanout:malformed",
                generation,
                "preserve-and-reconcile",
            )
        reason_code = str(fanout_outcome.get("reason_code", "malformed-result"))
        checkpoint_identity = str(fanout_outcome.get("checkpoint_identity", "address-fanout"))
        if not fanout_outcome.get("mutated"):
            status = "success" if fanout_outcome.get("status") == "success" else "blocked"
            outcome = _outcome(
                status,
                reason_code,
                list(fanout_outcome.get("evidence", ())),
                "repository-write",
                checkpoint_identity,
                generation,
                "continue-parent" if status == "success" else "preserve-and-reconcile",
                quarantined=bool(fanout_outcome.get("quarantined")),
            )
            if isinstance(record, Mapping):
                outcome["address_fanout"] = record
            return outcome
        manifest["address_fanout"] = next_record
        self._save(manifest)
        return _outcome(
            "success",
            reason_code,
            list(fanout_outcome.get("evidence", ())),
            "repository-write",
            checkpoint_identity,
            generation,
            "continue-parent",
            address_fanout_generation=next_record["generation"],
            quarantined=False,
            address_fanout=next_record,
        )

    def finalize_address_fanout(
        self,
        round_id: str,
        generation: int,
        manifest_projection_path: Path | str,
        sidecar_path: Path | str,
        projection_writer: Callable[[Path, str], None] | None = None,
        sidecar_writer: Callable[[Path, Mapping[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Render both fan-out projections from one lock-held machine-state snapshot.

        ``manifest.md`` and the sidecar ``extensions.address_fanout`` render
        from the same snapshot with the same fan-out generation; a stale
        generation cannot authorize the finalization (and with it the
        round's single address commit), and completion is never advertised
        when projection replacement fails.
        """

        # Lazily imported: see record_address_fanout.
        import execute_plan_address_fanout as address_fanout

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                return _mutation_unavailable(self, "address-fanout:finalize", action_scope="repository-write")
            manifest = load_manifest(self.manifest_path)
            record = manifest.get("address_fanout")
            generation_now = manifest.get("generation", 0)
            checkpoint_identity = f"address-fanout:{round_id}:finalize"

            def _blocked(reason_code: str, evidence: list[str]) -> dict[str, Any]:
                return _outcome(
                    "blocked",
                    reason_code,
                    evidence,
                    "repository-write",
                    checkpoint_identity,
                    generation_now,
                    "preserve-and-reconcile",
                    commit_authorized=False,
                )

            if not isinstance(record, Mapping) or record.get("round") != str(round_id):
                return _blocked("stale-attempt", ["no live address fan-out record for the round"])
            if record.get("status") != "active":
                return _blocked("stale-attempt", [f"address fan-out record is {record.get('status')}"])
            if generation != record.get("generation"):
                return _blocked(
                    "stale-attempt",
                    [f"generation {generation} does not identify the active fan-out generation {record.get('generation')}"],
                )
            manifest_text = address_fanout.render_manifest_projection(record)
            sidecar_payload = address_fanout.render_sidecar_projection(record)
            manifest_target = Path(manifest_projection_path)
            sidecar_target = Path(sidecar_path)
            write_text = projection_writer or self._write_projection_text
            write_payload = sidecar_writer or self._write_sidecar_extension
            try:
                write_text(manifest_target, manifest_text)
                write_payload(sidecar_target, sidecar_payload)
            except (OSError, ValueError, RuntimeError) as exc:
                return _blocked("projection-failed", [f"projection replacement failed: {exc}"])
            finalized_record = dict(record)
            finalized_record["status"] = "finalized"
            finalized_record["finalized"] = {
                "generation": record.get("generation"),
                "manifest_projection": str(manifest_target),
                "sidecar": str(sidecar_target),
            }
            manifest["address_fanout"] = finalized_record
            self._save(manifest)
            return _outcome(
                "success",
                "finalized",
                [f"fan-out projections rendered at generation {record.get('generation')}"],
                "repository-write",
                checkpoint_identity,
                generation_now,
                "continue-parent",
                commit_authorized=True,
                address_fanout_generation=record.get("generation"),
                address_fanout=finalized_record,
            )

    @staticmethod
    def _write_projection_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------
    # Budget-boundary watcher authority (canonical standing resume watcher)
    # ------------------------------------------------------------------

    def resume_watcher_snapshot(self) -> dict[str, Any]:
        """Lock-held read of the watcher-relevant machine state.

        The read-only observation acquires the manifest lock first; on
        persistent contention it still returns the on-disk state rather than
        blocking the watcher fire path, because a read cannot corrupt state
        and every mutating transition re-checks its fences under the lock.
        """

        with _manifest_lock(self.manifest_path, self.owner) as acquired:
            if not acquired:
                pass  # Read-only observation: fall through to the on-disk read.
            manifest = load_manifest(self.manifest_path)
            watcher = manifest.get("resume_watcher")
            return {
                "plan_slug": manifest.get("plan_slug"),
                "workflow_state": manifest.get("workflow_state"),
                "generation": int(manifest.get("generation", 0)),
                "progress_revision": int(manifest.get("progress_revision", 0)),
                "boundary_generation": int(manifest.get("boundary_generation", 0)),
                "resume_watcher": dict(watcher) if isinstance(watcher, Mapping) else None,
                "user_interrupt": manifest.get("user_interrupt"),
                "peer_resumed_at_epoch": float(manifest.get("peer_resumed_at_epoch", 0.0) or 0.0),
                "updated_at": float(manifest.get("updated_at", 0.0)),
                "repo_root": str(self.repo_root),
            }

    def _mark_peer_resumed(self) -> None:
        """Record a resume-path re-entry for the watcher peer fence.

        Only ``resume`` and ``continue`` operations write this field: a
        session re-entering the run after a watcher was scheduled is exactly
        the peer-resume stand-down signal, while construction, progress,
        interrupt, and checkpoint writes never trip the fence. Lock
        unavailability skips the mark quietly: a missed stand-down risk is
        carried by the watcher's other fences, and the fire path re-reads
        machine state anyway.
        """

        try:
            with _manifest_lock(self.manifest_path, self.owner) as acquired:
                if not acquired:
                    return
                manifest = load_manifest(self.manifest_path)
                manifest["peer_resumed_at_epoch"] = float(self.clock())
                self._save(manifest)
        except OSError:
            return

    @_locked_mutation
    def record_progress(self, evidence: Sequence[str] | None = None) -> dict[str, Any]:
        """Advance the monotonic semantic progress revision under the lock.

        The orchestrator records semantic progress after every checkpoint and
        done boundary, so a scheduled watcher's expected progress revision
        goes stale exactly when the work moved.
        """

        manifest = load_manifest(self.manifest_path)
        next_revision = int(manifest.get("progress_revision", 0)) + 1
        manifest["progress_revision"] = next_revision
        manifest.setdefault("history", []).append(
            {"event": "progress-recorded", "revision": next_revision, "evidence": bounded_evidence(list(evidence or ()))}
        )
        self._save(manifest)
        return _outcome(
            "success",
            "progress-recorded",
            [f"progress_revision={next_revision}"],
            "repository-write",
            "runtime:progress",
            manifest.get("generation", 0),
            "continue-parent",
            progress_revision=next_revision,
        )

    @_locked_mutation
    def reconcile_interruption(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Release an interrupted launch only after a fresh empty inventory witness.

        The receipt is bound to the exact blocked claim and is idempotent by
        caller-supplied key. No worktree state is inspected or modified here;
        the subsequent task commit boundary remains path-scoped.
        """
        manifest = load_manifest(self.manifest_path)
        key = payload.get("idempotency_key")
        task_id = str(payload.get("task_id", ""))
        claim_token = payload.get("claim_token")
        generation = payload.get("generation")
        if not isinstance(key, str) or not key.strip() or len(key) > 200:
            return _outcome("blocked", "malformed-result", ["idempotency_key must be a non-empty string of at most 200 characters"], "runtime", "runtime:reconcile-interruption", manifest.get("generation", 0), "preserve-and-reconcile")
        receipts = manifest.setdefault("interruption_reconciliations", {})
        prior = receipts.get(key)
        if isinstance(prior, Mapping):
            if (prior.get("task_id") != task_id or prior.get("claim_token") != claim_token
                    or prior.get("generation") != generation):
                return _outcome("blocked", "stale-attempt", ["idempotency_key was already consumed by a different claim identity"], "repository-task", f"{task_id}:reconcile-interruption", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
            return dict(prior.get("outcome", {}))
        task = manifest.get("tasks", {}).get(task_id)
        claim = manifest.get("claims", {}).get(task_id)
        if (not isinstance(task, Mapping) or task.get("status") != "blocked"
                or task.get("resume_allowed") is not False
                or not isinstance(claim, Mapping) or claim.get("state") != "blocked"
                or claim.get("token") != claim_token or claim.get("generation") != generation):
            return _outcome("blocked", "stale-claim", ["interruption reconciliation identity does not match the exact blocked claim"], "repository-task", f"{task_id}:reconcile-interruption", manifest.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        blocked = task.get("blocked_receipt")
        if not isinstance(blocked, Mapping) or blocked.get("reason_code") not in {"timeout", "parent-shutdown", "session-interrupted", "user-interruption"}:
            return _outcome("blocked", "malformed-result", ["blocked receipt is absent or not an eligible interruption"], "repository-task", f"{task_id}:reconcile-interruption", generation, "preserve-and-reconcile", resume_allowed=False)
        expected_reservation = f"{task_id}:{generation}:{claim.get('launch_id')}"
        reservations = manifest.get("capacity", {}).get("reservations", {})
        reservation = reservations.get(expected_reservation) if isinstance(reservations, Mapping) else None
        if (not isinstance(reservation, Mapping) or reservation.get("claim_token") != claim_token
                or reservation.get("generation") != generation or reservation.get("task_id") != task_id):
            return _outcome("blocked", "stale-claim", ["matching launch reservation is missing or does not match claim identity"], "repository-task", f"{task_id}:reconcile-interruption", generation, "preserve-and-reconcile", resume_allowed=False)
        # Reconcile provider state on a detached view with launch reservations
        # omitted. Other claims keep their reservations in the authoritative
        # manifest and still fence any subsequent launch through the normal
        # capacity transition.
        observed_manifest = copy.deepcopy(manifest)
        observed_manifest.setdefault("capacity", {})["reservations"] = {}
        target_worker_registered = any(
            worker.get("task_id") == task_id
            and worker.get("claim_token") == claim_token
            and worker.get("generation") == generation
            for worker in observed_manifest.get("workers", {}).values()
        )
        result = self.reconcile_worker_capacity(observed_manifest)
        target_worker_released = any(
            worker.get("task_id") == task_id
            and worker.get("claim_token") == claim_token
            and worker.get("generation") == generation
            and worker.get("state") == "terminal"
            and observed_manifest.get("capacity", {}).get("entries", {}).get(
                worker.get("capacity_entry_id"), {}
            ).get("counts_toward_capacity") is False
            for worker in observed_manifest.get("workers", {}).values()
        )
        observation_state = observed_manifest.get("capacity", {}).get("last_reconciliation", {}).get("status")
        exact_worker_cleanup_proven = target_worker_released if target_worker_registered else (
            result.get("status") == "available" and observation_state == "available"
        )
        if not exact_worker_cleanup_proven:
            outcome = _outcome("blocked", "cleanup-unverified", [f"fresh provider inventory did not prove the interrupted worker absent: {result.get('reason', result.get('status'))}"], "repository-task", f"{task_id}:reconcile-interruption", generation, "verify-owned-process-termination-and-retry-reconciliation", resume_allowed=False)
            task["resume_allowed"] = False
            task["blocked_receipt"] = {**dict(blocked), "reconciliation": outcome}
            self._save(manifest)
            return outcome
        manifest["workers"] = observed_manifest["workers"]
        manifest["capacity"]["entries"] = observed_manifest["capacity"]["entries"]
        manifest["capacity"]["last_reconciliation"] = observed_manifest["capacity"].get("last_reconciliation")
        reservations.pop(expected_reservation, None)
        claim["state"] = "replaced"
        claim["replacement_reason"] = "interruption-reconciled"
        task["status"] = "pending"
        task["resume_allowed"] = False
        for field in ("session_id", "blocked_receipt"):
            task.pop(field, None)
        outcome = _outcome("success", "interruption-reconciled", ["fresh provider inventory proved no owned worker remains", "matching launch reservation released", "worktree contents preserved for path-scoped task commit"], "repository-task", f"{task_id}:reconcile-interruption", generation, "continue-parent", task_id=task_id, idempotency_key=key)
        receipts[key] = {"task_id": task_id, "claim_token": claim_token, "generation": generation, "outcome": outcome}
        manifest.setdefault("history", []).append({"event": "interruption-reconciled", "task_id": task_id, "generation": generation, "idempotency_key": key})
        failure = self._persist_recovery_transition(manifest, "reconcile-interruption")
        if failure is not None:
            return _outcome("blocked", "recovery-postvalidation-failed", [failure], "repository-task", f"{task_id}:reconcile-interruption", generation, "preserve-and-reconcile", resume_allowed=False)
        return outcome

    @_locked_mutation
    def record_interrupt(self, timestamp: str | None = None) -> dict[str, Any]:
        """Persist ``user_interrupt`` under the lock, keeping workflow_state.

        A plain interrupt stays resumable: this operation records the
        ISO-8601 interrupt timestamp only and never changes
        ``workflow_state``. The standing resume watcher stands down when this
        field is newer than its scheduling epoch, so a latched old interrupt
        never trips a later watcher.
        """

        manifest = load_manifest(self.manifest_path)
        value = str(timestamp) if timestamp else datetime.fromtimestamp(self.clock()).astimezone().isoformat()
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            return _outcome(
                "blocked",
                "malformed-result",
                [f"user_interrupt must be an ISO-8601 timestamp: {exc}"],
                "repository-write",
                "runtime:interrupt",
                manifest.get("generation", 0),
                "preserve-and-reconcile",
            )
        manifest["user_interrupt"] = value
        manifest.setdefault("history", []).append({"event": "user-interrupt-recorded", "user_interrupt": value})
        self._save(manifest)
        return _outcome(
            "success",
            "interrupt-recorded",
            [f"user_interrupt={value}", "workflow_state unchanged"],
            "repository-write",
            "runtime:interrupt",
            manifest.get("generation", 0),
            "continue-parent",
            user_interrupt=value,
            workflow_state=manifest.get("workflow_state"),
            parsed_epoch=parsed.timestamp(),
        )

    @_locked_mutation
    def record_resume_watcher(self, transition: Mapping[str, Any]) -> dict[str, Any]:
        """Atomic watcher-receipt write: install, replace, or clear.

        The one lock-held writer for every watcher transition (schedule,
        replace, supersede, and no-schedule clear). Each transition carries
        compare-and-swap expectations on the pending watcher id, the manifest
        generation, and the current boundary generation; a stale transition
        is a blocked ``stale-attempt`` outcome with no mutation. A successful
        schedule records the superseded watcher id as the new receipt's
        ``replaces`` predecessor and bumps the boundary generation; a
        supersede clears the pending watcher and bumps it too.
        """

        # Schema owner: execute_plan_resume_watcher; the CAS stale
        # predicate is the one shared copy.
        import execute_plan_resume_watcher

        manifest = load_manifest(self.manifest_path)
        generation = int(manifest.get("generation", 0))
        boundary = int(manifest.get("boundary_generation", 0))
        current = manifest.get("resume_watcher")
        current_id = current.get("watcher_id") if isinstance(current, Mapping) else None
        if not isinstance(transition, Mapping):
            return self._watcher_blocked("malformed-result", ["watcher transition must be a mapping"], generation, current)
        action = transition.get("action")
        if execute_plan_resume_watcher.watcher_cas_stale(transition, current_id, generation, boundary):
            expected_id = transition.get("expected_watcher_id")
            expected_generation = transition.get("expected_generation")
            expected_boundary = transition.get("expected_boundary_generation")
            return self._watcher_blocked(
                "stale-attempt",
                [
                    "watcher compare-and-swap failed",
                    f"expected_watcher_id={expected_id}",
                    f"current_watcher_id={current_id}",
                    f"expected_generation={expected_generation}",
                    f"current_generation={generation}",
                    f"expected_boundary_generation={expected_boundary}",
                    f"current_boundary_generation={boundary}",
                ],
                generation,
                current,
            )
        if action == "schedule":
            receipt = dict(transition.get("receipt") or {})
            try:
                execute_plan_resume_watcher.validate_resume_watcher_receipt(receipt)
            except ValueError as exc:
                return self._watcher_blocked("malformed-result", [str(exc)], generation, current)
            receipt["replaces"] = current_id
            receipt["boundary_generation"] = boundary + 1
            manifest["resume_watcher"] = receipt
            manifest["boundary_generation"] = boundary + 1
            manifest.setdefault("history", []).append(
                {"event": "resume-watcher-scheduled", "watcher_id": receipt["watcher_id"], "replaces": current_id}
            )
            self._save(manifest)
            return _outcome(
                "success",
                "resume-watcher-scheduled",
                [f"watcher_id={receipt['watcher_id']}", f"replaces={current_id}"],
                "repository-write",
                f"resume-watcher:{receipt['watcher_id']}",
                generation,
                "continue-parent",
                resume_watcher=receipt,
                cas_applied=True,
            )
        if action == "supersede":
            manifest["resume_watcher"] = None
            manifest["boundary_generation"] = boundary + 1
            if current_id is not None:
                manifest.setdefault("history", []).append(
                    {"event": "resume-watcher-superseded", "watcher_id": current_id, "reason": str(transition.get("reason", "boundary-decision"))}
                )
            self._save(manifest)
            return _outcome(
                "success",
                "resume-watcher-cleared",
                [f"superseded_watcher_id={current_id}", f"reason={transition.get('reason', 'boundary-decision')}"],
                "repository-write",
                "resume-watcher:supersede",
                generation,
                "continue-parent",
                resume_watcher=None,
                superseded_watcher_id=current_id,
                cas_applied=True,
            )
        if action == "re-carrier":
            # The schedule arm's post-chain carrier rectification.
            # The install compare-and-swap stamps the identity the chain was
            # built to arm; when the launchd link then refuses, the receipt
            # must state the outcome before the schedule result returns.
            # The pending receipt stays installed (the pause chain still
            # owns the window; the manual command is named by the outcome):
            # only its ``armed_launchd`` record is replaced, with no
            # boundary bump - the fire fences keep comparing the same
            # window. The CAS predicate above fences a concurrent writer.
            receipt = manifest.get("resume_watcher")
            if not isinstance(receipt, Mapping) or receipt.get("watcher_id") != transition.get("expected_watcher_id"):
                return self._watcher_blocked("stale-attempt", ["watcher receipt changed before the carrier rectification"], generation, current)
            patch = transition.get("armed_launchd")
            if not isinstance(patch, Mapping) or "armed" not in patch:
                return self._watcher_blocked("malformed-result", ["carrier rectification requires an armed_launchd record"], generation, current)
            rectified = dict(receipt)
            rectified["armed_launchd"] = dict(patch)
            manifest["resume_watcher"] = rectified
            manifest.setdefault("history", []).append({
                "event": "resume-watcher-carrier-rectified",
                "watcher_id": rectified.get("watcher_id"),
                "reason": str(transition.get("reason", "launchd-arm-outcome")),
                "armed": patch.get("armed") is True,
            })
            self._save(manifest)
            return _outcome(
                "success",
                "resume-watcher-carrier-rectified",
                [f"watcher_id={rectified.get('watcher_id')}", f"armed={patch.get('armed') is True}"],
                "repository-write",
                f"resume-watcher:{rectified.get('watcher_id')}",
                generation,
                "continue-parent",
                resume_watcher=rectified,
                cas_applied=True,
            )
        return self._watcher_blocked("malformed-result", [f"unknown watcher transition action: {action}"], generation, current)

    @staticmethod
    def _watcher_blocked(reason_code: str, evidence: list[str], generation: int, current: Any) -> dict[str, Any]:
        return _outcome(
            "blocked",
            reason_code,
            evidence,
            "repository-write",
            "resume-watcher:cas",
            generation,
            "preserve-and-reconcile",
            resume_watcher=dict(current) if isinstance(current, Mapping) else None,
            cas_applied=False,
        )


    @staticmethod
    def _write_sidecar_extension(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: dict[str, Any] = {}
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("sidecar is not a JSON object; refusing to replace its projections")
            existing = loaded
        extensions = existing.setdefault("extensions", {})
        extensions["address_fanout"] = payload
        _safe_write_json(path, existing)


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
        archived_plan = Path(directory) / "docs/history/plans/completed/selftest.md"
        archived_plan.parent.mkdir(parents=True, exist_ok=True)
        archived_plan.write_text("# selftest plan\n\n- [x] task-1\n", encoding="utf-8")
        # Staged terminal protocol: the final stage refuses without a
        # conforming pre-archive gate receipt, so the selftest seeds one with
        # the same shape as the suite's seed_archive_gate helper (declared
        # destination equal to the archived path, digest over the archived
        # bytes, source at the absent active path).
        state = load_manifest(path)
        state["archive_gate"] = {
            "plan_path": "docs/history/plans/selftest.md",
            "declared_destination": "docs/history/plans/completed/selftest.md",
            "plan_digest": hashlib.sha256(archived_plan.read_bytes()).hexdigest(),
            "last_commit_sha": "abcdef1",
            "phase5_checklist": ["selftest"],
            "recorded_at": 1234.0,
        }
        _safe_write_json(path, state)
        terminal = driver.mark_terminal("docs/history/plans/completed/selftest.md", "abcdef1", ["selftest"])
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
    if not tasks:
        # A zero-task manifest would answer every later claim with a silent
        # success no-op while readiness and terminal refuse it: refuse the
        # seed itself instead of creating that wedge.
        raise ValueError("create operation requires at least one task")
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
        criteria = task.get("required_criteria")
        commands = task.get("verification_commands")
        if not isinstance(criteria, list) or not criteria or not isinstance(commands, list) or not commands:
            raise ValueError(f"create operation task {task.get('id', '<mapping-key>')} requires non-empty required_criteria and verification_commands")
    # The lock lease is independent of manifest existence: fencing the
    # exists-check, create, and owner write inside _manifest_lock makes a
    # concurrent create fail closed instead of last-writer-wins.
    with _manifest_lock(manifest_path, str(args.owner or f"create-{uuid.uuid4().hex}")) as acquired:
        if not acquired:
            raise ValueError(f"manifest creation is held by another owner: {manifest_path}")
        if manifest_path.exists():
            raise ValueError(f"manifest already exists; create refuses to overwrite: {manifest_path}")
        # Seeding canonicalizes: raw Files: entries persist as canonical
        # allowed_paths with persisted document ordinals; within-task
        # canonical duplicates are rejected here.
        manifest = create_manifest(manifest_path, plan_slug, tasks, repo_root=repo_root)
        manifest["evidence_enforcement"] = True
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


def _operation_readiness(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only readiness decision (requires ``--plan``): runs before the shared mutating dispatch; the driver is constructed with ``persist_construction=False`` and no adapter (an explicit ``--runtime`` is still resolved by the CLI beforehand), so owner backfill and capability receipts are never persisted at construction, the readiness decision itself contains no write path, and an already-owned manifest stays byte-identical across the operation."""

    driver = RuntimeDriver(
        args.manifest,
        plan_slug=args.plan_slug,
        owner=args.owner,
        repo_root=args.repo_root,
        persist_construction=False,
    )
    return driver.readiness(args.plan)


def _operation_reclaim(args: argparse.Namespace, adapter: Any | None = None) -> dict[str, Any]:
    """Lease-gated claim reclaim using the configured adapter inventory port."""

    driver = RuntimeDriver(
        args.manifest,
        plan_slug=args.plan_slug,
        adapter=adapter,
        owner=args.owner,
        repo_root=args.repo_root,
        persist_construction=False,
    )
    return driver.reclaim(args.task_id)


def _operation_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only first-failed-transition report: runs before the shared mutating dispatch with the same ``persist_construction=False``, adapter-free driver construction as readiness; diagnose performs no adapter I/O and contains no write path, so an already-owned manifest stays byte-identical across the operation."""

    driver = RuntimeDriver(
        args.manifest,
        plan_slug=args.plan_slug,
        owner=args.owner,
        repo_root=args.repo_root,
        persist_construction=False,
    )
    return driver.diagnose()


def _operation_recover_done_pending(args: argparse.Namespace, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Operator-invoked done-pending recovery (requires a JSON payload): runs before the shared mutating dispatch with the same ``persist_construction=False``, adapter-free driver construction as readiness; recovery performs no adapter I/O, and the locked recovery transition is the operation's single manifest write. The payload carries the task id, the claim token, the disposition, the bounded terminal evidence list, and the optional backlog evidence path for the defer disposition."""

    if not isinstance(payload, Mapping):
        raise ValueError("recover-done-pending operation requires a JSON object payload")
    task_id = str(payload.get("task_id") or "")
    token = payload.get("token")
    disposition = str(payload.get("disposition") or "")
    if not task_id.strip():
        raise ValueError("recover-done-pending payload requires a non-empty 'task_id'")
    if token is None or not str(token).strip():
        raise ValueError("recover-done-pending payload requires a non-empty 'token'")
    if not disposition.strip():
        raise ValueError("recover-done-pending payload requires a non-empty 'disposition'")
    driver = RuntimeDriver(
        args.manifest,
        plan_slug=args.plan_slug,
        owner=args.owner,
        repo_root=args.repo_root,
        persist_construction=False,
    )
    return driver.recover_done_pending(
        task_id,
        str(token),
        disposition,
        payload.get("terminal_evidence"),
        backlog_evidence=payload.get("backlog_evidence"),
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
                # cannot be evaluated at all: malformed, not merely failed.
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


def _watcher_operation(
    operation: str,
    payload: Mapping[str, Any],
    driver: "RuntimeDriver",
) -> dict[str, Any]:
    """Production invocation path for the standing resume watcher.

    One shared CLI handler in ``execute_plan_resume_watcher``
    carries the schedule / supersede / fire arms for both watcher
    boundaries; this wrapper supplies the runtime boundary's identity: the
    driver-backed adapter, the driver's compare-and-swap writer as the
    supersede sink, and the driver's plan slug as the schedule fallback.
    ``watcher-schedule`` records one budget-boundary decision from the
    probe report and runs the CLI fallback chain; ``watcher-supersede``
    clears a pending watcher; ``watcher-fire`` is the entry the automation
    prompt invokes: it evaluates the four stand-down checks and the fences
    against the pending receipt and clears the guard flag and fired marker
    only on a resume decision.
    """

    import execute_plan_resume_watcher as watcher

    def reconcile_before_fire() -> Mapping[str, Any]:
        snapshot = driver.refresh_manifest()
        reconciliation_payload = driver._interruption_reconciliation_payload(snapshot, "watcher")
        if reconciliation_payload is None:
            return _outcome("success", "no-interrupted-claim", ["no terminal interrupted claim requires reconciliation"], "parent-continuation", "watcher:reconcile-interruption", snapshot.get("generation", 0), "continue-parent")
        if reconciliation_payload.get("missing_claim"):
            return _outcome("blocked", "stale-claim", ["interrupted task has no durable claim"], "parent-continuation", f"{reconciliation_payload['task_id']}:reconcile-interruption", snapshot.get("generation", 0), "preserve-and-reconcile", resume_allowed=False)
        return driver.reconcile_interruption(reconciliation_payload)

    return watcher.run_cli_watcher_operation(
        operation.removeprefix("watcher-"),
        payload,
        adapter=watcher.RuntimeResumeWatcherAdapter(driver),
        supersede=driver.record_resume_watcher,
        outcome_factory=_outcome,
        identity_prefix="watcher",
        plan_slug=str(payload.get("plan_slug") or driver.plan_slug or ""),
        repo_root=str(driver.repo_root),
        reconcile_interruption=reconcile_before_fire,
    )


_PLANS_WATCHER_OPERATIONS = (
    "plans-watcher-schedule",
    "plans-watcher-supersede",
    "plans-watcher-fire",
    "plans-resume-marker",
    "plans-progress",
    "plans-interrupt",
    "plans-terminal",
)


def _plans_watcher_operation(
    operation: str,
    payload: Mapping[str, Any],
    repo_root: Path | str,
) -> dict[str, Any]:
    """Production invocation path for the plans authoring watcher.

    Manifest-free mirror of the ``watcher-*`` operations over the
    ``PlansAuthoringWatcherAdapter``: the authoring machine-state JSON at
    ``{tmp_dir}/plan-requirements-<slug>.json`` is the authority, so these
    operations take the payload ``state_path`` instead of ``--manifest``.
    One shared CLI handler in ``execute_plan_resume_watcher``
    carries the schedule / supersede / fire arms for both watcher
    boundaries; this wrapper supplies the authoring boundary's identity:
    the state-file adapter, the adapter's own compare-and-swap supersede
    sink, and the authoring boundary's fire default (the canonical guard
    flag path, so the fire's cleanup contract matches the
    runtime boundary instead of silently skipping it).
    ``plans-watcher-schedule`` records one budget-boundary decision and
    runs the same CLI fallback chain as the runtime boundary;
    ``plans-watcher-supersede`` clears a pending watcher under
    compare-and-swap; ``plans-watcher-fire`` is the automation prompt's
    fire entry over the authoring state; ``plans-resume-marker`` records a
    resume-path re-entry so a scheduled watcher stands down on the shared
    peer fence; ``plans-progress`` / ``plans-interrupt`` /
    ``plans-terminal`` drive the authoring loop's progress revision,
    user-interrupt fence, and completion, archival, or abort bookkeeping
    under the same shared lock. Without these operations the authoring
    fences were prose-only machinery no operator could invoke.
    """

    import execute_plan_resume_watcher as watcher

    state_path = str(payload.get("state_path") or "").strip()
    if not state_path:
        raise ValueError(f"{operation} requires payload state_path (the authoring machine-state JSON)")
    adapter = watcher.PlansAuthoringWatcherAdapter(state_path, repo_root=str(repo_root))
    kind = operation.removeprefix("plans-").removeprefix("watcher-")
    if kind == "resume-marker":
        return adapter.record_resume([str(item) for item in (payload.get("evidence") or ())])
    if kind == "progress":
        return adapter.record_progress([str(item) for item in (payload.get("evidence") or ())])
    if kind == "interrupt":
        return adapter.record_interrupt(payload.get("user_interrupt"))
    if kind == "terminal":
        return adapter.record_terminal(str(payload.get("kind") or ""))
    return watcher.run_cli_watcher_operation(
        kind,
        payload,
        adapter=adapter,
        supersede=adapter.compare_and_swap_supersede,
        outcome_factory=_outcome,
        identity_prefix="plans-watcher",
        plan_slug=str(payload.get("plan_slug") or ""),
        repo_root=str(repo_root),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--operation", choices=("create", "claim", "verify", "checkpoint", "done", "resume", "continue", "terminal", "precondition", "interrupt", "reconcile-interruption", "reserve-continuation", "worker-start", "recover-handoff", "progress", "readiness", "preflight", "reclaim", "diagnose", "recover-done-pending", "watcher-schedule", "watcher-supersede", "watcher-fire") + _PLANS_WATCHER_OPERATIONS)
    parser.add_argument("--predecessors-file", type=Path, help="predecessors JSON document for the manifest-free precondition operation")
    parser.add_argument("--input", help="JSON object payload (create, verify, checkpoint, done, interrupt, progress, terminal, recover-done-pending, and the watcher-* and plans-* operations; verify takes task_id and command_id; plans-watcher-schedule takes the FULL probe report as probe_report, or the payload itself, plus plan_path, plan_slug, and state_path; the classifier reads status, binding, pause_decision, and the binding limit's reset_at_epoch from limits[], so a subset payload classifies unknown and degrades to the report-only supersede)")
    parser.add_argument("--plan", help="plan file path for the readiness operation")
    parser.add_argument("--task-id", help="task id for the reclaim operation")
    parser.add_argument("--plan-slug")
    parser.add_argument("--owner")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--runtime")
    parser.add_argument("--prompt", default="continue execute-plan", help="worker prompt for continue/launch operations")
    parser.add_argument("--batch", action="store_true", help="opt the claim or continue operation into the batch implement launch protocol")
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
        elif args.operation in _PLANS_WATCHER_OPERATIONS:
            # Manifest-free authoring watcher operations: the
            # payload state_path names the authoring machine-state JSON, so
            # --manifest is not required and no runtime driver is built.
            pass
        elif args.manifest is None or args.operation is None:
            parser.error("--manifest and --operation are required unless --selftest is used (or --operation precondition with --predecessors-file)")
        if args.operation in ("readiness", "preflight") and args.plan is None:
            # Refuse before any driver construction so the manifest stays
            # byte-identical on this fail-closed argparse exit.
            parser.error("--plan is required for --operation readiness")
        if args.operation == "reclaim" and getattr(args, "task_id", None) is None:
            # Same fail-closed argparse exit as the readiness --plan gate.
            parser.error("--task-id is required for --operation reclaim")
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
        if args.operation == "readiness":
            # Read-only decision; _operation_readiness owns the write-free construction contract.
            result = _operation_readiness(args)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.operation == "preflight":
            # Read-only pre-launch preflight; the same write-free construction
            # contract as readiness: nothing is persisted, a failing preflight
            # leaves every claim and handoff retryable.
            driver = RuntimeDriver(
                args.manifest,
                plan_slug=args.plan_slug,
                owner=args.owner,
                repo_root=args.repo_root,
                persist_construction=False,
            )
            result = driver.preflight(args.plan)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.operation == "reclaim":
            # Lease-gated reclaim; _operation_reclaim owns the construction contract.
            result = _operation_reclaim(args, adapter=adapter)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.operation == "diagnose":
            # Read-only report; _operation_diagnose owns the write-free construction contract.
            result = _operation_diagnose(args)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.operation == "recover-done-pending":
            # Operator-invoked recovery; _operation_recover_done_pending owns
            # the construction contract and the payload mapping.
            result = _operation_recover_done_pending(args, payload)
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
        if args.operation in _PLANS_WATCHER_OPERATIONS:
            # Authoring watcher operations: manifest-free, the
            # adapter owns its own state-file lock; a malformed payload
            # fails closed through the shared handler below.
            result = _plans_watcher_operation(args.operation, payload, args.repo_root or Path.cwd())
            print(json.dumps(result, sort_keys=True))
            return 0
        driver = RuntimeDriver(
            args.manifest,
            plan_slug=args.plan_slug,
            adapter=adapter,
            profile=profile,
            owner=args.owner,
            repo_root=args.repo_root,
            persist_construction=True,
        )
        if args.operation == "claim":
            parallel_members = payload.get("parallel_group") if isinstance(payload, Mapping) else None
            if parallel_members is not None:
                # The parallel-group opt-in: --input carries the requested
                # member ids; the driver validates the full membership.
                if not isinstance(parallel_members, list) or not parallel_members or not all(isinstance(item, str) and item for item in parallel_members):
                    raise ValueError("parallel_group claim payload must be a non-empty list of task ids")
                result = driver.claim_parallel_group(parallel_members)
            else:
                result = driver.claim_next_task(batch=args.batch)
        elif args.operation == "verify":
            result = driver.capture_verification_evidence(str(payload.get("task_id", "")), str(payload.get("command_id", "")))
        elif args.operation == "checkpoint":
            result = driver.record_worker_checkpoint(payload)
        elif args.operation == "done":
            result = driver.record_done(payload)
        elif args.operation == "resume":
            result = driver.resume()
        elif args.operation == "continue":
            parallel_member = payload.get("parallel_member") if isinstance(payload, Mapping) else None
            if parallel_member is not None:
                # Launch one claimed member of a live parallel group.
                result = driver.launch_member_task(str(parallel_member), prompt=args.prompt)
            else:
                result = driver.continue_parent(prompt=args.prompt, batch=args.batch)
        elif args.operation == "interrupt":
            # User Interruption fence: persists user_interrupt under the
            # manifest lock while keeping workflow_state unchanged.
            result = driver.record_interrupt(payload.get("user_interrupt"))
        elif args.operation == "reconcile-interruption":
            result = driver.reconcile_interruption(payload)
        elif args.operation == "reserve-continuation":
            result = driver.reserve_continuation(payload)
        elif args.operation == "worker-start":
            result = driver.record_worker_start(payload)
        elif args.operation == "recover-handoff":
            result = driver.recover_ambiguous_handoff(payload)
        elif args.operation == "progress":
            # Semantic progress revision: the orchestrator records progress
            # after every checkpoint and done boundary.
            result = driver.record_progress(payload.get("evidence"))
        elif args.operation in ("watcher-schedule", "watcher-supersede", "watcher-fire"):
            # Standing resume watcher operations: the only
            # production invocation path for the watcher state machine.
            result = _watcher_operation(args.operation, payload, driver)
        else:
            result = driver.mark_terminal(
                archived_plan_path=str(payload.get("archived_plan_path", "")),
                last_commit_sha=str(payload.get("last_commit_sha", "")),
                phase5_checklist=payload.get("phase5_checklist"),
                stage=str(payload.get("stage", "final")),
                plan_path=str(payload.get("plan_path", "")),
                destination=str(payload.get("destination", "")),
                review_sidecar=str(payload.get("review_sidecar", "")),
                residual_policy=payload.get("residual_policy"),
            )
        print(json.dumps(result, sort_keys=True))
    except (AssertionError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        label = "selftest" if args.selftest else "operation"
        print(f"execute-plan runtime {label} failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
