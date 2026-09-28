- **Filed:** 2026-09-30
- **Status:** done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-execute-plan-zero-allowed-path-refuse-at-create.md, squash main b39383de, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** consumer-feedback (witnessed twice in one day: the residual-exit ordering execution and the emdash-residuals execution, both in this repo)
- **Driving force:** reliability
- **Class:** fence-class

# Create accepts a zero-allowed-path task that launch always refuses

## Problem

The `create` operation validates each task's allowed-path entries but accepts an empty list, seeding the task as launchable state. The launch envelope's worker-role contract requires a non-empty allowed-paths list (`_worker_role_contract` returns None when `not allowed_paths` under evidence enforcement), so every `continue` for such a task refuses with "canonical single-task worker role is missing or mismatched". The plan shape that produces this is any verification-only task whose plan section declares no `Files:` (two witnessed plans used exactly that shape: one wrote "Files: - none (verification only)", the other simply had no Files list). The run wedges at that task: the launch refusal is read-only, so the claim never reaches the launched hold that `recover-evidence-contract` requires, and no other driver operation replaces the immutable contract on an unlaunched claim.

The only sanctioned exit today is outside the driver: a non-semantic plan correction giving the task a real `Files:` entry (the file its gates execute, never edited), a focused re-cert review of the correction, then a fresh session re-seed whose manifest is rebuilt by `create` from the corrected plan, replaying the already-completed tasks' done receipts against their existing commits. That is three manual disciplines per occurrence, and the correction's classification (the added path is never exercised) is judgment the driver could make unnecessary.

## Observed versus expected

- Observed: `create` seeds what `launch` unconditionally refuses; the wedge is discoverable only at the first `continue`, after seeding "succeeded".
- Expected: one of the two boundaries aligns. Preferred: `create` refuses a task whose allowed_paths is empty with an actionable error naming the task and the verification-only remedy (declare the file its verification commands execute); acceptable: the launch envelope admits a verification-only contract (evidence owner worker, non-empty criteria and commands, empty write scope) as a special shape with no write authorization.

## Witnesses

- Residual-exit same-day ordering execution (landed 10dd0ec9): Task 3 "Files: - none (verification only)"; wedged at launch; resolved via plan correction + re-cert + session-2 re-seed with receipt replay.
- Em-dash residuals canary execution (superseded by peer landing abe72523): Task 4 (final validation, no Files section); same refusal.
- Related distinct item: docs/history/backlog/2026-09-28-execute-plan-preimplemented-task-closeout.md (done fencing for baseline-present work; different boundary, same evidence-enforcement family).
