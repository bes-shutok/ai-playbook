#!/usr/bin/env bash
# Per-git-repo exclusive locks: the done workflow (learn → docs-branch → commit)
# and merge/landing critical sections. One lock lifecycle, two command families
# (done-* and merge-*); the mode selects the root env var, the session-file
# name, and the export names, so a holder may hold both locks at once.
# Agent-agnostic: invoked from done/SKILL.md Step 0 and Step 6.
set -euo pipefail

# The mode derives from the command prefix. Everything downstream reads only
# the resolved names below; it never touches DONE_LOCK_* / MERGE_LOCK_* again.
LOCK_MODE="done"
case "${1:-}" in
  merge-*) LOCK_MODE="merge" ;;
esac

if [[ "$LOCK_MODE" == "merge" ]]; then
  PROG="merge-lock"
  WORKFLOW_NOUN="landing workflow"
  SESSION_NAME="merge-lock.session"
  LOCK_ROOT="${MERGE_LOCK_ROOT:-${HOME}/.ai-playbook/locks/merge}"
  POLL_SECS="${MERGE_LOCK_POLL_SECS:-30}"
  STALE_SECS="${MERGE_LOCK_STALE_SECS:-600}"
  INCOMPLETE_SECS="${MERGE_LOCK_INCOMPLETE_SECS:-5}"
  DEAD_HOLDER_GRACE_SECS="${MERGE_LOCK_DEAD_HOLDER_GRACE_SECS:-5}"
  LOCK_HOLDER_PID="${MERGE_LOCK_HOLDER_PID:-}"
  LOCK_DIR_ENV="${MERGE_LOCK_DIR:-}"
  LOCK_TOKEN_ENV="${MERGE_LOCK_TOKEN:-}"
  ENV_PREFIX="MERGE_LOCK"
else
  PROG="done-lock"
  WORKFLOW_NOUN="done workflow"
  SESSION_NAME="done-lock.session"
  LOCK_ROOT="${DONE_LOCK_ROOT:-${HOME}/.ai-playbook/locks/done}"
  POLL_SECS="${DONE_LOCK_POLL_SECS:-30}"
  STALE_SECS="${DONE_LOCK_STALE_SECS:-1800}"
  INCOMPLETE_SECS="${DONE_LOCK_INCOMPLETE_SECS:-5}"
  DEAD_HOLDER_GRACE_SECS="${DONE_LOCK_DEAD_HOLDER_GRACE_SECS:-5}"
  LOCK_HOLDER_PID="${DONE_LOCK_HOLDER_PID:-}"
  LOCK_DIR_ENV="${DONE_LOCK_DIR:-}"
  LOCK_TOKEN_ENV="${DONE_LOCK_TOKEN:-}"
  ENV_PREFIX="DONE_LOCK"
fi
DIR_VAR="${ENV_PREFIX}_DIR"
TOKEN_VAR="${ENV_PREFIX}_TOKEN"
META_FILE="meta.env"

# The outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run
# ends with exactly one final `OUTCOME: <pass|fail|indeterminate|tool_error>`
# line matching the exit code. Declared placement deviation: the acquire
# subcommands emit the line on STDERR so their eval-consumed stdout stays
# export-only; every other subcommand emits it on stdout. --help and usage
# text are metadata-exempt (no OUTCOME line).
IS_ACQUIRE_CMD=0
emit_outcome() {
  local outcome="$1"
  if [[ "$IS_ACQUIRE_CMD" -eq 1 ]]; then
    echo "OUTCOME: ${outcome}" >&2
  else
    echo "OUTCOME: ${outcome}"
  fi
}

usage() {
  cat <<'EOF'
Usage: done-lock.sh <command> [args...]

Commands:
  acquire [--label TEXT]     Try once; print DONE_LOCK_DIR and DONE_LOCK_TOKEN on stdout when acquired.
  wait-acquire [--label TEXT] [--max-wait SECS]
                             Poll until acquired (default max wait: 7200s). Prints exports on success.
  release                    Remove lock when DONE_LOCK_DIR and DONE_LOCK_TOKEN match (env only).
  release-repo               Same as release; requires env (refuses shared session load).
  status                     Show holder for current repo, or "free".
  stale-clean                Remove stale/abandoned/incomplete lock for current repo.
                             Also removes a session-fenced lock when age >= DONE_LOCK_STALE_SECS
                             (operator escape; auto-acquire still protects live or ambiguous holders).
  selftest                   Run built-in race/fence fixtures (pass/fail outcome).

Merge landing lock (merge-* commands; same semantics and exit codes as the
done commands above, over a separate namespace: default root
~/.ai-playbook/locks/merge, session file .ai-playbook/merge-lock.session in
the checkout that holds the git common dir (the primary checkout), MERGE_LOCK_DIR / MERGE_LOCK_TOKEN exports; a holder may hold both the done
lock and the merge lock at once). Merge locks are keyed per-REPOSITORY: any
linked worktree of one repo acquires and observes the same lock (the key
derives from the resolved git common dir); done-mode locks stay keyed
per-worktree on --show-toplevel.
  merge-acquire [--label TEXT]
  merge-wait-acquire [--label TEXT] [--max-wait SECS]
  merge-release              Token-fenced release from MERGE_LOCK_* env.
  merge-release-repo         Same as merge-release; requires env (no session load).
  merge-status               Show merge holder for current repo, or "free".
  merge-stale-clean          Remove stale/abandoned/incomplete merge lock
                             (operator escape at MERGE_LOCK_STALE_SECS age).

Environment:
  DONE_LOCK_ROOT             Lock parent directory (default: ~/.ai-playbook/locks/done)
  DONE_LOCK_POLL_SECS        Poll interval for wait-acquire (default: 30)
  DONE_LOCK_STALE_SECS       Age before stale-clean may remove a fenced lock (default: 1800)
  DONE_LOCK_DEAD_HOLDER_GRACE_SECS
                             Minimum age before a verified dead holder may be auto-recovered (default: 5)
  DONE_LOCK_INCOMPLETE_SECS  Age before meta-less lock_dir is treated as crash leftover (default: 5)
  DONE_LOCK_HOLDER_PID       For one-shot shell callers: pin this to a long-lived process
                             so the lock survives the acquiring call's exit; leave unset
                             when eval'ing from a persistent shell (the default stays the
                             PPID of the eval'ing shell; do not use the acquire script's
                             own PID).
  DONE_LOCK_DIR / DONE_LOCK_TOKEN
                             Required in env for release / release-repo. Session file is
                             fence/status only; release-repo will not source it.
  MERGE_LOCK_ROOT            Merge lock parent directory (default: ~/.ai-playbook/locks/merge)
  MERGE_LOCK_POLL_SECS       Poll interval for merge-wait-acquire (default: 30)
  MERGE_LOCK_STALE_SECS      Age before merge-stale-clean may remove a fenced lock (default: 600)
  MERGE_LOCK_DEAD_HOLDER_GRACE_SECS
                             Minimum age before a verified dead merge-lock holder
                             may be auto-recovered (default: 5)
  MERGE_LOCK_INCOMPLETE_SECS Age before a meta-less merge lock_dir is treated as
                             crash leftover (default: 5)
  MERGE_LOCK_HOLDER_PID      Merge-mode equivalent of DONE_LOCK_HOLDER_PID.
  MERGE_LOCK_DIR / MERGE_LOCK_TOKEN
                             Required in env for merge-release / merge-release-repo.

Outcome contract (scripts/OUTCOME_CONTRACT.md):
  Every non-metadata run ends with exactly one final line
  `OUTCOME: <pass|fail|indeterminate|tool_error>` matching the exit code:
  0 pass; 1 fail (modeled violation; the offending evidence precedes the
  line); 2 indeterminate (evidence insufficient or ambiguous; the caller
  decides); 3 tool error (usage, environment, or unsupported lock data).
  A run with no final OUTCOME line is tool error: stop and re-derive from
  disk. Placement deviation: the acquire subcommands (acquire, wait-acquire,
  merge-acquire, merge-wait-acquire) print the OUTCOME line on STDERR so
  their eval-consumed stdout stays export-only; every other subcommand
  prints it on stdout. --help and this usage text are metadata-exempt (no
  OUTCOME line).
  Per-subcommand mapping:
    acquire / wait-acquire / merge-acquire / merge-wait-acquire
      success pass; held or max-wait exhaustion fail with the holder
      evidence; ambiguous holder (meta-less lock past the incomplete age,
      or unverifiable holder identity) indeterminate; usage and
      not-a-git-repo tool error.
    status      pass with the reported state in the evidence lines.
    stale-clean free pass; incomplete-too-new indeterminate (safety cannot
                be adjudicated); lock-changed-under-us or still-active fail
                with the race/holder evidence; unreadable lock metadata
                tool error.
    release / release-repo
                success pass; token mismatch and lock-changed-under-us
                fail; missing-env and missing-metadata refusals tool error.
    selftest    pass or fail by harness result.
EOF
}

require_git_repo() {
  if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "${PROG}: not inside a git repository" >&2
    emit_outcome tool_error
    exit 3
  fi
  if [[ "$LOCK_MODE" == "merge" ]]; then
    # Merge mode keys the lock per-REPOSITORY, not per-worktree: every linked
    # worktree of one repo shares the git common dir, so the repo identity is
    # derived from the resolved common dir. Keying choice (documented): hash
    # the resolved common dir with a trailing /.git stripped, i.e. the primary
    # checkout root; `repo_root` becomes that shared root, so the session
    # fence also lands in the primary checkout's .ai-playbook/ where every
    # worktree of the repo sees it. `git rev-parse --git-common-dir` may be
    # relative (it is ".git" in the primary checkout); --path-format=absolute
    # needs git 2.31+, so the value is resolved with cd + pwd -P instead
    # (bash 3.2 compatible, and pwd -P keeps the same physical path git
    # itself reports in worktrees). The physicalization is UNCONDITIONAL
    # (r2 CF1): an absolute common dir can still be a LOGICAL spelling of the
    # same directory (a symlinked path, e.g. an exported GIT_DIR named via
    # /tmp on a host where /tmp is a symlink to /private/tmp), and every
    # spelling of one repo must key the same lock. Done mode keeps
    # per-worktree keying on --show-toplevel, byte-identical.
    local common_dir
    if ! common_dir="$(git rev-parse --git-common-dir 2>/dev/null)"; then
      echo "${PROG}: not inside a git repository" >&2
      emit_outcome tool_error
      exit 3
    fi
    common_dir="$(cd "$common_dir" 2>/dev/null && pwd -P)" || {
      echo "${PROG}: cannot resolve the git common dir: ${common_dir}" >&2
      emit_outcome tool_error
      exit 3
    }
    case "$common_dir" in
      */.git) repo_root="${common_dir%/.git}" ;;
      *) repo_root="$common_dir" ;;
    esac
  fi
  repo_id="$(printf '%s' "$repo_root" | shasum -a 256 | cut -c1-16)"
  lock_dir="${LOCK_ROOT}/${repo_id}"
}

