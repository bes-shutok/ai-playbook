# Backlog: the per-project memory index runs 2.25x over its load budget; operator decision requested on compress-and-index consolidation

- **Filed:** 2026-10-31, memory-index-audit lane run 1 (recurring task, cadence 7 days)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** audit-lane finding (self-serving evidence caveat: the witnessed truncation was seen in a consumer of this project's memory store - the maintenance scheduler sessions this repo runs - so the lane files it rather than silently treating it as its own)
- **Class:** maintainability
- **Skill/step:** the per-project memory store `~/.zcode/cli/memories/projects/ai-playbook-a1cd2d2260fa7300/memory/` (MEMORY.md index beside its topic files); measured and reported by the memory-index-audit lane, state record `.ai-playbook/maintenance/memory-index-audit.json`

## Problem

The index measures 450 physical lines against the roughly 200-line load budget the session runtime loads per context (2.25x), and the runtime truncates: the 2026-10-31 dispatching scheduler session loaded only 111 of 450 lines (its own truncation notice cut the index at line 112), so recorded state - do-not-redo markers included - is silently absent from context. That is a redo risk, not noise: a session whose index tail never loads can re-execute a landed plan or re-file a filed row. Store shape: 1326 topic files, 346 indexed (26.1 percent), 449 index pointers with zero dangling, 980 unindexed topic files. The unindexed corpus is dominated by type=project run-completion records carrying do-not-redo markers (durable by the index-rather-than-prune rule) whose current state is however already carried by newer index entries and by the repository's own durable records (archived plans, git history, scheduler state file) - time-supersession, not a classification dichotomy violation.

Pointer integrity is clean; the finding is the load budget and the indexed fraction, not link rot.

## Expected

Every session loads the whole index within the ~200-line budget, so every do-not-redo marker and standing preference the store holds is actually present in context; superseded run records stop accumulating as unindexed topic-file growth.

## Operator decision requested

The lane cannot fix this itself: it never rewrites the index mid-lane, never bulk-deletes topic files, and never deletes a topic file whose live do-not-redo marker a lane still depends on. The one-time consolidation is operator-gated per the lane's charter (the operator's recorded rescope runs it ad hoc only):

1. Compress and index: fold the durable signal of time-superseded run records into a small set of current index entries (per-run outcome lines retire into per-mandate summary lines), add one-line pointers for durable still-current records, staying within the ~200-line budget.
2. Then a reviewed prune of topic files whose entire durable signal is captured by the compressed index and the repository's own durable records - reviewed, never bulk.
3. A standing write discipline so the store does not regrow past the budget (the one-line-entry convention already exists; the missing half is a retirement rule for superseded entries).

In doubt stays index-recommendation; nothing is deleted in doubt.

## Lane-quiet window

A window with no live authoring or execution claims under the memory/tmp directories: the consolidation touches only the user-level memory store, so any scheduler-turn gap with zero in-flight children qualifies; the next such gap after operator approval.

## Evidence

- State record `.ai-playbook/maintenance/memory-index-audit.json` (run 1, 2026-10-31): 450 lines measured; 111-of-450 loaded witnessed in the dispatching session's runtime context; 449 pointers, 0 dangling; 1326 topic files, 26.1 percent indexed.
- Spot-read classification of a 60-name sorted prefix (6.1 percent covered; remainder drains across runs under the recorded 30000-token budget): durable 60, conversation-scoped 0.
