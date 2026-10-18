# Plan: plan execution budget and dependency-chained splitting discipline

Backlog origin: docs/history/backlog/2026-10-05-plan-sizing-execution-budget.md
Driving force: efficiency (primary) + token-usage (secondary)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-plan-sizing-execution-budget-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Execution budget: the plans-template header line `Execution budget: <total>h total, largest task <max>h`, an optional member of the required metadata block, where both numbers are the author's non-negative decimal-hour estimates with an optional single fractional part (`3h` and `3.0h` are the same value; a missing number, a negative, or a non-numeric value is a malformed line) computed with the task-shape table before tasks are written; the readiness gate reads the declared numbers and never estimates cost from plan content.
- Task-shape table: the weight table beside the budget line in the plans skill (prose-only 0.25-0.5h; new module with selftest ~1h; large existing-file refactor 1-1.5h; any task estimated above 1.5h splits into its own plan); the weights are calibration defaults updated as landed runs provide data, not a gate.
- Sizing warning: the new non-blocking `readiness PRE-ROUND WARNING:` stderr output of scripts/plan_readiness.py's pre-round gate; one line per breached threshold emitted in the declared order (total, then largest task, then task count); a warning never changes the exit code, the stdout OK line, or the failure path.
- Two-round alarm: the plans-skill authoring rule that when a second review round ends without certification, the mechanism is too novel and the author splits the mechanism, not the tasks.
- Seam rule: the plans-skill splitting rule that a split boundary never cuts a shared-file set (tasks editing the same production or test file stay in one plan or become strictly sequenced plans with a header-declared execution dependency).
- Parked-dependency machinery: the existing execute-plan queue-drain contract (header-declared execution dependency, live parked_dependencies entries, dependency-blocked marks in the D1 selection); this plan rides it unmodified.
- Header region: the region between the plan title line and the first `## ` heading, where the required metadata block lives and where the budget-line parser looks.
- Guard doctrine: the prove-first and fail-loud rules in projects/.ai-playbook/agent_workflow_guidelines.md section 64 (no new guard before its harm class shows recorded cases and time lost; report posture by default, refusal posture reserved for the landing-fence class).
- Unit identifiers: the frozen rolling-log entry `execution-pipeline-friction` (docs/history/backlog/PLAN-PROMPTS.md) numbers this plan's sibling units; the standing D-4 authoring directive (the maintenance loop's standing authoring order) keeps the lane continuous; U1 (the read contract) landed, U2 (execution-loop friction) is peer-held, and U4 (directory shape) is strictly after U1 and this plan's own unit U3 (the sizing and splitting unit these bytes author).

## Why

Plans carry no cost model today, so oversizing surfaces at hour six of an execution instead of at authoring: the witnessed nine-task run spent about 16 hours against the operator's two-to-three-hour per-plan target. A declared execution budget sized from the task-shape table, readiness warnings on the declared numbers, and the two-round alarm move the split decision to authoring time where it is cheap. The seam rule keeps those splits from manufacturing rebase churn across shared files.

## Outcome

Plans declare an execution budget header line sized from the task-shape table, the readiness pre-round gate warns non-blocking on oversize budget, task, and count, and the authoring rules split the mechanism after two uncertified rounds along boundaries that never cut a shared-file set.

- The template metadata block gains the optional Execution budget line with the task-shape table beside it, so an author sizes before writing tasks instead of discovering cost mid-execution.
- scripts/plan_readiness.py's pre-round gate emits stderr warnings when the declared total exceeds 3.0h, the largest declared task exceeds 1.5h, or the plan exceeds four tasks, stays silent for plans without the line, and never blocks.
- The plans rules gain the two-round alarm and the seam rule, so repeated review rounds trigger a mechanism split and split boundaries respect shared-file sets under the parked-dependency machinery.

