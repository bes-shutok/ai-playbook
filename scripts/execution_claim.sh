#!/usr/bin/env bash
# Execution claim gateway: the mechanical prerequisite between a plan-work
# start and its run worktree. `take` is the atomic unit: claim
# create-or-refuse immediately followed by run-worktree creation; a failed
# take leaves no half-created state. `claim` is the same create-or-refuse
# arm without worktree creation (the authorized primary-placement lane).
# `refresh` re-stamps the claim's updated line (recreating after a
# takeover, writing the base and start-commit lines when passed, fencing a
# claim naming a foreign session). `release` deletes the claim only while
# it names this session; a missing claim is a loud refusal. `sweep` walks
# the whole claims directory and deletes exactly the spent claims: a claim
# whose plan is landed (the plan file exists under the plans root's
# completed/ archive, or the plan is absent from the whole plans root
# while a landing commit subject on the main-history branch names the
# claim's slug) and
# whose recorded branch line resolves to no worktree; every other claim is
# skipped untouched with a one-line reason (fail closed per claim), and
# the scan itself always ends pass.
#
# Claim file: docs/tmp/execution-claims/<artifact-slug>.md in the PRIMARY
# checkout (the first `git worktree list --porcelain` worktree entry); four
# frontmatter lines at creation (session, plan, created, updated) plus the
# branch line when --branch is passed (required for take; occupancy
# evidence and the recorded run branch elsewhere), the start-commit line
# when --start-commit is passed (the value resolved through
# `git rev-parse --verify <sha>^{commit}` first; an unresolvable value is
# a usage refusal writing nothing), and the base line at the take itself
# when --base is passed, otherwise at the first refresh that passes it.
# The artifact slug derives through
# the python single source of truth (`plan_readiness.py
# --print-artifact-slug` next to this script); it is never reimplemented
# here.
#
# Freshness: one cadence period, two hours (FRESHNESS_SECS, pinned). A
# foreign claim whose updated line is fresher than two hours refuses the
# take with the holder session, the claim age, the occupying worktree when
# derivable, and the override route named. A stale foreign claim is taken
# over: the claim is re-read immediately before the unlink and unlinked only
# while it still names the same foreign session with a stale updated line,
# the takeover is recorded, then this session's claim is created. The
# branch-occupant gate runs before the takeover: a stale foreign claim on a
# branch held by an existing worktree is refused BEFORE any takeover, the
# foreign claim preserved (the refusal names the occupying worktree path
# and both remedies, adopt the existing worktree per the recognition arm or
# remove it deliberately). The gate runs again after the claim is acquired
# (an unclaimed leftover worktree lands there, and so does an occupant that
# appeared after the pre-takeover gate); either refusal cleans up the fresh
# claim this invocation created. Any failure of the worktree add after a
# claim created in this invocation deletes that claim, rolls back the
# branch this add created (never a branch that pre-existed: `git worktree
# add -b` creates the branch before validating the path), and names the git
# error. The same guarantee binds to the exit path: a trap on exit,
# interrupt, and termination removes this invocation's fresh claim on any
# later failure or signal (an uncreatable worktree parent, a signal landing
# while the worktree add is in flight), removes any worktree that this
# invocation's own add brought into existence (best-effort `git worktree
# remove --force`; a path that already carried a registered worktree before
# the add is never touched, and an unregistered leftover directory may
# survive, the removal being best-effort), and disarms once the take has
# succeeded, so no exit route strands a half-created take: any non-zero
# exit leaves neither the fresh claim nor a worktree this add created, and
# only the success path leaves both.
#
# Repository anchor: the git toplevel of the process working directory; the
# claims directory always resolves in the primary checkout of that
# repository. Tests fabricate their own primary checkout by running this
# script inside a scratch `git init` repository (that scratch repository is
# its own primary checkout, the first entry of its own worktree listing), so
# production resolution carries no override and no repository ever has to
# point the script elsewhere.
#
# Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with a final stdout
# line `OUTCOME: pass`, 1 `OUTCOME: fail` (modeled refusal; the evidence
# lines go to stderr and the final `OUTCOME: fail` line to stdout), 3
# `OUTCOME: tool_error` (usage violations carry the usage text, the error,
# and the final line on stderr per the argparse-override precedent;
# environment failures carry the message on stderr and the final line on
# stdout). There is no indeterminate class today. `--help` is a metadata
# exit with no OUTCOME line.
set -euo pipefail

FRESHNESS_SECS=7200  # one cadence period: two hours
CLAIMS_REL="docs/tmp/execution-claims"
PYTHON="python3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE=""
PLAN_ARG=""
SESSION=""
BRANCH=""
WT_PARENT=""
BASE=""
START_COMMIT=""

# Shared resolution results (set by resolve_context)
ANCHOR=""
PRIMARY=""
CLAIMS_DIR=""
SLUG=""
CLAIM_PATH=""
# State machine results (set by acquire_claim)
CREATED_HERE=0
OWN_CLAIM_HOOK=""
CONVERSION_DONE=0
# Per-mode pre-takeover gate: when set, it runs inside acquire_claim after
# the fresh-foreign refusal and before the stale takeover (take mode's
# branch-occupant check lives here, so a stale foreign claim with an
# occupied branch is refused before its claim is destroyed).
PRE_TAKEOVER_HOOK=""
# Exit-path cleanup state: TAKE_GATE arms the cleanup for the take mode,
# TAKE_OK marks the success path (the worktree add succeeded, so the claim
# must survive). CREATED_HERE stays the acquire_claim discipline: the claim
# was created by this process in this invocation, and only such a claim is
# ever removed by the cleanup. WT_AT_RISK arms the cleanup's worktree arm
# (the worktree removal and the branch rollback) from just before the add
# is attempted until TAKE_OK; the WT_PRE_REGISTERED witness (captured
# before the add) scopes the removal to worktrees this invocation's own
# add may have brought into existence, and the BRANCH_PRE_EXISTED witness
# scopes the rollback to branches absent just before the add.
TAKE_GATE=0
TAKE_OK=0
WT_AT_RISK=0
# Witnesses captured before the worktree add is attempted (both lead the
# add): a path already carrying a registered worktree is never removed by
# the exit-path cleanup (WT_PRE_REGISTERED), and a branch that already
# existed is never deleted by either rollback, the add-failure arm's or
# the exit-path cleanup's (BRANCH_PRE_EXISTED).
WT_PRE_REGISTERED=0
BRANCH_PRE_EXISTED=0