now_epoch() {
  date +%s
}

meta_field() {
  # Read KEY=value from meta without sourcing into caller scope (avoids clobbering locals).
  local meta="$1"
  local key="$2"
  local line
  line="$(grep -E "^${key}=" "$meta" 2>/dev/null | head -n1 || true)"
  printf '%s' "${line#${key}=}"
}

load_lock_meta() {
  local meta="${lock_dir}/${META_FILE}"
  lock_meta_label=""
  lock_meta_started_epoch=""
  lock_meta_started_at=""
  lock_meta_hostname=""
  lock_meta_holder_pid=""
  lock_meta_holder_identity=""
  lock_meta_token=""
  [[ -f "$meta" ]] || return 1
  lock_meta_label="$(meta_field "$meta" label)"
  lock_meta_started_epoch="$(meta_field "$meta" started_epoch)"
  lock_meta_started_at="$(meta_field "$meta" started_at)"
  lock_meta_hostname="$(meta_field "$meta" hostname)"
  lock_meta_holder_pid="$(meta_field "$meta" holder_pid)"
  lock_meta_holder_identity="$(meta_field "$meta" holder_identity)"
  lock_meta_token="$(meta_field "$meta" lock_token)"
  return 0
}

lock_age_secs() {
  # Fail closed: a truncated/partial meta with unset or non-numeric
  # started_epoch has an unknown age, never an infinitely-old one.
  load_lock_meta || true
  if [[ "$lock_meta_started_epoch" =~ ^[0-9]+$ ]]; then
    echo $(( $(now_epoch) - lock_meta_started_epoch ))
  else
    echo unknown
  fi
}

holder_pid_alive() {
  local pid="${1:-}"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

process_identity() {
  local pid="${1:-}"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
  ps -p "$pid" -o lstart= 2>/dev/null | sed 's/^[[:space:]]*//' | head -n1
}

holder_state() {
  # A reused PID or missing identity witness is ambiguous and never
  # auto-stealable. A dead PID is independently verified by the process table.
  local current_identity
  [[ "$lock_meta_holder_pid" =~ ^[1-9][0-9]*$ ]] || { echo unknown; return; }
  current_identity="$(process_identity "$lock_meta_holder_pid" || true)"
  [[ -n "$current_identity" ]] || { echo dead; return; }
  [[ -n "$lock_meta_holder_identity" ]] || { echo unknown; return; }
  if [[ "$current_identity" == "$lock_meta_holder_identity" ]]; then
    echo alive
  else
    echo ambiguous
  fi
}

is_stale_lock() {
  [[ -d "$lock_dir" ]] || return 1
  # Staleness requires a parsed token and a known numeric age; a truncated
  # meta without both is age-unknown and never stale.
  load_lock_meta || return 1
  [[ -n "$lock_meta_token" ]] || return 1
  local age
  age="$(lock_age_secs)"
  [[ "$age" =~ ^[0-9]+$ ]] || return 1
  [[ "$age" -ge "$STALE_SECS" ]]
}

is_dead_holder_lock() {
  [[ -d "$lock_dir" ]] || return 1
  load_lock_meta || return 1
  [[ -n "$lock_meta_holder_pid" ]] || return 1
  [[ "$(holder_state)" == "dead" ]] || return 1
  local grace_age
  grace_age="$(lock_age_secs)"
  [[ "$grace_age" =~ ^[0-9]+$ ]] || return 1
  [[ "$grace_age" -ge "$DEAD_HOLDER_GRACE_SECS" ]] || return 1
  # A matching session fence is not a live-process witness. Once the recorded
  # holder is independently verified dead, reclaim it after the grace period.
  return 0
}

session_fence_matches_lock() {
  local session_file s_dir s_token
  session_file="$(lock_session_file)"
  [[ -f "$session_file" ]] || return 1
  s_dir="$(grep -E "^${DIR_VAR}=" "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  s_token="$(grep -E "^${TOKEN_VAR}=" "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  [[ -n "$s_dir" && -n "$s_token" ]] || return 1
  load_lock_meta || return 1
  [[ "$s_dir" == "$lock_dir" && "$s_token" == "$lock_meta_token" ]]
}

is_stealable_lock() {
  # A verified-dead holder is reclaimable even when its session fence remains.
  is_dead_holder_lock && return 0
  # All other states, including session-fenced live or ambiguous holders, are
  # protected; stale-clean remains the explicit escape hatch.
  return 1
}

classify_held_outcome() {
  # Outcome classifier for an acquire refusal (scripts/OUTCOME_CONTRACT.md):
  # "held" means the refusal is definitively evidenced (verified-live holder,
  # a dead holder still inside its dead-recovery grace window, or an
  # in-flight meta-less peer younger than the incomplete age); "ambiguous"
  # means the hold cannot be adjudicated (meta-less lock past the incomplete
  # age, an unverifiable holder identity, or evidence that vanished
  # mid-race). The acquire subcommands map held to fail and ambiguous to
  # indeterminate.
  if [[ ! -d "$lock_dir" ]]; then
    echo ambiguous
    return 0
  fi
  if [[ ! -f "${lock_dir}/${META_FILE}" ]]; then
    local mtime now age
    mtime="$(stat -f %m "$lock_dir" 2>/dev/null || stat -c %Y "$lock_dir" 2>/dev/null || echo 0)"
    now="$(now_epoch)"
    age=$(( now - mtime ))
    if [[ "$age" -ge "$INCOMPLETE_SECS" ]]; then
      echo ambiguous
    else
      echo held
    fi
    return 0
  fi
  if ! load_lock_meta; then
    echo ambiguous
    return 0
  fi
  case "$(holder_state)" in
    alive|dead) echo held ;;
    *) echo ambiguous ;;
  esac
}

resolve_holder_pid() {
  # Prefer explicit long-lived PID; else PPID (eval'ing / waiting shell), never $$.
  if [[ -n "$LOCK_HOLDER_PID" ]]; then
    printf '%s' "$LOCK_HOLDER_PID"
  else
    printf '%s' "$PPID"
  fi
}

force_remove_lock() {
  # Unconditional remove (stale-clean / explicit). Prefer steal_remove_if_unchanged for steal path.
  local reason="${1:-abandoned}"
  if [[ -d "$lock_dir" ]]; then
    rm -rf "$lock_dir"
    echo "${PROG}: removed ${reason} lock at ${lock_dir}" >&2
  fi
}

steal_remove_if_unchanged() {
  # Compare-and-swap steal: only remove if token+epoch still match the steal decision.
  # Re-check meta inside the tomb after mv so a peer that recreated lock_dir between
  # compare and mv cannot destroy the newer generation (restore tomb on mismatch).
  local expected_token="$1"
  local expected_epoch="$2"
  local reason="${3:-abandoned}"
  local meta="${lock_dir}/${META_FILE}"
  [[ -d "$lock_dir" && -f "$meta" ]] || return 1
  local cur_token cur_epoch
  cur_token="$(meta_field "$meta" lock_token)"
  cur_epoch="$(meta_field "$meta" started_epoch)"
  if [[ "$cur_token" != "$expected_token" || "$cur_epoch" != "$expected_epoch" ]]; then
    return 1
  fi
  local tomb="${lock_dir}.removing.$$.$RANDOM"
  if ! mv "$lock_dir" "$tomb" 2>/dev/null; then
    return 1
  fi
  local tomb_token tomb_epoch
  tomb_token="$(meta_field "${tomb}/${META_FILE}" lock_token)"
  tomb_epoch="$(meta_field "${tomb}/${META_FILE}" started_epoch)"
  if [[ "$tomb_token" != "$expected_token" || "$tomb_epoch" != "$expected_epoch" ]]; then
    if [[ ! -d "$lock_dir" ]]; then
      mv "$tomb" "$lock_dir" 2>/dev/null || mv "$tomb" "${lock_dir}.conflict.$$" 2>/dev/null || rm -rf "$tomb"
    else
      mv "$tomb" "${lock_dir}.conflict.$$" 2>/dev/null || rm -rf "$tomb"
    fi
    return 1
  fi
  rm -rf "$tomb"
  echo "${PROG}: removed ${reason} lock at ${lock_dir}" >&2
  return 0
}

write_meta() {
  local lock_token="$1"
  local label="$2"
  local started holder meta tmp
  # A newline or carriage return in the label could forge later identity
  # fields (meta_field reads first match); reject instead of escaping.
  if [[ "$label" == *$'\n'* || "$label" == *$'\r'* ]]; then
    echo "${PROG}: --label must not contain newline or carriage return" >&2
    return 1
  fi
  started="$(now_epoch)"
  holder="$(resolve_holder_pid)"
  local holder_identity="$(process_identity "$holder" || true)"
  meta="${lock_dir}/${META_FILE}"
  # Refuse to overwrite a peer's meta if they claimed the dir first.
  if [[ -f "$meta" ]]; then
    return 1
  fi
  # Write atomically (temp file + mv -n) so a crash mid-write can never
  # expose a truncated meta.env to a concurrent reader.
  tmp="${meta}.tmp.$$.$RANDOM"
  if ! cat >"${tmp}" <<EOF
lock_token=${lock_token}
repo_root=${repo_root}
label=${label}
started_epoch=${started}
started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
hostname=$(hostname -s 2>/dev/null || hostname)
holder_pid=${holder}
holder_identity=${holder_identity}
EOF
  then
    rm -f "$tmp"
    return 1
  fi
  if ! mv -n "$tmp" "$meta" 2>/dev/null || [[ "$(meta_field "$meta" lock_token)" != "$lock_token" ]]; then
    rm -f "$tmp"
    return 1
  fi
  return 0
}

print_exports() {
  local token="$1"
  printf 'export %s=%q\n' "$DIR_VAR" "$lock_dir"
  printf 'export %s=%q\n' "$TOKEN_VAR" "$token"
}

lock_session_file() {
  echo "${repo_root}/.ai-playbook/${SESSION_NAME}"
}

