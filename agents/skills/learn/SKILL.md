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
- Facts document: a local-only file providing **machine- and environment-specific** values (paths, accounts, domains, repo path keys). **Not** for portable workflow policy, numeric thresholds, or skill behavior; those belong in the owning skill's `SKILL.md`. This skill reads facts keys for path resolution, see `user_facts_path` and repo `repo_facts_rel`.

## When to Use
Use this skill when asked to:
- learn from communication in the current task,
- capture recurring mistakes/corrections,
- update repository docs or instruction rules from lessons learned,
- consolidate duplicated documentation.

Keep this skill scoped to documentation/instruction corpus updates. Do not use it to trigger product code or contract refactors. Commit boundary: `learn` commits only its own learn-authored artifacts (Step 1.8 skills-repo artifacts and the skill-placement commit workflow, plus each Step 1.9 off-tree backlog row in its destination checkout); the parent owns the intermediate boundary's plain commit in the run checkout, and the `done` skill owns the closeout's commits, except the docs-branch skill's orphan-branch commits (done may stage artifacts in the failed-capture set, after asking; defined in done Step 4). Learn is invoked outside `done` at every intermediate boundary and by done Step 1 only at the final closeout. Before each corpus write, re-read the destination file and re-apply the placement against its fresh state; the project-corpus `#N` lesson number is derived in that same fresh read as the maximum existing `## N.` heading number plus one, never from a number read earlier in the session; when a parallel learn run wrote first, retry once on the re-read content before reporting the drift as a manual follow-up.

**Writing project lessons corpus:** Before each Write/Edit to the repo's project lessons file (`docs/maintenance/development_lessons.md`), refresh the skill-gate learn marker per `ai-playbook/agents/hooks/skill-gate/README.md` (learn class WRITE RECIPE: derive `project` and `session` per Terms, invoke the shared `session_channel.py` subprocess VERBATIM, then `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker learn --session-id "$SID"`). Run this on EVERY project-corpus write (create AND update). FAIL-LOUD if the marker write fails. Do NOT inline path/body/window constants here; the README is the single source (Family D).

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

### Repeated failures and mechanical invariants

When the same class of failure appears more than once, do not only restate prompt advice. Ask which harness component is missing (instruction, source of truth, tool, validator, permission rule, eval, or recovery path), then encode the fix at the right scope. Prefer mechanical checks (lint rules, schema validators, hooks, regression evals) when the rule is enforceable without judgment. For the general harness pattern, see `agents-best-practices/references/agent-legibility-feedback-loops.md`.

## Module dispatch (the router contract)