usage() {
  cat <<'EOF'
Usage: execution_claim.sh <mode> [plan-path] [options]

Modes:
  take     Claim create-or-refuse immediately followed by run-worktree
           creation (the atomic gateway; the only way to obtain the run
           worktree).
  claim    The same create-or-refuse arm without worktree creation (the
           authorized primary-placement lane).
  refresh  Re-stamp the claim's updated line; recreates the claim after a
           takeover deleted it; writes the base line when --base is passed
           and the start-commit line when --start-commit is passed;
           refuses a claim naming a foreign session.
  release  Delete the claim only while it names this session; a foreign
           claim is refused untouched; a missing claim is a loud refusal.
  sweep    Delete every spent claim in the claims directory: a claim is
           deleted only when its plan is landed (the plan file exists
           under the plans root's completed/ archive, or the plan is
           absent from the whole plans root while a landing commit subject
           (the repository's `check: land ...` form) on the main-history
           branch names the claim's slug) AND its recorded branch line
           resolves to no worktree; every other claim is skipped untouched
           with a one-line reason (fail closed per claim). Takes no plan
           operand; the scan ends pass.

Options:
  --session <id>           This session's id (required in every mode).
  --branch <name>          The run branch (required for take; occupancy
                           evidence elsewhere); recorded as the claim's
                           branch line when passed.
  --worktree-parent <dir>  Parent directory for the run worktree; the
                           worktree lands at <dir>/<branch> (required for
                           take).
  --base <ref>             Starting point of the created worktree (take);
                           the base line written into the claim (refresh).
  --start-commit <sha>     The run's start commit; resolved through
                           `git rev-parse --verify` and recorded resolved
                           as the claim's start-commit line; an
                           unresolvable value is a usage refusal writing
                           nothing.
  --help                   This text (metadata exit, no OUTCOME line).

The plan operand (required for take, claim, refresh, and release; never
accepted by sweep) must be a readable file; its canonical artifact slug
derives through plan_readiness.py --print-artifact-slug.
EOF
}

usage_error() {
  usage >&2
  printf 'error: %s\n' "$1" >&2
  printf 'OUTCOME: tool_error\n' >&2
  exit 3
}

die_tool() {
  # Runtime environment failure: the message on stderr, the final line on
  # stdout, so a classified run still ends with exactly one OUTCOME line.
  printf 'error: %s\n' "$1" >&2
  printf 'OUTCOME: tool_error\n'
  exit 3
}

die_fail() {
  # Modeled refusal: the evidence lines were already written to stderr.
  printf 'OUTCOME: fail\n'
  exit 1
}

evidence() {
  printf '%s\n' "$1"
}

refuse() {
  printf '%s\n' "$1" >&2
}

cleanup_fresh_claim() {
  # The exit-path cleanup backing the atomic take: removes this
  # invocation's fresh claim, and any worktree this invocation's own add
  # may have brought into existence, when the take did not reach its
  # success path. Every gate must hold: the take mode armed the cleanup
  # (TAKE_GATE), the claim was created by this process (CREATED_HERE), is
  # still present, and still names this session (the owner check keeps a
  # signal landing in a takeover race's clear-side window from deleting a
  # concurrent winner's claim; the explicit refusal arms remove this
  # invocation's own claim themselves, so this never double-cleans), the
  # take has not succeeded (TAKE_OK), and the add was attempted
  # (WT_AT_RISK). The worktree arm's two halves are witness-gated
  # separately: the worktree removal runs only when the path carried no
  # registered worktree before the add (WT_PRE_REGISTERED), and the branch
  # rollback runs only when the branch was absent just before the add
  # (BRANCH_PRE_EXISTED). The cleanup can be reached with a pre-registered
  # path (the add fails over the occupied path and the refusal exits), so
  # the witness gates, not the arm point alone, keep the halves off
  # pre-existing occupants; nesting the branch rollback under the path
  # witness too would let a signal mid-add over an occupied path strand
  # the add-created branch. The worktree removal is best-effort: `git
  # worktree remove --force` refuses a path that is not a registered
  # worktree, and that refusal is the safe outcome. An interrupted run
  # answers no OUTCOME line and is classified tool error by the contract's
  # no-final-line rule.
  if (( TAKE_GATE && ! TAKE_OK )); then
    if (( CREATED_HERE )) \
      && [[ -e "$CLAIM_PATH" ]] \
      && [[ "$(claim_field "$CLAIM_PATH" session)" == "$SESSION" ]]; then
      rm -f "$CLAIM_PATH"
      refuse "cleanup: removed this invocation's fresh claim $CLAIM_PATH"
    fi
    if (( WT_AT_RISK )); then
      if (( ! WT_PRE_REGISTERED )); then
        if git -C "$ANCHOR" worktree remove --force "$WT_PARENT/$BRANCH" 2>/dev/null; then
          refuse "cleanup: removed this invocation's half-created worktree $WT_PARENT/$BRANCH"
        fi
      fi
      if (( ! BRANCH_PRE_EXISTED )); then
        if git -C "$ANCHOR" branch -D "$BRANCH" >/dev/null 2>&1; then
          refuse "cleanup: removed this invocation's stranded branch $BRANCH"
        fi
      fi
    fi
  fi
}
run_exit_cleanup() {
  # The combined exit-path cleanup: gateway-owned lock release first (a
  # handled exit never strands the conversion locks), then the atomic-take
  # claim/worktree cleanup.
  gateway_cleanup_trap
  cleanup_fresh_claim
}
trap run_exit_cleanup EXIT
trap 'run_exit_cleanup; exit 130' INT
trap 'run_exit_cleanup; exit 143' TERM
iso_now() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

iso_to_epoch() {
  # YYYY-MM-DDTHH:MM:SSZ (the writer's UTC form) to epoch seconds, in pure
  # bash (Howard Hinnant's days_from_civil), so no date dialect is assumed.
  local iso="$1"
  [[ "$iso" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2}) ]] || return 1
  local y=${BASH_REMATCH[1]} m=${BASH_REMATCH[2]} d=${BASH_REMATCH[3]}
  local hh=${BASH_REMATCH[4]} mi=${BASH_REMATCH[5]} ss=${BASH_REMATCH[6]}
  # The $-expansions after the base prefixes are required: a bare variable
  # name after `10#` is parsed as a literal, and zero-prefixed months,
  # days, and seconds would otherwise trip octal arithmetic.
  local yy=$y mm=$((10#$m))
  if (( mm <= 2 )); then
    yy=$((yy - 1))
    mm=$((mm + 12))
  fi
  local era=$((yy / 400))
  local yoe=$((yy - era * 400))
  local doy=$(((153 * (mm - 3) + 2) / 5 + 10#$d - 1))
  local doe=$((yoe * 365 + yoe / 4 - yoe / 100 + doy))
  local days=$((era * 146097 + doe - 719468))
  printf '%s\n' $((days * 86400 + 10#$hh * 3600 + 10#$mi * 60 + 10#$ss))
}

claim_field() {
  # First `key: value` frontmatter value of the claim file, empty when the
  # line is absent. The key is a caller literal (session, plan, created,
  # updated, base, branch, start-commit).
  sed -n "s/^$2: //p" "$1" 2>/dev/null | head -n 1
}

claim_session() {
  # The claim's session value; returns nonzero when the record carries no
  # session line. The caller dies in the parent shell (never inside a
  # command substitution), so the run's final OUTCOME line still prints.
  local value
  value="$(claim_field "$1" session)"
  [[ -n "$value" ]] || return 1
  printf '%s\n' "$value"
}

resolve_anchor() {
  git rev-parse --show-toplevel 2>/dev/null
}

resolve_primary() {
  # The first `worktree` entry of `git worktree list --porcelain`; a failed
  # or empty listing is the tool-error class at the caller.
  local line
  line="$(git -C "$1" worktree list --porcelain 2>/dev/null | grep -m1 '^worktree ' || true)"
  [[ -n "$line" ]] || return 1
  printf '%s\n' "${line#worktree }"
}

occupying_worktree() {
  # The worktree path holding the requested branch per the porcelain
  # listing, nonzero when none holds it.
  local anchor="$1" branch="$2" cur="" line
  [[ -n "$branch" ]] || return 1
  while IFS= read -r line; do
    case "$line" in
      "worktree "*) cur="${line#worktree }" ;;
      "branch refs/heads/"*)
        if [[ "${line#branch refs/heads/}" == "$branch" ]]; then
          printf '%s\n' "$cur"
          return 0
        fi
        ;;
    esac
  done < <(git -C "$anchor" worktree list --porcelain 2>/dev/null)
  return 1
}

norm_path() {
  # Physical form of an existing path (symlinked parents, the macOS
  # /private forms git stores in its worktree registry); echoes the input
  # unchanged when it cannot be resolved (an absent path has no physical
  # form to resolve).
  local resolved
  resolved="$(cd "$1" 2>/dev/null && pwd -P)" || { printf '%s\n' "$1"; return 0; }
  printf '%s\n' "$resolved"
}

path_is_registered_worktree() {
  # True when the porcelain listing already carries a `worktree <path>`
  # entry equal (physical-normalized on both sides) to the target path,
  # whatever that entry holds: a different-branch or detached occupant at
  # the take path is still an occupant of the path, and both pre-add
  # branch-scoped guards are blind to it.
  local target="$1" cur="" line target_norm entry_norm
  target_norm="$(norm_path "$target")"
  while IFS= read -r line; do
    case "$line" in
      "worktree "*)
        cur="${line#worktree }"
        entry_norm="$(norm_path "$cur")"
        if [[ "$entry_norm" == "$target_norm" ]]; then
          return 0
        fi
        ;;
    esac
  done < <(git -C "$ANCHOR" worktree list --porcelain 2>/dev/null)
  return 1
}

derive_slug() {
  # The canonical artifact slug through the python SOT flag. Prints the
  # slug on stdout on success only; on any failure it writes one sanitized
  # diagnostic to stderr and returns nonzero, so the caller dies in the
  # parent shell and the run's final OUTCOME line still prints. The capture
  # is stdout-only (child stderr dropped), so a stray stderr line can never
  # become the slug, and the diagnostic strips any embedded child
  # `OUTCOME:` lines, so a blob can never carry a counterfeit final line.
  local plan="$1" out blob slug
  if ! out="$("$PYTHON" "$SCRIPT_DIR/plan_readiness.py" --print-artifact-slug "$plan" 2>/dev/null)"; then
    blob="$(printf '%s\n' "$out" | grep -v '^OUTCOME:' || true)"
    printf 'error: artifact slug derivation failed for %s (child: %s)\n' "$plan" "$blob" >&2
    return 1
  fi
  slug="$(printf '%s\n' "$out" | head -n 1)"
  if [[ -z "$slug" ]] || [[ "$(printf '%s\n' "$out" | tail -n 1)" != "OUTCOME: pass" ]]; then
    blob="$(printf '%s\n' "$out" | grep -v '^OUTCOME:' || true)"
    printf 'error: artifact slug derivation answered outside its vocabulary for %s (child: %s)\n' "$plan" "$blob" >&2
    return 1
  fi
  printf '%s\n' "$slug"
}

create_claim_noclobber() {
  # The create-if-absent noclobber write: four frontmatter lines at
  # creation, plus the branch and start-commit lines this invocation holds
  # (the takeover and recreate rebuild paths carry the recorded identity,
  # never silently dropping it); refuses (nonzero) when the file already
  # exists, leaving it untouched.
  local path="$1" session="$2" plan="$3" stamp
  stamp="$(iso_now)"
  (
    set -o noclobber
    {
      printf 'session: %s\nplan: %s\ncreated: %s\nupdated: %s\n' \
        "$session" "$plan" "$stamp" "$stamp"
      if [[ -n "$BRANCH" ]]; then
        printf 'branch: %s\n' "$BRANCH"
      fi
      if [[ -n "$START_COMMIT" ]]; then
        printf 'start-commit: %s\n' "$START_COMMIT"
      fi
    } >"$path"
  ) 2>/dev/null
}

write_claim_stamped() {
  # Atomic rewrite (temp plus rename): session, plan, created, updated,
  # the branch and start-commit lines when non-empty, and the base line
  # only when non-empty.
  local path="$1" session="$2" plan="$3" created="$4" updated="$5" base="$6" \
    branch="$7" start_commit="$8" tmp
  tmp="$(mktemp "${path}.rewrite.XXXXXX")"
  {
    printf 'session: %s\nplan: %s\ncreated: %s\nupdated: %s\n' \
      "$session" "$plan" "$created" "$updated"
    if [[ -n "$branch" ]]; then
      printf 'branch: %s\n' "$branch"
    fi
    if [[ -n "$start_commit" ]]; then
      printf 'start-commit: %s\n' "$start_commit"
    fi
    if [[ -n "$base" ]]; then
      printf 'base: %s\n' "$base"
    fi
  } >"$tmp"
  # Arm-4 last-instant compare-and-delete on the stamped rewrite: when the
  # target already exists, its session is re-verified as the move's
  # immediately-preceding operation; a foreign session there is a lost race
  # (the racing holder keeps its claim) and this write refuses.
  if [[ -e "$path" ]]; then
    local cur_holder
    cur_holder="$(claim_field "$path" session 2>/dev/null || true)"
    if [[ -n "$cur_holder" && "$cur_holder" != "$session" ]]; then
      rm -f "$tmp"
      return 1  # lost race: the racing holder is $cur_holder
    fi
  fi
  mv -f "$tmp" "$path"
}

restamp_claim() {
  # Re-stamp updated (refresh semantics); keeps session, plan, and created;
  # replaces the base line when a base argument is passed, keeps the
  # existing one otherwise; the branch and start-commit lines follow the
  # same rule (replaced when an argument is passed, kept otherwise).
  local path="$1" base="${2:-}" branch="${3:-}" start_commit="${4:-}"
  local session plan created existing_base existing_branch existing_start_commit
  session="$(claim_field "$path" session)"
  plan="$(claim_field "$path" plan)"
  created="$(claim_field "$path" created)"
  existing_base="$(claim_field "$path" base)"
  existing_branch="$(claim_field "$path" branch)"
  existing_start_commit="$(claim_field "$path" start-commit)"
  if [[ -n "$base" ]]; then
    existing_base="$base"
  fi
  if [[ -n "$branch" ]]; then
    existing_branch="$branch"
  fi
  if [[ -n "$start_commit" ]]; then
    existing_start_commit="$start_commit"
  fi
  if ! write_claim_stamped "$path" "$session" "$plan" "${created:-$(iso_now)}" \
      "$(iso_now)" "$existing_base" "$existing_branch" "$existing_start_commit"; then
    refuse "refresh refused: claim $path changed under this restamp (racing holder: $(claim_field "$path" session 2>/dev/null || echo unattributed))"
    refuse "  the stamped write lost its compare-and-delete; the claim is left untouched"
    die_fail
  fi
}

refuse_fresh_foreign_claim() {
  # The shared fresh-foreign refusal: the holder session, the claim age,
  # the occupying worktree when derivable, and the override route.
  local holder="$1" updated_raw updated_epoch now_epoch age occupant
  updated_raw="$(claim_field "$CLAIM_PATH" updated)"
  [[ -n "$updated_raw" ]] || die_tool "claim $CLAIM_PATH carries no updated: line; freshness cannot be decided"
  updated_epoch="$(iso_to_epoch "$updated_raw")" || die_tool "claim $CLAIM_PATH carries an unparseable updated: value '$updated_raw'"
  now_epoch="$(date -u +%s)"
  age=$((now_epoch - updated_epoch))
  if (( age >= FRESHNESS_SECS )); then
    # Stale foreign claims do not refuse; callers run the takeover instead.
    return 1
  fi
  refuse "claim refused: a fresh foreign claim holds this plan"
  refuse "  claim: $CLAIM_PATH"
  refuse "  holder session: $holder"
  refuse "  claim age: ${age}s (updated: $updated_raw)"
  occupant="$(occupying_worktree "$ANCHOR" "$BRANCH" || true)"
  if [[ -n "$occupant" ]]; then
    refuse "  occupying worktree: $occupant"
  elif [[ -n "$BRANCH" ]]; then
    refuse "  occupying worktree: none derivable for branch $BRANCH"
  else
    refuse "  occupying worktree: none derivable (no branch requested)"
  fi
  refuse "  override: interactive user-directed proceed only (agents/skills/maintenance/SKILL.md); name this refusal in the decision reason"
  die_fail
}

# --- Dead-run conversion: lock roots, facts resolution, discovery ---------- #

os_account_home() {
  # The OS account record's home directory, the lock roots' derivation
  # source (the plan Terms: the gateway derives both lock roots from the OS
  # account record and clears caller HOME and lock variables, so a poisoned
  # caller environment cannot select the root). The trusted lock-root
  # resolver seam: EXECUTION_CLAIM_LOCK_HOME overrides the resolved home for
  # the test harness only — the same same-account trust class as the
  # session channel (it is not an authentication boundary); production
  # callers never set it, and it sits outside the cleared HOME/DONE_LOCK_*/
  # MERGE_LOCK_* namespaces.
  if [[ -n "${EXECUTION_CLAIM_LOCK_HOME:-}" ]]; then
    printf '%s\n' "$EXECUTION_CLAIM_LOCK_HOME"
    return 0
  fi
  "$PYTHON" -c 'import os, pwd; print(pwd.getpwuid(os.getuid()).pw_dir)'
}

facts_tmp_dir_for() {
  # The worktree's facts-resolved tmp_dir (the Run manifest term: resolve
  # {tmp_dir} from the facts document in the specific registered worktree
  # being inspected; missing or unreadable facts refuse discovery; never
  # substitute docs/tmp). Prints the directory with any trailing slash
  # stripped; a relative value resolves against the worktree root. Returns
  # 1 when discovery is refused.
  local wt="$1" facts value
  facts="$wt/.ai-playbook/facts.md"
  [[ -r "$facts" ]] || return 1
  value="$(sed -n -E "s/^[[:space:]]*tmp_dir[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"].*/\1/p" "$facts" 2>/dev/null | head -n 1)" || return 1
  [[ -n "$value" ]] || return 1
  value="${value%/}"
  if [[ "$value" == /* ]]; then
    :
  else
    value="$wt/$value"
  fi
  printf '%s\n' "$value"
}

manifest_path_for() {
  # The canonical run-manifest path for a worktree and plan slug; returns 1
  # when the worktree's facts refuse discovery.
  local wt="$1" slug="$2" tmp_dir
  tmp_dir="$(facts_tmp_dir_for "$wt")" || return 1
  printf '%s\n' "$tmp_dir/execute-plan/$slug/manifest.md"
}

scan_registered_manifest() {
  # The stale-preservation discovery (the Manifest identity term: stale
  # take and sweep preserve a claim whenever either supported manifest form
  # remains at its exact registered-worktree path; multiple matches or
  # missing facts refuse unchanged). Emits one tab-separated verdict line:
  #   found<tab><manifest-path><tab><worktree-path>  exactly one registered
  #                  worktree carries a non-symlink manifest file at the
  #                  exact facts-resolved path (form recognition is the
  #                  classification helper's job; this scan's preservation
  #                  predicate is file presence)
  #   multiple      two or more registered worktrees carry one (ambiguous)
  #   none          no manifest file exists at any resolvable path
  #   inconclusive  a manifest path holds a symlink (never followed)
  # A worktree whose facts refuse discovery makes the scan inconclusive
  # (the Terms: missing facts refuse unchanged — the claim is preserved,
  # never taken over or swept, because a manifest could hide behind the
  # unreadable facts). No default-path fallback exists.
  local slug="$1" line cur manifest count=0 found_mf="" found_wt=""
  while IFS= read -r line; do
    cur="${line#worktree }"
    if manifest="$(manifest_path_for "$cur" "$slug")"; then
      if [[ -L "$manifest" ]]; then
        printf 'inconclusive\n'
        return 0
      fi
      if [[ -f "$manifest" ]]; then
        count=$((count + 1))
        found_mf="$manifest"
        found_wt="$cur"
        if (( count > 1 )); then
          printf 'multiple\n'
          return 0
        fi
      fi
    else
      printf 'inconclusive\n'
      return 0
    fi
  done < <(git -C "$ANCHOR" worktree list --porcelain 2>/dev/null | grep '^worktree ')
  if (( count == 1 )); then
    printf 'found\t%s\t%s\n' "$found_mf" "$found_wt"
  else
    printf 'none\n'
  fi
  return 0
}

worktree_registered_branch() {
  # The attached branch of the registered worktree at the given path
  # (physical-normalized comparison against the porcelain entries); empty
  # output when the path is not a registered worktree or is detached. The
  # verdict resolves per entry: the branch/detached lines follow their own
  # worktree line, so the match prints and returns immediately.
  local target="$1" cur="" line target_norm entry_norm=""
  target_norm="$(norm_path "$target")"
  while IFS= read -r line; do
    case "$line" in
      "worktree "*)
        cur="${line#worktree }"
        entry_norm="$(norm_path "$cur")"
        ;;
      "branch refs/heads/"*)
        if [[ "$entry_norm" == "$target_norm" ]]; then
          printf '%s\n' "${line#branch refs/heads/}"
          return 0
        fi
        ;;
      "detached")
        if [[ "$entry_norm" == "$target_norm" ]]; then
          return 0
        fi
        ;;
    esac
  done < <(git -C "$ANCHOR" worktree list --porcelain 2>/dev/null)
  return 0
}

# --- Dead-run claim conversion: manifest identity classification (pure) ---
# resume_manifest_identity MANIFEST CLAIM PLAN_OPERAND
# Emits one classification line on stdout and returns 0 when the manifest's
# owner and plan match the claim's owner and the exact plan operand per the
# plan Terms' three supported identity forms:
#   canonical: manifest session_id: + exact plan_path:
#   legacy-full: manifest Session: + Plan:
#   legacy-session: manifest session_id: alone, claim supplies exact plan:
# Returns 1 (named reason on stderr) on unreadable manifest, symlinked
# manifest, unrecognized form, or owner/plan mismatch. Never mutates either
# file; a symlinked manifest is a refusal, never followed.
resume_manifest_identity() {
  local manifest="$1" claim="$2" plan_operand="$3"
  if [[ -L "$manifest" ]]; then
    echo "resume-evidence: manifest is a symlink: $manifest" >&2
    return 1
  fi
  if [[ ! -r "$manifest" ]]; then
    echo "resume-evidence: manifest unreadable: $manifest" >&2
    return 1
  fi
  local claim_owner claim_plan
  claim_owner="$(claim_field "$claim" session)" || return 1
  claim_plan="$(claim_field "$claim" plan)" || return 1
  local parsed
  parsed="$(MANIFEST="$manifest" python3 - <<'PYPARSE'
import os, re, sys
path = os.environ["MANIFEST"]
text = open(path, encoding="utf-8", errors="replace").read()
def field(name):
    m = re.search(rf"^{name}:(.*)$", text, re.M)
    return m.group(1).strip() if m else None
sid, plan_path = field("session_id"), field("plan_path")
legacy_session, legacy_plan = field("Session"), field("Plan")
run_worktree, run_branch = field("run_worktree"), field("run_branch")
if sid and plan_path:
    form, owner, plan = "canonical", sid, plan_path
elif legacy_session and legacy_plan:
    form, owner, plan = "legacy-full", legacy_session, legacy_plan
elif sid:
    form, owner, plan = "legacy-session", sid, None
else:
    sys.exit(1)
print(f"{form}\t{owner}\t{plan or ''}\t{run_worktree or ''}\t{run_branch or ''}")
PYPARSE
)" || {
    echo "resume-evidence: manifest identity unrecognized: $manifest" >&2
    return 1
  }
  local form owner plan run_worktree run_branch
  IFS=$'\t' read -r form owner plan run_worktree run_branch <<<"$parsed"
  [[ -z "$plan" ]] && plan="$claim_plan"
  if [[ "$owner" != "$claim_owner" ]]; then
    echo "resume-evidence: manifest owner $owner != claim owner $claim_owner" >&2
    return 1
  fi
  if [[ "$plan" != "$plan_operand" ]]; then
    echo "resume-evidence: manifest plan $plan != operand $plan_operand" >&2
    return 1
  fi
  echo "identity=$form owner=$owner plan=$plan run_worktree=${run_worktree:--} run_branch=${run_branch:--}"
  return 0
}

takeover_stale_claim() {
  # Re-read the claim immediately before the unlink and unlink it only
  # while it still names the same foreign session with a stale updated
  # line; record the takeover; create this session's claim. Returns 1 when
  # the claim changed under us (the caller re-evaluates).
  local holder="$1" re_holder re_updated re_epoch
  re_holder="$(claim_field "$CLAIM_PATH" session)"
  re_updated="$(claim_field "$CLAIM_PATH" updated)"
  if [[ "$re_holder" != "$holder" ]] || [[ -z "$re_updated" ]]; then
    return 1
  fi
  re_epoch="$(iso_to_epoch "$re_updated")" || return 1
  if (( $(date -u +%s) - re_epoch < FRESHNESS_SECS )); then
    return 1
  fi
  evidence "takeover: replaced stale claim of session $holder"
  # Arm-4 last-instant compare-and-delete (plan
  # 2026-10-10-coordination-single-writer-ttl, Task 2): the session check is
  # the unlink's immediately-preceding operation, never a second lock.
  if ! grep -q "^session: ${holder}\$" "$CLAIM_PATH" 2>/dev/null || ! rm -f "$CLAIM_PATH"; then
    return 1  # lost race: the claim changed under us; the caller re-evaluates
  fi
  # The flag leads the create (the same window-closing discipline as
  # acquire_claim): a signal between create and flag could otherwise strand
  # the fresh claim past the exit-path cleanup.
  CREATED_HERE=1
  if ! create_claim_noclobber "$CLAIM_PATH" "$SESSION" "$PLAN_ARG"; then
    CREATED_HERE=0  # a concurrent writer won the create; its claim is not ours
    return 1
  fi
  return 0
}

# --- Dead-run conversion: gateway-owned locks ------------------------------ #

GATEWAY_DONE_LOCK_DIR=""
GATEWAY_DONE_LOCK_TOKEN=""
GATEWAY_MERGE_LOCK_DIR=""
GATEWAY_MERGE_LOCK_TOKEN=""
GATEWAY_TMP=""

gateway_lock_env_prefix() {
  # The env prefix for every lock-helper invocation: the roots derive from
  # the OS account record (or the trusted harness seam) and the caller's
  # HOME and lock variables are cleared, so a poisoned caller environment
  # can neither select the root nor appear as a verified hold. The
  # holder-pin variables mark the hold as deliberately pinned to the live
  # gateway PID (never a command-substitution parent: the helper is invoked
  # directly from the gateway shell, with output redirected to files).
  local root
  root="$(os_account_home)" || return 1
  [[ -n "$root" ]] || return 1
  GATEWAY_LOCK_ENV=(
    env -u HOME -u DONE_LOCK_DIR -u DONE_LOCK_TOKEN -u MERGE_LOCK_DIR
    -u MERGE_LOCK_TOKEN -u DONE_LOCK_ROOT -u MERGE_LOCK_ROOT
    -u DONE_LOCK_HOLDER_PID -u MERGE_LOCK_HOLDER_PID
    -u DONE_LOCK_HOLD_PIN -u MERGE_LOCK_HOLD_PIN
    "DONE_LOCK_ROOT=$root/.ai-playbook/locks/done"
    "MERGE_LOCK_ROOT=$root/.ai-playbook/locks/merge"
    "DONE_LOCK_HOLDER_PID=$$" "DONE_LOCK_HOLD_PIN=1"
    "MERGE_LOCK_HOLDER_PID=$$" "MERGE_LOCK_HOLD_PIN=1"
  )
  return 0
}

gateway_lock_helper() {
  # The lock helper invocation form: bash done-lock.sh, executed directly
  # (never inside a command substitution), stdout to $1, stderr to $2, with
  # the gateway's lock env prefix. The caller supplies the working
  # directory (the per-worktree done lock keys on the cwd's toplevel).
  local out="$1" errfile="$2"; shift 2
  "${GATEWAY_LOCK_ENV[@]}" bash "$SCRIPT_DIR/done-lock.sh" "$@" >"$out" 2>"$errfile"
}

gateway_parse_exports() {
  # Parse one acquire output file for the helper's two export lines and
  # set the GATEWAY_-prefixed variables from the helper's eval-safe %q
  # form. $2 selects the pair: "done" (DONE_LOCK_DIR/TOKEN) or "merge"
  # (MERGE_LOCK_DIR/TOKEN). Returns 1 on any missing line.
  local file="$1" kind="$2" dir_var tok_var line
  if [[ "$kind" == "done" ]]; then
    dir_var=DONE_LOCK_DIR; tok_var=DONE_LOCK_TOKEN
  else
    dir_var=MERGE_LOCK_DIR; tok_var=MERGE_LOCK_TOKEN
  fi
  local dir_line tok_line
  dir_line="$(grep -m1 "^export ${dir_var}=" "$file" 2>/dev/null)" || return 1
  tok_line="$(grep -m1 "^export ${tok_var}=" "$file" 2>/dev/null)" || return 1
  eval "GATEWAY_${dir_var}=${dir_line#export ${dir_var}=}"
  eval "GATEWAY_${tok_var}=${tok_line#export ${tok_var}=}"
  return 0
}

gateway_meta_field() {
  sed -n "s/^$2=//p" "$1/meta.env" 2>/dev/null | head -n 1
}

gateway_verify_done_lock_meta() {
  # Verify the acquired done-lock records: our pinned holder PID, our
  # token, and the target worktree as the repo root (the Terms: verify both
  # tokens and paths before provider invocation). Any mismatch is a
  # refuse-with-release, never a proceed.
  local wt="$1" holder token repo_root
  [[ -r "$GATEWAY_DONE_LOCK_DIR/meta.env" ]] || { refuse "gateway lock: done-lock meta unreadable: $GATEWAY_DONE_LOCK_DIR/meta.env"; return 1; }
  holder="$(gateway_meta_field "$GATEWAY_DONE_LOCK_DIR" holder_pid)"
  token="$(gateway_meta_field "$GATEWAY_DONE_LOCK_DIR" lock_token)"
  repo_root="$(gateway_meta_field "$GATEWAY_DONE_LOCK_DIR" repo_root)"
  if [[ "$holder" != "$$" ]]; then
    refuse "gateway lock: done-lock holder_pid record is $holder, want the gateway pid $$"
    return 1
  fi
  if [[ "$token" != "$GATEWAY_DONE_LOCK_TOKEN" ]]; then
    refuse "gateway lock: done-lock token record does not match the acquired token"
    return 1
  fi
  if [[ -n "$repo_root" && "$(norm_path "$repo_root")" != "$(norm_path "$(git -C "$wt" rev-parse --show-toplevel 2>/dev/null)")" ]]; then
    refuse "gateway lock: done-lock repo_root record is $repo_root, want the target worktree $wt"
    return 1
  fi
  return 0
}

gateway_release_all() {
  # Release every owned lock in reverse acquisition order (merge, then
  # done); release runs directly from the gateway shell with the acquired
  # exports re-exported, never through a command substitution. A failed
  # release is retried once; a still-stranded hold is named loudly (a
  # stranded hold blocks the next conversion's merge-acquire, which is the
  # designed visibility).
  local rc=0
  if [[ -n "$GATEWAY_MERGE_LOCK_DIR" ]]; then
    local mdir="$GATEWAY_MERGE_LOCK_DIR" mtok="$GATEWAY_MERGE_LOCK_TOKEN"
    GATEWAY_MERGE_LOCK_DIR=""
    GATEWAY_MERGE_LOCK_TOKEN=""
    if ! "${GATEWAY_LOCK_ENV[@]}" MERGE_LOCK_DIR="$mdir" MERGE_LOCK_TOKEN="$mtok" \
        bash "$SCRIPT_DIR/done-lock.sh" merge-release >/dev/null 2>&1; then
      if ! "${GATEWAY_LOCK_ENV[@]}" MERGE_LOCK_DIR="$mdir" MERGE_LOCK_TOKEN="$mtok" \
          bash "$SCRIPT_DIR/done-lock.sh" merge-release >/dev/null 2>&1; then
        refuse "gateway lock: MERGE_LOCK_DIR=$mdir release failed twice; stranded hold label execution-claim-conversion"
        rc=1
      fi
    fi
  fi
  if [[ -n "$GATEWAY_DONE_LOCK_DIR" ]]; then
    local ddir="$GATEWAY_DONE_LOCK_DIR" dtok="$GATEWAY_DONE_LOCK_TOKEN"
    GATEWAY_DONE_LOCK_DIR=""
    GATEWAY_DONE_LOCK_TOKEN=""
    if ! "${GATEWAY_LOCK_ENV[@]}" DONE_LOCK_DIR="$ddir" DONE_LOCK_TOKEN="$dtok" \
        bash "$SCRIPT_DIR/done-lock.sh" release >/dev/null 2>&1; then
      if ! "${GATEWAY_LOCK_ENV[@]}" DONE_LOCK_DIR="$ddir" DONE_LOCK_TOKEN="$dtok" \
          bash "$SCRIPT_DIR/done-lock.sh" release >/dev/null 2>&1; then
        refuse "gateway lock: DONE_LOCK_DIR=$ddir release failed twice; stranded hold label execution-claim-conversion"
        rc=1
      fi
    fi
  fi
  return "$rc"
}

gateway_cleanup_trap() {
  # The exit-path arm for gateway-owned lock state: every handled exit
  # releases through gateway_release_all; abrupt death leaves the locks for
  # the verified-dead-holder recovery. A signal landing between an acquire
  # and its export parse is covered by the recovery arm below: the acquire
  # output files in the scratch dir carry the exports, so the trap adopts
  # them and releases the just-acquired holds (the handled-interruption
  # contract: only the gateway's own tokens are ever released).
  if [[ -n "$GATEWAY_TMP" && -d "$GATEWAY_TMP" ]]; then
    if [[ -z "$GATEWAY_DONE_LOCK_DIR" && -f "$GATEWAY_TMP/done-acquire.out" ]] \
        && grep -q '^export DONE_LOCK_DIR=' "$GATEWAY_TMP/done-acquire.out" 2>/dev/null \
        && grep -q '^export DONE_LOCK_TOKEN=' "$GATEWAY_TMP/done-acquire.out" 2>/dev/null; then
      gateway_parse_exports "$GATEWAY_TMP/done-acquire.out" done || true
    fi
    if [[ -z "$GATEWAY_MERGE_LOCK_DIR" && -f "$GATEWAY_TMP/merge-acquire.out" ]] \
        && grep -q '^export MERGE_LOCK_DIR=' "$GATEWAY_TMP/merge-acquire.out" 2>/dev/null \
        && grep -q '^export MERGE_LOCK_TOKEN=' "$GATEWAY_TMP/merge-acquire.out" 2>/dev/null; then
      gateway_parse_exports "$GATEWAY_TMP/merge-acquire.out" merge || true
    fi
    local tmp_claim="$CLAIM_PATH.conversion.$$"
    [[ -e "$tmp_claim" ]] && rm -f "$tmp_claim"
  fi
  if [[ -n "$GATEWAY_DONE_LOCK_DIR" || -n "$GATEWAY_MERGE_LOCK_DIR" ]]; then
    gateway_release_all || true
  fi
  if [[ -n "$GATEWAY_TMP" && -d "$GATEWAY_TMP" ]]; then
    rm -rf "$GATEWAY_TMP"
  fi
}

merge_lock_hold_or_reuse() {
  # The five-command merge-lock discipline (the plan Task 1 box: all five
  # claim commands acquire the repository merge-lock before claim access,
  # pinned to the command PID; reuse only this session's verified token,
  # else try once and refuse with the holder). When this invocation already
  # holds a verified merge lock (the conversion arm acquired it after its
  # done-lock), the hold is reused; otherwise one merge-acquire runs, a
  # refusal names the holder and refuses (OUTCOME: fail) with nothing
  # mutated. Release runs through gateway_release_all on every path (the
  # exit trap is the backstop); the caller releases when its claim access
  # ends. Requires gateway_lock_env_prefix to have run.
  if [[ -n "$GATEWAY_MERGE_LOCK_DIR" ]]; then
    local holder token
    holder="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" holder_pid)"
    token="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" lock_token)"
    if [[ "$holder" == "$$" && "$token" == "$GATEWAY_MERGE_LOCK_TOKEN" ]]; then
      return 0
    fi
    refuse "gateway lock: the recorded merge-lock hold does not verify as this command's; refusing"
    return 1
  fi
  local out="$GATEWAY_TMP/merge-acquire.out" err="$GATEWAY_TMP/merge-acquire.err"
  if ! gateway_lock_helper "$out" "$err" merge-acquire --label "execution-claim pid=$$"; then
    refuse "claim access refused: the repository merge-lock is held (one-shot contention refusal)"
    sed 's/^/  /' "$err" >&2 2>/dev/null || true
    return 1
  fi
  if ! gateway_parse_exports "$out" merge; then
    refuse "gateway lock: merge-lock acquire output unparseable at $out"
    return 1
  fi
  local holder token
  holder="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" holder_pid)"
  token="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" lock_token)"
  if [[ "$holder" != "$$" || "$token" != "$GATEWAY_MERGE_LOCK_TOKEN" ]]; then
    refuse "gateway lock: the acquired merge-lock records do not verify (holder $holder, want $$)"
    return 1
  fi
  return 0
}

verify_completed_run_boundary() {
  # The completed-run boundary over the stable evidence tuple (the plan
  # Terms), with the bounded legacy binding applied to pre-tuple artifacts.
  # Refuses (returns 1, findings on stderr) on any missing, duplicate,
  # incomplete, conflicting, unreferenced, or ambiguous evidence; never
  # rewrites any byte.
  #   $1 manifest path   $2 run worktree   $3 primary checkout
  #   $4 prior owner     $5 plan slug      $6 run tmp dir
  #   $7 plan operand path
  local manifest="$1" wt="$2" primary="$3" prior_owner="$4" slug="$5" \
    tmp_dir="$6" plan_operand="$7"
  local run_dir="$tmp_dir/execute-plan/$slug"
  [[ -d "$run_dir" ]] || {
    refuse "boundary: run directory missing: $run_dir"; return 1; }
  local state="$run_dir/runtime_state.json"
  [[ -f "$state" && ! -L "$state" ]] || {
    refuse "boundary: runtime state missing or symlinked: $state"; return 1; }
  manifest_run_session_id="$(sed -n 's/^run_session_id:[[:space:]]*//p' "$manifest" | head -n 1)"
  manifest_session_id="$(sed -n 's/^session_id:[[:space:]]*//p' "$manifest" | head -n 1)"
  MANIFEST_RUN_SESSION_ID="$manifest_run_session_id" MANIFEST_SESSION_ID="$manifest_session_id" \
  "$PYTHON" - "$state" "$slug" "$prior_owner" "$manifest" "$wt" "$primary" \
    "$plan_operand" "$tmp_dir" <<'PYBOUNDARY'
import hashlib, json, os, re, sys

state_path, slug, prior_owner, manifest_path, wt, primary, plan_operand, tmp_dir = sys.argv[1:9]
manifest_run_session_id = os.environ.get("MANIFEST_RUN_SESSION_ID") or None
manifest_session_id = os.environ.get("MANIFEST_SESSION_ID") or None

def refuse(msg):
    print(f"boundary: {msg}", file=sys.stderr)
    sys.exit(1)

try:
    with open(state_path, encoding="utf-8") as fh:
        state = json.load(fh)
except (OSError, ValueError) as exc:
    refuse(f"runtime state unparseable: {exc}")
if not isinstance(state, dict):
    refuse("runtime state is not a JSON object")
if state.get("plan_slug") != slug:
    refuse(f"runtime state plan_slug {state.get('plan_slug')!r} != slug {slug!r}")
if state.get("workflow_state") != "terminal":
    refuse(f"runtime state workflow_state {state.get('workflow_state')!r} is not terminal")
tasks = state.get("tasks")
if not isinstance(tasks, dict) or not tasks:
    refuse("runtime state carries no completed task map")
sanctioned = ("complete", "checkpointed", "deferred")
bad = {k: v for k, v in tasks.items()
       if not (isinstance(v, str) and v in sanctioned)}
if bad:
    refuse(f"tasks not in a sanctioned terminal state {list(sanctioned)}: {sorted(bad)}")
receipt = state.get("pre_archive_receipt")
if not isinstance(receipt, dict):
    refuse("pre_archive_receipt missing or not an object")
declared = receipt.get("declared_paths")
if not isinstance(declared, list) or not declared or \
        not all(isinstance(p, str) and p for p in declared):
    refuse("receipt declared_paths must be a non-empty list of paths")
digest = receipt.get("plan_digest")
if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
    refuse("receipt plan_digest must be a 64-hex sha256")
evidence = receipt.get("evidence")
if not isinstance(evidence, list) or not evidence or \
        not all(isinstance(p, str) and p for p in evidence):
    refuse("receipt evidence must be a non-empty list of record paths")
if not isinstance(receipt.get("recorded_at"), str) or not receipt["recorded_at"]:
    refuse("receipt recorded_at must be present")

# Stable tuple: run_session_id is the IMMUTABLE origin identity — it binds
# the run's artifacts to each other and carries through conversions
# unchanged (an R-to-S conversion legitimately differs from the current
# prior owner); the mutable session_id binds the owner and is verified by
# the identity classification. The split-owner shape (an origin equal to
# the mutable owner yet different from the verified prior owner) is
# unverifiable from here and fails closed.
for t in (manifest_run_session_id, state.get("run_session_id")):
    if isinstance(t, str) and t and manifest_session_id and t == manifest_session_id and t != prior_owner:
        refuse(f"stable tuple origin {t!r} equals the mutable owner but not the prior owner {prior_owner!r}")

def readable(path):
    for base in (wt, primary, None):
        if base is None:
            if not os.path.isabs(path):
                continue
            candidate = path
        else:
            candidate = os.path.join(base, path)
        if os.path.isfile(candidate) and not os.path.islink(candidate):
            return candidate
    return None

# Plan digest: the active plan bytes before the move; when the plan file
# has moved (archived), the receipt's archived copy carries the same bytes.
actual = None
for source in (plan_operand, receipt.get("archived_plan_path")):
    if isinstance(source, str) and source:
        found = readable(source)
        if found:
            with open(found, "rb") as fh:
                actual = hashlib.sha256(fh.read()).hexdigest()
            break
if actual is None:
    refuse("plan digest unverifiable: neither the plan operand nor the archived copy is readable")
if actual != digest:
    refuse(f"receipt plan_digest {digest} does not hash the active plan bytes ({actual})")

for record in evidence:
    if readable(record) is None:
        refuse(f"evidence record not found: {record}")

# One parent-owned boundary record per completed task, and each task's
# implement log at its unique contract path.
try:
    with open(manifest_path, encoding="utf-8", errors="replace") as fh:
        manifest_text = fh.read()
except OSError as exc:
    refuse(f"manifest unreadable during boundary check: {exc}")
boundary_rows = len(re.findall(r"^task_boundary:", manifest_text, re.M))
if boundary_rows < len(tasks):
    refuse(f"manifest carries {boundary_rows} task_boundary rows, want at least {len(tasks)}")
task_tokens = re.findall(r"^task_boundary:.*?[Tt]ask[=_ ](\w+)", manifest_text, re.M)
for task_id in tasks:
    if task_tokens.count(task_id) != 1:
        refuse(f"task {task_id} has {task_tokens.count(task_id)} boundary rows naming it, want exactly one parent-owned record")
for task_id in tasks:
    rel = f"execute-plan/{slug}/task-{task_id}-implement.log.md"
    if readable(os.path.join(tmp_dir, rel)) is None:
        refuse(f"task {task_id} implement log missing at its contract path: {rel}")

# Phase 3 exit binding: the run's exit report (terminal_receipt) or a
# recorded residual policy must exist — a terminal-shaped runtime state
# without either never passed the review boundary.
terminal_receipt = state.get("terminal_receipt")
residual = re.search(r"^residual_policy:[^\s]", manifest_text, re.M)
if not (isinstance(terminal_receipt, dict) and terminal_receipt) and not residual:
    refuse("no Phase 3 exit binding: runtime state carries no terminal_receipt and the manifest records no residual_policy")
PYBOUNDARY
}

try_dead_run_conversion() {
  # The dead-run claim conversion arm (plan 2026-10-21-dead-run-resume-
  # claim-conversion): take mode only, invoked from acquire_claim when a
  # foreign claim exists. Verdicts:
  #   0 and CONVERSION_DONE=1  converted: the claim was atomically replaced
  #                            and the manifest canonicalized under both
  #                            gateway-owned locks; the caller reports
  #                            success and returns before the occupant gate
  #                            and the worktree add
  #   2                        no conversion context (no registered target
  #                            at the take path, or no manifest at its
  #                            facts-resolved path): the caller falls
  #                            through to the historical fresh-refusal /
  #                            takeover flow
  #   3                        the claim changed under the locks; the
  #                            caller re-evaluates from the loop top
  #   1 (via die_fail)         refused: the evidence lines name the reason;
  #                            the claim and manifest bytes are untouched
  #                            and every owned lock is released
  local holder="$1" wt manifest rc
  CONVERSION_DONE=0
  [[ -n "$BRANCH" && -n "$WT_PARENT" && -n "$SLUG" ]] || return 2
  wt="$WT_PARENT/$BRANCH"

  # The preservation scan runs BEFORE any fall-through: a surviving
  # manifest anywhere in the registered worktrees protects the claim, so a
  # take whose target is not the manifest's worktree (branch switched,
  # unregistered target path) refuses with the claim preserved instead of
  # reaching the historical unlink takeover. Only a scan that resolves
  # every registered worktree and finds no manifest returns no-context —
  # and a found manifest at the take path is itself the registration
  # witness (the scan walks registered worktrees only).
  local scan verdict scan_mf scan_wt
  scan="$(scan_registered_manifest "$SLUG")"
  verdict="${scan%%$'\t'*}"
  case "$verdict" in
    multiple)
      refuse "conversion refused: run manifests for slug $SLUG exist in more than one registered worktree (ambiguous)"
      refuse "  ambiguity preserves the claim for operator reconciliation"
      die_fail
      ;;
    inconclusive)
      refuse "conversion refused: the registered-manifest scan is inconclusive (facts refuse discovery, or a symlinked manifest path)"
      refuse "  the claim is preserved for operator reconciliation"
      die_fail
      ;;
    found)
      IFS=$'\t' read -r verdict scan_mf scan_wt <<<"$scan"
      if [[ "$(norm_path "$scan_wt")" != "$(norm_path "$wt")" ]]; then
        refuse "conversion refused: the run manifest is registered to another worktree: $scan_wt"
        refuse "  conversion runs only through a take of the exact registered run worktree; the claim is preserved"
        die_fail
      fi
      manifest="$scan_mf"
      ;;
    none)
      return 2
      ;;
  esac

  # Trusted session channel: the active ID must equal --session exactly,
  # before any lock acquisition or mutation (empty or mismatched refuses).
  # It sits behind the scan gate: a take with no conversion context falls
  # through to the historical flow without consulting the channel.
  local active
  active="$("$PYTHON" "$SCRIPT_DIR/session_channel.py" 2>/dev/null || true)"
  if [[ -z "$active" || "$active" != "$SESSION" ]]; then
    refuse "conversion refused: the session channel's active id (${active:-empty}) does not equal --session $SESSION"
    refuse "  the trusted session channel boundary refuses before lock acquisition or mutation"
    die_fail
  fi

  # Attached exact registered target: a detached target refuses conversion
  # (a detached entry cannot hold the manifest's recorded branch).
  local registered_branch
  registered_branch="$(worktree_registered_branch "$wt")"
  if [[ -z "$registered_branch" ]]; then
    refuse "conversion refused: the registered target worktree is detached: $wt"
    refuse "  every detached target refuses conversion unchanged; the claim is preserved"
    die_fail
  fi

  if [[ -L "$manifest" ]]; then
    refuse "conversion refused: the run manifest is a symlink: $manifest"
    refuse "  symlinks are never followed; the claim and manifest are untouched"
    die_fail
  fi
  if [[ ! -r "$manifest" ]]; then
    refuse "conversion refused: the run manifest is unreadable: $manifest"
    die_fail
  fi

  # Identity classification: manifest owner/plan against the claim and the
  # exact plan operand (all three supported identity forms).
  local identity_line form m_owner m_run_wt m_run_branch
  if ! identity_line="$(resume_manifest_identity "$manifest" "$CLAIM_PATH" "$PLAN_ARG")"; then
    refuse "conversion refused: the manifest identity does not verify against the claim and operand"
    refuse "  mismatched or interrupted owner state refuses unchanged for operator reconciliation"
    die_fail
  fi
  form="$(sed -n 's/^identity=\([^ ]*\).*/\1/p' <<<"$identity_line")"
  m_run_wt="$(sed -n 's/.* run_worktree=\([^ ]*\).*/\1/p' <<<"$identity_line")"
  m_run_branch="$(sed -n 's/.* run_branch=\([^ ]*\).*/\1/p' <<<"$identity_line")"
  if [[ "$m_run_wt" != "-" && "$(norm_path "$m_run_wt")" != "$(norm_path "$wt")" ]]; then
    refuse "conversion refused: the manifest records run_worktree $m_run_wt, want the attached target $wt"
    die_fail
  fi
  if [[ "$m_run_branch" != "-" && "$m_run_branch" != "$registered_branch" ]]; then
    refuse "conversion refused: the manifest records run_branch $m_run_branch, want the target's branch $registered_branch"
    die_fail
  fi

  # Snapshot the claim bytes: the authoritative re-read under both locks
  # must match them byte-for-byte before the replacement. The scratch dir
  # and lock env come from the caller (acquire_claim created both).
  [[ -n "$GATEWAY_TMP" && -d "$GATEWAY_TMP" ]] || die_tool "conversion: gateway scratch directory missing"
  if ! cp "$CLAIM_PATH" "$GATEWAY_TMP/claim.before" 2>/dev/null; then
    die_tool "conversion: claim snapshot failed at $CLAIM_PATH"
  fi

  # Lock roots from the OS account record; caller lock variables cleared.
  if ! gateway_lock_env_prefix; then
    die_tool "conversion: lock roots unresolvable from the OS account record"
  fi

  # Target done-lock, with the orphaned-holder recovery arm first: a
  # verified-dead past-grace holder is released; live, ambiguous, unknown,
  # and too-young holders refuse the conversion unchanged. The status word
  # is the output's first line ("free" when free; the held shape is
  # "done-lock: held (...)" naming the holder).
  local status_out="$GATEWAY_TMP/status.out" status_err="$GATEWAY_TMP/status.err"
  if ( cd "$wt" && gateway_lock_helper "$status_out" "$status_err" status ) && \
      ! grep -q "^free$" "$status_out" 2>/dev/null; then
    if ! ( cd "$wt" && gateway_lock_helper "$status_out" "$status_err" release-orphaned ); then
      refuse "conversion refused: the target worktree holds a live or ambiguous done-lock that release-orphaned would not clear: $wt"
      sed 's/^/  /' "$status_err" >&2 2>/dev/null || true
        die_fail
    fi
  fi

  local acq_out="$GATEWAY_TMP/done-acquire.out" acq_err="$GATEWAY_TMP/done-acquire.err"
  if ! ( cd "$wt" && gateway_lock_helper "$acq_out" "$acq_err" acquire --label "execution-claim-conversion pid=$$" ); then
    refuse "conversion refused: the target worktree's done-lock is held (acquire refused)"
    sed 's/^/  /' "$acq_err" >&2 2>/dev/null || true
    die_fail
  fi
  if ! gateway_parse_exports "$acq_out" done; then
    sed 's/^/  acquire-stderr: /' "$acq_err" >&2 2>/dev/null || true
    gateway_release_all || true
    die_tool "conversion: done-lock acquire output unparseable at $acq_out"
  fi
  if ! gateway_verify_done_lock_meta "$wt"; then
    gateway_release_all || true
    die_fail
  fi

  # Repository merge-lock second (one-shot contention refusal naming the
  # holder); both locks hold through provider lookup, replacement, and
  # manifest refresh.
  local macq_out="$GATEWAY_TMP/merge-acquire.out" macq_err="$GATEWAY_TMP/merge-acquire.err"
  if ! gateway_lock_helper "$macq_out" "$macq_err" merge-acquire --label "execution-claim-conversion pid=$$"; then
    refuse "conversion refused: the repository merge-lock is held (one-shot contention refusal)"
    sed 's/^/  /' "$macq_err" >&2 2>/dev/null || true
    gateway_release_all || true
    die_fail
  fi
  if ! gateway_parse_exports "$macq_out" merge; then
    gateway_release_all || true
    die_tool "conversion: merge-lock acquire output unparseable at $macq_out"
  fi
  # The merge hold verifies like the done hold: our pinned PID and token,
  # the repository as the recorded root (the Terms: verify both tokens and
  # paths before provider invocation).
  local m_holder m_token
  m_holder="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" holder_pid)"
  m_token="$(gateway_meta_field "$GATEWAY_MERGE_LOCK_DIR" lock_token)"
  if [[ "$m_holder" != "$$" || "$m_token" != "$GATEWAY_MERGE_LOCK_TOKEN" ]]; then
    refuse "gateway lock: merge-lock records do not verify (holder ${m_holder:-none}, want $$)"
    gateway_release_all || true
    die_fail
  fi

  # Session status provider: only a terminal prior owner proceeds; the
  # provider's own contract (10s bound, stream caps, exact JSON) refuses
  # everything else unchanged.
  local prov_out="$GATEWAY_TMP/provider.out" prov_err="$GATEWAY_TMP/provider.err"
  if ! "$PYTHON" "$SCRIPT_DIR/session_status.py" "$PRIMARY/.ai-playbook/facts.md" "$holder" \
      >"$prov_out" 2>"$prov_err"; then
    refuse "conversion refused: the session status provider did not return prior owner $holder terminal"
    sed 's/^/  provider: /' "$prov_err" >&2 2>/dev/null || true
    gateway_release_all || true
    die_fail
  fi
  # Exit 0 names a matching live session in the closed vocabulary; only
  # the terminal status proceeds (live, paused, and unresolved refuse).
  # The JSON object is the output's first line (a final OUTCOME: line
  # follows per the outcome contract).
  local prov_status
  prov_status="$(head -n 1 "$prov_out" | "$PYTHON" -c 'import json, sys; print(json.load(sys.stdin).get("status", ""))' 2>/dev/null)" \
    || prov_status=""
  if [[ "$prov_status" != "terminal" ]]; then
    refuse "conversion refused: prior owner $holder is ${prov_status:-unresolved}, not terminal"
    gateway_release_all || true
    die_fail
  fi

  # Completed-run boundary over the stable evidence tuple.
  if ! verify_completed_run_boundary "$manifest" "$wt" "$PRIMARY" "$holder" "$SLUG" \
      "$(facts_tmp_dir_for "$wt")" "$PLAN_ARG"; then
    gateway_release_all || true
    die_fail
  fi

  # Authoritative re-read under both locks: owner or byte change refuses
  # (nothing was mutated; the caller re-evaluates).
  if ! cmp -s "$CLAIM_PATH" "$GATEWAY_TMP/claim.before"; then
    gateway_release_all || true
    refuse "conversion: the claim changed under the gateway locks"
    return 3
  fi
  if [[ "$(claim_field "$CLAIM_PATH" session)" != "$holder" ]]; then
    gateway_release_all || true
    refuse "conversion: the claim's owner changed under the gateway locks"
    return 3
  fi
  # The manifest is re-verified under both locks: a swap or rewrite between
  # the pre-lock checks and the canonicalization refuses (fail closed).
  if [[ -L "$manifest" || ! -r "$manifest" ]]; then
    gateway_release_all || true
    refuse "conversion: the run manifest changed identity under the gateway locks"
    return 3
  fi
  if ! resume_manifest_identity "$manifest" "$CLAIM_PATH" "$PLAN_ARG" >/dev/null; then
    gateway_release_all || true
    refuse "conversion: the manifest identity no longer verifies under the gateway locks"
    return 3
  fi

  # Replacement claim shape (the Terms): the resumer's session and the
  # exact operand, the prior created stamp, a fresh updated stamp, and the
  # prior branch/start-commit/base values; a recorded manifest conflict
  # with any of them refuses before the replacement; missing optional
  # fields are never synthesized.
  local prior_created prior_branch prior_base prior_start
  local m_start m_base_branch
  prior_created="$(claim_field "$CLAIM_PATH" created)"
  prior_branch="$(claim_field "$CLAIM_PATH" branch)"
  prior_base="$(claim_field "$CLAIM_PATH" base)"
  prior_start="$(claim_field "$CLAIM_PATH" start-commit)"
  m_start="$(sed -n 's/^session_start_commit:[[:space:]]*//p' "$manifest" | head -n 1)"
  m_base_branch="$(sed -n 's/^run_base:[[:space:]]*//p' "$manifest" | head -n 1 | sed 's/[[:space:]].*//')"
  if [[ -n "$prior_branch" && "$m_run_branch" != "-" && "$m_run_branch" != "$prior_branch" ]]; then
    gateway_release_all || true
    refuse "conversion refused: manifest run_branch $m_run_branch conflicts with the claim's branch $prior_branch"
    die_fail
  fi
  if [[ -n "$prior_start" && -n "$m_start" && "$m_start" != "$prior_start" ]]; then
    gateway_release_all || true
    refuse "conversion refused: manifest session_start_commit $m_start conflicts with the claim's start-commit $prior_start"
    die_fail
  fi
  if [[ -n "$prior_base" && -n "$m_base_branch" && "$m_base_branch" != "$prior_base" ]]; then
    gateway_release_all || true
    refuse "conversion refused: manifest run_base branch $m_base_branch conflicts with the claim's base $prior_base"
    die_fail
  fi
  local tmp_claim="$CLAIM_PATH.conversion.$$"
  {
    printf 'session: %s\nplan: %s\ncreated: %s\nupdated: %s\n' \
      "$SESSION" "$PLAN_ARG" "${prior_created:-$(iso_now)}" "$(iso_now)"
    [[ -n "$prior_branch" ]] && printf 'branch: %s\n' "$prior_branch"
    [[ -n "$prior_start" ]] && printf 'start-commit: %s\n' "$prior_start"
    [[ -n "$prior_base" ]] && printf 'base: %s\n' "$prior_base"
    true
  } >"$tmp_claim"
  # The atomic replacement: one rename over the verified prior claim, no
  # unlink gap (a crash leaves either the old complete claim or the new).
  if ! mv -f "$tmp_claim" "$CLAIM_PATH"; then
    rm -f "$tmp_claim"
    gateway_release_all || true
    die_tool "conversion: claim replacement rename failed at $CLAIM_PATH"
  fi

  # Manifest canonicalization (the Canonicalized manifest term): the
  # resumer, the exact operand, the registered target and its branch;
  # legacy Session:/Plan: aliases removed; unrelated content preserved;
  # written atomically. An interruption here leaves the claim naming the
  # resumer and the manifest naming the prior owner: the next attempt
  # refuses unchanged (no lineage is inferred, no automatic recovery).
  MANIFEST="$manifest" NEW_SESSION="$SESSION" NEW_PLAN="$PLAN_ARG" \
    NEW_WT="$wt" NEW_BRANCH="$registered_branch" PRIOR_OWNER="$holder" "$PYTHON" <<'PYCANON'
import os, re, sys

path = os.environ["MANIFEST"]
with open(path, encoding="utf-8", errors="surrogateescape") as fh:
    lines = fh.read().splitlines()

values = {
    "session_id": os.environ["NEW_SESSION"],
    "plan_path": os.environ["NEW_PLAN"],
    "run_worktree": os.environ["NEW_WT"],
    "run_branch": os.environ["NEW_BRANCH"],
}
prior_owner = os.environ["PRIOR_OWNER"]
seen = set()
out = []
for line in lines:
    if re.match(r"^(Session|Plan):", line):
        continue  # legacy aliases removed on canonicalization
    m = re.match(r"^(session_id|plan_path|run_worktree|run_branch):(.*)$", line)
    if m:
        key = m.group(1)
        seen.add(key)
        out.append(f"{key}: {values[key]}")
    else:
        out.append(line)
missing = [k for k in ("session_id", "plan_path", "run_worktree", "run_branch") if k not in seen]
if "run_session_id" not in seen and not any(
    line.startswith("run_session_id:") for line in out
):
    # The stable identity materializes at conversion: the verified prior
    # owner is the immutable origin identity (the Terms' recovery arm).
    insert_at = 0
    for line in out:
        if line.startswith("#"):
            insert_at += 1
        else:
            break
    out.insert(insert_at, f"run_session_id: {prior_owner}")
if missing:
    insert_at = 0
    for line in out:
        if line.startswith("#"):
            insert_at += 1
        else:
            break
    for key in reversed(missing):
        out.insert(insert_at, f"{key}: {values[key]}")
tmp = path + ".canonicalize.tmp"
with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as fh:
    fh.write("\n".join(out) + "\n")
os.replace(tmp, path)
PYCANON
  rc=$?
  if (( rc != 0 )); then
    gateway_release_all || true
    die_tool "conversion: manifest canonicalization failed at $manifest"
  fi

  # Post-replacement verification, then the success report; the caller
  # returns before the occupant refusal and the worktree add.
  if [[ "$(claim_field "$CLAIM_PATH" session)" != "$SESSION" ]]; then
    gateway_release_all || true
    die_tool "conversion: the replaced claim does not read back under session $SESSION"
  fi
  evidence "conversion: claim $CLAIM_PATH transferred from prior owner $holder to $SESSION (identity form: $form)"
  evidence "conversion: manifest canonicalized: $manifest"
  gateway_release_all || true
  CONVERSION_DONE=1
  TAKE_OK=1
  WT_PRE_REGISTERED=1
  return 0
}

