# Backlog: receiving-review does not bind edits to the PR's current head

- **Filed:** 2026-10-09, session analysis
- **Status:** covered (docs/history/plans/2026-10-16-receiving-review-bind-local-work-to-live-pr-head.md)
- **Workflow:** backlog
- **Priority:** high (a review fix was started after the PR had merged and the local branch did not represent its current head)
- **Origin class:** consumer-feedback (company)
- **Consumer urgency:** Consumer projects using the shared review skill need this preflight; do not defer it as formal-hardening based only on the skills repository's personal priority profile.
- **Class:** fix-class
- **Driving force:** simplicity + reliability
- **Skill/step:** `agents/skills/receiving-review/SKILL.md`, Feedback-source Workflow before implementation; `agents/skills/github-pr-workflow/SKILL.md`, PR context resolution

## Problem

The passive-review workflow resolves PR metadata and checks branch scope, but it does not require comparing the PR's current state and head commit with the local checkout before edits begin. In a consumer session, review work continued after the PR had merged while the checkout was on a different feature branch. This can place a valid fix on the wrong branch or make the agent reason from stale PR state.

## Expected

Before implementation, verify the PR lifecycle state, base and head branches, current head commit, and local branch/commit. If the PR is merged or the checkout does not match the PR head, identify the safe follow-up path and verify the target before editing. Preserve the existing all-replies thread review; this item concerns branch and lifecycle binding, not comment disposition.

Acceptance: the preflight removes the manual branch migration needed when review work starts from a checkout that does not match the PR's current state and head.

## Suggested direction

Add a concise pre-edit reconciliation step to `receiving-review` that consumes the source adapter's current PR metadata, compares it with the checkout, and defines the safe stop or follow-up path for merged, stale, or mismatched targets. Add a realistic sample-context validation for an already-merged PR and a checkout on a different branch. Keep thread disposition and branch binding as separate checks.

## Evidence

- Environment: Codex desktop, ai-playbook repo copy of the shared skill. Observed during a consumer-project review session on 2026-10-09: work was started after the PR had merged, with the local checkout on another feature branch; the fix needed a follow-up branch.
- `agents/skills/receiving-review/SKILL.md` checks whether a file belongs to the branch scope before staging, but does not require comparing the local branch and commit to the PR's current branch and head SHA before implementation.
- `agents/skills/github-pr-workflow/SKILL.md` resolves PR state and head metadata, so the missing control is a use-and-compare step in the receiving workflow.
- Severity: High. Source reference: session analysis, 2026-10-09. Capture hygiene: `scan-public-hygiene --files` pass.

## Dedup probe

Searched open backlog filenames and problem text for `merged pull request`, `PR head`, `checkout`, `local branch`, and `PR state`. The nearest item, `docs/history/backlog/2026-10-05-done-dirt-regression-blocks-reviewed-fix.md`, concerns a done-time dirt regression against the base branch and explicitly records no stale-checkout evidence. It does not cover binding passive review edits to a live PR head, so this is a distinct workflow gap.

## Why not fixed now

This session is an instruction and process analysis, not a review-fix run. The missing preflight affects several source adapters and needs a small design pass to define the safe continuation for merged and mismatched targets. The existing reply-inspection omission is already fixed in the current `receiving-review` and `github-pr-workflow` instructions, so it is not duplicated here.

## Source

Session analysis, 2026-10-09. This item describes the shared skill behavior and omits consumer-project names and identifiers.
