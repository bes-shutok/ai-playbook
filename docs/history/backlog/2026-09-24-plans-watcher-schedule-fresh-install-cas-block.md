# Backlog: plans-watcher-schedule fresh-install CAS block degrades the authoring budget-gate boundary

Status: open
Priority: medium
Workflow: backlog
Date: 2026-09-24
Class: skills-corpus defect (plans skill Budget gate / execute-plan runtime driver)

## Observed versus expected

The plans skill's Budget gate mirror (authoring boundaries) prescribes recording each boundary through the driver's manifest-free `plans-watcher-schedule` operation over the payload `state_path`. On a fresh authoring run (no prior `plan-requirements-<slug>.json` machine state), the operation answered `status: blocked`, `reason_code: watcher-cas-stale`, `classification: install`, `recovery_action: preserve-and-reconcile`, `scheduling: none`: the compare-and-swap wants a pre-existing state generation the first boundary has not written. Expected: a first boundary on a fresh run should bootstrap its machine state (generation 0 accepted as the install case) or the skill text should name the fresh-install path and its fallback (report-only supersede) so the degrading session records it deliberately.

## Reproduction (trimmed)

`python3 scripts/execute_plan_runtime.py --operation plans-watcher-schedule --input '<full probe report JSON plus plan_path and state_path>'` from a repo worktree with no pre-existing payload state file returned the blocked envelope above (witnessed 2026-09-24 during a plans-skill authoring run's pre-round budget boundary). The invocation shape (operation plus --input, no --state-path flag) matched the help text.

## Environment

Repo-local driver copy (scripts/execute_plan_runtime.py), date 2026-09-24, worktree checkout; the plans skill's Budget gate section is the owning surface, the execute-plan runtime contract's CLI boundary section the operation's home.

## Suspected root area

The watcher state machine's fresh-install bootstrap in the driver, or a missing fresh-install clause in the plans/execute-plan Budget-gate skill text (either the operation accepts generation-0 installs or the skills document the blocked install verdict as the expected report-only degrade).
