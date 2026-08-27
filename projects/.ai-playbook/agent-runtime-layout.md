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
- documenting how Claude Code, Codex, Copilot, Gemini CLI, or OpenCode load reusable instructions.

## Verified Runtime Sources
### Shared Agent Skill Registry
- Runtime source: `~/.agents/skills`
- Mirror target: `agents/skills/`
- Notes: shared skills such as `$learn` come from this registry in the current setup.

### Repo agent bootstrap (`agents/skills/bootstrap-ai-playbook/`)
- `bootstrap-ai-playbook`: bootstraps the gitignored `.ai-playbook/` runtime dir on a target project (gitignore gate, on-disk path discovery, `.ai-playbook/facts.md` creation or refresh). Runs once per project when triggers fire (missing file, invalid TOML, incomplete keys, not gitignored, stale paths); not every session. Consumer skills read TOML keys from `.ai-playbook/facts.md` via `using-skills` Step 0.

### Doc-hierarchy skill family (`agents/skills/doc-hierarchy*/`)
- `doc-hierarchy`: schema reference (Layer 1/2/3 layout, migration-complete signal).
- `doc-hierarchy-migrate`: migration workflow and `scripts/verify-doc-hierarchy.sh` gates.
- `doc-hierarchy-upkeep`: post-migration Layer 1/2 upkeep.
- Vendored with the shared registry; not a separate runtime source.

### Agent harness design (`agents/skills/agents-best-practices/`)
- `agents-best-practices`: vendored from [DenisSergeevitch/agents-best-practices](https://github.com/DenisSergeevitch/agents-best-practices) (MIT; upstream `metadata.version` in `SKILL.md` frontmatter, currently `1.2.0`).
- Scope: provider-neutral harness design (loops, permissions, MVP blueprints, evals, MCP/skills governance). Complements first-party workflow skills (`plans`, `execute-plan`, `learn`, `how-to-write-skills`).
- Re-sync: `git clone --depth 1` or `rsync` from upstream; preserve upstream `LICENSE` copyright in `LICENSE.txt`; run `public_hygiene_scan_script` before commit.

### ADHD-friendly output style (`agents/skills/i-have-adhd/`)
- `i-have-adhd`: vendored from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT; `metadata.upstream` set).
- Scope: shape replies for ADHD-friendly actionability (lead with next action, numbered steps, no preamble/closers). Opt-in: `/i-have-adhd`; off with "stop adhd mode".
- Runtime: shared registry covers Cursor, Claude skills path, Gemini/Antigravity skills symlink. Claude Code / Codex / Antigravity also use their native plugin installs when configured on the host.
- Re-sync: sparse-copy upstream `skills/i-have-adhd/` (drop `agents/`); refresh `LICENSE.txt` from upstream `LICENSE`; run `public_hygiene_scan_script` before commit.

