# Backlog: a primary-checkout record commit swept a dead peer run's stranded staged delta and reverted a peer landing's record state on main

- **Filed:** 2026-11-19, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture)
- **Status:** covered (docs/history/plans/completed/2026-11-19-stale-capture-record-commit-peer-clobber.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed cross-record corruption (one incident, main history carries the corrupted bytes; the residue walled one authoring turn and cost three more sessions attribution steps)
- **Skill/step:** the authoring lane's certification-checkpoint commit ("plans: checkpoint <plan> certified plan bytes", pre-landing record durability) and every primary-checkout record commit made in a checkout shared with concurrent sessions, versus the foreign-staged verification the Standing rules block of `docs/history/backlog/PLAN-PROMPTS.md` pins for rolling-log writes and the learn commit rule pins for its own commits
- **Cluster:** docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md (same primary-tree stranded-record family; that row owns stranded appends left uncommitted, this row owns a commit that swept stranded staged state into history)
- **Cluster:** docs/history/backlog/2026-11-06-exec-plan-checkbox-marking-primary-strand.md (same shared-checkout plan-file hazard, write-side instance)
- **Cluster:** docs/history/backlog/2026-11-02-primary-tree-backlog-writes-no-commit-leg.md (same family: primary-tree record writes whose commit leg never ran)
- **Cluster:** docs/history/backlog/2026-11-19-certification-checkpoint-main-placement-add-add-conflicts.md (same checkpoint commit class; that row owns the placement-induced landing conflicts, this row owns the foreign-delta sweep hazard)
- **Cluster:** docs/history/backlog/2026-11-19-authoring-freeze-checkout-state-refusal-no-decay-arm.md (same wall, class arm: this row owns repairing this instance's residue bytes; that row owns the missing unattended-decay/recovery arm for the sweep-refusal class itself)

## Problem

Witnessed sequence, all legs verified on disk and in the window's session records:

1. An execution session landed `4f7a36be8` (the handoff-reconciler-dead-drift-mappings landing: archive rename to `docs/history/plans/completed/2026-11-13-handoff-reconciler-dead-drift-mappings.md` with `Executed: yes` bytes, origin-row deletion, its Phase 3 backlog row `docs/history/backlog/2026-11-18-completed-plan-evidence-series-criterion.md` filed `Status: open`) and then died mid-finalize (manifest `20261119T004829Z`, recorded pid gone), leaving stranded staged record mutations (deletions and renames) plus uncommitted record edits in the shared primary checkout.
2. The next authoring session's freeze write was refused by the landing sweep on that foreign staged state (gate-correct); the session reverted its own bytes, polled the dead holder for about 20 minutes, established the holder dead, and stood down reporting operator cleanup owed (0/1), per the operator-reconciliation doctrine for foreign-owned paths.
3. The following primary-checkout record commit, `e7c281cdf` (the read-only-verification-lane certification checkpoint, 01:44:48Z), committed a delta that includes deleting the peer landing's fresh open row and an `R057` rename of the executed archive twin back to the living plans-root path with pre-execution bytes (`Executed: no`). Whether those deltas were the dead peer's stranded staged entries or the committing session's unverified index state, the effect is the same: a record commit composed over an unverified shared index published another run's half-done finalize as history.
4. The landing that followed in the same series (`0c0080b10`) rode on top without noticing. Main's durable record for the executed plan is wrong as of this filing: the living path claims `Executed: no` with pre-execution terms, the executed archive twin and the open row exist only as untracked worktree bytes, and a fresh session scanning the plans root reads an executed plan as dispatchable again.
5. Downstream cost in the same window: the residue walled one authoring turn end to end, three peer exec sessions independently re-attributed the scene's uncommitted dirt, and the 02:00 author re-verified the same surfaces a third time.

## Why the existing protections did not apply

The contract exists at every neighboring class but not at this one: the Standing rules require rolling-log writes to verify the ref/OID pair under the primary done lock before any edit and refuse foreign staged deltas at the runner; the learn commit rule requires an own-edit word-diff check and refuses bare commits on an unverified shared index; the landing machinery refuses on any staged state at its snapshot. The certification-checkpoint commit class and primary-checkout record commits generally have no equivalent preflight: nothing re-derives, under the done lock, that the index holds only the writer's own hunks before composing the commit, and nothing reconciles a dead peer's stranded staged delta before the next record write lands on top of it.

## Expected

A primary-checkout record commit composes only from a verified index: under the done lock, the writer enumerates the staged set and word-diffs it against its own hunks; any foreign staged entry (including a dead peer's stranded D/R) stops the commit for reconciliation instead of riding into history. A dead peer run's stranded staged delta is drained (or explicitly parked operator-side) before the next record commit in that checkout, and the classes that already carry the check (log writes, learn commits, landings) name one shared preflight rather than three private copies.

## Suggested direction

Two arms, one plan: (a) repair main's record state (restore the executed archive twin at the completed path, restore the open row, remove the reverted living-path copy so the archive rename stands as the peer landing recorded it, commit the three stranded `docs/history/certification-seal-landing-diagnostics.md` appends sitting uncommitted in the same window, and drain the dead run's remaining residue per the operator-reconciliation doctrine); (b) bind an owned-staged-set preflight to the primary-checkout record-commit class (checkpoint commits first), by reference to the Standing rules' existing guard rather than a new mechanism.

## Machinery admission (guard arm)

- Concrete incident: this row; the corrupting commit is `e7c281cdf`, the peer landing it published half of is `4f7a36be8`, both reachable from main; the walled authoring turn is the 01:00 carrier session's stand-down report.
- Expected catch frequency: the preflight fires only when a shared index holds foreign hunks at record-commit time, which the window shows is not rare (one dead-peer strand plus one near-miss where a wrong union resolution almost clobbered a peer's landed prune receipt); rare per commit, high harm per catch.
- False-positive cost: a record commit refused on a flagged foreign hunk pays one re-derivation turn; the existing failure semantics (report and park) bound it.
- Sunset/review date: 2026-12-19; lands warning-only first, promotion per the repository guidelines' Machinery admission protocol after a second true catch.

## Evidence

- `git diff --name-status e7c281cdf^ e7c281cdf`: D of the row, R057 completed-to-living rename-back, A of the checkpointing plan.
- `git show e7c281cdf:docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md` reads `Executed: no`; the completed twin in `4f7a36be8`'s tree reads `Executed: yes (0f19aee5...)`.
- `git status --short` at filing: the completed twin and the row untracked; `docs/history/certification-seal-landing-diagnostics.md` carrying three uncommitted post-landing appends.
- The 01:00 carrier session's stand-down report (manifest `20261119T004829Z`, dead-pid forensics, refused freeze, operator-cleanup-owed) and the 02:00 session's re-walk, both in the window's session records.
- Second carrier burn: the 04:00 author carrier (2026-11-19, one-shot automation-1a3f6579) stopped 0/1 at the same state; its Phase 0 freeze transaction was refused by the landing sweep (`plans-archive-twin` rc=1 on the living/completed basename pair, `doc-registry` rc=1 HARD on the untracked completed twin), with an ownership-checked cleanup (lock orphan-released, frozen-line edit reverted, claim deleted) and no plan bytes written.
- Directive check at that stop: D-19 (`docs/maintenance/operator-directives.md`) pre-gives the operator direction for a foreign staged delta ON the log path only; the checkout-record-state refusal class has no pre-given direction (`docs/history/backlog/2026-11-19-authoring-freeze-checkout-state-refusal-no-decay-arm.md` owns the class).

## Dedup probe

Searched open backlog for `captured-tree`, `stale-base`, `checkpoint`, dead-peer, and the archive-rename family: the dead-peer-blocks-foreign-owned-path doctrine and the stranded-run drain machinery own the recovery flow, but no row owns a record commit that swept stranded staged state into history or the missing preflight on the checkpoint commit class.

## 2026-11-19 ~12:05Z re-derivation witness (24h session-pattern harvest re-run)

Independent re-derivation at the main tip 2ce4bc9b5 confirms every strand fact still stands and the repair arm remains unexecuted roughly ten hours after filing: the row and the completed archive twin are still untracked worktree bytes, the living plans-root copy is still present in HEAD's tree at the pre-execution state, and `docs/history/certification-seal-landing-diagnostics.md` still carries the same three uncommitted post-landing appends (mtimes 2026-11-18 15:04Z, 2026-11-19 00:44Z, 01:53Z). At least five further sessions ran in the same checkout since filing without a repair leg (the 07:0x operator arc, the 05:01 exec carrier whose final report re-attributes the same dirt as "Not mine, left untouched", the 11:42-12:04 scheduler-session arc), each paying fresh attribution or avoidance cost - the witnessed cost the authoring turn prices has grown accordingly. The checkout's uncommitted record set has also grown: the PLAN-PROMPTS.md intake-continuity entry swap (the scheduler session's monitor prune output, still uncommitted as of this re-derivation while its owner session landed adjacent work at 12:04Z) and the corrections-writer plan checkbox ticks (a foreign codex run's state, untouched since 2026-11-18 19:47 local) now share the scene, so the repair turn must re-derive ownership at execution time and sweep the grown set, not just the filed strand. Priority re-affirmed: high.

## 2026-11-19 ~15:20Z repair-progress witness (operator-ordered analyze-and-fix turn)

The 12:05Z re-derivation was overtaken on two legs: the operator-directed migration `9d098910c` (12:09:45Z) completed both archive legs (living-root copy removed from the plans root, completed twin tracked with `Executed: yes (0f19aee5...)`), and the PLAN-PROMPTS intake-continuity entry landed with its owner arc (`d7c35ab00`, 13:10Z). This turn lands the repair arm's remaining record legs in the commit carrying this witness: the three stranded `certification-seal-landing-diagnostics.md` appends (2026-11-18T15:04Z run `20261118T144705Z-e01ea6ed342b` serialized receipt for landing `6da656be9`; compact outcome rows for the `e4db909a4` and `0c0080b10f` filings, runs `e79c54929dd9`/`7ab10d1ecb73`) landed verbatim in append order, and the open row `2026-11-18-completed-plan-evidence-series-criterion.md` restored (claims re-verified first: r1 F4 and the completed twin's Task 4 criterion line). The two compact rows deviate from the ledger's serialized-receipt shape with no contract receipt in either ledger; routed to `docs/history/backlog/2026-11-19-certification-seal-receipt-shape-residual.md`. The corrections-writer ticks re-verified as a live codex run's worktree mirror (claim session `01a1f00b`, blob-identical to branch tip `4b9b6d1c0`), self-resolving on that branch's landing, left untouched. Arm (b), the owned-staged-set preflight, remains this row's open work.
