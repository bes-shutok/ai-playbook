#!/usr/bin/env bash
# scan-public-hygiene.sh - local public-instruction hygiene scan
# (tracked canonical source in repo-root scripts/; runtime copy at ~/.ai-playbook/scripts/)
#
# Usage (from instructions repo root):
#   bash scripts/scan-public-hygiene.sh                         # scan full tree (default)
#   bash scripts/scan-public-hygiene.sh --changed-from <ref>    # scan only files changed since <ref>
#   bash scripts/scan-public-hygiene.sh --selftest              # run built-in self-tests
#   bash scripts/scan-public-hygiene.sh --help
#   PUBLIC_HYGIENE_REPO_ROOT=/path/to/ai-playbook bash scripts/scan-public-hygiene.sh
#
# Deny patterns: ~/.ai-playbook/public-hygiene.patterns (override: PUBLIC_HYGIENE_PATTERNS_FILE)
# Allowed personal contact: copyright email in **/LICENSE.txt only.

set -euo pipefail

ROOT="${PUBLIC_HYGIENE_REPO_ROOT:-.}"
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

# Usage message.
print_usage() {
  cat <<'EOF'
Usage: scan-public-hygiene.sh [--changed-from <ref>] [--selftest] [--help]

Modes:
  (no args)               Scan the full tracked tree (agents/skills, create-documentation, projects).
  --changed-from <ref>    Scan only files changed relative to <ref> (git diff <ref>:
                          working tree vs ref, including uncommitted edits) plus untracked
                          files under the scan scope.
  --selftest              Run hermetic built-in self-tests (temp git repo, no live-repo mutation).
  --help                  Show this help.

Environment:
  PUBLIC_HYGIENE_REPO_ROOT        Repo root to scan (default: current dir).
  PUBLIC_HYGIENE_PATTERNS_FILE    Local deny-patterns file (default: ~/.ai-playbook/public-hygiene.patterns).
EOF
}

