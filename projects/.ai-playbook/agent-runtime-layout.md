# Agent Runtime Layout

## Core Concepts
- Runtime source: the home-directory folder an agent actually reads for reusable commands, skills, or registration copies.
- Mirror target: the repository folder that vendors a runtime source for documentation, review, or reuse.
- Shared registry: a reusable instruction source that is not tied to a single agent vendor, such as `~/.agents/skills`.
- Agent-local state: config, logs, caches, and session files that describe a tool installation but are not a reusable command or skill library.

## Purpose
This document is the canonical source of truth for how agent-specific instruction folders on this machine map into this repository.

Use it when:
- deciding where a skill like `$learn` actually comes from,
- mirroring local agent assets into this repository,
- documenting how Claude Code, Codex, Copilot, or OpenCode load reusable instructions.

## Verified Runtime Sources
### Shared Agent Skill Registry
- Runtime source: `~/.agents/skills`
- Mirror target: `agents/skills/`
- Notes: shared skills such as `$learn` come from this registry in the current setup.

### Claude Code
- Runtime source: `~/.claude/skills` (symlink → `~/.agents/skills`)
- Mirror target: `claude/skills/` (symlink → `../agents/skills`)
- Notes: `~/.claude/skills` is a symlink to `~/.agents/skills`; the repo mirrors this with `claude/skills -> ../agents/skills`. Only skills are active; `~/.claude/commands` does not exist on this machine.

### Codex
- Runtime source: `~/.codex/skills`
- Mirror target: none — Codex manages its own skills autonomously; they are not vendored into this repository.

### OpenCode
- Runtime source: `~/.opencode/command`
- Repository-local registration target: `.opencode/command/`
- Notes: this machine currently uses OpenCode command registration copies rather than a separate skill tree.

### Copilot
- Runtime source (global instructions): `~/.copilot/copilot-instructions.md` (symlink → `~/.codex/AGENTS.md` → `docs/AGENTS.md` in `instructions_repo`; see `~/.ai-playbook/facts.md`)
- Observed local folder: `~/.copilot/`
- Notes: config, logs, and session state live here; reusable global instructions use the symlink chain above, not a separate prose copy.

### Codex (global instructions)
- Canonical source: `docs/AGENTS.md` in this repository (`instructions_repo` in `~/.ai-playbook/facts.md`)
- Runtime entrypoint: `~/.codex/AGENTS.md` (symlink to canonical)

### Claude Code (global instructions)
- Canonical source: same as Codex
- Runtime entrypoint: `~/.claude/CLAUDE.md` (regular file with `@<instructions-repo>/docs/AGENTS.md` — not a symlink)

### Cursor (global instructions)
- Canonical source: same as Codex
- Runtime entrypoint: `~/.cursor/rules/global-user-instructions.mdc` (`@` reference)

### Facts files (local, not in public AGENTS.md)
- User + workspace: `~/.ai-playbook/facts.md` — identity, GitHub accounts, workspace roots, `shared_docs_dir`, skill keys, brag paths, instruction entrypoints
- Ownership: personal-projects and company-work trees (paths in `~/.ai-playbook/facts.md`): each scope's `.ai-playbook/facts.md`, `dictionary.md`, and company `company-guidelines.md` / runbooks where applicable
- Repo: `docs/facts.md` (use `docs/facts.md.example` as template in public repos)

## Entrypoint verification

Canonical user rules live in `<instructions_repo>/docs/AGENTS.md`. Codex, Claude Code, and Copilot load that file through home-directory entrypoints (`~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.copilot/copilot-instructions.md`), not by reading the repo path during a normal session.

**Run the bash checks in `docs/AGENTS.md` (Verify wiring)** after migration or machine setup. That section is the source of truth because it ships in the same document agents actually consume via the symlinks above.

## Mirror Rules
- Verify the actual on-disk runtime source before documenting an agent import path.
- Distinguish shared registries from vendor-specific folders instead of assuming everything comes from the current agent's home directory.
- Mirror reusable commands and skills into repository folders that preserve the source tree shape.
- Document home-directory runtime sources with `~`-based paths and repository targets with repository-relative paths; do not commit absolute local filesystem paths such as `/Users/...`.
- Do not treat config, logs, caches, or session-state folders as reusable instruction libraries.
- Keep detailed runtime mapping here and let overview documents reference this file instead of duplicating the full mapping.

## Local agent config (`~/.ai-playbook/`)

- **`facts.md`:** identity, workspace roots, `shared_docs_dir`, skill keys, brag paths, entrypoints (never commit).
- **`README.md`:** overview of facts + guideline symlink layout (never commit).

## Shared project guidelines (`projects/.ai-playbook/`)

- **Canonical source:** this directory in `instructions_repo` (version-controlled): coding/JVM/language guidelines, agent workflow rules, and this runtime-layout doc.
- **Runtime:** `~/Projects/.ai-playbook/` is a **directory symlink** to `instructions_repo/projects/.ai-playbook/` on this machine.
- **Not in this directory:** `facts.md` and `README.md` live under `~/.ai-playbook/` only (local, never committed here).

### Wire the runtime directory symlink

```bash
# Set INSTRUCTIONS_REPO from ~/.ai-playbook/facts.md (key: instructions_repo)
SHARED_DOCS=~/Projects/.ai-playbook   # default; override if shared_docs_dir differs in facts

# WARNING: if SHARED_DOCS is a plain directory (not already a symlink), the step below
# deletes it. Back up first when it may contain local-only files:
#   [ -d "$SHARED_DOCS" ] && [ ! -L "$SHARED_DOCS" ] && mv "$SHARED_DOCS" "${SHARED_DOCS}.bak.$(date +%Y%m%d)"

if [ -d "$SHARED_DOCS" ] && [ ! -L "$SHARED_DOCS" ]; then rm -rf "$SHARED_DOCS"; fi
ln -sfn "${INSTRUCTIONS_REPO:?}/projects/.ai-playbook" "$SHARED_DOCS"
```

Day-to-day: edit files under `projects/.ai-playbook/` in the repo; agents read the same paths via `~/Projects/.ai-playbook/` (or `shared_docs_dir` in `~/.ai-playbook/facts.md`).

Before committing changes under `projects/.ai-playbook/`, scan for sensitive content:

```bash
# Add employer-specific domain patterns from local facts if needed; keep committed examples neutral
rg -n -i '/Users/|<employer-domain>|api[_-]?key|password|secret' projects/.ai-playbook/
```

## Refresh Commands
```bash
rsync -a --delete --exclude '.DS_Store' ~/.agents/skills/ ./agents/skills/
# claude/skills is a symlink to ../agents/skills — no separate sync needed
# codex/skills is managed by Codex autonomously — not vendored here

# Company ownership docs mirror (optional; resolve company_projects_root from ~/.ai-playbook/facts.md)
# rsync -a --exclude '.DS_Store' --exclude 'tmp/' <company-projects-root>/.ai-playbook/ ./projects/.ai-playbook/company/
```

## Related Files
- `README.md`: overview and usage index for this repository.
- `AGENTS.md` (repo root): guidance for maintaining **this** command-spec repository only.
- `docs/AGENTS.md`: version-controlled **user-level** cross-project instructions (canonical source for Codex, Claude Code, Copilot CLI, Cursor).
- `docs/facts.md.example`: public template for per-repo `docs/facts.md`.
- `projects/.ai-playbook/`: canonical shared cross-project guidelines and this runtime-layout doc; runtime directory symlink at `~/Projects/.ai-playbook/`.