claim_retry_gate() {
  # The single owner of the race-retry discipline shared by acquire_claim
  # and cmd_refresh: invoked once per loop iteration, it increments the
  # caller's attempt counter (passed by name) and dies with the
  # three-attempt ceiling's tool error when the count exceeds it. The
  # callers keep the zero initialization of their own attempt counters and
  # the full loop bodies (every continue site, and the state flags the
  # cleanup and exit traps consume); only the increment-plus-ceiling check
  # and its error text live here, so the ceiling and the wording cannot
  # drift between the two loops. The counter is read and written through
  # the caller's dynamic scope (printf -v, portable to bash 3.2; no
  # namerefs).
  local gate_var="$1" count
  count="${!gate_var}"
  count=$((count + 1))
  printf -v "$gate_var" '%s' "$count"
  if (( count > 3 )); then
    die_tool "claims directory kept racing at $CLAIM_PATH; re-derive the state from disk"
  fi
}

acquire_claim() {
  # The shared create-or-refuse state machine over $CLAIM_PATH. On return
  # 0 the session holds its own live claim and CREATED_HERE says whether
  # this invocation created it. An own live claim is handed to
  # $OWN_CLAIM_HOOK (per-mode disposition) without re-creation.
  local attempt=0 holder rc
  CREATED_HERE=0
  # The lock env and scratch dir serve every claim-access path (the
  # conversion arm and the merge-lock discipline both need them).
  GATEWAY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/execution-claim-gateway.XXXXXX")"
  if ! gateway_lock_env_prefix; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_tool "lock roots unresolvable from the OS account record"
  fi
  while :; do
    claim_retry_gate attempt
    if [[ ! -e "$CLAIM_PATH" ]]; then
      # The flag leads the create, closing the sub-command-boundary window
      # between claim creation and CREATED_HERE: a signal in that window
      # must still see the fresh claim as this invocation's own. The flag
      # clears again when a concurrent writer wins the noclobber create,
      # because the winner's claim is not ours to clean.
      if ! merge_lock_hold_or_reuse; then
        rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
        die_fail
      fi
      CREATED_HERE=1
      if ! create_claim_noclobber "$CLAIM_PATH" "$SESSION" "$PLAN_ARG"; then
        CREATED_HERE=0
        gateway_release_all || true
        continue  # a concurrent writer won the create; re-evaluate its claim
      fi
      gateway_release_all || true
      rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
      return 0
    fi
    holder="$(claim_session "$CLAIM_PATH")" \
      || die_tool "claim $CLAIM_PATH carries no session: line (unsupported record shape)"
    if [[ "$holder" == "$SESSION" ]]; then
      if ! merge_lock_hold_or_reuse; then
        rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
        die_fail
      fi
      "$OWN_CLAIM_HOOK"
      gateway_release_all || true
      rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
      return 0
    fi
    # Dead-run conversion (take mode): a foreign claim whose run manifest
    # remains at the registered target worktree converts only through the
    # gateway's evidence-gated arm (identity forms, session channel,
    # provider terminal status, completed-run boundary, both gateway-owned
    # locks, atomic replacement, canonicalization). A refusal preserves the
    # claim and exits; no conversion context falls through to the
    # historical fresh-refusal / takeover flow below.
    if [[ "$MODE" == "take" ]]; then
      # The if-context keeps the arm's nonzero verdicts off set -e's exit.
      rc=0
      if try_dead_run_conversion "$holder"; then
        rc=0
      else
        rc=$?
      fi
      case "$rc" in
        0) return 0 ;;   # converted: CONVERSION_DONE=1, TAKE_OK=1 set
        2) : ;;          # no conversion context: the historical flow judges
        3) continue ;;   # the claim changed under the locks; re-evaluate
        *) die_fail ;;   # a refusal exits inside the arm; safety net
      esac
    fi
    # A fresh foreign claim refuses inside the helper (die_fail); a stale
    # one reaches the mode's pre-takeover gate (take mode's branch-occupant
    # check refuses here, preserving the foreign claim) and then the
    # takeover. The merge-lock discipline covers this claim access; the
    # conversion arm above runs its own done-then-merge ordering instead.
    if ! merge_lock_hold_or_reuse; then
      rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
      die_fail
    fi
    refuse_fresh_foreign_claim "$holder" || true
    if [[ -n "$PRE_TAKEOVER_HOOK" ]]; then
      "$PRE_TAKEOVER_HOOK" "$holder"
    fi
    if ! takeover_stale_claim "$holder"; then
      gateway_release_all || true
      continue  # the claim changed under us; re-evaluate from the top
    fi
    gateway_release_all || true
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    return 0
  done
}

