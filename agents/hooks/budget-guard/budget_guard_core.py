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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, choices=("zcode", "codex"))
    parser.add_argument(
        "--flag-path",
        default="~/.ai-playbook/runtime/budget-guard.flag",
        help="Guard flag path; defaults to the host-global runtime location.",
    )
    parser.add_argument("--fired-path", default=None)
    args = parser.parse_args(argv)

    flag_path = pathlib.Path(args.flag_path).expanduser()
    fired_path = pathlib.Path(
        args.fired_path
        if args.fired_path is not None
        else flag_path.parent / "budget-guard.fired"
    )

    try:
        fields = parse_flag(flag_path.read_text(encoding="utf-8"))
    except OSError:
        return EXIT_OK  # Unreadable flag: fail open, never block.

    if not fields:
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
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
