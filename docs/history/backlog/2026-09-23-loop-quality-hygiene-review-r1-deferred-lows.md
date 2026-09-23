# Backlog: loop-quality-hygiene plan review r1 deferred Lows

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Class: review-deferral from the loop-quality-hygiene plan execution (Phase 3 r1)

## Problem

Three valid Low findings from the Phase 3 r1 code-review round were deferred
under the backlog-deferral default instead of fixed in-run:

1. `agents/skills/maintenance/SKILL.md` widened-arm enumeration names only the
   authoring and execution markers in the G1a/G1e occupancy rule; the new audit
   marker (zcode.md) claims audit prompts occupy only G1a, but during G1e's
   evaluation an audit-marked prompt falls into the "anything else occupies
   both lanes" catch-all. Conservative direction, but contradicts the overlay
   claim. Fix: add "an audit marker occupies only `G1a`" to the enumeration and
   state the marker-carriage requirement in the lane paragraph.
2. The plan's Validation Commands commentary (em-dash measurement dated
   2026-09-21) says "three in execute-plan SKILL.md"; execute-plan SKILL.md now
   carries zero (removed by the landed sequential-landing-discipline sibling).
   Fix: refresh or date-stamp the parenthetical as historical.
3. The new suppression-risk sentences in plans/execute-plan SKILL.md point at
   the ZCode-specific overlay `agents/skills/maintenance/zcode.md` — the first
   runtime-agnostic-skill references to a ZCode-only overlay on main. Fix:
   point at the maintenance dispatch-discipline section generically, with the
   zcode overlay named as the ZCode instance.

## r2 addition (2026-09-23)

4. The recipe's canonical invocation `--cadence-days "$FRICTION_AUDIT_CADENCE_DAYS"`
   fails with `invalid int value: ''` when the facts key is unset (argparse rc=2,
   fail-closed before any write). Fix: inline `${VAR:-7}` fallback in the
   invocation bullet.
