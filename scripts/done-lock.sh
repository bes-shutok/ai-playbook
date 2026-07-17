#!/usr/bin/env bash
# Per-git-repo exclusive lock for the done workflow (learn → docs-branch → commit).
# Agent-agnostic: invoked from done/SKILL.md Step 0 and Step 6.
set -euo pipefail

LOCK_ROOT="${DONE_LOCK_ROOT:-${HOME}/.ai-playbook/locks/done}"
POLL_SECS="${DONE_LOCK_POLL_SECS:-30}"
STALE_SECS="${DONE_LOCK_STALE_SECS:-1800}"
INCOMPLETE_SECS="${DONE_LOCK_INCOMPLETE_SECS:-5}"
META_FILE="meta.env"

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
                             (operator escape; auto-acquire never steals a live session fence).
  selftest                   Run built-in race/fence fixtures (exit 0 on pass).

Environment:
  DONE_LOCK_ROOT             Lock parent directory (default: ~/.ai-playbook/locks/done)
  DONE_LOCK_POLL_SECS        Poll interval for wait-acquire (default: 30)
  DONE_LOCK_STALE_SECS       Age before stale-clean may remove a fenced lock (default: 1800)
  DONE_LOCK_INCOMPLETE_SECS  Age before meta-less lock_dir is treated as crash leftover (default: 5)
  DONE_LOCK_HOLDER_PID       Long-lived holder PID (default: PPID of the acquire process).
                             Callers that `eval "$(done-lock.sh acquire)"` should leave this unset
                             so PPID is the eval'ing shell. Do not use the acquire script PID.
  DONE_LOCK_DIR / DONE_LOCK_TOKEN   Required in env for release / release-repo. Session file is
                             fence/status only; release-repo will not source it.

Exit codes:
  0 success
  1 usage / release mismatch / not a git repo
  2 acquire: held by another active holder (not stealable)
EOF
}

require_git_repo() {
  if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "done-lock: not inside a git repository" >&2
    exit 1
  fi
  repo_id="$(printf '%s' "$repo_root" | shasum -a 256 | cut -c1-16)"
  lock_dir="${LOCK_ROOT}/${repo_id}"
}

read_label() {
  label=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --label)
        shift
        label="${1:-}"
        [[ -n "$label" ]] || { echo "done-lock: --label requires a value" >&2; exit 1; }
        ;;
      *)
        echo "done-lock: unknown argument: $1" >&2
        exit 1
        ;;
    esac
    shift
  done
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
  lock_meta_started_epoch=0
  lock_meta_started_at=""
  lock_meta_hostname=""
  lock_meta_holder_pid=""
  lock_meta_token=""
  [[ -f "$meta" ]] || return 1
  lock_meta_label="$(meta_field "$meta" label)"
  lock_meta_started_epoch="$(meta_field "$meta" started_epoch)"
  lock_meta_started_epoch="${lock_meta_started_epoch:-0}"
  lock_meta_started_at="$(meta_field "$meta" started_at)"
  lock_meta_hostname="$(meta_field "$meta" hostname)"
  lock_meta_holder_pid="$(meta_field "$meta" holder_pid)"
  lock_meta_token="$(meta_field "$meta" lock_token)"
  return 0
}

lock_age_secs() {
  load_lock_meta || true
  echo $(( $(now_epoch) - lock_meta_started_epoch ))
}

