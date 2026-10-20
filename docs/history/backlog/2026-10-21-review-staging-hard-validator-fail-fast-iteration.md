# review-staging hard validator fail-fast iteration cost

Cluster: review-staging-validator
Status: open
Origin: exec session 2026-10-21 (plan gate-removal-closeout-accounting Phase 3 canonical record authoring; witnessed 2026-10-21).

Authoring one canonical code-review record took eight distinct fix-validate rounds against `scripts/validate_review_staging.py --hard`: each pass surfaced exactly one gate failure (finding conservation, counts parity, witness-ledger table shape, per-worker budget, F-id 1:1 block match, reachability enum, blast_radius enum, pattern-owner set, risk-signal tag, last-fix-commit agreement, id/base/run-id hex shapes, attempt deadlines). Every individual contract clause is documented in `agents/skills/review-staging/SKILL.md`, but the clauses are spread across sections, so a first-time canonical author cannot pre-check them and pays the fail-fast cost one error at a time.

- Witnessed cost: eight rounds for one record; the record still validated only after the eighth fix.
- The validator's ordering is deliberate (deterministic first-error ordering by coverage presence, source-kind family, and digest family, `scripts/validate_review_staging.py` module docstring and the ordering comment near the hard-mode gate), so the fix family is not obviously "report all errors".

Possible arms (to be weighed in investigation): multi-error hard-mode reporting that preserves deterministic ordering; an authoring-time preflight checklist consolidated at the record-template section of review-staging (anti-growth priced against the already-documented clauses); validator error lines naming the owning skill rule/section so each failure routes straight to its doc.
