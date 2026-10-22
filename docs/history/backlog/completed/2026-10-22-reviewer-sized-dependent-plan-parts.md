# Backlog: offer reviewer-sized dependent plan parts for one outcome

- **Filed:** 2026-10-22, operator request
- **Status:** covered (docs/history/plans/2026-10-23-reviewer-sized-dependent-plan-parts.md)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** projects using the shared `plans` and `execute-plan` skills need a clear way to request bounded, independently reviewable dependent parts; do not defer this solely under the skills repository's personal priority profile.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class (authoring affordance for an operator-requested split; no refusal or gate change is implied)
- **Cluster:** docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md (same artifact class: this origin's reserved authoring worktree and same-named branch outlived their session and were removed only on operator direction; see that row's Witness 2026-10-23)
- **Skill/step:** `agents/skills/plans/SKILL.md`, sizing and splitting rules; `agents/skills/execute-plan/SKILL.md`, task and plan execution boundaries
- **Severity:** low; operator-requested usability improvement, with no demonstrated integrity failure or measured review-cost baseline.
- **Source reference:** operator request in the 2026-10-22 session; capture hygiene: `scan-public-hygiene --files` pass.
- **Driving force:** new-capability
- **Dedup probe:** searched open backlog filenames and Problem bodies plus both rolling prompt logs for reviewer-sized parts, dependent plans, split boundaries, task and change limits, and reviewer experience. The nearest record is `docs/history/plans/completed/2026-10-05-plan-sizing-execution-budget.md`; it adds time and task-count warnings, a two-round mechanism-splitting rule, and the shared-file seam rule with execution dependencies. `docs/history/backlog/2026-10-11-execute-plan-sequential-workflow-trace.md` concerns runtime trace evidence for sequential tasks when a driver exists. Neither decides when an operator may split a cohesive outcome into reviewer-sized plan/PR parts or defines the relevant change-size measure; investigate that gap without duplicating the existing sizing or dependency machinery.

## Problem

The Plans skill already supports multiple plans for deployable phases, warns on declared execution time and task count, calls for splitting a mechanism after repeated uncertified review, and requires strictly sequenced plans to preserve shared-file seams through execution dependencies. It does not define whether an author should offer an optional split for reviewer experience when none of those triggers apply, nor how to bound each part by a measurable amount of change. An operator may therefore need to supply this decomposition manually, or accept a plan whose review surface is larger than desired. The requested outcome is one coherent goal delivered through two or more dependent, separately reviewable parts with a stated limit on the number or size of changes.

## Expected

Decide whether the existing phase, budget, task-count, and seam rules already provide enough support. If a gap remains, define an optional authoring path for two or more dependent parts, identify a measurable reviewer-size limit, and state how each part is independently reviewed and ordered. Reuse the existing plan dependency mechanism and shared-file seam rule; do not add a blocking size gate or a second dependency ledger without evidence that the current path fails.

## Evidence

- `agents/skills/plans/SKILL.md`, Universal Patterns: execution-budget sizing, safe-ship phases, the two-round alarm, and the seam rule.
- `agents/skills/execute-plan/SKILL.md`, Phase 1: tasks execute sequentially with a task boundary and intermediate review; each plan still has its own final review and landing lifecycle.
- Operator request in this session for two or more dependent parts that bound changes and make review easier.

## Options to investigate

- Keep the current rules and document a small decision recipe showing when to create ordered plans instead of adding more guidance; establish whether the existing seam rule is already sufficient.
- Add an optional authoring choice with a user-selected part count and a defined change-size measure, then map each part to a strictly sequenced plan using the existing execution dependency.
- Represent parts inside one plan with separate review and landing boundaries; assess whether the current per-task commit/review boundary and final whole-branch review can deliver the intended reviewer experience without changing the plan lifecycle.

## Why not fixed now

The user requested an investigation before implementation. The existing sizing and dependency rules cover much of the requested capability, so the remaining user value and the correct size measure need to be established before changing shared skills. Any resulting option should remain optional unless evidence supports stronger enforcement.
