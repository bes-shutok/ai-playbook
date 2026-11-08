#!/usr/bin/env python3
"""Receipt-backed reconciliation for one done-pending execute-plan handoff.

Bounded recovery operation for the host-native execute-plan orchestrator: a
task whose accepted worker completion is recorded as terminal (status
``done-pending`` in ``runtime_state.json``) while reviewed plan corrections
changed the plan digest or the task checkbox projection afterwards. The
helper validates a reconciliation receipt against disk evidence and applies
ONE atomic ``runtime_state.json`` replacement that stores, for that task
only, the receipt (``tasks[task_id].handoff_reconciliation``), the launched
task-scope digest (``tasks[task_id].task_scope_digest``), and the reconciled
checkbox projection.

Ownership boundary: this module owns only receipt validation and the atomic
per-task reconciliation. It never runs preflight, launches workers, owns
recovery routing, touches ``scripts/execute_plan_runtime.py``'s retained
operations, or commits. The orchestrator parent remains the sole caller and
keeps every other runtime-state update, ordinary preflight, the done commit
gate, and the existing prelaunch remedies (the reviewed task-scope change
referral and the fresh-review path) unchanged.

Serialization contract (the existing execution claim plus the parent-only
sequential writer): the helper requires the repository's active execution
claim to name the invoking session, re-derives run identity, task identity,
task-scope digest, and expected manifest generation immediately before the
replacement, and refuses on any drift. There is no new lock, dispatch gate,
or fence: the expected-generation binding is the compare-and-swap anchor,
and a refused or interrupted write leaves either the previous state bytes or
the complete new receipt and projection (temp file plus ``os.replace``).

Receipt identity and retries: the stored receipt's identity fields (all
fields except ``expected_generation``, which stays as the historical
compare-and-swap binding) must equal the freshly derived receipt, and the
stored reconciled projection must match the record, for an
``already-reconciled`` success without another write or generation
increment; any other difference refuses as a mismatch.

Task-scope digest (the plan Terms recipe): the sha256 of the complete task
section (the ``### Task N:`` heading through the line before the next
``### ``/``## `` heading or end of file, the shared ``plan_task_span`` span
rule) with only the ``[ ]``/``[x]`` checklist marker normalized to a single
canonical form, so completion marking does not change the worker's assigned
scope.

Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with a final stdout
line ``OUTCOME: pass`` (``status: success``, reason ``reconciled`` or
``already-reconciled``), 1 ``OUTCOME: fail`` (a modeled refusal; the JSON
result on stdout carries the named ``reason_code`` and evidence), 3
``OUTCOME: tool_error`` (unsupported data or an environment or write
failure; nothing mutated). ``--help`` is a metadata exit with no OUTCOME
line.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import plan_readiness
import validate_review_staging as vrs

DONE_PENDING_STATUS = "done-pending"
RECONCILED_STATUS = "complete"
RECEIPT_VERSION = 1
CLAIMS_REL = "docs/tmp/execution-claims"
REVIEWS_DIR_PARTS = (".ai-playbook", "reviews")
STATE_SUFFIX_NEWLINE = b"\n"

TASK_HEADING_RE = re.compile(r"^### Task (\d+):")
CHECKBOX_MARKER_RE = re.compile(r"^(\s*)- \[[ x]\]")
CHECKBOX_LINE_RE = re.compile(r"^\s*- \[([ x])\]")

PASS = "pass"
FAIL = "fail"
TOOL_ERROR = "tool_error"

# The already-reconciled comparison set: every receipt field that must match
# the freshly derived receipt exactly. ``expected_generation`` is excluded on
# purpose: it stays in the stored receipt as the historical compare-and-swap
# binding of the reconciliation write, while later unrelated parent-owned
# writes legitimately advance the live generation.
RECEIPT_IDENTITY_FIELDS = (
    "receipt_version",
    "run_session_id",
    "plan_slug",
    "plan_path",
    "plan_digest",
    "task_id",
    "plan_task",
    "task_scope_digest",
    "worker_receipt_digest",
    "review",
    "checkbox_projection",
    "reconciled_status",
)

# Re-read drift mapping: the receipt field whose change between validation
# and the immediate pre-replacement re-read names the refusal.
DRIFT_REASON_BY_FIELD = {
    "expected_generation": "stale-generation",
    "run_session_id": "run-identity-drift",
    "plan_slug": "plan-identity-drift",
    "plan_path": "plan-identity-drift",
    "plan_digest": "plan-bytes-changed",
    "task_id": "task-identity-drift",
    "plan_task": "task-identity-drift",
    "task_scope_digest": "task-scope-changed",
    "worker_receipt_digest": "worker-receipt-changed",
    "review": "review-evidence-drift",
    "checkbox_projection": "plan-bytes-changed",
}

NEXT_ACTION = (
    "rerun ordinary preflight and the done commit gate, then select the "
    "next task; never hand-edit runtime_state.json"
)


class _Refusal(Exception):
    """A modeled reconciliation refusal; nothing was mutated."""

    def __init__(self, reason_code: str, evidence: list[str], generation: int | None = None):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.evidence = evidence
        self.generation = generation


class _ToolError(Exception):
    """An unsupported input or unheld environment assumption; nothing was
    mutated and the run classifies as tool error."""

    def __init__(self, reason_code: str, evidence: list[str]):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.evidence = evidence


class _Success(Exception):
    """A terminal success shape (``reconciled`` or ``already-reconciled``)
    raised so refusals stay the only other result paths."""

    def __init__(self, reason_code: str, evidence: list[str], generation: int, receipt: dict[str, Any]):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.evidence = evidence
        self.generation = generation
        self.receipt = receipt


def _result(status: str, reason_code: str, evidence: list[str], **extra: Any) -> dict[str, Any]:
    result = {
        "status": status,
        "reason_code": reason_code,
        "evidence": evidence,
    }
    result.update(extra)
    return result


def _read_bytes(path: Path) -> bytes:
    """The one byte-read seam for state and plan operands, so the
    between-reads drift tests can interpose a mutation without touching the
    file layout the helper owns."""
    return path.read_bytes()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_object_digest(value: Any) -> str:
    """sha256 over a JSON object's canonical form; the binding for the
    accepted worker terminal receipt that the task record keeps verbatim."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stable_identity(path: Path, repo_root: Path) -> str:
    """Repository-relative posix identity for a path under the repo root;
    the resolved absolute form otherwise."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return str(resolved)


def _extract_task_section(plan_text: str, task_number: int) -> str:
    """The complete task section: the ``### Task N:`` heading through the
    line before the next ``### ``/``## `` heading or end of file (the shared
    span rule)."""
    lines = plan_text.splitlines(keepends=True)
    start = None
    for index, line in enumerate(lines):
        match = TASK_HEADING_RE.match(line)
        if match and int(match.group(1)) == task_number:
            start = index
            break
    if start is None:
        raise _Refusal(
            "task-not-found",
            [f"plan has no '### Task {task_number}:' heading; task identity cannot bind"],
        )
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("## ") or line.startswith("### "):
            return "".join(lines[start:index])
    return "".join(lines[start:])


def normalize_task_scope(section: str) -> str:
    """The task section with only the ``[ ]``/``[x]`` marker normalized to
    one canonical form; nothing else in the worker's assigned scope moves."""
    return "".join(
        CHECKBOX_MARKER_RE.sub(r"\1- [#]", line)
        for line in section.splitlines(keepends=True)
    )


