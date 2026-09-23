# Backlog: review-staging Integration Points row accuracy (record_kind twin + helper note)

Status: done 2026-09-23 (fixed by docs/plans/completed/2026-09-22-review-staging-infra-quality.md; executed plan Task 6: Integration Points rows verified narrowed in agents/skills/review-staging/SKILL.md)
Severity: Low
Origin: r4 code-review round of the review-records-contract execution (2026-09-19), staged findings F3 and F4 (contract-docs, design-simplicity); staging doc `docs/reviews/2026-09-16-review-records-contract-code-review-r4.md` (gitignored); capture hygiene: scan-public-hygiene --files pass (2026-09-19)

## Problem

In the `agents/skills/review-staging/SKILL.md` Integration Points consumer table (lines ~492-500): (a) the r3 narrowing was applied only to the rfc-design row; the review-confluence-doc and review-reconciliation rows still say "sidecar field + Metadata `Record kind:` twin" while neither producer's own bytes produce the twin, so a verbatim producer record fails its twin gate once post-fence before recovering via review-staging; (b) the execute-plan Phase 3 row asserts the selection-helper run while no execute-plan byte wires it (Task 3 scoped helper prose to doing-code-review and review-loop), and the doing-code-review row whose bytes DO require the helper carries no note.

## Fix shape

One reviewed prose pass applying the r3 narrowing principle uniformly: producer rows state the sidecar field and attribute the Metadata twin to the universal review-staging template; orchestrator rows state the helper requirement only where the consumer's own bytes mandate it.

## Trigger

The next Integration Points table edit, or the first producer-side gate friction reported from a verbatim record.
