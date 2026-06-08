# User-level instructions (AGENTS.md)

Cross-project engineering rules. **Source of truth:** `docs/AGENTS.md` in this repository (version-controlled). **Codex entrypoint:** `~/.codex/AGENTS.md` symlinked to that file. **Clone path** on your machine: `instructions_repo` in `~/.ai-playbook/facts.md` (see `docs/facts.md.example` for key names).

**Companion paths (thin or symlink — not separate full copies):**
- `ln -sf <instructions-repo>/docs/AGENTS.md ~/.codex/AGENTS.md`
- `~/.claude/CLAUDE.md` — thin file with `@<instructions-repo>/docs/AGENTS.md` (never symlink while editing; see hazard below).
- `ln -sf ~/.codex/AGENTS.md ~/.copilot/copilot-instructions.md` (Copilot does not expand `@` imports).
- Do **not** maintain `~/.claude/AGENTS.md` (retired).

**Hazard:** if `~/.claude/CLAUDE.md` symlinks to `~/.codex/AGENTS.md`, writing `CLAUDE.md` overwrites the canonical body. Keep `CLAUDE.md` as a regular thin file.

**Verify wiring:** agents load this file via `~/.codex/AGENTS.md` (symlink) or `~/.claude/CLAUDE.md` (`@` import), not by opening `<instructions_repo>/docs/AGENTS.md` in the repo during a normal session. After migration or machine setup, confirm the entrypoints point at the same canonical file:

```bash
# Set INSTRUCTIONS_REPO from ~/.ai-playbook/facts.md (key: instructions_repo)
CANONICAL="${INSTRUCTIONS_REPO:?}/docs/AGENTS.md"
test -L ~/.codex/AGENTS.md && [ "$(readlink -f ~/.codex/AGENTS.md)" = "$(readlink -f "$CANONICAL")" ]
test -L ~/.copilot/copilot-instructions.md && [ "$(readlink ~/.copilot/copilot-instructions.md)" = "$HOME/.codex/AGENTS.md" ]
test ! -L ~/.claude/CLAUDE.md && grep -q '@.*docs/AGENTS.md' ~/.claude/CLAUDE.md
diff -q ~/.codex/AGENTS.md "$CANONICAL"
```

If `~/.codex/AGENTS.md` is a regular file, back it up, then `ln -sf <instructions-repo>/docs/AGENTS.md ~/.codex/AGENTS.md`. Never symlink `~/.claude/CLAUDE.md` to `~/.codex/AGENTS.md`. Full runtime folder mapping (skills, `shared_docs_dir`, mirrors): `agent-runtime-layout.md` under `shared_docs_dir` in `~/.ai-playbook/facts.md`.

## Code Comments

### Inline comment policy in production and test code
- In production method and constructor bodies, avoid inline comments; document intent at the class or (preferably) interface level via Javadoc.
- A single-line inline comment is acceptable only when the behaviour is genuinely non-obvious from code structure, variable names, and method names alone (for example: idempotency safety-net, concurrent-race reconciliation, ordered-collection type choice such as `LinkedHashMap` for insertion order).
- For complex explanations that need more than one line, add a single-line reference to the relevant canonical doc (for example `// see docs/project-decisions.md`) rather than writing a multi-line inline explanation.
- In test method bodies, AAA scaffold labels (`// Arrange:`, `// Act:`, `// Assert:`) and step-by-step narrative comments are unnecessary; test method names, variable names, and assertion chains should tell the story.

## Instruction and facts hierarchy

**`AGENTS.md`** holds public, reusable engineering rules. **`facts.md`** holds local identity, paths, accounts, inventories, and other environment-specific values — never commit sensitive facts to public repos.

- In public user-level instructions and vendored skills, use neutral scope labels (personal projects, company work) and facts-document keys for machine paths; keep employer brand names and local directory literals in `facts.md` only. Copyright lines in `LICENSE.txt` are exempt.

| Tier | Rules (`AGENTS.md`) | Facts (`facts.md`) |
|------|---------------------|-------------------|
| User + workspace | `docs/AGENTS.md` in this repo (this file) | `~/.ai-playbook/facts.md` (local only: identity, roots, `shared_docs_dir`, skill keys) |
| Ownership | repo `AGENTS.md` | personal-projects or company ownership `facts.md` when scope matches (paths in `~/.ai-playbook/facts.md`) |
| Repo | repo `AGENTS.md` | `docs/facts.md` in the current repo (copy from `docs/facts.md.example` when needed) |

