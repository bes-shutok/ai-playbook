# Backlog: memory-index lane-file and overlay review residue from the consolidation-plan execution (six non-blocking findings)

Status: open
Priority: medium
Class: fix-class
Driving force: maintainability
Added: 2026-11-05, memory-index-load-budget-consolidation execution run (review r3 certifying-round residue, recorded not fixed so the landing stayed the certified bytes)
Capture hygiene: `scan-public-hygiene.sh` pass.
Cluster: docs/history/plans/completed/2026-11-02-memory-index-load-budget-consolidation.md (the execution whose certifying round staged these; the review record series lives session-local under `.ai-playbook/reviews/2026-11-05-memory-index-load-budget-consolidation-code-review-r3.md`)
Cluster: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md (same surface family; that row owns the index content lifecycle, retirement and fired-record refresh; this row owns the charter file's paperkeeping residue list)
Origin class: self-serving

## Problem

The execution's certifying code-review round (r3, verdict yes zero blocking, all three workers certifying) staged six non-blocking findings as recorded residue. None blocks the landed charter; each is a real small defect worth one consolidated pass on the two surfaces this execution owned.

1. (Medium) `documentation#report-enumeration-omits-primary-proxy` - `docs/maintenance/recurring-tasks/memory-index-audit.md:19`: the measured-values enumeration still reports line count only while the amended Load budget bullet makes byte the primary proxy, so lane runs never record the index byte count in state records. Fix: extend the enumeration to byte count first, and record the whole-load witness outcome.
2. `consistency#duplicate-gloss` (3-worker dedup) - `agents/skills/maintenance/zcode.md:110` vs `:118`: the bulk gloss survives at both the exception parenthetical and the terms paragraph; drop the parenthetical copy ("...are sanctioned targeted edits), while...") and optionally scope the line-118 fuller-definitions pointer to the plan coinages.
3. `consistency#pointer-taxonomy` - `docs/maintenance/recurring-tasks/memory-index-audit.md:35`: the in-file definitions group includes the retirement rule, whose definition is out-of-file; close the group at Classify and cite the retirement rule's home separately.
4. `architecture#standing-rule-depends-on-transient-machinery` - `docs/maintenance/recurring-tasks/memory-index-audit.md:31`: the Filing rule's lane-quiet window presumes a run claim file whose only acquisition mechanism lives in the one-time charter section; generalize the clause ("a run claim file beside the lane state record (per the Run claim member's shape)").
5. `consistency#abridged-handler-list` - `docs/maintenance/recurring-tasks/memory-index-audit.md:31` vs `:37`: the Filing rule's unobservable-writer clause omits "and the post-write verification" from the operative member's handling list; complete it.
6. `simplification#one-time-procedure-in-standing-home` - `docs/maintenance/recurring-tasks/memory-index-audit.md:33-51`: the operator-approved charter section has no post-run disposition arm; add the one-liner folding the section into the archived charter record once a lane re-measurement reads within budget.
7. `architecture#discovery-routing-gap` (Step 1.4b design review ARCH-5, appended at closeout) - `agents/skills/plans/template-execution.md`: the note-write duties carry no pointer to the memory-write convention home or the retirement rule; add the one-line pointer.

## Exact location

- `docs/maintenance/recurring-tasks/memory-index-audit.md` (items 1, 3, 4, 5, 6)
- `agents/skills/maintenance/zcode.md` (item 2; byte cap 116,647, at 114,864 as of the landing - the fix is byte-negative)

## Suggested direction

One two-file paperkeeping pass applying the six concrete fixes above verbatim from the r3 workers' suggested wording; no design choices open. The overlay edit is byte-negative; the lane file has no cap entry.

## Evidence

- Review record: `.ai-playbook/reviews/2026-11-05-memory-index-load-budget-consolidation-code-review-r3.md` (session-local; verdict yes, zero blocking, residue triaged backlogged by the run's exit)
- Landing: `0a3fa6aa1` (2026-11-05; the certified bytes these findings were staged over)
