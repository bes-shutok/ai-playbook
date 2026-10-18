# Backlog: legacy review records without source-plan identity make strict readiness fail closed with no disposition convention

- **Filed:** 2026-10-17
- **Status:** covered (docs/history/plans/2026-10-17-review-record-legacy-identity-blocks-readiness.md)
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** session-witnessed defect (exec-lane run, 2026-10-17)
- **Class:** fix-class
- **Driving force:** efficiency (a certified, execution-ready plan was blocked by record bookkeeping, not by work)

## Problem

Plan-review source-plan identity scoping landed 2026-10-16 (commit 5de323de9): `latest_review_round` resolves each round record's identity from its stats sidecar (`extensions.plan_identity`) or the record's `URL or Artifact:` line, and raises `AmbiguousReviewSeries` when a slug-matching record carries neither ("missing or unreadable identity metadata"). A same-day census found 854 review records in the reviews home predating the convention that carry neither form, plus 261 md records with no stats sidecar at all. Both witnessed instances blocked readiness consults on certified plans the same day:

1. `docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md` (r3-certified, execution-ready): its slug matches a legacy 2026-10-16 r1 record with no identity line, so the strict readiness consult refuses with "cannot resolve plan identity"; adding the missing line then trips the duplicate-round refusal (the new p7ffd23f5 series already owns r1). The sanctioned Step 0.5 gate (`plan_readiness.py --pre-round`) passes because it does not consult review records, but every strict consult fails.
2. `docs/history/plans/2026-10-17-personal-project-remote-boundary-enforcement.md` (r4-certified): its r4 record has no stats sidecar (r1-r3 do), so strict readiness refuses on the missing sidecar.
3. The same fail-closed shape at the closeout boundary: a same-day plan execution staged its r1 review record before the staging validator's schema deploy, and the done sweep's hard validation of every session-touched record then refused the pre-deploy record wholesale; the closeout cleared only after a record-side retrofit to the deployed schema with the repair noted in the record's metadata (the record-side repair class; still no written disposition convention).

## Expected

A written disposition convention for pre-convention and defective review records, and a readiness resolution rule that fails closed on genuine identity conflicts without permanently refusing plans whose series merely contain legacy records.

## Source

- Exec-lane session 2026-10-17 (rearm-dispatch dispatch attempt; census over `.ai-playbook/reviews/`).
- Witnessed again 2026-10-17 (placement-closing-doctrine-enforcement closeout): a pre-deploy r1 record failed the done sweep's hard staging validation and was repaired record-side to the deployed schema.
