# Backlog: finish the shared docs-branch witness contract

- **Filed:** 2026-10-09, execute-plan code review r6
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consuming projects that run the shared docs-branch skill need the generic witness contract and its failure-path test; the skills-repo personal priority profile must not defer this as formal-hardening for this repository alone.
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** docs + testability
- **Severity:** low; current runner preserves a failed witness commit, but the public contract remains over-specific and the recovery arm lacks a regression witness.
- **Source:** `docs/history/reviews/2026-10-09-docs-branch-scope-and-tmp-retention-code-review-r6.md`, findings F1 and F2; capture hygiene: scan-public-hygiene --files pass.
Cluster: docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md (same surface: the docs-branch skill and its runner tests)

## Problem

The canonical witness append now accepts a caller-supplied `lesson-scope-audit:` line and preserves a witness commit under a recovery ref when compare-and-swap loses a race. Two small gaps remain: the shared skill still calls one organization-specific sentence canonical, and the new runner has no test that interposes a competing docs-ref update and checks the recovery ref.

## Evidence and location

- `agents/skills/docs-branch/SKILL.md`, Step 3 witness contract: the caller's exact line is the API input, while a hardcoded example names one organization's audit configuration.
- `scripts/docs_branch_sync.sh`, `append_witness`: compare-and-swap failure creates `refs/docs-witness-recovery/<timestamp>-<pid>`.
- `scripts/test_docs_branch_sync.py`: direct publication and symbolic-ref refusal are covered, but a competing-tip interposition does not verify the recovery ref or preserve the competing tip.
- The R6 full panel found no unresolved blocking findings. These are low-severity contract portability and failure-path coverage improvements, not a reason to reopen the fixed direct-ref blocker family.

## Expected

Keep the shared skill's witness contract organization-neutral and document only the caller-supplied prefix and exact-line behavior. Add a deterministic test that moves the docs tip after the witness snapshot, then asserts the append refuses to overwrite the competing tip and preserves a recovery ref whose commit contains the witness line.

## Why not fixed now

The current implementation is safe on the reviewed paths and the remaining findings are nonblocking. They are grouped here as one bounded witness-contract follow-up so Phase 3 can close without another cycle for low-severity residuals.

## Dedup probe

Searched backlog filenames and Problem sections for witness append, docs-ref compare-and-swap, recovery refs, and witness portability. The nearest item is `docs/history/backlog/rejected/2026-09-18-witness-append-refusal-branch-test-coverage.md`, which records refusal branches for the retired shell helper and was explicitly closed for that implementation. This item covers the new canonical runner's CAS-recovery branch and the remaining shared-skill contract wording; it is not a duplicate.

## Suggested direction

Keep caller ownership of witness text in the skill and add one test seam that changes `refs/heads/docs` between snapshot and CAS. Verify the active tip is unchanged and the recovery ref is directly addressable and contains the witness.
