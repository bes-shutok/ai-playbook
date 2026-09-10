#!/usr/bin/env python3
"""Load and validate the execute-plan runtime capability registry.

The TOML inventory is the single owner of runtime identity and capability values.
This module validates that data and translates host results into the closed,
provider-neutral result shape used by the execute-plan driver.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = ROOT / "projects/.ai-playbook/execute-plan-runtime-inventory.toml"
CAPABILITY_OWNER = "registry"
CAPABILITY_NAMES = {
    "launch",
    "wait",
    "resume",
    "checkpoint",
    "approval",
    "parent_continuation",
    "final_response",
}
CAPABILITY_STATES = {"full", "degraded", "unsupported"}
NORMALIZED_STATUSES = {
    "success",
    "contract-violation",
    "blocked",
    "aborted",
    "error",
}
BLOCKING_REASON_CODES = {
    "approval-required",
    "cleanup-unverified",
    "malformed-result",
    "runtime-policy-unavailable",
    "stale-claim",
    "owner-mismatch",
    "commit-pending",
    "done-pending",
    "dirty-worktree",
}
# Closed reason-code set: every code the reference driver or adapter emits on
# the normalized result boundary. Unknown or missing codes fail closed as
# malformed results instead of defaulting to an undocumented value.
REASON_CODES = {
    "completed",
    "worker-hesitation",
    "contract-violation",
    "approval-required",
    "timeout",
    "dirty-worktree",
    "cleanup-unverified",
    "malformed-result",
    "owner-mismatch",
    "stale-claim",
    "explicit-abort",
    "runtime-policy-unavailable",
    "runtime-error",
    "authorized",
    "activation-verified",
    "worktree-witness-unavailable",
    "done-pending",
    "commit-pending",
}
# Reason codes whose blocked receipt may resume automatically.
RESUMABLE_REASONS = {"approval-required", "timeout", "runtime-error", "stale-claim"}
PROFILE_FIELDS = {
    "id",
    "display_name",
    "aliases",
    "source_catalogs",
    "eligibility",
    "adapter_entrypoint",
    "launch_operation",
    "wait_operation",
    "resume_operation",
    "capabilities",
    "fallback",
    "adapter_version",
    "approval_policy",
    "retry_budget",
}


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


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


def load_profiles(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Return the eligible runtime profiles keyed by canonical ID."""

    inventory = load_inventory(path)
    return inventory["runtimes"]


def validate_profile(profile: Mapping[str, Any]) -> None:
    """Validate one runtime profile and its explicit capability fallback."""

    missing = PROFILE_FIELDS - set(profile)
    if missing:
        raise ValueError(f"profile missing fields: {sorted(missing)}")
    if not isinstance(profile["id"], str) or not profile["id"]:
        raise ValueError("profile id must be non-empty")
    if profile["eligibility"] != "eligible":
        raise ValueError(f"profile {profile['id']} is not eligible")
    capabilities = profile["capabilities"]
    if not isinstance(capabilities, Mapping):
        raise ValueError(f"profile {profile['id']} capabilities must be a table")
    if set(capabilities) != CAPABILITY_NAMES:
        raise ValueError(
            f"profile {profile['id']} capability fields must be "
            f"{sorted(CAPABILITY_NAMES)}"
        )
    invalid_states = set(capabilities.values()) - CAPABILITY_STATES
    if invalid_states:
        raise ValueError(
            f"profile {profile['id']} has invalid capability states: "
            f"{sorted(invalid_states)}"
        )
    fallback = profile["fallback"]
    if any(state != "full" for state in capabilities.values()) and not (
        isinstance(fallback, str) and fallback.strip()
    ):
        raise ValueError(
            f"profile {profile['id']} needs a fallback for degraded/unsupported capabilities"
        )


