# Agent runtimes inside agterm

The `agtermctl` surface is identical no matter which agent CLI loads this skill. What differs per
runtime is: how you detect it, how to launch and resume it in a session, where its agent-status hook
is wired, and where this skill is installed. Everything below was checked against agterm 0.25 and
the CLIs' own `--help` output; re-verify the flags on the live machine before scripting them; the
CLIs move faster than agterm does.

## What any agent inherits inside agterm

Every process an agterm session spawns, the agent CLI, its hooks, its tool shells, gets the
`AGTERM_*` environment (see SKILL.md). This is why one mechanism serves every runtime: a hook or a
tool shell under ANY agent can call `agtermctl` and reach the right session via
`--target "$AGTERM_SESSION_ID"`. A runtime needs no agterm awareness of its own; it only needs a
place to hang a shell line.

## Runtime at a glance

| Runtime | Interactive launch | Resume a session | Inherited env marker | Status route |
|---|---|---|---|---|
| Claude Code | `claude` | `claude --resume <id>` (adding `--fork-session` MINTS A NEW id; see examples.md) | `CLAUDECODE=1`, `CLAUDE_CODE_SESSION_ID` | hooks in `~/.claude/settings.json` → `agterm-agent-status.sh` |
| Codex | `codex` | `codex resume <uuid>` (`--last` for the most recent) | none reliable | lifecycle hook `agterm-codex-status.sh` (installer-managed) |
| Cursor agent CLI | `cursor-agent` | `cursor-agent --resume [chatId]`, or `--continue` | `CURSOR_INVOKED_AS` (set by the launcher, inherited) | shell integration only (it is in the default `AGTERM_AGENT_RE`), coarse active/idle |
| Copilot CLI | `copilot` | `copilot --resume[=id]`, or `--continue` | none reliable | none shipped; add `copilot` to `AGTERM_AGENT_RE` (below) |
| ZCode | `zcode` | `zcode --resume <sess_…>`, or `-c` | `ZCODE_APP_VERSION` (and other `ZCODE_*`) | hooks in `~/.zcode/cli/config.json` → `agterm-agent-status.sh` |
| OpenCode | `opencode` | `opencode -c`, or `-s <session-id>` | none reliable | plugin `~/.config/opencode/plugins/agterm-status.js` (installer-managed) |
| Pi | `pi` | none documented (check `pi --help`) | none reliable | extension `~/.pi/agent/extensions/agterm-status.ts` (installer-managed) |

"None reliable" means the runtime sets no marker a child shell can test; detect those by which
hook config is live or by asking the user, not by env.

## Launching an agent into a session

`session new --command` binds the agent as the session process. The command runs argv-style with the
app's GUI `PATH` (no `/opt/homebrew/bin`), so wrap in a login shell or use absolute paths; exit 127
means you did not (troubleshooting.md). The same pattern fits every runtime:

```bash
agtermctl session new --cwd ~/proj --name "codex"   --command "zsh -lc 'codex'"
agtermctl session new --cwd ~/proj --name "cursor"  --command "zsh -lc 'cursor-agent'"
agtermctl session new --cwd ~/proj --name "copilot" --command "zsh -lc 'copilot'"
agtermctl session new --cwd ~/proj --name "zcode"   --command "zsh -lc 'zcode'"
```

Confirm in `tree --json` that the new node's `foreground` shows the agent, not a bare shell prompt
(a `zsh -lc` wrapper reports the zsh argv with the agent inside it). Add `--wait` to hold the row
open with the final output if the agent exits. To resume instead of starting fresh, wrap the
runtime's resume form from the table above the same way (`zsh -lc '<resume line>'`).

### Restoring an agent session across an agterm restart

`session restore <line>` pins the shell line a pane re-runs on the next launch. Pin the runtime's
resume form from the table:

```bash
agtermctl session restore "codex resume <uuid>"          --target "$AGTERM_SESSION_ID"
agtermctl session restore "cursor-agent --resume <chatId>" --target "$AGTERM_SESSION_ID"
```

A pin runs as a TYPED SHELL LINE in the session's login shell, not through `--command`'s argv path:
a binary on your normal PATH (claude, cursor-agent, codex) resolves bare, and shell operators work
as written. The `zsh -lc` wrap in the launch section exists for `--command`'s GUI PATH, not for
restore pins.

The pin is sticky: it fires on every restart until cleared. The known non-idempotent case is
Claude Code with `--fork-session` (each restart would mint a new id); the SessionStart-hook rewrite
in examples.md fixes it, and the same hook shape (rewrite the pin to the live id on every start)
ports to any runtime whose resume mints a new session id. Before relying on resume-in-place for the
other runtimes, verify it on your build: resume, restart, resume again by pin, and check you land
in the same conversation.

## Agent-status wiring per runtime

All routes end at `~/.config/agterm/agent-status/agterm-agent-status.sh`, the installer's wrapper:
it maps its first argument to `agtermctl session status <idle|active|completed|blocked>`, targets
`$AGTERM_SESSION_ID`, forwards `$AGTERM_PANE`/`$AGTERM_PANE_ID`, suppresses all output, and always
exits 0 so a hook can never block the agent. Two grades of fidelity:

- **Hook routes** (Claude Code, Codex, ZCode, OpenCode, Pi) give per-turn state: active while
  working, `completed` on stop, `blocked` when the agent asks for input or permission.
- **Shell integration** (bash/zsh/fish, `~/.config/agterm/agent-status/shell/integration.sh`)
  gives coarse process-level state: `active` while a matching foreground command runs, `idle` at the
  next prompt. Which commands match is `AGTERM_AGENT_RE`, default
  `^(gemini|cursor-agent|aider|crush|goose)([[:space:]]|$)`, overridable before the `source` line
  in your rc.

What the installer writes per runtime (check the live files; installs differ per machine):

- **Claude Code**, `~/.claude/settings.json` hooks: `UserPromptSubmit`/`PostToolUse` → `active
  --blink`, `Stop` → `completed --auto-reset`, `Notification` (matcher `permission_prompt`) →
  `blocked`. Restart Claude Code after a change so it re-reads its settings.
- **ZCode**, the `hooks` block of its user config (`~/.zcode/cli/config.json`): `SessionStart` /
  `UserPromptSubmit` / `PreToolUse` → `active`, `PermissionRequest` → `blocked --blink`,
  `PostToolUseFailure` → `blocked`, `Stop` → `completed --auto-reset`. Restart the session so hooks
  reload.
- **Codex**, the dedicated `~/.config/agterm/agent-status/agterm-codex-status.sh`: maps Codex's
  lifecycle actions (`session-start`, `user-prompt-submit`, `pre-tool-use`, `post-tool-use`,
  `permission-request`, `stop`) to statuses, and while Codex works, watches the session's own
  visible footer for a real approval prompt, so an auto-reviewed `permission-request` does not
  false-flag `blocked`. When the installer wires it, the entries live in Codex's hooks config
  (`~/.codex/hooks.json`); a machine can have the wrapper installed with NO wiring entry: the
  installer was skipped or the config was replaced. Tell the two apart by reading the file: no
  agterm entry means the glyph stays dead until you re-run Help ▸ Install Agent Status Hooks… or
  add the entries by hand. Restart Codex after any change.
- **Cursor agent CLI**: no dedicated hook ships. The shell integration covers it: `cursor-agent` is
  in the default `AGTERM_AGENT_RE`, giving coarse active/idle only. There is no per-turn hook route
  for it yet.
- **Copilot CLI**: nothing ships and `copilot` has no hooks feature the installer could target.
  Get coarse active/idle by extending the regex in your rc **before** the `source` line:

  ```bash
  export AGTERM_AGENT_RE='^(gemini|cursor-agent|aider|crush|goose|copilot)([[:space:]]|$)'
  source "$HOME/.config/agterm/agent-status/shell/integration.sh"
  ```

  Add a HOOK-COVERED CLI (zcode, claude, codex) to this regex only on machines where that runtime's
  hook wiring is absent. With its hooks live, the coarse layer fights the per-turn hooks on the
  same glyph, which is exactly why they are absent from the default.
- **Pi**, extension `~/.pi/agent/extensions/agterm-status.ts`; it installs only after Pi has
  created `~/.pi/agent`, and Pi must be restarted (or run `/reload`) to load it.
- **OpenCode**, plugin `~/.config/opencode/plugins/agterm-status.js`; it installs only after
  OpenCode has created `~/.config/opencode`, and OpenCode must be restarted to load it.

## Where this skill installs per runtime

The bundled scripts (`scripts/show-image.sh`) sit beside `SKILL.md` in every layout; resolve them
against the directory the `SKILL.md` was loaded from, never a fixed path:

- Claude Code: `~/.claude/skills/agterm/`
- Cursor: `~/.cursor/skills/agterm/`
- ZCode: `~/.agents/skills/agterm/` (the shared skill registry)
- Codex: `~/.codex/skills/agterm/` (a separate copy, not a symlink; re-sync it when the skill
  changes) or a plugin-cache install
- Copilot CLI: `~/.copilot/skills/<skill-name>/` where the runtime supports a skills directory
- The app's own **Help ▸ Install Agent Skill…** copy, wherever it was placed

## Diagnosing a runtime's status wiring

Run the flow in troubleshooting.md ("The agent-status glyph does not update"); it covers route
identification, hook registration, and the wrapper's `agtermctl` resolution, and points back here
for the per-runtime wiring facts. The one fact unique to this file is the by-hand wrapper test:

```bash
"$HOME/.config/agterm/agent-status/agterm-agent-status.sh" active --blink
```

The sidebar glyph for this session should flip immediately. If the wrapper works by hand but the
hook does not fire, the problem is the runtime's hook registration, not agterm. The third common
failure is environmental: the hook ran somewhere `AGTERM_SESSION_ID` was scrubbed or poisoned, not
inside the session it reported for (see troubleshooting.md, "The agent-status glyph updates the
wrong session").
