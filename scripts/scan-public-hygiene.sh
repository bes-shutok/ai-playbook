#!/usr/bin/env bash
# scan-public-hygiene.sh - local public-instruction hygiene scan
# (tracked canonical source in repo-root scripts/; runtime copy at ~/.ai-playbook/scripts/)
#
# Usage (from instructions repo root):
#   bash scripts/scan-public-hygiene.sh                         # scan full tree (default)
#   bash scripts/scan-public-hygiene.sh --changed-from <ref>    # scan only files changed since <ref>
#   bash scripts/scan-public-hygiene.sh --files <path>...       # scan exactly the named files
#   bash scripts/scan-public-hygiene.sh --selftest              # run built-in self-tests
#   bash scripts/scan-public-hygiene.sh --help
#   PUBLIC_HYGIENE_REPO_ROOT=/path/to/ai-playbook bash scripts/scan-public-hygiene.sh
#
# Deny patterns: ~/.ai-playbook/public-hygiene.patterns (override: PUBLIC_HYGIENE_PATTERNS_FILE)
# Allowed personal contact: copyright email in **/LICENSE.txt only.

set -euo pipefail

ROOT="${PUBLIC_HYGIENE_REPO_ROOT:-.}"
PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-${HOME}/.ai-playbook/public-hygiene.patterns}"

# Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
# with exactly one final `OUTCOME:` row on stdout; --help and the --selftest
# diagnostic run are metadata modes and emit none.
emit_outcome() {
  printf 'OUTCOME: %s\n' "$1"
}

SCAN_STRICT=(agents/skills projects)
# Pattern-quoting sources (2026-09-27): detector implementations whose bytes
# carry the deny patterns themselves, their detection fixtures, and archived
# plans or backlog records that quote sweep commands or placeholder home
# paths. These files cannot be reworded without destroying what they record,
# so they are out of scan scope; real identifiers elsewhere are masked, not
# excluded.
# Declared owner of the allowlist glob surface (single-sourcing): GLOB_BODIES
# below is the one list a maintainer edits. GLOB_EXCLUDES is the rg-argument
# view derived from it at this same site, and _path_is_excluded plus the
# changed-from filter consume GLOB_BODIES through the shared matcher
# _path_matches_glob, so all three scan modes follow one list mechanically.
GLOB_BODIES=(
  '**/LICENSE.txt'
  'docs/facts.md.example'
  'docs/reviews/**'
  'docs/tmp/**'
  'agents/skills/done/SKILL.md'
  'agents/skills/how-to-write-skills/**'
  'docs/AGENTS.md'
  'AGENTS.md'
  'CLAUDE.md'
  'scripts/scan-public-hygiene.sh'
  'scripts/done_sweep_gates_lib.py'
  'scripts/test_done_sweep_gates_lib.py'
  'scripts/check_review_agent_portability.py'
  'scripts/test_check_review_agent_portability.py'
  'docs/history/plans/completed/2026-08-19-confluence-split-and-create-documentation-removal.md'
  'docs/history/plans/completed/2026-09-03-docs-branch-temp-file-hygiene.md'
  'docs/history/plans/completed/2026-09-04-sot-unification-living-docs-and-grill-escalation.md'
  'docs/history/plans/completed/2026-09-05-docs-branch-trap-before-restore-region.md'
  'docs/history/plans/completed/2026-09-08-run-start-marker-content-hash.md'
  'docs/history/plans/rejected/2026-09-07-straggler-wording-pins.md'
  'docs/history/backlog/rejected/2026-09-07-token-telemetry-r5-residuals.md'
  'docs/history/backlog/completed/2026-09-07-run-start-marker-content-docs-branch-leak.md'
)
# Derived rg-argument view of GLOB_BODIES; the frozen rg invocations consume
# this view unchanged.
GLOB_EXCLUDES=()
for _glob_body in "${GLOB_BODIES[@]}"; do
  GLOB_EXCLUDES+=("--glob" "!${_glob_body}")
done
unset _glob_body

