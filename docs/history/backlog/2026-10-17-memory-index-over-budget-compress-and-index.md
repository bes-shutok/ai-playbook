# Memory index over load budget: compress-and-index consolidation request

- Added: 2026-10-17
- Origin: the memory-index-audit registry lane cold-start discharge (2026-10-17 11:00 carrier fire, scheduler turn)
- Origin class: audit-lane filing, consumer-witnessed: the load-budget truncation fires in this project's own sessions (see Evidence), so the defect is seen in the consumer, not only in the auditing lane
- Status: open
- Class: fix-class (the runtime degrades gracefully, it truncates the index and warns, but no sanctioned consolidation exit exists; the default shape simplifies the flow and adds no refusal path; acceptance: the truncation warning stops firing because the index loads whole within the load budget)
- Driving force: reliability (absent do-not-redo markers are a redo risk); secondary: maintainability

## Problem statement with evidence

The per-project memory index loads every session against a roughly 200-line load budget and is truncated when over. Measured 2026-10-17 11:1x local by the memory-index-audit lane (first completed run, cold start):

- Index: 2877 physical lines, 93294 bytes, against the ~200-line load budget (about 14x over).
- The runtime truncation is witnessed in-session every time the index loads: the loaded context carries the warning that only part of the index was loaded, so recorded state, including do-not-redo markers, can be absent from context. That absence is a redo risk: a lane may repeat work a marker already closed.
- Pointers: 346 pointer lines, 6 dangling (targets missing from the store): loop-parent-missing-20261010.md, memory/csw-ttl-exec-landed.md (stray directory prefix), done-closeout-rearm-mirror-fixed-20261011.md, exec-nonstop-0130-cycle1-landed-a00267d55.md, exec-nonstop-0130-cycle2-landed-8b873f8de.md, pced-plan-landed-20261016.md.
- Store: 1024 topic files beside the index; only 301 are pointed to by the index; 723 unindexed. A bounded classification sample (first 24 sorted unindexed) found none carrying frontmatter type markers; name signals suggest a predominantly conversation-scoped lane-state population, with durable gotcha-style notes mixed in.

Store locator (tilde form, per the audit task's recording rule): `~/.zcode/cli/memories/projects/<project-key>/memory/MEMORY.md` beside its topic files; the project key resolves per session and is not reproduced here.

## Exact location

The index file and its topic-file store named above; the audit's measured values and classification progress are in the lane's state record `.ai-playbook/maintenance/memory-index-audit.json` (untracked maintenance home).

## Suggested fix (options; operator decision required)

The audit lane never rewrites the index and never bulk-deletes topic files; the one-time consolidation below is the lane's recorded remediation request and runs ad hoc only, per the operator's recorded rescope. This row requests it; it does not self-authorize it.

1. Compress-and-index pass (the lane's named remediation): fold conversation-scoped lane-state notes (landing receipts, fire schedules, checkpoint notes whose outcomes are already recorded in the repo's scheduler state file and git history) into fewer topic files or retire them after a reviewed prune; index the durable remainder with one-line pointers per the append-first convention; repair the 6 dangling pointers beside their provenance.
2. Keep everything and only repair dangling pointers: rejected as insufficient by the audit's arithmetic, the index stays 14x over budget and the truncation, with its redo risk, persists.
3. Mechanical auto-prune by age: rejected, bulk deletion risks live do-not-redo markers the lanes still depend on; the audit procedure forbids it.

## Why not fixed now

The discharge turn is a bounded carrier scheduler turn with two same-second peer sessions live on the shared checkout; the consolidation is an operator-rescoped ad-hoc pass that needs a lane-quiet window and its own review, not a mid-lane edit. The audit lane's filing rule routes the finding here instead of rewriting the index.

## Lane-quiet window

The requested pass should run in a window with no live authoring or execution claims under the tmp authoring-claims directory and no in-flight worktree closeouts; at filing time the claims home holds only stale pre-2026-10-14 vintage plus one operator-session claim, and the two 2026-10-17 11:00 peer fires were still live, so the next carrier-fire boundary after the peers drain is the earliest candidate.

## Dedup probe

Keywords run over the open backlog corpus (filenames and problem bodies): memory index, MEMORY.md, load budget, compress and index. Nearest hits: 2026-10-10-quota-wall-stop-account-mismatch.md (quota accounting, not the memory index), 2026-10-08-plan-simplicity-challenge.md (unrelated), deferred/2026-10-08-investigate-renewal-trigger-on-row-rescope.md (unrelated). No open row owns the memory index over-budget defect; this row is the first filing from the lane's first completed run.

## Source reference

Registry task docs/maintenance/recurring-tasks/memory-index-audit.md; state record .ai-playbook/maintenance/memory-index-audit.json (measured values, dangling list, classification progress, next_due 2026-10-24).
