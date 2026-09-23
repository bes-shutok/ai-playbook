"""Hermetic renderer/checker for repository-owned Codex hook fixtures."""
from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_EVENTS = {"PreToolUse", "SubagentStart", "SubagentStop", "Stop", "Interrupt", "SessionStart", "PreCompact"}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_hook_definitions(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if document.get("schema_version") != 1:
        raise ValueError("unsupported hook definition schema_version")
    hooks = document.get("hooks")
    if not isinstance(hooks, dict) or set(hooks) != SUPPORTED_EVENTS:
        raise ValueError("hook definitions must declare exactly the supported lifecycle events")
    normalized: dict[str, list[dict[str, Any]]] = {}
    for event, entries in hooks.items():
        if not isinstance(entries, list) or not entries or any(not isinstance(row, dict) for row in entries):
            raise ValueError(f"{event} must have hook registration rows")
        normalized[event] = entries
    return normalized


def render(existing: dict[str, Any], definitions: dict[str, Any]) -> dict[str, Any]:
    additions = validate_hook_definitions(definitions)
    output = json.loads(json.dumps(existing))
    hooks = output.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("fixture hooks must be an object")
    for event, rows in additions.items():
        current = hooks.setdefault(event, [])
        if not isinstance(current, list):
            raise ValueError(f"fixture hook {event} must be an array")
        for row in rows:
            if row not in current:
                current.append(row)
    return output


def selected_model(config_path: Path) -> str:
    with config_path.open("rb") as stream:
        config = tomllib.load(stream)
    model = config.get("agents", {}).get("default_subagent_model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("selected subagent model is missing or malformed")
    return model.strip()


def validate_fixture(existing_path: Path, definitions_path: Path, config_path: Path) -> dict[str, Any]:
    existing = _read_json(existing_path)
    definitions = _read_json(definitions_path)
    expected_model = selected_model(config_path)
    rendered = render(existing, definitions)
    for event in SUPPORTED_EVENTS:
        if not rendered.get("hooks", {}).get(event):
            raise ValueError(f"rendered fixture is missing {event}")
    return {"status": "valid", "selected_subagent_model": expected_model, "rendered": rendered}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--definitions", type=Path, default=ROOT / "agents/hooks/codex-execute-plan/hooks.json.example")
    parser.add_argument("--config", type=Path, required=True, help="repository fixture; live host config is never read")
    args = parser.parse_args()
    try:
        outcome = validate_fixture(args.existing, args.definitions, args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(outcome, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
