Status: open
Priority: high
Class: fix-class
Origin class: witnessed defect (operator-directed recovery session over the 2026-11-04 primary checkout)
Dedup probe: searched open backlog filenames and bodies for `land-worktree`, `staged state`, `primary checkout`, and `desync`; the landing-serialization plan owns dispatch serialization and the ref-lock span around this same compare-and-swap but never the primary index state; the lock-acquire-export rows own merge-lock env capture across tool-call shells; the landing-identity tree-oid row owns the landing record's evidence shape; the closeout-clobber-guard family owns post-hoc clobber guards. None covers the omitted primary staged-state pre-refusal.
Cluster: docs/history/plans/2026-11-04-parallel-execution-landing-serialization-blockers.md (owns the landing serialization and the CAS critical section this desync rides)

# land-worktree moves main across a staged primary checkout with no staged-state guard

## Observed vs expected

Observed: a session staged its PLAN-PROMPTS.md catalog entry in the primary checkout at 14:38:55 and ended before its second commit; 35 seconds later a plan landing ran `land_squash.sh land-worktree`, which moved main across the staged path by compare-and-swap and by design neither inspects nor writes the primary checkout's index or worktree. The landing left no signal; the checkout then silently desynced from main's tree, displaying the landing's own rider edits to the file (Frozen-line removal, scope-arm narrowing) as a staged re-application of the pre-landing content against the new tip - a foreign-looking staged hunk inviting the next session to "fix" it by re-committing pre-landing bytes over the landing's rider.

Expected: the landing refuses when the primary checkout holds staged or locally-dirty state on a path the landing changes, naming the intersecting paths before any ref update; and a session that stages state in the primary checkout commits or restores it before its own boundary, never leaving staged state stranded for the next session to trip over.

## Evidence (trimmed)

- Timeline (2026-11-04): 14:32:29 the carrier-gc origin row committed (902dc6062); 14:38:55 its session staged the catalog entry (index ctime/mtime 14:38:55, blob 3e7b4418357216dbf4bf40b3ddcbdc5299bd580b) and ended before the second commit; 14:39:30 the producer-code-family-record-arm landing CAS-moved main a0f081210 -> ad3361d25 across the staged path (empty reflog entry, no landing-time signal); the checkout then showed the landing's rider edits as a staged resurrection. The stranded entry was recovered byte-identical by the peer investigate pass (a3e2fdcbc); the resurrection remainder was discarded by hand (path restore to HEAD at 38358461b).
- Second witness of the class: the 2026-10-28 teardown preserved an identical resurrection ("foreign staged dirt: PLAN-PROMPTS resurrection of pre-landing freeze blob e1ccdb106", content preserved at 0ae014837, still held in the stash list) - the class predates this witness by a week.
- The omission is by design, named verbatim in the tool's own usage text: land-worktree "Never writes the primary checkout's index or working tree and never runs porcelain or restore against it (land's snapshot, staged-state and dirty-intersection pre-refusals, and restore machinery are omitted)" (`scripts/land_squash.sh`); the mode was introduced 2026-10-18 (f3894756d) and hardened 2026-10-28 (53d4fcd2f) without gaining a primary-index check.
- `git update-ref` (the CAS) operates at the ref level only and cannot refuse on worktree state; the guard must therefore be an explicit read-only check inside the landing flow, not a property of the ref update.
- Same-evening witness for the stranded-record half (the census arm, no landing desync involved): the 20:31 execution-claim-gateway override append to `scripts/gate_liveness_ledger.json` (the done step's advisory append) was written by the interactive execution run that landed 1a1673921 at 21:08, whose landing omitted the ledger file and whose learn commit (e4fcf1a87) closed the run with the record still uncommitted; landed posthumously 22e99c4ec. The census duty's porcelain sweep covers this unstaged shape alongside the staged one.

## Suspected root area

`scripts/land_squash.sh` land-worktree mode: add the intersecting-path pre-refusal before the compare-and-swap (the changed-path set the landing already computes for land's dirty-intersection check is the same input). The stranded-staged-state half has its home in the primary-checkout closeout arms (`agents/skills/execute-plan/worktree-first.md`): a session-end `git status --porcelain` census with a commit-or-restore disposition for staged entries the session owns.

## Ship when

The pre-CAS guard refuses a fixture landing whose changed set intersects a staged primary path (suite cells in `scripts/test_land_squash.py`: intersecting staged path expects the named fail; non-intersecting staged path expects the landing to proceed), and the primary-checkout closeout carries the session-end staged-state census duty with the commit-or-restore disposition.
