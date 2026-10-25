# Plan: Warn when required reviewed paths are absent from task files

Backlog origin: docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md
Driving force: code-quality (a reviewed task should declare the files its required changes need)
Authoring claim: docs/tmp/authoring-claims/2026-10-09-execute-plan-live-claim-scope-widening.md (session c2c50c7a-4ec5-4c4d-924a-9f140cb7418a)
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-execute-plan-live-claim-scope-widening-r*.md
Execution budget: 1.5h total, largest task 1.5h

## Terms

- Explicit must-fix scope: the `Explicit must-fix` path list in a plan's `## Review Scope` section.
- Files-coverage arm: the warning-only `plan_files_coverage_warnings` check in `scripts/plan_readiness.py`, registered as `script:plan-files-coverage-arm` in `scripts/machinery_registry.json`.
- Task annotation: `(Task N)` assigns an explicit must-fix path to the task that implements it.
- Review-only annotation: `(review-only)` marks an explicit must-fix path that no task in this plan edits.

## Why

A plan can list a required implementation path in explicit must-fix scope without identifying its owning task, or list it under a different task. Readiness already warns about paths quoted by task acceptance items; it does not verify ownership for explicit must-fix paths.

## Gist & Examples

TLDR: readiness warns when an implementation path in explicit must-fix scope is absent from its assigned task Files list, surfacing a reviewed-scope gap before execution.

Before: `Review Scope` lists `scripts/example.py` but does not assign it to Task 1, or assigns it to Task 2 even though Task 1 must edit it. The task boundary stays ambiguous or wrong.

After: both readiness paths print a warning when an explicit must-fix path lacks an ownership annotation, names a missing task, or is absent from its named task's `Files:` list, even if a sibling lists it. A `(review-only)` annotation records that no task owns edits. Existing acceptance-item coverage remains unchanged. Warnings do not change the gate result.

Edge cases: a `(Task N)` annotation is checked against that exact task; a missing annotation, malformed marker, nonexistent task number, or undeclared path warns. `(review-only)` suppresses task-file matching. Other Review Scope categories do not trigger the new check. Task-specific acceptance coverage remains owned by the existing Files-coverage warning.

## Outcome

Readiness warns when an explicit must-fix path lacks a valid ownership annotation or does not match the named task's `Files:` list.

- A `(Task N)` annotation names the task owner; a sibling task declaration does not satisfy it.
- A `(review-only)` annotation explicitly records that no task owns edits.
- The origin is split: this plan covers pre-execution scope detection; a new backlog row retains the launched-claim recovery gap.
- The covered origin is archived under `docs/history/backlog/completed/` with `Status: covered`; the Plans skill, completed-backlog guide, and document registry agree with that lifecycle.
- Existing acceptance-item coverage warnings remain unchanged and continue to report task-specific quoted paths absent from that task's `Files:` list.

Gate delta: extend the existing warning-only Files-coverage arm; add no refusal, blocker, schema field, lock, or required ceremony. Simplification: keep both path sources in the existing arm and machinery registry entry, removing the need for a separate checker, warning channel, and machinery-registry row. Machinery admission: the witnessed incident is this plan's origin row, where a required path was absent from its launched task claim; expected catch frequency is any plan with an explicit must-fix path that lacks a valid ownership annotation or whose annotated task does not list it in `Files:`; false-positive cost is one advisory warning per missing or mismatched annotation, adjudicated before execution; retain the existing review date 2027-01-12 and no-catch sunset, and record adjudicated true catches in the existing registry note. The new backlog row tracks the distinct launched-claim recovery incident.

## Assumptions

- Every explicit must-fix path carries either `(Task N)` or `(review-only)`; readiness does not infer ownership from another task's file list. Existing acceptance-item coverage continues to check task-specific quoted paths. Basis: the task Files contract and `plan_files_coverage_warnings` source.
- Only the `Explicit must-fix` category is checked. Plan-related extensions and out-of-scope paths have different review semantics and are excluded. Basis: the execute-plan two-tier review contract.
- The launched-claim recovery requirement is split into `docs/history/backlog/2026-10-23-execute-plan-launched-claim-scope-recovery.md`; this plan neither implements nor closes it. Basis: the origin records a distinct post-launch failure shape and recovery boundary.
- The supplied repository instructions require covered origins to be archived. The current Plans skill and completed-backlog guide still prescribe deletion, so this task reconciles those instructions and registers the archived record. Basis: the repository-level AGENTS.md archive rule and the current conflicting lifecycle text.