clear_lock_session_if_token() {
  # Clear shared session only when it still names the token we released/stole.
  # mv + re-check so a concurrent write_lock_session cannot be deleted after replace.
  local expected_token="${1:-}"
  local session_file s_token tomb t_token
  session_file="$(lock_session_file)"
  [[ -f "$session_file" ]] || return 0
  [[ -n "$expected_token" ]] || return 0
  s_token="$(grep -E "^${TOKEN_VAR}=" "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  [[ "$s_token" == "$expected_token" ]] || return 0
  tomb="${session_file}.clearing.$$.$RANDOM"
  if ! mv "$session_file" "$tomb" 2>/dev/null; then
    return 0
  fi
  t_token="$(grep -E "^${TOKEN_VAR}=" "$tomb" 2>/dev/null | head -n1 | cut -d= -f2-)"
  if [[ "$t_token" != "$expected_token" ]]; then
    if [[ ! -f "$session_file" ]]; then
      mv "$tomb" "$session_file" 2>/dev/null || rm -f "$tomb"
    else
      rm -f "$tomb"
    fi
    return 0
  fi
  rm -f "$tomb"
}

write_lock_session() {
  local token="$1"
  local session_file tmp
  session_file="$(lock_session_file)"
  mkdir -p "$(dirname "$session_file")"
  [[ ! -d "$session_file" ]] || return 1
  tmp="${session_file}.tmp.$$.$RANDOM"
  if ! cat >"${tmp}" <<EOF
${DIR_VAR}=${lock_dir}
${TOKEN_VAR}=${token}
EOF
  then
    rm -f "$tmp"
    return 1
  fi
  if ! mv "${tmp}" "${session_file}"; then
    rm -f "$tmp"
    return 1
  fi
}

clear_lock_session() {
  # Unconditional clear (tests / incomplete-lock recovery only).
  local session_file
  session_file="$(lock_session_file)"
  rm -f "${session_file}"
}

remove_incomplete_lock_dir() {
  # mkdir succeeded but meta never landed (crash mid-acquire).
  # Only remove when the directory is old enough that an in-flight write_meta is unlikely;
  # otherwise a peer that just won mkdir looks identical to a crash leftover.
  [[ -d "$lock_dir" ]] || return 1
  [[ -f "${lock_dir}/${META_FILE}" ]] && return 1
  local mtime now age
  mtime="$(stat -f %m "$lock_dir" 2>/dev/null || stat -c %Y "$lock_dir" 2>/dev/null || echo 0)"
  now="$(now_epoch)"
  age=$(( now - mtime ))
  if [[ "$age" -lt "$INCOMPLETE_SECS" ]]; then
    return 1
  fi
  local tomb="${lock_dir}.incomplete-removing.$$.$RANDOM"
  if ! mv "$lock_dir" "$tomb" 2>/dev/null; then
    return 1
  fi
  if [[ -f "${tomb}/${META_FILE}" ]]; then
    mv "$tomb" "$lock_dir" 2>/dev/null || mv "$tomb" "${lock_dir}.conflict.$$" 2>/dev/null || rm -rf "$tomb"
    return 1
  fi
  rm -rf "$tomb"
  echo "${PROG}: removed incomplete lock at ${lock_dir}" >&2
  return 0
}

install_lock() {
  # Shared acquisition body for both try_acquire call sites (fresh mkdir and
  # post-steal re-mkdir): write meta, write the session fence, re-verify, export.
  local label="$1"
  local token
  token="$(uuidgen 2>/dev/null || openssl rand -hex 16)"
  if ! write_meta "$token" "$label"; then
    # Peer claimed meta first, or dir was recycled under us; do not export a false hold.
    return 1
  fi
  if ! write_lock_session "$token"; then
    load_lock_meta || true
    steal_remove_if_unchanged "$token" "$lock_meta_started_epoch" "fence-write-failed" || true
    return 1
  fi
  # Re-read: abort if meta no longer matches our token (lost race after write).
  load_lock_meta || return 1
  if [[ "$lock_meta_token" != "$token" ]]; then
    return 1
  fi
  print_exports "$token"
  return 0
}

try_acquire() {
  local label="$1"
  mkdir -p "$(dirname "$lock_dir")"
  if mkdir "$lock_dir" 2>/dev/null; then
    install_lock "$label"
    return
  fi
  # Do not rm -rf incomplete dirs from the acquire path (TOCTOU with in-flight write_meta).
  # Operator/stale-clean removes aged incomplete dirs.
  if is_stealable_lock; then
    local reason="stale"
    local expected_token expected_epoch
    load_lock_meta || return 1
    expected_token="${lock_meta_token}"
    expected_epoch="${lock_meta_started_epoch}"
    [[ -n "$expected_token" ]] || return 1
    is_dead_holder_lock && reason="abandoned"
    if steal_remove_if_unchanged "$expected_token" "$expected_epoch" "$reason"; then
      if mkdir "$lock_dir" 2>/dev/null; then
        install_lock "$label"
        return
      fi
    fi
  fi
  return 1
}

require_label_value() {
  if [[ $# -eq 0 || -z "${1:-}" ]]; then
    echo "${PROG}: --label requires a value" >&2
    emit_outcome tool_error
    exit 3
  fi
}

cmd_acquire() {
  local label=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --label)
        shift
        require_label_value "$@"
        label="$1"
        shift
        ;;
      *)
        echo "${PROG}: unknown argument: $1" >&2
        emit_outcome tool_error
        exit 3
        ;;
    esac
  done
  require_git_repo
  if try_acquire "$label"; then
    emit_outcome pass
    exit 0
  fi
  local held_class
  held_class="$(classify_held_outcome)"
  if [[ "$held_class" == "ambiguous" ]]; then
    echo "${PROG}: blocked by a lock for ${repo_root}; holder state ambiguous (cannot adjudicate)" >&2
    status_report >&2
    emit_outcome indeterminate
    exit 2
  fi
  echo "${PROG}: held by another ${WORKFLOW_NOUN} for ${repo_root}" >&2
  status_report >&2
  emit_outcome fail
  exit 1
}

cmd_wait_acquire() {
  local label=""
  local max_wait=7200
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --label)
        shift
        require_label_value "$@"
        label="$1"
        shift
        ;;
      --max-wait)
        shift
        max_wait="${1:-}"
        shift
        ;;
      *)
        echo "${PROG}: unknown argument: $1" >&2
        emit_outcome tool_error
        exit 3
        ;;
    esac
  done
  require_git_repo
  local deadline=$(( $(now_epoch) + max_wait ))
  while true; do
    if try_acquire "$label"; then
      emit_outcome pass
      exit 0
    fi
    if [[ "$(now_epoch)" -ge "$deadline" ]]; then
      local held_class
      held_class="$(classify_held_outcome)"
      if [[ "$held_class" == "ambiguous" ]]; then
        echo "${PROG}: timed out after ${max_wait}s waiting for lock on ${repo_root}; holder state ambiguous (cannot adjudicate)" >&2
        status_report >&2
        emit_outcome indeterminate
        exit 2
      fi
      echo "${PROG}: timed out after ${max_wait}s waiting for lock on ${repo_root}" >&2
      status_report >&2
      emit_outcome fail
      exit 1
    fi
    echo "${PROG}: waiting for lock on ${repo_root} (poll ${POLL_SECS}s)..." >&2
    status_report >&2
    sleep "$POLL_SECS"
  done
}

cmd_release() {
  local dir="${LOCK_DIR_ENV:-}"
  local token="${LOCK_TOKEN_ENV:-}"
  # Same confused-deputy guard as release-repo: never adopt the shared session file.
  if [[ -z "$dir" || -z "$token" ]]; then
    echo "${PROG}: release requires ${DIR_VAR} and ${TOKEN_VAR} in env" >&2
    echo "${PROG}: re-export them from your acquire Step 0 output; refusing shared session load" >&2
    emit_outcome tool_error
    exit 3
  fi
  local meta="${dir}/${META_FILE}"
  if [[ ! -d "$dir" ]]; then
    echo "${PROG}: lock already released (${dir})" >&2
    require_git_repo 2>/dev/null && clear_lock_session_if_token "$token" || true
    emit_outcome pass
    exit 0
  fi
  if [[ ! -f "$meta" ]]; then
    echo "${PROG}: lock directory missing metadata; refusing unsafe release" >&2
    emit_outcome tool_error
    exit 3
  fi
  local meta_token meta_epoch released_for
  meta_token="$(meta_field "$meta" lock_token)"
  meta_epoch="$(meta_field "$meta" started_epoch)"
  if [[ "$token" != "$meta_token" ]]; then
    echo "${PROG}: token mismatch; not releasing ${dir}" >&2
    emit_outcome fail
    exit 1
  fi
  released_for="$(meta_field "$meta" repo_root)"
  released_for="${released_for:-$dir}"
  # CAS remove: refuse if another waiter replaced the lock after our token check.
  lock_dir="$dir"
  if ! steal_remove_if_unchanged "$meta_token" "$meta_epoch" "released"; then
    echo "${PROG}: lock changed under us; not releasing ${dir}" >&2
    emit_outcome fail
    exit 1
  fi
  require_git_repo 2>/dev/null && clear_lock_session_if_token "$token" || true
  echo "${PROG}: released lock for ${released_for}"
  emit_outcome pass
}

cmd_release_repo() {
  require_git_repo
  # Confused-deputy guard: do not adopt the shared session file when env is empty.
  # After stale-clean + peer acquire, session names the new holder; sourcing it would
  # let an overthrown chat CAS-release the live lock. Callers must reuse the
  # ${ENV_PREFIX}_* exports from their acquire output (same shell or re-exported).
  if [[ -z "$LOCK_DIR_ENV" || -z "$LOCK_TOKEN_ENV" ]]; then
    echo "${PROG}: release-repo requires ${DIR_VAR} and ${TOKEN_VAR} in env" >&2
    echo "${PROG}: re-export them from your acquire Step 0 output; refusing shared session load" >&2
    if [[ -f "$(lock_session_file)" ]]; then
      echo "${PROG}: hint: session file exists for status/fence only; not used for release-repo" >&2
    fi
    emit_outcome tool_error
    exit 3
  fi
  cmd_release
}

