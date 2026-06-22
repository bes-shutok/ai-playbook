# User-level instructions

Cross-project engineering rules. **Source of truth:** `docs/AGENTS.md` in this repository. **Entrypoints:** `~/.codex/AGENTS.md` (symlink); `~/.claude/CLAUDE.md` (thin `@` import); `~/.copilot/copilot-instructions.md` (symlink via codex); `~/.gemini/GEMINI.md` (thin `@` import); Cursor `global-user-instructions.mdc` (`@`). Clone path: `instructions_repo` in `user_facts_path`.

**Hazard:** never symlink `~/.claude/CLAUDE.md` or `~/.gemini/GEMINI.md` to `~/.codex/AGENTS.md` (or the canonical file). Session tools append or rewrite those entrypoints; edits would overwrite the canonical body.

**Verify wiring** (after machine setup):

```bash
# Resolve INSTRUCTIONS_REPO from user_facts_path (key: instructions_repo)
CANONICAL="${INSTRUCTIONS_REPO:?}/docs/AGENTS.md"

test -L ~/.codex/AGENTS.md && test "$(readlink ~/.codex/AGENTS.md)" = "$CANONICAL"
test -L ~/.copilot/copilot-instructions.md
grep -q '@' ~/.claude/CLAUDE.md
grep -q '@' ~/.gemini/GEMINI.md
test -L ~/.agents/skills
test -L ~/.claude/skills
test ! -e ~/.gemini/skills
test -L ~/.gemini/config/skills
test -f ~/.gemini/config/skills/bootstrap-ai-playbook/SKILL.md
python3 -c "import os; assert os.path.realpath(os.path.expanduser('~/.gemini/config/skills')) == os.path.realpath(os.path.expanduser('~/.agents/skills'))"
```

## Context loading policy

| Always-on (every task) | On demand (read only what the task needs) |
|------------------------|-------------------------------------------|
| This file | `shared_docs_dir` files (`coding_guidelines.md`, `jvm_guidelines.md`, language files, `agent_workflow_guidelines.md`) |
| Repo `AGENTS.md` (project deltas) | `company_guidelines_master` |
| Applicable `facts.md` files | `project_guidelines_rel` in the current repo |
| Triggered skill `SKILL.md` bodies | Layer 2 repo docs (`docs/architecture/`, `docs/maintenance/`) |

**Do not bulk-load** canonical guideline files or whole skill corpora at task start. Open the **specific section or numbered rule** when editing, reviewing, or adding guidance in that domain (see `agent_workflow_guidelines.md` §51).

At task start: read **`user_facts_path`**, then ownership/repo facts when scoped (Cursor: `load-facts-at-task-start`).

## Instruction and facts hierarchy

**`AGENTS.md`:** public cross-project rules and pointers. **`facts.md`:** identity, paths, accounts, inventories (local only). **Skills:** portable workflow policy and numeric thresholds; not facts (see `agent_workflow_guidelines.md` §50).

| Tier | Rules | Facts |
|------|-------|-------|
| User + workspace | this file | `user_facts_path` |
| Ownership | repo `AGENTS.md` | ownership facts when company/personal scope matches |
| Repo | repo `AGENTS.md` | `repo_facts_rel` |

**Guideline homes** (resolve from facts keys; never hardcode paths in skills):

| Scope | Facts key |
|-------|-----------|
| Cross-project JVM/coding | `shared_docs_dir` + filename |
| Company | `company_guidelines_master` (edit here first) |
| Company repo mirror | `company_guidelines_repo_mirror_rel` (sync only) |
| Project | `project_guidelines_rel` |

**Placement:** full rule text in the canonical tier for that scope; lower tiers get one-line pointers. LLM workflow rules → skills or this file; not repo `AGENTS.md`. Instruction files may reference other docs; other docs stay self-contained unless structurally required.

**Repo setup:** `ln -sf AGENTS.md CLAUDE.md` unless Cursor duplicates both; then thin `CLAUDE.md` with `@AGENTS.md`. Never symlink `.github/copilot-instructions.md` to repo `AGENTS.md` when both exist.

**Cursor hooks (optional):** versioned in `cursor/hooks/`; install to `~/.cursor/hooks/` (`cursor/hooks/README.md`). Enforces git safety (including unscoped `git clean`) and optional execute-plan / em-dash gates; contracts in skills, not duplicated here.

## Hard rules (keep inline; high frequency)

