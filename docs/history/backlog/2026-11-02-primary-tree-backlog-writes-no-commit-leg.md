# Backlog: primary-tree backlog writes have no tracked landing path when the writing session dies

- **Filed:** 2026-11-02, interactive session investigating uncommitted working-tree dirt
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/learn/SKILL.md` Step 1.9 investigate; `agents/skills/self-heal/SKILL.md` Recovery; repository guideline "A run that files durable records lands them in the same run or leaves a tracked landing path"
- **Catch frequency:** second witnessed instance (2026-11-02 uncommitted dirt attribution; earlier uncommitted-dirt incidents in session memory)
- **False-positive cost:** a row added to a landing sweep for dirt that was a deliberate WIP checkpoint
- **Review date:** 2026-12-02
- **Dedup probe:** searched open backlog for landing path / stranded / durable-record coverage. Worktree sessions get claims and stranded-run drain machinery; `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md` covers stub rows, not record files. No row covers records written directly into the primary tree (learn/investigate backlog filing) whose writing session terminated before its commit leg, leaving unattributed dirt.
- **Cluster:** `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (both own cross-session resource/record disposition; that row owns user-requested cleanup scope, this row owns the write-then-die commit-leg gap)

## Problem

A learn Step 1.9 investigate pass (and an earlier same-day pass) wrote durable backlog records directly into the primary working tree on `main`: a new origin row, two prompts-log entries, and a Cluster pointer addition to an already-committed row (mtimes 17:04 and 17:59, 2026-11-02). The session then terminated before any commit leg, so the records sat as uncommitted dirt with no claim, worktree, or sidecar pointing at them — the state the stranded-run drain machinery cannot see, because it only tracks worktree-scoped strands. Attribution required the blob-hash mirror test and mtime + introduction-trace analysis before the records could be safely landed.

## Expected

A session that writes durable records into the primary tree either commits them before terminating or leaves a discoverable record of the pending write set (the same "lands in the same run or leaves a tracked landing path" contract that binds landings). An investigating session finding primary-tree dirt whose content self-identifies as dated backlog records can attribute and land it without a full forensic pass.

## Suggested direction

Evaluate whether the learn/investigate step can append the pending write set (paths + blob hashes) to an existing discoverable surface (the run's own manifest or the closeout baseline) at write time, so a died session's writes are attributable by reading one file instead of mirror-testing blobs. Prefer reusing existing surfaces over any new ledger (Machinery admission protocol); read-only first, no blocking gate.

## Evidence

- `git status --short` at session start showed 3 modified + 1 untracked backlog file, all dated 2026-11-02, none traced by `git log -S` into history.
- Blob hashes of the dirt matched no peer worktree HEAD (mirror test: `0ef784dbd…`, `9e30e70e9…`, `817785847…` unique to the primary tree).
- The dirt content verified factually on inspection (machinery check's 2 regrowth FAILs, introducing landings 44f9499a5 / 137c50ebd), confirming genuine records rather than corruption.
