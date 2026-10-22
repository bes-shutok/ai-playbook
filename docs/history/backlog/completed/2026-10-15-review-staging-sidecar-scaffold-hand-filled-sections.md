# Backlog: review-staging sidecar scaffold or schema reference for the hand-filled sections

- **Filed:** 2026-10-15, learn closeout (skill-usage issue capture, done Step 1)
- **Status:** covered (docs/history/plans/completed/2026-10-19-review-staging-schema-scaffold-and-validation-reuse.md)
- **Workflow:** review-staging skill-text and validator tooling
- **Priority:** high
- **Origin class:** skill-usage issue (validator discoverability; project lesson 30, second witness)
- **Class:** fix-class (small tooling or reference-doc change)
- **Dedup:** probed the counts-parity row (closed family, covered by the 2026-10-16 counts-parity landing), `2026-10-08-review-staging-ancestor-validation-cache.md` (cache staleness), and the soft-mode outcome row (covered by the same landing); no open row covers schema discoverability for the hand-filled sections.
- **Skill/step:** `agents/skills/review-staging/SKILL.md` (record assembly steps); `scripts/validate_review_staging.py` (payload schema)
- **Witness:** the 2026-10-13 machinery-script-refactor-program and 2026-10-14 review-staging-series-wide-round-close-scope authoring cycles (reviews r1-r5 and r1-r3 under the gitignored reviews home); each cycle lost multiple preflight passes to schema rejections in hand-filled sections despite tool-minted usage records.
- **Cluster:** docs/history/backlog/2026-10-08-review-staging-ancestor-validation-cache.md

## Problem

The staging validator's schema surface is discoverable only through refusal messages. The tool-minted halves of a sidecar (the usage capture pair) validate, but the hand-filled sections (coverage outcome and its flat lens list, panel rows with their per-row launch field, triage outcomes, deduplication groups, extensions blocks, the soften table's anchored header, inherited-coverage rows on a yes verdict, empty-array edges that must drop the key entirely) each carry couplings that cost a preflight round per mismatch, and the same classes recurred across two cycles one day apart.

## Expected

An authoring session assembling a sidecar can satisfy the hand-filled sections' couplings in one draft, either by generating a filled skeleton from the validator (a scaffold mode emitting every required key with its shape) or by a schema reference section in the review-staging skill enumerating the couplings lesson 30's rule points at.

## Suggested direction

Prefer the validator-side scaffold (the schema's own tooling per lesson 30; a read-only emit keeps the validator warning-only posture and needs no admission test). Fallback: a reference section in the review-staging skill, paid for under the anti-growth rules with the coupling enumeration replacing itself at the next validator change.

## Rejected alternatives

- **Capture the field list as a project lesson:** rejected because the enumeration duplicates the validator as a second source of truth that drifts on every schema change; the pointer (lesson 30) plus tooling is the durable shape.
- **Leave it to refusal-message iteration:** rejected by the second witness; two cycles re-derived the same couplings at real round cost.
