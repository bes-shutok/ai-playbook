# Backlog: stale pin review-plan reads attempt state after resume fails at baseline

- **Filed:** 2026-10-30, agent-type-affinity-before-plan-work Task 1 boundary learn
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** reliability
- **Cluster:** docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md (same surface and root area: pin expected literals lagging skill text; that row owns lane-recovery semantics, not this pin's repair)
- **Cluster:** docs/history/plans/completed/2026-10-26-maintenance-pin-current-main-baseline-red.md (the prior repaired member of the class: an obsolete pin literal red on current main)
- **Cluster:** docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md (same defect class: a repo-wide gate red at baseline; mechanisms differ per member)
- **Skill/step:** `scripts/check_maintenance_pins.sh`, pin `review-plan reads attempt state after resume` (line 3514); `agents/skills/review-plan/SKILL.md`
- **Dedup probe:** searched `docs/history/backlog/` for `attempt state after resume`, `resumed post-fence`, `check_maintenance_pins`, `PIN FAIL`: no row names this pin; the 2026-10-15 row and the 2026-10-19 light-boundary residual (1) cover other pins (retired literals, a placement-pin advisory)
- **Source reference:** docs/tmp/execute-plan/agent-type-affinity-before-plan-work/task-1-review.log.md (Pass 1 off-plan note); lesson #320 witnessed the same red mid-session on 2026-10-30; capture hygiene: scan-public-hygiene --files pass

## Problem

`bash scripts/check_maintenance_pins.sh` exits 1 with `PIN FAIL: review-plan reads attempt state after resume`. The pin greps `agents/skills/review-plan/SKILL.md` for the retired sentence `A resumed post-fence workflow reads the latest value`; landing 3fe5371f6 (2026-10-30, self-heal invocation order) rewrote that sentence into the pause-before-reassessment form without updating the pin's expected literal. The pins suite is red at baseline, so a genuine pin drift cannot be distinguished from this red and the suite's pass signal is lost until repaired.

## Expected

A landing that rewrites pinned skill text updates the pin's expected literal in the same change (the same-change sweep duty of lesson #151 applied to the pin layer; lesson #67 owns the retirement-direction sweep over pin and fixture layers).

## Suggested direction

Update the pin's expected literal to the current sentence or its stable stem, rerun the suite to green, and record the repair; no pin weakening or removal without its recorded-red consult path.

## Why not fixed now

The pin repair sits outside the witnessing task's allowed file list; the learn boundary captures outside-scope witnessed defects and does not repair them.
