#!/usr/bin/env bash
# release-rewrite.sh - mechanical core of the release skill.
# Plan: docs/history/plans/2026-09-26-release-skill.md (Task 2).
#
# Usage (same shell invocation as release-authoring.sh, immediately after it):
#
#   bash scripts/release-rewrite.sh <groups-file>
#
# The groups file carries one "base <sha>" line, then alternating
# "group <count>" / "msg <subject>" lines, oldest group first; counts sum to
# the publish-delta size. Runs the gated history rewrite: backup ref, ad-hoc
# worktree rewrite oldest group first, byte-identical tree gate, per-commit
# privacy scan of every published blob and message, compare-and-swap ref
# update, and a persisted 0700 push script performing the pre-push
# re-assertions before the plain fast-forward publish. Nothing here ever
# rewrites the remote; publishing happens only when the generated push script
# is executed later, and forced updates of the remote are never used.
set -euo pipefail

top=""
worktree_path=""
temp_branch=""
hygiene_root=""
run_tmp=""
wt_parent=""

die() {
  printf 'release-rewrite: FATAL: %s\n' "$*" >&2
  exit 1
}

regroup() {
  printf 'REGROUP REQUIRED: %s\n' "$*" >&2
  exit 2
}

cleanup() {
  cd "$top" 2>/dev/null || true
  if [ -n "$worktree_path" ]; then
    git worktree remove --force "$worktree_path" >/dev/null 2>&1 || true
  fi
  if [ -n "$temp_branch" ]; then
    git branch -D "$temp_branch" >/dev/null 2>&1 || true
  fi
  if [ -n "$hygiene_root" ]; then rm -rf "$hygiene_root" || true; fi
  if [ -n "$run_tmp" ]; then rm -rf "$run_tmp" || true; fi
  if [ -n "$wt_parent" ]; then rm -rf "$wt_parent" || true; fi
  return 0
}
trap cleanup EXIT

# Configuration keys (documented in agents/skills/release/SKILL.md):
#   DONE_LOCK_SCRIPT             done-lock implementation (default: the
#                                runtime-home deployment at
#                                "${HOME}/.ai-playbook/scripts/done-lock.sh")
#   RELEASE_REMOTE               remote name (default: origin)
#   RELEASE_HYGIENE_SCANNER      repo-relative scanner path (default:
#                                scripts/scan-public-hygiene.sh), resolved
#                                against the PRIMARY checkout

[ "$#" -eq 1 ] || die "usage: release-rewrite.sh <groups-file>"
groups_in="$1"
groups_dir="$(dirname "$groups_in")"
groups_file="$(cd "$groups_dir" 2>/dev/null && pwd)/$(basename "$groups_in")"
[ -f "$groups_file" ] || die "groups file not found: $groups_in"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$top"
remote="${RELEASE_REMOTE:-origin}"
upstream="refs/remotes/${remote}/main"

# 1. Re-assert the done lock acquired by the authoring step is still held.
lock_script="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
[ -f "$lock_script" ] || die "lock script not found (set DONE_LOCK_SCRIPT): $lock_script"
# The real done-lock `status` is repo-keyed, not token-fenced (token fencing
# is the stub/selftest contract), so this re-assertion degrades to "some lock
# is held for this worktree" against the real implementation; the token
# release stays fenced in the invoking shell's hands.
lock_status="$("$lock_script" status 2>&1)" || lock_status="free"
case "$lock_status" in
  *held*) : ;;
  *) die "the done lock is not held by this run; refusing to rewrite history (run the authoring step first)" ;;
esac

# 2. Re-assert HEAD is main.
head_ref="$(git symbolic-ref HEAD 2>/dev/null)" || head_ref=""
[ "$head_ref" = "refs/heads/main" ] || die "refusing to rewrite: HEAD is ${head_ref:-detached}, not refs/heads/main"

# 3. Fetch and refuse a diverged remote: local main must be a descendant of
#    <remote>/main.
git fetch --quiet "$remote" || die "git fetch $remote failed"
git rev-parse --verify --quiet "$upstream" >/dev/null 2>&1 || die "$upstream not found after fetch"
if ! git merge-base --is-ancestor "$upstream" refs/heads/main; then
  die "main is not a descendant of $remote/main; reconcile with the remote before releasing"
fi

# 4. Report-only inventory (backup refs are never cleanup candidates; the
#    cleanup offer belongs to the skill prose, gated on user confirmation).
printf 'release-rewrite: report-only inventory (nothing below is cleaned by this run):\n' >&2
git for-each-ref --format='  backup ref: %(refname) %(objectname:short)' refs/release-backup/ >&2 || true
for pat in release-push-* release-hygiene-* release-run-* release-wt-* release-authoring-*; do
  for p in "${TMPDIR:-/tmp}"/$pat; do
    if [ -e "$p" ]; then
      printf '  leftover scratch artifact: %s\n' "$p" >&2
    fi
  done
