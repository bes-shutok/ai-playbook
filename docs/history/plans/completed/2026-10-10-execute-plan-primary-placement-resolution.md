# Plan: Execute-plan dispatch placement resolution (the primary-policy stand-down names its routes)

Backlog origin: docs/history/backlog/2026-10-07-execute-plan-primary-placement-resolution.md (the PLAN-PROMPTS entry `execute-plan-primary-placement-resolution` carries the operator-confirmed prompt)
Driving force: automation
Design input: docs/history/plans/completed/2026-10-04-execute-plan-primary-checkout-mode.md (the completed placement plan whose `primary-execution` semantics and protections must remain); the witnessed consumer run that stopped safely under `worktree_policy = "primary"` while the operator had to infer between a one-run worktree request and a durable placement setting
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-execute-plan-primary-placement-resolution-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-execute-plan-primary-placement-resolution.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The primary declaration: a project facts document explicitly declaring `worktree_policy = "primary"`. Under it, ordinary work runs in the primary checkout and the named worktree-requiring lanes hit the conflict-and-stop arm.
- The conflict-and-stop arm: today's resolution for a named lane under the primary declaration - the lane reports the isolation conflict (the lane requires an isolated checkout the project setting forbids) and stops for operator direction instead of creating a worktree or silently degrading. This plan extends the arm's stop report; the arm's semantics are otherwise untouched.
- The two authorized routes: (1) an operator's or user's explicit one-run worktree request for this run, subject to project instructions (the precedence ladder's explicit-request override); (2) configuring `worktree_policy = "primary-execution"` for ongoing primary-checkout execution, serialized and base-branch-checked, when that is the intended ongoing policy for the project.
- Bare invocation: an execute-plan invocation that carries neither route. It authorizes neither route; the fail-closed stop stands.

## Why

The conflict-and-stop arm stops safely but reports only the conflict, so the operator must infer the remedy from the standard's full precedence ladder - the witnessed cost of this entry. The fix is the smallest wording change that makes the stand-down actionable: the stop report names the two routes that DO authorize execution placement, states plainly that bare invocation authorizes neither, and the one surface that executes the stop (the Phase 0 consult) carries the duty to relay the naming. No placement mechanic changes: the precedence ladder (explicit request overrides), the primary-execution serialization, the recorded placement, the base-branch check, and the resume checks all keep their current semantics and text.

## Gist & Examples

TLDR: the conflict-and-stop arm names its two authorized routes and the no-authorization rule; Step 0.1's consult relays the naming into the stop report; four must-carry pins freeze the operative spans including the relay; every mechanic is untouched.

Before: a consumer run under `worktree_policy = "primary"` stops with "the lane requires an isolated checkout the project setting forbids"; the operator reads the whole standard to learn an operator-made one-run request would have worked, or that `primary-execution` exists.

After: the same stop names both routes (with their guard tags - who must make the request; the execution mode's serialization and base-branch check) and the no-authorization rule in one place; the operator picks a route or configures the policy without inference.

Edge cases: an operator or user request still overrides the declaration (route 1, precedence unchanged); `primary-execution` still authorizes exactly the plan-execution lane and stays serialized, base-branch-checked, and resume-guarded (route 2, semantics byte-identical in meaning); a project with no declaration keeps today's resolutions; an out-of-vocabulary `worktree_policy` value keeps the unconfigured-with-named-report treatment; the authoring lane is never granted primary placement.

## Outcome

A consumer run stopped by the primary declaration reads, in the stop report itself, the two routes that authorize execution placement and the rule that bare invocation authorizes neither; four must-carry pins make the naming survive drift.

Gate delta: one naming clause and the no-authorization statement added to the conflict-and-stop arm, one relay sentence added to Step 0.1, and four must-carry pins beside provenance; no new placement mode, no resolver script, no mechanic touched.

## Assumptions

- The policy paragraph is the single home of the routes: the reference-contract rule makes consumers reference the standard, never restate it (verified: no other execute-plan surface restates the conflict arm - the only hits for the arm's wording live in the policy paragraph itself), so one edit closes the gap at the doctrine layer; the Step 0.1 relay is a reference, not a second home. Basis: the entry's smallest-change constraint, the grep verification, and the review panel's reporting-duty finding (the Ship criterion depends on the stop site relaying the naming).
- The witness form is must-carry pins in the pins suite, not a new test file or a mechanical resolver: the placement consult is orchestrator-read prose, a resolver script would be new machinery under the admission protocol with no incident to justify it, and the pins suite is this repository's canonical span-freeze home for skill text. The route-3 witness class (refusal when neither route is authorized) is therefore text-presence only - no mechanical refusal exists to test for a prose consult, and this plan states that limit openly rather than implying an executable refusal witness. Basis: the entry's "no new placement mode or machinery" constraint, the pins suite's existing role, and the review panel's honesty finding.
- Route 2's guard tags ("serialized and base-branch-checked") satisfy the entry's prerequisites-and-consequences demand by reference: the same paragraph's primary-execution resolution owns the full semantics, so the stop report tags the consequences without restating them. Basis: the entry's route-2 phrasing and the reference-contract rule.
- Route 1's "subject to project instructions" stays in the wording: the witnessed project permits worktrees only on explicit user request, so the route names the override AND its limit AND its authorizer (an operator or user, never a loop agent's own inference) in one clause. The route clause is the primary-declaration authorization arm and is additive to the precedence ladder: the ladder's override text (an explicit user request) is untouched, and the arm's stop report names the same authorization for the stopped lane. Basis: the origin row's witnessed project shape, the precedence ladder's explicit-request precedence, and the review panel's self-authorization finding.
- Residual accepted: an operator who wants a one-run worktree on a NAMED lane other than execution still reads the lane list themselves - the stand-down names the routes, not per-lane eligibility tables (the named lanes are already enumerated in the same paragraph). Basis: the smallest-change constraint.

Decision points requiring a grill: none remain (the operator-confirmed entry names the two routes, the authorization statement, the three witnesses, and the four rejected alternatives).

## Standing constraints

- No placement mechanic changes: serialization, recorded placement, the base-branch check, and the resume checks keep their current semantics and text; `primary-execution` is never broadened to the authoring lane; no claim or placement mechanics are modified; the completed claim-write plan's gateway work (docs/history/plans/completed/2026-10-07-execution-claim-write-enforcement.md) is out of scope and untouched.
- The precedence ladder is preserved: an explicit operator or user request for a worktree still overrides the project policy and this standard's default, and the fail-closed stop stands when neither route is authorized.
- The full battery stays green at every task landing: the pins suite, the parallel-work regressions suite, em-dash over the touched path, the hygiene scan; a red suite stops the task for reconciliation, never a weakened check.
- Any pinned span the edit touches is kept intact or re-aimed beside its provenance in the same task (the pins suite covers execute-plan SKILL.md spans); this plan's own new spans pin in the same task as the text they freeze.
- Deploy truth: the skill edit reaches its runtime home at this plan's merge-locked landing (the vendored twin carries it in the same run).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the change is additive prose plus additive pins, so a revert restores today's text exactly; a post-landing revert that conflicts on the hot pins script replays the deleted lines forward instead of resolving by re-deletion.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the stop report names exactly the two authorized routes and states the no-authorization rule; no third route is implied and no existing resolution is reworded.
- regression safety: the pins suite and the parallel-work regressions suite green; every pinned execute-plan span intact or re-aimed beside provenance in the same landing.
- scope discipline: the changes touch only the conflict-and-stop arm's text and the Step 0.1 relay sentence in execute-plan SKILL.md, plus the pins script; no mechanic, mode, claim, or consumer skill file is edited.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- A consumer run stopped by the primary declaration can name its two routes and the no-authorization rule from the stop report alone; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the conflict-and-stop arm inside the Worktree-first standard's policy paragraph gains the two-route naming and the no-authorization statement, and the Step 0.1 consult paragraph gains the one-sentence relay duty; nothing else in the file)

**Tests:**
- `scripts/check_maintenance_pins.sh` (the four must-carry witness pins beside provenance, in the same task as the text they freeze)

**Docs:**
- `docs/history/backlog/2026-10-07-execute-plan-primary-placement-resolution.md` (read-only this plan; flipped covered by the landing rider)

**Read-only (referenced, never edited):**
- `docs/history/plans/completed/2026-10-04-execute-plan-primary-checkout-mode.md` (the completed placement plan whose primary-execution semantics this plan preserves)
- `docs/history/plans/completed/2026-10-07-execution-claim-write-enforcement.md` (the completed claim-write plan whose gateway work stays out of scope)
- `agents/skills/execute-plan/runtime-contract.md` (verified non-restating; opened to confirm the arm lives only in the policy paragraph)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-07-execute-plan-primary-placement-resolution.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## execute-plan-primary-placement-resolution` (frozen under docs/tmp/authoring-claims/2026-10-10-execute-plan-primary-placement-resolution.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "explicit one-run worktree request" agents/skills/execute-plan/SKILL.md   # expect 1 (route 1 named once, in the stand-down; 0 pre-edit)
grep -c "authorizes neither route" agents/skills/execute-plan/SKILL.md   # expect 1 (the fail-closed statement; 0 pre-edit)
grep -c 'configure `worktree_policy = "primary-execution"`' agents/skills/execute-plan/SKILL.md   # expect 1 (route 2 named once, in the stand-down; 0 pre-edit)
grep -c "reports the two authorized routes" agents/skills/execute-plan/SKILL.md   # expect 1 (the Step 0.1 relay duty; 0 pre-edit)
grep -c "stop for operator direction instead of creating a worktree or silently degrading" agents/skills/execute-plan/SKILL.md   # expect 1 (already 1 pre-edit; this asserts the edit did not duplicate or displace the arm's home)
```

**Tests:**
```bash
bash scripts/check_maintenance_pins.sh   # exit 0
python3 scripts/test_parallel_work_regressions.py   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md   # exit 0
bash scripts/scan-public-hygiene.sh   # exit 0 from the repo root (the in-repo copy, not a deployed twin that can lag)
```

### Task 1: the two-route stand-down wording, its relay, and its witness pins

Files:
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh

- [x] Extend the conflict-and-stop arm's stop in place (the primary declaration's resolution inside the Worktree-first standard's policy paragraph): after "stop for operator direction instead of creating a worktree or silently degrading", add the naming clause - the stop report names the two authorized routes, an operator's or user's explicit one-run worktree request for this run, subject to project instructions, or configure `worktree_policy = "primary-execution"` for ongoing primary-checkout execution, serialized and base-branch-checked, when that is the intended ongoing policy - and state that bare invocation authorizes neither route, so the fail-closed stop stands. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Step 0.1 relay sentence (the consult paragraph): a conflict-and-stop resolution under a primary declaration reports the two authorized routes and the no-authorization rule from the policy paragraph's conflict-and-stop arm in its stand-down report (the arm itself owns the stop). [class: IMPLEMENTATION_REQUIRED]
- [x] Add the three must-carry pins beside their provenance in the pins suite, in this same task, using the suite's own presence-pin or section-scoped exactly-once idiom (the worktree-first normalized-count block already in the pins suite is the precedent): one pin per route plus the fail-closed rule, each with a provenance comment naming the witnessed ambiguity (the 2026-10-07 consumer stand-down that stopped safely but named no remedy); the route pins freeze spans identical to the Validation Commands patterns ("explicit one-run worktree request"; 'configure `worktree_policy = "primary-execution"`'), the fail-closed pin freezes the full statement "bare invocation authorizes neither route, so the fail-closed stop stands" so the fragment cannot drift out of its arm-local scope, and the fourth pin freezes the relay span "reports the two authorized routes" so the operator-facing clause is witnessed too. [class: REPOSITORY_TEST]
- [x] Run the span checks and the battery from `## Validation Commands`; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
