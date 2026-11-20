#!/usr/bin/env bash
# PreToolUse (Bash) hook: plan-review gate backstop.
#
# Blocks `git commit` that stages a plan file under */plans/*.md when the newest
# matching review artifact (*-r<N>.md under a */reviews/ dir) records a No-Go
# verdict. This is a mechanical backstop for the plans-skill Quality Gate rule
# "Read the review artifact and confirm ready=yes before declaring the plan ready"
# -- it cannot verify the review-plan skill was used or the multi-lens catalog ran;
# the skill text remains the primary control.
#
# Repo-aware: honors `git -C <dir>` and a leading `cd <dir>` in the command so a
# staged No-Go plan in one repo never blocks an unrelated commit in another.
#
# Exit 0 = allow. Exit 2 = block (stderr shown to the agent). Other non-zero = non-blocking error.
# Only acts on commits that stage a plan file; all other Bash calls exit 0 immediately.

set -uo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | python3 -c 'import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("command",""))
except Exception:
    print("")
' 2>/dev/null || printf '')"

# Only inspect real `git commit` invocations. Require `commit` as the git subcommand
# (git commit, git -C <dir> commit), not the word "commit" appearing in an echo/flag.
if ! printf '%s' "$cmd" | grep -qE 'git[[:space:]]+commit|git[[:space:]]+-C[[:space:]]+[^[:space:]]+[[:space:]]+commit'; then
  exit 0
fi

# Determine the directory the commit will run in.
target_dir="$(pwd)"
# `git -C <dir>` takes precedence over `cd <dir>`.
gdir="$(printf '%s' "$cmd" | sed -nE 's/.*git[[:space:]]+-C[[:space:]]+([^[:space:]&|;]+).*/\1/p' | tail -1)"
if [ -n "$gdir" ]; then
  target_dir="$gdir"
else
  cdir="$(printf '%s' "$cmd" | sed -nE 's/.*(^|[[:space:](&|;)])cd[[:space:]]+([^[:space:]&|;]+).*/\2/p' | tail -1)"
  [ -n "$cdir" ] && target_dir="$cdir"
fi
target_dir="${target_dir/#\~/$HOME}"

repo_root="$(git -C "$target_dir" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$target_dir")"
# Staged files only (what this commit will actually include), in the TARGET repo.
staged="$(git -C "$target_dir" diff --cached --name-only 2>/dev/null || true)"
# Plan files: anything under a .../plans/ directory ending in .md.
# Exclude the skills repo (agents/skills/plans/SKILL.md) which is not a reviewed plan.
plans="$(printf '%s\n' "$staged" | grep -E '(^|/)plans/.*\.md$' | grep -vE '(^|/)skills/' || true)"
[ -z "$plans" ] && exit 0

# newest_review <repo_root> <slug>: print the review file to judge, or nothing.
# Candidates are the plan's own canonical plan-review rounds under */reviews/*:
#   <date>-plan-review-[<date>-|<KEY>-<n>-]<slug>[-p<8 hex>]-r<N>.md
# The highest round number N wins; equal N goes to the newest mtime, then the
# greatest basename. Non-canonical names (other review kinds, backup variants,
# longer slugs) are ignored.
newest_review() {
  local root="$1" slug="$2" esc re best="" bestn=-1 f b n
  esc="$(printf '%s' "$slug" | sed -E 's/[].[\\*^$(){}?+|]/\\&/g')"
  re="^[0-9]{4}-[0-9]{2}-[0-9]{2}-plan-review-([0-9]{4}-[0-9]{2}-[0-9]{2}-|[a-z]+-[0-9]+-)?${esc}(-p[0-9a-f]{8})?-r([0-9]+)\\.md\$"
  shopt -s nocasematch
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    b="$(basename "$f")"
    [[ "$b" =~ $re ]] || continue
    n=$((10#${BASH_REMATCH[3]}))
    if [ "$n" -gt "$bestn" ]; then
      best="$f"; bestn="$n"
    elif [ "$n" -eq "$bestn" ]; then
      if [ "$f" -nt "$best" ] || { ! [ "$best" -nt "$f" ] && [[ "$b" > "$(basename "$best")" ]]; }; then
        best="$f"
      fi
    fi
  done < <(find "$root" -type f -name '*-r[0-9]*.md' \
              -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null \
            | grep -E '/reviews/' || true)
  shopt -u nocasematch
  printf '%s' "$best"
}

block_reasons=""
warnings=""

while IFS= read -r plan_rel; do
  [ -z "$plan_rel" ] && continue
  plan_abs="$repo_root/$plan_rel"
  [ -f "$plan_abs" ] || continue

  # Slug = plan stem minus a leading date (YYYY-MM-DD-) or story key (PROJ-1234-).
  base="$(basename "$plan_rel" .md)"
  slug="$(printf '%s' "$base" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//; s/^[A-Z]+-[0-9]+-//')"

  newest="$(newest_review "$repo_root" "$slug")"

  if [ -z "$newest" ]; then
    warnings="${warnings}\n  - ${plan_rel}: no review artifact matching slug '${slug}' found under */reviews/* (correlation by filename may have failed; verify manually)."
    continue
  fi

  # Block only on an explicit No-Go verdict in the newest review.
  if grep -qiE 'No-Go|ready=no|Ready for execution:[* ]*No' "$newest"; then
    block_reasons="${block_reasons}\n  - ${plan_rel}: newest review '$(basename "$newest")' verdict is No-Go. Address all Blockers+Mediums until the latest review states ready=yes, then re-commit."
  fi
done <<< "$plans"

if [ -n "$warnings" ]; then
  printf 'plan-review gate (warning):%b\n' "$warnings" >&2
fi

if [ -n "$block_reasons" ]; then
  printf 'plan-review gate BLOCKED commit (No-Go review):%b\n' "$block_reasons" >&2
  printf '\nRe-run the review-plan skill and address findings until the latest review artifact says ready=yes / Go.\n' >&2
  exit 2
fi

exit 0
