#!/usr/bin/env bash
# stack_review_round.sh: mechanical helper for one post-publish review-fix
# round on a published stack (a sequence of stacked task branches, each with
# a draft PR whose base is the predecessor branch, already pushed to the
# remote). One subcommand per failure-prone round step; the skills own the
# procedure, this script owns only the mechanics and verifies their outcomes.
#
# Subcommands:
#   affected      Derive the affected set from a stack base, the stack's
#                 ordered branch chain (lowest-first, as recorded in the
#                 stack run record), and the edited branch names: the lowest
#                 edited branch plus its chain descendants in chain order.
#   restack       Ordered restack wrapping Method C (the explicit-rebase
#                 method of record in
#                 agents/skills/update-stacked-branches/SKILL.md; reused by
#                 reference, never re-derived or bypassed here): capture a
#                 backup ref for every rewritten tip BEFORE any rewrite,
#                 then per descendant in chain order `git checkout
#                 <descendant>` plus `git rebase --onto <predecessor-new-tip>
#                 <predecessor-old-tip> <descendant>` (for the first link the
#                 predecessor is the amended branch: its recorded new tip and
#                 old tip), and verify parentage per link (the descendant
#                 contains the predecessor's new tip and carries exactly its
#                 own commit count above the old boundary, so no parent
#                 commits are replayed into the child). On a rebase conflict
#                 or a parentage failure: `git rebase --abort`, restore
#                 every rewritten descendant from its backup ref, exit
#                 nonzero. A recorded old tip that is not an ancestor of a
#                 descendant's tip refuses before replaying that descendant
#                 (the wrong-range guard: a wrong range cannot replay the
#                 whole stack), with the partially restacked chain restored
#                 from the backups. A missing or unresolvable old-tip
#                 argument refuses before any rebase runs.
#   push-leases   One lease push per branch: the remote tip is read through
#                 ls-remote immediately before each push and the push runs
#                 `git push --force-with-lease=<branch>:<remote-tip>`.
#                 Protected branch names (trunk, default, main, master,
#                 case-insensitive) refuse a force push before any remote
#                 call. Every refusal reports per branch.
#   verify-heads  One ls-remote comparison per branch: the remote head
#                 against the expected head and the remote base branch
#                 against the expected base, reporting equality or the
#                 observed mismatch.
#   retest-set    Print the caller-provided command set scoped to the
#                 affected branches. The project test policy stays the owner
#                 of what runs; the helper never encodes project commands
#                 and runs nothing itself.
#
# Backup namespace: refs/stack-review-backup/<branch>, one ref per rewritten
# descendant tip, captured before the first rewrite and kept after the run;
# deleting them belongs to the caller after the round verifies.
#
# Test-only seam (never set in production; a run that honors the seam prints
# one loud evidence line naming the value and its env):
#   STACK_REVIEW_LS_REMOTE
#       The ls-remote command the helper shells out to (default
#       `git ls-remote`). The command receives <remote> and the full refspec
#       as arguments and must print standard ls-remote lines
#       (`<sha><TAB><ref>`). The focused suite interposes a stub through this
#       seam to stage a stale remote tip between read and push
#       deterministically, and to force read failures.
#
# Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run
# ends with exactly one final `OUTCOME: <pass|fail|indeterminate|tool_error>`
# line on stdout matching the exit code: 0 pass; 1 fail (modeled refusal or
# mismatch; the offending evidence precedes the line); 2 indeterminate
# (evidence insufficient or outside the modeled cases; in a multi-branch run
# observing both classified refusals and unclassifiable branches, the run
# reports indeterminate and still names every regressed branch); 3 tool
# error (usage, missing or unresolvable inputs, environment, internal
# failure). --help and usage text are metadata-exempt (no OUTCOME line). A
# run with no final OUTCOME line is tool error: stop and re-derive from
# disk. No placement deviation: every subcommand emits the line on stdout.
# Per-subcommand mapping:
#   affected      set derived pass; unresolvable stack base, an empty chain,
#                 or an edited branch outside the chain tool error naming it.
#   restack       full chain replayed with parentage verified pass; a rebase
#                 conflict, a parentage failure, or the safety-witness
#                 refusal fail with rewritten branches restored from the
#                 backups; a missing or unresolvable old tip or new tip tool
#                 error before any rewrite.
#   push-leases   every branch pushed pass; a protected-name refusal or a
#                 failed lease push fail; an ls-remote read failure names the
#                 branch and reports indeterminate (uncertainty dominates a
#                 multi-branch run).
#   verify-heads  every comparison equal pass; any mismatch fail; an
#                 ls-remote read failure names the branch and reports
#                 indeterminate (uncertainty dominates a multi-branch run).
#   retest-set    the caller command set printed pass; missing branches or a
#                 missing command set tool error (the helper never invents
#                 commands).
#
# Focused suite: scripts/test_stack_review_round.py (scratch git repos under
# mktemp -d with explicit teardown). Bash only: no zsh-only expansions.
set -euo pipefail