holder_pid_alive() {
  local pid="${1:-}"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

is_stale_lock() {
  [[ -d "$lock_dir" ]] || return 1
  local age
  age="$(lock_age_secs)"
  [[ "$age" -ge "$STALE_SECS" ]]
}

is_dead_holder_lock() {
  [[ -d "$lock_dir" ]] || return 1
  load_lock_meta || return 1
  [[ -n "$lock_meta_holder_pid" ]] || return 1
  holder_pid_alive "$lock_meta_holder_pid" && return 1
  # PID dead: do not auto-steal while a matching session fence still exists.
  # Agent Shell tool calls exit after acquire; the session file is the live hold signal.
  if session_fence_matches_lock; then
    return 1
  fi
  return 0
}

session_fence_matches_lock() {
  local session_file s_dir s_token
  session_file="$(lock_session_file)"
  [[ -f "$session_file" ]] || return 1
  s_dir="$(grep -E '^DONE_LOCK_DIR=' "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  s_token="$(grep -E '^DONE_LOCK_TOKEN=' "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  [[ -n "$s_dir" && -n "$s_token" ]] || return 1
  load_lock_meta || return 1
  [[ "$s_dir" == "$lock_dir" && "$s_token" == "$lock_meta_token" ]]
}

is_stealable_lock() {
  # Live session fence is never auto-stolen (including after stale TTL).
  # Operator escape: stale-clean can still remove a fenced stale lock.
  if session_fence_matches_lock; then
    return 1
  fi
  is_stale_lock && return 0
  is_dead_holder_lock && return 0
  return 1
}

resolve_holder_pid() {
  # Prefer explicit long-lived PID; else PPID (eval'ing / waiting shell), never $$.
  if [[ -n "${DONE_LOCK_HOLDER_PID:-}" ]]; then
    printf '%s' "$DONE_LOCK_HOLDER_PID"
  else
    printf '%s' "$PPID"
  fi
}

force_remove_lock() {
  # Unconditional remove (stale-clean / explicit). Prefer steal_remove_if_unchanged for steal path.
  local reason="${1:-abandoned}"
  if [[ -d "$lock_dir" ]]; then
    rm -rf "$lock_dir"
    echo "done-lock: removed ${reason} lock at ${lock_dir}" >&2
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
  echo "done-lock: removed ${reason} lock at ${lock_dir}" >&2
  return 0
}

write_meta() {
  local lock_token="$1"
  local label="$2"
  local started holder meta
  started="$(now_epoch)"
  holder="$(resolve_holder_pid)"
  meta="${lock_dir}/${META_FILE}"
  # noclobber: refuse to overwrite a peer's meta if they claimed the dir first.
  if [[ -f "$meta" ]]; then
    return 1
  fi
  set +o noclobber 2>/dev/null || true
  set -C
  if ! cat >"${meta}" <<EOF
lock_token=${lock_token}
repo_root=${repo_root}
label=${label}
started_epoch=${started}
started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
hostname=$(hostname -s 2>/dev/null || hostname)
holder_pid=${holder}
EOF
  then
    set +C
    return 1
  fi
  set +C
  return 0
}

print_exports() {
  local token="$1"
  printf 'export DONE_LOCK_DIR=%q\n' "$lock_dir"
  printf 'export DONE_LOCK_TOKEN=%q\n' "$token"
}

lock_session_file() {
  echo "${repo_root}/.ai-playbook/done-lock.session"
}

clear_lock_session_if_token() {
  # Clear shared session only when it still names the token we released/stole.
  # mv + re-check so a concurrent write_lock_session cannot be deleted after replace.
  local expected_token="${1:-}"
  local session_file s_token tomb t_token
  session_file="$(lock_session_file)"
  [[ -f "$session_file" ]] || return 0
  [[ -n "$expected_token" ]] || return 0
  s_token="$(grep -E '^DONE_LOCK_TOKEN=' "$session_file" 2>/dev/null | head -n1 | cut -d= -f2-)"
  [[ "$s_token" == "$expected_token" ]] || return 0
  tomb="${session_file}.clearing.$$.$RANDOM"
  if ! mv "$session_file" "$tomb" 2>/dev/null; then
    return 0
  fi
  t_token="$(grep -E '^DONE_LOCK_TOKEN=' "$tomb" 2>/dev/null | head -n1 | cut -d= -f2-)"
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
  tmp="${session_file}.tmp.$$.$RANDOM"
  cat >"${tmp}" <<EOF
DONE_LOCK_DIR=${lock_dir}
DONE_LOCK_TOKEN=${token}
EOF
  mv "${tmp}" "${session_file}"
}

clear_lock_session() {
  # Unconditional clear (tests / incomplete-lock recovery only).
  local session_file
  session_file="$(lock_session_file)"
  rm -f "${session_file}"
}

load_lock_session() {
  if [[ -n "${DONE_LOCK_DIR:-}" && -n "${DONE_LOCK_TOKEN:-}" ]]; then
    return 0
  fi
  local session_file
  session_file="$(lock_session_file)"
  if [[ ! -f "$session_file" ]]; then
    return 1
  fi
  # shellcheck disable=SC1090
  source "$session_file"
  [[ -n "${DONE_LOCK_DIR:-}" && -n "${DONE_LOCK_TOKEN:-}" ]]
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
  force_remove_lock "incomplete"
  return 0
}

try_acquire() {
  local label="$1"
  mkdir -p "$(dirname "$lock_dir")"
  if mkdir "$lock_dir" 2>/dev/null; then
    local token
    token="$(uuidgen 2>/dev/null || openssl rand -hex 16)"
    if ! write_meta "$token" "$label"; then
      # Peer claimed meta first, or dir was recycled under us; do not export a false hold.
      return 1
    fi
    write_lock_session "$token"
    # Re-read: abort if meta no longer matches our token (lost race after write).
    load_lock_meta || return 1
    if [[ "$lock_meta_token" != "$token" ]]; then
      return 1
    fi
    print_exports "$token"
    return 0
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
        local token
        token="$(uuidgen 2>/dev/null || openssl rand -hex 16)"
        if ! write_meta "$token" "$label"; then
          return 1
        fi
        write_lock_session "$token"
        load_lock_meta || return 1
        if [[ "$lock_meta_token" != "$token" ]]; then
          return 1
        fi
        print_exports "$token"
        return 0
      fi
    fi
  fi
  return 1
}

cmd_acquire() {
  local label=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --label)
        shift
        label="${1:-}"
        shift
        ;;
      *)
        echo "done-lock: unknown argument: $1" >&2
        exit 1
        ;;
    esac
  done
  require_git_repo
  if try_acquire "$label"; then
    exit 0
  fi
  echo "done-lock: held by another done workflow for ${repo_root}" >&2
  cmd_status >&2
  exit 2
}

