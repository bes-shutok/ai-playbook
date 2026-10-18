# Backlog: fprv certification residuals (escaped-quote today-mechanism gloss; scalar-invalid selftest input; two narrative loosening spans)

- **Filed:** 2026-10-17, certification-residual capture from the fprv plan review (series .ai-playbook/reviews/2026-10-17-plan-review-facts-path-resolver-valid-toml-strings-p5e88a2e8-r*.md, r3 certified ready=yes zero blocking)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** certification-residual overflow (four non-blocking Low findings routed to overflow with durable capture per the certification-residual routing)
- **Class:** fix-class
- **Cluster:** docs/history/plans/2026-10-17-facts-path-resolver-valid-toml-strings.md (the certified plan; its landing serves the parent origin)

## Residuals

1. Execution-relevant: Task 2's refusal-loop enumeration omits the scalar-invalid escape input (`"\U00110000"`), so the crash-class regression arm is absent from the selftest even though Task 1's prose witness covers it; the executor should include the scalar-invalid input in the combined refusal check.
2. Narrative: the escaped-quote input's today-mechanism is described as truncation in Task 2 and two further spans; measured, the end anchor fails the whole match and the line resolves as absent today (the RED is real; the cause is absence). Terms' "exactly as today" is false for the recorded flip class.

## Source

- The r3 certification round of the facts-path-resolver-valid-toml-strings plan review, 2026-10-17 (overflow manifest rows, folded: false).
