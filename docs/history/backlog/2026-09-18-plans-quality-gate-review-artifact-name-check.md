# Backlog: plans Plan Quality Gate lacks a per-round review-artifact name check against the readiness gate's discovery

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-18
Class: plans-skill authoring-loop harness gap (staging-artifact filenames are gate input)

## Problem

During an authoring run (six review rounds, 2026-09-18), the review-plan rounds were written under the
filename shape `<date>-<feature-slug>-plan-review-r<N>.md`. The plans skill's Plan Quality Gate prompt
template prescribes `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md`, and the mechanical
readiness gate (`plan_readiness.py`) discovers a plan's review rounds by the canonical glob. The earliest
rounds were therefore invisible to the gate: the staging validator passed every round (it validates
content, not the filename-to-gate binding), and the mismatch surfaced only at the done boundary when
`plan_readiness.py` reported `no review artifact for feature slug`. Recovery required renaming six files
and patching cross-round path references inside the sidecars (coverage attempt `artifact`/`sidecar`
fields and `inherited_coverage` links embed the artifact filename, so a rename orphans them silently;
the gate's local-mode coverage check refused the sidecar until its self-references were patched).

## Expected behavior

A per-round mechanical check in the plans skill's Plan Quality Gate fails loudly when a round's staging
path does not match the readiness gate's discovery shape, before the next round launches. Candidate
shapes: run `plan_readiness.py` (or a narrow name-shape probe) right after writing each round's artifact
pair, or derive each round's output path from the readiness validator's own discovery logic so the two
cannot diverge. The check should also cover the sidecar self-reference hazard above.

## Suspected root area

`agents/skills/plans/SKILL.md` Plan Quality Gate (the sub-agent prompt template prescribes the output
path but nothing re-verifies it per round); `agents/skills/review-staging` (its validator binds content
but not the filename-to-discovery binding). Witness environment: repo-local validators on the skills repo
checkout, 2026-09-18.