At task start, load applicable `facts.md` files for the current repo scope before relying on path or account assumptions.

1. **User-level rules** — this file; tool entrypoints symlink or `@`-reference it.
2. **Project-level rules** — repo `AGENTS.md` only; `CLAUDE.md` symlink or thin `@AGENTS.md`.
3. **Repo docs** — `docs/project-guidelines.md`, `docs/project-decisions.md`, etc.

### Placement rules
- When a rule is requested "for the project and for the user": place the full text as a numbered rule in `docs/project-guidelines.md`, add a one-line `see docs/project-guidelines.md #N` reference in project `AGENTS.md`, and copy the full rule text to user-level instructions in `ai-playbook`.
- LLM agent workflow rules belong in user-level instructions or skill files — never in project `AGENTS.md`.

### Instruction files: `AGENTS.md` source + entrypoints

| Tier | Canonical (edit here) | Entrypoints |
|------|----------------------|-------------|
| User | `docs/AGENTS.md` in this repo | `~/.codex/AGENTS.md` (symlink); `~/.claude/CLAUDE.md` (`@`); `~/.copilot/copilot-instructions.md` (symlink via codex); `~/.cursor/rules/global-user-instructions.mdc` (`@`) |
| Repo | `<repo>/AGENTS.md` | `<repo>/CLAUDE.md` (symlink or thin `@AGENTS.md`) |

**Repo setup:** `ln -sf AGENTS.md CLAUDE.md` unless Cursor duplicates both paths — then use thin `CLAUDE.md` with `@AGENTS.md` only.

**Never** symlink `.github/copilot-instructions.md` to repo `AGENTS.md` when both exist (Copilot merges both → duplicate).

### Cursor IDE (Agent)

- **Global:** `~/.cursor/rules/global-user-instructions.mdc` `@`-references this file via `instructions_repo` (or `~/.codex/AGENTS.md` symlink).
- **Per-repo:** repo `AGENTS.md` only for project deltas; do not duplicate user rules.

## Path References in Instruction and Documentation Files

Always use `~/` (home-relative) paths, never absolute `/Users/<name>/` paths, in any instruction file (`AGENTS.md`, `CLAUDE.md`), skill file, or documentation file. Absolute paths are brittle — they break on any machine with a different username and leak personal directory structure into shared artifacts.

## Skill Maintenance

- When renaming a skill, update: the `name:` front matter, the `# Title` heading, and all internal self-references (e.g. `Announce at start:` lines that mention the old skill name).
- When adapting a generic skill from `~/.codex/skills/` for shared multi-agent use, copy it into `~/.agents/skills/` and adapt the copy there; leave the original Codex skill untouched because it may depend on Codex-specific tooling, MCP wiring, or runtime assumptions.
- Generic skills must remain language-agnostic and project-agnostic. Code examples should use generic descriptions (e.g., "exact pattern matching with start/end anchors") not language-specific syntax (e.g., `re.match("^PATTERN$")` for Python, `Pattern.matches()` for Java). References to project-specific docs (e.g., `docs/domain/plan_quality_guidelines.md`) should be optional/cross-references only, not assumed to exist.
- Language-specific skill content: When a skill quality gate or checklist includes language-specific patterns (testing traps, idioms, framework-specific stubs), replace them with a cross-reference to the relevant language guidelines file (`kotlin_guidelines.md`, `python_guidelines.md`, etc.) rather than inlining. Inlining causes drift as guidelines evolve independently.
- "Language-agnostic" means replacing build-tool commands (e.g. `mvn`, `pytest`) and file extensions (`.kt`, `.py`) with generic placeholders (`<test-command>`, `.ext`). It does NOT mean removing project-doc references (e.g. `docs/metrics.md`, `docs/project-guidelines.md`) or domain terminology (e.g. `BO`) — those are concrete contextual examples that provide useful guidance and should be kept.

## Implementation Plans

