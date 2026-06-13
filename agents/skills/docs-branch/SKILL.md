---
name: docs-branch
description: Preserve gitignored LLM docs and instruction files by stashing them and syncing to a permanent orphan `docs` branch. Use standalone when you need to save docs without a full done/commit cycle, or invoked automatically from the done skill. Trigger phrases — "save docs", "sync docs branch", "preserve docs".
---

# Docs Branch — Preserve Gitignored Docs and Instructions

## Core Concepts

- **Gitignored LLM artifacts**: `docs/`, `.github/docs/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md` — files that provide LLM context but are excluded from the main working branch via `.gitignore` to avoid polluting the code history. On branches where committing `.gitignore` is not allowed (e.g. during a code review), add them to `.git/info/exclude` instead — a local-only ignore that requires no commit and is respected by `git check-ignore`.
- **Stash backup**: A `git stash` entry named `"docs and instructions"` that acts as a secondary backup layer. Files are pre-snapshotted to `PRESTASH_TMP` before stashing and restored from there — never via `git stash apply`, which is unreliable for ignored files.
- **`docs` orphan branch**: A single permanent local branch with no code history that stores the full history of all gitignored doc changes across all feature branches. Never pushed to remote.
- **Single-branch invariant**: The shadow history for gitignored docs must live on one branch named exactly `docs`. Branches such as `docs/master` or `docs/<feature>` are incorrect and must be consolidated back into `docs`, not reused.
- **`RESTORE_TMP`**: A temp directory snapshot taken before any branch switch, used as the reliable restore mechanism when returning to the working branch.

## Documentation paths

Resolve gitignored doc roots by invoking the `resolve-vars` skill at task start (`{reviews_dir}`, `{tmp_dir}`, etc.) **before** running the scripts below. Build candidate path lists from session resolution; do not rely on the hardcoded fallbacks when resolved paths are known.

```bash
# After doc-paths resolution — set REVIEWS_DIR and TMP_DIR from {reviews_dir} and {tmp_dir}
SHADOW_CANDIDATES=(docs/ .github/docs/ docs/personal/ AGENTS.md CLAUDE.md GEMINI.md COPILOT.md)
[ -n "${REVIEWS_DIR:-}" ] && SHADOW_CANDIDATES+=("${REVIEWS_DIR%/}/")
[ -n "${TMP_DIR:-}" ] && SHADOW_CANDIDATES+=("${TMP_DIR%/}/")
# Fallback only when resolution was not run
[ -z "${REVIEWS_DIR:-}" ] && SHADOW_CANDIDATES+=(docs/reviews/ docs/history/reviews/)
[ -z "${TMP_DIR:-}" ] && SHADOW_CANDIDATES+=(docs/tmp/)
```

The `STASH_ARGS` and `SHADOW_PATHS` loops below use `SHADOW_CANDIDATES` instead of a fixed dual-layout list.

## Related

- [`doc-hierarchy`](../doc-hierarchy/SKILL.md) — company service documentation hierarchy schema
- [`doc-hierarchy-migrate`](../doc-hierarchy-migrate/SKILL.md) — migration workflow (references this skill for gitignored doc preservation)
- [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md) — Layer 1/2 upkeep after migration
- [`resolve-vars`](../resolve-vars/SKILL.md) — path discovery and persistence (`{reviews_dir}`, `{tmp_dir}`, etc.)
- `done` — invokes this skill automatically before committing

## When to Use

- Called from the `done` skill as Step 2 (before committing).
- Standalone when you only need to sync docs to the `docs` branch (e.g., after a big doc update mid-session).
- When restoring missing docs after a branch switch wiped them.

## Step 1: Stash Gitignored Docs and Instructions

Stash all gitignored LLM artifact paths so they survive branch switches. Only include paths that actually exist to avoid a fatal `pathspec did not match` error.

> **Important:** `git stash push --all` removes gitignored files from disk, and `git stash apply` may restore them as empty directories rather than re-populating their content (a known git behaviour for ignored files). To avoid this, we snapshot the files into a temp directory **before** stashing and restore from that snapshot after — never relying on `git stash apply` to put the files back.

