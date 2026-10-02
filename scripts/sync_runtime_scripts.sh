#!/usr/bin/env bash
# sync_runtime_scripts.sh: manifest-driven symlink deployment of the
# loop-consumed runtime scripts from the canonical repo into the deployed
# home copy (default ~/.ai-playbook/scripts).
#
# Consumer-class boundary: this sync owns the loop-consumed scripts in symlink
# form (their bytes are canonical by construction). Provenance-pinned
# consumers (the .source-commit stamp) are a separate deployment convention
# outside this script's scope; this script touches no other tooling.
#
# Concurrency is explicitly out of scope (single-operator homelab premise).
# Rename-aside transient note: between the .bak rename and the ln -s the
# deployed name is absent for milliseconds; a concurrent loop reader fails
# closed and self-heals on its next resolution.
#
# Exit 0 when every manifest entry ended current/installed/converted/left;
# exit 1 when any entry escalated. Idempotent: a second run changes nothing.

set -u

CURRENT=0
INSTALLED=0
CONVERTED=0
LEFT=0
ESCALATED=0

# Canonical root: resolved from this script's own filesystem location THROUGH
# SYMLINK CHAINS, so the primary invocation mode (via the deployed symlink)
# resolves the canonical repo.
SELF="$(readlink -f "${BASH_SOURCE[0]}")" || {
  printf 'sync: escalated: cannot resolve the script path through symlink chains\n'
  exit 1
}
CANON="$(dirname "$SELF")"
REPO="$(dirname "$CANON")"

# Deployed root: pinnable via DEPLOYED_ROOT so tests can pin it. Fail-closed:
# it must exist, be a directory, and never resolve inside or equal to the
# canonical scripts/ directory, so a stale export can never retarget the
# rename-aside arm at the canonical repo itself.
DEPLOYED="${DEPLOYED_ROOT:-$HOME/.ai-playbook/scripts}"
if [ ! -d "$DEPLOYED" ]; then
  printf 'sync: escalated: deployed root is not a directory: %s\n' "$DEPLOYED"
  exit 1