cmd_wait_acquire() {
  local label=""
  local max_wait=7200
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --label)
        shift
        label="${1:-}"
        shift
        ;;
      --max-wait)
        shift
        max_wait="${1:-}"
        shift
        ;;
      *)
        echo "done-lock: unknown argument: $1" >&2
        exit 1
        ;;
    esac
  done
  require_git_repo
  local deadline=$(( $(now_epoch) + max_wait ))
  while true; do
    if try_acquire "$label"; then
      exit 0
    fi
    if [[ "$(now_epoch)" -ge "$deadline" ]]; then
      echo "done-lock: timed out after ${max_wait}s waiting for lock on ${repo_root}" >&2
      cmd_status >&2
      exit 2
    fi
    echo "done-lock: waiting for lock on ${repo_root} (poll ${POLL_SECS}s)..." >&2
    cmd_status >&2
    sleep "$POLL_SECS"
  done
}

cmd_release() {
  local dir="${DONE_LOCK_DIR:-}"
  local token="${DONE_LOCK_TOKEN:-}"
  # Same confused-deputy guard as release-repo: never adopt the shared session file.
  if [[ -z "$dir" || -z "$token" ]]; then
    echo "done-lock: release requires DONE_LOCK_DIR and DONE_LOCK_TOKEN in env" >&2
    echo "done-lock: re-export them from your acquire Step 0 output; refusing shared session load" >&2
    exit 1
  fi
  local meta="${dir}/${META_FILE}"
  if [[ ! -d "$dir" ]]; then
    echo "done-lock: lock already released (${dir})" >&2
    require_git_repo 2>/dev/null && clear_lock_session_if_token "$token" || true
    exit 0
  fi
  if [[ ! -f "$meta" ]]; then
    echo "done-lock: lock directory missing metadata; refusing unsafe release" >&2
    exit 1
  fi
  local meta_token meta_epoch released_for
  meta_token="$(meta_field "$meta" lock_token)"
  meta_epoch="$(meta_field "$meta" started_epoch)"
  if [[ "$token" != "$meta_token" ]]; then
    echo "done-lock: token mismatch; not releasing ${dir}" >&2
    exit 1
  fi
  released_for="$(meta_field "$meta" repo_root)"
  released_for="${released_for:-$dir}"
  # CAS remove: refuse if another waiter replaced the lock after our token check.
  lock_dir="$dir"
  if ! steal_remove_if_unchanged "$meta_token" "$meta_epoch" "released"; then
    echo "done-lock: lock changed under us; not releasing ${dir}" >&2
    exit 1
  fi
  require_git_repo 2>/dev/null && clear_lock_session_if_token "$token" || true
  echo "done-lock: released lock for ${released_for}"
}

cmd_release_repo() {
  require_git_repo
  # Confused-deputy guard: do not adopt the shared session file when env is empty.
  # After stale-clean + peer acquire, session names the new holder; sourcing it would
  # let an overthrown chat CAS-release the live lock. Callers must reuse DONE_LOCK_*
  # from their acquire exports (same shell or re-exported from Step 0 output).
  if [[ -z "${DONE_LOCK_DIR:-}" || -z "${DONE_LOCK_TOKEN:-}" ]]; then
    echo "done-lock: release-repo requires DONE_LOCK_DIR and DONE_LOCK_TOKEN in env" >&2
    echo "done-lock: re-export them from your acquire Step 0 output; refusing shared session load" >&2
    if [[ -f "$(lock_session_file)" ]]; then
      echo "done-lock: hint: session file exists for status/fence only; not used for release-repo" >&2
    fi
    exit 1
  fi
  cmd_release
}

