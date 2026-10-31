# Plan: maintenance stop-boundary continuation
Backlog origin: docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-10-27-plan-review-maintenance-stop-boundary-continuation-p54cc877b-r*.md
Execution budget: 1.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms
- **D-6**: The operator directive requiring an active maintenance turn to continue while a lane holds dispatchable work and quota permits.
- **Dispatchable work**: Work selected by the maintenance rules that is not blocked by a guard or external dependency.

## Why
The maintenance payload and child templates still direct the session to end after its report even when D-6 requires it to continue an available lane. This boundary can leave ready work idle until the next scheduled turn.

## Gist & Examples
TLDR: Continue eligible in-session maintenance work through the report boundary, following D-6, to reduce idle time.

Before: A child completes one lane, reports, and ends even when another lane has dispatchable work and quota remains healthy.
After: The turn continues the eligible lane under D-6, then reports and ends when the stop conditions apply.

## Outcome
Maintenance turns continue available work until D-6 permits the stop boundary.
- Authoring, execution, and unblock child instructions express the same D-6 stop conditions.
- The maintenance decision module and in-session authoring notes point to the same continuation rule.
- Quota-low and no-dispatchable-work boundaries retain their documented behavior.

Gate delta: none; this plan aligns existing instructions with D-6 and adds no gate, refusal class, fence, protocol layer, schema field, or dispatch pause.

## Assumptions
- assume the split child templates are the operative payload homes; basis: the authoring and execution template files contain the current FINAL STEP text and the prompt-templates file no longer contains those paragraphs.
- assume D-6 is the source of truth for continuation and quota stop conditions; basis: the open backlog row cites D-6 and the maintenance directive is its verbatim source.
Decision points requiring a grill: none remain.

## Evaluation Criteria
- The final-stop instructions consistently follow D-6 for authoring and execution lanes.
- The maintenance router and authoring primitive do not contradict the child templates.
- Existing no-work and quota-stop behavior remains clear, with no new blocking gate.

**Quality dimensions:**
- Correctness: each changed instruction matches D-6 and the live lane-selection rules.
- Simplicity: the continuation rule has one authoritative home and other surfaces reference it.

**Done when:** The applicable instruction files agree on when a maintenance turn continues and when it ends, and the full plan-readiness gate passes.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/maintenance/template-unblock.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `agents/skills/maintenance/zcode.md` (Task 3)

**Tests:**
- none

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Scheduler state schema or quota machinery; no state change is required to align the boundary text.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-maintenance-stop-boundary-continuation.md
```

### Task 1: Align child stop boundaries with D-6

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/template-unblock.md`

Primary class anchors:
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`
- `FINAL STEP` in `agents/skills/maintenance/template-execution.md`
- `FINAL STEP` in `agents/skills/maintenance/template-unblock.md`

- [x] Given another lane has dispatchable work after an authoring, execution, or unblock child report and the primary quota probe is below its pause threshold with decision `continue`, expects the turn to continue that lane in-session; given the primary quota is at a pause threshold, expects the turn to record the resume point and stop; given only the weekly-secondary window is paused while primary quota permits continuation, expects the turn to continue. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: compare all three child final-step paragraphs against the D-6 conditions and confirm all three currently contain an unconditional stop. [class: REPOSITORY_TEST]
- [x] Write the smallest text change that applies D-6 and names the directive as the rule source. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: confirm all three child paragraphs express matching continuation and stop conditions without adding a separate rule. [class: REPOSITORY_TEST]
- [x] For each changed operative skill file, remove equivalent operative bytes in the same change; review the per-file diff for growth without deletion. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: align maintenance child stop boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Align the operative maintenance continuation condition

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `continue-loop condition` in `agents/skills/maintenance/decisions.md`

- [x] Given no execution or authoring work is dispatchable, expects the turn to report and end; given either lane has dispatchable work and the primary quota probe permits continuation, expects the next lane decision to run. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: compare the current turn-boundary wording with D-6 and identify any unconditional end point. [class: REPOSITORY_TEST]
- [x] Write the smallest matching boundary update, leaving the router's lane order intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: verify the turn-boundary step and child instructions agree. [class: REPOSITORY_TEST]
- [x] For each changed operative skill file, remove equivalent operative bytes in the same change; review the per-file diff for growth without deletion. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: align maintenance continuation condition` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Align the in-session authoring carrier note

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `In-session authoring primitive` in `agents/skills/maintenance/zcode.md`

- [x] Given D2 selects an authoring target and the primary quota probe permits the full in-session authoring loop, expects the in-session authoring primitive to run without ending the turn at the preceding lane report. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: inspect the existing primitive note and demonstrate whether its current boundary can conflict with D-6. [class: REPOSITORY_TEST]
- [x] Update the note to reference the same D-6 conditions without changing carrier-selection policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: verify the primitive note, operative decision module, and child templates describe one compatible continuation path. [class: REPOSITORY_TEST]
- [x] For each changed operative skill file, remove equivalent operative bytes in the same change; review the per-file diff for growth without deletion. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: align authoring carrier continuation note` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Covered origin row docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md deleted per the covered-row rule at landing; this archived plan is the durable home of the disposition. Executed 2026-10-31 by the 22:00 WET one-shot exec carrier automation-8b22f46e (pick 2 of 2): three task commits 83308043b, 79ab199ed, abfd2ae10 aligning the three child FINAL STEP paragraphs, the decisions.md continue-loop condition, and the zcode.md in-session authoring primitive note with directive D-6; r6 re-bind round fresh blocking-clean over the ticked plan digest (2 staged fixed in-change, 4 overflow including the growth residual row 2026-10-31-stop-boundary-skill-text-growth-residual.md); full readiness gate pass.
