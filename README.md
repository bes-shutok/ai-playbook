# Useful Agentic Skills Setup

## What This Repo Is
This repository is a skill library: first-party workflow skills live under `agents/skills/`, alongside vendored shared agent skills, Claude skills, and Codex skills mirrored from the local home directory.

For the verified runtime source-to-repository mapping used on this machine, see [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md). For external skill sources to consult when extending the registry, see [projects/.ai-playbook/skill-upstream-catalog.md](projects/.ai-playbook/skill-upstream-catalog.md).

Skills can be used in two ways:
1. Skill mode: each agent loads skills from `agents/skills/` (directly or via its own registry or symlink); register or alias them per agent as needed.
2. Direct file/manual mode: pass a `SKILL.md` file's content to `codex`, `opencode`, or `claude`, or paste it manually in an interactive session.

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
└── projects/
    └── .ai-playbook/
        ├── agent-runtime-layout.md
        └── *-guidelines.md
```

- `claude/skills/`: symlink to `agents/skills/`, mirroring `~/.claude/skills → ~/.agents/skills`.
- `projects/.ai-playbook/`: shared cross-project guidelines plus runtime-layout documentation; mirrored at `~/Projects/.ai-playbook/` via directory symlink.

## Agent Folder Map
- Shared skills such as `$learn` come from `~/.agents/skills` in the current setup.
- Claude Code uses `~/.claude/skills` (symlink → `~/.agents/skills`); mirrored as `claude/skills → ../agents/skills`.
- Codex manages its own skills in `~/.codex/skills` autonomously and they are not vendored here.
- OpenCode uses `~/.opencode/command` for registered command copies.
- Copilot currently exposes local config/session state under `~/.copilot/`, not a reusable command or skill library.
- Gemini CLI discovers skills from `~/.agents/skills` (no separate `~/.gemini/skills` symlink needed). Antigravity global skills live under `~/.gemini/config/skills/` (symlink to the shared registry). Global instructions via `~/.gemini/GEMINI.md` (`@` import of `docs/AGENTS.md`).
- See [projects/.ai-playbook/agent-runtime-layout.md](projects/.ai-playbook/agent-runtime-layout.md) for the full verified mapping and mirror rules.

## Skill Catalog
| Skill | File | What It Does | Key Behavior |
|---|---|---|---|
| `jira-workflow` | `agents/skills/jira-workflow/SKILL.md` | Jira workflow: create/update Jira stories, create git branches from tickets, and build bug/incident tickets. | "Bug / Incident Ticket Format" section: strict ticket size limit (`<= 800 chars`, target 400), abbreviations clarified on first use, over-limit escalation asks the user what to trim; deep detail moves to a temporary Markdown document. |
| `rootly-retrospective` | `agents/skills/rootly-retrospective/SKILL.md` | Creates local, evidence-backed incident retrospectives for manual Rootly publishing. | Keeps external publishing out of scope, protects personal and sensitive data, uses connected Why paths, and replaces temporary chat links with local evidence excerpts. |
| `tdd-design` | `agents/skills/tdd-design/SKILL.md` | Generates a Technical Design Document with strict completeness rules. | Fixed sections 1–11 plus completeness/closure, semantic non-collapse, required-fields enforcement, traceability, and force diff completeness gates. |
| `learn` | `agents/skills/learn/SKILL.md` | Extracts lessons from communication and applies documentation governance rules. | Classifies lessons, enforces placement scope rules, and requires retroactive consistency checks. Invoked as a skill (`$learn`). |
| `review-confluence-doc` | `agents/skills/review-confluence-doc/SKILL.md` | Reviews RFC/TDD documents on Confluence for quality, clarity, and actionability. | Fetches Confluence page via Atlassian MCP, provides structured feedback on console, optionally posts accepted feedback as a page comment. |
| `confluence-page-sync` | `agents/skills/confluence-page-sync/SKILL.md` | Publishes and synchronizes local documents (RFCs, TDDs, design docs) to Confluence. | Full-body page updates, parent/child page creation, Mermaid diagram integrity via stored-HTML verification, and the Confluence version/source-revision ledger in the repository sync manifest. |
| `execute-plan` | `agents/skills/execute-plan/SKILL.md` | Orchestrates iterative implementation of a plans-skill plan via sub-agents. | Hard-gates every checklist item through the executable plan-task inclusion rule before implementation; then uses targeted review loops and one fresh blocking-clean exit. |
| `plans` | `agents/skills/plans/SKILL.md` | Full plan lifecycle: create, edit, and complete implementation plans. | Applies the checklist inclusion gate: executable plan tasks only. External prerequisites stay under Ship when and are never exception-admissible. Release-gate checklist exceptions require a bound receipt, why executable now, and completion evidence. Phase 1 confidence gate routes low-confidence unclear points to `grill-with-docs`; high-confidence points are listed as `## Assumptions`. |
| `review-plan` | `agents/skills/review-plan/SKILL.md` | Reviews implementation plans for correctness, completeness, and risk. | Treats checklist inclusion failures as blocking. External prerequisites never clear via exception. A release-gate exception passes only with bound receipt, why executable now, and completion evidence. |
| `doc-hierarchy` | `agents/skills/doc-hierarchy/SKILL.md` | Company service documentation hierarchy schema (Layer 1/2/3 layout, path resolution, migration-complete signal). | Read-only reference for where doc types belong; migration-complete signal includes `.ai-playbook/facts.md`; consumer skills read path keys from `.ai-playbook/facts.md`. |
| `doc-hierarchy-migrate` | `agents/skills/doc-hierarchy-migrate/SKILL.md` | Execute documentation hierarchy migration (Steps 0→6): classify, git mv, scaffold, verify. | Includes `scripts/verify-doc-hierarchy.sh` gates; run from skill install with `REPO_ROOT` set to the service repo. |
| `doc-hierarchy-upkeep` | `agents/skills/doc-hierarchy-upkeep/SKILL.md` | Keep Layer 1 and Layer 2 docs current after code changes on migration-complete repos. | Requires migration-complete signal; same PR/session as behavior or contract changes. |
| `bootstrap-ai-playbook` | `agents/skills/bootstrap-ai-playbook/SKILL.md` | Bootstraps the gitignored repo agent runtime dir (`.ai-playbook/`). | Gitignore gate, on-disk path discovery, `.ai-playbook/facts.md` creation or refresh; runs once per project when triggers fire (not every session); consumer skills read cached TOML keys from `.ai-playbook/facts.md`. |
| `agents-best-practices` | `agents/skills/agents-best-practices/SKILL.md` | Provider-neutral agent harness design and audit reference. | MVP blueprints, tool/permission matrices, workflow orchestration theory, skills/MCP governance, evals, and launch checklists; complements `how-to-write-skills`, `learn`, `plans`, and `execute-plan`. Vendored from upstream (see `agent-runtime-layout.md`). |
| `rfc-design` | `agents/skills/rfc-design/SKILL.md` | Create, edit, or review Design RFCs in Markdown. | Mode router (create/edit/review-local), tiered review pass (default agents include architecture, simplification, documentation; concurrency when matched at any depth), staging review under `{reviews_dir}/` per `review-staging`, regression evals in `references/eval-cases.md`; section template in `references/rfc-sections.md`; Confluence pages: reviews via `review-confluence-doc`; publishing via `confluence-page-sync`. |
| `review-staging` | `agents/skills/review-staging/SKILL.md` | Gold source for review staging docs under `{reviews_dir}/` and `## Review Statistics`. | Panel Solo/Echo, Pattern tags, discard reason codes, Severity calibration, Triage outcomes; required `.stats.json` sidecar; `wrong-owner` discard code for panel tuning. Consumed by all review orchestrators. |
| `review-loop` | `agents/skills/review-loop/SKILL.md` | Repeat review-fix-done until one fresh review has zero unresolved blocking findings. | Starts with the five-worker panel and uses targeted post-fix workers. |
| `cursor-agent-diagnose` | `agents/skills/cursor-agent-diagnose/SKILL.md` | Diagnose Cursor IDE agent runtime failures (shell, hooks, skills, done lock, gh account). | Ordered checklist with bundled `run.sh`; distinguishes IDE bugs from local config; minimal recovery map. |
| `grilling` | `agents/skills/grilling/SKILL.md` | One-question-at-a-time decision interview until shared understanding. | Complements `premortem` (failure modes) and `plans` Phase 1; use when the user asks to grill a plan or design. |
| `domain-modeling` | `agents/skills/domain-modeling/SKILL.md` | Active ubiquitous-language and ADR discipline. | Glossary and `project-decisions.md` paths aligned with doc-hierarchy; pairs with `grilling` via `grill-with-docs`. |
| `handoff` | `agents/skills/handoff/SKILL.md` | Compact the session into a handoff doc for a fresh agent. | Output under `{tmp_dir}/handoff/` when repo facts exist; format aligned with `agents-best-practices` compaction handoff. |
| `i-have-adhd` | `agents/skills/i-have-adhd/SKILL.md` | ADHD-friendly output style: lead with the next action, number steps, no preamble/closers. | Opt-in via `/i-have-adhd`; off with "stop adhd mode". Vendored from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd); see `agent-runtime-layout.md`. |

