#!/usr/bin/env bash
# Measure always-loaded instruction files against a byte budget (default 30,720; see learn/done skills).
# Modes: check | gate | hook-warn
set -euo pipefail

MODE="${1:-check}"

# Budget matches learn Step 6.5 / done Step 2.8 (override for local testing via env only).
MAX_BYTES="${INSTRUCTION_FILE_MAX_BYTES:-30720}"

DEFAULT_FILES=(AGENTS.md CLAUDE.md GEMINI.md COPILOT.md)
if [[ -n "${INSTRUCTION_FILES:-}" ]]; then
  # shellcheck disable=SC2206
  FILES=(${INSTRUCTION_FILES})
else
  FILES=("${DEFAULT_FILES[@]}")
fi

measure_file() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  wc -c <"$path" | tr -d ' '
}

list_oversized() {
  local path bytes
  for path in "${FILES[@]}"; do
    [[ -f "$path" ]] || continue
    bytes="$(measure_file "$path")"
    if (( bytes > MAX_BYTES )); then
      printf '%s:%s\n' "$path" "$bytes"
    fi
  done
}

print_report() {
  local dest="${1:-2}"
  local overs
  overs="$(list_oversized || true)"
  if [[ -z "$overs" ]]; then
    return 0
  fi
  {
    echo "Instruction size over budget (${MAX_BYTES} bytes max):"
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      local f="${line%%:*}"
      local b="${line#*:}"
      echo "  ${f}: ${b} bytes"
    done <<<"$overs"
    echo "Place full rule text in the canonical guideline tier first; keep instruction files to one-line cross-references. Run learn compaction before /done when these files change."
  } >&"$dest"
}

is_instruction_path() {
  local rel="$1"
  local base
  base="$(basename "$rel")"
  local candidate
  for candidate in "${FILES[@]}"; do
    [[ "$base" == "$candidate" ]] && return 0
  done
  return 1
}

case "$MODE" in
  check)
    overs="$(list_oversized || true)"
    if [[ -n "$overs" ]]; then
      print_report 2
      exit 1
    fi
    exit 0
    ;;

  gate)
    overs="$(list_oversized || true)"
    if [[ -z "$overs" ]]; then
      exit 0
    fi
    changed="$( {
      git diff --name-only 2>/dev/null || true
      git diff --cached --name-only 2>/dev/null || true
    } | sort -u)"
    blocked=0
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      f="${line%%:*}"
      if echo "$changed" | grep -Fxq "$f"; then
        blocked=1
      fi
    done <<<"$overs"
    if (( blocked )); then
      print_report 2
      exit 1
    fi
    exit 0
    ;;

  hook-warn)
    if ! command -v jq >/dev/null 2>&1; then
      echo '{"permission":"allow"}'
      exit 0
    fi
    input="$(cat)"
    cwd="$(echo "$input" | jq -r '.cwd // empty')"
    file_path="$(echo "$input" | jq -r '.tool_input.path // .tool_input.file_path // empty')"
    if [[ -z "$cwd" || -z "$file_path" ]]; then
      echo '{"permission":"allow"}'
      exit 0
    fi
    if [[ "$file_path" != /* ]]; then
      file_path="${cwd}/${file_path}"
    fi
    rel="${file_path#"$cwd"/}"
    rel="${rel#/}"
    if ! is_instruction_path "$rel"; then
      echo '{"permission":"allow"}'
      exit 0
    fi
    if [[ ! -f "$file_path" ]]; then
      echo '{"permission":"allow"}'
      exit 0
    fi
    bytes="$(measure_file "$file_path")"
    if (( bytes <= MAX_BYTES )); then
      echo '{"permission":"allow"}'
      exit 0
    fi
    msg="${rel} is ${bytes} bytes (budget ${MAX_BYTES}). Put full rule text in the canonical guideline doc; keep a one-line cross-reference in instruction files. Run learn compaction before /done."
    jq -n --arg am "$msg" '{permission: "allow", agent_message: $am}'
    exit 0
    ;;

  *)
    echo "Usage: $0 [check|gate|hook-warn]" >&2
    exit 2
    ;;
esac
