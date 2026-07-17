#!/usr/bin/env bash
# Cursor agent runtime diagnostic (checks 1-5 and optional 7).
# Exit 0 when all automated checks pass; non-zero when any FAIL.
set -u

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; FAILURES=$((FAILURES + 1)); }
info() { printf 'INFO  %s\n' "$1"; }

FAILURES=0
HOOKS_DIR="${CURSOR_HOOKS_DIR:-${HOME}/.cursor/hooks}"
DONE_LOCK="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
HYGIENE="${PUBLIC_HYGIENE_SCAN_SCRIPT:-${HOME}/.ai-playbook/scripts/scan-public-hygiene.sh}"

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

# --- 1) Shell alive ---
section=1
if out="$(echo "SHELL_OK"; date +%s 2>/dev/null; pwd; echo "exit=$?")" 2>&1; then
  if printf '%s\n' "$out" | grep -q 'SHELL_OK' && printf '%s\n' "$out" | grep -q 'exit=0'; then
    pass "1 shell alive"
    printf '%s\n' "$out" | sed 's/^/      /'
  else
    fail "1 shell alive (unexpected output)"
    printf '%s\n' "$out" | sed 's/^/      /'
  fi
else
  fail "1 shell alive (command failed)"
fi

# --- 2) Hooks ---
section=2
hook_ok=true
for hook in git-safety.sh no-em-dash.sh; do
  path="${HOOKS_DIR}/${hook}"
  if [ ! -f "$path" ]; then
    fail "2 hook missing: ${hook}"
    hook_ok=false
    continue
  fi
  if ! result="$(printf '%s' '{"command":"echo HOOK_OK"}' | "$path" 2>&1)"; then
    fail "2 hook ${hook} execution error"
    hook_ok=false
    continue
  fi
  if printf '%s' "$result" | grep -q '"permission"[[:space:]]*:[[:space:]]*"allow"'; then
    info "2 hook ${hook}: allow"
  else
    fail "2 hook ${hook} did not allow"
    printf '%s\n' "$result" | sed 's/^/      /'
    hook_ok=false
  fi
done
if $hook_ok; then
  pass "2 hooks allow test commands"
fi

# --- 3) GitHub account for current repo ---
section=3
ROOT="$(repo_root)"
cd "$ROOT" || exit 1
REMOTE="$(git remote get-url origin 2>/dev/null || echo no-remote)"
info "3 remote=${REMOTE}"

if command -v gh >/dev/null 2>&1; then
  auth_out="$(gh auth status 2>&1)" || true
  active="$(printf '%s\n' "$auth_out" | awk '
    /Logged in to github.com account/ {
      line = $0
      sub(/.*account /, "", line)
      sub(/ .*/, "", line)
      user = line
      active = 0
    }
    /Active account: true/ && user { print user; exit }
  ')"
  info "3 gh active=${active:-unknown}"
  repo_view="$(gh repo view --json nameWithOwner,owner 2>&1)" || repo_view="ERROR: $repo_view"
  if printf '%s' "$repo_view" | grep -q 'nameWithOwner'; then
    pass "3 github repo view"
    info "3 ${repo_view}"
    nwo="$(printf '%s' "$repo_view" | sed -n 's/.*"nameWithOwner"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
    owner_login="$(printf '%s' "$repo_view" | sed -n 's/.*"login"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
    owner_type=""
    if [ -n "$nwo" ]; then
      owner_type="$(gh api "repos/${nwo}" --jq '.owner.type' 2>/dev/null || true)"
    fi
    if [ -z "$owner_type" ]; then
      owner_id="$(printf '%s' "$repo_view" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
      case "$owner_id" in
        *Organization*) owner_type="Organization" ;;
        *User*) owner_type="User" ;;
      esac
    fi
    if [ -n "${GH_USER_EXPECTED:-}" ] && [ -n "$active" ] && [ "$active" != "$GH_USER_EXPECTED" ]; then
      fail "3 github account mismatch (GH_USER_EXPECTED=${GH_USER_EXPECTED}, active=${active})"
    elif [ "$owner_type" = "User" ] && [ -n "$owner_login" ] && [ -n "$active" ] && [ "$active" != "$owner_login" ]; then
      fail "3 github account mismatch (repo owner user=${owner_login}, active=${active})"
    elif [ "$owner_type" = "Organization" ]; then
      pass "3 github org repo accessible (org=${owner_login}, active=${active})"
    elif [ -n "$owner_login" ] && [ -n "$active" ]; then
      pass "3 github account matches repo owner"
    else
      info "3 github account (set GH_USER_EXPECTED to enforce a specific account)"
    fi
  else
    fail "3 github repo view"
    printf '%s\n' "$repo_view" | sed 's/^/      /'
  fi
