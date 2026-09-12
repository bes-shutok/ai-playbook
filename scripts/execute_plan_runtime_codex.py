#!/usr/bin/env python3
"""Thin Codex host adapter for the provider-neutral runtime driver."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Any, Mapping

import runtime_capabilities as capabilities
from runtime_capabilities import bounded_evidence


DEFAULT_LAUNCH_DEADLINE = 30.0
DEFAULT_WAIT_DEADLINE = 300.0
DANGEROUS_FLAGS = {"--approve-for-me", "--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust"}
SAFE_ENV_KEYS = {"PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR"}


def _subprocess_runner(argv: list[str], timeout_seconds: float, operation: str, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if operation in {"launch", "wait", "resume"} and not capabilities.validate_policy_token(policy_token, operation=operation):
        return {"returncode": 2, "stderr": "policy token required at process boundary"}
    environment = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
    if policy_token is not None:
        environment["EXECUTE_PLAN_POLICY_TOKEN"] = json.dumps(dict(policy_token), sort_keys=True)
        environment["EXECUTE_PLAN_ALLOWED_PATHS"] = json.dumps(policy_token["allowed_paths"])
    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(policy_token["repo_root"]) if isinstance(policy_token, Mapping) else None,
        env=environment,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return {"timed_out": True, "handle": process, "owned_pids": _process_tree_pids(process.pid), "stderr": "deadline exceeded"}
    return {"returncode": process.returncode, "stdout": stdout, "stderr": stderr}


def _process_tree_pids(root_pid: int) -> dict[int, str]:
    """Capture descendants and their start-time identity before cancellation.

    The identity map lets the timeout cleanup loop distinguish an owned
    descendant from an unrelated process that recycled its PID.
    """

    try:
        listing = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,lstart="],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.splitlines()
    except OSError:
        return {}
    children: dict[int, list[int]] = {}
    identities: dict[int, str] = {}
    for line in listing:
        fields = line.split(None, 2)
        if len(fields) != 3:
            continue
        try:
            pid, parent = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        children.setdefault(parent, []).append(pid)
        identities[pid] = fields[2].strip()
    result: dict[int, str] = {}
    pending = list(children.get(root_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in result:
            continue
        result[pid] = identities.get(pid, "")
        pending.extend(children.get(pid, ()))
    return result


def _pid_identity_matches(pid: int, identity: str) -> bool:
    """True when ``pid`` still holds the captured start-time identity.

    An empty captured identity or a lookup failure is ambiguous and keeps the
    conservative polling path; a mismatching identity means the PID was
    recycled and must be treated as exited rather than signalled.
    """

    if not identity:
        return True
    try:
        listing = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return True
    return listing == identity


def _cancel_process_tree(process: Any) -> None:
    if isinstance(process, subprocess.Popen):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass


def _verify_process_terminated(process: Any) -> bool:
    if not isinstance(process, subprocess.Popen):
        return True
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
        try:
            process.kill()
            process.wait(timeout=1)
        except (OSError, ProcessLookupError, subprocess.TimeoutExpired):
            return False
    # No post-reap process-group escalation: after the leader is reaped its
    # pgid can be recycled by an unrelated process, and an un-narrowed killpg
    # would signal it. Surviving descendants are covered by the
    # identity-narrowed owned-pids loop in _timeout_result.
    return process.poll() is not None


class CodexAdapter:
    """Translate the installed ``codex exec`` JSONL boundary.

    The adapter never adds approval automation or dangerous bypass flags. A
    caller must provide a separately verified non-interactive approval policy.
    """

    adapter_version = "1.0"

    def __init__(
        self,
        repo_root: Path | str,
        runner: Any = _subprocess_runner,
        approval_verified: bool = False,
        executable: str = "codex",
        launch_deadline: float | None = None,
        wait_deadline: float | None = None,
        approval_receipt: Path | str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.runner = runner
        self.approval_receipt_path: str | None = None
        if approval_receipt is not None:
            # Production source for the verified approval state: an auditable
            # receipt file validated here, never an ambient flag or env trust.
            receipt = capabilities.load_approval_receipt(approval_receipt)
            if receipt["runtime"] != "codex":
                raise ValueError("approval receipt does not verify the codex runtime")
            self.approval_verified = True
            self.approval_receipt_path = str(approval_receipt)
        else:
            self.approval_verified = approval_verified
        self.activation_receipt: dict[str, Any] | None = None
        self.executable = executable
        manifest_values: dict[str, Any] = {}
        manifest_path = os.environ.get("EXECUTE_PLAN_PACKAGE_MANIFEST")
        if manifest_path:
            try:
                with Path(manifest_path).open("rb") as stream:
                    manifest_values = tomllib.load(stream).get("adapters", {}).get("codex", {})
            except (OSError, tomllib.TOMLDecodeError):
                manifest_values = {}
        self.launch_deadline = self._finite(
            launch_deadline if launch_deadline is not None else manifest_values.get("launch_deadline_seconds"),
            DEFAULT_LAUNCH_DEADLINE,
        )
        self.wait_deadline = self._finite(
            wait_deadline if wait_deadline is not None else manifest_values.get("wait_deadline_seconds"),
            DEFAULT_WAIT_DEADLINE,
        )

    @staticmethod
    def _finite(value: float | None, default: float) -> float:
        try:
            number = float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
        return number if number > 0 and number != float("inf") else default

    def _run(self, argv: list[str], deadline: float, operation: str, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if any(flag in argv for flag in DANGEROUS_FLAGS):
            return {"returncode": 2, "stderr": "dangerous approval flag rejected"}
        try:
            if policy_token is None:
                result = self.runner(argv, deadline, operation)
            else:
                result = self.runner(argv, deadline, operation, policy_token=policy_token)
        except TypeError:
            if policy_token is not None:
                return {"returncode": 2, "stderr": "policy-aware process runner is required"}
            result = self.runner(argv, timeout_seconds=deadline, operation=operation)
        if not isinstance(result, Mapping):
            return {"returncode": 2, "stderr": "malformed process runner result"}
        return dict(result)

    @staticmethod
    def _jsonl(stdout: str) -> tuple[list[dict[str, Any]], bool]:
        envelopes: list[dict[str, Any]] = []
        malformed = False
        for line in stdout.splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                malformed = True
                continue
            if isinstance(value, dict):
                envelopes.append(value)
            else:
                malformed = True
        return envelopes, malformed

    def activation_check(self) -> dict[str, Any]:
        checks = (
            ([self.executable, "--version"], "version"),
            ([self.executable, "exec", "--help"], "launch"),
            ([self.executable, "exec", "resume", "--help"], "resume"),
        )
        evidence: list[str] = []
        for argv, operation in checks:
            result = self._run(argv, self.launch_deadline, f"activation-{operation}")
            if result.get("returncode") != 0:
                return self._blocked("runtime-policy-unavailable", [f"activation failed: {operation}"])
            stdout = str(result.get("stdout", ""))
            if operation == "launch" and "--json" not in stdout:
                return self._blocked("runtime-policy-unavailable", ["launch JSONL interface not verified"])
            if operation == "resume" and "--json" not in stdout:
                return self._blocked("runtime-policy-unavailable", ["resume JSONL interface not verified"])
            evidence.append(f"verified {operation} command shape")
        if not self.approval_verified:
            return self._blocked("runtime-policy-unavailable", evidence + ["no verified non-interactive approval configuration"])
        if self.approval_receipt_path:
            evidence.append(f"approval-receipt={self.approval_receipt_path}")
        result = self._success("activation-verified", evidence, "activation-check", "activation", 0)
        self.activation_receipt = {
            "executable": self.executable,
            "repo_root": str(self.repo_root),
            "evidence": list(result["evidence"]),
            "configuration": "non-interactive-default-deny",
            "approval_receipt": self.approval_receipt_path or "test-injected",
        }
        return result

    def _blocked(self, reason: str, evidence: list[str], scope: str = "repository-task", checkpoint: str = "codex:adapter", generation: int = 0) -> dict[str, Any]:
        return {
            "status": "blocked",
            "reason_code": reason,
            "evidence": bounded_evidence(evidence),
            "action_scope": scope,
            "checkpoint_identity": checkpoint,
            "generation": generation,
            "retry_policy": {"mode": "none", "max_attempts": 0, "attempts_remaining": 0},
            "recovery_action": "preserve-and-await-approval" if reason == "approval-required" else "preserve-and-reconcile",
        }

    @staticmethod
    def _success(reason: str, evidence: list[str], scope: str, checkpoint: str, generation: int) -> dict[str, Any]:
        return {
            "status": "success",
            "reason_code": reason,
            "evidence": bounded_evidence(evidence),
            "action_scope": scope,
            "checkpoint_identity": checkpoint,
            "generation": generation,
            "retry_policy": {"mode": "none", "max_attempts": 0, "attempts_remaining": 0},
            "recovery_action": "continue-parent",
        }

    def _timeout_result(self, process_result: Mapping[str, Any], operation: str, generation: int, checkpoint: str) -> dict[str, Any]:
        handle = process_result.get("handle")
        cancel = getattr(self.runner, "cancel", None)
        if callable(cancel):
            cancel(handle)
        else:
            _cancel_process_tree(handle)
        verify = getattr(self.runner, "verify_terminated", None)
        verified = bool(verify(handle)) if callable(verify) else _verify_process_terminated(handle)
        owned_pids = process_result.get("owned_pids", ())
        if isinstance(owned_pids, Mapping):
            owned_items = list(owned_pids.items())
        elif isinstance(owned_pids, (list, tuple)):
            owned_items = [(pid, "") for pid in owned_pids]
        else:
            owned_items = []
        if verified and owned_items:
            for pid, identity in owned_items:
                try:
                    numeric_pid = int(pid)
                except (ValueError, TypeError):
                    verified = False
                    break
                if not _pid_identity_matches(numeric_pid, str(identity)):
                    # PID was recycled by an unrelated process; treat as exited.
                    continue
                for _ in range(100):
                    try:
                        os.kill(numeric_pid, 0)
                    except OSError:
                        break
                    time.sleep(0.01)
                else:
                    # Consult the identity immediately before the kill: a PID
                    # whose captured identity flipped since the poll loop was
                    # recycled by a foreign process and must never be signalled.
                    # The check is a best-effort narrowing; the kernel-level
                    # recycle race is closed only by a pidfd-based signal where
                    # the platform provides one.
                    if not _pid_identity_matches(numeric_pid, str(identity)):
                        continue
                    try:
                        os.kill(numeric_pid, signal.SIGKILL)
                    except OSError:
                        pass
                    if not _pid_identity_matches(numeric_pid, str(identity)):
                        continue
                    try:
                        os.kill(numeric_pid, 0)
                    except OSError:
                        continue
                    verified = False
                    break
        return self._blocked("timeout" if verified else "cleanup-unverified", [f"{operation} deadline exceeded", f"owned_process={handle!r}"], generation=generation, checkpoint=checkpoint)

    def translate_host_result(self, host_result: Mapping[str, Any], generation: int, task_id: str) -> dict[str, Any]:
        """Translate one final host envelope into the normalized contract."""

        raw = dict(host_result)
        if "evidence" not in raw:
            raw["evidence"] = ["codex host envelope"]
        elif not isinstance(raw["evidence"], list):
            return self._blocked("malformed-result", ["host evidence must be a list of strings"], generation=generation, checkpoint=f"{task_id}:malformed")
        raw.setdefault("action_scope", "repository-task")
        raw.setdefault("checkpoint_identity", f"{task_id}:worker")
        raw.setdefault("generation", generation)
        if raw.get("status") == "approval-required" or raw.get("reason_code") == "approval-required":
            raw["status"] = "approval-required"
            raw["action_scope"] = str(raw.get("action_scope") or "approval-required")
            raw["evidence"] = list(raw.get("evidence", [])) + [f"action_scope={raw['action_scope']}"]
        try:
            result = capabilities.normalize_result(raw)
        except (TypeError, ValueError) as exc:
            return self._blocked("malformed-result", [str(exc)], generation=generation, checkpoint=f"{task_id}:malformed")
        if raw.get("status") == "approval-required":
            result["retry_policy"] = {"mode": "none", "max_attempts": 0, "attempts_remaining": 0}
            result["recovery_action"] = "preserve-and-await-approval"
        return result

    def _invoke_and_translate(self, argv: list[str], deadline: float, operation: str, generation: int, task_id: str, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        result = self._run(argv, deadline, operation, policy_token=policy_token)
        if result.get("timed_out"):
            return self._timeout_result(result, operation, generation, f"{task_id}:worker")
        if result.get("returncode") not in (0, None):
            return self._blocked("runtime-error", [f"{operation} exit={result.get('returncode')}", "nonzero host exit"], generation=generation, checkpoint=f"{task_id}:runtime")
        envelopes, malformed = self._jsonl(str(result.get("stdout", "")))
        if not envelopes:
            return self._blocked("malformed-result", ["Codex returned no JSONL envelope"], generation=generation, checkpoint=f"{task_id}:malformed")
        if malformed:
            return self._blocked("malformed-result", ["Codex returned malformed JSONL output"], generation=generation, checkpoint=f"{task_id}:malformed")
        thread_id = next((item.get("thread_id") or item.get("session_id") or item.get("id") for item in envelopes if item.get("thread_id") or item.get("session_id") or item.get("id")), None)
        final = next((item for item in reversed(envelopes) if "status" in item or item.get("type") in {"turn.completed", "result"}), envelopes[-1])
        translated = self.translate_host_result(final, generation, task_id)
        if thread_id:
            translated["session_id"] = str(thread_id)
        return translated

    @staticmethod
    def _option_like(value: Any) -> bool:
        return not isinstance(value, str) or not value or value.startswith("-")

    def launch(self, task: Mapping[str, Any], prompt: str, generation: int, deadline_seconds: float | None = None, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        task_id = str(task["id"])
        if self._option_like(prompt):
            return self._blocked("contract-violation", ["option-like or empty prompt rejected"], generation=generation, checkpoint=f"{task_id}:policy")
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        argv = [self.executable, "exec", "--json", "-C", str(self.repo_root), prompt]
        if self.activation_receipt is None:
            return self._blocked("runtime-policy-unavailable", ["adapter activation receipt is missing"], generation=generation, checkpoint=f"{task_id}:policy")
        result = self._invoke_and_translate(argv, self._finite(deadline_seconds, self.launch_deadline), "launch", generation, task_id, policy_token=policy_token)
        return result

    def wait(self, session_id: str, generation: int = 1, task_id: str | None = None, deadline_seconds: float | None = None, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        task_id = task_id or self._task_from_session(session_id)
        if self._option_like(session_id):
            return self._blocked("contract-violation", ["option-like or empty session id rejected"], generation=generation, checkpoint=f"{task_id}:policy")
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        argv = [self.executable, "exec", "resume", session_id, "--json"]
        return self._invoke_and_translate(argv, self._finite(deadline_seconds, self.wait_deadline), "wait", generation, task_id, policy_token=policy_token)

    def resume(self, session_id: str, prompt: str, generation: int, task_id: str | None = None, deadline_seconds: float | None = None, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        task_id = task_id or self._task_from_session(session_id)
        if self._option_like(session_id) or self._option_like(prompt):
            return self._blocked("contract-violation", ["option-like or empty session id or prompt rejected"], generation=generation, checkpoint=f"{task_id}:policy")
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        argv = [self.executable, "exec", "resume", session_id, "--json", prompt]
        return self._invoke_and_translate(argv, self._finite(deadline_seconds, self.wait_deadline), "resume", generation, task_id, policy_token=policy_token)

    @staticmethod
    def _task_from_session(session_id: str) -> str:
        match = session_id.rsplit("-", 1)
        return f"task-{match[-1]}" if match[-1].isdigit() else "task-unknown"


if __name__ == "__main__":
    raise SystemExit("Codex adapter is imported by the execute-plan driver")
