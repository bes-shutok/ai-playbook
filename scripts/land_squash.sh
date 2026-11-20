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
#   land-worktree --branch <source-branch> --expected-tip <sha>
#                 --message <text> [--expected-base <sha>]
#                 [--ack-egress <path>]
#       The worktree-complete landing under the narrowed ref-only lock
#       span: the source worktree is addressed through the worktree list,
#       the squash composes in a temp index reading the source worktree's
#       working-tree bytes (with the base-freshness, prompt-log prune-audit,
#       and plans-egress gates) all PRE-LOCK, and the primary checkout
#       receives only the final squash commit through one compare-and-swap
#       ref update taken under the merge lock the mode acquires itself
#       around the swap critical section (parentage verification,
#       compare-and-swap, post-landing gate, reconcile tail); the primary
#       checkout's index and working tree are never written and no arm runs
#       porcelain or restore against it.
#
# Outcome contract (scripts/OUTCOME_CONTRACT.md): born-conformant; every
# non-metadata run ends with exactly one final `OUTCOME: <pass|fail|
# indeterminate|tool_error>` line on stdout matching the exit code
# (0/1/2/3). --help is a metadata exit and emits no OUTCOME line.
#
# Test-only fault seam (never set in production; every honored seam prints a
# loud evidence line naming the value and its env):
#   LAND_SQUASH_TEST_FAULT=dirty-writer (land only) fires immediately after
#       the snapshot and appends one line to the tracked path named by the
#       test-only LAND_SQUASH_TEST_FAULT_PATH, exercising the
#       changed-since-snapshot writer block.
#   LAND_SQUASH_TEST_FAULT=backward-peer fires immediately after the CAS
#       succeeds and moves the base off the landing commit: to
#       <expected-tip>~1 in land, to the verified base tip's parent in
#       land-worktree (never --expected-tip).
#   LAND_SQUASH_TEST_FAULT=base-mover (land-worktree only) moves the base ref
#       to the verified base tip's parent between the check-landing pass and
#       the compare-and-swap.
#   LAND_SQUASH_TEST_FAULT=diverge-origin fires at the post-CAS point and
#       redirects the post-landing invocation's --origin-ref to the forged
#       fixture ref refs/remotes/land-squash-fault/diverged.
#   LAND_SQUASH_TEST_FAULT=prune-audit-unclassified (land-worktree only)
#       reclassifies the wired prompt-log prune audit's exit to an
#       unclassified value (42) after the audit ran, exercising the
#       tool-error arm for a result the real checker cannot produce.
#
# The script carries no in-file selftest mode: the python unittest suite
# scripts/test_land_squash.py is the fixture layer.
set -euo pipefail

PROG="land-squash"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENTAGE_GATE="$SCRIPT_DIR/landing_parentage_gate.py"
REVERSE_GUARD="$SCRIPT_DIR/reverse_squash_guard.py"
PROMPT_LOG_AUDIT="$SCRIPT_DIR/check_prompt_log_origins.py"

usage() {
  cat <<'EOF'
Usage: land_squash.sh probe --branch <source-branch>
       land_squash.sh land --branch <source-branch> --expected-tip <sha>
                           --message <text> [--expected-base <sha>]
       land_squash.sh land-worktree --branch <source-branch>
                                    --expected-tip <sha> --message <text>
                                    [--expected-base <sha>]
                                    [--ack-egress <path>]

Modes:
  probe   Pre-lock gate: containment (the source branch tip must contain the
          live base branch tip) plus a git merge-tree --write-tree conflict
          trial. Runs without the merge-lock environment and mutates nothing.
          On a fail, compose the rebase or conflict resolution in the
          execution worktree BEFORE acquiring the lock.
  land    The primary-checkout landing under a verified merge lock: lock
          authenticity (both MERGE_LOCK_DIR and MERGE_LOCK_TOKEN non-empty,
          the directory live, meta.env readable with a non-empty lock_token
          equal to MERGE_LOCK_TOKEN, and the record's repo_root equal to the
          resolved primary checkout root), base-branch resolution via git
          symbolic-ref (a detached primary HEAD is a tool error), ref-level
          tip and checked-out HEAD verification against --expected-tip, a
          porcelain snapshot, staged-state and dirty-intersection
          pre-refusals, a guarded git merge --squash, tree equality between
          the source branch tree and the composed index tree before
          commit-tree, the parentage gate's pre-swap invocation (with
          --source-branch and the optional --expected-base passthrough), a
          two-value compare-and-swap git update-ref, the parentage gate's
          post-landing invocation with --origin-ref
          refs/remotes/origin/<resolved-base-branch>, and the final new-tip
          report with its first-parent diffstat.
  land-worktree
          The worktree-complete landing under the narrowed ref-only lock
          span: base-branch resolution as land (the invocation runs from
          the primary checkout), with the source worktree addressed through
          the worktree list by --branch. Verifies the source worktree's
          branch ref and checked-out HEAD against --expected-tip (there
          --expected-tip carries the expected source tip, never the base
          tip), runs the wired check-landing base-freshness gate, runs
          the wired prompt-log prune audit when any commit in the landing
          range (the merge base through the verified source tip) touched
          either rolling prompt log (PLAN-PROMPTS.md or EXEC-PROMPTS.md;
          commit-history touch detection with rename detection disabled,
          so deletion, rename, or a later revert cannot hide a touch): a
          receipt-less removal refuses the landing before any ref update
          with one direct repair (put the removed entry's receipt in its
          removal commit, squash or recommit the pair per lesson 234,
          then retry); a checker tool error (exit 3 or unrecognized) is
          a named tool error with refs unchanged, recovered by the
          invoking workflow's single self-heal diagnosis/correction/retry
          pass (park with the exact evidence when it persists; the audit
          is never bypassed). Code-only ranges invoke no audit. Composes
          the squash in a GIT_INDEX_FILE-scoped temp index seeded from
          the verified base tip over the branch's changed paths, reading
          the source worktree's working-tree bytes, asserts tree equality
          against the source branch tip, and runs the wired plans-egress
          check-archive gate over the built landing commit anchored at the
          source worktree - all of that PRE-LOCK in the source worktree
          (the rebase duty runs there too, before the invocation). The mode
          then acquires the repository merge lock itself via the sibling
          done-lock.sh merge-wait-acquire (bounded wait,
          LAND_SQUASH_SWAP_LOCK_WAIT_SECS, default 300s; keyed to the
          primary checkout root; a held lock after the wait is a fail
          naming the holder), and the lock spans the parentage gate's
          pre-swap invocation (with the optional --expected-base
          passthrough), the two-value compare-and-swap whose old-value is
          the base tip resolved after check-landing passes, the parentage
          gate's post-landing invocation, and the landing-tail reconcile,
          releasing on every exit path. The compare-and-swap refusal names
          both the verified base tip and the value the ref now reads (the
          base tip moved between the pre-lock gates and the swap; the
          remedy is the rebase duty: rebase onto the moved tip, refresh
          the base pin, re-run the pre-lock gates, retry). The caller's
          MERGE_LOCK_DIR / MERGE_LOCK_TOKEN exports play no role in this
          mode (lock authenticity is by construction: the helper holds a
          lock it just acquired; do not hold a merge lock around the
          invocation - that hold is the contention the bounded wait
          reports). Never writes the primary checkout's index or working
          tree and never runs porcelain or restore against it (land's
          snapshot, staged-state and dirty-intersection pre-refusals, and
          restore machinery are omitted; the interleaved-tip arm keeps the
          inverse compare-and-swap without any restore call).
          --ack-egress forwards the operator-directed-archive ack to
          check-archive; the matching Archive-egress-ack: <path> trailer
          rides --message.

Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
with exactly one final `OUTCOME: <pass|fail|indeterminate|tool_error>` line
on stdout matching the exit code: 0 pass; 1 fail (a modeled refusal: in land
the prechecks, the tip-moved class, the tree-equality assertion, or a
propagated gate fail; in land-worktree the source-worktree tip refusals, the
tree-inequality assertion, the wired check-landing and check-archive
refusals, the prompt-log prune-audit receipt-less-removal refusal, the
compare-and-swap refusal, the swap-critical-section lock-contention refusal,
or a propagated parentage-gate fail);
2 indeterminate (in land a land-time merge failure, the interleaved-tip
refusal, or a mid-restore pipeline failure naming the unrestored paths; in
land-worktree the interleaved-tip refusal and the ambiguous swap-lock holder
state after the bounded wait); 3 tool error (lock authenticity in land,
detached HEAD, an unresolvable ref, a wired guard's tool failure, the
prompt-log prune audit's tool error, or a missing sibling done-lock.sh, an
export-less swap-lock acquire, or a done-lock.sh exit 3 (its usage,
environment, or unsupported lock data) from the swap-lock acquire in
land-worktree).
--help is a metadata exit and emits no OUTCOME line.