```bash
STASH_ARGS=()
PRESTASH_TMP=$(mktemp -d)
# Build SHADOW_CANDIDATES per Documentation paths section above
for p in "${SHADOW_CANDIDATES[@]}"; do
  clean="${p%/}"
  if [ -e "$clean" ] && git check-ignore -q "$clean"; then
    STASH_ARGS+=("$p")
    parent=$(dirname "$clean")
    mkdir -p "${PRESTASH_TMP}/${parent}"
    cp -rp "$clean" "${PRESTASH_TMP}/${parent}/"
  fi
done
[ -e ".claude" ] && STASH_ARGS+=(".claude/")
if [ ${#STASH_ARGS[@]} -gt 0 ]; then
  git stash push --all -m "docs and instructions" -- "${STASH_ARGS[@]}"
  # Restore from our own snapshot — git stash apply is unreliable for ignored files
  # (may create empty directories instead of fully restoring them).
  for p in "${STASH_ARGS[@]}"; do
    clean="${p%/}"
    parent=$(dirname "$clean")
    if [ -e "${PRESTASH_TMP}/${clean}" ]; then
      mkdir -p "./${parent}"
      rm -rf "./${clean}"
      cp -rp "${PRESTASH_TMP}/${clean}" "./${parent}/"
    fi
  done
fi
rm -rf "${PRESTASH_TMP}"
```

## Step 2: Sync to the `docs` Branch

Create or update the single `docs` branch only when at least one of the candidate paths is both present on disk and gitignored. Skip entirely when the only ignored path is `.claude/` or another local agent config directory — those stay protected by the stash only.

A single permanent `docs` branch is used regardless of which feature branch is active, keeping the full doc history in one place without per-branch fragmentation. Create it as an **orphan** on first use so it carries no code history.

If the repository already contains any `docs/...` branches, stop and consolidate them into the single `docs` branch before continuing. Do not route new updates into `docs/master`, `docs/<feature>`, or any other namespaced variant.

> **Critical:** Run this entire script as a **single bash invocation**. Shell variables (especially `RESTORE_TMP`) do not persist between separate tool calls. Splitting the snapshot → checkout → restore sequence across calls causes `RESTORE_TMP` to be empty in later calls, silently deleting files without restoring them. Do not run the script under zsh: `path` is a special zsh variable tied to `PATH`, so the `for path in ...` loops below can break command lookup mid-script.

> **Silent failure risk:** If a candidate file (e.g. `AGENTS.md`) is present on disk as an untracked but **not** gitignored file, `git check-ignore -q` returns failure and it is excluded from `SHADOW_PATHS`. However, `git checkout docs` will still fail with "untracked working tree files would be overwritten". Because the script does not use `set -e`, it continues silently and any subsequent `git commit` lands on the working branch instead of `docs`. **Prevention:** ensure all candidate files are gitignored before running this script — add them to `.git/info/exclude` if you cannot commit `.gitignore` changes.

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
DOCS_BRANCH="docs"

SHADOW_PATHS=()
for path in "${SHADOW_CANDIDATES[@]}"; do
  if [ -e "${path%/}" ] && git check-ignore -q "${path%/}"; then
    SHADOW_PATHS+=("$path")
  fi
done

