- Status: open
Priority: medium
Urgency remark: origin of the promoted deferred plan 2026-09-09-grilling-fork-answer-state-rules; protects the deliberate local grilling forks from an upstream-sync wipe
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)

- Workflow: backlog
- Priority: Low
- Created: 2026-09-09

# Grilling-family local fork of upstream-vendored skills

`agents/skills/grilling/` and `agents/skills/grill-with-docs/` are vendored skills (`metadata.upstream`) that now carry a deliberate local fork: the answer-state rule (per-question `open`/`closed` state), the exact opt-in phrase ("accept the recommendation for this question"), the per-question decision receipts (decision, source, date, affected plan section), the question-economy and consolidated-assumptions-list rule, and the bidirectional sync notes with the `plans` skill's Step 1.4 meta-rule.

A future upstream `rsync --delete` sync of these skills must re-apply these rules or consciously drop them; this item exists so the fork is visible and the sync cannot silently erase it.

Origin: `docs/plans/2026-09-08-plans-grill-answer-state-machine.md` Task 6 (Design Invariant: the two skills are vendored; the plan deepens the local fork).