done
git for-each-ref --format='  leftover temp branch: %(refname)' 'refs/heads/release-rewrite-tmp-*' >&2 || true
git worktree list --porcelain 2>/dev/null | grep '^worktree ' | grep 'release-wt-' | sed 's/^/  leftover rewrite worktree: /' >&2 || true

# 5. Create the backup ref at the pre-rewrite tip BEFORE any mutation:
#    create-only via the zero-OID expected-old update-ref form, retrying the
#    next -N on a same-day collision.
today="$(date +%Y-%m-%d)"
base_tip="$(git rev-parse refs/heads/main)"
zero_oid=0000000000000000000000000000000000000000
backup_ref=""
for suffix in "" -2 -3 -4 -5 -6 -7 -8 -9 -10; do
  candidate="refs/release-backup/pre-release-$today$suffix"
  if git update-ref "$candidate" "$base_tip" "$zero_oid" 2>/dev/null; then
    backup_ref="$candidate"
    break
  fi
done
[ -n "$backup_ref" ] || die "cannot create a backup ref under refs/release-backup/pre-release-$today (ten same-day releases?); refusing to rewrite without a backup"
printf 'release-rewrite: backup ref %s at %s\n' "$backup_ref" "$base_tip" >&2

# 6. Validate the groups file.
counts=()
msgs=()
expect="base"
base_sha=""
while IFS= read -r line || [ -n "$line" ]; do
  [ -n "$line" ] || continue
  case "$expect:$line" in
    base:base\ *)
      base_sha="${line#base }"
      expect="group"
      ;;
    group:group\ *)
      value="${line#group }"
      case "$value" in
        ''|*[!0-9]*) die "group count must be an integer, got: $value" ;;
      esac
      [ "$value" -ge 1 ] 2>/dev/null || die "group count must be at least 1, got: $value"
      counts+=("$value")
      expect="msg"
      ;;
    msg:msg\ *)
      value="${line#msg }"
      [ -n "$value" ] || die "group message must not be empty"
      msgs+=("$value")
      expect="group"
      ;;
    *)
      if [ "$expect" = "base" ]; then
        die "groups file must open with a 'base <sha>' line; got: $line"
      fi
      die "groups file must alternate 'group <count>' and 'msg <subject>' lines; got: $line"
      ;;
  esac
done < "$groups_file"
[ "$expect" = "group" ] || die "the groups file ends with an unmatched 'group' line"
[ "${#counts[@]}" -ge 1 ] || die "the groups file carries no groups"
[ "${#counts[@]}" -eq "${#msgs[@]}" ] || die "malformed groups file (group/msg pairs do not alternate)"
case "$base_sha" in
  [0-9a-fA-F]*) : ;;
  *) die "bad base sha in groups file: $base_sha" ;;
esac

main_tip="$(git rev-parse refs/heads/main)"
resolved_base="$(git rev-parse --verify --quiet "$base_sha^{commit}" 2>/dev/null)" || resolved_base=""
if [ -z "$resolved_base" ] || [ "$resolved_base" != "$main_tip" ]; then
  if [ -n "$resolved_base" ] && git merge-base --is-ancestor "$resolved_base" "$main_tip" 2>/dev/null; then
    regroup "main advanced past the groups base ${resolved_base}; a concurrent commit landed - regroup from the new tip"
  fi
  regroup "the groups base ${base_sha} is not the current main tip ${main_tip}; regroup from the new tip"
fi

# A merge commit anywhere fails the tiling, naming the offending commit; the
# range is then not linear and consecutive-count groups cannot tile it.
merge_shas="$(git rev-list --min-parents=2 "$upstream..refs/heads/main")"
if [ -n "$merge_shas" ]; then
  for m in $merge_shas; do
    printf 'release-rewrite: FATAL: merge commit %s sits inside the publish delta %s; a release needs a linear range\n' \
      "$m" "$upstream..refs/heads/main" >&2
  done
  exit 1
fi

range_count="$(git rev-list --count "$upstream..refs/heads/main")"
total=0
for c in "${counts[@]}"; do
  total=$((total + c))
done
[ "$total" -eq "$range_count" ] || die "groups tile $total of $range_count publish-delta commits; counts must sum to the range size"

commits=()
while IFS= read -r sha; do
  [ -n "$sha" ] || continue
  commits+=("$sha")
