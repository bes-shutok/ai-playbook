# A healthy-pause outstanding run blocks its whole quota window: a survey-time resume-first proposal arm

- **Filed:** 2026-11-10, execution of docs/history/plans/completed/2026-11-10-admission-staleness-and-continuation-pick.md Task 3 (the residual the plan deliberately left to the resume path)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (the witnessed 06:35 shape; the lane starves until the armed resume carrier fires even with allowance available)
- **Origin class:** plan-residual
- **Class:** design-class
- **Surface:** the maintenance survey's drain-duty family (`agents/skills/maintenance/SKILL.md` Step 1 / survey arms) and the execute-plan claim protocol
- **Cluster:** docs/history/backlog/2026-11-11-frozen-authoring-claim-strandage.md (same outstanding-state family, added 2026-11-11; that row owns the authoring entry's frozen claim and its parked state after a session death, this row the survey-time resume proposal for a paused run's claim)
- **Cluster:** docs/history/backlog/2026-11-14-user-only-blocker-classification-self-certified.md (same stop-boundary surface: the classification decision that routes a blocked stop to the operator instead of the landed retry/arming duties)
- **Source reference:** the 2026-11-10 06:35 exec turn: the paused run `operative-file-read-budget-gate` (claim updated 04:24Z, quota-wall pause, resume carrier armed for 11:00Z) blocked every candidate via the global admission consult; the landed claim-staleness horizon (8h) deliberately does NOT lift this case — a healthy pause ends inside the horizon at the carrier's fire time
- **Dedup probe:** searched open rows for resume-first, paused-run drain, and survey resume arms; the stranded-run drain mechanics cover post-review strands and dead roots, not paused mid-execution runs
- **Why not fixed now:** resuming another run's claim touches the claim protocol's ownership boundary; the design (proposal-only vs adoption, the branch-occupant gate's interaction, the pause owner's own probe rule) is an authoring question

## Problem

When a run pauses at a quota wall with a resume carrier armed, its admission record and fresh claim block the entire lane — every candidate of both lanes — for the pause's remainder, typically hours of the 5h window, even when the deciding turn's own quota probe is clean and unrelated candidates exist. The stale-parked horizon excludes this case by design (a healthy run re-stamps; its carrier fires within the window), so the blockage stands.

## Expected

A survey-time arm that proposes (never auto-executes) resuming the paused run when the deciding turn's quota probe is clean: the turn names the paused run, its claim, and its next step from the pause record, and either the turn adopts the resume through the claim protocol's own takeover path or the operator decides; the paused run's claim, worktree, and branch stay owned by its resume path throughout, and the existing branch-occupant gate keeps the no-second-executor guarantee. Shapes and guard interactions (the probe rule, the G1e discovery arm, the drain-duty family's placement) are open to authoring.

## Suggested fix

One survey arm proposing the resume continuation, plus whatever claim-protocol wording the adoption path needs; keep the horizon's abandoned-run semantics untouched.

## Investigation note (2026-11-16)

Re-derived from disk: the block is intersection-driven, not global. `scripts/dispatch_admission.py` `check_admission` refuses a candidate only when its owned-path set intersects an outstanding run's recorded set, or when that run's evidence is empty or source-less. The witnessed case was a true intersection: the paused run's record is seeded from the covering plan's whole `Files:` lists at claim creation and is never narrowed to the remaining tasks (`scripts/execution_claim.sh`). The existing takeover path cannot adopt a paused run whose owner is alive-but-waiting (the branch-occupant gate and the terminal-only dead-run conversion refuse it by design), so the row's resume-first arm needs new adoption wording plus carrier discharge and is a design plan, not a text edit.

Alternatives priced, with one witness in six days and the 8-hour stale-parked horizon bounding abandoned runs: (A) narrow the recorded owned-path set to remaining-task paths (fixes the witnessed intersection, no ownership change, touches `scripts/execution_claim.sh` and its tests); (B) the row's survey-time resume proposal (waits for a second witness showing A is insufficient); (C) re-probe at survey time (still needs a non-owner to wake the owner); (D) do nothing. Recommended order: A or D first. Unverified: whether a paused run has a done-session manifest, whether `Files:` lists map per task, and which tests cover the paused-run shape.
