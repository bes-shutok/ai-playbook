#!/usr/bin/env python3
"""Tests for the provider-neutral execute-plan runtime registry."""

from __future__ import annotations

import copy
import importlib
import inspect
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
        for reason in ("authorized", "activation-verified", "worktree-witness-unavailable", "done-pending", "commit-pending", "cleanup-required"):
            self.assertIn(reason, capabilities.REASON_CODES)
        # "created" is the CLI create envelope, outside the adapter
        # normalization boundary: it is not an adapter reason code.
        self.assertNotIn("created", capabilities.REASON_CODES)
        self.assertEqual(
            capabilities.RESUMABLE_REASONS,
            {"approval-required", "timeout", "runtime-error", "stale-claim", "cleanup-required", "precondition-unverified"},
        )

    def test_all_documented_runtimes_have_profiles(self) -> None:
        expected_canonical = set(self.expected_ids["canonical_ids"])
        expected_deferred = set(self.expected_ids["deferred_ids"])
        self.assertEqual(
            set(self.inventory["inventory"]["canonical_ids"]),
            expected_canonical,
        )
        self.assertEqual(
            set(self.inventory["inventory"]["deferred_ids"]), expected_deferred
        )
        eligible = expected_canonical - expected_deferred
        self.assertEqual(set(self.profiles), eligible)
        self.assertEqual(eligible, set(self.expected_ids["profiles"]))
        # Count cross-reference: every deferred id owns exactly one deferral row.
        self.assertEqual(
            sorted(self.inventory["deferrals"]),
            sorted(self.inventory["inventory"]["deferred_ids"]),
        )

        required_capabilities = {
            "parent_continuation",
            "final_response",
            "resume",
        }
        catalogs = {
            "runtime-layout": RUNTIME_LAYOUT_PATH.read_text(encoding="utf-8"),
            "agterm": AGTERM_CATALOG_PATH.read_text(encoding="utf-8"),
            "hooks-probe": HOOK_PROBE_PATH.read_text(encoding="utf-8"),
        }
        for runtime_id in eligible:
            profile = self.profiles[runtime_id]
            self.assertEqual(profile["id"], runtime_id)
            self.assertTrue(profile["display_name"])
            module, _, symbol = profile["adapter_entrypoint"].partition(":")
            self.assertIn(module, capabilities.ADAPTER_ENTRYPOINT_MODULES)
            self.assertTrue(symbol)
            self.assertTrue(profile["adapter_version"])
            self.assertTrue(profile["approval_policy"])
            self.assertTrue(profile["fallback"])
            self.assertEqual(set(profile["capabilities"]), required_capabilities)
            for state in profile["capabilities"].values():
                self.assertIn(state, {"full", "degraded", "unsupported"})
            aliases = [_normalized(alias) for alias in profile["aliases"]]
            for catalog_name in profile["source_catalogs"]:
                catalog = _normalized(catalogs[catalog_name])
                self.assertTrue(
                    any(alias in catalog for alias in aliases),
                    f"{runtime_id} is missing from {catalog_name}",
                )

    def test_independent_runtime_ids_match_every_catalog_and_probe(self) -> None:
        canonical = set(self.expected_ids["canonical_ids"])
        deferred = set(self.expected_ids["deferred_ids"])
        all_ids = canonical | deferred
        eligible = canonical - deferred
        self.assertTrue(eligible)
        self.assertEqual(eligible, set(self.expected_ids["profiles"]))
        self.assertIn("codex", eligible)
        self.assertEqual(len(deferred), len(self.expected_ids["deferred_ids"]))
        self.assertIn("pi", deferred)

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

    def _generated_activation_fixture(self, directory: Path) -> Path:
        """Assemble the activation fixture from committed seeds plus a generated loaded tree."""

        root = Path(directory) / "activation"
        root.mkdir()
        shutil.copy2(ACTIVATION_FIXTURE_PATH / "activation.json", root / "activation.json")
        shutil.copy2(ACTIVATION_FIXTURE_PATH / "help_probe.py", root / "help_probe.py")
        capabilities.stage_package(
            ROOT / "agents/skills/execute-plan", root / "loaded" / "execute-plan"
        )
        return root

    def test_verify_activation_against_generated_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._generated_activation_fixture(Path(directory))
            result = capabilities.verify_activation(root)
            self.assertEqual(result["status"], "success")
            self.assertEqual(
                set(result["checked_roles"]), {"skill", "driver", "registry", "adapter"}
            )
            self.assertEqual(result["help_probes"], 2)
            # The generated tree is never written under the committed fixture seeds.
            self.assertFalse((ACTIVATION_FIXTURE_PATH / "loaded").exists())

    def test_runtime_activation_fixture_fails_closed_on_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._generated_activation_fixture(Path(directory))
            drifted = root / "loaded" / "execute-plan" / "runtime" / "execute_plan_runtime.py"
            drifted.write_bytes(drifted.read_bytes() + b"\n")
            with self.assertRaises(ValueError):
                capabilities.verify_activation(root)

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

    def test_bounded_evidence_owned_by_capabilities(self) -> None:
        # Single home: the evidence helpers are defined in the capabilities
        # module only; the driver and the adapter import them from there.
        self.assertTrue(callable(capabilities.bounded_evidence))
        self.assertIsInstance(capabilities.MAX_EVIDENCE_BYTES, int)
        self.assertIsInstance(capabilities.MAX_EVIDENCE_ITEM_BYTES, int)
        driver_source = Path(runtime.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(driver_source, r"(?m)^MAX_EVIDENCE_BYTES\s*=")
        self.assertNotRegex(driver_source, r"(?m)^MAX_EVIDENCE_ITEM_BYTES\s*=")
        self.assertNotRegex(driver_source, r"(?m)^def bounded_evidence\s*\(")
        self.assertRegex(
            driver_source, r"(?m)^from runtime_capabilities import .*bounded_evidence"
        )
        adapter_source = Path(
            importlib.import_module("execute_plan_runtime_codex").__file__
        ).read_text(encoding="utf-8")
        self.assertNotIn("from execute_plan_runtime import", adapter_source)
        self.assertRegex(
            adapter_source, r"(?m)^from runtime_capabilities import .*bounded_evidence"
        )
        # Behavior witness: bounded and redacted regardless of the caller.
        result = capabilities.bounded_evidence(["token=secret", "x" * 2000])
        self.assertLessEqual(sum(map(len, result)), capabilities.MAX_EVIDENCE_BYTES)
        self.assertNotIn("secret", " ".join(result))

    def test_zero_retry_budget_grants_zero_retries(self) -> None:
        error = {
            "status": "error",
            "reason_code": "runtime-error",
            "evidence": ["runner"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1",
            "generation": 1,
        }
        zero = capabilities.normalize_result(dict(error), retry_budget=0)
        self.assertEqual(zero["retry_policy"]["mode"], "none")
        self.assertEqual(zero["retry_policy"]["max_attempts"], 0)
        self.assertEqual(zero["retry_policy"]["attempts_remaining"], 0)
        hostile = dict(
            error,
            retry_policy={"mode": "bounded", "max_attempts": 5000, "attempts_remaining": 5000},
        )
        clamped = capabilities.normalize_result(hostile, retry_budget=0)
        self.assertEqual(clamped["retry_policy"]["mode"], "none")
        self.assertEqual(clamped["retry_policy"]["max_attempts"], 0)
        self.assertEqual(clamped["retry_policy"]["attempts_remaining"], 0)
        granted = capabilities.normalize_result(dict(error), retry_budget=2)
        self.assertEqual(granted["retry_policy"]["max_attempts"], 2)
        self.assertEqual(granted["retry_policy"]["attempts_remaining"], 2)

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
        codex = self.profiles["codex"]["capabilities"]
        self.assertEqual(codex["parent_continuation"], "full")
        self.assertEqual(codex["resume"], "full")
        self.assertEqual(codex["final_response"], "degraded")
        # Deferral rows carry no lifecycle capabilities; the deferral itself
        # is the unsupported statement and resolve_adapter returns the
        # fail-closed UnsupportedAdapter carrying the deferral reason.
        with tempfile.TemporaryDirectory() as directory:
            for runtime_id, row in self.inventory["deferrals"].items():
                self.assertNotIn("capabilities", row)
                adapter = capabilities.resolve_adapter(runtime_id, directory)
                self.assertIsInstance(adapter, capabilities.UnsupportedAdapter, runtime_id)

    def test_resolve_adapter_uses_entrypoint_mapping(self) -> None:
        from execute_plan_runtime_codex import CodexAdapter

        with tempfile.TemporaryDirectory() as directory:
            adapter = capabilities.resolve_adapter("codex", directory, approval_verified=False)
            self.assertIsInstance(adapter, CodexAdapter)
            self.assertTrue(callable(adapter.launch))
            self.assertTrue(callable(adapter.resume))

            # A profile naming a missing entrypoint fails closed as a registry
            # error; the ImportError must never leak across the boundary.
            drifted = copy.deepcopy(self.inventory)
            drifted["runtimes"]["codex"]["adapter_entrypoint"] = "missing_runtime_adapter:Nothing"
            with mock.patch.object(capabilities, "load_inventory", return_value=drifted):
                with self.assertRaises(ValueError):
                    capabilities.resolve_adapter("codex", directory)

            # A profile naming a blank entrypoint is rejected by
            # validate_inventory before any profile resolves; a drifted
            # (unvalidated) inventory reaching resolve_adapter fails closed
            # as a registry error instead of an UnsupportedAdapter branch.
            unbound = copy.deepcopy(self.inventory)
            unbound["runtimes"]["codex"]["adapter_entrypoint"] = ""
            with self.assertRaises(ValueError):
                capabilities.validate_inventory(unbound)
            with mock.patch.object(capabilities, "load_inventory", return_value=unbound):
                with self.assertRaises(ValueError):
                    capabilities.resolve_adapter("codex", directory)

    def test_deferred_runtime_resolves_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            adapter = capabilities.resolve_adapter("pi", directory)
            self.assertIsInstance(adapter, capabilities.UnsupportedAdapter)
            self.assertEqual(
                adapter.reason,
                "Execute-plan resume behavior is not documented or verified for Pi.",
            )
            claude_adapter = capabilities.resolve_adapter("claude", directory)
            self.assertIsInstance(claude_adapter, capabilities.UnsupportedAdapter)
            self.assertEqual(claude_adapter.reason, "no verified adapter")
            blocked = claude_adapter.launch({"id": "task-1"}, "prompt", 1)
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(blocked["reason_code"], "runtime-policy-unavailable")

    def test_inventory_deferrals_section(self) -> None:
        deferred_ids = list(self.inventory["inventory"]["deferred_ids"])
        deferrals = self.inventory["deferrals"]
        self.assertEqual(len(deferred_ids), 8)
        self.assertEqual(set(deferrals), set(deferred_ids))
        reasons: dict[str, str] = {}
        for runtime_id in deferred_ids:
            row = deferrals[runtime_id]
            self.assertEqual(row["id"], runtime_id)
            self.assertTrue(row["display_name"], runtime_id)
            self.assertTrue(row["aliases"], runtime_id)
            self.assertEqual(row["eligibility"], "deferred", runtime_id)
            self.assertNotIn("capabilities", row, runtime_id)
            reasons[runtime_id] = row["reason"]
        for runtime_id in (
            "claude",
            "cursor",
            "zcode",
            "opencode",
            "copilot",
            "gemini",
            "antigravity",
        ):
            self.assertEqual(reasons[runtime_id], "no verified adapter", runtime_id)
        self.assertEqual(
            reasons["pi"],
            "Execute-plan resume behavior is not documented or verified for Pi.",
        )

        # Eligible profiles keep the adapter entrypoint plus the receipt
        # capabilities consumers read.
        codex = self.inventory["runtimes"]["codex"]
        self.assertEqual(codex["adapter_entrypoint"], "execute_plan_runtime_codex:CodexAdapter")
        self.assertEqual(
            set(codex["capabilities"]),
            {"parent_continuation", "final_response", "resume"},
        )

        # validate_inventory retains malformed-row rejection: a deferral row
        # missing its reason fails.
        malformed = copy.deepcopy(self.inventory)
        malformed["deferrals"]["pi"] = {
            key: value
            for key, value in malformed["deferrals"]["pi"].items()
            if key != "reason"
        }
        with self.assertRaises(ValueError):
            capabilities.validate_inventory(malformed)

    def test_no_name_based_adapter_special_case(self) -> None:
        source = Path(capabilities.__file__).read_text(encoding="utf-8")
        self.assertNotIn("runtime-adapter:", source)
        resolver_source = inspect.getsource(capabilities.resolve_adapter)
        self.assertNotIn("codex", resolver_source)

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

    def _receipt(self, root: Path, name: str, payload: dict, mode: int = 0o600) -> Path:
        receipt = root / name
        receipt.write_text(json.dumps(payload), encoding="utf-8")
        receipt.chmod(mode)
        return receipt

    def _receipt_config(self, root: Path, name: str = "config.toml", body: str = 'approval_policy = "never"\n') -> Path:
        config = root / name
        config.write_text(body, encoding="utf-8")
        return config

    def test_single_policy_token_validator(self) -> None:
        codex_module = importlib.import_module("execute_plan_runtime_codex")
        # One parameterized validator in runtime_capabilities.py serves both
        # boundaries; the codex-local copies are deleted.
        self.assertTrue(callable(capabilities.validate_policy_token))
        self.assertFalse(hasattr(codex_module, "_valid_policy_token"))
        self.assertFalse(hasattr(codex_module.CodexAdapter, "_validate_policy_token"))
        token = {
            "token": "policy",
            "repo_root": "/repo",
            "allowed_paths": ["task.txt"],
            "operation_kind": "repository-task",
            "network": False,
            "generation": 1,
        }
        # Launch-validity boundary: operation gating and token shape.
        self.assertTrue(capabilities.validate_policy_token(token, operation="launch"))
        self.assertFalse(capabilities.validate_policy_token(None, operation="launch"))
        self.assertFalse(capabilities.validate_policy_token(token, operation="activation-version"))
        self.assertFalse(capabilities.validate_policy_token(dict(token, repo_root="repo/relative"), operation="launch"))
        # Claim-revalidation boundary: equality binding to the adapter claim.
        self.assertTrue(capabilities.validate_policy_token(token, repo_root="/repo", generation=1))
        witnesses = {
            "repo-root mismatch": dict(token, repo_root="/other"),
            "generation mismatch": dict(token, generation=2),
            "foreign absolute repo root": dict(token, repo_root="/foreign/absolute"),
        }
        for label, witness in witnesses.items():
            self.assertFalse(
                capabilities.validate_policy_token(witness, repo_root="/repo", generation=1),
                f"expected rejection for {label}",
            )
        # The adapter routes both boundaries through the single validator.
        adapter = codex_module.CodexAdapter("/repo", runner=lambda *args, **kwargs: {})
        for label, witness in witnesses.items():
            blocked = adapter.launch({"id": "task-1"}, "implement", 1, policy_token=witness)
            self.assertEqual(blocked["reason_code"], "runtime-policy-unavailable", f"expected rejection for {label}")

    def test_load_approval_receipt_requires_owner_only_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._receipt_config(root)
            fingerprint = capabilities.approval_policy_fingerprint(config)

            def payload(**overrides: object) -> dict:
                data = {
                    "runtime": "codex",
                    "approval": "verified",
                    "config_path": str(config),
                    "policy_fingerprint": fingerprint,
                }
                data.update(overrides)
                return data

            permissive = self._receipt(root, "permissive.json", payload(), mode=0o644)
            with self.assertRaises(ValueError):
                capabilities.load_approval_receipt(permissive)
            owner_only = self._receipt(root, "owner-only.json", payload(), mode=0o600)
            self.assertEqual(capabilities.load_approval_receipt(owner_only)["runtime"], "codex")
            for field in ("config_path", "policy_fingerprint"):
                incomplete = self._receipt(root, f"missing-{field}.json", payload(**{field: None}), mode=0o600)
                with self.assertRaises(ValueError):
                    capabilities.load_approval_receipt(incomplete)

    def test_load_approval_receipt_cross_checks_config_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_root = root / "config-root"
            config_root.mkdir()
            config = self._receipt_config(config_root)
            fingerprint = capabilities.approval_policy_fingerprint(config)
            base = {
                "runtime": "codex",
                "approval": "verified",
                "config_path": "config.toml",
                "policy_fingerprint": fingerprint,
            }
            # A relative config path resolves against the injected config root,
            # never the ambient environment.
            receipt = self._receipt(root, "approval.json", base)
            self.assertEqual(capabilities.load_approval_receipt(receipt, config_root=config_root)["approval"], "verified")
            # Recorded config file is missing from the host.
            missing = self._receipt(root, "missing-config.json", dict(base, config_path="absent.toml"))
            with self.assertRaises(ValueError):
                capabilities.load_approval_receipt(missing, config_root=config_root)
            # Recorded non-interactive approval policy is absent.
            self._receipt_config(config_root, "no-policy.toml", body='model = "gpt-5"\n')
            no_policy = self._receipt(root, "no-policy.json", dict(base, config_path="no-policy.toml"))
            with self.assertRaises(ValueError):
                capabilities.load_approval_receipt(no_policy, config_root=config_root)
            # Recomputed fingerprint differs from the recorded one.
            self._receipt_config(config_root, "drifted.toml", body='approval_policy = "on-request"\n')
            drifted = self._receipt(root, "drifted.json", dict(base, config_path="drifted.toml"))
            with self.assertRaises(ValueError):
                capabilities.load_approval_receipt(drifted, config_root=config_root)
            # A relative config path without an injected config root is
            # rejected: it would otherwise resolve against the ambient CWD in
            # production. The error names the receipt path.
            relative = self._receipt(root, "relative-no-root.json", dict(base))
            with self.assertRaises(ValueError) as raised:
                capabilities.load_approval_receipt(relative)
            self.assertIn("relative-no-root.json", str(raised.exception))
            self.assertIn("absolute", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
