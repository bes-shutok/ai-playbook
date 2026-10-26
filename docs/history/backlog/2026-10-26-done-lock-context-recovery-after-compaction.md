# Backlog: Preserve a safe continuation path when done-lock context is compacted

- **Filed:** 2026-10-26
- **Status:** covered (docs/history/plans/2026-10-26-done-lock-context-compaction-recovery.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** `docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md`
- **Skill/step:** `agents/skills/done/SKILL.md` Steps 0 and 6; `scripts/done_run.sh` finalize
- **Class:** recovery-path gap
- **Origin class:** witnessed continuation stop
- **Driving force:** efficiency + correctness

## Problem

The done recovery instructions require retaining the original Step 0 token and lock witness in session context and correctly refuse recovery when either is unavailable. After context compaction, this session could no longer recover the original setup output or witness. The live authoring worktree's lock remains held by a process that is still alive, so tokenless recovery would risk releasing a different lock generation. This safe refusal also stopped work in that worktree even though the authorized documentation investigation could continue in the main checkout under its separate lock.

## Evidence

Observed on 2026-10-26 while resuming an authoring worktree: the manifest records a partial run, the worktree lock reports a live holder, and the current session has no original Step 0 exports or setup witness. The completed recovery plan explicitly says a fresh metadata read or run manifest cannot establish generation ownership and requires stopping when the original token or witness is unavailable (`docs/history/plans/completed/2026-10-18-done-live-owner-closeout-recovery.md`). A separate open item already tracks the replacement-generation risk in `done_run.sh finalize --from-holder` (`docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md`).

## Suggested fix

Decide whether a secret-free continuation handoff can preserve the existing generation-bound recovery across context compaction without persisting the raw lock token. Prefer using existing session or process continuity; keep the current refusal if no safe handoff exists. Document the separate-checkout continuation as a workaround for unrelated authorized work, leaving the original live lock and worktree untouched. Do not add a new lock, gate, validator, ledger, or recovery ceremony as part of this item.

## Why not fixed now

The current request authorizes investigation and a safe workaround, not a change to lock ownership or the secret-handling contract. Continuing the requested backlog work in the main checkout under its own lock avoids changing or releasing the live worktree lock.

## Dedup probe

The completed `done-run-resume-ownership-gap` plan fixes setup adoption of new manifest ownership claims; it does not recover a lost lock token. The completed `done-live-owner-closeout-recovery` plan covers re-export only while the original token and witness remain available. The open from-holder generation-binding row covers replacement-generation release safety, not context compaction. Cluster this row with that open item for a single investigation of the shared lock-recovery surface while preserving their distinct defects.

## Source

Observed during a resumed authoring session after context compaction. The current checkout's done lock was free, while the authoring worktree's lock remained held and its recorded holder was alive. No raw token, user-specific path, or process identifier is recorded here.