require_session() {
  [[ -n "$SESSION" ]] || usage_error "--session <id> is required in mode $MODE"
}

resolve_start_commit() {
  # Resolve --start-commit to a full commit sha through rev-parse --verify
  # before anything is written: an unresolvable value is a usage refusal
  # (exit 3, nothing written), a resolved value is recorded as the claim's
  # start-commit line.
  [[ -n "$START_COMMIT" ]] || return 0
  local resolved
  resolved="$(git -C "$ANCHOR" rev-parse --verify --quiet "${START_COMMIT}^{commit}" 2>/dev/null)" \
    || usage_error "--start-commit does not resolve to an existing commit: $START_COMMIT"
  START_COMMIT="$resolved"
}

resolve_context() {
  [[ -f "$PLAN_ARG" ]] || die_tool "plan operand not readable: $PLAN_ARG"
  ANCHOR="$(resolve_anchor)" || die_tool "repository anchor unresolvable: the working directory is not inside a git repository"
  resolve_start_commit
  PRIMARY="$(resolve_primary "$ANCHOR")" || die_tool "primary checkout unresolvable: no worktree entry in git worktree list --porcelain"
  CLAIMS_DIR="$PRIMARY/$CLAIMS_REL"
  mkdir -p "$CLAIMS_DIR" 2>/dev/null || die_tool "claims directory not creatable: $CLAIMS_DIR"
  SLUG="$(derive_slug "$PLAN_ARG")" \
    || die_tool "artifact slug derivation failed for $PLAN_ARG"
  CLAIM_PATH="$CLAIMS_DIR/$SLUG.md"
}

# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #

take_own_claim_hook() {
  # An own live claim with the worktree directory already on disk is the
  # adopt-instead-of-recreate refusal: exit 1 naming the existing worktree,
  # the claim kept untouched.
  if [[ -e "$WT_PARENT/$BRANCH" ]]; then
    refuse "take refused: worktree directory already exists at $WT_PARENT/$BRANCH"
    refuse "  the session adopts the existing worktree instead of recreating it; the claim is kept"
    die_fail
  fi
  restamp_claim "$CLAIM_PATH" "" "$BRANCH" "$START_COMMIT"
}

claim_own_claim_hook() {
  restamp_claim "$CLAIM_PATH" "" "$BRANCH" "$START_COMMIT"
  evidence "claim already held by this session: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
  printf 'OUTCOME: pass\n'
  exit 0
}

take_occupant_gate() {
  # The pre-takeover arm of the branch-occupant refusal (acquire_claim runs
  # this hook after the fresh-foreign refusal and before the stale
  # takeover): a stale foreign claim on an occupied branch is refused with
  # its claim preserved, so the dead session's registry entry survives for
  # the next reader while the refusal names the occupying worktree and both
  # remedies.
  local holder="$1" occupant
  occupant="$(occupying_worktree "$ANCHOR" "$BRANCH" || true)"
  if [[ -z "$occupant" ]]; then
    return 0
  fi
  refuse "take refused: branch $BRANCH is held by an existing worktree"
  refuse "  occupying worktree: $occupant"
  refuse "  stale claim preserved: $CLAIM_PATH (holder session: $holder)"
  refuse "  remedies: adopt the existing worktree per the recognition arm, or remove it deliberately, then take again"
  die_fail
}