Decision points requiring a grill: none (maintenance-selected authoring; the origin's prevention-first acceptance and the existing warning-only machinery posture determine the narrow implementation).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a must-fix path without an ownership annotation or missing from its named task is warned even if a sibling lists it; a review-only annotation is accepted; other Review Scope categories do not warn.
- Safety: both readiness entry points preserve exit behavior, and existing acceptance-item warnings keep their current matching and wording.
- Maintainability: the check shares the existing Files-coverage arm and registry row, with no second checker or warning surface.

**Done when:** focused readiness tests cover a missing annotation even when a sibling lists the path, a malformed annotation, a task-annotated path missing from its task, an annotated covered path, a missing task target, a review-only path absent from every task `Files:` list, non-must-fix exclusion, and unchanged acceptance-item cases; both readiness entry points emit the warning on their successful paths with Git repository overrides isolated; the full `scripts/test_plan_readiness.py` suite passes; the archive is registered, its exact immutable-history write passes the gate, and all sibling links resolve to their live follow-up.

**Ship when:** none; repository-only behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/plan_readiness.py` (Task 1) - extend the existing Files-coverage warning arm.
- `scripts/machinery_registry.json` (Task 1) - update the existing arm's admission note for this incident and scope.

**Tests:**
- `scripts/test_plan_readiness.py` (Task 1) - cover task annotations and preserve existing behavior.

**Documentation and records:**
- `agents/skills/plans/SKILL.md` (Task 1) - replace the existing Files-coverage rule with a shorter rule covering acceptance paths plus `(Task N)` and `(review-only)` explicit must-fix annotations.
- `agents/skills/plans/SKILL.md` (Task 1) - replace the backlog-origin deletion instruction with the repository's covered-origin archive procedure, paying for any growth within the same file.
- `docs/history/backlog/completed/README.md` (Task 1) - align the completed backlog home with archived covered origins.
- `docs/maintenance/document-registry.md` (Task 1) - register the completed origin archive.
- `docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md` (Task 1) - move the narrowed and covered origin to the completed home.
- `docs/history/backlog/completed/2026-10-09-execute-plan-live-claim-scope-widening.md` (Task 1) *(new)* - completed origin archive.
- `docs/history/backlog/2026-10-23-execute-plan-launched-claim-scope-recovery.md` (Task 1) *(new)* - record the remaining launched-claim recovery requirement.
- `docs/history/backlog/2026-10-05-execute-plan-reviewed-scope-recovery.md` (Task 1) - update its Cluster pointer to the completed origin.
- `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md` (Task 1) - update its Cluster pointer to the completed origin.
- `docs/history/backlog/2026-10-10-execute-plan-recovery-full-stem-resolution.md` (Task 1) - update its Cluster pointer to the completed origin.
- `docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md` (Task 1) - point its completed-origin reference at the launched-claim recovery follow-up.

**Plan-related extension:** none.

**Out of scope; reject unless plan-related:**
- Adding a blocking readiness refusal or changing an exit code.
- Implementing or claiming completion of launched-claim scope recovery; that work is tracked by the new follow-up row.
- Changing matching for `Plan-related extension` or `Out of scope` categories.

## Design Invariants

- Readiness exit codes and output schemas do not change.
- Existing acceptance-item warnings keep their current matching and wording.
- Explicit must-fix scope is the only new token source.
- A warning never widens a task's allowed paths or authorizes a launch.

## Validation Commands

```bash
python3 scripts/test_plan_readiness.py  # expect: OK (exit 0)
python3 scripts/doc_registry_validator.py validate  # expect: exit 0 and no unregistered warning for the README or archived origin
git -c core.quotePath=false diff --cached --name-status --no-renames -- docs/history/backlog/completed/README.md docs/history/backlog/completed/2026-10-09-execute-plan-live-claim-scope-widening.md | python3 scripts/doc_registry_validator.py check-writes --stdin  # stage these exact paths first; expect licensed README override, licensed archive add, and exit 0
```

A command's expected outcome on its comment line is the pass bar: the checkbox owning the command fails unless it exits 0.

### Task 1: Warn on explicit must-fix paths missing from their task

Context surface: this task, `## Terms`, `## Design Invariants`, and `## Review Scope`.

Files:
- `scripts/plan_readiness.py` *(edited)*
- `scripts/test_plan_readiness.py` *(edited)*
- `scripts/machinery_registry.json` *(edited)*
- `agents/skills/plans/SKILL.md` *(edited)*
- `docs/history/backlog/completed/README.md` *(edited)*
- `docs/maintenance/document-registry.md` *(edited)*
- `docs/history/backlog/2026-10-23-execute-plan-launched-claim-scope-recovery.md` *(new)*
- `docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md` *(moved)*
- `docs/history/backlog/completed/2026-10-09-execute-plan-live-claim-scope-widening.md` *(new)*
- `docs/history/backlog/2026-10-05-execute-plan-reviewed-scope-recovery.md` *(edited)*
- `docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md` *(edited)*
- `docs/history/backlog/2026-10-10-execute-plan-recovery-full-stem-resolution.md` *(edited)*
- `docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md` *(edited)*

Primary class anchors:
- `plan_files_coverage_warnings` in `scripts/plan_readiness.py`
- `run_pre_round` in `scripts/plan_readiness.py`
- `evaluate_readiness` in `scripts/plan_readiness.py`

- [x] [class: IMPLEMENTATION_REQUIRED] Extend `plan_files_coverage_warnings` to warn for missing or invalid ownership annotations and for `(Task N)` paths absent from that task's `Files:` list; accept `(review-only)` and preserve acceptance-item warnings.
- [x] [class: IMPLEMENTATION_REQUIRED] Keep the warning on successful pre-round and full-readiness paths only; preserve exit codes, schemas, and existing failure-path output.
- [x] [class: REPOSITORY_TEST] Test missing, malformed, mismatched, covered, and nonexistent task annotations; review-only, non-must-fix, sibling-listed, and unchanged acceptance cases.
- [x] [class: REPOSITORY_TEST] Give the `(review-only)` case a must-fix path absent from every task `Files:` list and assert that it emits no ownership warning.
- [x] [class: REPOSITORY_TEST] On both entry points, require named warnings for Task 2-only path annotated `(Task 1)` and sibling-listed path marked `(Task one)`.
- [x] [class: REPOSITORY_TEST] Clear inherited Git repository/index overrides for both CLI fixture repositories.
- [x] [class: IMPLEMENTATION_REQUIRED] Shorten the Files-coverage rule; retain acceptance paths and require `(Task N)` with matching `Files:` or `(review-only)` for each must-fix path, without growing the skill.
- [x] [class: IMPLEMENTATION_REQUIRED] Update `script:plan-files-coverage-arm` with the incident, catch scope, warning cost, review date, and sunset.
- [x] [class: IMPLEMENTATION_REQUIRED] Narrow the origin row to the pre-execution scope warning, link its launched-claim requirement to the new follow-up row, archive it under the completed home with `Status: covered`, and cite this plan as witness.
- [x] [class: IMPLEMENTATION_REQUIRED] Reconcile every operative deletion instruction in the Plans skill, including Plan Lifecycle and receiving-review integration, and the completed-backlog guide with the archive rule. Register both in the registry's parsed first table; give the README a dated `user-approved` audit note naming this run as cleanup owner, keep it through landing, then clear it in a post-landing cleanup commit and record the receipt.
- [x] [class: IMPLEMENTATION_REQUIRED] Create a launched-claim recovery follow-up row that carries the origin evidence and acceptance boundary; update related Cluster pointers to the completed origin.
- [x] [class: IMPLEMENTATION_REQUIRED] Specify either reviewed, receipt-fenced widening or bounded release-and-requeue without waiting on an unrelated lease.
- [x] [class: IMPLEMENTATION_REQUIRED] For widening, preserve baseline and claim-identity fencing, review-digest checks, no-manual-manifest-edit, worker-terminal and worktree-drift checks, reviewed-plan-derived scope, atomic evidence and digest recomputation, and ordinary preflight before relaunch.
- [x] [class: IMPLEMENTATION_REQUIRED] Require recovery to refuse stale digests, live workers, altered launch baselines, unreviewed paths, and caller-supplied replacement scope.
- [x] [class: IMPLEMENTATION_REQUIRED] Update the selector-test backlog row's reference from the covered origin to the launched-claim recovery follow-up.
- [x] [class: REPOSITORY_TEST] Run the readiness suite and registry `validate` command; the suite and validator exit 0, and validator output has no unregistered warning naming the README or archived origin.
- [x] [class: REPOSITORY_TEST] Stage the README and archived origin, feed their actual cached name-status lines to `check-writes`, and require exit 0 with the README override and archive add licensed. Keep the override through landing; in the post-landing cleanup commit, clear it, record the cleanup receipt, and rerun `validate`.
- [x] [class: REPOSITORY_TEST] Run the document-registry validation command from the repository root after the archive registration and again after post-landing cleanup; both runs exit 0 and neither reports the README or archived origin as unregistered.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `execute-plan: warn on uncovered reviewed scope paths`

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-09-execute-plan-live-claim-scope-widening.md` (filed 2026-10-09; recover when a reviewed plan scope exceeds a live execute-plan claim): the pre-launch half is implemented by this plan (the Files:-coverage arm's explicit must-fix ownership check, Task 1); the row was narrowed to that half and flipped `Status: covered` in place during execution, its disposition is folded here, and the file is deleted in this archive commit per the repository's fold-then-delete lifecycle (AGENTS.md covered-row rule, reconciled 2026-10-24). The post-launch half (receipt-fenced widening or bounded release-and-requeue for an already-launched claim) lives on as the open row `docs/history/backlog/2026-10-23-execute-plan-launched-claim-scope-recovery.md`, which carries the origin evidence and acceptance boundary.
- Execution note: the plan's Assumption 4 and its archive-under-`docs/history/backlog/completed/` sub-steps (origin move, README audit note, registry rows for the README and archived origin, the `check-writes` staging validation) predate the 2026-10-24 lifecycle reconcile and were vacuous under the rule at HEAD; they were marked complete on that basis with the disposition recorded in the run manifest and disclosed in the task commit, never silently skipped.
