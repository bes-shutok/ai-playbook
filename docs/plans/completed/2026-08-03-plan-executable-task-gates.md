# Plan: Executable plan-task gates (keep non-local work out of checklists)

Motivating incident (historical, do not edit): a completed feature plan that put staging deploy, cross-ticket rollout, and live shared-environment probes on the implementation checklist. Root failure was **authoring**, not checkbox marking.

Plan review: `docs/reviews/2026-08-03-plan-review-plan-executable-task-gates-r5.md` (r5, ready=yes)

## Terms

| Term | Meaning |
|------|---------|
| Executable plan task | Checklist item the default executor can finish now from the target repo and local tooling |
| Repository implementation | Work that lives in the target repo and local tooling; the only class that becomes checklist items by default (source of executable plan tasks) |
| External prerequisite | Work owned outside the current repo or ticket that must exist before a Ship-when condition |
| Release gate | Ship-when condition needing deployed or cross-team evidence; prose only unless the user confirms an exception **and** the plan records a **why executable now** line |
| Done when | Executable success criteria for the implementation phase |
| Ship when | Narrative release dependencies; no checkboxes; optional Jira only after user confirms ticket creation |
| Completed history artifact | Finished plan under `{plans_completed_dir}`, completed review digest, or non-mirror `docs/history/context/` (legacy `docs/context/`) |

Canonical definitions: `docs/maintenance/glossary.md`. Immutability policy: `docs/maintenance/project-decisions.md` ADR-0001.

## Gist & Examples

Implementation plans today encourage a **Release gates** list under Evaluation Criteria and freely mix those bullets into `### Task N` checklists. Agents then treat staging deploys, other teams' tickets, and unavailable environments as work to execute (or to mark skipped with `[x]`).

This change makes **authoring** the primary control:

1. Classify every proposed checklist candidate as **repository implementation**, **external prerequisite**, or **release gate**.
2. Only **repository implementation** may become `- [ ]` items by default.
3. Any exception (human PR merge, this-service-only deploy the user can run now, etc.) requires an **explicit user confirm** before it enters the checklist, plus a one-line **why executable now** written in the plan (env available, owner present). Bare "user said yes" is not enough; reject vacuous why-lines.
4. Evaluation Criteria split into **Done when** (executable) and **Ship when** (narrative). Ship when must not generate tasks without that exception confirm.
5. Non-executable dependencies may be tracked in Jira only after the user confirms ticket creation (never auto-create).
6. `review-plan` flags checklist items that fail the inclusion test. `execute-plan` pauses as a hard gate before implementing such an item (move into Ship when prose in the plan, write exception + **why executable now** into the plan, or stop).
7. Completed history artifacts stay immutable (ADR-0001). Confluence mirrors under `docs/history/context/confluence/` may still sync. Do not copy rollout checklist shapes from completed plans when authoring new ones.

**Inclusion allow/deny examples (required in `plans` skill text):**

| Candidate | Class | Checklist? |
|-----------|-------|------------|
| Add `app/src/test/k6/user-batches.js` and unit/IT coverage | repository implementation | Yes |
| Document Ship-when dependencies in ops docs | repository implementation | Yes |
| Deploy final commit to staging and prove p95 | release gate | No (Ship when) |
| Verify another ticket's service is deployed and probe it | external prerequisite | No (Ship when) |
| Open PR / request human review on this branch | exception only after user confirm + **why executable now** line in the plan | Only if confirmed |

**Why executable now examples (required beside the exception rule):**

| Why line | Accept? |
|----------|---------|
| Staging context `<env-alias>` reachable from this laptop; deploy script is in-repo (placeholders only in skill examples) | Yes |
| User said yes | No (vacuous) |

**Before / after (authoring):**

- Before: Task checklist includes "Deploy to staging and prove p95" and "Verify other-ticket reconciliation is deployed."
- After: Checklist may include "Add the local load-test script" and "Document Ship-when dependencies in ops docs." Staging run and other-ticket deploy stay under **Ship when** as prose (optional Jira only if the user confirms create).

**Before / after (execute-plan):**