cmd_take() {
  require_session
  [[ -n "$BRANCH" ]] || usage_error "take requires --branch <name>"
  [[ -n "$WT_PARENT" ]] || usage_error "take requires --worktree-parent <dir>"
  OWN_CLAIM_HOOK="take_own_claim_hook"
  PRE_TAKEOVER_HOOK="take_occupant_gate"
  resolve_context
  local wt_path="$WT_PARENT/$BRANCH" occupant add_err

  # Arm the exit-path cleanup before a claim can come into existence: from
  # here on, any failure or signal deletes this invocation's fresh claim
  # again, covering the paths without an explicit cleanup arm (an
  # uncreatable worktree parent, an interrupt mid-take).
  TAKE_GATE=1

  acquire_claim

  # Conversion success returns before the occupant refusal and the worktree
  # add (the adopted worktree is the run's own; the plan Terms: after
  # replacement and manifest refresh, verify the registered target, report
  # success, disarm cleanup, and return).
  if (( CONVERSION_DONE )); then
    evidence "claim: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
    evidence "worktree adopted: $WT_PARENT/$BRANCH (branch: $(worktree_registered_branch "$WT_PARENT/$BRANCH"))"
    printf 'OUTCOME: pass\n'
    return 0
  fi

  # The post-acquire claim mutations (the refusal arms' self-cleanup and
  # the success restamp) sit inside the merge-lock discipline: acquire_claim
  # released its hold at return, so this command re-takes it here.
  GATEWAY_TMP="${GATEWAY_TMP:-$(mktemp -d "${TMPDIR:-/tmp}/execution-claim-gateway.XXXXXX")}"
  [[ -n "${GATEWAY_LOCK_ENV+x}" ]] || { gateway_lock_env_prefix || { rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""; die_tool "lock roots unresolvable from the OS account record"; }; }
  if ! merge_lock_hold_or_reuse; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_fail
  fi

  # Branch occupation refused before any worktree creation, with the fresh
  # claim this invocation created cleaned up (an unclaimed leftover
  # worktree lands here, and so does an occupant that appeared after the
  # pre-takeover gate; the stale-foreign-claim case itself was already
  # refused inside acquire_claim with the foreign claim preserved).
  occupant="$(occupying_worktree "$ANCHOR" "$BRANCH" || true)"
  if [[ -n "$occupant" ]]; then
    refuse "take refused: branch $BRANCH is held by an existing worktree"
    refuse "  occupying worktree: $occupant"
    refuse "  remedies: adopt the existing worktree per the recognition arm, or remove it deliberately, then take again"
    if (( CREATED_HERE )); then
      rm -f "$CLAIM_PATH"
      refuse "  cleanup: removed this invocation's fresh claim $CLAIM_PATH"
    fi
    gateway_release_all || true
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_fail
  fi

  mkdir -p "$WT_PARENT" 2>/dev/null || die_tool "worktree parent not creatable: $WT_PARENT"
  # Both witnesses lead the add: the cleanup's removal gate reads
  # WT_PRE_REGISTERED (a path already carrying a registered worktree, on
  # any branch or detached, is never removed by the cleanup), and the
  # add-failure rollback reads BRANCH_PRE_EXISTED (a branch that was
  # already there is not this add's to delete).
  if path_is_registered_worktree "$wt_path"; then
    WT_PRE_REGISTERED=1
  fi
  if git -C "$ANCHOR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    BRANCH_PRE_EXISTED=1
  fi
  # The add is the take's irreversible step: from the attempt's start until
  # TAKE_OK the exit-path cleanup also removes any worktree this add
  # brought into existence (a signal landing mid-add, a failed add that
  # left partial state).
  WT_AT_RISK=1
  if ! add_err="$(git -C "$ANCHOR" worktree add -b "$BRANCH" "$wt_path" ${BASE:+"$BASE"} 2>&1)"; then
    refuse "worktree add failed: $add_err"
    # `git worktree add -b` creates the branch before validating the path,
    # so a failed add can strand the freshly created branch (every later
    # take of that branch name would fail until a manual delete); the
    # rollback is best-effort over a branch absent just before the add
    # (the BRANCH_PRE_EXISTED witness): a concurrent creator inside that
    # window can be misattributed (documented residual).
    if (( ! BRANCH_PRE_EXISTED )); then
      if git -C "$ANCHOR" branch -D "$BRANCH" >/dev/null 2>&1; then
        refuse "cleanup: removed this invocation's stranded branch $BRANCH"
      fi
    fi
    if (( CREATED_HERE )); then
      rm -f "$CLAIM_PATH"
      refuse "cleanup: removed this invocation's fresh claim $CLAIM_PATH"
    fi
    die_fail
  fi

  # Success path: the worktree add succeeded, so the take's irreversible
  # step is done and the claim survives every exit route from here.
  TAKE_OK=1

  # The base line rides along once the worktree exists (plan Terms: the
  # base line is written after the worktree creation, so a take with --base
  # records the run's starting point in the claim); the branch and
  # start-commit lines ride the same restamp.
  restamp_claim "$CLAIM_PATH" "$BASE" "$BRANCH" "$START_COMMIT"
  evidence "claim: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
  if [[ -n "$BASE" ]]; then
    evidence "worktree: $wt_path (branch: $BRANCH, base: $BASE)"
  else
    evidence "worktree: $wt_path (branch: $BRANCH)"
  fi
  gateway_release_all || true
  rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
  printf 'OUTCOME: pass\n'
}