else
  fail "3 gh not installed"
fi

# --- 4) done prerequisites ---
section=4
done_ok=true
if [ -x "$DONE_LOCK" ]; then
  info "4 done-lock script present"
else
  fail "4 done-lock script missing or not executable"
  done_ok=false
fi
if [ -x "$HYGIENE" ]; then
  info "4 hygiene scan script present"
else
  fail "4 hygiene scan script missing or not executable"
  done_ok=false
fi
if [ -x "$DONE_LOCK" ]; then
  lock_out="$("$DONE_LOCK" status 2>&1)" || lock_out="ERROR: $lock_out"
  info "4 ${lock_out}"
  if printf '%s' "$lock_out" | grep -q 'done-lock: free'; then
    pass "4 done lock free"
  elif printf '%s' "$lock_out" | grep -q 'done-lock: held'; then
    fail "4 done lock held"
  else
    info "4 done lock status unclear"
  fi
fi
if $done_ok; then
  pass "4 done scripts present"
fi

# --- 5) tmp dir shell-writable (proxy for probe target) ---
section=5
TMP_DIR="docs/tmp/"
if [ -f .ai-playbook/facts.md ]; then
  _tmp_cfg="$(awk '/^```toml/{f=1;next} f&&/^```/{exit} f&&/^tmp_dir/{gsub(/^tmp_dir[[:space:]]*=[[:space:]]*"/,""); gsub(/".*/,""); print; exit}' .ai-playbook/facts.md)"
  [ -n "$_tmp_cfg" ] && TMP_DIR="$_tmp_cfg"
fi
TMP_DIR="${TMP_DIR%/}/"
PROBE="${TMP_DIR}cursor-agent-diagnose-probe.shell"
info "5 tmp_dir=${TMP_DIR}"
if mkdir -p "$TMP_DIR" 2>/dev/null; then
  marker="PROBE_SHELL_OK ts=$(date +%s 2>/dev/null || echo 0)"
  if printf '%s\n' "$marker" > "$PROBE" 2>/dev/null; then
    if [ -f "$PROBE" ] && grep -Fxq "$marker" "$PROBE" 2>/dev/null; then
      pass "5 tmp dir writable"
      rm -f "$PROBE"
    else
      fail "5 tmp dir write/read mismatch"
      rm -f "$PROBE" 2>/dev/null || true
    fi
  else
    fail "5 tmp dir not writable"
  fi
else
  fail "5 tmp dir missing and could not create"
fi
unset _tmp_cfg PROBE marker

# --- 7) cursor-agent MCP (optional) ---
if command -v cursor-agent >/dev/null 2>&1; then
  ver="$(cursor-agent --version 2>/dev/null || true)"
  info "7 cursor-agent version=${ver:-unknown}"
  mcp_out="$(cursor-agent mcp list 2>&1)" || mcp_out="ERROR: $mcp_out"
  if printf '%s\n' "$mcp_out" | grep -q 'requires_authentication'; then
    info "7 MCP CLI requires auth (normal if IDE OAuth not synced to CLI)"
    printf '%s\n' "$mcp_out" | sed 's/^/      /'
  elif printf '%s\n' "$mcp_out" | grep -q 'ready'; then
    pass "7 cursor-agent MCP ready"
  else
    info "7 cursor-agent mcp list"
    printf '%s\n' "$mcp_out" | sed 's/^/      /'
  fi
else
  info "7 cursor-agent CLI not installed (skip)"
fi

# --- Summary ---
echo "---"
if [ "$FAILURES" -eq 0 ]; then
  echo "SUMMARY: ALL_AUTOMATED_CHECKS_PASS"
  exit 0
fi
echo "SUMMARY: ${FAILURES} automated check(s) FAILED"
exit 1
