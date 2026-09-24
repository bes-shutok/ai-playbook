# Backlog: plans-watcher-schedule returns blocked watcher-cas-stale at a continue boundary on a fresh authoring state file

Status: closed

Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md, Task 5): Discharged by executed docs/plans/completed/2026-09-24-exec-plan-recovery-interruptions.md lineage and the P50 repair (ce968c19): the plans SKILL.md authoring-watcher paragraph pins `plan_slug` in the payload (verified live this run) and the runtime argparse payload list names the FULL probe-report requirement for plans-watcher-schedule (verified live this run), so the fresh-state CAS block's root cause (an empty plan_slug receipt failure masquerading as watcher-cas-stale) is repaired at the runtime and the payload contract is documented at both layers.
Priority: high

Workflow: backlog

## Observed vs expected

Observed: during a plan-authoring session, the plans skill Budget gate probe returned `pause_decision: continue` with a trusted primary binding (used percent low, minutes remaining well above the round cost). Per the Budget gate's known-binding-only watcher branch, the authoring boundary then invoked the manifest-free driver operation `plans-watcher-schedule` (payload: `state_path` naming a not-yet-existing `{tmp_dir}/plan-requirements-<slug>.json`, `plan_path`, and the FULL probe report as `probe_report`). The operation returned `status: blocked`, `reason_code: watcher-cas-stale`, evidence `["boundary=stale", "classification=install", "scheduling=none"]`, `resume_watcher: null`. No watcher was scheduled and no boundary record was written, so the continue boundary carried no standing resume watcher at all.

Expected: at a continue boundary with a trusted binding reset epoch and a fresh (empty) authoring machine state, the schedule operation should record the boundary decision and schedule the standing resume watcher (fresh state means no expected generation or progress revision to compare against, so a compare-and-swap stale verdict looks wrong for this input), or return a distinct refusal code naming the actual unsatisfied precondition with a recovery action the authoring loop can take (for example record progress first). `classification=install` is also unexplained for a plain schedule call.

## Reproduction sketch

1. Fresh authoring run: probe with `--write-flag` returns `pause_decision: continue`, binding `primary`, with a future `reset_at_epoch`.
2. Call `execute_plan_runtime.py --operation plans-watcher-schedule --input '{"state_path": "<tmp>/plan-requirements-<slug>.json", "plan_path": "<plans>/<slug>.md", "probe_report": <full probe JSON>}'` where the state file does not exist yet.
3. Observe the blocked `watcher-cas-stale` result above.

## Environment context

Runtime: zcode agent session; playbook repo at main 59f65154 (worktree); vendored runtime equals repo copy. Date 2026-09-22.

## Suspected root area

`scripts/execute_plan_resume_watcher.py` (shared watcher state machine, compare-and-swap replacement and boundary-generation fences) and the `plans-watcher-schedule` operation in `scripts/execute_plan_runtime.py`; interaction between fresh-state initialization and the stale-boundary fence.

## Additional witness (2026-09-22, second authoring run)

The same blocked `watcher-cas-stale` result (evidence `boundary=stale`, `classification=install`, `scheduling=none`) reproduces when `plans-progress` is invoked FIRST and successfully records `progress_revision: 1` into the previously absent state file, and `plans-watcher-schedule` is retried with the identical payload against the now-existing state. Recording progress first does not satisfy the fence, so the recovery action sketched in Expected above ("record progress first") is ruled out as a workaround; the precondition the CAS actually compares against remains unnamed by the operation's output. The authoring run degraded to report-only per the non-schedulable-boundary rule (probe: continue, binding primary, low usage), so no watcher existed for the round; work was not blocked.

## Completion evidence (for the fixing plan)

A test where a fresh (absent) authoring state file plus a trusted continue-boundary probe report yields either a scheduled watcher receipt or a named recovery action, never the bare `watcher-cas-stale` blocked result; plus a second test pinning whatever precondition the fence actually guards.

## Additional witness (2026-09-22, later authoring session, same day)

Discriminating evidence narrowing the root area: on an identical fresh (absent) state file, the SAME call shape returned `status: success`, `reason_code: resume-watcher-scheduled`, `cas_applied: true` once ONE payload field was added: `plan_slug`. The first call's payload carried `state_path`, `plan_path`, and the full `probe_report` but no `plan_slug`; the failure therefore tracks the empty `plan_slug` failing receipt validation (`validate_resume_watcher_receipt` requires a non-empty string for `plan_slug`), not the fresh-state fence. Two implications:

1. The outer schedule arm maps EVERY inner machine failure (including `malformed-result` from receipt validation) to the coarse `watcher-cas-stale` reason code, so a missing payload field masquerades as a compare-and-swap race; the inner reason must surface in the outcome evidence.
2. The plans skill Budget gate section's authoring-mirror text lists `state_path`, `probe_report`, and `plan_path` for `plans-watcher-schedule` but not `plan_slug`, so a faithful reading of the skill produces the failing payload; the payload-field list in that section needs `plan_slug` (and the completion evidence should include a test that the documented payload shape schedules successfully).

Reproduction: same as the sketch above, plus the control case adding `"plan_slug": "<slug>"` to the payload, which succeeds on the same fresh state.
