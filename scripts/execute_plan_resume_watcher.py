#!/usr/bin/env python3
"""Workflow-neutral standing resume watcher state machine.

One state machine over two explicit adapter protocols:

- ``WatcherStateAdapter``: one workflow's authoritative machine-state
  operations (lock-held read, compare-and-swap replacement/cancellation,
  semantic-progress, boundary, and projection operations). Task 5 provides
  the execute-plan runtime-state adapter (``RuntimeResumeWatcherAdapter``);
  Task 6 adds the plans authoring-state adapter to this same file, so the
  two workflows never grow separate watcher protocols.
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
import os
import pathlib
import plistlib
import re
import shlex
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Iterator, Mapping, Optional, Sequence

GUARD_LOCK_NAME = "budget-guard.lock"
DEFAULT_FLAG_PATH = pathlib.Path("~/.ai-playbook/runtime/budget-guard.flag")
FIRED_MARKER_NAME = "budget-guard.fired"

# Standing resume watcher receipt fields (canonical machine-state fence).
# This workflow-neutral module owns the schema: the runtime driver and both
# adapters import it from here, never the reverse, so a layout without the
# runtime cannot break the authoring watcher with an import error.
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


def file_digest(path: os.PathLike | str | None) -> Optional[str]:
    """Current sha-256 of the plan bytes, or None when unreadable or absent."""

    if path is None:
        return None
    candidate = pathlib.Path(os.path.expanduser(str(path)))
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


class _SnapshotFencesMixin:
    """The snapshot-derived stand-down fences shared by every adapter.

    One copy of the semantic-progress, peer-resume, abort/interrupt, and
    projection logic; persistence layers (schedule/supersede CAS) stay
    per-workflow. ``peer_resumed`` anchors to ``scheduled_at_epoch`` against
    the dedicated ``peer_resumed_at_epoch`` machine-state field, which only
    resume/continue-path operations write (r1 F11): peer writes before a
    fire session's construction stay visible, and the fire session's own
    construction and bookkeeping writes never false-trip the fence.
    """

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


def watcher_cas_stale(
    transition: Mapping[str, Any],
    current_watcher_id: Any,
    generation: int,
    boundary_generation: int,
) -> bool:
    """The one compare-and-swap stale predicate for every watcher CAS writer.

    Shared by the driver's receipt writer and the authoring adapter: the
    transition's expected watcher id, generation, and boundary generation
    must all match current machine state.
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
    ) -> None:
        self._job_dir = pathlib.Path(job_dir)
        self._sentinel_path = pathlib.Path(sentinel_path)
        self._label = label
        self._bootstrap = bootstrap or launchctl_bootstrap
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

    def fire_command(self, manual_command: str) -> str:
        """The fire-time ``sh -c`` payload: fired-marker and sentinel guards,
        first-fire sentinel creation, then the manual resume command.

        The fired-marker guard (r3 F16) makes the daily calendar job inert
        once watcher-fire consumed the one-shot on a terminal decision: the
        sentinel is removed and the marker written, so a later daily fire
        exits before touching anything instead of re-running the resume.
        """

        fired = shlex.quote(str(self.fired_path))
        quoted = shlex.quote(str(self._sentinel_path))
        return f"test -e {fired} && exit 0; test -e {quoted} && exit 0; touch {quoted}; {manual_command}"

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
                self.fire_command(str(request.get("manual_command", ""))),
            ],
            "StartCalendarInterval": {"Minute": fire_at.minute, "Hour": fire_at.hour},
            "StandardOutPath": str(self._job_dir / f"{self._label}.out.log"),
            "StandardErrorPath": str(self._job_dir / f"{self._label}.err.log"),
        }
        # Serialize the identity check, the plist write, and the bootout
        # through the shared guard lock (r3 F14): two boundaries of the same
        # run arming in one window must not interleave a write and a bootout.
        # Lock unavailability fails open (best-effort, like the cleanup), so
        # the bound name is only the acquire result.
        with budget_guard_lock(self._sentinel_path):
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


