# Backlog: the corrections chain cannot deliver a zero-round re-bind for unclassified mechanical hops

- **Filed:** 2026-10-16, placement-closing-doctrine-enforcement execution, Task 3 intermediate review round 2 (operator-directed honest-reword disposition)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed machinery/doctrine mismatch (executed probe)
- **Class:** fix-class
- **Driving force:** correctness (the doctrine promises a route the gates refuse)
- **Skill/step:** `scripts/corrections_record.py` verifier legs; `scripts/validate_review_staging.py` graded stale-digest gate (~4045-4057); `scripts/plan_readiness.py` corrections context (~1475-1516); `agents/skills/review-staging/SKILL.md` operator-acked arm (~333)
Cluster: docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md (same surface: the plan-delta classifier's exempt-class taxonomy)
- **Environment:** local checkout, 2026-10-16; probes executed against the repo's own modules and fixtures

## Problem

The corrections chain's two row kinds promise coverage for unclassified hunks through the operator-acked arm, but the enforcing gates refuse every unclassified hop regardless of the row kind or a resolved receipt:

1. The exempt classes are format-only (`scripts/plan_delta_classifier.py` `EXEMPT_CLASSES`: checkbox-flip, whitespace, typography), so mechanical hash or reference substitutions classify `unclassified`.
2. The staging validator's graded stale-digest gate injects a strict classification hook unconditionally; `verify_corrections`' classification leg runs after the receipt leg with no kind awareness, so an operator-acked row over an unclassified hop verifies standalone ("chain verified") but refuses under the gate ("corrections verification: classification leg refused: hunk(s) not exempt"). Probe-verified with a complete resolving receipt (witness turn record plus committed classifier-gap row).
3. `plan_readiness.py` threads no witness path into its corrections context, so at the readiness and done gates even the receipt leg refuses ("unresolvable witness").
4. `agents/skills/review-staging/SKILL.md`'s operator-acked sentence says unclassified hunks are covered; the validator's own hook refuses them - a text/machinery discrepancy inside the same contract.

Net effect: any post-certification mechanical digest or reference correction (for example the closing move's hash corrections after a squash landing) forces a fresh review round today, and doctrine text promising the zero-round path for such corrections is false against the machinery (witnessed by the relocation-clause reword during the placement-closing-doctrine-enforcement run).

## Expected

A sanctioned route exists end to end for unclassified-but-mechanical hops: either a narrowly defined exempt class (for example digest-shaped substitutions: both hunk sides single 40- or 64-character hex tokens, hunk count bounded), or a kind-aware classification leg honoring a verified operator-acked receipt, plus witness threading in the readiness and done consumers, and the staging text and validator agreeing.

## Suggested direction

One authoring cycle owning the machinery change with its admission fields: the concrete incident this row witnesses, the catch frequency (every post-certification mechanical relocation correction), the false-positive cost (a semantic change smuggled as a digest-shaped swap; mitigated by the strict hex-shape hunk requirement and bounded hunk count), and a sunset or review date. The classifier widening and the hook change are gate edits and must not land ad hoc mid-lane.

## Current witness

- On 2026-10-18, a cap-closure correction row carried a complete operator-direction receipt and a committed classifier-gap witness, but hard staging validation still refused the substantive plan hunks as unclassified. The plan readiness gate also refused because it did not receive the witness path. Reproduction is preserved in `docs/history/plans/2026-10-18-worktree-closeout-single-start-baseline.md`, its r6 staging record. This confirms the existing issue remains open; priority stays high.

## Evidence

- Round-2 review probe (2026-10-16): acked row over a reference-substitution hop verifies without the gate hook and refuses with it, verbatim reasons quoted in the task review log of the placement-closing-doctrine-enforcement run.
- `scripts/plan_delta_classifier.py` line ~72; `scripts/corrections_record.py` lines ~1093-1113; `scripts/validate_review_staging.py` lines ~4045-4057; `scripts/plan_readiness.py` lines ~1475-1516; `agents/skills/review-staging/SKILL.md` ~333 and ~338.
