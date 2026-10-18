# Plan: WIP auto-checkpoint (D-10 as durable mechanism across execute-plan and the authoring workflow)

Backlog origin: docs/history/backlog/2026-10-09-authoring-plan-artifact-not-transferred-before-removal.md and docs/history/backlog/2026-10-09-execute-plan-restored-manifest-missing-terminal-receipts.md (the PLAN-PROMPTS entry `wip-auto-checkpoint` carries the operator-confirmed prompt; sanctioning policy directive D-10)
Driving force: reliability
Design input: docs/maintenance/operator-directives.md (D-10: work-in-progress is checkpointed, and no worktree dies holding owned work); docs/maintenance/machinery-blocker-audit-2026-10-09.md suggestion 4; the witnessed losses (the 8-hour quota-wall stall, the destroyed authoring plan)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-wip-auto-checkpoint-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-wip-auto-checkpoint.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- Checkpoint commit: a mechanical safety commit of a lane's owned work-in-progress on its own worktree branch, carrying the checkpoint commit-marker convention (`wip:` subject prefix) so the landing squash and the done classification can identify it; never operator-approved, never semantic.
- Checkpoint boundary: every task boundary and every pause signal (quota pause, budget pause, stand-down, carrier expiry) for execution lanes; every authored plan write for authoring sessions.
- Removal preflight: an owned-files-clean check run before any worktree removal, whose report records a transfer or commit for every owned file - the witnessed loss was an uncommitted authoring plan destroyed by removal.
- The resume restart: an execution resume path restarts from the last checkpoint (the worktree branch's tip), composing with the coordination plan's restored-worktree resume arm rather than duplicating it.

## Why

Two witnessed losses share one cause: uncommitted owned work destroyed or stalled by lane events. The 2026-10-07/08 quota-wall stall held uncommitted work-in-progress for roughly eight hours; the authoring plan of 2026-10-09 was destroyed by worktree removal before any recovery could run. Directive D-10 states the policy (commit at every task boundary and pause signal, no worktree removed while holding uncommitted owned files, checkpoints mechanical and never operator-approved); this plan lands it as durable mechanism so the policy survives the session and applies in every runtime. The value is autonomy exactly when the operator is absent.

## Gist & Examples

TLDR: lanes commit their owned work-in-progress at task boundaries and pause signals under a `wip:` marker the landing absorbs unchanged; worktree removal runs an owned-files-clean preflight; authoring sessions checkpoint the plan file at every authored write.

Before: a quota wall strands uncommitted work for hours; a worktree removal destroys an authored-but-uncommitted plan; recovery after loss is the only tool.

After: the same quota wall leaves the work committed at the last task boundary (the resume restarts from it); the removal preflight refuses with a report naming the uncommitted owned file and its remedy (commit or transfer) before anything is destroyed.

Edge cases: checkpoint commits never trip the semantic plan-change classifier (code checkpoints leave plan bytes unchanged, so a delta round is never triggered by a checkpoint); the final squash landing absorbs checkpoint commits unchanged (the landing's staged-set derivation already reads the branch delta); a worktree with zero owned files at removal passes the preflight trivially; the claims-drift rows stay out of scope (the entry's rejected alternatives do not name them and they are claim-surface fixes with their own witnesses).

## Outcome

The uncommitted-work loss class is closed at both witnessed shapes: execution and authoring lanes checkpoint mechanically at the named boundaries, the landing and classification machinery treat checkpoints as first-class commits, no worktree is removed while holding uncommitted owned files, and no operator approval is ever required for a checkpoint.

Gate delta: one checkpoint duty in the execution blueprint and one in the authoring payload (the pause-signal boundary they already name gains the mechanical commit), one commit-marker convention with its landing/classification recognition, the removal preflight in the execute-plan Worktree-first transfer-out and the plans-skill final handoff (the witnessed loss surface), the resume restart sentence beside the coordination plan's restored-worktree arm; pins added beside their provenance; no new state schema beyond the existing runtime manifest and claim file, no new ledger, no refusal added or removed, operator approval never required.

## Assumptions

- The commit-marker convention is the `wip:` subject prefix on the worktree branch: recognizable by grep at the landing squash (the squash absorbs whatever the branch carries, so recognition is for the done classification and human reading, not a landing precondition), cheap, and collision-free with the repo's conventional subject prefixes. Basis: the entry's "recognizable checkpoint commit-marker convention" wording and the landing's branch-delta derivation.
- The landing squash absorbs checkpoint commits unchanged with no landing-code change: the worktree-complete landing derives its staged set from the branch delta and verifies tree equality, both indifferent to how many commits the branch carries. Basis: the landed landing lifecycle (the branch delta derivation, the tree-equality gate) and the entry's "the final squash landing absorbs checkpoint commits unchanged".
- The dirt-classification verification is a test-arm duty, not a code change: the sweep-gate and classification behavior over a checkpointed tree (clean worktree, checkpoint commits in history) must be verified by fixtures proving the classification sees a checkpointed tree as clean, because the classification reads working-tree state, not history. Basis: the entry's arm (b) verify wording and the classifier's working-tree read surface.
- The removal preflight lands in the two witnessed surfaces - the execute-plan Worktree-first transfer-out (the execution lane's removal path) and the plans-skill final done handoff (the witnessed loss surface) - as a NEW pre-removal gate built in `scripts/worktree_closeout_migrate.py` (the existing sweep is report-by-default over `-wt-`-shaped candidates, not a per-removal owned-files gate; the gate-removal mode is the pre-removal precedent), plus a skill-text preflight duty naming the owned-files-clean report; the owned set includes the plan file's byte-identical presence at the primary destination per the backlog row's Expected fix.
- The authoring checkpoint (arm d) is a plans-skill duty: at every authored plan write the authoring session commits the plan file on its branch (the authoring worktree already exists per the Worktree-first standard, and the commit is the same mechanical `wip:` shape). Basis: the entry's arm (d) and the authoring worktree's existence.
- The unconsumed-successor-handoff row is dispositioned under arm (b) at execution time (the entry's own prune receipt witnesses its origin row consumed by the successor plan's reconcile-worker-start transition; the remaining disposition duty rides this plan's Task 2 as the named reconcile-arm check). Basis: the entry's Task (b) and its prune receipt.
- Residual accepted: checkpoint commits add merge-lock-free commits to the branch between landings; the landing absorbs them and the history reads slightly noisier - the price of never losing work. The resume-restart sentence is likewise a skill-lane duty (the runtime resume is manifest/claim-state driven and stays read-only; the sentence documents the takeover's existing branch-tip behavior for the lane, promising nothing new from the runtime). Basis: D-10's own trade and the runtime's read-only default.

Decision points requiring a grill: none remain (the operator confirmed the program as D-10; the entry fixes the four arms, the marker convention, the constraints - no new schema, no new ledger, never operator-approved - and the rejected alternatives including the stash shape and the approval-gated shape).

## Standing constraints

- Checkpoint commits are mechanical safety commits and never require operator approval; they never change plan bytes (code checkpoints), so the semantic plan-change classifier is never tripped by a checkpoint.
- No new state schema beyond the existing runtime manifest and claim file; no new ledger; the coordination plan's lock and claim semantics are composed with, never duplicated.
- The full battery stays green at every task landing: the runtime suites (scripts/test_execute_plan_runtime.py and its codex twin), the done-gates suite (~/.agents/venvs/ai-playbook-test/bin/python3 -m pytest), the parallel-work regressions (scripts/test_parallel_work_regressions.py), the pins suite, the liveness test, em-dash, hygiene; a red suite stops the task for reconciliation, never a weakened check.
- Deploy truth: the skill and script edits reach their runtime homes at this plan's merge-locked landing (the landing is the deploy).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the checkpoint duties are additive text and the preflight is additive script behavior, so each task reverts cleanly; the pins added beside provenance revert with their tasks.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the four arms each land in their named home with the marker convention, the classifier never trips on checkpoints, and the preflight refuses a worktree holding uncommitted owned files with a report naming the file and its remedy.
- regression safety: the runtime suites, the done-gates suite, the parallel-work regressions, and the pins suite green at every landing; the landing squash's behavior over checkpoint commits proven by fixture.
- scope discipline: the changes touch only the execution blueprint, the authoring payload, the plans-skill handoff, the execute-plan transfer-out, the migrate script's preflight surface, the done classification's marker recognition, the pins, and the covering tests.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- The next execution pause commits its work-in-progress under the marker, the next worktree removal runs the preflight, and a resume restarts from the last checkpoint; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the checkpoint duty at task boundaries and pause signals; the transfer-out preflight; the resume restart beside the restored-worktree arm)
- `agents/skills/execute-plan/subagent-prompts.md` (the blueprint's checkpoint duty mirror, if the payload carries the boundary list)
- `agents/skills/plans/SKILL.md` (the authoring checkpoint duty at every authored write; the final handoff preflight - the witnessed loss surface)
- `scripts/worktree_closeout_migrate.py` (the removal preflight's owned-files-clean check and report)
- `agents/skills/done/SKILL.md` (the done classification's checkpoint-marker recognition, if the classification needs the marker named)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (the landing-absorption fixture: fixture-created checkpoint commits, the landing absorbs, the classifier untouched)
- `scripts/test_done_sweep_gates_lib.py` (Task 2: the classification fixture over the porcelain reader)
- `scripts/check_maintenance_pins.sh` (the new pins beside provenance)

**Docs:**
- `docs/history/backlog/2026-10-09-authoring-plan-artifact-not-transferred-before-removal.md` (read-only this plan; flipped covered by the landing rider)
- `docs/history/backlog/2026-10-09-execute-plan-restored-manifest-missing-terminal-receipts.md` (read-only this plan; flipped covered by the landing rider)
- `docs/maintenance/operator-directives.md` (D-10, the policy of record, cited not edited)

**Read-only (referenced, never edited):**
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (suggestion 4)
- `scripts/execute_plan_runtime.py` (read-only unless a test proves a code surface needs the marker; the default is skill-text duties)

**Receipts:**
- Origin rows: the two backlog rows above (Status: open; the landing rider flips them covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## wip-auto-checkpoint` (frozen under docs/tmp/authoring-claims/2026-10-10-wip-auto-checkpoint.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "wip:" agents/skills/execute-plan/SKILL.md   # expect >=1 (the marker convention)
grep -c "checkpoint" agents/skills/execute-plan/SKILL.md   # expect >=2 (task boundaries + pause signals)
grep -c "checkpoint" agents/skills/plans/SKILL.md   # expect >=1 (the authoring duty)
grep -c "owned-files-clean" agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md   # expect >=1 each (the preflight homes)
grep -c "owned-files-clean" scripts/worktree_closeout_migrate.py   # expect >=1 (the new pre-removal gate)
grep -c "restarts from the last checkpoint" agents/skills/execute-plan/SKILL.md   # expect >=1 (the resume restart)
```

**Tests:**
```bash
python3 scripts/test_execute_plan_runtime.py -k checkpoint   # exit 0 (the new fixture)
python3 scripts/test_parallel_work_regressions.py   # exit 0
~/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_done_sweep_gates_lib.py -q   # exit 0
bash scripts/check_maintenance_pins.sh   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the checkpoint marker convention and the execution-lane duty

Files:
- agents/skills/execute-plan/SKILL.md
- agents/skills/execute-plan/subagent-prompts.md
- scripts/test_execute_plan_runtime.py
- scripts/check_maintenance_pins.sh

- [x] State the checkpoint commit-marker convention (`wip:` subject prefix on the worktree branch) in the execute-plan skill beside the task-boundary duty: execution lanes commit owned work-in-progress at every task boundary and every pause signal (quota pause, budget pause, stand-down, carrier expiry), the commits are mechanical safety commits never requiring operator approval, plan bytes are never changed by a code checkpoint (the semantic plan-change classifier is never tripped), and the final squash landing absorbs checkpoint commits unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] State the owned-commits-ledger disposition explicitly: the prompt arm's 'the owned-commits ledger records them' clause is superseded by the no-new-ledger constraint - the checkpoint commits are their own branch record (the `wip:` marker is greppable), and the runtime manifest's existing checkpoint fields stay the structured record where a run uses them; no new ledger lands. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the resume-restart sentence beside the coordination plan's restored-worktree resume arm as the skill-lane duty it is: a resume session restarts from the last checkpoint (the worktree branch's tip, the state the takeover adopts), composing with that arm's claim takeover rather than duplicating it; the unconsumed-successor-handoff disposition rides this arm's reconcile check per the entry. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the landing-absorption fixture in `scripts/test_execute_plan_runtime.py`: the fixture CREATES the `wip:` checkpoint commits itself (the pause-to-commit act is the skill duty for the lane, not runtime code - the plan keeps the runtime read-only), then asserts a subsequent landing absorbs the checkpoint commits unchanged (tree equality holds) and the squash commit contains their content. The classification arm (the post-checkpoint tree reads clean) is covered by the done-gates suite in Task 2, where the classification surfaces live. The `-k checkpoint` validation command asserts at least one test ran (the vacuous NO-TESTS-RAN pass is not a pass). Add the pins beside provenance. [class: REPOSITORY_TEST]
- [x] Run the runtime suite, the pins suite, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 2: the removal preflight and the authoring checkpoint duty

Files:
- agents/skills/plans/SKILL.md
- agents/skills/execute-plan/SKILL.md
- scripts/worktree_closeout_migrate.py
- scripts/test_done_sweep_gates_lib.py
- scripts/check_maintenance_pins.sh

- [x] Land the removal preflight in the two witnessed surfaces: the plans-skill final done handoff and the execute-plan Worktree-first transfer-out each run the owned-files-clean check before any worktree removal, and a worktree holding uncommitted owned files is never removed - the check's report records a transfer or commit per owned file first, per D-10. The check is a NEW pre-removal gate built in `scripts/worktree_closeout_migrate.py` (the existing sweep is report-by-default over `-wt-`-shaped candidates, not a per-removal owned-files gate; the gate-removal mode is the pre-removal precedent), and the owned set includes the plan file's byte-identical presence at the primary destination per the backlog row's Expected fix. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the authoring checkpoint duty to the plans skill: at every authored plan write (not only at task boundaries), the authoring session commits the plan file on its branch under the `wip:` marker. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the classification fixture in the done-gates suite (`scripts/test_done_sweep_gates_lib.py`): the dirt classification (the porcelain reader) sees a post-checkpoint tree (clean worktree, `wip:` commits in history) as clean, proving checkpoints are first-class. [class: REPOSITORY_TEST]
- [x] Run the full battery: the runtime suite, the done-gates suite, the parallel-work regressions, the pins suite, the liveness test, the em-dash scan over the touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
