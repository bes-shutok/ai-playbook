- Status: open
Priority: high
Urgency remark: execution-landing integrity defect witnessed live; until the landing gate exists, every plan execution squash can silently sever main's history again
Promoted: 2026-09-27 filed directly from the recovery session after the fix landed

- Workflow: backlog
- Priority: High
- Created: 2026-09-27

# Execution squash landing moved main to a parentless orphan commit and severed all history

## Witness (2026-09-27 03:58 local)

The review-loop churn-prevention plan execution landed by moving `main` to commit `351f704f` (message "squash: execute review-loop churn prevention plan"), which had NO parent: it was a root commit. The `git reflog main` entry for the move has an empty operation string, which points to a plumbing write (`commit-tree` / `update-ref` / `branch -f`) computing the new commit with a missing or empty parent variable, instead of a normal commit on top of main.

Because the orphan root still carried the full repository tree plus the plan's own 15-file change, all CONTENT was intact. But the history link was severed: `main` and `origin/main` had no merge base; `git status` reported "ahead 8, behind 155". 155 pushed commits plus 236 unpushed commits (everything through pre-squash tip `beae386b`, 03:55) became unreachable from main. The next seven commits (origin-class execution, run-start-marker re-certs and execution, plans-authoring execution, two backlog filings, 04:29 to 06:49) stacked normally on the orphan root, extending the severed chain.

## Fix performed (2026-09-27 ~07:05 local)

1. Recovery refs created before touching anything: `recovery/pre-squash-main` (pre-squash tip `beae386b`) and `recovery/orphan-main` (orphan-chain tip `699e111c`).
2. The squash commit was re-parented: `git commit-tree` produced `66986f0e` with the orphan root's exact tree, message, author, and dates, but parent `beae386b`. Its diff against `beae386b` is byte-identical to the orphan root's diff (15 files, 92 insertions, 264 deletions).
3. The seven descendant commits were cherry-picked in order onto `66986f0e` in a detached temp worktree; all applied cleanly (base content matched exactly).
4. Gates before the swap: rebuilt tip tree byte-identical to orphan tip tree (`git diff` empty); `origin/main` is an ancestor; 244 commits on top of `origin/main` (236 pre-squash + 8 rebuilt).
5. `main` swapped atomically via `git update-ref`; working tree and index untouched (trees identical, status stayed clean). New chain: `beae386b` > `66986f0e` > `35ae2f88` > `f3329c81` > `c0403c5b` > `c7ed9723` > `3b234a5e` > `ba1166b4` > `4d6f900e` (tip). Old-to-new mapping lives in the session memory under "orphan-squash history rebuild".

## Root cause to investigate (open)

Why the churn-prevention execution's landing path produced a parentless commit while the same-day plans-authoring execution (05:43) landed a normal parented commit. Suspects from that session's record: it hit reverse-squash dirt mid-run and released a done-lock under nonstandard conditions; a recovery-from-dirt arm may have rebuilt the landing commit with an empty base variable. Read that session's transcript before closing this item.

## Prevention (proposed fixes)

1. Landing parentage gate (execute-plan closeout): before swapping `main` to a squash commit, assert the commit has exactly one parent and that parent equals the observed pre-landing main tip. A parentless or unexpected-parent squash must hard-fail the landing.
2. Post-landing ancestry assertion: `main` must still descend from the pre-landing tip (and from `origin/main` for fast-forward pushes); a landing that drops ancestry fails loudly and leaves main untouched.
3. Extend the existing reverse-squash detector to cover this shape: a squash commit whose tree is a near-full-repo snapshot but whose parent set is empty.
4. In-flight sessions at fix time: the review-agents-corpus-family execution (worktree `ai-playbook-exec-racorpus`, branch `2026-09-27-execute-review-agents-corpus-family`, two commits on orphan commit `e6c19e10`) and the grilling-fork execution (worktree `ai-playbook-exec-grillfork`, branched at orphan tip `699e111c`) are based on the ORPHAN chain. Their landings must be diff-based onto the rebuilt main (trees are identical, so diffs apply cleanly); rebasing onto rebuilt main would find no common ancestor and explode. After they land, re-run the parentage gate on main.

## Follow-ups

- Operator decision: push main to origin (fast-forward, 244 commits) or keep local until the racorpus/grillfork landings complete.
- Keep both `recovery/*` branches until origin is updated and the in-flight worktrees land, then delete.