done < <(git rev-list --reverse "$upstream..refs/heads/main")
[ "${#commits[@]}" -eq "$range_count" ] || die "publish-delta enumeration disagrees with the range count"

# 7. Scratch roots: an ad-hoc rewrite worktree OUTSIDE the repo tree on a temp
#    branch, plus the hygiene materialization root and the run dir. All are
#    torn down by the EXIT trap on every path.
run_tmp="$(mktemp -d "${TMPDIR:-/tmp}/release-run-XXXXXXXX")"
base_short="${base_tip:0:10}"
hygiene_root="$(mktemp -d "${TMPDIR:-/tmp}/release-hygiene-${base_short}.XXXXXXXX")"
wt_parent="$(mktemp -d "${TMPDIR:-/tmp}/release-wt-XXXXXXXX")"
worktree_path="$wt_parent/wt"
temp_branch="release-rewrite-tmp-$(date +%Y%m%d%H%M%S)-$$"
git worktree add -q -b "$temp_branch" "$worktree_path" "$base_tip" \
  || die "cannot create the rewrite worktree at $worktree_path"

# 8. Privacy gate setup: resolve the scanner ONCE from the PRIMARY checkout's
#    repo-relative path (never the base-tip copy inside the rewrite worktree),
#    copy its bytes plus the resolved patterns file into the run temp dir, and
#    execute those immutable copies for every invocation.
scanner_rel="${RELEASE_HYGIENE_SCANNER:-scripts/scan-public-hygiene.sh}"
scanner_src="$top/$scanner_rel"
[ -f "$scanner_src" ] || die "hygiene scanner not found in the primary checkout: $scanner_src"
scanner_copy="$run_tmp/scan-public-hygiene.sh"
cp "$scanner_src" "$scanner_copy"
patterns_copy=""
if [ -n "${PUBLIC_HYGIENE_PATTERNS_FILE:-}" ]; then
  # Fail closed: an override naming a missing file must abort the run, never
  # silently drop the override and scan with the defaults the operator
  # explicitly replaced.
  [ -f "$PUBLIC_HYGIENE_PATTERNS_FILE" ] \
    || die "PUBLIC_HYGIENE_PATTERNS_FILE is set but the file does not exist: ${PUBLIC_HYGIENE_PATTERNS_FILE}; refusing to run the privacy gate without the override"
  cp "$PUBLIC_HYGIENE_PATTERNS_FILE" "$run_tmp/hygiene.patterns"
  patterns_copy="$run_tmp/hygiene.patterns"
  printf 'release-rewrite: PUBLIC_HYGIENE_PATTERNS_FILE override in effect: %s (scan copy: %s)\n' \
    "$PUBLIC_HYGIENE_PATTERNS_FILE" "$patterns_copy" >&2
fi
# The authored group messages become pushed commit subjects, so the groups
# file is scanned too; the copy lands inside the materialization root.
cp "$groups_file" "$hygiene_root/release-groups.txt"

# invoke_scanner: run the immutable scanner copies in explicit-paths mode with
# PUBLIC_HYGIENE_REPO_ROOT at the materialization root. Paths come from the
# global scan_call_paths array (the script's own invocation argument list).
# stdout is discarded (its FAIL blocks echo file content), stderr is captured
# and only skip-note lines re-emitted; any non-zero exit aborts with a
# sentinel line carrying the scanner exit code and the offending PATHS ONLY.
invoke_scanner() {
  scan_rc=0
  scan_err="$run_tmp/scanner-stderr.txt"
  if [ -n "$patterns_copy" ]; then
    PUBLIC_HYGIENE_REPO_ROOT="$hygiene_root" PUBLIC_HYGIENE_PATTERNS_FILE="$patterns_copy" \
      bash "$scanner_copy" --files "${scan_call_paths[@]}" >/dev/null 2>"$scan_err" || scan_rc=$?
  else
    PUBLIC_HYGIENE_REPO_ROOT="$hygiene_root" \
      bash "$scanner_copy" --files "${scan_call_paths[@]}" >/dev/null 2>"$scan_err" || scan_rc=$?
  fi
  if [ -s "$scan_err" ]; then
    grep -F 'skipped excluded path' "$scan_err" >&2 || true
  fi
  if [ "$scan_rc" -ne 0 ]; then
    printf 'PRIVACY GATE FAILED (scanner exit %s): offending paths: %s\n' \
      "$scan_rc" "${scan_call_paths[*]}" >&2
    if [ "$scan_rc" -eq 2 ]; then
      # Exit 2 of this script is reserved for REGROUP REQUIRED; a scanner
      # environment failure (no scan verdict) gets its own exit code.
      exit 3
    fi
    exit "$scan_rc"
  fi
}

