## Step 2: Placement Rules

**First:** Read path keys from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Use resolved paths for the rest of this run; do not invent layout.

### Fork-4 project-corpus existence check (mechanical gate  -  required before ANY corpus write)

If the chosen scope from Step 1.2 item 4 is **fork (4) project-specific**, verify the incident repo's project corpus exists BEFORE any corpus write. This is the enforceable backstop that makes the Step 1.2/1.7 judgment checks mechanically binding: a filesystem/facts lookup, not LLM judgment.

1. Resolve the project corpus path: `$REPO/docs/maintenance/development_lessons.md`, where `$REPO` is the **incident repo** (per Step 1.2 item 3b) and the relative path comes from the repo's `project_guidelines_rel` / `repo_facts_rel` in `.ai-playbook/facts.md`. Use the incident repo, not necessarily the cwd repo.
2. Check existence (filesystem): if that file does **NOT** exist, the placement **FAILS LOUD**. Do not silently fall back to the UL corpus. Choose one:
   - **(a)** bootstrap the project corpus in the incident repo (`docs/maintenance/development_lessons.md` with the convention header, and add `project_guidelines_rel` to that repo's facts if missing), then write the lesson there;
   - **(b)** `cd` to the incident repo and re-run `learn` so Step 1.2 item 3b's incident-repo == cwd-repo check passes and the lesson lands in that repo's project corpus;
   - **(c)** escalate to the user and defer the capture.
3. **Playbook-repo special case (the contamination vector):** the playbook repo (`skills_repo_path` / `instructions_repo`) is the skills/instructions home, not a project, and carries no `project_guidelines_rel`; since 2026-10 it also carries a project lessons corpus of its own (`docs/maintenance/development_lessons.md`) for playbook-machinery incidents (the loop, its landing machinery, the execute-plan driver, skills runtime behavior). A fork-4 candidate while cwd is the playbook routes there when the incident is the playbook's own machinery; it still fails loud to the incident repo's project corpus when the incident belongs to another project. Never default a project-specific incident into the UL corpus because the UL file is the corpus at hand - that defaulting is exactly the bug this gate exists to prevent.

This check is mechanical on purpose: even if the Step 1.2 item 3b judgment pre-check and the Step 1.7 item 6 residual-domain judgment test are both missed, this filesystem lookup cannot be rationalized away  -  a missing `development_lessons.md` is a missing file, full stop.

### Guideline file roles (resolve from facts keys only)

At learn start, read `user_facts_path`. Skills must **not** hardcode machine paths for guideline masters.

| Role | Facts key | Edit when |
|------|-----------|-----------|
| Cross-project JVM/coding | `shared_docs_dir` + filename | Universal or JVM/Spring rule |
| Company master | `company_guidelines_master` | Cross-repo company convention |
| Company repo mirror | `company_guidelines_repo_mirror_rel` | Sync only: after master edit; never canonical |
| Project (current repo) | `project_guidelines_rel` | Repo stack/domain rule |

**Company rule workflow:** edit `company_guidelines_master` first, then sync mirrors in affected company repos. **Multi-tier generalization** (JVM + company + project) updates each canonical home, not the repo mirror alone.

### Facts vs skill configuration (required before adding keys or constants)

Use this split when capturing lessons or extending agent automation:

| Belongs in **facts** (`user_facts_path`, ownership facts, repo `repo_facts_rel`) | Belongs in **skill** (`SKILL.md` for the owning workflow) |
|-----------------------------------------------------------------------------------|-------------------------------------------------------------|
| Machine paths and workspace roots | Workflow steps, gates, and completion criteria |
| GitHub accounts, domains, employer-specific identifiers | Numeric policy constants (byte budgets, loop limits, timeouts) |
| Repo path keys (`plans_dir`, `tmp_dir`, `project_guidelines_rel`) | Placement ladders and qualification gates for that skill |
| Local-only script locations that vary by machine | Default script **behavior** and mode names (`check`, `gate`) |
| Hygiene deny-pattern files (local regex lists) | When to invoke a script and how to interpret exit codes |

**Do not** add facts keys for portable policy the skill already owns (for example instruction byte budgets; define the number in `learn` / `done` Step text, not in `user_facts_path`). **Do not** duplicate skill workflow rules in facts.

When a user corrects "that should live in the skill, not facts", treat it as a **skill-scope** lesson: update the owning skill and `agent_workflow_guidelines.md` §50 if the split was unclear; do not re-home the constant into facts under another key name.

### Temporary artifacts
- Temporary artifacts belong under resolved `{tmp_dir}` (typically `docs/tmp/` when present).
- Do not create session scratch outside `{tmp_dir}` unless project-guidelines documents another gitignored scratch root.
- By end of run, delete temporary artifacts or promote them into canonical docs.
- Resolved `{proposals_dir}` is durable pre-canonical review, not temporary; do not move/delete there unless the user asks.
- Canonical exceptions (never treat as temporary): paths the project marks as durable in `project_guidelines_rel` or `AGENTS.md`.

### BEST_PRACTICES scope
Only place content in the project best-practices doc (resolve path, often `docs/maintenance/best-practices.md` or legacy `docs/BEST_PRACTICES.md`) if it is:
- understandable without system internals
- useful to humans outside incident context
- not LLM-reasoning correction text
- not generic troubleshooting filler
- not module/subsystem specific

### Module/system knowledge
- Internal behavior details belong in the **canonical home** documented by the project (`docs/architecture/<topic>.md`, `docs/maintenance/<topic>.md` after migration, per resolution).
- On **company services** with migration-complete signal ([`doc-hierarchy`](../doc-hierarchy/SKILL.md)): do **not** create new `docs/<module>/` or `docs/domain/` trees; route to architecture topics or `maintenance/`.
- Before migration-complete: legacy `docs/<module>/` may still exist for reads only; do not extend module-split trees; suggest `doc-hierarchy-migrate`.
- Prefer extending existing canonical docs.
- If no suitable canonical doc exists, create one in the layer/folder the project hierarchy specifies; if undocumented, ask the user or suggest updating `project_guidelines_rel`.
- Never place module internals in human best-practices docs.

### LLM examples/playbooks
- Place LLM-only examples in the project-resolved path (`caller_catalog`, `{tmp_dir}`).
- On company services **after** migration-complete: do **not** create new files under `docs/examples/`; merge into `caller_catalog` or use `{tmp_dir}`.
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
1. Rule vs fact: must prescribe/forbid behavior, not store a path, account, or environment value.
2. Facts vs skill: portable thresholds and workflow policy belong in the owning skill, not a new facts key.
3. Generalization: must apply to multiple future cases.
4. Preventive value: removing it should clearly increase risk.
5. Actionability: must say what to do or avoid.

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
- when changing the learn workflow itself, edit `~/.agents/skills/learn/SKILL.md` and commit it in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`) by explicit path, never a directory-wide add

Topic-sibling update rule:
- When placing new content in any document, **scan all other docs in the repo** (`docs/`, instruction files, READMEs) for documents that already cover the same topic or a parent/sibling concept.
- If a sibling document exists (e.g., `docs/shell-functions.md` covers agent selection and you are adding a new agent-selection feature to `AGENTS.md`), update **both** documents in the same pass.
- Do not rely on cross-reference checks in later steps to catch this; the content must be placed in all relevant documents during the initial placement pass: cross-reference wiring for session-created guidance happens at placement time, within the owning boundary's capture run (learn runs at every intermediate boundary and at the final closeout).
- Practical technique: after identifying the placement target, run `grep -rl "<topic keyword>"` across the repo to find sibling documents before writing.

Intra-document requirements:
- every non-trivial document starts with `Core Concepts`, `Key Concepts`, or `Terminology`
- define each core concept once
- later sections reference earlier definitions instead of re-defining

## Step 4.5: Add Cross-References for Lesson Discoverability

After placing a lesson in the project-resolved development-lessons path (for example `docs/maintenance/development-lessons.md` or a topic file under `docs/architecture/`), immediately add a cross-reference to the relevant instruction file (`CLAUDE.md` or `AGENTS.md`) so the lesson is discoverable when agents work on related code.

**Process:**
1. Identify which instruction section the lesson relates to.
2. Find the best location within that section, grouped with related rules for context.
3. Add a concise cross-reference to the resolved lesson doc path.
4. If the lesson introduces a new domain concept, update the matching **architecture** topic (for example `domain-model.md`) or `maintenance/<topic>.md`, not `docs/domain/` or `docs/<module>/` on migration-complete company services.

**Why this matters:** The instruction files are always loaded during tasks, but `development_lessons.md`
is loaded only when explicitly mentioned. Without cross-references, a lesson may exist in the corpus but never be
consulted when it's most relevant. Cross-references bridge this gap.

**Example:** Lesson #67 (Futures/Derivatives Liquidation Mechanics) should be referenced in the crypto capital gains
constraints section because that's where agents work with derivatives reporting. Lesson #68 (Decision Point Flags)
should be referenced near decision points and configuration rules.

**Topic-sibling check:** When adding a cross-reference, scan nearby rules for the same topic domain.
If multiple rules reference the same lesson, that's good; it reinforces the lesson's importance.
If you find a pattern where many lessons in one section all reference different docs, consider whether the lesson
could be consolidated or whether the instruction section could be reorganized for better flow.

## Step 5: Module Layout and Skill Workflow Lessons
- Module doc layout follows project resolution (`.ai-playbook/facts.md` path keys and `doc-hierarchy`): legacy `docs/<module>/`, flat `history/feature-notes/`, or architecture topics; do not impose a layout the project has not adopted.
- RFC / task tracker filenames follow project-guidelines or existing repo convention.
- If move/rename is required, propose minimal change set and ask for consent before applying. On company services with legacy layout, suggest `doc-hierarchy-migrate` instead of ad-hoc moves.

For lessons about a skill's workflow/style or output/content requirements:
- update the owning skill's `SKILL.md`
- add an example/playbook only in the project-resolved example path when one is needed to demonstrate the rule
- do not treat rewriting generated artifacts as the primary fix
- do **not** place these in resolved `project_guidelines_rel` / company mirror paths (`docs/maintenance/project-guidelines.md`, `docs/maintenance/company-guidelines.md` after migration), or instruction files; those are for project engineering conventions, not skill behavior
- edit skills at `~/.agents/skills/` (runtime source; `~/.claude/skills` resolves to the same tree when symlinked)

**Skill-scope detection:** When a lesson explicitly mentions a skill by name or describes a workflow that clearly belongs to a skill (e.g., "plans must investigate...", "execute-plan should...", "review feedback requires..."), detect this as a skill-scope lesson. Apply dual placement:
1. Place the generalized lesson in the project's `development_lessons.md` with cross-references
2. Also update the skill's `SKILL.md` under `agents/skills/<skill>/` in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`, or deduce via `readlink -f ~/.agents/skills`)

