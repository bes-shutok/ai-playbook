---
name: docs-branch
description: >
  Preserve recent review and metrics archives on the local `docs` branch. Use
  standalone to sync archives, or invoke automatically from the done skill.
  Trigger phrases: "save docs", "sync docs branch", "preserve docs".
---

# Docs Branch: Preserve Recent Review and Metrics Archives

## Core Concepts

- **Review and metrics archives**: the only local file roots retained by the docs-branch sync are the fixed `docs/reviews/` root plus the facts-resolved review and metrics roots.
- **Archive snapshot**: The canonical runner reads a single snapshot of the validated review and metrics roots before reconciling the docs branch. It does not snapshot tmp or general repository shadow paths.
- **`docs` orphan branch**: A single permanent local branch that stores the history of recent review and metrics archives across working branches. New docs history has no code parent, and the branch is never pushed.
- **Single-branch invariant**: The shadow history for gitignored docs must live on one branch named exactly `docs`. Branches such as `docs/master` or `docs/<feature>` are incorrect and must be consolidated back into `docs`, not reused.
- **Allowlisted archive invariant**: The local `docs` branch retains only recent files under the fixed `docs/reviews/` root and the facts-resolved review and metrics roots. It drops every excluded or expired branch path while preserving prior commits. Missing recent allowed branch files are restored only after a successful sync; existing local bytes remain untouched. The sync never traverses or deletes local `{tmp_dir}` files. `done` owns the separate `docs-tmp-sweep` lifecycle gate.
- **Sync backend**: `scripts/docs_branch_sync.sh` uses one repository-level temporary-index and `commit-tree` path with compare-and-swap. It does not create a temporary Git worktree or select a backend from `worktree_policy`.

## Documentation paths

Read the opening TOML block in `.ai-playbook/facts.md` before syncing. The archive roots are the fixed `docs/reviews/` root, `reviews_dir` or its default `.ai-playbook/reviews/`, and `metrics_dir` or its default `.ai-playbook/metrics/`. The canonical runner validates every configured and resolved root before walking an archive or reading the `docs` ref. Empty, malformed, broad, wrong-role, cross-role-overlapping, absolute, dot, parent, outside `docs/` or the `.ai-playbook/` audit home, or escaped roots refuse the sync.

A symlink at fixed `docs/reviews/` may alias the configured review root; the runner resolves and visits that target once. Symlinks below an archive root must stay within that root. The docs branch keeps only files under the resolved review and metrics roots. It excludes `docs/tmp/`, plans, backlog, runtime configuration, and other paths, including when those files are absent locally. Pruning the branch never deletes local source files.

The runner uses the latest committer timestamp that changed each existing archive path on `refs/heads/docs`. It prunes paths strictly older than two UTC calendar months, clamping month ends. A recent source with unchanged historical bytes does not renew an expired path; recent changed bytes can renew it, and a recent new archive path can be added. Recent allowed branch-only files are restored only after a successful sync, and existing local bytes are never overwritten.

## Related

- **`done`** invokes this skill through its commit run, after the one landing sweep gates the staged set. The runner holds the repository merge lock inside its own process for each mutation (the sync and the drift-witness append; the runner-owned span, released in an always-run finally before the runner returns), so no caller-side lock management exists.
- **`plans`** owns plan lifetime and cleanup under `{tmp_dir}`; this skill does not discover or sweep local tmp files.

## When to Use

- Called from the `done` skill's commit run after the landing sweep.
- Run standalone to save recent review and metrics archives to the local `docs` branch.

## Step 2: Sync to the `docs` branch

Run the canonical sync entry point from the target repository root as one command:

```bash
bash scripts/docs_branch_sync.sh
```

The runner uses one repository-level `commit-tree` backend with a temporary index and compare-and-swap, regardless of `worktree_policy`. If another writer moved the docs ref, the sync refuses and leaves the competing tip current; it restores no branch-only files. This backend preserves the active checkout and index, keeps earlier docs commits reachable, and never pushes. The runner restores only recent allowed branch-only archives after the branch update succeeds. It does not remove, sweep, or rewrite local `docs/tmp/` files. `done` retains its separate `docs-tmp-sweep` gate for plan-lifetime and one-off scratch cleanup.

The runner prints any pruned branch paths (including paths absent from the checkout) and the final outcome. Root validation and symlink containment failures stop before docs-branch ref mutation.

## Step 3: Lesson-Scope Drift Witness Append

