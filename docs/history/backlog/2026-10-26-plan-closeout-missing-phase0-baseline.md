# Backlog: Recover plan closeout after its Phase 0 baseline was missed

- **Filed:** 2026-10-26, operator-directed recovery investigation
- **Status:** covered (docs/history/plans/2026-10-27-plan-closeout-missing-phase0-baseline.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed execution blocker
- **Class:** recovery-path gap
- **Driving force:** reliability + efficiency
- **Skill/step:** `agents/skills/plans/SKILL.md` Phase 0 closeout-evidence duty; `agents/skills/done/SKILL.md` Step 2 worktree migration
- **Cluster:** `docs/history/backlog/2026-10-25-closeout-skip-record-producer-residuals.md` (shared surface: plan-slug baseline selection and closeout migration; this row is a missed Phase 0 setup, not either producer residual)

## Problem

A reviewed documentation plan reached done closeout from an authoring worktree without the canonical pre-work `closeout-baseline.json`. The closeout sweep passed, then migration refused because the baseline was missing. The plan directory also has no valid capture-failure skip record, so the existing scoped-copy fallback is not selected. The worktree and branch remain available, and the done lock was released.

## Evidence

- The refusal came from `scripts/worktree_closeout_migrate.py migrate`: the expected baseline under `docs/tmp/execute-plan/done-lock-context-compaction-recovery/` was absent, and the runner refused an implicit empty baseline.
- The completed [single-start baseline plan](../plans/completed/2026-10-18-worktree-closeout-single-start-baseline.md) says missing baseline and missing valid skip evidence must refuse; it forbids late capture and preserves the existing scoped-copy fallback only when a recorded skip governs.
- The authoring setup's `Closeout-evidence establishment duty` in `agents/skills/plans/SKILL.md` already requires the baseline or a genuine capture-failure skip before any gate or plan-file write.
- The source context-compaction origin is `docs/history/backlog/2026-10-26-done-lock-context-recovery-after-compaction.md`; its issue is lost lock-witness context, distinct from missing migration-baseline evidence.

## Suggested investigation

Determine whether a fresh closeout worktree can resume the reviewed branch through the existing Phase 0 setup and baseline migration, preserving review artifacts by their recorded digests. Compare that route with stopping for operator recovery. Decide whether this is only a missed procedure or a repeatable workflow gap that needs a separate origin. Do not relax the missing-baseline refusal, create a late baseline or synthetic skip record, or alter the existing context-compaction origin without its own completion witness.

## Origin disposition question

The context-compaction origin remains open in the main checkout. Decide whether it should stay separate from this baseline incident or be narrowed to the lock-witness behavior it actually records. Do not mark it covered or remove it on the basis of this migration refusal.

## Source

Observed during plan closeout on 2026-10-26. The closeout worktree was clean at its branch tip after its rider commit; no plan landing or artifact migration completed.