Test-only fault seam (fixtures only; production never sets these; every
honored seam prints a loud evidence line naming the value and its env):
  LAND_SQUASH_TEST_FAULT=dirty-writer (land only) with
      LAND_SQUASH_TEST_FAULT_PATH appends a writer line to the named tracked
      path after the snapshot.
  LAND_SQUASH_TEST_FAULT=backward-peer moves the base off the landing commit
      immediately after the CAS succeeds: to <expected-tip>~1 in land, to the
      verified base tip's parent in land-worktree (never --expected-tip).
  LAND_SQUASH_TEST_FAULT=base-mover (land-worktree only) moves the base ref
      to the verified base tip's parent between the check-landing pass and
      the compare-and-swap.
  LAND_SQUASH_TEST_FAULT=diverge-origin redirects the post-landing origin
      leg to refs/remotes/land-squash-fault/diverged.
  LAND_SQUASH_TEST_FAULT=reconcile-tool-failure (land and land-worktree)
      substitutes an unresolvable post-tip into the landing-tail reconcile
      gate's invocation at its single declared point, forcing the
      reconcile-gate refusal while the landed ref stays moved.
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

emit_grammar_notice() {
  # The compose-time landing-claim grammar notice (warning-only): the
  # message's first line is judged against the guard's LANDING_CLAIM_PREFIXES
  # read through a module import over the already-resolved REVERSE_GUARD path
  # (the constant is the grammar's single source; no copy of the prefix set
  # lives here). A non-conformant subject prints one warning line naming the
  # recognized prefixes; a conformant one prints nothing; a guard import
  # failure prints one note line and continues. The verb/diff mismatch arm
  # (plan docs/history/plans/2026-11-04-execution-lane-authored-plans-misread-as-landed.md
  # Task 2): an authoring-family subject (any LANDING_CLAIM_PREFIXES authoring
  # kind) whose landing diff carries operative-scope bytes outside
  # docs/history/ prints one mismatch warning;
  # warning-only, the outcome and exit code unchanged. The mismatch leg
  # consumes the guard's diff-composition classifier (the same classifier the
  # scan-time rename-boundary split uses), one classifier serving both
  # surfaces.
  local first_line notice_out
  first_line="${MESSAGE%%$'\n'*}"
  local delta_paths=""
  if git -C "$REPO_ROOT" rev-parse --verify --quiet \
      "refs/heads/${SOURCE_BRANCH}" >/dev/null 2>&1; then
    delta_paths="$(git -C "$REPO_ROOT" diff --name-only \
      "$(git -C "$REPO_ROOT" merge-base HEAD "refs/heads/${SOURCE_BRANCH}")" \
      "refs/heads/${SOURCE_BRANCH}" 2>/dev/null || true)"
  fi
  notice_out="$(DELTA_PATHS="$delta_paths" python3 - "$REVERSE_GUARD" "$first_line" 2>/dev/null <<'PY'
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location(
    "reverse_squash_guard", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
subject = sys.argv[2]
paths = [line for line in os.environ.get("DELTA_PATHS", "").splitlines()
         if line.strip()]
operative = module.operative_paths(paths)
authoring_prefixes = tuple(prefix for prefix, kind in
                           module.LANDING_CLAIM_PREFIXES
                           if kind == "authoring")
if not module.is_landing_claim(subject):
    print("grammar: " + ", ".join(
        repr(prefix) for prefix, _kind in module.LANDING_CLAIM_PREFIXES))
elif operative and subject.startswith(authoring_prefixes):
    print("mismatch: " + ", ".join(operative[:5]))
else:
    print("conformant")
PY
)" || true
  case "$notice_out" in
    conformant) : ;;
    "grammar: "*)
      echo "warning: landing message subject matches no recognized landing-claim grammar prefix (recognized: ${notice_out#grammar: }); rephrase the --message subject into the grammar before the landing commit is composed"
      ;;
    "mismatch: "*)
      echo "warning: landing-claim verb/diff mismatch: the subject claims the authoring family but the landing diff carries operative-scope bytes (${notice_out#mismatch: }); the execution-status writers complete the execution-direction flips at the closeout"
      ;;
    *)
      echo "note: the landing-claim grammar notice could not import the guard module (${REVERSE_GUARD}); the landing proceeds without the grammar warning"
      ;;
  esac
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

# Shared NUL-record parser for the -z porcelain forms. The helper's single
# NUL-record read occurrence lives below; the -z streams reach it through a
# temp file or process substitution, never a command substitution (bash
# strips NUL bytes through $(...)).
# Status mode: each record's first two bytes are the state, the remainder
# after the third byte is the path; a rename/copy record is destination-first
# and the NEXT NUL record is the origin path, consumed and discarded. Fills
# Z_PATHS/Z_STATES.
# Plain mode: each record is one path. Fills Z_ITEMS.
# Distinct per-mode destination globals keep concurrent parses independent.
Z_PATHS=()
Z_STATES=()
Z_ITEMS=()
parse_status_z() {
  local mode="$1" file="$2"
  Z_PATHS=()
  Z_STATES=()
  Z_ITEMS=()
  local -a records=()
  local rec st next_origin=0 i
  while IFS= read -r -d '' rec || [[ -n "$rec" ]]; do
    records+=("$rec")
  done < "$file"
  for i in "${!records[@]}"; do
    rec="${records[$i]}"
    if [[ "$mode" == "plain" ]]; then
      Z_ITEMS+=("$rec")
      continue
    fi
    if [[ "$next_origin" -eq 1 ]]; then
      # the origin record of a rename/copy: consumed and discarded
      next_origin=0
      continue
    fi
    st="${rec:0:2}"
    case "$st" in
      R*|C*) next_origin=1 ;;
    esac
    Z_STATES+=("$st")
    Z_PATHS+=("${rec:3}")
  done
}

