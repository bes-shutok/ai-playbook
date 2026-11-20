#!/usr/bin/env python3
"""Workflow-neutral standing resume watcher state machine.

One shared state machine over an explicit authoring-state adapter:

- ``WatcherStateAdapter`` owns authoritative machine-state operations (lock-held
  read, compare-and-swap replacement/cancellation, semantic progress, boundary,
  and projection operations). ``PlansAuthoringWatcherAdapter`` supplies the
  plans skill's machine-state JSON.
- ``SchedulerAdapter``: one host automation boundary. The pause-protocol
  fallback chain is automation create, then a launchd one-shot with a
  sentinel self-disable file, then report-only naming the exact resume
  command and time.

Guard cleanup contract (canonical): an atomic compare-and-delete under a
shared ``fcntl.flock`` lock file at the guard flag's directory
(``budget-guard.lock``; canonical ``~/.ai-playbook/runtime/budget-guard.lock``)
participated in by the probe writer (``scripts/quota_window_probe.py``), both
budget-guard hook adapters (``agents/hooks/budget-guard/budget_guard_core.py``),
this watcher, and fired-marker cleanup. The read, the compare, and the unlink
occur while that shared lock is held, and the writer's ``os.replace`` holds
the same lock. Never use a standalone re-read followed by unlink, or an inode
check without writer participation: a cleanup that decided on the old flag
must never remove a flag (or fired marker) replaced by a newer window.

Stdlib-only; no network access.
"""

from __future__ import annotations

import abc
import contextlib
import fcntl
import hashlib
import json
import math
import os
import pathlib
import plistlib
import re
import shutil
import shlex
import subprocess
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

GUARD_LOCK_NAME = "budget-guard.lock"
DEFAULT_FLAG_PATH = pathlib.Path("~/.ai-playbook/runtime/budget-guard.flag")
FIRED_MARKER_NAME = "budget-guard.fired"
CODEX_QUOTA_WAKE_FIXED_PROMPT = (
    "Resume the paused maintenance run. Re-read current state and primary quota; "
    "derive the target and phase from current state. Before maintenance work, "
    "run codex-quota-wake-reconcile using the JSON data on the next line."
)


def _has_control_character(value: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in value)

# Standing plans-authoring watcher receipt fields. The plans-authoring state
# adapter and CLI share this schema and state machine.
RESUME_WATCHER_FIELDS = (
    "watcher_id",
    "plan_slug",
    "repo_root",
    "plan_path",
    "plan_digest",
    "scheduled_at_epoch",
    "reset_at_epoch",
    "expected_generation",
    "expected_progress_revision",
    "boundary_generation",
    "binding",
    "status",
    "replaces",
)


def validate_resume_watcher_receipt(receipt: Mapping[str, Any]) -> None:
    """Fail closed on a malformed watcher receipt before any CAS mutation."""

    if not isinstance(receipt, Mapping):
        raise ValueError("resume watcher receipt must be a mapping")
    missing = [field for field in RESUME_WATCHER_FIELDS if field not in receipt]
    if missing:
        raise ValueError(f"resume watcher receipt missing fields: {', '.join(missing)}")
    for field in ("watcher_id", "plan_slug", "repo_root", "plan_path", "binding", "status"):
        if not isinstance(receipt[field], str) or not receipt[field].strip():
            raise ValueError(f"resume watcher receipt field must be a non-empty string: {field}")
    if receipt["status"] != "pending":
        raise ValueError("resume watcher receipt status must be 'pending' when scheduled")
    if receipt["replaces"] is not None and not isinstance(receipt["replaces"], str):
        raise ValueError("resume watcher receipt replaces must be a watcher id or null")
    for field in ("scheduled_at_epoch", "reset_at_epoch", "expected_generation", "expected_progress_revision", "boundary_generation"):
        value = receipt[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"resume watcher receipt field must be numeric: {field}")
    if not isinstance(receipt["plan_digest"], str) or not re.fullmatch(r"[0-9a-f]{64}", receipt["plan_digest"]):
        raise ValueError("resume watcher receipt plan_digest must be a sha-256 hex digest")


# The four stand-down reasons are spelled at their single evaluation site in
# :func:`evaluate_fire`; a constant tuple duplicating them invited a
# non-registry registry that could drift from the live checks (r2 F14
# deleted the duplicate).


# ---------------------------------------------------------------------------
# Shared guard lock and atomic compare-and-delete cleanup
# ---------------------------------------------------------------------------


def guard_lock_path(flag_path: os.PathLike | str) -> pathlib.Path:
    """The shared guard lock file: next to the flag, named budget-guard.lock."""

    return pathlib.Path(os.path.expanduser(str(flag_path))).parent / GUARD_LOCK_NAME


@contextlib.contextmanager
def budget_guard_lock(
    flag_path: os.PathLike | str,
    timeout_seconds: float = 2.0,
    poll_seconds: float = 0.02,
) -> Iterator[bool]:
    """Hold the shared budget-guard lock; yield True when acquired.

    Canonical lock acquisition for the watcher and fired-marker cleanup; the
    probe writer and both hook adapters hold the same file by the same name
    (they are deployed standalone and cannot import this module in every
    layout). On lock-unavailability the caller skips the removal quietly:
    fail-open behavior is unchanged and the next fire retries the cleanup.
    """

    path = guard_lock_path(flag_path)
    fd = None
    acquired = False
    try:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError:
            yield False
            return
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(poll_seconds)
        yield acquired
    finally:
        if fd is not None:
            try:
                if acquired:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def parse_guard_flag(text: str) -> dict[str, str]:
    """Parse the flag's ``key=value`` lines (mirrors the hook core)."""

    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    return fields


