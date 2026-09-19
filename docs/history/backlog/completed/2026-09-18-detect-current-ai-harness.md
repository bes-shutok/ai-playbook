# Backlog: detect the current AI harness before applying harness-scoped rules

Status: done (2026-09-18, executed via 2026-09-18-harness-detection-and-budgeting-skip plan)
Priority: high
Workflow: backlog
Source: user-directed 2026-09-18 (refined same day: rules stay harness-agnostic and skip when the live harness is outside the rule family's supported set). Budgeting today only implements `zcode` and `codex`, yet agents also run under Cursor and other harnesses. Without a shared harness check, unsupported sessions still call the Budget gate and the probe's auto-detect can bind to a peer runtime's quota window (for example `~/.zcode/cli/config.json` exists on the same host).
Severity: High (wrong-runtime budget decisions pause or resume the wrong session; unsupported harnesses have no quota surface in this corpus)
Scope: shared detection helper (new or extended script under `scripts/`), consumers in `agents/skills/execute-plan/SKILL.md` (Budget gate), `agents/skills/plans/SKILL.md` (Budget gate), `agents/skills/maintenance/SKILL.md` (quota leg), and docs that teach agents how to name the live harness

## Problem

Budget and maintenance skills assume the live agent is a probed runtime (`zcode` or `codex`). There is no single, skill-facing recipe that answers "which AI harness is this session?" before those rules run.

Today's fragments are scattered and incomplete for this use:

- `scripts/quota_window_probe.py` `detect_runtime` only returns `zcode` or `codex` from config/session paths on disk; it does not ask which process owns the current session.
- `agents/skills/agterm/agent-runtimes.md` lists env markers for agents inside agterm (`CLAUDECODE`, `CURSOR_INVOKED_AS`, `ZCODE_*`), not for Cursor IDE Composer tabs.
- Session hooks already know Cursor via `CURSOR_SESSION_ID` / `CURSOR_CONVERSATION_ID` (lessons-recall session channel), but Budget gate prose never consults that.

Consequence: a session on an unsupported harness (witness: Cursor IDE) on a host that also has ZCode or Codex installed can run the Budget gate against the wrong binding and pause that session for another product's quota window.

## Design principle

Harness detection is shared infrastructure. Rule families stay harness-agnostic in prose: they declare a supported-harness set, check the live harness once, and either apply or skip. They do not hardcode per-product branches like "if Cursor then …" in every skill.

## How to check the current harness (intended contract)

Add one small, stdlib-only helper (preferred: `scripts/detect_ai_harness.py`, or a `--detect-harness` mode on an existing script) that prints a single id and exits 0 when known.

Detection order (first match wins; document and pin with tests):

1. Explicit override: env `AI_HARNESS` or CLI `--harness <id>` (accepted ids: `cursor`, `zcode`, `codex`, `claude`, `agy`, and `unknown`).
2. Cursor IDE / Composer: non-empty `CURSOR_SESSION_ID` or `CURSOR_CONVERSATION_ID` (session bridge or product), or inherited `CURSOR_INVOKED_AS` (Cursor agent CLI under agterm).
3. Claude Code: non-empty `CLAUDE_CODE_SESSION_ID` or `CLAUDECODE=1`.
4. ZCode: non-empty `ZCODE_APP_VERSION` or other live `ZCODE_*` session marker (prefer process env over mere presence of `~/.zcode/cli/config.json`).
5. Codex: only when a Codex-owned session marker is present; do not treat `~/.codex/sessions` alone as "this session is Codex" (that path is host-global and can exist while another harness is running).
6. Else: `unknown`.

Output shape (stable for skills to parse):

```text
{"harness":"cursor|zcode|codex|claude|agy|unknown","evidence":["<signal used>"]}
```

Skills must parse `harness` from stdout JSON, never from exit code alone. Missing script or parse failure maps to `unknown`. The sibling item defines how budgeting treats harnesses outside its supported set (including `unknown`).

## Suggested fix

1. Land the helper and a hermetic selftest covering each signal and the override.
2. Document the recipe once (helper `--help` plus a short note in `docs/AGENTS.md` Hard rules or `agent_workflow_guidelines.md` near other harness notes): run the helper before any harness-scoped rule; compare against that rule family's declared supported set.
3. Point Budget gate and maintenance quota-leg prose at this helper instead of inventing per-skill detection.
4. Keep disk-path auto-detect inside `quota_window_probe.py` for "which provider quota API to call" only after the session harness is already known to be in the budgeting supported set.

## Acceptance criteria

- A Cursor Composer session with `CURSOR_SESSION_ID` set reports `harness: cursor` even when `~/.zcode/cli/config.json` and `~/.codex/sessions` exist.
- A ZCode session reports `zcode` from live env, not from Cursor vars.
- Override `AI_HARNESS=cursor` wins over every auto signal.
- execute-plan, plans, and maintenance Budget/quota sections name this helper as the harness check (exact command pin).
- Sibling backlog item `2026-09-18-skip-unsupported-harness-budgeting.md` can depend on this contract without redefining detection.

## Related

- docs/history/backlog/2026-09-18-skip-unsupported-harness-budgeting.md (consumer: skip budgeting when harness is outside the supported set)
- scripts/quota_window_probe.py (`detect_runtime` today: zcode/codex disk paths only)
- agents/hooks/lessons-recall/README.md (Cursor session channel vars)
- agents/skills/agterm/agent-runtimes.md (env markers inside agterm)