### Productivity and domain skills (vendored from [mattpocock/skills](https://github.com/mattpocock/skills))
- **License:** copy [upstream LICENSE](https://github.com/mattpocock/skills/blob/main/LICENSE) verbatim into each skill's `LICENSE.txt` (`Copyright (c) 2026 Matt Pocock`). Do not use the first-party `plans/LICENSE.txt` copyright for vendored copies.
- `grilling`: one-question-at-a-time decision interview before acting; complements `premortem` (failure modes) and `plans` Phase 1.
- `grill-with-docs`: combo of `grilling` + inline `domain-modeling` (glossary and ADRs during the interview); user-invoked, and invoked by the `plans` Phase 1 confidence gate for low-confidence unclear points.
- `domain-modeling`: active ubiquitous-language and ADR discipline; paths aligned with doc-hierarchy (`docs/maintenance/glossary.md`, `docs/maintenance/project-decisions.md`, `docs/architecture/domain-model.md`); legacy `CONTEXT.md` / `docs/adr/` read-only fallback only.
- `handoff`: user-invoked session handoff doc for fresh agents; output under `{tmp_dir}/handoff/` when repo facts exist; aligned with `agents-best-practices` compaction handoff format.
- **Skill design vocabulary** (formerly `writing-great-skills`): merged into `how-to-write-skills/references/skill-design-principles.md` and `skill-design-vocabulary.md`; do not re-vendor as a separate skill.
- Re-sync: sparse-clone upstream skill folders; refresh `LICENSE.txt` from upstream root `LICENSE`; drop vendor `agents/` folders (Codex-specific); run `public_hygiene_scan_script` before commit.

### External upstream catalog (`projects/.ai-playbook/skill-upstream-catalog.md`)
- Canonical list of external skill, plugin, and harness sources to consult when extending or refreshing `agents/skills/`.
- Includes vendored status, local overlap notes, and refresh checklist.
- Vendored skills still record `metadata.upstream` per skill; this catalog is the registry-level index.

### Review staging and panel (`agents/skills/review-staging/`, `review-agents/`, consumers)
- `review-staging`: gold source for grouped severity output, worker/lens launch accounting, descendant declarations, blocking-aware findings, overflow, and compatible sidecars.
- `review-agents`: shared lens catalogs bundled into the recommended five workers. `review-panel-selection.md` owns full/focused panels, escalation, conditional risk lenses, and tiered ownership; `severity-calibration.md` owns tangible consequence tiers and finding budgets.
- Consumers: `doing-code-review`, `review-plan`, `review-loop`, `receiving-code-review`, `rfc-design`, `review-confluence-doc`, `execute-plan` Phase 3, `done` (Step 2.64). Staging docs are gitignored on consumer repos; sync to orphan `docs` branch via `docs-branch`.

### Claude Code
- Runtime source: `~/.claude/skills` (symlink → `~/.agents/skills`)
- Mirror target: `claude/skills/` (symlink → `../agents/skills`)
- Notes: `~/.claude/skills` is a symlink to `~/.agents/skills`; the repo mirrors this with `claude/skills -> ../agents/skills`. Only skills are active; `~/.claude/commands` does not exist on this machine.

### Cursor (skills)
- Runtime source: `~/.cursor/skills` (symlink → shared registry or this repo's `agents/skills/` depending on machine setup)
- Mirror target: `agents/skills/` (canonical tracked copy)
- Notes: Cursor also loads global instructions via `~/.cursor/rules/` (see Cursor global instructions below). Do not assume `~/.cursor/skills` equals `~/.agents/skills` without verifying the symlink target.

### Codex
- Runtime source: `~/.codex/skills`
- Mirror target: none; Codex manages its own skills autonomously and they are not vendored into this repository.

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
- Runtime entrypoint: `~/.claude/CLAUDE.md` (regular file with `@<instructions-repo>/docs/AGENTS.md`; not a symlink)

### Cursor (global instructions)
- Canonical source: same as Codex
- Runtime entrypoint: `~/.cursor/rules/global-user-instructions.mdc` (`@` reference)
- Optional hooks: versioned under `cursor/hooks/` in this repo; install to `~/.cursor/hooks/` per `cursor/hooks/README.md`

### Gemini CLI and Antigravity (Google)
- Canonical skill source: `~/.agents/skills` (shared registry; symlink to `instructions_repo/agents/skills`).
- **Gemini CLI** discovers `~/.agents/skills/` natively. Do **not** add a redundant `~/.gemini/skills` symlink; it duplicates the same registry with no benefit.
- **Antigravity** global skills: `~/.gemini/config/skills/` ([official docs](https://antigravity.google/docs/skills)). Antigravity does **not** scan `~/.agents/skills/` on its own.
- **Wire Antigravity with one whole-directory symlink** to the shared registry (edit skills once):

```bash
ln -sfn ~/.agents/skills ~/.gemini/config/skills
```

- **Whole folder vs per-skill symlinks:** symlink the **directory**, not each skill inside it. Per-skill symlinks under Antigravity paths are silently ignored ([vercel-labs/skills#633](https://github.com/vercel-labs/skills/issues/633)). A single directory symlink exposes real skill subfolders through normal path traversal.
- **Fallback if Antigravity still misses skills:** Settings → Customizations → Skill Custom Paths → add the **absolute** path to `~/.agents/skills` (tilde may not expand). Restart IDE; open a fresh conversation.
- Runtime entrypoint (global instructions): `~/.gemini/GEMINI.md` (regular file with `@<instructions-repo>/docs/AGENTS.md`; supports `@` imports). **Not** a symlink: `/memory add` appends to the global file.
- Observed local folder: `~/.gemini/` (`config/` for Antigravity skills + MCP; session state under `antigravity/`)

### Facts files (local, not in public AGENTS.md)
- User + workspace: `user_facts_path` facts key → `~/.ai-playbook/facts.md`; identity, GitHub accounts, workspace roots, **guideline canonical keys**, skill **path** keys, brag paths, instruction entrypoints. **Not** portable workflow policy or numeric thresholds (those live in skill `SKILL.md`; see `agent_workflow_guidelines.md` §50). **Load first every task** (Cursor: `load-facts-at-task-start.mdc`).
- Ownership: personal-projects and company-work trees (`personal_ownership_docs_dir`, `company_ownership_docs_dir` keys): each scope's `facts.md`, `dictionary.md`, and **`company_guidelines_master`** / runbooks where applicable
- Repo: `repo_facts_rel` in the current repository (typically `.ai-playbook/facts.md`; see `bootstrap-ai-playbook` skill for format)

### Guideline masters vs repo mirrors (facts keys)
- Cross-project: `shared_docs_dir`; canonical JVM/coding guideline files
- Company: `company_guidelines_master`; canonical; repo `company_guidelines_repo_mirror_rel` is sync-only
- Project: `project_guidelines_rel` in the current repo; canonical for that repo

## Entrypoint verification

Canonical user rules live in `<instructions_repo>/docs/AGENTS.md`. Codex, Claude Code, Copilot, and Gemini CLI load that file through home-directory entrypoints (`~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.copilot/copilot-instructions.md`, `~/.gemini/GEMINI.md`), not by reading the repo path during a normal session.

**Run the bash checks in `docs/AGENTS.md` (Verify wiring)** after migration or machine setup. That section is the source of truth because it ships in the same document agents actually consume via the symlinks above.

### Wire Gemini CLI and Antigravity (instructions + skills)

```bash
# Set INSTRUCTIONS_REPO from ~/.ai-playbook/facts.md (key: instructions_repo)
CANONICAL="${INSTRUCTIONS_REPO:?}/docs/AGENTS.md"

# Shared skill registry (canonical edit path)
test -L ~/.agents/skills || ln -sfn "${INSTRUCTIONS_REPO}/agents/skills" ~/.agents/skills

# Antigravity vendor folder: whole-directory symlink (NOT per-skill links inside)
ln -sfn ~/.agents/skills ~/.gemini/config/skills        # Antigravity global

# Global instructions: thin @ import (do NOT symlink; /memory add appends here)
cat > ~/.gemini/GEMINI.md <<EOF
# User instructions (Gemini CLI)

Canonical cross-project rules: \`${CANONICAL}\` (edit there; version-controlled).

@${CANONICAL}
EOF

# Verify
grep -q '@' ~/.gemini/GEMINI.md
test -L ~/.agents/skills
test ! -e ~/.gemini/skills
test -L ~/.gemini/config/skills
test -f ~/.gemini/config/skills/bootstrap-ai-playbook/SKILL.md
python3 -c "import os; assert os.path.realpath(os.path.expanduser('~/.gemini/config/skills')) == os.path.realpath(os.path.expanduser('~/.agents/skills'))"
```

## Mirror Rules
- Verify the actual on-disk runtime source before documenting an agent import path.
- Distinguish shared registries from vendor-specific folders instead of assuming everything comes from the current agent's home directory.
- Mirror reusable commands and skills into repository folders that preserve the source tree shape.
- Document home-directory runtime sources with `~`-based paths and repository targets with repository-relative paths; do not commit absolute local filesystem paths such as ``$HOME/...` (absolute home paths)`.
- Do not treat config, logs, caches, or session-state folders as reusable instruction libraries.
- Keep detailed runtime mapping here and let overview documents reference this file instead of duplicating the full mapping.

## Local agent config (`~/.ai-playbook/`)

- **`facts.md`:** identity, workspace roots, `shared_docs_dir`, skill keys, brag paths, entrypoints, MCP auth **path keys** (never commit).
- **`credentials/`:** local OAuth backups for Slack/Atlassian MCP (`mcp-cursor.json`, `mcp-atlassian-mcp-remote/`). Mode `700`/`600`. Never commit.
- **`scripts/`:** runtime copies of tracked scripts. Phase 1 deploys and byte-checks `validate_review_staging.py` against the repository source; durable symlink or installer management is a later telemetry phase.
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
rg -n -i 'absolute-home-path|<employer-domain>|api[_-]?key|password|secret' projects/.ai-playbook/
```

## Refresh Commands
```bash
rsync -a --delete --exclude '.DS_Store' ~/.agents/skills/ ./agents/skills/
# claude/skills is a symlink to ../agents/skills; no separate sync needed
# codex/skills is managed by Codex autonomously; not vendored here

# Company ownership docs mirror (optional; resolve company_projects_root from ~/.ai-playbook/facts.md)
# rsync -a --exclude '.DS_Store' --exclude 'tmp/' <company-projects-root>/.ai-playbook/ ./projects/.ai-playbook/company/
```

## Related Files
- `README.md`: overview and usage index for this repository.
- `skill-upstream-catalog.md`: external skill/plugin/harness sources for vendoring and periodic refresh (this directory).
- `AGENTS.md` (repo root): guidance for maintaining **this** skill-library repository only.
- `docs/AGENTS.md`: version-controlled **user-level** cross-project instructions (canonical source for Codex, Claude Code, Copilot CLI, Gemini CLI, Cursor).
- `bootstrap-ai-playbook` skill: creates/updates repo `.ai-playbook/facts.md` (`repo_facts_rel`; no machine paths in repo).
- `projects/.ai-playbook/`: canonical shared cross-project guidelines and this runtime-layout doc; runtime directory symlink at `~/Projects/.ai-playbook/`.
