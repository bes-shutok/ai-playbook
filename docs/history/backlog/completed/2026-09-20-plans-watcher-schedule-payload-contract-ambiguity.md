# Backlog: plans-watcher-schedule payload contract is not pinned at the authoring boundary

Status: done
Priority: high
Workflow: backlog
Date: 2026-09-20
Class: skill-usage issue, plans skill Budget gate section (authoring watcher deltas) and the driver's plans-watcher-* CLI operations

## Observed vs expected

Observed: an orchestrator following the plans skill's Budget gate mirror ran the authoring-boundary scheduling step with a hand-assembled payload (`state_path`, `plan_slug`, a `probe_report` subset carrying binding/pause_decision/status/reset_at_epoch, and `plan_path`) through `scripts/execute_plan_runtime.py --operation plans-watcher-schedule`. The operation returned `classification=unknown`, `boundary=supersede`, `scheduling=none`, status `blocked` with reason `resume-watcher-superseded`: report-only, nothing armed.

Expected: the boundary was a continue with a trusted binding reset epoch (live probe report: primary binding, 4 percent used, 295 minutes remaining, `status: ok`), so the canonical contract says the standing resume watcher gets scheduled at reset plus one minute. A faithful reading of the skill text could not produce a payload that achieves this.

## Root area

The plans skill's Budget gate section names the operation and the `state_path` payload key but does not pin the input contract the way the canonical execute-plan section does (there the payload is specified as "the probe report JSON plus plan_path"). Without the exact field set and shape the driver's binding classifier requires (full probe report embedding? nested vs flat keys? which epoch fields?), the scheduling step at authoring boundaries silently degrades to report-only on every run: no watcher is ever armed from the authoring path, and the failure mode is invisible unless someone reads the receipt.

## Suggested fix

Pin the plans-watcher-schedule input contract in one place and reference it: either the driver documents the accepted payload schema in `--operation` help and the plans skill mirrors that schema, or the plans skill restates the canonical payload rule ("the full probe report JSON plus plan_path, plus state_path") so orchestrators stop guessing. Add one witness test asserting a trusted-epoch continue payload produces a scheduled receipt at the authoring boundary.

## Environment

ZCode runtime, 2026-09-20; repo-local driver copy (`scripts/execute_plan_runtime.py`) with vendored skill copies; outcome was safe (report-only supersedes, nothing armed, manual command echoed), so the defect is a contract-ambiguity and silent-degradation class, not a liveness bug.
