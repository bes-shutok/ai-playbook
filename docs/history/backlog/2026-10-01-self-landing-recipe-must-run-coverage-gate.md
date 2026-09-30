Status: done (2026-10-01; executed+landed docs/history/plans/completed/2026-10-01-self-landing-coverage-gate-step.md, squash main 43c3745e, exec review r1 ready=yes zero blocking)(2026-09-30 23:58 a second plan for an already-covered origin landed as 1d7ee68b, 25 minutes after the covering plan 5138a9fc landed; the coverage gate detects the conflict on the same bytes today; user directive: continuous interleave loop, investigate findings feed the next cycle)

# The authoring self-landing recipe must run the duplicate-origin coverage gate before the landing commit

## Problem

The plans skill's Plan Lifecycle carries the landing closeout as a hard gate: run `check_plan_origins_closed.py --check-coverage <plan>` before the landing commit (a non-zero exit refuses the landing, naming the covering plan and the first-landed-wins remedy), then `--mark-covered` so the covered flip rides the landing. The gate works: invoked against the landed duplicate today, it exits 1 and names the covering plan. But the operational procedure an authoring self-landing actually follows - the landing paragraph in `agents/skills/maintenance/prompt-templates.md` - never invokes either mode, so a self-landing that follows the recipe step by step skips the gate entirely.

Witnessed 2026-09-30: a peer authoring lane landed `1d7ee68b` (orphaned-manifest disposition and survey arm, origin `2026-09-29-interrupted-run-and-stranded-work-prevention-ideas` ideas B+D) at 23:58, twenty-five minutes after the covering plan `5138a9fc` (same origin, ideas B+D+E) had landed on main. Both plans prescribe overlapping machinery for the same origin (a disposition operation, a survey classification arm, detection changes). The gate on main detects the conflict (`--check-coverage` on the landed duplicate exits 1, first-landed-wins remedy), so the landing flow that produced 1d7ee68b did not run it. Second witness in the same incident: the peer lane also never created the authoring claim stub the same recipe file's AUTHORING CLAIM paragraph prescribes (the covering session's stub was live throughout their authoring window; no noclobber refusal fired on their side), so the recipe's steps are only as strong as a session's decision to follow the document rather than the skill's gate list.

## Observed versus expected

- Observed: two landed plans cite one origin with overlapping scope; the conflict was found by the covering session's next-cycle survey reading the main log, not by any gate; an execution of the duplicate is in flight, compounding the overlap.
- Expected: a self-landing whose plan names an already-covered origin refuses at the coverage gate with the first-landed-wins remedy, before the landing commit; the recipe that operationalizes the lifecycle carries the step.

## Proposal (minimal shape, for plan authoring to refine)

1. Add one step to the prompt-templates landing paragraph (before the commit step): run the coverage gate exactly as the lifecycle hard gate prescribes (repo-local script first, then the deployed copy; non-zero exit = refuse and report the covering plan and remedy), and after it passes run `--mark-covered` so the covered flip rides the landing commit.
2. Optionally mirror the step in any other operational landing recipe the corpus carries (grep for the landing-commit recipe shapes), so no landing path skips the lifecycle's hard gate.

## Rejected alternatives

- Rely on the lifecycle hard gate text alone: rejected; it is already on main and did not fire - the gap is the operational recipe the dispatched sessions follow step by step.
- Move the gate into a hook or the done sweep: rejected; machinery needing its own witness, and the landing commit is the latest point the refusal is still cheap (before it, the authoring session can fold into the covering plan without a landed artifact to unwind).

## Witnesses

- `1d7ee68b` (23:58) landed citing the origin already covered by `5138a9fc`'s citation (23:35-ish landing); `--check-coverage` on the duplicate exits 1 on current main naming the covering plan (re-derive at authoring time).
- The peer lane's authoring window shows no claim stub in `docs/tmp/authoring-claims/` for the item while the covering session's stub was live (the covering session created its stub at 22:55 and deleted it at closeout ~01:10).