def validate_inventory(inventory: Mapping[str, Any]) -> None:
    """Validate registry ownership, IDs, profile shape, and Pi deferral."""

    root = inventory.get("inventory")
    if not isinstance(root, Mapping):
        raise ValueError("inventory table is required")
    if root.get("capability_owner") != CAPABILITY_OWNER:
        raise ValueError("capability values must be owned by the registry")
    canonical_ids = root.get("canonical_ids")
    deferred_ids = root.get("deferred_ids")
    if not isinstance(canonical_ids, list) or not canonical_ids:
        raise ValueError("inventory.canonical_ids must be a non-empty list")
    if len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("inventory.canonical_ids must be unique")
    if not isinstance(deferred_ids, list):
        raise ValueError("inventory.deferred_ids must be a list")
    runtimes = inventory.get("runtimes")
    if not isinstance(runtimes, Mapping):
        raise ValueError("runtimes table is required")
    if set(runtimes) != set(canonical_ids):
        raise ValueError("runtime profile IDs must match inventory.canonical_ids")
    for runtime_id, profile in runtimes.items():
        if profile.get("id") != runtime_id:
            raise ValueError(f"profile key and id differ for {runtime_id}")
        validate_profile(profile)
    deferrals = inventory.get("deferrals")
    if not isinstance(deferrals, Mapping) or set(deferrals) != set(deferred_ids):
        raise ValueError("every deferred runtime needs an explicit deferral record")
    for deferred_id in deferred_ids:
        deferral = deferrals[deferred_id]
        if deferral.get("eligibility") != "deferred" or not deferral.get("reason"):
            raise ValueError(f"deferred runtime {deferred_id} needs a non-empty reason")


def canonicalize_runtime_id(
    value: str, inventory: Mapping[str, Any] | None = None
) -> str:
    """Resolve a canonical runtime ID from a display name or alias."""

    data = inventory or load_inventory()
    needle = _normalized(value)
    for runtime_id, profile in data["runtimes"].items():
        candidates = [runtime_id, profile["display_name"], *profile["aliases"]]
        if needle in {_normalized(candidate) for candidate in candidates}:
            return runtime_id
    for runtime_id, deferral in data["deferrals"].items():
        candidates = [runtime_id, deferral["display_name"], *deferral["aliases"]]
        if needle in {_normalized(candidate) for candidate in candidates}:
            return runtime_id
    raise KeyError(f"unknown runtime: {value}")


@dataclass
class UnsupportedAdapter:
    """Executable fail-closed adapter for profiles without a host binding."""

    reason: str

    def activation_check(self) -> dict[str, Any]:
        return {
            "status": "blocked",
            "reason_code": "runtime-policy-unavailable",
            "evidence": [self.reason],
        }

    def launch(self, task: Mapping[str, Any], prompt: str, generation: int, **_: Any) -> dict[str, Any]:
        return {
            "status": "blocked",
            "reason_code": "runtime-policy-unavailable",
            "evidence": [self.reason],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task.get('id', 'unknown')}:adapter",
            "generation": generation,
        }

    def resume(self, session_id: str, prompt: str, generation: int, task_id: str | None = None, **_: Any) -> dict[str, Any]:
        return {
            "status": "blocked",
            "reason_code": "runtime-policy-unavailable",
            "evidence": [self.reason, f"session={session_id}"],
            "action_scope": "repository-task",
            "checkpoint_identity": f"{task_id or 'unknown'}:adapter",
            "generation": generation,
        }

    def wait(self, session_id: str, generation: int = 0, task_id: str | None = None, **_: Any) -> dict[str, Any]:
        return self.resume(session_id, "", generation, task_id=task_id)


def load_approval_receipt(path: Path | str) -> dict[str, Any]:
    """Load and validate an auditable host approval-verification receipt.

    The receipt is the production source for the adapter's verified
    non-interactive approval state. It must name the runtime it verifies and
    record ``approval = "verified"``; anything else fails closed.
    """

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("runtime"), str)
        or not data["runtime"].strip()
        or data.get("approval") != "verified"
    ):
        raise ValueError(f"approval receipt is not a verified host approval policy: {path}")
    return data


def resolve_adapter(runtime_id: str, repo_root: Path | str, **kwargs: Any) -> Any:
    """Resolve every eligible registry profile to a real or fail-closed adapter."""

    inventory = load_inventory()
    canonical = canonicalize_runtime_id(runtime_id, inventory)
    profile = inventory["runtimes"].get(canonical)
    if profile is None:
        raise ValueError(f"runtime is not eligible: {canonical}")
    if profile["adapter_entrypoint"] == "runtime-adapter:codex":
        from execute_plan_runtime_codex import CodexAdapter

        return CodexAdapter(repo_root, **kwargs)
    return UnsupportedAdapter(
        f"no verified host adapter for runtime profile {canonical} ({profile['adapter_entrypoint']})"
    )