PROG="stack-review-round"
OUTCOME_EMITTED=0
METADATA_EXIT=0
SEVERITY=0  # 0 pass, 1 fail, 2 indeterminate; indeterminate dominates
CHAIN_ARR=()
LS_REMOTE_CMD="${STACK_REVIEW_LS_REMOTE:-git ls-remote}"
LS_REMOTE_OVERRIDE_REPORTED=0

emit_outcome() {
  if [[ "$OUTCOME_EMITTED" -eq 0 ]]; then
    echo "OUTCOME: $1"
    OUTCOME_EMITTED=1
  fi
}

finish() {  # finish <outcome> <exit-code>
  emit_outcome "$1"
  exit "$2"
}

on_exit() {
  local rc="$?"
  if [[ "$METADATA_EXIT" -eq 1 || "$OUTCOME_EMITTED" -eq 1 ]]; then
    return
  fi
  echo "${PROG}: unclassified exit (rc ${rc}) before any OUTCOME line; reporting tool error" >&2
  echo "OUTCOME: tool_error"
  OUTCOME_EMITTED=1
  exit 3
}
trap on_exit EXIT

escalate() {  # escalate <0|1|2>; the higher severity wins (2 beats 1)
  local level="$1"
  if [[ "$level" -gt "$SEVERITY" ]]; then
    SEVERITY="$level"
  fi
}

finish_severity() {
  if [[ "$SEVERITY" -eq 0 ]]; then
    finish pass 0
  elif [[ "$SEVERITY" -eq 1 ]]; then
    finish fail 1
  else
    finish indeterminate 2
  fi
}

usage() {
  cat <<'EOF'
Usage: bash scripts/stack_review_round.sh <subcommand> [args...]

Subcommands:
  affected --stack-base <ref> --chain <b1,b2,...> --edited <e1[,e2,...]>
      Print the affected set: the lowest edited branch (earliest chain
      position among the edited names) plus its chain descendants in chain
      order. The chain is the stack's ordered branch chain, lowest-first, as
      recorded in the stack run record.
  restack --old-tip <sha> --new-tip <sha> [--chain <d1,d2,...>]
      Restack the descendants of the amended branch in chain order, wrapping
      Method C: one backup ref per descendant tip
      (refs/stack-review-backup/<branch>) before any rewrite, then per
      descendant `git checkout <descendant>` plus `git rebase --onto
      <predecessor-new-tip> <predecessor-old-tip> <descendant>`, then
      per-link parentage verification. Conflicts and parentage failures
      abort and restore from the backups; an old tip that is not an ancestor
      of a descendant tip refuses before replaying that descendant. A
      missing or unresolvable --old-tip refuses before any rebase. With no
      --chain the restack is a recorded no-op. Backup refs are kept after
      the run.
  push-leases [--remote <name>] --branch <b> [--branch <b>...]
      One lease push per branch: read the remote tip via ls-remote
      immediately before each push, then
      `git push --force-with-lease=<branch>:<remote-tip>`. Protected branch
      names (trunk, default, main, master, case-insensitive) refuse before
      any remote call. Refusals report per branch. Default remote: origin.
  verify-heads [--remote <name>] (--branch <b> --base-ref <ref>
               --expected-base <sha> --expected-head <sha>)...
      One ls-remote comparison per branch: the branch's remote head against
      --expected-head and the base branch's remote tip against
      --expected-base, reporting equality or the observed mismatch per
      branch. Default remote: origin.
  retest-set --branch <b> [--branch <b>...] --command <cmd> [--command ...]
      Print the caller-provided command set scoped to the affected branches.
      The project test policy owns what runs; the helper never encodes or
      invents project commands.

Environment:
  STACK_REVIEW_LS_REMOTE
      Override the ls-remote command (default `git ls-remote`). Declared
      test-only seam; a run that honors it prints one loud evidence line
      naming the value and its env.

Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
with exactly one final line `OUTCOME: <pass|fail|indeterminate|tool_error>`
on stdout matching the exit code (0 pass; 1 fail, the modeled refusal with
the offending evidence above the line; 2 indeterminate; 3 tool error).
--help and this usage text are metadata-exempt (no OUTCOME line).
EOF
}

