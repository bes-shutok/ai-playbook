# Backlog: a done-lock hold was treated as a blanket veto on an unrelated commit

- **Filed:** 2026-10-30, operator-directed investigation after a diagnostics-ledger commit was deferred
- **Status:** open
- **Workflow:** backlog
- **Priority:** low (one small record was delayed and then committed; no loss or demonstrated concurrent-write hazard)
- **Origin class:** session-witnessed workflow friction
- **Class:** commit-continuity / lock-scope
- **Driving force:** simplicity (primary), efficiency (secondary)
- **Skill/step:** `agents/skills/done/SKILL.md` Step 0 and `docs/history/backlog/PLAN-PROMPTS.md` `Write boundary rule`
- **Source:** operator direction following the deferred commit of the certification-seal diagnostics receipt in this session
- **Dedup probe:** the completed `docs/history/plans/completed/2026-10-24-done-run-lock-span-and-append-ordering.md` owns the runner's lock spans, terminal-stop release, and primary rolling-log transaction; completed `docs/history/plans/completed/2026-10-26-done-lock-context-compaction-recovery.md` owns continuation after context compaction; open `docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md` owns generation binding for `--from-holder` release. None decides whether a standalone non-log history-record commit is subject to those lock boundaries.

## Problem

The primary checkout's `docs/history/certification-seal-landing-diagnostics.md` had a two-line receipt addition ready to commit. I deferred its commit because another run held the primary done lock, without first establishing that this standalone history-record commit used a lock-protected shared-state path. A later status showed the holder dead and the lock was recovered, after which the receipt landed as `4a8b4a22`; the earlier holder state and the exact time it died are not established here.

The controls have different jobs: `DONE_LOCK_AGENT_MAX_WAIT_SECS` defaults to 90 seconds in `scripts/done_run.sh`; `DONE_LOCK_DEAD_HOLDER_GRACE_SECS` defaults to 5 seconds and verified-dead holders are automatically reclaimable on acquire; `DONE_LOCK_STALE_SECS` defaults to 1800 seconds and governs the explicit `stale-clean` path for locks that are not verified dead. The incident therefore does not establish that the 30-minute stale threshold caused the delay. The demonstrated failure was treating a done-lock hold as a universal commit prohibition before checking whether the write was covered by the lock boundary.

## Expected

Commit procedures identify the actual protected write surface before standing down. A held done lock continues to serialize the primary rolling prompt-log transaction and any other explicitly lock-bound path; it does not by itself veto an unrelated, path-scoped commit. When a lock is required, the caller uses the existing verified-dead auto-recovery and bounded wait semantics, and reports a live or ambiguous hold accurately.

## Investigation question

Determine whether a narrow workflow clarification is sufficient to prevent blanket commit deferrals, and whether any measured recovery delay justifies changing the dead-holder grace or stale-clean threshold. Do not lower stale-clean's threshold as a proxy for dead-holder recovery: that threshold also governs the explicit escape for a live, session-fenced lock, where premature cleanup could overlap an active writer.