When the caller holds a lesson-scope-audit drift witness line (from done Step 3 item 4a) for a corpus whose path is gitignored, the docs-branch-only path has no `done` Step 3 corpus commit to carry the line, so this step lands it as the body of an append-only empty commit on the docs branch.

Contract: the caller passes the exact witness line as the single argument; the line must start with lesson-scope-audit: (fail loud otherwise). The caller owns the witness line text (done owns the content, docs-branch the append mechanics, per the integration point below); this skill defines no canonical line. Invoke the append from the audited project repository root; the skill does not resolve or verify the root (the docs-branch refusal only guards the current repo).

The append creates an empty commit parented to the observed docs tip and publishes it with compare-and-swap. If another writer moves the ref first, the append does not overwrite that tip; it preserves the witness commit under `refs/docs-witness-recovery/` and reports the retry path. A missing docs branch means no archive sync has established local history, so the append refuses rather than overstate coverage.

Run the canonical runner from the audited repository root. It serializes with ordinary syncs, rejects symbolic docs refs, and preserves a failed compare-and-swap under a direct recovery ref. Never push; the docs branch stays a local safety net per this skill's Rules:

```bash
test "$#" -eq 1 || { echo "usage: provide one lesson-scope-audit witness line" >&2; exit 2; }
bash scripts/docs_branch_sync.sh --append-witness "$1"
```

The witness line is byte-for-byte identical to the `done` Step 3 corpus-commit body line so one audit-note grep pattern covers both carriers.

## Recovery: Restoring a Missing Archive File

After a manual branch switch, restore only the specific recent review or metrics file you need from `refs/heads/docs`. Resolve its archive root from `.ai-playbook/facts.md` first. Do not restore `docs/`, `docs/tmp/`, plans, or unrelated branch paths.

```bash
# Restore one allowed archive file to the worktree without changing the index.
git restore --source refs/heads/docs --worktree -- <allowed-review-or-metrics-path>
```

Then run the canonical sync entry point to reconcile the allowed archive roots.

### Last-resort: searching historical git stash entries

Older versions of this workflow used `git stash push --all`. That command stores gitignored files in the stash's **third parent** (`stash@{N}^3`). If gitignored files are missing after an old run, inspect stash entries before assuming permanent loss:

```bash
# List gitignored files stored in each stash entry (requires --all stash)
git ls-tree -r --name-only stash@{0}^3
git ls-tree -r --name-only stash@{1}^3

# Extract a specific file from a stash entry
git show stash@{0}^3:.ai-playbook/reviews/my-file.md > .ai-playbook/reviews/my-file.md
```

This only works when an old `git stash push --all` run happened after the files were created. Stash entries that predate the file's creation contain nothing.

## Rules

- Keep the shadow history on one local branch named exactly `docs`. Consolidate any `refs/heads/docs/*` branches before syncing.
- Run `bash scripts/docs_branch_sync.sh` from the repository root. Do not copy or recreate sync logic in a skill fence or another script.
- The runner archives only the fixed `docs/reviews/` root and the validated review and metrics roots from facts. It prunes excluded and expired branch paths while keeping prior docs commits reachable.
- Do not pass or discover `{tmp_dir}` or any other shadow root as a sync candidate. The runner never reads, removes, or rewrites local tmp files. `done` retains its separate `docs-tmp-sweep` gate.
- Preserve local archive files. Restore only recent branch-only review or metrics files, only after a successful branch update, and never overwrite a path already present locally.
- Keep the active checkout and index in place. Use compare-and-swap for the docs ref and do not restore branch-only files after a failed update.
- Never push the docs branch or switch the active checkout to it. Never run whole-repository `git clean` or `git stash clear` during sync.
- Never use `git stash push --all` or `git stash apply` for gitignored files; stash operations can remove ignored content or restore only empty directories.
- Preserve earlier docs commits when pruning the current tree. Report each removed branch path, including paths absent from the checkout.

## Integration Points

### With `done` and `plans` skills (docs/tmp sweep)
The done landing sweep's `docs-tmp-sweep` gate and `plans` **Plan Lifecycle** own local `{tmp_dir}` cleanup. The docs-branch runner excludes tmp and leaves local tmp bytes untouched.

### With `done` (drift witness)
done Step 3 items 4a and 6 invoke this step's witness append when the audited corpus is gitignored; docs-branch owns the append mechanics, done owns the witness line text.