# scan_commit: materialize one rewritten commit's ACMRT paths into the
# materialization root at their ORIGINAL repo-relative locations (so the
# scanner's exclusion shapes match deterministically) and scan them
# immediately, before any later commit's paths are materialized. A commit
# whose ACMRT list is empty (deletion-only) is skipped with a note, never
# invoked with zero paths (the scanner exits 2 on an empty list).
scan_commit() {
  scan_c="$1"
  scan_call_paths=()
  while IFS= read -r -d '' p; do
    scan_call_paths+=("$p")
  done < <(git diff --name-only -z --diff-filter=ACMRT "${scan_c}^" "$scan_c")
  if [ "${#scan_call_paths[@]}" -eq 0 ]; then
    printf 'privacy gate: skip commit %s (no added/copied/modified/renamed/typechanged paths; deletion-only change)\n' "$scan_c" >&2
    return 0
  fi
  for p in "${scan_call_paths[@]}"; do
    case "$p" in
      /*|-*|*.lock) die "unexpected publish-delta path form: $p" ;;
    esac
    dest="$hygiene_root/$p"
    # The root is script-owned scratch for this run alone (per-run-unique
    # mktemp root), so anything already occupying the destination path is
    # this run's own leftover: a file where this commit needs a directory,
    # or a directory where it needs a file. A file-vs-dir shape flip across
    # commits is legal history; clear the path before materializing.
    rm -rf "$dest"
    mkdir -p "$(dirname "$dest")"
    if ! git show "$scan_c:$p" > "$dest"; then
      rm -f "$dest"
      die "git show failed for $scan_c:$p; refusing to scan a partially written blob"
    fi
  done
  invoke_scanner
}

# 9. Rewrite loop, oldest group first, inside the ad-hoc worktree. Per group:
#    reset --hard to the group's newest original commit, reset --soft to the
#    previous rewritten tip (seeded with the base tip), one commit carrying
#    the group message and the oldest original commit's author name and date.
#    Each rewritten commit must carry exactly its group-newest original tree,
#    and the final rewritten tip must be byte-identical to the base tree.
#    stdout carries ONLY the rewritten tip; diagnostics go to stderr.
rewritten_tip="$(
  cd "$worktree_path" || exit 1
  cursor=0
  # The rewritten chain is rooted at the publish-delta base (the remote tip),
  # so the squashed history replaces the unpushed pile; the groups-file base
  # tip stays the compare-and-swap expected-old value below.
  prev_tip="$(git rev-parse "$upstream")"
  [ -n "$prev_tip" ] || exit 1
  gi=0
  while [ "$gi" -lt "${#counts[@]}" ]; do
    count="${counts[$gi]}"
    msg="${msgs[$gi]}"
    group_oldest="${commits[$cursor]}"
    group_newest="${commits[$((cursor + count - 1))]}"
    git reset --hard -q "$group_newest" || exit 1
    git reset --soft -q "$prev_tip" || exit 1
    author_name="$(git log -1 --format=%an "$group_oldest")"
    author_email="$(git log -1 --format=%ae "$group_oldest")"
    author_date="$(git log -1 --format=%aI "$group_oldest")"
    if ! GIT_AUTHOR_NAME="$author_name" GIT_AUTHOR_EMAIL="$author_email" GIT_AUTHOR_DATE="$author_date" \
        git commit -q -m "$msg"; then
      printf 'release-rewrite: FATAL: rewrite commit failed for group %d (%s): the net tree change of this group is empty (its commits cancel out), so there is nothing to commit; fold this group into a neighboring group and regroup\n' \
        "$((gi + 1))" "$msg" >&2
      exit 1
    fi
    new_tip="$(git rev-parse HEAD)"
    if ! git diff --quiet "$new_tip" "$group_newest"; then
      printf 'release-rewrite: FATAL: rewritten group %d tree diverges from its source tip %s\n' \
        "$((gi + 1))" "$group_newest" >&2
      exit 1
    fi
    printf 'release-rewrite: group %d/%d rewritten as %s\n' "$((gi + 1))" "${#counts[@]}" "$new_tip" >&2
    prev_tip="$new_tip"
    cursor=$((cursor + count))
    gi=$((gi + 1))
  done
  if ! git diff --quiet "$prev_tip" "$base_tip"; then
    printf 'release-rewrite: FATAL: the rewritten tree diverges from the base tree %s\n' "$base_tip" >&2
    exit 1
  fi
  # Privacy gate BEFORE the swap: every rewritten commit is scanned right
  # after its own materialization. The gate iterates the ORIGINAL delta
  # commits (git rev-list upstream..main), not the folded rewritten group
  # commits: each original commit diff is scanned on its own, which is
  # strictly stronger than scanning only the group-level diffs. Intentional.
  # NOTE: comments inside this substitution must not contain apostrophes;
  # bash 3.2 misparses quotes in comments inside a command substitution.
  ri=0
  while [ "$ri" -lt "${#commits[@]}" ]; do
    scan_commit "${commits[$ri]}"
    ri=$((ri + 1))
  done
  scan_call_paths=("release-groups.txt")
  invoke_scanner
  printf '%s\n' "$prev_tip"
)"
[ -n "$rewritten_tip" ] || die "the rewrite produced no tip"

# 10. Compare-and-swap main to the rewritten tip; expected-old is the groups
#     base tip. A mismatch means a concurrent commit landed: regroup.
if ! git update-ref "refs/heads/main" "$rewritten_tip" "$base_tip"; then
  regroup "main moved during the rewrite (expected ${base_tip}, found $(git rev-parse refs/heads/main 2>/dev/null || echo unknown)); regroup from the new tip - the backup ref ${backup_ref} holds the pre-rewrite state"
fi

# 11. Post-swap status snapshot (hashed, never stored raw) and the persisted
#     push script: 0700, outside the trap-owned dirs, carrying the pre-push
#     re-assertions followed by the verified-value fast-forward publish. The
#     script removes itself on every exit via its own EXIT trap.
snapshot="$(git status --porcelain | shasum -a 256 | cut -d' ' -f1)"
push_script="$(mktemp "${TMPDIR:-/tmp}/release-push-${base_short}.XXXXXXXX")"
chmod 700 "$push_script"
{
  printf '#!/usr/bin/env bash\n'
  printf '# Generated by release-rewrite.sh: publish the verified release exactly once.\n'
  printf '# Every pre-push re-assertion runs first; any mismatch aborts BEFORE the\n'
  printf '# publish step, and the script removes itself on every exit.\n'
  printf 'set -euo pipefail\n'
  printf "trap 'rm -f -- \"\$0\"' EXIT\n"
  printf 'EXPECTED_TIP=%q\n' "$rewritten_tip"
  printf 'BACKUP_REF=%q\n' "$backup_ref"
  printf 'SNAPSHOT_SHA=%q\n' "$snapshot"
  printf 'REMOTE=%q\n' "$remote"
  printf 'REPO_ROOT=%q\n' "$top"
  cat <<'PUSH_BODY'

cd "$REPO_ROOT" || exit 1

push_abort() {
  echo "release push: ABORT: $1" >&2
  echo "release push: nothing was published. Restore path: reset main to the backup ref with 'git reset --hard \"$BACKUP_REF\"' (or 'git update-ref refs/heads/main \"$BACKUP_REF\" \"$EXPECTED_TIP\"'), reconcile with the advanced origin, then re-run the release." >&2
  exit 1
}

current_tip="$(git rev-parse refs/heads/main)"
[ "$current_tip" = "$EXPECTED_TIP" ] || push_abort "main (${current_tip}) no longer equals the rewritten tip (${EXPECTED_TIP})"
current_snapshot="$(git status --porcelain | shasum -a 256 | cut -d' ' -f1)"
[ "$current_snapshot" = "$SNAPSHOT_SHA" ] || push_abort "the working tree changed after the swap (post-swap status snapshot mismatch)"
git fetch --quiet "$REMOTE" || push_abort "git fetch $REMOTE failed"
git merge-base --is-ancestor "refs/remotes/$REMOTE/main" "$EXPECTED_TIP" \
  || push_abort "$REMOTE/main advanced past the rewritten tip; reconcile and re-run the release"
echo "release push: re-assertions hold; publishing the verified commit as a plain fast-forward (forced updates are never used)"
PUSH_BODY
  printf 'git push %q %q:refs/heads/main\n' "$remote" "$rewritten_tip"
  printf 'echo "release push: done; %s/main now carries the squashed release at %s"\n' "$remote" "$rewritten_tip"
} > "$push_script"

printf 'release-rewrite: swap complete; main is at the rewritten tip %s\n' "$rewritten_tip" >&2
printf 'release-rewrite: post-swap status snapshot sha256: %s\n' "$snapshot" >&2
printf 'release-rewrite: backup ref (local-only, never published): %s\n' "$backup_ref" >&2
printf 'release-rewrite: push script (execute it to publish): %s\n' "$push_script" >&2
# The push script path is this script's entire stdout contract.
printf '%s\n' "$push_script"