# Run the deny-pattern scan over a given set of path arguments.
#   $1 = mode label ("full-tree" | "changed")
#   $2 = path-args specifier:
#        "SCAN_STRICT" → use the full scan roots (full-tree mode)
#        otherwise     → the literal list of files to scan (already filtered to scope + excludes)
# Increments FAILS for each pattern with hits; prints FAIL blocks.
run_scan() {
  local mode="$1"; shift
  local paths_kind="$1"; shift

  local rg_paths=()
  if [ "$paths_kind" = "SCAN_STRICT" ]; then
    rg_paths=("${SCAN_STRICT[@]}")
  else
    # paths_kind already holds the file list as a single string; split on newlines.
    while IFS= read -r p; do
      [ -n "$p" ] && rg_paths+=("$p")
    done <<<"$paths_kind"
  fi

  # If the changed-file list is empty, nothing to scan.
  if [ "${#rg_paths[@]}" -eq 0 ]; then
    return 0
  fi

  report_hits_for_paths "$mode" '/Users/|/home/[a-zA-Z0-9._-]+/' "${rg_paths[@]}"
  report_hits_for_paths "$mode" 'Co-[Aa]uthored-[Bb]y:\s+.+<[^>]+@[^>]+>' "${rg_paths[@]}"

  if [ -f "$PATTERNS_FILE" ]; then
    local line
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%%#*}"
      line="${line#"${line%%[![:space:]]*}"}"
      line="${line%"${line##*[![:space:]]}"}"
      [ -z "$line" ] && continue
      report_hits_for_paths "$mode" "$line" "${rg_paths[@]}"
    done < "$PATTERNS_FILE"
  else
    echo "FATAL: missing $PATTERNS_FILE (copy from docs/scan-public-hygiene.patterns.example in instructions repo)" >&2
    exit 2
  fi
}

# report_hits_for_paths <label> <pattern> <path...>
report_hits_for_paths() {
  local label="$1"
  local pattern="$2"
  shift 2
  local hits
  hits="$(rg -n --hidden "$pattern" "$@" "${GLOB_EXCLUDES[@]}" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    echo "FAIL: $label"
    echo "$hits"
    echo
    FAILS=$((FAILS + 1))
  fi
}

# Emit final pass/fail verdict and exit with the right code.
emit_verdict() {
  if [ "$FAILS" -gt 0 ]; then
    echo "=== $FAILS public-hygiene failure(s) ==="
    exit 1
  fi
  echo "=== PASS (public hygiene) ==="
  exit 0
}

# Compute the list of changed files (tracked + untracked) under the scan scope,
# with GLOB_EXCLUDES applied. Prints one path per line to stdout.
#   $1 = git ref
changed_files_in_scope() {
  local ref="$1"
  local tmp_tracked tmp_untracked tmp_all tmp_err
  tmp_tracked="$(mktemp)"
  tmp_untracked="$(mktemp)"
  tmp_all="$(mktemp)"
  tmp_err="$(mktemp)"

  # Tracked changes: working tree vs <ref>. This catches staged + unstaged
  # modifications (added/modified/deleted) relative to the ref. We compare the
  # working tree directly so uncommitted-but-tracked edits are included.
  if ! git diff --name-only "$ref" >"$tmp_tracked" 2>"$tmp_err"; then
    cat "$tmp_err" >&2
    echo "FATAL: git diff against ref '$ref' failed" >&2
    rm -f "$tmp_tracked" "$tmp_untracked" "$tmp_all" "$tmp_err"
    return 1
  fi
  rm -f "$tmp_err"

  # Untracked files (not yet committed) under any path.
  git ls-files --others --exclude-standard > "$tmp_untracked" 2>/dev/null || true

  cat "$tmp_tracked" "$tmp_untracked" | sort -u > "$tmp_all"

  # Filter to existing files under one of the SCAN_STRICT roots.
  local out=""
  local p
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    [ -f "$p" ] || continue
    case "$p" in
      agents/skills/*|create-documentation/*|projects/*) ;;
      *) continue ;;
    esac
    # Apply the same GLOB_EXCLUDES the full-tree scan uses, by matching each
    # exclude glob against the path.
    local excluded=0
    local g
    for g in \
      '**/LICENSE.txt' \
      'docs/facts.md.example' \
      'docs/reviews/**' \
      'docs/tmp/**' \
      'agents/skills/done/SKILL.md' \
      'agents/skills/how-to-write-skills/**' \
      'docs/AGENTS.md' \
      'AGENTS.md' \
      'CLAUDE.md'
    do
      if _path_matches_glob "$p" "$g"; then
        excluded=1
        break
      fi
    done
    [ "$excluded" -eq 1 ] && continue
    printf '%s\n' "$p"
  done < "$tmp_all"

  rm -f "$tmp_tracked" "$tmp_untracked" "$tmp_all"
  return 0
}

# Match a path against a glob that may use ** (doublestar). Bash extglob handles
# the single-star and trailing-/** cases; we approximate ** as a greedy match.
#   $1 = path, $2 = glob
_path_matches_glob() {
  local path="$1"
  local glob="$2"
  # Translate the glob to an extglob pattern bash [[ ]] understands.
  # **/  → */ (zero or more dirs) — use a custom check via pattern matching.
  case "$glob" in
    '**/LICENSE.txt')
      [[ "$path" == */LICENSE.txt ]] ;;
    'docs/reviews/**'|'docs/tmp/**')
      local prefix="${glob%%/**}"
      [[ "$path" == "$prefix"/* ]] ;;
    'agents/skills/how-to-write-skills/**')
      [[ "$path" == agents/skills/how-to-write-skills/* ]] ;;
    *)
      # Literal or simple glob: use bash pattern match.
      [[ "$path" == $glob ]] ;;
  esac
}

cmd_full_tree() {
  cd "$ROOT"
  _require_rg
  FAILS=0
  run_scan "full-tree" "SCAN_STRICT"
  emit_verdict
}

cmd_changed_from() {
  local ref="$1"
  cd "$ROOT"
  _require_rg
  _require_git
  FAILS=0
  local files
  if ! files="$(changed_files_in_scope "$ref")"; then
    exit 2
  fi
  if [ -z "$files" ]; then
    echo "=== PASS (public hygiene, no changed files vs $ref) ==="
    exit 0
  fi
  run_scan "changed (vs $ref)" "$files"
  emit_verdict
}

_require_rg() {
  if ! command -v rg >/dev/null 2>&1; then
    echo "FATAL: rg (ripgrep) required" >&2
    exit 2
  fi
}

_require_git() {
  if ! command -v git >/dev/null 2>&1; then
    echo "FATAL: git required for --changed-from" >&2
    exit 2
  fi
}

# --- selftest ---------------------------------------------------------------

cmd_selftest() {
  _require_rg
  _require_git

  local tmp
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/pubhyg-selftest.XXXXXX")"
  # shellcheck disable=SC2064
  trap "rm -rf '$tmp'" EXIT

  local repo="$tmp/repo"
  mkdir -p "$repo"
  git -C "$repo" init -q
  git -C "$repo" config user.email "selftest@example.invalid"
  git -C "$repo" config user.name "selftest"
  git -C "$repo" config commit.gpgsign false

  local patterns="$tmp/patterns"
  cat > "$patterns" <<'EOF'
# selftest local deny patterns
\bFORBIDDEN-TOKEN\b
EOF

  # Baseline: an unchanged dirty file (should NOT be reported in changed mode).
  mkdir -p "$repo/agents/skills/pdf"
  printf 'baseline dirty: /Users/leaked/baseline\n' > "$repo/agents/skills/pdf/SKILL.md"
  mkdir -p "$repo/agents/skills/clean"
  printf '# clean baseline\n' > "$repo/agents/skills/clean/SKILL.md"
  git -C "$repo" add -A
  git -C "$repo" commit -q -m "baseline"

  local baseline_sha
  baseline_sha="$(git -C "$repo" rev-parse HEAD)"

  SELFTEST_FAILS=0

  selftest_check() {
    local name="$1"
    local expect="$2"   # pass | fail
    local actual_out
    local actual_rc
    set +e
    actual_out="$(PUBLIC_HYGIENE_REPO_ROOT="$repo" \
                  PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
                  bash "$0" --changed-from "$baseline_sha" 2>&1)"
    actual_rc=$?
    set -e
    local actual
    if [ "$actual_rc" -eq 0 ]; then actual="pass"; else actual="fail"; fi
    if [ "$actual" != "$expect" ]; then
      echo "selftest FAIL: $name — expected $expect, got $actual (rc=$actual_rc)" >&2
      echo "$actual_out" >&2
      SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
      return
    fi
    echo "selftest OK: $name"
  }

  # Sub-test 1: clean changed file → PASS.
  printf '# clean changed content\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check "clean-changed-file-passes" pass

  # Sub-test 2: changed file with absolute home path → FAIL.
  printf 'oops: /Users/leaked/changed\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check "changed-file-abs-home-path-fails" fail

  # Sub-test 3: changed file with local-pattern hit → FAIL.
  printf 'token FORBIDDEN-TOKEN here\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check "changed-file-local-pattern-fails" fail

  # Sub-test 4: changed file with Co-authored-by → FAIL.
  printf 'Co-authored-by: x <x@example.com>\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check "changed-file-coauthored-fails" fail

  # Sub-test 5: baseline dirty file NOT in changed set → must still PASS.
  #   (Restore clean content on the changed file so only the unchanged baseline
  #    file has a deny hit; the baseline file must be skipped.)
  printf '# clean again\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check "unchanged-dirty-file-skipped" pass

  # Sub-test 6: untracked file with deny hit → FAIL (untracked files included).
  # Create an untracked file under the scan scope and make the tracked file clean
  # so only the untracked file triggers the failure.
  printf '# clean tracked\n' > "$repo/agents/skills/clean/SKILL.md"
  printf 'untracked: /Users/leaked/untracked\n' > "$repo/agents/skills/untracked_new.md"
  selftest_check "untracked-file-with-hit-fails" fail
  rm -f "$repo/agents/skills/untracked_new.md"

  # Sub-test 7: no changed files (empty diff after re-pointing baseline to HEAD).
  git -C "$repo" add -A
  git -C "$repo" commit -q -m "settle" || true
  local head_sha
  head_sha="$(git -C "$repo" rev-parse HEAD)"
  SELFTEST_HEAD_OUT="$(PUBLIC_HYGIENE_REPO_ROOT="$repo" \
                       PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
                       bash "$0" --changed-from "$head_sha" 2>&1)" || true
  if echo "$SELFTEST_HEAD_OUT" | grep -q "PASS"; then
    echo "selftest OK: empty-diff-passes"
  else
    echo "selftest FAIL: empty-diff-passes — expected PASS, got:" >&2
    echo "$SELFTEST_HEAD_OUT" >&2
    SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
  fi

  if [ "$SELFTEST_FAILS" -gt 0 ]; then
    echo "scan-public-hygiene: --selftest FAILED ($SELFTEST_FAILS)" >&2
    return 1
  fi
  echo "scan-public-hygiene: --selftest ok"
  return 0
}

# --- entry point ------------------------------------------------------------

main() {
  local mode="full-tree"
  local changed_ref=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --help|-h)
        print_usage
        exit 0
        ;;
      --selftest)
        if [ "$#" -gt 1 ]; then
          echo "FATAL: --selftest takes no argument" >&2
          exit 2
        fi
        cmd_selftest
        exit $?
        ;;
      --changed-from)
        if [ "$#" -lt 2 ]; then
          echo "FATAL: --changed-from requires a <ref> argument" >&2
          exit 2
        fi
        mode="changed"
        changed_ref="$2"
        shift 2
        ;;
      --changed-from=*)
        mode="changed"
        changed_ref="${1#--changed-from=}"
        shift
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "FATAL: unknown option: $1" >&2
        print_usage >&2
        exit 2
        ;;
      *)
        echo "FATAL: unexpected argument: $1" >&2
        print_usage >&2
        exit 2
        ;;
    esac
  done

  if [ "$#" -gt 0 ]; then
    echo "FATAL: unexpected positional arguments: $*" >&2
    print_usage >&2
    exit 2
  fi

  case "$mode" in
    full-tree) cmd_full_tree ;;
    changed)   cmd_changed_from "$changed_ref" ;;
  esac
}

main "$@"