cmd_status() {
  require_git_repo
  if [[ ! -d "$lock_dir" ]]; then
    echo "done-lock: free (${repo_root})"
    return 0
  fi
  local meta="${lock_dir}/${META_FILE}"
  if [[ ! -f "$meta" ]]; then
    echo "done-lock: held (${lock_dir}); metadata missing"
    return 0
  fi
  load_lock_meta
  local age
  age="$(lock_age_secs)"
  echo "done-lock: held (${repo_root})"
  echo "  lock_dir: ${lock_dir}"
  echo "  label: ${lock_meta_label:-}"
  echo "  started_at: ${lock_meta_started_at:-unknown}"
  echo "  age_secs: ${age}"
  echo "  hostname: ${lock_meta_hostname:-unknown}"
  if [[ -n "${lock_meta_holder_pid:-}" ]]; then
    echo "  holder_pid: ${lock_meta_holder_pid}"
    if holder_pid_alive "$lock_meta_holder_pid"; then
      echo "  holder_alive: yes"
    else
      echo "  holder_alive: no"
      if session_fence_matches_lock; then
        echo "  session_fence: yes (PID dead but matching done-lock.session; not auto-stealable)"
      fi
    fi
  else
    echo "  holder_pid: unknown (pre-PID lock)"
  fi
  if is_stealable_lock; then
    if is_stale_lock; then
      echo "  stale: yes (>= ${STALE_SECS}s)"
    elif is_dead_holder_lock; then
      echo "  abandoned: yes (holder PID not running and no session fence)"
    fi
    echo "  stealable: yes"
  else
    echo "  stealable: no"
    if session_fence_matches_lock && is_stale_lock; then
      echo "  note: session-fenced and stale; auto-acquire will not steal; use stale-clean"
    fi
  fi
}

cmd_stale_clean() {
  require_git_repo
  if [[ -d "$lock_dir" ]] && [[ ! -f "${lock_dir}/${META_FILE}" ]]; then
    force_remove_lock "incomplete"
    clear_lock_session || true
    echo "done-lock: free (${repo_root})"
    return 0
  fi
  # Operator escape: allow removing a fenced lock only when it is also stale.
  local allow_fenced_stale=0
  if session_fence_matches_lock && is_stale_lock; then
    allow_fenced_stale=1
  fi
  if [[ -d "$lock_dir" ]] && { is_stealable_lock || [[ "$allow_fenced_stale" -eq 1 ]]; }; then
    local reason="stale"
    local expected_token expected_epoch
    load_lock_meta || exit 1
    expected_token="${lock_meta_token}"
    expected_epoch="${lock_meta_started_epoch}"
    if [[ "$allow_fenced_stale" -eq 1 ]]; then
      reason="stale-fenced"
    elif is_dead_holder_lock; then
      reason="abandoned"
    fi
    if ! steal_remove_if_unchanged "$expected_token" "$expected_epoch" "$reason"; then
      echo "done-lock: lock changed under us; still active (${repo_root})" >&2
      cmd_status
      exit 2
    fi
    clear_lock_session_if_token "$expected_token" || true
    echo "done-lock: free (${repo_root})"
  elif [[ -d "$lock_dir" ]]; then
    echo "done-lock: still active (${repo_root})"
    cmd_status
    exit 2
  else
    echo "done-lock: free (${repo_root})"
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
      DONE_LOCK_STALE_SECS="${DONE_LOCK_STALE_SECS:-1800}" \
      DONE_LOCK_DIR="${DONE_LOCK_DIR-}" \
      DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN-}" \
      bash "$script_path" "$@"
  }

  # 1) Session fence: dead PPID shell must not auto-steal
  (
    cd "$root"
    eval "$(run acquire --label fence)"
  )
  if (cd "$root" && run acquire --label steal 2>/dev/null); then
    echo "selftest FAIL: session fence did not block second acquire" >&2
    fail=1
  else
    echo "selftest OK: session fence blocks auto-steal"
  fi

  # 2) Stale + fence: auto-acquire still blocked; stale-clean allowed
  DONE_LOCK_STALE_SECS=0
  if (cd "$root" && DONE_LOCK_STALE_SECS=0 run acquire --label stale-steal 2>/dev/null); then
    echo "selftest FAIL: stale TTL auto-stole a fenced lock" >&2
    fail=1
  else
    echo "selftest OK: fenced lock not auto-stolen when stale"
  fi
  if ! (cd "$root" && DONE_LOCK_STALE_SECS=0 run stale-clean); then
    echo "selftest FAIL: stale-clean should remove fenced stale lock" >&2
    fail=1
  else
    echo "selftest OK: stale-clean removes fenced stale lock"
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
    eval "$(run acquire --label abandon-steal)"
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

  rm -rf "$tmp"
  if [[ "$fail" -ne 0 ]]; then
    echo "done-lock: selftest FAILED" >&2
    exit 1
  fi
  echo "done-lock: selftest passed"
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    acquire) cmd_acquire "$@" ;;
    wait-acquire) cmd_wait_acquire "$@" ;;
    release) cmd_release ;;
    release-repo) cmd_release_repo ;;
    status) cmd_status ;;
    stale-clean) cmd_stale_clean ;;
    selftest) cmd_selftest ;;
    -h|--help|help|"") usage ;;
    *)
      echo "done-lock: unknown command: ${cmd}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
