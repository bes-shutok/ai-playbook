#!/usr/bin/env python3
"""Block Codex work and worker launches unless they use GPT-5.6 Luna."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


ALLOWED_MODEL = "gpt-5.6-luna"
TAIL_BYTES = 1024 * 1024
HEAD_BYTES = 256 * 1024
WORKER_TOOL_MARKERS = ("spawn_agent", "spawn-agent", "subagent")


def transcript_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("file://"):
        parsed = urlparse(value)
        return Path(unquote(parsed.path))
    return Path(value)


def model_from_mapping(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None

    thread_settings = payload.get("thread_settings")
    if isinstance(thread_settings, dict):
        model = thread_settings.get("model")
        if isinstance(model, str):
            return model

    for key in ("model", "model_slug", "subagent_model", "agent_model"):
        model = payload.get(key)
        if isinstance(model, str):
            return model
    return None


def model_from_lines(lines: list[str]) -> str | None:
    latest: str | None = None
    for line in lines:
        try:
            record = json.loads(line)
        except (TypeError, ValueError):
            continue

        payload = record.get("payload") if isinstance(record, dict) else None
        model = model_from_mapping(payload)
        if model is not None:
            latest = model
    return latest


def active_model(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None

    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - TAIL_BYTES))
            tail = stream.read().decode("utf-8", errors="replace")
            model = model_from_lines(tail.splitlines())
            if model is not None:
                return model

            stream.seek(0)
            head = stream.read(HEAD_BYTES).decode("utf-8", errors="replace")
            return model_from_lines(head.splitlines())
    except OSError:
        return None


def worker_tool_name(event: dict[str, object]) -> str:
    for key in ("tool_name", "name"):
        value = event.get(key)
        if isinstance(value, str):
            return value.lower()
    return ""


def explicit_worker_model(event: dict[str, object]) -> str | None:
    tool_name = worker_tool_name(event)
    if not any(marker in tool_name for marker in WORKER_TOOL_MARKERS):
        return None

    for key in ("tool_input", "input", "arguments"):
        model = model_from_mapping(event.get(key))
        if model is not None:
            return model
    return None


def active_event_model(event: dict[str, object]) -> str | None:
    model = event.get("model")
    if isinstance(model, str):
        return model
    return active_model(transcript_path(event.get("transcript_path")))


def block(event: str, reason: str) -> None:
    if event == "PreToolUse":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    else:
        output = {"decision": "block", "reason": reason}
    print(json.dumps(output))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (TypeError, ValueError):
        event = {}

    if not isinstance(event, dict):
        event = {}

    event_name = str(event.get("hook_event_name", ""))
    requested_model = explicit_worker_model(event)
    if requested_model is not None and requested_model != ALLOWED_MODEL:
        block(
            event_name,
            f"Blocked: worker requested model {requested_model}, but this setup "
            f"permits only {ALLOWED_MODEL}.",
        )
        return 0

    model = active_event_model(event)
    if model == ALLOWED_MODEL:
        return 0

    if model is None:
        reason = (
            "Blocked: Codex could not verify that the active model is "
            f"{ALLOWED_MODEL}. Select Luna and retry."
        )
    else:
        reason = (
            f"Blocked: active model is {model}, but this setup permits only "
            f"{ALLOWED_MODEL}. Select Luna and retry."
        )
    block(event_name, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
