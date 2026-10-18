#!/usr/bin/env python3
"""Manifest-free helpers retained for plans authoring and repository checks.

The execute-plan implementation route is host-native and sequential. This
module no longer owns worker manifests, claims, launch lifecycle, or recovery.
It keeps only independently used authoring watcher and clocked-order CLI
operations plus small compatibility helpers used by repository tooling.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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
        offender = next(
            item for item in criteria
            if isinstance(item, str) and len(item.encode("utf-8")) > capabilities.MAX_EVIDENCE_ITEM_BYTES
        )
        return (
            f"task '{task_id}': {bare_message} ({len(offender.encode('utf-8'))} UTF-8 bytes, "
            f"limit {capabilities.MAX_EVIDENCE_ITEM_BYTES}): {offender}; split the criterion into "
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
                        str(task_id), criteria if isinstance(criteria, list) else [], dimension, message
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
)
_CLOCKED_ORDER_OPERATIONS = (
    "clocked-order-schedule", "clocked-order-cancel", "clocked-order-due", "clocked-order-discharge-on-fire",
)


def _plans_watcher_operation(operation: str, payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
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
        kind, payload, adapter=adapter, supersede=adapter.compare_and_swap_supersede,
        outcome_factory=_outcome, identity_prefix="plans-watcher",
        plan_slug=str(payload.get("plan_slug") or ""), repo_root=str(repo_root),
    )


def _clocked_order_operation(operation: str, payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    import execute_plan_resume_watcher as watcher
    root = Path(repo_root or Path.cwd()).resolve()
    ledger_path = payload.get("ledger_path")
    payload_home = payload.get("payload_home")
    if not ledger_path or not payload_home:
        state_dir = _resolved_facts_dir(root, "maintenance_state_dir") or root / ".ai-playbook" / "maintenance"
        ledger_path = ledger_path or state_dir / "clocked-orders.json"
        payload_home = payload_home or state_dir / "clocked-order-payloads"
    ledger = watcher.ClockedOrderLedger(ledger_path, payload_home, repo_root=str(root))
    return watcher.run_clocked_order_operation(operation.removeprefix("clocked-order-"), payload, repo_root=str(root), ledger=ledger)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("precondition", *_PLANS_WATCHER_OPERATIONS, *_CLOCKED_ORDER_OPERATIONS), required=True)
    parser.add_argument("--predecessors-file", type=Path)
    parser.add_argument("--input")
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
        elif args.operation in _PLANS_WATCHER_OPERATIONS:
            if not isinstance(payload, Mapping):
                raise ValueError("plans watcher input must be a JSON object")
            result = _plans_watcher_operation(args.operation, payload, args.repo_root)
        else:
            if not isinstance(payload, Mapping):
                raise ValueError("clocked order input must be a JSON object")
            result = _clocked_order_operation(args.operation, payload, args.repo_root)
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"execute-plan runtime operation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
