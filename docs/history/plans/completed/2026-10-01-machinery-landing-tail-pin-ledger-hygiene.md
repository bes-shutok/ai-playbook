# Machinery landing-tail, pin, and ledger hygiene

Backlog origins (scope of record): `docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md`, `docs/history/backlog/2026-09-28-execute-plan-repoint-missing-revisions-ledger-entry.md`, `docs/history/backlog/2026-09-28-landing-machinery-on-main-shorthand.md`, `docs/history/backlog/2026-09-28-landing-tail-parenthetical-precedence-and-pin.md`, `docs/history/backlog/2026-09-28-maintenance-pins-cherry-pick-comment-home.md`, `docs/history/backlog/2026-09-28-prompt-templates-deviation-entry-leadin-and-source-record.md`

Classification: [class: fix-class] payload-and-pin machinery hygiene with one behavior-bearing arm (the checkout-flow guard); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Landing tail**: the execution blueprint's final-merge paragraph in `agents/skills/maintenance/prompt-templates.md` (the `Finally squash merge to the repository's default branch` block), the payload's landing critical section.
- **Creation base**: the per-project base branch the run worktree was created from, resolved by the canonical Base-branch resolution rule; in a default-branch-integration project it equals the landing target, in a checkout-flow project it can differ.
- **Re-key in the same change**: a prose edit to a pinned span lands its pin's new literal in the same commit, per the pins suite's freeze-literal convention.

## Coverage dispositions (verified on disk 2026-10-01)

- Two of the frozen entry's eight origins are already done and are cited here as provenance, deliberately NOT in the Backlog origins line: the consolidation-comment rewrite (executed+landed 6251d8e2 via docs/history/plans/completed/2026-09-30-pins-consolidation-comment-narrowed-claim.md) and the S15 keying-basis pin restoration (executed+landed c6cbf608 by the done-lock-keying-basis-pin plan; its exec lane landed while this plan was being authored). This plan never re-edits their surfaces beyond what its own arms require.
- The tail parenthetical EXISTS (the `Finally squash merge ...` line's parenthetical states the default-branch-integration equality) but carries no checkout-flow carve-out and no pin: that is the survivor pair Task 1 and Task 2 fix.

## Tasks

### Task 1: the checkout-flow landing mismatch guard

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `grep -c 'creation base' agents/skills/maintenance/prompt-templates.md` returns at least 2
- `grep -q 'fails the landing closed' agents/skills/maintenance/prompt-templates.md`

- [ ] Run → expect RED: the first Evidence grep returns 0 and the second misses [class: REPOSITORY_TEST]
- [ ] In the execution blueprint's landing critical section, directly after the sentence holding the acquired MERGE_LOCK exports across the whole landing and before the PRE_TIP capture, insert the guard: before the squash, compare the run worktree's creation base (the base branch the worktree was created from, per the canonical Base-branch resolution rule) with the landing target (the repository's default branch); when they name different branches - a checkout-flow project's divergence - the mismatch fails the landing closed before any ref move: write the deferred-landing record and note per the deferred-landing record duty naming BOTH refs (the creation base and the default branch), keep the branch and worktree, and end the landing; never sweep operator-branch commits onto the default branch [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `payload: checkout-flow landing mismatch guard fails closed` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the tail parenthetical's carve-out framing and its exactly-once pin

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` exits 0
- `grep -c "equals the resolved base in a default-branch-integration project" agents/skills/maintenance/prompt-templates.md` returns 1