def supersede_carrier_teardown(receipt: Mapping[str, Any]) -> dict[str, Any]:
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
    """

    teardown: dict[str, Any] = {}
    armed = receipt.get("armed_launchd") if isinstance(receipt.get("armed_launchd"), Mapping) else None
    if armed is None or armed.get("armed") is not True:
        teardown["torn_down"] = False
        return teardown
    teardown["torn_down"] = True
    plist_path = armed.get("plist_path")
    if isinstance(plist_path, str) and plist_path.strip():
        job = pathlib.Path(os.path.expanduser(plist_path))
        teardown["bootout"] = launchctl_bootout(job)
        try:
            job.unlink()
        except OSError:
            pass
    sentinel_path = armed.get("sentinel_path")
    if isinstance(sentinel_path, str) and sentinel_path.strip():
        fired_marker = armed.get("fired_marker_path")
        teardown["sentinel"] = consume_resume_sentinel(
            sentinel_path,
            fired_path=fired_marker if isinstance(fired_marker, str) and fired_marker.strip() else None,
        )
    return teardown


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
    other decision (unknown, weekly-secondary, pause, abort, complete)
    supersedes and clears any pending watcher even when no replacement is
    scheduled.
    """

    if boundary_kind in {"abort", "complete"}:
        return boundary_kind
    decision = str(probe_report.get("pause_decision", "continue"))
    if decision == "pause":
        return "pause"
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
            return {
                "boundary": "stale",
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
        plan_digest = file_digest(plan_path)
        if plan_digest is None:
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
        }.get(boundary_name, "watcher-cas-stale")
        return outcome_factory(
            "success" if boundary_name == "install" else "blocked",
            reason_code,
            [
                f"boundary={boundary.get('boundary')}",
                f"classification={boundary.get('classification')}",
                f"scheduling={json.dumps(boundary.get('scheduling'), sort_keys=True) if boundary.get('scheduling') else 'none'}",
            ],
            "repository-write",
            f"{identity_prefix}:schedule",
            int((boundary.get("machine") or {}).get("generation", 0)),
            "continue-parent" if boundary_name == "install" else "preserve-and-reconcile",
            resume_watcher=(boundary.get("machine") or {}).get("resume_watcher"),
            scheduling=boundary.get("scheduling"),
            projection=boundary.get("projection"),
            manual_command=boundary.get("manual_command"),
            carrier_rectified=boundary.get("carrier_rectified"),
            cas_applied=boundary_name != "stale",
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
# execute-plan runtime adapter (Task 5)
# ---------------------------------------------------------------------------


class RuntimeResumeWatcherAdapter(_SnapshotFencesMixin, WatcherStateAdapter):
    """execute-plan runtime_state.json adapter over the durable driver."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def read_state(self) -> dict[str, Any]:
        snapshot = dict(self._driver.resume_watcher_snapshot())
        watcher = snapshot.get("resume_watcher")
        if isinstance(watcher, Mapping):
            snapshot["plan_path"] = watcher.get("plan_path")
            # Recompute the plan-byte digest now: this is the live fence.
            snapshot["plan_digest"] = file_digest(watcher.get("plan_path"))
        else:
            snapshot["plan_path"] = None
            snapshot["plan_digest"] = None
        snapshot.setdefault("repo_root", str(self._driver.repo_root))
        return snapshot

    def compare_and_swap_schedule(self, transition: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._driver.record_resume_watcher(transition)

    def compare_and_swap_supersede(self, transition: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._driver.record_resume_watcher(transition)

    def compare_and_swap_carrier(self, transition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Rectify the pending receipt's armed_launchd record (r6 F5)."""

        return self._driver.record_resume_watcher(transition)

    def record_resume(self, evidence: Sequence[str] | None = None) -> dict[str, Any]:
        """Mark a resume-path re-entry for the shared peer fence (r4 F4).

        The fire operation records the mark itself on a resume decision, so
        a duplicate fire inside the window before the resumed session runs
        stands down on machine state. The driver's lock-skipping writer is
        reused: a mark missed under contention is covered by the receipt
        supersede the fire performs next.
        """

        del evidence  # the runtime manifest keeps the epoch only
        self._driver._mark_peer_resumed()
        return {"status": "success", "reason_code": "peer-resume-marked"}

    def archived_or_completed(self, snapshot: Mapping[str, Any]) -> bool:
        # The runtime manifest records completion in workflow_state; the
        # authoring mirror additionally carries plan_status (its own
        # per-workflow delta below).
        return snapshot.get("workflow_state") in {"complete", "terminal"}


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


class PlansAuthoringWatcherAdapter(_SnapshotFencesMixin, WatcherStateAdapter):
    """plans authoring-state adapter over ``plan-requirements-<slug>.json``.

    The authoring JSON is the authority; the Markdown notes are the human
    and audit projection and receive a line only after a lock-held state
    transition. Because every observation delegates to the shared adapter
    protocol, this workflow shares the same replacement, cancellation,
    boundary generation, canonical plan path and digest, semantic-progress,
    peer-resume, archive, completion, abort, and interrupt fences as the
    execute-plan runtime adapter.
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
            # The authoring state owns the plan slug the same way the
            # runtime manifest does; the fence compares against it.
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
            self._save_unlocked(
                state,
                {
                    "event": "resume-watcher-superseded",
                    "watcher_id": current_id,
                    "reason": str(transition.get("reason", "boundary-decision")),
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

        The authoring mirror of the runtime driver's ``re-carrier`` action:
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

    # The snapshot-derived fences (semantic progress, peer resume, abort or
    # interrupt, projection) come from _SnapshotFencesMixin; only the
    # per-workflow archived trigger and the persistence below live here.

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