load_snapshot() {
  SNAP_PATHS=()
  SNAP_STATES=()
  parse_status_z status "$1"
  local i
  for i in "${!Z_PATHS[@]}"; do
    SNAP_PATHS+=("${Z_PATHS[$i]}")
    SNAP_STATES+=("${Z_STATES[$i]}")
  done
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
  local cur_file a_file st p i rc
  cur_file="$(mktemp "${TMPDIR:-/tmp}/land-squash-cur.XXXXXX")"
  a_file="$(mktemp "${TMPDIR:-/tmp}/land-squash-aset.XXXXXX")"
  git -C "$REPO_ROOT" status --porcelain=v1 -z > "$cur_file" || : > "$cur_file"
  parse_status_z status "$cur_file"
  # local copies so the plain-mode parse below cannot clobber them; index
  # expansion is set -u-safe for empty arrays, value expansion is not (3.2)
  local -a cur_paths=()
  local -a cur_states=()
  local ci
  for ci in "${!Z_PATHS[@]}"; do
    cur_paths+=("${Z_PATHS[$ci]}")
    cur_states+=("${Z_STATES[$ci]}")
  done
  rc=0
  git -C "$REPO_ROOT" diff --cached --name-only -z HEAD > "$a_file" || rc=$?
  local -a a_paths=()
  if [[ "$rc" -eq 0 ]]; then
    parse_status_z plain "$a_file"
    for i in "${!Z_ITEMS[@]}"; do
      a_paths+=("${Z_ITEMS[$i]}")
    done
  else
    UNRESTORED+=("(the failure-time staged set could not be derived: git diff --cached failed)")
  fi
  # direct array membership replaces the superseded grep-line helper
  in_staged_set() {
    local q="$1" j
    for j in "${!a_paths[@]}"; do
      [[ "${a_paths[$j]}" == "$q" ]] && return 0
    done
    return 1
  }
  # Classify the not-restored paths before any mutation.
  for i in "${!cur_paths[@]}"; do
    st="${cur_states[$i]}"
    p="${cur_paths[$i]}"
    if in_staged_set "$p"; then
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
  done
  # (b) merge-created untracked materialization: absent from the snapshot.
  for i in "${!cur_paths[@]}"; do
    st="${cur_states[$i]}"
    p="${cur_paths[$i]}"
    if [[ "$st" == "??" ]] && ! snapshot_contains "$p"; then
      REMOVED+=("$p")
      rm -rf "${REPO_ROOT}/${p}"
    fi
  done
  # (a) restore the failure-time staged set to HEAD, path by path.
  for i in "${!a_paths[@]}"; do
    p="${a_paths[$i]}"
    if git -C "$REPO_ROOT" restore --staged --worktree -- "$p" >/dev/null 2>&1; then
      if git -C "$REPO_ROOT" cat-file -e "HEAD:${p}" 2>/dev/null; then
        RESTORED+=("$p")
      else
        REMOVED+=("$p")
      fi
    else
      UNRESTORED+=("$p")
    fi
  done
  rm -f "$cur_file" "$a_file"
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

# The landing-tail reconcile gate (plan 2026-10-14-post-landing-reconciliation-enforcement):
# the landing tail runs the post-landing reconciliation itself, under the
# still-held merge lock, and writes its receipt to
# docs/tmp/landing-receipts/<post-tip>.txt. The completion verdict requires a
# receipt recording reconcile exit 0 or exit 1 (exit 1's block rows are the
# sanctioned partial state); a reconcile exit 2 refuses the completion
# verdict while the landed ref stays moved, the remedy naming the re-run.
run_reconcile_gate() {
  local pre="$1" post="$2"
  local seam_post="$post"
  if [[ "${LAND_SQUASH_TEST_FAULT:-}" == "reconcile-tool-failure" ]]; then
    seam_post="0000000000000000000000000000000000000000"
    echo "test-only fault seam honored: reconcile-tool-failure (LAND_SQUASH_TEST_FAULT=reconcile-tool-failure): the reconcile invocation's post-tip substituted with an unresolvable value"
  fi
  RRG_RC=0
  RRG_OUT="$(python3 "$SCRIPT_DIR/reconcile_post_landing.py" --repo "$REPO_ROOT" --base "$BASE_BRANCH" --pre-tip "$pre" --post-tip "$seam_post")" || RRG_RC=$?
  local receipt_dir="${REPO_ROOT}/docs/tmp/landing-receipts"
  mkdir -p "$receipt_dir" || tool_error "cannot create the receipt home: ${receipt_dir}"
  RRG_RECEIPT="${receipt_dir}/${post}.txt"
  {
    printf 'command: python3 %s --repo %s --base %s --pre-tip %s --post-tip %s\n' \
      "$SCRIPT_DIR/reconcile_post_landing.py" "$REPO_ROOT" "$BASE_BRANCH" "$pre" "$seam_post"
    printf 'exit code: %s\n' "$RRG_RC"
    printf '%s\n' "$RRG_OUT"
  } > "$RRG_RECEIPT"
  echo "reconcile-receipt: ${RRG_RECEIPT}"
  local restored removed blockrow wholesale synced
  restored="$(printf '%s\n' "$RRG_OUT" | grep -c '^restored ' || true)"
  removed="$(printf '%s\n' "$RRG_OUT" | grep -c '^removed ' || true)"
  blockrow="$(printf '%s\n' "$RRG_OUT" | grep -c '^block ' || true)"
  wholesale="$(printf '%s\n' "$RRG_OUT" | grep -c '^wholesale ' || true)"
  synced="$(printf '%s\n' "$RRG_OUT" | grep -c '^synced ' || true)"
  echo "reconcile rows: restored=${restored} removed=${removed} block=${blockrow} wholesale=${wholesale} synced=${synced}"
  if [[ "$RRG_RC" -eq 1 ]]; then
    printf '%s\n' "$RRG_OUT"
    echo "note: sanctioned partial state: every block row is recorded in the receipt; the landing completes"
  fi
  return "$RRG_RC"
}

run_reconcile_gate_or_refuse() {
  # errexit-safe: the gate's rc-1 sanctioned-partial shape must not kill the
  # run, only rc>=2 refuses
  local rc=0
  run_reconcile_gate "$1" "$2" || rc=$?
  if [[ "$rc" -ge 2 ]]; then
    echo "refuse: reconcile-gate: the post-landing reconciliation failed as a tool failure (reconcile exit ${rc})"
    echo "receipt: ${RRG_RECEIPT}"
    echo "remedy: re-run python3 ${SCRIPT_DIR}/reconcile_post_landing.py --repo ${REPO_ROOT} --base ${BASE_BRANCH} --pre-tip $1 --post-tip $2, then proceed to the closeout on the valid receipt; the landed ref stays moved"
    emit_outcome fail
    exit 1
  fi
  return 0
}

# ---- argument parsing ------------------------------------------------------

MODE="${1:-}"
case "$MODE" in
  -h|--help|help)
    usage
    exit 0
    ;;
  probe|land|land-worktree)
    shift
    ;;
  "")
    usage >&2
    tool_error "a mode argument is required (probe, land, or land-worktree)"
    ;;
  *)
    usage >&2
    tool_error "unknown mode: ${MODE} (expected probe, land, or land-worktree)"
    ;;
esac

