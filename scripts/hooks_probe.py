#!/usr/bin/env python3
"""Agent hook capability probe (read-only install diagnostic).

Reports PASS / DEGRADED / UNSUPPORTED / FAIL per (agent, hook) by checking
adapter symlinks under ``~/`` agent dirs and config registration documented in
``agents/hooks/*/README.md``. Never PASS when the adapter symlink or required
config registration is missing for a FULL-tier cell.

Stdlib-only leaf; no runtime effect on agents.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import runtime_capabilities as capabilities
except ModuleNotFoundError:
    # A deployed hook probe may be invoked through a symlink whose directory
    # does not contain sibling scripts. Resolve the canonical repository path;
    # if the registry module is absent, fail closed instead of using defaults.
    _SCRIPT_DIR = Path(__file__).resolve().parent
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))
    import runtime_capabilities as capabilities

Status = Literal["PASS", "DEGRADED", "UNSUPPORTED", "FAIL"]
Wiring = Literal["NONE", "DEGRADED", "FULL"]
ExpectedTier = Literal["FULL", "DEGRADED", "UNSUPPORTED"]

def probe_matrix(home: Path | None = None) -> list[tuple[str, str, ExpectedTier]]:
    """Read hook rows and expected tiers from the runtime registry."""

    inventory = capabilities.load_inventory()
    rows = inventory.get("hook_profiles")
    if not isinstance(rows, list):
        raise ValueError("registry hook_profiles are required")
    return [(str(row["agent"]), str(row["hook"]), _tier(str(row["expected"]))) for row in rows]


def _hook_profile(agent: str, hook: str) -> dict:
    for row in capabilities.load_inventory().get("hook_profiles", []):
        if row.get("agent") == agent and row.get("hook") == hook:
            return row
    raise KeyError(f"missing registry hook profile: {agent}/{hook}")


def _adapter_raw(agent: str, hook: str) -> str:
    return str(_hook_profile(agent, hook)["adapter"])

_CURSOR_BRIDGE_SYMLINK = "~/.cursor/hooks/cursor-session-bridge.sh"

_LESSONS_RECALL_NEEDLE = "lessons-recall"
_SKILL_GATE_NEEDLE = "skill-gate"
_CURSOR_BRIDGE_NEEDLE = "cursor-session-bridge"


@dataclass(frozen=True)
class ProbeResult:
    agent: str
    hook: str
    status: Status
    detail: str
    expected: ExpectedTier
    runtime_id: str = ""
    capability: str = ""


_RUNTIME_CAPABILITY = "final_response"


def _tier(value: str) -> ExpectedTier:
    tiers: dict[str, ExpectedTier] = {
        "full": "FULL",
        "degraded": "DEGRADED",
        "unsupported": "UNSUPPORTED",
    }
    try:
        return tiers[value.lower()]
    except KeyError as exc:
        raise ValueError(f"invalid registry capability tier: {value!r}") from exc


def profile_expected_tier(inventory: dict, runtime_id: str) -> ExpectedTier:
    """Return a profile capability tier without duplicating registry values."""

    if runtime_id in inventory.get("runtimes", {}):
        profile = inventory["runtimes"][runtime_id]
        capability = profile.get("capabilities", {}).get(_RUNTIME_CAPABILITY)
        if not isinstance(capability, str):
            raise ValueError(f"profile {runtime_id} has no {_RUNTIME_CAPABILITY} tier")
        return _tier(capability)
    if runtime_id in inventory.get("deferrals", {}):
        return "UNSUPPORTED"
    raise KeyError(f"runtime {runtime_id!r} is absent from the registry")


def _profile_data(inventory: dict, runtime_id: str) -> dict:
    if runtime_id in inventory.get("runtimes", {}):
        return inventory["runtimes"][runtime_id]
    if runtime_id in inventory.get("deferrals", {}):
        return inventory["deferrals"][runtime_id]
    raise KeyError(f"runtime {runtime_id!r} is absent from the registry")


def _profile_runtime_ids(inventory: dict) -> list[str]:
    """Order-preserving unique union of canonical and deferred runtime ids.

    Canonical-but-deferred runtimes appear in both lists; the dedupe keeps one
    probe row per runtime so the catalog length pin stays exact.
    """

    root = inventory.get("inventory", {})
    return list(dict.fromkeys(list(root.get("canonical_ids", ())) + list(root.get("deferred_ids", ()))))


def _profile_probe(runtime_id: str, inventory: dict, home: Path | None = None) -> ProbeResult:
    profile = _profile_data(inventory, runtime_id)
    expected = profile_expected_tier(inventory, runtime_id)
    display_name = str(profile.get("display_name", runtime_id))
    fallback = profile.get("fallback")
    if not isinstance(fallback, str) or not fallback.strip():
        fallback = "registry fallback is missing"

    if runtime_id in inventory.get("deferrals", {}):
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "UNSUPPORTED",
            f"unsupported runtime: {profile.get('reason', 'deferred by registry')}",
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )

    profile_row = next((row for row in capabilities.load_inventory().get("hook_profiles", []) if row.get("runtime_id") == runtime_id and row.get("hook") == "plan-readiness"), None)
    if profile_row is None:
        return ProbeResult(display_name, _RUNTIME_CAPABILITY, "DEGRADED" if expected == "DEGRADED" else "FAIL", f"missing adapter; degraded fallback: {fallback}", expected, runtime_id, _RUNTIME_CAPABILITY)
    adapter_raw = profile_row.get("adapter")
    if adapter_raw is None:
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "DEGRADED" if expected == "DEGRADED" else "FAIL",
            f"missing adapter; degraded fallback: {fallback}",
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )

    adapter_path = _expand(adapter_raw, home)
    sym, sym_detail = _symlink_state(adapter_path)
    if sym != "ok" or not adapter_path.is_file():
        detail = "malformed adapter" if sym == "ok" else "missing adapter"
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "FAIL" if expected == "FULL" else "DEGRADED",
            f"{detail}: {sym_detail}; degraded fallback: {fallback}",
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )

    host = str(profile_row["agent"])
    commands = _agent_commands(host, home or Path.home())
    if not _commands_reference(commands, "plan-readiness"):
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "FAIL" if expected == "FULL" else "DEGRADED",
            f"missing registration; degraded fallback: {fallback}",
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )
    if profile_row.get("event") == "final-response":
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "DEGRADED",
                f"unsupported event: {profile_row['event']}; degraded fallback: {fallback}",
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )
    if expected == "FULL":
        return ProbeResult(
            display_name,
            _RUNTIME_CAPABILITY,
            "PASS",
            sym_detail,
            expected,
            runtime_id,
            _RUNTIME_CAPABILITY,
        )
    return ProbeResult(
        display_name,
        _RUNTIME_CAPABILITY,
        "DEGRADED",
        f"degraded fallback: {fallback}",
        expected,
        runtime_id,
        _RUNTIME_CAPABILITY,
    )


def runtime_profile_rows(home: Path | None = None) -> list[ProbeResult]:
    """Probe every canonical and deferred runtime from the registry."""

    inventory = capabilities.load_inventory()
    return [_profile_probe(runtime_id, inventory, home) for runtime_id in _profile_runtime_ids(inventory)]


def _expand(path: str, home: Path | None = None) -> Path:
    if home is not None:
        raw = path.replace("~", str(home), 1) if path.startswith("~") else path
        return Path(raw)
    return Path(path).expanduser()


def _symlink_state(path: Path) -> tuple[str, str]:
    """Return (state, detail) where state is ok|missing|dangling|regular."""
    if path.is_symlink():
        if path.exists():
            return "ok", f"symlink -> {os.readlink(path)}"
        target = os.readlink(path)
        return "dangling", f"dangling symlink -> {target}"
    if path.exists():
        return "regular", "exists but is not a symlink"
    return "missing", "adapter symlink absent"


def _collect_commands(obj: object) -> list[str]:
    cmds: list[str] = []
    if isinstance(obj, dict):
        cmd = obj.get("command")
        if isinstance(cmd, str):
            cmds.append(cmd)
        for value in obj.values():
            cmds.extend(_collect_commands(value))
    elif isinstance(obj, list):
        for item in obj:
            cmds.extend(_collect_commands(item))
    return cmds


def _read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _read_toml_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _commands_reference(commands: list[str], needle: str, adapter: str | None = None) -> bool:
    return any(needle in cmd and (adapter is None or adapter in cmd) for cmd in commands)


def _claude_commands(home: Path) -> list[str]:
    doc = _read_json(home / ".claude" / "settings.json")
    if not isinstance(doc, dict):
        return []
    return _collect_commands(doc.get("hooks", doc))


def _codex_commands(home: Path) -> list[str]:
    hooks_json = _read_json(home / ".codex" / "hooks.json")
    if not isinstance(hooks_json, dict):
        return []
    return _collect_commands(hooks_json.get("hooks", hooks_json))


def _cursor_commands(home: Path) -> list[str]:
    doc = _read_json(home / ".cursor" / "hooks.json")
    if not isinstance(doc, dict):
        return []
    return _collect_commands(doc.get("hooks", doc))


def _ordered_session_start_commands(home: Path) -> list[str]:
    doc = _read_json(home / ".cursor" / "hooks.json")
    if not isinstance(doc, dict):
        return []
    hooks = doc.get("hooks", doc)
    if not isinstance(hooks, dict):
        return []
    session_start = hooks.get("sessionStart")
    if session_start is None:
        return []
    return _ordered_commands_from_hook_array(session_start)


def _ordered_commands_from_hook_array(arr: object) -> list[str]:
    cmds: list[str] = []
    if not isinstance(arr, list):
        return cmds
    for item in arr:
        if not isinstance(item, dict):
            continue
        cmd = item.get("command")
        if isinstance(cmd, str):
            cmds.append(cmd)
        nested = item.get("hooks")
        if isinstance(nested, list):
            cmds.extend(_ordered_commands_from_hook_array(nested))
    return cmds


def _cursor_bridge_detail(home: Path) -> str:
    bridge_path = _expand(_CURSOR_BRIDGE_SYMLINK, home)
    bridge_sym, _ = _symlink_state(bridge_path)
    if bridge_sym != "ok":
        return "no session bridge (no-session steady state)"

    ordered = _ordered_session_start_commands(home)
    bridge_indices = [
        i for i, cmd in enumerate(ordered) if _CURSOR_BRIDGE_NEEDLE in cmd
    ]
    if not bridge_indices:
        return "no session bridge (no-session steady state)"

    recall_indices = [
        i for i, cmd in enumerate(ordered) if _LESSONS_RECALL_NEEDLE in cmd
    ]
    if not recall_indices:
        return "bridge present but lessons-recall not in sessionStart"
    if min(bridge_indices) >= min(recall_indices):
        return "bridge present but not first"
    return "session bridge installed"


def _agy_commands(home: Path) -> list[str]:
    doc = _read_json(home / ".gemini" / "antigravity-cli" / "hooks.json")
    if not isinstance(doc, dict):
        return []
    return _collect_commands(doc.get("hooks", doc))


def _agent_commands(agent: str, home: Path) -> list[str]:
    if agent == "Claude":
        return _claude_commands(home)
    if agent == "Codex":
        return _codex_commands(home)
    if agent == "Cursor":
        return _cursor_commands(home)
    if agent == "agy":
        return _agy_commands(home)
    return []


def _event_commands(agent: str, event: str, home: Path) -> list[str]:
    """Read commands only from the registry-declared host event."""

    paths = {
        "Claude": home / ".claude" / "settings.json",
        "Codex": home / ".codex" / "hooks.json",
        "Cursor": home / ".cursor" / "hooks.json",
        "agy": home / ".gemini" / "antigravity-cli" / "hooks.json",
    }
    doc = _read_json(paths.get(agent, Path("/dev/null")))
    if not isinstance(doc, dict):
        return []
    hooks = doc.get("hooks", doc)
    if not isinstance(hooks, dict):
        return []
    return _ordered_commands_from_hook_array(hooks.get(event, []))


def _codex_has_blocking_pre_tool_use(home: Path) -> bool:
    commands = _event_commands("Codex", "PreToolUse", home)
    return _commands_reference(commands, _SKILL_GATE_NEEDLE, _adapter_raw("Codex", "skill-gate"))


def _assess_wiring(agent: str, hook: str, home: Path) -> Wiring:
    profile = _hook_profile(agent, hook)
    cmds = _event_commands(agent, str(profile["event"]), home)
    adapter = str(profile["adapter"])
    if hook == "lessons-recall":
        if not _commands_reference(cmds, _LESSONS_RECALL_NEEDLE, adapter):
            if agent == "Cursor" and _commands_reference(cmds, _CURSOR_BRIDGE_NEEDLE, _CURSOR_BRIDGE_SYMLINK):
                return "DEGRADED"
            return "NONE"
        if agent == "Claude":
            return "FULL"
        # Codex SessionStart, Cursor sessionStart, agy PreInvocation: degraded.
        return "DEGRADED"
    # skill-gate
    if not _commands_reference(cmds, _SKILL_GATE_NEEDLE, adapter):
        return "NONE"
    if agent == "Codex":
        return "FULL" if _codex_has_blocking_pre_tool_use(home) else "NONE"
    return "FULL"


def _product_ceiling(agent: str, hook: str) -> ExpectedTier:
    """Max tier the product supports even when fully wired."""
    if agent == "Codex":
        return "DEGRADED"
    if agent == "Cursor" and hook == "lessons-recall":
        return "DEGRADED"
    if agent == "agy" and hook == "lessons-recall":
        return "DEGRADED"
    return "FULL"


def _codex_skill_gate_symlink_only(agent: str, hook: str, wiring: Wiring, sym: str) -> bool:
    return agent == "Codex" and hook == "skill-gate" and wiring == "NONE" and sym == "ok"


def _probe_one(
    agent: str,
    hook: str,
    expected: ExpectedTier,
    home: Path | None = None,
) -> ProbeResult:
    # An expected UNSUPPORTED tier resolves BEFORE any adapter-symlink dict
    # lookup or existence check: UNSUPPORTED capabilities ship no adapter, so
    # the missing dict entry (KeyError) or absent symlink must not turn the
    # honest steady state into FAIL. Pinned by the
    # ``unsupported_without_symlink`` selftest fixture.
    if expected == "UNSUPPORTED":
        return ProbeResult(
            agent, hook, "UNSUPPORTED", "no adapter implemented (unwired by scope)", expected
        )

    symlink_raw = _adapter_raw(agent, hook)
    symlink_path = _expand(symlink_raw, home)
    sym, sym_detail = _symlink_state(symlink_path)

    if sym == "dangling":
        return ProbeResult(agent, hook, "FAIL", f"missing adapter: {sym_detail}", expected)
    if sym == "ok" and not symlink_path.is_file():
        return ProbeResult(agent, hook, "FAIL", "malformed adapter: target is not a file", expected)
    if sym in ("missing", "regular"):
        return ProbeResult(
            agent,
            hook,
            "FAIL",
            f"malformed adapter: {sym_detail}" if sym == "regular" else "missing adapter",
            expected,
        )

    wiring = _assess_wiring(agent, hook, home or Path.home())
    ceiling = _product_ceiling(agent, hook)

    if _codex_skill_gate_symlink_only(agent, hook, wiring, sym):
        detail = "unsupported event: pre_tool_use is not blocking; adapter present"
        return ProbeResult(agent, hook, "DEGRADED", detail, expected)

    if wiring == "NONE":
        return ProbeResult(
            agent,
            hook,
            "FAIL",
            "config registration missing",
            expected,
        )

    effective = wiring
    if ceiling == "DEGRADED" and effective == "FULL":
        effective = "DEGRADED"

    if expected == "FULL" and effective != "FULL":
        return ProbeResult(
            agent,
            hook,
            "FAIL",
            f"expected FULL wiring; got {effective.lower()}",
            expected,
        )

    if effective == "FULL" and ceiling == "FULL":
        detail = sym_detail
        if agent == "Cursor" and hook == "lessons-recall":
            detail += f"; {_cursor_bridge_detail(home or Path.home())}"
        return ProbeResult(agent, hook, "PASS", detail, expected)

    detail = sym_detail
    if agent == "Cursor" and hook == "lessons-recall":
        detail += f"; {_cursor_bridge_detail(home or Path.home())}"
    return ProbeResult(agent, hook, "DEGRADED", detail, expected)


def probe_all(home: Path | None = None) -> list[ProbeResult]:
    hook_rows = [_probe_one(agent, hook, expected, home) for agent, hook, expected in probe_matrix(home)]
    return hook_rows + runtime_profile_rows(home)


def _format_table(results: list[ProbeResult]) -> str:
    headers = ("Agent", "Hook", "Status", "Expected", "Detail")
    rows = [
        (r.agent, r.hook, r.status, r.expected, r.detail) for r in results
    ]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    lines = [
        "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        "  ".join("-" * widths[i] for i in range(len(headers))),
    ]
    for row in rows:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(row))))
    lines.append("")
    lines.append("Classifier: lessons_recall core default is v1 (--classifier v2 is opt-in CLI only).")
    return "\n".join(lines)


def selftest(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    filter_name: str | None = None
    for arg in args:
        if arg.startswith("--selftest#"):
            filter_name = arg[len("--selftest#") :]
            break

    all_ok = True

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal all_ok
        if filter_name is not None and filter_name not in label:
            return
        if condition:
            print(f"PASS: {label}")
        else:
            suffix = f" - {detail}" if detail else ""
            print(f"FAIL: {label}{suffix}")
            all_ok = False

    # ------------------------------------------------------------------ #
    # frozen_agents_listed: PROBE_MATRIX rows and expected tiers.
    # ------------------------------------------------------------------ #
    matrix = probe_matrix()
    agents = {row[0] for row in matrix}
    check(
        "frozen_agents_listed: Claude/Codex/agy/Cursor rows present",
        agents == {"Claude", "Codex", "agy", "Cursor"},
        repr(sorted(agents)),
    )
    expected_by_key = {(a, h): tier for a, h, tier in matrix}
    check(
        "frozen_agents_listed: Claude lessons-recall expected FULL",
        expected_by_key.get(("Claude", "lessons-recall")) == "FULL",
        repr(expected_by_key.get(("Claude", "lessons-recall"))),
    )
    check(
        "frozen_agents_listed: Codex lessons-recall expected DEGRADED",
        expected_by_key.get(("Codex", "lessons-recall")) == "DEGRADED",
        repr(expected_by_key.get(("Codex", "lessons-recall"))),
    )
    check(
        "frozen_agents_listed: Codex skill-gate expected DEGRADED",
        expected_by_key.get(("Codex", "skill-gate")) == "DEGRADED",
        repr(expected_by_key.get(("Codex", "skill-gate"))),
    )
    check(
        "frozen_agents_listed: agy skill-gate expected FULL",
        expected_by_key.get(("agy", "skill-gate")) == "FULL",
        repr(expected_by_key.get(("agy", "skill-gate"))),
    )
    check(
        "frozen_agents_listed: Cursor skill-gate expected FULL",
        expected_by_key.get(("Cursor", "skill-gate")) == "FULL",
        repr(expected_by_key.get(("Cursor", "skill-gate"))),
    )
    plan_readiness_tiers = {
        a: tier for a, h, tier in matrix if h == "plan-readiness"
    }
    # Derived from the single ``agents`` literal checked above (no re-hardcoded
    # four-agent copy): plan-readiness must cover the SAME agent set as the
    # wired hooks and be UNSUPPORTED for every one of them.
    check(
        "frozen_agents_listed: plan-readiness expected UNSUPPORTED for every agent",
        set(plan_readiness_tiers) == agents
        and all(tier == "UNSUPPORTED" for tier in plan_readiness_tiers.values()),
        repr(sorted(plan_readiness_tiers.items())),
    )
    check(
        "frozen_agents_listed: twelve (agent, hook) cells",
        len(matrix) == 12,
        str(len(matrix)),
    )

    # ------------------------------------------------------------------ #
    # unsupported_without_symlink: an expected UNSUPPORTED capability has no
    # adapter symlink (and no _ADAPTER_SYMLINKS entry); the probe must resolve
    # UNSUPPORTED, not FAIL, so --all exits 0 while the limitation stays
    # recorded. Pins the _probe_one ordering: UNSUPPORTED resolves BEFORE any
    # adapter-symlink dict lookup or existence check.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        result = _probe_one("Claude", "plan-readiness", "UNSUPPORTED", home=home)
        check(
            "unsupported_without_symlink: expected UNSUPPORTED, no adapter -> UNSUPPORTED (not FAIL)",
            result.status == "UNSUPPORTED",
            f"{result.status} {result.detail!r}",
        )

    # ------------------------------------------------------------------ #
    # detects_symlink_dangle: dangling adapter symlink -> FAIL.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        adapter_dir = home / ".claude" / "hooks"
        adapter_dir.mkdir(parents=True)
        victim = adapter_dir / "lessons-recall.sh"
        os.symlink(str(home / "missing-target"), str(victim))
        result = _probe_one("Claude", "lessons-recall", "FULL", home=home)
        check(
            "detects_symlink_dangle: dangling symlink -> FAIL",
            result.status == "FAIL" and "dangling" in result.detail,
            f"{result.status} {result.detail!r}",
        )

    # ------------------------------------------------------------------ #
    # Synthetic wiring arms (isolated HOME).
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)

        def install_adapter(
            agent: str, hook: str, *, home_dir: Path | None = None
        ) -> Path:
            install_home = home if home_dir is None else home_dir
            raw = _adapter_raw(agent, hook)
            path = _expand(raw, install_home)
            path.parent.mkdir(parents=True, exist_ok=True)
            target = install_home / f"adapter-{agent}-{hook.replace('-', '_')}.sh"
            target.write_text("# probe fixture\n", encoding="utf-8")
            if path.is_symlink() or path.exists():
                path.unlink()
            path.symlink_to(target)
            return path

        def write_claude_settings(commands: list[str]) -> None:
            hooks: dict[str, list] = {"SessionStart": [], "PreToolUse": []}
            for cmd in commands:
                if "lessons-recall" in cmd:
                    hooks["SessionStart"] = [
                        {"hooks": [{"type": "command", "command": cmd}]}
                    ]
                if "skill-gate" in cmd:
                    hooks["PreToolUse"] = [
                        {
                            "matcher": "Write|Edit|MultiEdit",
                            "hooks": [{"type": "command", "command": cmd}],
                        }
                    ]
            path = home / ".claude" / "settings.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"hooks": hooks}), encoding="utf-8")

        install_adapter("Claude", "lessons-recall")
        write_claude_settings(["~/.claude/hooks/lessons-recall.sh"])
        ok = _probe_one("Claude", "lessons-recall", "FULL", home=home)
        check(
            "wiring_claude_lessons: symlink + UserPromptSubmit -> PASS",
            ok.status == "PASS",
            f"{ok.status} {ok.detail}",
        )

        install_adapter("Claude", "skill-gate")
        write_claude_settings(
            [
                "~/.claude/hooks/lessons-recall.sh",
                "~/.claude/hooks/skill-gate.sh",
            ]
        )
        sg = _probe_one("Claude", "skill-gate", "FULL", home=home)
        check(
            "wiring_claude_skill_gate: symlink + PreToolUse -> PASS",
            sg.status == "PASS",
            f"{sg.status} {sg.detail}",
        )

        install_adapter("Codex", "skill-gate")
        codex_sg = _probe_one("Codex", "skill-gate", "DEGRADED", home=home)
        check(
            "wiring_codex_skill_gate: symlink only -> DEGRADED",
            codex_sg.status == "DEGRADED"
            and "unsupported event" in codex_sg.detail,
            f"{codex_sg.status} {codex_sg.detail}",
        )

        codex_hooks = home / ".codex" / "hooks.json"
        codex_hooks.parent.mkdir(parents=True, exist_ok=True)
        install_adapter("Codex", "lessons-recall")
        codex_hooks.write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "bash ~/.codex/hooks/lessons-recall.sh",
                                    }
                                ]
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        codex_lr = _probe_one("Codex", "lessons-recall", "DEGRADED", home=home)
        check(
            "wiring_codex_lessons: SessionStart wired -> DEGRADED (not PASS)",
            codex_lr.status == "DEGRADED",
            f"{codex_lr.status} {codex_lr.detail}",
        )

        with tempfile.TemporaryDirectory() as td2:
            home2 = Path(td2)
            install_adapter("Codex", "lessons-recall", home_dir=home2)
            no_cfg = _probe_one("Codex", "lessons-recall", "DEGRADED", home=home2)
            check(
                "honesty: Codex lessons symlink without config -> FAIL",
                no_cfg.status == "FAIL"
                and "config registration missing" in no_cfg.detail,
                f"{no_cfg.status} {no_cfg.detail}",
            )

        codex_config_only = home / ".codex" / "config.toml"
        codex_config_only.parent.mkdir(parents=True, exist_ok=True)
        codex_config_only.write_text(
            'unrelated = "path/to/lessons-recall.sh"\n',
            encoding="utf-8",
        )
        if (home / ".codex" / "hooks.json").is_file():
            (home / ".codex" / "hooks.json").unlink()
        stray_cfg = _probe_one("Codex", "lessons-recall", "DEGRADED", home=home)
        check(
            "honesty: Codex unrelated config.toml value without hooks -> FAIL",
            stray_cfg.status == "FAIL"
            and "config registration missing" in stray_cfg.detail,
            f"{stray_cfg.status} {stray_cfg.detail}",
        )

    # ------------------------------------------------------------------ #
    # cursor_bridge_order: sessionStart array order pins bridge-first rule.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        adapter_dir = home / ".cursor" / "hooks"
        adapter_dir.mkdir(parents=True)

        def install_cursor_fixture(commands: list[str]) -> None:
            for name, cmd in (
                ("lessons-recall.sh", "lessons-recall"),
                ("cursor-session-bridge.sh", "cursor-session-bridge"),
            ):
                path = adapter_dir / name
                target = home / f"fixture-{name}"
                if not target.exists():
                    target.write_text("# fixture\n", encoding="utf-8")
                if path.is_symlink() or path.exists():
                    path.unlink()
                path.symlink_to(target)
            hooks_path = home / ".cursor" / "hooks.json"
            hooks_path.parent.mkdir(parents=True, exist_ok=True)
            hooks_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "sessionStart": [
                                {"type": "command", "command": cmd}
                                for cmd in commands
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

        install_cursor_fixture(
            [
                "bash ~/.cursor/hooks/cursor-session-bridge.sh",
            ]
        )
        hooks_path = home / ".cursor" / "hooks.json"
        hooks_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "sessionStart": [
                            {
                                "type": "command",
                                "command": "bash ~/.cursor/hooks/cursor-session-bridge.sh",
                            }
                        ],
                        "preToolUse": [
                            {
                                "type": "command",
                                "command": "bash ~/.cursor/hooks/lessons-recall.sh",
                            }
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        miswired_recall = _probe_one("Cursor", "lessons-recall", "DEGRADED", home=home)
        check(
            "cursor_bridge_order: bridge without recall in sessionStart",
            miswired_recall.status == "DEGRADED"
            and "bridge present but lessons-recall not in sessionStart"
            in miswired_recall.detail,
            f"{miswired_recall.status} {miswired_recall.detail!r}",
        )

        install_cursor_fixture(
            [
                "bash ~/.cursor/hooks/cursor-session-bridge.sh",
                "bash ~/.cursor/hooks/lessons-recall.sh",
            ]
        )
        ok_order = _probe_one("Cursor", "lessons-recall", "DEGRADED", home=home)
        check(
            "cursor_bridge_order: bridge before recall -> session bridge installed",
            ok_order.status == "DEGRADED"
            and "session bridge installed" in ok_order.detail,
            f"{ok_order.status} {ok_order.detail!r}",
        )

        install_cursor_fixture(
            [
                "bash ~/.cursor/hooks/lessons-recall.sh",
                "bash ~/.cursor/hooks/cursor-session-bridge.sh",
            ]
        )
        bad_order = _probe_one("Cursor", "lessons-recall", "DEGRADED", home=home)
        check(
            "cursor_bridge_order: recall before bridge -> bridge present but not first",
            bad_order.status == "DEGRADED"
            and "bridge present but not first" in bad_order.detail,
            f"{bad_order.status} {bad_order.detail!r}",
        )

    # ------------------------------------------------------------------ #
    # registry_parity: every eligible and deferred runtime is represented by
    # a registry-derived capability row, and missing host wiring is never a
    # successful PASS result.
    # ------------------------------------------------------------------ #
    registry = capabilities.load_inventory()
    documented_ids = set(registry["inventory"]["canonical_ids"]) | set(
        registry["inventory"]["deferred_ids"]
    )
    profile_rows = runtime_profile_rows()
    check(
        "registry_parity: every documented runtime has one final-response row",
        {row.runtime_id for row in profile_rows} == documented_ids,
        repr(sorted(row.runtime_id for row in profile_rows)),
    )
    check(
        "registry_parity: profile rows use registry expected tiers",
        all(
            row.expected
            == profile_expected_tier(registry, row.runtime_id)
            for row in profile_rows
        ),
        repr([(row.runtime_id, row.expected) for row in profile_rows]),
    )
    check(
        "registry_parity: missing adapter or registration never PASSes",
        all(
            row.status != "PASS"
            for row in profile_rows
            if any(token in row.detail for token in ("missing adapter", "missing registration"))
        ),
    )
    check(
        "registry_parity: deferred runtime fails closed as UNSUPPORTED",
        all(
            row.status == "UNSUPPORTED"
            for row in profile_rows
            if row.runtime_id in registry["inventory"]["deferred_ids"]
        ),
    )

    # ------------------------------------------------------------------ #
    # diagnostic_classes: malformed adapter data, missing registration, and
    # unsupported host events remain distinct diagnostics.
    # ------------------------------------------------------------------ #
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        adapter = _expand(_adapter_raw("Codex", "skill-gate"), home)
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_text("not a symlink", encoding="utf-8")
        malformed = _probe_one("Codex", "skill-gate", "DEGRADED", home=home)
        check(
            "diagnostic_classes: malformed adapter is distinct and fail-closed",
            malformed.status == "FAIL" and "malformed adapter" in malformed.detail,
            f"{malformed.status} {malformed.detail!r}",
        )

    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--selftest" in args or any(a.startswith("--selftest#") for a in args):
        return selftest(args)

    parser = argparse.ArgumentParser(description="Probe agent hook install wiring.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print human-readable table for the live install.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run in-memory selftests.",
    )
    ns = parser.parse_args(args)

    if ns.all:
        results = probe_all()
        print(_format_table(results))
        if any(r.status == "FAIL" for r in results):
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
