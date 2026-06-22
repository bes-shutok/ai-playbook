#!/usr/bin/env bash
# Git safety hooks backing done / execute-plan / user AGENTS.md policies.
# Canonical copy: install to ~/.cursor/hooks/git-safety.sh (see cursor/hooks/README.md).
set -euo pipefail

input=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  echo '{"permission":"allow"}'
  exit 0
fi

command=$(echo "$input" | jq -r '.command // empty')

if [[ -z "$command" ]]; then
  echo '{"permission":"allow"}'
  exit 0
fi

is_ephemeral_git_clean_path() {
  local p="${1%/}"
  case "$p" in
    docs/tmp|docs/tmp/*|docs/history/reviews|docs/history/reviews/*|docs/reviews|docs/reviews/*|.ai-playbook|.ai-playbook/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

git_clean_is_scoped_to_ephemeral() {
  local cmd="$1"
  local after="${cmd#*git clean}"
  after="${after#"${after%%[![:space:]]*}"}"
  if [[ ! "$after" =~ --[[:space:]] ]]; then
    return 1
  fi
  local paths="${after#*--}"
  paths="${paths%%;*}"
  paths="${paths%%|*}"
  paths="${paths%%&*}"
  local path
  for path in $paths; do
    path="${path#"${path%%[![:space:]]*}"}"
    path="${path%"${path##*[![:space:]]}"}"
    [ -n "$path" ] || continue
    is_ephemeral_git_clean_path "$path" || return 1
  done
  return 0
}

# Never git reset --hard (done skill, execute-plan recovery, AGENTS.md).
if [[ "$command" =~ git[[:space:]]+reset[[:space:]]+(--[[:alnum:]-]+[[:space:]]+)*--hard ]]; then
  jq -n \
    --arg cmd "$command" \
    '{
      permission: "deny",
      user_message: "git reset --hard is blocked by workspace policy (wipes unrelated working-tree changes). Use git restore, git revert, or git commit-tree instead.",
      agent_message: ("Blocked: " + $cmd)
    }'
  exit 0
fi

# No Co-authored-by trailers or git commit --trailer attribution.
if [[ "$command" =~ [Cc]o-[Aa]uthored-[Bb]y: ]] || [[ "$command" =~ git[[:space:]]+commit.*--trailer ]]; then
  jq -n \
    '{
      permission: "deny",
      user_message: "Commit messages must not include Co-authored-by trailers or git commit --trailer attribution.",
      agent_message: "Use plain git commit -m without --trailer or Co-authored-by lines."
    }'
  exit 0
fi

# Whole-repo git clean deletes untracked WIP (docs-branch orphan first run used this).
# Allow only scoped clean on ephemeral LLM/runtime dirs (docs/tmp, docs/history/reviews, .ai-playbook).
# Skip when the shell command is git commit — commit messages may mention git clean.
if [[ "$command" =~ git[[:space:]]+clean ]] && [[ ! "$command" =~ (^|[;&|][[:space:]]*)git[[:space:]]+commit[[:space:]] ]]; then
  if git_clean_is_scoped_to_ephemeral "$command"; then
    echo '{"permission":"allow"}'
    exit 0
  fi
  jq -n \
    --arg cmd "$command" \
    '{
      permission: "deny",
      user_message: "git clean is blocked unless scoped to ephemeral dirs (docs/tmp/, docs/history/reviews/, .ai-playbook/). Use docs-branch untracked backup instead of whole-repo clean.",
      agent_message: ("Blocked destructive git clean. Do not run git clean -fdq on the repo root. Snapshot untracked files with git ls-files --others --exclude-standard, or use scoped clean only. Command: " + $cmd)
    }'
  exit 0
fi

# Force push requires explicit user approval (Git Push Policy).
if [[ "$command" =~ git[[:space:]]+push ]] && [[ "$command" =~ (^|[[:space:]])--force-with-lease($|[[:space:]])|(^|[[:space:]])--force($|[[:space:]])|(^|[[:space:]])-f($|[[:space:]]) ]]; then
  if [[ "$command" =~ (master|main|pre-release)(/|$|[[:space:]]) ]]; then
    jq -n \
      '{
        permission: "ask",
        user_message: "Force push to a protected branch requires your explicit approval.",
        agent_message: "Ask the user before force-pushing to main/master/pre-release."
      }'
    exit 0
  fi
fi

echo '{"permission":"allow"}'
exit 0
