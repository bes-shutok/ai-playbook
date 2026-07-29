# User-level instructions

Cross-project engineering rules. **Source of truth:** `docs/AGENTS.md` in this repository. **Entrypoints:** `~/.codex/AGENTS.md` (symlink); `~/.zcode/AGENTS.md` (thin `@` import); `~/.claude/CLAUDE.md` (thin `@` import); `~/.copilot/copilot-instructions.md` (symlink via codex); `~/.gemini/GEMINI.md` (thin `@` import); Cursor `global-user-instructions.mdc` (`@`). Clone path: `instructions_repo` in `user_facts_path`.

**Hazard:** never symlink `~/.claude/CLAUDE.md` or `~/.gemini/GEMINI.md` to `~/.codex/AGENTS.md` (or the canonical file). Session tools append or rewrite those entrypoints; edits would overwrite the canonical body.

**Verify wiring** (after machine setup):

```bash
# Resolve INSTRUCTIONS_REPO from user_facts_path (key: instructions_repo)
CANONICAL="${INSTRUCTIONS_REPO:?}/docs/AGENTS.md"

test -L ~/.codex/AGENTS.md && test "$(readlink ~/.codex/AGENTS.md)" = "$CANONICAL"
test -L ~/.copilot/copilot-instructions.md
grep -q '@' ~/.zcode/AGENTS.md
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

**ai-playbook-versioned hooks:** two cross-agent hooks ship under `agents/hooks/` (symlinked into each agent's `~/` config): lessons-recall (proactive recall via `UserPromptSubmit`/`PreInvocation` injection) and skill-gate (`PreToolUse` block on gated artifacts); the marker WRITE RECIPE and wiring live in `ai-playbook/agents/hooks/skill-gate/README.md` (single source). **Install, per-agent differences, session bridge, and same-repo multi-agent behavior:** `agents/hooks/lessons-recall/README.md` (**Install (step-by-step)**, **Agent differences (v2 at a glance)**, **Session channel precedence**). v2 Cursor-only change: optional `cursor-session-bridge.sh` exports `CURSOR_SESSION_ID` per composer tab; Claude/Codex/agy wiring unchanged. Probe: `python3 scripts/hooks_probe.py --all`.

## Hard rules (keep inline; high frequency)

- **Git push:** never push without explicit user instruction; never force-push without approval.
- **Slack outbound:** draft-only. Never send, post, schedule, edit, delete, or react in Slack, even when a request's phrasing could imply it. Create drafts only. Change this hard rule only if the user explicitly asks to do so; a request to "answer," "reply," or "write" means create a draft, not send it.
- **Execute-plan:** per-task `done` commits authorized for that run only; push still requires explicit instruction. See `execute-plan` skill.
- **Co-authored-by:** never add `Co-authored-by:` / `Co-Authored-By:` trailers; no `git commit --trailer` attribution. Disable Cursor Agent Attribution.
- **Formatting-only commits:** before commit, inspect full per-file diff; `git diff -w` is insufficient. See `agent_workflow_guidelines.md` #6.
- **Em dashes:** never use the em dash character (U+2014) in generated text; see `agent_workflow_guidelines.md` §39. Before commit, run `check-no-em-dash.sh` (`done` Step 2.76; default `~/.ai-playbook/scripts/check-no-em-dash.sh`).
- **Paths in docs/skills:** use `~/` home-relative paths, not `/Users/...`.
- **Public hygiene:** neutral placeholders in committed skills; run `public_hygiene_scan_script` before skill commits.
- **GitHub PR URL:** invoke `doing-code-review` or `receiving-code-review` per intent; see `agent_workflow_guidelines.md` #42 area / PR workflow skills.
- **Confluence ownership:** never update Confluence pages created by someone else unless the user specifically asks for that page to be changed. For any such page, request explicit user approval for each individual change before editing.
- **Personal projects:** local git only unless user asks to push/open PR (`personal_projects_root` in facts).
- **Compaction:** run `learn` before allowing context compaction.

## Coding execution discipline (always-on)

Biases toward caution over speed; for trivial tasks, use judgment. Full detail: `agent_workflow_guidelines.md` **§57**.

- **Think first:** state assumptions; if multiple interpretations exist, present them; if unclear, stop and ask before coding.
- **Explain simply, not simpler:** break down complicated ideas, cut unnecessary jargon, and explain as clearly as you can. Avoid details that are not strictly necessary in the current context. Truly understanding a topic means you can explain it simply. Do not oversimplify: if you make an idea too simple, it becomes inaccurate, misleading, or loses its core meaning.
- **Simplicity:** minimum code for the request; no speculative features, abstractions, or error handling for impossible cases; rewrite if overcomplicated. Climb the minimal solution ladder in `coding_guidelines.md` **#28** before adding code.
- **Surgical edits:** touch only what the task requires; match existing style; do not refactor or "improve" adjacent code; remove orphans your changes created only. See also `agent_workflow_guidelines.md` **§8**.
- **Verify goals:** turn requests into testable success criteria; for multi-step work, plan each step with a verify check (tests, repro, or observable outcome).
- **Recall before re-biting:** before a bug fix or a non-trivial design change, scan the symptom (or planned change) against the root-cause families table; if a family matches, grep the tagged corpus (user-level `development_lessons.md` + the repo's `docs/maintenance/development_lessons.md`) for the specific lesson and apply it BEFORE coding. Cross-project incidents are only reused if you check the pool; a re-bitten mistake is the exact failure this exists to prevent.

## Skill maintenance (summary)

Rename skill → update front matter, title, self-refs. Shared skills → edit `~/.agents/skills/`; keep Codex-local copies separate. Skills stay language-agnostic and agent-agnostic; see `how-to-write-skills` skill and `agent_workflow_guidelines.md` #47–#48.

## Plans and temporary artifacts (summary)

Plans: resolved `{plans_dir}` only; see `plans` skill. RFCs on doc-hierarchy repos: `docs/history/feature-notes/`. Temp artifacts: `{tmp_dir}`; promote or delete same cycle; never reference `{tmp_dir}` from canonical docs. Never dump `git diff` / review captures at the repo root (use `{tmp_dir}/code-review/…` or Cursor `agent-tools`; see `agent_workflow_guidelines.md` §50.3.2).

## Gitignored docs safety (summary)

Verify `git check-ignore` before staging. Never `git stash clear` when docs-branch workflow active. Run docs-branch bash as **one** shell invocation (`RESTORE_TMP` does not persist across calls). Docs-branch sync is **add-only**: missing shadow files (especially reviews) are restored from `refs/heads/docs`, not treated as deletions unless explicitly removed in the latest `docs` commit. Execute-plan session logs under `{tmp_dir}/execute-plan/`; snapshot before docs-branch sync. Details: `docs-branch` skill and `agent_workflow_guidelines.md` #6, #46.

## Shared guidelines index (`shared_docs_dir`; on demand)

| File | When to open |
|------|----------------|
| `agent_workflow_guidelines.md` | Review triage, scope, CI interpretation, formatting detection, coding discipline (**§57**), workflow lessons (**§1–§56**) |
| `coding_guidelines.md` | Universal coding patterns; #17 lesson tag-format spec + #17-#25 root-cause principle catalog (families A-H) |
| `jvm_guidelines.md` | JVM/Spring conventions (e.g. #2 Duration properties, #3 Spring Cloud Config name, #6 logging) |
| `kotlin_guidelines.md` | Kotlin-specific (e.g. #16 `CancellationException`) |
| `java_guidelines.md` | Java-specific |
| `python_guidelines.md` | Python-specific |

**Agent workflow lessons:** do not restate §1–§49 here; consult the matching section when the trigger matches (false-positive review, scope discipline, merge verification, telemetry, GitOps, PR template, plain language, facts vs skills §50, etc.).

**Company guidelines master:** when company-scoped and the task touches cross-repo conventions (DDD, logging, DB naming, branch hygiene, concurrency patterns cited in workflow lessons).

**Project guidelines:** repo `AGENTS.md` indexes rule numbers; open `project_guidelines_rel` sections only for the active task.

## Root-cause families (always-on recall index)

The point of the lessons corpus is to be recalled by **problem shape**, not by file location. When in doubt (reviewing a bug, writing a fix, designing, or a test fails), pattern-match the symptom against these families first, then grep the corpus for the specific tagged lesson. This table is the always-in-context index; full definitions and failure signatures live in `coding_guidelines.md` #18-#25.

| Cat | Family | Suspect it when |
|-----|--------|-----------------|
| #18 | **A. Equivalence-class coverage** | A test pins one cell of an input class; the fix must cover the whole partition, not just the tested cell |
| #19 | **B. Error-policy propagation** | A centralized fallible op is reused, but each call site's raise-vs-degrade policy was not carried over |
| #20 | **C. Representation: sentinel vs None vs exception** | "absent/invalid" is a sentinel, a None, or an exception and two got conflated; recoverability differs |
| #21 | **D. Single source of truth** | The same fact is authoritative in two places; one drifts |
| #22 | **E. Temporal / ordering invariants** | An earlier event consumes state a later event changes; a precondition went stale |
| #23 | **F. Layering / dependency direction** | Logic lives in the wrong layer, or a dependency points both ways (a lower layer reaches up) |
| #24 | **G. Data-loss observability** | A match/dedup/transform drops a record silently; exit 0 yet data is missing |
| #25 | **H. Verify the real thing, not the abstraction** | Code trusts a name, summary, mock, or field-name conflation instead of tracing real data |

**Corpus topology.** Cross-project incidents live in the **user-level** `development_lessons.md` under `shared_docs_dir` (strict `UL#N`, gated read-only by `lessons_index.py` at `learn` Step 6.6); per-repo incidents in each repo's `docs/maintenance/development_lessons.md` (convention `#N`, **skill-gate enforced** when hooks are installed: Write/Edit requires a fresh `learn.<project>.<session>.marker` from the `learn` skill; see `agents/hooks/skill-gate/README.md`).

**Recall command** (the tags ARE the index): `grep -nE '^\*\*Principle:\*\* Family <X>' <user_corpus_or_repo_file>` lists every lesson already tagged with the family. See the `generalize` and `learn` skills; a new user-level capture is gate-checked at `learn` Step 6.6.

**Citation policy.** Do not cite `UL#N` from project files; cite the lesson title (+ short description if decisive), else drop the sentence.

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
