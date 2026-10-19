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
authoring_run_dir=""

die() {
  printf 'release-rewrite: FATAL: %s\n' "$*" >&2
  exit 1
}

# The recovery refusal sentinel: every recovery precondition refusal carries
# this prefix, so a usage error can never satisfy a recovery refusal check.
rec_fail() {
  printf 'release-rewrite: RECOVERY REFUSED: %s\n' "$*" >&2
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
  # Tear down the authoring step's run dir (the groups file's producer
  # directory) at the rewrite's exit. The guard never removes an arbitrary
  # caller-supplied directory: only one sitting DIRECTLY under the
  # canonicalized temp root with the mktemp pattern's name. The canonicalized
  # root keeps a trailing-slash TMPDIR from desynchronizing the comparison
  # (dirname output is already canonical).
  if [ -n "$authoring_run_dir" ]; then
    tmpdir_root="$(cd "${TMPDIR:-/tmp}" 2>/dev/null && pwd)" || tmpdir_root=""
    case "$authoring_run_dir" in
      "$tmpdir_root"/release-authoring-*) rm -rf "$authoring_run_dir" || true ;;
    esac
  fi
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

# Argument parsing: the ordinary one-positional contract is unchanged; the
# recovery mode is selected by the two flags appearing TOGETHER, each at most
# once, each followed by its value. Anything else is a usage FATAL naming
# both recovery flags.
recovery_base=""
expect_remote_oid=""
recovery_mode=0
if [ "$#" -eq 1 ]; then
  :
elif [ "$#" -eq 5 ] && [ "$2" = "--recovery-base" ] && [ "$4" = "--expect-remote-oid" ]; then
  recovery_base="$3"
  expect_remote_oid="$5"
  recovery_mode=1
else
  die "usage: release-rewrite.sh <groups-file> [--recovery-base <oid> --expect-remote-oid <oid>]; the two recovery flags are accepted together, each exactly once, each followed by its value (got $# arguments)"
fi
groups_in="$1"
groups_dir="$(dirname "$groups_in")"
groups_file="$(cd "$groups_dir" 2>/dev/null && pwd)/$(basename "$groups_in")"
[ -f "$groups_file" ] || die "groups file not found: $groups_in"
# The authoring run dir is the groups file's own directory: the two steps are
# sibling processes (an export in one never reaches the other), so the file
# path is the only channel between them. The EXIT trap removes it under the
# TMPDIR mktemp-shape guard above.
authoring_run_dir="$(dirname "$groups_file")"

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

# 3. Fetch; then split by mode: ordinary mode refuses a diverged remote
#    (local main must be a descendant of <remote>/main, bytes unchanged);
#    recovery mode routes to its own precondition gate (selected base, the
#    expected remote OID, and the recovery-only delta admission).
git fetch --quiet "$remote" || die "git fetch $remote failed"
git rev-parse --verify --quiet "$upstream" >/dev/null 2>&1 || die "$upstream not found after fetch"
if [ "$recovery_mode" -eq 1 ]; then
  sel_base="$(git rev-parse --verify --quiet "${recovery_base}^{commit}" 2>/dev/null)" || sel_base=""
  [ -n "$sel_base" ] || rec_fail "the selected base ${recovery_base} does not resolve to a commit"
  recovery_main_tip="$(git rev-parse refs/heads/main)"
  [ "$sel_base" != "$recovery_main_tip" ] || rec_fail "the selected base equals the current main tip; nothing to recover"
  git merge-base --is-ancestor "$sel_base" refs/heads/main \
    || rec_fail "the selected base ${sel_base} is not an ancestor of main"
  # Capture-then-match, never `grep -q` in a pipeline: grep's early exit on a
  # match SIGPIPEs rev-list, and pipefail would read that as a miss.
  first_parent_line="$(git rev-list --first-parent refs/heads/main)"
  case "$first_parent_line" in
    *"$sel_base"*) : ;;
    *) rec_fail "the selected base ${sel_base} is not on main's first-parent line; the recovery tiling would not be exhaustive" ;;
  esac
  upstream_oid="$(git rev-parse --verify "$upstream")"
  [ "$upstream_oid" = "$expect_remote_oid" ] \
    || rec_fail "the fetched ${remote}/main (${upstream_oid}) does not equal the expected remote OID observed at authorization (${expect_remote_oid}); re-observe the remote tip and re-authorize the recovery"
  recovery_merge_shas="$(git rev-list --min-parents=2 "${upstream}..refs/heads/main")"
  if [ -z "$recovery_merge_shas" ] && git merge-base --is-ancestor "$upstream" refs/heads/main; then
    rec_fail "the publish delta is releasable by the ordinary release flow (no merge inside the delta and no divergence); use the ordinary release instead"
  fi
