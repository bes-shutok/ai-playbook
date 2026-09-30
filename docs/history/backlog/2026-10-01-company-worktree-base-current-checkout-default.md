Status: open
Priority: high
Workflow: backlog
Class: fence-class
Driving force: reliability
Origin class: consumer-feedback (company)
Consumer urgency: Company projects that run the shared plan and execution workflows need worktrees to preserve the active review branch as their integration base; do not defer this consumer failure as formal-hardening of the personal skills repository.
Date: 2026-10-01

# Company project worktrees must default to the branch checked out when the run starts

## Problem

The worktree-first workflow can select the repository's remote default branch when a company project's facts do not explicitly pin a base. That breaks stacked review work: the new plan or execution worktree omits commits on the active branch, and a later landing can target the wrong integration line.

This failure occurred while authoring a plan for a company Jira task on top of an active stacked review. The primary checkout was on the review branch at a commit two changes ahead of its remote tracking ref. Its remote default ref pointed at a different history, and the active-branch commit was not an ancestor of that default. The first authoring worktree was created from the remote default branch. The user corrected the base before any plan file was written. A replacement worktree was then created from the active branch. This was an observed wrong-checkout incident, not a hypothetical edge case; containment prevented plan work from being stranded on the wrong history.

## Exact locations

- Canonical base resolution and worktree lifecycle: `agents/skills/execute-plan/SKILL.md`, `Worktree-first standard` and `Base-branch resolution rule`.
- Plan-authoring entry point: `agents/skills/plans/SKILL.md`, `Phase 0`.
- Execution entry point and per-project base configuration: `agents/skills/execute-plan/SKILL.md`, `Phase 0` and the project configuration table.
- Company project setup defaults: `agents/skills/bootstrap-ai-playbook/SKILL.md` and any project facts template or bootstrap code that seeds `base_branch` or `project_class`.
- Automated company and idle-time dispatch paths: the maintenance payloads and landing tails that create a run worktree or choose its landing target. Audit the canonical payload source and generated payload producers before changing copies.

## Observed versus expected

- Observed: when project-class facts are absent, the canonical resolution defaults to `default-branch-integration`; that class can derive a base from `origin/HEAD`. In this incident, the selected ref omitted two commits on the operator's current company branch.
- Expected: for a company project, an unset base resolves from the primary checkout's branch at run start. The exact branch ref and commit are captured once and carried through worktree creation and the run's landing path. An explicit project base remains an override. A detached checkout or an unresolvable current branch fails closed instead of silently falling back to the remote default.

## Scope

This item covers the shared policy and its consumers for plan authoring, plan execution, and automated company-project dispatch. It changes the company-project default only. Personal projects keep their separately configured or documented default unless their owner chooses otherwise. The current-branch rule applies to the worktree base and the landing target for the same run so a correct creation base cannot later be redirected to a remote default branch.

The existing narrow item `docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md` concerns a related configured checkout-flow landing mismatch. Reconcile it with this item when planning implementation; do not leave two independent implementations of the same base/landing binding.

## Suggested fix

1. Update the canonical base-resolution rule so a company project with no explicit `base_branch` uses the active branch and commit from its primary checkout at run start. Resolve company scope from the existing user/project facts mechanism; do not hardcode machine paths or company names in shared skills.
2. Preserve explicit `base_branch` settings as the deliberate override. Resolve a detached checkout as an error requiring direction; never silently substitute `origin/HEAD` for a company project.
3. Capture the resolved base once. Make plan authoring, execute-plan, and automated company dispatch pass that ref to worktree creation and use the same captured target for landing. If any lane must use a different target for an established external reason, name that reason and add a fail-closed mismatch check.
4. Update company project bootstrap defaults so newly initialized company repositories use the same policy, and audit existing company facts for stale `default-branch-integration` settings that were only present to express the old default.
5. Keep one canonical rule in the execute-plan worktree standard. Update plans and maintenance entry points to reference it, and remove conflicting default-branch assumptions from their worktree and landing instructions.
6. Add regression coverage with a temporary repository whose active branch contains commits absent from the remote default branch. Verify both authoring and execution resolve the active branch, and verify the landing path retains that base. Include a detached-checkout case that refuses rather than falling back.
7. Reconcile the related checkout-flow landing mismatch backlog item into the resulting plan's origins and dispositions if the implementation covers its finding.

## Acceptance criteria

- With no explicit base setting in a company project, authoring and execution resolve the primary checkout's current branch ref and commit, even when `origin/HEAD` points elsewhere and the current branch contains additional commits.
- The resolved ref and commit are captured before worktree creation and remain the run's landing target; an intermediate change to a remote default branch cannot redirect the run.
- A detached or otherwise unresolvable primary checkout refuses worktree creation with a clear report and does not guess a base.
- Explicit per-project base configuration continues to work and is distinguishable from the company default.
- Company project bootstrap defaults, manual entry points, and automated dispatch paths agree with the canonical rule. Personal project policy is not changed as a side effect.
- Tests exercise the real branch resolver and worktree/landing selection with separate current and remote-default histories, including the active branch's extra commits.
- The related `checkout-flow-landing-mismatch-guard` item is explicitly merged, superseded, or left with a documented distinct acceptance boundary; no duplicated guard work remains.

## Why not fixed now

The user explicitly requested a durable ai-playbook backlog item for the cross-project policy correction. This session corrects the feature-plan authoring base first and does not broaden that plan task into a shared-skill implementation.

## Source reference

Direct user correction during feature-plan authoring on 2026-10-01, corroborated by the primary checkout's branch and commit graph. No review staging artifact applies. Severity: High, because the wrong base omitted active review commits and would have put plan work on the wrong integration history. Capture hygiene: `scan-public-hygiene.sh --files` pass.

## Dedup probe

Searched the open backlog filenames and bodies for `worktree branch`, `base branch`, `current branch`, `origin/HEAD`, and `checkout-flow`. The nearest open items are `2026-09-28-checkout-flow-landing-mismatch-guard.md` (landing mismatch after a project is already configured as checkout-flow), `2026-09-28-plan-g7-base-key-skip.md` (a plan's validation gate skips the configured base key), and `2026-09-28-landing-machinery-on-main-shorthand.md` (documentation wording). None sets the default base for company projects or binds the selected current branch through creation and landing. The checkout-flow item is related and named for reconciliation above; the others are distinct.
