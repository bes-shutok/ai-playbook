# Plan: Clarify review continuation and worktree teardown

Backlog origin: docs/history/backlog/2026-10-21-review-reconciliation-continuation-stop.md
Driving force: simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-10-21-plan-review-review-reconciliation-continuation-stop-p5dd4432a-r*.md (the highest rN for this source-plan path is authoritative)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Recurrence stop:** the rule requiring a new direction when a fresh review reopens the same root after reconciliation.
- **Teardown gate:** the closeout check that requires owned review records to be present in the primary reviews home before removing a worktree.
- **Authorized review:** one bounded review round covered by an explicit user direction in the current session.

## Why

The R28 review reopened a root that had already returned after reconciliation, so the recurrence stop correctly required new user direction before another panel. A separate teardown gate refused because review records had not yet been migrated; its refusal delayed worktree removal, not review in the retained worktree. State that distinction in the review handoff, preserving both existing protections.

## Gist & Examples

Title: Clarify review continuation and worktree teardown
TLDR: Separate the review recurrence stop from the teardown gate so an authorized review can continue while artifact migration is pending, preserving both protections with concise wording.
Before: A repeated root requires escalation before another review, while the teardown gate protects review records but its refusal can be mistaken for a review stop.
After: The handoff says that a recurring root needs fresh direction and a separate teardown refusal only delays removal; an explicitly authorized review may continue in the retained worktree.
Edge cases: A fresh review resets the recurrence count after completion unless the same root recurs; a repeated root still needs new direction; the worktree remains until records are migrated and the removal gate passes.

## Outcome

The review handoff distinguishes authorization to continue review from the evidence required to remove its worktree.

- A fresh review that reopens the same root still requires new direction before another round.
- A teardown refusal does not block a review explicitly authorized in the existing worktree.
- Review artifacts still migrate to the primary home and pass the existing gate before removal.

Gate delta: No gate or refusal condition changes; the handoff only separates review continuation from teardown.

## Problem Statement

The review-reconciliation skill escalates a recurring root, and the plans closeout gate protects review artifacts before worktree deletion. The recent handoff treated the gate refusal as though it could block continuing the review. Clarifying the ownership boundary should prevent that confusion without changing either gate or the scope of an operator's direction.

## Design Invariants

- Keep the recurrence stop and recurrence-chain retention unchanged.
- Keep the primary-home artifact migration and worktree-removal gate unchanged.
- An explicit direction authorizes only the bounded next review it names; a recurring root after that review requires renewed direction.
- A teardown refusal never authorizes bypassing artifact migration or deleting the worktree.
- Add no approval flag, state, validator, retry, worker, or refusal condition.
- Keep the operative skill edit in its existing return-control paragraph and do not grow that file in bytes.

## Detailed Design

Replace the existing caller-handoff wording in `agents/skills/review-reconciliation/SKILL.md` with a shorter statement that retains caller-owned fresh review and recurrence escalation, and clarifies that a separate teardown-gate refusal delays worktree removal but does not prevent an explicitly authorized review in the retained worktree. The same wording must keep the migration-and-pass requirement before removal. Do not edit `agents/skills/plans/SKILL.md` or `scripts/worktree_closeout_migrate.py`; they remain the source of the teardown behavior.

## Implementation Plan

### Task 1: Clarify review continuation and teardown boundaries

Context surface: the Return control to the original orchestrator section and the existing recurrence stop.

Files:
- `agents/skills/review-reconciliation/SKILL.md`
- `agents/skills/plans/SKILL.md` (read-only source for the teardown gate)
- `scripts/worktree_closeout_migrate.py` (read-only source for the removal refusal)
- `scripts/test_worktree_closeout_migrate.py` (read-only existing refusal coverage)
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r27-reconciliation.md`
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r28.md`
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r28-reconciliation.md`

- [ ] Given a fresh review reopens the same root, keep the existing recurrence chain and require fresh direction before another review; reset the recurrence counter after that review completes, unless the same root recurs and the stop applies again. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the removal gate refuses because review artifacts are missing from the primary home, state that an explicitly authorized review may continue in the retained worktree, while removal still waits for artifact migration and a passing gate. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the change within the existing handoff paragraph, make the edited skill file byte-neutral or smaller, and add no new gate or authorization state. [class: IMPLEMENTATION_REQUIRED]
- [ ] Confirm the historical R27/R28 sequence and teardown refusal from the backlog origin and the gate implementation/refusal coverage; do not claim that the current primary checkout still reproduces the historical missing-artifact refusal. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the public-hygiene and em-dash checks on the changed skill text; leave the existing closeout gate and its tests unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete the backlog origin in the landing rider and prune this plan's dispatch entry with the plan-file witness. [class: IMPLEMENTATION_REQUIRED]

## Evaluation Criteria

**Quality dimensions:** Correct ownership of the two stops; direct, bounded guidance; no weakening of evidence preservation.

**Done when:**
- The handoff distinguishes another review from worktree removal in one existing paragraph.
- The same-root stop still requires direction and retains its recurrence chain.
- Teardown still requires migrated artifacts and a passing gate.
- The changed skill file is no larger than its baseline and no other operative file changes.
- The backlog origin is removed in the same landing that carries the plan's covered witness.

**Ship when:** None. This is repository guidance with local validation.

## Review Scope

**Explicit must-fix:** findings that make the recurrence stop ambiguous, imply that teardown refusal blocks an authorized review, weaken artifact migration, or add unapproved machinery.

**Documentation:**
- `agents/skills/review-reconciliation/SKILL.md`

**Read-only evidence:**
- `docs/history/backlog/2026-10-21-review-reconciliation-continuation-stop.md`
- `agents/skills/plans/SKILL.md`
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r27-reconciliation.md`
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r28.md`
- `.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r28-reconciliation.md`

**Out of scope:**
- Changes to review behavior, caller worker selection, the recurrence counter, or operator authorization semantics.
- Changes to plans closeout, artifact migration, removal tooling, tests, flags, validators, and state files.

## Validation Commands

```bash
bash scripts/scan-public-hygiene.sh --files agents/skills/review-reconciliation/SKILL.md
bash scripts/check-no-em-dash.sh file agents/skills/review-reconciliation/SKILL.md
```

## Assumptions

- The user has already directed continuation and least-importance-first plan authoring; no additional choice is required for this bounded plan.
- The handoff wording, rather than either gate, is the only proposed edit surface.

Decision points requiring a grill: none remain.
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.