require_git_repo() {
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "${PROG}: not inside a git repository"
    finish tool_error 3
  fi
}

# split a comma list into the array named by $2 (caller's scope; bash 3.2)
split_csv() {
  local IFS=','
  read -r -a "$2" <<< "$1"
}

join_args() {  # join_args <elem>...: print the arguments comma-joined
  local IFS=','
  printf '%s' "$*"
}

need_flag_value() {  # need_flag_value <flag> <remaining-arg-count> <value>
  if [[ "$2" -lt 2 || -z "${3:-}" ]]; then
    echo "${PROG}: $1 requires a value" >&2
    finish tool_error 3
  fi
}

ls_remote_ref() {  # ls_remote_ref <remote> <refspec>: prints the sha; rc 1 on failure
  local remote="$1" refspec="$2" out sha
  if [[ "$LS_REMOTE_OVERRIDE_REPORTED" -eq 0 && -n "${STACK_REVIEW_LS_REMOTE:-}" ]]; then
    # The loud-seam advisory goes to STDERR: every caller captures this
    # function's stdout as the parsed remote tip.
    echo "${PROG}: ls-remote override honored: STACK_REVIEW_LS_REMOTE=${STACK_REVIEW_LS_REMOTE}" >&2
    LS_REMOTE_OVERRIDE_REPORTED=1
  fi
  if ! out="$($LS_REMOTE_CMD "$remote" "$refspec" 2>/dev/null)"; then
    return 1
  fi
  sha="$(printf '%s\n' "$out" | head -n1 | cut -f1)"
  if ! [[ "$sha" =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]]; then
    return 1
  fi
  printf '%s' "$sha"
}

is_protected_branch() {  # case-insensitive match on the four protected names
  local lc
  lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$lc" in
    trunk|default|main|master) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# affected
