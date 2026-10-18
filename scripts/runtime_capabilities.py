#!/usr/bin/env python3
"""Shared plan evidence and checklist helpers plus hook-probe inventory loading."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = ROOT / "projects/.ai-playbook/execute-plan-runtime-inventory.toml"
# Shared checklist classification and bounded criterion helpers used by
# plan authoring, readiness, and retained CLI checks.
# This module owns checklist and bounded-criterion helpers shared by plan
# authoring and readiness validation, so both apply the same labels and limits.
MAX_EVIDENCE_BYTES = 4096
MAX_EVIDENCE_ITEM_BYTES = 512
# Criterion bounds and receipt construction are owned by evidence_criterion_ids.


def check_checklist_action_classification(task_id: str, item: Mapping[str, Any]) -> None:
    """Raise the classification refusals for one task's checklist actions.

    The checklist-action check shared by plan authoring and readiness: the task body's checkbox lines are
    extracted (checked and unchecked classify alike) and compared against
    the declared ``checklist_actions`` - unclassified lines refuse, an
    incomplete classification refuses, and a malformed action mapping
    refuses. Raises nothing for a task with no checkbox lines and no
    declared actions.
    """

    actions = item.get("checklist_actions")
    task_body = item.get("task_body")
    checklist_text: list[str] = []
    if isinstance(task_body, str):
        checklist_text = [
            match.group(1).strip()
            for line in task_body.splitlines()
            # Checked and unchecked boxes classify alike: the collector
            # reads ``[[ xX]]`` boxes, so a checked-but-unclassified
            # action refuses seeding exactly like an unchecked one.
            if (match := re.match(r"^\s*[-*+]\s+\[[ xX]]\s+(.*)$", line)) is not None
        ]
    if checklist_text and actions is None:
        raise ValueError(f"task {task_id} has unclassified checklist actions")
    if checklist_text and isinstance(actions, list):
        action_text = [str(action.get("text", "")).strip() for action in actions if isinstance(action, Mapping)]
        if sorted(checklist_text) != sorted(action_text):
            raise ValueError(f"task {task_id} checklist action classification is incomplete")
    if actions is not None:
        if not isinstance(actions, list) or any(
            not isinstance(action, Mapping)
            or action.get("owner") not in {"worker", "parent"}
            or not isinstance(action.get("text"), str)
            or not action.get("text", "").strip()
            for action in actions
        ):
            raise ValueError(f"task {task_id} has an unclassified checklist action")


def derive_checklist_actions(task_id: str, item: Mapping[str, Any]) -> tuple[set[str], list[dict[str, Any]], str | None]:
    """The pure checklist-action derivation the classification checks consume.

    Promotes ``Commit:``-prefixed actions to owner ``parent`` (kind
    ``commit``), diffs the parent-owned criteria out of the task's required
    criteria, and collects the parent obligations. Returns
    ``(worker_criteria, parent_obligations, planned_commit)`` where
    ``planned_commit`` is the exact planned identity when any commit action
    was derived (``None`` otherwise). Raises the two derivation refusals:
    a commit action without its exact planned identity, and a task whose
    criteria are all parent-owned.
    """

    actions = item.get("checklist_actions")
    if actions is None:
        return set(item.get("required_criteria", ()) or ()), [], None
    worker_criteria = set(item.get("required_criteria", ()) or ())
    parent_obligations: list[dict[str, Any]] = []
    planned_commit: str | None = None
    for action in actions:
        is_commit = action.get("kind") == "commit" or action["text"].startswith("Commit:")
        if action["owner"] != "parent" and not is_commit:
            continue
        action = dict(action)
        if is_commit:
            action["owner"] = "parent"
        criteria = action.get("criteria", [action["text"]])
        worker_criteria.difference_update(criteria if isinstance(criteria, list) else [])
        if is_commit:
            text = action["text"]
            inferred_commit = text.split(":", 1)[1].strip() if text.startswith("Commit:") else None
            candidate = action.get("commit_identity", item.get("parent_commit", inferred_commit))
            if not isinstance(candidate, str) or not candidate.strip():
                raise ValueError(f"task {task_id} parent commit action requires its exact planned identity")
            planned_commit = candidate
        parent_obligations.append(dict(action))
    if not worker_criteria:
        raise ValueError(f"task {task_id} has no worker-owned criteria")
    return worker_criteria, parent_obligations, planned_commit


def derive_plan_checklist_actions(
    section_text: str, empty_refusal_label: str | None = None
) -> tuple[list[str], list[dict[str, Any]]]:
    """Derive the checklist actions and acceptance criteria from one plan
    task section, exactly as plan authoring and readiness require.

    Every acceptance checkbox line classifies: a ``Commit:``-prefixed line
    becomes a parent commit obligation (owner ``parent``, kind ``commit``);
    every other line defaults to owner ``worker`` and deduplicates into the
    task's acceptance criteria. Plan authoring and readiness consume the
    same derived shape, so a ``Commit:`` checkbox never false-fails the
    classification check on either surface. An empty checkbox line raises
    ``empty_refusal_label`` when supplied and is skipped when it is ``None``: the discovery-path refusal class
    stays the documented residual, out of certification parity).
    """

    criteria: list[str] = []
    checklist_actions: list[dict[str, Any]] = []
    for line in section_text.splitlines():
        match = re.match(r"^\s*[-*+]\s+\[[ xX]]\s+(.*)$", line)
        if match is None:
            continue
        text = match.group(1).strip()
        if not text:
            if empty_refusal_label is not None:
                raise ValueError(empty_refusal_label)
            continue
        if text.startswith("Commit:"):
            # The planned commit stays a parent obligation, mirroring the
            # parent-owned checklist classification rule.
            checklist_actions.append({"text": text, "owner": "parent", "kind": "commit"})
            continue
        if text not in criteria:
            criteria.append(text)
        checklist_actions.append({"text": text, "owner": "worker"})
    return criteria, checklist_actions


def checklist_clone_signature_problems(task_map: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The deep-equality global-checklist clone-signature detection.

    Two or more tasks declaring identical non-empty whole
    ``verification_commands`` lists (deep equality) are the signature of a
    plan's global Validation Commands block cloned into per-task verifiers
    instead of staying the whole-plan gate. Each problem attributes the
    PAIR (both cloned task ids) with basis ``clone-signature`` and the
    display string the plan consistency check joins.
    """

    ordered = sorted(task_map.items(), key=lambda entry: entry[1].get("ordinal", 0))
    declared = [(str(task_id), task.get("verification_commands")) for task_id, task in ordered]
    problems: list[dict[str, Any]] = []
    for index, (task_id, commands) in enumerate(declared):
        if not commands:
            continue
        for earlier_id, earlier_commands in declared[:index]:
            if earlier_commands and commands == earlier_commands:
                problems.append(
                    {
                        "task_ids": [earlier_id, task_id],
                        "basis": "clone-signature",
                        "display": (
                            f"pre-seed consistency gate: tasks {earlier_id} and {task_id} declare identical non-empty "
                            "verification_commands lists (deep equality); this is the signature of a global checklist "
                            "cloned into per-task verifiers instead of the whole-plan gate"
                        ),
                    }
                )
    return problems