- Plans go in `docs/plans/`; see the `plans` skill for the mandatory format and lifecycle rules.
- For company work projects, design RFCs go in `docs/rfcs/`.
- Do not create plans in session state, `docs/tmp/`, or any other location.
- Do not create plans in tool-default locations (`.claude/plans/`, `.opencode/plans/`, `.codex/`, `.cursor/`). Always write to `docs/plans/` regardless of what the tool suggests.
- Plans must follow TDD task ordering: RED (failing tests) before GREEN (implementation), refactor last.
- When a plan modifies domain types in a large file (>1k lines), include a task for evaluating extraction to a dedicated domain module.

## Temporary Artifacts

- Temporary artifacts (summaries, analyses, investigations, UAT records, worklogs) belong under `docs/tmp/` and must be promoted or deleted within the same feature cycle.
- Before creating a new temporary artifact, check whether an existing canonical doc under `docs/` can be enriched instead.
- Do not reference `docs/tmp/` from other `docs/` files or code comments.

## Sealed Class Sentinel Pattern

- When a sealed result type has a data-carrying success variant (e.g. `Claimed(handle)`), never reuse that variant with a dummy/empty payload for bypass or fail-open paths. Use a dedicated sentinel variant (e.g. `data object Bypassed`) so downstream code that only runs on the success branch cannot accidentally operate on invalid state.


## Background Task Duplicate Prevention and Async Retry