SOURCE_BRANCH=""
EXPECTED_TIP=""
MESSAGE=""
EXPECTED_BASE=""
ACK_EGRESS=""
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
    --ack-egress)
      [[ $# -ge 2 && -n "${2:-}" ]] || tool_error "--ack-egress requires a value"
      [[ -z "$ACK_EGRESS" ]] || tool_error "--ack-egress given more than once (at most one per invocation)"
      ACK_EGRESS="$2"
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
if [[ "$MODE" == "land-worktree" ]]; then
  [[ -n "$EXPECTED_TIP" ]] || tool_error "--expected-tip is required for land-worktree"
  [[ -n "$MESSAGE" ]] || tool_error "--message is required for land-worktree"
fi
if [[ -n "$ACK_EGRESS" && "$MODE" != "land-worktree" ]]; then
  tool_error "--ack-egress is only valid for land-worktree"
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
  # The tracked-ignored pass is report-only: it never changes the verdict
  # or exit code, and check-ignore's none-matched exit 1 must not abort the
  # pipeline under errexit and pipefail (the `|| true` guard), so a clean
  # branch reaches the pass verdict unchanged. The core.quotePath=false pin
  # sits on check-ignore, not the delta diff: check-ignore unquotes
  # C-quoted stdin itself (a diff-side pin would be a no-op) but re-quotes
  # its own stdout, and that echoed output is what the warning prints, so
  # non-ASCII delta paths reach the warning line as real bytes.
  # --diff-filter=ACMR keeps a landing that untracks inherited
  # tracked-ignored paths from warning about its own cleanup (arrivals and
  # modifications warn; removals stay silent).
  TRACKED_IGNORED="$(git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR "$BASE_TIP" "$SOURCE_TIP" |
    git -C "$REPO_ROOT" -c core.quotePath=false check-ignore --no-index --stdin)" || true
  while IFS= read -r TI_PATH; do
    [[ -n "$TI_PATH" ]] || continue
    echo "warning: tracked-ignored path on the branch delta: ${TI_PATH}"
  done <<< "$TRACKED_IGNORED"
  emit_outcome pass
  exit 0
fi

# ---- land-worktree mode: the worktree-complete landing ----------------------
#
# The worktree-complete landing class: the squash composes inside the source
# worktree's class shape while the primary checkout receives only the final
# squash commit through one two-value compare-and-swap ref update of the base
# branch ref. The narrowed lock span (ref-only class): the rebase duty, the
# wired check-landing base-freshness gate, the wired prompt-log prune audit,
# the composition, the tree-equality assertion, and the wired check-archive
# gate over the built landing commit all run PRE-LOCK in the source worktree;
# the mode itself then acquires the repository merge lock (bounded wait via
# the sibling done-lock.sh, keyed to this repository's primary checkout
# root) and the lock spans the parentage verification, the compare-and-swap
# ref update, the post-landing gate, and the reconcile tail, releasing on
# every exit path. Because the mode holds a lock it just acquired, lock
# authenticity is by construction and the caller's MERGE_LOCK_DIR /
# MERGE_LOCK_TOKEN exports play no role here. The mode reuses land's
# base-branch resolution, parentage pre-swap and post-landing invocations,
# and the two-value compare-and-swap form unchanged, and wires two existing
# gate implementations as declared re-homings: check-landing (the class
# prose's mandatory base-freshness gate; the mode's tree equality is
# staleness-blind by composition, so check-landing is the load-bearing
# stale-base guard) and check-archive over the built landing commit. The
# mode omits land's restore machinery entirely: no arm runs porcelain or
# restore against the primary checkout, whose index and working tree are
# never written.

if [[ "$MODE" == "land-worktree" ]]; then
  # The primary checkout root resolves first (the swap lock keys through
  # the same root), then the sibling lock script: a done-lock.sh absent
  # from the resolved scripts directory is a deployment gap, never a skip.
  resolve_repo_root
  SWAP_LOCK_SCRIPT="$SCRIPT_DIR/done-lock.sh"
  [[ -f "$SWAP_LOCK_SCRIPT" ]] || tool_error "done-lock.sh is missing beside the helper (${SCRIPT_DIR}); the land-worktree swap-critical-section merge lock cannot be acquired - record a deployment gap naming the probed path and defer the landing"

  # Base-branch resolution: the primary checkout's checked-out branch; the
  # source worktree is addressed through the worktree list by --branch.
  HEAD_SYMREF="$(git -C "$REPO_ROOT" symbolic-ref --quiet HEAD)" || {
    DETACHED_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
    tool_error "primary checkout HEAD is detached (checked-out HEAD: ${DETACHED_SHA}); the helper operates on the primary checkout's checked-out base branch; --expected-tip: ${EXPECTED_TIP}"
  }
  BASE_BRANCH="${HEAD_SYMREF#refs/heads/}"

  SOURCE_WT=""
  WL_PATH=""
  while IFS= read -r WL_LINE; do
    case "$WL_LINE" in
      "worktree "*) WL_PATH="${WL_LINE#worktree }" ;;
      "branch "*)
        if [[ "${WL_LINE#branch }" == "refs/heads/$SOURCE_BRANCH" ]]; then
          SOURCE_WT="$WL_PATH"
        fi
        ;;
    esac
  done < <(git -C "$REPO_ROOT" worktree list --porcelain)
  [[ -n "$SOURCE_WT" ]] || tool_error "no worktree checked out on the source branch: ${SOURCE_BRANCH} (the source worktree is addressed through the worktree list)"

  # Source-worktree tip verification: --expected-tip carries the expected
  # source tip, and both the branch ref and the checked-out HEAD must equal
  # it. A mismatch refuses before any composition.
  SOURCE_TIP="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "refs/heads/${SOURCE_BRANCH}^{commit}" 2>/dev/null)" || \
    tool_error "source branch unresolvable: ${SOURCE_BRANCH}"
  EXPECTED_TIP_SHA="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${EXPECTED_TIP}^{commit}" 2>/dev/null)" || \
    tool_error "expected tip unresolvable: ${EXPECTED_TIP}"
  if [[ "$SOURCE_TIP" != "$EXPECTED_TIP_SHA" ]]; then
    echo "refuse: the source worktree's checked-out HEAD (the source branch tip) ${SOURCE_TIP} does not equal --expected-tip ${EXPECTED_TIP_SHA}"
    echo "remedy: re-derive the landing from the source worktree's current tip and retry"
    emit_outcome fail
    exit 1
  fi
  WT_HEAD="$(git -C "$SOURCE_WT" rev-parse --verify HEAD)" || \
    tool_error "the source worktree's HEAD is unresolvable: ${SOURCE_WT}"
  if [[ "$WT_HEAD" != "$EXPECTED_TIP_SHA" ]]; then
    echo "refuse: the source worktree's checked-out HEAD ${WT_HEAD} does not equal --expected-tip ${EXPECTED_TIP_SHA} while refs/heads/${SOURCE_BRANCH} reads ${SOURCE_TIP}"
    echo "remedy: check the source worktree out on ${SOURCE_BRANCH} at ${EXPECTED_TIP_SHA} and retry"
    emit_outcome fail
    exit 1
  fi

  # Temp files for the two wired guard runs, the composition front-end,
  # and the swap-lock acquire evidence (the acquire stderr file is born
  # here so the EXIT trap covers the pre-acquire contention exits too).
  WTCL_OUT="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtcl.XXXXXX")"
  WTCL_ERR="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtcle.XXXXXX")"
  WTCA_OUT="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtca.XXXXXX")"
  WTCA_ERR="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtcae.XXXXXX")"
  WTPA_OUT="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtpa.XXXXXX")"
  WTPA_ERR="$(mktemp "${TMPDIR:-/tmp}/land-squash-wtpae.XXXXXX")"
  WT_TOUCH_OUT="$(mktemp "${TMPDIR:-/tmp}/land-squash-wttouch.XXXXXX")"
  WT_INDEX="$(mktemp "${TMPDIR:-/tmp}/land-squash-wt-index.XXXXXX")"
  WT_CHANGED="$(mktemp "${TMPDIR:-/tmp}/land-squash-wt-ch.XXXXXX")"
  SWAP_ACQ_ERR="$(mktemp "${TMPDIR:-/tmp}/land-squash-swap-acq.XXXXXX")"
  trap 'rm -f "$WTCL_OUT" "$WTCL_ERR" "$WTCA_OUT" "$WTCA_ERR" "$WTPA_OUT" "$WTPA_ERR" "$WT_TOUCH_OUT" "$WT_INDEX" "$WT_CHANGED" "$SWAP_ACQ_ERR"' EXIT

  # The wired check-landing base-freshness gate, resolved adjacent to the
  # helper (the $SCRIPT_DIR precedent the parentage gate sets): guard exit 1
  # is a modeled fail carrying the guard's evidence lines, exit 2 a tool
  # error; stderr is captured alongside stdout.
  WTGUARD_RC=0
  python3 "$REVERSE_GUARD" check-landing --source-branch "$SOURCE_BRANCH" \
    --target-ref "refs/heads/${BASE_BRANCH}" --repo "$SOURCE_WT" \
    > "$WTCL_OUT" 2> "$WTCL_ERR" || WTGUARD_RC=$?
  echo "check-landing:"
  sed 's/^/  /' "$WTCL_OUT" || true
  sed 's/^/  /' "$WTCL_ERR" || true
  if [[ "$WTGUARD_RC" -eq 1 ]]; then
    echo "remedy: rebase the source branch onto the current base tip before landing"
    emit_outcome fail
    exit 1
  fi
  [[ "$WTGUARD_RC" -eq 0 ]] || tool_error "check-landing failed (exit ${WTGUARD_RC})"

  # The compose-time landing-claim grammar notice, before the landing commit
  # is composed. The wired check-landing gate above already refused any run
  # whose guard copy is missing from every resolved path, so the notice's
  # import-failure note line is not reachable in this mode.
  emit_grammar_notice

  # The base tip resolved after check-landing passes: the compare-and-swap
  # old-value and both parentage base arguments feed from here, never from
  # the source tip.
  BASE_TIP="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
    tool_error "base branch ref unresolvable: refs/heads/${BASE_BRANCH}"

  # The wired prompt-log prune audit, before commit composition and before
  # the base ref moves. The landing range is every commit after the source
  # branch's merge base with the resolved base tip through the verified
  # source tip. When any commit in that range touched either rolling prompt
  # log (commit-history detection with rename detection disabled, so a
  # deletion, a rename, or a touch later reverted cannot hide), the existing
  # checker audits the range's prompt-log removals exactly once, over both
  # logs, with the verified source tip passed as the pinned upper endpoint
  # (--head) so a concurrent worktree HEAD move cannot change the audited
  # history. The checker anchor is an existing rolling log in the source
  # worktree: the surviving sibling when the touched log was deleted (the
  # checker audits both logs from either anchor). The audit's stdout and
  # stderr are preserved in the landing receipt; PRUNE-OK lines are retained
  # and a passing summary with no removals carries no PRUNE-OK line. Exit 1
  # refuses before any landing ref update with the single direct repair;
  # exit 3 or any unrecognized result is a named tool error with refs
  # unchanged (the invoking workflow's single self-heal recovery owns the
  # retry; the audit is never bypassed). A code-only range invokes no audit
  # and keeps the existing landing path unchanged.
  MERGE_BASE="$(git -C "$REPO_ROOT" merge-base "$BASE_TIP" "$SOURCE_TIP")" || \
    tool_error "merge base unresolvable between the base tip and ${SOURCE_TIP}"
  PROMPT_LOG_PLAN="docs/history/backlog/PLAN-PROMPTS.md"
  PROMPT_LOG_EXEC="docs/history/backlog/EXEC-PROMPTS.md"
  git -C "$REPO_ROOT" log --format=%H --no-renames \
    "${MERGE_BASE}..${SOURCE_TIP}" -- "$PROMPT_LOG_PLAN" "$PROMPT_LOG_EXEC" \
    > "$WT_TOUCH_OUT" || \
    tool_error "git log over the landing range's prompt-log touch failed"
  if [[ -s "$WT_TOUCH_OUT" ]]; then
    if [[ -f "$SOURCE_WT/$PROMPT_LOG_PLAN" ]]; then
      AUDIT_ANCHOR="$SOURCE_WT/$PROMPT_LOG_PLAN"
    elif [[ -f "$SOURCE_WT/$PROMPT_LOG_EXEC" ]]; then
      AUDIT_ANCHOR="$SOURCE_WT/$PROMPT_LOG_EXEC"
    else
      AUDIT_ANCHOR="$SOURCE_WT/$PROMPT_LOG_PLAN"
    fi
    WTPA_RC=0
    python3 "$PROMPT_LOG_AUDIT" --prune-audit --base "$MERGE_BASE" \
      --head "$SOURCE_TIP" "$AUDIT_ANCHOR" \
      > "$WTPA_OUT" 2> "$WTPA_ERR" || WTPA_RC=$?
    echo "prune-audit:"
    echo "  anchor: $AUDIT_ANCHOR"
    sed 's/^/  /' "$WTPA_OUT" || true
    sed 's/^/  /' "$WTPA_ERR" || true
    # Test-only seam at its single declared point: reclassifies a passing
    # audit exit to an unclassified value so the tool-error arm is
    # reachable without a fixture the real checker cannot produce.
    if [[ "${LAND_SQUASH_TEST_FAULT:-}" == "prune-audit-unclassified" ]]; then
      echo "test-only fault seam honored: prune-audit-unclassified (LAND_SQUASH_TEST_FAULT=prune-audit-unclassified): the prune-audit exit is reclassified to 42"
      WTPA_RC=42
    fi
    if [[ "$WTPA_RC" -eq 1 ]]; then
      echo "remedy: put the removed entry's receipt in its removal commit (the PLAN-PROMPTS-PRUNE/EXEC-PROMPTS-PRUNE ledger line or the same-commit receipt), squash or recommit that pair per lesson 234, then retry the landing"
      emit_outcome fail
      exit 1
    fi
    [[ "$WTPA_RC" -eq 0 ]] || tool_error "prompt-log prune audit failed (exit ${WTPA_RC})"
  fi

  # Test-only seam at its single declared point between the check-landing
  # pass and the compare-and-swap.
  if [[ "${LAND_SQUASH_TEST_FAULT:-}" == "base-mover" ]]; then
    WT_FAULT_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${BASE_TIP}~1" 2>/dev/null)" || \
      tool_error "the base-mover seam could not resolve ${BASE_TIP}~1"
    echo "test-only fault seam honored: base-mover (LAND_SQUASH_TEST_FAULT=base-mover): moved refs/heads/${BASE_BRANCH} to ${WT_FAULT_COMMIT} before the compare-and-swap"
    git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$WT_FAULT_COMMIT" "$BASE_TIP" || \
      tool_error "the base-mover seam ref move failed"
  fi

  # The composition front-end: a GIT_INDEX_FILE-scoped temp index seeded
  # from the verified base tip over the branch's changed paths, indexing the
  # source worktree's working-tree bytes. No checkout's index or working
  # tree is written. The producer runs with --no-renames so a rename feeds
  # update-index as the explicit delete-plus-add pair (default rename
  # detection names the new path alone and would leave the old path seeded
  # from the base tree).
  git -C "$REPO_ROOT" diff --name-only -z --no-renames "$BASE_TIP" "$SOURCE_TIP" > "$WT_CHANGED" || \
    tool_error "git diff over the branch's changed paths failed"
  GIT_INDEX_FILE="$WT_INDEX" git -C "$SOURCE_WT" read-tree "$BASE_TIP" || \
    tool_error "git read-tree failed seeding the temp index from the base tip"
  GIT_INDEX_FILE="$WT_INDEX" git -C "$SOURCE_WT" update-index -z --add --remove --stdin < "$WT_CHANGED" || \
    tool_error "git update-index failed indexing the source worktree's working-tree bytes"
  INDEX_TREE="$(GIT_INDEX_FILE="$WT_INDEX" git -C "$SOURCE_WT" write-tree)" || \
    tool_error "git write-tree failed over the composed temp index"

  # Tree equality against the source branch tip: the mode's composition is
  # staleness-blind by construction, so a diverging source worktree refuses
  # here with the divergent paths named, before the ref move.
  BRANCH_TREE="$(git -C "$REPO_ROOT" rev-parse "${SOURCE_TIP}^{tree}")" || \
    tool_error "source branch tree unresolvable: ${SOURCE_TIP}"
  WT_TREE_RC=0
  git -C "$REPO_ROOT" diff --quiet "$BRANCH_TREE" "$INDEX_TREE" || WT_TREE_RC=$?
  if [[ "$WT_TREE_RC" -eq 1 ]]; then
    echo "refuse: tree inequality between the source branch tip tree (${BRANCH_TREE}) and the composed temp-index tree (${INDEX_TREE}); the source worktree's working-tree bytes diverge from the branch tip; divergent paths:"
    git -C "$REPO_ROOT" diff --name-only "$BRANCH_TREE" "$INDEX_TREE" | sed 's/^/  /' || true
    echo "remedy: commit or restore the diverging bytes in the source worktree and retry"
    emit_outcome fail
    exit 1
  fi
  [[ "$WT_TREE_RC" -eq 0 ]] || tool_error "git diff --quiet failed (exit ${WT_TREE_RC})"

  LANDING_COMMIT="$(git -C "$REPO_ROOT" commit-tree "$INDEX_TREE" -p "$BASE_TIP" -m "$MESSAGE")" || \
    tool_error "git commit-tree failed"

  # The wired plans-egress check-archive gate over the built landing commit,
  # anchored at the source worktree (the root already resolved for tip
  # verification: the run's exec-review record exists on the source
  # worktree's disk, while the primary checkout's disk stays byte-unchanged):
  # guard exit 1 is a modeled fail before the ref move with the egress
  # findings named, exit 2 a tool error; stderr is captured alongside
  # stdout. --ack-egress forwards the operator-directed-archive ack; the
  # matching Archive-egress-ack trailer rides --message.
  WTCA_ARGS=(check-archive --rev "$LANDING_COMMIT" --repo "$SOURCE_WT")
  if [[ -n "$ACK_EGRESS" ]]; then
    WTCA_ARGS+=("--ack-egress" "$ACK_EGRESS")
  fi
  WTGUARD_RC=0
  python3 "$REVERSE_GUARD" "${WTCA_ARGS[@]}" > "$WTCA_OUT" 2> "$WTCA_ERR" || WTGUARD_RC=$?
  echo "check-archive:"
  sed 's/^/  /' "$WTCA_OUT" || true
  sed 's/^/  /' "$WTCA_ERR" || true
  if [[ "$WTGUARD_RC" -eq 1 ]]; then
    echo "remedy: satisfy the guard's evidence legs, or pass --ack-egress with the matching Archive-egress-ack trailer in --message"
    emit_outcome fail
    exit 1
  fi
  [[ "$WTGUARD_RC" -eq 0 ]] || tool_error "check-archive failed (exit ${WTGUARD_RC})"

  # ==== swap critical section: acquire the merge lock ====================
  # Everything above ran pre-lock in the source worktree. The lock spans
  # the parentage verification, the compare-and-swap ref update, the
  # post-landing gate, and the reconcile tail, and releases on every exit
  # path through the EXIT trap installed after a successful acquire. The
  # bounded wait keeps an intersecting landing queued behind the holder's
  # swap critical section only, never behind its whole composition.
  SWAP_WAIT="${LAND_SQUASH_SWAP_LOCK_WAIT_SECS:-300}"
  case "$SWAP_WAIT" in ''|*[!0-9]*) SWAP_WAIT=300 ;; esac
  echo "swap lock: acquiring the merge lock for the swap critical section (parentage verification, compare-and-swap, post-landing gate, reconcile tail; bounded wait ${SWAP_WAIT}s)"
  SWAP_ACQ_RC=0
  SWAP_ACQ_OUT="$(cd "$REPO_ROOT" && MERGE_LOCK_HOLDER_PID="$$" \
    bash "$SWAP_LOCK_SCRIPT" merge-wait-acquire \
    --label land-squash-swap --max-wait "$SWAP_WAIT" 2> "$SWAP_ACQ_ERR")" || SWAP_ACQ_RC=$?
  sed 's/^/  swap-lock: /' "$SWAP_ACQ_ERR" || true
  if [[ "$SWAP_ACQ_RC" -ne 0 ]]; then
    if [[ "$SWAP_ACQ_RC" -eq 2 ]]; then
      echo "refuse: the swap-critical-section merge lock state is ambiguous after the bounded wait (${SWAP_WAIT}s); re-derive the holder state via done-lock.sh merge-status and retry the landing"
      emit_outcome indeterminate
      exit 2
    fi
    if [[ "$SWAP_ACQ_RC" -eq 3 ]]; then
      # done-lock.sh's rc 3 is its usage/environment/lock-data tool error,
      # never a held lock: the held-after-wait fail prose would model a
      # retryable contention that no retry can clear.
      echo "refuse: the swap-critical-section lock acquire failed as a done-lock.sh tool error (exit 3: usage, environment, or unsupported lock data); the swap-lock: evidence lines above carry the acquire's diagnostics"
      emit_outcome tool_error
      exit 3
    fi
    echo "refuse: the swap-critical-section merge lock is held after the bounded wait (${SWAP_WAIT}s); the composition above already ran pre-lock, so retry the landing once the holder releases (the retry re-runs the full pre-lock gate sequence)"
    emit_outcome fail
    exit 1
  fi
  # The acquire's eval-consumed export block: the sanctioned consumption
  # form, so the %q-quoted values resolve exactly as done-lock.sh printed
  # them (a stale caller MERGE_LOCK_DIR/MERGE_LOCK_TOKEN export is
  # overwritten here and plays no gate role).
  eval "$SWAP_ACQ_OUT"
  SWAP_LOCK_DIR="${MERGE_LOCK_DIR:-}"
  SWAP_LOCK_TOKEN="${MERGE_LOCK_TOKEN:-}"
  SWAP_LOCK_RELEASED=0
  release_swap_lock() {
    # Idempotent: the EXIT trap is the single release point on every exit
    # path from the critical section; a failed release is a loud warning,
    # never a silent pass and never an outcome flip (the landing may
    # already stand).
    [[ "$SWAP_LOCK_RELEASED" -eq 0 ]] || return 0
    [[ -n "$SWAP_LOCK_DIR" && -n "$SWAP_LOCK_TOKEN" ]] || return 0
    SWAP_LOCK_RELEASED=1
    if ! MERGE_LOCK_DIR="$SWAP_LOCK_DIR" MERGE_LOCK_TOKEN="$SWAP_LOCK_TOKEN" \
        bash "$SWAP_LOCK_SCRIPT" merge-release >/dev/null 2>&1; then
      echo "warning: the swap-critical-section merge lock release failed (lock dir ${SWAP_LOCK_DIR}); release it via done-lock.sh merge-release before continuing" >&2
    fi
  }
  trap 'rm -f "$WTCL_OUT" "$WTCL_ERR" "$WTCA_OUT" "$WTCA_ERR" "$WTPA_OUT" "$WTPA_ERR" "$WT_TOUCH_OUT" "$WT_INDEX" "$WT_CHANGED" "$SWAP_ACQ_ERR"; release_swap_lock' EXIT
  [[ -n "$SWAP_LOCK_DIR" && -n "$SWAP_LOCK_TOKEN" ]] || \
    tool_error "the swap-critical-section acquire produced no lock exports (a done-lock.sh contract drift); stop and re-derive from disk"

  # The parentage gate's pre-swap invocation, always with --source-branch,
  # the pre-tip fed from the verified base tip, and the optional
  # --expected-base passthrough.
  GATE_ARGS=(pre-swap --repo "$SOURCE_WT" --pre-tip "$BASE_TIP" --new-commit "$LANDING_COMMIT" --source-branch "$SOURCE_BRANCH")
  if [[ -n "$EXPECTED_BASE" ]]; then
    EXPECTED_BASE_SHA="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${EXPECTED_BASE}^{commit}" 2>/dev/null)" || \
      tool_error "expected base unresolvable: ${EXPECTED_BASE}"
    GATE_ARGS+=("--expected-base" "$EXPECTED_BASE_SHA")
  fi
  GATE_RC=0
  GATE_OUT="$(python3 "$PARENTAGE_GATE" "${GATE_ARGS[@]}")" || GATE_RC=$?
  if [[ "$GATE_RC" -ne 0 ]]; then
    print_gate_evidence "$GATE_OUT"
    case "$GATE_RC" in
      1) emit_outcome fail; exit 1 ;;
      2) emit_outcome indeterminate; exit 2 ;;
      *) emit_outcome tool_error; exit 3 ;;
    esac
  fi
  print_gate_evidence "$GATE_OUT"

  # The two-value compare-and-swap ref move: the old-value is the verified
  # base tip resolved after the pre-lock gates passed; a refusal is the
  # base-tip-moved fail class, evidenced with both the verified base tip
  # and the value the ref actually reads now (the peer's move), so the
  # retry's rebase duty re-derives onto the moved tip without a second
  # probe.
  CAS_RC=0
  git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$LANDING_COMMIT" "$BASE_TIP" || CAS_RC=$?
  if [[ "$CAS_RC" -ne 0 ]]; then
    SWAP_CURRENT_BASE="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}" 2>/dev/null || echo unresolvable)"
    echo "refuse: the compare-and-swap ref move refused: refs/heads/${BASE_BRANCH} no longer reads the verified base tip ${BASE_TIP} and now reads ${SWAP_CURRENT_BASE} (the base tip moved between the check-landing pass and the compare-and-swap)"
    echo "remedy: rebase the source branch onto the moved tip ${SWAP_CURRENT_BASE}, refresh the recorded base pin, re-run the full pre-lock gate sequence, and retry the landing"
    emit_outcome fail
    exit 1
  fi

  # Test-only seams at their single declared post-CAS point; the
  # backward-peer target derives from the verified base tip (its parent),
  # never from --expected-tip.
  ORIGIN_REF="refs/remotes/origin/${BASE_BRANCH}"
  case "${LAND_SQUASH_TEST_FAULT:-}" in
    backward-peer)
      WT_FAULT_COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify --quiet "${BASE_TIP}~1" 2>/dev/null)" || \
        tool_error "the backward-peer seam could not resolve ${BASE_TIP}~1"
      echo "test-only fault seam honored: backward-peer (LAND_SQUASH_TEST_FAULT=backward-peer): moved refs/heads/${BASE_BRANCH} to ${WT_FAULT_COMMIT} (${BASE_TIP}~1)"
      git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$WT_FAULT_COMMIT" "$LANDING_COMMIT" || \
        tool_error "the backward-peer seam ref move failed"
      ;;
    diverge-origin)
      ORIGIN_REF="refs/remotes/land-squash-fault/diverged"
      echo "test-only fault seam honored: diverge-origin (LAND_SQUASH_TEST_FAULT=diverge-origin): the post-landing origin leg is redirected to ${ORIGIN_REF}"
      ;;
  esac

  # The parentage gate's post-landing invocation.
  POST_RC=0
  POST_OUT="$(python3 "$PARENTAGE_GATE" post-landing --repo "$SOURCE_WT" --pre-tip "$BASE_TIP" --default-ref "$BASE_BRANCH" --origin-ref "$ORIGIN_REF")" || POST_RC=$?
  if [[ "$POST_RC" -eq 0 ]]; then
    print_gate_evidence "$POST_OUT"
    run_reconcile_gate_or_refuse "$BASE_TIP" "$LANDING_COMMIT"
    echo "new tip: ${LANDING_COMMIT}"
    git -C "$REPO_ROOT" diff --stat "$BASE_TIP" "$LANDING_COMMIT" | sed 's/^/  /' || true
    emit_outcome pass
    exit 0
  fi
  if [[ "$POST_RC" -eq 1 ]]; then
    # POST_RC 1 is the pre-tip refusal alone (the gate's origin-only
    # divergence is an informational note with exit 0); the pre-swap gate
    # verified the landing commit's parentage onto the pre-tip, so a
    # pre-tip refusal here means the base ref no longer reads the landing
    # commit: an interleaved peer move.
    CURRENT_BASE="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
      tool_error "base branch ref unresolvable after the landing: refs/heads/${BASE_BRANCH}"
    # Interleaved-tip arm: the inverse compare-and-swap is the only
    # recovery write (old-value the landing commit, new-value the verified
    # base tip, never the source-worktree tip); no restore call exists in
    # this mode.
    print_gate_evidence "$POST_OUT"
    echo "refuse: post-landing pre-tip refusal: the base branch no longer descends from the pre-landing tip (interleaved tip ${CURRENT_BASE})"
    INV_RC=0
    git -C "$REPO_ROOT" update-ref "refs/heads/${BASE_BRANCH}" "$BASE_TIP" "$LANDING_COMMIT" || INV_RC=$?
    if [[ "$INV_RC" -ne 0 ]]; then
      echo "refuse: the inverse compare-and-swap rollback refused: refs/heads/${BASE_BRANCH} reads ${CURRENT_BASE}, not the landing commit ${LANDING_COMMIT} (a peer tip move interleaved with the landing); keeping the peer's tip"
      echo "  attempted rollback target: ${BASE_TIP}"
    else
      echo "note: the inverse compare-and-swap rolled refs/heads/${BASE_BRANCH} back to the verified base tip (a state the pre-tip leg cannot reach; reported for completeness)"
    fi
    emit_outcome indeterminate
    exit 2
  fi
  print_gate_evidence "$POST_OUT"
  case "$POST_RC" in
    2) emit_outcome indeterminate; exit 2 ;;
    *) emit_outcome tool_error; exit 3 ;;
  esac
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