**Generalization before skill placement:** Before writing to a skill's `SKILL.md`, apply the generalization pass (Step 1.2) rigorously. Examples in skill files must be generic enough to apply across projects. Replace:
- Project-specific terms (e.g., "Koinly Other Gains Report", "FIFO matching") → generic equivalents ("Source Report A", "data matching algorithm")
- Concrete dates/IDs → placeholders ("2025-01-13" → "<specific date>")
- Domain-specific assets → generic concepts ("BTC/USDT" → "asset pairs")

**Commit workflow:** Commit skill changes in the skills repository (`skills_repo_path` in `~/.ai-playbook/facts.md`), separately from project changes with a clear commit message; stage the changed files by explicit path, never a directory-wide add.

Examples:
- RFC section-content requirements belong in `rfc-design/SKILL.md` and `rfc-design/references/rfc-sections.md`
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
| `rfc-design` | SKILL.md workflow gates; `references/rfc-sections.md` section template and editing checklist |
| `plans` | SKILL.md scope/estimation rules |
| `learn` | This file's extraction or placement logic |
| `done` | SKILL.md commit/cleanup rules |
| Other skills | The skill's own SKILL.md, in the step closest to where the error originated |

**Self-application**: this rule applies to the learn skill itself. If a lesson extracted by learn is later found to be mis-placed, mis-scoped, or incorrectly generalized, that is a learn-skill output correction and should be fed back into this section's placement/generalization logic.
