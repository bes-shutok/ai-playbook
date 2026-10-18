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
# scopes the rollback to branches absent just before the add: the cleanup
# CAN be reached with a pre-registered path (the add fails over the
# occupied path and the refusal exits), and the witness gates, not the
# arm point alone, keep each half off that pre-existing occupant.
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
    if (( CREATED_HERE && ! ARM3_RESUME )) \
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
trap cleanup_fresh_claim EXIT
trap 'cleanup_fresh_claim; exit 130' INT
trap 'cleanup_fresh_claim; exit 143' TERM

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

resume_evidence_matches() {
  # Arm 3 (plan 2026-10-10-coordination-single-writer-ttl, Task 2): a
  # restored worktree whose state verifies as the same run resuming takes
  # over or re-derives its claim instead of colliding with the fresh-foreign
  # refusal. Evidence shape: receipt-to-row - the run worktree's session
  # manifest row (docs/tmp/execute-plan/<slug>/manifest.md) names the foreign
  # claim's holder session as its Session and this invocation's plan operand
  # as its Plan; the manifest is the durable receipt the pre-restart run
  # wrote, and no process enumeration is consulted. Verification failure
  # defaults to the refusal (the caller falls through to
  # refuse_fresh_foreign_claim).
  local holder="$1" wt manifest
  [[ -n "$BRANCH" && -n "$SLUG" && -n "$WT_PARENT" ]] || return 1
  wt="$WT_PARENT/$BRANCH"
  [[ -d "$wt" ]] || return 1
  manifest="$wt/docs/tmp/execute-plan/$SLUG/manifest.md"
  [[ -f "$manifest" ]] || return 1
  grep -q "^Session: ${holder}\$" "$manifest" 2>/dev/null || return 1
  grep -q "^Plan: .*${PLAN_ARG##*/}" "$manifest" 2>/dev/null || return 1
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
  local attempt=0 holder
  CREATED_HERE=0
  ARM3_RESUME="${ARM3_RESUME:-0}"
  while :; do
    claim_retry_gate attempt
    if [[ ! -e "$CLAIM_PATH" ]]; then
      # The flag leads the create, closing the sub-command-boundary window
      # between claim creation and CREATED_HERE: a signal in that window
      # must still see the fresh claim as this invocation's own. The flag
      # clears again when a concurrent writer wins the noclobber create,
      # because the winner's claim is not ours to clean.
      CREATED_HERE=1
      if ! create_claim_noclobber "$CLAIM_PATH" "$SESSION" "$PLAN_ARG"; then
        CREATED_HERE=0
        continue  # a concurrent writer won the create; re-evaluate its claim
      fi
      return 0
    fi
    holder="$(claim_session "$CLAIM_PATH")" \
      || die_tool "claim $CLAIM_PATH carries no session: line (unsupported record shape)"
    if [[ "$holder" == "$SESSION" ]]; then
      "$OWN_CLAIM_HOOK"
      return 0
    fi
    # Arm 3 runs beside the fresh-foreign refusal: a restored worktree whose
    # state verifies as the same run resuming takes over the claim instead of
    # colliding; verification failure defaults to the refusal below.
    if resume_evidence_matches "$holder"; then
      evidence "arm-3 restored-worktree takeover: verified same-run resume of session $holder"
      if grep -q "^session: ${holder}\$" "$CLAIM_PATH" 2>/dev/null && rm -f "$CLAIM_PATH"; then
        CREATED_HERE=1
        ARM3_RESUME=1
        if create_claim_noclobber "$CLAIM_PATH" "$SESSION" "$PLAN_ARG"; then
          return 0
        fi
        CREATED_HERE=0
      fi
      continue  # the claim changed under us; re-evaluate from the top
    fi
    # A fresh foreign claim refuses inside the helper (die_fail); a stale
    # one reaches the mode's pre-takeover gate (take mode's branch-occupant
    # check refuses here, preserving the foreign claim) and then the
    # takeover.
    refuse_fresh_foreign_claim "$holder" || true
    if [[ -n "$PRE_TAKEOVER_HOOK" ]]; then
      "$PRE_TAKEOVER_HOOK" "$holder"
    fi
    if ! takeover_stale_claim "$holder"; then
      continue  # the claim changed under us; re-evaluate from the top
    fi
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
    if (( CREATED_HERE && ! ARM3_RESUME )); then
      rm -f "$CLAIM_PATH"
      refuse "  cleanup: removed this invocation's fresh claim $CLAIM_PATH"
    fi
    if (( ARM3_RESUME )); then
      refuse "  the re-derived claim is kept (arm-3 same-run resume): the next take adopts the existing worktree"
    fi
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
    if (( CREATED_HERE && ! ARM3_RESUME )); then
      rm -f "$CLAIM_PATH"
      refuse "cleanup: removed this invocation's fresh claim $CLAIM_PATH"
    fi
    if (( ARM3_RESUME )); then
      refuse "the re-derived claim is kept (arm-3 same-run resume): the next take adopts the existing worktree"
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
    printf 'OUTCOME: pass\n'
    return 0
  done
}

cmd_release() {
  require_session
  resolve_context
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
  local deleted=0 skipped=0 claim_file plan_val branch_val slug occupant reason landed parked
  for claim_file in "$CLAIMS_DIR"/*.md; do
    [[ -e "$claim_file" ]] || break  # the claims directory holds no claim
    reason=""
    if [[ ! -f "$claim_file" ]]; then
      reason="not a regular file"
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
