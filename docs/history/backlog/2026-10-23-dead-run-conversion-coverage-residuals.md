# Dead-run conversion coverage and containment residuals

- Cluster: dead-run-resume-claim-conversion
- Cluster: docs/history/backlog/completed/2026-10-25-dead-run-conversion-zcode-runtime-gap.md (runtime reachability gap: session channel + status provider unconfigured; this row owns the refusal-path test coverage)
- Cluster: docs/history/backlog/2026-10-25-manifest-scan-cause-derivation-and-primary-symlink-coverage.md (manifest-scan cause derivation + primary-side symlink coverage)
- Status: open
- Priority: normal
- Age: new (2026-10-23)

## What is owed

Execution review r1 (`.ai-playbook/reviews/2026-10-23-plan-review-dead-run-resume-claim-conversion-exec-r1.md`, fold commit 00f8b27a5) folded every blocking finding and the cheap majors; these residuals ride this row with the receiving-review disposition instead of landing unverified in the same change:

1. **Holder-state quartet** — live/ambiguous/unknown/too-young foreign done-lock holders preserving lock, claim, and manifest (Task 2 cell; the `release-orphaned` arm is implemented and untested).
2. **Mid-provider lock inspection** — both locks identifying the live gateway PID during a parked provider call; another worktree unable to reclaim them.
3. **Interrupt injection** — rename/refresh failure injection and pre/post-write interrupts (files stay complete; retries refuse owner mismatch; abrupt death leaves the lock for verified-dead recovery).
4. **Provider environment cells** — non-primary facts source refusal, relative provider path refusal, poisoned-PATH cell.
5. **Containment** — receipt/declared/evidence paths resolving inside the run tree and the plan operand normalized repository-relative before comparison and canonicalization (the current `readable()` accepts absolute paths; the fixtures enshrine scratch-absolute paths, so the check needs a fixture overhaul together with the check).
6. **Full pre-lock triage move** — the manifest identity classification runs pre-lock with a re-verification under the locks (folded); moving the whole triage prelude behind the done+merge acquire is the stricter Task 1 letter.
7. **Crash residue sweep** — `manifest.md.canonicalize.tmp` from a killed canonicalizer (the `.conversion.$$` temp claim is trap-cleaned already).
8. **Provider argv shape** — `session_status_command` extra arguments are permitted; the Terms say "sole argument" (document or reject).

## Why deferred

Each is a refusal-path or test-coverage deepening behind an already fail-closed gate; the r1 folds prioritized the blocking sematics (preservation scan, boundary binding, tuple carry-through) and the hermetic harness. Trigger: the next execution touching `scripts/execution_claim.sh` or the conversion test batch picks this row up as a unit.
9. **Boundary-token regex word boundary** — the exactly-once naming check's `[Tt]ask[=_ ]` lacks a left word boundary (`subtask=1` false-accepts; r3 minor, false-accept direction only).
10. **Boundary-shape regression cells** — the review-row-beside pass and the duplicate-naming refusal verified by an r3 live probe, not pinned as suite cells (r3 minor).
