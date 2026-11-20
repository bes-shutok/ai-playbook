#!/usr/bin/env bash
# Publish-scope checker: names publish-delta files that must not be published.
#
# Reads one path per line on stdin (the publish delta's file list) and reports:
#   - Deny class 1: a path that is tracked-but-ignored in the repository
#     (PUBLISH-SCOPE: <path> (tracked-but-ignored)).
#   - Deny class 2: a dated item file (YYYY-MM-DD-*) strictly inside a
#     charter-empty directory and present at main's tip
#     (PUBLISH-SCOPE: <path> (charter-empty-directory)).
#
# Warning-only machinery: report lines go to stdout, diagnostics to stderr,
# and the exit status is 0 whenever the check itself ran, findings or not.
# A git failure exits nonzero with no report lines (tool failure, not a
# finding). The report is the delta intersection, never a repo-wide dump.
#
# Charter-empty directories: the list is a repo-side default constant citing
# docs/history/backlog/completed/README.md as the rule's home; the charter
# README itself and deleted rows under the directory never match.
#
# --selftest runs a self-contained fixture pass over both deny classes, the
# clean list, the deletion and README non-match arms, and a poisoned-env
# decoy; it pins its fixture repo's git config locally.

set -u

# Charter-empty directories (repo-side constant; rule home:
# docs/history/backlog/completed/README.md). Component-boundary matching
# below, never a string prefix.
CHARTER_EMPTY_DIRS="docs/history/backlog/completed"

REPORT_LINES=0
SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")

# git_enumerate-class environment scrub around every git call (mirrors
# git_enumerate() in scripts/scan-public-hygiene.sh). Worktree .gitignore
# files still apply.
scrub_git_env() {
  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
    GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_GRAFT_FILE \
    GIT_NAMESPACE GIT_CONFIG GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT \
    GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
  GIT_CONFIG_NOSYSTEM=1
  export GIT_CONFIG_NOSYSTEM
}

tracked_ignored_list() {
  (
    scrub_git_env
    set -o pipefail
    # -z: unquoted, NUL-delimited (paths with spaces and non-ASCII bytes
    # arrive verbatim); tr maps to newline-per-line for the intersection.
    git ls-files -i -c --exclude-standard -z 2>/dev/null | tr '\0' '\n'
  )
}

path_present_at_tip() {
  _path=$1
  (
    scrub_git_env
    exec git cat-file -e "main:$_path" 2>/dev/null
  )
}

