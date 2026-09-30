# Plan: Review-staging review-plan row sync

Backlog origin: `docs/history/backlog/2026-09-28-review-staging-integration-points-review-plan-row-stale.md`
Driving force: documentation precision; secondary reliability (a mirrored Integration Points claim that names a shape the peer skill no longer has is reporting drift; the corpus precedent for the non-closed-set force is the completed documentation-precision plan family)
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-review-staging-review-plan-row-sync-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The `review-plan` row of review-staging's Integration Points table describes the shape review-plan actually carries after the sidecar-schema-drift plan landed, so the mirrored claim stops advertising an inlined schema that no longer exists.

- The row reads that review-plan carries a stable-core summary of the sidecar schema with the enforced contract owned by the validator and review-staging's authoritative copy, matching review-plan's Step 3 byte-for-byte in substance.
- The mirror is truthful in both directions: review-plan's summary already names review-staging as the authority, and review-staging's row now names the summary form back.

Gate delta: none. The change rewords one table cell's description of an existing mechanism to match the mechanism's landed shape; it adds no refusal class, no gate, no checked condition, and no field, and removes nothing.

## Assumptions

- The sibling origin of the p93 log entry (`2026-09-28-review-posting-completion-evidence.md`) is already done: executed+landed `2026-09-30-review-posting-landing-receipt` (squash 294d1297, exec review r3 ready=yes zero blocking), so its posting-receipt arms are out of this plan's scope and the file is cited nowhere. (Basis: the completed copy's Status receipt, read today.)
- No review-plan edit: its Step 3 stable-core summary already declares "the enforced contract is the validator, not this copy" and names review-staging's authoritative documentation, so the mirror completes with this plan's one cell. (Basis: review-plan SKILL.md Step 3, read today.)
- The drift plan's scope decision (never editing review-staging inside itself) is why this row lands as its own tracked companion item. (Basis: the origin's Problem paragraph and the completed drift plan's scope decision.)
- No pins touch review-staging's SKILL.md. (Basis: check_maintenance_pins.sh sweep, zero hits, this cycle.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: review-staging's review-plan Integration Points row is reworded from "inlines sidecar schema (Step 3)" to the stable-core-summary form the drift plan landed; force: documentation precision.

The drift plan shrank review-plan's inline sidecar schema to a stable-core summary with a validator-first rule, and deliberately left review-staging (the documentation authority) alone. That left review-staging's table telling producers review-plan "inlines sidecar schema (Step 3)" - a claim about a copy that no longer exists in the advertised form. This plan lands the tracked companion: the one cell now says review-plan "carries a stable-core summary of the sidecar schema (Step 3; the enforced contract is the validator and review-staging's authoritative copy)". Everything else in the row and the file stays byte-identical.

## Evaluation Criteria

**Quality dimensions:**
- Truthfulness: the row's description matches review-plan's landed Step 3 (stable-core summary, validator-first, `--hard` gate) with no over-claim.
- Minimality: exactly one table cell changes; the other eight rows and every other line of review-staging stay byte-identical.

**Done when:**
- Every Validation Commands line exits 0, including the absence canaries proving the stale claim is gone and the anchored rows are undisturbed.

**Ship when:**
- The next plan-review round reads the row and finds the described shape on disk (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-staging/SKILL.md`

**Tests:**
- none; verification is the grep canaries and the command gates in Validation Commands.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-plan/SKILL.md`; reason: its Step 3 is the landed authority this row mirrors; no edit (Assumptions).
- `docs/history/backlog/2026-09-28-review-posting-completion-evidence.md`; reason: done with its own receipt (Assumptions), cited nowhere.
- the other eight Integration Points rows; reason: out of this origin's scope, untouched by any task.

## Validation Commands

```bash
grep -qF 'carries a stable-core summary of the sidecar schema (Step 3; the enforced contract is the validator and review-staging' agents/skills/review-staging/SKILL.md || { echo FAIL: row reword; exit 1; }
[ "$(grep -cF 'inlines sidecar schema (Step 3)' agents/skills/review-staging/SKILL.md)" -eq 0 ] || { echo FAIL: stale claim survives; exit 1; }
[ "$(grep -c '^| `review-plan` |' agents/skills/review-staging/SKILL.md)" -eq 1 ] || { echo FAIL: row count drift; exit 1; }
[ "$(grep -c '^| `doing-code-review` |' agents/skills/review-staging/SKILL.md)" -eq 1 ] || { echo FAIL: sibling row disturbed; exit 1; }
grep -qF 'stable-core summary of the sidecar schema' agents/skills/review-plan/SKILL.md || { echo FAIL: mirror source gone; exit 1; }
grep -qF 'the enforced contract is the validator, not this copy' agents/skills/review-plan/SKILL.md || { echo FAIL: validator-first rule gone; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL: pins baseline; exit 1; }
bash scripts/check-no-em-dash.sh file agents/skills/review-staging/SKILL.md docs/history/plans/2026-10-01-review-staging-review-plan-row-sync.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: reword the review-plan row to the stable-core-summary form

Files:
- `agents/skills/review-staging/SKILL.md`

Evidence:
- `grep -qF 'carries a stable-core summary of the sidecar schema (Step 3; the enforced contract is the validator and review-staging' agents/skills/review-staging/SKILL.md`; covers the row reworded
- `[ "$(grep -cF 'inlines sidecar schema (Step 3)' agents/skills/review-staging/SKILL.md)" -eq 0 ]`; covers the stale claim gone

- [ ] Run → expect RED: `grep -cF 'inlines sidecar schema (Step 3)' agents/skills/review-staging/SKILL.md` returns 1 [class: REPOSITORY_TEST]
- [ ] In the Integration Points table's `review-plan` row, replace the span `inlines sidecar schema (Step 3)` with `carries a stable-core summary of the sidecar schema (Step 3; the enforced contract is the validator and review-staging's authoritative copy)` keeping every other character of the row unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence commands; both absence canaries (`| \`review-plan\` |` and `| \`doing-code-review\` |` row counts) still return 1 [class: REPOSITORY_TEST]
- [ ] Commit: `skills: review-staging row mirrors review-plan's stable-core summary` [class: IMPLEMENTATION_REQUIRED]

### Task 2: mirror and regression verification

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the mirror truthfulness, the absence canaries, and the regression gates

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
- [ ] Confirm the mirror reads truthfully in both directions: review-staging's row names the stable-core summary with review-staging as authority, and review-plan's Step 3 names review-staging's authoritative documentation; record the two quotes in the task log [class: REPOSITORY_TEST]