Other vendored skills (`done`, `github-pr-workflow`, `receiving-review`, `doing-code-review`, `review-plan`, `tdd-guide`, etc.) live under [`agents/skills/`](agents/skills/). Browse that directory for the full set; register or invoke by skill path the same way as the table entries above.

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
### A) Skill Invocation
```text
# Invoke via your agent's skill mechanism (by name or trigger phrase), examples:
rfc-design <PRD + architecture + service docs context>
tdd-design <TDD template + PRD + architecture + service docs context>
jira-workflow "create a bug ticket: <incident summary + impact + expected behavior + references>"
```

### B) Direct File / Manual Mode
```bash
# Codex CLI (non-interactive)
codex exec "$(cat agents/skills/rfc-design/SKILL.md)

Context:
$(cat ./context/rfc-input.md)"

# OpenCode CLI (non-interactive)
opencode run "$(cat agents/skills/tdd-design/SKILL.md)

Context:
$(cat ./context/tdd-input.md)"

# Claude Code CLI (non-interactive)
claude -p "$(cat agents/skills/jira-workflow/SKILL.md)

Context:
$(cat ./context/incident-input.md)"
```

```text
# Interactive fallback (codex / opencode / claude):
1) Start your CLI in interactive mode.
2) Paste the target SKILL.md content.
3) Append task-specific context and inputs.
4) Execute and iterate.
```

## How to Add a New Skill
1. Create `agents/skills/<name>/SKILL.md` with a kebab-case name and frontmatter (`name`, trigger-phrase `description`).
2. Copy the MIT `LICENSE.txt` from `agents/skills/plans/LICENSE.txt` into the new skill directory.
3. Add the skill to the catalog table in this README.
4. Add bidirectional Integration Points: the provider skill lists its consumers; each consumer references the provider in its workflow.
5. Run the public hygiene scan from repo root (`bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`; exit 0 required) before committing.

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
2. Use `$learn` to capture lessons and propagate them into documentation, instruction files such as `AGENTS.md`, and skill files.
3. For tool dependencies needed by commands/skills, prefer an isolated shared virtual environment over mutating system-managed Python installations.
4. Before changing host-level tooling, state execution context and impact; if a command is interrupted, verify partial side effects before continuing.

## Current Status
- All first-party workflows in this repo are exposed as skills under `agents/skills/`.
- Shared agent skills, local Claude skills, and local Codex skills are now vendored into this repository.
