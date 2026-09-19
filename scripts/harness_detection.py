#!/usr/bin/env python3
"""Live-signal harness detection: which supported harness is running THIS process?

Process-scoped by design (see docs/plans/2026-09-18-harness-detection-and-budgeting-skip.md):
a live signal is evidence inside the current session's own process context --
environment variables the harness injected, or the session's process ancestry.
Host-installed-software evidence (a config file another runtime left on disk) is
deliberately NOT consulted: that file-presence rule was the defect of record that
auto-bound a foreign runtime's quota window.

Signal table (one row per supported harness; a new harness is a new row):
- zcode: any ``ZCODE_*`` environment key (the family, not one documented key).
- codex: a bounded parent-chain command scan (at most six ancestors), matching
  the FIRST token's basename against the codex executable name, so a "codex"
  mention inside an argument of some other executable never matches.

Detection precedence: environment first, then ancestry; documented and tested.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Callable, Mapping, Optional, Sequence, Tuple

SUPPORTED = ("zcode", "codex")

# Bounded ancestry walk: at most six ancestors scanned (inclusive).
ANCESTRY_DEPTH_BOUND = 6

_PS_LINE = re.compile(r"^\s*(\d+)\s+(.*)$")


def _default_ancestry() -> Sequence[str]:
    """Real bounded parent-chain walk via ``ps``; one command string per ancestor.

    Factored as a module-level function (not a closure) so the default path is
    testable: a fixture ``ps`` earlier on PATH answers a canned chain without
    spawning a real process tree.
    """
    commands: list[str] = []
    # Start at the PARENT, not self: the bound counts ancestors only, matching
    # the injected-chain contract (entry 0 is the first ancestor).
    pid = os.getppid()
    for _ in range(ANCESTRY_DEPTH_BOUND):
        try:
            output = subprocess.run(
                ["ps", "-o", "ppid=,command=", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            break
        match = _PS_LINE.match(output.splitlines()[0]) if output.splitlines() else None
        if match is None:
            break
        commands.append(match.group(2))
        pid = int(match.group(1))
        if pid <= 1:
            break
    return commands


def _first_token_basename(command: str) -> str:
    return os.path.basename(command.split()[0]) if command.split() else ""


def detect_harness(
    env: Optional[Mapping] = None,
    ancestry: Optional[Callable[[], Sequence[str]]] = None,
) -> Tuple[Optional[str], str]:
    """Answer (harness_id_or_None, method) from live signals only.

    ``env`` defaults to ``os.environ``; ``ancestry`` is an injectable callable
    returning the parent-chain command strings (default: ``_default_ancestry``).
    ``method`` is ``"env"`` or ``"ancestry"`` on a match, ``"none"`` when no
    supported live signal was found in environment or ancestry.
    """
    if env is None:
        env = os.environ
    if ancestry is None:
        ancestry = _default_ancestry
    zcode_keys = sorted(key for key in env if key.startswith("ZCODE_"))
    if zcode_keys:
        return "zcode", "env"
    for command in list(ancestry())[:ANCESTRY_DEPTH_BOUND]:
        if _first_token_basename(command) == "codex":
            return "codex", "ancestry"
    return None, "none"


def _evidence(method: str, env: Optional[Mapping] = None) -> str:
    if method == "env":
        keys = sorted(key for key in (env if env is not None else os.environ) if key.startswith("ZCODE_"))
        return "matched ZCODE_* environment key(s): {}".format(", ".join(keys))
    if method == "ancestry":
        return "matched a codex executable basename within {} process ancestors".format(ANCESTRY_DEPTH_BOUND)
    return "no supported live signal found in environment or process ancestry"


def main() -> int:
    harness, method = detect_harness()
    print(json.dumps({
        "harness": harness if harness in SUPPORTED else "none",
        "method": method,
        "evidence": _evidence(method),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