def _default_retry_policy(status: str, reason_code: str, retry_budget: int = 2) -> dict[str, Any]:
    if status == "contract-violation":
        return {"mode": "rewrite-and-retry", "max_attempts": 1, "attempts_remaining": 1}
    if status == "error" and reason_code not in {
        "malformed-result",
        "cleanup-unverified",
    }:
        return {"mode": "bounded", "max_attempts": retry_budget, "attempts_remaining": retry_budget}
    return {"mode": "none", "max_attempts": 0, "attempts_remaining": 0}


def normalize_result(raw: Mapping[str, Any], retry_budget: int = 2) -> dict[str, Any]:
    """Translate a worker or adapter result into the closed result schema."""

    if not isinstance(raw, Mapping):
        raise ValueError("result must be a mapping")
    raw_status = raw.get("status")
    status = "blocked" if raw_status == "approval-required" else raw_status
    if status not in NORMALIZED_STATUSES:
        raise ValueError(f"unknown result status: {raw_status}")
    reason_code = str(raw.get("reason_code") or "")
    if raw_status == "approval-required":
        reason_code = "approval-required"
    evidence = raw.get("evidence")
    if not isinstance(evidence, list) or not evidence or not all(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        raise ValueError("result evidence must be a non-empty list of strings")
    action_scope = raw.get("action_scope")
    if not isinstance(action_scope, str) or not action_scope.strip():
        raise ValueError("result action_scope must be non-empty")
    checkpoint_identity = raw.get("checkpoint_identity")
    if not isinstance(checkpoint_identity, str) or not checkpoint_identity.strip():
        raise ValueError("result checkpoint_identity must be non-empty")
    generation = raw.get("generation")
    if not isinstance(generation, int) or generation < 0:
        raise ValueError("result generation must be a non-negative integer")
    resume_allowed = raw.get("resume_allowed")
    if resume_allowed is not None and not isinstance(resume_allowed, bool):
        raise ValueError("resume_allowed must be boolean when present")
    if reason_code in {"permission-request", "conversational-hesitation"}:
        status = "contract-violation"
        reason_code = "worker-hesitation"
    if reason_code not in REASON_CODES:
        raise ValueError(f"unknown or missing reason code: {raw.get('reason_code')!r}")
    if reason_code in BLOCKING_REASON_CODES and status == "success":
        status = "blocked"
    if reason_code in {"approval-required", "cleanup-unverified"}:
        retry_policy = {"mode": "none", "max_attempts": 0, "attempts_remaining": 0}
    else:
        retry_policy = raw.get("retry_policy") or _default_retry_policy(status, reason_code, retry_budget)
    if not isinstance(retry_policy, Mapping):
        raise ValueError("retry_policy must be a mapping")
    retry_policy = dict(retry_policy)
    for key in ("max_attempts", "attempts_remaining"):
        if not isinstance(retry_policy.get(key), int) or retry_policy[key] < 0:
            raise ValueError(f"retry_policy.{key} must be a non-negative integer")
    if reason_code in {"approval-required", "malformed-result", "cleanup-unverified"}:
        retry_policy["mode"] = "none"
        retry_policy["max_attempts"] = 0
        retry_policy["attempts_remaining"] = 0
    else:
        # The profile owns the retry budget: clamp any worker- or
        # adapter-supplied policy to the profile cap so an untrusted envelope
        # cannot re-supply an unbounded budget (contract-violation is capped
        # at its single rewrite-and-retry).
        budget_cap = max(1, int(retry_budget))
        retry_cap = 1 if status == "contract-violation" else (budget_cap if status == "error" else 0)
        retry_policy["max_attempts"] = min(retry_policy["max_attempts"], retry_cap)
        retry_policy["attempts_remaining"] = min(retry_policy["attempts_remaining"], retry_cap)
    if status == "success":
        recovery_action = "continue-parent"
    elif reason_code == "approval-required":
        recovery_action = "preserve-and-await-approval"
    elif status == "contract-violation":
        recovery_action = "rewrite-and-retry"
    elif status == "aborted":
        recovery_action = "preserve-and-stop"
    else:
        recovery_action = str(raw.get("recovery_action") or "preserve-and-reconcile")
    return {
        "status": status,
        "reason_code": reason_code,
        "evidence": list(evidence),
        "action_scope": action_scope,
        "checkpoint_identity": checkpoint_identity,
        "generation": generation,
        "retry_policy": retry_policy,
        "recovery_action": recovery_action,
        "resume_allowed": bool(
            resume_allowed
            if resume_allowed is not None
            else status == "blocked"
            and reason_code in RESUMABLE_REASONS
        ),
    }


def _fixture_path(root: Path, relative: str) -> Path:
    """Resolve a fixture-owned relative path without allowing traversal."""

    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"activation fixture path escapes root: {relative}")
    return candidate