# ---------------------------------------------------------------------------
cmd_affected() {
  local stack_base="" chain_arg="" edited_arg=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --stack-base)
        need_flag_value --stack-base $# "${2:-}"
        stack_base="$2"; shift 2 ;;
      --chain)
        need_flag_value --chain $# "${2:-}"
        chain_arg="$2"; shift 2 ;;
      --edited)
        need_flag_value --edited $# "${2:-}"
        edited_arg="$2"; shift 2 ;;
      *)
        echo "${PROG}: affected: unknown argument: $1" >&2
        finish tool_error 3 ;;
    esac
  done
  require_git_repo

  local chain=()
  split_csv "$chain_arg" CHAIN_ARR
  local token
  for token in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
    if [[ -n "$token" ]]; then
      chain+=("$token")
    fi
  done
  if [[ "${#chain[@]}" -eq 0 ]]; then
    echo "${PROG}: affected: the ordered branch chain is empty; pass --chain <b1,b2,...> lowest-first"
    finish tool_error 3
  fi

  local edited=()
  split_csv "$edited_arg" CHAIN_ARR
  for token in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
    if [[ -n "$token" ]]; then
      edited+=("$token")
    fi
  done
  if [[ "${#edited[@]}" -eq 0 ]]; then
    echo "${PROG}: affected: no edited branch names; pass --edited <e1[,e2,...]>"
    finish tool_error 3
  fi

  local stack_base_sha
  stack_base_sha="$(git rev-parse --verify --quiet "${stack_base}^{commit}")" || true
  if [[ -z "$stack_base_sha" ]]; then
    echo "${PROG}: affected: stack base does not resolve: ${stack_base}"
    finish tool_error 3
  fi

  # The lowest edited branch: the earliest chain position among the edited
  # names. An edited name outside the chain is outside the model.
  local e i found lowest=-1
  for e in "${edited[@]}"; do
    found=-1
    for i in "${!chain[@]}"; do
      if [[ "${chain[$i]}" == "$e" ]]; then
        found="$i"
        break
      fi
    done
    if [[ "$found" -eq -1 ]]; then
      echo "${PROG}: affected: edited branch is not in the recorded chain: ${e}"
      finish tool_error 3
    fi
    if [[ "$lowest" -eq -1 || "$found" -lt "$lowest" ]]; then
      lowest="$found"
    fi
  done

  echo "${PROG}: affected: stack base: ${stack_base}"
  echo "${PROG}: affected: chain (lowest-first): $(join_args "${chain[@]}")"
  echo "${PROG}: affected: lowest edited branch: ${chain[$lowest]}"
  local suffix=()
  for ((i = lowest; i < ${#chain[@]}; i++)); do
    echo "${PROG}: affected: affected branch: ${chain[$i]}"
    suffix+=("${chain[$i]}")
  done
  echo "${PROG}: affected: affected set: $(join_args "${suffix[@]}")"
  finish pass 0
}

# ---------------------------------------------------------------------------
# restack
# ---------------------------------------------------------------------------
restore_chain_from_backups() {
  local d b_sha
  for d in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
    b_sha="$(git rev-parse --verify --quiet "refs/stack-review-backup/${d}")" || true
    if [[ -n "$b_sha" ]]; then
      if git update-ref "refs/heads/${d}" "$b_sha"; then
        echo "${PROG}: restack: restored ${d} from refs/stack-review-backup/${d}"
      else
        echo "${PROG}: restack: WARNING: restore failed for ${d}; re-derive from refs/stack-review-backup/${d}"
      fi
    fi
  done
}

cmd_restack() {
  local old_tip_arg="" new_tip_arg="" chain_present=0 chain_arg=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --old-tip)
        need_flag_value --old-tip $# "${2:-}"
        old_tip_arg="$2"; shift 2 ;;
      --new-tip)
        need_flag_value --new-tip $# "${2:-}"
        new_tip_arg="$2"; shift 2 ;;
      --chain)
        need_flag_value --chain $# "${2:-}"
        chain_present=1; chain_arg="$2"; shift 2 ;;
      *)
        echo "${PROG}: restack: unknown argument: $1" >&2
        finish tool_error 3 ;;
    esac
  done
  require_git_repo

  # The old tip gates everything: refuse before any rebase when missing or
  # unresolvable, naming the old tip.
  if [[ -z "$old_tip_arg" ]]; then
    echo "${PROG}: restack: the pre-captured old tip of the amended branch is missing (--old-tip); refusing before any rebase"
    finish tool_error 3
  fi
  local old_tip
  old_tip="$(git rev-parse --verify --quiet "${old_tip_arg}^{commit}")" || true
  if [[ -z "$old_tip" ]]; then
    echo "${PROG}: restack: the recorded old tip does not resolve to a commit: ${old_tip_arg}; refusing before any rebase"
    finish tool_error 3
  fi

  if [[ -z "$new_tip_arg" ]]; then
    echo "${PROG}: restack: the amended branch's new tip is missing (--new-tip); refusing before any rebase"
    finish tool_error 3
  fi
  local new_tip
  new_tip="$(git rev-parse --verify --quiet "${new_tip_arg}^{commit}")" || true
  if [[ -z "$new_tip" ]]; then
    echo "${PROG}: restack: the amended branch's new tip does not resolve to a commit: ${new_tip_arg}; refusing before any rebase"
    finish tool_error 3
  fi

  CHAIN_ARR=()
  if [[ "$chain_present" -eq 1 ]]; then
    local token
    split_csv "$chain_arg" CHAIN_ARR
    local compacted=()
    for token in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
      if [[ -n "$token" ]]; then
        compacted+=("$token")
      fi
    done
    CHAIN_ARR=()
    local d
    for d in ${compacted[@]+"${compacted[@]}"}; do
      CHAIN_ARR+=("$d")
    done
  fi

  if [[ "${#CHAIN_ARR[@]}" -eq 0 ]]; then
    echo "${PROG}: restack: no descendants recorded; nothing to restack"
    echo "${PROG}: restack: amended branch new tip: ${new_tip}"
    finish pass 0
  fi

  # Every descendant must resolve before anything is rewritten.
  local d d_tip
  for d in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
    d_tip="$(git rev-parse --verify --quiet "refs/heads/${d}")" || true
    if [[ -z "$d_tip" ]]; then
      echo "${PROG}: restack: descendant branch does not resolve: ${d}; refusing before any rewrite"
      finish tool_error 3
    fi
  done

  # Backup refs for every rewritten tip BEFORE any rewrite (Method C Phase 0
  # discipline: backups are load-bearing).
  for d in ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}; do
    d_tip="$(git rev-parse --verify "refs/heads/${d}")"
    git update-ref "refs/stack-review-backup/${d}" "$d_tip"
    echo "${PROG}: restack: backup ref captured before any rewrite: refs/stack-review-backup/${d} at ${d_tip}"
  done

  # Per-link replay in chain order. For link 0 the predecessor is the
  # amended branch (its recorded new tip and old tip); for link i the
  # predecessor is chain[i-1] (its tip after its own link, and its pre-restack
  # backup as the old boundary).
  local i pred_old pred_new backup_sha count_old count_new
  for i in ${CHAIN_ARR[@]+"${!CHAIN_ARR[@]}"}; do
    d="${CHAIN_ARR[$i]}"
    if [[ "$i" -eq 0 ]]; then
      pred_old="$old_tip"
      pred_new="$new_tip"
    else
      pred_old="$(git rev-parse --verify "refs/stack-review-backup/${CHAIN_ARR[$((i - 1))]}")"
      pred_new="$(git rev-parse --verify "refs/heads/${CHAIN_ARR[$((i - 1))]}")"
    fi
    backup_sha="$(git rev-parse --verify "refs/stack-review-backup/${d}")"

    # Safety witness: the recorded old boundary must anchor the replay range.
    # A wrong range refuses before replaying this descendant; it can never
    # replay the whole stack.
    if ! git merge-base --is-ancestor "$pred_old" "refs/heads/${d}"; then
      echo "${PROG}: restack: safety witness failed: recorded old tip ${pred_old} is not an ancestor of ${d} at $(git rev-parse "refs/heads/${d}"); refusing before replaying ${d}"
      echo "${PROG}: restack: restoring rewritten branches from backups"
      restore_chain_from_backups
      finish fail 1
    fi

    if ! git checkout --quiet "$d"; then
      echo "${PROG}: restack: checkout failed for ${d}; restoring rewritten branches from backups"
      restore_chain_from_backups
      finish tool_error 3
    fi

    if ! git rebase --onto "$pred_new" "$pred_old" "$d"; then
      echo "${PROG}: restack: rebase failed for ${d} (conflict or rejection); aborting and restoring from backups"
      git rebase --abort >/dev/null 2>&1 || true
      restore_chain_from_backups
      finish fail 1
    fi

    # Parentage verification: the descendant sits on the predecessor's new
    # tip and carries exactly its own commit count above the old boundary
    # (a parent reversal or a replayed parent commit moves the count).
    if ! git merge-base --is-ancestor "$pred_new" "refs/heads/${d}"; then
      echo "${PROG}: restack: parentage verification failed for ${d}: predecessor tip ${pred_new} is not an ancestor of the replayed ${d}; restoring from backups"
      restore_chain_from_backups
      finish fail 1
    fi
    count_old="$(git rev-list --count "${pred_old}..${backup_sha}")"
    count_new="$(git rev-list --count "${pred_new}..refs/heads/${d}")"
    if [[ "$count_old" != "$count_new" ]]; then
      echo "${PROG}: restack: parentage verification failed for ${d}: commit count changed across the replay (before ${count_old}, after ${count_new}); restoring from backups"
      restore_chain_from_backups
      finish fail 1
    fi
    echo "${PROG}: restack: link ${d}: replayed ${count_new} commit(s) onto ${pred_new}; parentage verified"
  done

  echo "${PROG}: restack: chain restacked in order ($(join_args ${CHAIN_ARR[@]+"${CHAIN_ARR[@]}"}))"
  echo "${PROG}: restack: backup refs kept for caller verification: refs/stack-review-backup/<branch>"
  finish pass 0
}

