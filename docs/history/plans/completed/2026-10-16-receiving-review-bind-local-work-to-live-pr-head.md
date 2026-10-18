# Plan: bind receiving-review edits to the live PR head

Backlog origin: docs/history/backlog/2026-10-09-receiving-review-pr-checkout-preflight.md
Driving force: code-quality + external (the consumer-recorded incident docs/history/backlog/2026-10-09-receiving-review-pr-checkout-preflight.md)
Plan review record: the staging series .ai-playbook/reviews/2026-10-16-plan-review-receiving-review-bind-local-work-to-live-pr-head-p9d8d102e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-16-receiving-review-bind-local-work-to-live-pr-head.md (session sess_automation-4f96f211-remainder)

## Terms

- pre-edit reconciliation: the new Feedback-source Workflow step that compares the resolved PR metadata with the local checkout before any edit begins.
- PR head metadata: the source adapter's resolved lifecycle state, base branch name, head branch name, and head commit SHA for the feedback PR.
- local checkout binding: the current local branch name and its HEAD commit, compared against the PR head metadata.
- safe follow-up path: the named next action for a stop outcome (a follow-up branch for a merged PR, or the operator-selected correct local branch), stated before any edit.
- advanced head: the PR head branch name matches the local branch but the head commit SHA differs; yields the stale stop.

## Why

A review fix was started after its PR had merged while the local checkout named a different feature branch, and the fix needed a follow-up branch. The workflow resolves PR metadata and checks folder scope, but nothing binds the local checkout to the PR's current state and head before edits, so valid work can land on the wrong branch from stale state.

## Gist & Examples

TLDR: receiving-review gains a pre-edit reconciliation step that stops before edits on a merged PR, a branch or head mismatch, or unreadable PR head metadata, naming the safe follow-up path instead of trusting the checkout; driving force: code-quality with the consumer incident as the external source.

Before: a consumer session processed review threads on a merged PR from a different local feature branch and began editing; the fix required a manual follow-up branch discovered after work started.
After: the same session's reconciliation compares state and head first, stops with "the PR is merged; the safe follow-up path is a new branch off the base, to be selected and verified before edits", and no edit happens on the stale checkout.
Edge cases: local-only personal or pet projects never query the remote for this step (the comparison consumes the metadata the workflow already resolved, or the operator supplies it); an advanced head (same branch name, different SHA) stops as stale rather than pulling automatically; metadata that cannot establish the target stops instead of inferring state from the branch name.

## Outcome

Review edits can no longer begin against a merged PR, a mismatched branch, an advanced head, or unreadable PR state: the workflow stops first and names the safe follow-up path (the four sample contexts cover the first three and the matching proceed state; unreadable metadata is a stop condition outside the sample set).

- The Feedback-source Workflow binds every fix to the PR's current lifecycle state and head commit before staging anything.
- The existing folder-scope check and thread disposition stay separate and unchanged.
- The stop carries its machinery admission inline: witnessed incident, expected frequency, false-positive cost, review date, and the late check it augments.

Gate delta: adds one prose workflow stop (the pre-edit reconciliation, a dispatch-pausing condition for review sessions) with its machinery admission priced here in full; removes nothing; no script, gate, fence, protocol layer, or schema field. Admission: witnessed incident, the merged-PR stale-checkout session recorded in the origin row; expected catch frequency, rare but recurring (every consumer session entering the workflow on a merged or rebound PR matches one stop class; one witnessed instance so far); false-positive cost, near zero (the only false positive is stopping on a truly matching checkout, a one-line verification the session then proceeds past); review date, 2027-01-16; augmented check, the existing branch-scope check, whose implicit trust of the checkout this step narrows and which stays in place for folder scope.

## Assumptions

