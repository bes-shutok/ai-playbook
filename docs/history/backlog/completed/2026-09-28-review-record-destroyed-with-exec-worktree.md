# Exec worktree teardown destroys the review record stored in gitignored docs

Captured: 2026-09-28 (source: release-skill-follow-ups execution session, done closeout)
- **Status:** done (2026-09-30; residual third expectation executed via docs/history/plans/completed/2026-09-30-done-step0-review-record-reconstruction-duty.md, exec review r1 ready=yes; first two expectations previously implemented)
Priority: high
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: self-serving
Consumer urgency: Review records are audit artifacts consumed by later review-reconciliation and certification passes; losing one forces byte-equivalent reconstruction from memory and undermines the review trail for every worktree-first execution.

## Problem

The worktree-first execution pattern keeps code review records under `docs/reviews/`, which is gitignored. The review ran inside the execution worktree against the working-tree diff. At closeout, the worktree was removed and with it the only copy of the review record; the done closeout had to recreate the record in the main checkout by hand, after the fact, with no source artifact to verify against.

This happened during the release-skill-follow-ups execution (main dac7fcc1): the r1/r2 record at `docs/reviews/2026-09-28-release-skill-follow-ups-code-review-r2.md` was destroyed with `ai-playbook-exec-release-followups` and recreated in the main checkout during done Step 0.

## Exact location

`agents/skills/execute-plan/SKILL.md` worktree teardown step (review-record migration before removal), and the worktree-first execution payload description; also `agents/skills/done/SKILL.md` Step 0, which currently has no expectation that a review record may need recreation.

## Expected

- Before worktree removal, every gitignored artifact this run produced (review records, sidecars, stats files) is migrated to the main checkout or explicitly verified as already present there.
- Teardown verifies presence by digest, not by memory: the migrated record must byte-match the worktree copy.
- If teardown has already happened and a review record is missing, done Step 0 flags it as a reconstruction duty with a witness note rather than silently proceeding.

## Severity and source reference

Severity: medium-high

Source: release-skill-follow-ups execution closeout, 2026-09-28; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The session was executing the release-skill follow-ups plan and running its done closeout, not amending the execute-plan or done skills. The defect is recorded for a dedicated skill fix.

## Dedup probe

Search terms: `review record worktree`, `gitignored docs migration`, `teardown review record`. No open item covers destruction of gitignored review artifacts at worktree removal; the stale-worktree teardown audit memory records teardowns but not artifact loss.

## Suggested fix

Add an explicit pre-teardown migration step to the execute-plan worktree pattern: enumerate gitignored docs paths the run created, copy them to the main checkout, verify byte equality, then remove the worktree. Add a done Step 0 recovery arm that detects a missing review record for a landed plan and requires a witnessed reconstruction note.
