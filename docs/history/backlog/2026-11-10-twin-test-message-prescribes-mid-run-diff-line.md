# Twin-equality test failure messages steer plan authors into a structurally RED mid-run diff line

- **Filed:** 2026-11-10 (published-stack-review-coverage-gap authoring closeout, learn Step 1.8)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** review finding (plan-review r4 four-worker echo, verified again by the r5 panel)
- **Class:** fix-class (a test failure message prescribes a remedy that is defective under the verified runtime layout)
- **Driving force:** reliability
- **Dedup probe:** searched open backlog filenames and bodies for twin-equality, vendored twin, twin diff, and the message phrases; no row covers the message's prescribed remedy. Related lessons: 309 (twin-pin diagnosis), 369 (sync timing), 433 (twin-diff gate prescription).
- **Cluster:** none
- **Capture hygiene:** scan-public-hygiene --files pass over this draft before landing (2026-11-10).

## Which skill and step

`scripts/test_done_sweep_gates_lib.py`, the two standing twin-equality tests (the execute-plan skill receipt pins test and the review-composition filed-rows pins test), and the plans skill's Validation Commands authoring that their failure messages address.

## Observed versus expected

Observed: both tests' failure messages say the twin sync and "the diff line in the plan's Validation Commands" own the equality, and that the diff line "must exit 0". A plan that edits either pinned file is thereby steered to carry a standing `diff <repo-file> "$HOME/.agents/skills/<file>"` gate. Where the runtime skills home is a symlink into the primary checkout, that line compares the executing worktree's file against the primary checkout's tracked file: GREEN at base, RED from the owning task's edit until the landing, and a trivial self-compare after it. It never measures twin drift, and the only way to green it mid-run is writing the shared primary checkout ahead of the merge-locked landing.

Expected: the message names a remedy that holds under the symlinked layout (the landing re-equalizes the pair; no mid-run diff line is owed), or scopes the diff line to the landed tree the way the diff-line precedent's own Ship-when does.

## Evidence

- A review round's testing worker read the messages plus the 2026-10-15 closeout-cycle precedent and prescribed the two diff lines; the fold added them under "Standing gates, from the executing worktree root".
- The next round measured the lines exit 1 against a faithful landing from the worktree and `-ef` identical from the primary checkout; four workers staged the defect (High, blocking) and the follow-up fold removed the lines.
- Measured behavior of the tests themselves: both pass at base, fail from the owning task's edit through the full landing overlay, and pass once the twin resolves to the landed tree.

## Environment

Playbook repo, 2026-11-10, worktree-first authoring run; runtime skills home symlinked to the primary checkout's `agents/skills`.

## Suspected root area

The two failure-message strings. Secondary: the plans skill's validation-authoring guidance carries no rule on twin-diff gate scoping (lesson 433 records the trap; a one-line pointer may suffice once the messages are fixed).