# ---------------------------------------------------------------------------
# push-leases
# ---------------------------------------------------------------------------
cmd_push_leases() {
  local remote="origin"
  local branches=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --remote)
        need_flag_value --remote $# "${2:-}"
        remote="$2"; shift 2 ;;
      --branch)
        need_flag_value --branch $# "${2:-}"
        branches+=("$2"); shift 2 ;;
      *)
        echo "${PROG}: push-leases: unknown argument: $1" >&2
        finish tool_error 3 ;;
    esac
  done
  if [[ "${#branches[@]}" -eq 0 ]]; then
    echo "${PROG}: push-leases: at least one --branch is required"
    finish tool_error 3
  fi
  require_git_repo

  SEVERITY=0
  local b tip push_out push_rc first_line
  for b in ${branches[@]+"${branches[@]}"}; do
    # Protected names refuse a force push before any remote call.
    if is_protected_branch "$b"; then
      echo "${PROG}: push-leases: ${b}: refused (protected branch name; force push refused before any remote call)"
      escalate 1
      continue
    fi
    if ! tip="$(ls_remote_ref "$remote" "refs/heads/${b}")"; then
      echo "${PROG}: push-leases: ${b}: ls-remote read failed for refs/heads/${b}; cannot build the lease"
      escalate 2
      continue
    fi
    push_rc=0
    push_out="$(git push --force-with-lease="${b}:${tip}" "$remote" "$b" 2>&1)" && push_rc=0 || push_rc=$?
    if [[ "$push_rc" -eq 0 ]]; then
      echo "${PROG}: push-leases: ${b}: pushed with lease ${tip}"
    else
      echo "${PROG}: push-leases: ${b}: refused (push failed; the remote tip moved between read and push or the lease mismatched)"
      first_line="$(printf '%s\n' "$push_out" | grep -m1 . || true)"
      if [[ -n "$first_line" ]]; then
        echo "    push: ${first_line}"
      fi
      escalate 1
    fi
  done
  finish_severity
}

