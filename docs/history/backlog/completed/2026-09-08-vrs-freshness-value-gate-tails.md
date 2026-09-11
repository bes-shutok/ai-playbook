# Backlog: validator freshness value-gate tails (round-5 residual family)

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Origin: execute-plan fresh-review-coverage-gaps Phase 3 review round 5 (fresh adversarial full panel over digest d9143e94; findings deferred at the five-round cap per the backlog-deferral default)

## Items

1. Empty-valued `Review mode:` Metadata line satisfies the date-keyed presence gate while disarming every mode value gate (enum, verification-only contradiction, fresh-adversarial twin): treat a gated freshness label whose value side is empty as a named error, or fire the fresh-adversarial twin whenever `Last fix commit` is present with a clean verdict and the mode did not parse to a valid enum value. Add a failing canary for the empty-mode shape.
2. Spelled-out zero verdict line (`No Medium+ findings; clear round.`) is not recognized as clean, disarming all clean-keyed freshness gates: add a named warning or error when the canonical verdict section contains a clear-round phrase without a recognizable clean-round match, with canary pair.
3. The `no-freshness-lines-before` grandfathering canary stages the freshness lines by default and does not exercise the stripped pre-fence shape it claims to pin: restage it stripped (or delete it in favor of the pre-fence-agreeing twin) and fix the comment.
4. The best-effort sidecar date read catches only `(OSError, json.JSONDecodeError)`; a non-UTF-8 sidecar raises an uncaught `UnicodeDecodeError` traceback instead of a named validation error: extend the except tuple (and optionally the two pre-existing unguarded reads).

Non-goals: none; each item is independent and canary-backed when implemented.
