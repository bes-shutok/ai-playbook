# Plan: Apply ASD-STE100 to Codex shared instructions and skills

Backlog origin: `docs/history/backlog/2026-11-16-asd-ste100-codex-canonical-policy-and-skill-corpus.md`
Cluster: `docs/history/backlog/2026-11-16-asd-ste100-claude-runtime-adoption.md`; `docs/history/backlog/2026-11-16-asd-ste100-zcode-runtime-adoption.md`
Required agent type: codex
Executed: yes (0fabe9b219478722c69796509b17bf424b6ff845)
Authoring claim: asd-ste100-codex-shared-corpus.md (session 01a1e4b6-199d-7a72-b9d1-0563830f52dd)
Driving force: clarity
Plan review record: `.ai-playbook/reviews/2026-11-16-plan-review-asd-ste100-codex-shared-corpus-p6ea06a10-r*.md`

## Terms

- **ASD-STE100 Issue 9**: the official controlled English standard for technical documentation, including its writing rules and dictionary. Use the official specification as the authority.
- **English prose**: human-readable English text authored in instructions, skills, plans, reviews, summaries, and user responses.
- **Preserved text**: code, commands, identifiers, schema and API names, proper names, exact quotations, user-provided text, and text in another language, unless the user asks to edit it.
- **Project-defined terminology**: technical terms owned by a project or subject area. Use approved dictionary words when they preserve meaning. Retain subject-specific technical nouns and verbs when Issue 9 permits them. Define terms through their canonical source and use them consistently.
- **Private decision method**: short facts, conditions, actions, and outcomes used to reach a decision. It does not require disclosure of private chain-of-thought.
- **Shared skill corpus**: all 170 tracked Markdown files under `agents/skills/`, including 50 `SKILL.md` entry files and 120 supporting Markdown files. The shared script outcome contract is a separate output-contract source.

## Why

The shared instructions and skills have no common policy for clear technical English or project-defined terminology. The request also asks agents to use ASD-STE100 for “thinking,” but the standard governs technical writing, not private model reasoning.

## Gist & Examples

TLDR: Add one shared writing policy and apply it to the Codex-owned instruction and skill sources to improve clarity.

Before (today): an agent writes a skill instruction, review summary, or user response without a shared rule for controlled technical English. The reader may see long sentences or unclear actions, and “use STE for thinking” has no defined meaning.

After (this plan): the same agent writes short English prose that follows ASD-STE100 Issue 9 where the standard applies. It preserves exact technical strings and user text. The agent uses facts, conditions, actions, and outcomes as a private decision method, then gives a concise rationale when useful. It does not disclose private chain-of-thought or claim formal certification.

## Outcome

The shared Codex instruction and skill corpus has one clear policy for ASD-STE100 English writing and private decision summaries.

- The canonical instructions define scope, exceptions, term handling, and the private decision method.
- Existing skill-writing guidance points to the canonical rule and rejects a dedicated skill unless it adds unique workflow logic.
- All 50 entry files and 120 supporting Markdown files follow the policy where English prose is authored or maintained.
- The official standard remains the authority; the repository does not copy its dictionary or claim certification.

Gate delta: no new blocking gate, validator, refusal class, or schema field; no existing blocker removed.

## Assumptions

- assume Issue 9 is the target edition; basis: the backlog names the official Issue 9 PDF dated 2025-01-15, and the ASD-STE100 site identifies Issue 9 as current.
- assume the canonical policy belongs in `docs/AGENTS.md`; basis: it is the shared user-level source of truth, and Codex loads it through the verified runtime entrypoint.
- assume a dedicated skill is not needed at the outset; basis: this is default writing behavior, and the repository's Skill Design Guidelines require unique workflow logic or domain knowledge for a skill.
- assume the migration covers all 170 tracked Markdown files under `agents/skills/`; basis: the tracked inventory contains 50 `SKILL.md` entry files and 120 supporting Markdown files.
- assume no blocking conformance checker should be added; basis: the machinery admission protocol requires a witnessed incident, and the backlog cites none.
- assume the policy applies to authored English prose and preserves the defined exact-content exceptions; basis: the official standard governs controlled technical English, while rewriting these preserved values can change meaning or break executable content.
- assume the shared corpus conversion will use a representative manual review and existing gates; basis: no proven need for a new validator exists and the repository already has text-budget and hygiene checks.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Clarity: a representative sample states one clear action or result per sentence where practical and uses direct wording.
- Meaning preservation: examples, identifiers, commands, quotes, and user-provided text retain their required content.
- Consistency: the canonical rule has one full-text home; skills reference it without copying the full policy. Project-defined terms keep their canonical meaning and use.
- Scope: all 170 tracked Markdown files are checked and all applicable English prose is revised.