# ---------------------------------------------------------------------------
# verify-heads
# ---------------------------------------------------------------------------
cmd_verify_heads() {
  local remote="origin"
  local branches=() base_refs=() expected_bases=() expected_heads=()
  local current=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --remote)
        need_flag_value --remote $# "${2:-}"
        remote="$2"; shift 2 ;;
      --branch)
        need_flag_value --branch $# "${2:-}"
        branches+=("$2"); base_refs+=(""); expected_bases+=(""); expected_heads+=("")
        current="${#branches[@]}"
        shift 2 ;;
      --base-ref)
        if [[ "$current" -eq 0 ]]; then
          echo "${PROG}: verify-heads: --base-ref before any --branch" >&2
          finish tool_error 3
        fi
        need_flag_value --base-ref $# "${2:-}"
        base_refs[$((current - 1))]="$2"; shift 2 ;;
      --expected-base)
        if [[ "$current" -eq 0 ]]; then
          echo "${PROG}: verify-heads: --expected-base before any --branch" >&2
          finish tool_error 3
        fi
        need_flag_value --expected-base $# "${2:-}"
        expected_bases[$((current - 1))]="$2"; shift 2 ;;
      --expected-head)
        if [[ "$current" -eq 0 ]]; then
          echo "${PROG}: verify-heads: --expected-head before any --branch" >&2
          finish tool_error 3
        fi
        need_flag_value --expected-head $# "${2:-}"
        expected_heads[$((current - 1))]="$2"; shift 2 ;;
      *)
        echo "${PROG}: verify-heads: unknown argument: $1" >&2
        finish tool_error 3 ;;
    esac
  done
  if [[ "${#branches[@]}" -eq 0 ]]; then
    echo "${PROG}: verify-heads: at least one --branch check is required"
    finish tool_error 3
  fi
  local i b bref eb eh
  for i in ${branches[@]+"${!branches[@]}"}; do
    if [[ -z "${base_refs[$i]}" || -z "${expected_bases[$i]}" || -z "${expected_heads[$i]}" ]]; then
      echo "${PROG}: verify-heads: incomplete check for ${branches[$i]}: --base-ref, --expected-base, and --expected-head are all required"
      finish tool_error 3
    fi
  done
  require_git_repo

  SEVERITY=0
  local obs_head obs_base
  for i in ${branches[@]+"${!branches[@]}"}; do
    b="${branches[$i]}"
    bref="${base_refs[$i]}"
    eb="${expected_bases[$i]}"
    eh="${expected_heads[$i]}"
    if ! obs_head="$(ls_remote_ref "$remote" "refs/heads/${b}")"; then
      echo "${PROG}: verify-heads: ${b}: ls-remote read failed for refs/heads/${b}; head unverifiable"
      escalate 2
    elif [[ "$obs_head" == "$eh" ]]; then
      echo "${PROG}: verify-heads: ${b}: head match (${obs_head})"
    else
      echo "${PROG}: verify-heads: ${b}: head mismatch (expected ${eh}, observed ${obs_head})"
      escalate 1
    fi
    if ! obs_base="$(ls_remote_ref "$remote" "refs/heads/${bref}")"; then
      echo "${PROG}: verify-heads: ${b}: ls-remote read failed for refs/heads/${bref} (base branch); base unverifiable"
      escalate 2
    elif [[ "$obs_base" == "$eb" ]]; then
      echo "${PROG}: verify-heads: ${b}: base match (${bref} at ${obs_base})"
    else
      echo "${PROG}: verify-heads: ${b}: base mismatch (${bref}; expected ${eb}, observed ${obs_base})"
      escalate 1
    fi
  done
  finish_severity
}