else
  if ! git merge-base --is-ancestor "$upstream" refs/heads/main; then
    die "main is not a descendant of $remote/main; reconcile with the remote before releasing"
  fi
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

# A merge commit anywhere fails the ordinary tiling, naming the offending
# commit; the range is then not linear and consecutive-count groups cannot
# tile it. Ordinary mode only: a recovery invocation skips this scan and
# reaches its own first-parent enumeration below.
if [ "$recovery_mode" -eq 0 ]; then
  merge_shas="$(git rev-list --min-parents=2 "$upstream..refs/heads/main")"
  if [ -n "$merge_shas" ]; then
    for m in $merge_shas; do
      printf 'release-rewrite: FATAL: merge commit %s sits inside the publish delta %s; a release needs a linear range\n' \
        "$m" "$upstream..refs/heads/main" >&2
    done
    exit 1
  fi
fi

commits=()
if [ "$recovery_mode" -eq 1 ]; then
  # The first-parent segment AFTER the selected base: git's first-parent
  # range walk keeps the range's own base commit in the listing, so the
  # selected base is filtered out explicitly and the count derives from
  # the filtered enumeration.
  while IFS= read -r sha; do
    [ -n "$sha" ] || continue
    if [ "$sha" = "$sel_base" ]; then continue; fi
    commits+=("$sha")
  done < <(git rev-list --reverse --first-parent "${sel_base}..refs/heads/main")
  range_count="${#commits[@]}"
else
  range_count="$(git rev-list --count "$upstream..refs/heads/main")"
  while IFS= read -r sha; do
    [ -n "$sha" ] || continue
    commits+=("$sha")
  done < <(git rev-list --reverse "$upstream..refs/heads/main")
fi
total=0
for c in "${counts[@]}"; do
  total=$((total + c))
done
[ "$total" -eq "$range_count" ] || die "groups tile $total of $range_count publish-delta commits; counts must sum to the range size"
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
# The caller discards scanner stdout, so the scanner's final `OUTCOME:` line
# (scripts/OUTCOME_CONTRACT.md) is not consumed here; the branch keys on the
# scanner's own-error class (tool error, exit 3) and the findings fall-through
# keeps its mapping.
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
    if [ "$scan_rc" -eq 2 ] || [ "$scan_rc" -eq 3 ]; then
      # The scanner's own-error classes (environment error, exit 2, and tool
      # error under the outcome contract, exit 3) abort the release on the
      # tool-error exit 3, never as a REGROUP-class exit 2 of this script.
      exit 3
    fi
    exit "$scan_rc"
  fi
}

# scan_commit: removed 2026-09-27 (operator directive). The gate no longer
# scans every original delta commit: per-commit scanning was unneeded work
# that made any historically dirty pile unpublishable even when the published
# trees are clean, because a blob added and later cleaned inside the pile
# kept failing the gate forever. The gate now scans the RESULT once: the
# rewritten tip tree, materialized below after the tree-identity gate.

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
  # The rewritten chain is rooted at the publish-delta base: the remote tip
  # in ordinary mode, the operator-selected first-parent base in recovery
  # mode. The groups-file base tip stays the compare-and-swap expected-old
  # value below.
  if [ "$recovery_mode" -eq 1 ]; then
    prev_tip="$sel_base"
  else
    prev_tip="$(git rev-parse "$upstream")"
  fi
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
  printf '%s\n' "$prev_tip"
)"
[ -n "$rewritten_tip" ] || die "the rewrite produced no tip"

# 10. Privacy gate BEFORE the swap: scan the published RESULT once. The
#     rewritten tip tree is exactly the content the release publishes, so the
#     gate materializes it into the hygiene root and scans every tracked
#     regular-file blob plus the groups file (the authored messages).
#     Operator directive 2026-09-27: per-original-commit scanning was retired
#     as unneeded work; dirt added and cleaned inside the pile never reaches
#     the result. The gate runs in the main shell (never inside a command
#     substitution: bash 3.2 misparses case statements and comment quotes
#     there).
if ! git archive "$rewritten_tip" | tar -x -C "$hygiene_root"; then
  die "materializing the rewritten tip tree ${rewritten_tip} for the privacy gate failed"
fi
scan_call_paths=()
# Regular-file blobs only: symlinks (120000) and gitlinks (160000) carry no
# scannable blob content, and naming them would fail the scanner existence
# check and abort the run as an environment failure.
while IFS= read -r -d '' entry; do
  meta="${entry%%$'\t'*}"
  p="${entry#*$'\t'}"
  case "$meta" in
    100644*|100755*) ;;
    *) continue ;;
  esac
  [ -n "$p" ] || continue
  scan_call_paths+=("$p")
