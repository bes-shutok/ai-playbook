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
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path

import runtime_capabilities as capabilities
import hooks_probe
import execute_plan_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "projects/.ai-playbook/execute-plan-runtime-inventory.toml"
CONTRACT_PATH = ROOT / "agents/skills/execute-plan/runtime-contract.md"
ADAPTER_PROFILE_PATH = ROOT / "agents/skills/execute-plan/runtime-adapters/codex.md"
RUNTIME_LAYOUT_PATH = ROOT / "projects/.ai-playbook/agent-runtime-layout.md"
AGTERM_CATALOG_PATH = ROOT / "agents/skills/agterm/agent-runtimes.md"
HOOK_PROBE_PATH = ROOT / "scripts/hooks_probe.py"
EXPECTED_IDS_PATH = ROOT / "scripts/testdata/execute-plan/expected-runtime-ids.json"
ACTIVATION_FIXTURE_PATH = ROOT / "scripts/testdata/execute-plan/activation"

PLANS_SKILL_PATH = ROOT / "agents/skills/plans/SKILL.md"
EXECUTE_PLAN_SKILL_PATH = ROOT / "agents/skills/execute-plan/SKILL.md"

# The normative shared skill bodies: the neutral core of the execute-plan
# contract. They must never name a host runtime; host behavior belongs in
# adapter profiles under agents/skills/execute-plan/runtime-adapters/.
SHARED_SKILL_PATHS = (
    PLANS_SKILL_PATH,
    EXECUTE_PLAN_SKILL_PATH,
    ROOT / "agents/skills/execute-plan/subagent-prompts.md",
    ROOT / "agents/skills/execute-plan/agent-logs.md",
)

# Cross-artifact contract pointers pinned by the coherence test: the neutral
# authoring (plans) and execution (execute-plan) artifacts reference the
# normative runtime contract and the adapter-profile home, the contract
# points back at the profile home it defines, and the adapter profile alone
# carries host-specific mechanics as a registry projection.
CONTRACT_REFERENCE = "agents/skills/execute-plan/runtime-contract.md"
ADAPTER_PROFILE_DIR_REFERENCE = "agents/skills/execute-plan/runtime-adapters/"

# Finite vendor and agent runtime names, vendor-specific commands, and
# vendor-specific event-envelope terms banned from the shared skill bodies.
# Generic scheduler and driver vocabulary stays allowed.
FORBIDDEN_SHARED_RUNTIME_TERMS: tuple[str, ...] = (
    # Vendor and agent runtime names (the registry's canonical ids).
    "claude",
    "codex",
    "cursor",
    "zcode",
    "opencode",
    "copilot",
    "gemini",
    "antigravity",
    "pi",
    # Vendor-specific commands.
    "codex exec",
    # Vendor-specific event-envelope terms.
    "jsonl",
    "hooks.json",
    "pretooluse",
    "mcp__",
    # Vendor-specific CLI flags.
    "--resume",
)

# The four incident obligations the adapter-profile contract must carry. For
# each obligation: the markers naming the obligation and the refusal-witness
# markers proving its refusal and recovery semantics. Every marker must
# appear in the runtime contract or the adapter profile combined.
ADAPTER_INCIDENT_OBLIGATIONS = (
    (
        "lifecycle and capacity reconciliation",
        ("worker registry", "capacity reconciliation"),
        ("stale inventory", "not_found", "stalled worker"),
    ),
    (
        "atomic handoff ownership rotation",
        ("atomic handoff",),
        ("owner mismatch", "replayed handoff"),
    ),
    (
        "machine-verifiable evidence",
        ("machine-verifiable evidence",),
        ("malformed receipt",),
    ),
    (
        "interruption reconciliation",
        ("interruption reconciliation",),
        ("non-resumable interruption",),
    ),
)

# Registry-owned profile fields the adapter profile must not assign; their
# values live only in the inventory registry.
REGISTRY_OWNED_PROFILE_FIELDS = (
    "adapter_entrypoint",
    "launch_operation",
    "wait_operation",
    "resume_operation",
    "adapter_version",
    "approval_policy",
    "retry_budget",
    "eligibility",
    "capabilities",
    "fallback",
)


def _expected_ids() -> dict[str, list[str]]:
    return json.loads(EXPECTED_IDS_PATH.read_text(encoding="utf-8"))


