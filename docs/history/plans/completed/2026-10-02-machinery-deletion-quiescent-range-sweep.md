# Plan: Adjudicate the quiescent-point deletion-range residual as covered by composed reconciliation

Backlog origin: docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md
Driving force: simplicity (the residual carries no witness of a failure the proposed arm would have changed; the composed mechanisms already cover the class, so the plan declines the new arm and records the adjudication in the owning document, per the burden-of-proof rule that keeping unproven complexity out is the same duty as deleting it)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-machinery-deletion-quiescent-range-sweep-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Close the quiescent-point residual by adjudication in the owning document instead of wiring a new deletion-consult arm.

- The Post-landing reconciliation implementation (the owning block in `agents/skills/execute-plan/SKILL.md`) carries a scope note of one to three sentences: the reconciliation's per-path classification covers the recorded landing's pre-tip-to-post-tip window, and the residual's older-deletion-range class is covered by composed mechanisms named per checkout shape, with the origin cited.
- `scripts/reconcile_post_landing.py` gains no quiescent arm, no new flag, and no new row class; the machinery deletion consult surface is unchanged.
- The origin item stops surviving only as a scheduler-state receipt line: the adjudication and its three-part reason are greppable in the owning document, and the executor closes the origin through the normal lifecycle.

Gate delta: none. The plan adds one adjudication sentence to an existing owning document and no gate, refusal class, fence, protocol layer, or scheduler state field; the proposed arm it declines would have been the machinery addition.

## Terms

- **Quiescent point**: a commit at which a since-deleted path was at rest; the residual proposed sweeping deletion-relevant history for such points older than the current landing window.
- **Tip guard**: the reconcile run's first check (HEAD must still equal the post-landing tip, else a newer landing owns the checkouts); the "tip window" is the recorded landing's pre-tip-to-post-tip range.
- **Deleted-arm**: the reconcile classification for paths a landing deleted (index-absent orphan removed; index blob matching no ancestor blocked as a peer's staged edit), per the script docstring and the owning block.
- **Composed coverage**: the property that no separate arm is needed because existing mechanisms jointly cover the class, per checkout shape (the ff-only fast-forward for detached checkouts, the stale-checkout discriminator's restore-and-record arm for base-branch checkouts, the classify-deleted REMOVE arm for untracked copies, and the full-history ancestor walk inside the landing window).

## Assumptions

- The residual's complete record trail is the scheduler-state receipt (the superseded landing-orphan-sweep authoring entry naming `scripts/reconcile_post_landing.py`'s tip-guard-blocked deleted-arm) plus the preserved audit record `docs/reviews/2026-10-01-plan-review-landing-orphan-sweep-r2.md`, whose round history carries the folded sibling-relationship sentence; the plan text itself survives only in that record (basis: both artifacts re-read on disk 2026-10-02; no plan file exists under `docs/history/plans/` or its subdirectories for the superseded authoring).
- The untracked-orphan deletion shape is owned by the peer's covering cycle: the plan landing `37beab52` (the worktree-closeout plan document; the prior origin's covered flip names that plan path) and the mechanism landing `5dc82ca5`, which introduced the index-absent-orphan REMOVE arm in `scripts/reconcile_post_landing.py` and the test witnessing it (basis: both commits' diffs read on disk; `37beab52` touches only the plan document, `5dc82ca5` touches the script, the skill, and both test files; the origin item's own verification confirms the landed mechanism contains no quiescent arm, which is exactly the gap this plan adjudicates rather than fills).
- Older-range deletions reach the two checkout shapes through different composed mechanisms: a detached checkout behind the post tip receives them through the restore phase's ff-only merge, which fires only for detached checkouts (the ff_needed flag is keyed on the detached attribute) and materializes every intermediate tree change, a refusal degrading to the ff-refused block row; a base-branch checkout (symref HEAD, the primary included) receives them through the stale-checkout discriminator's restore-and-record arm at the next classification site, whose landing-deleted-path clause restores from the base tip and thereby materializes the removal (basis: the script's ff gating read on disk and its module docstring, which scopes the merge to a detached checkout genuinely behind the post-landing tip; the Worktree-first standard's discriminator text, which covers a landing-deleted path carrying only pre-landing bytes).
- Within the recorded landing's window, staleness classification already walks the full deletion-relevant history: the ancestor-blob arm matches "the pre-landing tip's blob or any older ancestor" over `git log --format=%H -- <path>` (basis: the script's classification docstring, verified on disk).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the quiescent-point deletion-range residual is adjudicated as covered by composed mechanisms (the ff-only sweep at any later reconcile, the peer's untracked-orphan landing, the full-history ancestor walk inside the window), so the owning document records the scope boundary in one sentence and no new arm is wired (simplicity force: the complexity never cited a witness).

