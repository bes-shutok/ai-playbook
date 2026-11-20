#!/usr/bin/env bash
# Sync MCP OAuth credentials between Cursor, mcp-remote CLI, and ~/.ai-playbook/credentials/.
# Secrets stay in credentials/ (mode 600/700) — never in facts.md or committed repos.
set -euo pipefail

CRED_DIR="${HOME}/.ai-playbook/credentials"
CURSOR_CANONICAL="${HOME}/.cursor/projects/Users-andrey/mcp-auth.json"
MCP_REMOTE_BACKUP="${CRED_DIR}/mcp-atlassian-mcp-remote"
MCP_REMOTE_LIVE="${HOME}/.mcp-auth/mcp-remote-0.1.36"
CURSOR_BACKUP="${CRED_DIR}/mcp-cursor.json"

usage() {
  cat <<'EOF'
Usage: sync-mcp-credentials.sh <command>

Commands:
  snapshot   Copy live Cursor + mcp-remote tokens into ~/.ai-playbook/credentials/
  restore    Push backed-up tokens to Cursor user mcp-auth + mcp-remote CLI dir
  status     Show whether live and backup files exist (no token values printed)

After OAuth in Cursor, run: snapshot
When a new Cursor project lacks Slack/Atlassian auth, run: restore
EOF
}

has_tokens() {
  local file="$1" service="$2"
  python3 - "$file" "$service" <<'PY'
import json, sys
path, service = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(path))
except FileNotFoundError:
    print("missing")
    sys.exit(0)
node = data.get(service, {})
tokens = node.get("tokens", {})
print("ok" if tokens.get("access_token") and tokens.get("refresh_token") else "incomplete")
PY
}

cmd_snapshot() {
  mkdir -p "${CRED_DIR}" "${MCP_REMOTE_BACKUP}"
  chmod 700 "${CRED_DIR}"
  if [[ -f "${CURSOR_CANONICAL}" ]]; then
    cp -p "${CURSOR_CANONICAL}" "${CURSOR_BACKUP}"
    chmod 600 "${CURSOR_BACKUP}"
    echo "snapshot: ${CURSOR_BACKUP}"
  else
    echo "warn: ${CURSOR_CANONICAL} not found — skip Cursor backup" >&2
  fi
  if [[ -d "${MCP_REMOTE_LIVE}" ]]; then
    cp -p "${MCP_REMOTE_LIVE}/"* "${MCP_REMOTE_BACKUP}/"
    chmod 600 "${MCP_REMOTE_BACKUP}/"*
    echo "snapshot: ${MCP_REMOTE_BACKUP}/"
  else
    echo "warn: ${MCP_REMOTE_LIVE} not found — skip mcp-remote backup" >&2
  fi
}

cmd_restore() {
  if [[ -f "${CURSOR_BACKUP}" ]]; then
    mkdir -p "$(dirname "${CURSOR_CANONICAL}")"
    cp -p "${CURSOR_BACKUP}" "${CURSOR_CANONICAL}"
    chmod 600 "${CURSOR_CANONICAL}"
    echo "restore: ${CURSOR_CANONICAL}"
  else
    echo "error: ${CURSOR_BACKUP} missing — run snapshot first" >&2
    exit 1
  fi
  if [[ -d "${MCP_REMOTE_BACKUP}" ]] && [[ -n "$(ls -A "${MCP_REMOTE_BACKUP}" 2>/dev/null || true)" ]]; then
    mkdir -p "${MCP_REMOTE_LIVE}"
    cp -p "${MCP_REMOTE_BACKUP}/"* "${MCP_REMOTE_LIVE}/"
    chmod 600 "${MCP_REMOTE_LIVE}/"*
    echo "restore: ${MCP_REMOTE_LIVE}/"
  else
    echo "warn: ${MCP_REMOTE_BACKUP} empty — skip mcp-remote restore" >&2
  fi
  # Optional: copy to current repo Cursor project if CURSOR_PROJECT_DIR is set
  if [[ -n "${CURSOR_PROJECT_DIR:-}" && -f "${CURSOR_PROJECT_DIR}/mcp-auth.json" ]]; then
    cp -p "${CURSOR_BACKUP}" "${CURSOR_PROJECT_DIR}/mcp-auth.json"
    chmod 600 "${CURSOR_PROJECT_DIR}/mcp-auth.json"
    echo "restore: ${CURSOR_PROJECT_DIR}/mcp-auth.json"
  fi
}

cmd_status() {
  echo "Cursor canonical: ${CURSOR_CANONICAL}"
  echo "  atlassian: $(has_tokens "${CURSOR_CANONICAL}" atlassian)"
  echo "  slack: $(has_tokens "${CURSOR_CANONICAL}" slack)"
  echo "Cursor backup: ${CURSOR_BACKUP}"
  echo "  atlassian: $(has_tokens "${CURSOR_BACKUP}" atlassian)"
  echo "  slack: $(has_tokens "${CURSOR_BACKUP}" slack)"
  echo "mcp-remote live: ${MCP_REMOTE_LIVE}"
  echo "  tokens file: $([[ -f "${MCP_REMOTE_LIVE}/01910c24c5f2edcaf999bd1eaaeaeee8_tokens.json" ]] && echo ok || echo missing)"
  echo "mcp-remote backup: ${MCP_REMOTE_BACKUP}"
  echo "  tokens file: $([[ -f "${MCP_REMOTE_BACKUP}/01910c24c5f2edcaf999bd1eaaeaeee8_tokens.json" ]] && echo ok || echo missing)"
}

main() {
  case "${1:-}" in
    snapshot) cmd_snapshot ;;
    restore) cmd_restore ;;
    status) cmd_status ;;
    -h|--help|help|"") usage ;;
    *) echo "unknown command: $1" >&2; usage; exit 1 ;;
  esac
}

main "$@"
