#!/usr/bin/env python3
"""Tests for the provider-neutral execute-plan runtime registry."""

from __future__ import annotations

import os
import re
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import runtime_capabilities as capabilities
import hooks_probe
import execute_plan_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "projects/.ai-playbook/execute-plan-runtime-inventory.toml"
CONTRACT_PATH = ROOT / "agents/skills/execute-plan/runtime-contract.md"
RUNTIME_LAYOUT_PATH = ROOT / "projects/.ai-playbook/agent-runtime-layout.md"
AGTERM_CATALOG_PATH = ROOT / "agents/skills/agterm/agent-runtimes.md"
HOOK_PROBE_PATH = ROOT / "scripts/hooks_probe.py"
EXPECTED_IDS_PATH = ROOT / "scripts/testdata/execute-plan/expected-runtime-ids.json"
ACTIVATION_FIXTURE_PATH = ROOT / "scripts/testdata/execute-plan/activation"


def _expected_ids() -> dict[str, list[str]]:
    return json.loads(EXPECTED_IDS_PATH.read_text(encoding="utf-8"))


def _normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


class RuntimeCapabilitiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = capabilities.load_inventory(INVENTORY_PATH)
        cls.profiles = capabilities.load_profiles(INVENTORY_PATH)
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")
        cls.expected_ids = _expected_ids()

    def setUp(self) -> None:
        # Pin ambient execute-plan env inputs so an exported variable cannot
        # silently validate a foreign registry in these tests.
        self._saved_env = {key: os.environ.pop(key) for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST") if key in os.environ}

    def tearDown(self) -> None:
        os.environ.update(self._saved_env)
        for key in ("EXECUTE_PLAN_RUNTIME_INVENTORY", "EXECUTE_PLAN_PACKAGE_MANIFEST"):
            if key not in self._saved_env:
                os.environ.pop(key, None)

    def test_explicit_inventory_path_wins_over_ambient_env(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            foreign = Path(directory) / "foreign.toml"
            foreign.write_text("not a valid inventory", encoding="utf-8")
            with mock.patch.dict(os.environ, {"EXECUTE_PLAN_RUNTIME_INVENTORY": str(foreign)}):
                explicit = capabilities.load_inventory(INVENTORY_PATH)
                self.assertIn("runtimes", explicit)
                with self.assertRaises(ValueError):
                    capabilities.load_inventory()

    def test_reason_code_set_is_closed_and_fails_closed(self) -> None:
        base = {
            "status": "success",
            "evidence": ["worker"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1",
            "generation": 1,
        }
        for raw in (base, {**base, "reason_code": "invented-code"}):
            with self.assertRaises(ValueError):
                capabilities.normalize_result(raw)
        for reason in ("authorized", "activation-verified", "worktree-witness-unavailable", "done-pending", "commit-pending"):
            self.assertIn(reason, capabilities.REASON_CODES)
        self.assertEqual(
            capabilities.RESUMABLE_REASONS,
            {"approval-required", "timeout", "runtime-error", "stale-claim"},
        )

    def test_all_documented_runtimes_have_profiles(self) -> None:
        expected_canonical = set(self.expected_ids["canonical_ids"])
        expected_deferred = set(self.expected_ids["deferred_ids"])
        self.assertEqual(
            set(self.inventory["inventory"]["canonical_ids"]),
            expected_canonical,
        )
        self.assertEqual(set(self.profiles), expected_canonical)
        self.assertEqual(
            set(self.inventory["inventory"]["deferred_ids"]), expected_deferred
        )

        required_capabilities = {
            "launch",
            "wait",
            "resume",
            "checkpoint",
            "approval",
            "parent_continuation",
            "final_response",
        }
        for runtime_id in expected_canonical:
            profile = self.profiles[runtime_id]
            self.assertEqual(profile["id"], runtime_id)
            self.assertTrue(profile["display_name"])
            self.assertTrue(profile["adapter_entrypoint"])
            self.assertTrue(profile["adapter_version"])
            self.assertTrue(profile["approval_policy"])
            self.assertTrue(profile["fallback"])
            self.assertEqual(set(profile["capabilities"]), required_capabilities)
            for state in profile["capabilities"].values():
                self.assertIn(state, {"full", "degraded", "unsupported"})

        pi = self.inventory["deferrals"]["pi"]
        self.assertEqual(pi["eligibility"], "deferred")
        self.assertTrue(pi["reason"])
        self.assertIn("resume", pi["reason"].lower())

        catalogs = {
            "runtime-layout": RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"),
            "agterm": AGTERM_CATALOG_PATH.read_text(encoding="utf-8"),
            "hooks-probe": HOOK_PROBE_PATH.read_text(encoding="utf-8"),
        }
        for runtime_id, profile in self.profiles.items():
            aliases = [_normalized(alias) for alias in profile["aliases"]]
            for catalog_name in profile["source_catalogs"]:
                catalog = _normalized(catalogs[catalog_name])
                self.assertTrue(
                    any(alias in catalog for alias in aliases),
                    f"{runtime_id} is missing from {catalog_name}",
                )

        deferred_catalog = _normalized(catalogs["agterm"])
        self.assertTrue(any(alias in deferred_catalog for alias in ("pi",)))

    def test_independent_runtime_ids_match_every_catalog_and_probe(self) -> None:
        expected = set(self.expected_ids["canonical_ids"])
        deferred = set(self.expected_ids["deferred_ids"])
        all_ids = expected | deferred
        self.assertEqual(len(expected), 8)
        self.assertEqual(deferred, {"pi"})

        layout = _normalized(RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"))
        agterm = _normalized(AGTERM_CATALOG_PATH.read_text(encoding="utf-8"))
        for runtime_id, aliases in self.expected_ids["aliases"].items():
            self.assertIn(runtime_id, all_ids)
            catalog = layout if runtime_id in {"gemini", "antigravity"} else agterm
            self.assertTrue(
                any(_normalized(alias) in catalog for alias in aliases),
                f"{runtime_id} is absent from its source catalog",
            )

        rows = hooks_probe.runtime_profile_rows()
        self.assertEqual({row.runtime_id for row in rows}, all_ids)
        self.assertEqual(len(rows), len(all_ids))
        self.assertIn("pi", {row.agent.lower() for row in rows})
        self.assertIn("ZCode", RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"))
        self.assertIn("OpenCode", AGTERM_CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertIn("Gemini CLI", RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"))
        self.assertIn("Antigravity", RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"))

    def test_runtime_activation_fixture_verifies_loaded_package_bytes(self) -> None:
        result = capabilities.verify_activation(ACTIVATION_FIXTURE_PATH)
        self.assertEqual(result["status"], "success")
        self.assertEqual(
            set(result["checked_roles"]), {"skill", "driver", "registry", "adapter"}
        )
        self.assertEqual(result["help_probes"], 2)

    def test_runtime_activation_fixture_fails_closed_on_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ACTIVATION_FIXTURE_PATH, root / "activation")
            drifted = root / "activation" / "loaded" / "execute-plan" / "runtime" / "execute_plan_runtime.py"
            drifted.write_bytes(drifted.read_bytes() + b"\n")
            with self.assertRaises(ValueError):
                capabilities.verify_activation(root / "activation")

    def test_shared_contract_has_no_host_protocol(self) -> None:
        provider_neutral = self.contract.split(
            "## Runtime profile data", maxsplit=1
        )[0]
        forbidden = (
            "claude",
            "codex",
            "cursor",
            "zcode",
            "opencode",
            "copilot",
            "gemini",
            "antigravity",
            "pi",
            "hooks.json",
            "pretooluse",
            "--resume",
            "mcp__",
        )
        lowered = provider_neutral.lower()
        for term in forbidden:
            self.assertNotIn(term, lowered, f"host protocol leaked: {term}")

    def test_unsupported_capability_is_explicit(self) -> None:
        profile = dict(self.profiles["codex"])
        profile["capabilities"] = dict(profile["capabilities"])
        profile["capabilities"]["final_response"] = "unsupported"
        profile["fallback"] = "Return a receipt and let the parent process continue."
        capabilities.validate_profile(profile)

        profile["fallback"] = ""
        profile["capabilities"]["final_response"] = "unsupported"
        with self.assertRaises(ValueError):
            capabilities.validate_profile(profile)

    def test_approval_state_is_distinct_from_worker_hesitation(self) -> None:
        worker_success = capabilities.normalize_result(
            {
                "status": "success",
                "reason_code": "completed",
                "evidence": ["worker-log"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-1",
                "generation": 1,
            }
        )
        approval_required = capabilities.normalize_result(
            {
                "status": "blocked",
                "reason_code": "approval-required",
                "evidence": ["tool-request"],
                "action_scope": "external-write",
                "checkpoint_identity": "task-1",
                "generation": 1,
            }
        )
        self.assertEqual(worker_success["status"], "success")
        self.assertEqual(approval_required["status"], "blocked")
        self.assertNotEqual(worker_success["status"], approval_required["status"])
        self.assertEqual(approval_required["retry_policy"]["mode"], "none")
        self.assertEqual(approval_required["recovery_action"], "preserve-and-await-approval")

    def test_blocking_reason_cannot_remain_success(self) -> None:
        for reason in ("approval-required", "cleanup-unverified"):
            result = capabilities.normalize_result(
                {
                    "status": "success",
                    "reason_code": reason,
                    "evidence": [reason],
                    "action_scope": "repository-task",
                    "checkpoint_identity": "task-1",
                    "generation": 1,
                }
            )
            self.assertEqual(result["status"], "blocked", reason)

    def test_retry_budget_is_profile_owned(self) -> None:
        result = capabilities.normalize_result(
            {
                "status": "error",
                "reason_code": "runtime-error",
                "evidence": ["runner"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-1",
                "generation": 1,
            },
            retry_budget=1,
        )
        self.assertEqual(result["retry_policy"]["max_attempts"], 1)
        self.assertEqual(result["retry_policy"]["attempts_remaining"], 1)
        self.assertIn("resume_allowed", result)

    def test_worker_supplied_retry_policy_is_clamped_to_profile_budget(self) -> None:
        hostile = {
            "status": "error",
            "reason_code": "runtime-error",
            "evidence": ["runner"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1",
            "generation": 1,
            "retry_policy": {"mode": "bounded", "max_attempts": 5000, "attempts_remaining": 5000},
        }
        result = capabilities.normalize_result(hostile, retry_budget=2)
        self.assertEqual(result["retry_policy"]["max_attempts"], 2)
        self.assertEqual(result["retry_policy"]["attempts_remaining"], 2)
        violation = capabilities.normalize_result(
            {
                "status": "contract-violation",
                "reason_code": "permission-request",
                "evidence": ["asked"],
                "action_scope": "repository-task",
                "checkpoint_identity": "task-1",
                "generation": 1,
                "retry_policy": {"mode": "rewrite-and-retry", "max_attempts": 5000, "attempts_remaining": 5000},
            },
            retry_budget=2,
        )
        self.assertEqual(violation["retry_policy"]["max_attempts"], 1)
        self.assertEqual(violation["retry_policy"]["attempts_remaining"], 1)

    def test_registry_is_the_only_capability_owner(self) -> None:
        self.assertEqual(self.inventory["inventory"]["capability_owner"], "registry")
        self.assertEqual(
            self.inventory["inventory"]["registry_path"],
            "projects/.ai-playbook/execute-plan-runtime-inventory.toml",
        )
        self.assertEqual(
            len(self.inventory["inventory"]["canonical_ids"]),
            len(set(self.inventory["inventory"]["canonical_ids"])),
        )
        source = Path(capabilities.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?m)^\s*(PROBE_MATRIX|CAPABILITY_MATRIX)\s*=")
        self.assertNotIn("canonical_ids = [", source)
        self.assertNotIn("capabilities = {", source)

    def test_every_eligible_profile_resolves_to_an_executable_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for runtime_id in self.profiles:
                adapter = capabilities.resolve_adapter(runtime_id, directory, approval_verified=False)
                self.assertTrue(callable(getattr(adapter, "launch", None)), runtime_id)
                self.assertTrue(callable(getattr(adapter, "wait", None)), runtime_id)
                self.assertTrue(callable(getattr(adapter, "resume", None)), runtime_id)

    def test_unbound_profiles_are_explicitly_unsupported(self) -> None:
        for runtime_id, profile in self.profiles.items():
            if runtime_id == "codex":
                self.assertEqual(profile["capabilities"]["launch"], "full")
                self.assertEqual(profile["capabilities"]["wait"], "full")
                self.assertEqual(profile["capabilities"]["resume"], "full")
                continue
            self.assertEqual(profile["capabilities"]["launch"], "unsupported")
            self.assertEqual(profile["capabilities"]["wait"], "unsupported")
            self.assertEqual(profile["capabilities"]["resume"], "unsupported")

    def test_capability_state_matrix_preserves_unsupported(self):
        profile = dict(self.profiles["codex"])
        profile["capabilities"] = dict(profile["capabilities"])
        profile["capabilities"]["resume"] = "unsupported"
        manifest_path = Path(tempfile.mkdtemp()) / "state.json"
        runtime.create_manifest(manifest_path, "capability-state", [{"id": "task-1", "status": "pending"}], profile=profile)
        manifest = runtime.load_manifest(manifest_path)
        self.assertEqual(manifest["capabilities"]["resume"]["state"], "unsupported")
        self.assertNotEqual(manifest["capabilities"]["resume"]["state"], "degraded")

    def test_registry_probe_accepts_isolated_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rows = hooks_probe.runtime_profile_rows(Path(directory))
            self.assertEqual({row.runtime_id for row in rows}, set(self.expected_ids["canonical_ids"]) | set(self.expected_ids["deferred_ids"]))
            self.assertTrue(all(str(Path(directory)) not in row.detail for row in rows))

    def test_activation_owner_stages_and_probes_loaded_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = capabilities.activate("codex", ROOT / "agents/skills/execute-plan", Path(directory) / "loaded")
            self.assertEqual(result["status"], "success")
            self.assertIn("loaded_root", result)
            loaded = Path(result["loaded_root"])
            for relative in (
                "package-manifest.toml",
                "registry.toml",
                "runtime/execute_plan_runtime.py",
                "runtime/execute_plan_runtime_codex.py",
                "runtime/runtime_capabilities.py",
            ):
                self.assertTrue((loaded / relative).is_file(), relative)
            receipt = json.loads((loaded / "activation-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["runtime"], "codex")

    def test_activation_failure_restores_previous_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loaded_root = Path(directory) / "loaded"
            first = capabilities.activate("codex", ROOT / "agents/skills/execute-plan", loaded_root)
            previous_target = loaded_root.resolve()
            with mock.patch.object(Path, "write_text", side_effect=OSError("receipt write failed")):
                with self.assertRaises(OSError):
                    capabilities.activate("codex", ROOT / "agents/skills/execute-plan", loaded_root)
            self.assertEqual(loaded_root.resolve(), previous_target)
            self.assertTrue((loaded_root / "runtime/execute_plan_runtime.py").is_file())

    def test_unsupported_adapter_methods_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            adapter = capabilities.resolve_adapter("claude", directory)
            self.assertEqual(adapter.launch({"id": "task-1"}, "prompt", 1)["status"], "blocked")
            self.assertEqual(adapter.wait("session-1", task_id="task-1")["reason_code"], "runtime-policy-unavailable")

    def test_normative_action_envelope_example_matches_active_schema(self) -> None:
        match = re.search(r"## Action envelope and policy token.*?```json\n(.*?)\n```", self.contract, re.S)
        self.assertIsNotNone(match)
        example = json.loads(match.group(1))
        envelope = runtime.ActionEnvelope.from_mapping(example)
        self.assertEqual(envelope.operation_kind, "repository-task")
        self.assertFalse(envelope.network)
        self.assertTrue(envelope.evidence)


if __name__ == "__main__":
    unittest.main()
