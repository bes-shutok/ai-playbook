# Backlog: review-plan's round-close seal shape drifts from the seal parser's grammar

- **Filed:** 2026-10-15, witnessed during the framework-callback authoring cycle closeout
- **Status:** open
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

## Suspected root area

The review-plan skill's seal paragraph predates the corrections-record parser's section grammar and was never reconciled with it.
