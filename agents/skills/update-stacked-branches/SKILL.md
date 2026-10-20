---
name: update-stacked-branches
description: >
  Refresh an open stacked branch chain after its base moves, using a merge-based
  restack with optional squash and force-with-lease push. Use when the user asks to
  refresh a PR stack, update a branch chain, merge trunk into a stack, or restack
  one branch on another. An explicit request to run `git rebase` uses this skill's
  separate bottom-up rebase procedure, never its merge-based procedure.
  Post-squash-merge child reparenting stays in github-pr-workflow (`rebase --onto`).
---

# Update Stacked Branches

**Restack** means integrating an updated base into an open dependent branch chain. When no Git strategy is specified, this skill uses merge-based methods to preserve the branch's existing commits and avoid rewriting descendants of a shared parent. `git rebase` instead replays the branch commits individually with new commit IDs. A squash is a separate history choice: after integration, `git reset --soft` and one commit replace the branch's commit series with a single commit while retaining the integrated tree. Never interpret an explicit request for one strategy as permission to use another. If the branch state makes the requested strategy unsafe or its base cannot be identified, explain the concrete risk and ask before choosing another strategy.

## Routing Boundary

| User intent | Primary skill |
| --- | --- |
| Trunk moved; refresh open stack `A → B → C` without a specified Git strategy | **This skill** (merge-based restack; owns PR base retarget) |
| Explicit `git rebase` request for an open stack | **This skill**, Method C (bottom-up rebase; retains child commits by default unless squash is separately requested) |
| Parent already **squash-merged** into trunk; reparent child only | `github-pr-workflow` (`rebase --onto`) |
| One-off `-squashed` PR branch from a source tip | `github-pr-workflow` |
| PR description, stats, split, open PRs | `github-pr-workflow` |

## Hard rules

1. **Absorb before reparent.** Never `git reset --soft <parent>` unless `merge-base --is-ancestor <parent> HEAD` is already true (check immediately before the soft-reset). Soft-reset alone reverts parent commits.
2. **Bottom-up.** Trunk → branch[0] → branch[1] → …. Finish and verify each link before the next.
3. **Pick a method from the requested strategy and rewrite state**, not from "trunk advanced alone." Explicit rebase requests use Method C. Merge-based restacks use Method A or B; Method B is only for a parent tip that was rewritten this session (see Phase 1). Naive `git merge <parent>` after a parent squash uses an ancient merge-base and conflicts everywhere.
4. **Backups are load-bearing.** Phase 0 creates `backup/<branch>-<YYYYMMDD>` for every chain branch **before** rewriting any tip. Method B uses those dated refs as `backup_parent` / `backup_branch`. Keep them until the full chain finishes.
5. For merge-based methods, squash is optional. Ask **once per restack session**; the answer applies to every link unless the user opts out per branch. For an explicit rebase request, do not squash unless the user separately asks to squash.
6. **Push** only with explicit approval. Prefer asking once for the whole stack or per link after that link verifies. Use `--force-with-lease` after a fresh fetch of that branch. Never bare `--force`. **Never** force-push trunk / default / shared integration branch names (`main`, `master`, or the repo default).
7. Prefer **local** tips when `origin/<branch>` is behind local. **Exception:** trunk always comes from current `origin/<trunk>`.
8. No `git reset --hard` to discard work unless the user asks. Restore mid-restack with the **Restore from backup** commands below.

## Restore from backup

```bash
git merge --abort 2>/dev/null || true
git rebase --abort 2>/dev/null || true
git checkout -B <branch> backup/<branch>-<YYYYMMDD>
```

Use after a failed Method A/B/C or failed verify. Do not push the broken tip.

## Inputs

| Input | How |
| --- | --- |
| Trunk | User name, else bottom PR `baseRefName`, else repo default |
| Chain (ordered) | User list preferred; else infer from open PR bases and **stop** if not a single linear stack |
| Squash? | Hard rule 5 |
| Push? | Ask after local verification (hard rule 6) |

## Phase 0: Preflight

```bash
git fetch origin
git status --porcelain   # must be empty (or stash only with user OK)
```

Resolve trunk, then **require** remote tip for all bottom-link math:

```bash
git fetch origin <trunk>
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
# parent_tip for i==0 is always origin/<trunk> (never a possibly stale local trunk ref)
```

For each index `i` with `branch = branches[i]`, `parent = trunk` if `i == 0` else `branches[i-1]`, and `parent_tip = origin/<trunk>` if `i == 0` else `<parent>`:

```bash
git branch backup/<branch>-<YYYYMMDD> <branch>
git rev-parse <branch>                                         # old tip
git diff --stat <parent_tip>...<branch> | tail -1              # pre-delta magnitude
git merge-base --is-ancestor <parent_tip> <branch>; echo $?
gh pr list --head <branch> --json number,url,baseRefName,state
# Store open PR number for later gh pr edit (skip if none)
# When i > 0, detect merged parent PR only if there is NO open parent PR
# (branch-name reuse can leave historical MERGED PRs for the same head):
#   open=$(gh pr list --head <parent> --state open --json number -q 'length')
#   merged=$(gh pr list --head <parent> --state merged --json number -q 'length')
#   if [ "$open" = "0" ] && [ "$merged" != "0" ]; then STOP and hand off.
```

Stop if dirty tree, backup name collision, or ambiguous chain order.
Stop and hand off to `github-pr-workflow` (`rebase --onto`) when `i > 0`, the parent has **no open PR**, and `gh pr list --head <parent> --state merged` returns at least one PR. If the parent still has an open PR, continue this skill even if older merged PRs share the head name.

## Phase 1: Restack each link (bottom-up)

For `i = 0 .. n-1`:
`parent = trunk` if `i == 0` else `branches[i-1]`; `branch = branches[i]`.
`parent_tip = origin/<trunk>` if `i == 0` else `<parent>` (always use `parent_tip` for merge-base, soft-reset, diff, and verify).
`backup_parent` = `backup/<parent>-<YYYYMMDD>` when `i > 0` (Phase 0 ref for the previous chain branch).
`backup_branch` = `backup/<branch>-<YYYYMMDD>`.

### Choose method

First honor an explicit Git strategy. If the user explicitly requests `git rebase`, apply **Method C** to each link bottom-up and retain the child commits by default; squash only if separately requested. Do not use Methods A/B or squash as substitutes for the requested rebase. Otherwise use the merge-based method selected below, with squash only when requested.

| Condition | Method |
| --- | --- |
| `i == 0` (bottom link onto trunk) | **A: naive merge** of `origin/<trunk>` |
| `i > 0` and parent tip equals `backup_parent` (parent not rewritten this session) and `merge-base --is-ancestor <parent_tip> <branch>` | **A: naive merge** |
| `i > 0` and parent tip differs from `backup_parent` (parent rewritten this session) | **B: explicit-base** |
| Else | Stop; re-check chain order and backups |

### Method A: Naive merge

```bash
git checkout <branch>
git merge <parent_tip>    # origin/<trunk> when i==0; else <parent>
# resolve conflicts if any; commit merge if required
```

**Exit criteria (all required; abort and Restore from backup on failure):**

```bash
git merge-base --is-ancestor <parent_tip> HEAD   # MUST exit 0
test ! -f .git/MERGE_HEAD                        # merge finished
git diff --quiet && git diff --cached --quiet    # committed tip; ignore untracked
```

### Method B: Explicit-base (after parent rewrite)

```bash
git checkout -B <branch> <parent>
git merge-recursive <backup_parent> -- HEAD <backup_branch>
# resolve any remaining conflicts; index holds the merged tree; HEAD is still <parent>
```

If `merge-recursive` fails or conflict count is huge versus the pre-delta, **Restore from backup** and stop.

### Method C: Explicit rebase

Use only when the user requests `git rebase`. Rebase each child onto its updated parent, bottom-up, so each branch replays only its own commits. When the parent was not rewritten during this session:

```bash
git checkout <branch>
git rebase <parent_tip> <branch>
```

When the parent was rewritten during this session, use its pre-rewrite backup as the old boundary so the child's commits are replayed without replaying the parent's old commits:

```bash
git checkout <branch>
git rebase --onto <parent_tip> <backup_parent> <branch>
```

Do not squash this result unless the user separately requested a squash. If requested, finish and verify the rebase first, then follow Method C's squash arm below before updating the next child. After each link, verify the branch diff against its new parent against the preflight delta and confirm that no parent commits were replayed into the child. On conflict or verification failure, run `git rebase --abort`, restore the branch from its Phase 0 backup, and stop. If the old parent boundary is not the child's actual base, stop and establish that boundary before rebasing.

