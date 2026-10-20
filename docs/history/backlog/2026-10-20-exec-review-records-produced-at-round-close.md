# Backlog: produce and validate exec-review records at the Phase 3 exit, not at the landing gate

Status: open
Priority: high
Class: fix-class (instruction gap plus a tooling gap in the same step; no new blocking gate)
Origin class: learn Step 1.8 skill-usage capture, execution run of docs/history/plans/completed/2026-10-14-skill-monolith-module-extraction.md (2026-10-20)
Driving force: efficiency + simplicity

## Skill and step

agents/skills/execute-plan/SKILL.md: Step 3.1 verification gate item 3 ("doc follows doing-code-review staging format sufficiently for Step 3.2 parsing") and Step 3.4 round-close seal duty; Phase 4 / the Worktree-first landing bullet's plans-egress arm.

## Observed versus expected

Observed: the staging records' schema and the `-exec-r<N>` landing receipt are first checked by the done landing sweep and the plans-egress guard, after Phase 3 has closed and the archive commit exists. In the witnessing run that cost roughly ten validator fix cycles (the records were repaired one coupled invariant at a time against `scripts/validate_review_staging.py`; lesson #30 re-witnessed) and one refused landing attempt (the `-code-review-r<N>` records carried the archived digest but not the `*-plan-review-<slug>-exec-r<N>.md` name grammar; lesson #107 re-witnessed, fourth same-shape witness in a week).

Expected: Step 3.1's gate names the mechanical check (`python3 scripts/validate_review_staging.py <record>` exit 0 for each round record before Step 3.2), and the Phase 3 exit (the round-close seal duty) writes the `-exec-r<N>` receipt carrying the plan bytes' sha256 into the reviews home as part of closing the loop, so the landing gates confirm evidence that already exists instead of being the first detector.

## Tooling half

`scripts/regenerate_review_sidecar.py` transcribes only the zero-findings class; a round with findings has no producer-side helper or template, so the sidecar and the record's Panel, Counts, and per-finding sections are hand-authored against the validator's fixture builders (`_current_findings_markdown`, `_current_finding`). A producer helper (or a documented template derived from those builders) at Step 3.1 synthesis is the tooling fix; the fixture builders already encode the grammar.

## Evidence

Run records: .ai-playbook/reviews/2026-10-19-skill-monolith-module-extraction-code-review-r1.md and -r2.md (final shapes validate clean), the exec receipt 2026-10-20-plan-review-skill-monolith-module-extraction-exec-r1.md; the landing refusal text "missing evidence leg: exec-review record for slug ... (*-plan-review-<slug>-exec-r<N>.md, hyphen-bounded)". Environment: repo copy of the scripts, interactive run, 2026-10-20.

## Suspected root area

execute-plan Phase 3 record production: the skill text defers the mechanical check and the receipt to the closeout, so a producer-side gap surfaces only at landing. Fix shape per the machinery admission protocol: instruction text naming the existing validator run and the receipt at the exit (no new gate), plus the producer helper; retires the recurring landing-time discovery.