done < <(git ls-tree -r -z "$rewritten_tip")
if [ "${#scan_call_paths[@]}" -eq 0 ]; then
  die "the rewritten tip tree ${rewritten_tip} is empty; nothing to scan"
fi
scan_call_paths+=("release-groups.txt")
printf 'release-rewrite: privacy gate scanning the published result: %d files\n' "${#scan_call_paths[@]}" >&2
invoke_scanner

# 11. Compare-and-swap main to the rewritten tip; expected-old is the groups
#     base tip. A mismatch means a concurrent commit landed: regroup.
if ! git update-ref "refs/heads/main" "$rewritten_tip" "$base_tip"; then
  regroup "main moved during the rewrite (expected ${base_tip}, found $(git rev-parse refs/heads/main 2>/dev/null || echo unknown)); regroup from the new tip - the backup ref ${backup_ref} holds the pre-rewrite state"
fi

# 11. Post-swap status snapshot (hashed, never stored raw) and the persisted
#     push script: 0700, outside the trap-owned dirs, carrying the pre-push
#     re-assertions followed by the verified-value fast-forward publish. The
#     script removes itself on every exit via its own EXIT trap.
snapshot="$(git status --porcelain --untracked-files=no | shasum -a 256 | cut -d' ' -f1)"
push_script="$(mktemp "${TMPDIR:-/tmp}/release-push-${base_short}.XXXXXXXX")"
chmod 700 "$push_script"
if [ "$recovery_mode" -eq 1 ]; then
  # The recovery variant carries the recovery constants and its own 0700
  # asset directory: an immutable groups-file copy and an immutable copy of
  # the privacy scanner (plus the resolved patterns copy when the override
  # is set), so the push-time re-scan uses the same immutable scheme after
  # the rewrite's EXIT trap has removed the originals.
  final_tree="$(git rev-parse "${rewritten_tip}^{tree}")"
  push_asset="$(mktemp -d "${TMPDIR:-/tmp}/release-hygiene-push-${base_short}.XXXXXXXX")"
  cp "$scanner_src" "$push_asset/scan-public-hygiene.sh"
  chmod 755 "$push_asset/scan-public-hygiene.sh"
  push_patterns_copy=""
  if [ -n "$patterns_copy" ]; then
    cp "$patterns_copy" "$push_asset/hygiene.patterns"
    push_patterns_copy="$push_asset/hygiene.patterns"
  fi
  cp "$groups_file" "$push_asset/release-groups.txt"
  {
    printf '#!/usr/bin/env bash\n'
    printf '# Generated by release-rewrite.sh (recovery mode): publish the verified\n'
    printf '# recovery exactly once, lease-bound to the observed remote state. Every\n'
    printf '# pre-push re-assertion runs first; any mismatch aborts BEFORE the publish\n'
    printf '# step, and the script removes itself and its asset directory on every exit.\n'
    printf 'set -euo pipefail\n'
    printf "cleanup_push() { rm -f -- \"\$0\" 2>/dev/null || true; if [ -n \"\${scan_mat:-}\" ]; then rm -rf -- \"\$scan_mat\" || true; fi; if [ -n \"\${ASSET_DIR:-}\" ]; then rm -rf -- \"\$ASSET_DIR\" || true; fi; }\n"
    printf 'trap cleanup_push EXIT\n'
    printf 'EXPECTED_TIP=%q\n' "$rewritten_tip"
    printf 'BACKUP_REF=%q\n' "$backup_ref"
    printf 'SNAPSHOT_SHA=%q\n' "$snapshot"
    printf 'REMOTE=%q\n' "$remote"
    printf 'REPO_ROOT=%q\n' "$top"
    printf 'EXPECTED_REMOTE_OID=%q\n' "$expect_remote_oid"
    printf 'FINAL_TREE=%q\n' "$final_tree"
    printf 'ASSET_DIR=%q\n' "$push_asset"
    printf 'PATTERNS_COPY=%q\n' "$push_patterns_copy"
    cat <<'PUSH_BODY'

cd "$REPO_ROOT" || exit 1

push_abort() {
  echo "release push: RECOVERY ABORT: $1" >&2
  echo "release push: nothing was published. Restore path: reset main to the backup ref with 'git reset --hard \"$BACKUP_REF\"' (or 'git update-ref refs/heads/main \"$BACKUP_REF\" \"$EXPECTED_TIP\"'), then re-run from Step 1 so the new tree is re-proven and re-scanned." >&2
  exit 1
}

current_tip="$(git rev-parse refs/heads/main)"
[ "$current_tip" = "$EXPECTED_TIP" ] || push_abort "main (${current_tip}) no longer equals the rewritten tip (${EXPECTED_TIP}); re-run from Step 1 so the new tree is re-proven and re-scanned"
current_snapshot="$(git status --porcelain --untracked-files=no | shasum -a 256 | cut -d' ' -f1)"
[ "$current_snapshot" = "$SNAPSHOT_SHA" ] || push_abort "the working tree changed after the swap (post-swap status snapshot mismatch); re-run from Step 1 so the new tree is re-proven and re-scanned"
git fetch --quiet "$REMOTE" || push_abort "git fetch $REMOTE failed"
remote_oid="$(git rev-parse "refs/remotes/$REMOTE/main")"
[ "$remote_oid" = "$EXPECTED_REMOTE_OID" ] || push_abort "$REMOTE/main (${remote_oid}) no longer equals the expected remote OID observed at authorization (${EXPECTED_REMOTE_OID}); re-observe the remote tip and re-authorize the recovery, then re-run from Step 1 so the new tree is re-proven and re-scanned"
current_tree="$(git rev-parse "refs/heads/main^{tree}")"
[ "$current_tree" = "$FINAL_TREE" ] || push_abort "main's tree no longer equals the captured final tree; re-run from Step 1 so the new tree is re-proven and re-scanned"

# Publish-boundary verification: the tree proof ran above against the
# captured final tree; the privacy re-scan runs over the materialized
# current tree plus the immutable groups-file copy, on every legitimate
# publish, before anything is published.
scan_mat="$(mktemp -d "${TMPDIR:-/tmp}/release-scan-XXXXXXXX")"
git archive "refs/heads/main" | tar -x -C "$scan_mat" || push_abort "materializing the tree for the privacy re-scan failed"
cp "$ASSET_DIR/release-groups.txt" "$scan_mat/release-groups.txt"
scan_paths=()
while IFS= read -r -d '' entry; do
  meta="${entry%%$'\t'*}"; p="${entry#*$'\t'}"
  case "$meta" in
    100644*|100755*) ;;
    *) continue ;;
  esac
  [ -n "$p" ] || continue
  scan_paths+=("$p")
