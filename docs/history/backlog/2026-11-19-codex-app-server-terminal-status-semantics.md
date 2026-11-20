# Backlog: exact-ID app-server status does not distinguish terminal from paused

- **Filed:** 2026-11-19, execute-plan follow-up
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class (upstream runtime capability gap)
- **Driving force:** automation + reliability
- **Origin class:** plan follow-up disposition
- **Skill/step:** `agents/skills/maintenance/template-execution.md` provider contract and Codex app-server `thread/read` exact-ID status
- **Cluster:** docs/history/plans/completed/2026-11-19-codex-incomplete-run-owner-status-unavailable.md (the completed plan records the provider-availability verdict; this row owns the app-server status semantics needed to prove terminal state)
- **Cluster:** docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md (that row owns refusal-path tests; this row owns the upstream status evidence gap)
- **Catch frequency:** witnessed once during the 2026-11-19 provider capability probe.
- **False-positive cost:** accepting `notLoaded` as terminal could let recovery take over a paused or otherwise live session; retain unresolved status until upstream evidence distinguishes the states.
- **Review date:** 2027-02-19
- **Dedup probe:** searched open backlog names and bodies for `thread/read`, `notLoaded`, exact-ID status, and terminal-versus-paused semantics. The provider origin row owns general Codex provider availability and the dead-run residual row owns conversion refusal-path tests; neither tracks the specific app-server status union's inability to prove terminal state.

## Problem

The Codex app-server `thread/read` method accepts an exact session ID but returns `notLoaded` when the thread is not loaded. Its status values do not distinguish a terminal session from a paused or otherwise unavailable one. Rollout JSONL evidence also lacks an explicit terminal event. The existing provider contract requires exact-ID evidence that safely distinguishes `terminal`, `live`, `paused`, or `unresolved`, so the observed app-server response cannot support dead-run conversion (`docs/history/release-evidence/session-status-provider/codex.md`).

## Expected

An upstream Codex status surface should expose exact-ID state or terminal-event semantics that can safely distinguish a concluded session from a paused or live one, while allowing unknown state to remain unresolved.

## Suggested fix

Track the missing exact-ID terminal-versus-paused semantics against the Codex app-server surface. Re-probe after an upstream capability change and accept it only if it satisfies the existing provider contract; keep the current fail-closed refusal until then. Do not infer terminal state from `notLoaded`, task completion, or the absence of a live process alone.
