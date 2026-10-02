#!/usr/bin/env bash
# land_squash.sh: the lock-bound squash-landing helper for a primary checkout.
#
# The only sanctioned way to run a squash landing into a primary checkout
# (the witnessed incident class: archive riders, ad-hoc maintenance landings,
# manual recoveries). It refuses to run outside a live, token-matching merge
# lock, verifies the primary checkout's HEAD is the base branch at the
# caller's expected tip, snapshots porcelain before touching anything, refuses
# the start when staged state exists or when a locally dirty tracked path
# intersects the branch's changed paths, runs the squash, and on ANY failure
# restores the index and worktree PATH-EXCLUSIVELY (never a blanket restore),
# exiting per the declared outcome mapping and naming the failure and every
# restored, removed, skipped, or left-in-place path.
#
# Modes:
#   probe --branch <source-branch>
#       The pre-lock gate: containment plus a git merge-tree --write-tree
#       conflict trial, run WITHOUT the lock, mutating nothing. Gates lock
#       acquisition; on a fail the rebase or conflict resolution happens in
#       the execution worktree before the lock is acquired.
#   land --branch <source-branch> --expected-tip <sha> --message <text>
#        [--expected-base <sha>]
#       The landing itself, under the lock. --expected-base (the caller's
#       recorded base pin) is forwarded to the parentage gate's pre-swap leg
#       when provided and the leg is skipped otherwise.
#
# Outcome contract (scripts/OUTCOME_CONTRACT.md): born-conformant; every
# non-metadata run ends with exactly one final `OUTCOME: <pass|fail|
# indeterminate|tool_error>` line on stdout matching the exit code
# (0/1/2/3). --help is a metadata exit and emits no OUTCOME line.
#
# Test-only fault seam (never set in production; every honored seam prints a
# loud evidence line naming the value and its env):
#   LAND_SQUASH_TEST_FAULT=dirty-writer  fires immediately after the snapshot
#       and appends one line to the tracked path named by the test-only
#       LAND_SQUASH_TEST_FAULT_PATH, exercising the changed-since-snapshot
#       writer block.
#   LAND_SQUASH_TEST_FAULT=backward-peer fires immediately after the CAS
#       succeeds and moves the base to <expected-tip>~1 (a commit that does
#       not descend from the pre-landing tip).
#   LAND_SQUASH_TEST_FAULT=diverge-origin fires at the same point and
#       redirects the post-landing invocation's --origin-ref to the forged
#       fixture ref refs/remotes/land-squash-fault/diverged.
#
# The script carries no in-file selftest mode: the python unittest suite
# scripts/test_land_squash.py is the fixture layer.
set -euo pipefail

PROG="land-squash"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENTAGE_GATE="$SCRIPT_DIR/landing_parentage_gate.py"

usage() {
  cat <<'EOF'
Usage: land_squash.sh probe --branch <source-branch>
       land_squash.sh land --branch <source-branch> --expected-tip <sha>
                           --message <text> [--expected-base <sha>]

Modes:
  probe   Pre-lock gate: containment (the source branch tip must contain the
          live base branch tip) plus a git merge-tree --write-tree conflict
          trial. Runs without the merge-lock environment and mutates nothing.
          On a fail, compose the rebase or conflict resolution in the
          execution worktree BEFORE acquiring the lock.
  land    The landing under a verified merge lock: lock authenticity (both
          MERGE_LOCK_DIR and MERGE_LOCK_TOKEN non-empty, the directory live,
          meta.env readable with a non-empty lock_token equal to
          MERGE_LOCK_TOKEN, and the record's repo_root equal to the resolved
          primary checkout root), base-branch resolution via git symbolic-ref
          (a detached primary HEAD is a tool error), ref-level tip and
          checked-out HEAD verification against --expected-tip, a porcelain
          snapshot, staged-state and dirty-intersection pre-refusals, a
          guarded git merge --squash, tree equality between the source branch
          tree and the composed index tree before commit-tree, the parentage
          gate's pre-swap invocation (with --source-branch and the optional
          --expected-base passthrough), a two-value compare-and-swap
          git update-ref, the parentage gate's post-landing invocation with
          --origin-ref refs/remotes/origin/<resolved-base-branch>, and the
          final new-tip report with its first-parent diffstat.

Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
with exactly one final `OUTCOME: <pass|fail|indeterminate|tool_error>` line
on stdout matching the exit code: 0 pass; 1 fail (a modeled refusal: the
prechecks, the tip-moved class, the tree-equality assertion, or a propagated
gate fail); 2 indeterminate (a land-time merge failure, the interleaved-tip
refusal, or a mid-restore pipeline failure naming the unrestored paths);
3 tool error (lock authenticity, detached HEAD, or an unresolvable ref).
--help is a metadata exit and emits no OUTCOME line.

