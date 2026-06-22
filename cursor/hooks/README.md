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

## Wire `~/.cursor/hooks.json`

If you do not have `beforeShellExecution` yet, merge the example below. If you already have hooks, add only the `git-safety.sh` entry without removing your other hooks.

See `cursor/hooks.json.example` for a minimal `hooks.json` fragment.

Required entry:

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "./hooks/git-safety.sh",
        "matcher": "git ",
        "failClosed": false
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
