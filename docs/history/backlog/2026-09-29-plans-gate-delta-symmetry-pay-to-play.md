# Plans declare a net gate delta, and adding arms pay to play

- **Filed:** 2026-09-29
- **Status:** done (2026-09-30; executed by plan completed/2026-09-29-plans-machinery-delta-doctrine.md, landed main 32aba2dd, impl review r1 zero findings)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Driving force:** simplicity; secondary efficiency
- **Source:** operator direction, 2026-09-29 (Andrey), operationalizing the 2026-09-28 machinery cost-benefit adjudication ("machinery overshot; blockers cost real work vs minor incidents; keep short gate list, shrink rest"). Evidence gathered in the 2026-09-29 execute-plan session: the removal discipline landed by the machinery-elimination pass governs only existing machinery, while new machinery passes review on a code-quality driving force with no counter-declaration.

## Problem

Machinery grows through a one-way conversion: every incident files an origin, origins become plans, plans add gates, refusals, protocols, and state fields. Removal happens only in episodic passes (the 2026-09-28 machinery-elimination-pass), so between passes the ratchet only tightens. The elimination pass made KEEPING machinery disciplined: every registry row needs a witness. It left ADDING machinery undisciplined: a plan declares code-quality, a review panel rewards thoroughness, and the new fence lands. The cost of a new gate is diffuse, paid by every future run in re-checks, re-validations, and refusals, while its benefit is concentrated in one visible incident, so at review time growth always out-argues deletion.

Evidence on disk: `scripts/execute_plan_runtime.py` has accreted to roughly eight thousand lines of recovery paths, preseed gates, capacity reconciliation, and handoff settlement because this repository's largest consumer is its own execution loop and every execution pain becomes a runtime feature request. The in-flight worker-lifecycle plan carries a full reviewed-scope-refresh arm (snapshot-coherent readiness capture, replay fences, actor provenance, a new test suite) for a witnessed incident whose sanctioned exit needs one audited prelaunch transition.

## Issue archaeology

The machinery registry (`scripts/machinery_registry.json`, `scripts/machinery_inventory.py`) is deliberately blind to plan-time growth: a plan lands a new guard, registers it with a red test, and the standing check passes. The registry made deletion honest without making addition symmetric. Nothing in the plans skill or the review-plan workflow asks "how many gates does this plan add, and which does it remove?"

## Expected behavior

- Every plan's Outcome (or a dedicated `Gate delta:` line beside it) declares the net machinery delta: refusal classes, hard gates, fences, protocol layers, and schema state fields added versus removed or simplified.
- An arm that adds a gate must pay for it in the same plan: name the gate deleted or simplified in a sibling arm, or cite a witness showing the incident produced a completed integrity failure (state wrong, evidence lost), not merely a manual step or a stoppable block.
- The review-plan workflow gains one check: a plan adding machinery without pay or witness takes a blocking finding. The declaration is plan prose; no new script, hook, or registry row is created by this origin.

## Possibility space

- **Recommended: authoring rule plus review check, both prose.** One section in the plans skill's authoring rules, one finding class in review-plan. The counter-move to machinery growth must not itself begin as new machinery.
- **Rejected: a numeric gate budget per plan or per flow.** Arbitrary, gameable, and itself a machinery layer.
- **Rejected: extending `machinery_inventory.py` to score friction.** Friction measurement is a separate concern (per-run refusal telemetry) and deserves its own origin; folding it here would embed a telemetry layer inside a simplicity rule.
- **Rejected: banning code-quality as a driving force.** The taxonomy force is legitimate; the missing piece is the delta accounting, not the vocabulary.

## Dedup probe

The 2026-09-28 machinery-elimination-pass origin governs deletion of existing machinery and its regrowth guard; it does not constrain plan-time addition. The 2026-09-26 review-loop-churn-prevention work governs review rounds that generate findings, not gate counts. The 2026-09-28 review-loop-exit-condition-and-metrics origin measures review loop exits, not machinery deltas. No open origin covers the addition-side symmetry.

## Location

- `agents/skills/plans/SKILL.md`: authoring rules and the Outcome format (the gate-delta declaration and the pay-to-play rule).
- `agents/skills/review-plan/SKILL.md`: the review check that blocks unpaid additions.
- Integration Points in both directions per repository rules: plans declares the rule, review-plan verifies it; each consumer step names the provider skill's actual wording.

## Acceptance

- Plans authored after landing carry the gate-delta declaration; a fence-adding arm without a paying sibling arm or an integrity-failure witness draws a blocking finding.
- The change lands as prose in the two named skills with zero new scripts, hooks, or registry rows; the machinery inventory check still passes unchanged.