Test-only fault seam (fixtures only; production never sets these; every
honored seam prints a loud evidence line naming the value and its env):
  LAND_SQUASH_TEST_FAULT=dirty-writer with LAND_SQUASH_TEST_FAULT_PATH
      appends a writer line to the named tracked path after the snapshot.
  LAND_SQUASH_TEST_FAULT=backward-peer moves the base to <expected-tip>~1
      immediately after the CAS succeeds.
  LAND_SQUASH_TEST_FAULT=diverge-origin redirects the post-landing origin
      leg to refs/remotes/land-squash-fault/diverged.
EOF
}

emit_outcome() {
  echo "OUTCOME: $1"
}

tool_error() {
  echo "tool error: $*"
  emit_outcome tool_error
  exit 3
}

meta_field() {
  # Read KEY=value from the lock record without sourcing it.
  local meta="$1" key="$2" line=""
  line="$(grep -E "^${key}=" "$meta" 2>/dev/null | head -n1 || true)"
  printf '%s' "${line#${key}=}"
}

resolve_repo_root() {
  # The primary checkout root: the resolved git common dir minus .git,
  # physicalized the same way done-lock.sh keys the merge lock.
  local common_dir
  common_dir="$(git rev-parse --git-common-dir 2>/dev/null)" || \
    tool_error "not inside a git repository"
  common_dir="$(cd "$common_dir" 2>/dev/null && pwd -P)" || \
    tool_error "cannot resolve the git common dir: ${common_dir}"
  case "$common_dir" in
    */.git) REPO_ROOT="${common_dir%/.git}" ;;
    *) REPO_ROOT="$common_dir" ;;
  esac
}

SNAP_PATHS=()
SNAP_STATES=()

load_snapshot() {
  SNAP_PATHS=()
  SNAP_STATES=()
  local line p
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -n "$line" ]] || continue
    SNAP_STATES+=("${line:0:2}")
    p="${line:3}"
    case "$p" in
      *' -> ') p="${p##* -> }" ;;
    esac
    SNAP_PATHS+=("$p")
  done < "$1"
}

