# Backlog: Step 5 precheck precondition is phrased via the clocked-only quota leg, so it never literally triggers on idle-only turns

Status: open
Priority: deferred (formal-hardening triage 2026-09-21, user directive: on this personal/pet repo formal fixes are not a priority — no witnessed failure; gates, naming/wording pins, vacuity audits and hypothetical-input hardening auditing other gates defer by default. Revive only on a witnessed scanner/gate mis-fire or a project-priority-profile change. Per-project profiles: see 2026-09-21-project-priority-profiles backlog.)
Workflow: backlog
Class: contract-phrasing precision (wording-only; the overlay's lane-scoped precheck already covers the idle lane)
Discovered: 2026-09-20, review r1 of `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (five-lens panel, contract lens, deferred as Low)

## Finding

SKILL.md Step 5's precheck precondition sentence (around line 97) opens "Ladder precheck: after the quota leg fixes the final fire time and before any ladder step", but the quota leg fixes a fire time only for clocked dispatches. On a turn whose decided dispatch is idle-only (authoring lane through the idle-time primitive), the anchoring clause never literally occurs, so read hyper-literally the precheck is untriggered there; the operative clause that does cover it is "before any ladder step" plus the runtime overlay's own precheck bullet, which explicitly scopes the precheck per lane including the idle lane (`OffPeakCreate` in the required toolset). The contract reads correctly only when the overlay is loaded alongside SKILL.md.

## Driving force

SKILL.md is the runtime-agnostic contract of record and is read standalone by non-ZCode agents; a precondition whose trigger condition is vacuous in a whole dispatch class depends on the overlay for correctness and invites an idle-lane dispatch without a precheck on runtimes whose overlay omits it.

## Fix shape

Rephrase the anchor to be dispatch-class-neutral, for example: "Ladder precheck: after the quota leg (for a clocked dispatch) or the dispatch decision (for an idle-time dispatch), and before any ladder step, run the runtime overlay's ladder precheck for the lane". Keep the existing D3/`turn_error` consequence text unchanged.

## Trigger

Next edit of the SKILL.md Step 5 precondition sentence (any maintenance plan touching Step 5, or the next review that re-prices Step 5 wording), folded together with the pins-suite update the rewording requires (see the companion pin-vacuity backlog item).
