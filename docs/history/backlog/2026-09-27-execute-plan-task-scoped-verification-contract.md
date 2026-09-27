# Execute-plan: validate task-scoped verification contracts before manifest creation

- **Filed:** 2026-09-27
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Company projects that run execute-plan need this guard so a malformed task evidence contract is caught before work is launched; the skills-repo personal priority profile must not park or defer it as formal-hardening for the skills repo alone.
- **Origin class:** consumer-feedback (company)
- **Driving force:** reliability; secondary testability
- **Source:** Task 1 execute-plan run in a company consumer repository, 2026-09-27. The private worker log is retained in that run's session tmp. The task-scoped driver checkpoint returned `blocked malformed-result` because criteria from later tasks were bound to Task 1's immutable verification contract. Capture hygiene: `bash scripts/scan-public-hygiene.sh --files docs/history/backlog/2026-09-27-execute-plan-task-scoped-verification-contract.md` pass.

## Problem

During a consumer plan's manifest seeding, the plan's complete `## Validation Commands` block was assigned as the verification command for every task. That block is a valid final whole-plan gate and contains checks for outputs from later tasks. The driver correctly required the first task to prove all criteria declared for it, then rejected its otherwise successful worker result because those future-task artifacts did not exist. The task's targeted test passed, but the run is now held at a launched claim with no checkpoint or task commit.

This is a witnessed consumer-run failure, not a plan defect or hook failure. The plan readiness gate passed and the global validation block expresses final acceptance. The skill requires immutable task criteria and verification commands at manifest creation, but does not provide a concrete pre-seed procedure or guard to prevent whole-plan validation criteria from being copied into each task. The skill-gate hook controls plan-file writes; it does not create or semantically validate runtime evidence contracts. The runtime driver behaved fail-closed as designed.

## Location

- `agents/skills/execute-plan/SKILL.md`, Phase 0 session bootstrap / machine-manifest seeding instructions and task-evidence contract.
- `agents/skills/execute-plan/runtime-contract.md`, “Verification evidence envelope”.
- `scripts/execute_plan_runtime.py`, create validation accepts complete per-task criteria/command declarations but cannot establish that the criteria belong to the named task or that their outputs are available at that point in the plan.

## Expected behavior and suggested fix

Before creating the machine manifest, require a task-to-evidence mapping derived from each task's own acceptance criteria and files. Keep the plan's global `## Validation Commands` as the final whole-plan gate; do not clone its complete criteria set into every task. For each task, use only checks that are runnable after that task and cover its declared task criteria. If a criterion cannot be independently verified at that boundary, record a clear task-local observable check or defer it to the appropriate later task/final gate without making it a Task 1 prerequisite.

Add a pre-seed consistency gate, preferably in the execute-plan skill plus a driver/preflight check where mechanically supportable: reject or stop before any worker launch when a task verifier depends on an artifact first produced by a later task, or when task criteria are merely a repeated copy of the global validation checklist. Add a regression fixture with two tasks: Task 1 has a targeted verifier; the global gate references a Task 2 output; manifest seeding must not make Task 1 require that output, and the final global gate remains intact.

## Why not fixed now

The consumer run is already in an active launched claim and the driver refuses the malformed result read-only. Editing the machine manifest by hand is prohibited, and changing the immutable verifier contract in place would invalidate the active evidence contract. Fixing the shared skill/driver is outside the consumer feature's implementation scope. Preserve the run state and first-task changes until the supported recovery path or an explicit disposition is chosen.

## Severity and evidence

High reliability issue: the first implementation task was blocked after the worker and its focused test completed, leaving the plan active without a checkpoint. Evidence is the runtime driver's `malformed-result` refusal, the private worker log, and the plan's ordered task dependency structure. The refusal avoided a false checkpoint or commit, so no incorrect task completion was recorded.