**Required finalize:** Method B reconstructs the branch delta on the rewritten parent and always records it as one commit before verify. This preserves the resulting tree after conflict resolution, not the branch's original sequence of commits; it is neither a merge commit nor a `git rebase` replay:

```bash
git commit -m "<single message for this branch story>"
```

**Exit criteria (all required; abort and Restore from backup on failure):**

```bash
git merge-base --is-ancestor <parent_tip> HEAD   # MUST exit 0
test "$(git rev-list --count <parent_tip>..HEAD)" -eq 1
git diff --quiet && git diff --cached --quiet    # committed tip; ignore untracked
```

### Optional squash

For Method A, squash only after its ancestry check. Method B already produces one commit, so do not soft-reset it again. For Method C, squash only when separately requested, after the rebase succeeds and before advancing to the next child; this preserves the rebased tree while replacing that branch's commit series with one commit.

```bash
# Methods A and C only; soft-reset onto parent_tip (origin/<trunk> for i==0):
git merge-base --is-ancestor <parent_tip> HEAD   # MUST exit 0; abort if not
git reset --soft <parent_tip>
git commit -m "<single message for this branch story>"
test "$(git rev-list --count <parent_tip>..HEAD)" -eq 1
```

### Verify no parent reversal

Run only on a **committed** tip (`git diff --quiet && git diff --cached --quiet`):

```bash
git diff --stat <parent_tip>...HEAD | tail -1
git merge-base --is-ancestor <parent_tip> HEAD   # MUST exit 0; else Restore from backup and stop (do not push)
```

Checks (all hard stops):

- Ancestry command exited 0.
- Post-delta magnitude ≈ Phase 0 pre-delta for this link (same order of files/lines).
- Spot-check files only on `<parent_tip>` since `backup_parent` (or trunk) are still present.
- No conflict markers: `git grep -n '^<<<<<<<\|^>>>>>>>' -- .` (ignore prose docs that mention markers).

On failure: **Restore from backup**, stop, do not push.

### Push (gated)

With user approval:

```bash
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
current=$(git branch --show-current)
test "$current" = "<branch>" || { echo "wrong checkout: $current"; exit 1; }
case "<branch>" in
  "$DEFAULT_BRANCH"|"<trunk>"|main|master)
    echo "refusing force-push to trunk/default/integration: <branch>"; exit 1 ;;
esac
git fetch origin <branch>
git push --force-with-lease origin HEAD:<branch>
# or first publish: git push -u origin HEAD:<branch>
# <n> from Phase 0 open PR for this head (skip if none)
gh pr edit <n> --base <parent>    # this skill owns base retarget during restack
```

Never use bare `git push --force` / lease bypasses. If lease rejects, fetch, inspect remote tip, and ask; do not bypass the lease.

Then continue to the next child.

## Phase 2: Report

| Branch | Parent | Method | Squashed? | Old tip | New tip | PR | Base OK? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| … | … | A/B | yes/no | … | … | … | … |

Confirm ancestry for each link. Completion: every link verified; push status reported (pushed / skipped); open PR bases confirmed when PRs exist.

## Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Squash undoes trunk/parent | Soft-reset without absorb | Restore backup; Method A/B first |
| Conflicts on most files after `git merge <parent>` | Parent was squashed; wrong merge-base | Abort; Method B with Phase 0 dated backups |
| Method B selected for trunk-only advance | Wrong method table | Use Method A for `i == 0` |
| Empty post-delta after Method B | Forgot required commit | Commit index; re-verify |
| `--force-with-lease` rejected | Remote moved | Fetch branch; inspect; ask; never bare `--force` |
| Push target is trunk/default | Misordered chain | Refuse; fix chain inputs |
| Parent PR already MERGED | Wrong skill for parent reparenting | Hand off to `github-pr-workflow` `rebase --onto` |

## Anti-patterns

- Soft-resetting the whole stack onto trunk in one step
- Updating the top branch first
- Naive-merging a child after the parent was squashed in the same restack
- Discarding Phase 0 backups before the full chain finishes
- Pushing before no-reversal verification
- Force-pushing `main` / `master`

## Integration Points

### With `github-pr-workflow`

PR admin, `-squashed` branch creation, and post-squash-merge `rebase --onto` stay there. During an open-stack restack, this skill owns `gh pr edit --base`. Use github-pr-workflow only if bases are still wrong afterward.

### With `doing-code-review` / `receiving-review`

History rewrite invalidates prior line anchors. Prefer a fresh review pass after restack if review continuity matters.
