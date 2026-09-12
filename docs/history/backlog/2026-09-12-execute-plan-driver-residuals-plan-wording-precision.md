# Backlog: execute-plan driver residuals plan wording precision (r2 Lows)

Status: open
Workflow: backlog
Source: docs/reviews/2026-09-12-plan-review-execute-plan-driver-residuals-r2.md (ready=yes, zero blocking; both findings Low, non-blocking)
Severity: Low (plan-text precision only; the plan is executable as certified)

## Problem

Two wording-precision Lows on `docs/plans/2026-09-12-execute-plan-driver-residuals.md` (digest de13d9d2), left unfixed at the r2 exit because they regenerate on sentences earlier folds touched (the r1 fold edited Assumption 3 and the adjacent Ship-when bullet; r2 flagged another clause of each). Regenerating prose class, ADR-0002 default: backlog capture instead of a third edit plus r3.

1. **F1 (contract-docs, Low)**: Assumption 3's parenthetical "(archived and completed plan bodies are immutable)" cites archive-immutability for `docs/plans/2026-09-10-execute-plan-runtime-residuals.md`, which is still in-flight under `docs/plans/` today; the Review Scope freeze is the operative pre-archive protection, and the Task 1 sequencing gate guarantees the archived state at execution time.
2. **F2 (correctness-completeness, Low)**: Ship-when bullet 1 says the sequencing gate "proves" the prior executions landed; the gate proves repository-verifiable archive placement (file predicates), the lifecycle proxy.

## Suggested fix

Fold at the next plan update (for example immediately before execution, alongside the Task 1 drift re-derivation): reword the Assumption 3 parenthetical to name the Review Scope freeze as the pre-archive protection and the sequencing gate as the archive guarantee; reword "proves" to "verifies repository-verifiable archive placement". Either edit changes the digest and requires a fresh certification round.

## Why not fixed now

Exit condition was already met at r2 (fresh blind-inclusive round on the post-fold digest, ready=yes, zero blocking); a third edit of the same sentences risked manufacturing the next round's findings (the r9-r14 non-convergence family; reconciliation record 2026-09-11).

## r3 additions (same class, same disposition)

The mechanical Files-block fix (readiness gate: bare `none` Files entries) changed the digest and required round r3 (blind correctness-completeness exit probe; ready=yes, zero blocking, digest 1ac5bef8). r3 added two non-blocking Lows of the same regenerating wording class:

3. **F1 (r3, Low)**: Task 1's dissolved-machinery probes reference the `expect_absent` helper defined only inside the Validation Commands block; a fresh probe shell hits command-not-found (rc 127 still fails closed, so probe friction only). Fix: inline the rc-split helper at first Task 1 use or move the helper definition above both blocks.
4. **F2 (r3, Low)**: Task 2's "delete the re-inlined status invocation and its parse loop" could be misread as dropping the untracked-union loop; the "keep the sorted-union return" clause and the two RED/GREEN tests bound the exposure. Fix: name the deleted span precisely (the status `subprocess.run` call plus its inline `for ... in self._parse_porcelain_z(status.stdout)` loop).

Fold all four at the next plan update (for example immediately before execution, alongside the Task 1 drift re-derivation); each edit changes the digest and requires a fresh certification round.

