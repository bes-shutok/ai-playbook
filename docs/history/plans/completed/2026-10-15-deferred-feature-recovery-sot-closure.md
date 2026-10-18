# Plan: Deferred feature findings keep the recovery boundary and the feature SOT link

Backlog origin: docs/history/backlog/2026-10-15-deferred-feature-recovery-sot-closure.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-deferred-feature-recovery-sot-closure-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.25h total, largest task 0.5h

## Terms

- recovery boundary: the statement separating what current code and tests already recover (an existing retry or reconciliation path, with its owner and trigger) from the behavior that remains unrecovered when the caller does not retry.
- implementer SOT: the existing feature-level source-of-truth document, or the documentation section owning a deferred behavior's implementation anchor, that a backlink from the backlog item hangs from.
- deferred feature-behavior finding: a valid review finding deferred unfixed whose subject is product or feature behavior; a code-only cleanup with no deferred behavior is not one.
- capture condition: a required-content rule in receiving-review's Backlog capture list; prose the capturing session must satisfy, never a validator.
- no-SOT route: the explicit disposition for a deferred finding with no feature-level implementer SOT: the item records that absence and no backlink task is created.

## Why

A valid deferred feature finding reached its backlog draft without the recovery boundary or a link from the feature's implementer source of truth, and the user had to correct both before the handoff was accurate. The three skills that hand a finding along each hold part of the duty and none states it, so the correction is not reproducible on the next deferral.

## Gist & Examples

TLDR: Backlog capture for deferred feature-behavior findings states the evidenced recovery boundary and links the item from the feature's implementer source of truth, because a deferral that misstates recovery or drops the SOT thread is a handoff reliability defect (declared force code-quality; the plans closed set has no reliability tag, which the origin row declares).

Before: a deferred finding is captured by name and scope alone; the draft can claim "no retry or reconciliation path exists" while an idempotent caller-triggered retry does exist, and nothing connects the item to the document that owns the deferred behavior.
After: the capture records the boundary (what already recovers, what remains, who owns the retry, the trigger condition), names the item for the missing behavior, and links the item from the feature's implementer SOT when one exists; a deferred feature-behavior finding with no such SOT records that absence explicitly through the no-SOT route.
Edge: a feature whose implementer SOT is a code anchor rather than a document links from the documentation section owning that anchor; a code-only cleanup sits outside the capture condition's scope entirely and gains neither the condition's duties nor a documentation task; a plan authored later from the item preserves the recorded boundary instead of re-deriving scope.

## Outcome

The review-to-backlog-to-plan handoff reproduces the corrected deferral without a user correction.

- Deferred feature-behavior backlog items carry the evidenced recovery boundary.
- Items for deferred feature behavior are linked from the feature's implementer SOT when one exists, and the no-SOT route is explicit.
- Plans and execute-plan closeouts preserve the recorded boundary instead of diverging from the source document.

Gate delta: prose-only capture-condition and preservation duties added across three existing skills; no refusal class, hard gate, fence, protocol layer, or schema field is added or removed, and no checked set grows: the plans edit is one preservation sentence beside an existing rule, and the execute-plan edit extends the content an existing scope summary already names per deferred capability (it adds no exit-time check); the one scoped capture bullet is priced by the origin row's recorded alternatives and rejections (docs/history/backlog/2026-10-15-deferred-feature-recovery-sot-closure.md, Problem, Expected, and Suggested investigation), the origin-cited justification for a fix-class duty whose origin records the alternatives.

## Assumptions

- assume the capture condition scopes to deferred findings whose subject is product or feature behavior; basis: the origin Expected paragraph's cleanup-only counterexample.
- assume an implementer SOT may be a document or the documentation section owning a code anchor; basis: the origin's "implementer source of truth" wording.
- assume no review-agent lens change is needed; the capture condition is checked at capture time; basis: the entry's Orientation (a lens needs only a pointer, not a new duty) and the entry's Machinery admission line.
- assume the plans and execute-plan edits are pointers to the capture condition, never restatements; basis: the origin's "Prefer consolidating or clarifying current prose" arm.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill-text edits follow the repository guidelines' Skill text anti-growth rules: land the rule; the incident stays in the origin row.
- An edit never rewrites prose outside the lines the task touches, and never reorders existing sections.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the edited capture conditions reproduce the origin's corrected deferral (recovery boundary, feature-oriented naming, SOT backlink, no-SOT route) with no new machinery.
- maintainability: each skill edit is a pointer or one consolidated bullet; no duty restated across files.

