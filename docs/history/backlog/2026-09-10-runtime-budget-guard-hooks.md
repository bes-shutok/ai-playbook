# Backlog: runtime budget-guard hooks (PreToolUse backstop for the 5h quota window)

Status: open
Workflow: backlog
Source: user request 2026-09-10 to research hook-driven budget checks; split out of the execute-plan quota-window item as an independent mechanical backstop
Severity: Low-Medium (defense in depth; the skill-level gate in the companion item is the primary control)
Class: runtime resilience / quota-aware orchestration

## Problem

The execute-plan quota-window gate (companion item
`2026-09-10-execute-plan-quota-window-pause-resume.md`) stops runs only at
clean checkpoint boundaries. Between boundaries, a long implement or review
sub-agent can still run the window into the ground: the provider then rejects
mid-task and the session dies on an opaque error. The same exposure exists for
any long-running flow outside execute-plan (review loops, grilling sessions,
multi-hour interactive work).

Both runtimes expose a tool-call interceptor that can enforce this
mechanically, which no amount of skill discipline can guarantee:

1. ZCode: `hooks.events.PreToolUse` in `~/.zcode/cli/config.json` (hook
   contract proven by the existing `~/.zcode/hooks/no-russian-reply.py` Stop
   hook: JSON on stdin, `{"decision": "block", "reason": ...}` plus exit code 2
   as the block signal, exit 0 to pass).
2. Codex (v0.117.0+): `PreToolUse` in `~/.codex/hooks.json` (feature flag
   `[features] hooks = true` already set in `~/.codex/config.toml`). PreToolUse
   can deny a call via `permissionDecision: "deny"` with a reason; it cannot
   rewrite tool input.

## Location

- `agents/hooks/budget-guard/` (new, pattern of `agents/hooks/skill-gate/` and
  `agents/hooks/plan-readiness/`): hook script(s) plus README with
  registration snippets for both runtimes
- `scripts/`: reuses the shared probe script and its JSON contract from the
  companion item; if the companion item has not landed, the hook ships its own
  minimal probe read (flag-file protocol below keeps this decoupled)
- Host registration (user-managed, never committed): `~/.zcode/cli/config.json`
  hooks block; `~/.codex/hooks.json`

## Suggested fix

1. Flag-file protocol so the hook stays cheap and offline: the probe (from the
   companion item, run at checkpoint boundaries or on a timer) writes a flag
   file under the session tmp (for example
   `budget-guard.<runtime>.flag` containing the reset time) when the binding
   window is close; the PreToolUse hook only checks for that file. No network
   call inside the hook (hook timeouts are 5-10s and every tool call pays the
   latency).
2. Hook behavior when the flag exists: block with a reason that instructs the
   orchestrator, for example: "Provider quota window ends at <time>. Do not
   start new tool work. Finish the current sub-agent step, land the pending
   done commit if any, record the budget pause, and schedule the resume."
   The reason text is the only channel: on ZCode a blocked tool result goes
   back to the model; on Codex the deny reason does the same.
3. Anti-thrash guard: blocking every tool call after the flag exists can
   spiral (each block consumes a model turn). Allow-list the minimal set the
   wrap-up needs (for example git status/commit, file writes to the manifest
   and tmp), or auto-expire the flag after N blocks, or restrict the hook to
   fire only once per session by writing a `fired` marker. Pick one in the
   plan; the default should be the fired marker (single intervention, then the
   skill-level gate owns the rest).
4. Scope: ZCode supports PreToolUse blocks; Codex PreToolUse denies. Do NOT
   use the Stop event for this: on Codex a Stop block means "continue", the
   opposite of the desired effect, and on ZCode a Stop block forces a reply
   rewrite. Keep the surface to PreToolUse only.
5. README in `agents/hooks/budget-guard/` documents: registration JSON for
   both runtimes (tilde paths only, no machine-specific values), the flag-file
   contract, the fail-open rule (missing probe or flag file never blocks), and
   a fixture test mode (synthetic flag file) so the suite needs no network.

## Acceptance

- With a synthetic flag file present, the hook blocks a sampled tool call on
  both runtimes and emits the exact wrap-up reason; without it, every call
  passes (fixture-tested, no network, no credentials).
- The anti-thrash guard is exercised by test: after the chosen mechanism
  triggers, subsequent calls are not blocked again (or the allow-listed wrap-up
  set passes).
- Hook runtime is within the configured timeout budgets (ZCode 5-10s,
  Codex default), measured, not assumed.
- Registration snippets in the README use tilde paths and commit nothing
  host-specific; hygiene scan exits 0.

## Why not fixed now

Depends on the probe and thresholds designed in the companion item; authoring
it first would duplicate the probe logic. Sequence it after (or fold with) the
execute-plan quota-window item once its probe script exists.
