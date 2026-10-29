# Plan: Phase 2 baseline suite repair

Backlog origin: docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md, docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md
Driving force: code-quality + efficiency
Plan review record: .ai-playbook/reviews/2026-10-29-plan-review-phase2-baseline-repair-r*.md
Authoring claim: 2026-10-29-phase2-baseline-repair.md (session 01a188a2-1a1c-75a0-a934-1984adb3c891)

## Terms

- **Baseline failure:** a test failure reproduced on the configured local `main` base, independent of the paused stacked-plan changes.
- **Contract pin:** an assertion for an externally visible output, error, exit code, or state transition that must remain stable.
- **Repair canary:** a focused failing example that proves the defect before the smallest repair is written.
- **Full inventory:** every tracked `scripts/test_*.py` suite run with the repository's prescribed pytest or unittest command.
- **Phase 2:** the execute-plan validation phase that runs the full tracked suite after task work and before final review.
- **Paused stacked-plan run:** the preserved execution worktree and claim for the separate stacked-PR plan that exposed these baseline failures.
- **Quota-wall doctrine:** the execute-plan and maintenance text governing retry classification, timed resume, and launch-wave records after a usage-wall refusal.
- **Claim and receipts:** the local execution claim and append-only evidence files that bind a run to its worktree, commit, and validation results.

## Why

The paused stacked-plan run found 26 failures in six unrelated suites, and the same failure families were reproduced against local `main`. Leaving those reds in place prevents the normal Phase 2 inventory from distinguishing a new regression from existing drift. This plan repairs the baseline contracts in isolated tasks and leaves the paused stacked run untouched.

## Gist & Examples

TLDR: repair six baseline test families and restore trustworthy full-suite validation, driven by code quality and efficiency.

**Before (today):** The telemetry, landing, quota-doctrine, rearm, rejected-archive, and machinery checks contain pre-existing red paths. Some are stale output pins or fixture closure gaps; others are production or registry drift. A full inventory therefore stops before the stacked plan can claim a clean Phase 2.

**After (this plan):** Each failure family has a named canary, the smallest contract-preserving repair, and focused validation. The six suites pass on a refreshed local base, the complete tracked inventory is rerun, and any remaining red is reported as an explicit blocker rather than hidden by weakened assertions.

For example, the telemetry task updates only stale fixture pins and the copied helper closure after a canary proves the real scripts still behave correctly. The rearm task first proves the listing-derived state transition, then repairs the atomic bookkeeping path without changing unrelated state fields. The machinery task either restores a green registry baseline or records that the current base is already green and closes only the two matching backlog rows.

## Outcome

The repository's six baseline failure families are repaired or explicitly isolated so the full tracked test inventory is a trustworthy Phase 2 gate.

- The six focused suites pass with contract and negative-path coverage intact.
- The full tracked `scripts/test_*.py` inventory is rerun at one refreshed HEAD with every command and result recorded.
- The paused stacked-plan run can later resume from its preserved claim and worktree without inheriting unrelated repair edits.

Gate delta: no net new refusal class, hard gate, fence, protocol layer, schema field, or blocking review duty. Task 4 restores the quota-wall policy in its declared execution owner from `docs/history/plans/completed/2026-10-08-quota-wall-dispatch-doctrine.md` and the still-operative `agents/skills/maintenance/zcode.md` source; it does not add a new refusal surface or checked set. The remaining tasks repair existing behavior, fixtures, registry rows, and contract pins and remove no existing guard.

## Assumptions

- The six scope families and the 26-failure count are the paused run's reproduced evidence: invocation telemetry (6), landing helper (3), machinery inventory (1 observed during that run), quota-wall doctrine (12), rearm-on-touch (3), and rejected-archive lifecycle (1); each task re-runs its canary on the current local `main` before editing.
- Personal and pet project policy keeps all work local; no fetch, remote query, PR, push, merge, or remote branch operation is part of this plan.
- The two machinery backlog rows are the durable origin for the registry-red family; the other five families are sourced from the paused-run baseline report and their named tests.

Decision points requiring a grill: Decision: park the stacked execution and repair these six baseline families in a separate plan, source: user reply in this conversation, date: 2026-10-29, affected sections: scope and execution boundary; Decision: keep the paused run's claim, worktree, and receipts intact while this plan is authored, source: user reply in this conversation, date: 2026-10-29, affected sections: outcome and standing constraints; Decision: do not execute this repair plan in the authoring turn, source: user reply in this conversation, date: 2026-10-29, affected sections: ship condition and handoff.

## Standing constraints

