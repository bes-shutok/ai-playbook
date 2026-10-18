# Plan: execute-plan pays only for the done boundaries that need a worker

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-done-commit-batching.md`
- `docs/history/backlog/2026-10-05-execution-design-review-early-lens.md`

Driving force: efficiency and token usage (two witnessed 2026-10-05 findings from the same execution retrospective, landing 9d6cdc75: nine per-task done sub-agents each spent two to six minutes and roughly 300k tokens to produce a one-file commit the parent had already verified minutes earlier, about 35 minutes and 2.5M tokens recurring on every multi-task execution; and the run's only architecture-level adversarial review fired in Phase 3 at hour 13, after every consumer task had been built on the core mechanism, so two blocking architectural findings cost a 17M-token six-file fold that a task-2-local fold would have capped at an order of magnitude less)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-execute-plan-execution-cost-boundaries-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Done delta: the working-tree change a task's done boundary commits: the implement work plus the task's Step 1.3 checkbox flips in the plan file.
- Checkbox-flip-only delta: a done delta whose plan-file diff classifies checkbox-flip-only (the runtime's own marker-only classifier, `execute_plan_runtime._diff_is_checkbox_marker_only`, imported never re-implemented) and whose flipped boxes all sit inside the completed task's section span of the plan text.
- Fast-path done: the parent-side scripted done sequence this plan adds for a checkbox-flip-only delta: the done lock, the sensitive-data scan, the docs-branch sync when owed, per-task learn capture with the implement log, the scripted verification conditions, the commit (or the driver's done handoff receipt under a machine manifest) with explicit pathspec, and the manifest row, all without spawning a done sub-agent and with the enforcement layer amended to name the fast path as the sanctioned arm.
- Scripted verification conditions: the fast path runs only when every condition holds mechanically: the implement log exists and is non-empty; the implement log's evidence envelope recorded success with the task's validation green; the task's `inter_review` line records `clean` or `backlogged-candidates` (never `failed-relaunch-exhausted`, which keeps the Hard Gate 25 stop) and names no repository-file backlog path outside the fast-path commit pathspec; the plan-file delta classifies checkbox-flip-only with flips confined to the task section; no other working-tree path is dirty inside the task's declared scope.
- Mechanism-defining task: the task that introduces the run's core mechanism, resolved from the plan text before the first Phase 1 launch: the plan header line `Design review anchor: after Task N` when present, else the default convention: the first task whose Files list names a path that no earlier task's Files list names and that any later task's section text references (the decidable consumption proxy; consumer tasks typically edit, not co-list, the modules they import).
- Early design review: the one architecture-lens review the orchestrator launches after the mechanism-defining task's done boundary, scoped to the mechanism's diff against the plan's contract terms and threat model, folded before any consumer task starts.
- Consumer task: any task whose Files list depends on a path the mechanism-defining task introduced; under the default convention, every later task intersecting that path.
- Design-review fold: the accept/drop/disposition record for the early review's findings, recorded on a `design_review:` manifest line with the finding anchors, before Task N+1 launches.

## Why

Both defects are pipeline-shape costs the 2026-10-05 retrospective measured on one run. The per-task done boundary exists to give learn a per-task log handoff and keep a defect boundary per task; a dedicated sub-agent spawn adds nothing to either goal when the whole delta is the parent's own verified checkbox flips, yet the current Step 1.4 launches one unconditionally. The Phase 3 panel is the right final gate but the wrong first gate: per-task intermediate reviews are task-local by design and correctly missed the cross-task architectural flaws, so the first adversarial look at the mechanism happened when the fold was most expensive. One plan keeps the two efficiency changes coherent on the same pipeline seam and prices each against the same witnessed run.

## Outcome

- A checkbox-flip-only done delta completes through the fast-path done: the parent runs learn with the per-task log, satisfies the scripted verification conditions, commits with an explicit pathspec, and records the manifest row; a done sub-agent launches only when the delta is broader or any verification condition fails mechanically, which is today's unconditional path unchanged.
- After the mechanism-defining task's done boundary, the orchestrator launches one early design review scoped to the mechanism; its findings fold (or are dispositioned with anchors) on a `design_review:` manifest line before any consumer task starts, and Phase 3 remains the final fresh adversarial gate byte-for-byte unchanged.

Gate delta: one grown refusal surface, one amended hard gate, and one new stop-condition, all priced by the witnessed run. The grown surface is Step 1.4's launch decision, which gains the checkbox-flip-only test as the fast path's admission arm; a failed condition routes to today's unconditional sub-agent launch (the existing behavior is the fallback, never a new refusal to fix). The amended hard gate is Hard Gate 4's launch mandate, which gains the fast path as its second sanctioned arm. The new stop-condition is the early design review's fold-before-consumer-tasks duty, registered as a numbered hard gate with the `design_review:` manifest line as its witness: no consumer task launches while an unreviewed mechanism or an undispositioned blocking finding stands, and a batch or parallel group never spans the anchor task. Witnesses: the two filed rows carry the recorded run costs (nine done spawns at 2.5M tokens; the 17M-token Phase 3 fold), and each change's class-default alternatives are rejected in the origins: keep the per-task sub-agent (the priced defect), skip learn on the fast path (breaks the per-task capture contract), batch broader deltas (loses the per-task defect boundary), keep Phase 3 as the only architecture review (the priced defect), replace Phase 3 with the early review (loses the final fresh adversarial gate), widen per-task reviews to architecture scope (task-local by design, re-priced and rejected in origin row 2).

## Assumptions

- assume authoring runs unattended under the standing operator directive, so no interactive confirmation step interrupts the authoring of this plan; the plan carries no interactive gates of its own; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the venv pytest runner (`$HOME/.agents/venvs/ai-playbook-test/bin/python`) is an external prerequisite: on a host without it, create the venv or fall back to `python3 -m pytest` with the deviation recorded in the session notes; basis: the validation commands' canonical-invocation comments.
- assume the fast path is text-level in this plan: it composes the existing `execute_plan_runtime._diff_is_checkbox_marker_only` import with a parent-side section-confinement check, and adds no new script, flag, or schema field; under a machine manifest the fast path reuses the driver's existing done operation and receipt rather than bypassing it, and the enforcement-layer amendments (Hard Gate 4, the anti-pattern rows, the Announcement enumeration, the Phase 1 step-summary line) are text edits on surfaces this plan's Files list owns; basis: origin row 1's Expected ("the parent performs the done commit itself under a scripted verification").
- assume learn keeps its per-task capture contract on the fast path: the parent invokes learn with the implement log exactly as the done sub-agent would have, so the capture inputs are unchanged; basis: origin row 1's Expected ("Learn's per-task capture contract keeps its per-task log inputs either way").
- assume the early design review reuses the existing lens-worker launch machinery and template surface rather than a new template: its prompt scopes the architecture lens to the mechanism diff, the plan's contract terms, and the threat model; basis: origin row 2's Evidence ("lens templates exist and are reusable for an early architecture lens").
- assume the early review's log lives beside the per-task review log as `design-review-<anchor-task>.log.md` in the session directory, added to agent-logs.md's path table; basis: the path-table convention and the create-versus-append discipline it inherits.
- assume the three execute-plan/SKILL.md edit sites (Step 1.4 plus its enforcement-layer amendments, Task 1's; the new Step 1.4b subsection and the Hard Gates registry row, Task 2's) and the two agent-logs.md edit sites (the fast-path note as a paragraph after the path-convention table, Task 1's; the design-review table row, Task 2's) and the two subagent-prompts.md edit sites (the Done (per task) template's applicability sentence, Task 1's; the Review lens worker template's usage line, Task 2's) are disjoint spans; Tasks 1 and 2 declare their own and never touch another task's span; basis: the shared-file seam rule.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: an execute-plan run stops spawning a done sub-agent to commit the parent's own verified checkbox flips, and gains one cheap architecture-level review right after the mechanism exists instead of at hour 13.

Before (today): every task's done boundary spawns a sub-agent that reads the log, runs learn, commits, and updates the manifest, even when the commit is only the task's checkbox flips; and the first architecture-scoped adversarial review waits for Phase 3, after every consumer task built on the mechanism, so architectural findings fold at maximum blast radius.

After (this plan): a checkbox-flip-only delta completes through the fast path (learn with the per-task log, the scripted verification conditions, explicit-pathspec commit, manifest row), and only a broader delta or a failed condition spawns the sub-agent, exactly as today; and once the mechanism-defining task's done boundary closes, one architecture-lens review runs against the mechanism, its findings fold onto a `design_review:` manifest line, and consumer tasks start only after that fold.

Edge cases pinned: a delta mixing checkbox flips with any other plan byte change is not checkbox-flip-only (the marker-only classifier refuses same-line byte changes by construction) and takes the sub-agent path; flips in a foreign task's section fail the confinement check and take the sub-agent path; a failed implement-log envelope, a `failed-relaunch-exhausted` inter_review verdict, or an inter_review-named backlog path outside the pathspec routes to the sub-agent path or the mandated stop; a batch or parallel group never spans the anchor task; a machine-manifest run's fast path flows through the driver's done operation with the receipt echoed; the parent-side verification equivalents are recorded on the `done_fast_path:` row; a task with no Commit line keeps the justified nothing-to-commit boundary and the fast path records the none receipt without spawning; a plan with no `Design review anchor` line and no qualifying default (no later-task-consumed new path) runs no early review; a `Design review anchor: after Task N` naming a nonexistent task is an authoring defect the orchestrator reports and treats as no-anchor rather than guessing; blocking early-review findings stop consumer launches until folded; Phase 3's panel, caps, and seals are untouched.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the fast path's admission test is fully mechanical (classifier import plus section-span containment plus envelope success plus scope cleanliness) and every failed condition falls back to today's unconditional sub-agent launch; the anchor resolution is decidable from the plan text alone.
- fail-closed shape: the fast path never commits when a verification condition cannot be evaluated; the early review never silently passes (findings fold or disposition with anchors onto the manifest line before Task N+1).
- observability: the manifest records which tasks took the fast path (a `done_fast_path:` row per task with the condition results) and the `design_review:` line records the review's verdict and fold, so an auditor can reconstruct both boundaries from the manifest alone.
- maintainability: both changes are text-level edits composing existing classifiers and templates; no new script, flag, or schema field.

**Done when:**
- all task boxes checked; the shared-skill contract suites pass under the venv pytest runner; each pinned grep flips as its task records; the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-execution-cost-boundaries.md` exits 0 on the final bytes.

