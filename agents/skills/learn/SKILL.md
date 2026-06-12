---
name: learn
description: Capture concrete lessons from task communication and update the documentation and instruction corpus with strict placement, consolidation, and enforceable-rule criteria.
---

# Learn from Communication and Update Documentation Corpus

## Core Concepts
- Communication lesson: a concrete correction, missing detail, or repeated friction point observed during the task.
- Placement scope: the single destination category for a lesson (`BEST_PRACTICES`, module docs, LLM rule, LLM example, or temporary artifact).
- Canonical document: long-lived source of truth under `docs/`.
- Temporary artifact: summary/review/analysis/note/draft/worklog with short-lived value.
- Enforceable LLM rule: a concise do/do-not instruction that prevents repeat mistakes.
- Facts document: a local-only file providing environment-specific values (paths, domains). This skill references keys from the user's facts documents — see the project or shared `facts.md` for values. Key used: `shared_docs_dir` (cross-project guidelines directory).

## When to Use
Use this skill when asked to:
- learn from communication in the current task,
- capture recurring mistakes/corrections,
- update repository docs or instruction rules from lessons learned,
- consolidate duplicated documentation.

Keep this skill scoped to documentation/instruction corpus updates. Do not use it to trigger product code or contract refactors. Do not commit changes — committing is the `done` skill's responsibility.

## Goal
In one run:
1. Extract lessons from communication in the current task context.
2. Reset the learn counter by deleting `/tmp/learn-counter-${PPID}-<dir_hash>` where `<dir_hash>` is the first 12 hex chars of `shasum` of `$PWD` (the session+project-scoped counter that reminds you to run learn before compaction).
3. Place each lesson at the correct scope.
3. Consolidate docs to remove duplication.
4. Update instruction files only with enforceable, high-value rules.
5. Consolidate instruction rules by grouping overlaps and removing ambiguous/redundant duplicates.
6. Keep repository structure and module layout compliant.
7. Keep this workflow scoped to documentation/instruction corpus updates only.

## Step 1: Extract Lessons
Review communication from this task and list concrete items:
- mistakes and false assumptions
- user corrections and constraints
- missing or misleading documentation
- recurring rework/friction

Classify each lesson as exactly one:
- Human best-practice guidance
- Module/system-specific knowledge
- Enforceable LLM instruction rule
- LLM-only example/playbook
- Temporary artifact

**Important: style and wording corrections are lessons too.** If a user corrects the tone, phrasing, vocabulary, or formatting of generated output (e.g. "remove long dashes", "use simpler words", "prefer globish", "use API contract not wire contract"), treat it as a lesson and capture it as a skill rule — not just apply it to the current artifact and move on. Vocabulary replacements that apply across projects go in `agent_workflow_guidelines.md` §45.2; recurring workspace terms go in the relevant `dictionary.md` or repo glossary (`docs/maintenance/glossary.md` after migration; legacy `docs/glossary.md`).

### Source-check self-audit
When the user corrects a factual detail or asks what could have been learned by digging deeper, explicitly ask:
- Could an available source system, repository artifact, ticket comment, PR state, log, or local file have revealed this before the user corrected it?
- Did I stop at a summary when primary sources were available?
- Is the lesson only the corrected fact, or is the deeper lesson a missing verification step?

If the answer is yes, capture the deeper verification rule, not only the corrected output. For example, if a weekly report missed replaced PRs, Jira-comment-only work, or ownership split across two Jira stories, the lesson is to check GitHub/Jira source state before drafting ambiguous report sections.

### Generalization pass
Before writing any lesson to its final destination, apply a generalization pass:

1. **Identify the abstract principle** behind the specific incident. Ask: "What is the underlying pattern, independent of this particular technology, file, or module?"
2. **State the general rule first**, then add the specific instance as a concrete example. The rule should remain correct even if the specific tool, framework, or module changes.
3. **Check whether the generalized rule already exists** in canonical docs or instruction files. If it does, add only the missing concrete example — do not create a duplicate rule.
4. **Decide the scope**: after generalizing, assess whether the rule is truly universal or still carries domain-specific assumptions. Apply this test:
   - **Shared canonical (cross-project docs directory)**: Would this rule be correct and useful in *any* project — a Kotlin microservice, a Python data pipeline, a frontend app? If the rule mentions FIFO matching, batch aggregation, CSV parsing, report generation, or similar domain concepts, it is likely too specific for shared docs even after generalization. Resolve the shared docs path from the user's facts document (key: `shared_docs_dir`).
   - **Project-level instruction (repo `CLAUDE.md`/`AGENTS.md`) or project docs (`docs/`)**: The rule is a reusable principle within this project but depends on domain context (financial calculations, data matching, tax reporting). Write it as a general principle with repo-specific examples, and keep it in the project.
   - **Module-level**: The rule is genuinely specific to one module's quirks. Keep it module-scoped but still phrase it as a reusable principle for that module rather than a one-off incident report.
5. **Place accordingly**: write the full text at the chosen scope. If the rule goes to shared canonical docs, reduce the project instruction to a cross-reference. If it stays project-level, write it directly in the project instruction or docs.
6. **Add cross-references for discoverability**: When placing or updating a lesson in project docs (development_lessons.md), also add or update cross-references from instruction files (CLAUDE.md, AGENTS.md) so the lesson is discoverable when working on the relevant topic. A guideline in `development_lessons.md` is only useful if agents know to look for it when processing related code. Check for sibling documents (grep for related keywords) that should reference the same lesson.

Example:
- **Too specific**: "Excel column headers in the crypto gains sheet should say 'Quantity' instead of 'Amount'"
- **Generalized (shared scope)**: "User-facing output labels (column headers, API field names, report section titles) should use self-explanatory terminology, not terse names inherited from upstream source formats." → applies to any project, any output surface → place in `coding_guidelines.md`.
- **Generalized but project-scoped**: "Post-aggregation validation must run after all groups are accumulated, not per-row." → sounds general but assumes batch row processing with mid-accumulation state — only relevant in data-pipeline projects → keep in project instruction as full text, do not elevate to `coding_guidelines.md`.