# ---------------------------------------------------------------------------
# retest-set
# ---------------------------------------------------------------------------
cmd_retest_set() {
  local branches=() commands=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --branch)
        need_flag_value --branch $# "${2:-}"
        branches+=("$2"); shift 2 ;;
      --command)
        need_flag_value --command $# "${2:-}"
        commands+=("$2"); shift 2 ;;
      *)
        echo "${PROG}: retest-set: unknown argument: $1" >&2
        finish tool_error 3 ;;
    esac
  done
  if [[ "${#branches[@]}" -eq 0 ]]; then
    echo "${PROG}: retest-set: at least one --branch is required"
    finish tool_error 3
  fi
  if [[ "${#commands[@]}" -eq 0 ]]; then
    echo "${PROG}: retest-set: no retest commands provided; the project test policy owns the command set and the helper never encodes project commands"
    finish tool_error 3
  fi

  echo "${PROG}: retest-set: affected branches: $(join_args "${branches[@]}")"
  echo "${PROG}: retest-set: command set (as provided by the caller):"
  local b c
  for b in ${branches[@]+"${branches[@]}"}; do
    for c in ${commands[@]+"${commands[@]}"}; do
      echo "${PROG}: retest-set: ${b}: ${c}"
    done
  done
  finish pass 0
}

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
main() {
  local cmd="${1:-}"
  if [[ $# -gt 0 ]]; then
    shift
  fi
  case "$cmd" in
    affected) cmd_affected "$@" ;;
    restack) cmd_restack "$@" ;;
    push-leases) cmd_push_leases "$@" ;;
    verify-heads) cmd_verify_heads "$@" ;;
    retest-set) cmd_retest_set "$@" ;;
    -h|--help|help)
      METADATA_EXIT=1
      usage
      exit 0
      ;;
    "")
      echo "${PROG}: a subcommand is required (affected, restack, push-leases, verify-heads, retest-set)" >&2
      usage >&2
      finish tool_error 3
      ;;
    *)
      echo "${PROG}: unknown subcommand: ${cmd}" >&2
      usage >&2
      finish tool_error 3
      ;;
  esac
}

main "$@"
