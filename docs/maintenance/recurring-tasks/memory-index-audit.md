```toml
id = "memory-index-audit"
cadence_days = 7
kind = "audit"
```

# Recurring task: memory-index-audit lane

You are running the `recurring task memory-index-audit lane` in the repository at <REPO_ROOT> (the resolved repository root; this body runs verbatim in a fresh session with only that root). The registry consult owns this task's due-read and dispatch; this file is the run's procedure of record. The lane gives the per-project memory index a periodic reader: it measures, checks, classifies, and reports through its state record and the filing rule - it never rewrites the index.

## Store locator

The measured store is the per-project memory directory the executing session's own runtime context names beside its loaded `MEMORY.md` index (the runtime derives the per-project path; for this repository it resolves under the user-level store, recorded in tilde form, never an absolute path in committed files or reports). The audit measures that directory's store: the `MEMORY.md` index file beside its topic files.

## Measure and check

- Load budget: count the index's physical lines against the roughly 200-line load budget the runtime loads per session; beyond it the runtime truncates the index and recorded state (do-not-redo markers included) can be absent from context, which is a redo risk, not noise.
- Pointer integrity: an index pointer is any line carrying a Markdown link whose target ends in `.md`, wherever the link sits in the line (the shape covers legacy multi-line blob entries too); a pointer resolves when the target topic file exists relative to `MEMORY.md`'s own directory, subdirectory targets resolving along their relative path. Report every dangling pointer in the state record.
- Report the measured values (line count, pointer count, dangling pointers, topic-file count, indexed fraction) in the state record.

## Classify

Classify unindexed topic files durable versus conversation-scoped under index-rather-than-prune: durable means the content outlives the conversation that wrote it (a do-not-redo marker, a standing preference, or project state); conversation-scoped records session or lane state and is not durable memory. A mixed note classifies by its dominant signal. In doubt, index rather than prune: a topic file in doubt gets an index pointer recommendation, never a deletion. The classification pass is bounded to the run's recorded token budget: when the unindexed set exceeds what the budget covers, classify a prefix of the directory listing in sorted order, record the covered fraction, and drain the remainder across runs.

## State record

Write ONE atomic state-record update per run (default path `.ai-playbook/maintenance/memory-index-audit.json`): measured values, pointer findings, classification progress, `last_run_at`, and the advanced `next_due` together, through a temp file plus atomic replace, so a death mid-run leaves either the prior record or a complete one.

## Filing rule

On an over-budget finding (or any finding needing operator decision), file the compress-and-index remediation request through the filing rule as a NEW backlog row: check open, completed, and deferred rows first (a dated evidence line on an existing row beats a duplicate), compose per receiving-review's Backlog capture required content with its `Origin class:` line set per that rule (an audit-lane filing is self-serving unless the witnessed defect was seen in a consumer project), and name a lane-quiet window (a period with no live authoring or execution claims under the tmp directory) for the requested pass. The row carries the operator-decision framing and never self-authorizes plan work: the one-time consolidation (compress and index, then the reviewed prune) runs ad hoc only, per the operator's recorded rescope. No audit or remediation run ever rewrites the index mid-lane; never bulk-delete topic files; never delete a topic file whose live do-not-redo marker a lane still depends on.

## Failure arm and caps

A failed run records a one-line `last_result`, advances `next_due` by one day through the consult's failure advance, and increments `consecutive_failures` (a completed run resets it). Caps: at most 2 sub-agents, a recorded token budget (recorded by the first completed run), idle/off-peak preferred.