snapshot_contains() {
  local p="$1" i count
  count=${#SNAP_PATHS[@]}
  if [[ "$count" -eq 0 ]]; then
    return 1
  fi
  for i in "${!SNAP_PATHS[@]}"; do
    if [[ "${SNAP_PATHS[$i]}" == "$p" ]]; then
      return 0
    fi
  done
  return 1
}

snapshot_state_of() {
  local p="$1" i count
  count=${#SNAP_PATHS[@]}
  if [[ "$count" -eq 0 ]]; then
    return 1
  fi
  for i in "${!SNAP_PATHS[@]}"; do
    if [[ "${SNAP_PATHS[$i]}" == "$p" ]]; then
      printf '%s' "${SNAP_STATES[$i]}"
      return 0
    fi
  done
  return 1
}

snapshot_has_dirty() {
  # True when PATH was a locally modified tracked path at snapshot time.
  local p="$1" i count st y
  count=${#SNAP_PATHS[@]}
  if [[ "$count" -eq 0 ]]; then
    return 1
  fi
  for i in "${!SNAP_PATHS[@]}"; do
    if [[ "${SNAP_PATHS[$i]}" != "$p" ]]; then
      continue
    fi
    st="${SNAP_STATES[$i]}"
    if [[ "$st" == "??" ]]; then
      return 1
    fi
    y="${st:1:1}"
    if [[ "$y" != " " && "$y" != "?" && "$y" != "!" ]]; then
      return 0
    fi
    return 1
  done
  return 1
}

RESTORED=()
REMOVED=()
SKIPPED_WRITER=()
LEFT_IN_PLACE=()
UNRESTORED=()

in_path_list() {
  printf '%s\n' "$1" | grep -Fxq -- "$2"
}

run_restore() {
  # Derive the restore set at failure time per the plan's Terms and restore
  # it path by path: (a) the failure-time staged set (git diff --cached
  # --name-only HEAD, exactly the failed merge's residue because the index is
  # verified clean at snapshot) restored to HEAD; (b) untracked paths absent
  # from the snapshot (merge-created materialization) removed. Paths changed
  # since the snapshot outside both sets are a concurrent non-locking writer's
  # write and are skipped and named; paths dirty at snapshot time are never
  # restored and are named.
  RESTORED=()
  REMOVED=()
  SKIPPED_WRITER=()
  LEFT_IN_PLACE=()
  UNRESTORED=()
  local cur a_list line st p x
  cur="$(git -C "$REPO_ROOT" status --porcelain=v1)" || cur=""
  a_list="$(git -C "$REPO_ROOT" diff --cached --name-only HEAD)" || {
    UNRESTORED+=("(the failure-time staged set could not be derived: git diff --cached failed)")
    a_list=""
  }
  # Classify the not-restored paths before any mutation.
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    st="${line:0:2}"
    p="${line:3}"
    case "$p" in
      *' -> ') p="${p##* -> }" ;;
    esac
    if in_path_list "$a_list" "$p"; then
      continue
    fi
    if [[ "$st" == "??" ]]; then
      continue
    fi
    if snapshot_contains "$p"; then
      if [[ "$(snapshot_state_of "$p")" == "$st" ]]; then
        LEFT_IN_PLACE+=("$p")
      else
        SKIPPED_WRITER+=("$p")
      fi
    else
      SKIPPED_WRITER+=("$p")
    fi
  done <<< "$cur"
  # (b) merge-created untracked materialization: absent from the snapshot.
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    st="${line:0:2}"
    p="${line:3}"
    case "$p" in
      *' -> ') p="${p##* -> }" ;;
    esac
    if [[ "$st" == "??" ]] && ! snapshot_contains "$p"; then
      REMOVED+=("$p")
      rm -rf "${REPO_ROOT}/${p}"
    fi
  done <<< "$cur"
  # (a) restore the failure-time staged set to HEAD, path by path.
  while IFS= read -r p; do
    [[ -n "$p" ]] || continue
    if git -C "$REPO_ROOT" restore --staged --worktree -- "$p" >/dev/null 2>&1; then
      if git -C "$REPO_ROOT" cat-file -e "HEAD:${p}" 2>/dev/null; then
        RESTORED+=("$p")
      else
        REMOVED+=("$p")
      fi
    else
      UNRESTORED+=("$p")
    fi
  done <<< "$a_list"
}

print_restore_report() {
  local p
  if [[ ${#RESTORED[@]} -gt 0 ]]; then
    echo "restored to HEAD:"
    for p in "${RESTORED[@]}"; do echo "  ${p}"; done
  fi
  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "removed (created after the snapshot):"
    for p in "${REMOVED[@]}"; do echo "  ${p}"; done
  fi
  if [[ ${#SKIPPED_WRITER[@]} -gt 0 ]]; then
    echo "skipped (changed after the snapshot; a concurrent writer's bytes stay in place):"
    for p in "${SKIPPED_WRITER[@]}"; do echo "  ${p}"; done
  fi
  if [[ ${#LEFT_IN_PLACE[@]} -gt 0 ]]; then
    echo "left in place (dirty at snapshot; never restored):"
    for p in "${LEFT_IN_PLACE[@]}"; do echo "  ${p}"; done
  fi
}

restore_or_stop() {
  run_restore
  local p
  if [[ ${#UNRESTORED[@]} -gt 0 ]]; then
    echo "indeterminate: the restore pipeline failed mid-restore; unrestored paths (partial mutations left in place; the agent re-derives from disk):"
    for p in "${UNRESTORED[@]}"; do echo "  ${p}"; done
    emit_outcome indeterminate
    exit 2
  fi
}

print_gate_evidence() {
  # The gate's evidence lines without its own final OUTCOME line: the helper
  # emits exactly one final OUTCOME line per run.
  printf '%s\n' "$1" | grep -v '^OUTCOME: ' || true
}

# ---- argument parsing ------------------------------------------------------

MODE="${1:-}"
case "$MODE" in
  -h|--help|help)
    usage
    exit 0
    ;;
  probe|land)
    shift
    ;;
  "")
    usage >&2
    tool_error "a mode argument is required (probe or land)"
    ;;
  *)
    usage >&2
    tool_error "unknown mode: ${MODE} (expected probe or land)"
    ;;
esac

SOURCE_BRANCH=""
EXPECTED_TIP=""
MESSAGE=""
EXPECTED_BASE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      [[ $# -ge 2 && -n "${2:-}" ]] || tool_error "--branch requires a value"
      SOURCE_BRANCH="$2"
      shift 2
      ;;
    --expected-tip)
      [[ $# -ge 2 && -n "${2:-}" ]] || tool_error "--expected-tip requires a value"
      EXPECTED_TIP="$2"
      shift 2
      ;;
    --message)
      [[ $# -ge 2 && -n "${2:-}" ]] || tool_error "--message requires a value"
      MESSAGE="$2"
      shift 2
      ;;
    --expected-base)
      [[ $# -ge 2 && -n "${2:-}" ]] || tool_error "--expected-base requires a value"
      EXPECTED_BASE="$2"
      shift 2
      ;;
    *)
      tool_error "unknown argument: $1"
      ;;
  esac
done
[[ -n "$SOURCE_BRANCH" ]] || tool_error "--branch is required"
if [[ "$MODE" == "land" ]]; then
  [[ -n "$EXPECTED_TIP" ]] || tool_error "--expected-tip is required for land"
  [[ -n "$MESSAGE" ]] || tool_error "--message is required for land"
fi

# ---- probe mode: pre-lock gate, no lock env required, mutates nothing ------

if [[ "$MODE" == "probe" ]]; then
  resolve_repo_root
  HEAD_SYMREF="$(git -C "$REPO_ROOT" symbolic-ref --quiet HEAD)" || {
    DETACHED_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
    tool_error "primary checkout HEAD is detached (checked-out HEAD: ${DETACHED_SHA}); the helper operates on the primary checkout's checked-out base branch"
  }
  BASE_BRANCH="${HEAD_SYMREF#refs/heads/}"
  SOURCE_TIP="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${SOURCE_BRANCH}^{commit}" 2>/dev/null)" || \
    tool_error "source branch unresolvable: ${SOURCE_BRANCH}"
  BASE_TIP="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
    tool_error "base branch ref unresolvable: refs/heads/${BASE_BRANCH}"

  # The conflict trial runs FIRST: a conflicting branch is necessarily stale
  # relative to the base (both sides changed one path since the fork), so a
  # containment-first order would make the trial unreachable and report the
  # less actionable remedy for the witnessed conflict class.
  TRIAL_RC=0
  TRIAL_OUT="$(git -C "$REPO_ROOT" merge-tree --write-tree --name-only "$BASE_TIP" "$SOURCE_TIP")" || TRIAL_RC=$?
  if [[ "$TRIAL_RC" -gt 1 ]]; then
    tool_error "git merge-tree --write-tree failed (exit ${TRIAL_RC})"
  fi
  if [[ "$TRIAL_RC" -eq 1 ]]; then
    CONFLICTED="$(printf '%s\n' "$TRIAL_OUT" | awk 'NR>1 && $0=="" {exit} NR>1 {print}')"
    echo "refuse: merge-tree trial reports conflicts in:"
    printf '%s' "$CONFLICTED" | sed 's/^/  /' || true
    echo "remedy: resolve the conflicts in the execution worktree before acquiring the lock (the pre-lock composition duty)"
    emit_outcome fail
    exit 1
  fi
  echo "ok: merge-tree trial found no conflicts"

  if git -C "$REPO_ROOT" merge-base --is-ancestor "$BASE_TIP" "$SOURCE_TIP"; then
    echo "ok: containment verified (${SOURCE_BRANCH} contains the base branch tip ${BASE_TIP})"
  else
    FORK_BASE="$(git -C "$REPO_ROOT" merge-base "$BASE_TIP" "$SOURCE_TIP")" || \
      tool_error "git merge-base failed over the resolved tips"
    echo "refuse: source branch ${SOURCE_BRANCH} does not contain the base branch tip ${BASE_TIP} (stale base)"
    echo "  fork-point merge base: ${FORK_BASE}"
    echo "  fork-point delta paths (the paths the base branch gained since the fork that the branch lacks):"
    git -C "$REPO_ROOT" diff --name-only "$FORK_BASE" "$BASE_TIP" | sed 's/^/    /' || true
    emit_outcome fail
    exit 1
  fi
  emit_outcome pass
  exit 0
fi

# ---- land mode: the lock-bound landing --------------------------------------

LOCK_DIR="${MERGE_LOCK_DIR:-}"
LOCK_TOKEN="${MERGE_LOCK_TOKEN:-}"
[[ -n "$LOCK_DIR" ]] || tool_error "land requires MERGE_LOCK_DIR set and non-empty (the merge lock is verified, never assumed)"
[[ -n "$LOCK_TOKEN" ]] || tool_error "land requires MERGE_LOCK_TOKEN set and non-empty (the merge lock is verified, never assumed)"
[[ -d "$LOCK_DIR" ]] || tool_error "merge lock directory does not exist: ${LOCK_DIR}"
LOCK_META="${LOCK_DIR}/meta.env"
[[ -f "$LOCK_META" ]] || tool_error "merge lock record meta.env is missing: ${LOCK_DIR}"
META_TOKEN="$(meta_field "$LOCK_META" lock_token)"
META_REPO="$(meta_field "$LOCK_META" repo_root)"
[[ -n "$META_TOKEN" ]] || tool_error "merge lock record carries an empty lock_token: ${LOCK_META}"
[[ "$LOCK_TOKEN" == "$META_TOKEN" ]] || tool_error "MERGE_LOCK_TOKEN does not equal the record's lock_token (a stale generation or a fabricated environment)"
resolve_repo_root
[[ "$META_REPO" == "$REPO_ROOT" ]] || tool_error "merge lock record repo_root '${META_REPO}' does not equal this repository's primary checkout root '${REPO_ROOT}' (a stale sibling-repo environment)"

HEAD_SYMREF="$(git -C "$REPO_ROOT" symbolic-ref --quiet HEAD)" || {
  DETACHED_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
  tool_error "primary checkout HEAD is detached (checked-out HEAD: ${DETACHED_SHA}); the helper operates on the primary checkout's checked-out base branch; --expected-tip: ${EXPECTED_TIP}"
}
BASE_BRANCH="${HEAD_SYMREF#refs/heads/}"

SOURCE_TIP="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${SOURCE_BRANCH}^{commit}" 2>/dev/null)" || \
  tool_error "source branch unresolvable: ${SOURCE_BRANCH}"
EXPECTED_TIP_SHA="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${EXPECTED_TIP}^{commit}" 2>/dev/null)" || \
  tool_error "expected tip unresolvable: ${EXPECTED_TIP}"

REF_TIP="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
  tool_error "base branch ref unresolvable: refs/heads/${BASE_BRANCH}"
if [[ "$REF_TIP" != "$EXPECTED_TIP_SHA" ]]; then
  echo "refuse: base branch tip moved: refs/heads/${BASE_BRANCH} is at ${REF_TIP} but --expected-tip is ${EXPECTED_TIP_SHA}"
  echo "remedy: re-derive the landing from the new tip and retry"
  emit_outcome fail
  exit 1
fi
HEAD_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
if [[ "$HEAD_SHA" != "$EXPECTED_TIP_SHA" ]]; then
  echo "refuse: the checked-out HEAD ${HEAD_SHA} does not equal --expected-tip ${EXPECTED_TIP_SHA} while refs/heads/${BASE_BRANCH} reads ${REF_TIP}"
  echo "remedy: re-derive the landing from the new tip and retry"
  emit_outcome fail
  exit 1
fi

# The snapshot: porcelain captured after the tip verification, before the
# first mutating step. It records per-path state, not content.
SNAP_FILE="$(mktemp "${TMPDIR:-/tmp}/land-squash-snap.XXXXXX")"
MERGE_OUT="$(mktemp "${TMPDIR:-/tmp}/land-squash-mout.XXXXXX")"
MERGE_ERR="$(mktemp "${TMPDIR:-/tmp}/land-squash-merr.XXXXXX")"
trap 'rm -f "$SNAP_FILE" "$MERGE_OUT" "$MERGE_ERR"' EXIT
git -C "$REPO_ROOT" status --porcelain=v1 > "$SNAP_FILE" || \
  tool_error "git status --porcelain failed over the primary checkout"
load_snapshot "$SNAP_FILE"

# Test-only seam at its single declared pre-merge point.
if [[ "${LAND_SQUASH_TEST_FAULT:-}" == "dirty-writer" ]]; then
  FAULT_PATH="${LAND_SQUASH_TEST_FAULT_PATH:-}"
  [[ -n "$FAULT_PATH" ]] || tool_error "the dirty-writer seam requires LAND_SQUASH_TEST_FAULT_PATH"
  echo "test-only fault seam honored: dirty-writer (LAND_SQUASH_TEST_FAULT=dirty-writer, LAND_SQUASH_TEST_FAULT_PATH=${FAULT_PATH}): appended a writer line to ${FAULT_PATH} after the snapshot"
  printf 'writer line appended after the snapshot\n' >> "${REPO_ROOT}/${FAULT_PATH}"
fi

# Pre-refusal: staged state in the primary index.
STAGED_LIST=""
SNAP_COUNT=${#SNAP_STATES[@]}
if [[ "$SNAP_COUNT" -gt 0 ]]; then
  for i in "${!SNAP_STATES[@]}"; do
    st="${SNAP_STATES[$i]}"
    if [[ "$st" == "??" ]]; then
      continue
    fi
    x="${st:0:1}"
    if [[ "$x" != " " && "$x" != "?" && "$x" != "!" ]]; then
      STAGED_LIST="${STAGED_LIST}${SNAP_PATHS[$i]}"$'\n'
    fi
  done
fi
if [[ -n "$STAGED_LIST" ]]; then
  echo "refuse: staged state exists in the primary index (the landing requires a clean index at the snapshot):"
  printf '%s' "$STAGED_LIST" | sed 's/^/  /' || true
  emit_outcome fail
  exit 1
fi

# Pre-refusal: a locally dirty tracked path intersecting the branch's changed
# paths (the record-only-dirt protection; allowlist-agnostic by design).
BRANCH_PATHS="$(git -C "$REPO_ROOT" diff --name-only "$EXPECTED_TIP_SHA" "$SOURCE_TIP")" || \
  tool_error "git diff over the branch's changed paths failed"
INTERSECT=""
while IFS= read -r p; do
  [[ -n "$p" ]] || continue
  if snapshot_has_dirty "$p"; then
    INTERSECT="${INTERSECT}${p}"$'\n'
  fi
done <<< "$BRANCH_PATHS"
if [[ -n "$INTERSECT" ]]; then
  echo "refuse: dirty intersection: locally modified tracked paths intersect the branch's changed paths (the landing would fold concurrent-writer bytes into the squash):"
  printf '%s' "$INTERSECT" | sed 's/^/  /' || true
  emit_outcome fail
  exit 1
fi

# The guarded squash merge.
MERGE_RC=0
git -C "$REPO_ROOT" merge --squash "$SOURCE_BRANCH" > "$MERGE_OUT" 2> "$MERGE_ERR" || MERGE_RC=$?
if [[ "$MERGE_RC" -ne 0 ]]; then
  restore_or_stop
  echo "merge failure: git merge --squash ${SOURCE_BRANCH} failed (exit ${MERGE_RC}); the landing is indeterminate and the restore is path-exclusive"
  head -n 5 "$MERGE_ERR" | sed 's/^/  merge: /' || true
  print_restore_report
  emit_outcome indeterminate
  exit 2
fi

# Tree equality before the landing commit: the composed index tree must equal
# the source branch tree, or the landing would silently drop or carry base
# divergence.
BRANCH_TREE="$(git -C "$REPO_ROOT" rev-parse "${SOURCE_TIP}^{tree}")" || \
  tool_error "source branch tree unresolvable: ${SOURCE_TIP}"
INDEX_TREE="$(git -C "$REPO_ROOT" write-tree)" || \
  tool_error "git write-tree failed over the composed index"
TREE_DIFF_RC=0
git -C "$REPO_ROOT" diff --quiet "$BRANCH_TREE" "$INDEX_TREE" || TREE_DIFF_RC=$?
if [[ "$TREE_DIFF_RC" -eq 1 ]]; then
  restore_or_stop
  echo "refuse: tree inequality between the source branch tree (${BRANCH_TREE}) and the composed index tree (${INDEX_TREE}); divergent paths:"
  git -C "$REPO_ROOT" diff --name-only "$BRANCH_TREE" "$INDEX_TREE" | sed 's/^/  /' || true
  echo "remedy: re-derive the branch from the current base tip and rebase before landing"
  print_restore_report
  emit_outcome fail
  exit 1
fi
[[ "$TREE_DIFF_RC" -eq 0 ]] || tool_error "git diff --quiet failed (exit ${TREE_DIFF_RC})"

LANDING_COMMIT="$(git -C "$REPO_ROOT" commit-tree "$INDEX_TREE" -p "$EXPECTED_TIP_SHA" -m "$MESSAGE")" || \
  tool_error "git commit-tree failed"

# The parentage gate's pre-swap invocation, always with --source-branch and
# the optional --expected-base passthrough.
GATE_ARGS=(pre-swap --repo "$REPO_ROOT" --pre-tip "$EXPECTED_TIP_SHA" --new-commit "$LANDING_COMMIT" --source-branch "$SOURCE_BRANCH")
if [[ -n "$EXPECTED_BASE" ]]; then
  EXPECTED_BASE_SHA="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${EXPECTED_BASE}^{commit}" 2>/dev/null)" || \
    tool_error "expected base unresolvable: ${EXPECTED_BASE}"
  GATE_ARGS+=("--expected-base" "$EXPECTED_BASE_SHA")
fi
GATE_RC=0
GATE_OUT="$(python3 "$PARENTAGE_GATE" "${GATE_ARGS[@]}")" || GATE_RC=$?
if [[ "$GATE_RC" -ne 0 ]]; then
  restore_or_stop
  print_gate_evidence "$GATE_OUT"
  print_restore_report
  case "$GATE_RC" in
    1) emit_outcome fail; exit 1 ;;
    2) emit_outcome indeterminate; exit 2 ;;
    *) emit_outcome tool_error; exit 3 ;;
  esac
fi
print_gate_evidence "$GATE_OUT"

# The two-value compare-and-swap ref move: a refusal is the tip-moved fail
# class (declared; no dedicated fixture at birth).
CAS_RC=0
git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$LANDING_COMMIT" "$EXPECTED_TIP_SHA" || CAS_RC=$?
if [[ "$CAS_RC" -ne 0 ]]; then
  restore_or_stop
  echo "refuse: the compare-and-swap ref move refused: refs/heads/${BASE_BRANCH} no longer reads ${EXPECTED_TIP_SHA} (the tip moved during the landing)"
  echo "remedy: re-derive the landing from the new tip and retry"
  print_restore_report
  emit_outcome fail
  exit 1
fi

# Test-only seams at their single declared post-CAS point.
ORIGIN_REF="refs/remotes/origin/${BASE_BRANCH}"
case "${LAND_SQUASH_TEST_FAULT:-}" in
  backward-peer)
    FAULT_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${EXPECTED_TIP_SHA}~1" 2>/dev/null)" || \
      tool_error "the backward-peer seam could not resolve ${EXPECTED_TIP_SHA}~1"
    echo "test-only fault seam honored: backward-peer (LAND_SQUASH_TEST_FAULT=backward-peer): moved refs/heads/${BASE_BRANCH} to ${FAULT_COMMIT}"
    git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$FAULT_COMMIT" "$LANDING_COMMIT" || \
      tool_error "the backward-peer seam ref move failed"
    ;;
  diverge-origin)
    ORIGIN_REF="refs/remotes/land-squash-fault/diverged"
    echo "test-only fault seam honored: diverge-origin (LAND_SQUASH_TEST_FAULT=diverge-origin): the post-landing origin leg is redirected to ${ORIGIN_REF}"
    ;;
esac

# The parentage gate's post-landing invocation.
POST_RC=0
POST_OUT="$(python3 "$PARENTAGE_GATE" post-landing --repo "$REPO_ROOT" --pre-tip "$EXPECTED_TIP_SHA" --default-ref "$BASE_BRANCH" --origin-ref "$ORIGIN_REF")" || POST_RC=$?
if [[ "$POST_RC" -eq 0 ]]; then
  print_gate_evidence "$POST_OUT"
  echo "new tip: ${LANDING_COMMIT}"
  git -C "$REPO_ROOT" diff --stat "$EXPECTED_TIP_SHA" "$LANDING_COMMIT" | sed 's/^/  /' || true
  emit_outcome pass
  exit 0
fi
if [[ "$POST_RC" -eq 1 ]]; then
  CURRENT_BASE="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
    tool_error "base branch ref unresolvable after the landing: refs/heads/${BASE_BRANCH}"
  if [[ "$CURRENT_BASE" == "$LANDING_COMMIT" ]]; then
    # Origin-leg-only arm: the landing is complete and the divergence
    # predates it; a fail exit would send callers into a re-landing that the
    # empty-diff refusal then has to absorb.
    print_gate_evidence "$POST_OUT"
    echo "note: the landing is kept (divergence note: the base does not descend from ${ORIGIN_REF}, so only the origin leg refused while the base ref equals the landing commit); operator reconciliation: reconcile the origin ref with the landed tip before the next landing"
    echo "new tip: ${LANDING_COMMIT}"
    git -C "$REPO_ROOT" diff --stat "$EXPECTED_TIP_SHA" "$LANDING_COMMIT" | sed 's/^/  /' || true
    emit_outcome pass
    exit 0
  fi
  # Interleaved-tip arm: the reachable inverse-CAS arm is its refusal (a peer
  # tip move): keep the landing, restore, exit indeterminate citing the
  # interleaved tip.
  restore_or_stop
  print_gate_evidence "$POST_OUT"
  echo "refuse: post-landing pre-tip refusal: the base branch no longer descends from the pre-landing tip (interleaved tip ${CURRENT_BASE})"
  INV_RC=0
  git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$EXPECTED_TIP_SHA" "$LANDING_COMMIT" || INV_RC=$?
  if [[ "$INV_RC" -ne 0 ]]; then
    echo "refuse: the inverse compare-and-swap rollback refused: refs/heads/${BASE_BRANCH} reads ${CURRENT_BASE}, not the landing commit ${LANDING_COMMIT} (a peer tip move interleaved with the landing); keeping the peer's tip"
  else
    echo "note: the inverse compare-and-swap rolled refs/heads/${BASE_BRANCH} back to the pre-landing tip (a state the pre-tip leg cannot reach; reported for completeness)"
  fi
  print_restore_report
  emit_outcome indeterminate
  exit 2
fi
restore_or_stop
print_gate_evidence "$POST_OUT"
print_restore_report
case "$POST_RC" in
  2) emit_outcome indeterminate; exit 2 ;;
  *) emit_outcome tool_error; exit 3 ;;
esac