status_report() {
  # The status evidence body, without the outcome line: the acquire and
  # stale-clean refusal paths reuse it as holder evidence, and only the
  # status subcommand appends the contract's final OUTCOME line.
  require_git_repo
  if [[ ! -d "$lock_dir" ]]; then
    echo "${PROG}: free (${repo_root})"
    return 0
  fi
  local meta="${lock_dir}/${META_FILE}"
  if [[ ! -f "$meta" ]]; then
    echo "${PROG}: held (${lock_dir}); metadata missing"
    return 0
  fi
  load_lock_meta
  local age
  age="$(lock_age_secs)"
  echo "${PROG}: held (${repo_root})"
  echo "  lock_dir: ${lock_dir}"
  echo "  label: ${lock_meta_label:-}"
  echo "  started_at: ${lock_meta_started_at:-unknown}"
  echo "  age_secs: ${age}"
  echo "  hostname: ${lock_meta_hostname:-unknown}"
  if [[ -n "${lock_meta_holder_pid:-}" ]]; then
    echo "  holder_pid: ${lock_meta_holder_pid}"
    local state
    state="$(holder_state)"
    echo "  holder_alive: ${state}"
    if [[ "$state" == "dead" ]]; then
      if session_fence_matches_lock; then
        echo "  session_fence: yes (PID dead; verified-dead recovery ignores the fence)"
      fi
    fi
  else
    echo "  holder_pid: unknown (pre-PID lock)"
  fi
  if is_stealable_lock; then
    if is_stale_lock; then
      echo "  stale: yes (>= ${STALE_SECS}s)"
    elif is_dead_holder_lock; then
      if session_fence_matches_lock; then
        echo "  abandoned: yes (holder PID not running; matching session fence is ignored)"
      else
        echo "  abandoned: yes (holder PID not running and no session fence)"
      fi
    fi
    echo "  stealable: yes"
  else
    echo "  stealable: no"
    if session_fence_matches_lock && is_stale_lock; then
      echo "  note: session-fenced and stale with no verified-dead holder; use stale-clean"
    fi
  fi
}

cmd_status() {
  status_report
  emit_outcome pass
}

cmd_stale_clean() {
  require_git_repo
  if [[ -d "$lock_dir" ]] && [[ ! -f "${lock_dir}/${META_FILE}" ]]; then
    if ! remove_incomplete_lock_dir; then
      echo "${PROG}: incomplete lock is too new; refusing unsafe cleanup" >&2
      emit_outcome indeterminate
      exit 2
    fi
    clear_lock_session_if_token "${lock_meta_token:-}" || true
    echo "${PROG}: free (${repo_root})"
    emit_outcome pass
    return 0
  fi
  # Operator escape: allow removing a fenced lock only when it is also stale.
  local allow_fenced_stale=0
  local allow_operator_stale=0
  if session_fence_matches_lock && is_stale_lock; then
    allow_fenced_stale=1
  fi
  if [[ -d "$lock_dir" ]] && is_stale_lock && ! session_fence_matches_lock; then
    allow_operator_stale=1
  fi
  if [[ -d "$lock_dir" ]] && { is_stealable_lock || [[ "$allow_fenced_stale" -eq 1 ]] || [[ "$allow_operator_stale" -eq 1 ]]; }; then
    local reason="stale"
    local expected_token expected_epoch
    load_lock_meta || { echo "${PROG}: lock metadata unreadable; refusing cleanup (${lock_dir})" >&2; emit_outcome tool_error; exit 3; }
    expected_token="${lock_meta_token}"
    expected_epoch="${lock_meta_started_epoch}"
    if [[ "$allow_fenced_stale" -eq 1 ]]; then
      reason="stale-fenced"
    elif [[ "$allow_operator_stale" -eq 1 ]]; then
      local operator_holder_state
      operator_holder_state="$(holder_state)"
      if [[ "$operator_holder_state" != "dead" ]]; then
        reason="operator-stale"
        # Merge mode only: warn before evicting a lock whose holder process
        # is still alive (done-mode selftest output stays byte-identical).
        if [[ "$LOCK_MODE" == "merge" ]]; then
          echo "${PROG}: WARNING: holder_state=${operator_holder_state}; holder process alive; evicting anyway" >&2
        fi
      fi
    elif is_dead_holder_lock; then
      reason="abandoned"
    fi
    if ! steal_remove_if_unchanged "$expected_token" "$expected_epoch" "$reason"; then
      echo "${PROG}: lock changed under us; still active (${repo_root})" >&2
      status_report
      emit_outcome fail
      exit 1
    fi
    clear_lock_session_if_token "$expected_token" || true
    echo "${PROG}: free (${repo_root})"
    emit_outcome pass
  elif [[ -d "$lock_dir" ]]; then
    echo "${PROG}: still active (${repo_root})"
    status_report
    emit_outcome fail
    exit 1
  else
    echo "${PROG}: free (${repo_root})"
    emit_outcome pass
  fi
}

