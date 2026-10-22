# Plan: Reviewer-Sized Dependent Plan Parts

Backlog origin: docs/history/backlog/2026-10-22-reviewer-sized-dependent-plan-parts.md
Driving force: new-capability; this user-requested authoring option is implemented because it is not one of the five driving principles, and park-triage would not provide the capability.
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-reviewer-sized-dependent-plan-parts-r*.md
Execution budget: 0.75h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-22-reviewer-sized-dependent-plan-parts.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms
- Dependent plan: a plan that waits for an earlier plan to land before it starts.
- Execution dependency: the existing plan-header field that names the earlier plan a dependent plan waits for.
- `parked_dependencies`: maintenance state entries that keep a dependent plan from starting before its predecessor lands.
- Review-size limit: the requester-specified maximum change size for each plan part, recorded with its measure and unit.
- Part count: the requester-stated number of plans, kept separate from the per-part review-size limit.
- Shared-file seam: production or test files that must stay within one plan; a split never puts tasks editing the same file in separate plans.

## Why
The plan authoring questions do not clearly capture a requested review-size limit or separate plan and pull request landing boundaries. Task-level reviews do not create separate plan or pull request landings.

## Gist & Examples
TLDR: capture a per-part review-size limit and offer dependent plan parts, to support bounded review and landing (new-capability).

Before: a request for separately reviewable parts can be mistaken for task-level reviews or phased deployment, and a part count can leave each plan size unbounded.
After: the author records the requested per-part maximum change size with its measure and unit, separately from any desired part count, then maps dependent plans to distinct outcomes and acceptance criteria. If the size limit is missing, the author asks through the existing Phase 1 clarification flow and keeps the single-plan default until it is supplied. Shared-file sets stay within one plan, and later plans use the existing execution dependency.

## Outcome
When requested, plan authors can record a per-part review-size limit and map a coherent outcome to separately reviewable and landable dependent plans.

- The single-plan path remains the default until a requester-specified per-part maximum change size, measure, and unit are available.
- Each chosen part has its own behavior, acceptance criteria, and file ownership, and stays within the stated per-part limit; a desired part count is recorded separately.
- Tasks editing the same production or test file stay in one plan; the existing execution dependency orders separate plans.

Gate delta: none; this adds no gate, fence, refusal, protocol layer, state field, or dispatch pause, and removes none.

## Assumptions
- A review-size split needs a requester-specified maximum change size for each part, with its measure and unit; a desired part count is separate. If the per-part limit is absent, the existing Phase 1 clarification flow asks for it while the single-plan path remains available. Basis: origin Problem and Expected sections.
- Existing rollout strategy language covers deployable release phases, not independent review and landing boundaries; basis: plans skill Phase 1 and execution-plan review lifecycle.
- The existing execution dependency and maintenance queue state can order separate plans; tasks editing the same production or test file remain in one plan. Basis: plans skill seam rule and maintenance state-file guidance.
- Scope extension `docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md` is omitted (`omit-extension`, maintenance-selected arm); basis: it concerns run closeout ownership and is unrelated to plan authoring boundaries.
Decision points requiring a grill: none remain.

## Evaluation Criteria
The optional authoring choice records a requester-stated per-part review-size limit, preserves the single-plan default, and relies only on existing dependency and shared-file seam guidance.

**Quality dimensions:**
- Clarity: the author can distinguish task reviews, deployment phases, and separate plan landings.
- Scope: no repository-wide size threshold, automatic split, new ledger, or second review lifecycle is introduced.

**Done when:**
- `agents/skills/plans/SKILL.md` describes the choice and its boundaries in the existing Phase 1 rollout-strategy question.
- The skill retains the single-plan default and points split choices to existing dependency and shared-file seam rules.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:** none.

**Tests:** none.

**Documentation:**
- `agents/skills/plans/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; reason: execution lifecycle is unchanged.
- `agents/skills/maintenance/state-file.md`; reason: existing dependency state is sufficient.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-23-reviewer-sized-dependent-plan-parts.md --pre-round
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Add the optional dependent-plan authoring choice

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/plans/SKILL.md`

- [ ] `agents/skills/plans/SKILL.md` offers the optional separate-plan choice in the existing Phase 1 rollout-strategy question: given a request for independently reviewable landings, expects the author to record a requester-specified per-part maximum change size with its measure and unit, separately from any desired part count [class: IMPLEMENTATION_REQUIRED]
- [ ] When a requester wants separate plans but has not given a per-part maximum, the existing Phase 1 clarification flow asks for the limit while preserving the single-plan default [class: IMPLEMENTATION_REQUIRED]
- [ ] Each requested part has distinct behavior, acceptance criteria, and file ownership and stays within its recorded size limit; separate plans use the existing execution dependency [class: IMPLEMENTATION_REQUIRED]
- [ ] Tasks editing the same production or test file remain in one plan; no repository-wide size threshold, automatic split, ledger, or review lifecycle is added [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: offer dependent plan parts for review boundaries` [class: IMPLEMENTATION_REQUIRED]
