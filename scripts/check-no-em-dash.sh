#!/usr/bin/env bash
# Scan text files for em dash (U+2014). Policy: agent_workflow_guidelines.md §39.
# Agent-agnostic: use from done, pre-commit, CI, or any shell workflow.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check-no-em-dash.sh <command> [args...]

Commands:
  file <path>...       Exit 1 if any file contains U+2014
  paths <path>...      Same as file (alias)
  staged               Scan git-staged paths (added/copied/modified)
  touched              Scan unstaged + staged + untracked paths in current repo
  stdin                Read file list from stdin (one path per line)

Prose paths scanned by default: *.md, *.mdc, AGENTS.md, CLAUDE.md, GEMINI.md, COPILOT.md
Use CHECK_NO_EM_DASH_ALL=1 to scan every path argument regardless of extension.

Exit 0 when clean; exit 1 when em dash found (prints paths and line numbers).
EOF
}

is_prose_path() {
  local path="$1"
  [[ "${CHECK_NO_EM_DASH_ALL:-0}" == "1" ]] && return 0
  case "$path" in
    *.md|*.mdc|AGENTS.md|CLAUDE.md|GEMINI.md|COPILOT.md) return 0 ;;
    *) return 1 ;;
  esac
}

scan_file() {
  local path="$1"
  [[ -f "$path" ]] || return 0
  is_prose_path "$path" || return 0
  python3 - "$path" <<'PY'
import sys
path = sys.argv[1]
with open(path, encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        if "\u2014" in line:
            print(f"{path}:{i}:{line.rstrip()}")
            sys.exit(1)
sys.exit(0)
PY
}

scan_paths() {
  local found=0
  for path in "$@"; do
    if scan_file "$path"; then
      :
    else
      found=1
    fi
  done
  return "$found"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  file|paths)
    [[ $# -gt 0 ]] || { echo "check-no-em-dash: missing paths" >&2; exit 2; }
    scan_paths "$@"
    ;;
  staged)
    files=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && files+=("$line")
    done < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
    [[ ${#files[@]} -eq 0 ]] && exit 0
    scan_paths "${files[@]}"
    ;;
  touched)
    files=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && files+=("$line")
    done < <(
      {
        git diff --name-only 2>/dev/null || true
        git diff --cached --name-only 2>/dev/null || true
        git ls-files --others --exclude-standard 2>/dev/null || true
      } | sort -u
    )
    [[ ${#files[@]} -eq 0 ]] && exit 0
    scan_paths "${files[@]}"
    ;;
  stdin)
    files=()
    while IFS= read -r line; do
      [[ -n "$line" ]] && files+=("$line")
    done
    [[ ${#files[@]} -eq 0 ]] && exit 0
    scan_paths "${files[@]}"
    ;;
  -h|--help|help|"")
    usage
    [[ -z "$cmd" ]] && exit 0 || exit 0
    ;;
  *)
    echo "check-no-em-dash: unknown command: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