The learn run's operative step text lives in per-concern modules beside this router; each dispatch entry below is the one-paragraph contract plus the module pointer, and the run loads the named module's whole text before executing that step (load-on-dispatch: a clean run's read set is this router plus the in-flight step modules, never the full pre-split body). No rule is restated here; each module's headings are byte-verbatim and its bodies are the moved originals (plan docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md Task 5). Execute the steps in the run order the Goal section states; the dispatch list below is the ordered step list of record, Step 1 through the Completion Checklist.

- **Step 1: Extract Lessons (with Steps 1.5 through 1.9)** - load `agents/skills/learn/step-1-extract.md` (the `## Step 1: Extract Lessons` heading with the lesson inventory and classification, the correction ledger, the source-check self-audit, the Generalization pass, the premature-dismissal anti-pattern, plus the `## Step 1.5: Ralphex Execution Log Analysis (when available)`, `## Step 1.6: Internet Research Capture`, `## Step 1.7: Proper-Noun Justification Review (required before any lesson is written)`, `## Step 1.8: Skill-usage issue capture` headings with the backlog-item and skills-repo commit workflow, and the `## Step 1.9: Project issue backlog capture` heading with the related-project routing, dedupe, create, commit, and investigate-invocation workflow) when capture starts, before any corpus write.
- **Steps 2 through 5: placement** - load `agents/skills/learn/step-2-placement.md` (the `## Step 2: Placement Rules` heading with the fork-4 project-corpus existence check, the guideline file roles, the facts-vs-skill split, and the destination scopes, `## Step 3: LLM Rule Qualification Gate`, `## Step 4: Documentation Consolidation`, `## Step 4.5: Add Cross-References for Lesson Discoverability`, and `## Step 5: Module Layout and Skill Workflow Lessons` with the skill-output improvement arm) after extraction.
- **Steps 6, 6.5, 6.6, and 7: instruction updates and gates** - load `agents/skills/learn/step-6-instruction-updates.md` (the `## Step 6: Instruction File Updates` heading with the instruction placement ladder and the consolidation and compaction passes, `## Step 6.5: Instruction size gate (required before finishing learn)`, `## Step 6.6: Corpus gates (required before finishing learn)` with the user-level lessons-corpus script gate and the lesson concision gate, and `## Step 7: API Contract Naming Hygiene`) after placement, before finishing.
- **Completion checklist** - load `agents/skills/learn/step-completion.md` (the `## Completion Checklist` heading with the before-finishing verification list) before reporting the run finished.

## Integration Points

### With `bootstrap-ai-playbook` skill
Writes and refreshes `.ai-playbook/facts.md` when Terms triggers fire (`using-skills` Step 0). This skill reads documentation path keys from that file during lesson placement.

### With `agents-best-practices` skill (provider)
`learn` is the operational feedback loop for this playbook: it turns recurring failures into durable docs, enforceable rules, and mechanical checks. `agents-best-practices/references/agent-legibility-feedback-loops.md` describes the general harness pattern (source-of-truth artifacts, validators, garbage collection). When auditing or designing a harness, read that reference; when a concrete failure occurred in this session, run `learn`.

### With `done` skill
At intermediate boundaries the light boundary's parent invokes `learn` outside `done`, after the boundary's plain commit; learn's skills-repo commits, its off-tree row commits, and the investigate entry receipts land before the boundary's manifest row. `done` Step 1 invokes `learn` only at the final closeout; learn's skills-repo commit (Step 1.8 backlog items and the skill-placement commit workflow) lands during that step, before any `done` commit step. `done` Step 4 keeps only the non-learn fallback for remaining skills-repo changes.

### With `execute-plan` skill
Consumer at every intermediate boundary: the parent-owned light boundary (execute-plan Step 1.4 per task, Step 3.4 per review iteration) invokes learn after the boundary's plain commit, over the boundary's implement and review logs (the same set under both placements); learn's placement, scope, and dedupe rules govern what the invocation lands, and its Step 1.9 row paths and commit receipts feed the boundary's `task_boundary:` manifest row. The boundary procedure is owned by execute-plan's Light boundary section; this entry references it and never restates it.

### With `investigate` skill
Consumer. When Step 1.9 created or updated rows, learn invokes investigate anchored on them within the same learn run; investigate's stages, verdict routing, boundary, and hard gates apply unchanged, and its same-turn entry commit lands where the anchored rows live (in the destination checkout for off-tree rows, so the entry lands in that project's own logs; foreign-data redaction applies).

### With `maintenance` skill
Bidirectional. Consumer side (maintenance): the loop's per-cycle harvest duty (maintenance SKILL.md Step 3) invokes learn once per completed cycle under a live standing directive, over the cycle's session logs and outputs; learn's own placement, scope, and duplicate-refusal rules govern what lands - the duty invokes the skill and never restates them. Producer side (learn): lessons harvested by the harvest duty follow learn's normal placement rules, and learn records nothing about the loop itself.

### With `receiving-review` skill
`receiving-review`'s "Backlog capture for valid findings not fixed in scope" is the shape provider for Step 1.8's backlog items and, project-side, for Step 1.9's related-project rows. The source relation: Step 1.8's skills-corpus source is disjoint from `receiving-review`'s review-finding source; Step 1.9's project-issue source can overlap it, filing in the same destination home when the related project is the current checkout, and Step 1.9's dedupe-against-the-destination-home rule governs that overlap. Neither source owns another's home.

### With `review-loop` skill
Consumer at every round boundary: review-loop's step 4 runs the same light boundary (plain commit, then learn, then the record mirror; the procedure is execute-plan's Light boundary section, referenced not restated), invoking learn after the boundary's plain commit; the same capture contract applies.