fi
DEPLOYED_RESOLVED="$(readlink -f "$DEPLOYED" 2>/dev/null)" || DEPLOYED_RESOLVED=""
case "$DEPLOYED_RESOLVED" in
  "$CANON" | "$CANON"/*)
    printf 'sync: escalated: deployed root resolves inside the canonical scripts directory: %s\n' "$DEPLOYED_RESOLVED"
    exit 1
    ;;
esac

MANIFEST="$CANON/runtime-scripts.list"
if [ ! -f "$MANIFEST" ]; then
  printf 'sync: escalated: manifest file missing: %s\n' "$MANIFEST"
  exit 1
fi
if [ ! -r "$MANIFEST" ]; then
  printf 'sync: escalated: manifest file not readable: %s\n' "$MANIFEST"
  exit 1
fi
# An empty or all-comments inventory can never pass as a vacuous all-current
# run: zero entries escalates.
manifest_entries="$(grep -cve '^[[:space:]]*$' -e '^[[:space:]]*#' "$MANIFEST")"
if [ -z "$manifest_entries" ]; then
  printf 'sync: escalated: manifest unreadable: %s\n' "$MANIFEST"
  exit 1
fi
if [ "$manifest_entries" -eq 0 ]; then
  printf 'sync: escalated: manifest yields zero inventory entries (empty or all-comments): %s\n' "$MANIFEST"
  exit 1
fi

digest_of() { shasum -a 256 "$1" 2>/dev/null | awk '{print $1}'; }

# git-clean | git-dirty | git-unknown: recorded in converted report lines,
# never gating (the operator judges quarantine with the restore in hand).
canonical_git_state() {
  local out
  if out="$(git -C "$REPO" status --porcelain -- "scripts/$1" 2>/dev/null)"; then
    if [ -z "$out" ]; then
      printf 'git-clean'
    else
      printf 'git-dirty'
    fi
  else
    printf 'git-unknown'
  fi
}

escalate() {
  ESCALATED=$((ESCALATED + 1))
  printf 'sync: %s: escalated (%s)\n' "$1" "$2"
}

while IFS= read -r name || [ -n "$name" ]; do
  case "$name" in
    '' | '#'*) continue ;;
  esac
  dep="$DEPLOYED/$name"
  canon_entry="$CANON/$name"

  if [ -L "$dep" ]; then
    # BSD readlink -f prints the resolved path but exits 1 when the final
    # component dangles; capture the output regardless of that status.
    res="$(readlink -f "$dep" 2>/dev/null)"
    if [ -z "$res" ]; then
      escalate "$name" "symlink target unresolvable"
    elif [ "$res" = "$canon_entry" ]; then
      if [ -e "$res" ]; then
        printf 'sync: %s: current\n' "$name"
        CURRENT=$((CURRENT + 1))
      else
        escalate "$name" "dangling deployed symlink (target missing: $res)"
      fi
    elif [ "$res" = "$CANON" ] || [ "${res#"$CANON"/}" != "$res" ]; then
      escalate "$name" "symlink resolves into the canonical scripts directory at an unexpected target: $res"
    else
      escalate "$name" "symlink resolves outside the canonical scripts directory: $res"
    fi

  elif [ -e "$dep" ]; then
    if [ ! -f "$dep" ]; then
      escalate "$name" "unsupported deployed entry type (neither symlink nor regular file): $dep"
      continue
    fi
    if [ ! -e "$canon_entry" ]; then
      printf 'sync: %s: left (no canonical counterpart; deployed copy untouched)\n' "$name"
      LEFT=$((LEFT + 1))
      continue
    fi
    if [ ! -f "$canon_entry" ]; then
      escalate "$name" "canonical counterpart is not a regular file: $canon_entry"
      continue
    fi
    dep_digest="$(digest_of "$dep")"
    canon_digest="$(digest_of "$canon_entry")"
    if [ -z "$dep_digest" ] || [ -z "$canon_digest" ]; then
      escalate "$name" "digest unavailable"
      continue
    fi
    if [ "$dep_digest" = "$canon_digest" ]; then
      compare_outcome="digest-current"
    else
      compare_outcome="digest-drifted"
    fi
    git_outcome="$(canonical_git_state "$name")"
    bak="$dep.bak-$(date +%Y%m%d)"
    # -L catches a dangling .bak symlink too: existence must not follow links.
    if [ -e "$bak" ] || [ -L "$bak" ]; then
      escalate "$name" "rename-aside refused, .bak name already exists: $bak"
      continue
    fi
    if ! mv "$dep" "$bak"; then
      escalate "$name" "rename-aside failed"
      continue
    fi
    if ! ln -s "$canon_entry" "$dep"; then
      escalate "$name" "post-rename ln -s refused (noclobber; rename-aside residue kept: $bak)"
      continue
    fi
    printf 'sync: %s: converted (%s, %s, backup=%s)\n' "$name" "$compare_outcome" "$git_outcome" "$bak"
    CONVERTED=$((CONVERTED + 1))

  else
    if [ ! -e "$canon_entry" ]; then
      escalate "$name" "absent both deployed and canonical (dangling-inventory hazard; no link installed)"
      continue
    fi
    if ! ln -s "$canon_entry" "$dep"; then
      escalate "$name" "ln -s refused (noclobber; fail-closed)"
      continue
    fi
    printf 'sync: %s: installed\n' "$name"
    INSTALLED=$((INSTALLED + 1))
  fi
done <"$MANIFEST"

printf 'sync: summary: current=%d installed=%d converted=%d left=%d escalated=%d\n' \
  "$CURRENT" "$INSTALLED" "$CONVERTED" "$LEFT" "$ESCALATED"

if [ "$ESCALATED" -gt 0 ]; then
  exit 1
fi
exit 0
