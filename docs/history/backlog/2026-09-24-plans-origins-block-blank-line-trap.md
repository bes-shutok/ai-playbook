# Backlog: plans origins block ends at its first blank line; blank line after the header silently orphans the list

- Backlog origin: learn Step 1.8 skill-usage capture, 2026-09-24 P56 plan authoring session
- Driving force: workflow reliability
- Status: open
- Priority: high
- Workflow: backlog

## Problem

`scripts/check_plan_origins_closed.py` `extract_origin_basenames` ends the origins block at the first blank line after the `Backlog origins (scope of record):` header line. A plan that renders the block the way Markdown authors naturally write it, a header line, then a blank line, then the bulleted list, collects zero origins: the gate reports "no origins block; nothing to verify" and every promoted item is ungated at completion. A landed plan in the corpus (`docs/plans/2026-09-23-p50-scheduler-state-durability-leftovers.md`) carries exactly that shape with prose on the header line plus a blank line before its seven-item list, and the parser returns only 1 origin (a single backlog path quoted in the header prose) instead of 7. The plans skill's Plan Format template documents neither the contiguity requirement nor the failure mode, so the next author re-creates the trap.

## Expected

The authoring surface and the parser agree on the block shape, and the failure is loud rather than silent. Either the Plan Format template (and the origins-gate docstring) pins "the bulleted list must be contiguous with the header line; a blank line ends the block", or the parser tolerates one blank line between the header and the first list item, and a readiness-level check warns when a plan's Origins block yields fewer basenames than the prose section "Origins and dispositions" lists.

## Skill / step

- Skill: `agents/skills/plans/SKILL.md` (Plan Format, metadata block / Backlog origin placement guidance)
- Script: `scripts/check_plan_origins_closed.py` (`extract_origin_basenames`, the first-blank-line break) and `scripts/plan_readiness.py` (no cross-check that dispositions prose matches parsed origins)

## Suspected root area

Authoring-surface documentation gap plus a permissive parser shape: the block grammar (header through first blank) is undocumented in the authoring rules, and no mechanical gate compares the parsed origin set against the plan's own dispositions ledger, so the zero-origins and one-of-N outcomes both stay green.