**Done when:**
- `docs/AGENTS.md` defines the policy and `how-to-write-skills` points to it.
- The 50 entry files and 120 supporting Markdown files have been audited and updated where needed. The shared script outcome contract has also been audited, with machine-readable terms preserved.
- Representative short, dense, template, and structured-output samples receive the selected reviews.
- The skill text byte-budget check, public hygiene scan, and em-dash scan pass.

**Ship when:** none. This plan changes local instructions and shared skills only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `scripts/OUTCOME_CONTRACT.md` (Task 4)
- `docs/AGENTS.md` (Task 1)
- `agents/skills/how-to-write-skills/SKILL.md` (Task 1)
- `agents/skills/agents-best-practices/SKILL.md` (Task 2)
- `agents/skills/agterm/SKILL.md` (Task 2)
- `agents/skills/bootstrap-ai-playbook/SKILL.md` (Task 2)
- `agents/skills/confluence-page-sync/SKILL.md` (Task 2)
- `agents/skills/cursor-agent-diagnose/SKILL.md` (Task 2)
- `agents/skills/doc-hierarchy-migrate/SKILL.md` (Task 2)
- `agents/skills/doc-hierarchy-upkeep/SKILL.md` (Task 2)
- `agents/skills/doc-hierarchy/SKILL.md` (Task 2)
- `agents/skills/docs-branch/SKILL.md` (Task 2)
- `agents/skills/doing-code-review/SKILL.md` (Task 2)
- `agents/skills/domain-modeling/SKILL.md` (Task 2)
- `agents/skills/done/SKILL.md` (Task 2)
- `agents/skills/execute-plan-stack/SKILL.md` (Task 2)
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `agents/skills/generalize/SKILL.md` (Task 2)
- `agents/skills/github-pr-workflow/SKILL.md` (Task 2)
- `agents/skills/graphify/SKILL.md` (Task 2)
- `agents/skills/grill-with-docs/SKILL.md` (Task 2)
- `agents/skills/grilling/SKILL.md` (Task 2)
- `agents/skills/handoff/SKILL.md` (Task 2)
- `agents/skills/i-have-adhd/SKILL.md` (Task 2)
- `agents/skills/investigate/SKILL.md` (Task 2)
- `agents/skills/jira-workflow/SKILL.md` (Task 2)
- `agents/skills/learn/SKILL.md` (Task 2)
- `agents/skills/lessons-migrate/SKILL.md` (Task 2)
- `agents/skills/maintenance/SKILL.md` (Task 2)
- `agents/skills/pdf/SKILL.md` (Task 2)
- `agents/skills/plan-stack/SKILL.md` (Task 2)
- `agents/skills/plans/SKILL.md` (Task 2)
- `agents/skills/premortem/SKILL.md` (Task 2)
- `agents/skills/receiving-review/SKILL.md` (Task 2)
- `agents/skills/release/SKILL.md` (Task 2)
- `agents/skills/review-agents/SKILL.md` (Task 2)
- `agents/skills/review-confluence-doc/SKILL.md` (Task 2)
- `agents/skills/review-loop/SKILL.md` (Task 2)
- `agents/skills/review-plan/SKILL.md` (Task 2)
- `agents/skills/review-reconciliation/SKILL.md` (Task 2)
- `agents/skills/review-staging/SKILL.md` (Task 2)
- `agents/skills/rfc-design/SKILL.md` (Task 2)
- `agents/skills/rootly-retrospective/SKILL.md` (Task 2)
- `agents/skills/self-heal/SKILL.md` (Task 2)
- `agents/skills/slack-message/SKILL.md` (Task 2)
- `agents/skills/systematic-debugging/SKILL.md` (Task 2)
- `agents/skills/tdd-design/SKILL.md` (Task 2)
- `agents/skills/tdd-guide/SKILL.md` (Task 2)
- `agents/skills/transcription-cross-check/SKILL.md` (Task 2)
- `agents/skills/unit-test-runner/SKILL.md` (Task 2)
- `agents/skills/update-stacked-branches/SKILL.md` (Task 2)
- `agents/skills/using-skills/SKILL.md` (Task 2)
- `agents/skills/agents-best-practices/README.md` (Task 3)
- `agents/skills/agents-best-practices/references/agent-legibility-feedback-loops.md` (Task 3)
- `agents/skills/agents-best-practices/references/agentic-loop.md` (Task 3)
- `agents/skills/agents-best-practices/references/architecture.md` (Task 3)
- `agents/skills/agents-best-practices/references/checklists.md` (Task 3)
- `agents/skills/agents-best-practices/references/coding-agents.md` (Task 3)
- `agents/skills/agents-best-practices/references/context-memory-compaction.md` (Task 3)
- `agents/skills/agents-best-practices/references/coverage-audit.md` (Task 3)
- `agents/skills/agents-best-practices/references/evals.md` (Task 3)
- `agents/skills/agents-best-practices/references/mvp-agent-blueprint.md` (Task 3)
- `agents/skills/agents-best-practices/references/planning-and-goals.md` (Task 3)
- `agents/skills/agents-best-practices/references/prompt-caching-and-cost.md` (Task 3)
- `agents/skills/agents-best-practices/references/provider-api-patterns.md` (Task 3)
- `agents/skills/agents-best-practices/references/security-observability.md` (Task 3)
- `agents/skills/agents-best-practices/references/skills-and-connectors.md` (Task 3)
- `agents/skills/agents-best-practices/references/source-links.md` (Task 3)
- `agents/skills/agents-best-practices/references/system-prompts-instructions.md` (Task 3)
- `agents/skills/agents-best-practices/references/tools-and-permissions.md` (Task 3)
- `agents/skills/agents-best-practices/references/workflow-orchestration.md` (Task 3)
- `agents/skills/agterm/agent-runtimes.md` (Task 3)
- `agents/skills/agterm/cookbook.md` (Task 3)
- `agents/skills/agterm/examples.md` (Task 3)
- `agents/skills/agterm/reference-appearance.md` (Task 3)
- `agents/skills/agterm/reference-connection.md` (Task 3)
- `agents/skills/agterm/reference-layout.md` (Task 3)
- `agents/skills/agterm/reference-restore.md` (Task 3)
- `agents/skills/agterm/reference-session.md` (Task 3)
- `agents/skills/agterm/reference-windows.md` (Task 3)
- `agents/skills/agterm/reference.md` (Task 3)
- `agents/skills/agterm/troubleshooting.md` (Task 3)
- `agents/skills/doc-hierarchy/company-decisions.md` (Task 3)
- `agents/skills/doc-hierarchy/content-ownership.md` (Task 3)
- `agents/skills/doc-hierarchy/instruction-templates.md` (Task 3)
- `agents/skills/doc-hierarchy/migration-map.md` (Task 3)
- `agents/skills/doing-code-review/general.md` (Task 3)
- `agents/skills/doing-code-review/java-spring.md` (Task 3)
- `agents/skills/doing-code-review/kotlin-spring.md` (Task 3)
- `agents/skills/doing-code-review/python.md` (Task 3)
- `agents/skills/domain-modeling/adr-format.md` (Task 3)
- `agents/skills/domain-modeling/glossary-format.md` (Task 3)
- `agents/skills/execute-plan/agent-logs.md` (Task 3)
- `agents/skills/execute-plan/archive-and-cleanup.md` (Task 3)
- `agents/skills/execute-plan/implementation-loop.md` (Task 3)
- `agents/skills/execute-plan/invocation-and-orchestration.md` (Task 3)
- `agents/skills/execute-plan/launch-rules-and-gates.md` (Task 3)
- `agents/skills/execute-plan/phase-3-review.md` (Task 3)
- `agents/skills/execute-plan/recovery-and-integration.md` (Task 3)
- `agents/skills/execute-plan/run-setup.md` (Task 3)
- `agents/skills/execute-plan/runtime-contract.md` (Task 3)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 3)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)
- `agents/skills/graphify/references/add-watch.md` (Task 3)
- `agents/skills/graphify/references/exports.md` (Task 3)
- `agents/skills/graphify/references/extraction-spec.md` (Task 3)
- `agents/skills/graphify/references/github-and-merge.md` (Task 3)
- `agents/skills/graphify/references/hooks.md` (Task 3)
- `agents/skills/graphify/references/query.md` (Task 3)
- `agents/skills/graphify/references/transcribe.md` (Task 3)
- `agents/skills/graphify/references/update.md` (Task 3)
- `agents/skills/how-to-write-skills/references/frontmatter-guide.md` (Task 3)
- `agents/skills/how-to-write-skills/references/progressive-disclosure.md` (Task 4)
- `agents/skills/how-to-write-skills/references/skill-design-principles.md` (Task 4)
- `agents/skills/how-to-write-skills/references/skill-design-vocabulary.md` (Task 4)
- `agents/skills/how-to-write-skills/references/skill-sizes.md` (Task 4)
- `agents/skills/how-to-write-skills/references/skill-structure.md` (Task 4)
- `agents/skills/learn/step-1-extract.md` (Task 4)
- `agents/skills/learn/step-2-placement.md` (Task 4)
- `agents/skills/learn/step-6-instruction-updates.md` (Task 4)
- `agents/skills/learn/step-completion.md` (Task 4)
- `agents/skills/maintenance/CHANGELOG.md` (Task 4)
- `agents/skills/maintenance/codex.md` (Task 4)
- `agents/skills/maintenance/decisions.md` (Task 4)
- `agents/skills/maintenance/duties-core.md` (Task 4)
- `agents/skills/maintenance/failure-cap.md` (Task 4)
- `agents/skills/maintenance/guards.md` (Task 4)
- `agents/skills/maintenance/prompt-templates.md` (Task 4)
- `agents/skills/maintenance/quota-policy.md` (Task 4)
- `agents/skills/maintenance/scheduling.md` (Task 4)
- `agents/skills/maintenance/state-file.md` (Task 4)
- `agents/skills/maintenance/survey-arms.md` (Task 4)
- `agents/skills/maintenance/template-authoring.md` (Task 4)
- `agents/skills/maintenance/template-execution.md` (Task 4)
- `agents/skills/maintenance/template-unblock.md` (Task 4)
- `agents/skills/maintenance/templates-CHANGELOG.md` (Task 4)
- `agents/skills/maintenance/zcode-context-audit.md` (Task 4)
- `agents/skills/maintenance/zcode-dispatch-ladder.md` (Task 4)
- `agents/skills/maintenance/zcode-primitive-verification.md` (Task 4)
- `agents/skills/maintenance/zcode-quota-effort.md` (Task 4)
- `agents/skills/maintenance/zcode-recurring-recipe.md` (Task 4)
- `agents/skills/maintenance/zcode-scheduling-primitives.md` (Task 4)
- `agents/skills/maintenance/zcode.md` (Task 4)
- `agents/skills/plans/budget-gate.md` (Task 4)
- `agents/skills/plans/handoff-and-done.md` (Task 4)
- `agents/skills/plans/integration-points.md` (Task 4)
- `agents/skills/plans/phase-0-placement.md` (Task 4)
- `agents/skills/plans/phase-1-requirements.md` (Task 4)
- `agents/skills/plans/plan-format.md` (Task 4)
- `agents/skills/plans/plan-lifecycle.md` (Task 4)
- `agents/skills/plans/plan-quality-gate.md` (Task 4)
- `agents/skills/plans/task-design.md` (Task 4)
- `agents/skills/plans/universal-patterns.md` (Task 4)
- `agents/skills/plans/validation-authoring-rules.md` (Task 4)
- `agents/skills/review-agents/architecture.md` (Task 4)
- `agents/skills/review-agents/concurrency.md` (Task 4)
- `agents/skills/review-agents/consistency.md` (Task 4)
- `agents/skills/review-agents/documentation.md` (Task 4)
- `agents/skills/review-agents/implementation.md` (Task 4)
- `agents/skills/review-agents/premortem.md` (Task 4)
- `agents/skills/review-agents/quality.md` (Task 4)
- `agents/skills/review-agents/review-panel-selection.md` (Task 4)
- `agents/skills/review-agents/security.md` (Task 4)
- `agents/skills/review-agents/severity-calibration.md` (Task 4)
- `agents/skills/review-agents/simplification.md` (Task 4)
- `agents/skills/review-agents/testing.md` (Task 4)
- `agents/skills/rfc-design/references/contract-blueprint-example.md` (Task 4)
- `agents/skills/rfc-design/references/eval-cases.md` (Task 4)
- `agents/skills/rfc-design/references/rfc-sections.md` (Task 4)
- `agents/skills/tdd-guide/java-kotlin.md` (Task 4)
- `agents/skills/tdd-guide/python.md` (Task 4)
- `agents/skills/unit-test-runner/maven.md` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Runtime-specific instruction files for Claude and ZCode; their required-agent backlog items own those changes.
- Non-Markdown skill assets and external agent installations; this plan updates the tracked shared Markdown source only.
- A blocking validator or gate; no witnessed incident supports one.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
```

### Task 1: Set the canonical policy and authoring guidance

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `docs/AGENTS.md`
- `agents/skills/how-to-write-skills/SKILL.md`

- [x] Add a concise ASD-STE100 Issue 9 policy under the existing `Hard rules (keep inline; high frequency)` section. State the scope, preserved text, official authority, meaning-preservation rule, and no-certification claim. [class: IMPLEMENTATION_REQUIRED]
- [x] State the term rule: use approved words when they preserve meaning; retain subject-specific technical nouns and verbs when Issue 9 permits them; preserve project-defined terms through their canonical source and use them consistently. Do not treat every term absent from the general dictionary as an error. [class: IMPLEMENTATION_REQUIRED]
- [x] Define “thinking” as a private method based on facts, conditions, actions, and outcomes. Do not require disclosure of private chain-of-thought; ask for concise rationale summaries when needed. [class: IMPLEMENTATION_REQUIRED]
- [x] State that a dedicated skill is out of scope unless the work identifies unique, repeatable workflow logic that the existing shared instructions and authoring skill cannot own. [class: IMPLEMENTATION_REQUIRED]
- [x] Add concise authoring guidance to `how-to-write-skills` that points to `docs/AGENTS.md`; do not duplicate the full policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Select `contract-docs` and `correctness-completeness` from the existing panel policy for the normative policy review. Record the scope-based rationale in the review record. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the policy review and resolve every blocking finding before converting the corpus. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: define ASD-STE100 shared writing policy` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Convert shared skill entry files

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/agents-best-practices/SKILL.md`
- `agents/skills/agterm/SKILL.md`
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/confluence-page-sync/SKILL.md`
- `agents/skills/cursor-agent-diagnose/SKILL.md`
- `agents/skills/doc-hierarchy-migrate/SKILL.md`
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/domain-modeling/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan-stack/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/generalize/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `agents/skills/graphify/SKILL.md`
- `agents/skills/grill-with-docs/SKILL.md`
- `agents/skills/grilling/SKILL.md`
- `agents/skills/handoff/SKILL.md`
- `agents/skills/i-have-adhd/SKILL.md`
- `agents/skills/investigate/SKILL.md`
- `agents/skills/jira-workflow/SKILL.md`
- `agents/skills/learn/SKILL.md`
- `agents/skills/lessons-migrate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/pdf/SKILL.md`
- `agents/skills/plan-stack/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/premortem/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/release/SKILL.md`
- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-reconciliation/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/rootly-retrospective/SKILL.md`
- `agents/skills/self-heal/SKILL.md`
- `agents/skills/slack-message/SKILL.md`
- `agents/skills/systematic-debugging/SKILL.md`
- `agents/skills/tdd-design/SKILL.md`
- `agents/skills/tdd-guide/SKILL.md`
- `agents/skills/transcription-cross-check/SKILL.md`
- `agents/skills/unit-test-runner/SKILL.md`
- `agents/skills/update-stacked-branches/SKILL.md`
- `agents/skills/using-skills/SKILL.md`

- [x] Audit each entry file for authored English prose, examples, and output requirements. Update applicable text to follow the canonical policy while preserving meaning and required technical literals. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep each skill's workflow, gates, and output contract intact unless the policy requires a clarity edit. Do not add repeated copies of the full shared policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Record project-defined terms with their canonical source and meaning. Use an approved word only when it preserves the technical meaning. Record other intentional exceptions with a reason. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep each changed file within its byte cap. When a file exceeds its cap, remove equivalent bytes in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the skill-focused review selected by the existing panel policy against the exact changed skill diff. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: apply ASD-STE100 to skill entry files` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Convert the first supporting-document batch

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/agents-best-practices/README.md`
- `agents/skills/agents-best-practices/references/agent-legibility-feedback-loops.md`
- `agents/skills/agents-best-practices/references/agentic-loop.md`
- `agents/skills/agents-best-practices/references/architecture.md`
- `agents/skills/agents-best-practices/references/checklists.md`
- `agents/skills/agents-best-practices/references/coding-agents.md`
- `agents/skills/agents-best-practices/references/context-memory-compaction.md`
- `agents/skills/agents-best-practices/references/coverage-audit.md`
- `agents/skills/agents-best-practices/references/evals.md`
- `agents/skills/agents-best-practices/references/mvp-agent-blueprint.md`
- `agents/skills/agents-best-practices/references/planning-and-goals.md`
- `agents/skills/agents-best-practices/references/prompt-caching-and-cost.md`
- `agents/skills/agents-best-practices/references/provider-api-patterns.md`
- `agents/skills/agents-best-practices/references/security-observability.md`
- `agents/skills/agents-best-practices/references/skills-and-connectors.md`
- `agents/skills/agents-best-practices/references/source-links.md`
- `agents/skills/agents-best-practices/references/system-prompts-instructions.md`
- `agents/skills/agents-best-practices/references/tools-and-permissions.md`
- `agents/skills/agents-best-practices/references/workflow-orchestration.md`
- `agents/skills/agterm/agent-runtimes.md`
- `agents/skills/agterm/cookbook.md`
- `agents/skills/agterm/examples.md`
- `agents/skills/agterm/reference-appearance.md`
- `agents/skills/agterm/reference-connection.md`
- `agents/skills/agterm/reference-layout.md`
- `agents/skills/agterm/reference-restore.md`
- `agents/skills/agterm/reference-session.md`
- `agents/skills/agterm/reference-windows.md`
- `agents/skills/agterm/reference.md`
- `agents/skills/agterm/troubleshooting.md`
- `agents/skills/doc-hierarchy/company-decisions.md`
- `agents/skills/doc-hierarchy/content-ownership.md`
- `agents/skills/doc-hierarchy/instruction-templates.md`
- `agents/skills/doc-hierarchy/migration-map.md`
- `agents/skills/doing-code-review/general.md`
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/kotlin-spring.md`
- `agents/skills/doing-code-review/python.md`
- `agents/skills/domain-modeling/adr-format.md`
- `agents/skills/domain-modeling/glossary-format.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/archive-and-cleanup.md`
- `agents/skills/execute-plan/implementation-loop.md`
- `agents/skills/execute-plan/invocation-and-orchestration.md`
- `agents/skills/execute-plan/launch-rules-and-gates.md`
- `agents/skills/execute-plan/phase-3-review.md`
- `agents/skills/execute-plan/recovery-and-integration.md`
- `agents/skills/execute-plan/run-setup.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/graphify/references/add-watch.md`
- `agents/skills/graphify/references/exports.md`
- `agents/skills/graphify/references/extraction-spec.md`
- `agents/skills/graphify/references/github-and-merge.md`
- `agents/skills/graphify/references/hooks.md`
- `agents/skills/graphify/references/query.md`
- `agents/skills/graphify/references/transcribe.md`
- `agents/skills/graphify/references/update.md`
- `agents/skills/how-to-write-skills/references/frontmatter-guide.md`

