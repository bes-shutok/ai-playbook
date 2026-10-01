#!/usr/bin/env python3
"""Read-only alignment check for the active Codex model guard.

Output contract: every result is a JSON object with the status discriminator
``status`` (``ok`` or ``runtime-policy-unavailable``), the value-bearing
fields of the successful check (``hook_path``, ``config_path``,
``selected_model``), and, on success,
the three empty refusal-detail fields ``failed_check``, ``error``, and
``recovery`` carried as empty strings beside them; a refusal instead fills
``failed_check``, ``error``, and ``recovery`` with the failing check name,
the human-readable reason, and the operator remedy. The empty refusal-detail
fields are part of the success shape the process-level test's allowlist
enforces, so a consumer can key on the full key set regardless of outcome.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import stat
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "agents/hooks/codex-model-guard/require-luna.py"
DEFAULT_REGISTRATION = Path.home() / ".codex" / "hooks.json"
DEFAULT_CONFIG = Path.home() / ".codex" / "config.toml"
WORKER_TOOL = "Agent"
MAX_POLICY_BYTES = 1024 * 1024


def _read_policy_file(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode) or details.st_size > MAX_POLICY_BYTES:
            raise OSError("policy input is not a bounded regular file")
        content = os.read(descriptor, MAX_POLICY_BYTES + 1)
        if len(content) > MAX_POLICY_BYTES:
            raise OSError("policy input exceeds size limit")
        return content
    finally:
        os.close(descriptor)


def _resolve_path(path: Path) -> Path:
    allow_missing = getattr(os.path, "ALLOW_MISSING", None)
    if allow_missing is not None:
        return Path(os.path.realpath(path, strict=allow_missing))
    try:
        return path.resolve(strict=True)
    except FileNotFoundError:
        return path.resolve()


def _matches_worker(matcher: object) -> bool:
    if matcher is None or matcher == "":
        return True
    if not isinstance(matcher, str):
        return False
    try:
        return re.fullmatch(matcher, WORKER_TOOL) is not None
    except re.error:
        return False


def _direct_target(command: object, cwd: Path | None = None) -> Path:
    if not isinstance(command, str) or not command.strip():
        raise ValueError("active hook command is missing")
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError("active hook command is malformed") from exc
    if len(argv) == 1:
        target = Path(argv[0]).expanduser()
    elif len(argv) == 2 and Path(argv[0]).name in {"python", "python3"}:
        target = Path(argv[1]).expanduser()
    else:
        raise ValueError("active hook command must directly invoke one executable")
    if not target.is_absolute():
        target = (cwd or Path.cwd()) / target
    try:
        return _resolve_path(target)
    except (OSError, RuntimeError):
        raise ValueError("registered target cannot be canonicalized") from None


def active_target(document: dict[str, Any], cwd: Path | None = None) -> Path:
    hooks = document.get("hooks")
    if not isinstance(hooks, dict):
        raise ValueError("PreToolUse registration is missing")
    rows = hooks.get("PreToolUse")
    if not isinstance(rows, list):
        raise ValueError("PreToolUse registration is missing")
    targets: list[Path] = []
    for row in rows:
        if not isinstance(row, dict) or not _matches_worker(row.get("matcher")):
            continue
        entries = row.get("hooks")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("type") != "command":
                continue
            command = entry.get("command")
            if not isinstance(command, str):
                continue
            # A guard registration is identified by the expected script name;
            # malformed attempts to wrap it are still refusals, not ignored rows.
            if "require-luna.py" in command:
                targets.append(_direct_target(command, cwd))
    unique = list(dict.fromkeys(targets))
    if len(unique) != 1:
        raise ValueError("enabled PreToolUse registration matching Agent is missing or ambiguous")
    return unique[0]


def selected_model(config_path: Path) -> str:
    config = tomllib.loads(_read_policy_file(config_path).decode("utf-8"))
    agents = config.get("agents")
    value = agents.get("default_subagent_model") if isinstance(agents, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("selected subagent model is missing or malformed")
    return value.strip()


def effective_config(env: dict[str, str] | None = None, cwd: Path | None = None,
                     default_config: Path | None = None) -> Path:
    environment = os.environ if env is None else env
    value = environment.get("CODEX_CONFIG")
    if not value:
        return _resolve_path((default_config or DEFAULT_CONFIG).expanduser())
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (cwd or Path.cwd()) / path
    return _resolve_path(path)


def probe(registration_path: Path = DEFAULT_REGISTRATION, source_path: Path = SOURCE,
          config_path: Path | None = None, *, env: dict[str, str] | None = None,
          cwd: Path | None = None, default_config: Path | None = None) -> dict[str, str]:
    try:
        policy_path = _resolve_path(config_path) if config_path else effective_config(env, cwd, default_config)
    except (OSError, RuntimeError):
        return _failure("selected_config", "Effective Codex config path cannot be resolved.",
                        "Correct the effective Codex config path and rerun the probe.")
    try:
        registration = json.loads(_read_policy_file(registration_path).decode("utf-8"))
        if not isinstance(registration, dict):
            raise ValueError("hook registration must be a JSON object")
        target = active_target(registration, cwd)
    except OSError:
        return _failure("registration", "Hook registration is unreadable.",
                        "Restore the active PreToolUse registration and rerun the probe.")
    except (ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        return _failure("registration", _registration_error(exc),
                        "Correct the active PreToolUse registration and rerun the probe.")
    try:
        installed = _read_policy_file(target)
    except OSError:
        return _failure("installed_guard", "Installed model guard is unreadable.",
                        "Restore the installed model guard from the versioned source and rerun the probe.")
    try:
        source = _read_policy_file(source_path)
    except OSError:
        return _failure("versioned_source", "Versioned model guard source is unreadable.",
                        "Restore access to the repository model guard source and rerun the probe.")
    if installed != source:
        return _failure("guard_alignment", "Installed model guard bytes differ from versioned source.",
                        "Restore the installed model guard from the versioned source and rerun the probe.")
    try:
        model = selected_model(policy_path)
    except OSError:
        return _failure("selected_config", "Selected model config is unreadable.",
                        "Restore access to the effective Codex config and rerun the probe.")
    except (ValueError, tomllib.TOMLDecodeError):
        return _failure("selected_config", "Selected model config is malformed or has no selected model.",
                        "Correct agents.default_subagent_model in the effective Codex config and rerun the probe.")
    return {"status": "ok", "hook_path": str(target), "config_path": str(policy_path),
            "selected_model": model, "failed_check": "", "error": "", "recovery": ""}


def _failure(stage: str, error: str, recovery: str, **fields: str) -> dict[str, str]:
    return {"status": "runtime-policy-unavailable", "failed_check": stage,
            **fields, "error": error, "recovery": recovery}


def _registration_error(exc: Exception) -> str:
    if isinstance(exc, json.JSONDecodeError):
        return "Hook registration is malformed JSON."
    if "canonicalized" in str(exc):
        return "Registered model guard target cannot be canonicalized."
    message = str(exc)
    if "ambiguous" in message:
        return "Enabled PreToolUse registration matching Agent is ambiguous."
    return "Enabled PreToolUse registration matching Agent is missing or malformed."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    result = probe(args.registration, args.source, args.config)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
