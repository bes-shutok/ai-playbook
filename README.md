# Useful Agentic Commands Setup

## What This Repo Is
This repository is an agent instruction library: it contains first-party command specs plus vendored shared agent skills, Claude skills, and Codex skills mirrored from the local home directory.

For the verified runtime source-to-repository mapping used on this machine, see [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md). For external skill sources to consult when extending the registry, see [projects/.ai-playbook/skill-upstream-catalog.md](projects/.ai-playbook/skill-upstream-catalog.md).

Commands can be used in two ways:
1. Registered command mode: copy/link files into `.opencode/command/` and invoke by command name.
2. Direct file/manual mode: pass command file content to `codex`, `opencode`, or `claude`, or paste it manually in an interactive session.

## Repository Layout
```text
.
├── agents/
│   └── skills/
│       ├── agents-best-practices/   # vendored harness design (loops, permissions, evals, MCP)
│       ├── bootstrap-ai-playbook/   # repo .ai-playbook/ bootstrap (once per project when triggers fire)
│       ├── doc-hierarchy/
│       ├── doc-hierarchy-migrate/
│       ├── doc-hierarchy-upkeep/
│       └── i-have-adhd/             # vendored ADHD-friendly output style
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
│   └── scan-public-hygiene.patterns.example
├── projects/
│   └── .ai-playbook/
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
- Codex manages its own skills in `~/.codex/skills` autonomously and they are not vendored here.
- OpenCode uses `~/.opencode/command` for registered command copies.
- Copilot currently exposes local config/session state under `~/.copilot/`, not a reusable command or skill library.
- Gemini CLI discovers skills from `~/.agents/skills` (no separate `~/.gemini/skills` symlink needed). Antigravity global skills live under `~/.gemini/config/skills/` (symlink to the shared registry). Global instructions via `~/.gemini/GEMINI.md` (`@` import of `docs/AGENTS.md`).
- See [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md) for the full verified mapping and mirror rules.

## Command Catalog
| Command | File | What It Does | Key Behavior |
|---|---|---|---|
| `create-bug-ticket` | `create-documentation/create-bug-ticket.md` | Builds a concise Jira incident/bug description. | Enforces strict ticket size limit (`<= 800 chars`) and moves deep detail into a separate temporary Markdown document. |
| `create-design-rfc` | `agents/skills/rfc-design/SKILL.md` | Generates an MVP design RFC (implementation-ready, succinct). | **Canonical:** `rfc-design` skill. `create-documentation/create-design-rfc.md` is a redirect stub for OpenCode registration only. Hard gates, tiered review, section template in `references/rfc-sections.md`. |
| `create-tdd` | `create-documentation/create-tdd.md` | Generates a technical design document with strict completeness rules. | Requires mandatory sections and detailed testable content; enforces strong inference/traceability constraints. |
| `learn` | `agents/skills/learn/SKILL.md` | Extracts lessons from communication and applies documentation governance rules. | Classifies lessons, enforces placement scope rules, and requires retroactive consistency checks. Invoked as a skill (`$learn`). |
| `review-confluence-doc` | `agents/skills/review-confluence-doc/SKILL.md` | Reviews RFC/TDD documents on Confluence for quality, clarity, and actionability. | Fetches Confluence page via Atlassian MCP, provides structured feedback on console, optionally posts accepted feedback as a page comment. |
| `execute-plan` | `agents/skills/execute-plan/SKILL.md` | Orchestrates iterative implementation of a plans-skill plan via sub-agents. | Uses the recommended five-worker initial review, targeted post-fix workers, one fresh blocking-clean exit, at most five full-panel rounds, and one escalation per active run. |
| `plans` | `agents/skills/plans/SKILL.md` | Full plan lifecycle: create, edit, and complete implementation plans. | Phase 0 branch setup, Phase 1 requirements discovery interview, plan format enforcement with Evaluation Criteria, TDD task ordering, Plan Quality Gate (review/fix until Blocker=0 and Medium=0). |
| `doc-hierarchy` | `agents/skills/doc-hierarchy/SKILL.md` | Company service documentation hierarchy schema (Layer 1/2/3 layout, path resolution, migration-complete signal). | Read-only reference for where doc types belong; migration-complete signal includes `.ai-playbook/facts.md`; consumer skills read path keys from `.ai-playbook/facts.md`. |
| `doc-hierarchy-migrate` | `agents/skills/doc-hierarchy-migrate/SKILL.md` | Execute documentation hierarchy migration (Steps 0→6): classify, git mv, scaffold, verify. | Includes `scripts/verify-doc-hierarchy.sh` gates; run from skill install with `REPO_ROOT` set to the service repo. |
| `doc-hierarchy-upkeep` | `agents/skills/doc-hierarchy-upkeep/SKILL.md` | Keep Layer 1 and Layer 2 docs current after code changes on migration-complete repos. | Requires migration-complete signal; same PR/session as behavior or contract changes. |
| `bootstrap-ai-playbook` | `agents/skills/bootstrap-ai-playbook/SKILL.md` | Bootstraps the gitignored repo agent runtime dir (`.ai-playbook/`). | Gitignore gate, on-disk path discovery, `.ai-playbook/facts.md` creation or refresh; runs once per project when triggers fire (not every session); consumer skills read cached TOML keys from `.ai-playbook/facts.md`. |
| `agents-best-practices` | `agents/skills/agents-best-practices/SKILL.md` | Provider-neutral agent harness design and audit reference. | MVP blueprints, tool/permission matrices, workflow orchestration theory, skills/MCP governance, evals, and launch checklists; complements `how-to-write-skills`, `learn`, `plans`, and `execute-plan`. Vendored from upstream (see `agent-runtime-layout.md`). |
| `rfc-design` | `agents/skills/rfc-design/SKILL.md` | Create, edit, or review Design RFCs in Markdown. | Mode router (create/edit/review-local), tiered review pass (default agents include architecture, simplification, documentation; concurrency when matched at any depth), staging review under `{reviews_dir}/` per `review-staging`, regression evals in `references/eval-cases.md`; section template in `references/rfc-sections.md`; Confluence pages use `review-confluence-doc`. |
| `review-staging` | `agents/skills/review-staging/SKILL.md` | Gold source for review staging docs under `{reviews_dir}/` and `## Review Statistics`. | Panel Solo/Echo, Pattern tags, discard reason codes, Severity calibration, Triage outcomes; required `.stats.json` sidecar; `wrong-owner` discard code for panel tuning. Consumed by all review orchestrators. |
| `review-loop` | `agents/skills/review-loop/SKILL.md` | Repeat review-fix-done until one fresh review has zero unresolved blocking findings. | Starts with the five-worker panel and uses targeted post-fix workers. |
| `cursor-agent-diagnose` | `agents/skills/cursor-agent-diagnose/SKILL.md` | Diagnose Cursor IDE agent runtime failures (shell, hooks, skills, done lock, gh account). | Ordered checklist with bundled `run.sh`; distinguishes IDE bugs from local config; minimal recovery map. |
| `grilling` | `agents/skills/grilling/SKILL.md` | One-question-at-a-time decision interview until shared understanding. | Complements `premortem` (failure modes) and `plans` Phase 1; use when the user asks to grill a plan or design. |
| `domain-modeling` | `agents/skills/domain-modeling/SKILL.md` | Active ubiquitous-language and ADR discipline. | Glossary and `project-decisions.md` paths aligned with doc-hierarchy; pairs with `grilling` via `grill-with-docs`. |
| `handoff` | `agents/skills/handoff/SKILL.md` | Compact the session into a handoff doc for a fresh agent. | Output under `{tmp_dir}/handoff/` when repo facts exist; format aligned with `agents-best-practices` compaction handoff. |
| `i-have-adhd` | `agents/skills/i-have-adhd/SKILL.md` | ADHD-friendly output style: lead with the next action, number steps, no preamble/closers. | Opt-in via `/i-have-adhd`; off with "stop adhd mode". Vendored from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd); see `agent-runtime-layout.md`. |

