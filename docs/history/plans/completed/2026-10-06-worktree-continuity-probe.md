# Plan: Per-boundary run-continuity probe

Backlog origin: docs/history/backlog/2026-10-05-worktree-continuity-probe.md

Driving force: reliability (outside the five driving principles; justification: a witnessed run's Task 1 implement worker recreated the provisioned worktree mid-run, silently discarding an untracked draft and the transferred gitignored inputs, and the loss surfaced only at the closeout migration refusal, so the boundary probe ships rather than parks; park-triage would not take it: the probe re-uses the Worktree-first standard's existing predicates as one script with pinned fixtures)

Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-worktree-continuity-probe-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 1.5h total, largest task 1.0h

Execution dependency: docs/history/plans/2026-10-05-execute-plan-done-boundary-evidence-gates.md; docs/history/plans/2026-10-05-live-claim-plan-deletion-fence.md (landings; shared-file seam rule: both plans queue edits to the execute-plan skill files this plan edits, so this plan's execution waits on their landed branches through the parked-dependency machinery)

## Terms

- Continuity probe: the mechanical check this plan adds; at every task boundary the orchestrator runs `scripts/check_run_continuity.py check` over the run's recorded identity and reads the outcome contract.
- Linked worktree: a checkout whose `git rev-parse --git-dir` and `git rev-parse --git-common-dir` resolve to different paths; the Worktree-first standard's existing predicate.
- Recorded run identity: the run worktree root and run branch a run records at Phase 0 (the execution claim and manifest identity block).
- Closeout baseline state: the captured `closeout-baseline.json` or its `closeout-baseline-skip.json` sibling in the run's manifest directory; both count as recorded, neither means uncaptured.
- Task boundary: the green boundary a task leaves behind (verification gate passed, commit landed, manifest updated); the same checkpoint the Task-boundary checkpoint duty and the execution-claim refresh fire at.
- Stop-and-repair gate: a failed probe stops the boundary and routes into the existing repair arms (re-transfer inputs, re-capture or skip-record the baseline); the run never continues silently and never re-provisions its own worktree.
- Primary placement: a run whose worktree policy resolves the execution lane to the primary checkout (no run worktree); its probe skips the worktree checks.
- Outcome contract: `scripts/OUTCOME_CONTRACT.md`; exit 0 pass, exit 1 fail, exit 2 indeterminate, exit 3 tool error, final `OUTCOME:` line required.
- Shared-file seam rule: the plans-skill rule that plans editing the same production or test file are strictly sequenced through a header-declared execution dependency under the parked-dependency machinery.
- Worktree-first standard: the execute-plan section owning the run-worktree lifecycle this plan extends (creation, transfer-in, landing, transfer-out).
- Phase 0: the run-setup phase that creates the worktree, transfers inputs in, and captures the baseline before any task work.
- Execution claim: the per-run claim file under `docs/tmp/execution-claims/` whose `updated:` refresh fires at phase and task boundaries.
- Task-boundary checkpoint duty: the execute-plan paragraph that stands each green task boundary as durable, resumable state.
- Implement Task template (and its Batch sibling): the subagent-prompts worker prompt templates; their `## Rules` lists are the worker-binding rule home an implement worker actually reads.
- Transfer-in implementation: the standard's procedure copying the gitignored inputs (facts file, reviews directory) into a fresh worktree.
- Closeout migration: the worktree-closeout step that copies gitignored run artifacts to the primary checkout and refuses removal until it verifies them.
- Baseline-less closeout arm: the closeout degradation that records a `closeout-baseline-skip.json` when baseline capture failed, and stops when neither file exists.
- Maintenance pins: the literal-span assertions in `scripts/check_maintenance_pins.sh` naming shipped mechanism spans; an edit that rewords a pinned span re-keys the pin in the same change.
- Witnessed run: the review-cert-graded-binding execution run the origin row records, whose Task 1 implement worker recreated the provisioned worktree mid-run.

## Why

Phase 0 provisions the worktree and transfers the gitignored inputs once, and every later boundary assumes that state immutable; the witnessed run lost its worktree, inputs, and baseline mid-run and only the closeout migration refusal noticed.

## Outcome

Execution runs re-verify their provisioning at every task boundary and stop with a named repair instead of continuing on lost state.

- The task boundary runs a mechanical probe of the recorded worktree, branch, gitignored inputs, and baseline state, failing loud with per-check evidence.
- A failed probe routes into the existing repair arms (re-transfer from the primary checkout, re-capture or baseline-skip record) before the run continues.
- A worker that finds its provisioned worktree or branch missing returns `blocked` instead of provisioning its own checkout.

Gate delta: adds one stop-and-repair gate (the per-boundary probe) and one worker refusal rule (no self-provisioned checkout); paying sibling arm: the closeout migration refusal and the baseline-less closeout arm already stop at closeout, and this gate moves the same stop to the boundary where the loss happens; witnessed integrity failure: the origin row's run, whose Task 1 worker recreated the worktree and silently dropped the facts file, reviews directory, and closeout baseline; guard liveness ledger at authoring time: total catches=4, incidents=11 (4:11).

## Assumptions

- assume the probe rides the existing task boundary (the checkpoint the Task-boundary checkpoint duty and the execution-claim refresh fire at) rather than a new boundary; basis: the origin row's Expected section and the EXECUTION CLAIM paragraph's refresh cadence (every task completion inside the implementation loop).
- assume the probe is a script under `scripts/`, not inline shell in the skill body; basis: the plans skill's runnable-carrier rule for exact multi-line bash in skill text.
- assume a primary-placement run runs the input and baseline checks only, the worktree checks skipped by flag; basis: the policy paragraph records the placement as no run worktree, making those checks vacuous.
- assume both queued plans sharing the execute-plan skill files strictly sequence before this plan; basis: the shared-file seam rule and the origin entry's boundary clause.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: runs re-probe their worktree, branch, inputs, and baseline at every task boundary, and workers never provision their own checkout, closing the silent mid-run state-loss class.

The witnessed run's Task 1 implement worker found its assigned worktree and branch absent and created its own checkout, discarding an untracked draft and silently dropping the transferred facts file, reviews directory, and closeout baseline; the loss surfaced only when the closeout migration refused on the missing baseline. Under this plan the same drift is caught at the next task boundary: the probe names the failed check (`linked`, `registered`, `branch`, `facts`, `reviews`, `baseline`) with observed evidence, and the boundary stops into the repair arms instead of continuing. A worker prompt now also carries the refusal rule, so the recreation shape returns `blocked` before any state is discarded.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each probe check fails on its own defect shape with per-check evidence (hermetic scratch-repo fixtures for every refused shape and the green path)
- integration: the probe paragraph lives once in the Worktree-first standard section and is referenced, never restated, at the wiring points

**Done when:**
- `scripts/check_run_continuity.py` implements the six checks and the four-outcome contract, with `--skip-worktree-checks` for primary placements
- the selftest suite passes: green run, each fail shape, indeterminate and tool-error shapes, the primary-placement skip form
- the Worktree-first standard section carries the Per-boundary continuity probe paragraph; the Task-boundary checkpoint duty references it; the Implement Task and Batch Rules lists carry the provisioned-checkout refusal rule
- `bash scripts/check_maintenance_pins.sh` passes with any pin this edit moved re-keyed in the same change

**Ship when:**
- the next executed run over the deployed skills passes a full boundary sequence with the probe green, or a probe failure is caught and repaired at the boundary instead of at closeout

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_run_continuity.py` *(new)*
- `agents/skills/execute-plan/SKILL.md` (the Per-boundary continuity probe paragraph in the Worktree-first standard section; one sentence appended to the Task-boundary checkpoint duty)
- `agents/skills/execute-plan/subagent-prompts.md` (the provisioned-checkout refusal rule added to the Implement Task and Implement Task Batch `## Rules` lists)

**Tests:**
- `scripts/test_check_run_continuity.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; the EXECUTION CLAIM paragraph is the claim procedure of record and this plan changes no claim mechanics
- any other Worktree-first standard lifecycle step; this plan adds one paragraph and two references, it does not rework the lifecycle

## Validation Commands

```bash
python3 -m unittest discover -s scripts -p 'test_check_run_continuity.py' -v
python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py' -v
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-06-worktree-continuity-probe.md
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-06-worktree-continuity-probe.md
```

### Task 1: The continuity probe script

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/check_run_continuity.py` *(new)*
- `scripts/test_check_run_continuity.py` *(new)*

Evidence:
- `python3 -m unittest discover -s scripts -p 'test_check_run_continuity.py' -v`; covers every checklist criterion in this task

- [x] `CheckRunContinuityTest#test_green_linked_worktree_passes`; given a scratch repo with a linked worktree on the recorded branch and the facts file, reviews directory, and baseline present, expects exit 0, `OUTCOME: pass`, and one pass line per the six checks [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_branch_mismatch_fails`; given the worktree checked out to a branch other than the recorded one, expects exit 1, `OUTCOME: fail`, and a `branch` check line naming the observed branch [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_missing_inputs_fail_individually`; given each of a missing facts file, missing reviews directory, and missing baseline with no skip sibling, expects exit 1 with exactly that check's failure line and the other checks still reported [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_baseline_skip_sibling_passes`; given `closeout-baseline-skip.json` present and the baseline absent, expects the `baseline` check to pass [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_non_linked_repo_fails_linked_check`; given the primary checkout itself as `--repo`, expects exit 1 with the `linked` check failing on equal git-dir paths [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_standalone_checkout_fails_linked_and_registered`; given a plain standalone clone (a valid repository that is not a linked worktree and appears in no registration) as `--repo`, expects exit 1 with both the `linked` and `registered` checks failing [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_broken_gitdir_is_indeterminate`; given a `--repo` whose git plumbing fails over an existing checkout (including a worktree whose registration entry was pruned while its `.git` gitfile remains), expects exit 2, `OUTCOME: indeterminate`, with evidence naming the invalid gitfile [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_usage_errors_are_tool_error`; given a missing `--branch` or a nonexistent `--repo` path, expects exit 3, `OUTCOME: tool_error` [class: REPOSITORY_TEST]
- [x] `CheckRunContinuityTest#test_primary_placement_skips_worktree_checks`; given `--skip-worktree-checks`, expects the three worktree checks reported as skipped and the input and baseline checks still enforced [class: REPOSITORY_TEST]
- [x] Write the test file implementing the nine fixtures above [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 -m unittest discover -s scripts -p 'test_check_run_continuity.py' -v` (implementation module `check_run_continuity` absent; every test errors on import) [class: REPOSITORY_TEST]
- [x] Write minimal implementation: the `check` invocation whose `registered` check enumerates `git worktree list --porcelain` from the resolved common dir and compares the worktree's realpath, whose git plumbing failure over an existing checkout classifies the whole run exit 2 and suppresses per-check fail lines, and which carries the six checks, the skip flag, and the four-outcome contract per `scripts/OUTCOME_CONTRACT.md` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: probe run continuity at task boundaries so mid-run state loss stops the boundary instead of surfacing at closeout` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Wire the boundary gate and the worker refusal rule

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

Evidence:
- `grep -c "Per-boundary continuity probe" agents/skills/execute-plan/SKILL.md`; covers the probe paragraph's presence
- `grep -c "Provisioned checkout" agents/skills/execute-plan/subagent-prompts.md`; covers the refusal rule in both implement templates (expect 2)
- `bash scripts/check_maintenance_pins.sh`; covers no pin names a span this edit moved
- `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py' -v`; covers the shared-body gates over the edited skill files

- [x] Add the **Per-boundary continuity probe** paragraph to the Worktree-first standard section after the Transfer-in implementation paragraph: the probe invocation over the run's recorded identity, and the exit-1 stop-and-repair routing (re-transfer inputs per the Transfer-in implementation, re-capture or skip-record the baseline, re-run to green; a worktree or branch failure stops for operator disposition, never self-re-provisioning) [class: IMPLEMENTATION_REQUIRED]
- [x] Carry the paragraph's remaining outcome branches: exit 2 and exit 3 stop the boundary and are never read as a pass, a run without a final `OUTCOME:` line is a tool error, and the primary-placement form passes `--skip-worktree-checks` so the three worktree checks report skipped [class: IMPLEMENTATION_REQUIRED]
- [x] Append one sentence to the Task-boundary checkpoint duty: each green task boundary also runs the per-boundary continuity probe before the boundary stands as resumable state [class: IMPLEMENTATION_REQUIRED]
- [x] Add a numbered rule to the Implement Task template's `## Rules` list and the same rule to the Implement Task Batch template's `## Rules` list: the worker stays inside the provisioned checkout its launch context names, returns `blocked` naming the missing worktree or branch, and never creates a worktree, branch, or checkout to recover [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; re-key any pin naming a span this edit moved in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 -m unittest discover -s scripts -p 'test_execute_plan_runtime.py' -v` [class: REPOSITORY_TEST]
- [x] Commit: `feat: wire the continuity probe into the task boundary and bar workers from provisioning their own checkout` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-wcp on branch 2026-10-06-worktree-continuity-probe (base be5f9a4a). Task 1 commit 136aba00 (probe script + 9-test suite, RED confirmed first; one blocking interim-review finding on the indeterminate/tool-error boundary folded by amend, plus the single-parser delegation to facts_paths), Task 2 commit 17ae0ec5 (probe paragraph in the Worktree-first standard after Transfer-in, checkpoint-duty sentence, refusal rule in both implement templates; no pin re-keying needed), fold commit 9feaafe2 (outcome-contract register row for the born-conformant probe). Phase 3 panel: zero blocking; two mediums dispositioned as the register-row fold and the backlog row below; low residuals left in place with evidence in the staging record. Both execution dependencies (done-boundary-evidence-gates be5f9a4a, live-claim-plan-deletion-fence d6948519) landed before this run started.

Backlog capture (off-plan, plan-level): docs/history/backlog/2026-10-06-continuity-probe-baseline-recapture-loss.md - the exit-1 repair arm's re-capture-the-baseline route can freeze surviving artifacts as pre-existing in a surviving-state loss shape, reintroducing the silent-loss class this plan closes; fixing it needs a plan-level amendment, not an in-task edit.