### Anti-pattern: premature dismissal as "already covered"
Before discarding a candidate lesson because an existing rule seems to cover it,
verify that the **specific failure mode** from this session is addressed — not
just the general topic. Common missed distinctions:
- **Policy vs methodology**: an existing rule says *what* to do (e.g. "don't
  commit formatting-only files") but the lesson is about *how* to do it reliably
  (e.g. "`git diff -w` misses trailing commas"). Both need separate rules.
- **Narrow vs broad**: the specific instance was captured (e.g. "link RFC
  references to Confluence") but the general principle was not (e.g. "protect
  any non-obvious design choice with an inline rationale comment").
- **Symptom vs root cause**: a correction was made (e.g. "restore Dispatchers.IO")
  but the preventive measure was not captured (e.g. "add inline comments to
  prevent future removal of intentional design choices").

When in doubt, write the candidate lesson and run it through Step 3's
qualification gate rather than skipping it at extraction time.

## Step 1.5: Ralphex Execution Log Analysis (when available)

When `.ralphex/progress/` exists in the current project directory:

1. Read the 5 most recent `*.txt` files from `.ralphex/progress/` (by modification time).
2. For each log, extract recurring patterns:
   - **Rate-limit hits** — phase where the limit was hit (task/review/automation), frequency, reset window noted in the log.
   - **Review-phase warnings** — `first review pass did not complete cleanly` (non-fatal; flag if frequent).
   - **Already-done detection** — agent found work pre-completed in a prior commit; note if it caused repeated plan runs.
   - **Environment/tool gaps** — tool not found inside container (Maven, Python, etc.) during a phase that assumed it was available.
   - **Automated review loop failures** — external review parse or exit errors.
3. Classify each extracted pattern using the same Step 1 categories (human guidance, module knowledge, LLM rule, or temporary).
4. Feed classified patterns into the placement workflow (Steps 2–6) alongside lessons from communication.

**Specific placement guidance for common patterns:**
- Frequent rate-limit hits → resolved best-practices path (`docs/maintenance/best-practices.md` after migration; legacy `docs/BEST_PRACTICES.md` only when exploration confirms it still exists) or cross-project shared docs (from facts `shared_docs_dir`): plan size guidelines, recommended run windows.
- Container tool gaps → project `AGENTS.md` / `CLAUDE.md`: document which tools are available in which execution phase.
- Automated review loop failures → note disabling the external review loop in project or user-level docs when applicable.
- Non-fatal review warnings → no action needed unless they occur in every run; if so, note as known pattern in project docs.

## Step 1.6: Internet Research Capture

When research is conducted via web search or other external sources:

**Always capture findings to dedicated documentation:**
- Create or update canonical docs in `docs/` with numbered chapters/clauses
- Use descriptive filenames (e.g., `pdf_generation_guidelines.md`, not `research.md`)
- Include comparison tables, code examples, and source links
- Reference these docs from instruction files (e.g., `see pdf_generation_guidelines.md #1`)

**Format for research docs:**
- Start with Purpose section explaining what the doc covers
- Use numbered chapters (## 1, ## 2) and clauses (### 1.1, ### 1.2)
- Include "Quick Reference" or comparison tables when applicable
- Add Sources section at the end with URLs and dates

**LLM examples vs canonical docs:**
- Canonical docs = technical facts, best practices, comparisons (home per project spec — see `_shared/doc-paths.md`)
- LLM examples / playbooks = reasoning patterns, anti-patterns (resolve `caller_catalog`, `{tmp_dir}`, or project-documented example path — do not assume `docs/examples/`)
- Examples file should reference main doc, not duplicate it

**When to create new research docs:**
- After web search for best practices, technical comparisons, tool selection
- When user asks for research on a topic
- When the same questions recur across sessions
- Before making technical decisions with alternatives

## Step 2: Placement Rules

**First:** Resolve documentation paths per `_shared/doc-paths.md` resolution order (`user_facts_path` keys, repo `AGENTS.md`, on-disk `project_guidelines_rel`, explore `docs/`). Use resolved paths for the rest of this run — do not invent layout.

### Guideline file roles (resolve from facts keys only)

At learn start, read `user_facts_path`. Skills must **not** hardcode machine paths for guideline masters.

| Role | Facts key | Edit when |
|------|-----------|-----------|
| Cross-project JVM/coding | `shared_docs_dir` + filename | Universal or JVM/Spring rule |
| Company master | `company_guidelines_master` | Cross-repo company convention |
| Company repo mirror | `company_guidelines_repo_mirror_rel` | Sync only — after master edit; never canonical |
| Project (current repo) | `project_guidelines_rel` | Repo stack/domain rule |

**Company rule workflow:** edit `company_guidelines_master` first, then sync mirrors in affected company repos. **Multi-tier generalization** (JVM + company + project) updates each canonical home — not the repo mirror alone.

### Temporary artifacts
- Temporary artifacts belong under resolved `{tmp_dir}` (typically `docs/tmp/` when present).
- Do not create session scratch outside `{tmp_dir}` unless project-guidelines documents another gitignored scratch root.
- By end of run, delete temporary artifacts or promote them into canonical docs.
- Resolved `{proposals_dir}` is durable pre-canonical review — not temporary; do not move/delete there unless the user asks.
- Canonical exceptions (never treat as temporary): paths the project marks as durable in `project_guidelines_rel` or `AGENTS.md`.

### BEST_PRACTICES scope
Only place content in the project best-practices doc (resolve path — often `docs/maintenance/best-practices.md` or legacy `docs/BEST_PRACTICES.md`) if it is:
- understandable without system internals
- useful to humans outside incident context
- not LLM-reasoning correction text
- not generic troubleshooting filler
- not module/subsystem specific

### Module/system knowledge
- Internal behavior details belong in the **canonical home** documented by the project (`docs/architecture/<topic>.md`, `docs/maintenance/<topic>.md` after migration — per resolution).
- On **company services** with migration-complete signal ([`doc-hierarchy`](../doc-hierarchy/SKILL.md)): do **not** create new `docs/<module>/` or `docs/domain/` trees; route to architecture topics or `maintenance/`.
- Before migration-complete: legacy `docs/<module>/` may still exist for reads only — do not extend module-split trees; suggest `doc-hierarchy-migrate`.
- Prefer extending existing canonical docs.
- If no suitable canonical doc exists, create one in the layer/folder the project hierarchy specifies; if undocumented, ask the user or suggest updating `project_guidelines_rel`.
- Never place module internals in human best-practices docs.

### LLM examples/playbooks
- Place LLM-only examples in the project-resolved path (`caller_catalog`, `{tmp_dir}`).
- On company services **after** migration-complete: do **not** create new files under `docs/examples/` — merge into `caller_catalog` or use `{tmp_dir}`.
- Before migration-complete: legacy `docs/examples/<topic>.md` only when exploration confirms the repo still uses that layout.
- Split by module/domain so only relevant context is loaded.
- Every LLM example file must start with: `LLM examples - not human documentation`.
- Do not copy LLM examples into `docs/BEST_PRACTICES.md`.
- Do not embed LLM examples inside instruction-rule files.

### LLM instruction rules
- LLM reasoning-guard lessons belong in instruction rule files (`AGENTS.md` and command specs).
- Keep rules enforceable and concise.
- Do not place LLM reasoning guidance in `docs/BEST_PRACTICES.md`.
- Instruction files (`AGENTS.md`, `CLAUDE.md`) must remain language-agnostic. Language-specific patterns (Kotlin, Python, etc.) belong in the corresponding language guidelines file under the shared docs directory (from facts `shared_docs_dir`, e.g. `kotlin_guidelines.md`, `python_guidelines.md`), not in instruction files. When a lesson is language-specific, place it in the language file and add or update the reference in the instruction file's **Guidelines Loading** section.

### Exact class-name hygiene
- Do not hard-code exact test or implementation class names in canonical docs under `docs/` when a role/category description is sufficient.
- Do not hard-code exact class names in instruction files (`AGENTS.md`, `CLAUDE.md`) or command specs when the guidance is normative rather than operational.
- Prefer responsibility-based wording in those locations (for example "dedicated JSON naming/runtime guardrail test", "transport-slice test", "broader transport integration test").
- Exact class names are allowed only when they are operationally useful or intentionally canonical:
  - runnable single-test commands
  - migration checklists where file-level parity matters
  - places where the repo intentionally designates one canonical file/class anchor
- If a lesson is "this doc or instruction should not pin exact class names", place that as an enforceable instruction/command rule, not in `docs/maintenance/company-guidelines.md` (or legacy `docs/company-guidelines.md`) or other cross-repository baseline docs.

## Step 3: LLM Rule Qualification Gate
Before adding any rule, enforce all checks:
1. Rule vs fact: must prescribe/forbid behavior.
2. Generalization: must apply to multiple future cases.
3. Preventive value: removing it should clearly increase risk.
4. Actionability: must say what to do or avoid.

If a candidate fails:
- rewrite once into a concise rule
- if still weak, discard it

## Step 4: Documentation Consolidation
Review and normalize under resolved doc roots (`docs/`, `{tmp_dir}`, and any example/caller-catalog path from resolution):

Required outcomes:
- one canonical document per topic
- subtopics as sections inside canonical docs (not fragmented duplicates)
- overview docs reference canonical docs instead of restating content
- no canonical docs referencing `docs/tmp/`
- workflow-spec docs contain workflow guidance only; do not append raw command outputs unless they improve the workflow itself
- canonical docs and normative instructions avoid brittle exact class-name references unless they are intentionally canonical or operationally necessary
- when changing the learn workflow itself, edit `~/.agents/skills/learn/SKILL.md` and commit in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`)

Topic-sibling update rule:
- When placing new content in any document, **scan all other docs in the repo** (`docs/`, instruction files, READMEs) for documents that already cover the same topic or a parent/sibling concept.
- If a sibling document exists (e.g., `docs/shell-functions.md` covers agent selection and you are adding a new agent-selection feature to `AGENTS.md`), update **both** documents in the same pass.
- Do not rely on cross-reference checks in later steps to catch this — the content must be placed in all relevant documents during the initial placement pass.
- Practical technique: after identifying the placement target, run `grep -rl "<topic keyword>"` across the repo to find sibling documents before writing.

Intra-document requirements:
- every non-trivial document starts with `Core Concepts`, `Key Concepts`, or `Terminology`
- define each core concept once
- later sections reference earlier definitions instead of re-defining

## Step 4.5: Add Cross-References for Lesson Discoverability

After placing a lesson in the project-resolved development-lessons path (for example `docs/maintenance/development-lessons.md` or a topic file under `docs/architecture/`), immediately add a cross-reference to the relevant instruction file (`CLAUDE.md` or `AGENTS.md`) so the lesson is discoverable when agents work on related code.

**Process:**
1. Identify which instruction section the lesson relates to.
2. Find the best location within that section — group with related rules for context.
3. Add a concise cross-reference to the resolved lesson doc path.
4. If the lesson introduces a new domain concept, update the matching **architecture** topic (for example `domain-model.md`) or `maintenance/<topic>.md` — not `docs/domain/` or `docs/<module>/` on migration-complete company services.

**Why this matters:** The instruction files are always loaded during tasks, but `development_lessons.md`
is loaded only when explicitly mentioned. Without cross-references, a lesson may exist in the corpus but never be
consulted when it's most relevant. Cross-references bridge this gap.

**Example:** Lesson #67 (Futures/Derivatives Liquidation Mechanics) should be referenced in the crypto capital gains
constraints section because that's where agents work with derivatives reporting. Lesson #68 (Decision Point Flags)
should be referenced near decision points and configuration rules.

**Topic-sibling check:** When adding a cross-reference, scan nearby rules for the same topic domain.
If multiple rules reference the same lesson, that's good — it reinforces the lesson's importance.
If you find a pattern where many lessons in one section all reference different docs, consider whether the lesson
could be consolidated or whether the instruction section could be reorganized for better flow.

## Step 5: Module Layout and Skill Workflow Lessons
- Module doc layout follows project resolution (`_shared/doc-paths.md`): legacy `docs/<module>/`, flat `history/feature-notes/`, or architecture topics — do not impose a layout the project has not adopted.
- RFC / task tracker filenames follow project-guidelines or existing repo convention.
- If move/rename is required, propose minimal change set and ask for consent before applying. On company services with legacy layout, suggest `doc-hierarchy-migrate` instead of ad-hoc moves.

For lessons about a skill's workflow/style or output/content requirements:
- update the owning skill's `SKILL.md`
- add an example/playbook only in the project-resolved example path when one is needed to demonstrate the rule
- do not treat rewriting generated artifacts as the primary fix
- do **not** place these in resolved `project_guidelines_rel` / company mirror paths (`docs/maintenance/project-guidelines.md`, `docs/maintenance/company-guidelines.md` after migration), or instruction files — those are for project engineering conventions, not skill behavior
- edit skills at `~/.agents/skills/` (runtime source; `~/.claude/skills` resolves to the same tree when symlinked)

**Skill-scope detection:** When a lesson explicitly mentions a skill by name or describes a workflow that clearly belongs to a skill (e.g., "plans must investigate...", "execute-plan should...", "review feedback requires..."), detect this as a skill-scope lesson. Apply dual placement:
1. Place the generalized lesson in the project's `development_lessons.md` with cross-references
2. Also update the skill's `SKILL.md` under `agents/skills/<skill>/` in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`, or deduce via `readlink -f ~/.agents/skills`)

**Generalization before skill placement:** Before writing to a skill's `SKILL.md`, apply the generalization pass (Step 1.2) rigorously. Examples in skill files must be generic enough to apply across projects. Replace:
- Project-specific terms (e.g., "Koinly Other Gains Report", "FIFO matching") → generic equivalents ("Source Report A", "data matching algorithm")
- Concrete dates/IDs → placeholders ("2025-01-13" → "<specific date>")
- Domain-specific assets → generic concepts ("BTC/USDT" → "asset pairs")

**Commit workflow:** Commit skill changes in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`), separately from project changes with a clear commit message.

Examples:
- RFC section-content requirements belong in `~/.agents/skills/rfc-design/SKILL.md`
- done-workflow rules belong in `~/.agents/skills/done/SKILL.md`
- Investigation quality requirements belong in `~/.agents/skills/plans/SKILL.md` (not just in project docs)

### Skill Output Improvement (corrected/retracted/downgraded outputs)

When a skill's output was **corrected, retracted, downgraded, or significantly rewritten** after user feedback, extract lessons using these questions:

1. **What was the incorrect assumption?** (e.g. "assumed no downstream dedup guard", "assumed cache was still alive at call time", "assumed the user wanted verbose output")
2. **What verification step would have produced the correct output initially?** (e.g. "grep for dedup/idempotent in the downstream domain", "check TTL calculation and compare to method call timing", "re-read the user's original phrasing")
3. **Can the verification be encoded as a mandatory step in the skill?** If yes, it becomes a rule in that skill's `SKILL.md` or sub-agent prompts.
4. **Where in the skill does it go?** Map to the skill's internal structure:
   - Pre-execution checks / input validation steps
   - Core execution logic / sub-agent prompts
   - Post-execution assessment / quality gates
   - Output formatting / tone rules

**Trigger**: any of these patterns in the session:
- User corrects or overrides a skill's output
- Output severity/priority was changed (e.g. High to Low)
- Output was deleted or fully rewritten
- User challenges the feasibility or relevance of the output
- Suggested action was rejected as too costly, wrong-scoped, or unnecessary
- User says "but we already have X" or "that's not how it works"

**Placement guidance by skill type:**

| Skill | Where to place verification rules |
|-------|----------------------------------|
| `doing-code-review` | Sub-agent prompts (quality.md, concurrency.md, etc.) for domain checks; SKILL.md Step 4 for cross-cutting assessment rules |
| `rfc-design` | SKILL.md input collection gates or section generation rules |
| `plans` | SKILL.md scope/estimation rules |
| `learn` | This file's extraction or placement logic |
| `done` | SKILL.md commit/cleanup rules |
| Other skills | The skill's own SKILL.md, in the step closest to where the error originated |

**Self-application**: this rule applies to the learn skill itself. If a lesson extracted by learn is later found to be mis-placed, mis-scoped, or incorrectly generalized, that is a learn-skill output correction and should be fed back into this section's placement/generalization logic.

## Step 6: Instruction File Updates
Update instruction rules in three sections only:
1. Reusable engineering rules (Java/Kotlin ecosystem)
2. Repository style and conventions
3. Repository constraints

Placement test:
- reusable anywhere -> section 1
- repo consistency/look-alike -> section 2
- hard limit/prohibition -> section 3
- when unsure -> section 1

Instruction consolidation pass (required):
- Scan updated instruction files for overlapping bullets that prescribe the same behavior.
- Group overlaps into one canonical rule per intent; keep wording explicit and enforceable.
- Remove weaker/ambiguous duplicates instead of keeping multiple variants.
- If two rules are both needed, make scopes non-overlapping and clearly distinguish baseline rule vs exception rule.

Compaction pass (required):
- When an instruction rule restates or elaborates a convention already fully documented in company or project guidelines, replace the rule body with a compact reference (for example `see company-guidelines.md #N` or `see project-guidelines.md #N`) and keep only the incremental constraint or local exception in the instruction file. Edit the **canonical** file for the tier (`company_guidelines_master` or `project_guidelines_rel` per facts keys) — not a repo company mirror alone.
- When a rule in a project-level instruction file (`repo AGENTS.md`) duplicates content already present in user-level instructions (`~/.codex/AGENTS.md`), remove the project-level duplicate or reduce it to a one-line cross-reference. User-level rules are always loaded; restating them per-project adds no enforcement value and creates drift risk.
- When adding a NEW project-specific technical or architectural convention (for example persistence configuration, test infrastructure pattern, schema layout, tool-specific settings), place the detailed content as a numbered rule in the current repo's project guidelines (`project_guidelines_rel` facts key) first; add only a one-line `see project-guidelines.md #N` reference in instruction files. Full-text rules in instruction files are reserved for cross-cutting reasoning guards that have no suitable canonical doc home.
- When adding a NEW cross-repository convention or baseline standard, choose the canonical home by scope. Read `user_facts_path` and resolve:
  - **Universal coding principle** (applies in any language, any company): `<shared_docs_dir>/coding_guidelines.md`
  - **Ecosystem-specific** (shared across JVM languages, Spring Boot patterns, Reactor/Mono): `<shared_docs_dir>/jvm_guidelines.md` — not in `coding_guidelines.md` because ecosystem rules are irrelevant to Python/Go/Rust projects.
  - **Language/framework-specific** (Kotlin stdlib idiom, MockK, Java Optional): `<shared_docs_dir>/kotlin_guidelines.md` / `java_guidelines.md` etc.
  - **Company-specific convention** (naming, error code format, logging policy shared across company repos but not universal): **`company_guidelines_master`** (facts key) — not `company_guidelines_repo_mirror_rel`; sync repo mirrors after editing the master.
  - Do NOT default to company guidelines for general programming principles — that file is for company-specific conventions only.
  - Add only a one-line `see company-guidelines.md #N` reference in instruction files (repo-relative label for humans; canonical edit target remains the facts key).
- When multiple instruction bullets share the same governing principle, merge into one generalized rule with examples rather than keeping N specific variants.
- When a rule can be stated more concisely without losing its enforceable meaning, shorten it; prefer one-sentence rules over multi-sentence explanations.
- When an instruction rule is only needed for specific infrequent task types (for example Jira story creation, PR description writing, PR chunk splitting), move it to a dedicated skill such as `jira-pr-workflow` rather than keeping it in the always-loaded instruction files; add or update the trigger description in the skill's front matter.
- Do not remove a rule solely to save space — only when the canonical doc or a more general rule already covers it.

## Step 7: API Contract Naming Hygiene
When lessons involve external API naming or endpoint shape:
- Prefer resource-oriented OpenAPI paths and avoid RPC verb segments (`/set`, `/check`, `/resolve`, `/merge`, `/unsuppress`).
- Use kebab-case for multi-word path segments and consistent module-aligned roots.
- Record old-to-new endpoint mapping and rationale in canonical docs (`docs/project-decisions.md`) as documentation-only deprecation context.
- If API path or `operationId` renames were already made in the implementation workflow, verify docs remain synchronized with those changes; do not perform implementation refactors as part of this learn workflow.

## Completion Checklist
Before finishing, verify:
- lesson placement is complete and unambiguous
- no temporary artifacts remain outside policy
- no `docs/` references to `docs/tmp/`
- no duplicate concept definitions inside changed documents
- instruction-rule updates are grouped/deduplicated with no overlapping or contradictory bullets for the same intent
- no instruction rule restates a convention already documented in full in company or project guidelines; full text lives in the canonical file for that tier (`company_guidelines_master`, `project_guidelines_rel`, or `shared_docs_dir` file per facts keys); instruction files hold only the incremental constraint or a reference
- no project-level instruction rule duplicates a rule already present in user-level instructions (`~/.codex/AGENTS.md`); project-level copies are reduced to a cross-reference or removed
- every new full-text rule added to instruction files is either (a) a cross-cutting reasoning guard with no suitable canonical doc home, or (b) already has its detailed content in the tier-appropriate canonical guideline file with only a `see … #N` reference in the instruction file
- instruction files (`CLAUDE.md`, `AGENTS.md`) do not exceed 30,720 bytes each; if they do, apply the compaction pass again targeting the largest remaining rules for cross-ref replacement or occasional-skill extraction
- exact class names appear only where operationally useful or intentionally canonical; normative instructions and canonical docs use role-based wording instead
- if the learn workflow changed, `~/.agents/skills/learn/SKILL.md` is updated and committed in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`)
- RFC-workflow lessons updated in skill/example files where applicable
- changed API docs and OpenAPI artifacts remain synchronized
- the learn counter file (`/tmp/learn-counter-${PPID}-<dir_hash>`) has been deleted so the nudge timer restarts