- Before: implement sub-agent tries staging work or the user says skip and items become `[x]`.
- After: orchestrator stops, states why the item fails the inclusion test, and takes only an allowed hard-gate outcome (below). Silent skip-`[x]` for inclusion failures is forbidden.

### Design Invariants (CR Guard)

- **Authoring is the primary fix.** Review and execute-plan are backstops, not the main control.
- **No archival hard-block** for `[x]`-as-skip. Keep bad tasks out; do not police skip marks after the fact.
- **Do not edit completed history artifacts** to "clarify" process outcomes (ADR-0001).
- **Public skills stay tool-agnostic and org-neutral.** Use placeholders; no company ticket IDs, env hostnames, or personal paths in skill examples.
- **`claude/skills` is a symlink** to `agents/skills`; edit only under `agents/skills/`.
- **execute-plan pause for inclusion failure is a hard gate**, compatible with "do not ask between steps" (pause only on hard gates). Allowed outcomes only: (a) if `**Ship when:**` is missing, create it (or rename narrative Release gates content into Ship when), then move the item into **Ship when** as explicit prose, remove it from the checklist, and continue (forbid delete-without-Ship-when and delete-only when the heading cannot be resolved), (b) interactive exception confirm, then write exception + **why executable now** into the plan file before continue (this is the only inclusion outcome that asks the user), (c) stop the run with a recorded hard-gate reason. Never silent skip-`[x]`. Inclusion-check failure is a pause, not by itself a mandatory ask (do not dump it onto the Hard Gate 17 ask-only list).

## Evaluation Criteria

**Quality dimensions (Done when):**
- Correctness: `plans` refuses to add external prerequisite / release gate items as checkboxes without user-confirmed exception plus **why executable now** written in the plan; Evaluation Criteria template uses Done when / Ship when (including Universal Patterns and Plan Format Rules); allow/deny example table present.
- Backstop coverage: `review-plan` (via consistency ownership in `review-panel-selection.md`) and `execute-plan` (Phase 1 hard gate with taxonomy inclusion check and explicit pause outcomes) both name the inclusion test.
- Consistency: glossary terms and ADR-0001 match skill language (including Repository implementation); Integration Points updated in both directions; no leftover wording that turns Release gates into checklist tasks.
- Hygiene: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.

**Ship when:**
- None for this playbook change (skills and docs only; no deploy).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill / guideline Markdown):**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/documentation.md` *(optional one-line xref only)*
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`
- `README.md`

**Tests:**
- *(none; doc/skill edits; validation is grep + hygiene scan)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Any file under `docs/plans/completed/` or other repos' `{plans_completed_dir}/`; immutable completed history (ADR-0001).
- `agents/skills/done/SKILL.md`; no archival hard-block in this plan.
- Company guidelines master; thin pointer lives in shared `agent_workflow_guidelines.md` only.
- Company project guidelines or product feature plans; prevention is skill-level.
- Dual Cursor+Claude skill-gate marker cwd mismatch (session incident); monitor / separate follow-up, not this plan's tasks.

## Validation Commands

