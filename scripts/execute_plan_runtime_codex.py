#!/usr/bin/env python3
"""Thin Codex host adapter for the provider-neutral runtime driver."""

from __future__ import annotations

import json
import hashlib
import fcntl
import os
import signal
import shlex
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any, Mapping

import runtime_capabilities as capabilities
from runtime_capabilities import bounded_evidence


# In-code default deadlines: they equal the contract baseline pinned in
# agents/skills/execute-plan/package-manifest.toml and apply only when a
# manifest omits the deadline keys. The wait default covers a legitimate
# 20-minute worker body of work (the same budget the driver's claim-lease
# comment sizes against) while staying finite and bounded. No environment
# variable or CLI flag overrides these: the package manifest is the only
# configuration surface.
DEFAULT_LAUNCH_DEADLINE = 900.0
DEFAULT_WAIT_DEADLINE = 1500.0
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
        process_snapshot: Any | None = None,
        capacity_lock_path: Path | str | None = None,
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
        if process_snapshot is not None:
            self.process_snapshot = process_snapshot
        elif runner is _subprocess_runner:
            self.process_snapshot = self._system_process_snapshot
        else:
            # An injected runner is a hermetic test boundary. Its empty
            # inventory is explicit; tests for unavailable or occupied
            # capacity inject a process_snapshot witness.
            self.process_snapshot = lambda: subprocess.CompletedProcess([], 0, "1 Mon Jan 01 00:00:00 2024 test-runner\\n", "")
        self._test_capacity_lock_dir = None
        if capacity_lock_path is not None:
            self.capacity_lock_path = Path(capacity_lock_path)
        elif runner is _subprocess_runner:
            self.capacity_lock_path = Path.home() / ".codex" / "execute-plan" / "codex-capacity.lock"
        else:
            self._test_capacity_lock_dir = tempfile.TemporaryDirectory(prefix="execute-plan-codex-capacity-")
            self.capacity_lock_path = Path(self._test_capacity_lock_dir.name) / "capacity.lock"
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

    def __del__(self) -> None:
        test_lock_dir = getattr(self, "_test_capacity_lock_dir", None)
        if test_lock_dir is not None:
            test_lock_dir.cleanup()

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

    @staticmethod
    def normalize_observation(kind: str, state: str, *, provider_session_id: str | None = None, process_identity: Mapping[str, Any] | None = None, observed_at: float | None = None, freshness_window: float = 30.0) -> dict[str, Any]:
        """Translate Codex host facts into the neutral observation port."""
        if state not in {"available", "terminal", "stale", "unavailable", "malformed", "timed-out", "unsupported"}:
            state = "malformed"
        effect = "release" if state == "terminal" else "retain" if state == "available" else "quarantine"
        return {"version": 1, "observation_kind": str(kind), "state": state, "observed_at": float(observed_at if observed_at is not None else time.monotonic()), "freshness_window": float(freshness_window), "provider_identity": {"session_id": provider_session_id} if provider_session_id else {}, "process_identity": dict(process_identity or {}), "capacity_slot_effect": effect}

    def observe_inventory(self) -> dict[str, Any]:
        """Return a fresh inventory of active Codex CLI execution processes.

        ``ps`` is the host process table, not a session-history database. A
        successful, completely parsed snapshot can prove that no adapter-owned
        ``codex exec`` process is active; command failure or malformed output
        remains unavailable. The process start time fences PID reuse.
        """
        try:
            snapshot = self.process_snapshot()
            if not isinstance(snapshot, subprocess.CompletedProcess) or snapshot.returncode != 0:
                raise ValueError("process snapshot command failed")
            inventory = self._parse_process_snapshot(str(snapshot.stdout))
        except (OSError, TypeError, ValueError, subprocess.SubprocessError):
            return self.normalize_observation("inventory", "unavailable") | {"inventory": None}
        return self.normalize_observation("inventory", "available") | {"inventory": inventory}

    @staticmethod
    def _system_process_snapshot() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/ps", "-ww", "-axo", "pid=,lstart=,command="],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )

    @staticmethod
    def _parse_process_snapshot(output: str) -> list[dict[str, Any]]:
        if not output.strip():
            raise ValueError("empty process snapshot")
        inventory: list[dict[str, Any]] = []
        for line in output.splitlines():
            fields = line.split(None, 6)
            if len(fields) != 7:
                raise ValueError("malformed process row")
            command = fields[6]
            if "codex" not in command.lower():
                continue
            try:
                pid = int(fields[0])
                argv = shlex.split(command)
            except (ValueError, TypeError) as exc:
                raise ValueError("malformed process row") from exc
            if pid <= 0 or not argv:
                raise ValueError("malformed process identity")
            start_time = " ".join(fields[1:6])
            codex_index = next(
                (index for index, value in enumerate(argv[:-1]) if Path(value).name in {"codex", "codex.exe"}),
                None,
            )
            if codex_index is None or argv[codex_index + 1] != "exec":
                continue
            invocation = argv[codex_index + 2:]
            if not invocation or not (invocation[0] == "--json" or (invocation[0] == "resume" and "--json" in invocation[1:])):
                continue
            identity = {"pid": pid, "start_time": start_time}
            session_suffix = hashlib.sha256(start_time.encode("utf-8")).hexdigest()[:12]
            inventory.append({
                "provider_session_id": f"codex-process-{pid}-{session_suffix}",
                "process_identity": identity,
            })
        return inventory

    def _with_capacity_fence(self, operation: str, generation: int, task_id: str, invoke: Any, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Serialize process discovery and launch/resume across local runs."""
        try:
            self.capacity_lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            descriptor = os.open(self.capacity_lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        except OSError:
            return self._blocked("capacity-unavailable", ["Codex capacity lock is unavailable"], generation=generation, checkpoint=f"{task_id}:{operation}")
        try:
            try:
                os.fchmod(descriptor, 0o600)
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return self._blocked("capacity-unavailable", ["another Codex worker holds the host capacity reservation"], generation=generation, checkpoint=f"{task_id}:{operation}")
            except OSError:
                return self._blocked("capacity-unavailable", ["Codex capacity lock is unavailable"], generation=generation, checkpoint=f"{task_id}:{operation}")
            observation = self.observe_inventory()
            if observation.get("state") != "available":
                return self._blocked("capacity-unavailable", ["Codex process inventory is unavailable"], generation=generation, checkpoint=f"{task_id}:{operation}")
            inventory = observation.get("inventory") or []
            allowed = policy_token.get("parallel_member_processes", []) if isinstance(policy_token, Mapping) else []
            allowed_keys = {json.dumps(item, sort_keys=True) for item in allowed if isinstance(item, Mapping)}
            unrelated = [item for item in inventory if json.dumps(item.get("process_identity", {}), sort_keys=True) not in allowed_keys]
            if unrelated:
                return self._blocked("capacity-unavailable", [f"Codex process inventory reports {len(unrelated)} unrelated execution process(es)"], generation=generation, checkpoint=f"{task_id}:{operation}")
            result = invoke()
            if isinstance(result, dict) and result.get("status") == "success" and operation == "launch":
                after = self.observe_inventory()
                if after.get("state") == "available":
                    prior_keys = {json.dumps(item.get("process_identity", {}), sort_keys=True) for item in inventory}
                    started = [item for item in after.get("inventory", []) if json.dumps(item.get("process_identity", {}), sort_keys=True) not in prior_keys]
                    if len(started) == 1:
                        result["process_identity"] = {"provider": "codex", **dict(started[0].get("process_identity", {}))}
            return result
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

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
        """Translate one final host envelope into the normalized contract.

        An optional batch member-progress envelope (batch id, member id and
        ordinal, attempt, anchor session id) is validated and preserved on
        the normalized result; a partial or mistyped envelope fails closed
        as a malformed result.
        """

        raw = dict(host_result)
        event_type = raw.get("type")
        if event_type == "turn.completed":
            raw.update({"status": "success", "reason_code": "completed"})
            raw.setdefault("evidence", ["Codex emitted turn.completed"])
        elif event_type in {"turn.failed", "error"}:
            failure = raw.get("error")
            message = failure.get("message") if isinstance(failure, Mapping) else None
            raw.update({"status": "blocked", "reason_code": "runtime-error"})
            raw.setdefault("evidence", [f"Codex emitted {event_type}", str(message or "Codex turn failed")])
        batch_progress = raw.get("batch_progress")
        normalized_progress: dict[str, Any] | None = None
        if batch_progress is not None:
            try:
                normalized_progress = capabilities.normalize_batch_progress(batch_progress)
            except (TypeError, ValueError) as exc:
                return self._blocked("malformed-result", [f"batch progress envelope rejected: {exc}"], generation=generation, checkpoint=f"{task_id}:malformed")
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
        if normalized_progress is not None:
            result["batch_progress"] = normalized_progress
            # The envelope's anchor session id is preserved on the result so
            # every later member resume reuses that one session.
            result.setdefault("session_id", normalized_progress["session_id"])
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
            translated["provider_session_id"] = str(thread_id)
            translated["worker_id"] = f"worker-{task_id}-{thread_id}"
            translated["launch_id"] = hashlib.sha256(f"{task_id}:{thread_id}:{generation}".encode()).hexdigest()[:24]
            translated["capacity_entry_id"] = f"capacity-{task_id}-{thread_id}"
            translated["command_identity"] = hashlib.sha256(" ".join(argv).encode()).hexdigest()[:24]
            translated["process_identity"] = {"provider": "codex", "session_id": str(thread_id)}
            translated["observed_at"] = time.monotonic()
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
        return self._with_capacity_fence(
            "launch",
            generation,
            task_id,
            lambda: self._invoke_and_translate(argv, self._finite(deadline_seconds, self.launch_deadline), "launch", generation, task_id, policy_token=policy_token),
            policy_token,
        )

    def wait(self, session_id: str, generation: int = 1, task_id: str | None = None, deadline_seconds: float | None = None, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        task_id = task_id or self._task_from_session(session_id)
        if self._option_like(session_id):
            return self._blocked("contract-violation", ["option-like or empty session id rejected"], generation=generation, checkpoint=f"{task_id}:policy")
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        argv = [self.executable, "exec", "resume", session_id, "--json"]
        return self._with_capacity_fence(
            "wait",
            generation,
            task_id,
            lambda: self._invoke_and_translate(argv, self._finite(deadline_seconds, self.wait_deadline), "wait", generation, task_id, policy_token=policy_token),
        )

    def resume(self, session_id: str, prompt: str, generation: int, task_id: str | None = None, deadline_seconds: float | None = None, policy_token: Mapping[str, Any] | None = None) -> dict[str, Any]:
        task_id = task_id or self._task_from_session(session_id)
        if self._option_like(session_id) or self._option_like(prompt):
            return self._blocked("contract-violation", ["option-like or empty session id or prompt rejected"], generation=generation, checkpoint=f"{task_id}:policy")
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        argv = [self.executable, "exec", "resume", session_id, "--json", prompt]
        return self._with_capacity_fence(
            "resume",
            generation,
            task_id,
            lambda: self._invoke_and_translate(argv, self._finite(deadline_seconds, self.wait_deadline), "resume", generation, task_id, policy_token=policy_token),
        )

    @staticmethod
    def _task_from_session(session_id: str) -> str:
        match = session_id.rsplit("-", 1)
        return f"task-{match[-1]}" if match[-1].isdigit() else "task-unknown"


if __name__ == "__main__":
    raise SystemExit("Codex adapter is imported by the execute-plan driver")