def _flag_reset_epoch(fields: Mapping[str, str]) -> Optional[int]:
    raw = fields.get("reset_at_epoch", "")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _read_marker_epoch(path: pathlib.Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def compare_and_delete_flag(
    flag_path: os.PathLike | str,
    expected_reset_at_epoch: int,
    fired_path: os.PathLike | str | None = None,
) -> dict[str, Any]:
    """Atomic compare-and-delete of the guard flag and its fired marker.

    The read, the compare against ``expected_reset_at_epoch``, and the unlink
    all occur while the shared guard lock is held, so a probe writer's
    replacement can never interleave between this cleanup's decision and its
    unlink. A flag whose epoch differs from the expected one is a newer
    window: it is refused and survives. The fired marker is removed only
    when it still binds to the expected window, so a marker re-written for
    the current window survives (fired-marker replacement protection).
    """

    flag = pathlib.Path(os.path.expanduser(str(flag_path)))
    fired = pathlib.Path(os.path.expanduser(str(fired_path))) if fired_path is not None else flag.parent / FIRED_MARKER_NAME
    with budget_guard_lock(flag) as acquired:
        if not acquired:
            return {"removed": False, "refused": False, "reason": "guard-lock-unavailable", "flag_path": str(flag)}
        try:
            fields = parse_guard_flag(flag.read_text(encoding="utf-8"))
        except OSError:
            fields = {}
        current_epoch = _flag_reset_epoch(fields) if fields else None
        if current_epoch is None:
            return {"removed": False, "refused": False, "reason": "flag-absent", "flag_path": str(flag)}
        if current_epoch != int(expected_reset_at_epoch):
            return {
                "removed": False,
                "refused": True,
                "reason": "newer-window",
                "flag_reset_at_epoch": current_epoch,
                "expected_reset_at_epoch": int(expected_reset_at_epoch),
                "flag_path": str(flag),
            }
        try:
            flag.unlink()
        except OSError:
            pass
        marker = _read_marker_epoch(fired)
        marker_removed = False
        if marker == str(int(expected_reset_at_epoch)):
            try:
                fired.unlink()
            except OSError:
                pass
            marker_removed = True
        return {
            "removed": True,
            "refused": False,
            "reason": "cleared",
            "marker_removed": marker_removed,
            "flag_path": str(flag),
            "fired_path": str(fired),
        }


# ---------------------------------------------------------------------------
# Scheduling math and prompt rendering
# ---------------------------------------------------------------------------


def compute_fire_epoch(reset_at_epoch: int) -> int:
    """Reset time rounded UP to the whole minute, plus one minute."""

    minute = 60
    reset = int(reset_at_epoch)
    rounded = -(-reset // minute) * minute
    return rounded + minute


def compute_resume_at_iso(fire_epoch: int) -> str:
    return datetime.fromtimestamp(int(fire_epoch)).astimezone().isoformat()


def build_manual_resume_command(plan_path: str) -> str:
    """The exact manual resume command named by every report-only outcome.

    The plan path is shell-quoted at build time: the command is a
    fire-time ``sh -c`` payload (launchd one-shot) and a report-only
    string, so metacharacters in the path must never split words or
    execute (launchd-resume command injection; probe r4 F1 precedent).
    """

    return f"execute {shlex.quote(str(plan_path))}"


def build_resume_prompt(receipt: Mapping[str, Any], guard_cleanup: Mapping[str, Any] | None = None) -> str:
    """The watcher's self-contained resume prompt (exact plan path inside).

    Fire-aware (r2 F12): this prompt is rendered by the driver's
    ``watcher-fire`` operation AFTER the fences and the four stand-down
    checks already passed, so the prompt must not re-teach the manual
    pre-CLI procedure (re-applying the checks and compare-and-deleting
    guards by hand) or a literal agent loops and the automation never
    invokes watcher-fire. The manual procedure stays the SKILL.md
    no-CLI fallback only.

    The guard sentence is rendered from the actual cleanup receipt, never
    asserted ahead of it (r3 F4), across three outcomes (r5 F5): cleared
    (the compare-and-delete removed the guards, or none existed), attempted
    but not achieved (a cleanup is configured and ran but was refused or
    could not complete - it must claim no clearing and carry the retry
    guidance), and not configured (``guard_cleanup`` None - it must claim
    no clearing and still forbid the by-hand deletion).
    """

    if guard_cleanup is None:
        guard_sentence = (
            "no guard cleanup is configured for this boundary, so there is nothing cleared and nothing to "
            "retry: do not re-apply the stand-down checks and do not delete the guard flag and fired marker "
            "by hand; continue the loop."
        )
    elif guard_cleanup.get("removed") or guard_cleanup.get("reason") == "flag-absent":
        guard_sentence = (
            "the guards were "
            "already cleared through the atomic compare-and-delete on the resume decision, so do not re-apply "
            "the stand-down checks or delete the guard flag and fired marker by hand. If a guard cleanup was "
            "refused once by the budget guard, retry that cleanup after the single block; otherwise continue "
            "the loop."
        )
    else:
        reason = str(guard_cleanup.get("reason") or "guard-lock-unavailable")
        guard_sentence = (
            f"the guard cleanup was configured and attempted but did not complete (reason: {reason}), so "
            "nothing was cleared yet: retry that cleanup after the single block, and do not re-apply the "
            "stand-down checks or delete the guard flag and fired marker by hand; continue the loop."
        )
    return (
        f"Standing resume watcher {receipt.get('watcher_id')} fired for the budget-window reset and has "
        f"already cleared every fence and stand-down check. Re-enter execute-plan on the plan path "
        f"{receipt.get('plan_path')} and continue the loop from the Step 0.5 resume rules; "
        + guard_sentence
    )


def render_manifest_projection(snapshot: Mapping[str, Any]) -> str:
    """The human-readable manifest.md projection; machine state is authority."""

    watcher = snapshot.get("resume_watcher")
    if isinstance(watcher, Mapping):
        return (
            "pending_resume_watcher: {watcher_id} (binding={binding}, status={status}, "
            "reset_at_epoch={reset_at_epoch}, scheduled_at_epoch={scheduled_at_epoch}, "
            "boundary_generation={boundary_generation}, replaces={replaces})"
        ).format(
            watcher_id=watcher.get("watcher_id"),
            binding=watcher.get("binding"),
            status=watcher.get("status"),
            reset_at_epoch=watcher.get("reset_at_epoch"),
            scheduled_at_epoch=watcher.get("scheduled_at_epoch"),
            boundary_generation=watcher.get("boundary_generation"),
            replaces=watcher.get("replaces"),
        )
    return "pending_resume_watcher: none"


def plan_operand_digest(path: os.PathLike | str) -> tuple[Optional[str], Optional[str]]:
    """Digest of one plan operand through the shared shape resolver.

    Returns ``(digest, refusal)`` with exactly one non-None: a file operand
    digests its raw bytes; a well-formed plan directory digests the
    resolver's canonical manifest serialization, so the scheduled receipt
    and the live fire fence compare the same both-shapes recipe
    (plan-directory-shape plan, Task 3); a malformed DIRECTORY operand
    returns the resolver's named refusal (defect plus operand path, never a
    bare traceback). A FILE operand the resolver refuses (for example
    non-UTF-8 bytes) falls back to the raw-bytes sha256 digest, the
    pre-Task-3 behavior, so only a genuinely malformed directory operand
    refuses at schedule time. ``(None, None)`` when the sibling resolver
    module is unavailable, so a layout without it keeps the legacy
    unreadable refusal instead of an ImportError.
    """

    try:
        import plan_shape
    except ImportError:
        return None, None
    candidate = pathlib.Path(os.path.expanduser(str(path)))
    try:
        shape = plan_shape.resolve_plan_operand(candidate)
    except plan_shape.PlanShapeRefusal as exc:
        if candidate.is_dir():
            # A malformed directory operand keeps the named refusal: the
            # schedule-time fence must catch a wrong-shape operand.
            return None, str(exc)
        # A refused file operand digests its raw bytes (pre-Task-3
        # behavior): the digest fence compares bytes, so an unreadable file
        # still fails closed with the resolver's named refusal.
        try:
            return hashlib.sha256(candidate.read_bytes()).hexdigest(), None
        except OSError:
            return None, str(exc)
    return hashlib.sha256(shape.digest_payload).hexdigest(), None


def file_digest(path: os.PathLike | str | None) -> Optional[str]:
    """Current digest of the plan operand, or None when unreadable or absent.

    A file operand digests its raw bytes (unchanged); a directory operand
    digests through the shared shape resolver's manifest serialization
    (plan-directory-shape plan, Task 3). A malformed directory digests to
    None, so the digest fence fails closed exactly like an unreadable file.
    """

    if path is None:
        return None
    candidate = pathlib.Path(os.path.expanduser(str(path)))
    if candidate.is_dir():
        digest, _refusal = plan_operand_digest(candidate)
        return digest
    try:
        return hashlib.sha256(candidate.read_bytes()).hexdigest()
    except OSError:
        return None


def interrupt_after(user_interrupt: Any, scheduled_at_epoch: float) -> bool:
    """True when the user_interrupt field is newer than the scheduling epoch.

    A missing or unparseable field never trips; a latched old interrupt
    (recorded before this watcher was scheduled) never trips a later watcher.
    """

    if not isinstance(user_interrupt, str) or not user_interrupt.strip():
        return False
    try:
        moment = datetime.fromisoformat(user_interrupt)
    except ValueError:
        return False
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.timestamp() > float(scheduled_at_epoch)


# ---------------------------------------------------------------------------
# Adapter protocols
# ---------------------------------------------------------------------------


class WatcherStateAdapter(abc.ABC):
    """One workflow's machine-state operations for the shared watcher.

    Every operation that observes or mutates authoritative state is
    lock-held inside the adapter; the state machine itself owns no locks.
    Adapters expose the same read, compare-and-swap replacement/cancellation,
    semantic-progress, boundary, and projection operations so two workflows
    cannot drift into separate watcher protocols.
    """

    @abc.abstractmethod
    def read_state(self) -> Mapping[str, Any]:
        """Lock-held read of the watcher-relevant machine state."""

    @abc.abstractmethod
    def compare_and_swap_schedule(self, transition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Install or replace the pending watcher under the machine lock."""

    @abc.abstractmethod
    def compare_and_swap_supersede(self, transition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Supersede and clear the pending watcher under the machine lock."""

    @abc.abstractmethod
    def semantic_progress_changed(self, snapshot: Mapping[str, Any], expected_progress_revision: int) -> bool:
        """The semantic progress revision changed after the scheduling point."""

    @abc.abstractmethod
    def peer_resumed(self, snapshot: Mapping[str, Any], scheduled_at_epoch: int) -> bool:
        """A peer session resumed the work."""

    @abc.abstractmethod
    def archived_or_completed(self, snapshot: Mapping[str, Any]) -> bool:
        """The plan is archived or the run completed."""

    @abc.abstractmethod
    def aborted_or_interrupted(self, snapshot: Mapping[str, Any], scheduled_at_epoch: int) -> bool:
        """Aborted workflow state, or a user_interrupt newer than scheduling."""

    @abc.abstractmethod
    def projection(self, snapshot: Mapping[str, Any]) -> str:
        """Human-readable manifest.md projection of the watcher state."""


def watcher_cas_stale(
    transition: Mapping[str, Any],
    current_watcher_id: Any,
    generation: int,
    boundary_generation: int,
) -> bool:
    """The one compare-and-swap stale predicate for every watcher CAS writer.

    The transition's expected watcher id, generation, and boundary
    generation must all match the current authoring state.
    """

    return (
        transition.get("expected_watcher_id") != current_watcher_id
        or transition.get("expected_generation") != generation
        or transition.get("expected_boundary_generation") != boundary_generation
    )


class SchedulerAdapter(abc.ABC):
    """One host automation boundary for the watcher."""

    @abc.abstractmethod
    def schedule(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """Arm the one-shot; returns ``{"scheduled": bool, "mechanism": str, ...}``."""


class AutomationScheduler(SchedulerAdapter):
    """Host one-shot automation create; a refused create falls through."""

    def __init__(self, create: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None) -> None:
        self._create = create

    def schedule(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if self._create is None:
            return {"scheduled": False, "mechanism": "automation", "reason": "automation-capability-unavailable"}
        try:
            result = self._create(request)
        except Exception as exc:  # noqa: BLE001 - any refusal must fall through
            return {"scheduled": False, "mechanism": "automation", "reason": f"automation-create-refused: {exc}"}
        if not isinstance(result, Mapping) or result.get("scheduled") is not True:
            return {"scheduled": False, "mechanism": "automation", "reason": "automation-create-refused", "detail": result}
        return {"scheduled": True, "mechanism": "automation", "automation": dict(result)}


def launchd_identity_key(plan_slug: str | None, repo_root: str | None) -> str:
    """The short launchd identity key for one watcher's plan and repository.

    Concurrent schedules for different runs must never share one launchd
    label, job path, or sentinel (r3 F14): run B's plist write would clobber
    run A's job file and run B's bootout would remove A's loaded resume. The
    key is a 12-hex-digit digest over the plan slug and the canonical
    repository root, so two runs collide only when they are the same run.
    """

    return hashlib.sha256(f"{plan_slug or ''}\0{repo_root or ''}".encode("utf-8")).hexdigest()[:12]


def default_launchd_identity(plan_slug: str | None, repo_root: str | None) -> dict[str, str]:
    """The keyed default job dir, sentinel, and label for one watcher.

    The defaults the CLI watcher operations arm when the payload names no
    explicit paths (r3 F14): everything is keyed by the launchd identity key
    so concurrent runs stay isolated end to end.
    """

    key = launchd_identity_key(plan_slug, repo_root)
    return {
        "key": key,
        "job_dir": str(DEFAULT_LAUNCHD_JOB_DIR / key),
        "sentinel_path": str(DEFAULT_RESUME_SENTINEL.with_name(f"{DEFAULT_RESUME_SENTINEL.stem}-{key}{DEFAULT_RESUME_SENTINEL.suffix}")),
        "label": f"ai-playbook.budget-resume.{key}",
    }


def launchd_plist_path(job_dir: os.PathLike | str, label: str) -> pathlib.Path:
    """The one plist path for a job dir and label.

    Arm-side shared derivation (G2): the scheduler writes the job here, the
    receipt's carrier-identity record names the same path, and a structural
    test pins that no consumer re-derives an identity at fire time.
    """

    return pathlib.Path(str(job_dir)) / f"{label}.plist"


def armed_launchd_identity(job_dir: os.PathLike | str, sentinel_path: os.PathLike | str, label: str) -> dict[str, str]:
    """The FULL launchd carrier-identity record the arm persists (G2).

    The receipt is the sole carrier-identity source after the arm: label,
    job dir, plist path, sentinel path, and fired-marker path are persisted
    together by the schedule arm, so fire/clean/consume read exactly what
    the arm armed and never re-derive an identity at use time. ``armed`` is
    True only on this record; a schedule that arms no launchd (an automation
    echo) records ``{"armed": False, ...}`` explicitly instead.
    """

    return {
        "armed": True,
        "label": str(label),
        "job_dir": str(job_dir),
        "plist_path": str(launchd_plist_path(job_dir, str(label))),
        "sentinel_path": str(sentinel_path),
        "fired_marker_path": str(fired_marker_path(sentinel_path)),
    }


class LaunchdOneShotScheduler(SchedulerAdapter):
    """launchd one-shot with a sentinel self-disable file.

    Arming writes the job definition and THEN bootstraps it into the
    caller's launchd domain (r2 F4): a plist written to a non-scan
    directory is never loaded by launchd on its own, and even a scan-dir
    plist written after login stays inert without a bootstrap, so the
    old write-only arm reported ``scheduled=True`` for a job launchd
    would never fire. The bootstrap result is the arm result: a failed
    bootstrap removes the just-written plist and reports not-scheduled
    (reason ``launchd-bootstrap-failed``) so the fallback chain proceeds
    to report-only naming the manual command, never a silent stall.

    The job itself creates the sentinel at its first fire (``touch``
    before the manual command), so arming never short-circuits the very
    job it schedules (r1 F1) and the daily ``StartCalendarInterval``
    self-disables after the first fire. Exactly one arm per sentinel: a
    scheduler asked to arm while the sentinel already exists reports
    self-disabled so the fallback chain proceeds to report-only;
    a sentinel whose fired marker exists is a spent one-shot whose fire
    reached a terminal decision (r3 F16), so the marker and the stale
    sentinel are cleared and the arm re-arms for the new window.

    The job writes its stdout and stderr to log files next to the plist
    (r3 F16): a fire whose decision never reaches a resume (a fence
    refusal, a stand-down, an agent re-entry that never invoked
    watcher-fire) must leave its decision output on disk, not in
    launchd's void.

    The job definition is built with ``plistlib`` and the shell command
    quotes the sentinel path, so plan-path metacharacters can never break
    the plist XML or execute at fire time (r1 F14).
    """

    def __init__(
        self,
        job_dir: os.PathLike | str,
        sentinel_path: os.PathLike | str,
        label: str = "ai-playbook.budget-resume",
        bootstrap: Callable[[pathlib.Path], tuple[bool, str]] | None = None,
        cleanup_dir: os.PathLike | str | None = None,
        fail_closed_on_lock_unavailable: bool = False,
    ) -> None:
        self._job_dir = pathlib.Path(job_dir)
        self._sentinel_path = pathlib.Path(sentinel_path)
        self._label = label
        self._bootstrap = bootstrap or launchctl_bootstrap
        # The fail-closed arm lock (plan 2026-11-06-budget-resume-carrier-gc
        # Task 3) is a budget-resume-family behavior: the clocked-order
        # family shares the same budget-guard.lock file (its sentinels live
        # in the same runtime directory), and a discharge holding that lock
        # across its launchctl legs must park a clocked order on its own
        # legacy fail-open retry posture, not strand it report-only.
        self._fail_closed_on_lock_unavailable = fail_closed_on_lock_unavailable
        # r5 F13: the spent-pair cleanup unlinks paths, so it may only run
        # inside the sanctioned runtime directory (the keyed default
        # directory resolve_launchd_identity derives into). A payload-named
        # sentinel outside it is never unlinked; its stale pair refuses the
        # arm instead so the chain falls through to report-only honestly.
        self._cleanup_dir = (
            pathlib.Path(os.path.expanduser(str(cleanup_dir)))
            if cleanup_dir is not None
            else DEFAULT_RESUME_SENTINEL.parent
        )

    def _spent_pair_cleanup_scoped(self) -> bool:
        """Whether this scheduler's sentinel may be cleaned up (r5 F13)."""

        try:
            sentinel = pathlib.Path(os.path.realpath(self._sentinel_path))
            sanctioned = pathlib.Path(os.path.realpath(self._cleanup_dir))
            return sentinel.parent == sanctioned
        except OSError:
            return False

    @property
    def fired_path(self) -> pathlib.Path:
        """The one-shot's fired marker: next to the sentinel (r3 F16)."""

        return fired_marker_path(self._sentinel_path)

    def fire_command(self, manual_command: str, carrier_segment: str | None = None) -> str:
        """The fire-time ``sh -c`` payload: fired-marker and sentinel guards,
        first-fire sentinel creation, then the manual resume command.

        The fired-marker guard (r3 F16) makes the daily calendar job inert
        once watcher-fire consumed the one-shot on a terminal decision: the
        sentinel is removed and the marker written, so a later daily fire
        exits before touching anything instead of re-running the resume.

        ``carrier_segment`` (plan 2026-11-06-budget-resume-carrier-gc
        Task 3): when present, the arm-unique discriminator rides a
        fixed-marker no-op trailing segment appended after the manual
        command, so every destructive actor can verify live ownership
        against the receipt value already persisted. The guard segments
        stay first, so the guard-first payload shape is unchanged.
        """

        fired = shlex.quote(str(self.fired_path))
        quoted = shlex.quote(str(self._sentinel_path))
        command = f"test -e {fired} && exit 0; test -e {quoted} && exit 0; touch {quoted}; {manual_command}"
        if carrier_segment:
            command += f"; : {carrier_segment}"
        return command

    def schedule(self, request: Mapping[str, Any]) -> dict[str, Any]:
        fired = self.fired_path
        if self._sentinel_path.exists():
            if not fired.exists():
                return {
                    "scheduled": False,
                    "mechanism": "launchd",
                    "reason": "sentinel self-disable file present",
                    "sentinel": str(self._sentinel_path),
                }
            if not self._spent_pair_cleanup_scoped():
                # r5 F13: a foreign sentinel with a spent marker is not this
                # watcher's window handshake; unlinking it (or anything
                # outside the sanctioned runtime directory) is refused, and
                # the chain falls through to report-only.
                return {
                    "scheduled": False,
                    "mechanism": "launchd",
                    "reason": "spent one-shot cleanup outside the sanctioned runtime directory is refused",
                    "sentinel": str(self._sentinel_path),
                }
            # A spent one-shot (r3 F16): the previous window's fire reached a
            # terminal decision through watcher-fire, which removed the
            # sentinel and wrote the fired marker. Clear both so this window
            # re-arms; without this the first launchd resume would make every
            # later pause end report-only forever.
            for path in (self._sentinel_path, fired):
                try:
                    path.unlink()
                except OSError:
                    pass
        elif fired.exists():
            if not self._spent_pair_cleanup_scoped():
                return {
                    "scheduled": False,
                    "mechanism": "launchd",
                    "reason": "stale fired marker outside the sanctioned runtime directory is refused",
                    "sentinel": str(self._sentinel_path),
                }
            # A spent one-shot whose sentinel watcher-fire already removed
            # (r3 F16): the stale marker alone would trip the new job's
            # fired-guard and short-circuit its own first fire.
            try:
                fired.unlink()
            except OSError:
                pass
        job = launchd_plist_path(self._job_dir, self._label)
        fire_at = datetime.fromtimestamp(int(request["fire_at_epoch"])).astimezone()
        plist = {
            "Label": self._label,
            "ProgramArguments": [
                "/bin/sh",
                "-c",
                self.fire_command(
                    str(request.get("manual_command", "")),
                    carrier_segment=str(request["carrier_watcher_segment"]) if request.get("carrier_watcher_segment") else None,
                ),
            ],
            "StartCalendarInterval": {"Minute": fire_at.minute, "Hour": fire_at.hour},
            "StandardOutPath": str(self._job_dir / f"{self._label}.out.log"),
            "StandardErrorPath": str(self._job_dir / f"{self._label}.err.log"),
        }
        # Serialize the identity check, the plist write, and the bootout
        # through the shared guard lock (r3 F14): two boundaries of the same
        # run arming in one window must not interleave a write and a bootout.
        # The arm serializes fail-closed (plan
        # 2026-11-06-budget-resume-carrier-gc Task 3): a lock that does not
        # acquire returns not-scheduled with the named reason so the chain
        # falls through to report-only, instead of writing the plist and
        # bootstrapping unlocked - a discharge holding the lock across its
        # launchctl legs then cannot overlap a peer's unlocked re-arm at
        # the shared identity.
        with budget_guard_lock(self._sentinel_path) as guard_acquired:
            if not guard_acquired and self._fail_closed_on_lock_unavailable:
                return {
                    "scheduled": False,
                    "mechanism": "launchd",
                    "reason": "launchd-guard-lock-unavailable",
                    "sentinel": str(self._sentinel_path),
                }
            try:
                existing = plistlib.loads(job.read_bytes()) if job.exists() else None
            except (OSError, ValueError):
                existing = None
            if isinstance(existing, Mapping) and existing.get("Label") not in (None, self._label):
                # A foreign job sits at this watcher's job path (r3 F14):
                # overwriting it and booting it out would silently destroy
                # another run's armed resume. Refuse with label-conflict so
                # the fallback chain proceeds to report-only.
                return {
                    "scheduled": False,
                    "mechanism": "launchd",
                    "reason": "label-conflict: job path holds another watcher's job definition",
                    "job": str(job),
                    "conflict_label": str(existing.get("Label")),
                }
            try:
                self._job_dir.mkdir(parents=True, exist_ok=True)
                with job.open("wb") as handle:
                    plistlib.dump(plist, handle)
            except OSError as exc:
                return {"scheduled": False, "mechanism": "launchd", "reason": f"launchd-arm-failed: {exc}"}
            loaded, detail = self._bootstrap(job)
        if not loaded:
            # Not-scheduled is the honest arm outcome (r2 F4): a plist
            # launchd refused is a dead job, and reporting scheduled=True
            # would end the pause chain with a resume that never fires.
            # Remove the inert plist so no dead definition lingers, and
            # let the chain fall through to report-only.
            try:
                job.unlink()
            except OSError:
                pass
            return {
                "scheduled": False,
                "mechanism": "launchd",
                "reason": f"launchd-bootstrap-failed: {detail}",
                "job": str(job),
            }
        # No arm-time sentinel here (r1 F1): the job's first fire creates it,
        # so the fire-time guard cannot short-circuit the job it guards.
        return {"scheduled": True, "mechanism": "launchd", "job": str(job), "sentinel": str(self._sentinel_path)}


def launchctl_bootout(job: os.PathLike | str) -> dict[str, Any]:
    """Best-effort bootout of one plist from this user's launchd domain.

    The one bootout primitive: the arm's pre-bootstrap unload (r2 F4) and
    the supersede carrier teardown (r6 F3) share it. Not-loaded and removed
    paths are fine; the exit code is reported, never raised. Tests fake this
    helper to stay hermetic, like :func:`launchctl_bootstrap`.
    """

    domain = f"gui/{os.getuid()}"
    completed = subprocess.run(
        ["launchctl", "bootout", domain, str(job)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return {"job": str(job), "exited": completed.returncode}


def launchctl_bootstrap(job: pathlib.Path) -> tuple[bool, str]:
    """Load one plist into this user's launchd domain; ``(loaded, detail)``.

    A prior window's job with the same label may still be loaded, so the
    bootout is best-effort first (not-loaded is fine), and the bootstrap
    result decides. Runs in the ``gui/<uid>`` domain of the arming user.
    """

    launchctl_bootout(job)
    domain = f"gui/{os.getuid()}"
    completed = subprocess.run(
        ["launchctl", "bootstrap", domain, str(job)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        return False, detail or f"launchctl bootstrap exited {completed.returncode}"
    return True, ""


def launchctl_verify_loaded(label: str) -> tuple[bool, str]:
    """Verify the exact user-domain service label is loaded."""

    domain = f"gui/{os.getuid()}/{label}"
    completed = subprocess.run(
        ["launchctl", "print", domain],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        return False, detail or f"launchctl print exited {completed.returncode}"
    return True, completed.stdout.decode("utf-8", "replace").strip()


def launchd_calendar_occurrences(
    fields: Mapping[str, Any], *, timezone: Any = None, year: int | None = None
) -> list[int]:
    """Return this year's epochs represented by a launchd calendar row.

    ``fold=0`` and ``fold=1`` expose both physical minutes during a repeated
    daylight-saving interval. A spring-forward gap normalizes to another
    local time and therefore contributes no matching epoch. launchd does not
    support a Year key, so the caller supplies the occurrence year separately.
    """

    timezone = timezone or _system_local_timezone()
    try:
        values = {
            "Year": int(year if year is not None else fields.get("Year")),
            "Month": int(fields["Month"]),
            "Day": int(fields["Day"]),
            "Hour": int(fields["Hour"]),
            "Minute": int(fields["Minute"]),
        }
        local = datetime(**{
            "year": values["Year"],
            "month": values["Month"],
            "day": values["Day"],
            "hour": values["Hour"],
            "minute": values["Minute"],
            "tzinfo": timezone,
        })
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid launchd calendar fields: {exc}") from exc
    epochs: set[int] = set()
    for fold in (0, 1):
        candidate = local.replace(fold=fold)
        epoch = int(candidate.timestamp())
        observed = datetime.fromtimestamp(epoch, timezone)
        if (
            observed.year == values["Year"]
            and observed.month == values["Month"]
            and observed.day == values["Day"]
            and observed.hour == values["Hour"]
            and observed.minute == values["Minute"]
            and observed.second == 0
        ):
            epochs.add(epoch)
    return sorted(epochs)


def next_launchd_occurrence(
    fields: Mapping[str, Any], *, after_epoch: int, timezone: Any = None
) -> int | None:
    """Find the next occurrence of launchd's yearless calendar fields."""

    tz = timezone or _system_local_timezone()
    start_year = datetime.fromtimestamp(after_epoch, tz).year
    for year in range(start_year, start_year + 9):
        try:
            occurrences = launchd_calendar_occurrences(fields, timezone=tz, year=year)
        except ValueError:
            continue
        future = [epoch for epoch in occurrences if epoch > after_epoch]
        if future:
            return min(future)
    return None


def compute_unique_launchd_minute(
    reset_at_epoch: int, *, timezone: Any = None, margin_seconds: int = 600,
    not_before_epoch: int | None = None,
) -> tuple[int, dict[str, int]]:
    """Choose the first unique local launchd minute at/after reset + margin."""

    if isinstance(reset_at_epoch, bool) or not isinstance(reset_at_epoch, (int, float)) or reset_at_epoch <= 0:
        raise ValueError("primary reset epoch must be a positive number")
    tz = timezone or _system_local_timezone()
    threshold = float(reset_at_epoch) + int(margin_seconds)
    if not_before_epoch is not None:
        if isinstance(not_before_epoch, bool) or not isinstance(not_before_epoch, int) or not_before_epoch <= 0:
            raise ValueError("minimum fire epoch must be a positive integer")
        threshold = max(threshold, float(not_before_epoch))
    candidate_epoch = int(math.ceil(threshold / 60) * 60)
    for _ in range(24 * 60 + 1):
        local = datetime.fromtimestamp(candidate_epoch, tz)
        fields = {
            "Month": local.month,
            "Day": local.day,
            "Hour": local.hour,
            "Minute": local.minute,
        }
        occurrences = launchd_calendar_occurrences(fields, timezone=tz, year=local.year)
        if not occurrences:
            raise ValueError("launchd calendar occurrence could not be proven")
        if len(occurrences) == 1 and occurrences[0] == candidate_epoch:
            return candidate_epoch, fields
        candidate_epoch += 60
    raise ValueError("launchd calendar occurrence could not be proven within one day")


def recompute_bounded_retry_epoch(
    saved_epoch: int, now_epoch: int, deadline_epoch: int, *, timezone: Any = None
) -> int | None:
    """Return the first unique retry minute at/after max(saved, now + 60), within deadline."""

    try:
        retry_epoch, _calendar = compute_unique_launchd_minute(
            max(saved_epoch - 60, now_epoch),
            timezone=timezone,
            margin_seconds=60,
            not_before_epoch=saved_epoch,
        )
    except ValueError:
        return None
    return retry_epoch if retry_epoch <= deadline_epoch else None


def _system_local_timezone() -> ZoneInfo:
    """Load a transition-aware zone for the local timezone used by launchd."""
    # launchd interprets StartCalendarInterval in the host timezone; a caller's
    # TZ override only changes that process and must not redefine the carrier.
    try:
        with pathlib.Path("/etc/localtime").open("rb") as handle:
            return ZoneInfo.from_file(handle)
    except (OSError, ValueError) as exc:
        raise ValueError("system local timezone has no transition-aware zone data") from exc


def capture_codex_runtime_binding(
    env: Mapping[str, str], *, which: Callable[[str], str | None] | None = None
) -> dict[str, Any]:
    """Resolve the runnable Codex command and its environment-dependent paths."""

    which = which or shutil.which
    codex_home_raw = str(env.get("CODEX_HOME") or "").strip()
    codex_home = pathlib.Path(codex_home_raw).expanduser() if codex_home_raw else None
    if codex_home is None or not codex_home.is_absolute() or not codex_home.is_dir() or not os.access(codex_home, os.R_OK | os.W_OK | os.X_OK):
        raise ValueError("CODEX_HOME must be an absolute readable and writable directory")
    codex_raw = which("codex")
    if not codex_raw:
        raise ValueError("Codex executable could not be resolved")
    codex = pathlib.Path(codex_raw).expanduser()
    if not codex.is_absolute() or not codex.is_file() or not os.access(codex, os.X_OK):
        raise ValueError("Codex executable must be an absolute runnable file")
    codex = codex.resolve()
    try:
        with codex.open("rb") as handle:
            first_line = handle.readline(4096).decode("utf-8", "replace").strip()
    except OSError as exc:
        raise ValueError(f"Codex executable could not be inspected: {exc}") from exc
    interpreter: pathlib.Path | None = None
    entry_point: pathlib.Path | None = None
    interpreter_args: list[str] = []
    interpreter_command: str | None = None
    if first_line.startswith("#!"):
        try:
            shebang = shlex.split(first_line[2:].strip())
        except ValueError as exc:
            raise ValueError(f"Codex executable has an invalid shebang: {exc}") from exc
        if not shebang:
            raise ValueError("Codex executable has an empty shebang")
        if pathlib.Path(shebang[0]).name == "env":
            command = [part for part in shebang[1:] if part != "-S"]
            if not command or command[0].startswith("-"):
                raise ValueError("Codex env shebang has no supported interpreter")
            interpreter_command = command[0]
            interpreter_raw = which(command[0])
            if not interpreter_raw:
                raise ValueError("Codex shebang interpreter could not be resolved")
            interpreter = pathlib.Path(interpreter_raw).expanduser()
            if not interpreter.is_absolute() or not interpreter.is_file() or not os.access(interpreter, os.X_OK):
                raise ValueError("Codex shebang interpreter must be an absolute runnable file")
            entry_point = codex
            interpreter_args = command[1:]
        else:
            interpreter = pathlib.Path(shebang[0]).expanduser()
            if not interpreter.is_absolute() or not interpreter.is_file() or not os.access(interpreter, os.X_OK):
                raise ValueError("Codex shebang interpreter must be an absolute runnable file")
            entry_point = codex
            interpreter_args = shebang[1:]
    return {
        "codex_home": str(codex_home.resolve()),
        "codex_executable": str(codex),
        "codex_interpreter": str(interpreter.resolve()) if interpreter else None,
        "codex_entry_point": str(entry_point.resolve()) if entry_point else None,
        "codex_interpreter_args": interpreter_args,
        "codex_interpreter_command": interpreter_command,
    }


suppression_reasons = frozenset({"stop", "survey-only-stop", "safety-hold", "empty-queue", "target-changed"})


def codex_quota_wake_token(payload_digest: str, scheduled_epoch: int) -> str:
    """Return the stable identity carried by a queued quota continuation."""

    if not re.fullmatch(r"[0-9a-f]{64}", str(payload_digest)):
        raise ValueError("payload digest must be a SHA-256 hex digest")
    if isinstance(scheduled_epoch, bool) or not isinstance(scheduled_epoch, int) or scheduled_epoch <= 0:
        raise ValueError("scheduled epoch must be a positive integer")
    return f"{payload_digest}:{scheduled_epoch}"


def _atomic_json_write(path: pathlib.Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != value:
            raise OSError("receipt read-back mismatch")
    finally:
        temporary.unlink(missing_ok=True)


def _verified_wake_consume(sentinel: pathlib.Path, fired_marker: pathlib.Path) -> tuple[bool, str]:
    """Write and read back the carrier marker before unlinking its sentinel."""

    marker_value = f"consumed-at={int(time.time())}\n"
    temporary = fired_marker.with_name(fired_marker.name + f".{os.getpid()}.tmp")
    try:
        fired_marker.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(marker_value, encoding="utf-8")
        os.replace(temporary, fired_marker)
        if fired_marker.read_text(encoding="utf-8") != marker_value:
            return False, "fired-marker-readback-mismatch"
    except OSError:
        temporary.unlink(missing_ok=True)
        return False, "fired-marker-write-failed"
    try:
        sentinel.unlink(missing_ok=True)
        if sentinel.exists():
            return False, "sentinel-unlink-failed"
    except OSError:
        return False, "sentinel-unlink-failed"
    return True, "consumed"


def reconcile_codex_quota_wake_delivery(receipt_path: os.PathLike | str, continuation: str, current_thread_id: str | None = None) -> dict[str, Any]:
    """Mark a queued wake delivered only when its exact token reached the thread."""

    path = pathlib.Path(receipt_path).expanduser()
    if not path.is_absolute() or not path.is_file():
        return {"decision": "stand_down", "reason": "receipt-unreadable"}
    try:
        initial = json.loads(path.read_text(encoding="utf-8"))
        payload = json.loads((path.parent / "payload.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"decision": "stand_down", "reason": "receipt-unreadable", "detail": str(exc)}
    if not isinstance(initial, Mapping) or not isinstance(payload, Mapping):
        return {"decision": "stand_down", "reason": "receipt-unreadable"}
    thread_id = str(initial.get("thread_id") or "")
    if thread_id != str(payload.get("thread_id") or ""):
        return {"decision": "stand_down", "reason": "receipt-identity-mismatch", "receipt": initial}
    active_thread = str(current_thread_id if current_thread_id is not None else os.environ.get("CODEX_THREAD_ID") or "").strip()
    if not active_thread or active_thread != thread_id:
        return {"decision": "stand_down", "reason": "thread-binding-changed", "receipt": initial}
    wakes_root = path.parent.parent
    thread_key = hashlib.sha256((str(pathlib.Path(str(payload.get("repo_root") or "")).resolve()) + "\0" + thread_id).encode("utf-8")).hexdigest()[:16]
    thread_lock_path = wakes_root / f"thread-{thread_key}.lock"
    try:
        thread_lock = thread_lock_path.open("a+")
    except OSError as exc:
        return {"decision": "stand_down", "reason": "thread-lock-unavailable", "detail": str(exc)}
    try:
        try:
            fcntl.flock(thread_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"decision": "stand_down", "reason": "already-claimed"}
        try:
            lock_path = path.with_name("fire.lock")
            with lock_path.open("a+") as lock:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return {"decision": "stand_down", "reason": "already-claimed"}
                try:
                    receipt = json.loads(path.read_text(encoding="utf-8"))
                    payload = json.loads((path.parent / "payload.json").read_text(encoding="utf-8"))
                    if not isinstance(receipt, Mapping) or not isinstance(payload, Mapping):
                        return {"decision": "stand_down", "reason": "receipt-unreadable"}
                    arm_receipt = json.loads((path.parent / "arm-receipt.json").read_text(encoding="utf-8"))
                    if (
                        payload.get("payload_digest") != CodexQuotaWakeScheduler._payload_digest(payload)
                        or not isinstance(arm_receipt, Mapping)
                        or arm_receipt.get("payload_digest") != payload.get("payload_digest")
                        or arm_receipt.get("payload") != payload
                    ):
                        return {"decision": "stand_down", "reason": "receipt-identity-mismatch", "receipt": receipt}
                    expected_token = codex_quota_wake_token(str(payload.get("payload_digest") or ""), int(payload.get("scheduled_epoch") or 0))
                    if (
                        receipt.get("payload_digest") != payload.get("payload_digest")
                        or receipt.get("thread_id") != thread_id
                        or receipt.get("target") != payload.get("target")
                        or receipt.get("wake_token") != expected_token
                    ):
                        return {"decision": "stand_down", "reason": "receipt-identity-mismatch", "receipt": receipt}
                    if receipt.get("status") == "carrier-consume-failed":
                        previous = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome")
                        if previous not in {"queued", "queued-but-unconfirmed"}:
                            return {"decision": "stand_down", "reason": "carrier-repair-outcome-ineligible", "receipt": receipt}
                        sentinel = pathlib.Path(str(payload.get("sentinel_path") or ""))
                        if not sentinel.exists():
                            sentinel.parent.mkdir(parents=True, exist_ok=True)
                            sentinel.write_text("fired\n", encoding="utf-8")
                        consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
                        if not consumed:
                            return {"decision": "stand_down", "reason": "carrier-repair-failed", "detail": reason, "receipt": receipt}
                        receipt.update(status=previous, carrier_repair=reason, updated_at_epoch=int(time.time()))
                    if receipt.get("status") not in {"queued", "queued-but-unconfirmed"}:
                        return {"decision": "stand_down", "reason": "receipt-not-awaiting-delivery", "receipt": receipt}
                    token = receipt.get("wake_token")
                    if not isinstance(token, str) or not token:
                        return {"decision": "stand_down", "reason": "receipt-token-missing", "receipt": receipt}
                    if token in str(continuation or ""):
                        receipt.update(status="delivered", delivery_verified=True, updated_at_epoch=int(time.time()))
                        decision = "delivered"
                    else:
                        # Keep the queued disposition so a later exact-token
                        # continuation can reconcile; do not expose the target.
                        receipt.update(delivery_verified=False, delivery_error="stable wake token absent from resumed continuation")
                        decision = "operator-required"
                    _atomic_json_write(path, receipt)
                    return {"decision": decision, "receipt": receipt}
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    return {"decision": "stand_down", "reason": "receipt-unreadable", "detail": str(exc)}
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        finally:
            fcntl.flock(thread_lock.fileno(), fcntl.LOCK_UN)
    finally:
        thread_lock.close()


class CodexQuotaWakeScheduler:
    """Arm one date-specific, thread-bound Codex quota-reset continuation."""

    def __init__(
        self,
        *,
        state_dir: os.PathLike | str,
        repo_root: os.PathLike | str,
        env: Mapping[str, str] | None = None,
        clock: Callable[[], float] = time.time,
        timezone: Any = None,
        which: Callable[[str], str | None] | None = None,
        bootstrap: Callable[[pathlib.Path], tuple[bool, str]] | None = None,
        verify_loaded: Callable[[str], tuple[bool, str]] | None = None,
        bootout: Callable[[pathlib.Path], Mapping[str, Any]] | None = None,
        queue_command: Callable[[Sequence[str], Mapping[str, str], pathlib.Path], Any] | None = None,
        fire_guard: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        pre_queue_guard: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        schedule_guard: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        self._state_dir = pathlib.Path(state_dir).expanduser()
        self._repo_root = pathlib.Path(repo_root).expanduser()
        self._env = dict(os.environ if env is None else env)
        self._clock = clock
        self._timezone = timezone
        self._which = which or shutil.which
        self._bootstrap = bootstrap or launchctl_bootstrap
        self._verify_loaded = verify_loaded or launchctl_verify_loaded
        self._bootout = bootout or launchctl_bootout
        self._queue_command = queue_command or self._run_queue_command
        self._fire_guard = fire_guard or (lambda _payload: {"ready": False, "reason": "fire-time guards unavailable"})
        self._pre_queue_guard = pre_queue_guard or self._fire_guard
        self._schedule_guard = schedule_guard or (lambda _payload: {"ready": False, "reason": "schedule-admission guards unavailable"})

    @staticmethod
    def _run_queue_command(argv: Sequence[str], env: Mapping[str, str], cwd: pathlib.Path) -> Any:
        return subprocess.run(argv, cwd=cwd, env=dict(env), capture_output=True, text=True, timeout=60, check=False)

    @staticmethod
    def _definitive_queue_refusal(returncode: int, stderr: str) -> bool:
        """Recognize only the CLI parser's pre-dispatch usage refusal."""

        normalized = stderr.strip().lower()
        return (
            returncode == 2
            and normalized.startswith("error:")
            and "usage: codex queue" in normalized
        )

    @staticmethod
    def _payload_digest(payload: Mapping[str, Any]) -> str:
        identity = {key: value for key, value in payload.items() if key not in {"payload_digest", "label"}}
        canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def _acquire_thread_wake_lock(self, identity: Mapping[str, Any]):
        repo_root = str(pathlib.Path(str(identity["repo_root"])).resolve())
        thread_id = str(identity["thread_id"])
        key = hashlib.sha256((repo_root + "\0" + thread_id).encode("utf-8")).hexdigest()[:16]
        path = self._state_dir / "codex-quota-wakes" / f"thread-{key}.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return None
        return lock

    def _acquire_target_wake_lock(self, identity: Mapping[str, Any]):
        repo_root = str(pathlib.Path(str(identity["repo_root"])).resolve())
        target = str(identity["target"])
        kind = str(identity["kind"])
        key = hashlib.sha256((repo_root + "\0" + target + "\0" + kind).encode("utf-8")).hexdigest()[:16]
        path = self._state_dir / "codex-quota-wakes" / f"target-{key}.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return None
        return lock

    @staticmethod
    def _release_thread_wake_lock(lock) -> None:
        if lock is None:
            return
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        finally:
            lock.close()

    @staticmethod
    def _release_target_wake_lock(lock) -> None:
        if lock is None:
            return
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        finally:
            lock.close()

    def _consume_fire_carrier(
        self, receipt: dict[str, Any], receipt_path: pathlib.Path, sentinel: pathlib.Path
    ) -> tuple[bool, str]:
        consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
        if not consumed:
            previous = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome") or "not-attempted"
            receipt.update(
                status="operator-required" if receipt.get("carrier_error") else "carrier-consume-failed",
                previous_queue_outcome=previous,
                queue_outcome=previous,
                carrier_error=reason,
                updated_at_epoch=int(self._clock()),
            )
            _atomic_json_write(receipt_path, receipt)
        return consumed, reason

    def _retire_losing_wake_carrier(
        self,
        payload_path: pathlib.Path,
        payload: Mapping[str, Any],
        receipt: dict[str, Any],
        receipt_path: pathlib.Path,
        *,
        require_active_thread: bool = True,
    ) -> tuple[bool, str]:
        """Retire a duplicate same-target wake only after identity and unload checks."""

        try:
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            label = str(payload.get("label") or "")
            expected_label = f"ai-playbook.codex-quota-wake.{str(payload.get('payload_digest') or '')[:12]}"
            if not label or label != expected_label:
                return False, "target-lock-loser-label-identity-mismatch"
            plist_path = payload_path.parent / f"{label}.plist"
            booted = self._bootout(plist_path)
            bootout_rc = booted.get("exited")
            if not (bootout_rc is True or (isinstance(bootout_rc, int) and not isinstance(bootout_rc, bool) and bootout_rc == 0)):
                return False, "target-lock-loser-bootout-refused"
            loaded, detail = self._verify_loaded(label)
            if loaded:
                return False, f"target-lock-loser-still-loaded: {detail}"
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            sentinel = pathlib.Path(str(payload["sentinel_path"]))
            consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
            if not consumed:
                return False, reason
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            receipt.update(
                status="suppressed",
                queue_outcome="not-attempted",
                carrier_repair="target-lock-loser-retired-and-unloaded",
                updated_at_epoch=int(self._clock()),
            )
            _atomic_json_write(receipt_path, receipt)
            return True, "target-lock-loser-retired"
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            return False, f"target-lock-loser-retirement-failed: {exc}"

    def _record_target_lock_loss(
        self,
        payload_path: pathlib.Path,
        payload: Mapping[str, Any],
        receipt_path: pathlib.Path,
        token: str,
        original_epoch: int,
    ) -> dict[str, Any]:
        """Durably park/retire this duplicate without queueing outside the target lock."""

        lock_path = receipt_path.parent / "fire.lock"
        try:
            with lock_path.open("a+") as lock:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return {"decision": "stand_down", "reason": "already-claimed"}
                try:
                    if receipt_path.exists():
                        try:
                            existing = json.loads(receipt_path.read_text(encoding="utf-8"))
                        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                            return {
                                "decision": "stand_down",
                                "reason": "existing-receipt-unreadable",
                                "detail": str(exc),
                            }
                        if not isinstance(existing, Mapping):
                            return {"decision": "stand_down", "reason": "existing-receipt-unreadable"}
                        expected_identity = {
                            "payload_digest": str(payload.get("payload_digest") or ""),
                            "thread_id": str(payload.get("thread_id") or ""),
                            "target": str(payload.get("target") or ""),
                            "original_scheduled_epoch": original_epoch,
                            "wake_token": token,
                        }
                        if any(existing.get(key) != value for key, value in expected_identity.items()):
                            return {"decision": "stand_down", "reason": "existing-receipt-identity-mismatch"}
                        attempt_count = existing.get("attempt_count", 0)
                        safe_to_replace = (
                            existing.get("status") in {"pending", "scheduled"}
                            and isinstance(attempt_count, int)
                            and not isinstance(attempt_count, bool)
                            and attempt_count == 0
                            and existing.get("queue_outcome") in {None, "not-attempted"}
                            and existing.get("previous_queue_outcome") in {None, "not-attempted"}
                        )
                        # The receipt is the durable queue-outcome witness. A
                        # target-lock loser must not replace an attempted or
                        # queued outcome with a synthetic not-attempted state.
                        if not safe_to_replace:
                            return {
                                "decision": "stand_down",
                                "reason": "already-claimed",
                                "receipt": dict(existing),
                                "carrier_consumed": False,
                                "carrier_reason": "existing fire receipt preserved",
                            }
                    payload = self._revalidate_fire_payload(payload_path, payload)
                    replacement = self._verified_loaded_same_target_replacement(payload)
                    receipt = {
                        "payload_digest": payload["payload_digest"],
                        "thread_id": payload["thread_id"],
                        "original_scheduled_epoch": original_epoch,
                        "wake_token": token,
                        "attempt_count": 0,
                        "retry_fire_epoch": None,
                        "queue_outcome": "not-attempted",
                        "previous_queue_outcome": "not-attempted",
                        "status": "carrier-consume-failed",
                        "target": payload["target"],
                        "carrier_error": (
                            "target-lock-loser-retirement-pending"
                            if replacement
                            else "target-lock-loser-replacement-not-verified"
                        ),
                        "retire_label_on_repair": bool(replacement),
                        "rearm_original_on_repair": not bool(replacement),
                        "updated_at_epoch": int(self._clock()),
                    }
                    _atomic_json_write(receipt_path, receipt)
                    if not replacement:
                        return {
                            "decision": "stand_down",
                            "reason": "already-claimed",
                            "receipt": receipt,
                            "carrier_consumed": False,
                            "carrier_reason": "same-target replacement was not verified; original carrier retained",
                        }
                    retired, reason = self._retire_losing_wake_carrier(payload_path, payload, receipt, receipt_path)
                    if not retired:
                        receipt.update(
                            status="carrier-consume-failed",
                            carrier_error=reason,
                            updated_at_epoch=int(self._clock()),
                        )
                        _atomic_json_write(receipt_path, receipt)
                    return {
                        "decision": "stand_down",
                        "reason": "already-claimed",
                        "receipt": receipt,
                        "carrier_consumed": retired,
                        "carrier_reason": reason,
                    }
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            return {"decision": "stand_down", "reason": "already-claimed", "detail": str(exc)}

    def _verified_loaded_same_target_replacement(self, payload: Mapping[str, Any]) -> bool:
        """Return true only for another valid same-target arm whose label is loaded."""
        root = self._state_dir / "codex-quota-wakes"
        if not root.is_dir():
            return False
        for arm_path in root.glob("*/arm-receipt.json"):
            if arm_path.parent == pathlib.Path(str(payload.get("payload_path") or "")).parent:
                continue
            try:
                arm = json.loads(arm_path.read_text(encoding="utf-8"))
                candidate = arm.get("payload") if isinstance(arm, Mapping) else None
                if not isinstance(candidate, Mapping):
                    continue
                if (
                    candidate.get("repo_root") != payload.get("repo_root")
                    or candidate.get("target") != payload.get("target")
                    or candidate.get("kind") != payload.get("kind")
                    or candidate.get("payload_digest") == payload.get("payload_digest")
                    or arm.get("payload_digest") != candidate.get("payload_digest")
                    or candidate.get("payload_digest") != self._payload_digest(candidate)
                ):
                    continue
                label = str(candidate.get("label") or "")
                plist_path = arm_path.parent / f"{label}.plist"
                verified_arm_path = arm_path.parent / "verified-arm.json"
                if not label or not plist_path.is_file():
                    continue
                verified_arm = json.loads(verified_arm_path.read_text(encoding="utf-8"))
                fire_epoch = verified_arm.get("fire_epoch") if isinstance(verified_arm, Mapping) else None
                if (
                    not isinstance(verified_arm, Mapping)
                    or verified_arm.get("payload_digest") != candidate.get("payload_digest")
                    or verified_arm.get("label") != label
                    or isinstance(verified_arm.get("verified_at_epoch"), bool)
                    or not isinstance(verified_arm.get("verified_at_epoch"), int)
                    or isinstance(fire_epoch, bool)
                    or not isinstance(fire_epoch, int)
                ):
                    continue
                fire_receipt_path = arm_path.parent / "fire-receipt.json"
                if fire_receipt_path.exists():
                    fire_receipt = json.loads(fire_receipt_path.read_text(encoding="utf-8"))
                    if (
                        not isinstance(fire_receipt, Mapping)
                        or fire_receipt.get("payload_digest") != candidate.get("payload_digest")
                        or fire_receipt.get("thread_id") != candidate.get("thread_id")
                        or fire_receipt.get("original_scheduled_epoch") != candidate.get("scheduled_epoch")
                        or fire_receipt.get("status") != "retry-available"
                        or fire_receipt.get("recovery") != "retry-carrier-rearmed"
                        or fire_receipt.get("retry_fire_epoch") != fire_epoch
                        or fire_receipt.get("queue_outcome") not in {"not-attempted", "definitive-refusal"}
                    ):
                        continue
                elif fire_epoch != candidate.get("scheduled_epoch"):
                    continue
                loaded, _detail = self._verify_loaded(label)
                if loaded:
                    return True
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
        return False

    def _verified_same_target_delivery_replacement(self, payload: Mapping[str, Any]) -> bool:
        """Return true for another same-target queued wake or verified same-reset delivery."""
        root = self._state_dir / "codex-quota-wakes"
        if not root.is_dir():
            return False
        own_dir = pathlib.Path(str(payload.get("payload_path") or "")).parent
        for arm_path in root.glob("*/arm-receipt.json"):
            if arm_path.parent == own_dir:
                continue
            try:
                arm = json.loads(arm_path.read_text(encoding="utf-8"))
                candidate = arm.get("payload") if isinstance(arm, Mapping) else None
                if not isinstance(candidate, Mapping):
                    continue
                if (
                    candidate.get("repo_root") != payload.get("repo_root")
                    or candidate.get("target") != payload.get("target")
                    or candidate.get("kind") != payload.get("kind")
                    or candidate.get("payload_digest") == payload.get("payload_digest")
                    or arm.get("payload_digest") != candidate.get("payload_digest")
                    or candidate.get("payload_digest") != self._payload_digest(candidate)
                ):
                    continue
                receipt_path = arm_path.parent / "fire-receipt.json"
                if not receipt_path.is_file():
                    continue
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                expected_token = codex_quota_wake_token(
                    str(candidate.get("payload_digest") or ""),
                    int(candidate.get("scheduled_epoch") or 0),
                )
                status = receipt.get("status") if isinstance(receipt, Mapping) else None
                queued = status in {"queued", "queued-but-unconfirmed"} and receipt.get("queue_outcome") == status
                delivered = (
                    status == "delivered"
                    and receipt.get("delivery_verified") is True
                    and receipt.get("queue_outcome") in {"queued", "queued-but-unconfirmed"}
                    and candidate.get("reset_at_epoch") == payload.get("reset_at_epoch")
                )
                if (
                    not (queued or delivered)
                    or receipt.get("payload_digest") != candidate.get("payload_digest")
                    or receipt.get("thread_id") != candidate.get("thread_id")
                    or receipt.get("target") != candidate.get("target")
                    or receipt.get("original_scheduled_epoch") != candidate.get("scheduled_epoch")
                    or receipt.get("wake_token") != expected_token
                ):
                    continue
                return True
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
        return False

    def _validate_fire_payload(self, payload_path: pathlib.Path) -> dict[str, Any]:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("quota wake payload must be a JSON object")
        digest = payload.get("payload_digest")
        if not isinstance(digest, str) or digest != self._payload_digest(payload):
            raise ValueError("quota wake payload digest mismatch")
        required = ("thread_id", "repo_root", "target", "phase", "reset_at_epoch", "scheduled_epoch", "codex_home", "codex_executable")
        if any(not payload.get(key) for key in required):
            raise ValueError("quota wake payload is missing a required identity")
        if _has_control_character(str(payload.get("target") or "")) or _has_control_character(str(payload.get("phase") or "")):
            raise ValueError("quota wake target and phase may not contain control characters")
        if pathlib.Path(payload["repo_root"]).resolve() != self._repo_root.resolve():
            raise ValueError("quota wake repository binding changed")
        if pathlib.Path(payload["codex_home"]).is_dir() is False or os.access(payload["codex_home"], os.R_OK | os.W_OK | os.X_OK) is False:
            raise ValueError("captured CODEX_HOME is no longer readable and writable")
        executable = pathlib.Path(payload["codex_executable"])
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError("captured Codex executable is no longer runnable")
        if payload.get("codex_interpreter"):
            interpreter = pathlib.Path(payload["codex_interpreter"])
            entry_point = pathlib.Path(payload.get("codex_entry_point") or "")
            if not interpreter.is_absolute() or not interpreter.is_file() or not os.access(interpreter, os.X_OK):
                raise ValueError("captured Codex interpreter is no longer runnable")
            if not entry_point.is_absolute() or not entry_point.is_file() or not os.access(entry_point, os.R_OK):
                raise ValueError("captured Codex entry point is no longer readable")
        try:
            first_line = executable.open("r", encoding="utf-8").readline().strip()
        except (OSError, UnicodeDecodeError):
            first_line = ""
        if first_line.startswith("#!"):
            command = shlex.split(first_line[2:].strip())
            if command and pathlib.Path(command[0]).name == "env":
                command = command[1:]
                if command and command[0] == "-S":
                    command = shlex.split(" ".join(command[1:]))
                elif command and command[0].startswith("-"):
                    command = []
                if not command or not payload.get("codex_interpreter") or payload.get("codex_interpreter_command") != command[0]:
                    raise ValueError("captured Codex interpreter no longer matches its env shebang")
                if pathlib.Path(str(payload.get("codex_entry_point") or "")).resolve() != executable.resolve():
                    raise ValueError("captured Codex entry point no longer matches its shebang script")
                if list(payload.get("codex_interpreter_args") or []) != command[1:]:
                    raise ValueError("captured Codex interpreter arguments no longer match its shebang")
            elif command:
                if not payload.get("codex_interpreter") or pathlib.Path(str(payload["codex_interpreter"])).resolve() != pathlib.Path(command[0]).resolve():
                    raise ValueError("captured Codex interpreter no longer matches its shebang")
                if list(payload.get("codex_interpreter_args") or []) != command[1:]:
                    raise ValueError("captured Codex interpreter arguments no longer match its shebang")
        elif payload.get("codex_interpreter") or pathlib.Path(str(payload.get("codex_entry_point") or "")).resolve() != executable.resolve():
            raise ValueError("captured Codex executable binding changed")
        return payload

    def _revalidate_fire_payload(
        self,
        payload_path: pathlib.Path,
        expected_payload: Mapping[str, Any],
        *,
        require_active_thread: bool = True,
    ) -> dict[str, Any]:
        """Re-read an armed identity, optionally requiring this session's thread."""

        payload = self._validate_fire_payload(payload_path)
        active_thread = str(self._env.get("CODEX_THREAD_ID") or "").strip()
        if require_active_thread and active_thread and active_thread != str(payload.get("thread_id") or ""):
            raise ValueError("thread-binding-changed")
        arm_receipt_path = payload_path.parent / "arm-receipt.json"
        arm_receipt = json.loads(arm_receipt_path.read_text(encoding="utf-8"))
        if (
            not isinstance(arm_receipt, Mapping)
            or arm_receipt.get("payload_digest") != payload.get("payload_digest")
            or arm_receipt.get("payload") != payload
            or payload != dict(expected_payload)
        ):
            raise ValueError("arm-receipt-mismatch")
        return payload

    def _queue_argv(self, payload: Mapping[str, Any], token: str) -> tuple[list[str], dict[str, str]]:
        receipt_path = pathlib.Path(str(payload.get("payload_path") or ""))
        # Payloads are written beside the durable fire receipt. The queue prompt
        # carries this explicit path so the resumed same-thread session can
        # close the delivery receipt before normal maintenance work.
        receipt_path = receipt_path.parent / "fire-receipt.json"
        message = CODEX_QUOTA_WAKE_FIXED_PROMPT + "\n" + json.dumps(
            {"wake_token": token, "receipt_locator": str(receipt_path)},
            sort_keys=True,
            separators=(",", ":"),
        )
        if payload.get("codex_interpreter"):
            argv = [str(payload["codex_interpreter"]), *payload.get("codex_interpreter_args", []), str(payload["codex_entry_point"])]
        else:
            argv = [str(payload["codex_executable"])]
        argv.extend(["queue", "--thread", str(payload["thread_id"]), "--message", message, "--resume"])
        return argv, {"CODEX_HOME": str(payload["codex_home"]), "CODEX_THREAD_ID": str(payload["thread_id"])}

    def _repair_pending_carrier_receipts(self) -> str | None:
        """Repair spent carrier pairs before a scheduler can arm another wake."""

        root = self._state_dir / "codex-quota-wakes"
        if not root.is_dir():
            return None
        for receipt_path in root.glob("*/fire-receipt.json"):
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                payload_path = receipt_path.parent / "payload.json"
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return f"unreadable fire receipt blocks new wake arm: {receipt_path}"
            if not isinstance(receipt, Mapping) or not isinstance(payload, Mapping):
                return f"unreadable fire receipt blocks new wake arm: {receipt_path}"
            status = receipt.get("status")
            if status not in {"carrier-consume-failed", "retry-available", "retry-arm-failed"}:
                continue
            sentinel = pathlib.Path(str(payload.get("sentinel_path") or ""))
            thread_lock = self._acquire_thread_wake_lock(payload)
            if thread_lock is None:
                return f"carrier repair already claimed: {receipt_path}"
            target_lock = None
            try:
                # Repairs that may arm or retire a competing carrier join the
                # repository/target reservation. Consume-only reconciliation
                # retains thread→wake.
                if self._carrier_repair_needs_target_reservation(receipt):
                    target_lock = self._acquire_target_wake_lock(payload)
                    if target_lock is None:
                        return f"carrier repair target already claimed: {receipt_path}"
                with (receipt_path.parent / "fire.lock").open("a+") as fire_lock:
                    try:
                        fcntl.flock(fire_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        return f"carrier repair already claimed: {receipt_path}"
                    try:
                        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                        if not isinstance(receipt, Mapping):
                            return f"unreadable fire receipt blocks new wake arm: {receipt_path}"
                        if receipt.get("status") not in {"carrier-consume-failed", "retry-available", "retry-arm-failed"}:
                            continue
                        payload = self._revalidate_fire_payload(
                            payload_path, payload, require_active_thread=False
                        )
                        if (
                            receipt.get("payload_digest") != payload.get("payload_digest")
                            or receipt.get("thread_id") != payload.get("thread_id")
                            or receipt.get("target") != payload.get("target")
                            or receipt.get("original_scheduled_epoch") != payload.get("scheduled_epoch")
                            or receipt.get("wake_token") != codex_quota_wake_token(payload["payload_digest"], int(payload["scheduled_epoch"]))
                        ):
                            return f"carrier repair identity mismatch: {receipt_path}"
                        status = receipt.get("status")
                        previous_outcome = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome")
                        saved_retry_epoch = receipt.get("retry_fire_epoch")
                        guard = receipt.get("guard")
                        if (
                            previous_outcome == "not-attempted"
                            and status == "carrier-consume-failed"
                            and isinstance(guard, Mapping)
                            and guard.get("reason") in suppression_reasons
                        ):
                            consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
                            if not consumed:
                                receipt.update(
                                    status="carrier-consume-failed",
                                    carrier_error=reason,
                                    updated_at_epoch=int(self._clock()),
                                )
                                _atomic_json_write(receipt_path, receipt)
                                return f"suppressed carrier consume repair failed: {reason}"
                            receipt.update(
                                status="suppressed",
                                queue_outcome="not-attempted",
                                previous_queue_outcome="not-attempted",
                                carrier_repair=reason,
                                updated_at_epoch=int(self._clock()),
                            )
                            _atomic_json_write(receipt_path, receipt)
                            continue
                        if (
                            previous_outcome == "not-attempted"
                            and status in {"carrier-consume-failed", "retry-available", "retry-arm-failed"}
                            and isinstance(saved_retry_epoch, int)
                            and not isinstance(saved_retry_epoch, bool)
                            and receipt.get("recovery") != "retry-carrier-rearmed"
                        ):
                            deadline = int(receipt.get("original_scheduled_epoch", 0)) + 86400
                            now = int(self._clock())
                            repaired_status = self._carrier_repair_agreed_status(receipt, previous_outcome, now, deadline)
                            if repaired_status == "retry-expired":
                                receipt.update(
                                    status="retry-expired",
                                    queue_outcome="not-attempted",
                                    previous_queue_outcome="not-attempted",
                                    updated_at_epoch=now,
                                )
                                _atomic_json_write(receipt_path, receipt)
                                continue
                            retry_epoch = int(receipt["retry_fire_epoch"])
                            receipt.update(
                                status="retry-available",
                                queue_outcome="not-attempted",
                                previous_queue_outcome="not-attempted",
                                retry_fire_epoch=retry_epoch,
                                updated_at_epoch=now,
                            )
                            _atomic_json_write(receipt_path, receipt)
                            armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                                payload, payload_path, sentinel, receipt, receipt_path, retry_epoch,
                                require_active_thread=False,
                                on_arm_failure=lambda r: r.update(
                                    previous_queue_outcome="not-attempted",
                                    queue_outcome="not-attempted",
                                ),
                            )
                            if not armed:
                                return f"early retry recovery arm failed: {arm_reason}"
                            receipt.update(
                                recovery="retry-carrier-rearmed",
                                updated_at_epoch=int(self._clock()),
                            )
                            _atomic_json_write(receipt_path, receipt)
                            continue
                        if status == "carrier-consume-failed" and receipt.get("rearm_original_on_repair"):
                            if (
                                self._verified_loaded_same_target_replacement(payload)
                                or self._verified_same_target_delivery_replacement(payload)
                            ):
                                retired, reason = self._retire_losing_wake_carrier(
                                    payload_path,
                                    payload,
                                    dict(receipt),
                                    receipt_path,
                                    require_active_thread=False,
                                )
                                if not retired:
                                    receipt.update(
                                        carrier_error=reason,
                                        updated_at_epoch=int(self._clock()),
                                    )
                                    _atomic_json_write(receipt_path, receipt)
                                    return f"target-lock-loser replacement retirement failed: {reason}"
                                continue
                            deadline = int(receipt.get("original_scheduled_epoch", 0)) + 86400
                            retry_base = max(int(self._clock()), int(payload.get("scheduled_epoch") or 0))
                            retry_epoch, _calendar = compute_unique_launchd_minute(
                                retry_base, timezone=self._timezone, margin_seconds=60
                            )
                            if retry_epoch > deadline:
                                receipt.update(status="operator-required", carrier_error="target-lock-loser retry window expired", updated_at_epoch=int(self._clock()))
                                _atomic_json_write(receipt_path, receipt)
                                return "target-lock-loser carrier retry window expired"
                            receipt.update(
                                status="retry-available",
                                attempt_count=max(1, int(receipt.get("attempt_count", 0))),
                                retry_fire_epoch=retry_epoch,
                                updated_at_epoch=int(self._clock()),
                            )
                            _atomic_json_write(receipt_path, receipt)
                            armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                                payload, payload_path, sentinel, receipt, receipt_path, retry_epoch,
                                require_active_thread=False,
                            )
                            if not armed:
                                return f"target-lock-loser carrier re-arm failed: {arm_reason}"
                            receipt.update(
                                recovery="retry-carrier-rearmed",
                                rearm_original_on_repair=False,
                                carrier_repair="target-lock-loser-original-rearmed",
                                updated_at_epoch=int(self._clock()),
                            )
                            _atomic_json_write(receipt_path, receipt)
                            continue
                        if status in {"retry-available", "retry-arm-failed"}:
                            if receipt.get("recovery") == "retry-carrier-rearmed":
                                if self._verified_same_target_delivery_replacement(payload):
                                    retired, reason = self._retire_losing_wake_carrier(
                                        payload_path,
                                        payload,
                                        dict(receipt),
                                        receipt_path,
                                        require_active_thread=False,
                                    )
                                    if not retired:
                                        receipt.update(
                                            carrier_error=reason,
                                            updated_at_epoch=int(self._clock()),
                                        )
                                        _atomic_json_write(receipt_path, receipt)
                                        return f"queued replacement retirement failed: {reason}"
                                continue
                            if previous_outcome not in {"not-attempted", "definitive-refusal"}:
                                if previous_outcome in {"unknown", "queued", "queued-but-unconfirmed"}:
                                    repaired = self._carrier_repair_agreed_status(receipt, previous_outcome, int(self._clock()), int(receipt.get("original_scheduled_epoch", 0)) + 86400)
                                    receipt.update(
                                        status=repaired,
                                        updated_at_epoch=int(self._clock()),
                                    )
                                    _atomic_json_write(receipt_path, receipt)
                                continue
                            retry_epoch = receipt.get("retry_fire_epoch")
                            if isinstance(retry_epoch, bool) or not isinstance(retry_epoch, int):
                                return f"retry recovery epoch unavailable: {receipt_path}"
                            now = int(self._clock())
                            deadline = int(receipt.get("original_scheduled_epoch", 0)) + 86400
                            retry_epoch = recompute_bounded_retry_epoch(
                                retry_epoch, now, deadline, timezone=self._timezone
                            )
                            if retry_epoch is None:
                                receipt.update(
                                    status="retry-expired",
                                    updated_at_epoch=now,
                                )
                                _atomic_json_write(receipt_path, receipt)
                                continue
                            receipt.update(retry_fire_epoch=retry_epoch, updated_at_epoch=now)
                            _atomic_json_write(receipt_path, receipt)
                            armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                                payload, payload_path, sentinel, receipt, receipt_path, retry_epoch,
                                require_active_thread=False,
                                on_arm_failure=lambda r: r.pop("recovery", None),
                            )
                            if not armed:
                                return f"retry recovery arm failed: {arm_reason}"
                            receipt.update(
                                status="retry-available",
                                recovery="retry-carrier-rearmed",
                                carrier_error=None,
                                updated_at_epoch=int(self._clock()),
                            )
                            _atomic_json_write(receipt_path, receipt)
                            continue
                        if receipt.get("retire_label_on_repair"):
                            if not self._verified_loaded_same_target_replacement(payload):
                                receipt.update(
                                    retire_label_on_repair=False,
                                    carrier_error="target-lock-loser replacement no longer verified",
                                    updated_at_epoch=int(self._clock()),
                                )
                                _atomic_json_write(receipt_path, receipt)
                                return "target-lock-loser replacement is no longer loaded; original carrier retained"
                            retired, reason = self._retire_losing_wake_carrier(
                                payload_path,
                                payload,
                                dict(receipt),
                                receipt_path,
                                require_active_thread=False,
                            )
                            if not retired:
                                receipt.update(
                                    status="carrier-consume-failed",
                                    carrier_error=reason,
                                    updated_at_epoch=int(self._clock()),
                                )
                                _atomic_json_write(receipt_path, receipt)
                                return f"target-lock-loser carrier repair failed: {reason}"
                            continue
                        previous_outcome = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome")
                        if previous_outcome not in {"queued", "queued-but-unconfirmed", "definitive-refusal", "not-attempted", "unknown"}:
                            receipt.update(status="operator-required", updated_at_epoch=int(self._clock()))
                            _atomic_json_write(receipt_path, receipt)
                            return f"carrier repair outcome is not eligible: {receipt_path}"
                        if not sentinel.exists():
                            sentinel.parent.mkdir(parents=True, exist_ok=True)
                            sentinel.write_text("fired\n", encoding="utf-8")
                        consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
                        if not consumed:
                            receipt.update(status="operator-required" if receipt.get("carrier_error") else "carrier-consume-failed", previous_queue_outcome=previous_outcome, queue_outcome=previous_outcome, carrier_error=reason, updated_at_epoch=int(self._clock()))
                            _atomic_json_write(receipt_path, receipt)
                            return f"carrier repair failed: {reason}"
                        now = int(self._clock())
                        if previous_outcome == "queued" or previous_outcome == "queued-but-unconfirmed":
                            repaired = self._carrier_repair_agreed_status(receipt, previous_outcome, now, int(receipt.get("original_scheduled_epoch", 0)) + 86400)
                            receipt.update(status=repaired, carrier_repair=reason, updated_at_epoch=now)
                            _atomic_json_write(receipt_path, receipt)
                            return "carrier repaired; prior queue outcome requires reconciliation"
                        if previous_outcome == "definitive-refusal":
                            retry_epoch = receipt.get("retry_fire_epoch")
                            deadline = int(receipt.get("original_scheduled_epoch", 0)) + 86400
                            if not isinstance(retry_epoch, int) or isinstance(retry_epoch, bool):
                                receipt.update(status="retry-expired", carrier_repair=reason, updated_at_epoch=now)
                                _atomic_json_write(receipt_path, receipt)
                                continue
                            retry_epoch = recompute_bounded_retry_epoch(
                                retry_epoch, now, deadline, timezone=self._timezone
                            )
                            if retry_epoch is None:
                                receipt.update(status="retry-expired", carrier_repair=reason, updated_at_epoch=now)
                                _atomic_json_write(receipt_path, receipt)
                                continue
                            receipt["retry_fire_epoch"] = retry_epoch
                            _atomic_json_write(receipt_path, receipt)
                            receipt.update(status="retry-available", carrier_repair=reason, updated_at_epoch=now)
                            armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                                payload, payload_path, sentinel, receipt, receipt_path, retry_epoch,
                                require_active_thread=False,
                            )
                            if not armed:
                                return f"retry recovery arm failed: {arm_reason}"
                            receipt.update(recovery="retry-carrier-rearmed", updated_at_epoch=int(self._clock()))
                            _atomic_json_write(receipt_path, receipt)
                            continue
                        if previous_outcome == "unknown":
                            receipt.update(status="operator-required", carrier_repair=reason, updated_at_epoch=now)
                        else:
                            receipt.update(status="retry-expired", carrier_repair=reason, updated_at_epoch=now)
                        _atomic_json_write(receipt_path, receipt)
                        continue
                    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                        return f"carrier repair failed: {exc}"
                    finally:
                        fcntl.flock(fire_lock.fileno(), fcntl.LOCK_UN)
            finally:
                self._release_target_wake_lock(target_lock)
                self._release_thread_wake_lock(thread_lock)
        return None

    def _carrier_repair_agreed_status(
        self,
        receipt: Mapping[str, Any],
        previous_outcome: Any,
        now: int,
        deadline: int,
    ) -> str | None:
        """Prior-outcome classifier for the mappings both entry points agree on.

        In: the receipt fields, now, and the 24h deadline. Out: the repaired
        status, or None when the mapping is caller-divergent (the suppression
        gates and the no-epoch/invalid-epoch branches stay at their callers).
        A recomputed in-window retry epoch is written back to the receipt.
        """
        if previous_outcome in {"queued", "queued-but-unconfirmed"}:
            return previous_outcome
        if previous_outcome == "unknown":
            return "operator-required"
        if previous_outcome in {"not-attempted", "definitive-refusal"}:
            saved_epoch = receipt.get("retry_fire_epoch")
            if isinstance(saved_epoch, int) and not isinstance(saved_epoch, bool):
                retry_epoch = recompute_bounded_retry_epoch(saved_epoch, now, deadline, timezone=self._timezone)
                if retry_epoch is not None:
                    receipt["retry_fire_epoch"] = retry_epoch
                return "retry-available" if retry_epoch is not None else "retry-expired"
        return None

    def _carrier_repair_rearm_or_restore(
        self,
        payload: Mapping[str, Any],
        payload_path: pathlib.Path,
        sentinel: pathlib.Path,
        receipt: dict[str, Any],
        receipt_path: pathlib.Path,
        retry_epoch: int,
        *,
        require_active_thread: bool = True,
        on_arm_failure=None,
    ) -> tuple[bool, str | None, bool | None]:
        """One bounded-retry arm-or-restore for the carrier-repair transition.

        Lock contract: every caller already holds thread + fire.lock, plus the
        target lock where its path joins it; this helper inherits whatever the
        caller holds and never acquires, asserts, or releases locks itself.
        On arm failure it restores the spent pair, lets ``on_arm_failure``
        apply the caller's divergent field edits (adds or pops), writes the
        restored-or-consume-failed
        status, and persists. On success the helper persists nothing; each
        caller performs its own success write (or none, per its divergent
        contract) after the helper returns.
        """
        armed, arm_reason = self._arm_existing_carrier(
            payload, payload_path, retry_epoch, require_active_thread=require_active_thread
        )
        if armed:
            return True, None, None
        restored = self._restore_spent_pair(sentinel)
        if on_arm_failure is not None:
            on_arm_failure(receipt)
        receipt.update(status="retry-arm-failed" if restored else "carrier-consume-failed", carrier_error=arm_reason, updated_at_epoch=int(self._clock()))
        _atomic_json_write(receipt_path, receipt)
        return False, arm_reason, restored

    @staticmethod
    def _carrier_repair_needs_target_reservation(receipt: Mapping[str, Any]) -> bool:
        """Classify from the scan snapshot; locked identity/status is revalidated later."""

        status = receipt.get("status")
        outcome = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome")
        if receipt.get("retire_label_on_repair"):
            return False
        guard = receipt.get("guard")
        if (
            status == "carrier-consume-failed"
            and outcome == "not-attempted"
            and isinstance(guard, Mapping)
            and guard.get("reason") in {"stop", "survey-only-stop", "safety-hold", "empty-queue", "target-changed"}
        ):
            return False
        if status == "carrier-consume-failed" and receipt.get("rearm_original_on_repair"):
            return True
        if status == "retry-available" and receipt.get("recovery") == "retry-carrier-rearmed":
            return True
        if outcome == "not-attempted" and status in {"carrier-consume-failed", "retry-available", "retry-arm-failed"}:
            retry_epoch = receipt.get("retry_fire_epoch")
            if isinstance(retry_epoch, int) and not isinstance(retry_epoch, bool) and receipt.get("recovery") != "retry-carrier-rearmed":
                return True
        if status in {"retry-available", "retry-arm-failed"} and receipt.get("recovery") != "retry-carrier-rearmed":
            return outcome in {"not-attempted", "definitive-refusal"}
        return status == "carrier-consume-failed" and outcome == "definitive-refusal"

    def _prune_terminal_wake_receipts(self) -> dict[str, Any]:
        """Remove only verified-unloaded terminal artifacts past bounded retention."""

        root = self._state_dir / "codex-quota-wakes"
        terminal = {"delivered", "suppressed", "retry-expired", "retry-exhausted", "superseded-reset"}
        if not root.is_dir():
            return {"removed": [], "retained": []}
        now = int(self._clock())
        items: list[tuple[pathlib.Path, dict[str, Any], dict[str, Any], int]] = []
        retained: list[dict[str, str]] = []
        for receipt_path in root.glob("*/fire-receipt.json"):
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                payload = json.loads((receipt_path.parent / "payload.json").read_text(encoding="utf-8"))
                updated = receipt.get("updated_at_epoch")
                if not isinstance(receipt, dict) or not isinstance(payload, dict):
                    raise ValueError("receipt or payload is not an object")
                if receipt.get("status") not in terminal:
                    continue
                if isinstance(updated, bool) or not isinstance(updated, int) or updated <= 0:
                    retained.append({"path": str(receipt_path), "reason": "terminal timestamp unreadable"})
                    continue
                items.append((receipt_path, receipt, payload, updated))
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                retained.append({"path": str(receipt_path), "reason": f"identity unreadable: {exc}"})
        to_remove = {item[0] for item in items if item[3] < now - 30 * 86400}
        if len(items) > 128:
            by_age = sorted(items, key=lambda item: (item[3], str(item[0])))
            to_remove.update(item[0] for item in by_age[:len(items) - 128])
        removed: list[str] = []
        for receipt_path, _initial_receipt, initial_payload, _updated in sorted(
            (item for item in items if item[0] in to_remove), key=lambda item: (item[3], str(item[0]))
        ):
            thread_lock = self._acquire_thread_wake_lock(initial_payload)
            if thread_lock is None:
                retained.append({"path": str(receipt_path), "reason": "thread lock held"})
                continue
            try:
                with (receipt_path.parent / "fire.lock").open("a+") as wake_lock:
                    try:
                        fcntl.flock(wake_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        retained.append({"path": str(receipt_path), "reason": "wake lock held"})
                        continue
                    try:
                        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                        payload_path = receipt_path.parent / "payload.json"
                        payload = self._revalidate_fire_payload(
                            payload_path, initial_payload, require_active_thread=False
                        )
                        status = receipt.get("status")
                        if (
                            status not in terminal
                            or receipt.get("payload_digest") != payload.get("payload_digest")
                            or receipt.get("thread_id") != payload.get("thread_id")
                            or receipt.get("target") != payload.get("target")
                            or receipt.get("original_scheduled_epoch") != payload.get("scheduled_epoch")
                        ):
                            retained.append({"path": str(receipt_path), "reason": "identity or status changed"})
                            continue
                        age = receipt.get("updated_at_epoch")
                        over_cap = len(items) > 128 and receipt_path in to_remove
                        if not (isinstance(age, int) and not isinstance(age, bool) and (age < now - 30 * 86400 or over_cap)):
                            retained.append({"path": str(receipt_path), "reason": "retention boundary changed"})
                            continue
                        label = str(payload.get("label") or "")
                        expected_label = f"ai-playbook.codex-quota-wake.{str(payload.get('payload_digest') or '')[:12]}"
                        if not label or label != expected_label:
                            retained.append({"path": str(receipt_path), "reason": "recorded label missing"})
                            continue
                        plist_path = receipt_path.parent / f"{label}.plist"
                        booted = self._bootout(plist_path)
                        bootout_rc = booted.get("exited")
                        if not (bootout_rc is True or (isinstance(bootout_rc, int) and not isinstance(bootout_rc, bool) and bootout_rc == 0)):
                            retained.append({"path": str(receipt_path), "reason": "label bootout refused"})
                            continue
                        loaded, detail = self._verify_loaded(label)
                        if loaded:
                            retained.append({"path": str(receipt_path), "reason": f"label remains loaded: {detail}"})
                            continue
                        # Keep both locks through deletion: no concurrent fire or
                        # reconciler can recreate this terminal receipt in between.
                        shutil.rmtree(receipt_path.parent)
                        removed.append(str(receipt_path))
                    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                        retained.append({"path": str(receipt_path), "reason": f"prune verification failed: {exc}"})
                    finally:
                        fcntl.flock(wake_lock.fileno(), fcntl.LOCK_UN)
            except OSError as exc:
                retained.append({"path": str(receipt_path), "reason": f"wake lock unavailable: {exc}"})
            finally:
                self._release_thread_wake_lock(thread_lock)
        return {"removed": removed, "retained": retained}

    def _existing_message_blocks_arm(self, identity: Mapping[str, Any], *, include_armed: bool = False) -> str | None:
        root = self._state_dir / "codex-quota-wakes"
        if not root.is_dir():
            return None
        pending = {"attempting", "retry-available", "queued", "queued-but-unconfirmed", "unknown", "operator-required", "retry-exhausted", "carrier-consume-failed", "retry-arm-failed"}
        for arm_receipt_path in root.glob("*/arm-receipt.json"):
            try:
                arm_receipt = json.loads(arm_receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return f"existing quota wake state unreadable: {arm_receipt_path}"
            if not isinstance(arm_receipt, Mapping):
                return f"existing quota wake state unreadable: {arm_receipt_path}"
            old_payload = arm_receipt.get("payload")
            if not isinstance(old_payload, Mapping):
                return f"existing quota wake state unreadable: {arm_receipt_path}"
            if old_payload.get("repo_root") != identity.get("repo_root"):
                continue
            same_thread = old_payload.get("thread_id") == identity.get("thread_id")
            same_target_kind = (
                old_payload.get("target") == identity.get("target")
                and old_payload.get("kind") == identity.get("kind")
            )
            if not same_thread and not same_target_kind:
                continue
            if identity.get("payload_digest") and arm_receipt.get("payload_digest") == identity.get("payload_digest"):
                continue
            receipt_path = arm_receipt_path.parent / "fire-receipt.json"
            delivered_same_reset = False
            if receipt_path.is_file():
                try:
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    return f"existing quota wake state unreadable: {receipt_path}"
                if not isinstance(receipt, Mapping):
                    return f"existing quota wake state unreadable: {receipt_path}"
                status = receipt.get("status")
                if status == "delivered" and receipt.get("delivery_verified") is True:
                    expected_token = codex_quota_wake_token(
                        str(old_payload.get("payload_digest") or ""),
                        int(old_payload.get("scheduled_epoch") or 0),
                    )
                    delivered_same_reset = (
                        same_target_kind
                        and arm_receipt.get("payload_digest") == old_payload.get("payload_digest")
                        and old_payload.get("reset_at_epoch") == identity.get("reset_at_epoch")
                        and old_payload.get("payload_digest") == self._payload_digest(old_payload)
                        and receipt.get("queue_outcome") in {"queued", "queued-but-unconfirmed"}
                        and receipt.get("payload_digest") == old_payload.get("payload_digest")
                        and receipt.get("thread_id") == old_payload.get("thread_id")
                        and receipt.get("target") == old_payload.get("target")
                        and receipt.get("original_scheduled_epoch") == old_payload.get("scheduled_epoch")
                        and receipt.get("wake_token") == expected_token
                    )
            elif include_armed:
                label = str(old_payload.get("label") or "")
                plist_path = launchd_plist_path(arm_receipt_path.parent, label)
                loaded, _detail = self._verify_loaded(label) if plist_path.is_file() else (False, "plist missing")
                sentinel = pathlib.Path(str(old_payload.get("sentinel_path") or ""))
                # launchd can stop reporting the label after its callback starts;
                # the callback creates the sentinel before entering Python.
                status = "armed" if loaded or sentinel.is_file() else "unarmed"
            else:
                continue
            if status in pending or delivered_same_reset or (include_armed and status == "armed"):
                return f"existing pending message requires reconciliation: {status}"
        return None

    def fire(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Process one carrier fire with an exclusive durable receipt."""

        payload_path = pathlib.Path(str(request.get("payload_path") or "")).expanduser()
        if not payload_path.is_absolute() or not payload_path.is_file():
            return {"decision": "stand_down", "reason": "payload-unreadable"}
        try:
            payload = self._validate_fire_payload(payload_path)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return {"decision": "stand_down", "reason": "payload-invalid", "detail": str(exc)}
        digest = str(payload["payload_digest"])
        arm_receipt_path = payload_path.parent / "arm-receipt.json"
        try:
            arm_receipt = json.loads(arm_receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {"decision": "stand_down", "reason": "arm-receipt-unreadable", "detail": str(exc)}
        if (
            not isinstance(arm_receipt, Mapping)
            or arm_receipt.get("payload_digest") != digest
            or arm_receipt.get("payload") != payload
        ):
            return {"decision": "stand_down", "reason": "arm-receipt-mismatch"}
        original_epoch = int(payload["scheduled_epoch"])
        token = codex_quota_wake_token(digest, original_epoch)
        active_thread = str(self._env.get("CODEX_THREAD_ID") or "").strip()
        if active_thread and active_thread != str(payload["thread_id"]):
            return {"decision": "stand_down", "reason": "thread-binding-changed"}
        wake_dir = payload_path.parent
        receipt_path = wake_dir / "fire-receipt.json"
        lock_path = wake_dir / "fire.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        thread_lock = self._acquire_thread_wake_lock(payload)
        if thread_lock is None:
            return {"decision": "stand_down", "reason": "already-claimed"}
        target_lock = self._acquire_target_wake_lock(payload)
        if target_lock is None:
            try:
                return self._record_target_lock_loss(
                    payload_path, payload, receipt_path, token, original_epoch
                )
            finally:
                self._release_thread_wake_lock(thread_lock)
        try:
            lock_handle = lock_path.open("a+")
        except OSError as exc:
            self._release_target_wake_lock(target_lock)
            self._release_thread_wake_lock(thread_lock)
            return {"decision": "stand_down", "reason": "wake-lock-unavailable", "detail": str(exc)}
        with lock_handle as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self._release_target_wake_lock(target_lock)
                self._release_thread_wake_lock(thread_lock)
                return {"decision": "stand_down", "reason": "already-claimed"}
            try:
                verified_arm_path = wake_dir / "verified-arm.json"
                try:
                    verified_arm_path.unlink(missing_ok=True)
                    if verified_arm_path.exists():
                        return {"decision": "stand_down", "reason": "verified-arm-marker-invalidation-failed"}
                except OSError as exc:
                    return {"decision": "stand_down", "reason": "verified-arm-marker-invalidation-failed", "detail": str(exc)}
                unresolved = self._existing_message_blocks_arm(payload)
                if unresolved:
                    return {"decision": "stand_down", "reason": "pending-message-requires-reconciliation", "detail": unresolved}
                now_epoch = int(self._clock())
                sentinel = pathlib.Path(payload.get("sentinel_path") or (wake_dir / "wake.sentinel"))
                receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {
                    "payload_digest": digest,
                    "thread_id": payload["thread_id"],
                    "original_scheduled_epoch": original_epoch,
                    "wake_token": token,
                    "attempt_count": 0,
                    "retry_fire_epoch": None,
                    "queue_outcome": None,
                    "status": "pending",
                    "target": payload["target"],
                }
                if receipt.get("payload_digest") != digest or receipt.get("thread_id") != payload["thread_id"] or receipt.get("original_scheduled_epoch") != original_epoch or receipt.get("wake_token") != token or receipt.get("target") != payload["target"]:
                    return {"decision": "stand_down", "reason": "receipt-identity-mismatch"}
                if receipt.get("status") == "attempting":
                    receipt.update(status="unknown", queue_outcome="unknown", updated_at_epoch=now_epoch)
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "previous-attempt-unknown", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                if receipt.get("status") in {"carrier-consume-failed", "retry-arm-failed"}:
                    prior_consume_error = receipt.get("carrier_error")
                    try:
                        sentinel.parent.mkdir(parents=True, exist_ok=True)
                        if not sentinel.exists():
                            sentinel.write_text("fired\n", encoding="utf-8")
                    except OSError as exc:
                        receipt.update(status="operator-required", carrier_repair=str(exc), updated_at_epoch=now_epoch)
                        _atomic_json_write(receipt_path, receipt)
                        return {"decision": "stand_down", "reason": "operator-required", "receipt": receipt}
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    previous_outcome = receipt.get("previous_queue_outcome") or receipt.get("queue_outcome")
                    if consumed:
                        guard = receipt.get("guard")
                        if previous_outcome == "not-attempted" and isinstance(guard, Mapping) and guard.get("reason") in suppression_reasons:
                            repaired_status = "suppressed"
                        else:
                            repaired_status = self._carrier_repair_agreed_status(receipt, previous_outcome, now_epoch, original_epoch + 86400)
                            if repaired_status is None:
                                repaired_status = "operator-required"
                        receipt.update(status=repaired_status, carrier_repair=reason, updated_at_epoch=now_epoch)
                    else:
                        receipt.update(status="operator-required" if prior_consume_error else "carrier-consume-failed", previous_queue_outcome=previous_outcome or "not-attempted", queue_outcome=previous_outcome or "not-attempted", carrier_error=reason, updated_at_epoch=now_epoch)
                    _atomic_json_write(receipt_path, receipt)
                    if consumed and receipt.get("status") == "retry-available":
                        retry_epoch = int(receipt["retry_fire_epoch"])
                        armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                            payload, payload_path, sentinel, receipt, receipt_path, retry_epoch,
                            on_arm_failure=lambda r: r.pop("recovery", None),
                        )
                        if not armed:
                            return {"decision": receipt["status"], "reason": arm_reason, "receipt": receipt}
                        receipt.update(recovery="retry-carrier-rearmed", updated_at_epoch=int(self._clock()))
                        _atomic_json_write(receipt_path, receipt)
                    return {"decision": "stand_down", "reason": "carrier-repaired-outcome-preserved" if consumed else "operator-required", "receipt": receipt, "retry_armed": bool(consumed and receipt.get("recovery") == "retry-carrier-rearmed")}
                if receipt.get("status") in {"queued", "queued-but-unconfirmed", "unknown", "operator-required", "suppressed", "retry-exhausted", "retry-expired", "superseded-reset", "delivered"}:
                    return {"decision": "stand_down", "reason": "receipt-terminal", "receipt": receipt}
                early_retry = (
                    receipt.get("status") == "retry-available"
                    and receipt.get("previous_queue_outcome") == "not-attempted"
                    and isinstance(receipt.get("retry_fire_epoch"), int)
                    and not isinstance(receipt.get("retry_fire_epoch"), bool)
                )
                expected_epoch = (
                    receipt.get("retry_fire_epoch")
                    if early_retry or receipt.get("attempt_count", 0) != 0
                    else original_epoch
                )
                if isinstance(expected_epoch, bool) or not isinstance(expected_epoch, int):
                    return {"decision": "stand_down", "reason": "receipt-fire-epoch-invalid"}
                supplied_epoch = request.get("expected_fire_epoch", expected_epoch)
                if supplied_epoch != expected_epoch:
                    return {"decision": "stand_down", "reason": "fire-epoch-mismatch"}
                try:
                    payload = self._revalidate_fire_payload(payload_path, payload)
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    return {"decision": "stand_down", "reason": "payload-changed-before-fire", "detail": str(exc), "target": receipt.get("target")}
                early_fire = now_epoch < int(expected_epoch)
                if early_fire:
                    # Persist the recovery epoch and identity before touching
                    # the fired marker or sentinel. A crash during re-arm can
                    # then be repaired from this receipt without guessing the
                    # original calendar minute.
                    attempt_count = int(receipt.get("attempt_count", 0))
                    if attempt_count == 0:
                        previous_outcome = "not-attempted"
                    else:
                        # queue_outcome advances after a real attempt; the
                        # older previous_queue_outcome may still describe the
                        # original early fire and must not mask that result.
                        previous_outcome = (
                            receipt.get("queue_outcome")
                            or receipt.get("previous_queue_outcome")
                            or "not-attempted"
                        )
                    # A prior successful early retry may have left this marker
                    # behind. Clear it in the same durable write as the new
                    # retry intent, before consuming the carrier, so repair
                    # cannot mistake an interrupted re-arm for a completed one.
                    receipt.pop("recovery", None)
                    receipt.update(
                        status="retry-available",
                        queue_outcome=previous_outcome,
                        previous_queue_outcome=previous_outcome,
                        retry_fire_epoch=int(expected_epoch),
                        updated_at_epoch=now_epoch,
                    )
                    _atomic_json_write(receipt_path, receipt)
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if not sentinel.exists():
                        sentinel.write_text("fired\n", encoding="utf-8")
                except OSError as exc:
                    return {"decision": "operator-required", "reason": "sentinel-create-failed", "detail": str(exc)}
                if early_fire:
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    if not consumed:
                        return {"decision": "stand_down", "reason": "early-fire-carrier-consume-failed", "carrier_reason": reason, "receipt": receipt, "target": payload["target"]}
                    armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                        payload, payload_path, sentinel, receipt, receipt_path, int(expected_epoch),
                        on_arm_failure=lambda r: r.update(
                            queue_outcome=previous_outcome,
                            previous_queue_outcome=previous_outcome,
                        ),
                    )
                    if not armed:
                        return {"decision": "stand_down", "reason": "early-fire-rearm-failed", "detail": arm_reason, "carrier_restored": restored, "receipt": receipt, "target": payload["target"]}
                    receipt.update(
                        recovery="retry-carrier-rearmed",
                        updated_at_epoch=int(self._clock()),
                    )
                    _atomic_json_write(receipt_path, receipt)
                    return {"decision": "stand_down", "reason": "early-fire-rearmed", "target": payload["target"], "payload_path": str(payload_path), "fire_epoch": int(expected_epoch)}
                deadline = original_epoch + 86400
                if now_epoch > deadline:
                    receipt.update(status="retry-expired", queue_outcome="not-attempted", updated_at_epoch=now_epoch)
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "retry-expired" if int(receipt.get("attempt_count", 0)) else "wake-expired", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                if receipt.get("status") == "retry-available" and now_epoch < int(expected_epoch):
                    return {"decision": "stand_down", "reason": "retry-not-due", "receipt": receipt}
                try:
                    payload = self._revalidate_fire_payload(payload_path, payload)
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "payload-changed-before-attempt", "detail": str(exc), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                receipt.update(status="attempting", updated_at_epoch=now_epoch, wake_token=token)
                _atomic_json_write(receipt_path, receipt)
                try:
                    payload = self._revalidate_fire_payload(payload_path, payload)
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "payload-changed-before-guard", "detail": str(exc), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                guard = dict(self._fire_guard(payload))
                queue_now = int(self._clock())
                if queue_now > deadline:
                    receipt.update(status="retry-expired", queue_outcome="not-attempted", updated_at_epoch=queue_now)
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "retry-expired" if int(receipt.get("attempt_count", 0)) else "wake-expired", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                try:
                    payload = self._revalidate_fire_payload(payload_path, payload)
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "payload-changed-after-guard", "detail": str(exc), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                if not guard.get("ready"):
                    if guard.get("reason") in {"primary-reset-changed", "primary-quota-paused", "primary-quota-wait-for-reset"} and guard.get("target") == payload.get("target"):
                        return self._schedule_replacement_wake(payload, receipt, receipt_path, guard, sentinel, thread_lock, target_lock)
                    status = "suppressed" if guard.get("reason") in {"stop", "survey-only-stop", "safety-hold", "empty-queue", "target-changed"} else "operator-required"
                    receipt.update(status=status, queue_outcome="not-attempted", guard=guard, updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": guard.get("reason", "fire-guard-refused"), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                argv, child_env = self._queue_argv(dict(payload, payload_path=str(payload_path)), token)
                try:
                    payload = self._revalidate_fire_payload(payload_path, payload)
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "payload-changed-before-queue", "detail": str(exc), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                # Scheduler turns replace this file atomically but do not
                # share a write lock with wake delivery. Recheck stop and
                # target state after argv preparation, immediately before the
                # external queue side effect.
                final_guard = dict(self._pre_queue_guard(payload))
                if not final_guard.get("ready"):
                    if final_guard.get("reason") in {"primary-reset-changed", "primary-quota-paused", "primary-quota-wait-for-reset"} and final_guard.get("target") == payload.get("target"):
                        return self._schedule_replacement_wake(payload, receipt, receipt_path, final_guard, sentinel, thread_lock, target_lock)
                    status = "suppressed" if final_guard.get("reason") in {"stop", "survey-only-stop", "safety-hold", "empty-queue", "target-changed"} else "operator-required"
                    receipt.update(status=status, queue_outcome="not-attempted", guard=final_guard, updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": final_guard.get("reason", "fire-guard-refused"), "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                queue_now = int(self._clock())
                if queue_now > deadline:
                    receipt.update(status="retry-expired", queue_outcome="not-attempted", updated_at_epoch=queue_now)
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "stand_down", "reason": "retry-expired" if int(receipt.get("attempt_count", 0)) else "wake-expired", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                try:
                    result = self._queue_command(argv, child_env, pathlib.Path(payload["repo_root"]))
                except (OSError, subprocess.TimeoutExpired) as exc:
                    receipt.update(status="operator-required", queue_outcome="unknown", error=str(exc), updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "operator-required", "reason": "queue-outcome-unknown", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
                stdout = str(getattr(result, "stdout", "") or "")
                stderr = str(getattr(result, "stderr", "") or "")
                returncode = int(getattr(result, "returncode", 1))
                warning = "failed to resume" in (stdout + "\n" + stderr).lower()
                attempts = int(receipt.get("attempt_count", 0)) + 1
                if returncode == 0:
                    status = "queued-but-unconfirmed" if warning else "queued"
                    receipt.update(status=status, queue_outcome=status, attempt_count=attempts, updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    if not consumed:
                        receipt.update(status="carrier-consume-failed", previous_queue_outcome=status, carrier_error=reason)
                        _atomic_json_write(receipt_path, receipt)
                    return {"decision": status, "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                if not self._definitive_queue_refusal(returncode, stderr):
                    receipt.update(status="operator-required", queue_outcome="unknown", error=stderr or stdout or f"codex queue exited {returncode}", updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    if not consumed:
                        receipt.update(status="carrier-consume-failed", previous_queue_outcome="unknown", carrier_error=reason)
                        _atomic_json_write(receipt_path, receipt)
                    return {"decision": "operator-required", "reason": "queue-outcome-unknown", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                if attempts >= 2:
                    receipt.update(status="retry-exhausted", queue_outcome="definitive-refusal", attempt_count=attempts, updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "retry-exhausted", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                refusal_epoch = int(self._clock())
                retry_epoch, _calendar = compute_unique_launchd_minute(
                    refusal_epoch, timezone=self._timezone, margin_seconds=60
                )
                if retry_epoch > deadline:
                    receipt.update(status="retry-expired", queue_outcome="definitive-refusal", attempt_count=attempts, updated_at_epoch=int(self._clock()))
                    _atomic_json_write(receipt_path, receipt)
                    sentinel = pathlib.Path(payload.get("sentinel_path") or (wake_dir / "wake.sentinel"))
                    consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                    return {"decision": "retry-expired", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason, "target": payload["target"]}
                receipt.update(status="retry-available", queue_outcome="definitive-refusal", attempt_count=attempts, retry_fire_epoch=retry_epoch, updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                if not consumed:
                    receipt.update(status="carrier-consume-failed", previous_queue_outcome="definitive-refusal", carrier_error=reason)
                    _atomic_json_write(receipt_path, receipt)
                    return {"decision": "operator-required", "reason": "carrier-consume-failed", "receipt": receipt}
                arm_now = int(self._clock())
                if retry_epoch <= arm_now:
                    try:
                        retry_epoch, _calendar = compute_unique_launchd_minute(
                            arm_now, timezone=self._timezone, margin_seconds=60
                        )
                    except ValueError:
                        retry_epoch = deadline + 1
                    if retry_epoch > deadline:
                        receipt.update(
                            status="retry-expired",
                            retry_fire_epoch=None,
                            updated_at_epoch=arm_now,
                        )
                        _atomic_json_write(receipt_path, receipt)
                        return {
                            "decision": "retry-expired",
                            "reason": "retry-expired",
                            "receipt": receipt,
                            "carrier_consumed": True,
                            "target": payload["target"],
                        }
                    receipt.update(retry_fire_epoch=retry_epoch, updated_at_epoch=arm_now)
                    _atomic_json_write(receipt_path, receipt)
                armed, arm_reason, restored = self._carrier_repair_rearm_or_restore(
                    payload, payload_path, sentinel, receipt, receipt_path, int(retry_epoch),
                    on_arm_failure=lambda r: r.update(previous_queue_outcome="definitive-refusal"),
                )
                if not armed:
                    return {"decision": receipt["status"], "reason": arm_reason, "receipt": receipt, "target": payload["target"]}
                return {"decision": "retry-available", "receipt": receipt, "target": payload["target"], "retry_armed": True}
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                self._release_target_wake_lock(target_lock)
                self._release_thread_wake_lock(thread_lock)

    def _restore_spent_pair(self, sentinel: pathlib.Path) -> bool:
        marker = fired_marker_path(sentinel)
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("consumed\n", encoding="utf-8")
            sentinel.write_text("fired\n", encoding="utf-8")
            return marker.is_file() and sentinel.is_file()
        except OSError:
            return False

    def _arm_existing_carrier(
        self,
        payload: Mapping[str, Any],
        payload_path: pathlib.Path,
        fire_epoch: int,
        *,
        require_active_thread: bool = True,
    ) -> tuple[bool, str]:
        """Replace the calendar date after a verified spent-pair cleanup."""

        try:
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return False, f"payload-revalidation-failed: {exc}"
        label = str(payload.get("label") or "")
        plist_path = launchd_plist_path(payload_path.parent, label)
        try:
            booted = self._bootout(plist_path)
            if booted.get("exited") not in (0, True):
                return False, "spent-job-bootout-failed"
            loaded, detail = self._verify_loaded(label)
            if loaded:
                return False, f"spent-job-still-loaded: {detail}"
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            sentinel = pathlib.Path(str(payload["sentinel_path"]))
            marker = fired_marker_path(sentinel)
            sentinel.unlink(missing_ok=True)
            if sentinel.exists():
                return False, "spent-sentinel-cleanup-failed"
            marker.unlink(missing_ok=True)
            if marker.exists():
                return False, "spent-marker-cleanup-failed"
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            local = datetime.fromtimestamp(fire_epoch, self._timezone or _system_local_timezone())
            calendar = {"Month": local.month, "Day": local.day, "Hour": local.hour, "Minute": local.minute}
            plist = plistlib.loads(plist_path.read_bytes())
            plist["StartCalendarInterval"] = calendar
            arguments = list(plist["ProgramArguments"])
            input_index = arguments.index("--input") + 1
            arguments[input_index] = json.dumps({"payload_path": str(payload_path), "expected_fire_epoch": fire_epoch}, separators=(",", ":"))
            plist["ProgramArguments"] = arguments
            temporary = plist_path.with_suffix(".plist.tmp")
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            with temporary.open("wb") as handle:
                plistlib.dump(plist, handle)
            os.replace(temporary, plist_path)
            if plistlib.loads(plist_path.read_bytes()) != plist:
                return False, "retry-plist-readback-failed"
            payload = self._revalidate_fire_payload(
                payload_path, payload, require_active_thread=require_active_thread
            )
            loaded, detail = self._bootstrap(plist_path)
            if not loaded:
                return False, f"retry-bootstrap-failed: {detail}"
            loaded, detail = self._verify_loaded(label)
            if not loaded:
                return False, f"retry-loaded-label-verification-failed: {detail}"
            try:
                payload = self._revalidate_fire_payload(
                    payload_path, payload, require_active_thread=require_active_thread
                )
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                try:
                    booted = self._bootout(plist_path)
                    if booted.get("exited") not in (0, True):
                        return False, f"payload-revalidation-failed-after-bootstrap; stale retry bootout failed: {exc}"
                    still_loaded, cleanup_detail = self._verify_loaded(label)
                    if still_loaded:
                        return False, f"payload-revalidation-failed-after-bootstrap; stale retry remains loaded: {cleanup_detail}"
                except (OSError, ValueError, KeyError, TypeError) as cleanup_exc:
                    return False, f"payload-revalidation-failed-after-bootstrap; stale retry cleanup failed: {cleanup_exc}"
                return False, f"payload-revalidation-failed-after-bootstrap: {exc}"
            verified_arm = {
                "payload_digest": payload["payload_digest"],
                "label": label,
                "fire_epoch": int(fire_epoch),
                "verified_at_epoch": int(self._clock()),
            }
            _atomic_json_write(payload_path.parent / "verified-arm.json", verified_arm)
            return True, "retry-armed"
        except (OSError, ValueError, KeyError) as exc:
            return False, str(exc)

    def _schedule_replacement_wake(self, payload: Mapping[str, Any], receipt: dict[str, Any], receipt_path: pathlib.Path, guard: Mapping[str, Any], sentinel: pathlib.Path, thread_lock, target_lock) -> dict[str, Any]:
        """Re-arm only after the fresh disk guard still names the same target."""
        payload_path = receipt_path.parent / "payload.json"
        try:
            payload = self._revalidate_fire_payload(payload_path, payload)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
            _atomic_json_write(receipt_path, receipt)
            return {"decision": "stand_down", "reason": "payload-changed-before-replacement", "receipt": receipt}
        reset = guard.get("reset_at_epoch")
        if guard.get("target") != payload.get("target"):
            return {"decision": "stand_down", "reason": "target-changed", "receipt": receipt}
        if isinstance(reset, bool) or not isinstance(reset, int) or reset <= 0:
            return {"decision": "stand_down", "reason": "primary-reset-unverified", "receipt": receipt}
        if guard.get("reason") == "primary-quota-wait-for-reset":
            current_guard = dict(self._fire_guard(payload))
            if current_guard.get("reason") in {"stop", "survey-only-stop", "safety-hold", "empty-queue", "target-changed"}:
                receipt.update(status="suppressed", queue_outcome="not-attempted", guard=current_guard, updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                return {"decision": "stand_down", "reason": current_guard["reason"], "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
            current_reset = current_guard.get("reset_at_epoch")
            if (
                current_guard.get("reason") != "primary-quota-wait-for-reset"
                or current_guard.get("target") != payload.get("target")
                or isinstance(current_reset, bool)
                or not isinstance(current_reset, int)
                or current_reset <= 0
                or current_reset != reset
            ):
                receipt.update(status="operator-required", queue_outcome="not-attempted", guard=current_guard, updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                consumed, reason = self._consume_fire_carrier(receipt, receipt_path, sentinel)
                return {"decision": "operator-required", "reason": "replacement-admission-changed", "receipt": receipt, "carrier_consumed": consumed, "carrier_reason": reason}
        old_label = str(payload.get("label") or "")
        old_plist = launchd_plist_path(receipt_path.parent, old_label)
        try:
            booted = self._bootout(old_plist)
            if booted.get("exited") not in (0, True):
                raise ValueError("old wake bootout failed")
            loaded, detail = self._verify_loaded(old_label)
            if loaded:
                raise ValueError(f"old wake remains loaded: {detail}")
            try:
                payload = self._revalidate_fire_payload(payload_path, payload)
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                return {"decision": "operator-required", "reason": "payload-changed-after-replacement-bootout", "receipt": receipt}
            consumed, reason = _verified_wake_consume(sentinel, fired_marker_path(sentinel))
            if not consumed:
                receipt.update(status="carrier-consume-failed", previous_queue_outcome="not-attempted", carrier_error=reason)
                _atomic_json_write(receipt_path, receipt)
                return {"decision": "operator-required", "reason": "carrier-consume-failed", "receipt": receipt}
            try:
                payload = self._revalidate_fire_payload(payload_path, payload)
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                receipt.update(status="operator-required", queue_outcome="not-attempted", identity_error=str(exc), updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                return {"decision": "operator-required", "reason": "payload-changed-after-replacement-consume", "receipt": receipt}
            receipt.update(status="superseded-reset", queue_outcome="not-attempted", replacement_reset_at_epoch=reset, updated_at_epoch=int(self._clock()))
            _atomic_json_write(receipt_path, receipt)
            replacement_env = dict(self._env)
            replacement_env["CODEX_THREAD_ID"] = str(payload["thread_id"])
            replacement_env["CODEX_HOME"] = str(payload["codex_home"])
            interpreter_command = payload.get("codex_interpreter_command")

            def captured_which(name: str) -> str | None:
                if name == "codex":
                    return str(payload["codex_executable"])
                if interpreter_command and name == interpreter_command:
                    return str(payload["codex_interpreter"])
                return self._which(name)

            def replacement_schedule_guard(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
                fresh = dict(self._fire_guard(candidate))
                fresh_reset = fresh.get("reset_at_epoch")
                if (
                    fresh.get("reason") != "primary-quota-wait-for-reset"
                    or fresh.get("target") != candidate.get("target")
                    or isinstance(fresh_reset, bool)
                    or not isinstance(fresh_reset, int)
                    or fresh_reset <= 0
                    or fresh_reset != candidate.get("reset_at_epoch")
                ):
                    return fresh
                return {
                    "ready": True,
                    "target": candidate["target"],
                    "kind": candidate["kind"],
                    "reset_at_epoch": fresh_reset,
                }

            replacement_scheduler = CodexQuotaWakeScheduler(
                state_dir=self._state_dir, repo_root=self._repo_root, env=replacement_env,
                clock=self._clock, timezone=self._timezone, which=captured_which,
                bootstrap=self._bootstrap, verify_loaded=self._verify_loaded,
                bootout=self._bootout, queue_command=self._queue_command, fire_guard=self._fire_guard,
                pre_queue_guard=self._pre_queue_guard,
                schedule_guard=(replacement_schedule_guard if guard.get("reason") == "primary-quota-wait-for-reset" else self._schedule_guard),
            )
            payload = self._revalidate_fire_payload(payload_path, payload)
            scheduled = replacement_scheduler.schedule({
                "thread_id": payload["thread_id"], "repo_root": payload["repo_root"],
                "target": payload["target"], "kind": payload["kind"],
                "phase": payload["phase"], "reset_at_epoch": reset,
            }, _held_thread_lock=thread_lock, _held_target_lock=target_lock, _not_before_epoch=int(self._clock()) + 60)
            if not scheduled.get("scheduled"):
                receipt.update(status="operator-required", replacement_arm_error=scheduled.get("reason"), updated_at_epoch=int(self._clock()))
                _atomic_json_write(receipt_path, receipt)
                return {"decision": "operator-required", "reason": "replacement-arm-failed", "receipt": receipt, "replacement": scheduled}
            return {"decision": "replacement-scheduled", "replacement": scheduled, "target": payload["target"]}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            receipt.update(status="operator-required", replacement_arm_error=str(exc), updated_at_epoch=int(self._clock()))
            _atomic_json_write(receipt_path, receipt)
            return {"decision": "operator-required", "reason": "replacement-arm-failed", "receipt": receipt}

    def _validate(self, request: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        if not isinstance(request, Mapping):
            raise ValueError("Codex quota wake request must be an object")
        thread_id = str(request.get("thread_id") or "").strip()
        try:
            parsed_thread_id = uuid.UUID(thread_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError("thread_id must be a valid UUID") from exc
        runtime_thread_id = str(self._env.get("CODEX_THREAD_ID") or "").strip()
        try:
            parsed_runtime_id = uuid.UUID(runtime_thread_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError("CODEX_THREAD_ID must be a valid UUID") from exc
        if parsed_thread_id != parsed_runtime_id:
            raise ValueError("thread_id does not match CODEX_THREAD_ID")
        root_raw = str(request.get("repo_root") or "").strip()
        root = pathlib.Path(root_raw).expanduser()
        if not root.is_absolute() or not root.is_dir():
            raise ValueError("repo_root must be an absolute existing directory")
        if root.resolve() != self._repo_root.resolve():
            raise ValueError("repo_root does not match the scheduler repository")
        target = request.get("target")
        phase = request.get("phase")
        kind = request.get("kind")
        if isinstance(target, str) and _has_control_character(target):
            raise ValueError("target may not contain control characters")
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a nonempty string")
        if isinstance(phase, str) and _has_control_character(phase):
            raise ValueError("phase may not contain control characters")
        if not isinstance(phase, str) or not phase.strip():
            raise ValueError("phase must be a nonempty string")
        if kind not in {"execute", "author", "audit", "retriage"}:
            raise ValueError("kind must name the pending maintenance dispatch kind")
        reset_at = request.get("reset_at_epoch")
        if isinstance(reset_at, bool) or not isinstance(reset_at, int) or reset_at <= 0:
            raise ValueError("primary reset epoch must be a positive integer")
        binding = capture_codex_runtime_binding(self._env, which=self._which)
        return {
            "thread_id": str(parsed_thread_id),
            "repo_root": str(root.resolve()),
            "target": target.strip(),
            "kind": kind,
            "phase": phase.strip(),
            "reset_at_epoch": reset_at,
        }, binding

    def schedule(
        self, request: Mapping[str, Any], *, _held_thread_lock=None, _held_target_lock=None, _not_before_epoch: int | None = None
    ) -> dict[str, Any]:
        payload_path: pathlib.Path | None = None
        plist_path: pathlib.Path | None = None
        wake_dir: pathlib.Path | None = None
        label: str | None = None
        bootstrapped = False
        carrier_sentinel: pathlib.Path | None = None
        wake_lock = None
        thread_lock = _held_thread_lock
        owns_thread_lock = _held_thread_lock is None
        target_lock = _held_target_lock
        owns_target_lock = _held_target_lock is None
        spent_pair_cleared = False
        armed_ok = False
        try:
            self._prune_terminal_wake_receipts()
            repair = self._repair_pending_carrier_receipts()
            if repair:
                raise ValueError(repair)
            identity, runtime = self._validate(request)
            fire_epoch, calendar = compute_unique_launchd_minute(
                identity["reset_at_epoch"], timezone=self._timezone,
                not_before_epoch=_not_before_epoch,
            )
            if fire_epoch <= int(self._clock()):
                raise ValueError("scheduled launchd minute is already in the past")
            if next_launchd_occurrence(
                calendar, after_epoch=int(self._clock()), timezone=self._timezone
            ) != fire_epoch:
                raise ValueError("next launchd calendar occurrence does not match the scheduled epoch")
            identity.update(runtime)
            identity["scheduled_epoch"] = fire_epoch
            identity["calendar"] = calendar
            identity["runtime_script"] = str(pathlib.Path(__file__).resolve())
            identity["runtime_python"] = str(pathlib.Path(sys.executable).resolve())
            # Refuse a known armed/queued competitor before taking the shared
            # target reservation. Otherwise a fire of that existing carrier can
            # mistake this refusal-only lock hold for a successful takeover.
            preflight_unresolved = self._existing_message_blocks_arm(identity, include_armed=True)
            if preflight_unresolved:
                raise ValueError(preflight_unresolved)
            carrier_key = hashlib.sha256((identity["repo_root"] + "\0" + identity["thread_id"]).encode("utf-8")).hexdigest()[:16]
            identity["sentinel_path"] = str(self._state_dir / "codex-quota-wakes" / f"wake-{carrier_key}.sentinel")
            carrier_sentinel = pathlib.Path(identity["sentinel_path"])
            if thread_lock is None:
                thread_lock = self._acquire_thread_wake_lock(identity)
            if thread_lock is None:
                raise ValueError("same-thread quota wake admission already claimed")
            if target_lock is None:
                target_lock = self._acquire_target_wake_lock(identity)
            if target_lock is None:
                raise ValueError("same-target quota wake admission already claimed")
            if not pathlib.Path(identity["runtime_python"]).is_file() or not os.access(identity["runtime_python"], os.X_OK):
                raise ValueError("runtime Python must be an absolute runnable file")
            canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(canonical).hexdigest()
            wake_dir = self._state_dir / "codex-quota-wakes" / digest[:16]
            wake_dir.mkdir(parents=True, exist_ok=True)
            wake_lock = (wake_dir / "fire.lock").open("a+")
            try:
                fcntl.flock(wake_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                wake_lock.close()
                wake_lock = None
                raise ValueError("same-wake quota wake admission already claimed")
            locked_identity, locked_runtime = self._validate(request)
            core_identity = {key: identity[key] for key in ("thread_id", "repo_root", "target", "kind", "phase", "reset_at_epoch")}
            if locked_identity != core_identity or locked_runtime != runtime:
                raise ValueError("quota wake identity changed while acquiring scoped locks")
            locked_identity.update(locked_runtime)
            locked_fire_epoch, locked_calendar = compute_unique_launchd_minute(
                locked_identity["reset_at_epoch"], timezone=self._timezone,
                not_before_epoch=_not_before_epoch,
            )
            if locked_fire_epoch != fire_epoch or locked_calendar != calendar:
                raise ValueError("quota wake calendar changed while acquiring scoped locks")
            admission = dict(self._schedule_guard(locked_identity))
            if not admission.get("ready"):
                detail = f": {admission['detail']}" if admission.get("detail") else ""
                raise ValueError(f"schedule admission changed under lock: {admission.get('reason', 'unknown')}{detail}")
            unresolved = self._existing_message_blocks_arm(identity, include_armed=True)
            if unresolved:
                raise ValueError(unresolved)
            payload_path = wake_dir / "payload.json"
            label = f"ai-playbook.codex-quota-wake.{digest[:12]}"
            plist_path = launchd_plist_path(wake_dir, label)
            verified_arm_path = wake_dir / "verified-arm.json"
            verified_arm_path.unlink(missing_ok=True)
            if verified_arm_path.exists():
                raise ValueError("stale verified-arm marker could not be removed")
            payload = dict(identity, payload_digest=digest, label=label)
            carrier_marker = fired_marker_path(carrier_sentinel)
            if carrier_sentinel.exists() and not carrier_marker.exists():
                raise ValueError("an unspent carrier sentinel blocks a new quota wake arm")
            if carrier_marker.exists():
                try:
                    carrier_sentinel.unlink(missing_ok=True)
                except OSError as exc:
                    self._restore_spent_pair(carrier_sentinel)
                    raise ValueError("spent carrier sentinel cleanup could not be verified") from exc
                if carrier_sentinel.exists():
                    self._restore_spent_pair(carrier_sentinel)
                    raise ValueError("spent carrier sentinel cleanup could not be verified")
                try:
                    carrier_marker.unlink(missing_ok=True)
                except OSError as exc:
                    self._restore_spent_pair(carrier_sentinel)
                    raise ValueError("spent carrier marker cleanup could not be verified") from exc
                if carrier_marker.exists():
                    self._restore_spent_pair(carrier_sentinel)
                    raise ValueError("spent carrier marker cleanup could not be verified")
                spent_pair_cleared = True
            wake_dir.mkdir(parents=True, exist_ok=True)
            payload_tmp = payload_path.with_suffix(".json.tmp")
            payload_tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(payload_tmp, payload_path)
            arm_receipt_path = wake_dir / "arm-receipt.json"
            _atomic_json_write(arm_receipt_path, {"payload_digest": digest, "payload": payload})
            arguments = [
                payload["runtime_python"],
                payload["runtime_script"],
                "--operation",
                "codex-quota-wake-fire",
                "--input",
                json.dumps({"payload_path": str(payload_path), "expected_fire_epoch": fire_epoch}, separators=(",", ":")),
                "--repo-root",
                payload["repo_root"],
            ]
            plist = {
                "Label": label,
                "ProgramArguments": arguments,
                "StartCalendarInterval": calendar,
                "EnvironmentVariables": {"CODEX_HOME": payload["codex_home"]},
                "StandardOutPath": str(wake_dir / "fire.out.log"),
                "StandardErrorPath": str(wake_dir / "fire.err.log"),
            }
            plist_tmp = plist_path.with_suffix(".plist.tmp")
            with plist_tmp.open("wb") as handle:
                plistlib.dump(plist, handle)
            os.replace(plist_tmp, plist_path)
            loaded, detail = self._bootstrap(plist_path)
            if not loaded:
                raise ValueError(f"launchd bootstrap failed: {detail}")
            bootstrapped = True
            verified, detail = self._verify_loaded(label)
            if not verified:
                raise ValueError(f"launchd loaded-label verification failed: {detail}")
            persisted_plist = plistlib.loads(plist_path.read_bytes())
            if persisted_plist != plist:
                raise ValueError("launchd plist read-back did not match the requested date and command")
            persisted_payload = json.loads(payload_path.read_text(encoding="utf-8"))
            if persisted_payload != payload or persisted_payload.get("payload_digest") != digest:
                raise ValueError("Codex quota wake payload read-back did not match its identity")
            persisted_arm_receipt = json.loads(arm_receipt_path.read_text(encoding="utf-8"))
            if persisted_arm_receipt != {"payload_digest": digest, "payload": payload}:
                raise ValueError("Codex quota wake arm receipt read-back did not match its identity")
            _atomic_json_write(verified_arm_path, {
                "payload_digest": digest,
                "label": label,
                "fire_epoch": fire_epoch,
                "verified_at_epoch": int(self._clock()),
            })
            armed_ok = True
            return {
                "scheduled": True,
                "mechanism": "launchd",
                "label": label,
                "fire_epoch": fire_epoch,
                "calendar": calendar,
                "payload_path": str(payload_path),
                "plist_path": str(plist_path),
                "payload_digest": digest,
                "runtime": runtime,
            }
        except (OSError, ValueError, TypeError, KeyError) as exc:
            cleanup = None
            if wake_dir is not None:
                try:
                    (wake_dir / "verified-arm.json").unlink(missing_ok=True)
                    if (wake_dir / "verified-arm.json").exists():
                        cleanup = "verified-arm marker could not be invalidated"
                except OSError as marker_error:
                    cleanup = f"verified-arm marker cleanup could not be verified: {marker_error}"
            if plist_path is not None and plist_path.exists():
                if bootstrapped:
                    try:
                        self._bootout(plist_path)
                        still_loaded, detail = self._verify_loaded(label or "")
                        if still_loaded:
                            cleanup = f"launchd job may remain loaded: {detail}"
                        else:
                            plist_path.unlink(missing_ok=True)
                    except (OSError, ValueError, TypeError) as cleanup_error:
                        cleanup = f"launchd cleanup could not be verified: {cleanup_error}"
                else:
                    try:
                        plist_path.unlink(missing_ok=True)
                    except OSError as cleanup_error:
                        cleanup = f"unloaded plist cleanup failed: {cleanup_error}"
            if wake_dir is not None:
                for temporary in (wake_dir / "payload.json.tmp", wake_dir / f"{label}.plist.tmp"):
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
            if spent_pair_cleared and not armed_ok and carrier_sentinel is not None:
                self._restore_spent_pair(carrier_sentinel)
            result = {"scheduled": False, "mechanism": "launchd", "reason": str(exc)}
            if payload_path is not None and payload_path.is_file():
                result["payload_path"] = str(payload_path)
            if cleanup:
                result["cleanup"] = cleanup
            return result
        finally:
            if wake_lock is not None:
                try:
                    fcntl.flock(wake_lock.fileno(), fcntl.LOCK_UN)
                finally:
                    wake_lock.close()
            if owns_target_lock:
                self._release_target_wake_lock(target_lock)
            if owns_thread_lock:
                self._release_thread_wake_lock(thread_lock)


class ReportOnlyScheduler(SchedulerAdapter):
    """Terminal fallback: name the exact manual resume command and time."""

    def schedule(self, request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "scheduled": False,
            "mechanism": "report-only",
            "manual_command": request.get("manual_command"),
            "resume_at_iso": request.get("resume_at_iso"),
        }


def schedule_with_fallback(chain: Sequence[SchedulerAdapter], request: Mapping[str, Any]) -> dict[str, Any]:
    """Run the pause-protocol fallback chain; report-only is terminal."""

    trail: list[dict[str, Any]] = []
    for scheduler in chain:
        result = dict(scheduler.schedule(request))
        trail.append(result)
        if result.get("scheduled"):
            return {"scheduled": True, "mechanism": result.get("mechanism"), "trail": trail, "result": result}
        if result.get("mechanism") == "report-only":
            return {"scheduled": False, "mechanism": "report-only", "trail": trail, "result": result}
    last = trail[-1] if trail else {}
    return {"scheduled": False, "mechanism": last.get("mechanism"), "trail": trail, "result": last}


def launchd_refusal_reason(scheduling: Mapping[str, Any]) -> str | None:
    """The chain's launchd link refusal reason, or None (r6 F5).

    Reads the per-scheduler trail a fallback chain produced: the entry whose
    mechanism is ``launchd`` carries its own ``reason`` when it refused to
    arm (sentinel self-disable, spent-pair cleanup refusal, label conflict,
    plist write failure, bootstrap failure). None when the trail has no
    launchd entry or the entry scheduled.
    """

    for entry in scheduling.get("trail") or ():
        if isinstance(entry, Mapping) and entry.get("mechanism") == "launchd":
            reason = entry.get("reason")
            return str(reason) if reason else None
    return None


# Production invocation defaults for the CLI watcher operations (r1 F5):
# the launchd one-shot fallback and the report-only terminal link live in
# this module; the orchestrator-owned automation create stays the first
# link of the pause-protocol chain and is echoed into the CLI when it
# already succeeded. The tilde is expanded at import time (r2 F4 follow-up):
# a literal "~" in a pathlib default never expands, so an arm under the
# defaults wrote the job plist into a "./~" directory under the caller's
# working directory and bootstrapped launchd with that repo-relative path.
DEFAULT_LAUNCHD_JOB_DIR = pathlib.Path("~/.ai-playbook/runtime/launchd").expanduser()
DEFAULT_RESUME_SENTINEL = pathlib.Path("~/.ai-playbook/runtime/budget-resume.sentinel").expanduser()


def resolve_launchd_identity(
    job_dir: os.PathLike | str | None,
    sentinel_path: os.PathLike | str | None,
    plan_slug: str | None,
    repo_root: str | None,
) -> dict[str, str]:
    """The one launchd-identity derivation for the CLI watcher arms (r4 F3).

    The identity is keyed per run whenever EITHER path is left at its
    default: a half-custom payload that named only one explicit path used
    to fall back to the shared unkeyed identity for both, so a second run's
    arm silently overwrote and bootout the first run's loaded job without a
    label-conflict refusal. A caller that brings both paths explicitly
    keeps the unkeyed identity for them, and with no identity inputs (plan
    slug and repository root both absent) the defaults stay shared. Both
    the scheduler chain and the schedule arm derive through this helper so
    the armed job, the armed sentinel, and the receipt's recorded identity
    cannot drift.
    """

    identity = default_launchd_identity(plan_slug, repo_root) if (plan_slug or repo_root) else None
    both_explicit = job_dir is not None and sentinel_path is not None
    if identity is not None and not both_explicit:
        return {
            "job_dir": str(job_dir) if job_dir is not None else identity["job_dir"],
            "sentinel_path": str(sentinel_path) if sentinel_path is not None else identity["sentinel_path"],
            "label": identity["label"],
        }
    return {
        "job_dir": str(job_dir) if job_dir is not None else str(DEFAULT_LAUNCHD_JOB_DIR),
        "sentinel_path": str(sentinel_path) if sentinel_path is not None else str(DEFAULT_RESUME_SENTINEL),
        "label": "ai-playbook.budget-resume",
    }


def cli_scheduler_chain(
    automation_result: Mapping[str, Any] | None = None,
    job_dir: os.PathLike | str | None = None,
    sentinel_path: os.PathLike | str | None = None,
    plan_slug: str | None = None,
    repo_root: str | None = None,
    resolved_identity: Mapping[str, Any] | None = None,
) -> list[SchedulerAdapter]:
    """The CLI pause-protocol fallback chain (r1 F5).

    When ``automation_result`` carries an already-successful orchestrator
    automation create, the chain echoes it as the scheduled mechanism so no
    launchd job is armed on top of it; otherwise the chain is the launchd
    one-shot fallback, then report-only naming the exact manual command.
    With a plan slug and repository root (r3 F14) the launchd identity is
    keyed per run whenever either path is left at its default (r4 F3, the
    shared :func:`resolve_launchd_identity` derivation); a caller that
    brings both an explicit job dir and sentinel keeps the unkeyed identity
    for those paths. The arm path passes ``resolved_identity`` (r6 F7): the
    schedule arm resolves the identity once and the chain consumes exactly
    that resolution, so the receipt's recorded carrier and the scheduler's
    armed carrier cannot disagree; without it the chain derives through the
    same shared helper for direct callers.
    """

    resolved = (
        {str(key): str(value) for key, value in resolved_identity.items()}
        if isinstance(resolved_identity, Mapping) and {"job_dir", "sentinel_path", "label"} <= set(resolved_identity)
        else resolve_launchd_identity(job_dir, sentinel_path, plan_slug, repo_root)
    )
    chain: list[SchedulerAdapter] = []
    if isinstance(automation_result, Mapping):
        chain.append(AutomationScheduler(lambda _request: dict(automation_result)))
    chain.append(
        LaunchdOneShotScheduler(
            resolved["job_dir"],
            resolved["sentinel_path"],
            label=resolved["label"],
            fail_closed_on_lock_unavailable=_budget_resume_family_label(resolved["label"]),
        )
    )
    chain.append(ReportOnlyScheduler())
    return chain


def fired_marker_path(sentinel_path: os.PathLike | str) -> pathlib.Path:
    """The one-shot's fired marker: next to its sentinel (r3 F16).

    The one name for the spent-one-shot handshake (r4 F17): the scheduler's
    guard and watcher-fire's marker write derive the same path through this
    helper, so the re-arm handshake cannot drift.
    """

    sentinel = pathlib.Path(os.path.expanduser(str(sentinel_path)))
    return sentinel.with_name(sentinel.name + ".fired")


def consume_resume_sentinel(sentinel_path: os.PathLike | str, fired_path: os.PathLike | str | None = None) -> dict[str, Any]:
    """Consume the launchd one-shot sentinel on a terminal fire decision.

    watcher-fire removes the sentinel and writes the fired marker next to it
    (r3 F16): the still-loaded daily job's fired-marker guard keeps every
    later calendar fire inert, the fire decision is marked as reached (so a
    sentinel left behind is unambiguous evidence of a fire that never
    decided), and the next window's arm clears the spent pair and re-arms.
    A missing sentinel means launchd armed nothing; the marker write is then
    skipped so a stale marker can never outlive its window. The fired-marker
    path is the receipt's ``armed_launchd.fired_marker_path`` when the
    caller supplies one (G2: the receipt is the sole carrier-identity
    source); direct callers without one get the same name derived beside the
    sentinel, which is where the arm wrote it.
    """

    sentinel = pathlib.Path(os.path.expanduser(str(sentinel_path)))
    fired = pathlib.Path(os.path.expanduser(str(fired_path))) if fired_path is not None else fired_marker_path(sentinel)
    if not sentinel.exists():
        return {"consumed": False, "reason": "sentinel-absent", "sentinel": str(sentinel)}
    try:
        fired.write_text(f"{datetime.now().astimezone().isoformat()}\n", encoding="utf-8")
    except OSError:
        pass
    try:
        sentinel.unlink()
    except OSError:
        pass
    return {"consumed": True, "sentinel": str(sentinel), "fired": str(fired)}


def consume_resume_sentinel_scoped(
    sentinel_path: os.PathLike | str,
    fired_path: os.PathLike | str | None = None,
    *,
    cleanup_dir: os.PathLike | str | None = None,
) -> dict[str, Any]:
    """The sanctioned-directory scoped consume (r6 F6).

    The fire payload's explicit ``sentinel_path`` override is an
    operator-supplied path, so its unlink is scoped exactly like the
    scheduler's spent-pair cleanup (r5 F13): a path outside the sanctioned
    runtime directory (the keyed default directory
    :func:`resolve_launchd_identity` derives into, or the caller-supplied
    ``cleanup_dir``) is refused with nothing consumed and no marker written,
    so a wrong explicit path can never consume or mark the wrong pair.
    """

    sentinel = pathlib.Path(os.path.expanduser(str(sentinel_path)))
    sanctioned = pathlib.Path(os.path.expanduser(str(cleanup_dir))) if cleanup_dir is not None else DEFAULT_RESUME_SENTINEL.parent
    refused = {"consumed": False, "reason": "sentinel override outside the sanctioned runtime directory is refused", "sentinel": str(sentinel)}
    try:
        if pathlib.Path(os.path.realpath(sentinel)).parent != pathlib.Path(os.path.realpath(sanctioned)):
            return refused
    except OSError:
        return refused
    return consume_resume_sentinel(sentinel, fired_path=fired_path)


def _carrier_watcher_segment(payload_command: str) -> Optional[str]:
    """The embedded arm-unique discriminator in a carrier payload, or None.

    The budget-resume arm appends a fixed-marker no-op trailing segment
    (``; : <watcher_id>``) after the manual resume command, so the
    discriminator is always the last ``shlex.split`` token with ``:`` right
    before it. The parse is strictly positional (plan
    2026-11-06-budget-resume-carrier-gc Task 3): a legacy payload that
    happens to contain a fake segment string mid-command is never matched,
    because only the fixed trailing position is read.
    """

    try:
        tokens = shlex.split(payload_command)
    except ValueError:
        return None
    if len(tokens) >= 2 and tokens[-2] == ":" and tokens[-1] != ":":
        return tokens[-1]
    return None


def _realpath_inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    """Whether ``path`` realpath-resolves inside ``root`` (containment scope)."""

    try:
        return pathlib.Path(os.path.realpath(path)) == pathlib.Path(os.path.realpath(root)) or pathlib.Path(
            os.path.realpath(path)
        ).is_relative_to(pathlib.Path(os.path.realpath(root)))
    except OSError:
        return False


def supersede_carrier_teardown(
    receipt: Mapping[str, Any],
    *,
    own_watcher_id: Optional[str] = None,
    enforce_ownership: bool = False,
    legacy_on_unverifiable: str = "teardown",
    use_lock: bool = False,
    require_bootout_pass: bool = False,
    remove_logs: bool = False,
    remove_job_dir: bool = False,
    launchd_root: os.PathLike | str | None = None,
    runtime_root: os.PathLike | str | None = None,
) -> dict[str, Any]:
    """Tear down the outgoing receipt's armed launchd carrier (r6 F3).

    A supersede that clears a watcher whose receipt records an armed
    carrier must tear that carrier down in the same operation: the
    recorded plist is booted out (best-effort, the shared bootout
    primitive) and the recorded sentinel/fired pair is consumed, so the
    orphan job's later fire can no longer write a bare sentinel that
    refuses every subsequent arm and silently reverts automated resume to
    manual. Receipt-only (G2): both paths come from the receipt's
    ``armed_launchd`` record and no identity is derived. A receipt without
    a carrier record, or one recording ``armed: false`` (an automation
    echo), tears nothing down.

    Hardened shared core (plan 2026-11-06-budget-resume-carrier-gc Task 3):
    the plist unlink is scoped to the launchd job-dir root and the sentinel
    consume switched to the scoped variant for every caller (the named
    intended deltas), so an explicit-path receipt outside the sanctioned
    roots refuses those legs with named reasons while the bootout still
    runs. The keyword parameters keep the three existing supersede call
    sites' present bootout-outcome-gate and log-leg semantics at their
    legacy defaults; the discharge passes the enforcing values (ownership gate
    against the receipt's ``watcher_id``, the budget-guard lock, the
    bootout-outcome gate, the log and job-dir legs).
    """

    teardown: dict[str, Any] = {}
    armed = receipt.get("armed_launchd") if isinstance(receipt.get("armed_launchd"), Mapping) else None
    if armed is None or armed.get("armed") is not True:
        teardown["torn_down"] = False
        return teardown
    launcher = pathlib.Path(os.path.expanduser(str(launchd_root))) if launchd_root is not None else DEFAULT_LAUNCHD_JOB_DIR
    runtime = pathlib.Path(os.path.expanduser(str(runtime_root))) if runtime_root is not None else DEFAULT_RESUME_SENTINEL.parent
    sentinel_path = armed.get("sentinel_path")

    def _refuse(reason: str) -> dict[str, Any]:
        teardown["torn_down"] = False
        teardown["retained_reason"] = reason
        return teardown

    def _refuse(reason: str) -> dict[str, Any]:
        teardown["torn_down"] = False
        teardown["retained_reason"] = reason
        return teardown

    def _teardown_body() -> dict[str, Any]:
        # The discharge holds the budget-guard lock derived from the receipt's
        # sentinel path ACROSS its destructive legs (plan Task 2): the lock
        # wraps the ownership check, the bootout, and every unlink/consume/rm
        # leg, so a fail-closed re-arm cannot slip in at the shared identity
        # mid-teardown. The shared core takes no lock of its own without this
        # parameter.

        plist_path = armed.get("plist_path")
        job: Optional[pathlib.Path] = None
        if isinstance(plist_path, str) and plist_path.strip():
            job = pathlib.Path(os.path.expanduser(plist_path))
        if enforce_ownership and job is not None and job.exists():
            try:
                data = plistlib.loads(job.read_bytes())
                arguments = data.get("ProgramArguments") if isinstance(data, Mapping) else None
                command = str(arguments[2]) if isinstance(arguments, (list, tuple)) and len(arguments) >= 3 else ""
            except (OSError, ValueError):
                command = ""
            embedded = _carrier_watcher_segment(command) if command else None
            if embedded is None:
                if legacy_on_unverifiable != "teardown":
                    return _refuse("legacy-unverifiable")
            elif own_watcher_id is None:
                if legacy_on_unverifiable != "teardown":
                    return _refuse("legacy-unverifiable")
            elif embedded != own_watcher_id:
                return _refuse("carrier-mismatch-retained")
        teardown["torn_down"] = True
        bootout_ok = True  # no bootout ran: no loaded job the marker must guard
        if job is not None:
            teardown["bootout"] = launchctl_bootout(job)
            bootout_ok = dict(teardown["bootout"]).get("exited") == 0
            booted = dict(teardown["bootout"])
            if booted.get("exited") not in (0, None):
                label = armed.get("label")
                loaded = read_loaded_labels()
                not_loaded = isinstance(label, str) and bool(label) and label not in loaded
                if require_bootout_pass and not not_loaded:
                    # The bootout-outcome gate (plan Task 2): a nonzero bootout
                    # is only survivable when the label is confirmed absent from
                    # the loaded view (not-loaded); anything else is ambiguous
                    # and retains the guards.
                    return _refuse("carrier-retained-ambiguous-bootout")
                bootout_ok = not_loaded
            if _realpath_inside(job, launcher):
                try:
                    job.unlink()
                except OSError:
                    pass
            else:
                teardown["plist_unlink_refused"] = "plist path outside the launchd job-dir root is refused"
        if isinstance(sentinel_path, str) and sentinel_path.strip():
            fired_marker = armed.get("fired_marker_path")
            derived = fired_marker_path(sentinel_path)
            if isinstance(fired_marker, str) and fired_marker.strip() and pathlib.Path(os.path.expanduser(fired_marker)) != derived:
                teardown["sentinel"] = {"consumed": False, "reason": "fired-marker path deviates from the sentinel derivation", "sentinel": str(sentinel_path)}
            elif not _realpath_inside(pathlib.Path(os.path.expanduser(sentinel_path)), runtime):
                teardown["sentinel"] = {"consumed": False, "reason": "sentinel outside the sanctioned runtime directory is refused", "sentinel": str(sentinel_path)}
            else:
                teardown["sentinel"] = consume_resume_sentinel_scoped(
                    sentinel_path,
                    fired_path=fired_marker if isinstance(fired_marker, str) and fired_marker.strip() else None,
                    cleanup_dir=runtime,
                )
                # The consume primitive re-creates the fired marker when it
                # wrote one, so the leftover marker is removed only after the
                # consume (plan 2026-11-06-budget-resume-carrier-gc Task 2),
                # keeping the one-shot's inert guard honest on a discharge
                # where the job is gone.
                if teardown["sentinel"].get("consumed") and bootout_ok:
                    # The consume primitive re-creates the fired marker when it
                    # wrote one, so the leftover marker is removed only after
                    # the consume (plan Task 2) - and only when the bootout
                    # outcome says no orphan job is still loaded: the marker is
                    # that job's inert guard, so removing it on a failed or
                    # ambiguous bootout would let the orphan's next calendar
                    # fire execute the resume command into a dead context.
                    try:
                        derived.unlink()
                        teardown["sentinel"]["leftover_fired_marker_removed"] = True
                    except OSError:
                        pass
                if remove_logs and isinstance(armed.get("label"), str) and armed.get("label"):
                    job_dir = armed.get("job_dir")
                    label = str(armed["label"])
                    if isinstance(job_dir, str) and job_dir.strip():
                        for suffix in (".out.log", ".err.log"):
                            log_path = pathlib.Path(os.path.expanduser(job_dir)) / f"{label}{suffix}"
                            if _realpath_inside(log_path, launcher):
                                try:
                                    log_path.unlink()
                                except OSError:
                                    pass
                if remove_job_dir and isinstance(armed.get("job_dir"), str) and armed.get("job_dir").strip():
                    keyed_dir = pathlib.Path(os.path.expanduser(armed["job_dir"]))
                    if re.fullmatch(r"[0-9a-f]{12}", keyed_dir.name) and _realpath_inside(keyed_dir, launcher):
                        try:
                            keyed_dir.rmdir()
                            teardown["job_dir_removed"] = True
                        except OSError:
                            teardown["job_dir_removed"] = False
                    else:
                        teardown["job_dir_removed"] = False
                        teardown["job_dir_refused"] = "job dir outside the launchd job-dir root or not keyed is refused"
        return teardown



    # The discharge holds the budget-guard lock derived from the receipt's
    # sentinel path ACROSS its destructive legs (plan Task 2): the lock
    # wraps the ownership check, the bootout, and every unlink/consume/rm
    # leg, so a fail-closed re-arm cannot slip in at the shared identity
    # mid-teardown. The shared core takes no lock of its own without this
    # parameter.
    if use_lock:
        if not (isinstance(sentinel_path, str) and sentinel_path.strip()):
            return _refuse("lock-unavailable-retained")
        with budget_guard_lock(sentinel_path) as acquired:
            if not acquired:
                return _refuse("lock-unavailable-retained")
            return _teardown_body()
    return _teardown_body()


def read_loaded_labels() -> set[str]:
    """The launchd loaded-label view: labels from ``launchctl list`` output.

    The one module-level loaded-label read primitive the census and the
    bootout-outcome gate call (plan 2026-11-06-budget-resume-carrier-gc
    Task 1); injectable for tests by patching this module attribute. A
    failing read yields an empty set (the census reports the loaded view
    as unavailable rather than inventing rows).
    """

    try:
        completed = subprocess.run(
            ["launchctl", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    labels: set[str] = set()
    for line in completed.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[-1].strip():
            labels.add(parts[-1].strip())
    return labels


BUDGET_RESUME_LABEL_ROOT = "ai-playbook.budget-resume"
BUDGET_RESUME_LEGACY_LABEL = BUDGET_RESUME_LABEL_ROOT


def _budget_resume_family_label(label: Any) -> bool:
    """Whether a label names a budget-resume-family carrier."""

    if not isinstance(label, str) or not label:
        return False
    return label == BUDGET_RESUME_LEGACY_LABEL or label.startswith(BUDGET_RESUME_LABEL_ROOT + ".")


def _sentinel_report_state(sentinel: pathlib.Path, runtime: pathlib.Path) -> dict[str, Any]:
    """Read the sentinel/fired state for one carrier from the runtime root."""

    state: dict[str, Any] = {"sentinel_path": str(sentinel), "sentinel": sentinel.exists()}
    fired = fired_marker_path(sentinel)
    state["fired_marker_path"] = str(fired)
    state["fired"] = fired.exists()
    return state


def budget_carrier_census(
    job_dir: os.PathLike | str | None = None,
    runtime_root: os.PathLike | str | None = None,
    loaded_labels: Optional[set[str]] = None,
) -> dict[str, Any]:
    """The read-only budget-resume carrier census (plan Task 1).

    Enumerates every budget-resume-family carrier under the runtime launchd
    job dir (keyed 12-hex job dirs and legacy flat plists) plus the loaded
    label view, plus the sentinel-only source read from the runtime root
    (sentinels and their fired markers live beside the job dirs, not inside
    them). Foreign-family co-tenants such as clocked-order carriers are
    excluded as co-tenants, never census rows; a corrupt plist yields a
    per-carrier error row while healthy carriers still report; the census
    never repairs and never writes.
    """

    launcher = pathlib.Path(os.path.expanduser(str(job_dir))) if job_dir is not None else DEFAULT_LAUNCHD_JOB_DIR
    runtime = pathlib.Path(os.path.expanduser(str(runtime_root))) if runtime_root is not None else DEFAULT_RESUME_SENTINEL.parent
    loaded = set(loaded_labels) if loaded_labels is not None else read_loaded_labels()
    rows: list[dict[str, Any]] = []
    seen_labels: set[str] = set()

    def _plist_label(path: pathlib.Path) -> tuple[Optional[str], Optional[str]]:
        try:
            data = plistlib.loads(path.read_bytes())
        except (OSError, ValueError) as exc:
            return None, f"unreadable plist {path.name}: {exc}"
        label = data.get("Label") if isinstance(data, Mapping) else None
        return (str(label) if isinstance(label, str) else None), None

    if launcher.is_dir():
        # Keyed job dirs: filtered to the 12-hex key shape; the label is
        # read from each candidate plist's Label key, never from the name.
        for entry in sorted(launcher.iterdir()):
            if not entry.is_dir() or not re.fullmatch(r"[0-9a-f]{12}", entry.name):
                continue
            dir_row_base = {"source": "keyed", "job_dir": str(entry)}
            plists = sorted(entry.glob("*.plist"))
            label: Optional[str] = None
            error: Optional[str] = None
            plist_path: Optional[pathlib.Path] = None
            for candidate in plists:
                candidate_label, candidate_error = _plist_label(candidate)
                if candidate_error:
                    error = candidate_error
                    continue
                if candidate_label and _budget_resume_family_label(candidate_label):
                    label, plist_path = candidate_label, candidate
                    break
            if label is None:
                logs_only = sorted(entry.glob("*.log"))
                if logs_only:
                    rows.append({**dir_row_base, "label": None, "loaded": False, "note": "logs-only job dir (no budget-resume plist)", "error": error})
                elif error:
                    rows.append({**dir_row_base, "label": None, "loaded": False, "error": error})
                continue
            seen_labels.add(label)
            sentinel = runtime / f"{DEFAULT_RESUME_SENTINEL.stem}-{entry.name}{DEFAULT_RESUME_SENTINEL.suffix}"
            rows.append({
                **dir_row_base,
                "label": label,
                "plist": str(plist_path),
                "loaded": label in loaded,
                **_sentinel_report_state(sentinel, runtime),
                **({"error": error} if error else {}),
            })
        # Legacy flat plists sit in the shared flat root; reported as
        # census rows when family-labeled, never removed.
        for candidate in sorted(launcher.glob("*.plist")):
            label, error = _plist_label(candidate)
            if error:
                rows.append({"source": "legacy", "label": None, "loaded": False, "error": error})
                continue
            if label and _budget_resume_family_label(label):
                seen_labels.add(label)
                rows.append({
                    "source": "legacy",
                    "label": label,
                    "plist": str(candidate),
                    "loaded": label in loaded,
                    **_sentinel_report_state(runtime / DEFAULT_RESUME_SENTINEL.name, runtime),
                })
    # Loaded labels with no plist anywhere: plist-less loaded records.
    for label in sorted(loaded):
        if _budget_resume_family_label(label) and label not in seen_labels:
            seen_labels.add(label)
            rows.append({"source": "loaded", "label": label, "loaded": True, "note": "loaded label with no plist"})
    # Sentinel-only carriers: a sentinel (or its fired marker) whose job
    # dir is already gone, reported from the runtime-root sentinel state.
    for candidate in sorted(runtime.glob(f"{DEFAULT_RESUME_SENTINEL.stem}*{DEFAULT_RESUME_SENTINEL.suffix}")):
        name = candidate.name
        legacy_form = name == DEFAULT_RESUME_SENTINEL.name
        keyed_form = re.fullmatch(rf"{re.escape(DEFAULT_RESUME_SENTINEL.stem)}-[0-9a-f]{{12}}{DEFAULT_RESUME_SENTINEL.suffix}", name)
        if not (legacy_form or keyed_form):
            continue
        key = name[len(DEFAULT_RESUME_SENTINEL.stem) + 1 : -len(DEFAULT_RESUME_SENTINEL.suffix)] if keyed_form else ""
        label = f"{BUDGET_RESUME_LABEL_ROOT}.{key}" if key else BUDGET_RESUME_LEGACY_LABEL
        # One row per carrier: a sentinel whose keyed job dir still exists
        # (or whose legacy flat plist row was already reported) is that
        # live carrier's sentinel, not a sentinel-only carrier - the
        # keyed/legacy enumeration already reported its state.
        if keyed_form and (launcher / key).is_dir():
            continue
        if legacy_form and label in seen_labels:
            continue
        if candidate.exists() or fired_marker_path(candidate).exists():
            if label in seen_labels:
                continue
            seen_labels.add(label)
            rows.append({
                "source": "sentinel-only",
                "label": label,
                "loaded": label in loaded,
                "note": "sentinel-only carrier (job dir gone)",
                **_sentinel_report_state(candidate, runtime),
            })
    return {"census": rows, "loaded_view_available": bool(loaded) or loaded_labels is not None}


def budget_carrier_discharge_for_state(
    state_path: os.PathLike | str,
    *,
    launchd_root: os.PathLike | str | None = None,
    runtime_root: os.PathLike | str | None = None,
    loaded_labels: Optional[set[str]] = None,
) -> dict[str, Any]:
    """Discharge a run's own armed carrier from its machine state (plan Task 2).

    Receipt-only input: the run's own ``resume_watcher`` record read from
    the machine-state JSON through the plans-watcher record pattern; when
    that record is null because the run's own fire-resume supersede cleared
    it, the discharge falls back to the latest fired supersede history
    event's retained ``armed_launchd`` fields. A state with neither tears
    nothing down.
    """

    state_file = pathlib.Path(os.path.expanduser(str(state_path)))
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"discharged": False, "retained_reason": f"unreadable machine state: {exc}"}
    if not isinstance(state, Mapping):
        return {"discharged": False, "retained_reason": "unreadable machine state: not a JSON object"}
    armed: Optional[Mapping[str, Any]] = None
    watcher_id: Optional[str] = None
    record = state.get("resume_watcher")
    if isinstance(record, Mapping):
        candidate = record.get("armed_launchd")
        if isinstance(candidate, Mapping) and candidate.get("armed") is True:
            armed = candidate
            watcher_id = str(record.get("watcher_id") or "") or None
    if armed is None:
        for event in reversed(state.get("history") or []):
            if not isinstance(event, Mapping) or event.get("event") != "resume-watcher-superseded":
                continue
            candidate = event.get("armed_launchd")
            if isinstance(candidate, Mapping) and candidate.get("armed") is True:
                armed = candidate
                watcher_id = str(event.get("watcher_id") or "") or None
                break
    if armed is None:
        return {"discharged": False, "retained_reason": "no armed_launchd record"}
    receipt = {"armed_launchd": dict(armed)}
    return supersede_carrier_teardown(
        receipt,
        own_watcher_id=watcher_id,
        enforce_ownership=True,
        legacy_on_unverifiable="retain",
        use_lock=True,
        require_bootout_pass=True,
        remove_logs=True,
        remove_job_dir=True,
        launchd_root=launchd_root,
        runtime_root=runtime_root,
    )


# ---------------------------------------------------------------------------
# Watcher state machine (workflow-neutral)
# ---------------------------------------------------------------------------


def current_watcher_id(snapshot: Mapping[str, Any]) -> Optional[str]:
    watcher = snapshot.get("resume_watcher")
    if isinstance(watcher, Mapping):
        value = watcher.get("watcher_id")
        return str(value) if isinstance(value, str) and value.strip() else None
    return None


def fence_mismatches(snapshot: Mapping[str, Any], receipt: Mapping[str, Any]) -> list[str]:
    """Pre-fire fence: id, generation, state, root, plan path, digest, boundary."""

    mismatches: list[str] = []
    if current_watcher_id(snapshot) != receipt.get("watcher_id"):
        mismatches.append("watcher-id")
    if int(snapshot.get("generation", 0)) != int(receipt.get("expected_generation", 0)):
        mismatches.append("generation")
    if int(snapshot.get("boundary_generation", 0)) != int(receipt.get("boundary_generation", 0)):
        mismatches.append("boundary-generation")
    if snapshot.get("workflow_state") not in {"active", "complete", "terminal", "aborted"}:
        mismatches.append("workflow-state")
    if snapshot.get("plan_slug") is not None and snapshot.get("plan_slug") != receipt.get("plan_slug"):
        mismatches.append("plan-slug")
    if snapshot.get("repo_root") is not None and str(snapshot.get("repo_root")) != str(receipt.get("repo_root")):
        mismatches.append("repository-root")
    if snapshot.get("plan_path") is not None and snapshot.get("plan_path") != receipt.get("plan_path"):
        mismatches.append("plan-path")
    receipt_digest = receipt.get("plan_digest")
    live_digest = snapshot.get("plan_digest")
    if receipt_digest:
        # Fail closed (r2 F6): a receipt naming a plan digest must see the
        # same digest live. A deleted or unreadable plan digests to None
        # here; the old None-skip cleared the fence for exactly the
        # deletion window the digest fence exists for.
        if not isinstance(live_digest, str) or not live_digest.strip() or live_digest != receipt_digest:
            mismatches.append("plan-digest")
    elif live_digest is not None and live_digest != receipt_digest:
        mismatches.append("plan-digest")
    return mismatches


def evaluate_fire(adapter: WatcherStateAdapter, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Re-read machine state immediately before firing and decide.

    Fences first: a watcher refuses to clear guards or relaunch when its id,
    generation, progress revision, workflow state, canonical repository root,
    canonical plan path, plan digest, or current boundary generation no
    longer matches machine state. Then the four stand-down checks, each with
    its own machine-state detection. Untouched state yields the resume
    decision with the exact plan-path prompt.
    """

    snapshot = adapter.read_state()
    mismatches = fence_mismatches(snapshot, receipt)
    if mismatches:
        return {
            "decision": "refuse",
            "reason": "fence-mismatch",
            "mismatches": mismatches,
            "guards_cleared": False,
            "relaunch": False,
            "snapshot_generation": snapshot.get("generation"),
        }
    if adapter.semantic_progress_changed(snapshot, int(receipt.get("expected_progress_revision", 0))):
        return {"decision": "stand_down", "reason": "semantic-progress", "guards_cleared": False, "relaunch": False}
    if adapter.peer_resumed(snapshot, int(receipt.get("scheduled_at_epoch", 0))):
        return {"decision": "stand_down", "reason": "peer-resumed", "guards_cleared": False, "relaunch": False}
    if adapter.archived_or_completed(snapshot):
        return {"decision": "stand_down", "reason": "archived-or-completed", "guards_cleared": False, "relaunch": False}
    if adapter.aborted_or_interrupted(snapshot, int(receipt.get("scheduled_at_epoch", 0))):
        return {"decision": "stand_down", "reason": "aborted-or-interrupted", "guards_cleared": False, "relaunch": False}
    return {
        "decision": "resume",
        "reason": "untouched-state",
        "prompt": build_resume_prompt(receipt),
        "relaunch": True,
    }


def fire_watcher(
    adapter: WatcherStateAdapter,
    receipt: Mapping[str, Any],
    flag_path: os.PathLike | str | None = None,
    fired_path: os.PathLike | str | None = None,
    cleanup: Callable[..., Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate the fire decision, then clear guards only on a resume decision.

    Guard clearing is the atomic compare-and-delete with the receipt's reset
    epoch: a flag replaced by a newer window survives. Any refuse or
    stand-down outcome leaves the guards untouched. ``guards_cleared`` is
    emitted on EVERY decision (r3 F4): False on refuse/stand-down and
    whenever the configured cleanup did not end cleared (r5 F5), so the
    resume envelope can never omit the field its prompt sentence is rendered
    from.
    """

    decision = dict(evaluate_fire(adapter, receipt))
    if decision.get("decision") != "resume":
        decision["guards_cleared"] = False
        decision["relaunch"] = False
        return decision
    if flag_path is not None:
        clear = (cleanup or compare_and_delete_flag)(flag_path, int(receipt.get("reset_at_epoch", 0)), fired_path=fired_path)
        decision["guard_cleanup"] = dict(clear)
        decision["guards_cleared"] = bool(clear.get("removed") or clear.get("reason") == "flag-absent")
    else:
        decision["guards_cleared"] = False
    # The prompt's guard sentence is rendered from the actual cleanup
    # receipt, never asserted ahead of it (r3 F4); build_resume_prompt
    # renders the three outcomes (cleared, attempted-not-achieved,
    # not configured) from that receipt (r5 F5).
    decision["prompt"] = build_resume_prompt(receipt, decision.get("guard_cleanup"))
    return decision


def build_schedule_transition(
    snapshot: Mapping[str, Any],
    *,
    watcher_id: str,
    plan_slug: str,
    repo_root: str,
    plan_path: str,
    plan_digest: str,
    reset_at_epoch: int,
    scheduled_at_epoch: int,
    binding: str,
) -> dict[str, Any]:
    """Build one compare-and-swap schedule transition from a fresh snapshot."""

    return {
        "action": "schedule",
        "expected_watcher_id": current_watcher_id(snapshot),
        "expected_generation": int(snapshot.get("generation", 0)),
        "expected_boundary_generation": int(snapshot.get("boundary_generation", 0)),
        "receipt": {
            "watcher_id": watcher_id,
            "plan_slug": plan_slug,
            "repo_root": str(repo_root),
            "plan_path": str(plan_path),
            "plan_digest": str(plan_digest),
            "scheduled_at_epoch": int(scheduled_at_epoch),
            "reset_at_epoch": int(reset_at_epoch),
            "expected_generation": int(snapshot.get("generation", 0)),
            "expected_progress_revision": int(snapshot.get("progress_revision", 0)),
            "boundary_generation": int(snapshot.get("boundary_generation", 0)) + 1,
            "binding": str(binding),
            "status": "pending",
            "replaces": None,
        },
    }


def build_supersede_transition(snapshot: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
    """Build one compare-and-swap supersede transition from a fresh snapshot."""

    return {
        "action": "supersede",
        "expected_watcher_id": current_watcher_id(snapshot),
        "expected_generation": int(snapshot.get("generation", 0)),
        "expected_boundary_generation": int(snapshot.get("boundary_generation", 0)),
        "reason": str(reason),
    }


def trusted_binding_reset_epoch(probe_report: Mapping[str, Any]) -> Optional[int]:
    """The binding window's reset epoch from a trusted (status ok) report."""

    if probe_report.get("status") != "ok":
        return None
    binding = probe_report.get("binding")
    for limit in probe_report.get("limits", ()) or ():
        if isinstance(limit, Mapping) and limit.get("kind") == binding and isinstance(limit.get("reset_at_epoch"), int):
            return int(limit["reset_at_epoch"])
    return None


def classify_boundary(probe_report: Mapping[str, Any], boundary_kind: Optional[str] = None) -> str:
    """One classification per boundary decision.

    install: a known continue with a trusted binding reset epoch. Every
    other decision (unknown, weekly-secondary, wait-for-reset, pause,
    abort, complete) supersedes and clears any pending watcher even when
    no replacement is scheduled. wait-for-reset is the probe's in-session
    ride-through: the boundary arms nothing, records no receipt, and the
    orchestrator waits wait_minutes and re-probes, the fresh report
    governing the boundary - classify_boundary must never arm a watcher
    into a live wait. Precedence: the pause_decision check runs before the
    status and binding checks, so a wait-for-reset decision classifies
    wait-for-reset even when the binding is weekly-secondary or the status
    is unknown (all three classes are non-schedulable).
    """

    if boundary_kind in {"abort", "complete"}:
        return boundary_kind
    decision = str(probe_report.get("pause_decision", "continue"))
    if decision == "pause":
        return "pause"
    if decision == "wait-for-reset":
        return "wait-for-reset"
    if probe_report.get("status") != "ok":
        return "unknown"
    if probe_report.get("binding") == "secondary":
        return "weekly-secondary"
    if trusted_binding_reset_epoch(probe_report) is None:
        return "unknown"
    return "install"


def record_budget_boundary(
    adapter: WatcherStateAdapter,
    scheduler_chain: Sequence[SchedulerAdapter],
    *,
    probe_report: Mapping[str, Any],
    plan_slug: str,
    plan_path: str,
    plan_digest: str,
    repo_root: str,
    watcher_id_factory: Callable[[], str] | None = None,
    clock: Callable[[], float] = time.time,
    boundary_kind: Optional[str] = None,
    armed_launchd: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Record one budget-boundary decision atomically, then schedule.

    A known continue installs or replaces exactly one watcher (later
    boundaries replace, never stack); every non-schedulable boundary
    supersedes and clears any pending watcher even when no replacement is
    scheduled. The machine write is the compare-and-swap transition; the
    scheduler chain only runs after the machine state accepted the receipt.
    ``armed_launchd`` (r4 F3, full identity since G2) is persisted into the
    receipt: it is the FULL carrier identity (:func:`armed_launchd_identity`:
    label, job dir, plist path, sentinel path, fired-marker path) the chain
    was built to arm, so a later fire consumes exactly that carrier instead
    of reconstructing the identity; when the chain's launchd link is
    unreachable (an automation echo that deterministically succeeds arms no
    launchd job, r5 F4) the caller passes an explicit not-armed record so
    the receipt states that no carrier was armed instead of silently
    omitting the field, and when the reachable link refuses (r6 F5) the
    receipt is rectified to an explicit ``armed: false`` record naming the
    refusal before the schedule outcome returns. A supersede whose outgoing
    receipt records an armed carrier tears that carrier down in the same
    operation (r6 F3: bootout plus sentinel consume, receipt-only).
    """

    classification = classify_boundary(probe_report, boundary_kind)
    snapshot = adapter.read_state()
    if classification == "install":
        reset_epoch = trusted_binding_reset_epoch(probe_report)
        assert reset_epoch is not None  # classification guarantees it
        new_id = (watcher_id_factory or (lambda: f"rw-{uuid.uuid4().hex}"))()
        scheduled_at = int(clock())
        transition = build_schedule_transition(
            snapshot,
            watcher_id=new_id,
            plan_slug=plan_slug,
            repo_root=str(repo_root),
            plan_path=str(plan_path),
            plan_digest=str(plan_digest),
            reset_at_epoch=reset_epoch,
            scheduled_at_epoch=scheduled_at,
            binding=str(probe_report.get("binding")),
        )
        if isinstance(armed_launchd, Mapping):
            transition["receipt"]["armed_launchd"] = dict(armed_launchd)
        machine = adapter.compare_and_swap_schedule(transition)
        if machine.get("status") != "success":
            # A genuine compare-and-swap refusal keeps the stale boundary
            # (r3 F7); a receipt-validation refusal returns its own
            # malformed boundary so the CLI arm can surface the named
            # precondition instead of masquerading it as a lost race.
            machine_reason = machine.get("reason_code")
            cas_refused = machine_reason is None or machine_reason == "" or machine_reason == "stale-attempt"
            return {
                "boundary": "stale" if cas_refused else "malformed",
                "classification": classification,
                "machine": dict(machine),
                "scheduling": None,
            }
        receipt = dict(machine.get("resume_watcher") or transition["receipt"])
        fire_epoch = compute_fire_epoch(int(receipt["reset_at_epoch"]))
        request = {
            "fire_at_epoch": fire_epoch,
            "resume_at_iso": compute_resume_at_iso(fire_epoch),
            "manual_command": build_manual_resume_command(str(plan_path)),
            "watcher_id": receipt["watcher_id"],
            # Plan 2026-11-06-budget-resume-carrier-gc Task 3: the receipt's
            # arm-unique discriminator rides the dedicated request key so
            # the scheduler embeds it as the fixed-marker no-op trailing
            # segment after the manual command; the destructive actors
            # verify live ownership against the persisted receipt value.
            "carrier_watcher_segment": shlex.quote(str(receipt["watcher_id"])),
        }
        scheduling = schedule_with_fallback(scheduler_chain, request)
        # r6 F5: the pre-compare-and-swap record states the identity the
        # chain was BUILT to arm (the crash-window-safe intent stamp), but
        # the persisted receipt must state the actual outcome. When the
        # launchd link was reachable and refused (sentinel self-disable,
        # spent-pair cleanup refusal, label conflict, plist write failure,
        # bootstrap failure) the chain ended report-only while the receipt
        # still claimed an armed carrier; rectify the receipt to an explicit
        # ``armed: false`` record naming the refusal, in the same operation
        # and before the schedule outcome returns. An automation echo
        # already stamps ``armed: false``; a scheduled launchd arm keeps the
        # full identity record.
        carrier_rectified = None
        stamped = transition["receipt"].get("armed_launchd")
        if (
            isinstance(stamped, Mapping)
            and stamped.get("armed") is True
            and not scheduling.get("scheduled")
        ):
            refusal = launchd_refusal_reason(scheduling)
            patch_carrier = getattr(adapter, "compare_and_swap_carrier", None)
            if refusal is not None and callable(patch_carrier):
                honest_record = {"armed": False, "reason": refusal}
                patched = patch_carrier({
                    "action": "re-carrier",
                    "expected_watcher_id": receipt.get("watcher_id"),
                    "expected_generation": receipt.get("expected_generation"),
                    "expected_boundary_generation": receipt.get("boundary_generation"),
                    "armed_launchd": honest_record,
                    "reason": "launchd-arm-outcome",
                })
                if isinstance(patched, Mapping) and patched.get("status") == "success":
                    receipt = dict(patched.get("resume_watcher") or receipt)
                    carrier_rectified = dict(honest_record)
        return {
            "boundary": "install",
            "classification": classification,
            "watcher_id": receipt["watcher_id"],
            "replaces": receipt.get("replaces"),
            "fire_epoch": fire_epoch,
            "machine": dict(machine),
            "scheduling": scheduling,
            "carrier_rectified": carrier_rectified,
            "projection": adapter.projection(adapter.read_state()),
        }
    machine = adapter.compare_and_swap_supersede(build_supersede_transition(snapshot, reason=classification))
    if machine.get("status") != "success":
        return {"boundary": "stale", "classification": classification, "machine": dict(machine), "scheduling": None}
    # r6 F3: the cleared receipt's armed carrier must not outlive the
    # receipt - an orphan job's later fire writes a bare sentinel that
    # refuses every subsequent arm. The teardown is receipt-only and
    # no-ops on an unarmed record.
    return {
        "boundary": "supersede",
        "classification": classification,
        "superseded_watcher_id": machine.get("superseded_watcher_id"),
        "machine": dict(machine),
        "scheduling": None,
        "carrier_teardown": supersede_carrier_teardown(snapshot.get("resume_watcher") if isinstance(snapshot.get("resume_watcher"), Mapping) else {}),
        # Report-only bookkeeping: the boundary names the exact manual resume
        # command even though it schedules no watcher.
        "manual_command": build_manual_resume_command(str(plan_path)),
        "projection": adapter.projection(adapter.read_state()),
    }


def run_cli_watcher_operation(
    kind: str,
    payload: Mapping[str, Any],
    *,
    adapter: WatcherStateAdapter,
    supersede: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    outcome_factory: Callable[..., dict[str, Any]],
    identity_prefix: str,
    plan_slug: str = "",
    repo_root: str = "",
    reconcile_interruption: Callable[[], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """The ONE CLI handler for the schedule / supersede / fire arms (r3 F4).

    Both watcher boundaries (the runtime ``watcher-*`` operations and the
    manifest-free authoring ``plans-watcher-*`` operations) used to carry
    near-verbatim copies of these arms and already diverged on the fire
    guard default. This shared handler parameterizes the divergence points
    (the supersede sink, the identity prefix, the plan-slug fallback) so
    the arms cannot drift again; the fire's guard cleanup defaults to the
    canonical flag path on both boundaries (r3 F4).

    - ``schedule`` records one budget-boundary decision from the probe
      report and runs the CLI fallback chain; a stale compare-and-swap
      surfaces as the distinct ``watcher-cas-stale`` reason code with
      ``cas_applied`` False (r3 F7), never as a supersede that cleared
      something. The launchd identity the chain was built to arm is
      resolved once on this arm path and passed to the chain (r6 F7), then
      persisted into the receipt as the FULL carrier identity (r4 F3, G2):
      label, job dir, plist path, sentinel path, and fired-marker path. A
      schedule that arms no launchd (an automation echo) records that
      explicitly with an ``armed: false`` carrier record, so fire consumes
      exactly what the arm armed and never re-derives an identity; a
      reachable launchd link that refuses is rectified into the receipt the
      same way before the schedule result returns (r6 F5).
    - ``supersede`` clears a pending watcher through the caller's sink and
      tears the outgoing receipt's armed carrier down in the same operation
      (r6 F3: receipt-only bootout plus sentinel consume).
    - ``fire`` is the automation prompt's entry: it evaluates the fences
      and the four stand-down checks, clears the guard flag and fired
      marker only on a resume decision, always emits ``guards_cleared``
      (r3 F4), and consumes the launchd one-shot sentinel on any terminal
      decision so the decision is marked and a later window can re-arm
      (r3 F16). A resume decision also consumes the receipt itself inside
      the fire operation (r4 F4): the peer-resume mark is recorded and the
      receipt is superseded (compare-and-swap bumping the boundary
      generation), so a duplicate fire inside the window before the
      resumed session runs is refused deterministically on machine state.
    """

    if kind == "schedule":
        probe_report = payload.get("probe_report")
        if not isinstance(probe_report, Mapping):
            probe_report = payload
        raw_plan_path = str(payload.get("plan_path") or "").strip()
        if not raw_plan_path:
            raise ValueError(f"{identity_prefix}-schedule requires payload plan_path")
        # Canonical plan identity at schedule time (r2 F6): expanduser and
        # resolve so the persisted receipt, the live fence, and a later
        # fire from a different working directory compare one absolute
        # path, never an invocation-relative spelling of it.
        plan_path = str(pathlib.Path(raw_plan_path).expanduser().resolve())
        # Plan operand passthrough (plan-directory-shape plan, Task 3): the
        # operand resolves through the shared shape resolver, so a plan
        # directory schedules with the manifest digest and a malformed one
        # refuses through the resolver's named arm; a file operand keeps
        # the legacy raw-bytes digest and unreadable refusal.
        plan_digest, plan_refusal = plan_operand_digest(plan_path)
        if plan_digest is None:
            if plan_refusal is not None:
                raise ValueError(f"{identity_prefix}-schedule plan operand refused: {plan_refusal}")
            raise ValueError(f"{identity_prefix}-schedule plan path is unreadable: {plan_path}")
        payload_job_dir = payload.get("job_dir")
        payload_sentinel = payload.get("sentinel_path")
        resolved_launchd = resolve_launchd_identity(payload_job_dir, payload_sentinel, plan_slug, repo_root)
        automation_echo = payload.get("automation") if isinstance(payload.get("automation"), Mapping) else None
        # r5 F4 + G2: the receipt always records the carrier decision. When
        # the chain's launchd link is reachable, the arm persists the FULL
        # carrier identity (label, job dir, plist path, sentinel path, fired
        # marker path) it was built to arm; an automation echo carrying a
        # successful create succeeds deterministically in the chain's first
        # link, so no launchd job is armed on top of it and the receipt
        # records that explicitly instead of stamping an identity that was
        # never armed (a later fire would then consume a sentinel nothing
        # wrote). r6 F5: this stamp is the intent record - when the reachable
        # link refuses, record_budget_boundary rectifies the receipt to the
        # actual outcome before the schedule result returns.
        launchd_reachable = not (
            isinstance(automation_echo, Mapping) and automation_echo.get("scheduled") is True
        )
        if launchd_reachable:
            carrier_record = armed_launchd_identity(
                resolved_launchd["job_dir"],
                resolved_launchd["sentinel_path"],
                resolved_launchd["label"],
            )
        else:
            carrier_record = {"armed": False, "reason": "automation-echo-scheduled"}
        boundary = record_budget_boundary(
            adapter,
            # r6 F7: the identity is resolved once above and the chain
            # consumes exactly that resolution, so the receipt's recorded
            # carrier and the scheduler's armed carrier cannot disagree.
            cli_scheduler_chain(
                automation_result=automation_echo,
                resolved_identity=resolved_launchd,
                job_dir=payload_job_dir,
                sentinel_path=payload_sentinel,
                plan_slug=plan_slug,
                repo_root=repo_root,
            ),
            probe_report=probe_report,
            plan_slug=plan_slug,
            plan_path=plan_path,
            plan_digest=plan_digest,
            repo_root=str(repo_root),
            boundary_kind=payload.get("boundary_kind"),
            armed_launchd=carrier_record,
        )
        boundary_name = str(boundary.get("boundary"))
        # A stale compare-and-swap is not a supersede (r3 F7): nothing was
        # cleared and any pending watcher is still armed, so the stale
        # outcome carries its own reason code and cas_applied False.
        reason_code = {
            "install": "resume-watcher-scheduled",
            "supersede": "resume-watcher-superseded",
            "stale": "watcher-cas-stale",
            "malformed": "watcher-receipt-invalid",
        }.get(boundary_name, "watcher-cas-stale")
        machine_block = boundary.get("machine") or {}
        evidence = [
            f"boundary={boundary.get('boundary')}",
            f"classification={boundary.get('classification')}",
            f"scheduling={json.dumps(boundary.get('scheduling'), sort_keys=True) if boundary.get('scheduling') else 'none'}",
        ]
        if boundary_name not in {"install", "supersede"}:
            # The machine trail on every refused boundary: the machine
            # result's reason code plus its evidence strings, so the caller
            # sees the exact precondition (the ValueError naming the
            # unsatisfied receipt field) instead of a bare boundary name;
            # the genuine stale outcome carries the same trail.
            evidence.append(f"machine-reason={machine_block.get('reason_code')}")
            evidence.extend(str(item) for item in (machine_block.get("evidence") or []))
        return outcome_factory(
            "success" if boundary_name == "install" else "blocked",
            reason_code,
            evidence,
            "repository-write",
            f"{identity_prefix}:schedule",
            int((boundary.get("machine") or {}).get("generation", 0)),
            "continue-parent" if boundary_name == "install" else "preserve-and-reconcile",
            resume_watcher=(boundary.get("machine") or {}).get("resume_watcher"),
            scheduling=boundary.get("scheduling"),
            projection=boundary.get("projection"),
            manual_command=boundary.get("manual_command"),
            carrier_rectified=boundary.get("carrier_rectified"),
            carrier_teardown=boundary.get("carrier_teardown"),
            # The machine refused the write on a refused boundary, so the
            # envelope must not claim an applied swap; the true value scopes
            # to the install and supersede boundaries.
            cas_applied=boundary_name in {"install", "supersede"},
        )
    if kind == "supersede":
        snapshot = adapter.read_state()
        transition = build_supersede_transition(snapshot, reason=str(payload.get("reason", "boundary-decision")))
        outcome = supersede(transition)
        # r6 F3: a supersede whose outgoing receipt records an armed carrier
        # tears that carrier down in the same operation - bootout the
        # recorded plist, consume the recorded sentinel/fired pair - so the
        # orphan job's later fire cannot leave a bare sentinel that refuses
        # every subsequent arm. Receipt-only; no-op on an unarmed record;
        # a stale compare-and-swap (nothing cleared) tears nothing down.
        if isinstance(outcome, Mapping) and outcome.get("status") == "success":
            outgoing = snapshot.get("resume_watcher")
            outcome = dict(outcome)
            outcome["carrier_teardown"] = supersede_carrier_teardown(outgoing if isinstance(outgoing, Mapping) else {})
        return outcome
    if kind == "fire":
        snapshot = adapter.read_state()
        receipt = snapshot.get("resume_watcher")
        fire_identity = f"{identity_prefix}:fire"
        if not isinstance(receipt, Mapping) or not str(receipt.get("watcher_id") or "").strip():
            return outcome_factory(
                "blocked",
                "stale-attempt",
                ["no pending resume watcher to fire"],
                "repository-write",
                fire_identity,
                int(snapshot.get("generation", 0)),
                "preserve-and-reconcile",
            )
        requested_id = payload.get("watcher_id")
        if requested_id is not None and str(requested_id) != str(receipt.get("watcher_id")):
            return outcome_factory(
                "blocked",
                "stale-attempt",
                [f"watcher_id={requested_id} does not name the pending watcher {receipt.get('watcher_id')}"],
                "repository-write",
                fire_identity,
                int(snapshot.get("generation", 0)),
                "preserve-and-reconcile",
            )
        if reconcile_interruption is not None:
            candidate = evaluate_fire(adapter, receipt)
            if candidate.get("decision") == "resume":
                reconciled = reconcile_interruption()
                if not isinstance(reconciled, Mapping) or reconciled.get("status") != "success":
                    return {
                        **dict(reconciled or {}),
                        "decision": "refuse",
                        "reason": "interruption-reconciliation-failed",
                        "guards_cleared": False,
                        "relaunch": False,
                    }
        flag_default = DEFAULT_FLAG_PATH
        decision = fire_watcher(
            adapter,
            receipt,
            flag_path=payload.get("flag_path", str(flag_default)),
            fired_path=payload.get("fired_path"),
        )
        decision["checkpoint_identity"] = fire_identity
        decision["action_scope"] = "repository-write"
        decision["watcher_id"] = receipt.get("watcher_id")
        if decision.get("decision") == "resume":
            # A resume decision consumes the receipt inside the fire
            # operation (r4 F4): the pending receipt used to survive the
            # minutes-wide window before the resumed session recorded its
            # peer-resume mark, so a duplicate fire (automation retry,
            # manual re-fire) re-evaluated the identical receipt and emitted
            # a second resume. Two machine writes close the window: the
            # peer-resume mark stands any same-window re-evaluation down,
            # and the supersede compare-and-swap bumps boundary_generation
            # so a fire naming the consumed receipt refuses deterministically
            # on machine state, never on the peer timestamp.
            mark = getattr(adapter, "record_resume", None)
            if callable(mark):
                decision["peer_resume_mark"] = mark([f"watcher-fire:{receipt.get('watcher_id')}"])
            supersede_outcome = supersede(build_supersede_transition(adapter.read_state(), reason="fired"))
            decision["receipt_superseded"] = {
                "watcher_id": receipt.get("watcher_id"),
                "status": supersede_outcome.get("status"),
                "reason_code": supersede_outcome.get("reason_code"),
            }
        # Consume the one-shot on any terminal decision (r3 F16): the fired
        # job wrote the sentinel before the resume command ran; watcher-fire
        # removes it and writes the fired marker so the still-loaded daily
        # job stays inert and a later window's arm re-arms. Receipt-only
        # carrier identity (G2): the consumed sentinel and fired marker come
        # from the receipt's ``armed_launchd`` record and from nothing else.
        # A receipt with no carrier record (or one recording armed: false,
        # an automation echo) consumes nothing: no identity is derived at
        # fire time, and a structural test forbids that. One documented
        # override (r6 F6): an explicit payload ``sentinel_path`` takes
        # precedence over the receipt's carrier record as the operator's
        # manual-recovery input, and it is scoped to the sanctioned runtime
        # directory (r5 F13) so a wrong path consumes and marks nothing.
        armed = receipt.get("armed_launchd") if isinstance(receipt.get("armed_launchd"), Mapping) else None
        if payload.get("sentinel_path") is not None:
            decision["sentinel"] = consume_resume_sentinel_scoped(payload["sentinel_path"])
        elif armed is not None and armed.get("armed") is True:
            sentinel_path = armed.get("sentinel_path")
            if isinstance(sentinel_path, str) and sentinel_path.strip():
                fired_marker = armed.get("fired_marker_path")
                decision["sentinel"] = consume_resume_sentinel(
                    sentinel_path,
                    fired_path=fired_marker if isinstance(fired_marker, str) and fired_marker.strip() else None,
                )
        return decision
    raise ValueError(f"unknown watcher operation kind: {kind}")


# ---------------------------------------------------------------------------
# plans authoring adapter (Task 6): the authoring machine-state JSON at
# {tmp_dir}/plan-requirements-<slug>.json is the authority; the Markdown
# notes (plan-requirements-<slug>.md) are a projection appended only after
# a lock-held state transition, and authoring progress is never inferred
# from Markdown updated: text. This workflow shares the one watcher state
# machine above; it does not grow a second protocol.
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def authoring_state_lock(state_path: os.PathLike | str) -> Iterator[bool]:
    """The shared watcher lock for one authoring machine-state JSON.

    Every adapter read, every compare-and-swap transition, and the
    authoring loop's progress / interrupt / terminal updates hold this file
    lock, so a watcher transition can never interleave with a round
    boundary or handoff update.
    """

    lock_path = pathlib.Path(str(state_path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


class PlansAuthoringWatcherAdapter(WatcherStateAdapter):
    """plans authoring-state adapter over ``plan-requirements-<slug>.json``.

    The authoring JSON is the authority; the Markdown notes are the human
    and audit projection and receive a line only after a lock-held state
    transition. Its observation methods implement the replacement, cancellation,
    boundary generation, canonical plan path and digest, semantic-progress,
    peer-resume, archive, completion, abort, and interrupt fences required by plans authoring.
    """

    def __init__(
        self,
        state_path: os.PathLike | str,
        notes_path: os.PathLike | str | None = None,
        *,
        repo_root: str,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._state_path = pathlib.Path(state_path)
        if notes_path is not None:
            self._notes_path: pathlib.Path | None = pathlib.Path(notes_path)
        else:
            text = str(state_path)
            stem = text[:-5] if text.endswith(".json") else text
            self._notes_path = pathlib.Path(stem + ".md")
        self._repo_root = str(repo_root)
        self._clock = clock

    # -- lock-held machine-state primitives ------------------------------

    def _locked_read(self) -> dict[str, Any]:
        with authoring_state_lock(self._state_path):
            return self._read_unlocked()

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if not isinstance(state, dict):
            state = {}
        state.setdefault("plan_slug", "")
        state.setdefault("workflow_state", "active")
        state.setdefault("plan_status", None)
        state.setdefault("generation", 0)
        state.setdefault("progress_revision", 0)
        state.setdefault("boundary_generation", 0)
        state.setdefault("resume_watcher", None)
        state.setdefault("user_interrupt", None)
        state.setdefault("peer_resumed_at_epoch", 0.0)
        state.setdefault("updated_at", 0.0)
        return state

    def _save_unlocked(self, state: dict[str, Any], event: Mapping[str, Any]) -> None:
        state["updated_at"] = float(self._clock())
        state.setdefault("history", []).append(dict(event))
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_path.with_name(self._state_path.name + ".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self._state_path)

    def _project_unlocked(self, state: Mapping[str, Any]) -> None:
        """Append the projection line to the Markdown notes; called only
        inside a held lock after a successful state transition."""

        if self._notes_path is None:
            return
        line = render_manifest_projection({"resume_watcher": state.get("resume_watcher")})
        self._notes_path.parent.mkdir(parents=True, exist_ok=True)
        with self._notes_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def _cas_blocked(self, transition: Mapping[str, Any], state: dict[str, Any]) -> dict[str, Any] | None:
        current = state.get("resume_watcher")
        current_id = current.get("watcher_id") if isinstance(current, Mapping) else None
        if watcher_cas_stale(transition, current_id, int(state.get("generation", 0)), int(state.get("boundary_generation", 0))):
            return self._blocked("stale-attempt", ["watcher compare-and-swap failed"], state)
        return None

    @staticmethod
    def _blocked(reason_code: str, evidence: list[str], state: Mapping[str, Any]) -> dict[str, Any]:
        current = state.get("resume_watcher")
        return {
            "status": "blocked",
            "reason_code": reason_code,
            "evidence": list(evidence),
            "resume_watcher": dict(current) if isinstance(current, Mapping) else None,
            "cas_applied": False,
        }

    # -- WatcherStateAdapter protocol ------------------------------------

    def read_state(self) -> dict[str, Any]:
        snapshot = self._locked_read()
        watcher_receipt = snapshot.get("resume_watcher")
        if isinstance(watcher_receipt, Mapping):
            snapshot["plan_path"] = watcher_receipt.get("plan_path")
            # Recompute the plan-byte digest now: this is the live fence.
            snapshot["plan_digest"] = file_digest(watcher_receipt.get("plan_path"))
        else:
            snapshot["plan_path"] = None
            snapshot["plan_digest"] = None
        snapshot.setdefault("repo_root", self._repo_root)
        return snapshot

    def compare_and_swap_schedule(self, transition: Mapping[str, Any]) -> dict[str, Any]:
        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            blocked = self._cas_blocked(transition, state)
            if blocked is not None:
                return blocked
            receipt = dict(transition.get("receipt") or {})
            try:
                validate_resume_watcher_receipt(receipt)
            except ValueError as exc:
                return self._blocked("malformed-result", [str(exc)], state)
            current = state.get("resume_watcher")
            current_id = current.get("watcher_id") if isinstance(current, Mapping) else None
            receipt["replaces"] = current_id
            receipt["boundary_generation"] = int(state.get("boundary_generation", 0)) + 1
            state["resume_watcher"] = receipt
            state["boundary_generation"] = receipt["boundary_generation"]
            # The authoring state owns the canonical plan slug; the fence
            # compares against it.
            state["plan_slug"] = receipt["plan_slug"]
            self._save_unlocked(
                state,
                {"event": "resume-watcher-scheduled", "watcher_id": receipt["watcher_id"], "replaces": current_id},
            )
            self._project_unlocked(state)
            return {
                "status": "success",
                "reason_code": "resume-watcher-scheduled",
                "resume_watcher": dict(receipt),
                "cas_applied": True,
            }

    def compare_and_swap_supersede(self, transition: Mapping[str, Any]) -> dict[str, Any]:
        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            blocked = self._cas_blocked(transition, state)
            if blocked is not None:
                return blocked
            current = state.get("resume_watcher")
            current_id = current.get("watcher_id") if isinstance(current, Mapping) else None
            state["resume_watcher"] = None
            state["boundary_generation"] = int(state.get("boundary_generation", 0)) + 1
            # Plan 2026-11-06-budget-resume-carrier-gc Task 2: the fired
            # supersede history event retains the outgoing record's
            # armed_launchd fields beside the watcher_id it already records,
            # so the closeout discharge's fallback can run the ownership
            # check and act on the recorded paths after the fire-resume
            # cleared the record.
            outgoing_armed = current.get("armed_launchd") if isinstance(current, Mapping) else None
            self._save_unlocked(
                state,
                {
                    "event": "resume-watcher-superseded",
                    "watcher_id": current_id,
                    "reason": str(transition.get("reason", "boundary-decision")),
                    **({"armed_launchd": dict(outgoing_armed)} if isinstance(outgoing_armed, Mapping) else {}),
                },
            )
            self._project_unlocked(state)
            return {
                "status": "success",
                "reason_code": "resume-watcher-cleared",
                "resume_watcher": None,
                "superseded_watcher_id": current_id,
                "cas_applied": True,
            }

    def compare_and_swap_carrier(self, transition: Mapping[str, Any]) -> dict[str, Any]:
        """Rectify the pending receipt's armed_launchd record (r6 F5).

        The plans-authoring carrier replacement operation:
        the pending receipt stays installed with its boundary generation
        unchanged, only the carrier record is replaced.
        """

        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            blocked = self._cas_blocked(transition, state)
            if blocked is not None:
                return blocked
            current = state.get("resume_watcher")
            if not isinstance(current, Mapping) or current.get("watcher_id") != transition.get("expected_watcher_id"):
                return self._blocked("stale-attempt", ["watcher receipt changed before the carrier rectification"], state)
            patch = transition.get("armed_launchd")
            if not isinstance(patch, Mapping) or "armed" not in patch:
                return self._blocked("malformed-result", ["carrier rectification requires an armed_launchd record"], state)
            receipt = dict(current)
            receipt["armed_launchd"] = dict(patch)
            state["resume_watcher"] = receipt
            self._save_unlocked(
                state,
                {
                    "event": "resume-watcher-carrier-rectified",
                    "watcher_id": receipt.get("watcher_id"),
                    "reason": str(transition.get("reason", "launchd-arm-outcome")),
                    "armed": patch.get("armed") is True,
                },
            )
            self._project_unlocked(state)
            return {
                "status": "success",
                "reason_code": "resume-watcher-carrier-rectified",
                "resume_watcher": dict(receipt),
                "cas_applied": True,
            }

    # Snapshot-derived stand-down fences live beside the persistence and
    # archived trigger they govern.

    def semantic_progress_changed(self, snapshot: Mapping[str, Any], expected_progress_revision: int) -> bool:
        return int(snapshot.get("progress_revision", 0)) != int(expected_progress_revision)

    def peer_resumed(self, snapshot: Mapping[str, Any], scheduled_at_epoch: int) -> bool:
        return float(snapshot.get("peer_resumed_at_epoch", 0.0) or 0.0) > float(scheduled_at_epoch)

    def aborted_or_interrupted(self, snapshot: Mapping[str, Any], scheduled_at_epoch: int) -> bool:
        if snapshot.get("workflow_state") == "aborted":
            return True
        return interrupt_after(snapshot.get("user_interrupt"), scheduled_at_epoch)

    def projection(self, snapshot: Mapping[str, Any]) -> str:
        return render_manifest_projection(snapshot)

    def archived_or_completed(self, snapshot: Mapping[str, Any]) -> bool:
        # The completed-plan stand-down trigger is a declared delta of this
        # mirror: completed OR archived, either trigger stands down.
        if snapshot.get("workflow_state") in {"complete", "terminal"}:
            return True
        return snapshot.get("plan_status") == "archived"

    # -- authoring loop updates (shared-lock writers) --------------------

    def record_resume(self, evidence: Sequence[str] | None = None) -> dict[str, Any]:
        """Mark a resume-path re-entry for the shared peer fence (r1 F11).

        The plans loop calls this whenever a session re-enters authoring
        through the resume path, so a watcher scheduled before the re-entry
        stands down at fire time (``peer_resumed`` compares this field
        against its scheduling epoch), while construction and
        bookkeeping writes never trip it.
        """

        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            state["peer_resumed_at_epoch"] = float(self._clock())
            self._save_unlocked(
                state,
                {
                    "event": "authoring-resume-recorded",
                    "peer_resumed_at_epoch": state["peer_resumed_at_epoch"],
                    "evidence": [str(item) for item in (evidence or ())],
                },
            )
            return {"status": "success", "reason_code": "authoring-resume-recorded"}

    def record_progress(self, evidence: Sequence[str] | None = None) -> dict[str, Any]:
        """Advance the authoring progress revision under the shared lock.

        The authoring loop calls this before and after each review round
        and done handoff, so a scheduled watcher's expected progress
        revision goes stale exactly when authoring moved.
        """

        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            next_revision = int(state.get("progress_revision", 0)) + 1
            state["progress_revision"] = next_revision
            self._save_unlocked(
                state,
                {
                    "event": "progress-recorded",
                    "revision": next_revision,
                    "evidence": [str(item) for item in (evidence or ())],
                },
            )
            return {"status": "success", "reason_code": "progress-recorded", "progress_revision": next_revision}

    def record_interrupt(self, timestamp: str | None = None) -> dict[str, Any]:
        """Persist ``user_interrupt`` under the shared lock, keeping
        ``workflow_state`` unchanged (a plain interrupt stays resumable)."""

        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            value = str(timestamp) if timestamp else datetime.fromtimestamp(float(self._clock())).astimezone().isoformat()
            try:
                datetime.fromisoformat(value)
            except ValueError as exc:
                return {
                    "status": "blocked",
                    "reason_code": "malformed-result",
                    "evidence": [f"user_interrupt must be an ISO-8601 timestamp: {exc}"],
                }
            state["user_interrupt"] = value
            self._save_unlocked(state, {"event": "user-interrupt-recorded", "user_interrupt": value})
            return {"status": "success", "reason_code": "interrupt-recorded", "user_interrupt": value}

    def record_terminal(self, kind: str) -> dict[str, Any]:
        """Record completion or archival under the shared lock.

        ``complete`` sets ``workflow_state`` to ``complete``; ``archived``
        sets ``plan_status`` to ``archived``; ``aborted`` sets
        ``workflow_state`` to ``aborted``. The archived trigger stays out of
        ``workflow_state`` so the shared fence's workflow-state check does
        not consume the archived-or-completed stand-down.
        """

        if kind not in {"complete", "archived", "aborted"}:
            raise ValueError("terminal kind must be one of: complete, archived, aborted")
        with authoring_state_lock(self._state_path):
            state = self._read_unlocked()
            if kind == "archived":
                state["plan_status"] = "archived"
            else:
                state["workflow_state"] = kind
            self._save_unlocked(state, {"event": "authoring-terminal-recorded", "kind": kind})
            return {"status": "success", "reason_code": "authoring-terminal-recorded", "kind": kind}


# ---------------------------------------------------------------------------
# Clocked operator orders (plan 2026-10-05-authoring-clocked-resume-order,
# Task 1): the order ledger, its four CLI operations, and the discharge path.
# The ledger is a standalone store, NOT a WatcherStateAdapter subclass (A8):
# pending_rearm is cadence-armed with no per-order wall-clock time, the
# authoring adapter is plan-slug-keyed and carries resume fences an order
# does not carry, and the scheduler-state intent family is single-valued by
# design. The order machinery reuses their patterns - the locked atomic
# state file, the pairing discipline, the report-only shape, and the
# scheduler adapter chain with its sentinel lifecycle - without overloading
# their contracts.
# ---------------------------------------------------------------------------


CLOCKED_ORDER_STATES = ("pending", "armed", "discharged", "cancelled", "missed")
CLOCKED_ORDER_TERMINAL_STATES = ("discharged", "cancelled", "missed")
CLOCKED_ORDER_LABEL_PREFIX = "ai-playbook.clocked-order."
# The provider-config environment the fire payload exports explicitly (the
# maintenance overlay's Launchd carrier bullet): a launchd-fired job cannot
# rely on the desktop app's interactive session to supply them, so the
# builder snapshots the named variable plus every ZCODE provider-config
# sibling present in the arming environment into the payload itself.
CLOCKED_ORDER_PROVIDER_CONFIG_VARS = ("ZCODE_BUILTIN_PROVIDER_CONFIG_FILE",)


def default_clocked_order_ledger_paths(repo_root: os.PathLike | str) -> dict[str, str]:
    """The A1 default ledger paths under the maintenance state home.

    The resolved ``maintenance_state_dir`` (fallback
    ``.ai-playbook/maintenance/``) holds ``clocked-orders.json`` and the
    ``clocked-order-payloads/`` home beside it, both under the gitignored
    maintenance home. The runtime wrapper resolves the facts key and passes
    explicit paths; tests inject temp dirs through the same constructor
    parameters.
    """

    root = pathlib.Path(os.path.expanduser(str(repo_root))).resolve()
    state_dir = root / ".ai-playbook" / "maintenance"
    return {
        "ledger_path": str(state_dir / "clocked-orders.json"),
        "payload_home": str(state_dir / "clocked-order-payloads"),
    }


def default_clocked_order_identity(order_id: str | None, repo_root: str | None) -> dict[str, str]:
    """The keyed default job dir, sentinel, and label for one order carrier.

    The per-order identity key sits beside the existing plan-keyed one (the
    existing keyed-identity precedent): the key digests the order id and the
    canonical repository root under the distinct ``ai-playbook.clocked-order.``
    label prefix, so an order carrier never shares a label, job path, or
    sentinel with a budget-resume watcher or with another order.
    """

    key = launchd_identity_key(f"clocked-order:{order_id or ''}", repo_root)
    return {
        "key": key,
        "job_dir": str(DEFAULT_LAUNCHD_JOB_DIR / f"clocked-order-{key}"),
        "sentinel_path": str(DEFAULT_RESUME_SENTINEL.with_name(f"clocked-order-{key}.sentinel")),
        "label": f"{CLOCKED_ORDER_LABEL_PREFIX}{key}",
    }


def resolve_clocked_order_identity(
    job_dir: os.PathLike | str | None,
    sentinel_path: os.PathLike | str | None,
    order_id: str | None,
    repo_root: str | None,
) -> dict[str, str]:
    """The one launchd-identity derivation for the clocked-order arms.

    Mirror of :func:`resolve_launchd_identity` keyed on the order identity:
    keyed whenever either path is left at its default, unkeyed only when the
    caller brings both paths explicitly.
    """

    identity = default_clocked_order_identity(order_id, repo_root) if (order_id or repo_root) else None
    both_explicit = job_dir is not None and sentinel_path is not None
    if identity is not None and not both_explicit:
        return {
            "job_dir": str(job_dir) if job_dir is not None else identity["job_dir"],
            "sentinel_path": str(sentinel_path) if sentinel_path is not None else identity["sentinel_path"],
            "label": identity["label"],
        }
    return {
        "job_dir": str(job_dir) if job_dir is not None else str(DEFAULT_LAUNCHD_JOB_DIR),
        "sentinel_path": str(sentinel_path) if sentinel_path is not None else str(DEFAULT_RESUME_SENTINEL),
        "label": CLOCKED_ORDER_LABEL_PREFIX.rstrip("."),
    }


def clocked_order_provider_config_exports(environ: Mapping[str, str] | None = None) -> str:
    """The env-complete export prefix for the order fire payload.

    The maintenance overlay's Launchd carrier bullet prescribes the
    env-complete headless form: the job exports
    ``ZCODE_BUILTIN_PROVIDER_CONFIG_FILE`` and its sibling provider-config
    variables explicitly, because a launchd-fired job cannot rely on the
    desktop app's interactive session to supply them (the instant-death
    witness of 2026-09-20). The builder snapshots the named variables plus
    every ZCODE provider-config sibling present in the arming environment.
    """

    env = os.environ if environ is None else environ
    names = list(CLOCKED_ORDER_PROVIDER_CONFIG_VARS)
    names.extend(
        sorted(
            name
            for name in env
            if name.startswith("ZCODE_") and "PROVIDER" in name and name not in names
        )
    )
    exports = []
    for name in names:
        value = env.get(name)
        if value:
            exports.append(f"export {name}={shlex.quote(str(value))}")
    return " && ".join(exports)


# The handoff lease the fire wrapper registers before ZCode starts: a due
# scan that overlaps the session prelude defers until it expires, and the
# session's own discharge refuses once it has expired (plan
# 2026-11-08-clocked-order-payload-session-execution; machinery registry
# entry protocol:clocked-order-handoff-lease).
CLOCKED_ORDER_HANDOFF_LEASE_SECONDS = 3600
# The named fail-closed refusal the session's first action prints when the
# ZCode runtime context supplies no session id (before any ledger write or
# discharge; the launchd shell never discharges the order).
CLOCKED_ORDER_FIRE_PRELUDE_STOP_REFUSAL = "clocked-order-refused-missing-session-identity"
# The no-progress horizon for a discharged order's linked child (the
# failure cap's ordinary six-hour pending-child check): a linked child still
# pending at ``fire_at`` plus six hours failed, mirroring the maintenance
# loop's own horizon (plan 2026-11-08-clocked-order-payload-session-execution
# Task 2).
CLOCKED_ORDER_PAYLOAD_RECOVERY_HORIZON_SECONDS = 6 * 3600
# The complete schema-4 children[] projection stored on the order at
# scheduling time, so a lost or stale scheduler-state row can be rebuilt
# without guessing a target, a fire time, or a progress baseline (plan Task
# 2; agents/skills/maintenance/state-file.md's schema block).
CLOCKED_ORDER_CHILD_TEMPLATE_FIELDS = (
    "order_id",
    "automation_id",
    "runtime_id",
    "kind",
    "target",
    "created_at",
    "requested_at",
    "fire_at",
    "quota_status",
    "outcome",
    "outcome_checked_at",
    "progress_mark",
    "resume_count",
    "outcome_reason",
    "dispatch_plan_sha",
    "quota_signal",
    "worktree",
)


def build_clocked_order_child_template(
    *,
    order_id: str,
    payload_slug: str,
    requested_at_iso: str,
    requested_epoch: int,
    created_epoch: float,
    automation_id: str | None = None,
) -> dict[str, Any]:
    """The complete schema-4 child-entry template stored on the order.

    Every field the scheduler state's ``children[]`` entry carries at
    dispatch time, recorded once at scheduling with the exact order id as
    the entry link: when the maintenance turn's Step 6 rewrite later drops
    the row or loses a projection field, the failure-cap reader rebuilds it
    from this template and the order's canonical outcome - never by
    guessing a target or a progress baseline.
    """

    template = {
        "order_id": str(order_id),
        "automation_id": str(automation_id) if automation_id else None,
        "runtime_id": "unknown",
        "kind": "execute",
        "target": str(payload_slug),
        "created_at": datetime.fromtimestamp(int(created_epoch)).astimezone().isoformat(),
        "requested_at": str(requested_at_iso),
        "fire_at": datetime.fromtimestamp(int(requested_epoch)).astimezone().isoformat(),
        "quota_status": "unknown",
        "outcome": "pending",
        "outcome_checked_at": None,
        "progress_mark": 0,
        "resume_count": 0,
        "outcome_reason": None,
        "dispatch_plan_sha": None,
        "quota_signal": None,
        "worktree": None,
    }
    return {field: template[field] for field in CLOCKED_ORDER_CHILD_TEMPLATE_FIELDS}


# The conventional plans ``completed/`` home used when the target repository's
# facts document carries no ``plans_completed_dir`` key (the same fallback the
# origins-closure gate applies to a missing facts key).
CLOCKED_ORDER_PLANS_COMPLETED_DIR_DEFAULT = "docs/history/plans/completed"


def _facts_plans_completed_dir(repo_root: os.PathLike | str) -> str:
    """The target repository's resolved ``plans_completed_dir`` (facts TOML).

    Reads the first ```toml fenced block of ``<repo root>/.ai-playbook/facts.md``
    for the single-line quoted string key (the same fenced-block shape the
    shared facts parser resolves; mirrored locally because this module imports
    no siblings) and returns its verbatim value. A missing or unreadable file,
    an absent fence, or an absent or unparseable key falls back to the
    conventional repo-relative default.
    """

    facts_path = pathlib.Path(repo_root) / ".ai-playbook" / "facts.md"
    try:
        text = facts_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return CLOCKED_ORDER_PLANS_COMPLETED_DIR_DEFAULT
    in_toml = False
    for line in text.splitlines():
        if not in_toml:
            if line.lstrip().startswith("```toml"):
                in_toml = True
            continue
        if line.lstrip().startswith("```"):
            break
        match = re.match(r"^\s*plans_completed_dir\s*=\s*(.+)$", line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                return value[1:-1].strip()
            return CLOCKED_ORDER_PLANS_COMPLETED_DIR_DEFAULT
    return CLOCKED_ORDER_PLANS_COMPLETED_DIR_DEFAULT


def _linked_clocked_plan_archived(repo_root: os.PathLike | str, order: Mapping[str, Any]) -> bool:
    """Whether the order's linked execution plan has archived (Task 3).

    The evidence is the plan move itself: the child template's ``target``
    path no longer exists at the recorded repository root and a file with
    the same basename exists under the facts-resolved plans ``completed/``
    directory. A surviving live twin (a copy-not-move defect) is not
    archival evidence, and a template-less order or an empty target proves
    nothing.
    """

    template = order.get("child_template")
    if not isinstance(template, Mapping):
        return False
    target = template.get("target")
    if not isinstance(target, str) or not target.strip():
        return False
    target_path = pathlib.Path(target.strip())
    name = target_path.name
    if not name:
        return False
    live = target_path if target_path.is_absolute() else pathlib.Path(repo_root) / target_path
    try:
        if live.exists():
            return False
        completed_dir = pathlib.Path(repo_root) / _facts_plans_completed_dir(repo_root)
        return (completed_dir / name).exists()
    except OSError:
        return False


def _atomic_replace_json(path: pathlib.Path, state: Mapping[str, Any]) -> None:
    """Temp-file plus atomic replace for one JSON document (schema shape)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _child_row_fire_epoch(value: Any) -> int | None:
    """Epoch of a children[] ``fire_at`` value, or None when unusable.

    A naive value reads in the machine's local zone (the
    ``requested_at_iso`` convention the deciding turn mirrors); a ``Z``
    suffix reads as UTC; anything unparseable is None, and a None never
    matches.
    """

    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return int(parsed.timestamp())


def _match_legacy_child_row(order: Mapping[str, Any], scheduler_state_path: os.PathLike | str | None) -> dict[str, Any]:
    """The legacy child match: exactly one row naming the order (plan Terms).

    A row matches when its kind is the clocked child kind (``execute``), its
    ``fire_at`` equals the order's requested epoch, its target names the
    order's recorded payload slug, and its carrier identity matches the
    recorded carrier label; a row carrying the exact ``order_id`` link
    satisfies the target and identity conjuncts by that link alone. Missing
    or ambiguous matches stay disabled for operator recovery.
    """

    order_id = str(order.get("order_id"))
    path = (
        pathlib.Path(os.path.expanduser(str(scheduler_state_path)))
        if scheduler_state_path
        else pathlib.Path(str(order.get("target_repo_root"))) / ".ai-playbook" / "scheduler-state.json"
    )
    if not path.exists():
        return {"unique": False, "matches": 0, "reason": "scheduler-state-absent"}
    try:
        scheduler_state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"unique": False, "matches": 0, "reason": "scheduler-state-unreadable"}
    children = scheduler_state.get("children") if isinstance(scheduler_state, dict) else None
    children = children if isinstance(children, list) else []
    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
    requested_epoch = int(order.get("requested_epoch", 0))
    slug = str(order.get("payload_slug"))
    template = order.get("child_template") if isinstance(order.get("child_template"), Mapping) else {}
    child_kind = str(template.get("kind") or "execute")
    matches = 0
    for entry in children:
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("kind") or "") != child_kind:
            continue
        if _child_row_fire_epoch(entry.get("fire_at")) != requested_epoch:
            continue
        exact_link = str(entry.get("order_id") or "") == order_id
        if not exact_link:
            if slug not in str(entry.get("target") or ""):
                continue
            identity = str(entry.get("automation_id") or "")
            if not identity or identity != str(carrier.get("label") or ""):
                continue
        matches += 1
    return {"unique": matches == 1, "matches": matches, "reason": "ok" if matches == 1 else "no-unique-match"}


def _clocked_order_fire_input(
    *,
    order_id: str,
    ledger_path: os.PathLike | str,
    payload_slug: str,
    repo_root: os.PathLike | str,
) -> str:
    """The JSON operation input naming one order's recorded identity."""

    repo = pathlib.Path(os.path.expanduser(str(repo_root))).resolve()
    return json.dumps(
        {
            "order_id": str(order_id),
            "ledger_path": str(ledger_path),
            "payload_slug": str(payload_slug),
            "repo_root": str(repo),
        },
        sort_keys=True,
    )


def build_clocked_order_fire_prompt(
    *,
    repo_root: os.PathLike | str,
    ledger_path: os.PathLike | str,
    order_id: str,
    payload_slug: str,
    payload_text: str,
    runner: str | None = None,
) -> str:
    """The headless session prompt: first-action prelude, then the payload.

    The prelude (1) performs the existing maintenance child re-arm first
    action pinned in agents/skills/maintenance/duties-core.md with its
    established park-and-continue refusal path preserved, then (2) obtains
    the session's own executor id from the ZCode runtime context - never
    from an inherited environment variable; the launchd shell has none and
    never discharges the order - (3) passes it explicitly through
    ``scripts/session_channel.py --session-id`` (which fails loud on an
    empty id), and (4) invokes the discharge operation with the order id and
    repository root. The stored payload runs only after an accepted
    discharge result; every refusal stops before it. The prompt is DATA:
    the caller passes it to ZCode as one shell-quoted argument.
    """

    repo = pathlib.Path(os.path.expanduser(str(repo_root))).resolve()
    scripts = repo / "scripts"
    runner_path = str(runner or sys.executable or "/usr/bin/python3")
    discharge_input = _clocked_order_fire_input(
        order_id=order_id,
        ledger_path=ledger_path,
        payload_slug=payload_slug,
        repo_root=repo,
    )
    prelude = f"""You are the headless executor session for clocked order {order_id}. Work in the repository root {repo}.

FIRST ACTION, before any gate or phase: perform the maintenance child re-arm first action exactly as pinned in agents/skills/maintenance/duties-core.md (its "FIRST ACTION" paragraph), state-first and without listing first. Preserve its established refusal path: a re-arm refusal records the "rearm_note" field and the paired "pending_rearm" payload copy, then CONTINUES this order (park-and-continue; the refusal is never a dispatch gate).

After the re-arm first action, discharge this clocked order before any other work:
1. Obtain YOUR OWN session id from the ZCode runtime context. Never read it from the environment (never CODEX_SESSION_ID); the launchd shell has no session identity. When the runtime context supplies no session id, STOP: print the refusal "{CLOCKED_ORDER_FIRE_PRELUDE_STOP_REFUSAL}" and do nothing else - no ledger write, no discharge, no payload.
2. Pass that id explicitly through the session channel (it fails loud on an empty id):
   {runner_path} {scripts / "session_channel.py"} --session-id <YOUR_SESSION_ID>
3. Invoke the discharge operation with this order's recorded identity:
   {runner_path} {scripts / "execute_plan_runtime.py"} --operation clocked-order-discharge-on-fire --repo-root {repo} --session-id <YOUR_SESSION_ID> --input {discharge_input}
4. When the operation prints a JSON result whose "status" is "success" and whose "discharged" is true, and only then, continue with the order payload below. On any refusal ("status": "blocked"), error, or non-zero exit, STOP: do not execute the order payload; the order stays recoverable.

----- order payload -----
"""
    return prelude + str(payload_text)


def build_clocked_order_fire_command(
    *,
    repo_root: os.PathLike | str,
    ledger_path: os.PathLike | str,
    order_id: str,
    payload_slug: str,
    payload_text: str,
    executable: str | None = None,
    zcode_executable: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """The env-complete headless launch of one order's payload session.

    Replaces the shell-only discharge invocation for order carriers (the
    witnessed silent-loss incident: the old command discharged the ledger
    and never ran the payload). Every file boundary - the repository root,
    the runtime script, the ledger - is a shell-quoted path, the
    provider-config exports ride in the payload itself, and the whole
    prompt (prelude + stored payload) is ONE shell-quoted argument, so the
    stored prompt text is data to ZCode and never shell syntax. The shell
    registers the 60-minute handoff lease through the ledger (begin-fire)
    before starting ``zcode --prompt`` in the recorded repository root; a
    refused lease exits the begin-fire leg with the runtime CLI's distinct
    begin-fire refusal exit, so the ``&&`` chain stops before the launch
    (no session, no clear-fire), and a launch that exits nonzero clears
    the lease under the lock (clear-fire) and propagates the failure exit.
    """

    repo = pathlib.Path(os.path.expanduser(str(repo_root))).resolve()
    script = repo / "scripts" / "execute_plan_runtime.py"
    runner = executable or sys.executable or "/usr/bin/python3"
    zcode = str(zcode_executable or "zcode")
    fire_input = _clocked_order_fire_input(
        order_id=order_id,
        ledger_path=ledger_path,
        payload_slug=payload_slug,
        repo_root=repo,
    )
    prompt = build_clocked_order_fire_prompt(
        repo_root=repo,
        ledger_path=ledger_path,
        order_id=order_id,
        payload_slug=payload_slug,
        payload_text=payload_text,
        runner=str(runner),
    )
    exports = clocked_order_provider_config_exports(environ)
    parts = []
    if exports:
        parts.append(exports)
    parts.append(f"cd {shlex.quote(str(repo))}")
    parts.append(
        f"{shlex.quote(str(runner))} {shlex.quote(str(script))}"
        " --operation clocked-order-begin-fire"
        f" --repo-root {shlex.quote(str(repo))}"
        f" --input {shlex.quote(fire_input)}"
    )
    launch = f"{shlex.quote(zcode)} --prompt {shlex.quote(prompt)} --cwd {shlex.quote(str(repo))}"
    clear = (
        f"{shlex.quote(str(runner))} {shlex.quote(str(script))}"
        " --operation clocked-order-clear-fire"
        f" --repo-root {shlex.quote(str(repo))}"
        ' --launcher-exit-code "$fire_rc"'
        f" --input {shlex.quote(fire_input)}"
    )
    # The launch segment is a brace group inside the && chain: a refused
    # begin-fire (nonzero) short-circuits before it - no session, no
    # clear-fire - while a failed launch inside the group still clears the
    # lease and propagates the failure exit.
    parts.append(f"{{ {launch}; fire_rc=$?; if [ \"$fire_rc\" -ne 0 ]; then {clear}; fi; exit \"$fire_rc\"; }}")
    return " && ".join(parts)


def _drain_running_fire_process(
    order_id: str,
    *,
    timeout_seconds: float = 30.0,
    poll_seconds: float = 0.5,
) -> dict[str, Any]:
    """Bounded drain of a running legacy fire process for one order.

    The legacy shell-only fire command embeds the exact order id in its
    ``--input`` JSON, so a live ``pgrep -f <order id>`` match is evidence a
    fire is still running; this process and its parent (the operator shell
    that invoked the migration carrying the same id in its own argv) are
    excluded. The drain waits until the match clears or the bounded timeout
    expires, so the ledger rewrite never races an in-flight discharge.
    """

    deadline = time.monotonic() + float(timeout_seconds)
    own_pids = {os.getpid(), os.getppid()}
    while True:
        try:
            probe = subprocess.run(
                ["pgrep", "-f", re.escape(str(order_id))],
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, ValueError):
            return {"drained": True, "reason": "pgrep-unavailable", "matches": []}
        matches = [
            int(line)
            for line in probe.stdout.split()
            if line.strip().isdigit() and int(line) not in own_pids
        ]
        if not matches:
            return {"drained": True, "reason": "no-running-fire-process", "matches": []}
        if time.monotonic() >= deadline:
            return {"drained": False, "reason": "drain-timeout", "matches": matches}
        time.sleep(float(poll_seconds))


def derive_requested_epoch(requested_at_iso: str) -> int:
    """The authoritative epoch derived from the operator's local ISO (A2).

    A naive ISO string is read in the machine's local zone; the epoch
    derived from the recorded ISO at schedule time is the authority.
    """

    moment = datetime.fromisoformat(str(requested_at_iso).strip())
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return int(moment.timestamp())


def request_epoch_refusal(requested_at_iso: str) -> str | None:
    """The named A2 refusal for a requested time, or None when acceptable.

    Sub-minute precision is refused (the carrier's calendar granularity is
    minutes), and an ISO whose re-derived epoch disagrees with the recorded
    wall clock (a nonexistent local time across a spring-forward boundary)
    refuses the schedule.
    """

    moment = datetime.fromisoformat(str(requested_at_iso).strip())
    if moment.second or moment.microsecond:
        return "clocked-order-refused-sub-minute-precision"
    epoch = derive_requested_epoch(requested_at_iso)
    rederived = datetime.fromtimestamp(epoch)
    if moment.tzinfo is not None:
        rederived = rederived.astimezone(moment.tzinfo)
    if rederived.replace(tzinfo=None) != moment.replace(tzinfo=None):
        return "clocked-order-refused-iso-epoch-mismatch"
    return None


def next_local_occurrence_epoch(hour: int, minute: int, now_epoch: float) -> int:
    """The next local occurrence of one calendar HH:MM at or after now.

    The arming proof's reader: launchd's ``StartCalendarInterval`` fires at
    the next occurrence of its wall-clock fields, so the armed fire epoch is
    derived from those fields and compared against the requested epoch (A3).
    """

    moment = datetime.fromtimestamp(int(now_epoch)).astimezone()
    candidate = moment.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if candidate.timestamp() < int(now_epoch):
        candidate += timedelta(days=1)
    return int(candidate.timestamp())


class ClockedOrderLedgerReadError(Exception):
    """The strict ledger read failed (unreadable, malformed, or non-object)."""


class ClockedOrderLedger:
    """The order ledger: a standalone store over ``clocked-orders.json``.

    Not a ``WatcherStateAdapter`` subclass (A8); the closed state set is
    ``pending`` (recorded, not armed; includes parked orders awaiting
    pickup), ``armed`` (a carrier receipt exists), ``discharged`` (consumed
    exactly once), ``cancelled`` (terminal by explicit request), and
    ``missed`` (terminal; the requested time passed undischarged, so its
    error records once). Every observation and every transition is lock-held
    (the shared ``.lock`` file beside the state file), the state is written
    through temp-file atomic replace, and each transition appends to the
    order's history under the lock. Payload copies live in the
    ``clocked-order-payloads/`` home beside the ledger and are retained
    until the order reaches a terminal state plus one day - except a
    discharged order, whose copy anchors on its recovery instead of its
    terminal boundary: recovery unresolved (no recorded
    ``payload_recovery_disposition_at_epoch``) keeps the copy indefinitely
    as the only repair input, and a recorded disposition (only an archived
    execution plan or a durable paired retry records one, exactly once,
    through the pre-sweep reconciliation) retains it at least 41 further
    days before the sweep deletes it (plan
    2026-11-08-clocked-order-payload-session-execution Tasks 2 and 3).
    """

    RETENTION_SECONDS = 86_400
    # The post-disposition retention horizon: at least 41 days from the
    # recorded recovery disposition, covering the quota probe's maximum
    # 40-day reset horizon plus the 10-minute carrier margin (plan
    # 2026-11-08-clocked-order-payload-session-execution Task 3).
    PAYLOAD_RECOVERY_RETENTION_SECONDS = 41 * 86_400

    def __init__(
        self,
        ledger_path: os.PathLike | str,
        payload_home: os.PathLike | str,
        *,
        repo_root: os.PathLike | str,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._ledger_path = pathlib.Path(ledger_path)
        self._payload_home = pathlib.Path(payload_home)
        self._repo_root = str(pathlib.Path(os.path.expanduser(str(repo_root))).resolve())
        self._clock = clock

    @property
    def ledger_path(self) -> pathlib.Path:
        return self._ledger_path

    @property
    def payload_home(self) -> pathlib.Path:
        return self._payload_home

    @property
    def repo_root(self) -> str:
        return self._repo_root

    def payload_copy_path(self, order_id: str) -> pathlib.Path:
        """The order's payload copy: ``<payload home>/<order id>.md`` (A1)."""

        return self._payload_home / f"{order_id}.md"

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            state = json.loads(self._ledger_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if not isinstance(state, dict):
            state = {}
        state.setdefault("orders", {})
        return state

    def _write_unlocked(self, state: dict[str, Any]) -> None:
        state["updated_at_epoch"] = float(self._clock())
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._ledger_path.with_name(self._ledger_path.name + ".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self._ledger_path)

    def read_strict(self) -> dict[str, Any]:
        """Lock-held fail-closed read of the whole ledger.

        Mirrors the fail-open ``_read_unlocked`` shape but raises
        :class:`ClockedOrderLedgerReadError` instead of substituting an
        empty state, for operations that must never report findings over a
        silently-unreadable ledger (the verify-successor leg).
        """

        with authoring_state_lock(self._ledger_path):
            try:
                state = json.loads(self._ledger_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise ClockedOrderLedgerReadError(
                    f"clocked-order ledger {self._ledger_path} is unreadable or malformed: {error}"
                ) from error
            if not isinstance(state, dict):
                raise ClockedOrderLedgerReadError(
                    f"clocked-order ledger {self._ledger_path} holds non-object JSON"
                )
            return state

    def read(self) -> dict[str, Any]:
        """Lock-held read of the whole ledger."""

        with authoring_state_lock(self._ledger_path):
            return self._read_unlocked()

    def order(self, order_id: str) -> dict[str, Any] | None:
        """Lock-held read of one order, or None when unrecorded."""

        order = (self.read().get("orders") or {}).get(str(order_id))
        return dict(order) if isinstance(order, Mapping) else None

    def orders(self) -> list[dict[str, Any]]:
        """Lock-held read of every order."""

        return [dict(value) for value in (self.read().get("orders") or {}).values()]

    def record_order(
        self,
        *,
        order_id: str,
        requested_at_iso: str,
        requested_epoch: int,
        payload_text: str,
        payload_slug: str,
    ) -> dict[str, Any]:
        """Record one pending order with its payload copy and digest (A1, A4).

        The payload copy is written to its ledger path first, and the
        recorded digest is the sha256 of the copy bytes - the discharge's
        copy-tamper check recomputes it against the same file.
        """

        now = float(self._clock())
        with authoring_state_lock(self._ledger_path):
            state = self._read_unlocked()
            orders = state["orders"]
            if str(order_id) in orders:
                raise ValueError(f"clocked order id already recorded: {order_id}")
            copy_path = self.payload_copy_path(order_id)
            copy_path.parent.mkdir(parents=True, exist_ok=True)
            copy_path.write_text(payload_text, encoding="utf-8")
            order = {
                "order_id": str(order_id),
                "state": "pending",
                "requested_at_iso": str(requested_at_iso),
                "requested_epoch": int(requested_epoch),
                "payload_path": str(copy_path),
                "payload_digest": hashlib.sha256(copy_path.read_bytes()).hexdigest(),
                "payload_slug": str(payload_slug),
                "target_repo_root": self._repo_root,
                "carrier": {"armed": False, "reason": "not-armed-yet"},
                "created_at_epoch": now,
                "updated_at_epoch": now,
                "history": [
                    {
                        "event": "order-recorded",
                        "at_epoch": now,
                        "requested_at_iso": str(requested_at_iso),
                        "requested_epoch": int(requested_epoch),
                    }
                ],
            }
            orders[order["order_id"]] = order
            self._write_unlocked(state)
            return dict(order)

    def mutate(
        self,
        order_id: str,
        *,
        event: str,
        from_states: set[str] | None = None,
        to_state: str | None = None,
        carrier: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
        history_extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """The one compare-and-set order transition under the ledger lock.

        Blocked without mutation when the order is unknown or its current
        state is outside ``from_states`` (``None`` admits every state); a
        success replaces the carrier record, applies ``extra``, moves the
        state, stamps the terminal boundary, appends the history event, and
        sweeps the payload-copy home - all in one locked atomic write. The
        body is the lock-held :meth:`_mutate_unlocked` helper: public
        wrappers acquire the lock exactly once and delegate, so a caller
        already inside the critical section can never nest a second flock.
        """

        with authoring_state_lock(self._ledger_path):
            return self._mutate_unlocked(
                order_id,
                event=event,
                from_states=from_states,
                to_state=to_state,
                carrier=carrier,
                extra=extra,
                history_extra=history_extra,
            )

    def _mutate_unlocked(
        self,
        order_id: str,
        *,
        event: str,
        from_states: set[str] | None = None,
        to_state: str | None = None,
        carrier: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
        history_extra: Mapping[str, Any] | None = None,
        now: float | None = None,
    ) -> dict[str, Any]:
        """The mutate body without the lock (the caller holds it)."""

        now = float(self._clock()) if now is None else float(now)
        state = self._read_unlocked()
        orders = state["orders"]
        order = orders.get(str(order_id))
        if not isinstance(order, Mapping):
            return {"status": "blocked", "reason_code": "clocked-order-unknown-order", "cas_applied": False}
        if from_states is not None and order.get("state") not in set(from_states):
            return {
                "status": "blocked",
                "reason_code": "clocked-order-state-conflict",
                "current_state": order.get("state"),
                "cas_applied": False,
                "order": dict(order),
            }
        if carrier is not None:
            order["carrier"] = dict(carrier)
        if extra:
            order.update(extra)
        if to_state is not None:
            order["state"] = to_state
        if order.get("state") in CLOCKED_ORDER_TERMINAL_STATES and "terminal_at_epoch" not in order:
            order["terminal_at_epoch"] = now
        order["updated_at_epoch"] = now
        record = {"event": str(event), "at_epoch": now, "state": order.get("state")}
        if history_extra:
            record.update(history_extra)
        order.setdefault("history", []).append(record)
        self._sweep_payload_copies_unlocked(orders, now)
        self._write_unlocked(state)
        return {"status": "success", "reason_code": str(event), "order": dict(order), "cas_applied": True}

    def _sweep_payload_copies_unlocked(self, orders: Mapping[str, Any], now: float) -> None:
        """The payload-copy retention rule (A1 plus the recovery horizon).

        A non-discharged terminal order (missed, cancelled) sweeps one day
        after its terminal boundary (A1). A discharged order anchors on its
        recovery instead of its terminal boundary: no recorded
        ``payload_recovery_disposition_at_epoch`` (the linked child failed
        without a durable paired retry, has not resolved at all, or only
        checkbox progress or ``outcome: progress`` is observed) is never
        swept - the payload is the only repair input and is kept
        indefinitely; a recorded disposition (only an archived execution
        plan or a durable paired retry records one, exactly once, through
        the pre-sweep reconciliation) retains the copy at least 41 further
        days from the disposition timestamp, and the sweep deletes it only
        after that horizon (plan
        2026-11-08-clocked-order-payload-session-execution Tasks 2 and 3).
        """

        for order in orders.values():
            if order.get("state") not in CLOCKED_ORDER_TERMINAL_STATES or order.get("payload_swept"):
                continue
            if order.get("state") == "discharged":
                # Retention arithmetic anchors on the disposition
                # timestamp, never on ``terminal_at_epoch``: discharge is
                # handoff evidence only, and the payload stays the repair
                # input until recovery resolves.
                disposition_at = order.get("payload_recovery_disposition_at_epoch")
                if not isinstance(disposition_at, (int, float)) or isinstance(disposition_at, bool):
                    continue
                if now - float(disposition_at) < self.PAYLOAD_RECOVERY_RETENTION_SECONDS:
                    continue
            else:
                terminal_at = float(order.get("terminal_at_epoch") or 0.0)
                if not terminal_at or now - terminal_at < self.RETENTION_SECONDS:
                    continue
            try:
                self.payload_copy_path(str(order["order_id"])).unlink()
            except OSError:
                pass
            order["payload_swept"] = True
            order.setdefault("history", []).append({"event": "payload-copy-swept", "at_epoch": now})

    def begin_fire(self, order_id: str) -> dict[str, Any]:
        """Register the order's 60-minute handoff lease (one locked write).

        The fire wrapper calls this before starting ZCode. One critical
        section over the unlocked read/write primitives - no nested
        ``mutate`` (recursive flock would deadlock): the order must be
        known, pending or armed, due (not before its requested minute), and
        free of a live lease; a refused lease starts no session. The runtime
        CLI turns every blocked refusal into its distinct begin-fire
        refusal exit, so the generated command's ``&&`` chain stops before
        the launch (and before the clear-fire leg behind it). The public
        wrapper acquires the ledger lock exactly once and delegates to the
        lock-held :meth:`_begin_fire_locked`.
        """

        with authoring_state_lock(self._ledger_path):
            return self._begin_fire_locked(order_id, now=float(self._clock()))

    def _begin_fire_locked(self, order_id: str, *, now: float) -> dict[str, Any]:
        """The begin-fire body without the lock (the caller holds it)."""

        state = self._read_unlocked()
        orders = state["orders"]
        order = orders.get(str(order_id))
        if not isinstance(order, Mapping):
            return {"status": "blocked", "reason_code": "clocked-order-unknown-order", "cas_applied": False}
        current_state = order.get("state")
        if current_state not in ("pending", "armed"):
            return {
                "status": "blocked",
                "reason_code": "clocked-order-terminal-state",
                "current_state": current_state,
                "order": dict(order),
                "cas_applied": False,
            }
        requested_epoch = int(order.get("requested_epoch", 0))
        if now < requested_epoch:
            return {
                "status": "blocked",
                "reason_code": "clocked-order-refused-early-fire",
                "requested_epoch": requested_epoch,
                "order": dict(order),
                "cas_applied": False,
            }
        live_until = order.get("handoff_lease_until_epoch")
        if isinstance(live_until, (int, float)) and not isinstance(live_until, bool) and now < float(live_until):
            return {
                "status": "blocked",
                "reason_code": "clocked-order-handoff-lease-live",
                "handoff_lease_until_epoch": float(live_until),
                "order": dict(order),
                "cas_applied": False,
            }
        lease_until = now + float(CLOCKED_ORDER_HANDOFF_LEASE_SECONDS)
        order["handoff_lease_until_epoch"] = lease_until
        order["updated_at_epoch"] = now
        order.setdefault("history", []).append(
            {
                "event": "handoff-lease-registered",
                "at_epoch": now,
                "handoff_lease_until_epoch": lease_until,
            }
        )
        self._write_unlocked(state)
        return {
            "status": "success",
            "reason_code": "handoff-lease-registered",
            "handoff_lease_until_epoch": lease_until,
            "order": dict(order),
            "cas_applied": True,
        }

    def clear_fire(self, order_id: str, *, launcher_exit_code: int | None = None) -> dict[str, Any]:
        """Clear the order's handoff lease after a failed launch (one locked
        write), so the due scan can recover the order without waiting for
        the expiry. Bookkeeping only: it never writes an order-discharged
        event and never changes the order state; a launcher exit code the
        caller carries in records one ``launch-failed`` history entry
        before the lease-clear entry, gated on the order still being
        pending or armed, so a post-discharge launcher crash records none;
        the public wrapper acquires the ledger lock exactly once and
        delegates to the lock-held :meth:`_clear_fire_locked`."""

        with authoring_state_lock(self._ledger_path):
            return self._clear_fire_locked(order_id, launcher_exit_code=launcher_exit_code, now=float(self._clock()))

    def _clear_fire_locked(self, order_id: str, *, launcher_exit_code: int | None = None, now: float) -> dict[str, Any]:
        """The clear-fire body without the lock (the caller holds it)."""

        state = self._read_unlocked()
        orders = state["orders"]
        order = orders.get(str(order_id))
        if not isinstance(order, Mapping):
            return {"status": "blocked", "reason_code": "clocked-order-unknown-order", "cas_applied": False}
        if "handoff_lease_until_epoch" not in order:
            return {
                "status": "blocked",
                "reason_code": "clocked-order-handoff-lease-absent",
                "order": dict(order),
                "cas_applied": False,
            }
        if launcher_exit_code is not None and str(order.get("state")) in ("pending", "armed"):
            order.setdefault("history", []).append(
                {"event": "launch-failed", "at_epoch": now, "launcher_exit_code": int(launcher_exit_code)}
            )
        order.pop("handoff_lease_until_epoch", None)
        order["updated_at_epoch"] = now
        order.setdefault("history", []).append({"event": "handoff-lease-cleared", "at_epoch": now})
        self._sweep_payload_copies_unlocked(orders, now)
        self._write_unlocked(state)
        return {
            "status": "success",
            "reason_code": "handoff-lease-cleared",
            "order": dict(order),
            "cas_applied": True,
        }

    def discharge_first_action(
        self,
        order_id: str,
        *,
        session_id: str,
        payload_slug: Any = None,
        fired_repo_root: str | None = None,
    ) -> dict[str, Any]:
        """The session's first action: validate, record the id, discharge.

        ONE critical section (plan
        2026-11-08-clocked-order-payload-session-execution Task 2): the
        existing ledger lock spans the full order validation, the live
        handoff-lease check, the executor-session-id recording on the exact
        order, and the pending/armed-to-discharged compare-and-swap, through
        the lock-held :meth:`_discharge_first_action_locked` helper that
        never reacquires the lock. Only the first session entering the
        section records its id; a competing session waits, re-reads the
        complete order, then refuses without replacing the winner. A
        refused identity, digest, target, or lease discharges nothing, so
        the stored payload never runs.
        """

        with authoring_state_lock(self._ledger_path):
            return self._discharge_first_action_locked(
                order_id,
                session_id=str(session_id or "").strip(),
                payload_slug=payload_slug,
                fired_repo_root=str(fired_repo_root) if fired_repo_root is not None else None,
            )

    def _discharge_first_action_locked(
        self,
        order_id: str,
        *,
        session_id: str,
        payload_slug: Any,
        fired_repo_root: str | None,
    ) -> dict[str, Any]:
        """The first-action body without the lock (the caller holds it).

        Returns a verdict dict: ``verdict`` names the outcome
        (``unknown-order``, ``blocked``, ``early-fire``, ``discharged``),
        ``requested_epoch`` carries the in-section order's requested time,
        ``update`` is the exact blocked-result payload for the CLI handler,
        and a ``discharged`` verdict already consumed the order sentinel
        inside the same critical section.
        """

        now = float(self._clock())
        state = self._read_unlocked()
        order = state["orders"].get(str(order_id))
        if not isinstance(order, Mapping):
            return {"verdict": "unknown-order", "requested_epoch": None}
        requested_epoch = int(order.get("requested_epoch", 0))
        late_by = int(now - requested_epoch)
        if order.get("state") == "discharged":
            # The exactly-once fence seen from inside the critical section:
            # a concurrent fire that waited on the lock and a late duplicate
            # fire are indistinguishable here, so ``discharged`` stays false
            # (this fire discharged nothing) and the additive marker names
            # the already-discharged order.
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-duplicate-fire",
                    "discharged": False,
                    "already_discharged": True,
                    "evidence": [f"clocked order {order_id} was already discharged"],
                },
            }
        if order.get("state") not in ("pending", "armed"):
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-terminal-state",
                    "current_state": order.get("state"),
                    "evidence": [f"clocked order {order_id} is terminal: {order.get('state')}"],
                },
            }
        # The A4 target-identity check: the canonical repository root plus
        # the payload slug, both recorded and compared; a mismatch refuses
        # without state change.
        if payload_slug is not None and str(payload_slug) != str(order.get("payload_slug")):
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-stale-target",
                    "evidence": [
                        f"payload slug {payload_slug} does not name the recorded target {order.get('payload_slug')}"
                    ],
                },
            }
        if fired_repo_root is not None and fired_repo_root != str(order.get("target_repo_root")):
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-stale-target",
                    "evidence": [
                        f"firing repository root {fired_repo_root} does not match the recorded target {order.get('target_repo_root')}"
                    ],
                },
            }
        # The A4 copy-tamper check: the digest recorded at schedule time is
        # recomputed against the payload copy; a mismatch refuses without
        # state change.
        live_digest = file_digest(order.get("payload_path"))
        if live_digest is None or live_digest != order.get("payload_digest"):
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-payload-digest-mismatch",
                    "evidence": [f"payload copy {order.get('payload_path')} does not match the recorded digest"],
                },
            }
        if now < requested_epoch:
            # Early fire: discharge nothing here; the handler consumes the
            # sentinel and runs the re-arm check outside the lock (the
            # re-arm path acquires the ledger lock itself).
            return {"verdict": "early-fire", "requested_epoch": requested_epoch, "order": dict(order)}
        # The session identity check (fail-closed before any ledger write):
        # the executor id comes from the headless ZCode runtime context and
        # rides the explicit --session-id input; a legacy shell-only fire
        # supplies none and never discharges the order.
        if not session_id:
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-refused-missing-session-identity",
                    "discharged": False,
                    "evidence": [
                        "no executor session id was supplied; the id must come from the ZCode runtime "
                        "context through the explicit --session-id input (the launchd shell never discharges the order)"
                    ],
                },
            }
        # The handoff lease check: the wrapper's begin-fire must have
        # registered a lease that is still live; a missing or expired lease
        # refuses (the due scan owns recovery once the lease expired).
        lease_until = order.get("handoff_lease_until_epoch")
        if (
            not isinstance(lease_until, (int, float))
            or isinstance(lease_until, bool)
            or now >= float(lease_until)
        ):
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-refused-handoff-lease",
                    "discharged": False,
                    "handoff_lease_until_epoch": lease_until if isinstance(lease_until, (int, float)) else None,
                    "evidence": [
                        "no live handoff lease on the order; begin-fire must register one before the session starts"
                    ],
                },
            }
        outcome = self._mutate_unlocked(
            order_id,
            event="order-discharged",
            # armed is admitted beside pending: a scheduled order is armed by
            # the time its minute arrives, so pending-only would deadlock the
            # machine (deviation from A4's pending-state wording, recorded).
            from_states={"pending", "armed"},
            to_state="discharged",
            extra={"executor_session_id": session_id},
            history_extra={"executor_session_id": session_id, "late_by_seconds": late_by, "late": late_by > 0},
            now=now,
        )
        if outcome.get("status") != "success":
            # The single consumption was won by a concurrent fire; the CAS
            # refusal is the exactly-once fence.
            return {
                "verdict": "blocked",
                "requested_epoch": requested_epoch,
                "update": {
                    "status": "blocked",
                    "reason_code": "clocked-order-duplicate-fire",
                    "discharged": False,
                    "cas": outcome,
                },
            }
        return {
            "verdict": "discharged",
            "requested_epoch": requested_epoch,
            "late": late_by > 0,
            "late_by_seconds": late_by,
            "sentinel": _consume_order_sentinel(outcome.get("order") or order),
        }

    def classify_due(self, now: float | None = None) -> dict[str, Any]:
        """The A6 missed classification in ONE ledger critical section.

        The whole scan - the order reads, the live-lease re-validation, and
        every missed mutation - runs inside a single acquisition of the
        ledger lock shared with begin-fire (plan
        2026-11-08-clocked-order-payload-session-execution Task 2), so a
        begin-fire that lands before the section leaves a live lease the
        section sees and defers to, and a begin-fire that lands after it
        finds a missed order and refuses the launch; a live session can
        never lose the discharge compare-and-swap to the scan.
        """

        resolved_now = float(self._clock()) if now is None else float(now)
        with authoring_state_lock(self._ledger_path):
            return self._classify_due_locked(resolved_now)

    def _classify_due_locked(self, now: float) -> dict[str, Any]:
        """The classification body without the lock (the caller holds it)."""

        missed: list[dict[str, Any]] = []
        state = self._read_unlocked()
        candidates = [
            str(key)
            for key, value in (state.get("orders") or {}).items()
            if isinstance(value, Mapping)
        ]
        for candidate in candidates:
            # The per-order re-read is the lease re-validation the carried
            # race finding demands: the decision mutates only what this
            # critical section's own read still shows, never a snapshot
            # taken before a concurrent lease write landed.
            order = (self._read_unlocked().get("orders") or {}).get(candidate)
            if not isinstance(order, Mapping):
                continue
            if order.get("state") not in ("pending", "armed"):
                continue
            if int(order.get("requested_epoch", 0)) > int(now):
                continue
            lease_until = order.get("handoff_lease_until_epoch")
            if isinstance(lease_until, (int, float)) and not isinstance(lease_until, bool) and now < float(lease_until):
                # A live handoff lease: the payload session's handoff may be
                # in flight. An expired lease falls through to recovery.
                continue
            carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
            if carrier.get("armed") and carrier.get("fired_marker_path"):
                # Live discharge evidence (A6): a fired marker from the
                # order's carrier record means a discharge is in flight.
                if pathlib.Path(str(carrier["fired_marker_path"])).exists():
                    continue
            outcome = self._mutate_unlocked(
                candidate,
                event="order-missed",
                from_states={"pending", "armed"},
                to_state="missed",
                history_extra={
                    "requested_at_iso": order.get("requested_at_iso"),
                    "requested_epoch": order.get("requested_epoch"),
                },
                now=now,
            )
            if outcome.get("status") == "success":
                missed.append(
                    {
                        "order_id": candidate,
                        "requested_at_iso": order.get("requested_at_iso"),
                        "requested_epoch": order.get("requested_epoch"),
                    }
                )
        return {"missed": missed}

    def record_paired_retry(self, order_id: str, retry_order_id: str) -> dict[str, Any]:
        """Record the paired retry reference on one unresolved order.

        The reference (the retry order id whose own payload copy is durable
        in the payload home) is stored before any recovery disposition can
        be recorded from it; recording again with the same reference is
        idempotent.
        """

        with authoring_state_lock(self._ledger_path):
            state = self._read_unlocked()
            orders = state["orders"]
            order = orders.get(str(order_id))
            if not isinstance(order, Mapping):
                return {"status": "blocked", "reason_code": "clocked-order-unknown-order", "cas_applied": False}
            now = float(self._clock())
            if order.get("payload_recovery_retry_ref") == str(retry_order_id):
                return {"status": "success", "reason_code": "paired-retry-recorded", "order": dict(order), "cas_applied": True}
            order["payload_recovery_retry_ref"] = str(retry_order_id)
            order["updated_at_epoch"] = now
            order.setdefault("history", []).append(
                {"event": "paired-retry-recorded", "at_epoch": now, "retry_order_id": str(retry_order_id)}
            )
            self._write_unlocked(state)
            return {"status": "success", "reason_code": "paired-retry-recorded", "order": dict(order), "cas_applied": True}

    def reconcile_child_projection(
        self,
        scheduler_state_path: os.PathLike | str | None = None,
        *,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Repair the scheduler child projection and replay the mirrors.

        Lock order: the scheduler-state lock first, then this ledger's -
        never reversed (plan
        2026-11-08-clocked-order-payload-session-execution Task 2). Inside
        the paired section, per order with a stored child template: a
        removed or field-stripped ``children[]`` row is rebuilt from the
        template; a durable row outcome the order mirror lacks is replayed
        onto the mirror idempotently (a crash between the state outcome and
        the mirror write repairs on restart); a discharged order whose
        child never showed progress fails at the six-hour horizon on both
        surfaces; a row a stale Step 6 rewrite reset to ``pending`` follows
        the canonical mirror back; and a durable paired retry or the
        linked execution plan's archived copy records the recovery
        disposition exactly once. A missing or unreadable
        scheduler state is reported, never guessed at.
        """

        resolved_now = float(self._clock()) if now is None else float(now)
        path = (
            pathlib.Path(os.path.expanduser(str(scheduler_state_path)))
            if scheduler_state_path
            else pathlib.Path(self._repo_root) / ".ai-playbook" / "scheduler-state.json"
        )
        report: dict[str, Any] = {
            "scheduler_state": "absent",
            "restored_rows": 0,
            "restored_fields": 0,
            "replayed_mirrors": 0,
            "horizon_failed": 0,
            "dispositions": 0,
        }
        # The pre-lock pass is an existence/format probe only: the document
        # is re-read and re-parsed inside the scheduler lock, so the
        # whole-document replace below can never revert a concurrent
        # targeted edit that landed between the probe and the lock.
        children: list[Any] | None = None
        scheduler_state: dict[str, Any] | None = None
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                report["scheduler_state"] = "unreadable"
                return report
            if not isinstance(loaded, dict):
                report["scheduler_state"] = "malformed"
                return report
            scheduler_state = loaded
            report["scheduler_state"] = "ok"
        # Lock order: the scheduler-state lock first, then this ledger's -
        # never reversed. With no scheduler state there is no row surface to
        # repair and the scheduler lock is not taken at all.
        scheduler_lock = authoring_state_lock(path) if scheduler_state is not None else contextlib.nullcontext()
        with scheduler_lock:
            if scheduler_state is not None:
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    report["scheduler_state"] = "unreadable"
                    return report
                if not isinstance(loaded, dict):
                    report["scheduler_state"] = "malformed"
                    return report
                scheduler_state = loaded
            if scheduler_state is not None:
                raw_children = scheduler_state.get("children")
                children = raw_children if isinstance(raw_children, list) else []
            with authoring_state_lock(self._ledger_path):
                ledger_state = self._read_unlocked()
                orders = ledger_state.get("orders") or {}
                ledger_dirty = False
                scheduler_dirty = False
                for order_id, order in list(orders.items()):
                    if not isinstance(order, Mapping):
                        continue
                    template = order.get("child_template")
                    if not isinstance(template, Mapping):
                        continue
                    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
                    order_state = order.get("state")
                    mirror = order.get("payload_recovery_outcome")
                    row = None
                    if children is not None:
                        row = next(
                            (
                                entry
                                for entry in children
                                if isinstance(entry, Mapping) and str(entry.get("order_id") or "") == str(order_id)
                            ),
                            None,
                        )
                        if row is None:
                            # The legacy-row fallback: a migrated order's
                            # surviving scheduler row predates the
                            # ``order_id`` link, so the unique kind + fire
                            # epoch + target + carrier-label match is stamped
                            # with the link instead of duplicated; ambiguous
                            # or missing legacy matches stay disabled for
                            # operator recovery.
                            child_kind = str(template.get("kind") or "execute")
                            requested_epoch = int(order.get("requested_epoch", 0))
                            slug = str(order.get("payload_slug"))
                            legacy = [
                                entry
                                for entry in children
                                if isinstance(entry, Mapping)
                                and not str(entry.get("order_id") or "")
                                and str(entry.get("kind") or "") == child_kind
                                and _child_row_fire_epoch(entry.get("fire_at")) == requested_epoch
                                and slug in str(entry.get("target") or "")
                                and str(entry.get("automation_id") or "")
                                and str(entry.get("automation_id")) == str(carrier.get("label") or "")
                            ]
                            if len(legacy) == 1:
                                row = legacy[0]
                                row["order_id"] = str(order_id)
                                scheduler_dirty = True
                                report["restored_fields"] += 1
                    # Dispatch evidence gates the restore: a parked order (the
                    # refusal mutate stored the template while the carrier
                    # disarmed, and no row was ever written) proves no
                    # dispatch, and a discharged order whose recovery already
                    # resolved has no live row to rebuild - only an armed
                    # carrier or a discharge with recovery still unresolved
                    # proves a row existed and may need rebuilding.
                    dispatched = carrier.get("armed") is True or (
                        order_state == "discharged" and mirror in (None, "pending", "in_progress")
                    )
                    # 1. Restore a removed row (or its stripped projection
                    # fields) from the stored template: target, kind, and the
                    # dispatch-time progress baseline are never guessed.
                    if children is not None and order_state in ("pending", "armed", "discharged") and dispatched:
                        if row is None:
                            row = dict(template)
                            children.append(row)
                            scheduler_dirty = True
                            report["restored_rows"] += 1
                        else:
                            for field in CLOCKED_ORDER_CHILD_TEMPLATE_FIELDS:
                                if row.get(field) in (None, "") and template.get(field) is not None:
                                    row[field] = template[field]
                                    scheduler_dirty = True
                                    report["restored_fields"] += 1
                    # 2. Replay a durable row outcome the mirror lacks: the
                    # child row is the evidence a crash left behind.
                    row_outcome = row.get("outcome") if isinstance(row, Mapping) else None
                    if isinstance(row_outcome, str) and row_outcome != "pending" and row_outcome != mirror:
                        order["payload_recovery_outcome"] = row_outcome
                        mirror = row_outcome
                        order["updated_at_epoch"] = resolved_now
                        order.setdefault("history", []).append(
                            {"event": "payload-recovery-mirror-replayed", "at_epoch": resolved_now, "outcome": row_outcome}
                        )
                        ledger_dirty = True
                        report["replayed_mirrors"] += 1
                    # 3. The six-hour no-progress horizon on a discharged
                    # order: still pending with no progress outcome fails on
                    # both surfaces (the ordinary pending-child check).
                    if (
                        order_state == "discharged"
                        and mirror in (None, "pending", "in_progress")
                        and resolved_now >= int(order.get("requested_epoch", 0)) + CLOCKED_ORDER_PAYLOAD_RECOVERY_HORIZON_SECONDS
                    ):
                        order["payload_recovery_outcome"] = "failed"
                        mirror = "failed"
                        order["updated_at_epoch"] = resolved_now
                        order.setdefault("history", []).append(
                            {"event": "payload-recovery-progress-horizon-elapsed", "at_epoch": resolved_now}
                        )
                        ledger_dirty = True
                        report["horizon_failed"] += 1
                        if isinstance(row, Mapping) and row.get("outcome") != "failed":
                            row["outcome"] = "failed"
                            scheduler_dirty = True
                    # 4. The canonical mirror wins: a row reset to pending by
                    # a stale Step 6 snapshot follows the mirror back.
                    if (
                        isinstance(row, Mapping)
                        and isinstance(mirror, str)
                        and mirror in ("failed", "progress")
                        and row.get("outcome") == "pending"
                    ):
                        row["outcome"] = mirror
                        scheduler_dirty = True
                        report["restored_fields"] += 1
                    # 5. Recovery disposition, exactly once, and only on
                    # durable evidence: a durable paired retry (the retry
                    # order's payload copy is durable in the payload home)
                    # or the linked execution plan archived under the
                    # facts-resolved plans ``completed/`` directory (plan
                    # 2026-11-08-clocked-order-payload-session-execution
                    # Task 3). Checkbox progress and ``outcome: progress``
                    # are never disposition evidence.
                    if "payload_recovery_disposition_at_epoch" not in order:
                        retry_ref = order.get("payload_recovery_retry_ref")
                        retry_durable = False
                        if retry_ref:
                            retry_order = orders.get(str(retry_ref))
                            if isinstance(retry_order, Mapping) and retry_order.get("payload_path"):
                                try:
                                    retry_durable = pathlib.Path(str(retry_order["payload_path"])).exists()
                                except OSError:
                                    retry_durable = False
                        plan_archived = False if retry_durable else _linked_clocked_plan_archived(self._repo_root, order)
                        if retry_durable or plan_archived:
                            order["payload_recovery_disposition_at_epoch"] = resolved_now
                            order["updated_at_epoch"] = resolved_now
                            order.setdefault("history", []).append(
                                {"event": "payload-recovery-disposition-recorded", "at_epoch": resolved_now}
                            )
                            ledger_dirty = True
                            report["dispositions"] += 1
                if scheduler_dirty and scheduler_state is not None:
                    # The keep-last-20 cap binds every appending writer in the
                    # same atomic replace (state-file.md's children retention
                    # pin): the restore arm may have appended rows, so the
                    # replace writes the trimmed list, never the raw append.
                    scheduler_state["children"] = children[-20:]
                    _atomic_replace_json(path, scheduler_state)
                if ledger_dirty:
                    self._write_unlocked(ledger_state)
                return report


def _consume_order_sentinel(order: Mapping[str, Any]) -> dict[str, Any]:
    """Consume the order carrier's one-shot sentinel, receipt-only (G2 shape).

    The consumed sentinel and its fired marker come from the order's
    recorded carrier record and from nothing else; an order without an armed
    launchd carrier consumes nothing.
    """

    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else None
    if carrier is None or carrier.get("armed") is not True or not carrier.get("sentinel_path"):
        return {"consumed": False, "reason": "no-armed-launchd-carrier"}
    fired_marker = carrier.get("fired_marker_path")
    return consume_resume_sentinel(
        str(carrier["sentinel_path"]),
        fired_path=str(fired_marker) if isinstance(fired_marker, str) and fired_marker.strip() else None,
    )


def _parse_naive_as_utc(value: Any) -> datetime | None:
    """ISO-8601 parse mirroring ``parse_iso`` in scripts/rearm_on_touch.py.

    Naive values read as UTC; a ``Z`` suffix reads as ``+00:00``; a
    non-string or unparseable value returns None. Mirrored locally rather
    than imported across modules.
    """

    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _order_attributed_entry_names(order: Mapping[str, Any]) -> list[str]:
    """The names a children[] entry can carry to evidence the order's turn."""

    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
    names = [str(order.get("order_id"))]
    label = carrier.get("label")
    if isinstance(label, str) and label:
        names.append(label)
    return names


def _run_clocked_order_verify_successor(
    ledger: ClockedOrderLedger,
    payload: Mapping[str, Any],
    *,
    repo_root: str,
    clock: Callable[[], float],
) -> dict[str, Any]:
    """The read-only discharged-without-successor verification leg.

    Warning-shaped by contract: no ledger mutation, no state write, no
    refusal that blocks a lane. A discharged order past its grace window
    flags when both successor pointers still name it and no ``children[]``
    entry attributable to the order exists (any outcome counts, ``failed``
    included, because it evidences the turn ran).
    """

    now = float(clock())
    if "grace_minutes" in payload:
        grace_raw = payload.get("grace_minutes")
    else:
        grace_raw = 30
    try:
        grace_minutes = float(grace_raw)
    except (TypeError, ValueError):
        grace_minutes = 0.0
    if not grace_minutes > 0:
        return {
            "operation": "clocked-order-verify-successor",
            "status": "blocked",
            "reason_code": "verify-successor-grace-invalid",
            "evidence": [f"grace_minutes must be a positive number, got {grace_raw!r}"],
        }
    state_path_raw = payload.get("scheduler_state_path")
    if state_path_raw is not None and not isinstance(state_path_raw, str):
        return {
            "operation": "clocked-order-verify-successor",
            "status": "blocked",
            "reason_code": "verify-successor-state-path-invalid",
            "evidence": [f"scheduler_state_path must be a string path, got {state_path_raw!r}"],
        }
    state_path = pathlib.Path(
        os.path.expanduser(str(state_path_raw))
        if state_path_raw
        else str(pathlib.Path(repo_root) / ".ai-playbook" / "scheduler-state.json")
    )
    try:
        ledger_state = ledger.read_strict()
    except ClockedOrderLedgerReadError as error:
        return {
            "operation": "clocked-order-verify-successor",
            "status": "blocked",
            "reason_code": "verify-successor-ledger-unreadable",
            "evidence": [str(error)],
        }
    if not state_path.exists():
        return {
            "operation": "clocked-order-verify-successor",
            "status": "success",
            "flagged": [],
            "note": "no-scheduler-state-file",
        }
    try:
        scheduler_state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {
            "operation": "clocked-order-verify-successor",
            "status": "blocked",
            "reason_code": "verify-successor-state-malformed",
            "evidence": [f"scheduler state {state_path} is unreadable or malformed: {error}"],
        }
    if not isinstance(scheduler_state, dict):
        return {
            "operation": "clocked-order-verify-successor",
            "status": "blocked",
            "reason_code": "verify-successor-state-malformed",
            "evidence": [f"scheduler state {state_path} holds non-object JSON"],
        }

    children = scheduler_state.get("children")
    children = children if isinstance(children, list) else []
    next_turn_raw = scheduler_state.get("next_turn_at")
    next_turn = _parse_naive_as_utc(next_turn_raw)
    parent_raw = scheduler_state.get("parent_automation_id")
    parent_moved: bool | None
    if isinstance(parent_raw, str) and parent_raw:
        parent_moved = None  # decided per order against its names
    else:
        parent_moved = False  # absent or non-string counts as unmoved

    grace_seconds = grace_minutes * 60.0
    flagged: list[dict[str, Any]] = []
    orders_state = ledger_state.get("orders")
    orders_state = orders_state if isinstance(orders_state, dict) else {}
    for order in orders_state.values():
        if not isinstance(order, Mapping):
            continue
        if order.get("state") != "discharged":
            continue
        requested_epoch = int(order.get("requested_epoch", 0))
        if now <= requested_epoch + grace_seconds:
            continue
        names = _order_attributed_entry_names(order)
        attributable = any(
            any(name in str(entry.get(field, "")) for name in names for field in ("automation_id", "cycle", "target", "note"))
            for entry in children
            if isinstance(entry, Mapping)
        )
        if attributable:
            continue
        next_turn_moved = next_turn is not None and int(next_turn.timestamp()) != requested_epoch
        if isinstance(parent_moved, bool):
            parent_left = parent_moved
        else:
            parent_left = parent_raw not in names
        if next_turn_moved and parent_left:
            continue
        evidence = [
            f"next_turn_at={next_turn_raw!r}",
            f"parent_automation_id={parent_raw!r}",
            f"children_entries={len(children)} (none attributable)",
        ]
        flagged.append(
            {
                "order_id": str(order.get("order_id")),
                "requested_at_iso": order.get("requested_at_iso"),
                "requested_epoch": requested_epoch,
                "evidence": evidence,
            }
        )
    return {
        "operation": "clocked-order-verify-successor",
        "status": "success",
        "now_epoch": int(now),
        "flagged": flagged,
    }


def _rearm_order_carrier(ledger: ClockedOrderLedger, order: Mapping[str, Any]) -> dict[str, Any]:
    """The check-and-arm-if-none re-arm from the order's recorded carrier.

    The recorded carrier identity is the only input (the receipt-only G2
    shape): the re-arm never re-derives a launchd identity at fire time - it
    drives the real launchd one-shot scheduler over the recorded job dir,
    sentinel, and label, so one armed receipt per order is kept.
    """

    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else None
    if carrier is None or carrier.get("armed") is not True or not carrier.get("plist_path"):
        return {"scheduled": False, "reason": "no-armed-launchd-carrier-to-rearm"}
    scheduler = LaunchdOneShotScheduler(
        str(carrier["job_dir"]),
        str(carrier["sentinel_path"]),
        label=str(carrier["label"]),
    )
    requested_epoch = int(order["requested_epoch"])
    try:
        rearm_payload_text = pathlib.Path(str(order["payload_path"])).read_text(encoding="utf-8")
    except OSError:
        # The discharge's digest check refuses an unreadable copy anyway;
        # the re-armed carrier simply carries an empty payload section.
        rearm_payload_text = ""
    scheduling = schedule_with_fallback(
        [scheduler, ReportOnlyScheduler()],
        {
            "fire_at_epoch": requested_epoch,
            "resume_at_iso": compute_resume_at_iso(requested_epoch),
            "manual_command": build_clocked_order_fire_command(
                repo_root=str(order["target_repo_root"]),
                ledger_path=str(ledger.ledger_path),
                order_id=str(order["order_id"]),
                payload_slug=str(order["payload_slug"]),
                payload_text=rearm_payload_text,
            ),
            "order_id": str(order["order_id"]),
        },
    )
    if scheduling.get("scheduled"):
        ledger.mutate(
            str(order["order_id"]),
            event="early-fire-rearm",
            from_states={"pending", "armed"},
            to_state="armed",
            history_extra={"rearm_mechanism": scheduling.get("mechanism")},
        )
    else:
        refusal = launchd_refusal_reason(scheduling) or "clocked-order-rearm-refused"
        ledger.mutate(
            str(order["order_id"]),
            event="early-fire-parked",
            from_states={"pending", "armed"},
            to_state="pending",
            carrier={"armed": False, "reason": refusal},
            history_extra={"rearm": scheduling},
        )
    return scheduling


def _migrate_order_carrier(
    ledger: ClockedOrderLedger,
    order_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """The legacy-carrier migration for one pending or armed order (plan
    2026-11-08-clocked-order-payload-session-execution Task 1).

    The recorded carrier receipt is the only identity input (G2): the
    loaded job is booted out, any running legacy fire process drains
    (bounded), and only then is the ledger-locked order re-armed through
    the same job dir, sentinel, and label with the NEW headless fire
    command. The job is bootstrapped and read back - label, fire time, and
    the begin-fire command present - before the cutover completes; a
    refused readback parks the order and preserves the payload.
    """

    def parked(event: str, reason: str, extra: Mapping[str, Any]) -> dict[str, Any]:
        outcome = ledger.mutate(
            order_id,
            event=event,
            from_states={"pending", "armed"},
            to_state="pending",
            carrier={"armed": False, "reason": reason},
            history_extra=dict(extra),
        )
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": reason,
            "order_id": order_id,
            "cas": outcome,
            **{key: value for key, value in extra.items() if key in {"drain", "scheduling", "readback_error", "child_match"}},
        }

    order = ledger.order(order_id)
    if order is None:
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": "clocked-order-unknown-order",
            "order_id": order_id,
        }
    if order.get("state") not in ("pending", "armed"):
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": "clocked-order-terminal-state",
            "current_state": order.get("state"),
            "order_id": order_id,
            "evidence": [f"clocked order {order_id} is terminal: {order.get('state')}; recovery, not migration, owns it"],
        }
    carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
    if not (
        carrier.get("armed") is True
        and carrier.get("plist_path")
        and carrier.get("job_dir")
        and carrier.get("sentinel_path")
        and carrier.get("label")
    ):
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": "clocked-order-migrate-no-armed-launchd-carrier",
            "order_id": order_id,
            "evidence": ["no armed launchd carrier recorded; the payload stays preserved for recovery"],
        }
    plist_path = pathlib.Path(os.path.expanduser(str(carrier["plist_path"])))
    # 1. Boot the loaded legacy job out BEFORE any ledger rewrite.
    bootout: dict[str, Any] = {}
    try:
        bootout = dict(launchctl_bootout(plist_path))
    except OSError as error:
        bootout = {"job": str(plist_path), "error": str(error)}
    try:
        plist_path.unlink(missing_ok=True)
    except OSError:
        pass
    # 2. Drain any running legacy fire process for this order (bounded).
    drain = _drain_running_fire_process(
        order_id,
        timeout_seconds=float(payload.get("drain_seconds", 30.0)),
        poll_seconds=float(payload.get("drain_poll_seconds", 0.5)),
    )
    # Post-drain re-read: a legacy fire may have completed during the drain.
    order = ledger.order(order_id) or {}
    if order.get("state") not in ("pending", "armed"):
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": "clocked-order-migrate-drained-order-terminal",
            "current_state": order.get("state"),
            "order_id": order_id,
            "drain": drain,
            "evidence": ["the legacy fire completed during the drain; the order is terminal"],
        }
    # 2.5 The legacy child match (plan
    # 2026-11-08-clocked-order-payload-session-execution Task 2, Terms):
    # exactly one existing children[] row with the order's target, fire
    # time, kind, and recorded carrier identity; a missing or ambiguous
    # match keeps the job disabled for operator recovery, the payload
    # preserved, and reports the match failure.
    child_match = _match_legacy_child_row(order, payload.get("scheduler_state_path"))
    if not child_match.get("unique"):
        return parked(
            "carrier-migration-parked",
            "clocked-order-migrate-no-unique-child-match",
            {"drain": drain, "child_match": child_match},
        )
    # 3. Re-arm through the recorded identity with the new headless command.
    try:
        payload_text = pathlib.Path(str(order["payload_path"])).read_text(encoding="utf-8")
    except OSError:
        payload_text = ""
    requested_epoch = int(order["requested_epoch"])
    scheduling = schedule_with_fallback(
        [
            LaunchdOneShotScheduler(
                str(carrier["job_dir"]),
                str(carrier["sentinel_path"]),
                label=str(carrier["label"]),
            )
        ],
        {
            "fire_at_epoch": requested_epoch,
            "resume_at_iso": compute_resume_at_iso(requested_epoch),
            "manual_command": build_clocked_order_fire_command(
                repo_root=str(order["target_repo_root"]),
                ledger_path=str(ledger.ledger_path),
                order_id=order_id,
                payload_slug=str(order["payload_slug"]),
                payload_text=payload_text,
            ),
            "order_id": order_id,
        },
    )
    if not scheduling.get("scheduled"):
        return parked(
            "carrier-migration-parked",
            launchd_refusal_reason(scheduling) or "clocked-order-migrate-rearm-refused",
            {"drain": drain, "scheduling": scheduling},
        )
    # 4. Read the job back: original carrier identity, original fire time,
    # new command - before the cutover completes.
    readback_error = None
    try:
        job = plistlib.loads(plist_path.read_bytes())
        fire_at = datetime.fromtimestamp(requested_epoch).astimezone()
        expected_interval = {"Minute": fire_at.minute, "Hour": fire_at.hour}
        arguments = job.get("ProgramArguments")
        command_text = str(arguments[2]) if isinstance(arguments, list) and len(arguments) > 2 else ""
        readback_ok = (
            str(job.get("Label")) == str(carrier["label"])
            and job.get("StartCalendarInterval") == expected_interval
            and "--operation clocked-order-begin-fire" in command_text
            and "--prompt" in command_text
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        readback_ok = False
        readback_error = str(error)
    if not readback_ok:
        try:
            launchctl_bootout(plist_path)
            plist_path.unlink(missing_ok=True)
        except OSError:
            pass
        return parked(
            "carrier-migration-parked",
            "clocked-order-migrate-readback-refused",
            {
                "drain": drain,
                "scheduling": scheduling,
                "readback_error": readback_error,
            },
        )
    # 5. Cutover: the ledger-locked order rewrite preserves the recorded
    # carrier identity verbatim; only the job's command content changed.
    # The stored child template rides the cutover too: a migrated order
    # gets the same template shape and canonical outcome the schedule
    # branch stores at arm - derived from the order's own recorded fields
    # (requested and payload stamps, the creation stamp, and the carrier
    # label the arming gate proved), never invented - so the projection
    # repair rebuilds a lost or stripped legacy row from the order record
    # instead of skipping it. An order that already stores a template or a
    # mirror keeps them verbatim.
    stored_template = order.get("child_template")
    migrate_template = (
        dict(stored_template)
        if isinstance(stored_template, Mapping)
        else build_clocked_order_child_template(
            order_id=order_id,
            payload_slug=str(order["payload_slug"]),
            requested_at_iso=str(order["requested_at_iso"]),
            requested_epoch=int(order["requested_epoch"]),
            created_epoch=float(order["created_at_epoch"]),
            automation_id=str(carrier["label"]),
        )
    )
    template_extra = {
        "child_template": migrate_template,
        "payload_recovery_outcome": str(order.get("payload_recovery_outcome") or "pending"),
    }
    receipt = dict(carrier)
    outcome = ledger.mutate(
        order_id,
        event="carrier-migrated",
        from_states={"pending", "armed"},
        to_state="armed",
        carrier=receipt,
        extra=template_extra,
        history_extra={"migration": {"drain": drain}},
    )
    if outcome.get("status") != "success":
        # A concurrent terminal flip slipped past the post-drain re-read:
        # tear the freshly armed job back down and report; the order state
        # (whatever won) stays authoritative.
        try:
            launchctl_bootout(plist_path)
            plist_path.unlink(missing_ok=True)
        except OSError:
            pass
        return {
            "operation": "clocked-order-migrate-carrier",
            "status": "blocked",
            "reason_code": "clocked-order-migrate-state-conflict",
            "order_id": order_id,
            "drain": drain,
            "cas": outcome,
        }
    return {
        "operation": "clocked-order-migrate-carrier",
        "status": "success",
        "reason_code": "carrier-migrated",
        "order_id": order_id,
        "bootout": bootout,
        "drain": drain,
        "carrier": dict(outcome.get("order", {}).get("carrier") or receipt),
    }


def run_clocked_order_operation(
    kind: str,
    payload: Mapping[str, Any],
    *,
    repo_root: str,
    ledger: ClockedOrderLedger | None = None,
    clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """The ONE CLI handler for the clocked-order operations.

    - ``schedule`` records the pending order (A2 refusals before any ledger
      write), arms it through the existing scheduler adapter chain with the
      per-order identity key, proves A3 (the armed carrier's recorded fire
      time equals the requested epoch), records the full armed receipt, and
      parks on refusal (the state stays pending, the payload copy is
      retained, the report-only result is recorded).
    - ``cancel`` tears the armed carrier down (the supersede-style bootout
      plus sentinel consume, or the automation retirement record) and is
      terminal.
    - ``due`` is the A6 classification: an order whose requested epoch
      passed, still pending or armed, with no fired marker from its carrier
      record (no discharge in flight), is marked missed. The restart
      reconciliation runs first: the scheduler child projection is repaired
      from the stored templates and the outcome mirrors replayed, all under
      the scheduler-state-then-ledger lock order.
    - ``discharge-on-fire`` is the fire payload's entry: it re-reads the
      order, applies the state, payload-digest, and target-identity checks,
      requires the executor session id from the headless runtime context and
      a live handoff lease, consumes the sentinel, discharges exactly once
      while recording the executor id, and re-arms on an early fire without
      discharging.
    - ``begin-fire`` / ``clear-fire`` are the fire wrapper's ledger legs
      (plan 2026-11-08-clocked-order-payload-session-execution Task 1):
      begin-fire registers the 60-minute handoff lease before ZCode starts;
      clear-fire removes it after a failed launch.
    - ``migrate-carrier`` moves a pending or armed legacy shell-only carrier
      to the new headless fire command, preserving the recorded identity and
      fire time.
    """

    def resolved_ledger() -> ClockedOrderLedger:
        nonlocal ledger
        if ledger is None:
            target_root = str(payload.get("repo_root") or repo_root)
            paths = default_clocked_order_ledger_paths(target_root)
            ledger = ClockedOrderLedger(
                payload.get("ledger_path") or paths["ledger_path"],
                payload.get("payload_home") or paths["payload_home"],
                repo_root=target_root,
                clock=clock,
            )
        return ledger

    if kind == "schedule":
        target = resolved_ledger()
        requested_at_iso = str(payload.get("requested_at_iso") or "").strip()
        if not requested_at_iso:
            return {
                "operation": "clocked-order-schedule",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["requested_at_iso is required"],
            }
        try:
            refusal = request_epoch_refusal(requested_at_iso)
        except ValueError:
            refusal = "clocked-order-refused-unparseable-requested-time"
        if refusal is not None:
            return {
                "operation": "clocked-order-schedule",
                "status": "blocked",
                "reason_code": refusal,
                "requested_at_iso": requested_at_iso,
                "evidence": [f"{refusal}: requested_at_iso={requested_at_iso}"],
            }
        requested_epoch = derive_requested_epoch(requested_at_iso)
        payload_slug = str(payload.get("payload_slug") or "").strip()
        payload_text = payload.get("payload_text")
        if payload_text is None:
            source = payload.get("payload_path")
            if not source:
                return {
                    "operation": "clocked-order-schedule",
                    "status": "blocked",
                    "reason_code": "clocked-order-refused-missing-field",
                    "evidence": ["payload_text or payload_path is required"],
                }
            try:
                payload_text = pathlib.Path(os.path.expanduser(str(source))).read_text(encoding="utf-8")
            except OSError as exc:
                return {
                    "operation": "clocked-order-schedule",
                    "status": "blocked",
                    "reason_code": "clocked-order-refused-unreadable-payload",
                    "evidence": [f"payload_path={source} is unreadable: {exc}"],
                }
        if not payload_slug:
            return {
                "operation": "clocked-order-schedule",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["payload_slug is required"],
            }
        order_id = str(payload.get("order_id") or f"co-{uuid.uuid4().hex}")
        try:
            order = target.record_order(
                order_id=order_id,
                requested_at_iso=requested_at_iso,
                requested_epoch=requested_epoch,
                payload_text=str(payload_text),
                payload_slug=payload_slug,
            )
        except ValueError as exc:
            return {
                "operation": "clocked-order-schedule",
                "status": "blocked",
                "reason_code": "clocked-order-refused-duplicate-order-id",
                "order_id": order_id,
                "evidence": [str(exc)],
            }
        # The paired retry reference (plan
        # 2026-11-08-clocked-order-payload-session-execution Task 2): a
        # schedule naming ``retry_for_order`` records the durable retry link
        # on that unresolved order, before any recovery disposition can be
        # recorded from it.
        retry_for_order = str(payload.get("retry_for_order") or "").strip()
        if retry_for_order:
            target.record_paired_retry(retry_for_order, order_id)
        # The arm path: the identity is resolved once here (inside the
        # schedule branch, per the launchd allowed-callers pin) and the
        # chain consumes exactly that resolution, so the order's recorded
        # carrier and the scheduler's armed carrier cannot disagree.
        automation_echo = payload.get("automation") if isinstance(payload.get("automation"), Mapping) else None
        resolved_identity = resolve_clocked_order_identity(
            payload.get("job_dir"),
            payload.get("sentinel_path"),
            order_id,
            target.repo_root,
        )
        launchd_reachable = not (isinstance(automation_echo, Mapping) and automation_echo.get("scheduled") is True)
        if launchd_reachable:
            carrier_record: dict[str, Any] = armed_launchd_identity(
                resolved_identity["job_dir"],
                resolved_identity["sentinel_path"],
                resolved_identity["label"],
            )
        else:
            carrier_record = {
                "armed": True,
                "carrier_form": "automation",
                "automation": dict(automation_echo),
                "fire_epoch": requested_epoch,
            }
        # The complete schema-4 child-entry template stored ON the order
        # (plan 2026-11-08-clocked-order-payload-session-execution Task 2):
        # automation id from the resolved carrier, target and fire time from
        # the recorded request, the initial pending outcome, and the
        # dispatch-time progress baseline - the repair source when a later
        # Step 6 rewrite drops the scheduler-state row or loses a field.
        template_automation_id = None
        if isinstance(carrier_record.get("label"), str) and carrier_record["label"]:
            template_automation_id = carrier_record["label"]
        elif isinstance(carrier_record.get("automation"), Mapping):
            echo_id = carrier_record["automation"].get("id")
            template_automation_id = str(echo_id) if echo_id else None
        child_template = build_clocked_order_child_template(
            order_id=order_id,
            payload_slug=payload_slug,
            requested_at_iso=requested_at_iso,
            requested_epoch=requested_epoch,
            created_epoch=clock(),
            automation_id=template_automation_id,
        )
        template_extra = {"child_template": child_template, "payload_recovery_outcome": "pending"}
        fire_command = build_clocked_order_fire_command(
            repo_root=target.repo_root,
            ledger_path=str(target.ledger_path),
            order_id=order_id,
            payload_slug=payload_slug,
            payload_text=str(payload_text),
        )
        scheduling = schedule_with_fallback(
            cli_scheduler_chain(
                automation_result=automation_echo,
                resolved_identity=resolved_identity,
                job_dir=payload.get("job_dir"),
                sentinel_path=payload.get("sentinel_path"),
                repo_root=target.repo_root,
            ),
            {
                "fire_at_epoch": requested_epoch,
                "resume_at_iso": compute_resume_at_iso(requested_epoch),
                "manual_command": fire_command,
                "order_id": order_id,
            },
        )
        # The A3 arming proof: read the armed carrier's recorded fire time
        # back and require it to equal the requested epoch (minute
        # granularity, at or before with zero tolerance). A proposed fire
        # time that rolls to a later occurrence (the requested minute
        # already passed) refuses and parks the order for pickup.
        proven_fire_epoch = None
        proof_note = None
        if scheduling.get("scheduled"):
            if scheduling.get("mechanism") == "launchd":
                try:
                    job = plistlib.loads(pathlib.Path(str(carrier_record["plist_path"])).read_bytes())
                    interval = job["StartCalendarInterval"]
                    armed_fire_epoch = next_local_occurrence_epoch(int(interval["Hour"]), int(interval["Minute"]), clock())
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    armed_fire_epoch = None
                    proof_note = f"clocked-order-arming-proof-unreadable: {exc}"
            else:
                echo_fire = automation_echo.get("fire_at_epoch")
                armed_fire_epoch = int(echo_fire) if echo_fire is not None else requested_epoch
            if armed_fire_epoch == requested_epoch:
                proven_fire_epoch = armed_fire_epoch
            elif proof_note is None:
                proof_note = (
                    f"clocked-order-arming-proof-refused: armed fire epoch {armed_fire_epoch} "
                    f"rolls past the requested epoch {requested_epoch}"
                )
        if proven_fire_epoch is not None:
            armed = target.mutate(
                order_id,
                event="order-armed",
                from_states={"pending"},
                to_state="armed",
                carrier=carrier_record,
                extra=template_extra,
                history_extra={"fire_epoch": proven_fire_epoch, "mechanism": scheduling.get("mechanism")},
            )
            return {
                "operation": "clocked-order-schedule",
                "status": "success",
                "reason_code": "clocked-order-armed",
                "order_id": order_id,
                "state": "armed",
                "fire_epoch": proven_fire_epoch,
                "requested_at_iso": requested_at_iso,
                "requested_epoch": requested_epoch,
                "carrier": dict(armed.get("order", {}).get("carrier") or carrier_record),
                "scheduling": scheduling,
                "payload_path": order["payload_path"],
                "payload_digest": order["payload_digest"],
            }
        refusal_reason = proof_note or launchd_refusal_reason(scheduling) or "report-only"
        if launchd_reachable:
            # Proof refused: the job was bootstrapped but never proven, so tear
            # it down before parking; a live unproven carrier must not survive.
            try:
                _pp = carrier_record.get("plist_path")
                if _pp:
                    _job = pathlib.Path(os.path.expanduser(str(_pp)))
                    launchctl_bootout(_job)
                    _job.unlink(missing_ok=True)
            except OSError:
                pass
            carrier_record = {"armed": False, "reason": refusal_reason}
        parked = target.mutate(
            order_id,
            event="order-parked",
            from_states={"pending"},
            to_state=None,
            carrier=carrier_record,
            extra=template_extra,
            history_extra={"reason": refusal_reason, "scheduling": scheduling},
        )
        return {
            "operation": "clocked-order-schedule",
            "status": "blocked",
            "reason_code": "clocked-order-parked-report-only",
            "order_id": order_id,
            "state": str(parked.get("order", {}).get("state") or "pending"),
            "requested_at_iso": requested_at_iso,
            "requested_epoch": requested_epoch,
            "carrier": dict(parked.get("order", {}).get("carrier") or carrier_record),
            "scheduling": scheduling,
            "payload_path": order["payload_path"],
            "payload_digest": order["payload_digest"],
        }

    if kind == "cancel":
        target = resolved_ledger()
        order_id = str(payload.get("order_id") or "")
        if not order_id:
            return {
                "operation": "clocked-order-cancel",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["order_id is required"],
            }
        order = target.order(order_id)
        if order is None:
            return {
                "operation": "clocked-order-cancel",
                "status": "blocked",
                "reason_code": "clocked-order-unknown-order",
                "order_id": order_id,
            }
        if order.get("state") in {"discharged", "cancelled"}:
            return {
                "operation": "clocked-order-cancel",
                "status": "blocked",
                "reason_code": "clocked-order-terminal-state",
                "order_id": order_id,
                "current_state": order.get("state"),
                "evidence": [f"clocked order {order_id} is terminal: {order.get('state')}"],
            }
        carrier = order.get("carrier") if isinstance(order.get("carrier"), Mapping) else {}
        teardown: dict[str, Any] = {}
        if carrier.get("armed") and carrier.get("plist_path"):
            # The launchd carrier tears down exactly like a superseded
            # watcher receipt: bootout of the recorded plist, the recorded
            # sentinel consumed - receipt-only, no identity derived.
            teardown = dict(supersede_carrier_teardown({"armed_launchd": dict(carrier)}))
            teardown["carrier_form"] = "launchd"
        elif carrier.get("armed"):
            # An automation-form carrier retires through the durable
            # retirement record naming the automation id the operator turn
            # deletes through the orchestrator-owned primitive.
            automation = carrier.get("automation") if isinstance(carrier.get("automation"), Mapping) else {}
            teardown = {
                "carrier_form": "automation",
                "automation_id": str(automation.get("id") or ""),
                "retired": True,
            }
        outcome = target.mutate(
            order_id,
            event="order-cancelled",
            from_states={"pending", "armed", "missed"},
            to_state="cancelled",
            history_extra={"carrier_teardown": teardown},
        )
        succeeded = outcome.get("status") == "success"
        return {
            "operation": "clocked-order-cancel",
            "status": outcome.get("status"),
            "reason_code": "clocked-order-cancelled" if succeeded else str(outcome.get("reason_code")),
            "order_id": order_id,
            "state": "cancelled" if succeeded else str(order.get("state")),
            "carrier_teardown": teardown,
            "order": outcome.get("order"),
        }

    if kind in ("begin-fire", "clear-fire"):
        target = resolved_ledger()
        order_id = str(payload.get("order_id") or "")
        if not order_id:
            return {
                "operation": f"clocked-order-{kind}",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["order_id is required"],
            }
        if kind == "begin-fire":
            result = target.begin_fire(order_id)
        else:
            launcher_exit_code = payload.get("launcher_exit_code")
            result = target.clear_fire(
                order_id,
                launcher_exit_code=None if launcher_exit_code is None else int(launcher_exit_code),
            )
        return {"operation": f"clocked-order-{kind}", **result}

    if kind == "migrate-carrier":
        target = resolved_ledger()
        order_id = str(payload.get("order_id") or "")
        if not order_id:
            return {
                "operation": "clocked-order-migrate-carrier",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["order_id is required"],
            }
        return _migrate_order_carrier(target, order_id, payload)

    if kind in ("clocked-order-verify-successor", "verify-successor"):
        return _run_clocked_order_verify_successor(
            resolved_ledger(), payload, repo_root=str(payload.get("repo_root") or repo_root), clock=clock
        )

    if kind == "due":
        target = resolved_ledger()
        now = float(clock())
        # Restart reconciliation before classification (plan
        # 2026-11-08-clocked-order-payload-session-execution Task 2): repair
        # the scheduler child projection from the stored templates and
        # replay the outcome mirrors, so classification and the later Step 6
        # projection read repaired surfaces.
        target.reconcile_child_projection(payload.get("scheduler_state_path"), now=now)
        missed = target.classify_due(now=now)["missed"]
        return {
            "operation": "clocked-order-due",
            "status": "success",
            "now_epoch": int(now),
            "missed": missed,
        }

    if kind == "discharge-on-fire":
        target = resolved_ledger()
        order_id = str(payload.get("order_id") or "")
        if not order_id:
            return {
                "operation": "clocked-order-discharge-on-fire",
                "status": "blocked",
                "reason_code": "clocked-order-refused-missing-field",
                "evidence": ["order_id is required"],
            }
        # The first action (plan 2026-11-08-clocked-order-payload-session-
        # execution Task 2): one ledger-lock acquisition spans the order
        # validation, the live-lease check, the executor-session-id
        # recording on the exact order, and the pending/armed-to-discharged
        # compare-and-swap; a refused identity, digest, target, or lease
        # discharges nothing, so the stored payload never runs.
        verdict = target.discharge_first_action(
            order_id,
            session_id=str(payload.get("session_id") or ""),
            payload_slug=payload.get("payload_slug"),
            fired_repo_root=str(pathlib.Path(os.path.expanduser(str(repo_root))).resolve()),
        )
        if verdict.get("verdict") == "unknown-order":
            return {
                "operation": "clocked-order-discharge-on-fire",
                "status": "blocked",
                "reason_code": "clocked-order-unknown-order",
                "order_id": order_id,
            }
        result: dict[str, Any] = {
            "operation": "clocked-order-discharge-on-fire",
            "order_id": order_id,
            "requested_epoch": verdict.get("requested_epoch"),
        }
        if verdict.get("verdict") == "early-fire":
            # Early fire: consume the sentinel, discharge nothing, and
            # re-arm check-and-arm-if-none for the requested minute (the
            # re-arm acquires the ledger lock itself, so it runs outside
            # the already-released first-action section).
            order = verdict["order"]
            result["sentinel"] = _consume_order_sentinel(order)
            result["early_fire"] = True
            result["discharged"] = False
            result["rearm"] = _rearm_order_carrier(target, order)
            return result
        result.update(verdict.get("update") or {})
        if verdict.get("verdict") == "discharged":
            result["sentinel"] = verdict.get("sentinel")
            result["discharged"] = True
            # The accepted-result marker the fire prelude gates the payload on
            # (the prelude continues only when status is success and discharged
            # is true).
            result["status"] = "success"
            result["late"] = verdict.get("late")
            result["late_by_seconds"] = verdict.get("late_by_seconds")
        return result

    raise ValueError(f"unknown clocked-order operation kind: {kind}")
