# Useful Agentic Commands Setup

## What This Repo Is
This repository is an agent instruction library: it contains first-party command specs plus vendored shared agent skills, Claude skills, and Codex skills mirrored from the local home directory.

For the verified runtime source-to-repository mapping used on this machine, see [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md).

Commands can be used in two ways:
1. Registered command mode: copy/link files into `.opencode/command/` and invoke by command name.
2. Direct file/manual mode: pass command file content to `codex`, `opencode`, or `claude`, or paste it manually in an interactive session.

## Repository Layout
```text
.
├── agents/
│   └── skills/
├── claude/
│   └── skills/
├── codex/
│   └── skills/
│       ├── .system/
│       ├── doc/
│       ├── openai-docs/
│       ├── pdf/
│       └── security-best-practices/
├── docs/
│   ├── AGENTS.md
│   ├── facts.md.example
│   └── projects/
│       ├── agent-runtime-layout.md
│       └── *-guidelines.md
└── create-documentation/
    ├── create-bug-ticket.md
    ├── create-design-rfc.md
    └── create-tdd.md
```

- `claude/skills/`: symlink to `agents/skills/`, mirroring `~/.claude/skills → ~/.agents/skills`.
- `projects/.ai-playbook/`: shared cross-project guidelines plus runtime-layout documentation; mirrored at `~/Projects/.ai-playbook/` via directory symlink.
- `create-documentation/`: commands for generating structured documentation artifacts.

## Agent Folder Map
- Shared skills such as `$learn` come from `~/.agents/skills` in the current setup.
- Claude Code uses `~/.claude/skills` (symlink → `~/.agents/skills`); mirrored as `claude/skills → ../agents/skills`.
- Codex manages its own skills in `~/.codex/skills` autonomously — not vendored here.
- OpenCode uses `~/.opencode/command` for registered command copies.
- Copilot currently exposes local config/session state under `~/.copilot/`, not a reusable command or skill library.
- See [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md) for the full verified mapping and mirror rules.

## Command Catalog
| Command | File | What It Does | Key Behavior |
|---|---|---|---|
| `create-bug-ticket` | `create-documentation/create-bug-ticket.md` | Builds a concise Jira incident/bug description. | Enforces strict ticket size limit (`<= 800 chars`) and moves deep detail into a separate temporary Markdown document. |
| `create-design-rfc` | `create-documentation/create-design-rfc.md` | Generates an MVP design RFC that is implementation-ready and succinct. | Uses hard gates: required inputs, assumptions/coverage confirmation, and explicit proceed signal before generation. |
| `create-tdd` | `create-documentation/create-tdd.md` | Generates a technical design document with strict completeness rules. | Requires mandatory sections and detailed testable content; enforces strong inference/traceability constraints. |
| `learn` | `agents/skills/learn/SKILL.md` | Extracts lessons from communication and applies documentation governance rules. | Classifies lessons, enforces placement scope rules, and requires retroactive consistency checks. Invoked as a skill (`$learn`). |
| `review-confluence-doc` | `agents/skills/review-confluence-doc/SKILL.md` | Reviews RFC/TDD documents on Confluence for quality, clarity, and actionability. | Fetches Confluence page via Atlassian MCP, provides structured feedback on console, optionally posts accepted feedback as a page comment. |
| `execute-plan` | `agents/skills/execute-plan/SKILL.md` | Orchestrates iterative implementation of a plans-skill plan via sub-agents. | Per-task and per-review-iteration `done` with preceding-step logs (`agent-logs.md`); review/fix loops (min 2, max 10 rounds) until two consecutive clear rounds (zero remaining Medium+ after `receiving-code-review` triage); archive plan; remove `docs/tmp/execute-plan/<slug>/` on success only. |
| `plans` | `agents/skills/plans/SKILL.md` | Full plan lifecycle: create, edit, and complete implementation plans. | Phase 0 branch setup, Phase 1 requirements discovery interview, plan format enforcement with Evaluation Criteria, TDD task ordering, Plan Quality Gate (review/fix until Blocker=0 and Medium=0). |

## Usage Examples (Hybrid)
### A) Registered Command Mode (`.opencode/command`)
```bash
# Register commands (example)
mkdir -p .opencode/command
cp create-documentation/create-design-rfc.md .opencode/command/create-design-rfc.md
cp create-documentation/create-tdd.md .opencode/command/create-tdd.md
cp create-documentation/create-bug-ticket.md .opencode/command/create-bug-ticket.md
```

```text
# Then invoke from your agent chat/command interface (examples)
/create-design-rfc <PRD + architecture + service docs context>
/create-tdd <TDD template + PRD + architecture + service docs context>
/create-bug-ticket <incident summary + impact + expected behavior + references>
```

### B) Direct File / Manual Mode
```bash
# Codex CLI (non-interactive)
codex exec "$(cat create-documentation/create-design-rfc.md)

Context:
$(cat ./context/rfc-input.md)"

# OpenCode CLI (non-interactive)
opencode run "$(cat create-documentation/create-tdd.md)

Context:
$(cat ./context/tdd-input.md)"

# Claude Code CLI (non-interactive)
claude -p "$(cat create-documentation/create-bug-ticket.md)

Context:
$(cat ./context/incident-input.md)"
```

```text
# Interactive fallback (codex / opencode / claude):
1) Start your CLI in interactive mode.
2) Paste the target command file content.
3) Append task-specific context and inputs.
4) Execute and iterate.
```

## How to Add a New Command
1. Create a new Markdown command spec in the appropriate folder.
2. Use a specific filename that avoids collisions with existing command names.
3. Add the command to the table in this README.
4. Add at least one usage example (registered mode and/or direct mode).
5. If a new command name collides (like `learn.md`), register it with a disambiguated alias.

## Vendored Agent Assets
Refresh the mirrored agent assets from the local home directory with:

```bash
rsync -a --delete --exclude '.DS_Store' ~/.agents/skills/ ./agents/skills/
# claude/skills is a symlink to ../agents/skills — no separate sync needed
# codex/skills is managed by Codex autonomously — not vendored here
```

Source mapping:
- `~/.agents/skills` -> `agents/skills`
- `~/.claude/skills` -> `claude/skills`
- `~/.codex/skills` -> `codex/skills`

## Lessons Learned
1. After a series of back-and-forth iterations, invoke the `$learn` skill to capture misunderstandings, mistakes, and corrections so the same issues are less likely to repeat.
2. Use `$learn` to capture lessons and propagate them into documentation, instruction files such as `AGENTS.md`, and command specs.
3. For tool dependencies needed by commands/skills, prefer an isolated shared virtual environment over mutating system-managed Python installations.
4. Before changing host-level tooling, state execution context and impact; if a command is interrupted, verify partial side effects before continuing.

## Current Status
- All files currently in this repo are used as command files.
- Shared agent skills, local Claude skills, and local Codex skills are now vendored into this repository.