- **Git push:** never push without explicit user instruction; never force-push without approval.
- **Execute-plan:** per-task `done` commits authorized for that run only; push still requires explicit instruction. See `execute-plan` skill.
- **Co-authored-by:** never add `Co-authored-by:` / `Co-Authored-By:` trailers; no `git commit --trailer` attribution. Disable Cursor Agent Attribution.
- **Formatting-only commits:** before commit, inspect full per-file diff; `git diff -w` is insufficient. See `agent_workflow_guidelines.md` #6.
- **Em dashes:** never use the em dash character (U+2014) in generated text; see `agent_workflow_guidelines.md` §39. Before commit, run `check-no-em-dash.sh` (`done` Step 2.76; default `~/.ai-playbook/scripts/check-no-em-dash.sh`).
- **Paths in docs/skills:** use `~/` home-relative paths, not `/Users/...`.
- **Public hygiene:** neutral placeholders in committed skills; run `public_hygiene_scan_script` before skill commits.
- **GitHub PR URL:** invoke `doing-code-review` or `receiving-code-review` per intent; see `agent_workflow_guidelines.md` #42 area / PR workflow skills.
- **Personal projects:** local git only unless user asks to push/open PR (`personal_projects_root` in facts).
- **Compaction:** run `learn` before allowing context compaction.

## Coding execution discipline (always-on)

Biases toward caution over speed; for trivial tasks, use judgment. Full detail: `agent_workflow_guidelines.md` **§57**.

- **Think first:** state assumptions; if multiple interpretations exist, present them; if unclear, stop and ask before coding.
- **Simplicity:** minimum code for the request; no speculative features, abstractions, or error handling for impossible cases; rewrite if overcomplicated.
- **Surgical edits:** touch only what the task requires; match existing style; do not refactor or "improve" adjacent code; remove orphans your changes created only. See also `agent_workflow_guidelines.md` **§8**.
- **Verify goals:** turn requests into testable success criteria; for multi-step work, plan each step with a verify check (tests, repro, or observable outcome).

## Skill maintenance (summary)

Rename skill → update front matter, title, self-refs. Shared skills → edit `~/.agents/skills/`; keep Codex-local copies separate. Skills stay language-agnostic and agent-agnostic; see `how-to-write-skills` skill and `agent_workflow_guidelines.md` #47–#48.

## Plans and temporary artifacts (summary)

Plans: resolved `{plans_dir}` only; see `plans` skill. RFCs on doc-hierarchy repos: `docs/history/feature-notes/`. Temp artifacts: `{tmp_dir}`; promote or delete same cycle; never reference `{tmp_dir}` from canonical docs.

## Gitignored docs safety (summary)

Verify `git check-ignore` before staging. Never `git stash clear` when docs-branch workflow active. Run docs-branch bash as **one** shell invocation (`RESTORE_TMP` does not persist across calls). Execute-plan session logs under `{tmp_dir}/execute-plan/`; snapshot before docs-branch sync. Details: `docs-branch` skill and `agent_workflow_guidelines.md` #6, #46.

## Shared guidelines index (`shared_docs_dir`; on demand)

| File | When to open |
|------|----------------|
| `agent_workflow_guidelines.md` | Review triage, scope, CI interpretation, formatting detection, coding discipline (**§57**), workflow lessons (**§1–§56**) |
| `coding_guidelines.md` | Universal coding patterns |
| `jvm_guidelines.md` | JVM/Spring conventions (e.g. #2 Duration properties, #3 Spring Cloud Config name, #6 logging) |
| `kotlin_guidelines.md` | Kotlin-specific (e.g. #16 `CancellationException`) |
| `java_guidelines.md` | Java-specific |
| `python_guidelines.md` | Python-specific |

**Agent workflow lessons:** do not restate §1–§49 here; consult the matching section when the trigger matches (false-positive review, scope discipline, merge verification, telemetry, GitOps, PR template, plain language, facts vs skills §50, etc.).

**Company guidelines master:** when company-scoped and the task touches cross-repo conventions (DDD, logging, DB naming, branch hygiene, concurrency patterns cited in workflow lessons).

**Project guidelines:** repo `AGENTS.md` indexes rule numbers; open `project_guidelines_rel` sections only for the active task.

## Domain snippets (pointer-first; detail in shared docs)

- Inline comments: avoid in bodies; see user `AGENTS.md` historical section → now `coding_guidelines` / project guidelines #38 where applicable.
- Sealed-class sentinel variants: dedicated bypass variant, not dummy success payload; see `coding_guidelines.md`.
- Background-task dedup / async retry: company guidelines #24–#25; concurrency audit before new controls; company #39; property reuse; company #40.
- Maven formatter-bound repos: scope `-pl … -am`; avoid root lifecycle that reformats all modules; `agent_workflow_guidelines.md` (scoped Maven section in prior body; fold into workflow doc if missing).
- Document creation: project `docs/` or `{tmp_dir}`; not session-state folders.
- Merge strategy: `git fetch` + verify remote before merge; full test suite after conflict resolution.
- Jira scoping ledger: `repo_facts_rel` **Related Jira tasks**; internal only; restate IDs in human-facing docs.
- External source archives: `sources.md` provenance under `docs/.../official/`.
- Brag documents: paths in `user_facts_path`.
