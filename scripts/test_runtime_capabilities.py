#!/usr/bin/env python3
"""Regression checks for retained plan helpers and retired adapter registration."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import runtime_capabilities as capabilities

ROOT = Path(__file__).resolve().parents[1]


class ExecutePlanRegistrationTest(unittest.TestCase):
    def test_package_has_no_adapter_or_worker_registry(self) -> None:
        package = tomllib.loads(
            (ROOT / "agents/skills/execute-plan/package-manifest.toml").read_text(encoding="utf-8")
        )
        self.assertNotIn("adapters", package)
        self.assertNotIn("worker_registry", package.get("runtime_modules", {}))
        self.assertNotIn("fixtures", package)

    def test_runtime_catalog_has_no_execute_plan_adapter_or_worker_hooks(self) -> None:
        inventory = capabilities.load_inventory(ROOT / "projects/.ai-playbook/execute-plan-runtime-inventory.toml")
        self.assertEqual(inventory["runtimes"], {})
        self.assertEqual(set(inventory["inventory"]["deferred_ids"]), set(inventory["inventory"]["canonical_ids"]) | {"pi"})
        self.assertNotIn("execute_plan_hooks", inventory)
        self.assertNotIn("adapter_entrypoint", inventory["deferrals"]["codex"])
        for retired in ("resolve_adapter", "UnsupportedAdapter", "normalize_evidence_envelope", "process_identity_fingerprint", "activate"):
            self.assertFalse(hasattr(capabilities, retired), retired)

    def test_plan_evidence_helpers_remain_available(self) -> None:
        self.assertEqual(capabilities.evidence_criterion_ids(["criterion"]), {"c001": "criterion"})
        task = {"required_criteria": ["criterion"], "checklist_actions": []}
        self.assertEqual(capabilities.derive_checklist_actions("task-1", task)[0], {"criterion"})

    def test_plans_authoring_watcher_operations_remain_reachable(self) -> None:
        runtime_source = (ROOT / "scripts/execute_plan_runtime.py").read_text(encoding="utf-8")
        watcher_source = (ROOT / "scripts/execute_plan_resume_watcher.py").read_text(encoding="utf-8")
        for operation in ("plans-watcher-schedule", "plans-watcher-supersede", "plans-watcher-fire"):
            self.assertIn(operation, runtime_source)
        self.assertIn("class PlansAuthoringWatcherAdapter", watcher_source)
        self.assertNotIn("class RuntimeResumeWatcherAdapter", watcher_source)


if __name__ == "__main__":
    unittest.main()