**Done when:**
- the three edited skill files pass the validation sweep (portability, doors, hygiene) with exit 0 each.
- the worked example (feature-behavior deferral with an SOT) and the counterexample (cleanup-only, no SOT) both classify correctly under the edited text.

**Ship when:**
- prose-only repository work; no external conditions.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any new validator, gate, ledger, artifact type, or review-agent prompt file; reason: the origin's Machinery admission line rejects blocking machinery without a witnessed catch, and the entry's rejected alternatives cover the lens and round additions.

## Validation Commands

```bash
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
bash scripts/scan-public-hygiene.sh
```

### Task 1: Backlog capture states the recovery boundary and the SOT disposition

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Backlog capture for valid findings not fixed in scope` in `agents/skills/receiving-review/SKILL.md`

- [x] The required-content list gains one scoped bullet for `deferred` findings whose subject is feature behavior: the item names the missing behavior (feature-oriented, not task-key-oriented) and states the recovery boundary with evidence: what current code or tests already recover, what remains unrecovered, who owns the retry or recovery, and the condition that makes the gap relevant [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet requires the SOT disposition: when a feature-level implementer SOT exists, the item is linked from that SOT; when none exists, the item records the no-SOT route explicitly and creates no backlink task [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the origin's observed draft (a no-retry-path claim over an existing caller-triggered retry, a task-key-oriented name, no SOT link), expects the edited capture conditions to classify the draft incomplete on all three counts [class: REPOSITORY_TEST]
- [x] Run → expect RED: neither "recovery boundary" nor "implementer SOT" appears in the section before the edit (grep probe, execution-selected) [class: REPOSITORY_TEST]
- [x] Apply the minimal edit: one consolidated bullet in the existing required-content list; no other prose rewritten [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the section names the recovery boundary, the feature-oriented naming rule, the SOT backlink, and the no-SOT route [class: REPOSITORY_TEST]
- [x] Commit: `skills: capture the recovery boundary and SOT disposition for deferred feature findings` [class: IMPLEMENTATION_REQUIRED]

### Task 2: plans and execute-plan preserve the recorded boundary at handoff

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `Origin acceptance that contradicts a current SOT placement rule` in `agents/skills/plans/SKILL.md`
- `Scope summary (per round, before the first lens launches)` in `agents/skills/execute-plan/SKILL.md`

- [x] plans: one sentence beside the existing origin-acceptance SOT rule: an origin that defers feature behavior carries its recovery boundary and SOT disposition into the plan, and the plan preserves them rather than re-deriving that scope; given a plan authored from such an origin, expects the plan's scope text to carry the recorded boundary verbatim rather than a re-derived recovery claim [class: IMPLEMENTATION_REQUIRED]
- [x] execute-plan: one clause in the Phase 3 scope-summary paragraph extending what the summary already names per deferred capability: the owning backlog reference is named together with its recorded SOT disposition; given a round whose deferred capability's item records an SOT link, expects the assembled scope summary to name that reference and disposition as reviewer input, with no new exit-time check [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the preservation sentence resolves in plans and the exit clause resolves in execute-plan (anchor grep, execution-selected) [class: REPOSITORY_TEST]
- [x] Commit: `skills: preserve the deferred-feature recovery boundary across plan and closeout handoffs` [class: IMPLEMENTATION_REQUIRED]

### Task 3: validation sweep and corpus audit

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `Backlog capture for valid findings not fixed in scope` in `agents/skills/receiving-review/SKILL.md`

- [x] Run the three Validation Commands; exit 0 each [class: REPOSITORY_TEST]
- [x] Corpus duplication audit: search receiving-review, plans, execute-plan, and the review-agents catalogs for existing recovery-boundary or SOT-link duties that overlap the new bullet; consolidate or point, none duplicated [class: REPOSITORY_TEST]
- [x] Worked-example verification: compose four classification cases (feature-behavior deferral with an SOT; feature-behavior deferral with no SOT; cleanup-only with no SOT; a plan-plus-round pair over an SOT-linked item) and record the edited text's disposition for each in the task log [class: REPOSITORY_TEST]
- [x] No branch commit (verification task) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

The origin row was deleted by the authoring landing c46d71755 with this plan as the covering witness, and the frozen PLAN-PROMPTS entry was pruned with its receipt in the same change. This plan is the covering disposition.
