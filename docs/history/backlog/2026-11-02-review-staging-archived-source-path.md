Status: covered (docs/history/plans/2026-11-02-review-staging-archived-plan-source-identity.md)
Priority: high
Class: fix-class
Origin class: self-serving
Consumer urgency: consumer projects using the shared plan-review and done workflows can hit the same closeout refusal after plan archival.
Driving force: maintainability

## Problem

When a plan is archived, earlier local-equivalence plan-review records keep pointing at the plan's former plans-root path. The final done landing sweep requires the referenced attempt artifact to exist, so it rejects an otherwise superseded historical review and blocks closeout. On 2026-11-02, review r10 for the Codex continuation plan failed because its source was moved to `docs/history/plans/completed/`; retargeting its artifact references to the completed path made the landing sweep pass while preserving the original `source_digest`.

## Exact location

- `agents/skills/plans/SKILL.md`, Plan Lifecycle archive move.
- `agents/skills/review-staging/SKILL.md` and `scripts/validate_review_staging.py`, local-equivalence artifact evidence.
- `agents/skills/done/SKILL.md`, final closeout review-staging gate.

## Suggested fix

Author a focused plan to preserve verifiable historical source identity when a plan moves to the completed archive. Compare archive-time reference relocation with a source-snapshot or validator-resolution approach; preserve the original digest and canonical identity, and keep all existing review gates intact. Do not weaken local-equivalence evidence requirements.

## Evidence and scope

Severity: High, because a historical record path made the authorized closeout fail after archive; the safe workaround was a targeted path update, not a gate bypass. Source reference: this session's review r10 staging pair and the final-closeout landing-sweep refusal, followed by a passing sweep after the path correction.

Why not fixed now: the completed maintenance plan changes continuation behavior and does not include plan archival or review-staging provenance. The one-record path repair is the narrow recovery for this run; the cross-workflow contract needs an implementation plan.

## Dedup probe

Searched open backlog and prompt logs for archived plan review source paths, local-equivalence artifacts, and review-path relocation. The nearby review-record producer constraints concern clean-round mint flags; the review-record durability work concerns missing archived-plan citations. Neither covers a live review record whose source path becomes stale when its plan is archived.
