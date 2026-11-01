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

# rg reads $RIPGREP_CONFIG_PATH as an extra config file when set: a planted
# config could silently weaken or redirect the scan (the same environment-
# poisoning class the git_enumerate scrub defends against for git), so it
# is cleared here before any rg invocation.
unset RIPGREP_CONFIG_PATH

ROOT="${PUBLIC_HYGIENE_REPO_ROOT:-.}"
PATTERNS_FILE="${PUBLIC_HYGIENE_PATTERNS_FILE:-${HOME}/.ai-playbook/public-hygiene.patterns}"

# Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
# with exactly one final `OUTCOME:` row on stdout; --help and the --selftest
# diagnostic run are metadata modes and emit none.
emit_outcome() {
  printf 'OUTCOME: %s\n' "$1"
}

SCAN_STRICT=(agents/skills projects)
# The deny patterns every scan mode runs over its own scope: the two built-in
# patterns and the shared patterns file's active lines. One list, so the
# blocking roots and the report-only tracked scope below can never drift
# apart on pattern membership.
BUILTIN_PATTERNS=(
  '/Users/|/home/[a-zA-Z0-9._-]+/'
  'Co-[Aa]uthored-[Bb]y:\s+.+<[^>]+@[^>]+>'
)
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
  'agents/skills/done/**'
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
  'docs/history/plans/completed/2026-10-18-review-runtime-sibling-module-deployment.md'
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
  (no args)               Blocking scan of agents/skills and projects
                          (working tree, untracked included); a hit fails
                          the run. Beside it, tracked regular blobs outside
                          those roots (symlinks and gitlinks excluded) are a
                          report-only scope: a match emits a
                          `PUBLIC_HYGIENE_REPORT: path=...` record and never
                          fails the run; enumeration failure emits
                          `PUBLIC_HYGIENE_REPORT: enumeration-unavailable`,
                          an rg scan failure after successful enumeration
                          emits `PUBLIC_HYGIENE_REPORT: scan-unavailable`,
                          and either skips only that scope. A missing or unreadable
                          patterns file fails the scan (tool error); the
                          report arm's patterns-unavailable record exists
                          only for direct programmatic invocation.
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

# The shared patterns file's active deny patterns, one per line (comments and
# blank lines stripped). The one reader for that file: run_scan (blocking
# modes) and run_report_scan (the report-only tracked scope) both consume it,
# so pattern membership can never drift between them.
_patterns_from_file() {
  local line
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    printf '%s\n' "$line"
  done < "$PATTERNS_FILE"
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
  local p
  if [ "$paths_kind" = "SCAN_STRICT" ]; then
    # Only existing roots are passed: rg exits 2 on a missing named path,
    # and since the fail-closed arm (2026-10-31) that exit is fatal, so a
    # repo without one of the declared roots must skip it here rather than
    # fail the whole scan.
    for p in "${SCAN_STRICT[@]}"; do
      [ -e "$p" ] && rg_paths+=("$p")
    done
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

  local pattern
  for pattern in "${BUILTIN_PATTERNS[@]}"; do
    report_hits_for_paths "$mode" "$pattern" "${rg_paths[@]}"
  done

  # r3 F1: the read gate is -r, not just -f. The file patterns ride a
  # process substitution, whose failure the parent cannot observe, so a
  # file that exists but is unreadable must be refused here: otherwise the
  # blocking scan silently degrades to builtin-only patterns and can exit 0
  # on a patterns-file-only hit.
  if [ -f "$PATTERNS_FILE" ] && [ -r "$PATTERNS_FILE" ]; then
    local line
    while IFS= read -r line; do
      report_hits_for_paths "$mode" "$line" "${rg_paths[@]}"
    done < <(_patterns_from_file)
  else
    echo "FATAL: missing or unreadable $PATTERNS_FILE (copy from docs/scan-public-hygiene.patterns.example in instructions repo)" >&2
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
    # r1 F3: the explicit-paths mode hardens the rg invocation. The allowlist
    # globs stay option positions, then "--" closes option parsing before
    # the named paths, so a crafted filename can never be parsed as an rg
    # option; the pattern rides -e so an active patterns line starting with
    # "-" cannot be parsed as options either (r3 F4); and an rg failure with
    # exit > 1 (for example an invalid regex line in the shared patterns
    # file) is fatal (a tool error, exit 3 under the outcome contract),
    # never a silent pass.
    hits="$(rg -n --hidden -e "$pattern" "${GLOB_EXCLUDES[@]}" -- "$@" 2>/dev/null)" || rg_rc=$?
    if [ "$rg_rc" -gt 1 ]; then
      echo "FATAL: rg failed (exit $rg_rc) in files mode; check the patterns file" >&2
      emit_outcome tool_error
      exit 3
    fi
  else
    # r2 comment residual, closed 2026-10-31: the frozen full-tree and changed
    # modes now mirror the files branch's fail-closed shape. Previously they
    # passed the pattern as a positional rg argument and swallowed exit > 1,
    # so a dash-led active patterns line was silently unapplied to the
    # blocking roots and an invalid regex degraded to pass.
    hits="$(rg -n --hidden -e "$pattern" "${GLOB_EXCLUDES[@]}" -- "$@" 2>/dev/null)" || rg_rc=$?
    if [ "$rg_rc" -gt 1 ]; then
      echo "FATAL: rg failed (exit $rg_rc) in $label mode; check the patterns file" >&2
      emit_outcome tool_error
      exit 3
    fi
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
  register_tmp "$tmp_tracked" "$tmp_untracked" "$tmp_all" "$tmp_err"

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
  emit_report_scope
  emit_verdict
}

