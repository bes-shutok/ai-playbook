#!/usr/bin/env python3
"""Thin Codex host adapter for the provider-neutral runtime driver."""

from __future__ import annotations

import json
import hashlib
import fcntl
import os
import re
import signal
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
# Per-consult bound for the terminal-evidence port. The ps snapshot
# precedent (2.0 seconds) sizes it. In-process record retrieval honors it
# cooperatively (deadline checks per scan candidate); a local file read
# cannot be preempted, which is the recorded in-process residual.
TERMINAL_EVIDENCE_TIMEOUT_SECONDS = 2.0
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

    # Flags that consume a separate value token in `codex exec` argvs. When
    # one appears before the first positional token after `resume`, the
    # conversation id is not attributable without a full flag table, so
    # extraction refuses: a mis-attributed join is worse than an unjoinable
    # row, which quarantines exactly as today.
    RESUME_VALUE_FLAGS = frozenset({"-C", "--cd", "-c", "--config", "-m", "--model", "--profile", "--image"})

    # Provider conversation-id shape for terminal-evidence lookup keys. The
    # persisted session id originates from the launch envelope with no shape
    # validation, so the port validates before any record path is derived:
    # one pattern rejects path separators, traversal segments, whitespace,
    # dots, and glob metacharacters in a single stroke.
    CONVERSATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")

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
        terminal_records_root: Path | str | None = None,
        consult_timeout_seconds: float | None = None,
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
        self.consult_timeout_seconds = self._finite(consult_timeout_seconds, TERMINAL_EVIDENCE_TIMEOUT_SECONDS)
        self._test_terminal_records_dir = None
        if terminal_records_root is not None:
            self.terminal_records_root = Path(terminal_records_root).expanduser().resolve()
        elif runner is _subprocess_runner:
            # Production source for the provider's own conversation records:
            # the canonical Codex records root under HOME. Consults only ever
            # read under it.
            self.terminal_records_root = Path.home() / ".codex" / "sessions"
        else:
            # An injected runner is a hermetic test boundary: its records
            # root is a session-local temp directory, never an ambient
            # home-relative read.
            self._test_terminal_records_dir = tempfile.TemporaryDirectory(prefix="execute-plan-codex-records-")
            self.terminal_records_root = Path(self._test_terminal_records_dir.name)
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
        test_records_dir = getattr(self, "_test_terminal_records_dir", None)
        if test_records_dir is not None:
            test_records_dir.cleanup()

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
    def _tolerant_tokens(command: str) -> list[str]:
        """Tokenize a process row's command text without shell parsing.

        Quotes read as literal characters and prompt text is never parsed
        as shell: the scan only needs to locate the wrapper binary token,
        the ``exec`` subcommand, and the accepted ``resume``/``--json``
        shape, all of which the adapter itself emits unquoted. One live
        worker's unmatched quote in its prompt arguments therefore cannot
        raise here and quarantine the host's capacity.
        """
        return command.split()

    @staticmethod
    def _locate_exec_invocation(argv: list[str]) -> list[str] | None:
        """Locate the wrapper binary token, ``exec``, and the invocation head.

        The one shape locator for both consumers, the inventory parse and
        the conversation-id extraction: the wrapper binary token is found
        by its path-independent name, ``exec`` must follow it directly, and
        the returned head is the token list after ``exec``. None when the
        row carries no recognized ``codex exec`` head.
        """
        codex_index = next(
            (index for index, value in enumerate(argv[:-1]) if Path(value).name in {"codex", "codex.exe"}),
            None,
        )
        if codex_index is None or argv[codex_index + 1] != "exec":
            return None
        return argv[codex_index + 2:]

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
            except (ValueError, TypeError) as exc:
                raise ValueError("malformed process row") from exc
            argv = CodexAdapter._tolerant_tokens(command)
            if pid <= 0 or not argv:
                raise ValueError("malformed process identity")
            start_time = " ".join(fields[1:6])
            invocation = CodexAdapter._locate_exec_invocation(argv)
            if not invocation or not (invocation[0] == "--json" or (invocation[0] == "resume" and "--json" in invocation[1:])):
                continue
            identity = {"pid": pid, "start_time": start_time}
            session_suffix = hashlib.sha256(start_time.encode("utf-8")).hexdigest()[:12]
            row = {
                "provider_session_id": f"codex-process-{pid}-{session_suffix}",
                "process_identity": identity,
            }
            conversation_id = CodexAdapter._resume_conversation_id(argv)
            if conversation_id is not None:
                # Additive join key: the conversation id a live `codex exec
                # resume` process carries in its argv. The row stays
                # process-keyed; rows with no parseable id are unchanged.
                row["conversation_id"] = conversation_id
            inventory.append(row)
        return inventory

    @staticmethod
    def _resume_conversation_id(argv: list[str]) -> str | None:
        """Extract the conversation id from an accepted ``exec resume`` argv.

        Accepted shapes are the production resume argv (the id directly
        after ``resume``) and variants where valueless flags precede or
        follow it, located through the shared ``codex exec`` head locator
        the inventory parse uses, over the tolerant token list. Returns
        None for everything else: fresh exec launches, resumes with no
        parseable id, and resumes whose id position is shadowed by a
        value-taking flag.
        """
        invocation = CodexAdapter._locate_exec_invocation(argv)
        if not invocation or invocation[0] != "resume":
            return None
        for token in invocation[1:]:
            if token in CodexAdapter.RESUME_VALUE_FLAGS:
                return None
            if not CodexAdapter._option_like(token):
                return token
        return None

    @classmethod
    def _valid_conversation_id(cls, conversation_id: Any) -> bool:
        return isinstance(conversation_id, str) and cls.CONVERSATION_ID_PATTERN.match(conversation_id) is not None

    def observe_terminal_evidence(self, conversation_id: str) -> dict[str, Any]:
        """Consult the provider's own conversation record for terminal evidence.

        Read-only against provider state: completion is derived only from
        the record content for the exact conversation launched under the
        claim, never from process absence, and no turn-starting command
        (``codex exec resume``) is ever invoked. The lookup key is
        shape-guarded before any record path is derived under the
        canonicalized records root. The port is total: every failure mode
        returns a non-terminal observation, never a raise, and the
        ``detail_signal`` field separates ``record-not-found`` (no record
        for the conversation) from ``record-not-terminal`` (record present,
        turn not proven completed) and refuses on identity mismatch, so the
        consuming wrapper can classify the bounded consult-outcome enum.
        ``observed_at`` is the consultation read time in the monotonic
        domain (``normalize_observation``'s default); the record's
        completion wall-clock timestamp, when present, rides as proof
        metadata only. The consult carries an explicit per-consult timeout
        (``consult_timeout_seconds``) that the in-process record scan
        honors cooperatively by checking the deadline per scan candidate;
        a local file read cannot be preempted, which is the recorded
        in-process residual.
        """
        try:
            return self._terminal_evidence(conversation_id)
        except Exception:  # the port is total: containment beats diagnosis
            return self._terminal_evidence_refusal("consult-error", ["terminal-evidence consult failed and was contained"])

    def _terminal_evidence(self, conversation_id: str) -> dict[str, Any]:
        if not self._valid_conversation_id(conversation_id):
            return self._terminal_evidence_refusal("invalid-conversation-id", [f"conversation id rejected as lookup key: {str(conversation_id)[:64]!r}"])
        record_text, retrieval_error = self._read_conversation_record(conversation_id)
        if retrieval_error is not None:
            return self._terminal_evidence_refusal(retrieval_error, [f"conversation record retrieval failed: {retrieval_error}"])
        if record_text is None:
            return self._terminal_evidence_refusal("record-not-found", ["no conversation record under the canonical records root"])
        envelopes, malformed = self._jsonl(record_text)
        if malformed or not envelopes:
            return self._terminal_evidence_refusal("record-not-terminal", ["conversation record is not a parseable JSONL envelope stream"])
        record_id = next(
            (
                identity
                for item in envelopes
                for source in (item, item.get("payload", {}))
                if isinstance(source, Mapping)
                for identity in (source.get("thread_id") or source.get("session_id") or source.get("id"),)
                if identity
            ),
            None,
        )
        if not isinstance(record_id, str) or record_id != conversation_id:
            # Identity binding derives from the record's content only: the
            # lookup argument is never echoed onto the observation.
            return self._terminal_evidence_refusal("identity-mismatch", ["conversation record identity does not verify against the lookup key"])
        final_envelope = next(
            (
                item
                for item in reversed(envelopes)
                if "status" in item
                or item.get("type") in {"turn.completed", "result"}
                or isinstance(item.get("payload"), Mapping)
                and (
                    "status" in item["payload"]
                    or item["payload"].get("type") in {"turn.completed", "task_complete", "result"}
                )
            ),
            envelopes[-1],
        )
        final_payload = final_envelope.get("payload")
        final = dict(final_payload) if isinstance(final_payload, Mapping) else dict(final_envelope)
        if final.get("type") == "task_complete":
            final["type"] = "turn.completed"
        final.setdefault("timestamp", final_envelope.get("timestamp"))
        translated = self.translate_host_result(final, 0, f"terminal-evidence:{conversation_id}")
        if translated.get("status") != "success" or translated.get("reason_code") != "completed":
            return self._terminal_evidence_refusal("record-not-terminal", [f"conversation record does not prove the turn completed: {translated.get('status')}/{translated.get('reason_code')}"])
        proof = {
            "verified": True,
            "kind": "provider-terminal",
            "record_completed_at": final.get("completed_at") or final.get("timestamp"),
        }
        return self.normalize_observation("terminal-evidence", "terminal", provider_session_id=record_id) | {"proof": proof, "detail_signal": "record-terminal"}

    def _terminal_evidence_refusal(self, detail: str, evidence: list[str]) -> dict[str, Any]:
        return self.normalize_observation("terminal-evidence", "unavailable") | {
            "proof": {"verified": False, "kind": "provider-terminal"},
            "detail_signal": detail,
            "evidence": bounded_evidence(evidence),
        }

    def _read_conversation_record(self, conversation_id: str) -> tuple[str | None, str | None]:
        """Read the conversation record under the canonicalized records root.

        Returns ``(text, error)``: ``(None, None)`` when no record exists
        (the caller classifies record-not-found), ``(None, reason)`` when
        retrieval failed, and ``(text, None)`` on success. The canonical
        direct layout is tried first; a bounded scan over the root covers
        date-partitioned rollout naming. The scan checks the consult
        deadline per candidate entry.
        """
        try:
            direct = self.terminal_records_root / f"{conversation_id}.jsonl"
            if direct.is_file():
                return direct.read_text(encoding="utf-8"), None
            started = time.monotonic()
            for candidate in self.terminal_records_root.rglob(f"*{conversation_id}.jsonl"):
                if time.monotonic() - started > self.consult_timeout_seconds:
                    return None, "consult-timeout"
                if candidate.is_file():
                    return candidate.read_text(encoding="utf-8"), None
            return None, None
        except (OSError, UnicodeDecodeError, ValueError):
            return None, "retrieval-error"

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
        if not capabilities.validate_policy_token(policy_token, repo_root=str(self.repo_root), generation=generation):
            return self._blocked("runtime-policy-unavailable", ["missing or invalid driver policy token"], generation=generation, checkpoint=f"{task_id}:policy")
        role = task.get("worker_role")
        try:
            prompt_contract = json.loads(prompt)
        except (TypeError, json.JSONDecodeError):
            prompt_contract = None
        if (
            not isinstance(role, Mapping)
            or role.get("role") != "single-task-worker"
            or role.get("task_id") != task_id
            or not isinstance(role.get("claim_token"), str)
            or not role["claim_token"].strip()
            or role.get("generation") != generation
            or not isinstance(role.get("task_body"), str)
            or not role["task_body"].strip()
            or not isinstance(role.get("allowed_paths"), list)
            or not role["allowed_paths"]
            or role["allowed_paths"] != list((policy_token or {}).get("allowed_paths", ()))
            or not isinstance(role.get("required_criteria"), list)
            or not role["required_criteria"]
            or not isinstance(role.get("validation_commands"), list)
            or not role["validation_commands"]
            or role.get("evidence_owner") != "worker"
            or not isinstance(role.get("parent_obligations"), list)
            or not isinstance(role.get("worker_log_destination"), str)
            or not role["worker_log_destination"].strip()
            or prompt_contract != dict(role)
        ):
            return self._blocked("contract-violation", ["missing or mismatched validated task-worker role"], generation=generation, checkpoint=f"{task_id}:policy")
        if self._option_like(prompt):
            return self._blocked("contract-violation", ["option-like or empty prompt rejected"], generation=generation, checkpoint=f"{task_id}:policy")
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
