---
name: docs-branch
description: >
  Preserve gitignored LLM docs and instruction files by stashing them and syncing
  to a permanent orphan `docs` branch. Use standalone when you need to save docs
  without a full done/commit cycle, or invoked automatically from the done skill.
  Trigger phrases: "save docs", "sync docs branch", "preserve docs".
---

# Docs Branch: Preserve Gitignored Docs and Instructions

## Core Concepts

- **Gitignored LLM artifacts**: `docs/`, `.github/docs/`, `/.ai-playbook/` (repo root only), `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT.md`: files that provide LLM context but are excluded from the main working branch via `.gitignore` to avoid polluting the code history. **Default:** add `/.ai-playbook/` to repo `.gitignore` (see `bootstrap-ai-playbook` skill). Use `.git/info/exclude` only when `.gitignore` cannot be committed (for example during a code review on a branch that cannot touch `.gitignore`).
- **Snapshot backup**: A plain temp-directory copy of shadow paths, taken before syncing. Never use `git stash push --all` for ignored shadow files because it removes them from disk.
- **`docs` orphan branch**: A single permanent local branch with no code history that stores the full history of all gitignored doc changes across all feature branches. Never pushed to remote.
- **Single-branch invariant**: The shadow history for gitignored docs must live on one branch named exactly `docs`. Branches such as `docs/master` or `docs/<feature>` are incorrect and must be consolidated back into `docs`, not reused.
- **Add-only sync invariant**: The `docs` branch sync never treats a missing on-disk file as a deletion. Sync adds or updates paths present on disk only. Paths tracked on `refs/heads/docs` but absent from disk are restored from that branch before sync (unless the path was explicitly deleted in the latest `docs` commit). Review directories (`{reviews_dir}` and fallbacks such as `docs/reviews/`, `docs/history/reviews/`) always follow this rule. **tmp sweep exception:** `{tmp_dir}` (fallback `docs/tmp/`) is the ONE sweep-eligible root: a path under it that is tracked on the branch, absent on disk, not explicitly deleted, not staged for deletion or rename in the live index, and still gitignored (committed tmp paths are restored like any other branch-tracked content) is DROPPED from the branch (staged as a deletion) instead of restored, because `{tmp_dir}` is scratch with plan lifetime (see the pre-docs sweep gate run's docs-tmp-sweep gate and `plans` **Plan Lifecycle** docs/tmp cleanup). Every other root, review directories above all, stays strictly add-only.
- **Temporary docs worktree**: A separate `git worktree` used for all `docs` branch operations. The live project checkout stays on the user's working branch and is only read from.

## Documentation paths

Read `{reviews_dir}`, `{tmp_dir}`, and related path keys from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0) **before** running the scripts below. Build candidate path lists from those values; do not rely on the hardcoded fallbacks when TOML keys are present.

A repo may also declare **extra shadow dirs** it wants preserved on the `docs` branch that are not under the standard `docs` tree (for example a personal-data directory like `resources/source/`). Set the optional `extra_shadow_dirs` TOML array in `.ai-playbook/facts.md` to a list of repo-relative paths. Entries may be gitignored files/directories or a container directory whose contents are ignored by rules such as `resources/source/*`; the sync treats `extra_shadow_dirs` as explicit preservation roots.

```bash
# After reading .ai-playbook/facts.md TOML: set REVIEWS_DIR and TMP_DIR from {reviews_dir} and {tmp_dir}
SHADOW_CANDIDATES=(docs/ .github/docs/ docs/personal/ .ai-playbook/ AGENTS.md CLAUDE.md GEMINI.md COPILOT.md)
[ -n "${REVIEWS_DIR:-}" ] && SHADOW_CANDIDATES+=("${REVIEWS_DIR%/}/")
[ -n "${TMP_DIR:-}" ] && SHADOW_CANDIDATES+=("${TMP_DIR%/}/")
# Fallback only when resolution was not run
[ -z "${REVIEWS_DIR:-}" ] && SHADOW_CANDIDATES+=(docs/reviews/ docs/history/reviews/)
[ -z "${TMP_DIR:-}" ] && SHADOW_CANDIDATES+=(docs/tmp/)
EXTRA_SHADOW_DIRS=()

docs_branch_add_shadow_candidate() {
  _candidate="$1"
  [ -n "$_candidate" ] || return 0
  for _existing in "${SHADOW_CANDIDATES[@]}"; do
    [ "$_existing" = "$_candidate" ] && return 0
  done
  SHADOW_CANDIDATES+=("$_candidate")
  EXTRA_SHADOW_DIRS+=("$_candidate")
}

# Coverage-scoped descendant-ignored candidate probe. Arms in order:
# (1) bare check-ignore: the ignore rule matches the candidate path itself;
# (2) tracked-content gate: a candidate with any tracked file under it never
#     takes the fallback, so tracked wholesale roots keep today's inclusion
#     paths and the fallback can never newly stage tracked content;
# (3) descendant-ignored fallback for untracked candidates whose ignore
#     coverage lives only in descendants (rules such as docs/history/reviews/**
#     match children but not the candidate path): the fixed-string needle
#     matches the collapsed candidate entry and strict descendants only, and
#     its trailing slash rejects collapsed ancestors and prefix-siblings.
docs_branch_candidate_ignored() {
  git check-ignore -q "$1" && return 0
  git ls-files --error-unmatch -- "$1" >/dev/null 2>&1 && return 1
  git ls-files --others --ignored --exclude-standard --directory -- "$1/" | grep -qF -e "$1/"
}

docs_branch_append_extra_shadow_dirs_from_facts() {
  _facts_file="$1"
  [ -f "$_facts_file" ] || return 0
  # F3: fence string built via sprintf so this code block contains no literal triple backticks (keeps the block extractable from SKILL.md)
  _extra_raw=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^extra_shadow_dirs[[:space:]]*=/{sub(/^extra_shadow_dirs[[:space:]]*=[[:space:]]*\[/,""); sub(/\].*$/,""); print; exit}' "$_facts_file")
  if [ -n "$_extra_raw" ]; then
    while IFS= read -r _item; do
      [ -n "$_item" ] || continue
      docs_branch_add_shadow_candidate "$_item"
    done <<EOF
$(printf '%s' "$_extra_raw" | tr ',' '\n' | sed "s/^[[:space:]]*//; s/[[:space:]]*$//; s/^['\"]//; s/['\"]$//")
EOF
  fi
  unset _facts_file _extra_raw _item
}

# Optional extra_shadow_dirs TOML array: additional repo-relative gitignored paths to preserve.
# Parse both live facts and the docs branch facts so a stale live facts file cannot
# silently drop already-configured shadow paths from future syncs.
docs_branch_append_extra_shadow_dirs_from_facts .ai-playbook/facts.md
if git show "refs/heads/docs:.ai-playbook/facts.md" >/tmp/docs-branch-facts.$$ 2>/dev/null; then
  docs_branch_append_extra_shadow_dirs_from_facts /tmp/docs-branch-facts.$$
  rm -f /tmp/docs-branch-facts.$$
fi
if [ -f /tmp/docs-branch-facts.$$ ]; then
  rm -f /tmp/docs-branch-facts.$$
fi
unset _candidate _existing
```

