# Resumed closeout runs cannot update ownership claims through the setup wrapper

- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Skill/step:** `agents/skills/done/SKILL.md` Step 0; `scripts/done_run.sh` setup and `scripts/done_sweep_gates_lib.py` write-manifest
- **Class:** fix-class
- **Origin class:** witnessed recovery-path defect
- **Driving force:** efficiency

## Problem

When a plan review artifact is created after done setup, the run manifest does not own that new review. Re-entering with `done_run.sh setup --from-manifest <run-id>` retains the existing boundary but ignores newly supplied `--owned-review` claims. Passing `--adopt <run-id>` to setup also fails at the interrupted-boundary classifier, which refuses before the lower-level manifest writer can adopt the run. The wrapper therefore advertises an adoption remedy it cannot execute, and the operator must discover and invoke `write-manifest --adopt` directly.

## Evidence

Witnessed on 2026-10-25 while authoring a plan with two review rounds. The setup manifest owned the first review. The second review passed the plan-review and hard digest gates but was not in the manifest. `--from-manifest` re-entered without adding the second review; `--adopt` stopped at the current-boundary classifier. The safe workaround closed the empty prior boundary with `recover-manifest`, created a new setup boundary with exact foreign-review inventory, then used `write-manifest --adopt` to add both owned reviews and the plan. The final adopted manifest correctly listed both review paths.

## Suggested fix

Make the composed setup recovery contract support adding ownership claims to an existing current boundary, or provide a named wrapper operation that adopts the existing manifest and merges new owned and foreign review paths. Keep the run's original start commit and paths, retain explicit foreign-review inventory, and test both wrapper-visible recovery choices plus a review artifact created after initial setup. Do not require operators to call the lower-level manifest writer by hand.

## Why not fixed now

This session was authoring a separate maintenance-selected plan. Editing the done-run recovery protocol and its regression suite would expand that plan's scope. The observed run was recovered without editing a gate or validator.

## Dedup probe

Searched the open backlog for setup re-entry, `--from-manifest`, writer adoption, and post-setup review ownership. The existing post-setup learn-edit plan covers an invocation-scoped declared-stage channel and explicitly keeps manifests fixed at write time; it does not cover adding review claims or the setup wrapper refusing its own `--adopt` argument. The done-boundary review-candidate row covers earlier test and wording residuals, not this recovery path. No matching open item found.

## Source

Observed during the 2026-10-25 maintenance plan-authoring resume; reproduced with `done_run.sh setup --from-manifest` and `--adopt`, then recovered through the documented manifest writer. Severity: high because the mismatch interrupts required closeout and risks losing owned review artifacts. Capture hygiene: public-hygiene and no-em-dash scans passed on this file.