# Primary land lock ownership (plan docs/history/plans/2026-10-25-primary-log-branch-drift-at-commit.md):
# the primary done lock is acquired before the merge lock and held through
# snapshot, landing, and recovery; the helper verifies both lock environments
# before its snapshot.
DONE_DIR="${DONE_LOCK_DIR:-}"
DONE_TOKEN="${DONE_LOCK_TOKEN:-}"
[[ -n "$DONE_DIR" ]] || tool_error "land requires DONE_LOCK_DIR set and non-empty (the Primary land lock ownership takes the primary done lock before the merge lock; acquire it via scripts/done-lock.sh and export the printed environment)"
[[ -n "$DONE_TOKEN" ]] || tool_error "land requires DONE_LOCK_TOKEN set and non-empty (the Primary land lock ownership takes the primary done lock before the merge lock; acquire it via scripts/done-lock.sh and export the printed environment)"
[[ -d "$DONE_DIR" ]] || tool_error "done lock directory does not exist: ${DONE_DIR}"
DONE_META="${DONE_DIR}/meta.env"
[[ -f "$DONE_META" ]] || tool_error "done lock record meta.env is missing: ${DONE_DIR}"
DONE_META_TOKEN="$(meta_field "$DONE_META" lock_token)"
[[ -n "$DONE_META_TOKEN" ]] || tool_error "done lock record carries an empty lock_token: ${DONE_META}"
[[ "$DONE_TOKEN" == "$DONE_META_TOKEN" ]] || tool_error "DONE_LOCK_TOKEN does not equal the record's lock_token (a stale generation or a fabricated environment)"
DONE_META_REPO="$(meta_field "$DONE_META" repo_root)"
[[ "$DONE_META_REPO" == "$REPO_ROOT" ]] || tool_error "done lock record repo_root '${DONE_META_REPO}' does not equal this primary checkout root '${REPO_ROOT}' (the Primary land done lock is keyed to the primary worktree)"

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
git -C "$REPO_ROOT" status --porcelain=v1 -z > "$SNAP_FILE" || \
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
  # Arm-1 bounded exit (plan 2026-10-10-coordination-single-writer-ttl, Task 1):
  # a foreign staged set gets a seconds-scale bounded wait before the refusal,
  # capped at 30s against the merge lock's own bounded-wait budget (300s), the
  # lock-hold extension acknowledged by staying under it; a live merge-lock
  # holder keeps the lock's own bounded wait (this arm only extends the
  # staged-set arm). After the wait, the staged set is re-derived and reported
  # with a holder-or-unattributed classification cross-referencing the open
  # execution/authoring claim files by plan path; the routing per D-9
  # (re-dispatch, park-for-operator, or skip-with-report) is the orchestrator's
  # call recorded in the session notes, and this refusal shape (the
  # park-for-operator route's reachable shape) is unchanged.
  STAGED_WAIT="${LAND_SQUASH_STAGED_WAIT_SECS:-5}"
  case "$STAGED_WAIT" in ''|*[!0-9]*) STAGED_WAIT=5 ;; esac
  (( STAGED_WAIT > 30 )) && STAGED_WAIT=30
  if (( STAGED_WAIT > 0 )); then
    sleep "$STAGED_WAIT"
  fi
  STAGED_AFTER=""
  STAGED_AFTER="$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | grep -v '^??' | grep -vE '^( M|MM| A| D)' | grep -E '^[MADRCU]{1,2} ' || true)"
  if [[ -z "$STAGED_AFTER" ]]; then
    echo "staged set cleared during the ${STAGED_WAIT}s bounded wait; continuing the landing"
  else
    CLAIMS_DIR="${REPO_ROOT}/docs/tmp/execution-claims"
    ACCLAIMS_DIR="${REPO_ROOT}/docs/tmp/authoring-claims"
    echo "refuse: staged state exists in the primary index (the landing requires a clean index at the snapshot):"
    printf '%s' "$STAGED_LIST" | sed 's/^/  /' || true
    echo "staged-set attribution (arm-1 bounded exit, waited ${STAGED_WAIT}s; route per D-9: re-dispatch, park-for-operator, or skip-with-report, recorded in the session notes):"
    while IFS= read -r sp; do
      [[ -n "$sp" ]] || continue
      sp_base="$(basename "$sp")"
      sp_stem="${sp_base%.*}"
      attributed=""
      for cd_dir in "$CLAIMS_DIR" "$ACCLAIMS_DIR"; do
        [[ -d "$cd_dir" ]] || continue
        for cf in "$cd_dir"/*.md; do
          [[ -f "$cf" ]] || continue
          if grep -q "${sp_base}" "$cf" 2>/dev/null || grep -q "${sp_stem}[^[:alnum:]]" "$cf" 2>/dev/null; then
            cf_sess="$(sed -n 's/^session: //p' "$cf" | head -n 1)"
            attributed="attributed to claim $(basename "$cf")${cf_sess:+ (session ${cf_sess})}"
            break 2
          fi
        done
      done
      if [[ -n "$attributed" ]]; then
        echo "  ${sp}: ${attributed}"
      else
        echo "  ${sp}: unattributed (no open claim file cross-references this path)"
      fi
    done <<< "$STAGED_LIST"
    emit_outcome fail
    exit 1
  fi
fi

# Pre-refusal: a locally dirty tracked path intersecting the branch's changed
# paths (the record-only-dirt protection; allowlist-agnostic by design).
BRANCH_PATHS_FILE="$(mktemp "${TMPDIR:-/tmp}/land-squash-bp.XXXXXX")"
if ! git -C "$REPO_ROOT" diff --name-only -z "$EXPECTED_TIP_SHA" "$SOURCE_TIP" > "$BRANCH_PATHS_FILE"; then
  rm -f "$BRANCH_PATHS_FILE"
  tool_error "git diff over the branch's changed paths failed"
fi
parse_status_z plain "$BRANCH_PATHS_FILE"
rm -f "$BRANCH_PATHS_FILE"
INTERSECT=""
for _bp_i in "${!Z_ITEMS[@]}"; do
  p="${Z_ITEMS[$_bp_i]}"
  if snapshot_has_dirty "$p"; then
    INTERSECT="${INTERSECT}${p}"$'\n'
  fi
done
if [[ -n "$INTERSECT" ]]; then
  echo "refuse: dirty intersection: locally modified tracked paths intersect the branch's changed paths (the landing would fold concurrent-writer bytes into the squash):"
  printf '%s' "$INTERSECT" | sed 's/^/  /' || true
  emit_outcome fail
  exit 1
fi

# The compose-time landing-claim grammar notice, before the landing commit
# is composed: warning-only, the landing outcome and exit code unchanged; a
# guard import failure here is one note line and the landing continues.
emit_grammar_notice

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
  run_reconcile_gate_or_refuse "$EXPECTED_TIP_SHA" "$LANDING_COMMIT"
  echo "new tip: ${LANDING_COMMIT}"
  git -C "$REPO_ROOT" diff --stat "$EXPECTED_TIP_SHA" "$LANDING_COMMIT" | sed 's/^/  /' || true
  emit_outcome pass
  exit 0
fi
if [[ "$POST_RC" -eq 1 ]]; then
  # POST_RC 1 is the pre-tip refusal alone (the gate's origin-only
  # divergence is an informational note with exit 0); the pre-swap gate
  # verified the landing commit's parentage onto the pre-tip, so a
  # pre-tip refusal here means the base ref no longer reads the landing
  # commit: an interleaved peer move.
  CURRENT_BASE="$(git -C "$REPO_ROOT" rev-parse --verify "refs/heads/${BASE_BRANCH}")" || \
    tool_error "base branch ref unresolvable after the landing: refs/heads/${BASE_BRANCH}"
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