def task_scope_digest(section: str) -> str:
    """The launched task-scope digest: sha256 over the normalized section."""
    return _sha256(normalize_task_scope(section).encode("utf-8"))


def checkbox_projection(section: str) -> dict[str, int]:
    """The observed checklist projection of the task section."""
    checked = 0
    total = 0
    for line in section.splitlines():
        match = CHECKBOX_LINE_RE.match(line)
        if match:
            total += 1
            if match.group(1) == "x":
                checked += 1
    return {"checked": checked, "total": total}


class HandoffReconciler:
    """Validate one done-pending handoff receipt and apply the atomic
    per-task runtime-state transition."""

    def __init__(
        self,
        state_path: Path | str,
        plan_path: Path | str,
        task_number: int,
        session: str,
        repo_root: Path | str,
        task_key: str | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        self.plan_path = Path(plan_path)
        self.task_number = int(task_number)
        self.session = str(session)
        self.repo_root = Path(repo_root).resolve()
        self.task_key = task_key if task_key is not None else str(self.task_number)

    # -- readers --------------------------------------------------------- #

    def _decode_plan(self, plan_raw: bytes) -> str:
        try:
            return plan_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise _ToolError("plan-unreadable", [f"plan operand is not decodable UTF-8: {exc}"]) from exc

    def _read_state(self) -> tuple[bytes, dict[str, Any]]:
        try:
            raw = _read_bytes(self.state_path)
        except OSError as exc:
            raise _ToolError(
                "state-unreadable", [f"runtime state unreadable at {self.state_path}: {exc}"]
            ) from exc
        try:
            state = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _ToolError(
                "state-unparseable", [f"runtime state unparseable at {self.state_path}: {exc}"]
            ) from exc
        if not isinstance(state, dict):
            raise _ToolError("state-shape-unusable", ["runtime state is not a JSON object"])
        for field in ("plan_slug", "run_session_id"):
            value = state.get(field)
            if not isinstance(value, str) or not value.strip():
                raise _ToolError(
                    "state-shape-unusable", [f"runtime state {field} must be a non-empty string"]
                )
        generation = state.get("generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise _ToolError(
                "state-shape-unusable",
                [f"runtime state generation must be a non-negative integer, got {generation!r}"],
            )
        tasks = state.get("tasks")
        if not isinstance(tasks, dict):
            raise _ToolError("state-shape-unusable", ["runtime state tasks must be a JSON object map"])
        return raw, state

    def _task_record(self, state: dict[str, Any]) -> dict[str, Any]:
        record = state["tasks"].get(self.task_key)
        if not isinstance(record, dict):
            raise _Refusal(
                "task-not-found",
                [f"runtime state tasks map carries no '{self.task_key}' record"],
                generation=state["generation"],
            )
        return record

    # -- execution claim --------------------------------------------------- #

    def _artifact_slug(self) -> str:
        try:
            return plan_readiness.artifact_slug(self.plan_path)
        except plan_readiness.ArtifactSlugRefusal as exc:
            raise _Refusal("artifact-slug-unusable", [str(exc)]) from exc

    def _resolve_primary_checkout(self) -> Path:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise _ToolError(
                "primary-checkout-unresolvable", [f"git worktree list failed: {exc}"]
            ) from exc
        if result.returncode != 0:
            raise _ToolError(
                "primary-checkout-unresolvable",
                [f"git worktree list failed: {result.stderr.strip()}"],
            )
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                return Path(line[len("worktree "):])
        raise _ToolError(
            "primary-checkout-unresolvable",
            ["git worktree list produced no worktree entry"],
        )

    @staticmethod
    def _claim_field(claim_path: Path, key: str) -> str:
        try:
            for line in claim_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith(f"{key}: "):
                    return line[len(f"{key}: "):].strip()
        except OSError:
            return ""
        return ""

    def _verify_claim(self) -> None:
        """The active execution claim gate: the helper itself refuses before
        any write path unless the repository's claim for this plan names the
        invoking session, so the recovery cannot be reached before claim
        acquisition even when only the parent would otherwise enforce it."""
        primary = self._resolve_primary_checkout()
        claim_path = primary / CLAIMS_REL / f"{self._artifact_slug()}.md"
        if not claim_path.is_file():
            raise _Refusal(
                "claim-missing",
                [
                    f"no active execution claim for plan slug {self._artifact_slug()!r} at {claim_path}",
                    "the host-native parent must hold the run claim before reconciliation",
                ],
            )
        claim_session = self._claim_field(claim_path, "session")
        if claim_session != self.session:
            holder = claim_session or "<missing>"
            raise _Refusal(
                "claim-foreign",
                [
                    f"active execution claim {claim_path} names session {holder!r}, "
                    f"want {self.session!r}",
                    "a foreign claim refuses the reconciliation untouched",
                ],
            )
        claim_plan = self._claim_field(claim_path, "plan")
        accepted_operands = {str(self.plan_path), _stable_identity(self.plan_path, self.repo_root)}
        if claim_plan and claim_plan not in accepted_operands:
            raise _Refusal(
                "claim-foreign",
                [
                    f"active execution claim {claim_path} binds plan {claim_plan!r}, "
                    f"want {self.plan_path} (or {_stable_identity(self.plan_path, self.repo_root)})",
                ],
            )

    # -- review evidence ---------------------------------------------------- #

    def _review_evidence(self, plan_digest: str) -> dict[str, Any]:
        reviews_dir = self.repo_root.joinpath(*REVIEWS_DIR_PARTS)
        slug = self._artifact_slug()
        if not reviews_dir.is_dir():
            raise _Refusal(
                "review-evidence-unusable",
                [f"no reviews directory at {reviews_dir}; no review record can bind the plan bytes"],
            )
        try:
            latest = plan_readiness.latest_review_round(
                reviews_dir,
                slug,
                plan_identity=_stable_identity(self.plan_path, self.repo_root),
            )
        except plan_readiness.AmbiguousReviewSeries as exc:
            raise _Refusal("review-evidence-unusable", [str(exc)]) from exc
        if latest is None:
            raise _Refusal(
                "review-evidence-unusable",
                [f"no review artifact for slug {slug!r} under {reviews_dir}"],
            )
        record_path, round_no = latest
        sidecar_path = vrs.stats_sidecar_path(record_path)
        try:
            payload = json.loads(_read_bytes(sidecar_path).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _Refusal(
                "review-evidence-unusable",
                [f"stats sidecar for round r{round_no} is unreadable or invalid JSON: {exc}"],
            ) from exc
        if not isinstance(payload, dict) or not vrs.is_current_shape(payload):
            raise _Refusal(
                "review-evidence-unusable",
                [f"stats sidecar for round r{round_no} is not a current-shape review payload"],
            )
        if payload.get("source_kind") != "plan":
            raise _Refusal(
                "review-evidence-unusable",
                [
                    f"stats sidecar for round r{round_no} declares source_kind "
                    f"{payload.get('source_kind')!r}, want 'plan'"
                ],
            )
        if payload.get("source_digest") != plan_digest:
            raise _Refusal(
                "plan-digest-stale",
                [
                    f"review round r{round_no} binds source_digest "
                    f"{payload.get('source_digest')!r}, but the current plan bytes hash to "
                    f"{plan_digest}",
                    "stale review evidence never reconciles; obtain the fresh ready review for "
                    "the current bytes first",
                ],
            )
        verdict = plan_readiness.sidecar_verdict(payload)
        if verdict != "yes":
            raise _Refusal(
                "review-verdict-no",
                [f"review round r{round_no} verdict is {verdict!r}, want 'yes'"],
            )
        return {
            "record": _stable_identity(record_path, self.repo_root),
            "sidecar": _stable_identity(sidecar_path, self.repo_root),
            "round": f"r{round_no}",
            "source_digest": plan_digest,
            "verdict": "yes",
        }

    # -- receipt derivation --------------------------------------------------- #

    def _terminal_receipt_digest(self, record: dict[str, Any]) -> str:
        receipt = record.get("terminal_receipt")
        if not isinstance(receipt, dict) or not receipt:
            raise _Refusal(
                "terminal-receipt-missing",
                [
                    f"task '{self.task_key}' carries no accepted worker terminal receipt "
                    "(tasks.task_id.terminal_receipt must be a non-empty object)",
                    "only an accepted done-pending completion reconciles",
                ],
            )
        return _canonical_object_digest(receipt)

    def _derive_receipt(
        self, plan_raw: bytes, state: dict[str, Any], require_done_pending: bool = True
    ) -> dict[str, Any]:
        """Derive the requested reconciliation receipt from disk evidence.

        Every precondition check runs here, so the immediate
        pre-replacement re-read re-derives the identical receipt and any
        drift or newly failed precondition names its own refusal without
        mutating anything. The validation pass (``require_done_pending``
        False) additionally admits a record already carrying its stored
        reconciliation receipt, so the exact-match retry comparison runs;
        the pre-replacement re-read always demands the strict done-pending
        state.
        """
        generation = state["generation"]
        plan_digest = _sha256(plan_raw)
        plan_text = self._decode_plan(plan_raw)
        try:
            section = _extract_task_section(plan_text, self.task_number)
        except _Refusal as exc:
            exc.generation = generation
            raise
        scope = task_scope_digest(section)
        projection = checkbox_projection(section)
        canonical_plan_slug = plan_readiness.feature_slug(self.plan_path)
        if state["plan_slug"] != canonical_plan_slug:
            raise _Refusal(
                "plan-identity-mismatch",
                [
                    f"runtime state plan_slug {state['plan_slug']!r} does not match the plan "
                    f"canonical filename slug {canonical_plan_slug!r}",
                ],
                generation=generation,
            )
        self._verify_claim()
        review = self._review_evidence(plan_digest)
        record = self._task_record(state)
        status = record.get("status")
        admitted = status == DONE_PENDING_STATUS or (
            not require_done_pending
            and status == RECONCILED_STATUS
            and isinstance(record.get("handoff_reconciliation"), dict)
        )
        if not admitted:
            raise _Refusal(
                "task-state-not-done-pending",
                [
                    f"task '{self.task_key}' status is {status!r}, want {DONE_PENDING_STATUS!r}",
                    "only a done-pending task (accepted worker terminal completion, boundary "
                    "not yet committed) reconciles",
                ],
                generation=generation,
            )
        worker_receipt_digest = self._terminal_receipt_digest(record)
        launched_scope = record.get("task_scope_digest")
        if launched_scope is not None:
            if launched_scope != scope:
                raise _Refusal(
                    "task-scope-changed",
                    [
                        f"launched task-scope digest {launched_scope} does not match the current "
                        f"normalized task section digest {scope}",
                        "task text changed beyond the checkbox markers after launch; the "
                        "reviewed task-scope change referral route stays the remedy for that case",
                    ],
                    generation=generation,
                )
        else:
            # Legacy done-pending record without the per-task scope digest:
            # the launch scope is recoverable ONLY from exact plan bytes whose
            # digest equals the run's saved launch plan_digest; the current
            # bytes then are the launch bytes.
            launch_digest = state.get("plan_digest")
            if not isinstance(launch_digest, str) or launch_digest != plan_digest:
                raise _Refusal(
                    "launch-scope-unverified",
                    [
                        f"task '{self.task_key}' carries no task_scope_digest and the current "
                        f"plan digest {plan_digest} does not equal the run's saved launch "
                        f"plan_digest {launch_digest!r}",
                        "no exact launch bytes prove the worker's assigned scope; refusing "
                        "without mutation",
                    ],
                    generation=generation,
                )
        if projection["checked"] < projection["total"]:
            raise _Refusal(
                "projection-incomplete",
                [
                    f"reviewed plan marks task '{self.task_key}' projection "
                    f"{projection['checked']}/{projection['total']} checked; a done-pending "
                    "handoff reconciles only against reviewed bytes that mark the task's "
                    "clauses complete",
                ],
                generation=generation,
            )
        return {
            "receipt_version": RECEIPT_VERSION,
            "run_session_id": state["run_session_id"],
            "plan_slug": state["plan_slug"],
            "plan_path": _stable_identity(self.plan_path, self.repo_root),
            "plan_digest": plan_digest,
            "task_id": self.task_key,
            "plan_task": self.task_number,
            "expected_generation": generation,
            "task_scope_digest": scope,
            "worker_receipt_digest": worker_receipt_digest,
            "review": review,
            "checkbox_projection": projection,
            "reconciled_status": RECONCILED_STATUS,
        }

    @staticmethod
    def _projection_applied(record: dict[str, Any], receipt: dict[str, Any]) -> bool:
        return (
            record.get("status") == receipt["reconciled_status"]
            and record.get("checkbox") == (receipt["checkbox_projection"]["total"] > 0)
            and record.get("task_scope_digest") == receipt["task_scope_digest"]
        )

    def _already_reconciled(self, record: dict[str, Any], requested: dict[str, Any]) -> bool:
        stored = record.get("handoff_reconciliation")
        if stored is None:
            return False
        if not isinstance(stored, dict):
            raise _Refusal(
                "reconciliation-mismatch",
                [
                    f"task '{self.task_key}' carries a malformed handoff_reconciliation value "
                    f"({type(stored).__name__}); refusing without mutation",
                ],
                generation=requested["expected_generation"],
            )
        differing = [field for field in RECEIPT_IDENTITY_FIELDS if stored.get(field) != requested.get(field)]
        if differing:
            raise _Refusal(
                "reconciliation-mismatch",
                [
                    f"stored handoff_reconciliation for task '{self.task_key}' differs from the "
                    f"requested receipt on: {', '.join(differing)}",
                    "stale or mismatched reconciliation evidence refuses; repair the evidence "
                    "or the state, then retry",
                ],
                generation=requested["expected_generation"],
            )
        if not self._projection_applied(record, stored):
            raise _Refusal(
                "reconciliation-mismatch",
                [
                    f"task '{self.task_key}' carries the requested receipt but its record does "
                    "not match the reconciled projection (status, checkbox, or task_scope_digest)",
                ],
                generation=requested["expected_generation"],
            )
        return True

    def _verify_before_replace(self, requested: dict[str, Any], plan_raw: bytes, state: dict[str, Any]) -> None:
        """The immediate pre-replacement re-read: re-derive every receipt
        input from the fresh bytes and refuse any drift, named per field.
        This is the last read before the atomic replacement."""
        fresh = self._derive_receipt(
            plan_raw, state, require_done_pending=True
        )  # newly failed preconditions refuse here
        drifted = [
            DRIFT_REASON_BY_FIELD[field]
            for field in RECEIPT_IDENTITY_FIELDS + ("expected_generation",)
            if fresh.get(field) != requested.get(field)
        ]
        if drifted:
            raise _Refusal(
                drifted[0],
                [
                    f"runtime state or plan bytes drifted between validation and the "
                    f"pre-replacement re-read (drift class {drifted[0]})",
                ],
                generation=state["generation"],
            )

    # -- atomic write ------------------------------------------------------------ #

    def _write_temp_payload(self, fd: int, payload: bytes) -> None:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

    def _atomic_write(self, payload: bytes) -> None:
        directory = self.state_path.parent
        try:
            fd, tmp_name = tempfile.mkstemp(dir=str(directory), prefix=".reconcile-handoff-", suffix=".tmp")
        except OSError as exc:
            raise _ToolError(
                "atomic-write-failed", [f"runtime state temp file creation failed: {exc}"]
            ) from exc
        tmp_path = Path(tmp_name)
        try:
            self._write_temp_payload(fd, payload)
            _replace(tmp_path, self.state_path)
        except Exception as exc:  # an injected or OS-level write failure
            raise _ToolError(
                "atomic-write-failed", [f"atomic runtime-state replacement failed: {exc}"]
            ) from exc
        finally:
            # os.replace moved the name away on success; the unlink only ever
            # removes a leftover temp from a failed attempt.
            try:
                tmp_path.unlink()
            except OSError:
                pass

    # -- entry point ---------------------------------------------------------------- #

    def reconcile(self) -> tuple[dict[str, Any], str]:
        try:
            self._reconcile()
        except _Success as exc:
            result = _result(
                "success",
                exc.reason_code,
                exc.evidence,
                task_id=self.task_key,
                plan_task=self.task_number,
                generation=exc.generation,
                receipt=exc.receipt,
                next_action=NEXT_ACTION,
            )
            return result, PASS
        except _Refusal as exc:
            result = _result(
                "refused",
                exc.reason_code,
                exc.evidence,
                task_id=self.task_key,
                generation=exc.generation,
            )
            return result, FAIL
        except _ToolError as exc:
            result = _result("error", exc.reason_code, exc.evidence, task_id=self.task_key)
            return result, TOOL_ERROR
        raise AssertionError("reconcile returned without a result")

    def _reconcile(self) -> None:
        try:
            plan_raw = _read_bytes(self.plan_path)
        except OSError as exc:
            raise _ToolError("plan-unreadable", [f"plan operand unreadable at {self.plan_path}: {exc}"]) from exc
        if not plan_raw.strip():
            raise _ToolError("plan-unreadable", [f"plan operand missing or empty: {self.plan_path}"])
        state_raw, state = self._read_state()
        requested = self._derive_receipt(plan_raw, state, require_done_pending=False)
        record = self._task_record(state)
        if self._already_reconciled(record, requested):
            raise _Success(
                "already-reconciled",
                [
                    f"task '{self.task_key}' already carries the requested receipt and "
                    "reconciled projection",
                ],
                state["generation"],
                record["handoff_reconciliation"],
            )
        # The immediate pre-replacement re-read: the last read before the
        # atomic replacement, refusing on any identity, scope, or generation
        # drift.
        fresh_plan_raw = _read_bytes(self.plan_path)
        fresh_state_raw, fresh_state = self._read_state()
        self._verify_before_replace(requested, fresh_plan_raw, fresh_state)
        new_state = copy.deepcopy(fresh_state)
        record = dict(new_state["tasks"][self.task_key])
        record["status"] = requested["reconciled_status"]
        record["checkbox"] = requested["checkbox_projection"]["total"] > 0
        record["task_scope_digest"] = requested["task_scope_digest"]
        record["handoff_reconciliation"] = requested
        new_state["tasks"][self.task_key] = record
        new_state["generation"] = fresh_state["generation"] + 1
        payload = (
            json.dumps(new_state, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
            + STATE_SUFFIX_NEWLINE
        )
        self._atomic_write(payload)
        raise _Success(
            "reconciled",
            [
                f"task '{self.task_key}' reconciled at generation {new_state['generation']}; "
                "receipt, task-scope digest, and reconciled projection stored in the same "
                "atomic replacement",
            ],
            new_state["generation"],
            requested,
        )


_replace = os.replace


class _OutcomeParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 with a final
    ``OUTCOME: tool_error`` line on stderr (the parser-override precedent);
    ``--help`` stays a metadata exit."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        sys.stderr.write(f"OUTCOME: {TOOL_ERROR}\n")
        raise SystemExit(3)


def build_parser() -> _OutcomeParser:
    parser = _OutcomeParser(
        prog="reconcile_execute_plan_handoff.py",
        description="Receipt-backed reconciliation for one done-pending "
        "execute-plan task handoff (validation plus one atomic "
        "runtime_state.json replacement; nothing else).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    operation = subparsers.add_parser(
        "reconcile",
        help="reconcile one done-pending task against the reviewed plan bytes",
    )
    operation.add_argument("--state", type=Path, required=True, help="the run's runtime_state.json path")
    operation.add_argument("--plan", type=Path, required=True, help="the exact active plan path")
    operation.add_argument("--task", type=int, required=True, help="the plan task number (### Task N:)")
    operation.add_argument(
        "--task-key",
        default=None,
        help="runtime_state tasks map key (defaults to the task number)",
    )
    operation.add_argument(
        "--session",
        required=True,
        help="this session's id; the active execution claim must name it",
    )
    operation.add_argument("--repo-root", type=Path, default=Path.cwd(), help="repository root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reconciler = HandoffReconciler(
        state_path=args.state,
        plan_path=args.plan,
        task_number=args.task,
        session=args.session,
        repo_root=args.repo_root,
        task_key=args.task_key,
    )
    result, outcome = reconciler.reconcile()
    print(json.dumps(result, sort_keys=True))
    print(f"OUTCOME: {outcome}")
    if outcome == PASS:
        return 0
    return 1 if outcome == FAIL else 3


if __name__ == "__main__":
    raise SystemExit(main())