def _normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def find_forbidden_shared_terms(
    text: str, terms: tuple[str, ...] = FORBIDDEN_SHARED_RUNTIME_TERMS
) -> list[str]:
    """Return the forbidden terms present in ``text``.

    A term edge that is alphanumeric requires a non-alphanumeric neighbor, so
    a short runtime name such as ``pi`` never matches inside ``pipeline``;
    terms with a non-alphanumeric edge (``--resume``, ``mcp__``) keep plain
    substring semantics.
    """

    lowered = text.lower()
    found: list[str] = []
    for term in terms:
        head = r"(?<![a-z0-9])" if term[0].isalnum() else ""
        tail = r"(?![a-z0-9])" if term[-1].isalnum() else ""
        if re.search(head + re.escape(term) + tail, lowered):
            found.append(term)
    return found


class RuntimeCapabilitiesTest(unittest.TestCase):
    def test_single_declaration_parser_home(self):
        # The single-parser invariant census. Census domain: every non-test
        # runtime script under scripts/, with exactly two exclusions stated
        # here: scripts/plan_readiness.py (the sanctioned second grammar
        # consumer, exempt from the census by the declaration-contract
        # design) and this census test's own file (a test module, named so
        # the exclusion is explicit). The census keys on the runtime
        # declaration parser's identifying markers: the `_TASK_FILE_ENTRY`
        # entry-pattern source and the `_plan_declared_files` entry point.
        # Both must appear in exactly one script: the runtime's sole
        # declaration-parsing source.
        scripts_dir = ROOT / "scripts"
        excluded = {"plan_readiness.py", "test_runtime_capabilities.py"}
        candidates = sorted(
            path for path in scripts_dir.glob("*.py")
            if not path.name.startswith("test_") and path.name not in excluded
        )
        markers = ("_TASK_FILE_ENTRY", "_plan_declared_files")
        homes = {marker: [path.name for path in candidates if marker in path.read_text(encoding="utf-8")] for marker in markers}
        for marker, owners in homes.items():
            self.assertEqual(owners, ["execute_plan_runtime.py"], (marker, owners))

    def test_evidence_contract_enforces_utf8_item_and_envelope_limits(self):
        self.assertEqual(len(capabilities.evidence_criterion_ids(["é" * 256])), 1)
        with self.assertRaisesRegex(ValueError, "item byte limit"):
            capabilities.evidence_criterion_ids(["é" * 257])
        with self.assertRaisesRegex(ValueError, "aggregate byte limit"):
            capabilities.evidence_criterion_ids([chr(97 + index) + "a" * 511 for index in range(9)])
        with self.assertRaisesRegex(ValueError, r"receipt item-count limit \(100\)"):
            capabilities.evidence_criterion_ids([f"c{index:03d}" for index in range(101)])
        contract = {"task-1": {"required_criteria": ["é" * 256], "verification_commands": [{"id": "v", "argv": ["true"], "criteria": ["é" * 256]}], "allowed_paths": []}}
        self.assertTrue(capabilities.evidence_contract_digest(contract))

    def test_evidence_envelope_requires_driver_captured_machine_fields(self):
        evidence = {
            "version": 1,
            "command": ["python3", "-m", "unittest", "test_runtime_capabilities"],
            "working_directory": "/repo/scripts",
            "exit_status": 0,
            "output_digest": "sha256:" + "a" * 64,
            "stdout_digest": "sha256:" + "b" * 64,
            "stderr_digest": "sha256:" + "c" * 64,
            "selected_tests": ["EvidenceVerifierTest.test_accepts_command_identity_and_criterion_coverage"],
            "baseline_paths": ["scripts/runtime_capabilities.py"],
            "changed_paths": ["scripts/runtime_capabilities.py"],
            "allowed_paths": ["scripts/runtime_capabilities.py"],
            "criteria": ["criterion-1"],
            "verified_by": "runtime-driver",
            "task_id": "task-4",
            "claim_token": "claim-4",
            "generation": 1,
            "launch_id": "launch-4",
            "evidence_contract_digest": "c" * 64,
            "source_digest": "sha256:" + "d" * 64,
        }
        self.assertEqual(capabilities.normalize_evidence_envelope(evidence), evidence)
        for field in ("command", "working_directory", "exit_status", "output_digest", "stdout_digest", "stderr_digest", "selected_tests", "changed_paths", "criteria"):
            malformed = dict(evidence)
            malformed.pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                capabilities.normalize_evidence_envelope(malformed)

    def test_evidence_envelope_rejects_worker_authored_facts_and_failed_commands(self):
        evidence = {
            "version": 1,
            "command": ["pytest"],
            "working_directory": "/repo",
            "exit_status": 0,
            "output_digest": "sha256:" + "b" * 64,
            "stdout_digest": "sha256:" + "b" * 64,
            "stderr_digest": "sha256:" + "c" * 64,
            "selected_tests": ["test_a"],
            "baseline_paths": [],
            "changed_paths": [],
            "allowed_paths": ["a.py"],
            "criteria": ["criterion-1"],
            "verified_by": "worker",
            "task_id": "task-4",
            "claim_token": "claim-4",
            "generation": 1,
            "launch_id": "launch-4",
            "evidence_contract_digest": "c" * 64,
            "source_digest": "sha256:" + "d" * 64,
        }
        with self.assertRaisesRegex(ValueError, "runtime driver"):
            capabilities.normalize_evidence_envelope(evidence)
        evidence["verified_by"] = "runtime-driver"
        evidence["exit_status"] = "0"
        with self.assertRaisesRegex(ValueError, "integer"):
            capabilities.normalize_evidence_envelope(evidence)

    def test_evidence_contract_digest_ignores_progress_and_tracks_contract(self):
        tasks = {"4": {"required_criteria": ["green"], "verification_commands": [{"id": "unit", "argv": ["python3", "-m", "unittest"], "criteria": ["green"]}], "allowed_paths": ["a.py"], "status": "pending", "checkbox": False}}
        initial = capabilities.evidence_contract_digest(tasks)
        tasks["4"].update({"status": "complete", "checkbox": True})
        self.assertEqual(capabilities.evidence_contract_digest(tasks), initial)
        tasks["4"]["required_criteria"] = ["green", "hygiene"]
        tasks["4"]["verification_commands"][0]["criteria"] = ["green", "hygiene"]
        self.assertNotEqual(capabilities.evidence_contract_digest(tasks), initial)

    def test_legacy_digest_skips_enforcement_for_pre_upgrade_criteria(self):
        # A pre-upgrade manifest's criteria exceed the post-upgrade receipt
        # limits; the legacy digest shape (include_criterion_ids=False)
        # validates them as written, while the enforced shape refuses.
        oversized = "x" * 513
        tasks = {"4": {"required_criteria": [oversized], "verification_commands": [{"id": "unit", "argv": ["python3", "-m", "unittest"], "criteria": [oversized]}], "allowed_paths": ["a.py"]}}
        legacy = capabilities.evidence_contract_digest(tasks, include_criterion_ids=False)
        self.assertTrue(legacy)
        with self.assertRaises(ValueError):
            capabilities.evidence_contract_digest(tasks, include_criterion_ids=True)
        many = [f"criterion-{index:03d}" for index in range(101)]
        tasks_many = {"4": {"required_criteria": many, "verification_commands": [{"id": "unit", "argv": ["true"], "criteria": many}], "allowed_paths": ["a.py"]}}
        self.assertTrue(capabilities.evidence_contract_digest(tasks_many, include_criterion_ids=False))
        with self.assertRaises(ValueError):
            capabilities.evidence_contract_digest(tasks_many, include_criterion_ids=True)

    def test_driver_evidence_is_bound_to_allowlisted_source_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git_env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
            subprocess.run(["git", "init", "-q"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=root, env=git_env, check=True)
            source = root / "task.py"
            source.write_text("print('initial')\n", encoding="utf-8")
            subprocess.run(["git", "add", "task.py"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, env=git_env, check=True)
            manifest_path = root / "runtime_state.json"
            task = {
                "id": "task-1", "status": "pending", "allowed_paths": ["task.py"],
                "required_criteria": ["tests-green"],
                "verification_commands": [
                    {"id": "unit", "argv": [os.sys.executable, "-c", "print('ok')"], "criteria": ["tests-green"]},
                    {"id": "fail", "argv": [os.sys.executable, "-c", "raise SystemExit(2)"], "criteria": ["tests-green"]},
                ],
            }
            runtime.create_manifest(manifest_path, "evidence-source", [task], repo_root=root)
            state = runtime.load_manifest(manifest_path)
            state["evidence_enforcement"] = True
            state["claims"]["task-1"] = {
                "task_id": "task-1", "state": "launched", "token": "claim-token", "generation": 1,
                "launch_id": "launch-id", "allowed_paths": ["task.py"], "baseline_revision": "",
            }
            runtime._safe_write_json(manifest_path, state)
            source.write_text("print('verified')\n", encoding="utf-8")
            baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, env=git_env, capture_output=True, text=True, check=True).stdout.strip()
            driver = runtime.RuntimeDriver(manifest_path, owner="test-owner", repo_root=root)
            result = {
                "status": "success", "reason_code": "completed", "evidence": ["worker receipt"],
                "action_scope": "repository-task", "checkpoint_identity": "task-1:worker",
                "generation": 1, "claim_token": "claim-token",
            }
            before_narrative = manifest_path.read_bytes()
            narrative = driver.validate_adapter_result(result)
            self.assertEqual(narrative["reason_code"], "malformed-result")
            self.assertEqual(manifest_path.read_bytes(), before_narrative)
            captured = driver.capture_verification_evidence("task-1", "unit")
            self.assertEqual(captured["status"], "success", captured)
            self.assertEqual(driver.validate_adapter_result(result)["status"], "success")
            failed_command = driver.capture_verification_evidence("task-1", "fail")
            self.assertEqual(failed_command["reason_code"], "contract-violation")
            valid_state = runtime.load_manifest(manifest_path)
            for field, value in (("working_directory", str(root / "wrong")), ("criteria", []), ("verified_by", "worker"), ("launch_id", "other-launch"), ("exit_status", 2)):
                with self.subTest(field=field):
                    altered_state = copy.deepcopy(valid_state)
                    altered_state["verification_evidence"]["task-1"]["unit"][field] = value
                    runtime._safe_write_json(manifest_path, altered_state)
                    before = manifest_path.read_bytes()
                    refused = driver.validate_adapter_result(result)
                    self.assertEqual(refused["status"], "blocked")
                    self.assertEqual(manifest_path.read_bytes(), before)
            runtime._safe_write_json(manifest_path, valid_state)
            subprocess.run(["git", "add", "task.py"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "commit", "-qm", "verified"], cwd=root, env=git_env, check=True)
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, env=git_env, capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(driver._task_source_digest(["task.py"], revision=commit), captured["envelope"]["source_digest"])
            state = runtime.load_manifest(manifest_path)
            state["claims"]["task-1"].update({"baseline_revision": baseline, "policy_token": {"allowed_paths": ["task.py"]}})
            runtime._safe_write_json(manifest_path, state)
            with mock.patch.object(driver, "_claim_drift_outcome", return_value=None):
                self.assertIsNone(driver._done_boundary_block(state["claims"]["task-1"], commit, "task-1:done", 1, state))
            source.write_text("print('after')\n", encoding="utf-8")
            subprocess.run(["git", "add", "task.py"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "commit", "-qm", "unverified"], cwd=root, env=git_env, check=True)
            changed_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, env=git_env, capture_output=True, text=True, check=True).stdout.strip()
            with mock.patch.object(driver, "_claim_drift_outcome", return_value=None):
                refused_commit = driver._done_boundary_block(state["claims"]["task-1"], changed_commit, "task-1:done", 1, state)
            self.assertEqual(refused_commit["reason_code"], "commit-pending")
            stale = driver.validate_adapter_result(result)
            self.assertEqual(stale["status"], "blocked")
            self.assertEqual(stale["reason_code"], "malformed-result")

    def test_two_drivers_cannot_reserve_the_same_last_capacity_slot(self):
        class InventoryAdapter:
            def observe_inventory(self):
                return {"version": 1, "observation_kind": "inventory", "state": "available", "observed_at": time.monotonic(), "freshness_window": 30, "capacity_slot_effect": "retain", "inventory": []}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git_env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
            subprocess.run(["git", "init", "-q"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "config", "user.name", "Runtime Test"], cwd=root, env=git_env, check=True)
            (root / ".gitignore").write_text("runtime_state.json\nruntime_state.json.lock\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore"], cwd=root, env=git_env, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, env=git_env, check=True)
            manifest_path = root / "runtime_state.json"
            # The seed records the runtime id like every create boundary since
            # the claim-boundary runtime-identity gate: a manifest with no
            # recorded runtime id refuses the group claim before the capacity
            # race this witness exercises can start.
            runtime.create_manifest(manifest_path, "capacity-race", [
                {"id": "task-1", "number": 1, "status": "pending", "allowed_paths": ["task-1.txt"]},
                {"id": "task-2", "number": 2, "status": "pending", "allowed_paths": ["task-2.txt"]},
            ], repo_root=root, runtime_id="codex")
            first_driver = runtime.RuntimeDriver(manifest_path, owner="race-test", repo_root=root, adapter=InventoryAdapter())
            claimed = first_driver.claim_parallel_group(["task-1", "task-2"])
            self.assertEqual(claimed["status"], "success")
            claims = runtime.load_manifest(manifest_path)["claims"]
            barrier = threading.Barrier(2)
            outcomes = {}

            def reserve(task_id):
                barrier.wait(timeout=2)
                driver = runtime.RuntimeDriver(manifest_path, owner="race-test", repo_root=root, adapter=InventoryAdapter())
                outcomes[task_id] = driver._mark_claim_launched(claims[task_id], task_id, {"allowed_paths": [f"{task_id}.txt"]})

            workers = [threading.Thread(target=reserve, args=(task_id,)) for task_id in ("task-1", "task-2")]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=5)
            self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(sum(outcome is None for outcome in outcomes.values()), 1, outcomes)
            self.assertEqual(sum(isinstance(outcome, dict) and outcome.get("status") == "blocked" for outcome in outcomes.values()), 1, outcomes)
            reservations = runtime.load_manifest(manifest_path)["capacity"]["reservations"]
            self.assertEqual(len(reservations), 1)

    def test_startup_reconciliation_ignores_unrelated_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "runtime_state.json"
            runtime.create_manifest(
                manifest_path,
                "dirty-startup",
                [{"id": "task-1", "status": "pending", "allowed_paths": ["owned.py"]}],
            )
            driver = runtime.RuntimeDriver(manifest_path, repo_root=root)
            with mock.patch.object(driver, "_git_worktree_dirty", return_value=True), mock.patch.object(
                driver, "_git_worktree_entries", return_value=[("??", "manual-change.py")]
            ):
                result = driver.reconcile_startup()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["reason_code"], "completed")

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
        leaked = find_forbidden_shared_terms(provider_neutral)
        self.assertEqual(
            leaked,
            [],
            "host protocol leaked: " + ", ".join(leaked),
        )

    def test_shared_skill_bodies_have_no_runtime_names(self) -> None:
        # Behavior witnesses for the matcher: the finite term set fires on a
        # vendor name, a vendor command, and a vendor event-envelope term,
        # while generic scheduler/driver vocabulary and words merely
        # containing a short name (``pipeline``) stay allowed.
        self.assertEqual(
            find_forbidden_shared_terms("use codex exec with jsonl events"),
            ["codex", "codex exec", "jsonl"],
        )
        self.assertEqual(
            find_forbidden_shared_terms(
                "The scheduler starts one driver per task and pipelines the probes."
            ),
            [],
        )
        violations: list[str] = []
        for path in SHARED_SKILL_PATHS:
            self.assertTrue(path.is_file(), f"missing shared skill file: {path}")
            for term in find_forbidden_shared_terms(path.read_text(encoding="utf-8")):
                violations.append(f"{path.relative_to(ROOT)}: {term}")
        self.assertEqual(
            violations,
            [],
            "shared skill bodies must not name a vendor runtime, vendor command, "
            "or vendor event envelope:\n" + "\n".join(violations),
        )

    def test_adapter_profile_carries_all_incident_obligations(self) -> None:
        if not ADAPTER_PROFILE_PATH.is_file():
            self.fail(
                f"missing adapter profile {ADAPTER_PROFILE_PATH.relative_to(ROOT)}: "
                "every incident obligation lacks its adapter-profile carrier, so "
                "no obligation names its refusal witness"
            )
        combined = _normalized(
            self.contract + ADAPTER_PROFILE_PATH.read_text(encoding="utf-8")
        )
        for label, obligations, witnesses in ADAPTER_INCIDENT_OBLIGATIONS:
            for phrase in obligations:
                self.assertIn(
                    _normalized(phrase),
                    combined,
                    f"{label}: missing obligation marker {phrase!r}",
                )
            for phrase in witnesses:
                self.assertIn(
                    _normalized(phrase),
                    combined,
                    f"{label}: missing refusal witness {phrase!r}",
                )

    def _assert_profile_references_registry_without_duplicate_owner(
        self, profile_text: str
    ) -> None:
        """Pin the adapter profile as a registry projection, not a second owner.

        The profile names the canonical runtime ID and the registry path,
        assigns no registry-owned field, and copies no registry-owned value.
        Shared by the direct ownership test and the cross-artifact coherence
        test so the two checks cannot drift apart.
        """

        normalized_profile = _normalized(profile_text)

        # The profile references the canonical runtime ID and the registry
        # path instead of restating any registry-owned value.
        self.assertIn("codex", self.inventory["inventory"]["canonical_ids"])
        self.assertRegex(profile_text, r"(?i)(?<![a-z0-9])codex(?![a-z0-9])")
        self.assertIn(
            _normalized("canonical runtime id"),
            normalized_profile,
            "profile must name the canonical runtime ID it projects",
        )
        registry_path = self.inventory["inventory"]["registry_path"]
        self.assertIn(
            _normalized(registry_path),
            normalized_profile,
            "profile must reference the registry path",
        )

        # No second capability owner: registry-owned fields appear in the
        # profile only as references, never as assignments or table rows, and
        # the registry-unique capability field names never appear at all.
        for field in REGISTRY_OWNED_PROFILE_FIELDS:
            self.assertNotRegex(
                profile_text,
                rf"(?im)^\s*\|?\s*`?{field}`?\s*(?:[:=]|\|)",
                f"profile must not assign registry-owned field {field}",
            )
        for capability in ("parent_continuation", "final_response"):
            self.assertNotIn(
                capability,
                profile_text,
                f"profile duplicates registry-owned capability {capability}",
            )

        # Registry-owned authoritative values are not copied into the profile.
        codex_row = self.inventory["runtimes"]["codex"]
        registry_owned_values = (
            "adapter_entrypoint",
            "launch_operation",
            "wait_operation",
            "resume_operation",
            "approval_policy",
            "fallback",
        )
        for field in registry_owned_values:
            value = codex_row[field]
            self.assertTrue(value, f"registry lost its {field} value")
            self.assertNotRegex(
                profile_text,
                re.escape(value),
                f"profile duplicates registry-owned {field} value {value!r}",
            )

    def test_profile_references_registry_without_duplicate_capability_owner(self) -> None:
        if not ADAPTER_PROFILE_PATH.is_file():
            self.fail(
                f"missing adapter profile {ADAPTER_PROFILE_PATH.relative_to(ROOT)}: "
                "no profile-to-registry reference exists and no duplicate "
                "capability owner can be ruled out"
            )
        self._assert_profile_references_registry_without_duplicate_owner(
            ADAPTER_PROFILE_PATH.read_text(encoding="utf-8")
        )

    def test_cross_artifact_contract_coherence(self) -> None:
        """plans, execute-plan, the runtime contract, and the adapter profile
        stay one linked contract set: the neutral authoring and execution
        artifacts reference the adapter-profile contract and carry no
        forbidden shared-runtime term, the contract points back at the
        profile home it defines, and the adapter profile alone carries
        host-specific lifecycle mechanics as a registry projection that
        duplicates no registry-owned profile value."""

        plans_text = PLANS_SKILL_PATH.read_text(encoding="utf-8")
        execute_plan_text = EXECUTE_PLAN_SKILL_PATH.read_text(encoding="utf-8")
        profile_text = ADAPTER_PROFILE_PATH.read_text(encoding="utf-8")

        # The authoring and execution boundaries point at the same normative
        # contract and the same adapter-profile home, so a future edit cannot
        # move one boundary and strand the other.
        for label, text in (("plans", plans_text), ("execute-plan", execute_plan_text)):
            self.assertIn(
                CONTRACT_REFERENCE,
                text,
                f"{label} skill must reference the normative runtime contract",
            )
            self.assertIn(
                ADAPTER_PROFILE_DIR_REFERENCE,
                text,
                f"{label} skill must reference the adapter-profile contract home",
            )

        # The contract-to-profile direction of the same link: the contract
        # defines the profile contract section and points at the profile home.
        self.assertIn(
            "## Adapter profile contract",
            self.contract,
            "runtime contract must define the adapter profile contract section",
        )
        self.assertIn(
            ADAPTER_PROFILE_DIR_REFERENCE,
            self.contract,
            "runtime contract must reference the adapter-profile home",
        )

        # Neither neutral artifact names a forbidden shared-runtime term, and
        # the provider-neutral part of the contract stays term-free too.
        for label, text in (
            ("plans", plans_text),
            ("execute-plan", execute_plan_text),
            (
                "runtime contract neutral part",
                self.contract.split("## Runtime profile data", maxsplit=1)[0],
            ),
        ):
            leaked = find_forbidden_shared_terms(text)
            self.assertEqual(
                leaked,
                [],
                f"{label} names forbidden shared-runtime terms: " + ", ".join(leaked),
            )

        # Host-specific lifecycle mechanics live in the adapter profile, the
        # one artifact allowed to name them (witnessed here by the vendor
        # launch command the neutral artifacts must never contain).
        self.assertIn(
            "codex exec",
            profile_text,
            "adapter profile must carry the host-specific launch mechanics "
            "banned from the neutral artifacts",
        )

        # The profile stays a non-authoritative registry projection: it
        # references the registry and duplicates no registry-owned value.
        self._assert_profile_references_registry_without_duplicate_owner(profile_text)

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

    def test_batch_result_and_member_policy_validation(self) -> None:
        valid = {
            "batch_id": "group-1",
            "member_id": "task-2",
            "member_ordinal": 2,
            "attempt": 1,
            "session_id": "sess-anchor",
        }
        # a valid batch progress envelope normalizes to itself
        self.assertEqual(capabilities.normalize_batch_progress(dict(valid)), valid)
        # an absent envelope is legitimate: the batch opt-in is optional
        self.assertIsNone(capabilities.normalize_batch_progress(None))
        # missing, stale-typed, and malformed partial envelopes fail closed
        malformed_envelopes = {
            "missing session": {k: v for k, v in valid.items() if k != "session_id"},
            "missing attempt": {k: v for k, v in valid.items() if k != "attempt"},
            "string ordinal": dict(valid, member_ordinal="2"),
            "zero attempt": dict(valid, attempt=0),
            "boolean ordinal": dict(valid, member_ordinal=True),
            "empty batch id": dict(valid, batch_id=""),
            "empty member id": dict(valid, member_id="  "),
            "non-mapping": ["group-1"],
        }
        for label, envelope in malformed_envelopes.items():
            with self.assertRaises(ValueError, msg=label):
                capabilities.normalize_batch_progress(envelope)
        # member receipt validation against expected active group state.
        # r1 F3: the normalized envelope carries no credential, so the
        # conforming receipt is the five-field shape WITHOUT any claim
        # token; the outer receipt's claim token is the authorization input,
        # verified by the driver's checkpoint fence.
        expected = {
            "batch_id": "group-1",
            "member_id": "task-2",
            "member_ordinal": 2,
            "attempt": 1,
        }
        # a conforming normalized envelope (no claim token inside) validates
        self.assertTrue(capabilities.validate_member_receipt(dict(valid), expected))
        # a claim_token key inside the envelope is ignored, never demanded
        self.assertTrue(capabilities.validate_member_receipt(dict(valid, claim_token="other-token"), expected))
        # an expected token field is equally inert: the envelope check pins
        # identity fields only
        self.assertTrue(capabilities.validate_member_receipt(dict(valid), dict(expected, token="member-2-token")))
        # missing, stale, mismatched, or cross-member receipts fail closed
        receipt = dict(valid)
        self.assertFalse(capabilities.validate_member_receipt(None, expected))
        self.assertFalse(capabilities.validate_member_receipt({"batch_id": "group-1"}, expected))
        stale_expected = {
            "stale attempt": dict(expected, attempt=2),
            "mismatched member": dict(expected, member_id="task-3"),
            "wrong batch": dict(expected, batch_id="group-2"),
            "wrong ordinal": dict(expected, member_ordinal=3),
        }
        for label, witness in stale_expected.items():
            self.assertFalse(capabilities.validate_member_receipt(receipt, witness), f"expected rejection for {label}")

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
