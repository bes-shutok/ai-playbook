#!/usr/bin/env bash
# sweep-tmp.sh - report and optionally clean throwaway scratch files in /tmp/
#
# Agents and ad-hoc sessions often leave probe programs, diffs, patches, and
# backups in plain /tmp/ instead of the project's resolved {tmp_dir}. This
# script makes that accumulation visible and offers an opt-in, per-group
# confirmed cleanup. It NEVER auto-deletes and NEVER touches files it does
# not list in report mode first.
#
# Usage:
#   bash ~/.ai-playbook/scripts/sweep-tmp.sh                  # report (default): files older than 7 days
#   bash ~/.ai-playbook/scripts/sweep-tmp.sh --days 14        # report files older than 14 days
#   bash ~/.ai-playbook/scripts/sweep-tmp.sh --dry-run        # show what --clean would delete
#   bash ~/.ai-playbook/scripts/sweep-tmp.sh --clean          # prompt per group, delete on confirmation
#   bash ~/.ai-playbook/scripts/sweep-tmp.sh --clean --yes    # delete without per-group prompt (still only listed files)
#
# Design notes:
# - Report-only by default. --clean requires explicit confirmation per group.
# - Only targets throwaway extensions (.py .sh .java .class .txt .diff .patch .json .bak .md .log .csv .tsv).
# - Excludes known-legitimate patterns: learn-counter-* (session state), system logs,
#   Microsoft/Apple files, and dotfiles. Add more to KEEP_PATTERNS below.
# - Shared /tmp/ is never glob-deleted; each candidate is filtered by extension, age, and exclusion.
#
# Companion to scan-public-hygiene.sh: that scans repo content for leaks; this manages scratch hygiene.

set -euo pipefail

DAYS=7
MODE="report"
ASSUME_YES=0
TMP_DIR="/tmp"

# Extensions considered throwaway scratch. Conservative: code-probe and doc/diff artifacts only.
SCRATCH_EXTS=(py sh java class txt diff patch json bak md log csv tsv)

# Patterns to ALWAYS keep (never report, never delete). Match against the basename.
# Add legitimate /tmp/ state for your setup here.
KEEP_PATTERNS=(
  'learn-counter-*'      # learn-skill session counter (persists across tool calls)
  'ralphex-*'            # ralphex nightly/runtime logs
  '.DS_Store'
  'com.apple.*'
  'com.microsoft.*'
  '.*'                   # all dotfiles/config
)

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --days) DAYS="$2"; shift 2;;
      --clean) MODE="clean"; shift;;
      --dry-run) MODE="dry-run"; shift;;
      --yes|-y) ASSUME_YES=1; shift;;
      --help|-h) usage 0;;
      *) echo "Unknown arg: $1" >&2; usage 1;;
    esac
  done
  # --yes only escalates --clean to unconfirmed deletion. It has no effect on report/dry-run.
  if [ "$MODE" = "clean" ] && [ "$ASSUME_YES" = 1 ]; then
    MODE="clean-yes"
  fi
}

# List candidate paths in $TMP_DIR: throwaway extensions, older than $DAYS days,
# excluding KEEP_PATTERNS. Uses ls + stat rather than find -mtime, because some
# hardened/sandboxed environments restrict find on world-writable dirs and it
# silently returns nothing. stat epoch-mtime is portable on macOS/BSD and Linux.
list_candidates() {
  local now min_mtime f base mtime age kept
  now="$(date +%s)"
  min_mtime=$(( now - DAYS * 86400 ))

  # Iterate regular files only (skip dirs/symlinks). ls is glob-expanded by the shell.
  local glob=""
  for e in "${SCRATCH_EXTS[@]}"; do glob="$glob $TMP_DIR/*.$e"; done
  # shellcheck disable=SC2086  # intentional glob expansion
  for f in $glob; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    # Skip keep patterns.
    kept=0
    for p in "${KEEP_PATTERNS[@]}"; do
      case "$base" in
        $p) kept=1; break;;
      esac
    done
    [ "$kept" = 1 ] && continue
    # Age check via stat epoch-mtime.
    mtime="$(stat -f '%m' "$f" 2>/dev/null || stat -c '%Y' "$f" 2>/dev/null || echo 0)"
    [ -n "$mtime" ] && [ "$mtime" -lt "$min_mtime" ] 2>/dev/null && printf '%s\n' "$f"
  done
}

# Group candidate paths by stem (strip trailing digits and extension) for readable output.
group_by_stem() {
  local f base stem
  while read -r f; do
    base="$(basename "$f")"
    # stem = basename with trailing <digits>.<ext> collapsed, and inner $-suffixes dropped
    stem="$(printf '%s' "$base" | sed -E 's/[0-9]+\.[^.]+$//; s/\$.*//; s/[-_.]+$//')"
    printf '%s\t%s\n' "$stem" "$f"
  done | sort
}

do_report() {
  local count
  count="$(list_candidates | wc -l | tr -d ' ')"
  echo "=== sweep-tmp report: files in $TMP_DIR older than $DAYS day(s) ==="
  echo "(throwaway extensions only; legitimate session state and system files excluded)"
  echo
  if [ "$count" -eq 0 ]; then
    echo "Nothing to report. $TMP_DIR is clean by these criteria."
    return 0
  fi
  echo "$count candidate file(s), grouped by stem:"
  echo
  list_candidates | group_by_stem | awk -F'\t' '
    { stems[$1] = stems[$1] $2 "\n"; n[$1]++ }
    END {
      for (s in n) printf "  %-30s %d file(s)\n", s, n[s]
    }' | sort
  echo
  echo "To review the full list:   bash $0 --days $DAYS --dry-run"
  echo "To clean (with prompts):   bash $0 --days $DAYS --clean"
}

do_dry_run() {
  echo "=== sweep-tmp DRY RUN (nothing will be deleted) ==="
  echo "Would delete these files (older than $DAYS day(s), throwaway extensions, exclusions applied):"
  echo
  local f
  list_candidates | while read -r f; do
    printf '  %s\n' "$f"
  done
  echo
  echo "$(list_candidates | wc -l | tr -d ' ') file(s) would be deleted."
}

# Delete a list of files read from stdin. Returns count deleted.
delete_files() {
  local f deleted=0
  while read -r f; do
    if rm -f -- "$f" 2>/dev/null; then
      deleted=$((deleted + 1))
    else
      echo "  WARN: could not delete $f" >&2
    fi
  done
  printf '%s' "$deleted"
}

do_clean() {
  local assume="$1"
  do_dry_run
  echo
  if [ "$(list_candidates | wc -l | tr -d ' ')" -eq 0 ]; then
    echo "Nothing to clean."
    return 0
  fi
  if [ "$assume" != "1" ]; then
    printf "Delete ALL of the above? This cannot be undone. Type 'yes' to confirm: "
    local resp
    read -r resp
    [ "$resp" = "yes" ] || { echo "Aborted. Nothing deleted."; exit 0; }
  fi
  local deleted
  deleted="$(list_candidates | delete_files)"
  echo "Deleted $deleted file(s)."
}

parse_args "$@"
case "$MODE" in
  report)    do_report ;;
  dry-run)   do_dry_run ;;
  clean)     do_clean 0 ;;
  clean-yes) do_clean 1 ;;
esac
