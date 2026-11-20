# pr-skill-reminder

A Claude-only `UserPromptSubmit` hook. When the user prompt references a
GitHub pull request, the hook injects a reminder to decide which code-review
skill applies — `doing-code-review` for active review, `receiving-review`
for passive review — before responding. The hook never blocks the prompt and
exits 0 unconditionally.

## Behavior

- A prompt carrying a PR reference (`github.com/<owner>/<repo>/pull/<N>`,
  `<owner>/<repo>#<N>`, `PR #<N>`, `pull request #<N>`; matched
  case-insensitively) emits the reminder naming the review skills (`doing-code-review`, `receiving-review`).
- A prompt whose FIRST token is a slash command naming an installed skill
  (a directory under one of the installed skills roots, `~/.claude/skills/`
  or `~/.agents/skills/`) emits nothing, even when the prompt also carries a
  PR reference: the skill is already invoked explicitly.
- A leading slash token naming NO installed skill (unknown or non-skill
  command) keeps the reminder when a PR reference is present.
- No PR reference emits nothing (exit 0).

## Boundary vs lessons-recall

The two hooks' boundary (independence, neither subsumes the other) is owned
by the boundary note in `agents/hooks/lessons-recall/README.md`
("Boundary vs pr-skill-reminder").

## Install pattern

The deployed user-level script `~/.claude/scripts/pr-skill-reminder.sh` is a
SYMLINK to this repository copy (this file is the source of record):

```bash
# INSTRUCTIONS_REPO = your local checkout of this repository (resolve from your own setup)
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/pr-skill-reminder/pr-skill-reminder.sh" \
  ~/.claude/scripts/pr-skill-reminder.sh
```

The `~/.claude/settings.json` registration is UNCHANGED: its `UserPromptSubmit`
entry keeps pointing at `~/.claude/scripts/pr-skill-reminder.sh`, which
resolves through the symlink to this versioned copy. `git pull` in the clone
updates hook behavior on the next prompt. Rollback: replace the symlink with
a regular file, or remove it together with the `UserPromptSubmit` entry in
`~/.claude/settings.json`.

## Probe wiring

`python3 scripts/hooks_probe.py --all` reports this hook's wiring from the
`Claude` / `pr-skill-reminder` row in
`projects/.ai-playbook/execute-plan-runtime-inventory.toml` (expected `FULL`,
event `UserPromptSubmit`). The probe also asserts that every skill name a
repository-versioned hook emits resolves under an installed skills root, so a
rename cannot leave the reminder pointing at a dead name. See the probe
overview in `agents/hooks/lessons-recall/README.md`.

## Dependencies

- `jq`: both the stdin extraction (`{"prompt": ...}`) and the envelope
  emission are jq-based. The jq-free python-parse convention in
  `agents/hooks/lessons-recall/README.md` is scoped to the four corpus
  adapters; this hook is Claude-only and Claude hosts ship jq, so it keeps
  the jq-based extraction.