- assume the preflight consumes PR head metadata the workflow already resolves (the source adapter's PR context resolution) rather than issuing a second query, so personal and pet projects stay within their no-remote gate; the comparison needs the four resolved fields (state, baseRefName, headRefName, headRefOid), and a resolved context lacking any of them routes to the unreadable-metadata stop with the operator-supplied path; basis: the source adapter's Resolve PR context primitive (whose current-branch resolution shape omits state and head SHA) and the project-scope gate's local-only rule.
- assume a same-branch different-head comparison uses the adapter's head commit SHA against local HEAD, never inference from the branch name; basis: plan-level design decision keyed to the origin's Expected verify-before-edit language (the origin records no rejected alternatives).
- assume no automatic branch switching, fetching, or pulling: every stop names the safe follow-up path and leaves the action to the operator or user; basis: plan-level design decision keyed to the project-scope gate's local-only rule and the origin's Expected section.

Decision points requiring a grill: none remain.

## Standing constraints

- Thread disposition and branch-scope binding remain separate checks; this plan only adds the pre-edit reconciliation.
- No new remote query is introduced; the step reuses metadata the workflow already resolved or the operator supplies.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every stop outcome names its condition and its safe follow-up path, and the matching state proceeds unambiguously.
- consistency: the step's wording agrees with the source adapter's metadata field names and the project-scope gate.
- admission honesty: the inline machinery admission carries all four fields.

**Done when:**
- The four offline sample contexts (merged, advanced head, mismatched branch, matching) appear in the skill text with their stop or proceed outcomes under those single names.
- The amended workflow reads as one ordered procedure with no duplicated scope rule.
- The public-hygiene scan exits 0 on the changed file.

**Ship when:**
- none (repository-internal skill text).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/receiving-review/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/github-pr-workflow/SKILL.md`; reason: the adapter primitive is the referenced single home and stays unchanged.
- `agents/skills/doing-code-review/SKILL.md`; reason: active review is a different workflow and the origin scopes this to receiving-review.

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
```

### Task 1: the pre-edit reconciliation step

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Feedback-source Workflow` in `agents/skills/receiving-review/SKILL.md`, which owns the ordered steps the reconciliation joins.

- [ ] The workflow gains the pre-edit reconciliation between the source-adapter identification step and the branch-scope check: given resolved PR head metadata, expects the comparison of lifecycle state, head branch name, and head commit SHA with the local checkout binding before any edit, reusing metadata the workflow already resolved. [class: IMPLEMENTATION_REQUIRED]
- [ ] The comparison requires the four resolved fields: given a resolved context lacking state, baseRefName, headRefName, or headRefOid, expects the reconciliation to route to the unreadable-metadata stop. [class: IMPLEMENTATION_REQUIRED]
- [ ] Each stop outcome names its safe follow-up path: given a merged or closed PR, expects a stop naming the follow-up branch off the base as the path to verify before edits; given a branch-name mismatch, expects a stop naming operator selection or creation of the correct local branch; given an advanced head (same branch name, different head commit SHA), expects a stale stop with no automatic pull. [class: IMPLEMENTATION_REQUIRED]
- [ ] The unreadable-metadata stop: given PR head metadata that cannot establish the target, expects a stop that never infers lifecycle state from the local branch name. [class: IMPLEMENTATION_REQUIRED]
- [ ] The local-only carve-out: given a personal or pet project, expects the step to consume already-resolved metadata or the operator's supplied state and never to issue a new remote query, and the sample text to avoid the pins-forbidden literal that blacklists the exact two-word project phrase the pins suite expects absent from this file. [class: IMPLEMENTATION_REQUIRED]
- [ ] The marker relationship is named and the pinned sentence preserved: given the amended workflow, expects one line stating the reconciliation's live comparison is the source of truth at pre-edit time and the review-thread marker's recorded branch head is refreshed after an operator rebind, while the marker section's pinned sentence survives byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `skills: bind receiving-review edits to the live PR head` [class: IMPLEMENTATION_REQUIRED]

### Task 2: sample contexts and admission

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Feedback-source Workflow` in `agents/skills/receiving-review/SKILL.md`, the section the samples and admission line join.

- [ ] The four offline sample contexts are present: given the skill text, expects realistic merged, advanced-head, mismatched-branch, and matching samples, each naming its stop or proceed outcome without consumer identifiers. [class: IMPLEMENTATION_REQUIRED]
- [ ] The machinery admission line is present: given the step's text, expects the witnessed incident, expected catch frequency, false-positive cost, review date, and the augmented late check named in one place. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `skills: reconciliation samples and admission` [class: IMPLEMENTATION_REQUIRED]

### Task 3: vendored-sync disposition and validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Feedback-source Workflow` in `agents/skills/receiving-review/SKILL.md`, the edited surface the disposition records.

- [ ] The vendored-sync disposition is recorded beside the landing: given the edited skill file, expects the run either to mirror it to the deployed runtime copy or to name the changed file in a tracked vendored-sync landing row. [class: IMPLEMENTATION_REQUIRED]
- [ ] The validation battery passes: given the two Validation Commands, expects both exit 0 in sequence with the changed file present. [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: the battery passes. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: receiving-review reconciliation validation` [class: IMPLEMENTATION_REQUIRED]