- [x] Audit the assigned supporting Markdown files for authored English prose, examples, templates, and output contracts. Update applicable text to follow the canonical policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve technical meaning, exact technical strings, user-provided text, and established workflow behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep full policy text in its canonical source. Use concise references only where an owning document needs a pointer. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep each changed skill file within its byte cap. Remove equivalent bytes in the same change when needed. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: apply ASD-STE100 to supporting skill docs` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Convert the remaining supporting documents and review the corpus

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/OUTCOME_CONTRACT.md`
- `agents/skills/how-to-write-skills/references/progressive-disclosure.md`
- `agents/skills/how-to-write-skills/references/skill-design-principles.md`
- `agents/skills/how-to-write-skills/references/skill-design-vocabulary.md`
- `agents/skills/how-to-write-skills/references/skill-sizes.md`
- `agents/skills/how-to-write-skills/references/skill-structure.md`
- `agents/skills/learn/step-1-extract.md`
- `agents/skills/learn/step-2-placement.md`
- `agents/skills/learn/step-6-instruction-updates.md`
- `agents/skills/learn/step-completion.md`
- `agents/skills/maintenance/CHANGELOG.md`
- `agents/skills/maintenance/codex.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/duties-core.md`
- `agents/skills/maintenance/failure-cap.md`
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/template-unblock.md`
- `agents/skills/maintenance/templates-CHANGELOG.md`
- `agents/skills/maintenance/zcode-context-audit.md`
- `agents/skills/maintenance/zcode-dispatch-ladder.md`
- `agents/skills/maintenance/zcode-primitive-verification.md`
- `agents/skills/maintenance/zcode-quota-effort.md`
- `agents/skills/maintenance/zcode-recurring-recipe.md`
- `agents/skills/maintenance/zcode-scheduling-primitives.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/plans/budget-gate.md`
- `agents/skills/plans/handoff-and-done.md`
- `agents/skills/plans/integration-points.md`
- `agents/skills/plans/phase-0-placement.md`
- `agents/skills/plans/phase-1-requirements.md`
- `agents/skills/plans/plan-format.md`
- `agents/skills/plans/plan-lifecycle.md`
- `agents/skills/plans/plan-quality-gate.md`
- `agents/skills/plans/task-design.md`
- `agents/skills/plans/universal-patterns.md`
- `agents/skills/plans/validation-authoring-rules.md`
- `agents/skills/review-agents/architecture.md`
- `agents/skills/review-agents/concurrency.md`
- `agents/skills/review-agents/consistency.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/implementation.md`
- `agents/skills/review-agents/premortem.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/security.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/review-agents/simplification.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/rfc-design/references/contract-blueprint-example.md`
- `agents/skills/rfc-design/references/eval-cases.md`
- `agents/skills/rfc-design/references/rfc-sections.md`
- `agents/skills/tdd-guide/java-kotlin.md`
- `agents/skills/tdd-guide/python.md`
- `agents/skills/unit-test-runner/maven.md`

- [x] Audit the assigned supporting Markdown files and `scripts/OUTCOME_CONTRACT.md` for authored English prose, examples, templates, and output contracts. Update applicable text to follow the canonical policy while preserving machine-readable outcome names, fields, and required exact strings. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the outcome tokens, final `OUTCOME:` line syntax, exit-code meanings, and machine-readable field names in `scripts/OUTCOME_CONTRACT.md`; verify that prose edits do not change these contract values. [class: IMPLEMENTATION_REQUIRED]
- [x] Review a representative sample across short skills, dense workflows, supporting modules, templates, and structured reports. Record the sample selection and any intentional exception in the review record. [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the full 170-file inventory was covered, the policy has one canonical owner, and no unsupported dedicated skill or blocking checker was added. [class: IMPLEMENTATION_REQUIRED]
- [x] Run all commands in `## Validation Commands` and resolve failures within this plan's scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the existing panel policy for the complete corpus diff. Resolve blocking findings and record accepted exceptions with evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: complete ASD-STE100 skill corpus review` [class: IMPLEMENTATION_REQUIRED]

Official source: [ASD-STE100 Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf); [About STE](https://www.asd-ste100.org/about_STE.html).

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-16-asd-ste100-codex-canonical-policy-and-skill-corpus.md`: completed by this plan. The canonical policy and shared Codex skill corpus work landed; the former origin is deleted in this completion pass. Claude and ZCode runtime adoption origins remain open under their own backlog records.
