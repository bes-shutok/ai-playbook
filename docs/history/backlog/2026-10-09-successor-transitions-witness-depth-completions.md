# Backlog: witness-depth completions for the successor reconciliation transitions

- **Filed:** 2026-10-09, execute-plan-successor-checkpoint-recovery execution code review r1 (overflow manifest, 8 items grouped; all fail-closed today, none blocking)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (execution r1 testing and design-simplicity overflow rows)
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `scripts/test_execute_plan_runtime.py` (SuccessorWorkerStartReconciliationTest, CommittedPlanProgressReconciliationTest); `scripts/execute_plan_runtime.py` refusal-prefix surface
- **Cluster:** docs/history/backlog/2026-10-09-successor-reconcile-terminality-consult-helper.md
- **Severity:** low; every item is fail-closed or bounded today; the cost is masked regressions and mildly misattributed operator evidence

## Problem

The r1 panel's five overflow-class items on the testing side and three on the design side are recorded here as one grouped row so the beyond-witness completeness work has a durable owner:

1. A port returning a non-Mapping `provider_identity` raises AttributeError out of the locked region (mirrors the pre-existing ambiguous-handoff sibling; trusted adapter boundary; untested malformed-observation shape).
2. Trivial malformed-request arms (request, worker_start_receipt, checkpoint_receipt, terminal_evidence not a Mapping) are untested; refuse-before-effect.
3. The committed-progress arm's TOCTOU guards ("plan bytes changed during discovery", "plan file became unreadable") and the scope-refresh ValueError refusal are untested.
4. The chain-suffix search beyond `start=0` (a stale first receipt with a bindable second) is untested.
5. No precedence witness: a ready review covering current bytes plus a stale receipt chain must take the ordinary plan-digest-refresh route with no committed event.
6. The arm's refresh tail repeats the ordinary route's tail without a shared helper (deliberate parity per the plan's recorded disposition; informational).
7. The chain search is O(n squared) in receipted deltas with up to 3 git subprocesses per probe (N tiny per manifest, within band).
8. Arm-specific refusals flow through the shared refuse closure whose fixed prefix names the reviewed-plan digest refresh, mildly misattributing the committing arm in operator-facing evidence.

## Exact location

`scripts/test_execute_plan_runtime.py`, the two reconciliation test classes; `scripts/execute_plan_runtime.py`, the digest-route refuse closure prefix.

## Suggested fix

Add the five witnesses (1-5); disposition 6 as accepted parity (no change) and 7 as within-band (no change) unless a future scale need arises; for 8, either thread an arm-specific prefix label through the shared closure (updating the asserting tests) or accept the misattribution with a comment. Acceptance: the runtime suite stays green; items 6-7 carry explicit accepted-residual notes if left.
