# Backlog: maintenance pin vacuity (precheck pin and stand-down-reason pins)

Status: rejected (2026-09-26; unwitnessed hardening: vacuity audit of a pin-checking script; checks about checks)
Priority: deferred (formal-hardening triage 2026-09-21, user directive: on this personal/pet repo formal fixes are not a priority — no witnessed failure; gates, naming/wording pins, vacuity audits and hypothetical-input hardening auditing other gates defer by default. Revive only on a witnessed scanner/gate mis-fire or a project-priority-profile change. Per-project profiles: see 2026-09-21-project-priority-profiles backlog.)
Workflow: backlog
Class: mechanical-pin vacuity (pins hold on fewer occurrences than the invariant they name)
Discovered: 2026-09-20, review r1 of `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (five-lens panel, risk lens, deferred as Low)

## Finding

Two Low pin-vacuity observations in `scripts/check_maintenance_pins.sh` (toolset-precheck block, lines ~350-363):

1. The SKILL.md `ladder precheck` pin (`grep -qF 'ladder precheck' "$S"`) is satisfied by the Step 5 Scoping-note occurrence alone: deleting the Step 5 precondition sentence (the operative contract the pin exists to anchor) still leaves the pin green because the phrase also appears in the scoping note.
2. Each stand-down-reason string pin (`clocked-primitives-absent`, `idle-primitive-absent` over `$Z`) is satisfied by either of the two occurrences in the overlay (the lane-scoped precheck bullet and the both-lanes precedence sentence), so removing any single occurrence passes.

## Driving force

A pin whose green state survives deletion of the content it names does not pin anything; code-quality-at-zero-cost mechanical anchors should fail closed on the exact text they claim to protect (same force as the earlier pins-suite repair rounds recorded in the SKILL.md Revisions ledger).

## Fix shape

Pin occurrence counts, not presence: for the precondition sentence pin, grep the full Step 5 precondition phrase (or assert a minimum count of `ladder precheck` in SKILL.md that only the precondition plus its references satisfy); for the reason strings, either pin the exact anchor sentence of each occurrence or assert the expected count per file so a single deletion trips the pin.

## Trigger

Next touch of `scripts/check_maintenance_pins.sh` (any pins-suite repair or extension round), or the next maintenance plan that edits the Step 5 precondition or the overlay's precheck bullet.
