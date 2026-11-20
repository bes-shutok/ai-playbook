# Backlog: resume binds execution work to an unrelated authoring claim

- **Status:** covered-pending-execution (docs/history/plans/2026-11-06-execution-resume-authoring-claim-identity-confusion.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consumer projects using plan execution need resume identity bound to the requested plan and its execution manifest; the skills-repo personal priority profile must not park or defer this as formal-hardening for the skills repo alone.
- **Origin class:** self-serving
- **Class:** fence-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 0 resume and `agents/skills/execute-plan/worktree-first.md` worktree adoption
- **Catch frequency:** two user corrections in one recovery session followed an execution resume that selected an authoring claim for a different backlog item and created its branch while closing another plan.
- **False-positive cost:** a required identity match may retain a run for recovery when its manifest is genuinely missing; selecting by a same-session claim can instead create or mutate work under the wrong item.
- **Review date:** 2026-12-04
- **Dedup probe:** searched open backlog filenames and bodies for resume identity, authoring claims, worktree selection, and plan-lifecycle confusion. `docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md` concerns queue classification from landing evidence, not choosing an execution worktree from an authoring claim. The covered `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` and its active plan cover complete resource disposition and reporting, not the selector that chose the wrong claim.
- **Cluster:** `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (shared resume and ownership surface; this row owns selection of the immutable execution identity, that row owns the terminal disposition of inventoried resources); `docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md` (related authoring-versus-execution classification, but a different selection mechanism); `docs/history/plans/completed/2026-11-06-authoring-continuation-owner-attribution.md (covered)` (same claim/session identity surface; this row owns execute-plan worktree selection, that row owns authoring-run continuation)

## Problem

The session began with an explicit `execute-plan` request for `docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md`. On resume, the assistant found that implementation had landed and then used a same-session authoring claim for `docs/history/backlog/2026-11-02-machinery-inventory-regrowth-two-runtime-scripts.md` to create an `authoring/` worktree, while passing the review-freshness plan to `done_run.sh setup --owned-plan`. The two identities did not match. The result was review-freshness work in a worktree named and frozen for the machinery-inventory backlog, with unrelated uncommitted changes left there.

The failure is not simply an unclear completion report: a claim belonging to one authoring item was treated as the execution run's identity. The existing resource-disposition plan covers reporting and preserving work, but does not pin the source of truth for selecting a resumed execution worktree.

A separate witness in a later execution used a stable claim and manifest that agreed on the requested plan, branch, and start commit, but their session identity did not equal the active ID returned by the shared session-channel helper. The fresh-foreign claim refusal fired even though the original setup turn and workers were complete and no peer run occupied the target. An existing interactive user-directed override preserved the claim and allowed the run to continue. This is not the wrong-authoring-claim selection above: it is ambiguity about how the immutable run identity, mutable owner session, active runtime identity, and claim `session` field relate during resume.

## Expected

On execute-plan resume, bind the run only from its immutable execution manifest identity: exact plan path, `run_session_id`, and recorded worktree/branch, cross-checked against the execution claim and current Git registration. An authoring claim may identify an authoring run only. If execution identity is absent or inconsistent, recover it from durable execution evidence or preserve the work and report the precise gap; never create a worktree from a claim for another item.

## Suggested direction

Trace Phase 0 resume and worktree adoption across `execute-plan`, `plans`, and the shared worktree standard. Compare the immutable execution manifest, execution claim, authoring claim, and Git registration contracts. Prefer a source-of-truth ordering and an explicit recovery path using existing records; add no new ledger or validator unless the current evidence shows those records cannot disambiguate the run.
Include the distinction between the active session-channel ID, the immutable `run_session_id`, and the mutable manifest `session_id`; derive the initial claim identity from the documented runtime identity source, then specify the existing authorized resume or dead-run route when those values differ. Do not rebind a matching claim or add a second guard before establishing the identity contract.

## Evidence

- The session's initiating user prompt names the review-freshness plan with `$execute-plan`.
- On resume, the session refreshed the authoring claim for the machinery-inventory backlog, created its authoring branch, and invoked `done_run.sh setup --owned-plan` with the review-freshness plan path.
- The worktree's branch and claim named the machinery-inventory backlog, while the worktree contained review-freshness plan changes. The review-freshness plan was later archived in commit `0085b695c`.
- The current `agents/skills/execute-plan/SKILL.md` requires resume identity to return to the recorded worktree and branch, and `agents/skills/execute-plan/worktree-first.md` defines the identity checks; the observed selection did not follow that contract.
- The machinery registry correction had already landed in Task 5 of `docs/history/plans/completed/2026-11-02-review-freshness-and-code-coverage-gaps.md` at implementation commit `7d4d3f7a2`; the archive was completed in `0085b695c`.
- Later witness: the claim and manifest matched the requested plan and branch, but their stable session identity differed from the active session-channel ID; the fresh-foreign refusal and subsequent authorized override are recorded in the same-session execution evidence. No peer execution was present on the target.

## Why not fixed now

This session is recording and investigating the workflow fault before changing shared execution and claim-selection behavior. The durable records already show the correct completed plan and preserve the mismatched worktree's uncommitted changes; correcting the selector requires the owning workflow review.
