#!/usr/bin/env bash
# UserPromptSubmit hook: detect GitHub PR references in the user prompt and
# remind Claude to invoke the appropriate code-review skill before responding.
# Exits 0 unconditionally; never blocks the prompt.
#
# Versioned home: agents/hooks/pr-skill-reminder/ (this file). The deployed
# user-level script ~/.claude/scripts/pr-skill-reminder.sh is a symlink to
# this copy; see README.md in this directory for install and behavior.
set -u

input=$(cat)
prompt=$(printf '%s' "$input" | jq -r '.prompt // ""' 2>/dev/null)

emit_reminder() {
  jq -nc '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: "GitHub PR reference detected in your prompt. Before responding, decide which code-review skill applies:\n- Active review (asked to review/look at/check the PR): invoke the `doing-code-review` skill.\n- Passive review (asked to address/respond to existing review comments): invoke the `receiving-review` skill.\n- Question only (e.g. \"what does this PR do?\"): no skill needed.\nDo not produce ad-hoc inline review findings without invoking the skill."
    }
  }'
}

# Patterns (case-insensitive, POSIX ERE — portable across macOS/Linux grep):
#   github.com/<owner>/<repo>/pull/<N>
#   <owner>/<repo>#<N>      e.g. owner/repo#123
#   PR #<N>                 e.g. "PR #231"
#   pull request #<N>
pattern='github\.com/[^[:space:]/]+/[^[:space:]/]+/pull/[0-9]+|[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+#[0-9]+|PR[[:space:]]+#[0-9]+|pull[[:space:]]+request[[:space:]]+#[0-9]+'

# Slash-command skip: when the prompt's FIRST token is a slash command that
# names an installed skill (a directory under one of the installed skills
# roots), the skill is already invoked explicitly and a reminder injection
# would be redundant — even when the prompt also carries a PR reference.
# A leading slash token naming NO installed skill (unknown or non-skill
# command) keeps the reminder when a PR reference is present.
read -r first_token _ <<< "$prompt"
case "$first_token" in
  /*)
    skill_name=${first_token#/}
    if [ -n "$skill_name" ] && { [ -d "$HOME/.claude/skills/$skill_name" ] || [ -d "$HOME/.agents/skills/$skill_name" ]; }; then
      exit 0
    fi
    ;;
esac

if printf '%s' "$prompt" | grep -qiE "$pattern"; then
  emit_reminder
fi

exit 0
