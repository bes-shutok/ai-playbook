#!/usr/bin/env python3
"""Agent-agnostic budget-guard PreToolUse backstop core.

Reads the guard flag written by scripts/quota_window_probe.py and, while the
flag is live and unexpired, blocks new tool work for the named runtime.
Fail-open by design: a missing, unreadable, or malformed flag NEVER blocks.
Stdlib-only; performs no network access. Ignores stdin entirely.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import os
import pathlib
import sys
import time

REASON_TEMPLATE = (
    "Provider quota window for runtime {runtime} ends at {reset_at_iso}. "
    "Do not start new tool work. Finish the current sub-agent step, land the "
    "pending done commit if any, record the budget pause, and schedule the "
    "resume. Budget guard flag: {flag_path} (armed by {armed_by})."
)

EXIT_BLOCK_ZCODE = 2
EXIT_OK = 0

# The guard lock file shared by the probe writer, both hook adapters, the
# standing resume watcher's compare-and-delete, and fired-marker cleanup.
# Canonical contract: scripts/execute_plan_resume_watcher.py
# (budget_guard_lock / compare_and_delete_flag); this core is deployed as a
# standalone real-file copy, so it holds the same file by the same name and
# the hermetic suites prove the interlock end to end.
GUARD_LOCK_NAME = "budget-guard.lock"

# The rate-limited decision log: JSON lines recording what each invocation
# decided. Block decisions and errors always append; allow decisions append
# at most one heartbeat line per hook per day (the first invocation of the
# day). Best-effort only: the log never changes the hook's decision or exit
# code. Overridable with --hook-outcomes-log.
HOOK_OUTCOMES_LOG_PATH = pathlib.Path(
    "~/.ai-playbook/runtime/hook-outcomes.log"
)

# Module-level date source for the heartbeat rate check (is today's
# heartbeat line already logged). The test suite overrides this to freeze
# the day, the same seam style as scripts/review_record_selection.py's
# DATE_SOURCE (module-level date callable, frozen by its suite).
DATE_SOURCE = datetime.date.today

# Fault-injection seam for the decision path, in the same seam style as the
# day source above: when set to a callable, the decision path invokes it
# right after entry and the callable raises, so the suite can induce the
# erroring invocation through main()'s exception guard. None in production.
DECISION_FAULT_SOURCE = None


@contextlib.contextmanager
def _shared_guard_lock(flag_path: pathlib.Path,
                       timeout_seconds: float = 2.0,
                       poll_seconds: float = 0.02):
    """Hold the shared budget-guard lock; yields True when acquired.

    The lock file lives next to the guard flag (canonical:
    ~/.ai-playbook/runtime/budget-guard.lock) so the read, compare, and
    unlink of every cleanup serialize against the probe writer's atomic
    os.replace of the same flag. On lock-unavailability the caller skips the
    removal quietly: fail-open is unchanged, and a skipped cleanup is
    retried by the next hook invocation.
    """

    path = flag_path.parent / GUARD_LOCK_NAME
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


def parse_flag(text: str) -> dict:
    """Parse the flag's `key=value` lines; returns {} when malformed."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    if "runtime" not in fields or "reset_at_iso" not in fields:
        return {}
    try:
        fields["reset_at_epoch"] = int(fields.get("reset_at_epoch", ""))
    except ValueError:
        return {}
    return fields


def remove_quiet(path: pathlib.Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def write_marker_best_effort(path: pathlib.Path, reset_at_epoch: int) -> None:
    # The marker records the window it fired for: a marker from an older
    # window must not suppress the next window's single block. Best-effort:
    # the block is the safety effect, the marker is anti-thrash only. The
    # caller holds the shared guard lock (flag-derived) across this write so
    # a concurrent cleanup's locked re-check never removes the fresh marker.
    try:
        path.write_text(str(reset_at_epoch) + "\n", encoding="utf-8")
    except OSError:
        pass  # Anti-thrash only; the block is the safety effect.


def _heartbeat_logged_today(log_path: pathlib.Path, hook_id: str) -> bool:
    """Whether the log already holds today's heartbeat line for this hook.

    The caller holds the shared guard lock, so the read and the append that
    may follow it cannot interleave a same-day duplicate. A missing,
    unreadable, corrupted (undecodable bytes), or malformed log counts as
    not-logged: the worst case is a duplicate heartbeat line, never a
    changed decision or an escaped error-line flood.
    """
    today = DATE_SOURCE().isoformat()
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, ValueError):
        # ValueError covers UnicodeDecodeError from a corrupted (non-UTF-8)
        # log: treating it as not-logged lets the heartbeat be written
        # instead of raising into main()'s guard and self-flooding the log
        # with one error line per invocation.
        return False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        if (record.get("event") == "heartbeat"
                and record.get("hook") == hook_id
                and isinstance(record.get("ts"), str)
                and record["ts"][:10] == today):
            return True
    return False


