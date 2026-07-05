#!/usr/bin/env bash
# Per-git-repo exclusive lock for the done workflow (learn → docs-branch → commit).
# Agent-agnostic: invoked from done/SKILL.md Step 0 and Step 6.
set -euo pipefail

LOCK_ROOT="${DONE_LOCK_ROOT:-${HOME}/.ai-playbook/locks/done}"
POLL_SECS="${DONE_LOCK_POLL_SECS:-30}"
STALE_SECS="${DONE_LOCK_STALE_SECS:-1800}"
META_FILE="meta.env"

usage() {
  cat <<'EOF'
Usage: done-lock.sh <command> [args...]

Commands:
  acquire [--label TEXT]     Try once; print DONE_LOCK_DIR and DONE_LOCK_TOKEN on stdout when acquired.
  wait-acquire [--label TEXT] [--max-wait SECS]
                             Poll until acquired (default max wait: 7200s). Prints exports on success.
  release                    Remove lock when DONE_LOCK_DIR and DONE_LOCK_TOKEN match (required env vars).
  status                     Show holder for current repo, or "free".
  stale-clean                Remove stale lock for current repo if present.

Environment:
  DONE_LOCK_ROOT             Lock parent directory (default: ~/.ai-playbook/locks/done)
  DONE_LOCK_POLL_SECS        Poll interval for wait-acquire (default: 30)
  DONE_LOCK_STALE_SECS       Steal lock after this many seconds (default: 1800 = 30m)
  DONE_LOCK_DIR / DONE_LOCK_TOKEN   Required for release; printed by acquire / wait-acquire.

Exit codes:
  0 success
  1 usage / release mismatch / not a git repo
  2 acquire: held by another active holder (not stale)
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

lock_age_secs() {
  local meta="${lock_dir}/${META_FILE}"
  [[ -f "$meta" ]] || return 0
  # shellcheck disable=SC1090
  source "$meta"
  local started="${started_epoch:-0}"
  echo $(( $(now_epoch) - started ))
}

is_stale_lock() {
  [[ -d "$lock_dir" ]] || return 1
  local age
  age="$(lock_age_secs)"
  [[ "$age" -ge "$STALE_SECS" ]]
}

force_remove_lock() {
  if [[ -d "$lock_dir" ]]; then
    rm -rf "$lock_dir"
    echo "done-lock: removed stale lock at ${lock_dir}" >&2
  fi
}

write_meta() {
  local lock_token="$1"
  local label="$2"
  local started
  started="$(now_epoch)"
  cat >"${lock_dir}/${META_FILE}" <<EOF
lock_token=${lock_token}
repo_root=${repo_root}
label=${label}
started_epoch=${started}
started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
hostname=$(hostname -s 2>/dev/null || hostname)
EOF
}

print_exports() {
  local token="$1"
  printf 'DONE_LOCK_DIR=%s\n' "$lock_dir"
  printf 'DONE_LOCK_TOKEN=%s\n' "$token"
}

try_acquire() {
  local label="$1"
  mkdir -p "$(dirname "$lock_dir")"
  if mkdir "$lock_dir" 2>/dev/null; then
    local token
    token="$(uuidgen 2>/dev/null || openssl rand -hex 16)"
    write_meta "$token" "$label"
    print_exports "$token"
    return 0
  fi
  if is_stale_lock; then
    force_remove_lock
    if mkdir "$lock_dir" 2>/dev/null; then
      local token
      token="$(uuidgen 2>/dev/null || openssl rand -hex 16)"
      write_meta "$token" "$label"
      print_exports "$token"
      return 0
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
  if [[ -z "$dir" || -z "$token" ]]; then
    echo "done-lock: release requires DONE_LOCK_DIR and DONE_LOCK_TOKEN" >&2
    exit 1
  fi
  local meta="${dir}/${META_FILE}"
  if [[ ! -d "$dir" ]]; then
    echo "done-lock: lock already released (${dir})" >&2
    exit 0
  fi
  if [[ ! -f "$meta" ]]; then
    echo "done-lock: lock directory missing metadata; refusing unsafe release" >&2
    exit 1
  fi
  # shellcheck disable=SC1090
  source "$meta"
  if [[ "$token" != "${lock_token:-}" ]]; then
    echo "done-lock: token mismatch; not releasing ${dir}" >&2
    exit 1
  fi
  rm -rf "$dir"
  echo "done-lock: released lock for ${repo_root:-$dir}"
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
  # shellcheck disable=SC1090
  source "$meta"
  local age
  age="$(lock_age_secs)"
  echo "done-lock: held (${repo_root})"
  echo "  lock_dir: ${lock_dir}"
  echo "  label: ${label:-}"
  echo "  started_at: ${started_at:-unknown}"
  echo "  age_secs: ${age}"
  echo "  hostname: ${hostname:-unknown}"
  if is_stale_lock; then
    echo "  stale: yes (>= ${STALE_SECS}s)"
  else
    echo "  stale: no"
  fi
}

cmd_stale_clean() {
  require_git_repo
  if [[ -d "$lock_dir" ]] && is_stale_lock; then
    force_remove_lock
    echo "done-lock: free (${repo_root})"
  elif [[ -d "$lock_dir" ]]; then
    echo "done-lock: still active (${repo_root})"
    cmd_status
    exit 2
  else
    echo "done-lock: free (${repo_root})"
  fi
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    acquire) cmd_acquire "$@" ;;
    wait-acquire) cmd_wait_acquire "$@" ;;
    release) cmd_release ;;
    status) cmd_status ;;
    stale-clean) cmd_stale_clean ;;
    -h|--help|help|"") usage ;;
    *)
      echo "done-lock: unknown command: ${cmd}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