Other vendored skills (`done`, `github-pr-workflow`, `receiving-code-review`, `doing-code-review`, `review-plan`, `tdd-guide`, etc.) live under [`agents/skills/`](agents/skills/). Browse that directory for the full set; register or invoke by skill path the same way as the table entries above.

## Scripts
| Script | What It Does |
|---|---|
| `scripts/facts_paths.py` | Facts-file key resolution and repo-anchor/project-key derivation (stdlib leaf). |
| `scripts/validate_review_staging.py` | Review staging doc and stats-sidecar validator; sidecar/conservation authority. |
| `scripts/summarize_review_stats.py` | Private review corpus discovery, conservation audit, and effectiveness report for Phase 2 review-effectiveness telemetry. Allowlisted facts-driven discovery (imports `facts_paths`), SHA-256 inventory into a local-only baseline under `~/.ai-playbook/review-telemetry/`, single-authority cutover classification (delegates per-sidecar classification to `validate_review_staging`), TOCTOU-safe private permissions, and a process-wide advisory lock across discover to publish. Aggregates current and legacy sidecars into cohort comparisons and emits a privacy-safe effectiveness report (`--json-report` / `--markdown-report`) with per-cohort `retain`, `review needed`, or `inconclusive` verdicts and an overall verdict. Path-level data and identifiers never enter tracked files. Run `python3 scripts/summarize_review_stats.py --selftest` for the built-in selftests. |