The `SNAPSHOT_PATHS` and `SHADOW_PATHS` loops below use `SHADOW_CANDIDATES` instead of a fixed dual-layout list.

## Related

- [`doc-hierarchy`](../doc-hierarchy/SKILL.md): company service documentation hierarchy schema
- [`doc-hierarchy-migrate`](../doc-hierarchy-migrate/SKILL.md): migration workflow (references this skill for gitignored doc preservation)
- [`doc-hierarchy-upkeep`](../doc-hierarchy-upkeep/SKILL.md): Layer 1/2 upkeep after migration
- [`bootstrap-ai-playbook`](../bootstrap-ai-playbook/SKILL.md): writes `.ai-playbook/facts.md`; path keys read via `using-skills` Step 0
- `done`: invokes this skill automatically before committing
- [`confluence-page-sync`](../confluence-page-sync/SKILL.md): owns wiki page republish and stored-HTML verification; route republish work there (never edit Confluence pages during a docs sync)

## When to Use

- Called from the `done` skill as Step 2 (before committing).
- Standalone when you only need to sync docs to the `docs` branch (e.g., after a big doc update mid-session).
- When restoring missing docs after a branch switch wiped them.

## Step 1: Snapshot Gitignored Docs and Instructions

Snapshot all gitignored LLM artifact paths before syncing them to the `docs` branch. Only include paths that actually exist to avoid a fatal `pathspec did not match` error.

> **Important:** Do not use `git stash push --all` for this workflow. It removes gitignored files from disk, and an interruption before restore can leave content missing. The live checkout must remain on the user's working branch and must only be read from.

```bash
SNAPSHOT_TMP=$(mktemp -d)
SNAPSHOT_PATHS=()
# Fences run as separate tool calls and do not share variables; define the
# docs-branch name here (Step 2 assigns the same value in its own fence).
DOCS_BRANCH="docs"
# Build SHADOW_CANDIDATES per Documentation paths section above
for p in "${SHADOW_CANDIDATES[@]}"; do
  clean="${p%/}"
  if [ -e "$clean" ] && docs_branch_candidate_ignored "$clean"; then
    SNAPSHOT_PATHS+=("$p")
    parent=$(dirname "$clean")
    mkdir -p "${SNAPSHOT_TMP}/${parent}"
    cp -Rp "$clean" "${SNAPSHOT_TMP}/${parent}/"
  elif [ -e "$clean" ] && ! git ls-files --error-unmatch -- "$clean" >/dev/null 2>&1 && \
       ! git ls-tree -r --name-only "refs/heads/${DOCS_BRANCH}" -- "$clean" 2>/dev/null | grep -q .; then
    # Loud skip: the candidate is still never staged (skip semantics unchanged),
    # but lost ignore coverage must name itself instead of vanishing quietly.
    # The arm fires only for true zero coverage: the helper returned nonzero, the
    # candidate is disk-only (no tracked content under it; ignore-else-track keeps
    # tracked candidates silent), and the docs-branch tree does not track it
    # either (a branch-tracked candidate is wholesale-synced by Step 2's mirror
    # arm, so warning it would be false).
    echo "docs-branch: shadow candidate '$clean' exists but is not gitignored (zero ignore coverage: git check-ignore rejects the path and no rule covers anything under it). Add the ignore rule to .gitignore, or add it to .git/info/exclude as the local-only fallback when .gitignore cannot be committed, or set the extra_shadow_dirs facts key when this is an extra shadow root whose ignore coverage drifted, or correct the facts reviews_dir/tmp_dir key, then re-run." >&2
  elif [ -e "$clean" ] && \
       git ls-files --error-unmatch -- "$clean" >/dev/null 2>&1 && \
       git ls-files --others --exclude-standard -- "$clean" | grep -q . && \
       ! git ls-tree -r --name-only "refs/heads/${DOCS_BRANCH}" -- "$clean" 2>/dev/null | grep -q .; then
    # Partially tracked: the candidate holds tracked content (ignore-else-track
    # keeps it out of the shadow, unchanged) alongside untracked content nothing
    # will sync: the candidate is absent from the docs-branch tree, so Step 2's
    # mirror arm never wholesale-copies it and its untracked remainder would
    # vanish unnamed. Warning only; no inclusion change.
    echo "docs-branch: shadow candidate '$clean' contains both tracked and untracked files but is not tracked on the docs branch; the untracked files inside are NOT shadowed and will not reach the docs branch." >&2
  fi
done
[ -e ".claude" ] && SNAPSHOT_PATHS+=(".claude/")
rm -rf "${SNAPSHOT_TMP}"
```

A candidate with zero ignore coverage at any level, no tracked content under it, and no docs-branch presence is skipped with the loud warning above, never a silent skip, because the reviews-dir shadow is the only durable copy of review records and lost ignore coverage must name itself. A candidate whose ignore coverage lives only in descendants (rule shapes that match children but not the candidate path itself) is included by the fallback probe (untracked roots only; the tracked-content gate keeps tracked wholesale roots on their existing inclusion paths). A candidate already tracked on the docs branch is re-included by Step 2's mirror arm (branch continuity) and wholesale-synced. Tracked candidates keep ignore-else-track unchanged (tracked content is product content, not a shadow target), and never-tracked unignored content inside a tracked, unbranched candidate is named by the partial-track warning above rather than lost unnamed.

## Step 1.5: Preserve Active Execute-Plan Session Logs (when present)

When `{tmp_dir}/execute-plan/<plan-slug>/` exists with `manifest.md`, Step 2 includes it in the shadow snapshot without replacing the live `docs/tmp/` directory. **This logic is integrated into the Step 2 script below** (do not run Step 1.5 as a separate tool call).

Reference (for reading only, use Step 2 script):

```bash
# EXECUTE_PLAN_BACKUP cleanup runs inside Step 2 after SHADOW_PATHS is built.
```

## Step 2: Sync to the `docs` Branch

Create or update the single `docs` branch only when at least one of the candidate paths is both present on disk and gitignored; descendant-only ignore coverage counts for untracked roots (a rule that matches only the root's children, such as `docs/history/reviews/**`, qualifies through the shared candidate probe's descendant-ignored fallback). Skip entirely when the only ignored path is `.claude/` or another local agent config directory, those stay local-only.

A single permanent `docs` branch is used regardless of which feature branch is active, keeping the full doc history in one place without per-branch fragmentation. Create it as an **orphan** on first use so it carries no code history.

If the repository already contains any `docs/...` branches, stop and consolidate them into the single `docs` branch before continuing. Do not route new updates into `docs/master`, `docs/<feature>`, or any other namespaced variant.

> **Critical:** Run this entire script as a **single shell invocation**. Shell variables (especially `SHADOW_TMP` and `DOCS_WORKTREE`) do not persist between separate tool calls. Do not use `path` as a loop variable: in zsh it is a special array tied to `PATH` and breaks command lookup mid-script.

