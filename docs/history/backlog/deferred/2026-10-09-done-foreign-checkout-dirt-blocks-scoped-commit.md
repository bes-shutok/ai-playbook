# Backlog: allow a safe scoped closeout when unrelated checkout dirt remains

- **Filed:** 2026-10-09, operator-directed
- **Status:** deferred (2026-10-09, operator routing: disposition rides the closeout-gate demotion program in docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md; warning-only conversion of the post-landing-staging unstaged leg (2 catches / 5 incidents in scripts/gate_liveness_ledger.json) removes the foreign-checkout blocking shape; scoped-closeout allowance re-checked after conversion)
- **Cluster:** docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-reported closeout blocker
- **Class:** fix-class
- **Skill/step:** `agents/skills/done/SKILL.md`, pre-commit `post-landing-staging`; `scripts/done_sweep_gates_lib.py`
- **Driving force:** reliability + simplicity
- **Consumer urgency:** A shared closeout safeguard blocked an explicitly requested documentation commit in a consumer repository because unrelated task changes remained in its primary checkout.

## Problem

The `post-landing-staging` gate requires the primary checkout to have no unrelated unstaged changes before a scoped commit can proceed. In a consumer repository with another task's modified source/config files and untracked templates, this prevented committing a separately staged documentation update. This is a mutual hard lock: the same residue prevents the other task from committing too, so waiting for that task to land first cannot resolve the cycle. The gate correctly prevents foreign changes from being accidentally included, but the consumer repository forbids worktrees and the files could not safely be stashed, restored, or committed as part of this task.

## Evidence

- On 2026-10-09, the consumer checkout had one staged documentation file and multiple unstaged source/config changes plus an untracked template directory.
- `done_sweep_gates.sh pre-commit` passed the sensitive-data and foreign-staging checks, then failed `post-landing-staging` on the unrelated unstaged paths.
- The merge lock and done lock were free. The pre-existing changes had no verified owner/liveness record, so treating them as dead residue and restoring them was unsafe.
- The consumer repository's instructions prohibit creating or using a Git worktree unless the user explicitly asks for one.
- The staged documentation change passed `git diff --cached --check`; the unrelated paths were left untouched.
- A second occurrence on 2026-10-09 in a consumer checkout reproduced the mutual block: a peer-owned operational guide edit caused the `post-landing-staging` gate to reject a separate authorized implementation commit. The peer task then completed without landing its edit, leaving no safe wait-based resolution.

## Expected

Replace the mutual checkout-wide commit lock with a safe scoped-landing rule. Evaluate a path-scoped commit path that proves the commit contains only explicitly authorized, reviewed paths while preserving all foreign worktree changes. Keep sensitive-data and commit-scope checks on the exact commit tree. Ensure the ordinary closeout can record ownership and resume after such a scoped landing without requiring the unrelated task to finish first. Do not weaken data-loss protections or prescribe stashing, restoring, or worktree creation where repository policy or uncertain ownership makes that unsafe.

## Immediate workaround

For an explicitly authorized landing, recheck the exact diff and sensitive-data scan, then use Git's path-scoped commit mode (`git commit --only -- <owned-paths>`). This writes only the named paths to the commit and leaves other task worktree changes intact, so neither task has to wait for the other's full completion. A second consumer occurrence is now proceeding with that exact-path method for its authorized nine-file change set. Keep the limitations visible: this is a narrow landing workaround, and the shared `done` manifest and remaining closeout bookkeeping still need an owner-defined resolution. Do not use it to include paths outside the user's authorized scope.

## Deduplication

`2026-10-06-done-unrelated-gate-blocks-closeout.md` is covered by the readiness-closeout plan and addresses unrelated workflow obligations; this item concerns unrelated working-tree state in a consumer checkout. `2026-10-08-done-closeout-ceremony-friction.md` covers manifest, review, and plan ceremonies. `2026-10-08-done-ledger-append-blocks-closeout.md` covers a specific shared advisory file and has a whole-file landing remedy. This item records the separate case where peer-owned source/config dirt creates a mutual commit lock in a repository that prohibits worktrees. A path-scoped commit is the immediate containment workaround; redesigning the shared gate so it supports that landing safely is the follow-up.

## Source

- Consumer closeout observed 2026-10-09; project, task, and person identifiers omitted.
