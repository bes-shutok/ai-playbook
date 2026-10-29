# Plan: Align light-boundary guidance and remove deferred prose duplication

Backlog origin: docs/history/backlog/2026-10-19-light-boundary-review-followups.md
Driving force: maintainability + consistency
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-light-boundary-stale-setup-directives-and-residuals-p976f552a-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-19-light-boundary-review-followups.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)

## Terms

- Light boundary: the intermediate task and review boundary that uses a parent-owned plain commit, learn capture, and record mirror.
- Final closeout: the single full done sequence at the end of a run.
- Preservation pin: a validation check that ensures required final-closeout duties remain present.
- Routed residual: a review finding retained in a separate open backlog item when its source artifact is no longer legally editable.

## Why

The repository's first-action instruction still sends worktree runs through done setup before editing, while the landed workflow starts those runs with Phase 0 setup and reserves done for final closeout. A receiving-review consumer also names a removed commit class, and several deferred wording shrinks remain safe only when their current validation pins stay intact.

## Gist & Examples

TLDR: align the stale worktree setup guidance and receiving-review wording, then remove six redundant passages without weakening their pins, for maintainability.

Before: AGENTS.md directs done setup as the first worktree action, lesson 81 describes that old trigger, receiving-review says captured files ride the task's done commit, and six deferred repetitions remain in the light-boundary skills.
After: worktree runs begin with their own Phase 0 setup and closeout-baseline capture, done setup occurs at final closeout, the consumer names the task boundary commit, and pin-safe wording removes the six repetitions.

## Outcome

The written guidance agrees with the landed light-boundary sequence and its remaining prose is shorter without losing a required closeout duty.

- Worktree setup guidance starts with Phase 0 and closeout-baseline capture; done runs once at final closeout.
- The receiving-review consumer names the task boundary commit.
- Six deferred wording shrinks land with the existing pins passing.
- Archived-plan validation residuals remain intact in a separate open follow-up record.

Gate delta: net removal of stale prose only; no refusal, gate, validator, lock, schema, or protocol is added; existing checks remain.

## Scope boundaries

- IN: correct the stale first-action wording in AGENTS.md and lesson 81; correct receiving-review Step 1.2b; apply the six listed pin-safe shrinks across the five light-boundary skills; preserve the accepted plan-validation and later-round residues in their separately owned follow-up record.
- OUT: change intermediate or final done behavior; edit the archived source plan's checklist or rationale; add gates or machinery.

Success criterion: the changed guidance matches the final-closeout-only cadence and all existing maintenance pins pass after the six prose shrinks.

Key invariants: retain the single final done closeout, parent-owned intermediate light boundary, and all existing validation pins. Preserve the distinct Step 1.8 capture/commit failure route and Step 1.9 capture/investigate-invocation failure route as nonblocking manual follow-up; consolidate only the shared session-log durability wording.

## Assumptions

- assume archived plan checklist and rationale bytes stay unchanged; basis: plans skill Plan Lifecycle allows only disposition and evidenced backfill edits after archive.
- assume the three plan-scoped validation findings, the unfenced failure-semantics item, and four later-round residues are routed to docs/history/backlog/2026-10-29-done-final-only-plan-validation-residuals.md; this row was authored and committed as a separate record in this authoring run and lands with the plan, remaining open for its own follow-up plan; basis: the archived source plan cannot be edited at this boundary.
- assume lesson 81 remains as historical evidence with a clear supersession note; basis: the origin asks for a note, not erasure of the witnessed rule.
Decision points requiring a grill: none remain.

Scope extensions (grilled): omit-extension (maintenance-selected arm).

Sources inspected: source plan Terms, Why, Gate delta, Outcome, and Validation Commands; origin backlog and frozen PLAN-PROMPTS entry; both cited review records; live AGENTS.md, lesson 81, execute-plan, and receiving-review consumers; plans Plan Lifecycle; git history for the stale directive.

## Standing constraints

- Keep the existing final closeout and intermediate boundary behavior intact.
- Do not change prose outside the named spans; the maintenance pin suite is the boundary for the six shrinks.

## Evaluation Criteria

