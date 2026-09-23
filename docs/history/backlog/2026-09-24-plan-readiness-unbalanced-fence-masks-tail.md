# Backlog: plan_readiness fence stripper silently masks an unclosed fence instead of failing closed

- Backlog origin: learn Step 1.8 skill-usage capture, 2026-09-24 P56 plan authoring session (plan-review round r4, finding F1, consistency#unclosed-fence-swallows-plan-tail)
- Driving force: workflow reliability
- Status: open
- Priority: high
- Workflow: backlog

## Problem

`scripts/plan_readiness.py` `_strip_fences` drops every line after an unclosed fence opener (332 lines in, 124 lines out on the witnessed plan) and the readiness probes then evaluate the masked prefix only: `scope_classification_problem`, the decision-marker probe, and the plan-ownership probes all returned clean on a plan whose entire task tail (seven tasks plus the origins ledger) was invisible. The certification verdict therefore passes by masking, voiding exactly the checklist-coverage guarantees the gate exists to enforce. An unbalanced fence is a malformed document; the gate treats it as quotable content and keeps scoring.

## Expected

An unbalanced fence (an opener with no closer, or a closer with no opener) is a hard readiness failure naming the line number, before any probe runs. A weaker acceptable arm: a measured in/out line ratio or tail-anchor presence check that fails when the stripped document loses a declared tail anchor (for example the last `##` heading) or drops more than a bounded fraction of the document.

## Skill / step

- Script: `scripts/plan_readiness.py` (`_strip_fences`, consumed by the readiness probes)
- Skill: `agents/skills/plans/SKILL.md` Plan Quality Gate (the round that certifies the plan relies on the masked probes)

## Suspected root area

The stripper implements quote-mode removal without a balance assertion at EOF, so its documented fail-closed behavior holds only for balanced documents; the review loop caught the masking ad hoc (a reviewer measured strip in/out counts), but the gate itself has no unbalanced-fence detector, so the next occurrence passes certification silently.