Example of the composed coverage: a path deleted on main three landings ago, still present as a clean tracked copy in a detached worktree behind the post tip, disappears when that worktree next reconciles, because the ff-only merge from its stale tip to the new post tip applies all three landings' tree changes; the same stale copy in a base-branch checkout (the primary included) disappears at the next classification site, where the stale-checkout discriminator's ancestor-blob match restores from the base tip and materializes the removal; an untracked copy of a path the recorded landing deleted is removed by the classify-deleted REMOVE arm from mechanism landing `5dc82ca5`; a modified tracked copy inside the current landing's window is classified by the full-history ancestor walk. The one sub-class no composed mechanism reaches is the untracked orphan of a path deleted in an older range: neither the REMOVE arm (which classifies only the recorded landing's changed-path window) nor the discriminator (which addresses tracked files) touches it, and this adjudication records it as the accepted residual. No witnessed incident shows a deletion decision any of these mechanisms would have missed.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the adjudication sentence states the three composed mechanisms accurately against the script's actual behavior (verified by reading the docstring and the owning block, not by trusting this plan).
- Traceability: the origin item path appears in the owning document beside the adjudication, so a future reader re-derives the full record trail instead of inheriting the claim.
- Restraint: no script, gate, or registry change rides the landing; the changed-file set is the owning document and this plan's own bytes.

**Done when:**
- `agents/skills/execute-plan/SKILL.md` carries the adjudication scope sentence exactly once, anchored after the "Every restore is per path and discriminator-gated" sentence in the Post-landing reconciliation implementation block.
- `grep -c "quiescent" agents/skills/execute-plan/SKILL.md` returns exactly 1.
- The public hygiene scan and the em-dash added-lines gate both exit 0 on the changed bytes.

**Ship when:**
- Nothing beyond Done when: the plan has no deployed, cross-team, or human-owned surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` *(modified; one sentence in the Post-landing reconciliation implementation block)*

**Tests:**
- None *(no test surface changes; the plan adds no code)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/reconcile_post_landing.py` and every other script; reason: the plan's contract is the adjudication, and wiring the arm is the branch the evidence declines.
- `scripts/machinery_registry.json` and the machinery consult surfaces; reason: no machinery is added, removed, or re-pointed.
- The origin item file `docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md`; reason: the executor's lifecycle (covered flip at landing) owns it, not a plan task.

## Validation Commands

```bash
# Executor note: run from the repository root. The count and the once-only
# anchors are the contracts for commands 1-4; exit status is the contract
# for commands 5-6.
grep -c "quiescent" agents/skills/execute-plan/SKILL.md
grep -c "Every restore is per path and discriminator-gated" agents/skills/execute-plan/SKILL.md
grep -c "docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md" agents/skills/execute-plan/SKILL.md
grep -c "5dc82ca5" agents/skills/execute-plan/SKILL.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base HEAD
```

### Task 1: Record the adjudication scope sentence in the owning document

Files:
- `agents/skills/execute-plan/SKILL.md` *(modified)*

Evidence:
- `grep -c "quiescent" agents/skills/execute-plan/SKILL.md`; covers "the adjudication is greppable in the owning document and appears exactly once"

- [ ] In the Post-landing reconciliation implementation block of `agents/skills/execute-plan/SKILL.md`, insert a scope note of one to three sentences immediately after the sentence beginning "Every restore is per path and discriminator-gated" (verify the anchor sentence appears exactly once before writing), stating: the reconciliation's per-path classification covers the recorded landing's pre-tip-to-post-tip window only; a detached checkout behind the post tip receives older-range deletions through the restore phase's ff-only merge (clean copies; a refusal degrades to the ff-refused block row); a base-branch checkout receives older-range deletions through the stale-checkout discriminator's restore-and-record arm at the next classification site; untracked copies of paths the recorded landing deleted are removed by the classify-deleted REMOVE arm from mechanism landing `5dc82ca5` (the worktree-closeout plan landing `37beab52` owns the plan document the prior origin's covered flip names), while an untracked orphan of a path deleted in an older range is the one sub-class no composed mechanism reaches and is recorded as the accepted residual of this adjudication; within-window staleness walks the full ancestor history; the adjudication records here rather than beside the maintenance skill's machinery regrowth guard consult because that consult owns registration and witness liveness while the deletion-range behavior the residual names is owned by this block; adjudicated 2026-10-02 with no witnessed older-range failure, origin `docs/history/backlog/2026-10-02-machinery-deletion-quiescent-range-sweep.md` [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the four Validation Command counts (quiescent once, restore anchor once, origin path once, mechanism-landing pin 5dc82ca5 once) before committing [class: REPOSITORY_TEST]
- [ ] Run the public hygiene scan and the em-dash added-lines gate over the changed bytes; both must exit 0 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: adjudicate quiescent-point deletion-range residual as composed-coverage in the reconcile owning block` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `git show --name-only --format=%h HEAD`; expect the commit covers exactly `agents/skills/execute-plan/SKILL.md` [class: REPOSITORY_TEST]
