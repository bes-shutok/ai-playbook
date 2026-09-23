#!/usr/bin/env python3
"""Thin Codex lifecycle hook bridge for the execute-plan runtime."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EVENTS = {"PreToolUse", "SubagentStart", "SubagentStop", "Stop", "Interrupt", "SessionStart", "PreCompact"}


def emit(value: dict) -> None:
    print(json.dumps(value, sort_keys=True))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        emit({"decision": "block", "reason": "malformed hook input"})
        return 2
    if not isinstance(event, dict) or event.get("hook_event_name") not in EVENTS:
        emit({"decision": "block", "reason": "unknown or malformed lifecycle event"})
        return 2
    name = event["hook_event_name"]
    if name == "SubagentStop" and event.get("stop_hook_active") is True:
        return 0
    root_value = event.get("repo_root") or os.getcwd()
    manifest_value = event.get("manifest_path")
    if not isinstance(root_value, str) or not isinstance(manifest_value, str):
        if name in {"Stop", "SubagentStop", "Interrupt", "SessionStart", "PreCompact", "SubagentStart"}:
            emit({"decision": "block", "reason": "runtime binding unavailable"})
            return 2
        return 0
    root = Path(root_value).resolve()
    manifest = Path(manifest_value)
    if not manifest.is_absolute():
        manifest = root / manifest
    manifest = manifest.resolve()
    if root not in manifest.parents or not manifest.is_file():
        emit({"decision": "block", "reason": "manifest path is outside repository or unavailable"})
        return 2
    try:
        state = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        emit({"decision": "block", "reason": "runtime manifest unavailable"})
        return 2
    operation = None
    payload: dict = {}
    if name == "SubagentStart":
        agent_id = event.get("agent_id")
        parent = event.get("session_id")
        bindings = []
        for key, intent in state.get("handoff_intents", {}).items():
            binding = intent.get("prelaunch_binding") if isinstance(intent, dict) else None
            if isinstance(binding, dict) and not binding.get("consumed") and binding.get("parent_session_id") == parent:
                bindings.append((key, intent, binding))
        if len(bindings) != 1 or not isinstance(agent_id, str) or not agent_id or not isinstance(event.get("agent_type"), str) or not isinstance(event.get("model"), str):
            emit({"decision": "block", "reason": "missing or ambiguous pre-launch binding"})
            return 2
        _, intent, binding = bindings[0]
        successor = intent.get("successor", {})
        payload = {"task_id": successor.get("task_id"), "run_writer_id": binding.get("run_writer_id"),
                   "parent_session_id": parent, "turn_id": event.get("turn_id"), "tool_use_id": event.get("tool_use_id"),
                   "claim_owner_id": binding.get("claim_owner_id"), "claim_token": binding.get("claim_token"),
                   "generation": binding.get("generation"), "launch_id": binding.get("launch_id"),
                   "expected_model": binding.get("expected_model"), "worker_id": agent_id,
                   "provider_session_id": event.get("agent_session_id") or agent_id,
                   "agent_type": event.get("agent_type"), "model": event.get("model"),
                   "repo_root": str(root), "manifest_path": str(manifest)}
        operation = "worker-start"
    elif name in {"SessionStart", "PreCompact", "Interrupt"}:
        operation = "interrupt" if name in {"Interrupt", "PreCompact"} else "reconcile-interruption"
        payload = event.get("receipt", {}) if isinstance(event.get("receipt", {}), dict) else {}
        if operation == "interrupt":
            timestamp = event.get("timestamp")
            if not isinstance(timestamp, str) or not timestamp:
                timestamp = datetime.now(timezone.utc).isoformat()
            payload = {"user_interrupt": timestamp}
        else:
            payload = {"source": event.get("source", "startup"), "session_id": event.get("session_id")}
    elif name in {"Stop", "SubagentStop"}:
        task_id = event.get("task_id")
        claim = state.get("claims", {}).get(task_id) if isinstance(task_id, str) else None
        if not isinstance(claim, dict):
            return 0
        operation = "reserve-continuation"
        payload = {"task_id": task_id, "claim_token": claim.get("token"), "generation": claim.get("generation"),
                   "event_id": event.get("turn_id") or event.get("agent_id") or event.get("timestamp"),
                   "parent_session_id": event.get("session_id"), "event": name,
                   "stop_hook_active": event.get("stop_hook_active") is True}
    if operation is None:
        return 0
    command = [sys.executable, str(root / "scripts/execute_plan_runtime.py"), "--manifest", str(manifest),
               "--operation", operation, "--input", json.dumps(payload, separators=(",", ":"))]
    try:
        result = subprocess.run(command, cwd=root, env={"PATH": os.environ.get("PATH", "")}, capture_output=True,
                                text=True, timeout=2.5 if name == "Interrupt" else 10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        emit({"decision": "block", "reason": "runtime bridge unavailable"})
        return 2
    if result.returncode != 0:
        emit({"decision": "block", "reason": "runtime bridge refused lifecycle receipt"})
        return 2
    try:
        outcome = json.loads(result.stdout)
    except ValueError:
        emit({"decision": "block", "reason": "malformed runtime bridge response"})
        return 2
    if name in {"Stop", "SubagentStop"} and outcome.get("status") == "reserved":
        emit({"decision": "block", "reason": "execute-plan continuation required"})
    elif outcome.get("status") in {"blocked", "refused"}:
        emit({"decision": "block", "reason": str(outcome.get("reason_code", "runtime reconciliation blocked"))})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
