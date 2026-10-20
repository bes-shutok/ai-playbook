# Backlog: review-plan's round-close seal shape drifts from the seal parser's grammar

- **Filed:** 2026-10-15, witnessed during the framework-callback authoring cycle closeout
- **Status:** covered (docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md; executed and landed 2026-10-21)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Quarantine:** 2026-10-15 (machinery-internal seal contract; routes to the operator's weekly batch review)
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-plan/SKILL.md`, staging-close step's round-close seal paragraph; consuming parser `scripts/corrections_record.py` (`parse_seal`/`load_seal_entry`)
- **Cluster:** docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md (same root area, the seal contract; that row owns the validator's freshness arm, this row owns the producer skill's documented shape)

## Problem

The review-plan skill's round-close seal paragraph documents the seal as "one line carrying the round, the artifact path, the round-start commit and digest, and the round-close commit". The consuming parser accepts only a different grammar: a `## round N` header line followed by lowercase `field: value` lines, with `round_start_commit` and `round_close_commit` as full 40-hex digests and `round_start_digest` as 64-hex; any other non-empty line makes the whole file unparsable. A seal written to the skill's documented shape loads as unresolvable, and every certification over it degrades corrections grading to the exact-match digest rule behind a warn-only message while validation still reports pass.

## Expected

The producer skill's seal paragraph shows the parser's own grammar with a worked example (or the parser accepts the documented one-line shape), and a certification whose grading degraded is treated as a defect to fix before closeout, not a passing round.

## Evidence

- Witnessed 2026-10-15 twice in one session: the r3 certification of `docs/history/plans/2026-10-15-framework-callback-readability-and-review-scope.md` first wrote the one-line shape and received the degradation warning (`WARN: corrections grading degraded to the exact-match digest rule: no certification seal entry resolves for round 3`); rewriting the seal file into the section grammar with full-width commits cleared the warning on the next `validate_review_staging.py --hard` run.
- The prior plan's seal (`.ai-playbook/review-certs/post-landing-origin-ancestry-diagnostic.md`, landing ede118d18's cycle) carries the same one-line shape and degrades the same way today.
- The 2026-10-07 cluster row already documents the parser's `## round N` / `key: value` block shape from the validator side.
- Witnessed 2026-10-20 (execution closeout, this repo): a code-family certification appended to a plan artifact's seal file exposed the round key space as family-blind. Seal entry selection matches the round number alone (`load_seal_entry` has no family dimension), the review sidecar's dual-typed round field strips its letter prefix (an `r2` staging round resolves seal round 2, which in a shared file is the plan-family entry whose base fields parse without the code evidence fields), and the appended entry's `family: code` and `staging_round: r2` disambiguator fields have no parser or validator consumer. Continuing the file's numbering (`## round 3`) avoided the collision but leaves the code entry unresolvable from its own staging round, since nothing passes the file-level round; a code entry reusing the plan family's number would resolve the wrong family's entry or, duplicated, refuse the round as non-unique.

## Environment

- ai-playbook repository, validator invocation `validate_review_staging.py --hard --source-plan <plan>`, seal parser `scripts/corrections_record.py`, seal home `.ai-playbook/review-certs/<artifact-slug>.md`; the vendored runtime copies equal the repo copies.

## Fix-class no-exit analysis

- A sanctioned override is rejected because it would certify a round without a resolvable seal and would preserve the exact silent-degradation path described above.
- Removing false positives is the chosen response: the implementation will accept the parser's canonical block grammar and the strictly recognized legacy prose rows evidenced by the committed corpus, while malformed or ambiguous entries continue to refuse.
- Warning-only handling is rejected because the witnessed degraded-grade warning currently permits a passing certification without the seal evidence this row requires.

## Suspected root area

The review-plan skill's seal paragraph predates the corrections-record parser's section grammar and was never reconciled with it.

## Witness (2026-10-21 session recurrence)

During a fresh plan-certification closeout, the seal was first written in the producer prose's one-line form. The parser could not resolve it; `validate_review_staging.py --hard --source-plan` reported the exact-match digest fallback warning while still returning `OUTCOME: pass`. Rewriting the same seal as `## round 36` with the required snake_case fields cleared the warning, and both hard review validation and `plan_readiness.py` passed. This exposed a producer-instruction mismatch, not a need to remove the seal: the seal remains the anchor for graded corrections freshness. Simplify the origin by keeping one parser-backed producer example and treating degraded grading as a closeout defect, as the open plan `docs/history/plans/2026-10-20-certification-seal-landing-survival.md` already specifies. The investigation found no basis for a new validator or a broader blocking gate.