> **Target shell is bash, not zsh.** This script uses the `${arr[@]+"${arr[@]}"}` empty-array idiom (see UL#166 for the bash-3.2 hazard it defends against). That idiom is bash-portable but NOT zsh-portable: under zsh, when the array is empty, the guard expands to a single empty-string word and the `for x in ...` loop body runs ONCE with `x=""`, which then aborts at `${x:?}` (`zsh:<line>: <var>: parameter not set`) AFTER the worktree is created but BEFORE the commit, leaving no commit and a partially reset working tree. When the invoking agent's default shell is zsh (macOS default), paste the canonical text into a temp `*.sh` file with a `#!/bin/bash` shebang and invoke `bash <file>`; do NOT paste the body directly into a zsh shell tool call. (UL#189.)

> **Safety model:** Step 2 syncs through a separate temporary worktree. It must never checkout `docs`, run `git clean`, or delete shadow paths in the live project checkout.

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
DOCS_BRANCH="docs"
# Build SHADOW_CANDIDATES per Documentation paths section above (the assembled
# section also defines the shared candidate-ignored probe used below).

docs_branch_under_tracked_subtree() {
  _candidate_path="$1"
  _shadow_root="$2"
  _ancestor=$(dirname "$_candidate_path")
  while [ "$_ancestor" != "." ] && [ "$_ancestor" != "/" ]; do
    [ "$_ancestor" = "$_shadow_root" ] && return 1
    if git ls-files -- "$_ancestor" | grep -q .; then
      return 0
    fi
    _ancestor=$(dirname "$_ancestor")
  done
  return 1
}

# Explicit deletes: only paths removed in the latest docs commit may be dropped.
DOCS_EXPLICIT_DELETES=()
if git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}"; then
  _docs_parent=$(git rev-parse "refs/heads/${DOCS_BRANCH}^" 2>/dev/null || true)
  if [ -n "$_docs_parent" ]; then
    while IFS= read -r _del; do
      [ -n "$_del" ] || continue
      DOCS_EXPLICIT_DELETES+=("$_del")
    done <<EOF
$(git diff --name-only --diff-filter=D "${_docs_parent}" "refs/heads/${DOCS_BRANCH}" 2>/dev/null)
EOF
  fi
fi
unset _docs_parent _del