```bash
set -euo pipefail

# Inclusion / Done when / Ship when present in plans (discriminating phrases)
plans_rules="$(awk '/^\*\*Rules:\*\*/{on=1} /^## Documentation Impact Assessment/{on=0} on' agents/skills/plans/SKILL.md)"
printf '%s\n' "$plans_rules" | grep -F '**Checklist inclusion gate:**'
printf '%s\n' "$plans_rules" | grep -F 'Only repository implementation becomes an **executable plan task**'
printf '%s\n' "$plans_rules" | grep -F 'Put external prerequisites and release conditions under **Ship when** as prose'
printf '%s\n' "$plans_rules" | grep -F 'exception confirmed by user:'
printf '%s\n' "$plans_rules" | grep -F 'why executable now:'
printf '%s\n' "$plans_rules" | grep -F 'completion evidence:'

# Plan-format Evaluation Criteria uses BOTH Done when and Ship when headings
grep -nE '\*\*Done when:\*\*' agents/skills/plans/SKILL.md
grep -nE '\*\*Ship when:\*\*' agents/skills/plans/SKILL.md

# Allow/deny table, anti-copy, and non-vacuous why examples (separate positives)
grep -nF 'allow/deny' agents/skills/plans/SKILL.md
grep -nF 'do not copy' agents/skills/plans/SKILL.md
grep -nF 'Checklist inclusion' agents/skills/plans/SKILL.md
grep -nF 'repository implementation' agents/skills/plans/SKILL.md
grep -nF 'external prerequisite' agents/skills/plans/SKILL.md
grep -nF 'why executable now' agents/skills/plans/SKILL.md
grep -nEi 'user said yes' agents/skills/plans/SKILL.md
# Skill examples stay placeholder-only (no org env aliases)
if grep -nE 'dev-crm' agents/skills/plans/SKILL.md; then
  echo 'organization-specific environment alias remains'
  exit 1
fi

# Exception phrase present in EACH skill (per-file; any-one-file is not enough)
grep -nF 'why executable now' agents/skills/plans/SKILL.md
grep -nF 'why executable now' agents/skills/review-plan/SKILL.md
grep -nF 'why executable now' agents/skills/execute-plan/SKILL.md

# review-plan + mandatory consistency home: inclusion present AND blocking severity
review_backstop="$(awk '/^[0-9]+\. \*\*Checklist inclusion backstop\*\*/{on=1} /^### Worker bundles/{on=0} on' agents/skills/review-plan/SKILL.md)"
printf '%s\n' "$review_backstop" | grep -F 'blocking plan defect'
printf '%s\n' "$review_backstop" | grep -F '`exception confirmed by user` receipt'
printf '%s\n' "$review_backstop" | grep -F '`completion evidence`'
consistency_gate="$(awk '/^### Plan and RFC `consistency` ownership/{on=1} /^\*\*Do not report:\*\*/{on=0} on' agents/skills/review-agents/review-panel-selection.md)"
printf '%s\n' "$consistency_gate" | grep -F 'blocking plan defect'
printf '%s\n' "$consistency_gate" | grep -F '`exception confirmed by user` receipt'
printf '%s\n' "$consistency_gate" | grep -F '`completion evidence`'

# execute-plan hard gate + silent skip + outcome (a) durability
execute_gate="$(awk '/^### Inclusion Hard Gate/{on=1} /^### Step 1.2:/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$execute_gate" | grep -F 'Move to Ship when'
printf '%s\n' "$execute_gate" | grep -F 'delete-without-Ship-when'
printf '%s\n' "$execute_gate" | grep -F 'silent skip'
printf '%s\n' "$execute_gate" | grep -F '`exception confirmed by user` receipt'
printf '%s\n' "$execute_gate" | grep -F '`completion evidence`'
printf '%s\n' "$execute_gate" | grep -F 'do **not** open interactive exception confirmation'
printf '%s\n' "$execute_gate" | grep -F 'Do **not** require repository-local completion proof to leave fail-closed'
printf '%s\n' "$execute_gate" | grep -F 'Outcome 2 is available only after affirmative release-gate classification'
printf '%s\n' "$execute_gate" | grep -F 'Phase 1 (before Step 1.2)'
printf '%s\n' "$execute_gate" | grep -F 'including already `[x]` lines'
printf '%s\n' "$execute_gate" | grep -F 'Ask the user whether this item is exceptionally executable now'
printf '%s\n' "$execute_gate" | grep -Ei 'create.*Ship when|rename.*Release gates'
# Recovery re-gate + ask-then-write
recovery_block="$(awk '/^## Recovery:/{on=1} /^## Integration Points/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$recovery_block" | grep -F 'including already `[x]`'
printf '%s\n' "$recovery_block" | grep -F 'Self-written receipts without that ask are forbidden'
printf '%s\n' "$recovery_block" | grep -F 'do **not** open interactive exception'
execute_exit="$(awk '/^\*\*Exit criteria \(sub-agent must satisfy before returning\):\*\*/{on=1} /^If the sub-agent reports failure/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$execute_exit" | grep -F 'verify the named `completion evidence`'
printf '%s\n' "$execute_exit" | grep -F 'keep the clause unchecked and stop'
# Implement refuse for non-admissible
grep -nF 'Refuse and return `blocked`' agents/skills/execute-plan/subagent-prompts.md
# Pause enumerations: Continuous execution + Step 1.5 + dedicated Inclusion Hard Gate
# (do NOT require inclusion-check failure on Hard Gate 17 ask-only list)
grep -nE 'Pause only on hard gates.*inclusion-check failure|Pause only on hard gates.*inclusion check failure' agents/skills/execute-plan/SKILL.md
grep -nE 'Only stop between tasks when' -A20 agents/skills/execute-plan/SKILL.md | grep -nE 'inclusion-check failure|inclusion check failure'
grep -nE 'Inclusion.*(hard gate|Hard Gate)|inclusion-check failure' agents/skills/execute-plan/SKILL.md
# HG17 ask-only list must NOT treat bare inclusion as mandatory ask
if grep -nE 'Ask the user only on.*inclusion-check failure|Ask the user only on.*inclusion check failure' agents/skills/execute-plan/SKILL.md; then
  echo 'bare inclusion failure remains on ask-only list'
  exit 1
fi

# Workflow guideline §62 pointer
grep -nE '^## 62\.' projects/.ai-playbook/agent_workflow_guidelines.md
grep -nE 'executable plan task|Ship when|Done when' projects/.ai-playbook/agent_workflow_guidelines.md

# Glossary + ADR: per-term positives (OR is not enough)
grep -nF 'Executable plan task' docs/maintenance/glossary.md
grep -nF 'Repository implementation' docs/maintenance/glossary.md
grep -nF 'External prerequisite' docs/maintenance/glossary.md
grep -nF 'Release gate' docs/maintenance/glossary.md
grep -nF 'Done when' docs/maintenance/glossary.md
grep -nF 'Ship when' docs/maintenance/glossary.md
grep -nF 'Completed history artifact' docs/maintenance/glossary.md
grep -nF 'why executable now' docs/maintenance/glossary.md
grep -n 'ADR-0001' docs/maintenance/project-decisions.md

# README: inclusion note on catalog lines for each skill
grep -nE 'plans' README.md | grep -nEi 'inclusion|Ship when|executable plan task'
grep -nE 'review-plan' README.md | grep -nEi 'inclusion|Ship when|executable plan task|feasibility'
grep -nE 'execute-plan' README.md | grep -nEi 'inclusion|Ship when|executable plan task'

# Jira / ticket tracking never auto-creates without confirm
grep -nEi 'auto-create|user confirms ticket|never auto-create' agents/skills/plans/SKILL.md

# Integration Points: inclusion-gate wiring (provider/consumers).
# Require inclusion language AND peer skill name (do not OR names with inclusion).
grep -nE '## Integration Points' -A40 agents/skills/plans/SKILL.md | grep -nE 'inclusion|why executable now|Checklist inclusion'
grep -nE '## Integration Points' -A40 agents/skills/plans/SKILL.md | grep -nE 'review-plan'
grep -nE '## Integration Points' -A40 agents/skills/plans/SKILL.md | grep -nE 'execute-plan'
grep -nE '## Integration Points' -A40 agents/skills/review-plan/SKILL.md | grep -nE 'inclusion|why executable now|Checklist inclusion'
grep -nE '## Integration Points' -A40 agents/skills/review-plan/SKILL.md | grep -nE 'plans'
grep -nE '## Integration Points' -A40 agents/skills/execute-plan/SKILL.md | grep -nE 'inclusion|why executable now|Checklist inclusion'
grep -nE '## Integration Points' -A40 agents/skills/execute-plan/SKILL.md | grep -nE 'plans'

# No instruction to edit completed plans as process reinterpretation
if grep -nE 'annotate completed|rewrite Task|clarify the archive' \
  agents/skills/plans/SKILL.md agents/skills/execute-plan/SKILL.md agents/skills/review-plan/SKILL.md; then
  echo 'completed-plan reinterpretation instruction remains'
  exit 1
fi

# No leftover "release gates become checklist tasks" authoring instruction
# Narrow imperative leftovers only; do not match Integration Points exception prose
# that legitimately pairs Checklist inclusion gate with release-gate exceptions.
if grep -nEi 'release gates?.*(must|should|become|turn).*(checkbox|checklist)|turn.*release gates?.*into.*(checkbox|checklist)|expand.*release gates?.*into.*(task|checkbox|checklist)' \
  agents/skills/plans/SKILL.md; then
  echo 'release-gates-as-checklist instruction remains'
  exit 1
fi

# Anti-pattern Recovery already-[x] pin (skim surface)
antipattern_row="$(awk '/Silently execute or skip-mark non-executable/{print; exit}' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$antipattern_row" | grep -F 'again in Recovery'
printf '%s\n' "$antipattern_row" | grep -F 'including already `[x]`'

# execute-plan rejects vacuous why on interactive exception write
execute_gate="$(awk '/^### Inclusion Hard Gate/{on=1} /^### Step 1.2:/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$execute_gate" | grep -F 'Reject vacuous why-lines'
printf '%s\n' "$execute_gate" | grep -F 'why executable now: user said yes'
recovery_block="$(awk '/^## Recovery:/{on=1} /^## Integration Points/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$recovery_block" | grep -F 'Reject vacuous why-lines'

# execute-plan IP Recovery already-[x] pin
ip_block="$(awk '/^## Integration Points/{on=1} /^### Consumes `tdd-guide`/{on=0} on' agents/skills/execute-plan/SKILL.md)"
printf '%s\n' "$ip_block" | grep -F 'including already `[x]`'

# Interview / skeleton no longer solicit Release gates as plan-owned section
if grep -nF 'What are the release gates?' agents/skills/plans/SKILL.md; then exit 1; fi
if grep -nE '^\*\*Release gates:\*\*' agents/skills/plans/SKILL.md; then exit 1; fi

# Universal Patterns / Plan Format Rules no longer teach undifferentiated release gates
if grep -nEi 'quality dimensions and release gates' agents/skills/plans/SKILL.md; then exit 1; fi
if grep -nEi 'release gates \(what must pass' agents/skills/plans/SKILL.md; then exit 1; fi

# Public-hygiene gate
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: Authoring gates in `plans`

Files:
- `agents/skills/plans/SKILL.md`
- `docs/maintenance/glossary.md`
- `docs/maintenance/project-decisions.md`

- [x] Add a **Checklist inclusion gate** (Phase 1 / plan format rules): every proposed checklist candidate is classified as repository implementation, external prerequisite, or release gate. Only repository implementation becomes `- [ ]` by default. Exceptions require asking the user, an explicit confirm, and a one-line **why executable now** recorded beside the task (canonical spaced phrase; write it into the plan file, not chat-only). Include one acceptable why-line example and one reject ("user said yes").
- [x] Include a short **allow/deny example table** in the skill (local script/docs/tests = in; staging deploy / other-ticket probe = Ship when; human PR merge = exception-only). Skill examples must use placeholders only (no org env aliases such as `dev-crm`).
- [x] Add an anti-pattern: do not copy rollout checklist shapes from completed plans; completed history is immutable context, not a template for Ship-when work.
- [x] Replace Evaluation Criteria template language that treats **Release gates** as plan-owned ship criteria with **Done when** / **Ship when**. Update Phase 1.3 interview prompts (remove `What are the release gates?`), the confirmation template, the plan-format skeleton (**both** `**Done when:**` and `**Ship when:**` headings, not `**Release gates:**`), Plan Format Rules (~"quality dimensions and release gates"), Universal Patterns (~"release gates (what must pass…)"), and any wording that expands release gates into tasks.
- [x] State that optional Jira (or equivalent) tracking for Ship when items is allowed only after the user confirms ticket creation; never auto-create.
- [x] If `docs/maintenance/glossary.md` or ADR-0001 in `docs/maintenance/project-decisions.md` is missing, create from the Terms table (including **Repository implementation** and exception + **why executable now** on Release gate). Otherwise verify they match Terms and tighten only on drift. Commit them with this task.
- [x] Update Integration Points: document consumers `review-plan` and `execute-plan` for the inclusion gate.
- [x] Run → expect: Validation Commands greps for `plans/SKILL.md`, glossary/ADR, Release-gates interview/skeleton/Universal Patterns negatives, and both Done when / Ship when heading positives succeed.
- [x] Commit: `plans: gate checklist items to executable work; Done when vs Ship when`

### Task 2: Feasibility backstop in `review-plan` and consistency ownership

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/documentation.md` *(optional one-line xref only)*

