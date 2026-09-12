#!/usr/bin/env python3
"""Agent-agnostic budget-guard PreToolUse backstop core.

Reads the guard flag written by scripts/quota_window_probe.py and, while the
flag is live and unexpired, blocks new tool work for the named runtime.
Fail-open by design: a missing, unreadable, or malformed flag NEVER blocks.
Stdlib-only; performs no network access. Ignores stdin entirely.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

REASON_TEMPLATE = (
    "Provider quota window for runtime {runtime} ends at {reset_at_iso}. "
    "Do not start new tool work. Finish the current sub-agent step, land the "
    "pending done commit if any, record the budget pause, and schedule the "
    "resume."
)

EXIT_BLOCK_ZCODE = 2
EXIT_OK = 0


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
    # window must not suppress the next window's single block.
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
        # Expired window: clean up flag AND fired marker, then pass. Re-read
        # before unlinking: a concurrent probe may have replaced the flag with
        # a newer window between our read and this removal; only unlink while
        # the on-disk epoch is still in the past. Re-read failure or a gone
        # file skips removal quietly.
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
        remove_quiet(fired_path)

    # Prefer the flag's own runtime line: the flag is host-global and may have
    # been armed by a different registered runtime than this adapter.
    reason = REASON_TEMPLATE.format(
        runtime=fields.get("runtime", args.runtime),
        reset_at_iso=fields["reset_at_iso"],
    )
    if args.runtime == "zcode":
        envelope = {"decision": "block", "reason": reason}
        exit_code = EXIT_BLOCK_ZCODE
    else:
        envelope = {"permissionDecision": "deny", "reason": reason}
        exit_code = EXIT_OK
    sys.stdout.write(json.dumps(envelope))
    write_marker_best_effort(fired_path, fields["reset_at_epoch"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
