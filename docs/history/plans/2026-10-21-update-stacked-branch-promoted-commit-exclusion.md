# Plan: Promotion-aware recovery for open-stack rebases

Backlog origin: docs/history/backlog/2026-10-21-update-stacked-branch-promoted-commit-exclusion.md
Driving force: correctness
Plan review record: the staging series .ai-playbook/reviews/2026-10-21-plan-review-update-stacked-branch-promoted-commit-exclusion-r*.md
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Method C:** the existing explicit, bottom-up rebase procedure for open stacked branches.
- **Promoted commit:** a child-branch commit that the operator has separately applied to the updated parent.
- **Exact equivalent:** a child commit whose complete change is already present in the updated parent, with the same affected paths and resulting content. A matching patch identifier can locate a candidate but does not prove this by itself.
- **Partial overlap:** a child commit whose change intersects the promoted change but still carries child-only work.
- **Parent-relative diff:** the child branch changes compared with its updated parent after rebasing.
- **Rebase todo:** the ordered list of commits an interactive rebase will replay, edit, or omit.

## Why

Method C handles explicit open-stack rebases, but it currently treats every conflict or verification failure as an unconditional abort. When a selected child commit has already been promoted to its parent, that rule cannot distinguish a safely removable duplicate from a later child commit that still needs its own changes.

## Gist & Examples

TLDR: Add a bounded promotion-aware path to Method C so a child rebase excludes work already in its updated parent while preserving child-only changes, for correctness.

**Before:** A promoted commit is replayed or conflicts with a later overlapping child commit; Method C aborts the entire rebase without a verified continuation path.

**After:** The operator drops only a child commit proven to be an exact equivalent of the promoted parent change, replays the remaining child commits, and verifies the child-only result against the pre-rebase delta.

**Edge cases:** A partial patch-id match is not enough to drop a commit. Keep overlapping child work and resolve it against the updated parent; abort and restore the backup if the remaining child delta cannot be proved.

## Outcome

A requested open-stack rebase can remove a change already promoted to its parent and retain the child's remaining work through an evidence-based recovery route.

- Exact promoted duplicates can be excluded without replaying them into the child branch.
- Later overlapping child changes remain present when they can be resolved and verified against the updated parent.
- Unresolved or unverified rebases keep the existing abort-and-restore protection.

Gate delta: None. This plan adds no gate, validator, lock, ledger, or required ceremony and removes no existing refusal; it documents a bounded continuation under Method C's existing backup and verification rules.

## Assumptions

- The promotion and exclusion route belongs in `update-stacked-branches` Method C. Basis: its routing table owns explicit rebases of open stacks; `github-pr-workflow` owns post-squash parent reparenting with `rebase --onto`.
- Use an interactive rebase todo to omit only exact-equivalent promoted commits and retain the existing child commit sequence. Basis: this is a smaller change to Method C than rebuilding the child and selecting commits again; partial overlaps stay in the rebase and must pass the existing backup, conflict, and final-delta checks.
- The `986665a65` introduction of Method C intentionally made conflicts abort-and-restore. Keep that protection for unresolved conflicts; this plan adds a narrow verified continuation for the witnessed promotion case.
- The origin's declared `fix-class` matches its body: the missing procedure is a repair to an existing workflow, with no new refusal class.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: only an exact-equivalent promoted commit is removed from the replay; partial overlap is preserved for resolution.
- Recovery safety: every uncertain or failed verification returns to the existing backup and abort path.
- Scope clarity: open-stack rebasing remains in `update-stacked-branches`; post-squash reparenting remains in `github-pr-workflow`.

**Done when:**
- Method C explains the promotion case, the exact-equivalence evidence, the partial-overlap route, and the final verification needed before continuing.
- The existing backup, abort, restore, ancestry, and parent-relative diff checks remain explicit.
- The `github-pr-workflow` routing boundary remains accurate and does not duplicate Method C.
- The hygiene and em-dash checks pass for the edited skill.

**Ship when:** None. This is a shared skill procedure with repository-local verification.

## Review Scope

**Explicit must-fix:** findings on this path are always in scope:

**Production code:** None.

**Documentation:**
- `agents/skills/update-stacked-branches/SKILL.md`

**Tests:** None; this plan changes a skill procedure and introduces no executable behavior.

**Plan-related extension:** `agents/skills/github-pr-workflow/SKILL.md` may change only if source review finds its routing text conflicts with the selected Method C route; otherwise leave it unchanged.

**Out of scope; reject unless plan-related:**
- Other rebase methods, merge-based restacking, PR administration, and remote pushing; the origin concerns only selected commit promotion during an explicit open-stack rebase.

## Validation Commands

```bash
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh
```

### Task 1: Add the promotion recovery to Method C

Context surface: the plan's Terms, this task, and the existing Method C backup and verification rules.

Files:
- `agents/skills/update-stacked-branches/SKILL.md`

- [ ] Add a Method C subcase that compares interactive todo omission with rebuilding the child on the updated parent and replaying only child-owned commits, then uses the interactive todo route for exact-equivalent promoted commits. [class: IMPLEMENTATION_REQUIRED]
- [ ] Require evidence beyond patch-id equality before dropping a commit; retain a partially overlapping commit and resolve it against the updated parent rather than dropping child-only work. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the continuation boundary: proceed only when the resolved tree preserves the parent's version and the final parent-relative diff and ancestry prove the expected child-only delta; otherwise abort and restore the Phase 0 backup. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve Method C's bottom-up order, no-squash default, push approval rule, and existing backup lifetime; leave the `github-pr-workflow` route unchanged unless its current wording contradicts the open-stack boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands and review the Method C wording against the routing table and the origin's exact-equivalence versus partial-overlap distinction. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: handle promoted commits in stacked rebases` [class: IMPLEMENTATION_REQUIRED]