cmd_selftest() {
  local script_path
  script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  local tmp root
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/done-lock-selftest.XXXXXX")"
  root="${tmp}/repo"
  mkdir -p "$root/.ai-playbook"
  (
    cd "$root"
    git init -q
    git -c user.email=t@t -c user.name=t commit --allow-empty -qm init
  )
  local fail=0
  local lock_root="${tmp}/locks"
  mkdir -p "$lock_root"

  run() {
    DONE_LOCK_ROOT="$lock_root" \
      DONE_LOCK_POLL_SECS="${DONE_LOCK_POLL_SECS:-30}" \
      DONE_LOCK_STALE_SECS="${DONE_LOCK_STALE_SECS:-1800}" \
      DONE_LOCK_DEAD_HOLDER_GRACE_SECS="${DONE_LOCK_DEAD_HOLDER_GRACE_SECS:-5}" \
      DONE_LOCK_HOLDER_PID="${DONE_LOCK_HOLDER_PID-}" \
      DONE_LOCK_DIR="${DONE_LOCK_DIR-}" \
      DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN-}" \
      bash "$script_path" "$@"
  }

  local mlock_root="${tmp}/merge-locks"
  mkdir -p "$mlock_root"

  mrun() {
    MERGE_LOCK_ROOT="$mlock_root" \
      MERGE_LOCK_POLL_SECS="${MERGE_LOCK_POLL_SECS:-30}" \
      MERGE_LOCK_STALE_SECS="${MERGE_LOCK_STALE_SECS:-600}" \
      MERGE_LOCK_DEAD_HOLDER_GRACE_SECS="${MERGE_LOCK_DEAD_HOLDER_GRACE_SECS:-5}" \
      MERGE_LOCK_HOLDER_PID="${MERGE_LOCK_HOLDER_PID-}" \
      MERGE_LOCK_DIR="${MERGE_LOCK_DIR-}" \
      MERGE_LOCK_TOKEN="${MERGE_LOCK_TOKEN-}" \
      bash "$script_path" "$@"
  }

  # 1) A verified-dead holder is auto-reclaimed even when its session fence remains
  (
    cd "$root"
    eval "$(run acquire --label fence)"
  )
  if ! (
    cd "$root"
    [[ -f .ai-playbook/done-lock.session ]]
    eval "$(DONE_LOCK_DEAD_HOLDER_GRACE_SECS=0 run acquire --label steal)"
    run release-repo
  ); then
    echo "selftest FAIL: dead fenced holder was not auto-reclaimed" >&2
    fail=1
  else
    echo "selftest OK: dead fenced holder auto-reclaimed"
  fi

  # 2) A stale live holder with a session fence remains protected; stale-clean
  # remains the explicit operator escape.
  if ! (
    cd "$root"
    sleep 120 &
    holder_pid=$!
    trap 'kill "$holder_pid" 2>/dev/null || true' EXIT
    eval "$(DONE_LOCK_HOLDER_PID="$holder_pid" run acquire --label stale-fence)"
    if DONE_LOCK_STALE_SECS=0 run acquire --label stale-steal 2>/dev/null; then
      echo "selftest FAIL: stale TTL auto-stole a fenced live lock" >&2
      exit 1
    fi
    if ! DONE_LOCK_STALE_SECS=0 run stale-clean; then
      echo "selftest FAIL: stale-clean should remove fenced stale lock" >&2
      exit 1
    fi
  ); then
    echo "selftest FAIL: fenced live lock remains protected" >&2
    fail=1
  else
    echo "selftest OK: fenced live lock remains protected; stale-clean removes it"
  fi

  # 3) Fresh acquire after clean (release in same shell so env is present)
  if ! (
    cd "$root"
    eval "$(run acquire --label after-clean)"
    run release-repo
  ); then
    echo "selftest FAIL: acquire/release after stale-clean" >&2
    fail=1
  else
    echo "selftest OK: acquire after stale-clean"
  fi

  # 4) Incomplete lock dir: acquire must not rm it; stale-clean recovers after age
  (
    cd "$root"
    repo_id="$(printf '%s' "$(git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
    mkdir -p "${lock_root}/${repo_id}"
    touch -t 202001010000 "${lock_root}/${repo_id}" 2>/dev/null || \
      touch -d '2020-01-01' "${lock_root}/${repo_id}" 2>/dev/null || true
  )
  if (cd "$root" && run acquire --label should-block 2>/dev/null); then
    echo "selftest FAIL: acquire must not auto-remove incomplete lock_dir" >&2
    fail=1
  else
    echo "selftest OK: acquire leaves incomplete lock_dir alone"
  fi
  if ! (
    cd "$root"
    run stale-clean
    eval "$(run acquire --label after-incomplete-clean)"
    run release-repo
  ); then
    echo "selftest FAIL: stale-clean should recover incomplete lock_dir" >&2
    fail=1
  else
    echo "selftest OK: stale-clean recovers incomplete lock_dir"
  fi

  # 5) Mismatched release must not clear a live peer session fence
  (
    cd "$root"
    eval "$(run acquire --label holder-b)"
    export HELD_DIR="$DONE_LOCK_DIR" HELD_TOKEN="$DONE_LOCK_TOKEN"
    DONE_LOCK_DIR="$HELD_DIR" DONE_LOCK_TOKEN="not-the-holder-token" run release 2>/dev/null || true
    if [[ ! -f .ai-playbook/done-lock.session ]]; then
      echo "selftest FAIL: mismatched release cleared peer session" >&2
      exit 1
    fi
    DONE_LOCK_DIR="$HELD_DIR" DONE_LOCK_TOKEN="$HELD_TOKEN" run release-repo
  ) || fail=1
  if [[ "$fail" -eq 0 ]]; then
    echo "selftest OK: mismatched release leaves peer session"
  fi

  # 5b) bare release without env also refuses session load
  (
    cd "$root"
    eval "$(run acquire --label release-env)"
  )
  if (cd "$root" && unset DONE_LOCK_DIR DONE_LOCK_TOKEN && run release 2>/dev/null); then
    echo "selftest FAIL: release without env adopted session" >&2
    fail=1
  else
    echo "selftest OK: release without env refuses session load"
  fi
  (
    cd "$root"
    eval "$(grep -E '^DONE_LOCK_' .ai-playbook/done-lock.session | sed 's/^/export /')"
    run release-repo
  ) || true

  # 6) Abandoned steal: dead PID + no matching session => acquire succeeds
  (
    cd "$root"
    eval "$(run acquire --label abandon-setup)"
  )
  rm -f "$root/.ai-playbook/done-lock.session"
  if ! (
    cd "$root"
    eval "$(DONE_LOCK_DEAD_HOLDER_GRACE_SECS=0 run acquire --label abandon-steal)"
    run release-repo
  ); then
    echo "selftest FAIL: abandoned steal (no session) should succeed" >&2
    fail=1
  else
    echo "selftest OK: abandoned steal without session fence"
  fi

  # 7) release-repo without env refuses shared session (confused-deputy guard)
  (
    cd "$root"
    eval "$(run acquire --label deputy)"
  )
  if (cd "$root" && unset DONE_LOCK_DIR DONE_LOCK_TOKEN && run release-repo 2>/dev/null); then
    echo "selftest FAIL: release-repo without env adopted session" >&2
    fail=1
  else
    echo "selftest OK: release-repo without env refuses session load"
  fi
  (
    cd "$root"
    eval "$(grep -E '^DONE_LOCK_' .ai-playbook/done-lock.session | sed 's/^/export /')"
    run release-repo
  ) || true

  repo_id="$(printf '%s' "$(cd "$root" && git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
  test_lock_dir="${lock_root}/${repo_id}"
  set_meta_field() {
    local key="$1"
    local value="$2"
    local meta="${test_lock_dir}/${META_FILE}"
    sed -i.bak -e "s/^${key}=.*/${key}=${value}/" "$meta"
    rm -f "${meta}.bak"
  }

  # 8) A stale live holder without a fence is blocked; only an explicit
  # stale-clean may remove it.
  if ! (
    cd "$root"
    sleep 120 &
    holder_pid=$!
    trap 'kill "$holder_pid" 2>/dev/null || true' EXIT
    eval "$(DONE_LOCK_HOLDER_PID="$holder_pid" run acquire --label live-stale)"
    rm -f .ai-playbook/done-lock.session
    set_meta_field started_epoch 1
    if DONE_LOCK_STALE_SECS=0 run acquire --label must-block-live 2>/dev/null; then
      echo "selftest FAIL: stale live holder was auto-stolen" >&2
      exit 1
    fi
    DONE_LOCK_STALE_SECS=0 run stale-clean
  ); then
    echo "selftest FAIL: live-holder stale recovery rule" >&2
    fail=1
  else
    echo "selftest OK: live holder blocks auto-steal; stale-clean is explicit"
  fi

  # 9) A dead holder is blocked until the grace period passes, then can be
  # recovered without a session fence.
  if ! (
    cd "$root"
    eval "$(DONE_LOCK_HOLDER_PID=999999 DONE_LOCK_DEAD_HOLDER_GRACE_SECS=60 run acquire --label dead-grace)"
    rm -f .ai-playbook/done-lock.session
    if DONE_LOCK_DEAD_HOLDER_GRACE_SECS=60 run acquire --label before-grace 2>/dev/null; then
      echo "selftest FAIL: dead holder bypassed grace period" >&2
      exit 1
    fi
    set_meta_field started_epoch 1
    eval "$(DONE_LOCK_DEAD_HOLDER_GRACE_SECS=60 run acquire --label after-grace)"
    run release-repo
  ); then
    echo "selftest FAIL: dead-holder grace rule" >&2
    fail=1
  else
    echo "selftest OK: dead-holder recovery waits for grace"
  fi

  # 10) Ambiguous PID identity is non-stealable, and an old generation cannot
  # release the replacement generation after takeover.
  if ! (
    cd "$root"
    sleep 120 &
    holder_pid=$!
    trap 'kill "$holder_pid" 2>/dev/null || true' EXIT
    eval "$(DONE_LOCK_HOLDER_PID="$holder_pid" run acquire --label ambiguous)"
    old_dir="$DONE_LOCK_DIR"
    old_token="$DONE_LOCK_TOKEN"
    rm -f .ai-playbook/done-lock.session
    set_meta_field holder_identity definitely-not-the-live-process
    set_meta_field started_epoch 1
    if run acquire --label ambiguous-takeover 2>/dev/null; then
      echo "selftest FAIL: ambiguous holder identity was stolen" >&2
      exit 1
    fi
    DONE_LOCK_DIR="$old_dir" DONE_LOCK_TOKEN="$old_token" run release 2>/dev/null || true
    rm -f .ai-playbook/done-lock.session
    eval "$(DONE_LOCK_HOLDER_PID=999999 run acquire --label generation-old)"
    old_dir="$DONE_LOCK_DIR"
    old_token="$DONE_LOCK_TOKEN"
    rm -f .ai-playbook/done-lock.session
    set_meta_field started_epoch 1
    eval "$(run acquire --label generation-new)"
    new_token="$DONE_LOCK_TOKEN"
    if [[ "$old_token" == "$new_token" ]]; then
      echo "selftest FAIL: takeover reused lock generation" >&2
      exit 1
    fi
    if DONE_LOCK_DIR="$old_dir" DONE_LOCK_TOKEN="$old_token" run release 2>/dev/null; then
      echo "selftest FAIL: old holder mutated replacement generation" >&2
      exit 1
    fi
    run release-repo
  ); then
    echo "selftest FAIL: generation and identity race witnesses" >&2
    fail=1
  else
    echo "selftest OK: ambiguous identity and old-generation mutation blocked"
  fi

  # 11) A fence write failure never leaves an apparently held lock behind.
  if ! (
    cd "$root"
    mkdir -p .ai-playbook/done-lock.session
    if run acquire --label fence-write-failure 2>/dev/null; then
      echo "selftest FAIL: fence-write failure reported success" >&2
      exit 1
    fi
    [[ ! -d "$test_lock_dir" ]]
    rmdir .ai-playbook/done-lock.session
  ); then
    echo "selftest FAIL: fence-write failure cleanup" >&2
    fail=1
  else
    echo "selftest OK: fence-write failure cleans the generation"
  fi

  # 12) A truncated meta.env (crash mid-write) is age-unknown: stale-clean
  # must refuse even with STALE_SECS=0 rather than remove a possibly-live lock.
  (
    cd "$root"
    rm -f .ai-playbook/done-lock.session
    mkdir -p "$test_lock_dir"
    printf 'lock_token=truncated\nlabel=partial' > "${test_lock_dir}/${META_FILE}"
    if DONE_LOCK_STALE_SECS=0 run stale-clean 2>/dev/null; then
      echo "selftest FAIL: stale-clean removed a truncated-meta lock" >&2
      exit 1
    fi
    [[ -d "$test_lock_dir" ]] || { echo "selftest FAIL: truncated-meta lock was deleted" >&2; exit 1; }
    rm -rf "$test_lock_dir"
  ) || fail=1
  if [[ "$fail" -eq 0 ]]; then
    echo "selftest OK: truncated meta refuses stale-clean"
  fi

  # 13) A newline in --label cannot forge meta.env identity fields.
  if (cd "$root" && run acquire --label "$(printf 'inj\nholder_pid=999999')" 2>/dev/null); then
    echo "selftest FAIL: newline label was accepted" >&2
    fail=1
  else
    echo "selftest OK: newline label rejected"
  fi

  # 14) --label validation: missing value and empty label are rejected with a
  # specific error by both argument-parsing stances (acquire, wait-acquire).
  local err
  for cmd in acquire wait-acquire; do
    err="$(cd "$root" && run "$cmd" --label 2>&1 >/dev/null || true)"
    if [[ "$err" != *"--label requires a value"* ]]; then
      echo "selftest FAIL: ${cmd} missing --label value error not specific: ${err}" >&2
      fail=1
    elif [[ "$err" != *"done-lock: --label requires a value"* ]]; then
      echo "selftest FAIL: ${cmd} missing --label value error mismatch" >&2
      fail=1
    fi
    err="$(cd "$root" && run "$cmd" --label "" 2>&1 >/dev/null || true)"
    if [[ "$err" != *"done-lock: --label requires a value"* ]]; then
      echo "selftest FAIL: ${cmd} empty label not rejected: ${err}" >&2
      fail=1
    fi
  done
  if [[ "$fail" -eq 0 ]]; then
    echo "selftest OK: --label missing value and empty label rejected"
  fi

  # 15) Token-only session shape: acquire writes exactly the two lock identity
  # keys, and the release path consumes that token-only fence end to end.
  if ! (
    cd "$root"
    rm -f .ai-playbook/done-lock.session
    # Case 13 leaves a meta-less lock dir behind (label rejected after mkdir); clear it.
    rm -rf "$test_lock_dir"
    eval "$(run acquire --label token-only-shape)"
    key_count="$(grep -c '^DONE_LOCK_' .ai-playbook/done-lock.session || true)"
    if [[ "$key_count" -ne 2 ]]; then
      echo "selftest FAIL: session file expected 2 identity keys, got ${key_count}" >&2
      exit 1
    fi
    # The meta file must not carry any dead lock-generation key: nothing in
    # the script reads one, and writing an unread identity field invites
    # drift between the fence and its record.
    if grep -q '^generation=' "${DONE_LOCK_DIR}/${META_FILE}"; then
      echo "selftest FAIL: meta file carries a dead generation key" >&2
      exit 1
    fi
    run release-repo
    [[ ! -f .ai-playbook/done-lock.session ]]
  ); then
    echo "selftest FAIL: token-only session shape release" >&2
    fail=1
  else
    echo "selftest OK: token-only session shape consumed by release"
  fi

  # 16) No-sourcing invariant: the script must never source a session file
  # (repo-controlled content; sourcing would be arbitrary code execution).
  local sourcing_hits
  sourcing_hits="$(grep -nE '(^|[[:space:];&])(source|\.)[[:space:]]+[^|]*done-lock\.session' "$script_path" || true)"
  if [[ -n "$sourcing_hits" ]]; then
    echo "selftest FAIL: script sources a session file: ${sourcing_hits}" >&2
    fail=1
  else
    echo "selftest OK: no source command reads session files"
  fi

  # 17) One-shot handoff: an acquire in an exiting subshell (no trap installed,
  # holder PID pinned to a live process) keeps the lock held across that exit;
  # a second acquire from a fresh process is blocked; a token-fenced release
  # re-exported from the first acquire's stdout succeeds in a later process.
  (
    cd "$root"
    sleep 120 &
    handoff_holder=$!
    handoff_dir_file="${tmp}/handoff-dir"
    handoff_token_file="${tmp}/handoff-token"
    cleanup_handoff() {
      kill "$handoff_holder" 2>/dev/null || true
      # Reap the killed job so bash prints no job-status notice on exit.
      wait "$handoff_holder" 2>/dev/null || true
      rm -f "$handoff_dir_file" "$handoff_token_file"
    }
    trap cleanup_handoff EXIT
    # One-shot acquire call: the acquiring subshell exits immediately and
    # installs no trap; only the exports from its stdout outlive it.
    (
      eval "$(DONE_LOCK_HOLDER_PID="$handoff_holder" run acquire --label one-shot)"
      printf '%s' "${DONE_LOCK_DIR:-}" > "$handoff_dir_file"
      printf '%s' "${DONE_LOCK_TOKEN:-}" > "$handoff_token_file"
    )
    if [[ ! -s "$handoff_dir_file" || ! -s "$handoff_token_file" ]]; then
      echo "selftest FAIL: one-shot acquire produced no handoff values" >&2
      exit 1
    fi
    second_rc=0
    # Zero the dead-holder grace for this probe: a dead holder would be
    # stolen (rc 0), so rc=1 here can only mean the pinned holder verified alive.
    DONE_LOCK_DEAD_HOLDER_GRACE_SECS=0 run acquire --label one-shot-second >/dev/null 2>&1 || second_rc=$?
    if [[ "$second_rc" -ne 1 ]]; then
      echo "selftest FAIL: lock did not survive the exiting one-shot subshell (rc=${second_rc}, want 1)" >&2
      exit 1
    fi
    if ! DONE_LOCK_DIR="$(cat "$handoff_dir_file")" DONE_LOCK_TOKEN="$(cat "$handoff_token_file")" run release-repo >/dev/null 2>&1; then
      echo "selftest FAIL: token-fenced release from re-exported handoff values failed" >&2
      exit 1
    fi
  ) || fail=1
  if [[ "$fail" -eq 0 ]]; then
    echo "selftest OK: one-shot handoff"
  fi

  # ---- Merge landing lock family (merge-* commands) ----

  # M1) merge_acquire_creates_lock_and_exports: a fresh merge-acquire exits 0,
  # keys a lock dir under the merge root by the repo hash, writes the
  # .ai-playbook/merge-lock.session fence in the repo, and prints the
  # MERGE_LOCK_DIR / MERGE_LOCK_TOKEN exports on stdout.
  if ! (
    cd "$root"
    merge_out="$(mrun merge-acquire --label merge-exports)"
    if [[ "$merge_out" != *"export MERGE_LOCK_DIR="* || "$merge_out" != *"export MERGE_LOCK_TOKEN="* ]]; then
      echo "selftest FAIL: merge-acquire printed no MERGE_LOCK_DIR/MERGE_LOCK_TOKEN exports" >&2
      exit 1
    fi
    merge_repo_id="$(printf '%s' "$(git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
    [[ -d "${mlock_root}/${merge_repo_id}" ]] || { echo "selftest FAIL: merge lock dir not under merge root keyed by repo hash" >&2; exit 1; }
    [[ -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: .ai-playbook/merge-lock.session missing" >&2; exit 1; }
    eval "$merge_out"
    mrun merge-release-repo >/dev/null
    [[ ! -d "${mlock_root}/${merge_repo_id}" ]] || { echo "selftest FAIL: merge-release-repo did not remove the merge lock dir" >&2; exit 1; }
  ); then
    echo "selftest FAIL: merge_acquire_creates_lock_and_exports" >&2
    fail=1
  else
    echo "selftest OK: merge-acquire creates lock, fence, and exports"
  fi

  # M2) merge_second_acquire_held: a second merge-acquire against a lock held
  # by another live holder exits 1 with the fail outcome and leaves the first
  # holder's lock intact.
  if ! (
    cd "$root"
    sleep 120 &
    merge_holder=$!
    trap 'kill "$merge_holder" 2>/dev/null || true' EXIT
    eval "$(MERGE_LOCK_HOLDER_PID="$merge_holder" mrun merge-acquire --label merge-first-holder)"
    [[ -n "${MERGE_LOCK_DIR:-}" && -n "${MERGE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: first merge-acquire produced no exports" >&2; exit 1; }
    first_dir="$MERGE_LOCK_DIR"
    first_token="$MERGE_LOCK_TOKEN"
    second_rc=0
    mrun merge-acquire --label merge-second-holder 2>"${tmp}/m2-err" || second_rc=$?
    if [[ "$second_rc" -ne 1 ]]; then
      echo "selftest FAIL: second merge-acquire rc=${second_rc}, want 1" >&2
      exit 1
    fi
    [[ "$(tail -n1 "${tmp}/m2-err")" == "OUTCOME: fail" ]] || { echo "selftest FAIL: second merge-acquire stderr does not end with OUTCOME: fail" >&2; exit 1; }
    [[ -d "$first_dir" ]] || { echo "selftest FAIL: first holder merge lock removed" >&2; exit 1; }
    first_meta_token="$(grep -E '^lock_token=' "${first_dir}/meta.env" | head -n1 | cut -d= -f2-)"
    [[ "$first_meta_token" == "$first_token" ]] || { echo "selftest FAIL: first holder merge token changed" >&2; exit 1; }
    [[ -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: first holder merge fence cleared" >&2; exit 1; }
    # Assertions done; release so later merge fixtures start from a free repo.
    mrun merge-release-repo >/dev/null
  ); then
    echo "selftest FAIL: merge_second_acquire_held" >&2
    fail=1
  else
    echo "selftest OK: second merge-acquire blocked; first holder intact"
  fi

  # M3) merge_release_token_fenced: a wrong token refuses and the lock
  # survives; the right token removes lock and fence.
  if ! (
    cd "$root"
    eval "$(mrun merge-acquire --label merge-fenced)"
    [[ -n "${MERGE_LOCK_DIR:-}" && -n "${MERGE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: merge-acquire produced no exports" >&2; exit 1; }
    held_dir="$MERGE_LOCK_DIR"
    held_token="$MERGE_LOCK_TOKEN"
    wrong_rc=0
    MERGE_LOCK_DIR="$held_dir" MERGE_LOCK_TOKEN="not-the-merge-token" mrun merge-release 2>/dev/null || wrong_rc=$?
    if [[ "$wrong_rc" -eq 0 ]]; then
      echo "selftest FAIL: merge-release accepted a wrong token" >&2
      exit 1
    fi
    [[ -d "$held_dir" ]] || { echo "selftest FAIL: wrong-token merge-release removed the lock" >&2; exit 1; }
    [[ -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: wrong-token merge-release cleared the fence" >&2; exit 1; }
    if ! MERGE_LOCK_DIR="$held_dir" MERGE_LOCK_TOKEN="$held_token" mrun merge-release-repo >/dev/null 2>&1; then
      echo "selftest FAIL: token-fenced merge-release-repo failed" >&2
      exit 1
    fi
    [[ ! -d "$held_dir" ]] || { echo "selftest FAIL: merge lock survived the correct release" >&2; exit 1; }
    [[ ! -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: merge fence survived the correct release" >&2; exit 1; }
  ); then
    echo "selftest FAIL: merge_release_token_fenced" >&2
    fail=1
  else
    echo "selftest OK: merge-release token-fenced; right token removes lock and fence"
  fi

  # M3b) merge-release-repo without env refuses the shared session fence.
  (
    cd "$root"
    eval "$(mrun merge-acquire --label merge-release-env-guard)"
  ) || true
  if (cd "$root" && unset MERGE_LOCK_DIR MERGE_LOCK_TOKEN && mrun merge-release-repo 2>/dev/null); then
    echo "selftest FAIL: merge-release-repo without env adopted session" >&2
    fail=1
  else
    echo "selftest OK: merge-release-repo without env refuses session load"
  fi
  (
    cd "$root"
    eval "$(grep -E '^MERGE_LOCK_' .ai-playbook/merge-lock.session | sed 's/^/export /')"
    mrun merge-release-repo >/dev/null
  ) || true

  # M4) merge_and_done_locks_independent: a held merge lock never blocks the
  # done lock and a held done lock never blocks merge-acquire.
  if ! (
    cd "$root"
    eval "$(mrun merge-acquire --label indep-merge-hold)"
    [[ -n "${MERGE_LOCK_DIR:-}" && -n "${MERGE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: merge-acquire produced no exports" >&2; exit 1; }
    eval "$(run acquire --label indep-done-takes)"
    [[ -n "${DONE_LOCK_DIR:-}" && -n "${DONE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: done acquire produced no exports" >&2; exit 1; }
    held_merge_dir="$MERGE_LOCK_DIR"
    held_merge_token="$MERGE_LOCK_TOKEN"
    MERGE_LOCK_DIR="$held_merge_dir" MERGE_LOCK_TOKEN="$held_merge_token" mrun merge-release-repo >/dev/null
    eval "$(mrun merge-acquire --label indep-merge-takes)"
    mrun merge-release-repo >/dev/null
    run release-repo >/dev/null
  ); then
    echo "selftest FAIL: merge_and_done_locks_independent" >&2
    fail=1
  else
    echo "selftest OK: merge and done locks are independent"
  fi

  # M5) merge_status_and_stale_clean: merge-status reports the holder label;
  # with the stale threshold overridden to a tiny value, merge-stale-clean
  # removes the lock and merge-status reports free.
  if ! (
    cd "$root"
    sleep 120 &
    merge_status_holder=$!
    trap 'kill "$merge_status_holder" 2>/dev/null || true' EXIT
    eval "$(MERGE_LOCK_HOLDER_PID="$merge_status_holder" mrun merge-acquire --label merge-status-holder)"
    merge_st="$(mrun merge-status)"
    if [[ "$merge_st" != *"label: merge-status-holder"* ]]; then
      echo "selftest FAIL: merge-status missing holder label" >&2
      exit 1
    fi
    if ! MERGE_LOCK_STALE_SECS=0 mrun merge-stale-clean >/dev/null 2>&1; then
      echo "selftest FAIL: merge-stale-clean refused a stale merge lock" >&2
      exit 1
    fi
    merge_st="$(mrun merge-status)"
    if [[ "$merge_st" != *"merge-lock: free"* ]]; then
      echo "selftest FAIL: merge-status not free after merge-stale-clean" >&2
      exit 1
    fi
  ); then
    echo "selftest FAIL: merge_status_and_stale_clean" >&2
    fail=1
  else
    echo "selftest OK: merge-status holder label; merge-stale-clean frees"
  fi

  # M6) cross_worktree_mutual_exclusion (r1 F1; r2 F13/CF1): a linked worktree
  # of the fixture repo and the primary checkout key the SAME merge lock (the
  # key derives from the resolved git common dir, not --show-toplevel): a hold
  # from the worktree blocks merge-acquire from the primary (exit 1, the fail
  # outcome),
  # merge-status from the primary sees the worktree holder label, and the
  # session fence lands in the shared primary checkout. The mirror direction
  # (hold from the primary, blocked from the worktree) holds too, and a
  # GIT_DIR-exported leg (r2 CF1) acquires through the .git path spelling
  # mktemp produced (a LOGICAL symlinked path when the temp parent is a
  # symlink) and must hit the same physical lock dir. Every inner subshell's
  # status is load-bearing (r2 F13): under `if !` errexit is suppressed for
  # the whole compound, whose status is the LAST inner subshell's, so an
  # unchained inner failure is swallowed and a revert to per-worktree keying
  # would still exit 0; each inner subshell therefore chains `|| exit 1`,
  # the setup (worktree add) subshell included.
  root_merge_id="$(printf '%s' "$(cd "$root" && git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
  if ! (
    wt="${tmp}/linked-wt"
    (
      cd "$root" || exit 1
      git worktree add -b wt-branch "$wt" >/dev/null 2>&1 || exit 1
    ) || exit 1
    (
      cd "$wt" || exit 1
      sleep 120 &
      wt_holder=$!
      trap 'kill "$wt_holder" 2>/dev/null || true' EXIT
      eval "$(MERGE_LOCK_HOLDER_PID="$wt_holder" mrun merge-acquire --label wt-holder)"
      [[ -n "${MERGE_LOCK_DIR:-}" && -n "${MERGE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: worktree merge-acquire produced no exports" >&2; exit 1; }
      [[ "$MERGE_LOCK_DIR" == "${mlock_root}/${root_merge_id}" ]] || { echo "selftest FAIL: worktree merge lock not keyed by the shared repo root (${MERGE_LOCK_DIR})" >&2; exit 1; }
      primary_rc=0
      (cd "$root" && MERGE_LOCK_DIR= MERGE_LOCK_TOKEN= mrun merge-acquire --label primary-blocked 2>"${tmp}/m6-primary-err") || primary_rc=$?
      [[ "$primary_rc" -eq 1 ]] || { echo "selftest FAIL: primary merge-acquire rc=${primary_rc} over a worktree hold, want 1" >&2; exit 1; }
      [[ "$(tail -n1 "${tmp}/m6-primary-err")" == "OUTCOME: fail" ]] || { echo "selftest FAIL: primary merge-acquire stderr does not end with OUTCOME: fail" >&2; exit 1; }
      primary_status="$(cd "$root" && mrun merge-status)"
      [[ "$primary_status" == *"label: wt-holder"* ]] || { echo "selftest FAIL: primary merge-status does not see the worktree holder: ${primary_status}" >&2; exit 1; }
      [[ -f "$root/.ai-playbook/merge-lock.session" ]] || { echo "selftest FAIL: merge fence did not land in the shared primary checkout" >&2; exit 1; }
      mrun merge-release-repo >/dev/null
    ) || exit 1
    (
      cd "$root" || exit 1
      sleep 120 &
      p_holder=$!
      trap 'kill "$p_holder" 2>/dev/null || true' EXIT
      eval "$(MERGE_LOCK_HOLDER_PID="$p_holder" mrun merge-acquire --label primary-holder)"
      wt_rc=0
      (cd "$wt" && MERGE_LOCK_DIR= MERGE_LOCK_TOKEN= mrun merge-acquire --label wt-blocked 2>"${tmp}/m6-wt-err") || wt_rc=$?
      [[ "$wt_rc" -eq 1 ]] || { echo "selftest FAIL: worktree merge-acquire rc=${wt_rc} over a primary hold, want 1" >&2; exit 1; }
      [[ "$(tail -n1 "${tmp}/m6-wt-err")" == "OUTCOME: fail" ]] || { echo "selftest FAIL: worktree merge-acquire stderr does not end with OUTCOME: fail" >&2; exit 1; }
      mrun merge-release-repo >/dev/null
    ) || exit 1
    (
      # GIT_DIR-exported leg (r2 CF1): the same repo addressed only through
      # the logical .git spelling of the shared checkout; the acquire must
      # resolve the common dir (here an absolute but possibly logical path,
      # which is exactly the branch the unconditional physicalization covers)
      # to the same physical lock dir a plain in-checkout acquire keys.
      cd "$root" || exit 1
      sleep 120 &
      g_holder=$!
      trap 'kill "$g_holder" 2>/dev/null || true' EXIT
      eval "$(MERGE_LOCK_HOLDER_PID="$g_holder" GIT_DIR="${root}/.git" mrun merge-acquire --label gitdir-holder)"
      [[ -n "${MERGE_LOCK_DIR:-}" && -n "${MERGE_LOCK_TOKEN:-}" ]] || { echo "selftest FAIL: GIT_DIR-exported merge-acquire produced no exports" >&2; exit 1; }
      [[ "$MERGE_LOCK_DIR" == "${mlock_root}/${root_merge_id}" ]] || { echo "selftest FAIL: GIT_DIR-exported acquire keyed ${MERGE_LOCK_DIR}, want ${mlock_root}/${root_merge_id}" >&2; exit 1; }
      mrun merge-release-repo >/dev/null
    ) || exit 1
  ); then
    echo "selftest FAIL: cross_worktree_mutual_exclusion" >&2
    fail=1
  else
    echo "selftest OK: cross-worktree holds share one merge lock"
  fi

  # M7) operator_stale_clean_warns_on_live_holder (r1 F11): merge-stale-clean
  # on a stale lock whose holder process is verified alive prints the
  # alive-holder warning (with the holder state) before the operator eviction.
  if ! (
    cd "$root"
    sleep 120 &
    evict_holder=$!
    trap 'kill "$evict_holder" 2>/dev/null || true' EXIT
    eval "$(MERGE_LOCK_HOLDER_PID="$evict_holder" mrun merge-acquire --label live-operator)"
    rm -f .ai-playbook/merge-lock.session
    evict_err="$(MERGE_LOCK_STALE_SECS=0 mrun merge-stale-clean 2>&1 1>/dev/null)"
    case "$evict_err" in
      *"holder process alive; evicting anyway"*) ;;
      *) echo "selftest FAIL: live-holder operator eviction printed no alive-holder warning: ${evict_err}" >&2; exit 1 ;;
    esac
    [[ ! -d "${mlock_root}/${root_merge_id}" ]] || { echo "selftest FAIL: operator stale-clean did not remove the live holder's lock" >&2; exit 1; }
  ); then
    echo "selftest FAIL: operator_stale_clean_warns_on_live_holder" >&2
    fail=1
  else
    echo "selftest OK: operator stale-clean warns before evicting a live holder"
  fi

  # M8) merge_wait_acquire_releases (r1 F7): merge-wait-acquire with a tiny
  # poll interval stays blocked while the lock is held, then acquires with
  # exit 0 and the exports once the holder releases; the waiter's own
  # token-fenced release then removes lock and fence.
  if ! (
    cd "$root"
    sleep 120 &
    wa_holder=$!
    cleanup_wa() { kill "$wa_holder" 2>/dev/null || true; }
    trap cleanup_wa EXIT
    eval "$(MERGE_LOCK_HOLDER_PID="$wa_holder" mrun merge-acquire --label wa-blocker)"
    (
      cd "$root"
      MERGE_LOCK_DIR= MERGE_LOCK_TOKEN= MERGE_LOCK_POLL_SECS=1 \
        mrun merge-wait-acquire --label wa-waiter --max-wait 15 >"${tmp}/wa-out" 2>/dev/null
    ) &
    waiter=$!
    sleep 2
    # Mid-hold observation (r2 T15a): before the holder releases, the waiter
    # must still be blocked -- it has produced nothing on stdout (the exports
    # print only at acquisition) and the lock dir is still present. Without
    # this observation the release leg cannot prove a blocked-to-acquired
    # transition; an early-acquiring lock would look identical to a waiter
    # that waited.
    [[ -d "${mlock_root}/${root_merge_id}" ]] || { echo "selftest FAIL: merge lock dir vanished while the holder still holds it (pre-release)" >&2; exit 1; }
    [[ ! -s "${tmp}/wa-out" ]] || { echo "selftest FAIL: waiter produced output before the holder released (no mid-hold block)" >&2; exit 1; }
    mrun merge-release-repo >/dev/null
    wait "$waiter" || { echo "selftest FAIL: merge-wait-acquire did not acquire after release" >&2; exit 1; }
    wa_out="$(cat "${tmp}/wa-out")"
    case "$wa_out" in
      *"export MERGE_LOCK_DIR="*"export MERGE_LOCK_TOKEN="*) ;;
      *) echo "selftest FAIL: merge-wait-acquire printed no exports on success" >&2; exit 1 ;;
    esac
    eval "$wa_out"
    mrun merge-release-repo >/dev/null
    [[ ! -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: fence survived the waiter's release" >&2; exit 1; }
  ); then
    echo "selftest FAIL: merge_wait_acquire_releases" >&2
    fail=1
  else
    echo "selftest OK: merge-wait-acquire acquires after release"
  fi

  # M9) merge_wait_acquire_zero_wait_times_out (r1 F7): --max-wait 0 against
  # a held lock exits 1 immediately with the fail outcome and prints no
  # exports on stdout.
  if ! (
    cd "$root"
    sleep 120 &
    m0_holder=$!
    trap 'kill "$m0_holder" 2>/dev/null || true' EXIT
    eval "$(MERGE_LOCK_HOLDER_PID="$m0_holder" mrun merge-acquire --label m0-blocker)"
    m0_rc=0
    m0_out="$(MERGE_LOCK_DIR= MERGE_LOCK_TOKEN= mrun merge-wait-acquire --label m0-waiter --max-wait 0 2>"${tmp}/m0-err")" || m0_rc=$?
    [[ "$m0_rc" -eq 1 ]] || { echo "selftest FAIL: merge-wait-acquire --max-wait 0 rc=${m0_rc}, want 1" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/m0-err")" == "OUTCOME: fail" ]] || { echo "selftest FAIL: max-wait-0 exhaustion stderr does not end with OUTCOME: fail" >&2; exit 1; }
    [[ -z "$m0_out" ]] || { echo "selftest FAIL: merge-wait-acquire printed exports on timeout" >&2; exit 1; }
    mrun merge-release-repo >/dev/null
  ); then
    echo "selftest FAIL: merge_wait_acquire_zero_wait_times_out" >&2
    fail=1
  else
    echo "selftest OK: merge-wait-acquire --max-wait 0 times out with OUTCOME: fail"
  fi

  # M10) merge_session_carries_only_merge_lock_keys (origin 6): a fresh
  # merge-acquire writes a session fence carrying exactly the two MERGE_LOCK_*
  # identity keys and nothing else. A mis-parameterized writer emitting
  # DONE_LOCK_* keys into the merge session would still work end to end (the
  # release and steal paths match only the MERGE_LOCK_ prefix), so the shape
  # is pinned here -- done fixture 15's shape check, merge-mode keys.
  if ! (
    cd "$root"
    eval "$(mrun merge-acquire --label merge-session-shape)"
    [[ -f .ai-playbook/merge-lock.session ]] || { echo "selftest FAIL: merge session file missing after merge-acquire" >&2; exit 1; }
    key_line_count="$(grep -cE '^[A-Z_]+=' .ai-playbook/merge-lock.session || true)"
    [[ "$key_line_count" -eq 2 ]] || { echo "selftest FAIL: merge session expected 2 key lines, got ${key_line_count}" >&2; exit 1; }
    merge_key_count="$(grep -c '^MERGE_LOCK_' .ai-playbook/merge-lock.session || true)"
    [[ "$merge_key_count" -eq 2 ]] || { echo "selftest FAIL: merge session expected 2 MERGE_LOCK_ keys, got ${merge_key_count}" >&2; exit 1; }
    if grep -q '^DONE_LOCK_' .ai-playbook/merge-lock.session; then
      echo "selftest FAIL: merge session carries a DONE_LOCK_ key" >&2
      exit 1
    fi
    mrun merge-release-repo >/dev/null
  ); then
    echo "selftest FAIL: merge_session_carries_only_merge_lock_keys" >&2
    fail=1
  else
    echo "selftest OK: merge session carries only merge lock keys"
  fi

  # ---- Outcome-contract arms (scripts/OUTCOME_CONTRACT.md) ----

  # O1) outcome_acquire_pass: an acquired acquire exits 0, ends its STDERR
  # with `OUTCOME: pass`, and keeps the two exports as the only STDOUT lines
  # (the eval-consumed stdout stays export-only).
  if ! (
    cd "$root"
    o1_rc=0
    run acquire --label outcome-pass >"${tmp}/o1-out" 2>"${tmp}/o1-err" || o1_rc=$?
    [[ "$o1_rc" -eq 0 ]] || { echo "selftest FAIL: outcome acquire rc=${o1_rc}, want 0" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/o1-err")" == "OUTCOME: pass" ]] || { echo "selftest FAIL: acquired acquire stderr does not end with OUTCOME: pass (got: $(tail -n1 "${tmp}/o1-err"))" >&2; exit 1; }
    [[ "$(grep -c '^export ' "${tmp}/o1-out" || true)" -eq 2 ]] || { echo "selftest FAIL: acquired acquire stdout is not exactly two export lines" >&2; exit 1; }
    eval "$(cat "${tmp}/o1-out")"
    run release-repo >/dev/null
  ); then
    echo "selftest FAIL: outcome acquire pass placement" >&2
    fail=1
  else
    echo "selftest OK: acquired acquire emits OUTCOME: pass on stderr; stdout export-only"
  fi

  # O2) outcome_wait_acquire_fail: a max-wait exhaustion against a live
  # holder exits 1 and ends its STDERR with `OUTCOME: fail` naming the
  # holder evidence; DONE_LOCK_POLL_SECS=1 keeps the exhaustion in seconds.
  if ! (
    cd "$root"
    sleep 120 &
    o2_holder=$!
    trap 'kill "$o2_holder" 2>/dev/null || true' EXIT
    eval "$(DONE_LOCK_HOLDER_PID="$o2_holder" run acquire --label outcome-holder)"
    o2_rc=0
    DONE_LOCK_POLL_SECS=1 run wait-acquire --label outcome-waiter --max-wait 2 \
      >"${tmp}/o2-out" 2>"${tmp}/o2-err" || o2_rc=$?
    [[ "$o2_rc" -eq 1 ]] || { echo "selftest FAIL: wait-acquire exhaustion rc=${o2_rc}, want 1" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/o2-err")" == "OUTCOME: fail" ]] || { echo "selftest FAIL: wait-acquire exhaustion stderr does not end with OUTCOME: fail (got: $(tail -n1 "${tmp}/o2-err"))" >&2; exit 1; }
    grep -q 'label: outcome-holder' "${tmp}/o2-err" || { echo "selftest FAIL: exhaustion evidence does not name the holder label" >&2; exit 1; }
    [[ ! -s "${tmp}/o2-out" ]] || { echo "selftest FAIL: exhausted wait-acquire printed exports" >&2; exit 1; }
    run release-repo >/dev/null
  ); then
    echo "selftest FAIL: outcome wait-acquire fail" >&2
    fail=1
  else
    echo "selftest OK: wait-acquire exhaustion emits OUTCOME: fail with holder evidence"
  fi

  # O3) outcome_acquire_ambiguous: a meta-less lock dir past the incomplete
  # age cannot be adjudicated: acquire exits 2 and ends its STDERR with
  # `OUTCOME: indeterminate`.
  if ! (
    cd "$root"
    repo_id="$(printf '%s' "$(git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
    rm -rf "${lock_root}/${repo_id}"
    mkdir -p "${lock_root}/${repo_id}"
    touch -t 202001010000 "${lock_root}/${repo_id}" 2>/dev/null || \
      touch -d '2020-01-01' "${lock_root}/${repo_id}" 2>/dev/null || true
    o3_rc=0
    run acquire --label outcome-ambiguous >"${tmp}/o3-out" 2>"${tmp}/o3-err" || o3_rc=$?
    [[ "$o3_rc" -eq 2 ]] || { echo "selftest FAIL: ambiguous-holder acquire rc=${o3_rc}, want 2" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/o3-err")" == "OUTCOME: indeterminate" ]] || { echo "selftest FAIL: ambiguous-holder acquire stderr does not end with OUTCOME: indeterminate (got: $(tail -n1 "${tmp}/o3-err"))" >&2; exit 1; }
    DONE_LOCK_STALE_SECS=0 run stale-clean >/dev/null 2>&1 || true
    rm -rf "${lock_root}/${repo_id}"
  ); then
    echo "selftest FAIL: outcome acquire ambiguous indeterminate" >&2
    fail=1
  else
    echo "selftest OK: ambiguous holder emits OUTCOME: indeterminate"
  fi

  # O4) outcome_usage_tool_error: a usage error exits 3 and ends its STDERR
  # with `OUTCOME: tool_error` (acquire-family placement).
  if ! (
    cd "$root"
    o4_rc=0
    run acquire --definitely-not-a-flag >"${tmp}/o4-out" 2>"${tmp}/o4-err" || o4_rc=$?
    [[ "$o4_rc" -eq 3 ]] || { echo "selftest FAIL: usage-error acquire rc=${o4_rc}, want 3" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/o4-err")" == "OUTCOME: tool_error" ]] || { echo "selftest FAIL: usage-error stderr does not end with OUTCOME: tool_error (got: $(tail -n1 "${tmp}/o4-err"))" >&2; exit 1; }
  ); then
    echo "selftest FAIL: outcome usage tool error" >&2
    fail=1
  else
    echo "selftest OK: usage error emits OUTCOME: tool_error"
  fi

  # O5) outcome_stale_clean_indeterminate: a meta-less lock dir younger than
  # the incomplete age cannot be safely adjudicated: stale-clean exits 2 and
  # ends its STDOUT with `OUTCOME: indeterminate` (non-acquire placement).
  if ! (
    cd "$root"
    repo_id="$(printf '%s' "$(git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
    rm -rf "${lock_root}/${repo_id}"
    mkdir -p "${lock_root}/${repo_id}"
    o5_rc=0
    run stale-clean >"${tmp}/o5-out" 2>"${tmp}/o5-err" || o5_rc=$?
    [[ "$o5_rc" -eq 2 ]] || { echo "selftest FAIL: too-new incomplete stale-clean rc=${o5_rc}, want 2" >&2; exit 1; }
    [[ "$(tail -n1 "${tmp}/o5-out")" == "OUTCOME: indeterminate" ]] || { echo "selftest FAIL: too-new incomplete stale-clean stdout does not end with OUTCOME: indeterminate (got: $(tail -n1 "${tmp}/o5-out"))" >&2; exit 1; }
    [[ -d "${lock_root}/${repo_id}" ]] || { echo "selftest FAIL: too-new incomplete lock dir was removed" >&2; exit 1; }
    touch -t 202001010000 "${lock_root}/${repo_id}" 2>/dev/null || \
      touch -d '2020-01-01' "${lock_root}/${repo_id}" 2>/dev/null || true
    run stale-clean >/dev/null 2>&1
    [[ ! -d "${lock_root}/${repo_id}" ]] || rm -rf "${lock_root}/${repo_id}"
  ); then
    echo "selftest FAIL: outcome stale-clean indeterminate" >&2
    fail=1
  else
    echo "selftest OK: too-new incomplete lock: stale-clean emits OUTCOME: indeterminate on stdout"
  fi

  rm -rf "$tmp"
  if [[ "$fail" -ne 0 ]]; then
    echo "${PROG}: selftest FAILED" >&2
    emit_outcome fail
    exit 1
  fi
  echo "${PROG}: selftest passed"
  emit_outcome pass
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    acquire|wait-acquire|merge-acquire|merge-wait-acquire) IS_ACQUIRE_CMD=1 ;;
  esac
  case "$cmd" in
    acquire) cmd_acquire "$@" ;;
    wait-acquire) cmd_wait_acquire "$@" ;;
    release) cmd_release ;;
    release-repo) cmd_release_repo ;;
    status) cmd_status ;;
    stale-clean) cmd_stale_clean ;;
    merge-acquire) cmd_acquire "$@" ;;
    merge-wait-acquire) cmd_wait_acquire "$@" ;;
    merge-release) cmd_release ;;
    merge-release-repo) cmd_release_repo ;;
    merge-status) cmd_status ;;
    merge-stale-clean) cmd_stale_clean ;;
    selftest) cmd_selftest ;;
    -h|--help|help|"") usage ;;
    *)
      echo "${PROG}: unknown command: ${cmd}" >&2
      usage >&2
      emit_outcome tool_error
      exit 3
      ;;
  esac
}

main "$@"
