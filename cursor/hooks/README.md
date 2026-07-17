# Cursor user hooks (optional runtime layer)

Versioned copies of user-level Cursor hooks. **Install target:** `~/.cursor/hooks/` (not committed inside service repos).

Policy contracts live in skills (`docs-branch`, `done`, `execute-plan`) and `agent_workflow_guidelines.md`. Hooks add a second line of defense for Cursor agents only.

## Prerequisites

- Cursor with Hooks enabled (Settings → Hooks)
- `jq` on `PATH` (hook fails open when missing)

## Install or update `git-safety.sh`

From this repository root:

```bash
mkdir -p ~/.cursor/hooks
install -m 755 cursor/hooks/git-safety.sh ~/.cursor/hooks/git-safety.sh
```

## Install or update `review-staging-gate.sh`

Optional second line of defense for review-loop / staging docs (pairs with
`scripts/validate_review_staging.py` synced to `~/.ai-playbook/scripts/`).

```bash
mkdir -p ~/.cursor/hooks ~/.ai-playbook/scripts
install -m 755 cursor/hooks/review-staging-gate.sh ~/.cursor/hooks/review-staging-gate.sh
install -m 644 scripts/validate_review_staging.py ~/.ai-playbook/scripts/validate_review_staging.py
```

Wire via `~/.cursor/hooks.json` (postToolUse after staging writes, beforeShellExecution
on review-loop commits, optional stop follow-up). See the script header for exact
matcher notes. If the validator file is missing, prefer failing closed or warning
loudly rather than silently allowing stub staging docs.

## Wire `~/.cursor/hooks.json`

Prefer copying from `cursor/hooks.json.example` (includes `git-safety.sh` and `review-staging-gate.sh`). If you already have hooks, merge both without removing your other entries.

See `cursor/hooks.json.example` for the full fragment. Minimum review-staging + git-safety wiring:

```json
{
  "version": 1,
  "hooks": {
    "postToolUse": [
      {
        "command": "./hooks/review-staging-gate.sh edit",
        "matcher": "Write"
      }
    ],
    "beforeShellExecution": [
      {
        "command": "./hooks/git-safety.sh",
        "matcher": "git ",
        "failClosed": false
      },
      {
        "command": "./hooks/review-staging-gate.sh commit",
        "matcher": "git "
      }
    ],
    "stop": [
      {
        "command": "./hooks/review-staging-gate.sh stop"
      }
    ]
  }
}
```

Path note: `command` is relative to `~/.cursor/` (user hooks), not the project root.

## What `git-safety.sh` blocks

| Command pattern | Action |
|-----------------|--------|
| `git reset --hard` | deny |
| `git commit` with `Co-authored-by` / `--trailer` | deny |
| Whole-repo `git clean` (including `git clean -fdq`) | deny |
| `git clean -- docs/tmp/` (and other ephemeral dirs) | allow |
| `git commit -m "..."` mentioning `git clean` in the message | allow |
| Force push to `main` / `master` / `pre-release` | ask |

Ephemeral dirs allowed for scoped clean: `docs/tmp/`, `docs/history/reviews/`, `docs/reviews/`, `.ai-playbook/`.

## Verify

```bash
bash cursor/hooks/git-safety.sh <<< '{"command":"git clean -fdq"}'
# expect permission deny

bash cursor/hooks/git-safety.sh <<< '{"command":"git clean -fd -- docs/tmp/"}'
# expect permission allow
```

After install, restart Cursor if hooks do not load immediately.

## Sync from canonical copy

When this directory changes, re-run the `install` command above. Do not edit `~/.cursor/hooks/git-safety.sh` by hand without backporting changes here.