def _append_outcome_line(log_path: pathlib.Path, hook_id: str, event: str,
                         decision: str, started: float,
                         **extra) -> None:
    """Append one JSON outcome line; the caller holds the shared guard lock.

    The write is best-effort and swallows every OSError: a logging failure
    never changes the hook's own decision or exit code. Error lines carry
    the failure kind, the message text, and the exit code the invocation
    returns (the fail-open 0) via the extra keyword fields.
    """
    record = {
        "ts": datetime.datetime.now().astimezone().isoformat(),
        "hook": hook_id,
        "event": event,
        "decision": decision,
        "duration_ms": int((time.monotonic() - started) * 1000),
    }
    record.update(extra)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    except OSError:
        pass  # Best-effort forensics; the decision stands either way.


def _log_allow_heartbeat(flag_path: pathlib.Path, log_path: pathlib.Path,
                         hook_id: str, started: float) -> None:
    """Append the day's single allow heartbeat for this hook.

    The already-today rate check and the append share one critical section
    on the shared guard lock so a same-day second invocation cannot
    interleave a duplicate heartbeat line or a doubled rate check. A
    lock-acquisition failure skips the log line; the allow decision is
    unchanged (fail-open).
    """
    with _shared_guard_lock(flag_path) as acquired:
        if not acquired:
            return  # Skipped log line; the decision is unchanged.
        if _heartbeat_logged_today(log_path, hook_id):
            return
        _append_outcome_line(log_path, hook_id, "heartbeat", "allow", started)


def _log_error_under_guard_lock(flag_path: pathlib.Path,
                                log_path: pathlib.Path, hook_id: str,
                                started: float, error_kind: str,
                                error_message: str, exit_code: int) -> None:
    """Append the error line for an unexpected decision-path exception.

    The append runs under the shared guard lock like every other outcome
    line; a lock-acquisition failure skips the line, and the fail-open exit
    code passed by the caller stands either way.
    """
    with _shared_guard_lock(flag_path) as acquired:
        if not acquired:
            return  # Skipped log line; the decision is unchanged.
        _append_outcome_line(log_path, hook_id, "error", "allow", started,
                             error_kind=error_kind,
                             error_message=error_message,
                             exit_code=exit_code)


def main(argv: list[str] | None = None) -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, choices=("zcode", "codex"))
    parser.add_argument(
        "--flag-path",
        default="~/.ai-playbook/runtime/budget-guard.flag",
        help="Guard flag path; defaults to the host-global runtime location.",
    )
    parser.add_argument("--fired-path", default=None)
    parser.add_argument(
        "--hook-outcomes-log",
        default=str(HOOK_OUTCOMES_LOG_PATH),
        help="Decision log path (JSON lines); defaults to the host-global "
             "runtime location.",
    )
    args = parser.parse_args(argv)

    flag_path = pathlib.Path(args.flag_path).expanduser()
    fired_path = pathlib.Path(
        args.fired_path
        if args.fired_path is not None
        else flag_path.parent / "budget-guard.fired"
    )
    log_path = pathlib.Path(args.hook_outcomes_log).expanduser()

    try:
        return _decide(args, flag_path, fired_path, log_path, started)
    except Exception as exc:
        # Unexpected exception on the decision path: append the error line
        # (best-effort, under the shared guard lock) and fail open exactly
        # as the invocation would have; the log write never changes the
        # decision or the exit code.
        try:
            _log_error_under_guard_lock(
                flag_path, log_path, args.runtime, started,
                error_kind=type(exc).__name__,
                error_message=str(exc),
                exit_code=EXIT_OK,
            )
        except Exception:
            pass  # The error line is best-effort; fail-open stands either way.
        return EXIT_OK