### Review Effectiveness Report
`scripts/summarize_review_stats.py --strict-audit` compares the pre-cutover baseline corpus against post-cutover (five-worker) growth reviews and writes a runtime-private effectiveness report when given `--json-report` / `--markdown-report` paths (conventionally `~/.ai-playbook/review-telemetry/effectiveness-report.{json,md}`, local only, never committed; both report flags default to none, so `--strict-audit` alone writes no report).

- **Cohort key** = `(review type, role, size bucket, domain-risk class)`, each derivable from both current and legacy sidecars. Panel mode is NOT a cohort key; it is the baseline/growth discriminator. Period (`baseline`/`growth`) is the sole within-cohort discriminator.
- **Verdict per cohort**: `inconclusive` when fewer than ten reviews on either side, or growth-side triage coverage is below 80% (baseline coverage does not gate, baseline is raw-only); otherwise `retain` only when median launches per initial full review fall by at least 25%, accepted unique findings do not fall by more than 20%, and the growth-side dropped-finding rate does not rise by more than 10 percentage points; else `review needed`. No automatic policy mutation.
- **Overall verdict**: `inconclusive` when there are zero evaluable cohorts; `retain` only when every evaluable cohort retains; otherwise `review needed` (per-cohort conjunction, no weighted average).
- **Privacy**: reports emit only aggregate counts and cohort verdicts. Repository names, paths, review filenames, ticket IDs, feature names, and content digests never appear. Privacy is enforced by a deny inventory built at audit time from the real corpus (`--emit-deny-inventory <path>` writes the built inventory to a runtime-private file under `~/.ai-playbook/review-telemetry/`); a fixed regex is kept only as a coarse pre-filter. Assert none of the built inventory strings appear in the public reports with `rg -nF -f <deny-inventory.txt> <report.json> <report.md>`. Historical review Markdown and sidecars are immutable read-only inputs (mechanically proven by a digest-comparison test, not a manual checkbox).
- **Determinism**: aggregate JSON is byte-stable across runs (canonical key order, stable trailing newline).

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
# claude/skills is a symlink to ../agents/skills; no separate sync needed
# codex/skills is managed by Codex autonomously; not vendored here
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # from repo root; see public_hygiene_scan_script in user facts
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
