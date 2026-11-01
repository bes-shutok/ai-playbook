# Stale pre-rewrite landing sha in the worktree_closeout_migrate gate-removal comment

Status: open
Workflow: backlog
Priority: low
Class: fix-class
Origin class: learn Step 1.9 project issue capture (2026-11-01 learn run over the same day's authoring session; the finding was raised by that run's plan-review confirm round and omitted from the plan as an out-of-scope extension)

## Problem

The gate-removal guard's inline comment in `scripts/worktree_closeout_migrate.py` (the swept-artifact classification paragraph) cites the landing of the 2026-10-31 closeout-gates trio as `52750a1fe`. That sha is a pre-rewrite twin: it resolves as an object but is not an ancestor of main, so the comment cites a landing that never landed (lesson 359: ancestry, not existence). The live landing of the same change is `eebc930c0`; both shas carry the identical subject line, which is the squash-twin signature.

## Evidence

- `git cat-file -e 52750a1fe` passes while `git merge-base --is-ancestor 52750a1fe main` fails; `eebc930c0` passes both, with the same subject ("closeout: land done-closeout-gates-trio ...").
- Comment site: the swept-artifact classification block (~line 3810), "landed 52750a1fe; shared-slug second witness".
- Second citing span: the `PLAN-PROMPTS-PRUNE: gate-removal-drained-destination-disposition` receipt line at the top of `docs/history/backlog/PLAN-PROMPTS.md` names the same dangling digest in full (`52750a1fe7ae0de83cc622f87a8d91bad9543216`) as its implementing-commit witness; the audit's token resolution passes on object existence, so the prune audit stays green over a witness that never landed.

## Suspected root area

Comment-only defect in `scripts/worktree_closeout_migrate.py` plus one receipt-line citation in the rolling log; no behavior change. The shas were carried from run telemetry instead of derived from the base branch.

## Fix shape (body-named, single bounded change-set, no open design choice)

Replace both cited shas with the live landing digest `eebc930c0` (full form re-derived from disk; or reword to path plus date per lesson 132), sweep the touched files for further pre-rewrite sha literals before committing, and run the script's test suite unchanged-pass as the guard.