cmd_claim() {
  require_session
  OWN_CLAIM_HOOK="claim_own_claim_hook"
  resolve_context
  acquire_claim
  evidence "claim: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
  printf 'OUTCOME: pass\n'
}

cmd_refresh() {
  require_session
  resolve_context
  GATEWAY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/execution-claim-gateway.XXXXXX")"
  if ! gateway_lock_env_prefix; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_tool "lock roots unresolvable from the OS account record"
  fi
  if ! merge_lock_hold_or_reuse; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_fail
  fi
  local attempt=0 holder
  while :; do
    claim_retry_gate attempt
    if [[ -e "$CLAIM_PATH" ]]; then
      holder="$(claim_session "$CLAIM_PATH")" \
        || die_tool "claim $CLAIM_PATH carries no session: line (unsupported record shape)"
      if [[ "$holder" != "$SESSION" ]]; then
        refuse "refresh refused: claim $CLAIM_PATH names session $holder"
        refuse "  a claim naming a foreign session is never modified by this session"
        die_fail
      fi
      restamp_claim "$CLAIM_PATH" "$BASE" "$BRANCH" "$START_COMMIT"
      evidence "refreshed: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
      gateway_release_all || true
      rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
      printf 'OUTCOME: pass\n'
      return 0
    fi
    # Recreate after a takeover unlinked the claim; the base line rides
    # along when --base was passed, the branch and start-commit lines ride
    # the noclobber write itself.
    if ! create_claim_noclobber "$CLAIM_PATH" "$SESSION" "$PLAN_ARG"; then
      continue
    fi
    if [[ -n "$BASE" ]]; then
      restamp_claim "$CLAIM_PATH" "$BASE" "$BRANCH" "$START_COMMIT"
    fi
    evidence "recreated: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
    gateway_release_all || true
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    printf 'OUTCOME: pass\n'
    return 0
  done
}

