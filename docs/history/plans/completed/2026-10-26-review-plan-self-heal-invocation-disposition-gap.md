# Plan: Make Self-Heal Invocation Order Clear Across Review Loops

Backlog origins (scope of record):
- docs/history/backlog/2026-10-25-review-loop-reuses-self-heal-disposition.md
- docs/history/backlog/2026-10-26-review-plan-self-heal-invocation-disposition-gap.md
Driving force: simplicity + code-quality
Plan review record: .ai-playbook/reviews/2026-10-26-plan-review-review-plan-self-heal-invocation-disposition-gap-p62b67d8d-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-26-review-plan-self-heal-invocation-disposition-gap.md (session 01a173fd-e065-7d41-a91d-8752a79627af)

## Terms

- **Active recurrence:** a review trigger that requires reconciliation before another review or fix pass.
- **Run-wide attempt state:** the existing `extensions.convergence.self_heal_attempt` value that tracks whether the review run's single authorized self-heal attempt is unused, consumed, or unknown.
- **Unknown state:** a run-wide attempt state that cannot authorize self-heal because prior attempt identity or chain evidence is missing or malformed.

## Why

The review-plan policy requires reconciliation followed by self-heal before pausing on active churn or recurrence, but the pause rule was misread as a stop before that assessment. The review-loop stop path also repeats a self-heal call after the run's one attempt may already be consumed. One clear owner sequence can address both errors.

## Gist & Examples

Title: Make Self-Heal Invocation Order Clear Across Review Loops
TLDR: Clarify one authorized self-heal assessment per review run, for simplicity and code quality.
Before: A required assessment can be skipped before a pause, while a separate stop path can request the assessment again after the attempt was used.
After: Review-plan owns the order, review-loop follows it, and the existing attempt state determines whether assessment is available or the run must pause.
Edge cases: Reconciliation still comes first; an unknown state or a consumed attempt never authorizes another assessment; caller authorization and review budgets still govern.

The sequence applies to two concrete cases. For an active recurrence with an unused state and caller authorization, reconcile, assess, reserve the attempt before a change, then run the required fresh review. If the state is consumed or unknown, reuse its existing evidence and pause before another review when the same blockers remain.

## Outcome

Make review-loop sessions assess active recurrence once before pausing and reuse the existing run state after that assessment.

- Active recurrence reaches reconciliation and the authorized self-heal assessment before a pause is considered.
- A consumed or unknown attempt state prevents a repeated assessment in the same run.
- The two backlog origins receive distinct dispositions in the completed plan.

Gate delta: removes the duplicate direct self-heal call from review-loop and clarifies the existing review-plan invocation order; adds no gate, refusal class, fence, protocol layer, state field, or review-layer duty. The existing one-attempt limit, authorization, reconciliation, budget, and pause boundaries stay in force.

## Assumptions

- assume `extensions.convergence.self_heal_attempt` remains the single source for the run-wide attempt allowance; basis: `review-staging/SKILL.md` defines unused, consumed, and unknown states and `review-plan/SKILL.md` consumes them.
- assume the missed assessment arose from execution noncompliance that clearer ordering can reduce; basis: the 2026-10-26 origin says the policy already required reconciliation and self-heal, and the recommendation was applied without invoking self-heal.
- assume review-plan owns the trigger, authorization, and attempt sequence; review-reconciliation owns reconciliation and returns to its caller; self-heal owns the bounded assessment and recovery action; basis: the three current skill contracts.

Decision points requiring a grill: reuse the existing attempt state and add no separate disposition field; user accepted this recommendation on 2026-10-26; affects the policy sequence and state contract.
Scope extensions (grilled): none proposed.
Sources inspected: both backlog origins; the `self-heal-review-invocation-disposition-contract` entry; `review-plan/SKILL.md` Scope and complexity policy and attempt-state paragraph; `review-loop/SKILL.md` orchestration rule 5 and integration points; `review-reconciliation/SKILL.md` trigger and handoff; `self-heal/SKILL.md` Repeated review cycles and Integration Points; `review-staging/SKILL.md` run-wide attempt state; the completed 2026-10-08 review-policy plan; review-loop r12 F1 and r13 F1.

## Standing constraints

- Keep reconciliation before another review or fix pass.
- Keep the caller's authorization, run-wide one-attempt limit, fresh-review requirement, review budgets, and pause conditions.
- Add no gate, validator, lock, ledger, state field, or required ceremony.
- Pay for any operative skill-text growth with equivalent deletions in the same change.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: active recurrence reaches the authorized assessment before a pause, and a consumed or unknown state cannot start another assessment.
- Clarity: review-plan owns the sequence and review-loop does not restate or duplicate it.
- Simplicity: the edited skill text does not grow without equivalent deletion.

**Done when:**
- The review-plan, review-loop, and self-heal integration text expresses one sequence using the existing state and caller authorization.
- The skipped-assessment origin is recorded as execution noncompliance with the clarified sequence; the duplicate-assessment origin is resolved by removing the redundant review-loop call.
- Realistic samples of both origin trajectories and the unused, consumed, and unknown states produce the expected next action.

**Ship when:** None; this is a repository policy change.

## Review Scope

**Explicit must-fix:** any finding that permits skipping the authorized assessment before a pause, repeats an assessment after the run state is consumed or unknown, or weakens caller authority or review limits.

**Production code:** none.

**Tests:** none added by this plan.

**Documentation:**
- `agents/skills/review-plan/SKILL.md` (Task 1)
- `agents/skills/review-loop/SKILL.md` (Task 1)
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Out of scope; reject unless plan-related:**
- Other review-loop budgets, schemas, validation rules, or machinery; reason: neither origin requires changing them.
- `review-reconciliation` behavior; reason: it already owns reconciliation and returns control to the original orchestrator.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh --files agents/skills/review-plan/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/self-heal/SKILL.md
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file agents/skills/review-plan/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/self-heal/SKILL.md
```

### Task 1: Clarify one state-aware self-heal sequence

Context surface: the plan's Terms, this task, and Standing constraints.

Files:
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/self-heal/SKILL.md`

- [x] Given active recurrence with unused state and caller authorization, expect reconciliation, one self-heal assessment before any pause, and attempt reservation before a concrete change. [class: IMPLEMENTATION_REQUIRED]
- [x] Given consumed state, expect reuse of the prior attempt and a pause before another review when the same blockers remain. [class: IMPLEMENTATION_REQUIRED]
- [x] Given unknown state, expect a pause without another self-heal assessment. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an active-churn path through review-loop, expect delegation to review-plan's sequence without a second direct self-heal call. [class: IMPLEMENTATION_REQUIRED]
- [x] Review both origin scenarios and realistic samples for unused, consumed, and unknown states; record the observed next action in the task log. [class: REPOSITORY_TEST]
- [x] Pay for any operative skill-text growth with equivalent deletions and preserve every standing constraint. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: clarify self-heal invocation order` [class: IMPLEMENTATION_REQUIRED]

## Disposition of the migrated backlog items

Both origin rows (2026-10-25-review-loop-reuses-self-heal-disposition, 2026-10-26-review-plan-self-heal-invocation-disposition-gap) are covered by this plan and deleted in the archive change (squash of branch 2026-10-26-self-heal-invocation-order). Phase 3 fresh-adversarial review returned 0 blocking, 0 backlogged candidates.