def evidence_criterion_ids(criteria: Any) -> dict[str, str]:
    """Build stable, compact receipt identifiers for full criterion text."""
    if not isinstance(criteria, (list, tuple)) or any(not isinstance(item, str) or not item for item in criteria):
        raise ValueError("required_criteria must be a list of non-empty strings")
    if len(criteria) != len(set(criteria)):
        raise ValueError("required_criteria contains duplicates")
    if len(criteria) > 100:
        raise ValueError("evidence criteria exceed receipt item-count limit (100)")
    if any(len(item.encode("utf-8")) > MAX_EVIDENCE_ITEM_BYTES for item in criteria):
        raise ValueError("evidence criterion exceeds UTF-8 item byte limit")
    if sum(len(item.encode("utf-8")) for item in criteria) > MAX_EVIDENCE_BYTES:
        raise ValueError("evidence criteria exceed UTF-8 aggregate byte limit")
    return {f"c{index:03d}": criterion for index, criterion in enumerate(sorted(criteria), 1)}

def load_inventory(path: Path | str | None = None) -> dict[str, Any]:
    """Load and validate the authoritative runtime inventory.

    An explicitly passed path always wins over the ambient
    ``EXECUTE_PLAN_RUNTIME_INVENTORY`` environment variable; the variable is
    consulted only when no path argument is supplied.
    """

    if path is None:
        path = os.environ.get("EXECUTE_PLAN_RUNTIME_INVENTORY", DEFAULT_INVENTORY_PATH)
    inventory_path = Path(path)
    with inventory_path.open("rb") as stream:
        inventory = tomllib.load(stream)
    validate_inventory(inventory)
    return inventory


def validate_inventory(inventory: Mapping[str, Any]) -> None:
    """Validate the runtime identifiers and independent hook-probe catalog."""

    root = inventory.get("inventory")
    if not isinstance(root, Mapping):
        raise ValueError("inventory table is required")
    canonical_ids = root.get("canonical_ids")
    deferred_ids = root.get("deferred_ids")
    if not isinstance(canonical_ids, list) or not canonical_ids or len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("inventory.canonical_ids must be a non-empty unique list")
    if not isinstance(deferred_ids, list) or len(deferred_ids) != len(set(deferred_ids)):
        raise ValueError("inventory.deferred_ids must be a unique list")
    runtimes = inventory.get("runtimes")
    if not isinstance(runtimes, Mapping) or set(runtimes) != set(canonical_ids) - set(deferred_ids):
        raise ValueError("runtime profile IDs must match eligible canonical IDs")
    deferrals = inventory.get("deferrals")
    if not isinstance(deferrals, Mapping) or set(deferrals) != set(deferred_ids):
        raise ValueError("every deferred runtime needs an explicit deferral record")
    for runtime_id, deferral in deferrals.items():
        if deferral.get("eligibility") != "deferred" or not deferral.get("reason"):
            raise ValueError(f"deferred runtime {runtime_id} needs a non-empty reason")
    if not isinstance(inventory.get("hook_profiles"), list):
        raise ValueError("registry hook_profiles are required")



def selftest() -> None:
    inventory = load_inventory()
    validate_inventory(inventory)
    if inventory.get("runtimes"):
        raise AssertionError("execute-plan runtime profiles are retired")
    evidence_criterion_ids(["selftest criterion"])
    print(f"shared plan capability selftest: {len(inventory['hook_profiles'])} hook profiles")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if not args.selftest:
        parser.error("--selftest is required")
    try:
        selftest()
    except (AssertionError, OSError, ValueError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"shared plan capability selftest failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