- Work only from local repository refs and the configured local `main`; never inspect or mutate remote state.
- Preserve observable contracts unless a canary proves the contract itself is wrong; do not weaken an assertion merely to turn a suite green.
- Keep task file ownership disjoint. If a repair needs a path owned by another task, stop and record the dependency instead of editing across the boundary.
- Run focused tests after each task, then rerun the complete tracked inventory at one refreshed HEAD before declaring the repair plan done.
- Keep the paused stacked run separate: do not edit its plan, task sources, claim, worktree receipts, or Phase 2 evidence from this plan.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each failing family has a failing canary, a minimal repair, and passing focused evidence without weakened negative paths.
- Contract fidelity: stdout, stderr, exit status, registry ownership, and state-file mutation assertions remain explicit and meaningful.
- Scope discipline: task files are disjoint, local-only, and do not modify the paused stacked run.
- Completeness: all tracked test suites are enumerated and rerun from the same refreshed HEAD.
- Maintainability: fixture helpers and registry rows explain their source-of-truth and do not duplicate production policy.

**Done when:**

- All six task-focused suites pass on a refreshed local HEAD and the full tracked inventory is green; if any family remains red, the plan remains incomplete and records its failing command, exact witness, and operator handoff.
- The full tracked inventory prescribed by `AGENTS.md` is rerun with no missing suite identity and its receipt is saved under `docs/tmp/`.
- `git diff --check`, the public-hygiene scan, and the em-dash added-lines check pass for the repair changes.

**Ship when:** The operator chooses a later execution session for this plan and confirms the paused stacked run may resume after this plan's landed local changes. No remote merge or deployment is part of this plan. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production and workflow code:**

- `scripts/invocation_telemetry.py` (Task 1)
- `scripts/land_squash.sh` (Task 2)
- `scripts/machinery_inventory.py` (Task 3)
- `agents/skills/execute-plan/SKILL.md` (Task 4)
- `agents/skills/maintenance/zcode.md` (Task 4)
- `scripts/rearm_on_touch.py` (Task 5)
- `scripts/done_sweep_gates_lib.py` (Task 6)
- `scripts/doc_registry_validator.py` (Task 6)

**Tests and registry:**

- `scripts/test_invocation_telemetry.py` (Task 1)
- `scripts/test_land_squash.py` (Task 2)
- `scripts/test_machinery_inventory.py` (Task 3)
- `scripts/machinery_registry.json` (Task 3)
- `scripts/test_quota_wall_doctrine.py` (Task 4)
- `agents/skills/execute-plan/agent-logs.md` (Task 4)
- `scripts/test_rearm_on_touch.py` (Task 5)
- `scripts/test_rejected_archive_lifecycle.py` (Task 6)
- `scripts/test_done_sweep_gates_lib.py` (Task 6)

**Documentation:**

- `docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md` (Task 3)
- `docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above only when the change is required by a named task's canary, contract, registry ownership, or wiring. If the link is weak or speculative, leave the path unchanged and report it as out of scope.

**Out of scope; reject unless plan-related:** the paused stacked plan and its execution receipts; remote GitHub state; unrelated test failures; broad refactors; changing a gate or validator merely to bypass a refusal.

## Validation Commands

Run from the repository root using the prescribed environment:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_invocation_telemetry.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_land_squash.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_machinery_inventory.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_wall_doctrine.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_rearm_on_touch.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_rejected_archive_lifecycle.py'
git diff --check
bash scripts/scan-public-hygiene.sh
```

For the full inventory, enumerate every tracked `scripts/test_*.py` file and run the exact pytest or unittest form selected by `AGENTS.md`; record all 79 suite identities and results at the refreshed HEAD. Do not treat a passing subset as complete.

### Task 1: Restore invocation telemetry contract fixtures

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/invocation_telemetry.py`
- `scripts/test_invocation_telemetry.py`

Primary class anchors:
- `record_invocation` in `scripts/invocation_telemetry.py`

- [ ] Given the six observed telemetry failures, expects a fresh canary to identify stale CLI output pins, closeout warning drift, and the intentionally incomplete helper-copy fixture separately. [class: REPOSITORY_TEST]
- [ ] Given the canary output, expects the smallest test-only fixture or literal repair to make all 24 telemetry tests pass while keeping the real instrumented scripts and fail-open behavior under test. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a changed exit status, telemetry schema, or unlisted stderr line, expects the test to remain red and the task to stop rather than weakening the contract pin. [class: REPOSITORY_TEST]
- [ ] Run the focused telemetry suite and record 24 passing tests with no production-file change unless a canary proves a library defect. [class: REPOSITORY_TEST]
- [ ] Commit: `test: restore invocation telemetry baseline contracts` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Repair landing-helper revert audit fixture

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`

Primary class anchors:
- `run_reconcile_gate_or_refuse` in `scripts/land_squash.sh`

