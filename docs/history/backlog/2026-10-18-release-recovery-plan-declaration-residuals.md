# Backlog: release recovery plan declaration residuals (r3 certification, non-blocking)

- **Filed:** 2026-10-18
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review residual (certification round, non-blocking, durable capture)
- **Class:** docs consistency
- **Skill/step:** `docs/history/plans/2026-10-18-release-merge-history-recovery.md` (Gate delta line; Task 1 RED checkpoint item)

## Problem

The r3 certification round (ready=yes, zero blocking) staged two Low non-blocking residuals whose fixes are wording-level and ride the certified plan's next natural edit:

1. The Gate delta line's removes-nothing clause names only the divergence refusal as mode-conditioned; the Tasks (and the r2 fold) also mode-condition the ordinary merge scan, so the declaration ledger under-declares by one refusal class.
2. Task 1's RED checkpoint bullet claims every recovery case fails at RED; the Usage-refusals case is already green against the script's existing argv FATAL (the case's expected refusal is that FATAL), so the executor should expect one green case among the recovery cases at that checkpoint.

## Expected

At the next natural edit of the certified plan (or as an authoring-lane follow-up before execution): extend the Gate delta clause to name both mode-conditioned refusals, and reword the RED bullet to state the expected RED-state split (usage-refusals case green, all other recovery cases red).

## Evidence

- r3 record: worktree reviews home `.ai-playbook/reviews/2026-10-18-plan-review-release-merge-history-recovery-pafcf0d49-r3.md` (findings F1 `quality#gate-delta-mode-conditioning-stale`, F2 `testing#red-checkpoint-overstates-case-colors`, both Low, blocking false).
- Certification seal: `.ai-playbook/review-certs/release-merge-history-recovery.md`.
