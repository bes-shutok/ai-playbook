# Backlog: closeout retains completed branches after base-history drift

- **Filed:** 2026-11-02, self-heal recovery of the quota-governor strand cleanup
- **Status:** covered (docs/history/plans/completed/2026-11-04-agent-resource-cleanup-disposition.md; executed tip 57c2b2158)
- **Priority:** medium
- **Origin class:** observed closeout refusal
- **Class:** fix-class
- **Driving force:** simplicity + operator time
- **Skill-step:** `scripts/worktree_closeout_migrate.py` `_gate_branch_closeout` and `_branch_landing_content_scope`
- **Incident:** closeout of `2026-11-01-keep-quota-evidence-within-runtime` at tip `6518732d6e82a45c69d9bbaeee7cf699a2eb5a6d`
- **Catch frequency:** witnessed once in this cleanup; future frequency is unknown
- **False-positive cost:** a completed branch ref remains allocated and requires manual recovery when its landed history is no longer reachable from current `main`
- **Review date:** 2026-12-02
- **Dedup probe:** `docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md` covers the branch-only completion signal, and `docs/history/backlog/2026-11-01-gate-removal-formal-residues.md` covers formal review residues; neither covers base-history drift making a completed branch appear to contain an out-of-scope path.
- **Cluster:** `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (shared worktree and branch cleanup surface; this row owns cross-turn inventory and disposition, that row owns false-negative landing proof)

## Problem

The closeout gate retained the execution branch with `no ancestry or exact-tree proof; branch content outside the landing's file set: README.md`. The branch tip's tree is identical to the old landing commit `944cb825c`, but that commit is not reachable from current `main`. The completed plan is present in the primary checkout, while later history changes make the gate's current destination-history proof miss the earlier landing. Its legacy changed-path analysis also treats the inherited `README.md` difference as branch content even though the branch's landing commit did not touch that file. The worktree was removable, but the branch-only closeout remained unresolved.

A second strand showed the related recovery cost: after the gate authorized removal of an authoring worktree while retaining its branch, the primary checkout's same-slug migration manifest still bound only the execution branch. The authoring branch's separate ignored manifest was lost with its worktree, so the branch-only retry could not use that strand's original evidence.

## Expected

The closeout path should distinguish a branch's authored delta from inherited base drift and should preserve the evidence needed to retry branch-only adjudication after a worktree is removed. Retain a branch when any authored content or required artifact is not proven at the destination. Investigate whether the existing checks can be narrowed or removed without increasing content-loss risk.

## Suggested investigation and direction

Trace how the worktree base, branch-authored changes, landing commit, destination history, and migration manifest are bound today. Compare the current ancestry/exact-tree rule with a narrowly scoped proof based on the recorded branch start and persisted landing artifacts. Evaluate the simplest supported repair, including keeping the current guard, narrowing its base-drift handling, and removing the branch-accounting guard entirely in favor of already-persisted artifact evidence plus the operator's explicit cleanup request. State which unlanded-delta cases each option could delete or strand. Do not manufacture ancestry, synthesize migration evidence, or add a second ledger; if a changed blocking rule is proposed, apply the repository Machinery admission protocol and name what existing blocker it retires or simplifies.

## Evidence

- `scripts/worktree_closeout_migrate.py` `_gate_branch_closeout`: ancestry or exact-tree accounting is required for deletion; legacy changed-path scope is explicitly evidence-only.
- `scripts/worktree_closeout_migrate.py` `_branch_landing_content_scope`: compares paths against the completed-plan landing's touched set and reported the inherited `README.md` path.
- Commit `944cb825c`: its tree equals the retained execution branch tip tree, but it is not an ancestor of current `main`.
- `docs/history/plans/completed/2026-11-01-quota-governor-runtime-evidence.md`: the completed plan is present in the primary checkout.