docs_branch_is_explicit_delete() {
  _target="$1"
  # set -u: empty array expansion fails on bash < 4.4 without the + guard
  for _del in "${DOCS_EXPLICIT_DELETES[@]+"${DOCS_EXPLICIT_DELETES[@]}"}"; do
    [ "$_target" = "$_del" ] && return 0
    case "$_target" in "$_del"/*) return 0 ;; esac
  done
  return 1
}

# EXECUTE_PLAN_BACKUP, the worktree mktemp -d dirs, FILTERED_GITIGNORE, and
# EXTRA_IGNORE_RULES are created below this line and are trap-owned; the trap
# covers every mktemp artifact of this script. It registers BEFORE the restore
# region so the region's three mktemp files are trap-covered from creation: a
# SIGINT/SIGTERM or mid-region abort can no longer leak them.
docs_branch_cleanup() {
  rc=$?
  trap - EXIT INT TERM
  if [ -n "${DOCS_WORKTREE:-}" ]; then
    git worktree remove -f "$DOCS_WORKTREE" 2>/dev/null || rm -rf "$DOCS_WORKTREE"
  fi
  [ -n "${DOCS_WORKTREE_PARENT:-}" ] && rm -rf "$DOCS_WORKTREE_PARENT"
  [ -n "${SHADOW_TMP:-}" ] && rm -rf "$SHADOW_TMP"
  [ -n "${EXECUTE_PLAN_BACKUP:-}" ] && rm -rf "$EXECUTE_PLAN_BACKUP"
  [ -n "${DOCS_STAGED_DELETES_FILE:-}" ] && rm -f "$DOCS_STAGED_DELETES_FILE"
  [ -n "${RESTORED_PATHS_FILE:-}" ] && rm -f "$RESTORED_PATHS_FILE"
  [ -n "${DOCS_TMP_SWEEP_FILE:-}" ] && rm -f "$DOCS_TMP_SWEEP_FILE"
  [ -n "${FILTERED_GITIGNORE:-}" ] && rm -f "$FILTERED_GITIGNORE"
  [ -n "${EXTRA_IGNORE_RULES:-}" ] && rm -f "$EXTRA_IGNORE_RULES"
  exit "$rc"
}
trap docs_branch_cleanup EXIT INT TERM

# Certified-plan ordering guard (fail-closed): the sync must never commit a
# plan file's older bytes over the newer certified shape the branch holds.
# The certification digest comes from the plan's latest review sidecar.
_ORD_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
_plans_dir_ord="docs/history/plans"
_reviews_dir_ord="${REVIEWS_DIR:-docs/reviews}"
if [ -f .ai-playbook/facts.md ]; then
  _pd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^plans_dir[[:space:]]*=/{gsub(/^plans_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_pd_cfg" ] && _plans_dir_ord="$_pd_cfg"
  _rd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^reviews_dir[[:space:]]*=/{gsub(/^reviews_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_rd_cfg" ] && _reviews_dir_ord="$_rd_cfg"
fi
PLAN_GUARD_SCRIPT="${DOCS_BRANCH_PLAN_GUARD_SCRIPT:-${_ORD_TOP}/scripts/docs_branch_plan_guard.py}"
[ -f "$PLAN_GUARD_SCRIPT" ] || PLAN_GUARD_SCRIPT="${HOME}/.ai-playbook/scripts/docs_branch_plan_guard.py"

# Add-only safety net: restore shadow files that exist on the docs branch but are
# missing on disk BEFORE sync. Without this, a file lost earlier (e.g. by a manual
# branch switch) would stay gone and never be re-synced. Reviews and all other
# shadow roots follow this rule. Fill-only; never overwrite existing on-disk data.
# A path the user has STAGED for deletion or rename is an intentional move, not
# data loss: it is never restored. Afterwards only the paths actually restored
# are unstaged; the reset must NEVER blanket the shadow roots (that unstaged the
# user's own staged git mv work; witnessed 2026-08-31).
DOCS_STAGED_DELETES_FILE=""
RESTORED_PATHS_FILE=""
DOCS_TMP_SWEEP_FILE=""
if git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}"; then
  DOCS_STAGED_DELETES_FILE=$(mktemp)
  RESTORED_PATHS_FILE=$(mktemp)
  DOCS_TMP_SWEEP_FILE=$(mktemp)
  git diff --cached --name-only --no-renames --diff-filter=D 2>/dev/null > "$DOCS_STAGED_DELETES_FILE" || true
  docs_branch_is_staged_delete() {
    _target="$1"
    [ -s "$DOCS_STAGED_DELETES_FILE" ] || return 1
    grep -qxF -- "$_target" "$DOCS_STAGED_DELETES_FILE"
  }
  for shadow_root in "${SHADOW_CANDIDATES[@]}"; do
    clean_root="${shadow_root%/}"
    tmp_root="${TMP_DIR:-docs/tmp}"
    tmp_root="${tmp_root%/}"
    git ls-tree -r --name-only "refs/heads/${DOCS_BRANCH}" -- "$clean_root" 2>/dev/null \
      | while IFS= read -r tracked; do
          [ -n "$tracked" ] || continue
          [ -e "$tracked" ] && continue
          docs_branch_is_explicit_delete "$tracked" && continue
          docs_branch_is_staged_delete "$tracked" && continue
          git check-ignore -q "$tracked" || continue
          case "$tracked" in
            "${tmp_root}"/*)
              # tmp sweep: {tmp_dir} is scratch with plan lifetime (the pre-docs
              # sweep gate run's docs-tmp-sweep gate, plans Plan Lifecycle
              # cleanup). Absent on disk means the owner
              # cleaned it up: drop from the branch instead of restoring. This is
              # the one non-add-only root; do NOT widen it to other roots.
              # Sits after the check-ignore gate so only genuinely gitignored
              # scratch is sweep-eligible (committed tmp paths are restored
              # like any other branch-tracked content).
              printf '%s\n' "$tracked" >> "$DOCS_TMP_SWEEP_FILE"
              continue
              ;;
          esac
          docs_branch_under_tracked_subtree "$tracked" "$clean_root" && continue
          mkdir -p "$(dirname "$tracked")"
          git cat-file -p "refs/heads/${DOCS_BRANCH}:${tracked}" > "$tracked" 2>/dev/null || true
          printf '%s\n' "$tracked" >> "$RESTORED_PATHS_FILE"
          echo "docs-branch: restored missing ${tracked} from refs/heads/${DOCS_BRANCH}" >&2
        done
  done
  # Unstage ONLY the files this restore wrote (the redirect write never touches
  # the index; the reset is defensive for paths whose ignore state drifted).
  # The restore loop runs inside a pipeline subshell, hence the temp file.
  if [ -s "$RESTORED_PATHS_FILE" ]; then
    sort -u "$RESTORED_PATHS_FILE" | while IFS= read -r _restored; do
      [ -n "$_restored" ] || continue
      git reset -q -- "$_restored" 2>/dev/null || true
    done
  fi
# Restore-leg certified-digest witness (warn-and-continue): a plan file just
# restored from the branch whose bytes do not match the latest certified
# sidecar digest is recorded loudly at restore time; refusal remains the
# overlay guard's job above.
if [ -s "$RESTORED_PATHS_FILE" ] && [ -f "$PLAN_GUARD_SCRIPT" ]; then
  grep "^${_plans_dir_ord%/}/" "$RESTORED_PATHS_FILE" | while IFS= read -r _restored_plan; do
    python3 "$PLAN_GUARD_SCRIPT" check-restored \
      --reviews-dir "$_reviews_dir_ord" "$_restored_plan" || true
  done
fi
  unset shadow_root clean_root tracked _restored
fi
[ -n "${DOCS_STAGED_DELETES_FILE:-}" ] && [ -f "$DOCS_STAGED_DELETES_FILE" ] && rm -f "$DOCS_STAGED_DELETES_FILE"
[ -n "${RESTORED_PATHS_FILE:-}" ] && [ -f "$RESTORED_PATHS_FILE" ] && rm -f "$RESTORED_PATHS_FILE"
# DOCS_TMP_SWEEP_FILE is intentionally NOT removed here: DOCS_STAGED_DELETES_FILE
# and RESTORED_PATHS_FILE are consumed and rm'd in the restore block above, while
# DOCS_TMP_SWEEP_FILE is filled there but consumed later (worktree sweep drop and
# staged deletion), so only it survives to trap removal; cleanup covers the SHADOW_PATHS-empty early exit.

SHADOW_PATHS=()
# Arm precedence pinned: a candidate ignored at bare OR descendant level (the
# shared probe helper) takes the include arm and never reaches the mirror arm;
# the elif is reachable only when the helper returned nonzero (branch
# continuity for candidates the branch already tracks).
for candidate in "${SHADOW_CANDIDATES[@]}"; do
  clean="${candidate%/}"
  if [ -e "$clean" ] && docs_branch_candidate_ignored "$clean"; then
    SHADOW_PATHS+=("$candidate")
  elif git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}" && \
       git ls-tree -r --name-only "refs/heads/${DOCS_BRANCH}" -- "$clean" 2>/dev/null | grep -q .; then
    SHADOW_PATHS+=("$candidate")
  fi
done
for extra_path in "${EXTRA_SHADOW_DIRS[@]+"${EXTRA_SHADOW_DIRS[@]}"}"; do
  clean_extra="${extra_path%/}"
  [ -e "$clean_extra" ] || continue
  _already_shadowed=0
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    [ "${shadow_path%/}" = "$clean_extra" ] && _already_shadowed=1 && break
  done
  [ "$_already_shadowed" -eq 0 ] && SHADOW_PATHS+=("$extra_path")
done
unset extra_path clean_extra _already_shadowed shadow_path

# Resolve tmp_dir for execute-plan session preservation (TOML first, then fallback)
EXEC_TMP=""
if [ -f .ai-playbook/facts.md ]; then
  EXEC_TMP=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^tmp_dir/{gsub(/^tmp_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
fi
EXEC_TMP="${EXEC_TMP:-${TMP_DIR:-docs/tmp/}}"
EXEC_TMP="${EXEC_TMP%/}"

EXECUTE_PLAN_BACKUP=""
if [ -d "${EXEC_TMP}/execute-plan" ]; then
  for session_dir in "${EXEC_TMP}/execute-plan"/*/; do
    [ -f "${session_dir}manifest.md" ] || continue
    EXECUTE_PLAN_BACKUP=$(mktemp -d)
    cp -Rp "${session_dir%/}" "${EXECUTE_PLAN_BACKUP}/"
    break  # one active session per run
  done
fi

if [ ${#SHADOW_PATHS[@]} -eq 0 ]; then
  exit 0
fi

# Worktree-based sync: never checkout docs in the live project checkout.
SHADOW_TMP=$(mktemp -d)
DOCS_WORKTREE_PARENT=$(mktemp -d "${TMPDIR:-/tmp}/docs-branch-worktree.XXXXXX")
DOCS_WORKTREE="${DOCS_WORKTREE_PARENT}/worktree"

for shadow_path in "${SHADOW_PATHS[@]}"; do
  src="${shadow_path%/}"  # strip trailing slash so cp -Rp copies the item itself (capital R preserves symlinks; lowercase -r follows them, which fails on OS-protected symlink targets and diverges from docs-branch history)
  if [ -e "$src" ]; then
    parent=$(dirname "$src")
    mkdir -p "${SHADOW_TMP}/${parent}"
    _extra_shadow_root=0
    for extra_path in "${EXTRA_SHADOW_DIRS[@]+"${EXTRA_SHADOW_DIRS[@]}"}"; do
      [ "${extra_path%/}" = "$src" ] && _extra_shadow_root=1 && break
    done
    if [ -d "$src" ] && [ "$_extra_shadow_root" -eq 1 ]; then
      git ls-files --others --ignored --exclude-standard -z -- "$src" \
        | while IFS= read -r -d '' ignored_path; do
            [ -e "$ignored_path" ] || continue
            docs_branch_under_tracked_subtree "$ignored_path" "$src" && continue
            mkdir -p "${SHADOW_TMP}/$(dirname "$ignored_path")"
            cp -p "$ignored_path" "${SHADOW_TMP}/${ignored_path}"
          done
    else
      cp -Rp "$src" "${SHADOW_TMP}/${parent}/"
    fi
  fi
done
unset _extra_shadow_root ignored_path
# Vim swap files are local editor recovery artifacts. Keep any live file in the
# working tree, but never copy it into the docs backup branch.
find "$SHADOW_TMP" -type f \( -name '.*.swp' -o -name '.*.swo' -o -name '.*.swn' \) -delete
[ -e ".gitignore" ] && cp ".gitignore" "${SHADOW_TMP}/.gitignore"

if git for-each-ref --format='%(refname)' 'refs/heads/docs/*' | grep -q .; then
  echo "ERROR: found invalid docs/* branches; consolidate them into refs/heads/docs first" >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/${DOCS_BRANCH}"; then
  if ! git worktree add "$DOCS_WORKTREE" "$DOCS_BRANCH"; then
    # Lost the worktree race (the docs branch is already checked out in another
    # worktree). Continuing would overlay into a plain directory and die at
    # commit with misleading errors; fail here instead, naming the holder.
    echo "ERROR: git worktree add failed for branch '${DOCS_BRANCH}' (already checked out?); holder per git worktree list:" >&2
    git worktree list >&2
    echo "Remedies in order: (1) intact-but-dead worktree holding the branch: git worktree remove <dir>; (2) stale gitdir entries only (the directory is already gone): git worktree prune" >&2
    exit 1
  fi
else
  git worktree add --detach "$DOCS_WORKTREE" HEAD
  (
    cd "$DOCS_WORKTREE"
    git checkout --orphan "$DOCS_BRANCH"
    git rm -r . --quiet 2>/dev/null || true
  )
fi

# Certified-plan ordering guard (fail-closed): compares the worktree's
# PRISTINE branch bytes against the incoming snapshot BEFORE the overlay
# overwrites them; a certified downgrade aborts the sync before staging.
if [ -d "${DOCS_WORKTREE}/${_plans_dir_ord}" ]; then
  if [ -f "$PLAN_GUARD_SCRIPT" ]; then
    python3 "$PLAN_GUARD_SCRIPT" guard \
      --incoming-root "$SHADOW_TMP" \
      --branch-root "$DOCS_WORKTREE" \
      --plans-dir "$_plans_dir_ord" \
      --reviews-dir "$_reviews_dir_ord" || exit 1
  else
    echo "WARN: certified-plan guard script not found; sync proceeds without the ordering check" >&2
  fi
fi

# Sync .gitignore from the working branch, then strip standard LLM artifact rules
# and any rules that match extra shadow paths so the docs branch can track its
# shadow files explicitly. Extra shadow paths are still staged with -f below.
if [ -e "${SHADOW_TMP}/.gitignore" ]; then
  FILTERED_GITIGNORE=$(mktemp)
  EXTRA_IGNORE_RULES=$(mktemp)

  grep -vE '^/?\.?github/docs/?$|^/docs/?$|^/\.ai-playbook/?$|^/AGENTS\.md$|^/CLAUDE\.md$|^/GEMINI\.md$|^/COPILOT\.md$|^AGENTS\.md$|^GEMINI\.md$|^CLAUDE\.md$|^/?docs/personal/?$|^/?docs/tmp/?$|^/?docs/reviews/?$|^/?docs/history/reviews/?$' "${SHADOW_TMP}/.gitignore" > "$FILTERED_GITIGNORE" || true

  for extra_path in "${EXTRA_SHADOW_DIRS[@]+"${EXTRA_SHADOW_DIRS[@]}"}"; do
    clean_extra="${extra_path%/}"
    [ -e "$clean_extra" ] || continue
    git check-ignore -v -- "$clean_extra" 2>/dev/null \
      | sed 's/^[^:]*:[0-9]*://; s/[[:space:]].*$//' >> "$EXTRA_IGNORE_RULES" || true
    if [ -d "$clean_extra" ]; then
      git ls-files --others --ignored --exclude-standard -z -- "$clean_extra" \
        | while IFS= read -r -d '' ignored_path; do
            git check-ignore -v -- "$ignored_path" 2>/dev/null \
              | sed 's/^[^:]*:[0-9]*://; s/[[:space:]].*$//' >> "$EXTRA_IGNORE_RULES" || true
          done
    fi
  done

  if [ -s "$EXTRA_IGNORE_RULES" ]; then
    sort -u "$EXTRA_IGNORE_RULES" -o "$EXTRA_IGNORE_RULES"
    awk 'NR==FNR {ignored[$0]=1; next} !($0 in ignored)' "$EXTRA_IGNORE_RULES" "$FILTERED_GITIGNORE" > "${DOCS_WORKTREE}/.gitignore"
  else
    cp "$FILTERED_GITIGNORE" "${DOCS_WORKTREE}/.gitignore"
  fi
  rm -f "$FILTERED_GITIGNORE" "$EXTRA_IGNORE_RULES"
  unset FILTERED_GITIGNORE EXTRA_IGNORE_RULES clean_extra extra_path
fi

for shadow_path in "${SHADOW_PATHS[@]}"; do
  src="${shadow_path%/}"
  case "$src" in
    ""|"."|".."|/*|../*|*/../*)
      echo "Refusing unsafe shadow path: ${shadow_path}" >&2
      exit 1
      ;;
  esac
  parent=$(dirname "$src")
  mkdir -p "${DOCS_WORKTREE}/${parent}"
  # Add-only: overlay disk snapshot; never rm -rf because files are absent from disk.
  if [ -e "${SHADOW_TMP}/${src}" ]; then
    cp -Rp "${SHADOW_TMP}/${src}" "${DOCS_WORKTREE}/${parent}/"
  fi
done

for del_path in "${DOCS_EXPLICIT_DELETES[@]+"${DOCS_EXPLICIT_DELETES[@]}"}"; do
  rm -rf -- "${DOCS_WORKTREE:?}/${del_path:?}" 2>/dev/null || true
done
unset del_path

# tmp sweep removals: drop swept {tmp_dir} paths from the docs worktree so the
# branch tip stops tracking them. Content stays recoverable from the
# pre-sweep history of this branch.
if [ -s "$DOCS_TMP_SWEEP_FILE" ]; then
  sort -u "$DOCS_TMP_SWEEP_FILE" | while IFS= read -r _swept; do
    [ -n "$_swept" ] || continue
    rm -rf -- "${DOCS_WORKTREE:?}/${_swept:?}" 2>/dev/null || true
    echo "docs-branch: tmp sweep dropped ${_swept}" >&2
  done
fi
unset _swept

# Plan-archive move detection: when a plan was archived on the working branch
# (moved from plans_dir to plans_completed_dir via ``git mv``), the add-only
# overlay above copies the new completed/ file into the worktree but leaves
# the stale old-path copy (``cp -Rp`` never deletes). The docs branch would
# then track both locations forever. Mirror the archive move by removing the
# stale old-path copy when the working tree no longer has it.
if [ -f .ai-playbook/facts.md ]; then
  _plans_dir_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^plans_dir[[:space:]]*=/{gsub(/^plans_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  _plans_completed_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^plans_completed_dir[[:space:]]*=/{gsub(/^plans_completed_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  _plans_dir_cfg="${_plans_dir_cfg%/}"
  _plans_completed_cfg="${_plans_completed_cfg%/}"
  if [ -n "$_plans_dir_cfg" ] && [ -n "$_plans_completed_cfg" ] && \
     [ -d "${DOCS_WORKTREE}/${_plans_completed_cfg}" ]; then
    find "${DOCS_WORKTREE}/${_plans_completed_cfg}" -maxdepth 1 -type f -name '*.md' -print0 \
      | while IFS= read -r -d '' _completed_file; do
          _base="$(basename "$_completed_file")"
          _old_worktree="${DOCS_WORKTREE}/${_plans_dir_cfg}/${_base}"
          _live_old="${_plans_dir_cfg}/${_base}"
          # Remove only if the old-path copy is stale (absent from working tree).
          if [ -e "$_old_worktree" ] && [ ! -e "$_live_old" ]; then
            rm -f -- "$_old_worktree"
          fi
        done
  fi
  unset _plans_dir_cfg _plans_completed_cfg _completed_file _base _old_worktree _live_old
fi

# Backlog duplicate sweep (warn-and-continue): drop a stale top-level
# {backlog_dir}/<name>.md copy when its archived twin under completed/,
# deferred/, or rejected/ exists on the branch and matches beyond the
# Status line; surface (never delete) on a deeper mismatch. Bounded:
# this removes duplicates of archived items only and never widens the
# sweep-root rule ({tmp_dir} stays the one sweep-eligible root).
_backlog_dir_cfg="docs/history/backlog"
if [ -f .ai-playbook/facts.md ]; then
  _bd_cfg=$(awk 'BEGIN{F3=sprintf("%c%c%c",96,96,96)} $0 ~ "^"F3"toml"{f=1;next} f && $0 ~ "^"F3{exit} f && /^backlog_dir[[:space:]]*=/{gsub(/^backlog_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)
  [ -n "$_bd_cfg" ] && _backlog_dir_cfg="$_bd_cfg"
fi
DEDUPE_SCRIPT="${DOCS_BRANCH_DEDUPE_SCRIPT:-${_ORD_TOP}/scripts/docs_branch_backlog_dedupe.py}"
[ -f "$DEDUPE_SCRIPT" ] || DEDUPE_SCRIPT="${HOME}/.ai-playbook/scripts/docs_branch_backlog_dedupe.py"
if [ -d "${DOCS_WORKTREE}/${_backlog_dir_cfg}" ]; then
  if [ -f "$DEDUPE_SCRIPT" ]; then
    python3 "$DEDUPE_SCRIPT" --worktree-root "$DOCS_WORKTREE" --backlog-dir "$_backlog_dir_cfg" \
      || echo "WARN: backlog duplicate sweep failed; continuing (warn-and-continue)" >&2
  else
    # Missing-script warn parity with the certified-plan guard above: the
    # sweep is skipped, but never silently.
    echo "WARN: backlog dedupe script not found; sync proceeds without the duplicate sweep" >&2
  fi
fi

# Doc-hierarchy rogue-dir detection: when the ``doc-hierarchy-migrate`` skill
# moves files out of a module-split dir (``docs/<rogue>/``) into a canonical
# tree (``architecture/``, ``maintenance/``, ``history/``, ``tmp/``), the
# add-only overlay leaves the stale ``docs/<rogue>/`` copy on the docs branch
# forever. Remove non-canonical top-level ``docs/<X>/`` dirs from the worktree
# when the working tree no longer has them.
#
# Guard: only active after the repo has migrated (``docs/maintenance/`` exists
# on the docs branch, the migration-complete signal). On unmigrated repos the
# canonical layout does not apply, so the add-only invariant is preserved.
if [ -d "${DOCS_WORKTREE}/docs/maintenance" ]; then
  _canonical_docs_roots=" architecture maintenance history tmp "
  for _wt_entry in "${DOCS_WORKTREE}/docs/"*/; do
    [ -d "$_wt_entry" ] || continue
    _wt_entry="${_wt_entry%/}"
    _dir_name="$(basename "$_wt_entry")"
    case "$_canonical_docs_roots" in
      *" $_dir_name "*) continue ;;  # canonical root, keep
    esac
    # Non-canonical dir on the docs worktree. Remove only if the working tree
    # no longer has it (signals a completed migration, not a temporary absence
    # that the add-only safety net should protect).
    if [ ! -d "docs/${_dir_name}" ]; then
      rm -rf -- "${DOCS_WORKTREE:?}/docs/${_dir_name:?}"
    fi
  done
  unset _canonical_docs_roots _wt_entry _dir_name
fi

# Ephemeral Confluence publish snapshots: prune stale *-cf-out.md and __pycache__
# from the docs worktree when absent from the live checkout (exception to add-only).
HYGIENE_SCRIPT="${CONFLUENCE_MIRROR_HYGIENE_SCRIPT:-${HOME}/.ai-playbook/scripts/confluence-mirror-hygiene.sh}"
if [ -x "$HYGIENE_SCRIPT" ]; then
  "$HYGIENE_SCRIPT" docs-worktree-prune "$DOCS_WORKTREE"
fi

# Nested repos must not be staged as submodule gitlinks on the docs branch.
find "$DOCS_WORKTREE" -mindepth 2 -name '.git' -type d | while read -r d; do rm -rf -- "$d"; done

(
  cd "$DOCS_WORKTREE"

  # Hygiene gate: abort sync if repo agent facts match deny patterns (never force-add secrets to docs branch)
  if [ -e ".ai-playbook/facts.md" ]; then
    PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-${HOME}/.ai-playbook/public-hygiene.patterns}"
    if [ ! -f "$PATTERNS_FILE" ] && [ -f docs/scan-public-hygiene.patterns.example ]; then
      PATTERNS_FILE="docs/scan-public-hygiene.patterns.example"
    fi
    HYGIENE_FAIL=0
    if [ -f "$PATTERNS_FILE" ]; then
      if rg -q -f "$PATTERNS_FILE" .ai-playbook/facts.md 2>/dev/null; then
        echo "ERROR: public hygiene patterns matched .ai-playbook/facts.md" >&2
        rg -n -f "$PATTERNS_FILE" .ai-playbook/facts.md >&2 || true
        HYGIENE_FAIL=1
      fi
    else
      echo "WARN: no hygiene patterns file; skipping deny-pattern scan (absolute-path check still runs)" >&2
    fi
    ABS_HOME_RG="$(printf '%s%s%s%s%s' '/' 'Users' '/|' '/home/' '[a-zA-Z0-9._-]+/')"
    if rg -q "$ABS_HOME_RG" .ai-playbook/facts.md 2>/dev/null; then
      echo "ERROR: absolute home paths in .ai-playbook/facts.md" >&2
      rg -n "$ABS_HOME_RG" .ai-playbook/facts.md >&2 || true
      HYGIENE_FAIL=1
    fi
    if [ "$HYGIENE_FAIL" -ne 0 ]; then
      echo "ERROR: abort docs-branch sync (fix .ai-playbook/facts.md or run public_hygiene_scan_script before retry)" >&2
      exit 1
    fi
  fi

  git add .gitignore 2>/dev/null || true
  for shadow_path in "${SHADOW_PATHS[@]}"; do
    git add -f "$shadow_path" 2>/dev/null || true
  done
  for del_path in "${DOCS_EXPLICIT_DELETES[@]+"${DOCS_EXPLICIT_DELETES[@]}"}"; do
    git add -f "$del_path" 2>/dev/null || true
  done
  if [ -s "$DOCS_TMP_SWEEP_FILE" ]; then
    sort -u "$DOCS_TMP_SWEEP_FILE" | while IFS= read -r _swept; do
      [ -n "$_swept" ] || continue
      git add -f "$_swept" 2>/dev/null || true
    done
  fi

  # Commit only if there are staged changes; include source branch for traceability.
  if ! git diff --cached --quiet; then
    git commit -m "docs: update from ${CURRENT_BRANCH}"
  fi
)

# Propagate the sync subshell status (e.g. the hygiene gate's exit 1) so a
# hygiene-aborted sync reports failure to the caller instead of silent success.
sync_rc=$?
exit "$sync_rc"
```

Failure semantics (sync): every failure path in the block is loud on stderr and splits into two classes. Exit 1 abort paths (nothing is staged or committed when they trip): the hygiene gate (a deny-pattern or absolute-home-path match in `.ai-playbook/facts.md` aborts the staging subshell, and the block tail re-raises that status so a hygiene-aborted sync reports failure to the caller instead of silent success), and the certified-downgrade refusal (exit 1, before staging), which enforces the Certified-plan ordering Rules bullet by refusing any overlay write that would replace plan bytes matching the latest certified sidecar digest with bytes that do not match it, and the docs-branch `git worktree add` refusal (exit 1, before staging, naming the holder per `git worktree list` with the two leak remedies in order), and the invalid docs/* branches consolidation error (exit 1, before staging: any `refs/heads/docs/*` sub-branch trips it; the reader action is the error line's own instruction - consolidate the sub-branches into `refs/heads/docs` first, then re-run the sync), and the unsafe-shadow-path refusal (exit 1, before any commit: an empty, dot, parent-relative, absolute, or parent-escaping shadow path trips it; the reader action is to fix the path list that produced the entry, naming the refused path from the error line). Warn-and-continue paths (the sync completes, and the skip is never silent): the certified-plan guard script missing (the sync proceeds without the ordering check), the dedupe script missing or the backlog duplicate sweep failing (the sync proceeds without dedupe), and the restored-plan witness warnings when a restore fills a plan file whose bytes do not match the latest certified sidecar digest. Deferral: the certified-downgrade refusal's absolute wording defers to the guard's progress-only overlay arm (see the Certified-plan ordering Rules bullet), under which an incoming plan that differs from certified branch bytes only in unchecked-to-checked checkbox marker flips is accepted with a named line instead of refused.

> **Note:** When `docs/` is also a directory on the working branch, `git log --oneline docs` is ambiguous. Always use `git log --oneline refs/heads/docs --` to reference the branch unambiguously.

## Step 3: Lesson-Scope Drift Witness Append

When the caller holds a lesson-scope-audit drift witness line (from done Step 3 item 4a) for a corpus whose path is gitignored, the docs-branch-only path has no `done` Step 3 corpus commit to carry the line, so this step lands it as the body of an append-only empty commit on the docs branch.

Contract: the caller passes the exact witness line as the single argument; the line must start with lesson-scope-audit: (fail loud otherwise). The canonical drift witness line this skill expects is: lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run. Invoke the append from the audited project repository root; the skill does not resolve or verify the root (the docs-branch refusal only guards the current repo).

Failure semantics: a missing docs branch, a failed worktree add, or a failed commit each returns non-zero with a loud message, as does a certified-downgrade refusal (the plan guard's exit 1 before staging, naming every refused row); a missing docs branch means no sync ever carried the corpus, so the append must refuse rather than overstate coverage.

Run this block as a single shell invocation, in bash not zsh, with the worktree removed on every exit path; never push, the docs branch stays a local safety net per this skill's Rules:

```bash
docs_branch_witness_append() {
  # $1: the exact witness line; must start with lesson-scope-audit:
  case "$1" in
    lesson-scope-audit:*) ;;
    *) echo "docs-branch: witness must start with lesson-scope-audit:" >&2; return 1 ;;
  esac
  # Everything below runs inside one subshell: `trap` is shell-global, so the
  # subshell scope keeps the caller's EXIT/INT/TERM traps (for example the done
  # Step 0 Variant A release trap) intact, discards this cleanup trap at subshell
  # exit (no `trap -` reset line), and keeps _w/_wt/_rc out of the caller shell.
  # The trap is the single cleanup authority: the refusal and post-commit paths
  # below carry no explicit worktree-removal lines.
  (
    _w="$1"
    git show-ref --verify --quiet refs/heads/docs || { echo "docs-branch: no docs branch; run a sync first" >&2; exit 1; }
    _wt="$(mktemp -d "${TMPDIR:-/tmp}/docs-branch-witness.XXXXXX")" || { echo "docs-branch: witness worktree dir failed" >&2; exit 1; }
    trap 'git worktree remove --force "$_wt" >/dev/null 2>&1 || rm -rf "$_wt"' EXIT INT TERM
    if ! git worktree add "$_wt" docs; then
      echo "docs-branch: witness worktree add failed; if a prior interrupted append leaked a worktree holding docs, run: git worktree prune" >&2
      exit 1
    fi
    if ! git -C "$_wt" symbolic-ref -q HEAD >/dev/null; then
      echo "docs-branch: witness worktree is detached; aborting (a detached worktree would drop the witness commit)" >&2
      exit 1
    fi
    ( cd "$_wt" && git commit --allow-empty -m "docs: lesson-scope-audit drift witness" -m "$_w" )
    _rc=$?
    if [ "$_rc" -ne 0 ]; then
      echo "docs-branch: witness commit failed" >&2
    fi
    exit "$_rc"
  )
}
```

The witness line is byte-for-byte identical to the `done` Step 3 corpus-commit body line so one audit-note grep pattern covers both carriers.

## Recovery: Restoring Missing Gitignored Files

Any manual `git checkout docs` (for history inspection, rebase, or reset) followed by `git checkout <feature-branch>` **will remove** `docs/`, `AGENTS.md`, `CLAUDE.md` and other gitignored files from disk. Git removes files that were tracked on the previous branch even when they are gitignored on the new branch.

To restore after a manual branch switch:

```bash
# Restore from the docs branch without switching to it
git checkout refs/heads/docs -- docs/ AGENTS.md CLAUDE.md .ai-playbook/
# Unstage: these files must NOT be committed on the feature branch
git restore --staged docs/ AGENTS.md CLAUDE.md .ai-playbook/
```

Then run the full docs-branch skill (Step 1 + Step 2) to re-sync any pending changes.

### Last-resort: searching historical git stash entries

Older versions of this workflow used `git stash push --all`. That command stores gitignored files in the stash's **third parent** (`stash@{N}^3`). If gitignored files are missing after an old run, inspect stash entries before assuming permanent loss:

```bash
# List gitignored files stored in each stash entry (requires --all stash)
git ls-tree -r --name-only stash@{0}^3
git ls-tree -r --name-only stash@{1}^3

# Extract a specific file from a stash entry
git show stash@{0}^3:docs/tmp/my-file.md > docs/tmp/my-file.md
```

This only works when an old `git stash push --all` run happened after the files were created. Stash entries that predate the file's creation contain nothing.

## Rules

- Never use `docs/master`, `docs/<feature>`, or any other `docs/...` shadow branches. The only valid shadow branch name is exactly `docs`.
- If any `refs/heads/docs/*` branches already exist, consolidate them into the single `docs` branch and delete the namespaced branches before the next sync. Do not keep using them as a workaround.
- **Before running this skill, verify all candidate files are gitignored** (`git check-ignore -q <file>`; descendant-only ignore coverage counts for untracked roots: a rule shape such as `docs/history/reviews/**` matches only children and leaves the root itself unmatched, and the skill's candidate probe includes such an untracked root via its descendant-ignored fallback). Repo `.gitignore` should include `/.ai-playbook/` (repo root only; see `bootstrap-ai-playbook`). If a file is untracked but not gitignored and you cannot commit `.gitignore`, add the path to `.git/info/exclude` (local-only fallback) before running the skill.
- Never switch the live project checkout to the `docs` branch during sync. Use a temporary `git worktree` for all `docs` branch operations.
- Run Step 2's script as a **single shell invocation**: never split across tool calls. Do not use `path` as a loop variable (zsh special variable).
- The `docs` branch is **never pushed to remote**: local safety net only.
- Create the `docs` branch as an **orphan** when it does not yet exist.
- **Never** include `.claude/` (or similar local config dirs) in `SHADOW_PATHS`: they stay local-only and are not synced to the branch.
- Build `extra_shadow_dirs` from the union of live `.ai-playbook/facts.md` and `refs/heads/docs:.ai-playbook/facts.md`. A stale live facts file must not remove already-configured shadow paths.
- **Add-only sync:** never treat a missing on-disk shadow file as a deletion on the `docs` branch. Restore fill-only from `refs/heads/docs` for every shadow root (including reviews) before sync. Only paths explicitly deleted in the latest `docs` commit may be removed from the worktree and staged as deletions. **Single exception (`{tmp_dir}`):** a path under `{tmp_dir}` (fallback `docs/tmp/`) that is tracked on the branch, absent on disk, not staged for deletion or rename in the live index, and still gitignored in the live repo is swept from the branch instead of restored, because `{tmp_dir}` is scratch with plan lifetime (the pre-docs sweep gate run's docs-tmp-sweep gate, `plans` **Plan Lifecycle** cleanup). Never widen this exception to `{reviews_dir}` or any other root. `scripts/review_retention.py docs-branch-commit` is a sanctioned producer of such explicit-delete commits: it commits the pruned review paths on the branch through a temporary worktree and verifies the removals before it removes the live shadow files.
- Backlog duplicate sweep: after the overlay, the sync drops a top-level {backlog_dir} copy whose archived twin under completed/, deferred/, or rejected/ exists on the branch and matches it beyond the Status: line; a deeper mismatch is surfaced and kept. A rejected/ twin (an explicit decision against the item; see the backlog rejected archive README) follows the same rules. Warn-and-continue always; never widen this to other roots.
- Certified-plan ordering: the sync refuses (exit 1, before staging) any overlay write that would replace plan bytes matching the plan's latest certified sidecar digest with bytes that do not match it, and warns when a restore fills a plan file whose bytes do not match the certification digest; a certified downgrade is never committed, and the refusal names the plan, the certified digest, and the sidecar. Progress-only overlay exception: when the branch bytes match the latest certified digest and the incoming plan differs from them only in checkbox marker flips, every differing line pair being an unchecked-to-checked flip (`[ ]` to `[x]` or `[X]`) on two otherwise byte-identical lines with equal line counts, the guard accepts the overlay and prints a named acceptance line carrying the plan, the flip count, and the certified digest; any other byte difference (a text edit, a structural change, a checked-to-unchecked regression, a bullet or spacing change) still refuses as a certified downgrade. A restored path under a plans archive subdirectory (completed/, deferred/, or rejected/) is classified as archived and skipped with an info line instead of being witnessed; archived plans are frozen history, and rejected plans are recorded decisions against the work.
- Ad-hoc worktree ordering: run the sync in the main checkout after closeout migration, never from a worktree that is about to be removed; a sync from a stale worktree can commit doomed bytes and, through the fill-only restore, re-export them later.
- **Ephemeral tmp prune:** after the add-only overlay, remove stale `docs/tmp/*-cf-out.md` and `docs/tmp/**/__pycache__/**` from the temporary docs worktree when they are absent from the live checkout (`confluence-mirror-hygiene.sh docs-worktree-prune`). The pre-docs sweep gate run's confluence-hygiene gate runs `audit-cf-out` first; cf-out is deleted only when hierarchy promotion is complete or the snapshot is STALE.
- Before syncing, restore any ignored shadow file that exists on the `docs` branch but is missing on disk (fill-only, never overwrite). This recovers content lost by an earlier manual branch switch and prevents the sync from dropping it from the `docs` backup. Paths staged for deletion or rename in the live index are intentional moves and are never restore targets; the follow-up unstage resets only the paths actually restored, never a blanket reset over the shadow roots (a blanket reset unstages the user's own staged work).
- Before staging on the `docs` branch, always strip LLM artifact gitignore rules and rules matching `extra_shadow_dirs` from `.gitignore` so the branch can track its own files. For a container root such as `resources/source/`, copy only ignored descendants that are not inside a tracked subtree; skip tracked or unignored children such as committed examples. Use `git add -f` when staging to also bypass any `.git/info/exclude` rules that may block adding gitignored paths.
- The live project checkout is read-only for shadow paths during sync. Copy shadow content to temp storage, then into the temporary docs worktree.
- **Never use `git stash push --all` or `git stash apply` for gitignored shadow files**: stash operations can remove ignored content from disk or restore only empty directories.
- **Never run `git stash clear`** in repos using this workflow, stash entries are the secondary backup layer alongside the `docs` branch.
- **Never delete shadow paths in the live checkout.** Deletes on the `docs` branch are allowed only for paths explicitly removed in the prior `docs` commit, and only inside the temporary docs worktree.
- **Nested git repos in SHADOW_PATHS** (e.g. `docs/personal/`): strip their `.git` inside the temporary docs worktree before staging (`find "$DOCS_WORKTREE" -mindepth 2 -name '.git' -type d | while read -r d; do rm -rf "$d"; done`). Without this, git treats them as submodule gitlinks and does not stage individual files.
- **Snapshot path correctness is data-loss critical**: `cp -Rp docs/foo SHADOW_TMP/` creates `SHADOW_TMP/foo/` (just the basename), NOT `SHADOW_TMP/docs/foo/`. Use the parent-preserving pattern everywhere: `parent=$(dirname "$src"); mkdir -p "${SHADOW_TMP}/${parent}"; cp -Rp "$src" "${SHADOW_TMP}/${parent}/"`. If the snapshot path doesn't match the worktree copy path, the sync silently omits content from the docs branch.
- **Never run whole-repo `git clean`** during docs-branch sync. The worktree implementation does not need it.
- **Preserve active execute-plan session logs** (`{tmp_dir}/execute-plan/<plan-slug>/` with `manifest.md`): the live checkout must remain untouched while the temporary docs worktree is updated.

## Integration Points

### With `done` and `plans` skills (docs/tmp sweep)
The `{tmp_dir}` sweep-eligible-root exception (Add-only sync invariant) exists to propagate the pre-docs sweep gate run's docs-tmp-sweep gate (ownerless scratch sweep; it never touches `review-loop*`/`code-review/`/`handoff/` scratch) and `plans` **Plan Lifecycle** (plan-completion docs/tmp cleanup) deletions to the branch. Never widen the exception for other consumers.

### With `done` (drift witness)
done Step 3 items 4a and 6 invoke this step's witness append when the audited corpus is gitignored; docs-branch owns the append mechanics, done owns the witness line text.
