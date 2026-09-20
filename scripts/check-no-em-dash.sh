#!/usr/bin/env bash
# Scan text files for em dash (U+2014). Policy: agent_workflow_guidelines.md §39.
# Agent-agnostic: use from done, pre-commit, CI, or any shell workflow.
set -euo pipefail

EM_DASH=$'\xe2\x80\x94'

usage() {
  cat <<'EOF'
Usage: check-no-em-dash.sh <command> [args...]

Commands:
  file <path>...       Exit 1 if any file contains U+2014
  paths <path>...      Same as file (alias)
  staged               Scan git-staged paths (added/copied/modified)
  touched              Scan unstaged + staged + untracked paths in current repo
  added-lines [--base REF] [paths...]
                       Scan git-diff added lines only (git diff -U0 against the
                       base; all extensions) and report file:new-file-line per
                       hit. The default base is HEAD, so the mode gates
                       working-tree insertions at authoring time; re-scanning
                       already-committed insertions is out of scope by design.
                       Git failures (exit status 2 or worse) abort non-zero
                       instead of reading as clean.
  stdin                Read file list from stdin (one path per line)

Prose paths scanned by default: *.md, *.mdc, AGENTS.md, CLAUDE.md, GEMINI.md, COPILOT.md
Use CHECK_NO_EM_DASH_ALL=1 to scan every path argument regardless of extension.
The added-lines command scans every extension regardless of this prose filter.

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

# Scan only the added lines of a git diff. New-file line numbers come from the
# hunk headers (the start line of each added run) and advance per added or
# context line; deleted lines never move the counter.
scan_added_lines() {
  local base="HEAD"
  local -a paths=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --base)
        if [[ $# -lt 2 || -z "$2" ]]; then
          echo "check-no-em-dash: --base requires a REF argument" >&2
          exit 2
        fi
        base="$2"
        shift 2
        ;;
      --base=*)
        base="${1#--base=}"
        if [[ -z "$base" ]]; then
          echo "check-no-em-dash: --base requires a REF argument" >&2
          exit 2
        fi
        shift
        ;;
      --)
        shift
        while [[ $# -gt 0 ]]; do
          paths+=("$1")
          shift
        done
        ;;
      --*)
        echo "check-no-em-dash: unknown option: $1" >&2
        exit 2
        ;;
      *)
        paths+=("$1")
        shift
        ;;
    esac
  done

  local git_status=0
  local diff_text=""
  if [[ ${#paths[@]} -gt 0 ]]; then
    diff_text="$(git diff -U0 "$base" -- "${paths[@]}")" || git_status=$?
  else
    diff_text="$(git diff -U0 "$base")" || git_status=$?
  fi
  if (( git_status >= 2 )); then
    echo "check-no-em-dash: git diff against $base failed (exit $git_status); aborting" >&2
    exit "$git_status"
  fi

  local found=0
  local in_hunk=0
  local file=""
  local new_line=0
  local line
  local hunk_re='^@@[[:space:]]-[0-9]+(,[0-9]+)?[[:space:]]\+([0-9]+)'
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      "diff --git "*)
        in_hunk=0
        ;;
      "+++ "*)
        if [[ "$in_hunk" -eq 0 ]]; then
          file="${line#+++ }"
          if [[ "$file" == b/* ]]; then
            file="${file#b/}"
          fi
        else
          # Inside a hunk this is an added line whose content starts with '++'.
          if [[ "$line" == *"$EM_DASH"* ]]; then
            found=1
            printf '%s:%s:%s\n' "$file" "$new_line" "${line#+}"
          fi
          new_line=$((new_line + 1))
        fi
        ;;
      "@@"*)
        if [[ "$line" =~ $hunk_re ]]; then
          new_line="${BASH_REMATCH[2]}"
          in_hunk=1
        fi
        ;;
      "+"*)
        if [[ "$line" == *"$EM_DASH"* ]]; then
          found=1
          printf '%s:%s:%s\n' "$file" "$new_line" "${line#+}"
        fi
        new_line=$((new_line + 1))
        ;;
      "-"*)
        # Deleted line: the new-file counter does not move.
        ;;
      " "*)
        new_line=$((new_line + 1))
        ;;
      *)
        # Headers (index, mode, Binary files, \ No newline...) carry no added
        # content lines; ignore them.
        ;;
    esac
  done <<<"$diff_text"
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
  added-lines)
    scan_added_lines "$@"
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