# charter-empty class: dated item file (YYYY-MM-DD-*) strictly inside a
# charter-empty directory. The directory component must be a full path
# component boundary (leading "docs/history/backlog/completed/" followed by
# the item), so sibling directories ("completed-spring/") never match.
is_charter_empty_item() {
  _path=$1
  _base=${_path##*/}
  case $_base in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*) ;;
    *) return 1 ;;
  esac
  # strip the item base to test the directory strictly
  _dir=${_path%/*}
  [ "$_dir" = "$_path" ] && return 1
  case $_dir in
    "$CHARTER_EMPTY_DIRS") return 0 ;;
    *) return 1 ;;
  esac
}

report() {
  printf 'PUBLISH-SCOPE: %s (%s)\n' "$1" "$2"
  REPORT_LINES=$((REPORT_LINES + 1))
}

check_stdin() {
  # Fail closed on a git tool failure: the class-1 list must be obtainable.
  TI_TMP=$(mktemp) || return 9
  tracked_ignored_list >"$TI_TMP" || {
    rm -f "$TI_TMP"
    return 9
  }

  status=0
  while IFS= read -r path || [ -n "$path" ]; do
    [ -z "$path" ] && continue
    if grep -Fqx -- "$path" "$TI_TMP"; then
      report "$path" tracked-but-ignored
    elif is_charter_empty_item "$path"; then
      if path_present_at_tip "$path"; then
        report "$path" charter-empty-directory
      fi
    fi
  done <&0
  rm -f "$TI_TMP"
  return $status
}

usage() {
  printf 'usage: release_publish_scope_check.sh [--selftest] < paths\n' >&2
}

SELFTEST_ONLY=0
case "${1-}" in
  --selftest) SELFTEST_ONLY=1 ;;
  ""|-) ;;
  -h|--help) usage; exit 0 ;;
  *) usage; exit 2 ;;
esac

selftest() {
  fixture=$(mktemp -d) || return 9
  trap 'rm -rf "$fixture"' EXIT
  cd "$fixture" || return 9
  # pin identity so ambient global config cannot flip a verdict
  git init -q -b main .
  git config user.email selftest@example.invalid
  git config user.name selftest
  git config core.excludesfile /dev/null
  mkdir -p docs/history/backlog/completed docs/history/backlog/completed-spring
  printf '# charter-empty rule home\n' >docs/history/backlog/completed/README.md
  printf 'x\n' >docs/history/backlog/completed/2026-01-01-item.md
  printf 'x\n' >docs/history/backlog/completed/2026-01-02-gone.md
  printf 'x\n' >docs/history/backlog/completed-spring/2026-01-03-item.md
  printf 'x\n' >plain-file.md
  printf 'ignored-secret.txt\n' >.gitignore
  printf 'secret\n' >ignored-secret.txt
  git add docs plain-file.md .gitignore
  git add -f ignored-secret.txt
  git commit -qm selftest

  out=$(git ls-files -i -c --exclude-standard)
  [ "$out" = "ignored-secret.txt" ] || {
    printf 'selftest: tracked-ignored baseline unexpected: %s\n' "$out" >&2
    return 1
  }

  # clean list: no report lines
  clean_out=$(printf 'plain-file.md\n' | "$SELF" 2>/dev/null)
  [ -z "$clean_out" ] || {
    printf 'selftest: clean list produced report: %s\n' "$clean_out" >&2
    return 1
  }

  # deny class 1: tracked-but-ignored delta path
  c1=$(printf 'ignored-secret.txt\n' | "$SELF" 2>/dev/null)
  [ "$c1" = "PUBLISH-SCOPE: ignored-secret.txt (tracked-but-ignored)" ] || {
    printf 'selftest: class 1 mismatch: %s\n' "$c1" >&2
    return 1
  }

  # deny class 2: dated item inside charter-empty dir, present at tip
  c2=$(printf 'docs/history/backlog/completed/2026-01-01-item.md\n' | "$SELF" 2>/dev/null)
  [ "$c2" = "PUBLISH-SCOPE: docs/history/backlog/completed/2026-01-01-item.md (charter-empty-directory)" ] || {
    printf 'selftest: class 2 mismatch: %s\n' "$c2" >&2
    return 1
  }

  # deletion arm: row deleted from the tip (not present at main) never matches
  git rm -q docs/history/backlog/completed/2026-01-02-gone.md
  git commit -qm 'delete row'
  del_out=$(printf 'docs/history/backlog/completed/2026-01-02-gone.md\n' | "$SELF" 2>/dev/null)
  [ -z "$del_out" ] || {
    printf 'selftest: deleted row matched: %s\n' "$del_out" >&2
    return 1
  }

  # README and sibling-directory non-match arms
  nm_out=$(printf 'docs/history/backlog/completed/README.md\ndocs/history/backlog/completed-spring/2026-01-03-item.md\n' | "$SELF" 2>/dev/null)
  [ -z "$nm_out" ] || {
    printf 'selftest: non-match arm matched: %s\n' "$nm_out" >&2
    return 1
  }

  # poisoned-env decoy: a poisoned GIT_DIR must not flip a verdict
  env_out=$(printf 'plain-file.md\n' | GIT_DIR=/nonexistent/.git GIT_WORK_TREE=/nonexistent "$SELF" 2>/dev/null)
  [ -z "$env_out" ] || {
    printf 'selftest: poisoned env flipped verdict: %s\n' "$env_out" >&2
    return 1
  }

  printf 'selftest: ok\n'
  return 0
}

if [ "$SELFTEST_ONLY" = 1 ]; then
  selftest
  exit $?
fi

check_stdin
rc=$?
if [ $rc -ne 0 ]; then
  printf 'release_publish_scope_check: git enumeration failed; no report emitted\n' >&2
  exit "$rc"
fi
exit 0