def _decide(args: argparse.Namespace, flag_path: pathlib.Path,
            fired_path: pathlib.Path, log_path: pathlib.Path,
            started: float) -> int:
    # The decision path, wrapped by main()'s exception guard. The
    # fault-injection seam fires here so an induced failure travels through
    # the guard and produces the error line with the fail-open exit code.
    if DECISION_FAULT_SOURCE is not None:
        DECISION_FAULT_SOURCE()

    try:
        fields = parse_flag(flag_path.read_text(encoding="utf-8"))
    except OSError:
        _log_allow_heartbeat(flag_path, log_path, args.runtime, started)
        return EXIT_OK  # Unreadable flag: fail open, never block.

    if not fields:
        _log_allow_heartbeat(flag_path, log_path, args.runtime, started)
        return EXIT_OK  # Malformed flag: fail open.

    if fields["reset_at_epoch"] <= int(time.time()):
        # Expired window: clean up flag AND fired marker, then pass. The
        # read, compare, and unlink happen while the shared budget-guard
        # lock is held (the probe writer's os.replace takes the same lock),
        # so a flag replaced with a newer live window before this cleanup
        # acquires the lock is seen by the locked re-read and survives; the
        # removal decision itself is unchanged (fail-open either way).
        with _shared_guard_lock(flag_path) as acquired:
            if acquired:
                try:
                    current = parse_flag(flag_path.read_text(encoding="utf-8"))
                except OSError:
                    current = None
                if current and current["reset_at_epoch"] <= int(time.time()):
                    remove_quiet(flag_path)
                    remove_quiet(fired_path)
        _log_allow_heartbeat(flag_path, log_path, args.runtime, started)
        return EXIT_OK

    if fired_path.is_file():
        # The marker binds to the flag's window: content is the reset epoch the
        # block fired for. A marker left over from an older window is stale —
        # remove it and fall through so the new window gets its single block.
        try:
            marker = fired_path.read_text(encoding="utf-8").strip()
        except OSError:
            marker = None
        if marker == str(fields["reset_at_epoch"]):
            _log_allow_heartbeat(flag_path, log_path, args.runtime, started)
            return EXIT_OK  # Already intervened once this window; anti-thrash.
        # Atomic compare-and-delete for the stale-marker cleanup: the unlink
        # re-checks the marker content while the shared guard lock is held,
        # so a marker re-written for the current window between the read
        # above and this removal survives (fired-marker replacement
        # protection; same lock file as the probe writer and the watcher).
        with _shared_guard_lock(flag_path) as acquired:
            if acquired:
                try:
                    current_marker = fired_path.read_text(encoding="utf-8").strip()
                except OSError:
                    current_marker = None
                if current_marker is not None and current_marker != str(fields["reset_at_epoch"]):
                    remove_quiet(fired_path)

    # Prefer the flag's own runtime line: the flag is host-global and may have
    # been armed by a different registered runtime than this adapter.
    reason = REASON_TEMPLATE.format(
        runtime=fields.get("runtime", args.runtime),
        reset_at_iso=fields["reset_at_iso"],
        flag_path=str(flag_path),
        armed_by=fields.get("armed_by", "unknown"),
    )
    if args.runtime == "zcode":
        envelope = {"decision": "block", "reason": reason}
        exit_code = EXIT_BLOCK_ZCODE
    else:
        envelope = {"permissionDecision": "deny", "reason": reason}
        exit_code = EXIT_OK
    sys.stdout.write(json.dumps(envelope))
    # The marker write holds the shared guard lock (flag-derived) so a
    # concurrent cleanup cannot remove the fresh marker mid-write.
    with _shared_guard_lock(flag_path) as acquired:
        if not acquired:
            pass  # Anti-thrash only; write anyway, the block already fired.
        write_marker_best_effort(fired_path, fields["reset_at_epoch"])
        if acquired:
            # Block outcomes always append. A lock-acquisition failure skips
            # the line quietly: the block is already on stdout, and the log
            # never changes the decision or the exit code.
            _append_outcome_line(log_path, args.runtime, "block", "block",
                                 started)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