cmd_release() {
  require_session
  resolve_context
  GATEWAY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/execution-claim-gateway.XXXXXX")"
  if ! gateway_lock_env_prefix; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_tool "lock roots unresolvable from the OS account record"
  fi
  if ! merge_lock_hold_or_reuse; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_fail
  fi
  local holder
  if [[ ! -e "$CLAIM_PATH" ]]; then
    refuse "release refused: no execution claim found at $CLAIM_PATH"
    refuse "  a missing claim is a loud refusal, never a silent pass"
    die_fail
  fi
  holder="$(claim_session "$CLAIM_PATH")" \
    || die_tool "claim $CLAIM_PATH carries no session: line (unsupported record shape)"
  if [[ "$holder" != "$SESSION" ]]; then
    refuse "release refused: claim $CLAIM_PATH names session $holder"
    refuse "  a claim naming a foreign session is never deleted by this session; the claim is left untouched"
    die_fail
  fi
  # Arm-4 last-instant compare-and-delete: the session check is the
  # unlink's immediately-preceding operation; a lost race refuses naming the
  # racing holder.
  if ! grep -q "^session: ${SESSION}\$" "$CLAIM_PATH" 2>/dev/null || ! rm -f "$CLAIM_PATH"; then
    refuse "release refused: claim $CLAIM_PATH changed under this release (racing holder: $(claim_session "$CLAIM_PATH" 2>/dev/null || echo unattributed))"
    refuse "  the mutation lost its last-instant compare-and-delete; the claim is left untouched"
    die_fail
  fi
  evidence "released: $CLAIM_PATH (session: $SESSION, slug: $SLUG)"
  gateway_release_all || true
  rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
  printf 'OUTCOME: pass\n'
}

# --------------------------------------------------------------------------- #
# Sweep mode
# --------------------------------------------------------------------------- #

sweep_facts_value() {
  # The named TOML-fence key's double-quoted value from the anchor's facts
  # document (the facts_paths.py parse shape, one sed over the key lines);
  # empty when the file or the key is unresolvable, so every caller keeps
  # its own conventional fallback.
  local anchor="$1" key="$2" facts value
  facts="$anchor/.ai-playbook/facts.md"
  [[ -r "$facts" ]] || return 0
  value="$(sed -n -E "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]+)\".*/\1/p" "$facts" 2>/dev/null | head -n 1)" || true
  printf '%s\n' "$value"
}

sweep_landing_subject_names_slug() {
  # True when the named branch's history carries a landing-shaped commit
  # subject (the repository's landing-subject convention: `check: land ...`)
  # naming the kebab-case slug as a hyphen-bounded segment (never as the
  # prefix or suffix of a longer token, so a longer slug cannot vouch for
  # its prefix). Subjects are captured whole before the match and matched
  # one per line, so a grep short-circuit can never flip the verdict
  # through a SIGPIPE'd producer under pipefail; an unreadable ref reads
  # as not-named (fail closed).
  local anchor="$1" ref="$2" slug="$3" re subjects subject
  subjects="$(git -C "$anchor" log --format=%s "$ref" -- 2>/dev/null)" || return 1
  while IFS= read -r subject; do
    case "$subject" in
      "check: land "*)
        re="(^|[^a-z0-9-])${slug}([^a-z0-9-]|\$)"
        if [[ "$subject" =~ $re ]]; then
          return 0
        fi
        ;;
    esac
  done <<<"$subjects"
  return 1
}

cmd_sweep() {
  require_session
  ANCHOR="$(resolve_anchor)" || die_tool "repository anchor unresolvable: the working directory is not inside a git repository"
  PRIMARY="$(resolve_primary "$ANCHOR")" || die_tool "primary checkout unresolvable: no worktree entry in git worktree list --porcelain"
  CLAIMS_DIR="$PRIMARY/$CLAIMS_REL"
  if [[ ! -d "$CLAIMS_DIR" ]]; then
    evidence "sweep: no claims directory at $CLAIMS_DIR; nothing to sweep"
    printf 'OUTCOME: pass\n'
    return 0
  fi
  # The plans root: the facts document's plans_dir key, the conventional
  # docs/history/plans default when the key is unresolvable (the
  # warn-and-scan-default fallback precedent); an absolute fact value is
  # the plans root itself, never joined onto the primary checkout (the
  # double prefix would miss the archive and misjudge the landedness
  # leg). The main-history branch: the confirmed base_branch fact, else
  # the origin HEAD's branch, else the primary checkout's current branch;
  # an unresolvable ref only degrades the history leg, and every claim
  # that then cannot prove its plan landed is skipped (fail closed per
  # claim), never deleted.
  local plans_root plans_dir main_ref
  plans_root="$(sweep_facts_value "$ANCHOR" plans_dir)"
  plans_root="${plans_root:-docs/history/plans}"
  plans_root="${plans_root%/}"
  if [[ "$plans_root" == /* ]]; then
    plans_dir="$plans_root"
  else
    plans_dir="$PRIMARY/$plans_root"
  fi
  main_ref="$(sweep_facts_value "$ANCHOR" base_branch)"
  if [[ -z "$main_ref" ]]; then
    main_ref="$(git -C "$ANCHOR" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')" || true
  fi
  if [[ -z "$main_ref" ]]; then
    main_ref="$(git -C "$PRIMARY" symbolic-ref --short HEAD 2>/dev/null)" || true
  fi
  # The merge-lock discipline covers the walk (claim access for every
  # claim); the lock env and scratch dir back it.
  GATEWAY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/execution-claim-gateway.XXXXXX")"
  if ! gateway_lock_env_prefix; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_tool "lock roots unresolvable from the OS account record"
  fi
  if ! merge_lock_hold_or_reuse; then
    rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
    die_fail
  fi
  local deleted=0 skipped=0 claim_file plan_val branch_val slug occupant reason landed parked
  for claim_file in "$CLAIMS_DIR"/*.md; do
    [[ -e "$claim_file" ]] || break  # the claims directory holds no claim
    reason=""
    if [[ ! -f "$claim_file" ]]; then
      reason="not a regular file"
    fi
    if [[ -z "$reason" ]]; then
      # The stale-preservation leg (the plan Terms: stale take and sweep
      # preserve a claim whenever either supported manifest form remains at
      # its exact registered-worktree path, regardless of branch, owner, or
      # plan mismatch; multiple matches or an unresolvable scan preserve
      # too). The claim's own file name is the plan's canonical artifact
      # slug, so the scan needs no claim fields.
      slug="$(basename "$claim_file" .md)"
      local scan verdict scan_wt
      scan="$(scan_registered_manifest "$slug")"
      verdict="${scan%%$'\t'*}"
      case "$verdict" in
        found)
          IFS=$'\t' read -r verdict scan_mf scan_wt <<<"$scan"
          reason="run manifest remains at its registered worktree: $scan_wt"
          ;;
        multiple)
          reason="run manifests for this slug exist in more than one registered worktree (ambiguous)"
          ;;
        inconclusive)
          reason="preservation scan inconclusive (a manifest path holds a symlink)"
          ;;
      esac
    fi
    if [[ -z "$reason" ]]; then
      # The branch leg first (one porcelain read): a recorded branch still
      # held by a worktree keeps the claim whatever the plan's state, and
      # the skip reason names the occupant the next reader must see.
      branch_val="$(claim_field "$claim_file" branch)"
      if [[ -z "$branch_val" ]]; then
        reason="no branch: line; branch liveness cannot be ruled out"
      else
        occupant="$(occupying_worktree "$ANCHOR" "$branch_val" || true)"
        if [[ -n "$occupant" ]]; then
          reason="branch $branch_val is held by worktree $occupant"
        fi
      fi
    fi
    if [[ -z "$reason" ]]; then
      # The landedness leg: the claim's own file name is the plan's
      # canonical artifact slug (the claim file is named by it at
      # creation), so the history leg never needs the plan file readable.
      plan_val="$(claim_field "$claim_file" plan)"
      slug="$(basename "$claim_file" .md)"
      landed=0
      if [[ -z "$plan_val" ]]; then
        reason="no plan: line"
      elif [[ -f "$plans_dir/completed/$(basename "$plan_val")" ]]; then
        landed=1
      else
        # Anything under the plans root outside completed/ (the open plan,
        # a deferred/ or rejected/ park) is not a landing: the claim stays
        # whatever a landing subject elsewhere names, because a parked
        # plan's slug can ride a landing commit of a different era.
        parked="$(find "$plans_dir" -name "$(basename "$plan_val")" -not -path "*/completed/*" -print -quit 2>/dev/null)" || true
        if [[ -n "$parked" ]]; then
          reason="plan present under the plans root but not in the completed/ archive: ${parked#"$PRIMARY"/}"
        elif [[ -z "$main_ref" ]]; then
          reason="plan absent from the plans root and the main-history branch unresolvable"
        elif sweep_landing_subject_names_slug "$ANCHOR" "$main_ref" "$slug"; then
          landed=1
        else
          reason="plan absent from the plans root and no $main_ref landing commit subject names the slug $slug"
        fi
      fi
    fi
    if [[ -n "$reason" ]]; then
      evidence "sweep: skipped $claim_file: $reason"
      skipped=$((skipped + 1))
      continue
    fi
    rm -f "$claim_file" || die_tool "sweep could not delete $claim_file"
    evidence "sweep: deleted $claim_file (plan landed, branch $branch_val holds no worktree)"
    deleted=$((deleted + 1))
  done
  evidence "sweep: scanned $CLAIMS_DIR (session: $SESSION): deleted $deleted, skipped $skipped"
  gateway_release_all || true
  rm -rf "$GATEWAY_TMP"; GATEWAY_TMP=""
  printf 'OUTCOME: pass\n'
}

# --------------------------------------------------------------------------- #
# Argument parsing (usage violations are tool errors per the contract)
# --------------------------------------------------------------------------- #

MODE="${1:-}"
case "$MODE" in
  ""|take|claim|refresh|release|sweep) : ;;
  --help|-h) usage; exit 0 ;;
  *) usage_error "unknown mode: $MODE (expected take | claim | refresh | release | sweep)" ;;
esac
[[ -n "$MODE" ]] || usage_error "a mode is required (take | claim | refresh | release | sweep)"
shift
# sweep walks the whole claims directory and takes no plan operand; every
# other mode addresses one claim through its plan operand.
if [[ "$MODE" == "sweep" ]]; then
  PLAN_ARG=""
else
  PLAN_ARG="${1:-}"
  [[ -n "$PLAN_ARG" ]] || usage_error "a plan operand is required for mode $MODE"
  shift
fi

while (("$#" > 0)); do
  case "$1" in
    --session)
      [[ $# -ge 2 ]] || usage_error "--session requires a value"
      SESSION="$2"
      shift 2
      ;;
    --branch)
      [[ $# -ge 2 ]] || usage_error "--branch requires a value"
      BRANCH="$2"
      shift 2
      ;;
    --worktree-parent)
      [[ $# -ge 2 ]] || usage_error "--worktree-parent requires a value"
      WT_PARENT="$2"
      shift 2
      ;;
    --base)
      [[ $# -ge 2 ]] || usage_error "--base requires a value"
      BASE="$2"
      shift 2
      ;;
    --start-commit)
      [[ $# -ge 2 ]] || usage_error "--start-commit requires a value"
      START_COMMIT="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      usage_error "unknown argument: $1"
      ;;
  esac
done

case "$MODE" in
  take) cmd_take ;;
  claim) cmd_claim ;;
  refresh) cmd_refresh ;;
  release) cmd_release ;;
  sweep) cmd_sweep ;;
esac
