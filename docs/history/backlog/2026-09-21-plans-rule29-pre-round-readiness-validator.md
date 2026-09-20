# Backlog: plans rule 29 pre-round mechanical gates omit the readiness validator

- **Status:** open
- **Date:** 2026-09-21
- **Origin:** authoring run of docs/plans/2026-09-20-quota-aware-scheduling-semantics.md (2026-09-20/21); captured per learn Step 1.8 (skills-corpus workflow gap, not a lesson duplicate)

## Skill and step

`agents/skills/plans/SKILL.md`, "Validation Commands (authoring rules)" rule 29 (run the repo's cheap mechanical format gates over the plan bytes before the first review round) and the Plan Quality Gate section it feeds.

## Observed versus expected

Observed: rule 29 names the no-em-dash scan and the public-hygiene scan only. An authoring run executed both pre-round gates faithfully, passed seven review-plan rounds (r1-r7) with zero findings on the point, and was then failed by the mechanical readiness validator at the exit gate (done Step 1.5 / plan certification): twelve checklist items carried no `[class: ...]` classification tag (fail-fast reported only the first). The tag rule is enforced exclusively by `scripts/plan_readiness.py` under the sidecar-date rule; reviewers never load it, so no review round can catch it. The post-certification tag fold forced one extra certification round (digest re-baseline), exactly the avoidable-recertification cost rule 29 exists to prevent.

Expected: the readiness validator runs as a third pre-round gate at authoring time. Its pre-round verdict is expected to fail on the absent-review-artifact condition (no sidecar yet), so the pre-round invocation is scoped to the validator's structural checks that do not depend on a review record (classification tags, decision-points trailer, Review Scope path categories) - i.e. the same gate, tolerated to fail on the missing-artifact condition only, with any OTHER failure blocking round 1 the same way a hygiene-scan hit does.

## Suggested fix

Extend plans rule 29: after the em-dash and hygiene scans, run the readiness validator and record its failure class. Failure on "no review artifact" (or the equivalent missing-sidecar condition) is the expected pre-round state and does not block; any structural failure (classification tags, trailer, path categories) blocks round 1 until fixed. Optionally note that a known structural-clean pre-round pass converts the exit gate into a pure digest/verdict binding check.

## Evidence

- 2026-09-20/21 authoring run: pre-round scans green, seven review rounds clean on the point, exit-gate readiness FAILED on "task checklist item in Task 1 carries no [class: ...] classification tag" (first of twelve), one extra certification round required after the tag-only fold.
- The plan's own Validation preamble recorded the empirical gate states, so the miss was visible in the artifact; the enforcing component is the validator, which no reviewer executes.

## Environment

- Playbook repo, ZCode runtime, 2026-09-20/21; repo-local validator copy (scripts/plan_readiness.py) with the deployed home fallback; vendored skill equal to runtime source (same repository).

Suspected root area: plans SKILL.md rule 29 gate enumeration; the readiness validator's role is documented as an exit gate in plans Plan Quality Gate and done Step 1.5 but never as a pre-round structural gate.
