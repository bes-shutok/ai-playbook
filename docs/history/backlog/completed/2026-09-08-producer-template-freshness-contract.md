# Backlog: producer-template freshness contract residuals (round-5 residual family)

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Origin: execute-plan fresh-review-coverage-gaps Phase 3 review round 5 (fresh adversarial full panel over digest d9143e94; findings deferred at the five-round cap per the backlog-deferral default)

## Items

1. The rfc-design and review-confluence-doc inlined staging Metadata templates omit the four freshness lines and the two ledger declaration lines; every post-fence staging doc built from those templates fails the skills' own mandated hard validator gate with named missing-line errors (replay-verified). Add the six Metadata lines mirroring the review-plan template update.
2. The doing-code-review and review-loop validator-refresh guidance quotes `undocumented top-level field`, but the validator emits `rejects unknown top-level field`; reword to the emitted text or drop the backticks.
3. The mirrored date-disagreement fence (pre-fence filename with post-fence sidecar date) is enforced but undocumented in review-staging; add one sentence stating the validator rejects either mixed-fence direction.

Non-goals: no validator behavior changes; items 1 and 3 are template/prose alignment, item 2 is an error-phrase correction.