if [ ${#SHADOW_PATHS[@]} -gt 0 ]; then
  # Snapshot shadow paths AND .gitignore to a temp dir BEFORE any branch switch.
  # git checkout removes files that are tracked on the docs branch but gitignored on the
  # current branch, so we cannot rely on git restore to bring them back reliably.
  # .gitignore is always included because it defines which files the shadow branch
  # preserves; any additions to .gitignore on the working branch must be reflected in
  # the shadow branch or it will silently fall out of sync.
  RESTORE_TMP=$(mktemp -d)
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    src="${shadow_path%/}"  # strip trailing slash so cp -rp copies the item itself
    if [ -e "$src" ]; then
      parent=$(dirname "$src")
      mkdir -p "${RESTORE_TMP}/${parent}"
      cp -rp "$src" "${RESTORE_TMP}/${parent}/"
    fi
  done
  [ -e ".gitignore" ] && cp ".gitignore" "${RESTORE_TMP}/.gitignore"

  # Stash uncommitted tracked changes so they don't block 'git checkout docs'.
  # Regular 'git stash push' (no --all) covers only tracked files, leaving gitignored
  # files untouched. Skip if the working tree is already clean.
  _TRACKED_STASH_CREATED=0
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git stash push -m "docs-branch: temp tracked stash"
    _TRACKED_STASH_CREATED=1
  fi

  if git for-each-ref --format='%(refname)' 'refs/heads/docs/*' | grep -q .; then
    echo "ERROR: found invalid docs/* branches; consolidate them into refs/heads/docs first" >&2
    exit 1
  fi

  # Switch to docs branch using -f (force) — never pre-delete shadow paths from disk.
  # Pre-deleting creates a dangerous window: if the checkout or restore later fails,
  # the files are permanently gone. Force-checkout lets git handle any working-tree
  # conflicts atomically; RESTORE_TMP was already snapshotted above and will overwrite
  # whatever git puts on disk, so no data from the working branch is lost.
  if git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}"; then
    git checkout -f "${DOCS_BRANCH}"
  else
    git checkout --orphan "${DOCS_BRANCH}"
    # Use --cached (index only) to avoid hanging on submodule directories (e.g. common/).
    # Then git clean removes all remaining untracked project files from the working tree
    # so that `git checkout -f ${CURRENT_BRANCH}` does not fail with "untracked files
    # would be overwritten". Shadow paths are still on disk and safe in RESTORE_TMP.
    git rm --cached -r . --quiet 2>/dev/null || true
    git clean -fdq 2>/dev/null || true
  fi

  # Sync .gitignore from the working branch, then strip any rules that exclude the
  # paths this branch exists to track. Use grep -vE (reliable on macOS and Linux).
  if [ -e "${RESTORE_TMP}/.gitignore" ]; then
    grep -vE '^/?\.?github/docs/?$|^/docs/?$|^/AGENTS\.md$|^/CLAUDE\.md$|^/GEMINI\.md$|^/COPILOT\.md$|^AGENTS\.md$|^GEMINI\.md$|^CLAUDE\.md$|^/?docs/personal/?$|^/?docs/tmp/?$|^/?docs/reviews/?$|^/?docs/history/reviews/?$' "${RESTORE_TMP}/.gitignore" > ./.gitignore || true
  fi
  git add .gitignore 2>/dev/null || true

  # Copy snapshot content into the shadow branch working tree BEFORE staging.
  # Must delete the destination first: if the directory already exists,
  # `cp -rp src dst` copies src INSIDE dst (creating dst/src/), causing nesting.
  # For nested paths (e.g. docs/personal/), ensure parent dir exists first.
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    src="${shadow_path%/}"
    parent=$(dirname "$src")
    mkdir -p "./${parent}"
    rm -rf "./${src}"
    cp -rp "${RESTORE_TMP}/${src}" "./${parent}/"
  done

  # Stage docs/instructions — use -f to bypass any .git/info/exclude rules that
  # shadow paths from the working branch; .gitignore rules for these paths were
  # already stripped above when switching to the docs branch.
  # First strip any nested .git dirs — nested git repos (e.g. docs/personal/) must
  # not be staged as submodule gitlinks; removing .git lets individual files be staged.
  find . -mindepth 2 -name '.git' -type d | while read -r d; do rm -rf "$d"; done
  for path in "${SHADOW_PATHS[@]}"; do
    git add -f "$path" 2>/dev/null || true
  done

  # Commit only if there are staged changes; include source branch for traceability.
  if ! git diff --cached --quiet; then
    git commit -m "docs: update from ${CURRENT_BRANCH}"
  fi

  # Return to the original branch with -f so any docs-branch tracked files that are
  # gitignored on the working branch don't block the checkout. The cp restore below
  # immediately brings them back from RESTORE_TMP.
  git checkout -f "${CURRENT_BRANCH}"

  # Restore tracked changes that were stashed before the branch switch.
  if [ "${_TRACKED_STASH_CREATED}" = "1" ]; then
    git stash pop
  fi

  # Restore shadow paths from the pre-switch snapshot (reliable, no git involvement).
  # Delete destination first to prevent nesting (cp -rp src dst copies src INSIDE dst
  # if dst already exists). For nested paths, ensure parent dir exists first.
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    src="${shadow_path%/}"
    parent=$(dirname "$src")
    mkdir -p "./${parent}"
    rm -rf "./${src}"
    [ -e "${RESTORE_TMP}/${src}" ] && cp -rp "${RESTORE_TMP}/${src}" "./${parent}/"
  done
  rm -rf "${RESTORE_TMP}"

  # Guard: if a SHADOW_PATH is also a directory tracked on the working branch (e.g. docs/),
  # the cp restore above may overwrite tracked files inside it with stale docs-branch content.
  # Scope the guard to only the tracked files within each SHADOW_PATH — never restore
  # AGENTS.md, CLAUDE.md, or other tracked files outside the SHADOW_PATHS from HEAD, as
  # that would revert uncommitted changes that were correctly restored by git stash pop above.
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    src="${shadow_path%/}"
    git ls-files -- "$src" | while read -r f; do git checkout HEAD -- "$f" 2>/dev/null || true; done
  done
fi
```

> **Note:** When `docs/` is also a directory on the working branch, `git log --oneline docs` is ambiguous. Always use `git log --oneline refs/heads/docs --` to reference the branch unambiguously.

## Recovery: Restoring Missing Gitignored Files

Any manual `git checkout docs` (for history inspection, rebase, or reset) followed by `git checkout <feature-branch>` **will remove** `docs/`, `AGENTS.md`, `CLAUDE.md` and other gitignored files from disk. Git removes files that were tracked on the previous branch even when they are gitignored on the new branch.

To restore after a manual branch switch:

```bash
# Restore from the docs branch without switching to it
git checkout refs/heads/docs -- docs/ AGENTS.md CLAUDE.md
# Unstage — these files must NOT be committed on the feature branch
git restore --staged docs/ AGENTS.md CLAUDE.md
```

Then run the full docs-branch skill (Step 1 + Step 2) to re-sync any pending changes.

### Last-resort: searching git stash for gitignored files

`git stash push --all` stores gitignored files in the stash's **third parent** (`stash@{N}^3`). If gitignored files are missing and no `RESTORE_TMP` or `PRESTASH_TMP` snapshot exists, inspect stash entries before assuming permanent loss:

```bash
# List gitignored files stored in each stash entry (requires --all stash)
git ls-tree -r --name-only stash@{0}^3
git ls-tree -r --name-only stash@{1}^3

# Extract a specific file from a stash entry
git show stash@{0}^3:docs/tmp/my-file.md > docs/tmp/my-file.md
```

This only works when a `git stash push --all` was run after the files were created. Stash entries that predate the file's creation contain nothing; the files are unrecoverable from stash in that case.

## Rules

- Never use `docs/master`, `docs/<feature>`, or any other `docs/...` shadow branches. The only valid shadow branch name is exactly `docs`.
- If any `refs/heads/docs/*` branches already exist, consolidate them into the single `docs` branch and delete the namespaced branches before the next sync. Do not keep using them as a workaround.
- **Before running this skill, verify all candidate files are gitignored** (`git check-ignore -q <file>`). If a file is untracked but not gitignored, `git checkout docs` will fail with "untracked working tree files would be overwritten". Because the script has no `set -e`, it continues silently and any commit lands on the wrong branch. Fix: add the file to `.git/info/exclude` (local-only, no commit needed) before running the skill.
- Before switching to the `docs` branch, always stash uncommitted tracked changes (`git stash push`) and pop them after returning — dirty tracked files block checkout even with `-f` for staged changes.
- Run Step 2's script as a **single bash invocation** — never split across tool calls and never run it under zsh.
- The `docs` branch is **never pushed to remote** — local safety net only.
- Create the `docs` branch as an **orphan** when it does not yet exist.
- **Never** include `.claude/` (or similar local config dirs) in `SHADOW_PATHS` — they trigger the stash only, not the branch.
- Before staging on the `docs` branch, always strip LLM artifact gitignore rules from `.gitignore` so the branch can track its own files. Use `git add -f` when staging to also bypass any `.git/info/exclude` rules that may block adding gitignored paths.
- After returning to the working branch, always restore from `RESTORE_TMP` — never rely on `git restore` for gitignored files after a branch switch.
- **Never use `git stash apply` to restore gitignored files** — git may restore the directory entry but leave it empty. Always restore from the `PRESTASH_TMP` snapshot taken in Step 1, which is a plain `cp -rp` copy made before the stash push.
- **Never run `git stash clear`** in repos using this workflow — stash entries are the secondary backup layer alongside the `docs` branch.
- **Never pre-delete shadow paths from disk before the branch switch.** Pre-deleting creates an unrecoverable window: if the checkout or restore step fails, the files are gone permanently. Use `git checkout -f` instead — force-checkout handles working-tree conflicts atomically and RESTORE_TMP overwrites whatever git places on disk.
- **Nested git repos in SHADOW_PATHS** (e.g. `docs/personal/`): strip their `.git` before staging on the docs branch (`find . -mindepth 2 -name '.git' -type d | while read -r d; do rm -rf "$d"; done`). Without this, git treats them as submodule gitlinks and does not stage individual files. The nested `.git` is NOT present in `RESTORE_TMP` either way since `cp -rp` copies it but the docs branch never needs it.
- **Snapshot/restore path correctness is data-loss critical**: `cp -rp docs/foo RESTORE_TMP/` creates `RESTORE_TMP/foo/` (just the basename), NOT `RESTORE_TMP/docs/foo/`. Use the parent-preserving pattern everywhere: `parent=$(dirname "$src"); mkdir -p "${RESTORE_TMP}/${parent}"; cp -rp "$src" "${RESTORE_TMP}/${parent}/"`. If the snapshot path doesn't match the restore path, the restore silently fails and the file is lost. When adding a new path to SHADOW_PATHS, echo-test the snapshot/restore paths before running the script for real.
- **Scope the post-restore guard to SHADOW_PATHS only.** The guard that restores tracked files from HEAD must iterate only the tracked files _within_ each SHADOW_PATH — never restore AGENTS.md, CLAUDE.md, or other tracked files outside SHADOW_PATHS from HEAD. A broad guard (`git ls-files -- docs/ AGENTS.md CLAUDE.md`) reverts uncommitted changes that `git stash pop` correctly restored, silently losing work.
