# plans: rewrite the inline trailer-date restatement (plans SKILL.md) as a pointer

Status: done
Origin: tooling-polish plan code review r4 F4 (docs/reviews/2026-09-09-plan-authoring-tooling-polish-code-review-r4.md); EXISTING debt (sentence predates the branch) surfaced by the Task 3 governance rule

## Finding (Low)

agents/skills/plans/SKILL.md (~line 364, authoring workflow) states the concrete trailer gate date `2026-09-08`, restating what `DECISION_MARKER_MIN_DATE` in `scripts/plan_readiness.py` owns. The Task 3 governance sentence (same diff) declares the template block + validator the two surfaces and bars siblings from restating acceptance mechanics; the owner file itself now carries a third statement that drifts if the constant is ever bumped.

## Candidate fix

Rewrite the sentence tail to a pointer: "...enforces the trailer under the sidecar-date rule (see the DECISION_MARKER_MIN_DATE constant in scripts/plan_readiness.py for the exact date and exemption semantics)".
