#!/usr/bin/env bash
# scan-public-hygiene.sh - local public-instruction hygiene scan (tracked canonical source in repo-root scripts/; runtime copy at ~/.ai-playbook/scripts/)
#
# Usage (from instructions repo root):
#   bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
#   PUBLIC_HYGIENE_REPO_ROOT=/path/to/ai-playbook bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
#
# Deny patterns: ~/.ai-playbook/public-hygiene.patterns (override: PUBLIC_HYGIENE_PATTERNS_FILE)
# Allowed personal contact: copyright email in **/LICENSE.txt only.

set -euo pipefail

ROOT="${PUBLIC_HYGIENE_REPO_ROOT:-.}"
cd "$ROOT"

if ! command -v rg >/dev/null 2>&1; then
  echo "FATAL: rg (ripgrep) required" >&2
  exit 2
fi

PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-${HOME}/.ai-playbook/public-hygiene.patterns}"

SCAN_STRICT=(agents/skills create-documentation projects)
GLOB_EXCLUDES=(
  --glob '!**/LICENSE.txt'
  --glob '!docs/facts.md.example'
  --glob '!docs/reviews/**'
  --glob '!docs/tmp/**'
  --glob '!agents/skills/done/SKILL.md'
  --glob '!agents/skills/how-to-write-skills/**'
  --glob '!docs/AGENTS.md'
  --glob '!AGENTS.md'
  --glob '!CLAUDE.md'
)

FAILS=0

report_hits() {
  local label="$1"
  local pattern="$2"
  local hits
  hits="$(rg -n --hidden "$pattern" "${SCAN_STRICT[@]}" "${GLOB_EXCLUDES[@]}" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    echo "FAIL: $label"
    echo "$hits"
    echo
    FAILS=$((FAILS + 1))
  fi
}

report_hits "absolute home paths" '/Users/|/home/[a-zA-Z0-9._-]+/'
report_hits "Co-authored-by trailers with email" 'Co-[Aa]uthored-[Bb]y:\s+.+<[^>]+@[^>]+>'

if [ -f "$PATTERNS_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    report_hits "local pattern: $line" "$line"
  done < "$PATTERNS_FILE"
else
  echo "FATAL: missing $PATTERNS_FILE (copy from docs/scan-public-hygiene.patterns.example in instructions repo)" >&2
  exit 2
fi

if [ "$FAILS" -gt 0 ]; then
  echo "=== $FAILS public-hygiene failure(s) ==="
  exit 1
fi

echo "=== PASS (public hygiene) ==="
exit 0
