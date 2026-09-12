# Backlog: budget gate pause protocol — keep the budget_pause manifest record on a secondary-bound pause

Status: open
Origin: review r5 CD-R5-1 (execute-plan runtime guardrails; round-cap deferral, zero blocking)
Discovered: 2026-09-12

In `agents/skills/execute-plan/SKILL.md` Budget-pause protocol step 2, the secondary-window clause says "skip to the report-for-user-decision step", which skips step 3 — the unconditional `budget_pause` manifest record. This contradicts the plan's Terms ("Budget pause: ... append a budget_pause record") and drops the audit trail for the one pause variant a user must investigate manually. Fix: reword so steps 3 (record) still runs and only the flag/scheduling steps (4-6) are skipped; align step 7. The plan is archived (docs/plans/completed/2026-09-11-execute-plan-runtime-guardrails.md) — its Terms stay historical; the SKILL wording is the fix surface.

Related deferred-by-cap notes: the archived plan's Task 1 checkbox text documents superseded pause-on-expired semantics (r4 CC-R4-1; behavior now fails open per r3) and the "never as the sole proof" grammar family (r1 CD-6 / r2 CD-R2-02; fixing the sentence requires updating the archived plan's pinned grep span). Treat this item as the disposition record for all three wording residuals.