- [ ] Run → expect RED: a pins-suite grep for the new parenthetical fragment misses (no pin covers the parenthetical today; the lead-in prefix pin survives any parenthetical rewrite) [class: REPOSITORY_TEST]
- [ ] Extend the landing tail's parenthetical with the carve-out framing mirroring the canonical sentence: after the default-branch-integration equality clause, add that a checkout-flow project's resolved base differs from this landing target and the mismatch guard (the Task 1 guard in the landing critical section) fails the landing closed naming both refs [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a wrap-tolerant exactly-once pin (the S16 normalized-count idiom) on the parenthetical's distinctive fragment (`equals the resolved base in a default-branch-integration project`), scoped to `$P`, so the reconciling clause cannot silently drift or invert with the suite green [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [ ] Commit: `pins: tail parenthetical gains the checkout-flow carve-out and its exactly-once pin` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the on-main shorthand rewords to the default-branch form

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `grep -c "verify the landed commit on main" agents/skills/maintenance/prompt-templates.md` returns 0
- `grep -c "its own landing is not verified on main" agents/skills/maintenance/prompt-templates.md` returns 0
- `bash scripts/check_maintenance_pins.sh` exits 0

- [ ] Run → expect RED: both old-literal counts return 1 today (lines 241 and 285's successor conjunct; both literals are pin-frozen at scripts/check_maintenance_pins.sh 1463-1464) [class: REPOSITORY_TEST]
- [ ] Reword both shorthand sites to the default-branch form (`verify the landed commit on the repository's default branch`; `its own landing is not verified on the default branch`) and RE-KEY the two pins that freeze the old literals (pins 1463-1464, `blueprint landed-commit verification` and `successor own-landing conjunct`) to the new literals in the same change. The gate is scoped to the two exact old literals: the file's third and fourth `on main` substrings sit inside the 2026-09-23 historical deviation entry (line 21), which the origin does not demand touched and whose paraphrase precedent stays [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: all three Evidence commands (the two count lines print 0 and exit 1; the printed counts are the assertions) [class: REPOSITORY_TEST]
- [ ] Commit: `payload: on-main shorthand reworded to the default-branch form, pins re-keyed` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the cherry-pick pin's operator comment names the span's home

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` exits 0 (a comment-only edit; no pin keys on comment text)
- `grep -c "linked-worktree bootstrap" scripts/check_maintenance_pins.sh` returns 0

- [ ] Run → expect RED: `grep -c "linked-worktree bootstrap" scripts/check_maintenance_pins.sh` returns 1 today (line 1259's operator comment above the unlanded-plan cherry-pick pin) [class: REPOSITORY_TEST]
- [ ] Reword that operator comment to name the span's actual home (the canonical Worktree-first standard's Transfer-in implementation in agents/skills/execute-plan/SKILL.md), leaving the pinned grep literal untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]
- [ ] Commit: `pins: cherry-pick pin comment names the transfer-in implementation home` [class: IMPLEMENTATION_REQUIRED]

### Task 5: the deviation list gains the r5 re-pin entry and a living source of record

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `grep -c "2026-09-13-maintenance-scheduler-skill" agents/skills/maintenance/prompt-templates.md` returns 2 (the line-3 source of record and the line-27 fill-in annotation, both re-pointed)
- `grep -c "docs/history/backlog/completed/2026-09-13-maintenance-scheduler-skill.md" agents/skills/maintenance/prompt-templates.md` returns 0 (the dead backlog path gone)

- [ ] Run → expect RED: the second Evidence grep returns 1 today (the dead backlog path at the line-3 source-of-record sentence only; the line-27 fill-in annotation ALREADY cites the surviving archived plan and needs no edit) [class: REPOSITORY_TEST]
- [ ] Add the deviation-list entry for the r5 final-merge lead-in re-pin (paraphrase-only wording so the body-scoped count pins hold), and re-point the line-3 source-of-record sentence to the surviving archived plan `docs/history/plans/completed/2026-09-13-maintenance-scheduler-skill.md` (section "Current manual baseline", verified present; the stem count reaches 2 with line 27's existing citation) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [ ] Commit: `payload: deviation list registers the r5 re-pin and re-points to the archived plan` [class: IMPLEMENTATION_REQUIRED]

### Task 6: the Revisions ledger gains the supersession re-point entry

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -c "worktree-first consolidation" agents/skills/maintenance/SKILL.md` returns at least 1 inside the Revisions ledger region

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] Append a dated `## Revisions` ledger entry recording the worktree-first consolidation's re-point of the supersession-chain paragraph to the Worktree-first standard section (2026-09-28, owning plan docs/history/plans/completed/2026-09-28-worktree-first-standard-only-mode.md, the re-aimed execute-plan Phase 0 sentence set), so the chain's edit history is auditable from the ledger alone [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [ ] Commit: `skills: revisions ledger records the supersession re-point` [class: IMPLEMENTATION_REQUIRED]

### Task 7: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the guard, the carve-out pin, the re-keyed shorthand pins, the comment home, the deviation re-point, and the ledger entry

- [ ] Run the full Validation Commands block from the repository root; every line exits 0, except the four count lines that pass by printing 0 per the floor-line conventions (the two re-keyed old-literal counts, the retired bootstrap comment count, and the dead backlog path count) [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
grep -c "creation base" agents/skills/maintenance/prompt-templates.md
grep -q "fails the landing closed" agents/skills/maintenance/prompt-templates.md
grep -c "equals the resolved base in a default-branch-integration project" agents/skills/maintenance/prompt-templates.md
grep -c "verify the landed commit on main" agents/skills/maintenance/prompt-templates.md
grep -c "its own landing is not verified on main" agents/skills/maintenance/prompt-templates.md
grep -c "linked-worktree bootstrap" scripts/check_maintenance_pins.sh
grep -c "docs/history/backlog/completed/2026-09-13-maintenance-scheduler-skill.md" agents/skills/maintenance/prompt-templates.md
grep -c "worktree-first consolidation" agents/skills/maintenance/SKILL.md
```

Floor-line conventions: the `creation base` count line prints at least 2 after Task 1 (presence floor, exit 0); the two re-keyed old-literal count lines, the `linked-worktree bootstrap` count line, and the dead-path count line each print 0 after their tasks and pass by printing 0 (grep -c exits 1 at a zero count; the printed count is the assertion); every other line is an exit-0 presence gate.

## Assumptions

- The frozen entry's arms 6 (consolidation comment) and 8 (S15 keying-basis pin) are covered by landed executions (6251d8e2, c6cbf608) and are cited as provenance, not re-implemented; this plan's pins edits never touch the S16-idiom keying-basis pin the c6cbf608 execution landed except by reading it as the idiom precedent for Task 2's new pin.
- The checkout-flow guard is payload prose (the blueprint's own critical-section instruction), not a script gate: the executor child enforces it by reading, matching the payload's other fail-closed arms; no Python behavior changes anywhere in this plan.
- The Task 3 re-key keeps the two pins' names and comment provenance, changing only the grepped literals to the reworded spans, per the suite's freeze-literal convention.
- The deviation entry is paraphrase-only so the body-scoped count pins over the blueprint bodies hold.
- Pins keyed on any reworded span are re-keyed in the same change; every comment or ledger edit verifies by a green pins-suite run.

Decision points requiring a grill: Task 1 guard shape (payload-prose fail-closed arm with the deferred-landing record naming both refs, never a log-and-continue); Task 1 insertion point (after the lock hold, before the PRE_TIP capture, so a mismatch never reaches a ref move); Task 2 carve-out framing (mirror the canonical sentence, defer to the Task 1 guard); Task 3 re-key discipline (pin names and comments stable, literals only); Task 5 re-point target (the surviving archived plan, verified present, over declaring the deviation list the record); Task 6 ledger form (dated entry naming the owning plan, matching the ledger's existing entry shape).

## Review Scope

- `docs/history/plans/2026-10-01-machinery-landing-tail-pin-ledger-hygiene.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-09-28-checkout-flow-landing-mismatch-guard.md`
- `docs/history/backlog/2026-09-28-execute-plan-repoint-missing-revisions-ledger-entry.md`
- `docs/history/backlog/2026-09-28-landing-machinery-on-main-shorthand.md`
- `docs/history/backlog/2026-09-28-landing-tail-parenthetical-precedence-and-pin.md`
- `docs/history/backlog/2026-09-28-maintenance-pins-cherry-pick-comment-home.md`
- `docs/history/backlog/2026-09-28-prompt-templates-deviation-entry-leadin-and-source-record.md`