done < <(git ls-tree -r -z "refs/heads/main")
scan_paths+=("release-groups.txt")
if [ -n "$PATTERNS_COPY" ]; then
  PUBLIC_HYGIENE_REPO_ROOT="$scan_mat" PUBLIC_HYGIENE_PATTERNS_FILE="$PATTERNS_COPY" \
    bash "$ASSET_DIR/scan-public-hygiene.sh" --files "${scan_paths[@]}" >/dev/null 2>&1 \
    || push_abort "the privacy re-scan hit on the publish boundary; re-run from Step 1 so the new tree is re-proven and re-scanned"
else
  PUBLIC_HYGIENE_REPO_ROOT="$scan_mat" \
    bash "$ASSET_DIR/scan-public-hygiene.sh" --files "${scan_paths[@]}" >/dev/null 2>&1 \
    || push_abort "the privacy re-scan hit on the publish boundary; re-run from Step 1 so the new tree is re-proven and re-scanned"
fi
echo "release push: re-assertions hold; publishing the recovery as a lease-bound force bound to the observed remote state"
PUSH_BODY
    printf 'git push --force-with-lease=refs/heads/main:%q %q %q:refs/heads/main\n' "$expect_remote_oid" "$remote" "$rewritten_tip"
    printf 'echo "release push: done; %s/main now carries the recovered release at %s"\n' "$remote" "$rewritten_tip"
  } > "$push_script"
else
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
current_snapshot="$(git status --porcelain --untracked-files=no | shasum -a 256 | cut -d' ' -f1)"
[ "$current_snapshot" = "$SNAPSHOT_SHA" ] || push_abort "the working tree changed after the swap (post-swap status snapshot mismatch)"
git fetch --quiet "$REMOTE" || push_abort "git fetch $REMOTE failed"
git merge-base --is-ancestor "refs/remotes/$REMOTE/main" "$EXPECTED_TIP" \
  || push_abort "$REMOTE/main advanced past the rewritten tip; reconcile and re-run the release"
echo "release push: re-assertions hold; publishing the verified commit as a plain fast-forward (forced updates are never used)"
PUSH_BODY
    printf 'git push %q %q:refs/heads/main\n' "$remote" "$rewritten_tip"
    printf 'echo "release push: done; %s/main now carries the squashed release at %s"\n' "$remote" "$rewritten_tip"
  } > "$push_script"
fi

printf 'release-rewrite: swap complete; main is at the rewritten tip %s\n' "$rewritten_tip" >&2
printf 'release-rewrite: post-swap status snapshot sha256: %s\n' "$snapshot" >&2
printf 'release-rewrite: backup ref (local-only, never published): %s\n' "$backup_ref" >&2
printf 'release-rewrite: push script (execute it to publish): %s\n' "$push_script" >&2
# The push script path is this script's entire stdout contract.
printf '%s\n' "$push_script"
