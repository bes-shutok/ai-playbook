#!/usr/bin/env python3
"""Enforce Codex's selected default subagent model before worker launch."""

from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse


WORKER_TOOL_MARKERS = ("agent", "spawn_agent", "spawn-agent", "subagent")


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


def selected_subagent_model(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        with path.open("rb") as stream:
            value = tomllib.load(stream).get("agents", {}).get("default_subagent_model")
    except (OSError, tomllib.TOMLDecodeError, AttributeError):
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


def worker_tool_name(event: dict[str, object]) -> str:
    for key in ("tool_name", "name"):
        value = event.get(key)
        if isinstance(value, str):
            return value.lower()
    return ""


def explicit_worker_model(event: dict[str, object]) -> str | None:
    if worker_tool_name(event) not in WORKER_TOOL_MARKERS:
        return None

    for key in ("tool_input", "input", "arguments"):
        model = model_from_mapping(event.get(key))
        if model is not None:
            return model
    return None


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
    if worker_tool_name(event) not in WORKER_TOOL_MARKERS:
        return 0
    model = selected_subagent_model(Path(os.environ["CODEX_CONFIG"]) if os.environ.get("CODEX_CONFIG") else Path.home() / ".codex" / "config.toml")
    requested_model = explicit_worker_model(event)
    if model is None:
        block(event_name, "Blocked: selected subagent model policy is missing or malformed.")
        return 0
    if requested_model is None:
        block(event_name, "Blocked: worker launch has no direct, nonempty model or selected policy correlation.")
        return 0
    if requested_model != model:
        block(event_name, f"Blocked: worker requested model {requested_model}, but selected subagent model is {model}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