def verify_activation(fixture_root: Path | str) -> dict[str, Any]:
    """Verify a file-backed runtime package activation fixture.

    The fixture injects the loaded skill path and supplies local help probes.
    Package bytes are compared with the repository sources so a stale or
    partially installed runtime fails closed before it can be selected.
    """

    root = Path(fixture_root).resolve()
    manifest_path = _fixture_path(root, "activation.json")
    with manifest_path.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    roles = manifest.get("roles")
    if not isinstance(roles, Mapping) or set(roles) != {"skill", "driver", "registry", "adapter"}:
        raise ValueError("activation fixture must define skill, driver, registry, and adapter roles")

    loaded_skill_path = manifest.get("loaded_skill_path")
    if not isinstance(loaded_skill_path, str) or not loaded_skill_path:
        raise ValueError("activation fixture needs a loaded_skill_path")
    loaded_skill = _fixture_path(root, loaded_skill_path)
    if not loaded_skill.is_file():
        raise ValueError("injected loaded skill path is absent")

    checked_roles: list[str] = []
    for role in ("skill", "driver", "registry", "adapter"):
        entry = roles[role]
        if not isinstance(entry, Mapping):
            raise ValueError(f"activation role is malformed: {role}")
        source_relative = entry.get("source")
        loaded_relative = entry.get("loaded")
        if not isinstance(source_relative, str) or not isinstance(loaded_relative, str):
            raise ValueError(f"activation role paths are malformed: {role}")
        source = _fixture_path(ROOT, source_relative)
        loaded = _fixture_path(root, loaded_relative)
        if not source.is_file() or not loaded.is_file():
            raise ValueError(f"activation package file is absent: {role}")
        if source.read_bytes() != loaded.read_bytes():
            raise ValueError(f"activation package bytes differ: {role}")
        checked_roles.append(role)

    loaded_registry = tomllib.loads(
        _fixture_path(root, roles["registry"]["loaded"]).read_text(encoding="utf-8")
    )
    expected_ids_path = manifest.get("expected_runtime_ids")
    if not isinstance(expected_ids_path, str) or not expected_ids_path:
        raise ValueError("activation fixture needs an independent runtime expectation")
    expected_ids = json.loads(_fixture_path(ROOT, expected_ids_path).read_text(encoding="utf-8"))
    loaded_inventory = loaded_registry.get("inventory", {})
    if loaded_inventory.get("canonical_ids") != expected_ids.get("canonical_ids"):
        raise ValueError("activation registry canonical IDs do not match expectation")
    if loaded_inventory.get("deferred_ids") != expected_ids.get("deferred_ids"):
        raise ValueError("activation registry deferred IDs do not match expectation")
    profiles = loaded_registry.get("runtimes", {})
    expected_profiles = expected_ids.get("profiles", {})
    if set(profiles) != set(expected_ids.get("canonical_ids", ())):
        raise ValueError("activation registry profile set does not match expectation")
    for runtime_id, expected in expected_profiles.items():
        profile = profiles.get(runtime_id)
        if not isinstance(profile, Mapping):
            raise ValueError(f"activation profile is absent: {runtime_id}")
        for field in ("adapter_entrypoint", "capabilities", "retry_budget"):
            if profile.get(field) != expected.get(field):
                raise ValueError(f"activation profile differs from expectation: {runtime_id}.{field}")

    probes = manifest.get("help_probes")
    if not isinstance(probes, list) or not probes:
        raise ValueError("activation fixture needs help probes")
    probe_environment = {
        "HOME": str(root / "home"),
        "PATH": "",
        "PYTHONPATH": str(root / "loaded/execute-plan/runtime"),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "EXECUTE_PLAN_LOADED_SKILL": str(loaded_skill),
        "EXECUTE_PLAN_RUNTIME_INVENTORY": str(_fixture_path(root, roles["registry"]["loaded"])),
    }
    loaded_driver = _fixture_path(root, "loaded/execute-plan/runtime/execute_plan_runtime.py")
    for probe in probes:
        if not isinstance(probe, Mapping) or not isinstance(probe.get("argv"), list):
            raise ValueError("activation help probe is malformed")
        argv = [
            str(item)
            .replace("${FIXTURE_ROOT}", str(root))
            .replace("${LOADED_SKILL_PATH}", str(loaded_skill))
            .replace("${LOADED_DRIVER_PATH}", str(loaded_driver))
            .replace("__PYTHON__", sys.executable)
            for item in probe["argv"]
        ]
        if not argv or any("\x00" in item for item in argv):
            raise ValueError("activation help probe contains an invalid argument")
        try:
            completed = subprocess.run(
                argv,
                cwd=root,
                env=probe_environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError(f"activation help probe failed to run: {exc}") from exc
        expected = str(probe.get("expected", ""))
        if completed.returncode != 0 or expected not in completed.stdout:
            raise ValueError(f"activation help probe failed: {probe.get('name', 'unnamed')}")

    return {
        "status": "success",
        "checked_roles": checked_roles,
        "help_probes": len(probes),
        "loaded_skill_path": str(loaded_skill),
    }


def _probe_loaded_package(destination: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import runtime_capabilities as c; "
                "i=c.load_inventory(); "
                "assert 'codex' in i['runtimes']; "
                "a=c.resolve_adapter('codex', '.'); "
                "assert callable(a.launch) and callable(a.resume); "
                "print('loaded runtime registry and adapter probe: ok')"
            ),
        ],
        cwd=destination,
        env={
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(destination),
            "PYTHONPATH": str(destination / "runtime"),
            "EXECUTE_PLAN_RUNTIME_INVENTORY": str(destination / "registry.toml"),
            "EXECUTE_PLAN_PACKAGE_MANIFEST": str(destination / "package-manifest.toml"),
            "LANG": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def activate(runtime_id: str, source: Path | str, loaded_root: Path | str | None = None) -> dict[str, Any]:
    """Atomically stage an execute-plan package and verify its loaded driver."""

    inventory = load_inventory()
    canonical = canonicalize_runtime_id(runtime_id, inventory)
    if canonical not in inventory["runtimes"]:
        raise ValueError(f"runtime is deferred: {canonical}")
    source_path = Path(source).resolve()
    if not source_path.is_dir():
        raise ValueError("activation source must be a directory")
    package_manifest_path = source_path / "package-manifest.toml"
    if not package_manifest_path.is_file():
        raise ValueError("activation package manifest is absent")
    with package_manifest_path.open("rb") as stream:
        package_manifest = tomllib.load(stream)
    package = package_manifest.get("package", {})
    if package.get("name") != "execute-plan-runtime":
        raise ValueError("activation package name is invalid")
    driver_entrypoint = package_manifest.get("driver", {}).get("entrypoint")
    adapter_entrypoint = package_manifest.get("adapters", {}).get("codex", {}).get("entrypoint")
    if driver_entrypoint != "scripts/execute_plan_runtime.py:RuntimeDriver" or adapter_entrypoint != "scripts/execute_plan_runtime_codex.py:CodexAdapter":
        raise ValueError("activation package entrypoints are invalid")
    destination = Path(loaded_root or (source_path.parent / ".execute-plan-activated" / canonical)).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{canonical}-", dir=destination.parent))
    package = staging / "execute-plan"
    shutil.copytree(source_path, package)
    runtime_dir = package / "runtime"
    runtime_dir.mkdir()
    for relative in ("execute_plan_runtime.py", "execute_plan_runtime_codex.py", "runtime_capabilities.py"):
        shutil.copy2(ROOT / "scripts" / relative, runtime_dir / relative)
    shutil.copy2(DEFAULT_INVENTORY_PATH, package / "registry.toml")
    for path in package.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o600)
    rollback = destination.with_name(destination.name + ".rollback")
    if not destination.exists() and rollback.exists():
        os.replace(rollback, destination)
    probe = _probe_loaded_package(package)
    if probe.returncode != 0:
        shutil.rmtree(staging, ignore_errors=True)
        raise ValueError(f"loaded runtime probe failed before swap: {probe.stderr.strip()}")
    pointer = destination.parent / f".{destination.name}.active-{uuid.uuid4().hex}"
    versioned = destination.parent / f".{destination.name}-{uuid.uuid4().hex}"
    try:
        os.replace(package, versioned)
        os.symlink(versioned, pointer)
        if destination.is_symlink():
            if rollback.exists() or rollback.is_symlink():
                if rollback.is_dir() and not rollback.is_symlink():
                    shutil.rmtree(rollback)
                else:
                    rollback.unlink()
            # Keep the current pointer in place until the new pointer is
            # ready; os.replace then makes the activation switch atomic.
            os.symlink(os.readlink(destination), rollback)
        elif destination.exists():
            if rollback.exists() or rollback.is_symlink():
                if rollback.is_dir() and not rollback.is_symlink():
                    shutil.rmtree(rollback)
                else:
                    rollback.unlink()
            os.replace(destination, rollback)
        os.replace(pointer, destination)
        receipt = destination / "activation-receipt.json"
        receipt.write_text(
            json.dumps(
                {
                    "runtime": canonical,
                    "loaded_root": str(destination),
                    "rollback": str(rollback) if rollback.exists() else "",
                    "status": "success",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(receipt, 0o600)
    except Exception:
        pointer.unlink(missing_ok=True)
        if versioned.exists() or versioned.is_symlink():
            if versioned.is_dir() and not versioned.is_symlink():
                shutil.rmtree(versioned)
            else:
                versioned.unlink()
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink():
                destination.unlink()
            elif destination.is_dir():
                shutil.rmtree(destination)
        if rollback.exists() or rollback.is_symlink():
            os.replace(rollback, destination)
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "status": "success",
        "runtime": canonical,
        "loaded_root": str(destination),
        "rollback": str(rollback) if rollback.exists() else "",
        "probe": probe.stdout.strip(),
    }


def selftest() -> None:
    inventory = load_inventory()
    profiles = load_profiles()
    if set(profiles) != set(inventory["inventory"]["canonical_ids"]):
        raise AssertionError("registry profile IDs are not internally consistent")
    if canonicalize_runtime_id("agy", inventory) != "antigravity":
        raise AssertionError("Antigravity alias did not normalize")
    success = normalize_result(
        {
            "status": "success",
            "reason_code": "completed",
            "evidence": ["checkpoint"],
            "action_scope": "repository-task",
            "checkpoint_identity": "task-1",
            "generation": 1,
        }
    )
    approval = normalize_result(
        {
            "status": "approval-required",
            "reason_code": "approval-required",
            "evidence": ["approval request"],
            "action_scope": "external-write",
            "checkpoint_identity": "task-1",
            "generation": 1,
        }
    )
    if success["status"] != "success" or approval["status"] != "blocked":
        raise AssertionError("result normalization did not preserve approval boundary")
    if approval["retry_policy"]["mode"] != "none":
        raise AssertionError("approval-required results must not be retried")
    print(
        f"runtime capability selftest: {len(profiles)} profiles, "
        f"{len(inventory['inventory']['deferred_ids'])} deferred runtime"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--verify-activation", action="store_true")
    parser.add_argument("--activate")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--loaded-root", type=Path)
    parser.add_argument("--fixture-root", type=Path)
    args = parser.parse_args(argv)
    if not args.selftest and not args.verify_activation and not args.activate:
        parser.error("--selftest, --verify-activation, or --activate is required")
    try:
        if args.selftest:
            selftest()
        if args.verify_activation:
            if args.fixture_root is None:
                parser.error("--fixture-root is required with --verify-activation")
            result = verify_activation(args.fixture_root)
            print(f"runtime activation verification: {result['status']} ({result['help_probes']} help probes)")
        if args.activate:
            if args.source is None:
                parser.error("--source is required with --activate")
            result = activate(args.activate, args.source, args.loaded_root)
            print(json.dumps(result, sort_keys=True))
    except (AssertionError, OSError, ValueError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"runtime capability selftest failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