- [ ] Given a changed-then-reverted rolling-log entry, expects the canary to distinguish a legitimate in-commit removal receipt from a revert that removes the witness and to report the named remedy. [class: REPOSITORY_TEST]
- [ ] Given the canary's three identical failures across the landing test classes, expects one shared minimal repair in the helper or fixture contract, not three assertion relaxations. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a clean log removal and a receipt-bearing removal commit, expects the landing helper to retain its existing pass outcome and no-mutation guarantees. [class: REPOSITORY_TEST]
- [ ] Run the complete `scripts/test_land_squash.py` suite and record all 161 tests passing. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: repair reverted landing audit contract` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Reconcile machinery inventory baseline drift

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_inventory.py`
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`
- `docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md`
- `docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md`

Primary class anchors:
- `check_failures` in `scripts/machinery_inventory.py`

- [ ] Given the paused-run red receipt and the current-base probe, expects a first canary to classify each stale witness, unregistered path, state-field row, and stale removal row as an actual defect or already-resolved drift. [class: REPOSITORY_TEST]
- [ ] Given an actual drift row, expects the registry or inventory logic to receive a resolving witness or a principled disposition without suppressing future regrowth detection. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the current base is already green, expects the task to make no speculative source change and instead reconcile the two matching backlog rows with durable evidence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run both the fixture suite and `python3 scripts/machinery_inventory.py --check`, recording the exact row set and a green exit. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: restore machinery inventory baseline` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Restore quota-wall doctrine witnesses

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/test_quota_wall_doctrine.py`

- [ ] Given the twelve doctrine failures, expects a canary to identify missing or relocated doctrine text, launch-ledger wording drift, and the directive-history comparison mismatch as separate causes. [class: REPOSITORY_TEST]
- [ ] Given the authoritative execution and maintenance text, expects the smallest documentation or test-baseline repair to restore the two-class quota-wall rule, one timed resume, and launch-ledger parsing without deleting a safety clause. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a second usage-wall death, expects a named deviation; given a transient error without a reset time, expects the conformant transient classification; given a changed pre-existing directive, expects the byte-level baseline witness to stay red with the named deviation. [class: REPOSITORY_TEST]
- [ ] Run `scripts/test_quota_wall_doctrine.py` and record 16 passing tests plus a byte-level check that pre-existing directive records remain unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: restore quota wall doctrine witnesses` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Repair rearm-on-touch bookkeeping transitions

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/rearm_on_touch.py`
- `scripts/test_rearm_on_touch.py`

Primary class anchors:
- `classify_with_listing` in `scripts/rearm_on_touch.py`

- [ ] Given an enabled recognition match, expects `parent-ok`, clearing `parent_absent_since` and `rearm_note` through one targeted atomic write. [class: REPOSITORY_TEST]
- [ ] Given a live recorded parent plus a differing match, expects the adoption guards to preserve the live id while clearing only listing-derived bookkeeping. [class: REPOSITORY_TEST]
- [ ] Given a differing absent or disabled parent with an enabled recognition match, expects adoption to clear the absence timestamp and rearm note in one `os.replace` without touching unrelated fields; given no enabled recognition match, expects the earliest absence timestamp to be retained. [class: REPOSITORY_TEST]
- [ ] Given malformed state or listing input, expects the existing tool-error outcome and no state-file mutation. [class: REPOSITORY_TEST]
- [ ] Run the focused rearm suite and record all 15 tests passing. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: restore rearm bookkeeping transitions` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Repair rejected-archive lifecycle enforcement

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/doc_registry_validator.py`
- `scripts/test_rejected_archive_lifecycle.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `derive_plan_readiness_candidates` in `scripts/done_sweep_gates_lib.py`
- `cmd_check_writes` in `scripts/doc_registry_validator.py`

- [ ] Given a rejected plan, a failing active plan, and a completed control, expects `gate_plan_readiness` to keep the rejected and completed plans out of candidates, report the active failure as advisory with `failed=1` and aggregate `rc=0`, and prune the rejected, failed, and completed deliverable lines while preserving the existing warning evidence. [class: REPOSITORY_TEST]
- [ ] Given a rejected archive with valid date and reason, expects active readiness to exclude it while the live control copy remains eligible. [class: REPOSITORY_TEST]
- [ ] Given malformed rejected metadata or an unregistered rejected path, expects a hard validator finding; given a licensed add or rename into the rejected archive, expects the existing lifecycle exception. [class: REPOSITORY_TEST]
- [ ] Run the focused rejected-archive suite and record all four tests passing without weakening the readiness or write gate. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: restore rejected archive lifecycle gate` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- The two machinery backlog rows are updated only when Task 3 has durable evidence to close or defer them; no new narrative incident dossier is added to operative skill text.
- The execute-plan and maintenance source-of-truth docs are updated only in Task 4 where their quota-wall contract is missing or drifted; detailed failure evidence remains in task receipts under `docs/tmp/`.
- No README or public catalog change is required because this plan repairs existing test and workflow contracts rather than adding a skill.