Gate delta: one new non-blocking warning class in plan_readiness --pre-round (three strictly-greater thresholds plus a malformed-line warning; report posture per the guard doctrine, never a refusal; the harm class is the witnessed nine-task ~16h run against the 2-3h target, the origin row's Evidence block), one new optional template metadata line with its task-shape weight table, and two new authoring rules (the two-round alarm and the seam rule); no refusal class grows, no fence, no protocol layer, no schema state field, and plans without the new line behave byte-identically.

## Assumptions

- assume the caps stay warnings that force the split question and never hard refusals; basis: the origin row's Expected sentence and the entry's recorded rejected alternative "Raise the size caps into hard refusals".
- assume the budget line is an optional member of the template's required metadata block, so existing plans without it stay valid and the warnings skip silently; basis: the metadata block's optional-member composition (the External gate precedent), the metadata retrofit rule, and the migrate-on-touch convention.
- assume the line's grammar carries two author-computed non-negative decimal hours (integers valid, optional single fractional part) so the pre-round gate stays structural-only: plan_readiness parses declared numbers and task headings, never content semantics; basis: run_pre_round's structural contract (no review-record consultation, first-problem-wins probes) and the origin's "the author's weighted estimate from a task-shape table".
- assume the task-shape weights live in the plans skill beside the line with no new data file or tool; basis: the origin's "calibrated over time from landed runs" and the fewer-moving-artifacts principle.
- assume the two-round alarm is authoring-doctrine text in the plans skill, not a readiness probe, because at pre-round time no review rounds exist; basis: the origin's "the authoring-side alarm fires when certification passes ~2 rounds" and the gate's structural-only contract.
- assume the seam rule lands as authoring-doctrine text and rides the execute-plan dependency machinery unmodified; basis: the origin's Source section (the queue-drain paragraph) and the frozen entry's "riding the existing header-declared execution dependency and parked-dependency machinery" wording.
- assume strictly-greater threshold comparisons (3.0h total, 1.5h largest task, and exactly 4 tasks are silent; the first step over each warns); basis: the origin row's "exceeds ~3h", "exceeds ~1.5h", and "exceeds roughly 4 tasks" wording, with the frozen entry's "over ~3h / over ~1.5h / over roughly 4 tasks" phrasing naming the same thresholds.
- assume sibling units own different files (the U2 lanes are peer-held over the done and execute-plan surfaces; U4 is strictly after U1 and U3 and re-keys plan_readiness later for the directory shape), so anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the frozen entry's seam rule and the freeze line's two-claim witness.
- assume the new warning class satisfies the guard doctrine's prove-first rule: its harm class shows recorded cases and time lost (the witnessed ~16h nine-task run and the origin row), and its posture is report, not refusal; basis: projects/.ai-playbook/agent_workflow_guidelines.md section 64 as landed in 538f1f08.
- assume authoring runs under the standing D-4 authoring directive plus the live operator order to resume authoring by priority, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the maintenance loop's authoring blueprint under the standing operator directive.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: plans declare an execution budget and the authoring gates warn on oversize, so splits happen at authoring time instead of hour six of an execution (efficiency).

Before (today): a plan carries no cost declaration, task count and shape are unchecked, and oversizing is discovered mid-execution; the witnessed nine-task run ran about 16 hours across quota windows against the operator's two-to-three-hour target, and the five-round certification outlier was a novel-mechanism monolith whose seam was visible from round 1.

After (this plan): the author weighs each task against the task-shape table, declares `Execution budget: 2.5h total, largest task 1.0h` in the header, and the pre-round gate warns when the declared numbers or the task count exceed the caps; a second uncertified review round triggers the two-round alarm (split the mechanism), and no split boundary cuts a shared-file set.

Edge cases pinned: a plan without the budget line behaves byte-identically to today (silent skip); a malformed line produces one non-blocking warning naming the grammar; the at-threshold values 3.0h, 1.5h, and 4 tasks are silent and the first step over each warns; integers are valid hours (`4h` equals `4.0h`); a plan breaching several thresholds emits one warning line per breach in the declared order (total, largest task, task count); warnings never change the exit code, the stdout OK line, or the failure path (a probe failure emits zero warning lines); a five-task plan warns even when its declared budget is small; the task-shape table is calibration defaults, never a gate.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the parser accepts the pinned grammar (non-negative decimal hours, optional fraction, integers valid), skips silently when the line is absent, warns once on a malformed line naming the grammar, and compares strictly greater against 3.0h, 1.5h, and 4 tasks (counted from the `### Task N:` headings), emitting one warning line per breach in the declared order (total, largest task, task count).
- non-blocking semantics: warnings go to stderr as `readiness PRE-ROUND WARNING:` lines before the OK line; the exit code, the stdout OK line, and the failure path stay byte-identical.
- additive template arm: the budget line is optional with migrate-on-touch; existing plans stay valid; no existing probe's behavior changes.
- maintainability: one template line, one weight table, two rules in the skill; one warning emitter and its fixtures in the gate; no new tool, no data file, no driver change.

**Done when:**
- all task boxes checked; the readiness suite passes under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_readiness.py -q` exits 0; bare `python3` off-venv fails rc 1 with a pytest import error, fail-closed); the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-sizing-execution-budget.md --pre-round` exits 0 on the final bytes.

**Ship when:**
- the template declares the budget line, the weight table, and the two splitting rules, a pre-round run over an over-budget plan emits the three warning classes without blocking, and a plan without the line behaves byte-identically to today.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (the pre-round sizing warnings, the budget-line parser, and the inline pre-round selftest family only)
- `agents/skills/plans/SKILL.md` (the metadata block's budget line, the task-shape table, and the two splitting rules only)

**Tests:**
- `scripts/test_plan_readiness.py` (new sizing-warning test items)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/` files: the dependency machinery is ridden, never modified (queue-drain paragraph, parked_dependencies, D1 selection).
- `scripts/plan_task_span.py` and the Standing-constraints surfaces: owned by the landed plan-worker-read-contract plan.
- the other frozen-entry units (the peer-held U2 lanes, U4 directory shape): separate plans under the frozen entry's seam rule.
- the runtime driver `scripts/execute_plan_runtime.py`: no runtime change; the warnings live in the authoring gate only.
- any hard refusal path for size caps: the caps stay split-questions by the origin's own words.

## Validation Commands

```bash
# Readiness suite (new sizing-warning cases; the venv runner is the
# canonical invocation; bare python3 off-venv fails rc 1 with a pytest
# import error, fail-closed)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_readiness.py -q
# Pins: verify no pin keys a span this edit touches; a moved anchor
# re-keys its pin in the same edit
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never
# argless; it witnesses committed bytes, so the GREEN checkpoints run it
# after the task's commit)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Pre-round structural gate on this plan (fail-closed)
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-sizing-execution-budget.md --pre-round
```

### Task 1: The execution budget sizing warnings in the readiness gate (TDD)

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_readiness.py -q`; covers every criterion below at the task boundary (bare `python3` off-venv fails rc 1 with a pytest import error)
- `grep -c "PRE-ROUND WARNING" scripts/plan_readiness.py`; covers the warning emitter presence (RED at authoring: zero hits)
- `grep -c "Execution budget" scripts/plan_readiness.py`; covers the line parser presence (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: run_pre_round's probe order and exit contract (fence balance, decision marker, review scope, plan ownership, scope classification; first problem wins; the OK line on stdout, failures on stderr), the inline pre-round selftest family's pinned expectations, the plans skill metadata block's fixed-line composition, and whether any pin keys a plan_readiness or plans-skill span; if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] `test_pre_round_budget_warning_over_total`; given a plan whose header declares `Execution budget: 4.0h total, largest task 1.0h`, expects one stderr warning naming the over-budget total, the unchanged stdout OK line, and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_warning_largest_task`; given a plan declaring `Execution budget: 2.0h total, largest task 1.6h`, expects one warning naming the largest-task threshold and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_warning_task_count`; given a plan with five `### Task N:` headings declaring `Execution budget: 1.0h total, largest task 0.5h`, expects one warning naming the task-count threshold and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_absent_silent`; given a plan without the line, expects no warnings and output byte-identical to the pre-plan behavior [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_malformed_warns`; given a header line `Execution budget: TBD`, expects one warning naming the line grammar and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_at_threshold_silent`; given `Execution budget: 3.0h total, largest task 1.5h` and exactly four task headings, expects no warnings [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_integer_hours_in_grammar`; given `Execution budget: 4h total, largest task 1h`, expects the over-budget total warning (integers parse as whole hours) and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_multi_breach_order`; given a plan declaring `Execution budget: 4.0h total, largest task 1.6h` with five task headings, expects exactly three warning lines in the declared order (total, largest task, task count) and exit 0 [class: REPOSITORY_TEST]
- [x] `test_pre_round_budget_failure_path_no_warnings`; given a plan that fails a structural probe (its Assumptions section lacks the required decision-points trailer) while declaring `Execution budget: 4.0h total, largest task 1.0h`, expects the unchanged `readiness PRE-ROUND FAILED:` stderr line, exit 1, and zero `PRE-ROUND WARNING:` lines [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner (the warning emitter does not exist; the new tests fail on the missing warnings) [class: REPOSITORY_TEST]
- [x] Implement the sizing warnings in scripts/plan_readiness.py inside run_pre_round after the existing probes pass: parse the header region for the `Execution budget:` line with the pinned grammar (non-negative decimal hours with an optional single fractional part, integers valid; a missing number, a negative, or a non-numeric value is the malformed line), emit `readiness PRE-ROUND WARNING:` lines to stderr for the strictly-greater thresholds (total over 3.0h, largest task over 1.5h, task count over 4 counted from the `### Task N:` headings), one line per breach in the declared order (total, largest task, task count), one malformed-line warning naming the grammar, silent skip when the line is absent, the stdout OK line and the exit contract unchanged (warnings never block; the failure path emits zero warning lines), and extend the inline pre-round selftest family with the warning-path case so --selftest keeps pinning the family's contract [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: full suite OK [class: REPOSITORY_TEST]
- [x] Commit: `feat: plan readiness pre-round gains non-blocking execution budget sizing warnings` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The plans template arm: budget line, weight table, two-round alarm, seam rule

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_execute_plan_runtime.py -q -k shared_skill_bodies`; covers the shared-body gate criterion (the plans skill is a gate-covered shared-body file)
- `bash scripts/check_maintenance_pins.sh`; covers the pins criterion (verify no pin keys a span this edit touches; a moved anchor re-keys its pin in the same edit)
- `grep -c "Execution budget" agents/skills/plans/SKILL.md`; covers the template arm presence (RED at authoring: zero hits)

- [x] Add the `Execution budget: <total>h total, largest task <max>h` line to the template metadata block's fixed lines as an optional member, with the task-shape weight table beside it (prose-only 0.25-0.5h; new module with selftest ~1h; large existing-file refactor 1-1.5h; any task estimated above 1.5h splits into its own plan) and the calibration sentence: the weights are defaults updated as landed runs provide data [class: IMPLEMENTATION_REQUIRED]
- [x] Add the two authoring rules beside the template rules: the two-round alarm (when a second review round ends without certification, the mechanism is too novel: split the mechanism, not the tasks) and the seam rule (a split boundary never cuts a shared-file set; strictly sequenced plans declare a header execution dependency under the existing parked-dependency machinery); verify no pin keys a span this edit touches and re-key any moved pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run the standing gates: the shared-body runtime test OK, the readiness suite OK, the pins suite exits 0 with OUTCOME: pass, the public hygiene scan exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-sizing-execution-budget.md --pre-round` exits 0 on the final bytes; the em-dash added-lines scan runs after the task's commit so it witnesses the committed bytes [class: REPOSITORY_TEST]
- [x] Commit: `feat: plans template gains the execution budget line and the splitting rules` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-pse (branch plan-plan-sizing-execution-budget-exec) by the standing maintenance execution lane. Task 1 (2e223532): the nine named pre-round budget warning tests land in scripts/test_plan_readiness.py with the RED split (six failing on missing warnings, three unchanged-behavior guards passing), and run_pre_round gains the non-blocking sizing warnings after the existing probes: header-region parse with the pinned grammar, strictly-greater thresholds (total 3.0h, largest task 1.5h, task count 4), warning lines in the declared order, one malformed-line warning, silent absence, unchanged stdout and exit contract, and the inline --selftest family extended with the warning-path case. Task 2 (f3d54c99): the plans template gains the optional Execution budget line with the task-shape weight table and calibration sentence, plus the two-round alarm and the seam rule beside the template rules; no pin keyed a moved span.

Validation: readiness suite 67 passed + 44 subtests under the venv runner; inline --selftest ALL PASS; pins suite exit 0; hygiene scan exit 0; pre-round on the final bytes exit 0; em-dash added-lines scan exit 0. One pre-existing failure is recorded as out of scope: test_shared_skill_bodies_remain_runtime_neutral fails on main's tip itself (a forbidden runtime term in agents/skills/execute-plan/SKILL.md restored by the 38e6f44e race-repair commit); this plan's three files carry zero forbidden-term hits, and a separate repair lane owns the execute-plan file. Exec review r4 (fresh-adversarial, one worker) found zero blocking findings with two Low residuals accepted (bare-line missing-number edge; fence-blind task-count probe) and one overflow (duplicate-line first-match); records at docs/reviews/2026-10-05-plan-review-plan-sizing-execution-budget-r4.{md,stats.json}.

Deferred residuals: the r4 Lows above; the shared-body forbidden-term repair row. Origin row docs/history/backlog/2026-10-05-plan-sizing-execution-budget.md is covered by this execution and folded in the landing.
