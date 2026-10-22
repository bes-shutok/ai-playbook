#!/usr/bin/env python3
"""Session status provider query for the execution-claim gateway.

The dead-run claim conversion (plan 2026-10-21-dead-run-resume-claim-conversion)
refuses to move a claim unless the prior owner session has verifiably ended.
Verification is delegated to a runtime-configured provider executable named by
``session_status_command`` in the PRIMARY checkout's local facts file
(``.ai-playbook/facts.md``); this module is the gateway-side query half:

- resolves the provider configuration from the primary facts file only
  (the caller passes the resolved absolute facts path; a relative provider
  executable or a missing/unreadable/ambiguous key refuses),
- invokes the provider with the prior session ID as its sole argument in a
  controlled environment (a fixed minimal PATH, empty session-influencing
  variables, no inherited lock variables) under a 10-second timeout,
- caps stdout and stderr at 65,536 bytes each; a timeout or an overflow
  terminates and reaps the whole provider process group,
- enforces the Terms' response contract exactly: exit 0, exactly one JSON
  object on stdout with exactly the two string fields ``session_id`` and
  ``status``, ``session_id`` equal to the queried ID, and ``status`` equal
  to ``terminal`` | ``live`` | ``paused`` | ``unresolved``.

Only ``terminal`` proceeds. Every other outcome raises
:class:`SessionStatusRefused` carrying the named reason; the gateway turns
that into its unchanged refusal. This module never reads or writes claim,
manifest, or lock state; it is a pure query with a closed contract.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tomllib
from dataclasses import dataclass

PROVIDER_KEY = "session_status_command"
TIMEOUT_SECS = 10.0
MAX_STREAM_BYTES = 65_536
STATUSES = ("terminal", "live", "paused", "unresolved")
# The controlled environment: the provider sees a fixed PATH and no
# caller-controlled session, lock, or home state (Terms: caller-controlled
# PATH or status variables refuse; the gateway owns the invocation env).
CONTROLLED_ENV = {
    "PATH": "/usr/bin:/bin:/usr/local/bin",
    "HOME": os.environ.get("HOME", "/"),
}


class SessionStatusRefused(Exception):
    """A named refusal; the gateway refuses conversion unchanged."""


@dataclass
class SessionStatus:
    session_id: str
    status: str


def read_provider_command(facts_path: str) -> str:
    """Resolve ``session_status_command`` from the primary facts file.

    Returns the configured command string. Refuses (never defaults) when the
    facts file is missing/unreadable, is not valid TOML, lacks the key, or
    carries a non-string or relative value (Terms: absolute executable
    required; no default provider exists).
    """
    try:
        with open(facts_path, "rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise SessionStatusRefused(
            f"provider facts file not found: {facts_path}"
        ) from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SessionStatusRefused(
            f"provider facts file unreadable or malformed: {facts_path}: {exc}"
        ) from exc
    raw = data.get(PROVIDER_KEY)
    if raw is None:
        raise SessionStatusRefused(
            f"{PROVIDER_KEY} not configured in {facts_path}; the existing "
            "branch-occupant refusal remains active"
        )
    if not isinstance(raw, str) or not raw.strip():
        raise SessionStatusRefused(
            f"{PROVIDER_KEY} must be a non-empty string in {facts_path}"
        )
    command = raw.strip()
    # The absolute-executable requirement: the first word must be an absolute
    # path (the executable itself; arguments may be relative to the caller's
    # intent but the program location may never depend on caller PATH).
    if not os.path.isabs(command.split()[0]):
        raise SessionStatusRefused(
            f"{PROVIDER_KEY} must name an absolute executable path; got "
            f"{command.split()[0]!r}"
        )
    return command


def query_session_status(
    facts_path: str, prior_session_id: str
) -> SessionStatus:
    """Query the configured provider for the prior session's status.

    Enforces the full Terms contract: the provider runs under a 10-second
    timeout with 65,536-byte per-stream caps enforced LIVE (a reader that
    crosses its cap terminates and reaps the whole process group
    immediately, never buffering unboundedly), must exit 0, and must write
    exactly one JSON object with exactly the two string fields, the queried
    ID, and a status in the closed vocabulary. Any deviation raises
    SessionStatusRefused.
    """
    if not prior_session_id or not prior_session_id.strip():
        raise SessionStatusRefused("prior session ID is empty")
    command = read_provider_command(facts_path)
    argv = command.split() + [prior_session_id]
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(CONTROLLED_ENV),
            start_new_session=True,
        )
    except OSError as exc:
        raise SessionStatusRefused(f"provider executable failed to start: {exc}") from exc

    import threading

    chunks: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
    overflow: dict[str, bool] = {"stdout": False, "stderr": False}

    def _read_stream(name: str, pipe) -> None:
        try:
            while True:
                blob = pipe.read(4096)
                if not blob:
                    return
                stream = chunks[name]
                if len(stream) + len(blob) > MAX_STREAM_BYTES:
                    overflow[name] = True
                    _kill_process_group(proc)
                    return
                stream.extend(blob)
        except (OSError, ValueError):
            return  # the pipe closed on group kill; the reader just ends

    readers = [
        threading.Thread(target=_read_stream, args=(name, pipe), daemon=True)
        for name, pipe in (("stdout", proc.stdout), ("stderr", proc.stderr))
    ]
    for reader in readers:
        reader.start()
    try:
        proc.wait(timeout=TIMEOUT_SECS)
    except subprocess.TimeoutExpired:
        _kill_process_group(proc)
        raise SessionStatusRefused(
            f"provider exceeded the {TIMEOUT_SECS:g}s bound; process group "
            "terminated and reaped"
        )
    except KeyboardInterrupt:
        _kill_process_group(proc)
        raise
    for reader in readers:
        reader.join(timeout=5)
    if overflow["stdout"] or overflow["stderr"]:
        name = "stdout" if overflow["stdout"] else "stderr"
        raise SessionStatusRefused(
            f"provider {name} exceeded the {MAX_STREAM_BYTES}-byte cap; "
            "process group terminated and reaped"
        )
    if proc.returncode != 0:
        raise SessionStatusRefused(
            f"provider exited {proc.returncode} (nonzero refuses unchanged)"
        )
    return _parse_response(
        bytes(chunks["stdout"]).decode("utf-8", errors="replace"), prior_session_id
    )


def _parse_response(stdout_text: str, prior_session_id: str) -> SessionStatus:
    payload = stdout_text.strip()
    if not payload:
        raise SessionStatusRefused("provider wrote no stdout")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SessionStatusRefused(f"provider stdout is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SessionStatusRefused("provider response is not a JSON object")
    extra = sorted(set(data) - {"session_id", "status"})
    missing = sorted({"session_id", "status"} - set(data))
    if extra or missing:
        raise SessionStatusRefused(
            f"provider response fields wrong (missing {missing}, extra {extra})"
        )
    session_id, status = data["session_id"], data["status"]
    if not isinstance(session_id, str) or not isinstance(status, str):
        raise SessionStatusRefused("provider response fields must be strings")
    if session_id != prior_session_id:
        raise SessionStatusRefused(
            f"provider response names session {session_id!r}, queried "
            f"{prior_session_id!r}"
        )
    if status not in STATUSES:
        raise SessionStatusRefused(
            f"provider status {status!r} is outside the closed vocabulary "
            f"{list(STATUSES)}"
        )
    return SessionStatus(session_id=session_id, status=status)


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Terminate then kill the provider's whole process group and reap it."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass  # reaped by init; nothing further to do


def main() -> int:
    """CLI: ``session_status.py <facts-path> <prior-session-id>``.

    Prints the provider's verdict as JSON and exits 0 when the provider
    reports the matching session ``terminal``; every refusal exits 3 with
    the named reason on stderr (the outcome contract's tool_error class;
    the gateway maps every refusal to its unchanged refusal).
    """
    if len(sys.argv) != 3:
        print(
            "usage: session_status.py <facts-path> <prior-session-id>",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    try:
        result = query_session_status(sys.argv[1], sys.argv[2])
    except SessionStatusRefused as exc:
        print(f"session-status refused: {exc}", file=sys.stderr)
        print("OUTCOME: fail")
        return 1
    print(json.dumps({"session_id": result.session_id, "status": result.status}))
    print("OUTCOME: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