**Duplicate prevention — layered approach (company-guidelines #24):**
When a background task can be picked up by multiple pods simultaneously:
- **Distributed lock (first line)**: non-blocking `tryLock` (wait = 0) on the task/item key prevents concurrent re-entry within the same window. Lease must cover expected max processing time.
- **DB status transition (backstop)**: an optimistic `UPDATE … WHERE status = EXPECTED_STATUS` with row-count check ensures only one pod commits state even if the lock is bypassed.
- **Dedup guard (optional third layer)**: a Redis claim/confirm state machine protects against re-entry when the lock lease expires mid-processing. Add it only when processing time can legitimately exceed the lock lease; when added alongside an existing lock, align `claimTtl` with the lock lease — a longer `claimTtl` turns a pod crash into a longer retry blackout than the lock alone would have caused.

**Async retry via DB status (company-guidelines #25):**
Use a persistent DB status field as the retry anchor. A query of `status = PENDING AND scheduled_time <= now()` implicitly retries without extra infrastructure — the item stays retryable until its status is updated to a terminal value. `confirmedTtl` for a dedup guard should be the minimum realistic window between a confirmed send and the next retry attempt, not an arbitrary large value; once DB status is terminal the cron will no longer select the item regardless of Redis state.

## Concurrency Audit Before New Controls

Before introducing any new concurrency control (distributed lock, Redis flag, DB status field, dedup guard, or similar), audit what is already in place for the same code path: existing locks (key, lease, wait duration), DB status transitions, and any prior dedup layer. Verify whether the new mechanism overlaps, extends, or genuinely fills a gap. Document the reasoning in the plan. Overlapping controls are not automatically harmless — a longer TTL on a new layer can silently extend retry blackout windows beyond what the existing layer would have caused (see company-guidelines #39).

## Reuse Existing Properties When There Is a Dependency

When a new config property has a functional dependency on an existing property (e.g. a TTL that must not exceed a lock lease, a page size bounded by a batch limit), reuse or derive from the existing property rather than introducing a new independent constant. Two separate properties with the same semantic constraint are two sources of truth that will diverge. If the dependency cannot be expressed at the type level, document it explicitly in a KDoc comment on both properties and validate alignment in an `init` block or at startup (see company-guidelines #40).

## Spring `@ConfigurationProperties` — Duration Fields

Use `Duration` as the field type for any `@ConfigurationProperties` duration property — not `Long`/`Int` with a unit suffix (e.g. `windowHours`, `maxIdleMinutes`). Spring Boot parses human-readable strings (`8h`, `3m`, `30s`, `1d`, `500ms`) automatically via `DurationStyle`. Validate positivity in a startup `SmartInitializingSingleton`. See `jvm_guidelines.md #2`.

## Spring Cloud Config — application name

Never set `spring.application.name` in the bundled `application.yml` of a service that uses Spring Cloud Config. See `jvm_guidelines.md #3`.

## Coroutine Fail-Open Catch Blocks — `CancellationException` and Stack Traces

Every `catch (e: Exception)` inside a `suspend` function must rethrow `CancellationException` before fail-open handling; swallowing it prevents scope cancellation. See `kotlin_guidelines.md #16`.

Always pass the exception object `e` (not `e.message`) as the last argument to `log.error` — SLF4J appends the full stack trace only when the last argument is a `Throwable`. See `jvm_guidelines.md #6`.

## Git Push Policy

Never push to `origin` (or any remote) without an explicit instruction from the user to do so. Completing a commit or merge does not imply permission to push. After every local commit, stop and wait for the user's next instruction — do not chain `git push` unless the user's message explicitly asked for it.

Never run `git push --force`, `git push --force-with-lease`, or any other force push without explicit user approval. Ask first even when fixing a mistaken push or rewriting history.

When the user asks to squash commits before push, squash only commits not yet on the remote (`git log origin/<branch>..HEAD`), using `git reset --soft origin/<branch>` on the current branch. Do not rewrite the full repository history (`git checkout --orphan`) unless the user explicitly asks for that.

Before pushing to a public repository, audit commit messages in the push range for `Co-authored-by:` trailers and employer or client brand names in subjects (keep employer references in local `facts.md` only). Scan file content too; see the `done` skill Step 2.7.

## Text Output Formatting

Never use em dashes (—) in any generated text: code comments, PR review comments, commit messages, documentation, plans, or conversational replies. Use alternatives: commas, semicolons, colons, parentheses, or split into separate sentences. This rule applies unconditionally to all output surfaces.

## Document Creation

Always create documents (findings, notes, drafts, reports, Slack-shareable writeups) inside the relevant project's `docs/` folder (use `docs/tmp/` for temporary or shareable artifacts). Never create them in the session state folder (`~/.copilot/session-state/`).

## Merge Strategy Verification

Before starting any branch merge, always run `git fetch origin && git log origin/<branch> --oneline -5` to verify the actual remote state of the target branch. Do not rely on session history or assumptions — the branch may have been squash-merged, reset, or diverged. Choose the merge strategy (squash, cherry-pick, full merge) only after confirming the remote state.

After resolving any conflicts, always run the full test suite before committing the merge result. A passing test run is required before the merge commit is made.

## Personal projects

For repositories under the **personal projects** workspace root (`personal_projects_root` in `~/.ai-playbook/facts.md`), perform git operations locally by default: squash-merge into the target branch locally; do not push branches or open GitHub PRs unless the user explicitly asks.

Git author, GitHub account selection, and workspace roots: see `~/.ai-playbook/facts.md`.

## GitHub PR URL — Skill Trigger

When the user sends a GitHub PR URL (`github.com/<owner>/<repo>/pull/<N>`, `<repo>#<N>`, or `PR #<N>`), invoke a code-review skill before producing output:

- Active review ("review", "look at", "check the PR"): invoke `doing-code-review`. Do not produce ad-hoc inline findings.
- Passive review ("address", "respond to", "process existing comments"): invoke `receiving-code-review`.
- Question only ("what does this PR do?", "summarize"): no skill needed; answer directly.

A quick scan looking sufficient is not a reason to skip; the skill enforces sub-agent fan-out, premortem, and staging-doc protocol.

## Git Commit Trailer Policy

Never add `Co-authored-by:` (or `Co-Authored-By:`) trailers to commit messages, including `Co-authored-by: Cursor <cursoragent@cursor.com>`. Do not pass `git commit --trailer` for agent attribution.

In Cursor IDE, turn off **Settings → Agent → Attribution** so the shell wrapper does not append the Cursor co-author trailer to agent-driven commits.

## Formatting-Only Files Must Not Be Committed

Before every commit, read the full diff of **every** staged file and restore any whose entire diff is purely cosmetic. `git diff -w` alone is not sufficient — ktlint and other formatters apply semantic reformatting (trailing commas, multi-line ↔ single-line expression wraps, `when` block re-indentation, method chain splitting) that `git diff -w` cannot detect.

For each staged file run `git diff --cached -- <file>` and restore it with `git restore --staged --worktree <file>` if all changes match cosmetic-only patterns: whitespace/blank-line changes, trailing commas added/removed, multi-line ↔ single-line wraps, `when` block indentation, method chain reformatting, newline at end of file.

Apply the same check before marking a PR ready: scan the full branch diff with `git diff $(git merge-base HEAD origin/$(git remote show origin | awk '/HEAD branch/{print $NF}'))..HEAD --name-only` and revert any formatting-only files.

## Scoped Maven Lifecycle Commands In Formatter-Bound Repos

When working in a Maven multi-module repository that binds an auto-formatter `format` goal into the default lifecycle (especially at `process-sources`), do not run root-level lifecycle commands such as `mvn clean compile`, `mvn clean test-compile`, `mvn clean test`, or `mvn clean verify` unless repo-wide formatting is intentional. Those commands can silently rewrite files across every module. Scope the run to affected modules with `-pl <module1>,<module2> -am`, and review any formatter-only diffs before committing.

## Repo-local `.claude/` Bootstrap Convention

Never commit local LLM agent config directories; add `.claude/`, `.opencode/`, `.codex/`, `.continue/`, `.cursor/rules` to `.gitignore` from project inception. Treat repo-local `.claude/settings.local.json` as bootstrap-only: merge its permissions to `~/.claude/settings.json` on first setup, then delete the directory and any `docs` shadow branch.

## Gitignored Docs and Instructions — Git Safety Rules

These rules apply to any repository where `docs/`, `AGENTS.md`, or `CLAUDE.md` are gitignored (LLM agent artifacts preserved via stash and shadow branch).

- Before staging any file with `git add`, verify it is not gitignored: `git check-ignore -q <file>`. If the file is gitignored but appears in `git diff` (previously force-tracked), remove it from tracking with `git rm --cached <file>` — never commit it on the feature branch.
- Never run `git stash clear` in a repository where gitignored docs/instructions are preserved via stash — stash entries serve as backup transport across branch switches and a second backup layer alongside the `docs` shadow branch. Dropping them removes that redundancy.
- When executing any multi-step bash script that involves branch switches and uses a shared variable (e.g. `RESTORE_TMP`), run all steps in a **single bash tool call**. Shell variables do not persist between separate tool calls; splitting the sequence causes temp paths to be empty in later calls, silently deleting files without restoring them.
- For cross-platform line filtering in bash, use `grep -vE` rather than `sed -i`. macOS ships BSD `sed` where `\?` is a literal `?` (not zero-or-one quantifier), causing silent mis-filtering on macOS while working on Linux.

## External Source Archive Provenance And Freshness

Every downloaded external source mirrored under `docs/.../official/` must have a corresponding `sources.md` entry that records the official URL, issuing date, retrieval date, purpose, and the exact articles, sections, annexes, chapters, or clauses relied on. Each time an archived external source is used for analysis, implementation, or user-facing advice, check the official source first for a newer version. If a newer official version exists, archive it in the correct folder and update the manifest before relying on that source.


## Document Cross-Reference Policy

Documentation files are self-contained by default. Referencing one document from another is only allowed when explicitly requested or structurally required for consistency (e.g. a workflow doc that is the canonical definition of a process). In all other cases, extract the required data directly into the document that needs it. This avoids fragile inter-document dependencies where a reader must follow a chain of references to understand a single document, and prevents breakage when IDs, section numbers, or file paths change.

- **Default**: copy or paraphrase the needed information inline; do not add a cross-document reference.
- **Allowed exceptions**: explicit user request, or a canonical definition that must not be duplicated (e.g. a shared glossary entry that is the single source of truth and changes rarely).
- **Instruction files** (`AGENTS.md`, `CLAUDE.md`) are the only documents that may freely reference other docs — that is their purpose.
- When in doubt, inline it.

## Jira Task Context Ledger

When Jira task context is needed for a feature (for example, to distinguish the primary ticket from parallel or follow-up stories), record the relevant ticket IDs and a one-line relevance summary in `docs/facts.md` under **Related Jira Tasks**. Use that section only for internal scoping clarity; do not cite `docs/facts.md` from RFCs, PR descriptions, or code comments. Any human-facing document that needs Jira context must restate the relevant ticket IDs inline.

## Guidelines and facts loading

At task start, read applicable **facts** (see hierarchy table above) and **guidelines** for the current context.

### Facts (environment-specific)

1. `~/.ai-playbook/facts.md` — git author, GitHub accounts, workspace roots, `shared_docs_dir`, skill keys, brag paths, instruction entrypoints.
2. Ownership: company or personal-projects ownership `facts.md` when the repo path matches (paths in `~/.ai-playbook/facts.md`).
3. Repo: `docs/facts.md` when present in the current repository.

### Guidelines (public rules)

Load from `shared_docs_dir` in `~/.ai-playbook/facts.md` (directory symlink to `instructions_repo/projects/.ai-playbook/`): `agent_workflow_guidelines.md`, `coding_guidelines.md`, and language files (`jvm`, `kotlin`, `java`, `python`) as applicable; add `company-guidelines.md` from the company ownership docs directory when scope applies. Load `docs/project-guidelines.md` in the current repo when it exists.

### Deduplication

Elevate reusable **rules** to this `AGENTS.md` or shared guidelines; keep **identity, inventories, and machine paths** in `facts.md` only. When elevating a rule, reduce lower tiers to cross-references.

## Compaction

Always run the `learn` skill before triggering or allowing context compaction. Compaction discards conversation history; running `learn` first ensures any lessons from the session are captured in the instruction corpus before that history is lost.

## Agent Workflow Lessons

- Multi-direction aggregation: test each subtype before implementing. See `agent_workflow_guidelines.md` #1.
- Review false positives: run the test first; do not trace code for a finding a test run can deny. See `agent_workflow_guidelines.md` #2.
- Field semantics: never repurpose one field for another's gate logic. See `agent_workflow_guidelines.md` #3.
- Post-refactoring cleanup: detect unused imports and duplicate defs before committing. See `agent_workflow_guidelines.md` #4.
- Gitignored docs in code comments: use shared Confluence URL, not local file path; add inline rationale for RFC constraints. See `agent_workflow_guidelines.md` #5.
- Formatting-only file detection: `git diff -w` misses trailing commas, import reorder, line wraps; read full diff per file. See `agent_workflow_guidelines.md` #6.
- Protect non-obvious design choices: add inline comment with rationale + shared doc link to prevent accidental removal. See `agent_workflow_guidelines.md` #7.
- Scope discipline: don't make "while I'm here" improvements to unrelated files, and don't add unrequested properties/settings within an in-scope file (e.g. extra logging rules when only one was asked for); note extras for a separate PR. See `agent_workflow_guidelines.md` #8.
- Failing tests are the current branch's responsibility: no such thing as "pre-existing" or "unrelated infra" failures; fix them or annotate with a tracked skip before merge. See `agent_workflow_guidelines.md` #11.
- Out-of-scope revert: before reverting a candidate file, verify no in-scope file calls any API changed in it; a compile error after revert is hard evidence of a missed dependency. See `agent_workflow_guidelines.md` #10.
- Verify test execution count after adding @Test methods: count mismatch is the only signal of silently skipped tests; silence from the runner is not confirmation of success. See `agent_workflow_guidelines.md` #12.
- Portable shell locking: use `mkdir`-based locks, not `flock` (not on macOS). See `agent_workflow_guidelines.md` #13.
- Agent-specific hook wrappers: keep shared scripts agent-agnostic; use thin wrappers for protocol translation (e.g. Codex JSON vs Claude plain text). See `agent_workflow_guidelines.md` #14.
- Python test CSV data: verify alignment with parsed-dict print; copy from existing tests. See `python_guidelines.md` #1 under `shared_docs_dir`.
- Python post-extraction: `ruff check <source> --select=F401,F811`. See `python_guidelines.md` #2 under `shared_docs_dir`.
- Addressing PR comments: invoke the `github-pr-workflow` skill — the full flow is fetch → assess → fix → reply → resolve. Fixing code without replying and resolving threads leaves them dangling.
- Merge-time compile errors from divergent refactoring: before propagating a fix to a source branch, check the source branch's DTO/interface with `git show <branch>:<file>`; if the fields are absent there, the error is a merge artifact and the fix belongs only in the merged result. See `agent_workflow_guidelines.md` #16.
- CI application ERROR logs are not test failures: check `Failures: 0, Errors: 0` in the JUnit summary line first; ERROR lines in log output are the service logging invalid-input rejections, not JUnit failures. See `agent_workflow_guidelines.md` #17.
- Markdown tables break when cell values contain `|`: escape pipes as `\|` inside cells, or switch to a numbered/bulleted list when the values are long or pipe-heavy (e.g. Grafana panel titles with dimension separators). See `agent_workflow_guidelines.md` #41.
- PR chain awareness: before flagging missing tests/logic in a PR, check downstream branches in the chain; if the change exists there, skip the comment. See `agent_workflow_guidelines.md` #22.
- Rollback ambiguity: `git revert` adds a new commit (preserves history); `git reset --hard` + force-push removes it. Clarify intent before rolling back a pushed commit. See `agent_workflow_guidelines.md` #23.
- Context sharing is not an action directive: when a user shares PR comments, logs, or review notes without an explicit action instruction, ask about working mode before implementing anything. See `agent_workflow_guidelines.md` #24.
- Intent-dependent review findings should be framed as open questions, not directive corrections: cite the observation, the documented intent, and ask the author to decide. See `agent_workflow_guidelines.md` #25.
- Read telemetry before proposing remediation: do not anchor on the first plausible hypothesis; frame initial guesses as hypotheses and verify framework semantics (knob name ≠ runtime effect) before computing capacity. See `agent_workflow_guidelines.md` #26.
- Separate chronic noise from blocking urgency: pre-existing failures that retries catch are not release blockers; gate urgency on permanent-drop counters, not raw error rate. See `agent_workflow_guidelines.md` #27.
- Do not add unnecessary coordination steps to tickets/PRs: if the change does not move peak load, contract shape, or cross shared infra ownership, no DBA/SRE approval line is needed. See `agent_workflow_guidelines.md` #28.
- Confirm timezone before correlating user-shared dashboards to UTC events: include both representations (`HH:MM UTC = HH:MM local`) when stating a correlation. See `agent_workflow_guidelines.md` #29.
- Verify observability artifact inputs before authoring: confirm the metric is emitted today and that PromQL regex matches actual label values (case-sensitive; Micrometer often uses bean-name camelCase). See `agent_workflow_guidelines.md` #30.
- Prefer `INSERT IGNORE` (MySQL) or `ON CONFLICT DO NOTHING` (PostgreSQL) over select-then-insert to eliminate TOCTOU races on unique constraints. Use the affected-row count to branch post-insert logic without a separate existence check. See project-guidelines.md #24.
- When converting per-item operations to batch operations, audit safety invariants the per-item design provided: status guards (re-read status inside lock), lock coverage (outer lock lease vs. batch duration), and failure blast radius (batch failure = all items retry). Preserve or explicitly accept their loss. See project-guidelines.md #25.
- Verify terminal state after automation, not intermediate confirmations: "Successfully triggered" is not "successfully applied"; sample the observable end-state before concluding the action took effect. See `agent_workflow_guidelines.md` #31.
- GitOps reconcilers revert imperative changes: a `kubectl rollout restart` (or similar) on an Argo CD / Flux-managed resource gets reverted on the next sync; the reliable path is to commit the change to git. Check for `argocd.argoproj.io/instance` labels before troubleshooting restart-didn't-restart symptoms. See `agent_workflow_guidelines.md` #32.
- Follow the project PR template when automation depends on it: custom PR descriptions can silently disable CI behaviour gated on template fields (`[x]` checkbox, `isRestartRequired: true` metadata); preserve the template's machine-readable blocks. Squash-merge with a cleaned commit body is the second failure mode of the same rule: warn the user at PR creation and at merge time not to squash-merge with a cleared body. See `agent_workflow_guidelines.md` #33.
- Check internal runbooks (Confluence, repo wiki, README) before diagnosing platform tooling: a 5-minute read often settles questions that would take an hour of cluster probing. See `agent_workflow_guidelines.md` #34.
- Public repo push hygiene: never force-push without explicit approval; squash only unpushed commits unless the user asks for full history rewrite; audit commit messages and skills for `Co-authored-by:` trailers and employer brand names before push. See `agent_workflow_guidelines.md` #44.
- Plain language for human-facing artifacts: prefer "API contract" / "public API response shape" over "wire contract"; add a `## Terms` section when using 3+ project-specific words; capture new replacements via `learn` into `agent_workflow_guidelines.md` #45. See `agent_workflow_guidelines.md` #45.

## Brag document activity

When a notable company work activity should be recorded for career tracking, follow paths and file naming in `~/.ai-playbook/facts.md` and the personal-projects ownership `facts.md` when applicable.