- correctness: each changed instruction states the existing workflow accurately.
- maintainability: six duplicate passages are removed without weakening their owning pins.
- history: accepted archived-plan findings have a durable follow-up path and the archived source remains unchanged.

Done when:
- AGENTS.md and lesson 81 state the current setup order, receiving-review names the task boundary commit, all six shrinks are applied, the routed residual record exists, and the maintenance pins pass.
- the em-dash and public-hygiene scans pass over the changed set.

Ship when:
- none.

## Review Scope

Explicit must-fix: stale cadence, commit-target, pin safety, archived-plan boundary, and backlog routing findings.

Production code:
- none.

Documentation and skills:
- AGENTS.md (Agent-Specific Runtime Safety bullet)
- docs/maintenance/development_lessons.md (lesson 81 only)
- agents/skills/receiving-review/SKILL.md (Step 1.2b only)
- agents/skills/execute-plan/SKILL.md (the six review-identified shrink spans only)
- agents/skills/learn/step-1-extract.md (the two Step 1.9/1.8 Failure semantics paragraphs only; all other spans are frozen)
- agents/skills/review-loop/SKILL.md (the copied round-row leg list only)
- agents/skills/done/SKILL.md (the Step 1 and Integration Points duplicate clause only)
- agents/skills/investigate/SKILL.md (the third placement-universality statement only)
- docs/history/backlog/2026-10-29-done-final-only-plan-validation-residuals.md (durable routed residuals)
- docs/history/plans/completed/2026-10-18-done-final-only-learn-intermediate.md (read-only; archived bytes frozen)

## Validation Commands

- Run `bash scripts/check_maintenance_pins.sh`; require exit 0 and its passing outcome.
- Run `bash scripts/check-no-em-dash.sh added-lines --base origin/main -- AGENTS.md docs/maintenance/development_lessons.md agents/skills/receiving-review/SKILL.md agents/skills/execute-plan agents/skills/learn agents/skills/review-loop agents/skills/done agents/skills/investigate docs/history/backlog/2026-10-29-done-final-only-plan-validation-residuals.md`; require a passing outcome.
- Run the public-hygiene scan resolved from the user facts for the changed set; require exit 0.
- Confirm the stale instruction is absent from AGENTS.md, lesson 81 describes it as superseded by the current Phase 0 and final-closeout order, and receiving-review no longer names the task's done commit.
- Confirm the six review-identified passages are removed or tightened only at their cited spans, and no unrelated prose in the frozen files changed.

## Tasks

### Task 1: Align first-action and consumer guidance

Context surface: Terms, this task, and Standing constraints.

Files:
- `AGENTS.md`
- `docs/maintenance/development_lessons.md`
- `agents/skills/receiving-review/SKILL.md`

Acceptance criteria:
- [ ] Replace the stale AGENTS.md first-action sentence with the worktree Phase 0 and baseline order, reserving done setup for final closeout. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a supersession note to lesson 81 while preserving its witnessed incident and chronology. [class: IMPLEMENTATION_REQUIRED]
- [ ] Change only receiving-review Step 1.2b's commit target from the task's done commit to the task boundary commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-read execute-plan's Phase 0 and final-closeout rules; verify the edits preserve the existing order. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: align light-boundary setup guidance and review consumer` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Apply the six pin-safe wording shrinks

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/learn/step-1-extract.md` (Failure semantics paragraphs only; all other spans are frozen)
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/investigate/SKILL.md`

Acceptance criteria:
- [ ] Remove the duplicate Hard Gate 25 precondition and Step 1.4 residual row-reference sentence at their review-identified spans. [class: IMPLEMENTATION_REQUIRED]
- [ ] Remove the third placement-universality statement and the done Step 1 versus Integration Points twin clause. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve the distinct Step 1.8 capture/commit failure route and Step 1.9 capture/investigate-invocation failure route as nonblocking manual follow-up; consolidate only their repeated session-log durability sentence across the cited learn blocks. Remove the review-loop copied round-row leg list. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the maintenance pin suite after the edits and retain all currently pinned literals and counts; verify both failure-specific routes remain present and share one durability statement. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: trim pin-safe light-boundary prose` [class: IMPLEMENTATION_REQUIRED]


