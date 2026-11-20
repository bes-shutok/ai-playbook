#!/usr/bin/env python3
"""Manifest-free helpers retained for plans authoring and repository checks.

The execute-plan implementation route is host-native and sequential. This
module no longer owns worker manifests, claims, launch lifecycle, or recovery.
It keeps independently used authoring watcher, clocked-order, and Codex quota
wake CLI operations plus small compatibility helpers used by repository tooling.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import runtime_capabilities as capabilities


def _outcome(
    status: str,
    reason_code: str,
    evidence: list[str],
    action_scope: str,
    checkpoint_identity: str,
    generation: int,
    next_action: str,
    **extra: Any,
) -> dict[str, Any]:
    """Build the stable result envelope shared by retained CLI operations."""

    result = {
        "status": status,
        "reason_code": reason_code,
        "evidence": evidence,
        "action_scope": action_scope,
        "checkpoint_identity": checkpoint_identity,
        "generation": generation,
        "next_action": next_action,
    }
    result.update(extra)
    return result


_EVIDENCE_LIMIT_DIMENSIONS = (
    ("evidence criterion exceeds UTF-8 item byte limit", "item bytes"),
    ("evidence criteria exceed UTF-8 aggregate byte limit", "aggregate bytes"),
    ("evidence criteria exceed receipt item-count limit", "count"),
)
_EVIDENCE_PROOF_LINE = "limits are never raised silently without consumer proof"


def _evidence_limit_message(task_id: str, criteria: list[Any], dimension: str, bare_message: str) -> str:
    byte_counts = [len(item.encode("utf-8")) for item in criteria if isinstance(item, str)]
    total = sum(byte_counts)
    if dimension == "item bytes":
        offenders = [
            (len(item.encode("utf-8")), item)
            for item in criteria
            if isinstance(item, str)
            and len(item.encode("utf-8")) > capabilities.MAX_EVIDENCE_ITEM_BYTES
        ]
        details = "; ".join(
            f"{size} UTF-8 bytes, limit {capabilities.MAX_EVIDENCE_ITEM_BYTES}): {item}"
            for size, item in offenders
        )
        return (
            f"task '{task_id}': {bare_message} (over-cap criteria: {details}; split the criteria into "
            f"independently verifiable criteria preserving complete acceptance coverage; {_EVIDENCE_PROOF_LINE}"
        )
    if dimension == "aggregate bytes":
        return (
            f"task '{task_id}': {bare_message} ({total} UTF-8 bytes, limit {capabilities.MAX_EVIDENCE_BYTES}); "
            f"consolidate the criteria (or split them further) so the aggregate fits; {_EVIDENCE_PROOF_LINE}"
        )
    return (
        f"task '{task_id}': {bare_message}: {len(criteria)} criteria supplied; "
        f"consolidate the criteria so the count fits; {_EVIDENCE_PROOF_LINE}"
    )


def _named_evidence_limit_error(task_map: Mapping[str, Mapping[str, Any]], error: ValueError) -> ValueError:
    """Attribute an existing evidence-limit refusal to the task that caused it."""

    message = str(error)
    dimension = next((name for needle, name in _EVIDENCE_LIMIT_DIMENSIONS if needle in message), None)
    if dimension is None:
        return error
    for task_id in sorted(task_map):
        criteria = task_map[task_id].get("required_criteria", [])
        try:
            capabilities.evidence_criterion_ids(criteria)
        except ValueError as task_error:
            if str(task_error) == message:
                return ValueError(
                    _evidence_limit_message(
                        str(task_id),
                        list(criteria) if isinstance(criteria, (list, tuple)) else [],
                        dimension,
                        message,
                    )
                )
    return error


def _checkbox_flip_identity(content: str, *, checked: bool) -> str | None:
    marker = "- [x]" if checked else "- [ ]"
    if not content.startswith(marker):
        return None
    rest = content[len(marker):]
    return rest[1:] if rest.startswith(" ") else rest


def _diff_is_checkbox_marker_only(diff_text: str) -> bool:
    """Recognize a diff made solely of paired unchecked-to-checked flips."""

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
    return bool(removed or added) and sorted(removed) == sorted(added)


def _resolved_facts_dir(repo_root: Path, key: str) -> Path | None:
    try:
        import facts_paths
        raw = facts_paths.resolve_toml_key_raw(repo_root, key)
    except (ImportError, AttributeError):
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _safe_relative_path(repo_root: Path, value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("path must be non-empty and NUL-free")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or value.startswith(("~", "-")):
        raise ValueError("path escapes repository root")
    resolved = (repo_root / candidate).resolve()
    if resolved != repo_root and repo_root not in resolved.parents:
        raise ValueError("path escapes repository root")
    if value.endswith("/") or resolved.is_dir():
        raise ValueError(f"allowed path names a directory; list files explicitly instead of a directory prefix: {value}")
    return resolved.relative_to(repo_root).as_posix()


def _git_commit_matching_reference(repo_root: Path, reference: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", "--quiet", f"{reference}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _git_head_revision(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _artifact_clause_malformation(value: Any, field: str) -> str | None:
    """Describe a malformed artifact clause field value, naming the field."""

    if isinstance(value, str):
        return None if value else f"{field} must be a non-empty string"
    if isinstance(value, (list, tuple)):
        if not value:
            return f"{field} must be a non-empty list of non-empty strings"
        if any(not isinstance(clause, str) or not clause for clause in value):
            return f"{field} must be a list of non-empty strings"
        return None
    return f"{field} must be a non-empty string or a non-empty list of non-empty strings"


def _artifact_contains_malformation(contains: Any) -> str | None:
    """Describe a malformed artifact 'contains' value, naming the field."""

    if contains is None:
        return "contains must be a non-empty string or a non-empty list of non-empty strings"
    return _artifact_clause_malformation(contains, "contains")


def _artifact_must_not_contain_malformation(must_not_contain: Any) -> str | None:
    """Describe a malformed artifact 'must_not_contain' value, naming the field."""

    if must_not_contain is None:
        return None
    return _artifact_clause_malformation(must_not_contain, "must_not_contain")


def verify_preconditions(repo_root: Path | str, document: Mapping[str, Any]) -> dict[str, Any]:
    """Verify plan-declared repository-local predecessor evidence."""

    root = Path(repo_root).resolve()

    def malformed(message: str) -> dict[str, Any]:
        return _outcome("blocked", "precondition-unverified", [message], "repository-read", "precondition:verify", 0, "preserve-and-reconcile", resume_allowed=True, predecessors=[])

    if not root.is_dir():
        return malformed(f"repository root missing or not a directory: {root}")
    if not isinstance(document, Mapping):
        return malformed("malformed predecessors document: expected a JSON object mapping")
    if "predecessors" in document and not isinstance(document["predecessors"], (list, tuple)):
        return malformed("malformed predecessors document: 'predecessors' must be a list")
    predecessors = document.get("predecessors", [])
    head = _git_head_revision(root)
    diagnostics: list[str] = []
    evidence: list[str] = []
    per_predecessor: list[dict[str, Any]] = []

    for declaration in predecessors:
        ref = declaration.get("ref") if isinstance(declaration, Mapping) else None
        outcomes = declaration.get("outcomes") if isinstance(declaration, Mapping) else None
        label = ref if isinstance(ref, str) and ref.strip() else "<missing>"
        if not isinstance(ref, str) or not ref.strip() or not isinstance(outcomes, (list, tuple)) or not outcomes:
            diagnostics.append(f"malformed predecessor declaration: ref={label} requires a non-empty ref and a non-empty outcomes list")
            per_predecessor.append({"ref": label, "verified": False, "verified_by": None})
            continue
        verified_by = None
        attempted: list[str] = []
        malformed_decl = False
        for outcome in outcomes:
            if not isinstance(outcome, Mapping):
                malformed_decl = True
                attempted.append("malformed-outcome")
                continue
            kind = str(outcome.get("kind", ""))
            if kind not in {"history-ref", "ancestry", "artifact", "validator"}:
                malformed_decl = True
                attempted.append(f"unknown-kind {kind or '<missing>'}")
                continue
            if kind == "validator":
                attempted.append("validator (orchestrator-run; exit evidence in manifest.md)")
                continue
            target = outcome.get("value") or outcome.get("path")
            detail = str(target or "<missing>")
            if kind in {"history-ref", "ancestry"} and isinstance(target, str) and target.startswith("-"):
                malformed_decl = True
                attempted.append(f"{kind} {detail} (malformed declaration: leading-dash value)")
                continue
            if kind == "artifact":
                contains_fault = _artifact_contains_malformation(outcome.get("contains"))
                forbidden_fault = _artifact_must_not_contain_malformation(outcome.get("must_not_contain"))
                if not isinstance(outcome.get("path"), str) or contains_fault is not None or forbidden_fault is not None:
                    malformed_decl = True
                    faults = "".join(
                        f": {fault}" for fault in (contains_fault, forbidden_fault) if fault is not None
                    )
                    attempted.append(f"artifact {detail} (malformed declaration{faults})")
                    continue
            attempted.append(f"{kind} {detail}")
            matched = False
            if kind == "history-ref" and isinstance(target, str):
                matched = _git_commit_matching_reference(root, target)
            elif kind == "ancestry" and isinstance(target, str) and head:
                matched = _git_is_ancestor(root, target, head)
            elif kind == "artifact":
                file_text = None
                try:
                    safe_path = _safe_relative_path(root, str(outcome["path"]))
                    file_text = (root / safe_path).read_text(encoding="utf-8")
                except (OSError, ValueError):
                    file_text = None
                if file_text is None:
                    matched = False
                else:
                    declared = outcome["contains"]
                    required = list(declared) if isinstance(declared, (list, tuple)) else [declared]
                    missing = [clause for clause in required if clause not in file_text]
                    forbidden_declared = outcome.get("must_not_contain")
                    if forbidden_declared is None:
                        forbidden: list[str] = []
                    else:
                        forbidden = list(forbidden_declared) if isinstance(forbidden_declared, (list, tuple)) else [forbidden_declared]
                    hits = [clause for clause in forbidden if clause in file_text]
                    matched = not missing and not hits
                    if missing:
                        attempted[-1] += f" (missing required clause: {'; '.join(missing)})"
                    if hits:
                        attempted[-1] += f" (forbidden clause present: {'; '.join(hits)})"
            if matched and verified_by is None:
                verified_by = {"kind": kind, "target": str(target or "")}
        per_predecessor.append({"ref": ref, "verified": verified_by is not None, "verified_by": verified_by})
        if verified_by is not None:
            evidence.append(f"ref={ref} verified by {verified_by['kind']}")
        else:
            note = " (malformed declaration)" if malformed_decl else ""
            diagnostics.append(f"predecessor ref={ref} unverified{note}; outcomes tried: {', '.join(attempted)}")
    if diagnostics:
        return _outcome("blocked", "precondition-unverified", diagnostics, "repository-read", "precondition:verify", 0, "preserve-and-reconcile", resume_allowed=True, predecessors=per_predecessor)
    return _outcome("success", "completed", evidence or ["no predecessors declared"], "repository-read", "precondition:verify", 0, "continue-parent", predecessors=per_predecessor)


_PLANS_WATCHER_OPERATIONS = (
    "plans-watcher-schedule", "plans-watcher-supersede", "plans-watcher-fire",
    "plans-resume-marker", "plans-progress", "plans-interrupt", "plans-terminal",
    "budget-carrier-discharge",
)
_CLOCKED_ORDER_OPERATIONS = (
    "clocked-order-schedule", "clocked-order-cancel", "clocked-order-due", "clocked-order-discharge-on-fire",
    "clocked-order-begin-fire", "clocked-order-clear-fire", "clocked-order-migrate-carrier",
    "clocked-order-verify-successor",
)
# The distinct nonzero exit for a blocked clocked-order-begin-fire result
# (clocked-order-handoff-lease-live, clocked-order-terminal-state,
# clocked-order-refused-early-fire, clocked-order-unknown-order): the
# generated fire command chains the begin-fire leg to the ZCode launch with
# ``&&``, so only a nonzero exit stops the launch - a refused lease must
# start no session. Success still exits 0, and every other operation keeps
# its 0-or-1 contract (its consumer reads the printed JSON and decides).
CLOCKED_ORDER_BEGIN_FIRE_REFUSED_EXIT = 4
_CENSUS_OPERATION = "budget-carrier-census"
_CARRIER_LIVENESS_OPERATION = "carrier-liveness"
# The missed-fire grace window (plan
# 2026-11-12-maintenance-indefinite-operation-stop-gaps Task 4): a recorded
# fire time younger than this is never classified missed, because a fire
# that just happened may still be inside its survey turn and its store row
# may still lag the fire. Bounded default: two hours.
CARRIER_LIVENESS_GRACE_WINDOW_SECONDS = 2 * 60 * 60
_CODEX_QUOTA_WAKE_OPERATIONS = ("codex-quota-wake-schedule", "codex-quota-wake-fire", "codex-quota-wake-reconcile")


def _plans_watcher_operation(operation: str, payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher
    state_path = str(payload.get("state_path") or "").strip()
    if not state_path:
        raise ValueError(f"{operation} requires payload state_path (the authoring machine-state JSON)")
    adapter = watcher.PlansAuthoringWatcherAdapter(state_path, repo_root=str(repo_root))
    kind = (
        "carrier-discharge"
        if operation == "budget-carrier-discharge"
        else operation.removeprefix("plans-").removeprefix("watcher-")
    )
    if kind == "resume-marker":
        return adapter.record_resume([str(item) for item in (payload.get("evidence") or ())])
    if kind == "progress":
        return adapter.record_progress([str(item) for item in (payload.get("evidence") or ())])
    if kind == "interrupt":
        return adapter.record_interrupt(payload.get("user_interrupt"))
    if kind == "terminal":
        return adapter.record_terminal(str(payload.get("kind") or ""))
    if kind == "carrier-discharge":
        return watcher.budget_carrier_discharge_for_state(
            state_path,
            launchd_root=payload.get("launchd_root"),
            runtime_root=payload.get("runtime_root"),
        )
    return watcher.run_cli_watcher_operation(
        kind, payload, adapter=adapter, supersede=adapter.compare_and_swap_supersede,
        outcome_factory=_outcome, identity_prefix="plans-watcher",
        plan_slug=str(payload.get("plan_slug") or ""), repo_root=str(repo_root),
    )


def _clocked_order_operation(
    operation: str,
    payload: Mapping[str, Any],
    repo_root: Path | str,
    session_id: str | None = None,
    launcher_exit_code: int | None = None,
) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher
    root = Path(repo_root or Path.cwd()).resolve()
    ledger_path = payload.get("ledger_path")
    payload_home = payload.get("payload_home")
    if not ledger_path or not payload_home:
        state_dir = _resolved_facts_dir(root, "maintenance_state_dir") or root / ".ai-playbook" / "maintenance"
        ledger_path = ledger_path or state_dir / "clocked-orders.json"
        payload_home = payload_home or state_dir / "clocked-order-payloads"
    merged_payload = dict(payload)
    if session_id is not None:
        # The explicit runtime-context identity input: the headless session
        # passes its own id here (the launchd shell never discharges an
        # order); the flag outranks any payload-carried value.
        merged_payload["session_id"] = str(session_id)
    if launcher_exit_code is not None:
        # The explicit launcher exit code operand (the fire wrapper's clear
        # leg): merged per the --session-id precedent; absent, the payload
        # carries no key and the clear records no launch-failed event.
        merged_payload["launcher_exit_code"] = int(launcher_exit_code)
    ledger = watcher.ClockedOrderLedger(ledger_path, payload_home, repo_root=str(root))
    return watcher.run_clocked_order_operation(
        operation.removeprefix("clocked-order-"), merged_payload, repo_root=str(root), ledger=ledger
    )


def _codex_quota_wake_operation(payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher

    root = Path(repo_root or Path.cwd()).expanduser().resolve()
    state_dir = _resolved_facts_dir(root, "maintenance_state_dir") or root / ".ai-playbook" / "maintenance"
    return watcher.CodexQuotaWakeScheduler(
        state_dir=state_dir,
        repo_root=root,
        schedule_guard=lambda wake: _codex_quota_wake_schedule_guard(root, wake),
    ).schedule(payload)


def _codex_quota_wake_state_guard(root: Path, wake: Mapping[str, Any]) -> Mapping[str, Any]:
    state_path = root / ".ai-playbook" / "scheduler-state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ready": False, "reason": "state-unreadable", "detail": str(exc)}
    if not isinstance(state, Mapping):
        return {"ready": False, "reason": "state-unreadable"}
    cycle_gate = state.get("authoring_cycle_gate")
    if isinstance(cycle_gate, Mapping) and cycle_gate.get("gate"):
        return {"ready": False, "reason": "stop"}
    if state.get("survey_only"):
        return {"ready": False, "reason": "survey-only-stop"}
    if state.get("alert") is not None:
        return {"ready": False, "reason": "safety-hold"}
    target = str(wake.get("target") or "")
    kind = str(wake.get("kind") or "")
    pending = state.get("pending_dispatch")
    if not isinstance(pending, Mapping):
        return {"ready": False, "reason": "empty-queue"}
    if pending.get("target") != target or pending.get("kind") != kind:
        return {"ready": False, "reason": "target-changed", "target": target}
    relative = Path(target)
    if relative.is_absolute() or ".." in relative.parts or any(part == "completed" for part in relative.parts):
        return {"ready": False, "reason": "target-changed", "target": target}
    target_path = (root / relative).resolve()
    try:
        target_path.relative_to(root.resolve())
    except ValueError:
        return {"ready": False, "reason": "target-changed", "target": target}
    if not target_path.is_file():
        return {"ready": False, "reason": "target-changed", "target": target}
    return {"ready": True, "target": target, "kind": kind}


def _codex_quota_wake_quota_report(root: Path, wake: Mapping[str, Any]) -> Mapping[str, Any]:
    probe = root / "scripts" / "quota_window_probe.py"
    env = dict(os.environ)
    env["CODEX_HOME"] = str(wake.get("codex_home") or "")
    codex_executable = Path(str(wake.get("codex_executable") or ""))
    if not codex_executable.is_absolute() or not codex_executable.is_file():
        raise ValueError("captured Codex executable is unavailable")
    path_entries = [str(codex_executable.parent)]
    interpreter = str(wake.get("codex_interpreter") or "").strip()
    if interpreter:
        interpreter_path = Path(interpreter)
        if interpreter_path.is_absolute():
            path_entries.append(str(interpreter_path.parent))
    path_entries.extend([os.defpath, env.get("PATH", "")])
    env["PATH"] = os.pathsep.join(entry for entry in path_entries if entry)
    result = subprocess.run(
        [sys.executable, str(probe), "--runtime", "codex"], cwd=root, env=env,
        capture_output=True, text=True, timeout=60, check=False,
    )
    # The probe deliberately returns 1 for every non-pause report, including
    # a valid continue report; other exit codes are failures.
    if result.returncode not in (0, 1):
        raise ValueError(f"quota probe exited {result.returncode}")
    report = json.loads(result.stdout)
    if (
        not isinstance(report, Mapping)
        or report.get("runtime") != "codex"
        or report.get("status") != "ok"
        or not isinstance(report.get("limits"), list)
    ):
        raise ValueError("quota state is unusable")
    return report


def _codex_quota_wake_schedule_guard(root: Path, wake: Mapping[str, Any]) -> Mapping[str, Any]:
    before = _codex_quota_wake_state_guard(root, wake)
    if not before.get("ready"):
        return before
    try:
        report = _codex_quota_wake_quota_report(root, wake)
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"ready": False, "reason": "quota-state-unusable", "detail": str(exc)}
    primary = next((row for row in report["limits"] if isinstance(row, Mapping) and row.get("kind") == "primary"), None)
    reset = primary.get("reset_at_epoch") if isinstance(primary, Mapping) else None
    if report.get("binding") != "primary" or report.get("pause_decision") != "pause":
        return {"ready": False, "reason": "primary-pause-not-current", "target": wake.get("target")}
    if isinstance(reset, bool) or not isinstance(reset, (int, float)) or int(reset) != int(wake.get("reset_at_epoch") or 0):
        return {"ready": False, "reason": "primary-reset-changed", "reset_at_epoch": reset, "target": wake.get("target")}
    after = _codex_quota_wake_state_guard(root, wake)
    if not after.get("ready"):
        return after
    return {"ready": True, "target": wake["target"], "kind": wake["kind"], "quota_report": report}


def _codex_quota_wake_fire_guard(root: Path, wake: Mapping[str, Any]) -> Mapping[str, Any]:
    """Re-read the maintenance target and primary quota immediately before queueing."""
    before = _codex_quota_wake_state_guard(root, wake)
    if not before.get("ready"):
        return before
    target = str(wake.get("target") or "")
    try:
        report = _codex_quota_wake_quota_report(root, wake)
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        reason = "quota-state-unusable" if "quota state is unusable" in str(exc) else "quota-probe-unavailable"
        return {"ready": False, "reason": reason, "detail": str(exc)}
    primary = next((row for row in report["limits"] if isinstance(row, Mapping) and row.get("kind") == "primary"), None)
    reset = primary.get("reset_at_epoch") if isinstance(primary, Mapping) else None
    if isinstance(reset, bool) or not isinstance(reset, (int, float)) or reset <= 0:
        return {"ready": False, "reason": "quota-state-unusable"}
    if report.get("binding") != "primary":
        return {"ready": False, "reason": "secondary-quota-binding", "reset_at_epoch": int(reset), "target": target}
    decision = report.get("pause_decision")
    if decision == "pause":
        reason = "primary-quota-paused"
        if int(reset) != int(wake.get("reset_at_epoch") or 0):
            reason = "primary-reset-changed"
        return {"ready": False, "reason": reason, "reset_at_epoch": int(reset), "target": target}
    if decision == "wait-for-reset" and report.get("status") == "ok":
        after = _codex_quota_wake_state_guard(root, wake)
        if not after.get("ready"):
            return after
        return {
            "ready": False,
            "reason": "primary-quota-wait-for-reset",
            "reset_at_epoch": int(reset),
            "target": target,
        }
    if decision != "continue":
        return {"ready": False, "reason": "quota-state-unusable", "reset_at_epoch": int(reset), "target": target}
    after = _codex_quota_wake_state_guard(root, wake)
    if not after.get("ready"):
        return after
    return {"ready": True, "target": target, "reset_at_epoch": int(reset), "quota_report": report}


def _codex_quota_wake_fire_operation(payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher

    root = Path(repo_root or Path.cwd()).expanduser().resolve()
    state_dir = _resolved_facts_dir(root, "maintenance_state_dir") or root / ".ai-playbook" / "maintenance"

    scheduler = watcher.CodexQuotaWakeScheduler(
        state_dir=state_dir,
        repo_root=root,
        fire_guard=lambda wake: _codex_quota_wake_fire_guard(root, wake),
        pre_queue_guard=lambda wake: _codex_quota_wake_fire_guard(root, wake),
    )
    return scheduler.fire(payload)


def _codex_quota_wake_reconcile_operation(payload: Mapping[str, Any]) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher

    return watcher.reconcile_codex_quota_wake_delivery(
        str(payload.get("receipt_path") or ""),
        str(payload.get("continuation") or ""),
        str(os.environ.get("CODEX_THREAD_ID") or ""),
    )


def _carrier_liveness_verdict(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    result = {"status": status, "reason": reason}
    result.update(extra)
    return result


def _carrier_liveness_epoch_from_iso(value: str) -> float | None:
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.timestamp()


def _carrier_liveness_parent_listing(db_path: Path, automation_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Read the recorded parent's listing row from the task-index store with
    maintenance_fire_outcomes.py's conventions (the mode=ro URI connect, then
    the same missing-database / db-error / missing-table / missing-columns
    unknown family; an absent parent row is parent-automation-absent).
    Returns (listing, None) on success or (None, unknown-verdict)."""
    path = Path(db_path)
    if not path.is_file():
        return None, _carrier_liveness_verdict("unknown", "missing-database", db_path=str(db_path))
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % path.resolve().as_posix(), uri=True)
    except sqlite3.Error as exc:
        return None, _carrier_liveness_verdict("unknown", "db-error", db_path=str(db_path), detail=str(exc))
    try:
        try:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(automations)").fetchall()}
        except sqlite3.Error as exc:
            return None, _carrier_liveness_verdict("unknown", "db-error", db_path=str(db_path), detail=str(exc))
        if not columns:
            return None, _carrier_liveness_verdict("unknown", "missing-table", table="automations")
        import maintenance_fire_outcomes as fire_outcomes
        required = fire_outcomes.REQUIRED_AUTOMATION_COLUMNS | {"last_run_at"}
        if not required.issubset(columns):
            return None, _carrier_liveness_verdict(
                "unknown", "missing-columns", table="automations",
                missing=sorted(required - columns),
            )
        try:
            row = conn.execute(
                "SELECT last_run_at, enabled, lifecycle_status FROM automations"
                " WHERE automation_id = ?",
                (automation_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            return None, _carrier_liveness_verdict("unknown", "db-error", db_path=str(db_path), detail=str(exc))
    finally:
        conn.close()
    if row is None:
        return None, _carrier_liveness_verdict("unknown", "parent-automation-absent", automation_id=automation_id)
    last_run_at, enabled, lifecycle_status = row
    listing = {
        # lastRunAt appears in the listing only after the first run; a
        # non-numeric cell reads the same as an absent one.
        "last_run_at_epoch_ms": last_run_at if isinstance(last_run_at, (int, float)) and not isinstance(last_run_at, bool) else None,
        "parent_enabled": bool(enabled) if isinstance(enabled, int) else None,
        "parent_lifecycle_status": lifecycle_status if isinstance(lifecycle_status, str) else None,
    }
    return listing, None


ZERO_TURN_CENSUS_LOOKBACK_SECONDS = 48 * 60 * 60


def _zero_turn_census_member(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    """Build the additive ``zero_turn_census`` verdict member; the member is
    always present on every carrier-liveness verdict, warning-only, and its
    consumer (a survey turn, report-only) decides."""
    result = {"status": status, "reason": reason, "warnings": [], "markers": []}
    result.update(extra)
    return result


def _zero_turn_census_load_facts(facts_path: Path) -> dict[str, Any]:
    """Mirror scripts/tool_runtime_stats.py's ``load_facts``: parse the
    opening TOML fence of the facts document; a missing file resolves to no
    facts (an absent-data fallback, never a wrong store)."""
    import tomllib

    try:
        text = facts_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Absent data and undecodable bytes both resolve to no facts (the
        # census stays warning-only; a malformed fence degrades the same
        # way instead of losing the whole verdict).
        return {}
    import re as _re

    match = _re.search(r"```toml\s*\n(.*?)```", text, _re.DOTALL)
    if not match:
        return {}
    try:
        return tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError:
        # A malformed TOML fence resolves to no facts (the census stays
        # warning-only; the tool_runtime_stats adapter's fail-open arm
        # covers absent data, and a malformed fence degrades the same way
        # instead of losing the whole verdict).
        return {}


def _zero_turn_census_session_store(payload: Mapping[str, Any], root: Path) -> tuple[Path | None, str | None]:
    """Resolve the session store: the explicit ``session_db_path`` payload
    key wins (the live store is never read when the key is present), then
    the facts document's ``session_store_path`` key, then the home default;
    an unresolvable store yields the census unknown marker."""
    explicit = payload.get("session_db_path")
    if explicit is not None and str(explicit).strip():
        return Path(str(explicit)).expanduser(), None
    facts = _zero_turn_census_load_facts(root / ".ai-playbook" / "facts.md")
    from_facts = facts.get("session_store_path")
    if from_facts:
        return Path(str(from_facts)).expanduser(), None
    home_default = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
    if home_default.is_file():
        return home_default, None
    return None, "unresolvable-session-store"


def _zero_turn_session_content_after(conn: "sqlite3.Connection", session_id: str, after_ms: int) -> bool:
    """Content-bearing read: an assistant record created after ``after_ms``
    with text parts (the ``part`` table joined on ``message_id``) or output
    tokens above zero (``model_usage`` completed after the same cutoff)."""
    try:
        messages = conn.execute(
            "SELECT id, data FROM message WHERE session_id = ? AND time_created > ?",
            (session_id, after_ms),
        ).fetchall()
    except sqlite3.Error:
        return False
    for message_id, data in messages:
        try:
            record = json.loads(data) if isinstance(data, (str, bytes)) else {}
        except (ValueError, TypeError):
            record = {}
        if not isinstance(record, Mapping) or record.get("role") != "assistant":
            continue
        try:
            parts = conn.execute(
                "SELECT data FROM part WHERE message_id = ?", (message_id,)
            ).fetchall()
        except sqlite3.Error:
            parts = []
        for (part_data,) in parts:
            try:
                part_record = json.loads(part_data) if isinstance(part_data, (str, bytes)) else {}
            except (ValueError, TypeError):
                part_record = {}
            if (
                isinstance(part_record, Mapping)
                and part_record.get("type") == "text"
                and str(part_record.get("text") or "").strip()
            ):
                return True
    try:
        usage = conn.execute(
            "SELECT 1 FROM model_usage WHERE session_id = ? AND completed_at > ?"
            " AND output_tokens > 0 LIMIT 1",
            (session_id, after_ms),
        ).fetchone()
    except sqlite3.Error:
        usage = None
    return usage is not None


def _zero_turn_census_operation(payload: Mapping[str, Any], root: Path, now_epoch: float) -> dict[str, Any]:
    """The fired-but-zero-turn carrier census arm (plan
    2026-11-13-errored-zero-turn-carrier-recovery Task 1).

    Reads failed ``automation_runs`` rows inside the lookback (the
    ``lookback_seconds`` payload key, default
    ``ZERO_TURN_CENSUS_LOOKBACK_SECONDS`` = 48 hours, bounded on
    ``automation_runs.created_at``), joins each to its ``tasks`` row by
    ``tasks.task_id = automation_runs.session_id``, and warns for a run
    whose linked task row reads ``task_status`` ``error`` and whose session
    holds no content-bearing assistant record created after the run's
    ``created_at`` (the witnessed conjunction: the task-status half of the
    warning contract is required, not the task row's mere presence).
    Read-only: every connection opens
    ``file:...?mode=ro`` with ``uri=True`` and nothing is written; every
    query wraps ``sqlite3.Error`` into the verdict, never raising, so the
    census stays warning-only with exit 0."""
    import maintenance_fire_outcomes as fire_outcomes

    task_db_path = fire_outcomes.resolve_db_path(payload.get("db_path"))
    if not task_db_path.is_file():
        return _zero_turn_census_member("unknown", "missing-database", db_path=str(task_db_path))
    raw_lookback = payload.get("lookback_seconds")
    if raw_lookback is None:
        lookback_seconds = ZERO_TURN_CENSUS_LOOKBACK_SECONDS
    elif isinstance(raw_lookback, (int, float)) and not isinstance(raw_lookback, bool) and raw_lookback >= 0:
        lookback_seconds = float(raw_lookback)
    else:
        raise ValueError("carrier-liveness lookback_seconds must be a non-negative number of seconds")
    cutoff_ms = int((now_epoch - lookback_seconds) * 1000)
    try:
        task_conn = sqlite3.connect("file:%s?mode=ro" % task_db_path.resolve().as_posix(), uri=True)
    except sqlite3.Error as exc:
        return _zero_turn_census_member("unknown", "db-error", db_path=str(task_db_path), detail=str(exc))
    runs: list[tuple] = []
    titles: dict[str, str] = {}
    try:
        try:
            run_columns = {row[1] for row in task_conn.execute("PRAGMA table_info(automation_runs)").fetchall()}
            task_columns = {row[1] for row in task_conn.execute("PRAGMA table_info(tasks)").fetchall()}
            automation_columns = {row[1] for row in task_conn.execute("PRAGMA table_info(automations)").fetchall()}
        except sqlite3.Error as exc:
            return _zero_turn_census_member("unknown", "db-error", db_path=str(task_db_path), detail=str(exc))
        required_run = {"run_id", "automation_id", "session_id", "created_at", "scheduled_at", "outcome"}
        if not run_columns:
            return _zero_turn_census_member("unknown", "missing-table", table="automation_runs", db_path=str(task_db_path))
        if not required_run.issubset(run_columns):
            return _zero_turn_census_member(
                "unknown", "missing-columns", table="automation_runs",
                missing=sorted(required_run - run_columns), db_path=str(task_db_path),
            )
        if not task_columns:
            return _zero_turn_census_member("unknown", "missing-table", table="tasks", db_path=str(task_db_path))
        if not {"task_id", "task_status"}.issubset(task_columns):
            return _zero_turn_census_member(
                "unknown", "missing-columns", table="tasks",
                missing=sorted({"task_id", "task_status"} - task_columns), db_path=str(task_db_path),
            )
        if automation_columns and {"automation_id", "title"}.issubset(automation_columns):
            # The title join is best-effort: an automations table without a
            # title column still censuses (the warning row's title reads
            # None), the warning itself never depending on the join.
            try:
                titles = {
                    row[0]: row[1]
                    for row in task_conn.execute("SELECT automation_id, title FROM automations").fetchall()
                    if isinstance(row[0], str)
                }
            except sqlite3.Error as exc:
                return _zero_turn_census_member("unknown", "db-error", db_path=str(task_db_path), detail=str(exc))
        try:
            runs = task_conn.execute(
                "SELECT run_id, automation_id, session_id, created_at, scheduled_at"
                " FROM automation_runs WHERE outcome = 'failed' AND created_at >= ?",
                (cutoff_ms,),
            ).fetchall()
            task_statuses = {
                row[0]: row[1]
                for row in task_conn.execute("SELECT task_id, task_status FROM tasks").fetchall()
                if isinstance(row[0], str)
            }
        except sqlite3.Error as exc:
            return _zero_turn_census_member("unknown", "db-error", db_path=str(task_db_path), detail=str(exc))
    finally:
        task_conn.close()

    session_db_path, store_reason = _zero_turn_census_session_store(payload, root)
    if session_db_path is None:
        return _zero_turn_census_member("unknown", store_reason or "unresolvable-session-store")
    if not session_db_path.is_file():
        return _zero_turn_census_member("unknown", "missing-database", db_path=str(session_db_path))
    try:
        session_conn = sqlite3.connect("file:%s?mode=ro" % session_db_path.resolve().as_posix(), uri=True)
    except sqlite3.Error as exc:
        return _zero_turn_census_member("unknown", "db-error", db_path=str(session_db_path), detail=str(exc))
    warnings: list[dict[str, Any]] = []
    markers: list[str] = []
    try:
        try:
            message_count_columns = {row[1] for row in session_conn.execute("PRAGMA table_info(message)").fetchall()}
            part_columns = {row[1] for row in session_conn.execute("PRAGMA table_info(part)").fetchall()}
            usage_columns = {row[1] for row in session_conn.execute("PRAGMA table_info(model_usage)").fetchall()}
        except sqlite3.Error as exc:
            return _zero_turn_census_member("unknown", "db-error", db_path=str(session_db_path), detail=str(exc))
        if not message_count_columns:
            return _zero_turn_census_member("unknown", "missing-table", table="message", db_path=str(session_db_path))
        if not {"id", "session_id", "time_created", "data"}.issubset(message_count_columns):
            return _zero_turn_census_member(
                "unknown", "missing-columns", table="message",
                missing=sorted({"id", "session_id", "time_created", "data"} - message_count_columns),
                db_path=str(session_db_path),
            )
        if part_columns and not {"message_id", "data"}.issubset(part_columns):
            return _zero_turn_census_member(
                "unknown", "missing-columns", table="part",
                missing=sorted({"message_id", "data"} - part_columns), db_path=str(session_db_path),
            )
        if usage_columns and not {"session_id", "completed_at", "output_tokens"}.issubset(usage_columns):
            return _zero_turn_census_member(
                "unknown", "missing-columns", table="model_usage",
                missing=sorted({"session_id", "completed_at", "output_tokens"} - usage_columns),
                db_path=str(session_db_path),
            )
        for run_id, automation_id, session_id, created_at, scheduled_at in runs:
            if not isinstance(session_id, str) or not session_id.strip():
                markers.append("missing-session|run=%s" % (run_id,))
                continue
            # The missing-task branch (the run-to-task join is
            # tasks.task_id = automation_runs.session_id): a failed run
            # inside the lookback with no task row warns nothing and marks.
            if session_id not in task_statuses:
                markers.append("missing-task|run=%s|session=%s" % (run_id, session_id))
                continue
            # The task-status conjunction: the warning contract requires the
            # linked task row to read task_status error, so a failed run
            # whose task row carries any other status warns nothing.
            if task_statuses.get(session_id) != "error":
                continue
            try:
                transcript_rows = session_conn.execute(
                    "SELECT 1 FROM message WHERE session_id = ? LIMIT 1", (session_id,)
                ).fetchone()
            except sqlite3.Error:
                transcript_rows = None
            row_markers: list[str] = []
            if transcript_rows is None:
                row_markers.append("transcript-absent")
            content_after = False if transcript_rows is None else _zero_turn_session_content_after(
                session_conn, session_id, int(created_at)
            )
            if content_after:
                # A contrast run: the session holds a content-bearing
                # assistant record created after the run's created_at, so
                # this run is not a zero-turn carrier.
                continue
            warnings.append({
                "automation_id": automation_id,
                "automation_title": titles.get(automation_id) if isinstance(automation_id, str) else None,
                "session_id": session_id,
                "scheduled_at": scheduled_at,
                "run_id": run_id,
                "markers": row_markers,
            })
    finally:
        session_conn.close()
    return _zero_turn_census_member("ok", "census-complete", warnings=warnings, markers=markers)


def _carrier_liveness_operation(payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    """The read-only missed-fire carrier-liveness verdict (plan
    2026-11-12-maintenance-indefinite-operation-stop-gaps Task 4).

    Classifies the scheduler carrier's fire state from the state file's
    ``next_turn_at`` recorded fire time plus the recorded parent's listing
    state (its ``lastRunAt``) read through the task-index store conventions
    scripts/maintenance_fire_outcomes.py already uses. ``ok`` covers a fire
    not yet due, a fresh fire still inside the two-hour grace window
    (``CARRIER_LIVENESS_GRACE_WINDOW_SECONDS``: a fresh fire is never a
    missed classification), and a fire whose lastRunAt advanced past it;
    ``missed-fire`` requires the recorded fire time past the grace window
    with lastRunAt not advanced past it; an unreadable state file or store
    is ``unknown`` and infers nothing. Read-only: writes nothing. Optional
    payload keys: ``state_path`` (default
    ``<repo-root>/.ai-playbook/scheduler-state.json``), ``db_path`` (default
    the store ``maintenance_fire_outcomes`` resolves), and ``now_epoch``
    (epoch seconds; default the current time, so tests and re-derivations
    pin the clock).

    Every returned verdict also carries the additive ``zero_turn_census``
    member (plan 2026-11-13-errored-zero-turn-carrier-recovery Task 1): the
    fired-but-zero-turn census read runs before and independent of the
    missed-fire early returns, computed from the task-index store plus the
    session store (payload key ``session_db_path``, then the facts
    document's ``session_store_path`` key, then the home default); a store
    failure yields the census unknown marker with the member still present.
    Warning-only report data; the consumer decides."""
    root = Path(repo_root or Path.cwd()).resolve()
    raw_now = payload.get("now_epoch")
    if raw_now is None:
        now_epoch = datetime.now(timezone.utc).timestamp()
    elif isinstance(raw_now, (int, float)) and not isinstance(raw_now, bool):
        now_epoch = float(raw_now)
    else:
        raise ValueError("carrier-liveness now_epoch must be an epoch-seconds number")
    # The census arm runs before and independent of the missed-fire early
    # returns: every verdict below carries the additive member, and a store
    # failure degrades the census to its unknown marker without touching
    # the missed-fire classification.
    census = _zero_turn_census_operation(payload, root, now_epoch)
    verdict = _carrier_liveness_core(payload, root, now_epoch)
    verdict["zero_turn_census"] = census
    return verdict


def _carrier_liveness_core(payload: Mapping[str, Any], root: Path, now_epoch: float) -> dict[str, Any]:
    """The missed-fire classification proper (the state-file read plus the
    recorded parent's listing), split so the census arm wraps every
    verdict."""
    import maintenance_fire_outcomes as fire_outcomes

    state_path = Path(str(payload.get("state_path") or (root / ".ai-playbook" / "scheduler-state.json")))
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _carrier_liveness_verdict("unknown", "state-unreadable", state_path=str(state_path), detail=str(exc))
    if not isinstance(state, Mapping):
        return _carrier_liveness_verdict("unknown", "state-unreadable", state_path=str(state_path), detail="state file is not a JSON object")
    recorded_fire_at = state.get("next_turn_at")
    parent_id = state.get("parent_automation_id")
    if not isinstance(recorded_fire_at, str) or not recorded_fire_at.strip():
        return _carrier_liveness_verdict("unknown", "missing-next-turn-at", state_path=str(state_path))
    fire_epoch = _carrier_liveness_epoch_from_iso(recorded_fire_at)
    if fire_epoch is None:
        return _carrier_liveness_verdict("unknown", "unparseable-next-turn-at", state_path=str(state_path), recorded_fire_at=recorded_fire_at)
    if not isinstance(parent_id, str) or not parent_id.strip():
        return _carrier_liveness_verdict("unknown", "missing-parent-automation-id", state_path=str(state_path), recorded_fire_at=recorded_fire_at)
    context = {
        "recorded_fire_at": recorded_fire_at,
        "recorded_fire_epoch": fire_epoch,
        "parent_automation_id": parent_id,
        "grace_window_seconds": CARRIER_LIVENESS_GRACE_WINDOW_SECONDS,
        "now_epoch": now_epoch,
    }
    if now_epoch < fire_epoch:
        return _carrier_liveness_verdict("ok", "not-yet-due", **context)
    if now_epoch < fire_epoch + CARRIER_LIVENESS_GRACE_WINDOW_SECONDS:
        return _carrier_liveness_verdict("ok", "fresh-fire-inside-grace-window", **context)
    listing, unknown = _carrier_liveness_parent_listing(
        fire_outcomes.resolve_db_path(payload.get("db_path")), parent_id
    )
    if unknown is not None:
        unknown.update(context)
        return unknown
    assert listing is not None
    last_run_ms = listing["last_run_at_epoch_ms"]
    advanced = last_run_ms is not None and last_run_ms > int(fire_epoch * 1000)
    return _carrier_liveness_verdict(
        "ok" if advanced else "missed-fire",
        "last-run-advanced-past-fire" if advanced else "past-grace-window-last-run-not-advanced",
        last_run_advanced=advanced,
        **listing,
        **context,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("precondition", *_PLANS_WATCHER_OPERATIONS, *_CLOCKED_ORDER_OPERATIONS, _CENSUS_OPERATION, _CARRIER_LIVENESS_OPERATION, *_CODEX_QUOTA_WAKE_OPERATIONS), required=True)
    parser.add_argument("--predecessors-file", type=Path)
    parser.add_argument(
        "--input",
        help="inline JSON object passed as one argument (never a file path or per-key flags); "
        "for --operation clocked-order-schedule the object keys are requested_at_iso, payload_slug, "
        "and payload_path (or payload_text); requested_at_iso must be minute precision (seconds and "
        "microseconds zero; a sub-minute value refuses at schedule time); a pickup re-record under a derived id also passes order_id, "
        "and a retry order passes retry_for_order naming the unresolved original order; "
        "for clocked-order-discharge-on-fire the object keys are order_id, ledger_path, payload_slug, "
        "and repo_root; "
        "for clocked-order-due the object keys may add scheduler_state_path naming the scheduler state "
        "whose children[] projection the restart reconciliation repairs; "
        f"for clocked-order-begin-fire the object keys are order_id, ledger_path, payload_slug, and "
        f"repo_root; a blocked refusal (live lease, terminal state, early fire, unknown order) exits "
        f"{CLOCKED_ORDER_BEGIN_FIRE_REFUSED_EXIT} so a refused lease starts no session - success exits 0; "
        "for codex-quota-wake-schedule: thread_id, target, kind, phase, reset_at_epoch, repo_root; "
        "for codex-quota-wake-reconcile: receipt_path, continuation; "
        "for carrier-liveness the object keys are all optional: state_path "
        "(default <repo-root>/.ai-playbook/scheduler-state.json), db_path "
        "(default the task-index store maintenance_fire_outcomes resolves), "
        "and now_epoch (epoch seconds; default the current time)",
    )
    parser.add_argument(
        "--session-id",
        help="explicit executor session id (the ZCode runtime-context identity) merged into the "
        "clocked-order operation payload; the discharge refuses without one",
    )
    parser.add_argument(
        "--launcher-exit-code",
        type=int,
        help="explicit launcher exit status merged into the clocked-order-clear-fire payload; "
        "the fire wrapper's brace group passes the captured launch exit status here",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input) if args.input else {}
        if args.operation == "precondition":
            if args.predecessors_file is None:
                parser.error("--predecessors-file is required for --operation precondition")
            try:
                predecessors_document = json.loads(
                    args.predecessors_file.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                result = _outcome(
                    "blocked",
                    "precondition-unverified",
                    [f"predecessors file could not be read or parsed: {args.predecessors_file}: {exc}"],
                    "repository-read",
                    "precondition:verify",
                    0,
                    "preserve-and-reconcile",
                    resume_allowed=True,
                    predecessors=[],
                )
            else:
                result = verify_preconditions(args.repo_root, predecessors_document)
        elif args.operation == _CENSUS_OPERATION:
            # The census dispatch branch (plan
            # 2026-11-06-budget-resume-carrier-gc Task 1): requires no
            # state_path and builds no authoring adapter; the roots are
            # optional payload keys so tests can inject temporary roots.
            import execute_plan_resume_watcher as watcher
            if not isinstance(payload, Mapping):
                raise ValueError("census input must be a JSON object")
            result = watcher.budget_carrier_census(
                job_dir=payload.get("job_dir"),
                runtime_root=payload.get("runtime_root"),
            )
        elif args.operation == _CARRIER_LIVENESS_OPERATION:
            # The carrier-liveness dispatch branch (plan
            # 2026-11-12-maintenance-indefinite-operation-stop-gaps Task 4):
            # a read-only verdict, no state_path requirement and no
            # authoring adapter; the payload keys are optional injection
            # points so tests can pin the state file, the store, and the
            # clock. Warning-only: the verdict exits 0 and its consumer
            # (a survey turn, report-only) decides.
            if not isinstance(payload, Mapping):
                raise ValueError("carrier-liveness input must be a JSON object")
            result = _carrier_liveness_operation(payload, args.repo_root)
        elif args.operation == "codex-quota-wake-schedule":
            if not isinstance(payload, Mapping):
                raise ValueError("Codex quota wake input must be a JSON object")
            result = _codex_quota_wake_operation(payload, args.repo_root)
        elif args.operation == "codex-quota-wake-fire":
            if not isinstance(payload, Mapping):
                raise ValueError("Codex quota wake fire input must be a JSON object")
            result = _codex_quota_wake_fire_operation(payload, args.repo_root)
        elif args.operation == "codex-quota-wake-reconcile":
            if not isinstance(payload, Mapping):
                raise ValueError("Codex quota wake reconcile input must be a JSON object")
            result = _codex_quota_wake_reconcile_operation(payload)
        elif args.operation in _PLANS_WATCHER_OPERATIONS:
            if not isinstance(payload, Mapping):
                raise ValueError("plans watcher input must be a JSON object")
            result = _plans_watcher_operation(args.operation, payload, args.repo_root)
        else:
            if not isinstance(payload, Mapping):
                raise ValueError("clocked order input must be a JSON object")
            result = _clocked_order_operation(
                args.operation, payload, args.repo_root, session_id=args.session_id, launcher_exit_code=args.launcher_exit_code
            )
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"execute-plan runtime operation failed: {exc}", file=sys.stderr)
        return 1
    if args.operation == "clocked-order-begin-fire" and result.get("status") == "blocked":
        # The fire wrapper's && chain: a refused begin-fire stops the launch
        # here, before ``zcode --prompt``, with the distinct refusal exit; no
        # clear-fire runs (it lives behind the launch it guards).
        return CLOCKED_ORDER_BEGIN_FIRE_REFUSED_EXIT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