# --- report-only tracked scope (default mode) -------------------------------

# Tracked-scope Git enumeration, hardened: the subshell pins the repo root
# (PUBLIC_HYGIENE_REPO_ROOT) and clears inherited Git repository overrides,
# so a decoy GIT_DIR or GIT_WORK_TREE in the caller's environment cannot
# redirect the enumeration to another repository or index, and the global
# and system config files cannot contribute a redirect either (r3 F5:
# GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM join the scrub beside the
# GIT_CONFIG_NOSYSTEM export). NUL-delimited output, so any filename byte
# survives the stream.
git_enumerate() {
  (
    cd "$ROOT" || exit 9
    unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_GRAFT_FILE \
      GIT_NAMESPACE GIT_CONFIG GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT \
      GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
    GIT_CONFIG_NOSYSTEM=1
    export GIT_CONFIG_NOSYSTEM
    exec git ls-files -s -z 2>/dev/null
  )
}

# Populate REPORT_SCOPE_PATHS with the report-only tracked scope: tracked
# regular blobs (index modes 100644/100755) outside the blocking roots, as
# existing working-tree regular files, under the shared exclusions
# (GLOB_BODIES through the shared matcher). Tracked symlinks (120000) and
# gitlinks (160000) carry no scannable blob content and never enter the set.
# Returns 1 when Git enumeration fails; the caller then emits the fixed
# enumeration-unavailable record and skips only this scope.
collect_report_scope_paths() {
  REPORT_SCOPE_PATHS=()
  local tmp_enum rec meta mode path
  tmp_enum="$(mktemp "${TMPDIR:-/tmp}/pubhyg-enum.XXXXXX")" || return 1
  register_tmp "$tmp_enum"
  if ! git_enumerate >"$tmp_enum"; then
    rm -f "$tmp_enum"
    return 1
  fi
  while IFS= read -r -d '' rec; do
    meta="${rec%%$'\t'*}"
    mode="${meta%% *}"
    case "$mode" in
      100644|100755) ;;
      *) continue ;;
    esac
    path="${rec#*$'\t'}"
    case "$path" in
      agents/skills|projects|agents/skills/*|projects/*) continue ;;
    esac
    [ -f "$path" ] || continue
    [ -L "$path" ] && continue
    _path_is_excluded "$path" && continue
    REPORT_SCOPE_PATHS+=("$path")
  done <"$tmp_enum"
  rm -f "$tmp_enum"
  return 0
}

# Byte-wise reversible ASCII-only JSON quoting of a filename: printable ASCII
# bytes pass through (double quote and backslash escaped), and every other
# byte, including undecodable ones, becomes a \u00XX escape. The result is
# pure ASCII with no raw terminal controls and represents every filename
# byte, so a report record can neither leak nor mangle a crafted name.
json_quote_path() {
  local hex out="" i=0 pair code ch
  hex="$(printf '%s' "$1" | od -An -v -tx1 | tr -d ' \n')"
  while [ "$i" -lt "${#hex}" ]; do
    pair="${hex:$i:2}"
    code=$(( 16#${pair} ))
    if [ "$code" -ge 32 ] && [ "$code" -le 126 ]; then
      case "$pair" in
        22) out+='\"' ;;
        5c) out+='\\' ;;
        *) printf -v ch '%b' "\\0$(printf '%03o' "$code")"; out+="$ch" ;;
      esac
    else
      out+="\\u00${pair}"
    fi
    i=$(( i + 2 ))
  done
  printf '%s' "$out"
}

# Scan the report-only tracked scope with the same deny patterns as the
# blocking scan (BUILTIN_PATTERNS plus the shared patterns file through the
# one shared reader) and emit one `PUBLIC_HYGIENE_REPORT: path=...` record
# per matching file, paths after `--` so option-shaped names stay paths.
# Never touches FAILS or the exit code: an enumeration failure emits the
# fixed enumeration-unavailable record, an rg scan failure after successful
# enumeration emits the fixed scan-unavailable record (r2 F4a: no longer
# mislabeled enumeration-unavailable; same prefix grammar, so the done
# gate's verbatim forwarding is unchanged), and a missing-or-unreadable
# shared patterns file emits the fixed patterns-unavailable record
# (r3 F1), each skipping only this scope, and matched file content never
# reaches the output (plan 2026-10-26-hygiene-scanner-default-scope-parity).
run_report_scan() {
  local rc=0 pattern p
  # r3 F1: same read gate as the blocking consumer, for the same reason: a
  # file that exists but is unreadable must never silently degrade this
  # scope to builtin-only pattern membership. The fixed record keeps the
  # PUBLIC_HYGIENE_REPORT: prefix grammar, so the done gate's forwarding is
  # unchanged.
  if [ ! -f "$PATTERNS_FILE" ] || [ ! -r "$PATTERNS_FILE" ]; then
    echo "PUBLIC_HYGIENE_REPORT: patterns-unavailable"
    return 0
  fi
  local tmp_matches
  tmp_matches="$(mktemp "${TMPDIR:-/tmp}/pubhyg-report.XXXXXX")" || {
    echo "PUBLIC_HYGIENE_REPORT: enumeration-unavailable"
    return 0
  }
  register_tmp "$tmp_matches"
  # r2 design-simplicity c1: the builtin and shared-file patterns ride one
  # rg pass as repeated -e flags (the previous shape ran one rg per pattern
  # over the same scope), removing the duplicated loop and the per-pattern
  # process churn without changing the record grammar.
  local -a pattern_args=()
  for pattern in "${BUILTIN_PATTERNS[@]}"; do
    pattern_args+=(-e "$pattern")
  done
  while IFS= read -r pattern; do
    pattern_args+=(-e "$pattern")
  done < <(_patterns_from_file)
  rc=0
  rg -l --null --hidden "${pattern_args[@]}" -- "${REPORT_SCOPE_PATHS[@]}" >>"$tmp_matches" 2>/dev/null || rc=$?
  if [ "$rc" -gt 1 ]; then
    echo "PUBLIC_HYGIENE_REPORT: scan-unavailable"
    return 0
  fi
  if [ -s "$tmp_matches" ]; then
    while IFS= read -r -d '' p; do
      printf 'PUBLIC_HYGIENE_REPORT: path=%s\n' "$(json_quote_path "$p")"
    done < <(LC_ALL=C sort -u -z "$tmp_matches")
  fi
  rm -f "$tmp_matches"
  return 0
}

# The default mode's non-blocking report-only arm: tracked regular blobs
# outside the blocking roots, scanned under the same deny patterns, matches
# reported (never failing), and any acquisition failure skipping only this
# scope while the old roots' results stand (plan
# 2026-10-26-hygiene-scanner-default-scope-parity).
emit_report_scope() {
  if ! collect_report_scope_paths; then
    echo "PUBLIC_HYGIENE_REPORT: enumeration-unavailable"
    return 0
  fi
  if [ "${#REPORT_SCOPE_PATHS[@]}" -eq 0 ]; then
    return 0
  fi
  run_report_scan
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
  # final `OUTCOME: <label>` row on the run's output. An optional
  # --patterns <file> overrides the child's deny-patterns file, so an arm
  # can pin a hostile patterns-line shape (dash-led, invalid regex) without
  # disturbing the shared file. Arguments after -- are passed to the
  # scanner verbatim.
  selftest_check_files() {
    local name="$1"
    local expect="$2"   # pass | fail | rc=<N>
    shift 2
    local needle=""
    local want_outcome=""
    local patterns_file="$patterns"
    while :; do
      case "$1" in
        --contains) needle="$2"; shift 2 ;;
        --outcome) want_outcome="$2"; shift 2 ;;
        --patterns) patterns_file="$2"; shift 2 ;;
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
                  PUBLIC_HYGIENE_PATTERNS_FILE="$patterns_file" \
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

  # r3 F1: an existing-but-unreadable patterns file must fail closed, never
  # silently degrade the blocking scan to builtin-only patterns. The named
  # file carries a patterns-file-only hit (FORBIDDEN-TOKEN matches no
  # builtin), so a silent degrade would exit 0 here; the pin demands the
  # tool error (exit 3) instead.
  printf 'token FORBIDDEN-TOKEN here\n' > "$repo/agents/skills/clean/notes.md"
  chmod 000 "$patterns"
  selftest_check_files "unreadable-patterns-file-fails-closed-files-mode" rc=3 \
    --outcome tool_error --contains "unreadable" -- \
    --files "agents/skills/clean/notes.md"
  chmod 600 "$patterns"

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

  # 2026-10-31 (frozen-full-tree-rg-fail-closed-arm row): the frozen
  # full-tree and changed modes are fail-closed on hostile patterns lines,
  # mirroring the files branch. A dash-led active patterns line was
  # previously parsed as an rg option and silently unapplied to the
  # blocking roots - the hit file below passed under the old shape; now
  # the pattern rides -e and matches.
  local dash_patterns="$tmp/patterns-dash"
  printf '%s\n' '-dashboard' > "$dash_patterns"
  printf 'see -dashboard config here\n' > "$repo/agents/skills/clean/SKILL.md"
  selftest_check_files "changed-dash-led-patterns-line-applies" fail \
    --contains "dashboard" --patterns "$dash_patterns" -- \
    --changed-from "$baseline_sha"

  # An invalid regex in the shared patterns file is a tool error (exit 3)
  # in the frozen modes too, never a silent degrade to pass; each mode's
  # message names its own label, so a case cannot pass via the wrong arm.
  local badre_patterns="$tmp/patterns-badre"
  printf '%s\n' '([unclosed' > "$badre_patterns"
  selftest_check_files "changed-invalid-regex-fails-closed" rc=3 \
    --outcome tool_error --contains "rg failed (exit 2) in changed (vs" \
    --patterns "$badre_patterns" -- \
    --changed-from "$baseline_sha"
  selftest_check_files "full-tree-invalid-regex-fails-closed" rc=3 \
    --outcome tool_error --contains "rg failed (exit 2) in full-tree mode" \
    --patterns "$badre_patterns" --

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

  # --- default-mode report-only tracked scope pins (plan
  # 2026-10-26-hygiene-scanner-default-scope-parity, Task 2): every arm below
  # runs the scanner with NO arguments (the report-only arm exists only in
  # the default mode) against the fixture repo through
  # PUBLIC_HYGIENE_REPO_ROOT, and pins the report contract: old-root hits
  # still exit 1, new-root tracked hits emit path records without content and
  # never fail, exclusions hold, crafted path bytes stay escaped, and the
  # enumeration is bound to the pinned root whatever the caller's
  # environment carries.

  # Absolute scanner path, so an arm may run from a foreign cwd.
  local self_abs
  self_abs="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

  # Report-arm harness: strict pass/fail verdict (rc plus verdict marker,
  # so an own-error exit can never satisfy either) plus the report-record
  # contract. Options before the trailing "--": expect=pass|fail,
  # --cd <dir> (run the child from a foreign working directory),
  # --env K=V (repeatable, injected into the child environment),
  # --record <path-needle> (asserts the exact
  # `PUBLIC_HYGIENE_REPORT: path=<needle>` row), --require <needle>
  # (positive fixed-text pin, for the enumeration-unavailable row),
  # --forbid <needle> (negative fixed-text pin; matched file content,
  # raw byte shapes, and redirected-repo names are asserted here),
  # --forbid-line <text> (negative whole-line fixed-text pin; a raw
  # newline leaking into a record splits it into output lines, which a
  # substring search cannot distinguish from the escaped record).
  # Every arm additionally pins that no raw control byte reaches the
  # output, so a report record can never carry a terminal control.
  selftest_check_report() {
    local name="$1"
    shift
    local expect="pass"
    local cd_dir=""
    local -a extra_env=()
    local -a want_records=()
    local -a require=()
    local -a forbid=()
    local -a forbid_lines=()
    while [ "$#" -gt 0 ]; do
      case "$1" in
        expect=*) expect="${1#expect=}"; shift ;;
        --cd) cd_dir="$2"; shift 2 ;;
        --env) extra_env+=("$2"); shift 2 ;;
        --record) want_records+=("$2"); shift 2 ;;
        --require) require+=("$2"); shift 2 ;;
        --forbid) forbid+=("$2"); shift 2 ;;
        --forbid-line) forbid_lines+=("$2"); shift 2 ;;
        *) break ;;
      esac
    done
    if [ "${1:-}" = "--" ]; then
      shift
    fi
    local actual_out actual_rc ok=false
    set +e
    if [ "${#extra_env[@]}" -gt 0 ]; then
      actual_out="$(cd "${cd_dir:-$PWD}" && env "${extra_env[@]}" \
        PUBLIC_HYGIENE_REPO_ROOT="$repo" \
        PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
        bash "$self_abs" 2>&1)"
    else
      actual_out="$(cd "${cd_dir:-$PWD}" && \
        PUBLIC_HYGIENE_REPO_ROOT="$repo" \
        PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
        bash "$self_abs" 2>&1)"
    fi
    actual_rc=$?
    set -e
    case "$expect" in
      pass)
        if [ "$actual_rc" -eq 0 ] && printf '%s\n' "$actual_out" | grep -q "PASS (public hygiene"; then
          ok=true
        fi
        ;;
      fail)
        if [ "$actual_rc" -eq 1 ] && printf '%s\n' "$actual_out" | grep -q "FAIL:"; then
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
    local needle
    for needle in ${want_records[@]+"${want_records[@]}"}; do
      if ! printf '%s\n' "$actual_out" | grep -qF "PUBLIC_HYGIENE_REPORT: path=$needle"; then
        echo "selftest FAIL: $name (missing report record: $needle)" >&2
        echo "$actual_out" >&2
        SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
        return
      fi
    done
    for needle in ${require[@]+"${require[@]}"}; do
      if ! printf '%s\n' "$actual_out" | grep -qF -- "$needle"; then
        echo "selftest FAIL: $name (missing required text: $needle)" >&2
        echo "$actual_out" >&2
        SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
        return
      fi
    done
    for needle in ${forbid[@]+"${forbid[@]}"}; do
      if printf '%s\n' "$actual_out" | grep -qF -- "$needle"; then
        echo "selftest FAIL: $name (forbidden text present: $needle)" >&2
        echo "$actual_out" >&2
        SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
        return
      fi
    done
    for needle in ${forbid_lines[@]+"${forbid_lines[@]}"}; do
      if printf '%s\n' "$actual_out" | grep -qFx -- "$needle"; then
        echo "selftest FAIL: $name (forbidden whole line present: $needle)" >&2
        echo "$actual_out" >&2
        SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
        return
      fi
    done
    if printf '%s\n' "$actual_out" | LC_ALL=C grep -q '[[:cntrl:]]'; then
      echo "selftest FAIL: $name (raw control byte in output)" >&2
      printf '%s\n' "$actual_out" | LC_ALL=C cat -v >&2
      SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
      return
    fi
    echo "selftest OK: $name"
  }

  # Old-root tracked hit: the blocking roots keep their failing verdict, and
  # the hit never surfaces as a report record. First give the other old-root
  # fixtures clean content (the tracked clean root and the untracked notes
  # file left dirty by the earlier arms) so the baseline-dirty file is the
  # only hit.
  printf '# clean report-section clean root\n' > "$repo/agents/skills/clean/SKILL.md"
  printf '# clean report-section notes\n' > "$repo/agents/skills/clean/notes.md"
  selftest_check_report "report-old-root-tracked-hit-still-fails" expect=fail \
    --forbid 'PUBLIC_HYGIENE_REPORT:' --

  # Old-root untracked hit: still exit 1, never a report record (untracked
  # files are outside the enumerated tracked scope).
  printf 'untracked: /Users/leaked/untracked-report\n' > "$repo/agents/skills/untracked-report.md"
  selftest_check_report "report-old-root-untracked-hit-still-fails" expect=fail \
    --forbid 'PUBLIC_HYGIENE_REPORT:' --
  rm -f "$repo/agents/skills/untracked-report.md"

  # Clean tracked file on a new root: run passes and emits no path record
  # at all. Give the first old-root fixture clean content so the old roots
  # stand clean from here on.
  printf '# clean report-section pdf\n' > "$repo/agents/skills/pdf/SKILL.md"
  printf '# clean new-root file\n' > "$repo/docs/report-newroot-clean.md"
  git -C "$repo" add -- docs/report-newroot-clean.md
  selftest_check_report "report-clean-new-root-tracked-emits-no-record" \
    --forbid 'PUBLIC_HYGIENE_REPORT:' --

  # Matching tracked file on a new root: one report record carrying the
  # path only (matched content never reaches the output) and a passing run.
  printf 'newroot leak: /Users/leaked/report-newroot\n' > "$repo/docs/report-newroot-hit.md"
  git -C "$repo" add -- docs/report-newroot-hit.md
  selftest_check_report "report-new-root-tracked-hit-records-without-content" \
    --record 'docs/report-newroot-hit.md' \
    --forbid '/Users/leaked/report-newroot' --

  # Shared exclusions hold inside the report scope: a docs/tmp child and a
  # root AGENTS.md carrying hits are excluded, never recorded.
  printf 'tmp hit: /Users/leaked/report-scope-tmp\n' > "$repo/docs/tmp/report-scope-excluded.md"
  printf 'agents hit: /Users/leaked/report-scope-agents-md\n' > "$repo/AGENTS.md"
  git -C "$repo" add -- docs/tmp/report-scope-excluded.md AGENTS.md
  selftest_check_report "report-shared-exclusions-hold-in-report-scope" \
    --record 'docs/report-newroot-hit.md' \
    --forbid 'path=docs/tmp/report-scope-excluded.md' \
    --forbid 'path=AGENTS.md' \
    --forbid '/Users/leaked/report-scope-tmp' \
    --forbid '/Users/leaked/report-scope-agents-md' --

  # Tracked symlink entry: excluded from the scannable set even though its
  # target would match (mode 120000 carries no scannable blob content).
  ln -s docs/report-newroot-hit.md "$repo/docs/report-newroot-link.md"
  git -C "$repo" add -- docs/report-newroot-link.md
  selftest_check_report "report-symlink-entry-excluded" \
    --record 'docs/report-newroot-hit.md' \
    --forbid 'report-newroot-link' --

  # Tracked gitlink entry: excluded from the scannable set (mode 160000).
  git -C "$repo" update-index --add --cacheinfo "160000,$head_sha,docs/report-gitlink-mod"
  selftest_check_report "report-gitlink-entry-excluded" \
    --record 'docs/report-newroot-hit.md' \
    --forbid 'report-gitlink-mod' --

  # Crafted path bytes survive as ASCII-only JSON escapes: a newline, a
  # control byte, a DEL byte, an option-shaped name, and non-ASCII bytes
  # each produce one single-line record with no raw control anywhere. (A
  # truly undecodable byte is unrepresentable on this host's filesystem,
  # which rejects invalid UTF-8 names outright; the non-ASCII bytes pin the
  # same >=0x7f escape arm byte-wise.)
  printf 'crafted: /Users/leaked/crafted-content\n' > "$repo/docs/report-line1"$'\n'"line2.md"
  printf 'crafted: /Users/leaked/crafted-content\n' > "$repo/docs/report-ctrl"$'\001'"byte"$'\177'"end.md"
  printf 'crafted: /Users/leaked/crafted-content\n' > "$repo/docs/--report-option-shaped.md"
  printf 'crafted: /Users/leaked/crafted-content\n' > "$repo/docs/report-r"$'\303\251'"sum"$'\303\251'".md"
  # A root-level option-shaped name reaches rg as a dash-leading path
  # argument (the docs/ twin above only ever rides as a path component
  # after "--"), so it is the arm that bites if the frozen "--" separator
  # before the enumerated paths regresses.
  printf 'crafted: /Users/leaked/crafted-content\n' > "$repo/--report-option-shaped.md"
  git -C "$repo" add -- \
    "docs/report-line1"$'\n'"line2.md" \
    "docs/report-ctrl"$'\001'"byte"$'\177'"end.md" \
    "docs/--report-option-shaped.md" \
    "docs/report-r"$'\303\251'"sum"$'\303\251'".md" \
    "--report-option-shaped.md"
  selftest_check_report "report-crafted-path-bytes-escaped" \
    --record 'docs/report-line1\u000aline2.md' \
    --record 'docs/report-ctrl\u0001byte\u007fend.md' \
    --record 'docs/--report-option-shaped.md' \
    --record 'docs/report-r\u00c3\u00a9sum\u00c3\u00a9.md' \
    --record '--report-option-shaped.md' \
    --forbid-line 'line2.md' \
    --forbid "$(printf 'report-ctrl\001byte')" \
    --forbid '/Users/leaked/crafted-content' --

  # Direct json_quote_path pin on a byte no filesystem fixture can carry on
  # this host: a raw 0xFF byte (an invalid UTF-8 lead byte) must come back
  # as its reversible ASCII-only escape, with the printable neighbors
  # untouched.
  local quoted_raw_byte
  quoted_raw_byte="$(json_quote_path "$(printf 'a\377b')")"
  if [ "$quoted_raw_byte" = 'a\u00ffb' ]; then
    echo "selftest OK: json-quote-path-raw-byte-escape"
  else
    echo "selftest FAIL: json-quote-path-raw-byte-escape (got: $quoted_raw_byte)" >&2
    SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
  fi

  # PUBLIC_HYGIENE_REPO_ROOT pins the scanned root independent of the cwd:
  # run from the neutral temp parent, the pinned repo's record still comes
  # back (a cwd-defaulted scan would enumerate nothing and emit none).
  selftest_check_report "report-repo-root-env-pins-scan-from-foreign-cwd" \
    --cd "$tmp" \
    --record 'docs/report-newroot-hit.md' --

  # A decoy GIT_DIR/GIT_WORK_TREE pair in the caller environment cannot
  # redirect the enumeration: the pinned repo's index is still what lists
  # (the decoy repo carries its own matching tracked file whose name must
  # never surface).
  local decoy="$tmp/decoy-repo"
  mkdir -p "$decoy"
  git -C "$decoy" init -q
  git -C "$decoy" config user.email "selftest@example.invalid"
  git -C "$decoy" config user.name "selftest"
  printf 'decoy: /Users/leaked/DECOY-REDIRECT\n' > "$decoy/DECOY-REDIRECT.md"
  git -C "$decoy" add -A
  git -C "$decoy" commit -q -m decoy
  selftest_check_report "report-decoy-git-dir-cannot-redirect-enumeration" \
    --cd "$tmp" \
    --env "GIT_DIR=$decoy/.git" \
    --env "GIT_WORK_TREE=$decoy" \
    --record 'docs/report-newroot-hit.md' \
    --forbid 'DECOY-REDIRECT' --

  # r3 F1: run_report_scan carries the same readable gate as the blocking
  # consumer, pinned directly (the default mode can only reach the report
  # arm after the blocking arm accepted the patterns file, so the
  # in-process direct call is the observable seam): an unreadable file
  # emits the fixed patterns-unavailable record and never builtin-only
  # partial results. The direct call reads the script-level PATTERNS_FILE,
  # so the pin re-points it at the fixture file for the duration.
  local saved_patterns_file="$PATTERNS_FILE"
  PATTERNS_FILE="$patterns"
  chmod 000 "$patterns"
  REPORT_SCOPE_PATHS=("docs/report-newroot-hit.md")
  local report_out
  report_out="$(cd "$repo" && run_report_scan)"
  chmod 600 "$patterns"
  if [ "$report_out" = "PUBLIC_HYGIENE_REPORT: patterns-unavailable" ]; then
    echo "selftest OK: report-unreadable-patterns-file-emits-patterns-unavailable"
  else
    echo "selftest FAIL: report-unreadable-patterns-file-emits-patterns-unavailable (got: $report_out)" >&2
    SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
  fi
  # Readable control: the same direct call emits the path record, so the pin
  # above cannot pass via a broken run_report_scan.
  report_out="$(cd "$repo" && run_report_scan)"
  PATTERNS_FILE="$saved_patterns_file"
  if [ "$report_out" = "PUBLIC_HYGIENE_REPORT: path=docs/report-newroot-hit.md" ]; then
    echo "selftest OK: report-readable-patterns-file-emits-path-record"
  else
    echo "selftest FAIL: report-readable-patterns-file-emits-path-record (got: $report_out)" >&2
    SELFTEST_FAILS=$((SELFTEST_FAILS + 1))
  fi

  # Explicit modes keep their prior semantics beside the widened default:
  # --changed-from still selects only the old roots (staged new-root dirt
  # stays invisible to it), while the same new-root hit named through
  # --files still blocks.
  selftest_check_files "changed-mode-keeps-prior-selection-report-scope-not-scanned" pass -- \
    --changed-from "$head_sha"
  selftest_check_files "files-mode-report-scope-hit-still-blocking" fail -- \
    --files "docs/report-newroot-hit.md"

  # Enumeration failure: the fixed record is emitted and only the report
  # scope is skipped, while the old-root scan still runs and its hit still
  # fails the run. A shimmed `git` fails the enumeration without touching
  # the old-root rg scan, after recording its environment: the shim runs
  # inside the enumeration subshell, so the record is exactly the
  # environment the scrub produced.
  local shim="$tmp/git-shim"
  mkdir -p "$shim"
  {
    printf '#!/bin/sh\n'
    printf 'env > "%s/enumerate-child-env.txt"\n' "$tmp"
    printf 'exit 42\n'
  } > "$shim/git"
  chmod +x "$shim/git"
  printf 'old-root oops: /Users/leaked/enum-fail\n' > "$repo/agents/skills/pdf/SKILL.md"
  printf '[core]\n\tdecoyRedirect = 1\n' > "$tmp/decoy-gitconfig"
  selftest_check_report "report-enumeration-unavailable-preserves-old-root-results" expect=fail \
    --env "PATH=$shim:$PATH" \
    --env "GIT_DIR=$decoy/.git" \
    --env "GIT_WORK_TREE=$decoy" \
    --env "GIT_INDEX_FILE=$decoy/.git/index" \
    --env "GIT_OBJECT_DIRECTORY=$decoy/.git/objects" \
    --env "GIT_COMMON_DIR=$decoy/.git" \
    --env "GIT_ALTERNATE_OBJECT_DIRECTORIES=$decoy/.git/objects/alt" \
    --env "GIT_GRAFT_FILE=$decoy/.git/info/grafts" \
    --env "GIT_NAMESPACE=decoy-namespace" \
    --env "GIT_CONFIG=$tmp/decoy-gitconfig" \
    --env "GIT_CONFIG_PARAMETERS='core.decoyRedirect=1'" \
    --env "GIT_CONFIG_COUNT=1" \
    --env "GIT_CONFIG_GLOBAL=$tmp/decoy-gitconfig" \
    --env "GIT_CONFIG_SYSTEM=$tmp/decoy-gitconfig" \
    --env "RIPGREP_CONFIG_PATH=$tmp/decoy-rg-config" \
    --require 'PUBLIC_HYGIENE_REPORT: enumeration-unavailable' \
    --forbid 'path=docs/report-newroot-hit.md' --

  # 2026-10-31 (report-scope-degradation row, r2 F4a): an rg scan failure
  # after successful enumeration emits the fixed scan-unavailable record -
  # no longer mislabeled enumeration-unavailable. An rg shim that fails
  # only the report scope's -l invocations keeps the blocking scan (rg -n)
  # real, so the run still fails on the baseline hit and the record rides
  # the warnings channel.
  local rg_shim="$tmp/rg-shim"
  mkdir -p "$rg_shim"
  {
    printf '#!/bin/sh\n'
    printf 'if [ "$1" = "-l" ]; then exit 42; fi\n'
    printf 'exec "%s" "$@"\n' "$(command -v rg)"
  } > "$rg_shim/rg"
  chmod +x "$rg_shim/rg"
  selftest_check_report "report-scan-unavailable-not-mislabeled" expect=fail \
    --env "PATH=$rg_shim:$PATH" \
    --require 'PUBLIC_HYGIENE_REPORT: scan-unavailable' \
    --forbid 'enumeration-unavailable' --

  # The recorded enumeration child environment pins the scrub itself: the
  # pinned GIT_CONFIG_NOSYSTEM=1 export is present, and every var on the
  # git_enumerate scrub list is absent, so each injected decoy (the repo
  # redirect pair, the object/index/graft/namespace surfaces, and the
  # config-file and config-parameter surfaces) is proven scrubbed.
  local child_env="$tmp/enumerate-child-env.txt"
  local scrub_ok=true scrub_var
  if [ ! -f "$child_env" ] || ! grep -q '^GIT_CONFIG_NOSYSTEM=1$' "$child_env"; then
    scrub_ok=false
  elif grep -q '^RIPGREP_CONFIG_PATH=' "$child_env"; then
    # the preamble rg-config unset rides the same poisoning class; pin it here
    scrub_ok=false
  else
    for scrub_var in GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE \
        GIT_OBJECT_DIRECTORY GIT_COMMON_DIR \
        GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_GRAFT_FILE GIT_NAMESPACE \
        GIT_CONFIG GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT \
        GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM; do
      if grep -q "^${scrub_var}=" "$child_env"; then
        scrub_ok=false
        break
      fi
    done
  fi
  if $scrub_ok; then
    echo "selftest OK: report-enumeration-child-env-scrubbed"
  else
    echo "selftest FAIL: report-enumeration-child-env-scrubbed" >&2
    if [ -f "$child_env" ]; then
      cat "$child_env" >&2
    else
      echo "no recorded child environment at $child_env" >&2
    fi
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

# r2 F4b: production scratch files (changed-mode diff lists, the report
# enumeration list, report matches) are registered here and trap-cleaned at
# exit, so an interrupted run leaves no residue in $TMPDIR, matching the
# selftest's trapped temp dir. The selftest replaces this trap with its own
# temp-dir cleanup, which is fine: the selftest arms run the scanner as
# child processes, and the two direct in-process run_report_scan calls
# inline-rm their tmp_matches on their exercised paths.
CLEANUP_FILES=()
register_tmp() {
  CLEANUP_FILES+=("$1")
}
trap '[ ${#CLEANUP_FILES[@]} -eq 0 ] || rm -f "${CLEANUP_FILES[@]}"' EXIT

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