# Usage message.
print_usage() {
  cat <<'EOF'
Usage: scan-public-hygiene.sh [--changed-from <ref>] [--files <path>...] [--selftest] [--help]

Modes:
  (no args)               Scan the full tracked tree (agents/skills, projects).
  --changed-from <ref>    Scan only files changed relative to <ref> (git diff <ref>:
                          working tree vs ref, including uncommitted edits) plus untracked
                          files under the scan scope.
  --files <path>...       Scan exactly the named files (tracked or untracked, relative to
                          the repo root), with the same built-in patterns, the same shared
                          patterns file, and the standard allowlist globs applied. Exit 1
                          on any hit; the script's own errors are tool errors (exit 3).
  --selftest              Run hermetic built-in self-tests (temp git repo, no live-repo mutation).
  --help                  Show this help.

Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
  with exactly one final stdout row: `OUTCOME: pass` (clean), `OUTCOME: fail`
  (findings), or `OUTCOME: tool_error` (the script's own error, exit 3).
  --help and the --selftest diagnostic run are metadata modes and emit no
  OUTCOME row.

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
    emit_outcome tool_error
    exit 3
  fi
}

# report_hits_for_paths <label> <pattern> <path...>
report_hits_for_paths() {
  local label="$1"
  local pattern="$2"
  shift 2
  local hits
  local rg_rc=0
  if [ "$label" = "files" ]; then
    # r1 F3: the explicit-paths mode hardens the rg invocation. The
    # allowlist globs stay option positions, then "--" closes option
    # parsing before the named paths, so a crafted filename can never be
    # parsed as an rg option; and an rg failure with exit > 1 (for example
    # an invalid regex line in the shared patterns file) is fatal (a tool
    # error, exit 3 under the outcome contract), never a silent pass. The
    # frozen full-tree and changed modes keep their argv and swallow-to-pass
    # behavior untouched.
    hits="$(rg -n --hidden "$pattern" "${GLOB_EXCLUDES[@]}" -- "$@" 2>/dev/null)" || rg_rc=$?
    if [ "$rg_rc" -gt 1 ]; then
      echo "FATAL: rg failed (exit $rg_rc) in files mode; check the patterns file" >&2
      emit_outcome tool_error
      exit 3
    fi
  else
    hits="$(rg -n --hidden "$pattern" "$@" "${GLOB_EXCLUDES[@]}" 2>/dev/null)" || rg_rc=$?
  fi
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
    emit_outcome fail
    exit 1
  fi
  echo "=== PASS (public hygiene) ==="
  emit_outcome pass
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
      agents/skills/*|projects/*) ;;
      *) continue ;;
    esac
    # Apply the declared allowlist (GLOB_BODIES) through the shared matcher,
    # the same list the full-tree and explicit-paths modes consume. The
    # SCAN_STRICT root filter above stays ahead of the matcher, so globs
    # outside the roots stay inert here.
    local excluded=0
    local g
    for g in "${GLOB_BODIES[@]}"; do
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

# True when a path matches one of the declared allowlist globs (GLOB_BODIES),
# consumed by the explicit-paths mode and the changed-from filter. The shared
# matcher carries rg doublestar semantics, so a bare root LICENSE.txt is
# excluded in every mode (the declared r3 F5 alignment: all modes agree).
#   $1 = path
_path_is_excluded() {
  local p="$1"
  local g
  for g in "${GLOB_BODIES[@]}"; do
    if _path_matches_glob "$p" "$g"; then
      return 0
    fi
  done
  return 1
}

# Shared glob matcher with rg doublestar semantics over the declared
# GLOB_BODIES list: a leading **/ matches zero or more directories (so a
# bare root LICENSE.txt matches '**/LICENSE.txt'), a trailing /** stays
# inside its prefix (docs/tmp/** must not match
# docs/history/backlog/draft.md), and plain entries match literally. This is
# the only copy of the matching logic; _path_is_excluded and the
# changed-from filter both consume it.
#   $1 = path, $2 = glob
_path_matches_glob() {
  local path="$1"
  local glob="$2"
  local rest prefix
  if [[ "$glob" == '**/'* ]]; then
    rest="${glob#'**/'}"
    if [[ "$rest" == *'/**' ]]; then
      prefix="${rest%'/**'}"
      [[ "$path" == "$prefix"/* ]]
    else
      [[ "$path" == "$rest" || "$path" == */"$rest" ]]
    fi
  elif [[ "$glob" == *'/**' ]]; then
    prefix="${glob%'/**'}"
    [[ "$path" == "$prefix"/* ]]
  else
    [[ "$path" == "$glob" ]]
  fi
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
    emit_outcome tool_error
    exit 3
  fi
  if [ -z "$files" ]; then
    echo "=== PASS (public hygiene, no changed files vs $ref) ==="
    emit_outcome pass
    exit 0
  fi
  run_scan "changed (vs $ref)" "$files"
  emit_verdict
}

# Lexically normalize a path argument: collapse "." segments and resolve
# ".." against the preceding segment. A leading ".." on a relative path is
# kept; on an absolute path it collapses toward the root. Used by the
# explicit-paths mode so the exclusion test matches the path the argument
# NAMES, not the spelling it arrived with (r2 overflow: a ..-path under an
# excluded prefix must not silently pass unscanned, and a ..-path that
# ducks into an excluded prefix must not silently escape it).
#   $1 = path
_normalize_path() {
  local p="$1"
  local absolute=false
  case "$p" in
    /*) absolute=true ;;
  esac
  local -a segs=()
  local -a parts=()
  local IFS='/'
  # shellcheck disable=SC2086
  read -r -a segs <<< "$p"
  local seg
  for seg in "${segs[@]}"; do
    case "$seg" in
      ""|".")
        ;;
      "..")
        if [ "${#parts[@]}" -gt 0 ]; then
          case "${parts[$(( ${#parts[@]} - 1 ))]}" in
            "..") parts+=("$seg") ;;
            *) unset 'parts[${#parts[@]}-1]' ;;
          esac
        elif ! $absolute; then
          parts+=("$seg")
        fi
        ;;
      *)
        parts+=("$seg")
        ;;
    esac
  done
  local out=""
  local idx
  for idx in "${!parts[@]}"; do
    if [ -n "$out" ]; then
      out="$out/${parts[$idx]}"
    else
      out="${parts[$idx]}"
    fi
  done
  if $absolute; then
    printf '/%s' "$out"
  else
    printf '%s' "$out"
  fi
}

cmd_files() {
  cd "$ROOT"
  _require_rg
  FAILS=0
  local kept=()
  local p
  for p in "$@"; do
    # r1 F3: input validation for the named paths. A path that is empty,
    # starts with a dash, or embeds a newline can smuggle itself past the
    # scan (as an rg option, or by not round-tripping the newline-joined
    # file list); fail closed on the script's own-error class (a tool
    # error, exit 3 under the outcome contract) instead of silently passing
    # an unscanned file.
    case "$p" in
      "")
        echo "FATAL: empty path argument" >&2
        emit_outcome tool_error
        exit 3
        ;;
      -*)
        echo "FATAL: path must not start with '-': $p" >&2
        emit_outcome tool_error
        exit 3
        ;;
      *$'\n'*)
        echo "FATAL: path must not contain a newline" >&2
        emit_outcome tool_error
        exit 3
        ;;
    esac
    if [ ! -f "$p" ]; then
      echo "FATAL: no such file: $p" >&2
      emit_outcome tool_error
      exit 3
    fi
    # Standard allowlist globs apply in explicit mode too: an excluded path
    # named on the command line is skipped, never scanned. r2 overflow: the
    # exclusion test matches the NORMALIZED path, never the literal
    # argument, so a ..-path cannot borrow an excluded prefix to slip past
    # the scan (or duck into one unnoticed), and the skip is audited so an
    # excluded named path is never silently dropped.
    local norm
    norm="$(_normalize_path "$p")"
    if _path_is_excluded "$norm"; then
      echo "note: skipped excluded path: $p (normalized: $norm)" >&2
    else
      kept+=("$p")
    fi
  done

  if [ "${#kept[@]}" -eq 0 ]; then
    echo "=== PASS (public hygiene, all named files excluded) ==="
    emit_outcome pass
    exit 0
  fi

  local list
  list="$(printf '%s\n' "${kept[@]}")"
  run_scan "files" "$list"
  emit_verdict
}

_require_rg() {
  if ! command -v rg >/dev/null 2>&1; then
    echo "FATAL: rg (ripgrep) required" >&2
    emit_outcome tool_error
    exit 3
  fi
}

_require_git() {
  if ! command -v git >/dev/null 2>&1; then
    echo "FATAL: git required for --changed-from" >&2
    emit_outcome tool_error
    exit 3
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
\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
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

  # Generalized selftest harness with strict verdict assertions: a pass
  # needs exit 0 plus the PASS marker; a fail needs exit 1 (a pattern hit)
  # plus a FAIL block; an rc=<N> expectation asserts the exact exit code,
  # so an own-error exit (3 under the outcome contract) is distinguishable
  # from a pattern hit and from a pass (r1 F10; r2 overflow D4 folded the
  # former selftest_check_files_rc third harness copy in here; r3 F7 folded
  # the last remaining copy, the changed-mode selftest_check, in here too,
  # so both modes run through this one harness). An optional --contains
  # needle pins output text, so a case cannot satisfy a rc/message
  # expectation via the wrong arm (r2 overflow T4). An optional --outcome
  # label (batch 2 Task 5, scripts/OUTCOME_CONTRACT.md) pins exactly one
  # final `OUTCOME: <label>` row on the run's output. Arguments after --
  # are passed to the scanner verbatim.
  selftest_check_files() {
    local name="$1"
    local expect="$2"   # pass | fail | rc=<N>
    shift 2
    local needle=""
    local want_outcome=""
    while :; do
      case "$1" in
        --contains) needle="$2"; shift 2 ;;
        --outcome) want_outcome="$2"; shift 2 ;;
        *) break ;;
      esac
    done
    if [ "$1" = "--" ]; then
      shift
    fi
    local actual_out
    local actual_rc
    set +e
    actual_out="$(PUBLIC_HYGIENE_REPO_ROOT="$repo" \
                  PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
                  bash "$0" "$@" 2>&1)"
    actual_rc=$?
    set -e
    local ok=false
    case "$expect" in
      pass)
        if [ "$actual_rc" -eq 0 ] && echo "$actual_out" | grep -q "PASS (public hygiene"; then
          ok=true
        fi
        ;;
      fail)
        if [ "$actual_rc" -eq 1 ] && echo "$actual_out" | grep -q "FAIL:"; then
          ok=true
        fi
        ;;
      rc=*)
        if [ "$actual_rc" -eq "${expect#rc=}" ]; then
          ok=true
        fi
        ;;
    esac
    if ! $ok; then
      echo "selftest FAIL: $name (expected $expect, got rc=$actual_rc)" >&2
      echo "$actual_out" >&2
      SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
      return
    fi
    if [ -n "$needle" ] && ! printf '%s\n' "$actual_out" | grep -qF -- "$needle"; then
      echo "selftest FAIL: $name (verdict matched, but output is missing the expected text: $needle)" >&2
      echo "$actual_out" >&2
      SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
      return
    fi
    if [ -n "$want_outcome" ]; then
      local outcome_rows final_row
      outcome_rows="$(printf '%s\n' "$actual_out" | grep -c '^OUTCOME: ' || true)"
      final_row="$(printf '%s\n' "$actual_out" | grep '^OUTCOME: ' | tail -n 1 || true)"
      if [ "$outcome_rows" -ne 1 ] || [ "$final_row" != "OUTCOME: $want_outcome" ]; then
        echo "selftest FAIL: $name (expected exactly one final 'OUTCOME: $want_outcome' row, got $outcome_rows row(s), last: '$final_row')" >&2
        echo "$actual_out" >&2
        SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
        return
      fi
    fi
    echo "selftest OK: $name"
  }

  # Changed-mode sub-tests 1 through 7 (r3 F7) run through the same
  # generalized harness as the files-mode sub-tests below: a fail case
  # asserts exit 1 plus the FAIL block, so an own-error run (a tool error,
  # exit 3) can never satisfy a fail expectation.

  # Sub-test 1: clean changed file → PASS.
  printf '# clean changed content\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "clean-changed-file-passes" pass -- \
    --changed-from "$baseline_sha"

  # Sub-test 2: changed file with absolute home path → FAIL.
  printf 'oops: /Users/leaked/changed\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "changed-file-abs-home-path-fails" fail -- \
    --changed-from "$baseline_sha"

  # Sub-test 3: changed file with local-pattern hit → FAIL.
  printf 'token FORBIDDEN-TOKEN here\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "changed-file-local-pattern-fails" fail -- \
    --changed-from "$baseline_sha"

  # Sub-test 4: changed file with Co-authored-by → FAIL.
  printf 'Co-authored-by: x <x@example.com>\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "changed-file-coauthored-fails" fail -- \
    --changed-from "$baseline_sha"

  # Sub-test 5: baseline dirty file NOT in changed set → must still PASS.
  #   (Restore clean content on the changed file so only the unchanged baseline
  #    file has a deny hit; the baseline file must be skipped.)
  printf '# clean again\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "unchanged-dirty-file-skipped" pass -- \
    --changed-from "$baseline_sha"

  # Sub-test 6: untracked file with deny hit → FAIL (untracked files included).
  # Create an untracked file under the scan scope and make the tracked file clean
  # so only the untracked file triggers the failure.
  printf '# clean tracked\n' > "$repo/agents/skills/clean/SKILL.md"
  printf 'untracked: /Users/leaked/untracked\n' > "$repo/agents/skills/untracked_new.md"
  selftest_check_files "untracked-file-with-hit-fails" fail -- \
    --changed-from "$baseline_sha"
  rm -f "$repo/agents/skills/untracked_new.md"

  # Sub-test 7: no changed files (empty diff after re-pointing baseline to
  # HEAD) → PASS (exit 0 plus the PASS marker).
  git -C "$repo" add -A
  git -C "$repo" commit -q -m "settle" || true
  local head_sha
  head_sha="$(git -C "$repo" rev-parse HEAD)"
  selftest_check_files "empty-diff-passes" pass -- --changed-from "$head_sha"

  # Sub-test 8: --files over a clean file → PASS.
  printf '# clean explicit file\n' > "$repo/agents/skills/clean/notes.md"
  selftest_check_files "files-clean-file-passes" pass -- \
    --files "agents/skills/clean/notes.md"

  # Sub-test 9: --files over a file carrying an absolute home path and a
  # local-pattern hit → FAIL (exit 1 on a hit, not an error exit).
  printf 'contact /Users/leaked/one and FORBIDDEN-TOKEN\n' > "$repo/agents/skills/clean/notes.md"
  selftest_check_files "files-abs-home-and-local-pattern-fail" fail -- \
    --files "agents/skills/clean/notes.md"

  # Sub-test 10: --files over a LICENSE.txt carrying a copyright email → PASS
  # (the allowlist glob applies in explicit mode too).
  mkdir -p "$repo/pkg"
  printf 'Copyright (c) 2026 Selftest Author <author@example.invalid>\n' > "$repo/pkg/LICENSE.txt"
  selftest_check_files "files-license-allowlist-passes" pass -- \
    --files "pkg/LICENSE.txt"

  # Sub-test 11: a named file outside the default scan roots is scanned when
  # named explicitly → FAIL on its deny hit.
  mkdir -p "$repo/docs/history/backlog"
  printf 'context: /Users/leaked/backlog-draft\n' > "$repo/docs/history/backlog/draft.md"
  selftest_check_files "files-outside-scan-roots-scanned" fail -- \
    --files "docs/history/backlog/draft.md"

  # r1 F10: the files mode's own error paths must fail closed on their own
  # error class, never pass or fail-as-hit. Batch 2 Task 5 remaps that class
  # to the outcome contract's tool error: exit 3 with exactly one final
  # `OUTCOME: tool_error` row (the legacy own-error exit 2 is retired).
  # r2 overflow T4: each case also pins its arm-specific message, so a case
  # cannot stay green via a different arm's exit code.

  # Sub-test 12: a named file that does not exist -> own error, exit 3.
  selftest_check_files "files-missing-file-own-error-exits-3" rc=3 \
    --outcome tool_error --contains "no such file" -- \
    --files "agents/skills/clean/does-not-exist.md"

  # Sub-test 13: a named path starting with a dash -> exit 3 (r1 F3 input
  # validation; it must never reach rg as an option). The dash-specific
  # message is asserted so the case cannot pass via the missing-file arm.
  selftest_check_files "files-dash-leading-path-own-error-exits-3" rc=3 \
    --outcome tool_error --contains "must not start with '-'" -- \
    --files "-weird.md"

  # Sub-test 14: --files combined with --changed-from -> exit 3 (a usage
  # violation is a tool error, not the legacy exit 2).
  selftest_check_files "files-changed-from-conflict-own-error-exits-3" rc=3 \
    --outcome tool_error --contains "cannot be combined" -- \
    --changed-from "$head_sha" --files "agents/skills/clean/notes.md"

  # r2 overflow T5: the empty-path and newline-embedded-path arms of
  # cmd_files are pinned with their own own-error cases.
  selftest_check_files "files-empty-path-own-error-exits-3" rc=3 \
    --outcome tool_error --contains "empty path" -- \
    --files ""
  selftest_check_files "files-newline-path-own-error-exits-3" rc=3 \
    --outcome tool_error --contains "must not contain a newline" -- \
    --files "$(printf 'a\nb.md')"

  # Batch 2 Task 5 outcome-emission arms (scripts/OUTCOME_CONTRACT.md): a
  # clean run ends with exactly one final `OUTCOME: pass` row on stdout, a
  # findings run ends with `OUTCOME: fail` after the hit rows, and an
  # own-error run exits 3 with `OUTCOME: tool_error`.
  printf '# clean outcome emission\n' > "$repo/agents/skills/clean/notes.md"
  selftest_check_files "files-clean-run-outcome-pass" pass --outcome pass -- \
    --files "agents/skills/clean/notes.md"

  printf 'outcome probe: /Users/leaked/outcome\n' > "$repo/agents/skills/clean/notes.md"
  selftest_check_files "files-findings-run-outcome-fail" fail --outcome fail -- \
    --files "agents/skills/clean/notes.md"

  selftest_check_files "files-own-error-outcome-tool-error" rc=3 \
    --outcome tool_error --contains "no such file" -- \
    --files "agents/skills/clean/absent-outcome-probe.md"

  # r2 overflow (literal-path-exclusion-bypass): the exclusion test runs on
  # the NORMALIZED path. A ..-path that escapes an excluded prefix is
  # scanned (the literal spelling must not blind the scan)...
  mkdir -p "$repo/docs/reviews"
  printf 'escape: /Users/leaked/dotdot-escape\n' > "$repo/docs/history/backlog/escape.md"
  selftest_check_files "files-dotdot-escape-from-excluded-prefix-scanned" fail \
    --contains "dotdot-escape" -- \
    --files "docs/reviews/../history/backlog/escape.md"
  # ...and a ..-path that ducks INTO an excluded prefix is skipped with an
  # audited skip line, never silently.
  printf 'hidden: /Users/leaked/dotdot-duck\n' > "$repo/docs/reviews/hit.md"
  selftest_check_files "files-dotdot-into-excluded-prefix-skipped" pass \
    --contains "skipped excluded path" -- \
    --files "docs/./reviews/hit.md"

  # Single-sourcing agreement arms: the scan modes must return the same
  # verdict for each allowlisted fixture shape (every fixture carries a deny
  # hit, so an exclusion shows up as a skip, never as clean content passing).
  mkdir -p "$repo/agents/skills/x" "$repo/docs/tmp" "$repo/docs/reviews"
  printf 'nested license: /Users/leaked/nested-license\n' > "$repo/agents/skills/x/LICENSE.txt"
  printf 'tmp child: /Users/leaked/tmp-child\n' > "$repo/docs/tmp/child.txt"
  printf 'review: /Users/leaked/review\n' > "$repo/docs/reviews/r.md"
  printf 'Copyright (c) 2026 Selftest Author <author@example.invalid>\n' > "$repo/LICENSE.txt"
  printf 'agree: /Users/leaked/clean-agree\n' > "$repo/agents/skills/clean/SKILL.md"

  # Direct arm on the explicit-paths predicate: the nested and prefix shapes
  # are excluded, and the root LICENSE.txt leg is pinned per the declared r3
  # F5 alignment direction (see the GLOB_BODIES declared-owner comment).
  if _path_is_excluded "agents/skills/x/LICENSE.txt" \
     && _path_is_excluded "docs/tmp/child.txt" \
     && _path_is_excluded "docs/reviews/r.md" \
     && _path_is_excluded "LICENSE.txt" \
     && ! _path_is_excluded "docs/history/backlog/draft.md" \
     && ! _path_is_excluded "agents/skills/clean/SKILL.md"; then
    echo "selftest OK: files-predicate-allowlist-shapes"
  else
    echo "selftest FAIL: files-predicate-allowlist-shapes" >&2
    SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
  fi

  # Cross-mode agreement arm: full-tree and explicit-paths verdicts must
  # agree per fixture (the fixture shows up in the full-tree output iff the
  # files mode reports a FAIL block for it).
  selftest_mode_agree() {
    local p="$1"
    local ft_out files_out ft_hit files_hit
    ft_hit=0
    files_hit=0
    set +e
    ft_out="$(PUBLIC_HYGIENE_REPO_ROOT="$repo" PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" bash "$0" 2>&1)"
    set -e
    if printf '%s\n' "$ft_out" | grep -qF "$p"; then
      ft_hit=1
    fi
    set +e
    files_out="$(PUBLIC_HYGIENE_REPO_ROOT="$repo" PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" bash "$0" --files "$p" 2>&1)"
    set -e
    if printf '%s\n' "$files_out" | grep -q "FAIL:"; then
      files_hit=1
    fi
    if [ "$ft_hit" -eq "$files_hit" ]; then
      echo "selftest OK: mode-agreement ($p)"
    else
      echo "selftest FAIL: mode-agreement ($p) full-tree-hit=$ft_hit files-hit=$files_hit" >&2
      SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
    fi
  }
  selftest_mode_agree "agents/skills/x/LICENSE.txt"
  selftest_mode_agree "docs/tmp/child.txt"
  selftest_mode_agree "docs/reviews/r.md"
  selftest_mode_agree "LICENSE.txt"
  selftest_mode_agree "agents/skills/clean/SKILL.md"

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
  local file_paths=()

  # Usage violations are the script's own-error class: a tool error under
  # the outcome contract (exit 3, final `OUTCOME: tool_error` row on
  # stdout after the usage text on stderr).
  usage_error() {
    echo "FATAL: $1" >&2
    if [ "${2:-}" = "usage" ]; then
      print_usage >&2
    fi
    emit_outcome tool_error
    exit 3
  }

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --help|-h)
        print_usage
        exit 0
        ;;
      --selftest)
        if [ "$#" -gt 1 ]; then
          usage_error "--selftest takes no argument"
        fi
        cmd_selftest
        exit $?
        ;;
      --files)
        if [ "$mode" != "full-tree" ]; then
          usage_error "--files cannot be combined with --changed-from"
        fi
        mode="files"
        shift
        break   # every remaining argument is a file path
        ;;
      --changed-from)
        if [ "$#" -lt 2 ]; then
          usage_error "--changed-from requires a <ref> argument" usage
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
        usage_error "unknown option: $1" usage
        ;;
      *)
        usage_error "unexpected argument: $1" usage
        ;;
    esac
  done

  if [ "$mode" = "files" ]; then
    if [ "$#" -eq 0 ]; then
      usage_error "--files requires at least one <path>" usage
    fi
    file_paths=("$@")
  elif [ "$#" -gt 0 ]; then
    usage_error "unexpected positional arguments: $*" usage
  fi

  case "$mode" in
    full-tree) cmd_full_tree ;;
    changed)   cmd_changed_from "$changed_ref" ;;
    files)     cmd_files "${file_paths[@]}" ;;
  esac
}

main "$@"