**Ship when:**
- a multi-task execution whose tasks' done deltas are checkbox-flip-only completes its per-task boundaries through the fast path with learn capture intact, and a run whose mechanism-defining task folds architecture findings at task 2 instead of Phase 3.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Step 1.4's launch paragraph and its no-manufacture clause; the new Step 1.4b mechanism design review subsection; the new numbered hard gate row in the Hard Gates registry; Hard Gate 4's launch mandate; the anti-pattern table's Phase 1 commit-path rows; the Announcement paragraph's per-task loop enumeration; the Phase 1 step-summary line)
- `agents/skills/execute-plan/agent-logs.md` (the path-convention table's new design-review row; the fast-path manifest-row note placed as a paragraph after the path-convention table, before the briefing paragraph)
- `agents/skills/execute-plan/subagent-prompts.md` (the Review lens worker template's usage line, extended to admit Step 1.4b launches; the Done (per task) template's one fast-path applicability sentence, Task 1's)
- `agents/skills/done/SKILL.md` (the Step 1 learn-invocation note's fast-path clause only)

**Tests:**
- none: both changes are skill-text contracts; the mechanical classifier they compose (`execute_plan_runtime._diff_is_checkbox_marker_only`) is covered by scripts/test_execute_plan_runtime.py's consumer-path tests (dirty-entry tolerance and plan-edit disposition, both polarities), untouched here

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- Phase 3's panel composition, caps, seals, and the graded accepted-fix rule: frozen; the early review never replaces or reorders them.
- Step 1.2b's task-local scope: frozen; the origin row explicitly declines widening it to architecture scope.
- `scripts/code_delta_classifier.py` and `scripts/plan_delta_classifier.py`: adjacent classifiers with their own contracts; the fast path composes the runtime marker-only classifier, not these.
- the done skill beyond the one Step 1 learn-invocation clause: the done sub-agent path is byte-identical after this plan.
- the consumer STORY-KEY/9d6cdc75 runs: history, not an edit surface.

## Validation Commands

```bash
# Shared-skill contract suites over the exact bytes both tasks edit
# (shared-body runtime neutrality and pinned-span assertions; the venv
# runner is the canonical invocation)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_harness_policy_contract.py scripts/test_lessons_recovery_contract.py -q
# Task 1 pins (verified zero hits at authoring, fresh greps recorded
# 2026-10-05; each literal is contained verbatim in the checkbox text
# that prescribes it)
grep -F "checkbox-flip-only" agents/skills/execute-plan/SKILL.md
grep -F "never the fast path" agents/skills/execute-plan/SKILL.md
grep -F "capture contract applies unchanged" agents/skills/done/SKILL.md
grep -F "done_fast_path:" agents/skills/execute-plan/agent-logs.md
# Task 2 pins (verified zero hits at authoring, fresh greps recorded)
grep -F "Design review anchor" agents/skills/execute-plan/SKILL.md
grep -F "design_review:" agents/skills/execute-plan/SKILL.md
grep -F "no consumer task launches" agents/skills/execute-plan/SKILL.md
grep -F "design-review-<anchor-task>.log.md" agents/skills/execute-plan/agent-logs.md
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews; green arrives from the
# first record whose source_digest matches these bytes
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-execution-cost-boundaries.md
```

### Task 1: the fast-path done for checkbox-flip-only deltas

Files:
- `agents/skills/execute-plan/SKILL.md` (Step 1.4's launch paragraph and its no-manufacture clause; Hard Gate 4's launch mandate; the anti-pattern table's Phase 1 commit-path rows; the Announcement paragraph's per-task loop enumeration; the Phase 1 step-summary line)
- `agents/skills/execute-plan/agent-logs.md` (the path-convention table area's fast-path manifest-row note)
- `agents/skills/done/SKILL.md` (the Step 1 learn-invocation note's fast-path clause)
- `agents/skills/execute-plan/subagent-prompts.md` (the Done (per task) template's one fast-path applicability sentence)

Shared-file seam: this task owns Step 1.4 in execute-plan/SKILL.md and lands before Task 2; Task 2 owns the new Step 1.4b subsection and neither may edit Step 1.4.

Evidence:
- `grep -F "checkbox-flip-only" agents/skills/execute-plan/SKILL.md` and `grep -F "never the fast path" agents/skills/execute-plan/SKILL.md`; cover the fast-path insertion and the no-manufacture reconciliation (RED at authoring: zero hits, fresh greps recorded 2026-10-05)
- `grep -F "capture contract applies unchanged" agents/skills/done/SKILL.md`; covers the done-skill sentence (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `grep -F "done_fast_path:" agents/skills/execute-plan/agent-logs.md`; covers the manifest-row note (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_harness_policy_contract.py scripts/test_lessons_recovery_contract.py -q`; covers the shared-skill contract suites over the edited bytes (green at authoring; must stay green after the edits)

- [x] In Step 1.4, before the `Launch a sub-agent` sentence, insert the fast-path paragraph: when the task's done delta is checkbox-flip-only (the plan-file worktree-vs-HEAD diff classifies checkbox-flip-only through the runtime's own marker-only classifier `execute_plan_runtime._diff_is_checkbox_marker_only`, imported never re-implemented, and every flipped box sits inside the completed task's section span) and every scripted verification condition holds mechanically (the implement log exists and is non-empty; the implement log's evidence envelope recorded success with the task's validation green; the task's `inter_review` line records verdict `clean` or `backlogged-candidates`, a `failed-relaunch-exhausted` verdict routing to the Hard Gate 25 stop and never the fast path; the `inter_review` line names no repository-file backlog path unless those paths join the fast-path commit pathspec; no other working-tree path is dirty inside the task's declared scope), the parent executes the full done sequence itself in the done skill's own order (acquire the per-worktree done lock per done Step 0, invoke learn with the implement log exactly as the done sub-agent would, keeping the per-task capture contract's log inputs, run the docs-branch sync when the run's placement owes it, stage by explicit path, run the pre-commit sensitive-data scan over that staged content), then commit with an explicit pathspec naming the plan file, any learn-owned artifacts inside the task's declared paths, and any inter_review-named repository-file backlog paths, record a `done_fast_path:` manifest row carrying the scripted verification conditions' results and the commit sha, where a task whose section carries no `Commit:` line records the justified none receipt in place of the commit sha without spawning; when a machine manifest is active, submit the existing done handoff receipt through the driver's done operation instead of the bare commit, echoing the task's planned `Commit:` identity in `planned_commit` and using the plan-path handling already sanctioned for checkbox-marker-only deltas (learn-owned artifacts ride the fast-path commit only when inside the task's declared paths; otherwise they stay uncommitted exactly as today's sub-agent path leaves them), with the `done_fast_path:` row recording the driver outcome beside the receipt; the parent-side verification equivalents replace the sub-agent-phrased gate items inline (the parent read the implement log for the learn invocation; the recorded commit sha is at HEAD; the working tree is clean over the task's declared scope after the commit), leaving the gate items themselves byte-identical for the sub-agent path; if any condition fails or cannot be evaluated, fall back to today's unconditional sub-agent launch and record which condition failed on the manifest row [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the enforcement layer so the fast path is the sanctioned arm: in Hard Gate 4, extend the per-task launch mandate to read launch the done sub-agent (Step 1.4) or complete the fast-path done under Step 1.4's scripted conditions (parent-agent implementation satisfies this gate only through the fast path's recorded conditions); in the anti-pattern table, amend the Phase 1 commit-path rows to name the fast path as the sanctioned exception (commits still belong to the done boundary; the fast path is the parent executing that boundary under recorded conditions); in the Announcement paragraph's per-task loop enumeration and the Orchestrator Responsibilities step-summary line's Step 1.4 arm (the line containing `done sub-agent after every task` with its markdown bold markers), replace the bare `done sub-agent` wording with `done boundary (sub-agent or Step 1.4 fast path)` [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 1.4's existing no-manufacture clause (`never manufacture a checkbox-flip commit to satisfy the boundary`), append the reconciling clause so the two rules cannot read as contradictory: the fast path above is the sanctioned parent-side commit of the Step 1.3 flips themselves when the task section carries a `Commit:` line and the flips are the whole delta, the no-Commit-line fast path recording the justified none receipt instead; the prohibition binds sub-agents and the none-witness path, never the fast path [class: IMPLEMENTATION_REQUIRED]
- [x] In agent-logs.md, beside the path-convention table, add the fast-path note: a `done_fast_path:` manifest row is the parent's record that a task's done boundary completed without a done sub-agent, naming the scripted verification conditions' results and the commit sha; the per-task log handoff contract is unchanged and the implement log remains the learn input on the fast path [class: IMPLEMENTATION_REQUIRED]
- [x] In the done skill's Step 1 area, add one sentence to the learn-invocation note: when execute-plan's fast path invokes learn directly with the implement log, learn's capture contract applies unchanged; the parent executing the fast path has already acquired the done lock, invoked learn, run the docs-branch sync when owed, staged by explicit path, and run the pre-commit sensitive-data scan over the staged content in the done skill's own order, so the wrapper is the same sequence without the sub-agent [class: IMPLEMENTATION_REQUIRED]
- [x] In subagent-prompts.md's Done (per task) template area, add one applicability sentence: this template does not launch when Step 1.4's fast path applies (the parent records the boundary through the fast path instead) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive all anchor spans from live bytes before editing and verify the Step 1.4 pass-list and verification-gate items stay byte-identical outside the inserted paragraph and appended clause, and that the agent-logs.md fast-path note landed as its own paragraph after the path-convention table's last row and before the briefing paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all four greps flip to positive hits; the shared-skill contract suites still pass; the em-dash added-lines scan and the public hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan fast-path done for checkbox-flip-only deltas` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the early design review after the mechanism-defining task

Files:
- `agents/skills/execute-plan/SKILL.md` (the new Step 1.4b subsection between Step 1.4 and Step 1.5; the new numbered hard gate row in the Hard Gates registry)
- `agents/skills/execute-plan/agent-logs.md` (the path-convention table's design-review row)
- `agents/skills/execute-plan/subagent-prompts.md` (the Review lens worker template's usage line, extended to admit Step 1.4b launches)

Shared-file seam: this task owns the new Step 1.4b subsection and the Hard Gates registry row in execute-plan/SKILL.md and the path table's design-review row in agent-logs.md; Task 1 owns Step 1.4 and the fast-path note and neither may edit these.

Evidence:
- `grep -F "Design review anchor" agents/skills/execute-plan/SKILL.md`; covers the anchor resolution (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `grep -F "design_review:" agents/skills/execute-plan/SKILL.md`; covers the manifest-line duty (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `grep -F "design-review-<anchor-task>.log.md" agents/skills/execute-plan/agent-logs.md` and `grep -F "no consumer task launches" agents/skills/execute-plan/SKILL.md`; cover the log-path row and the stop-condition sentence (RED at authoring: zero hits, fresh greps recorded 2026-10-05)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py -q`; covers the shared-skill contract suites over the edited bytes (green at authoring; must stay green after the edits)

- [x] Add the new subsection `### Step 1.4b: Mechanism design review (anchor task)` between Step 1.4 and Step 1.5, reading: the anchor is resolved from the plan text before the first Phase 1 launch (the plan header line `Design review anchor: after Task N` when present, else the default convention: the first task whose Files list names a path that no earlier task's Files list names and that any later task's section text references, a grep over the plan bytes as the decidable consumption proxy; a header naming a nonexistent task is reported and treated as no-anchor, never guessed); the anchor task is never batched or parallel-grouped with a later task (a batch or group whose membership would span the anchor task stops at the anchor boundary), so the review fires before any consumer implement work exists; after the anchor task's Step 1.4 verification gate passes, the orchestrator launches one architecture-lens review scoped to the mechanism (the anchor task's diff, the plan's contract terms, the plan's threat model) through the Review lens worker template with the architecture lens, the template's usage line extended to admit Step 1.4b launches; the review produces a staging doc at `{reviews_dir}/YYYY-MM-DD-<plan-slug>-design-review.md` (a naming that never consumes the Phase 3 `-code-review-r<N>` counter) with scoped N/A rows where the full-panel elements do not apply (mutator matrix, Witness ledger), its findings fold or disposition with anchors onto a `design_review:` manifest line (verdict, finding anchors, dispositions), the review pass appends to `{tmp_dir}/execute-plan/<PLAN_SLUG>/design-review-<anchor-task>.log.md` with the create-versus-append rules and the Heartbeat section's final-Pass Status rule, and no consumer task launches while a blocking finding stands undispositioned (the duty registered as a numbered hard gate with the `design_review:` line as its witness, and the Recovery path skips Step 1.4b exactly as it skips Step 1.2b); Phase 3 remains the final fresh adversarial gate unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] In agent-logs.md's path-convention table, add the row: `Mechanism design review (Step 1.4b, parent-owned)` with path `{tmp_dir}/execute-plan/<PLAN_SLUG>/design-review-<anchor-task>.log.md`, inheriting the create-versus-append rules and the Heartbeat section's final-Pass Status rule [class: IMPLEMENTATION_REQUIRED]
- [x] In subagent-prompts.md, extend the Review lens worker template's usage line to admit Step 1.4b launches beside the Step 3.1 ones (one sentence; the template body is unchanged) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive the insertion anchor from live bytes before editing and verify Steps 1.4 and 1.5 stay byte-identical outside the new subsection, and re-derive the agent-logs.md table span including Task 1's fast-path note paragraph so the second-landed row cannot collide with it [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: all four greps flip to positive hits; the shared-skill contract suites still pass; the em-dash added-lines scan and the public hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [x] Commit: `feat: execute-plan early design review after the mechanism-defining task` [class: IMPLEMENTATION_REQUIRED]