- [x] Instruct `review-plan` (orchestrator and/or Step 2 worker brief) to treat checklist items that fail the inclusion test as **blocking** plan defects unless the plan records a user-confirmed exception **with** a **why executable now** line written in the plan.
- [x] Extend Plan/RFC `consistency` ownership in `review-panel-selection.md` as the **mandatory** home for inclusion-test bullets. Touch `documentation.md` only for a one-line cross-reference if needed; do not treat `documentation.md` as the primary checklist. Workers must flag: checkbox that is an external prerequisite or release gate; Ship when content smuggled into Tasks; Done when / Ship when section missing or collapsed into old Release-gates-as-tasks shape; bare "user confirmed" exception without **why executable now**.
- [x] Add Integration Point with `plans` (provider of the inclusion rule).
- [x] Run → expect: per-file greps hit `review-plan/SKILL.md` and `review-panel-selection.md` (documentation.md is not a positive gate).
- [x] Commit: `review-plan: flag non-executable checklist items as blocking`

### Task 3: execute-plan hard gate before non-executable tasks

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Before Step 1.2 (implement launch) for the selected task, require an **inclusion check** that applies the plans Checklist inclusion gate taxonomy on every unchecked item: pause as a hard gate unless the item is classified as repository implementation (default source of executable plan tasks), or the plan already records user-confirmed exception plus **why executable now**. Cover exception-class items (e.g. human PR merge) and bare-confirm-without-why, not only unavailable shared env / other-team deploy / non-local evidence symptoms.
- [x] Spell **allowed pause outcomes** only: (a) if `**Ship when:**` is missing, create it (or rename narrative Release gates content into Ship when), then move the item into **Ship when** as explicit prose, remove from checklist, continue (forbid delete-without-Ship-when and delete-only when the heading cannot be resolved), (b) interactive exception confirm, then write the exception + **why executable now** line into the plan file before continue (chat-only confirm is not enough; this is the only inclusion outcome that asks the user), (c) stop the run with a recorded hard-gate reason. Explicitly forbid silent skip-`[x]` for inclusion failures.
- [x] Add a dedicated **Inclusion Hard Gate** entry that spells outcomes (a)/(b)/(c). Also update Continuous execution (`Pause only on hard gates (...)`) and Step 1.5 stop list so each names `inclusion-check failure`. Do **not** put bare `inclusion-check failure` on Hard Gate 17's Ask-only list; near HG17 clarify that inclusion pause is not by itself a mandatory ask (ask only for outcome b).
- [x] Add the gate to the anti-patterns table (do not silently execute or skip-mark non-executable rollout work).
- [x] Update Integration Points with `plans` (consumes inclusion rule); IP section must mention inclusion / why executable now.
- [x] Run → expect: execute-plan greps for inclusion, silent skip, why executable now, delete-without-Ship-when, create/rename Ship when, Continuous execution + Step 1.5 + Inclusion Hard Gate anchors succeed; HG17 ask-only negative succeeds.
- [x] Commit: `execute-plan: hard-gate non-executable checklist items before implement`

### Task 4: Thin workflow guideline + catalog pointer + closure

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `README.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] Append **§62** (next free number after §61) to `agent_workflow_guidelines.md` as heading `## 62. ...`: short rule that implementation-plan checklists hold executable plan tasks only; Ship when stays narrative; exceptions and optional Jira need user confirm; point to `plans` / `review-plan` / `execute-plan` for procedure; point to ADR-0001 for completed-history immutability. Do not duplicate the full skill procedure.
- [x] Update the `plans` row in `README.md` catalog and ensure `review-plan` / `execute-plan` are indexed (or clearly linked) with a one-line note on the inclusion gate on those index lines; do not hedge with "if those rows exist" when the catalog already lists them.
- [x] Re-read bidirectional Integration Points across the three skills; each IP section must mention inclusion / why executable now and the provider/consumer link; fix any one-sided reference.
- [x] Run all commands in `## Validation Commands`; expect success.
- [x] Commit: `workflow: add executable plan-task gate pointer (§62)`
