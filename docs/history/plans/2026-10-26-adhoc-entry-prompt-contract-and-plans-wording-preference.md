# Plan: Keep ad-hoc prompts bound to their arm and honor plans wording

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-26-exec-entry-prompt-shadows-adhoc-arm-machinery.md`
Driving force: simplicity + code-quality
Execution budget: 1.0h total, largest task 0.5h
Authoring claim: `docs/tmp/authoring-claims/2026-10-26-exec-entry-prompt-shadows-adhoc-arm-machinery.md` (session `01a17a2c-0806-7db2-a8e6-7ed13dc2387b`)

## Terms

- **Ad-hoc backlog arm:** the existing maintenance selection path for ad-hoc backlog items, including its worktree, review, receipt, and landing duties.
- **Prompt entry:** a ready-to-dispatch entry in `docs/history/backlog/EXEC-PROMPTS.md`.
- **Plans segment:** open plans considered by the Exec-mode selection rule before non-plan candidates when the mandate asks to execute `N plan(s)`, matching the origin's witnessed wording.
- **Exec-mode selection rule:** the maintenance rule that orders plans, EXEC-PROMPTS entries, and ad-hoc candidates for exec-mode work.
- **Mode binding:** the maintenance rule that selects the session's author, exec, dual, or survey mode.
- **decision_reason:** the maintenance state-file record that explains the selected candidate and applied order.

## Why
The origin records a landed ad-hoc change whose prompt listed a shorter gate set than the existing Ad-hoc backlog arm, and a plans-worded mandate that selected an EXEC-PROMPTS entry. The plan makes prompt writing inherit the arm from its owning rule and makes the witnessed `exec N plan(s)` mandate form resolve candidate selection in favor of the plans segment.

## Gist & Examples

Title: Keep ad-hoc prompts bound to their arm and honor plans wording
TLDR: Make emitted prompts inherit the Ad-hoc backlog arm and make plans-worded mandates prefer plans, reducing duplicated instructions and selection ambiguity through simplicity and code quality.
Before: An ad-hoc prompt can carry a shorter list than the arm, and a plans-worded mandate can select a non-plan candidate by merged urgency.
After: Prompt emission points to the existing arm without restating its gates, and the witnessed `exec N plan(s)` wording selects from the plans segment first.
Edge cases: Keep the arm's existing duties intact; fall through to non-plan candidates only when the plans segment has no dispatchable candidate; do not change lane-mode binding or add machinery.

## Outcome
Make the ad-hoc prompt contract and the witnessed `exec N plan(s)` candidate preference explicit in their existing instruction owners.

- New ad-hoc prompt entries cannot shadow the arm by listing a shorter gate set.
- An exec mandate matching `exec N plan(s)` records that the plans segment was preferred and keeps existing ordering within each segment.

Gate delta: no refusal class, hard gate, fence, protocol layer, schema field, lock, validator, ledger, or required ceremony is added or removed; no task adds a new dispatch stop, while plans wording orders the plans segment before non-plan candidates and permits lower segments only when that segment has no dispatchable candidate; the prompt emission rule replaces duplicated gate lists with a pointer to the Ad-hoc backlog arm.

## Assumptions

- The origin row's two scope arms are the complete scope; its retroactive receipt-repair proposal remains excluded.
- Investigate Stage 4 owns prompt emission, while the EXEC-PROMPTS header can point to that owner without restating its rule.
- The Exec-mode selection rule owns candidate ordering; mode binding owns only the session's lane mode.
- Existing prompt-log, review, landing, and maintenance rules remain the sources of their current mechanics.
- The standing authorization applies to the best-supported in-scope choices recorded here; no user decision remains open.

Decision points requiring a grill: none remain; maintenance-selected authorization selects the two in-scope owners from the origin's explicit alternatives.
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Standing constraints

- Preserve the Ad-hoc backlog arm's current worktree, focused review, receipt, and squash-landing duties.
- Keep the prompt inheritance rule single-homed in Investigate Stage 4; the EXEC-PROMPTS header may only point to that owner.
- Keep mandate precedence in the Exec-mode selection rule and retain its existing order inside each candidate segment.
- Do not add a gate, validator, lock, ledger, schema field, review ceremony, or retroactive landing repair.

## Evaluation Criteria

**Quality dimensions:**
- Contract clarity: prompt writers can identify the one owner of the ad-hoc run duties.
- Selection accuracy: plans wording prefers a dispatchable plans-segment target and records the resolution.
- Scope control: no new machinery or retroactive repair enters the change.

**Done when:**
- Investigate Stage 4 owns the prompt inheritance rule and EXEC-PROMPTS points to it without repeating it.
- The Exec-mode selection rule resolves plans wording to the plans segment first and records that choice.
- The origin is closed under the repository's covered-row rule, and the plan's validation commands pass or report the known unrelated pins failure.

**Ship when:** No external, cross-team, or human-owned release condition.

## Review Scope

**Explicit must-fix:** any change that permits a Prompt to shorten the Ad-hoc arm, changes another candidate-order rule, or adds machinery outside the origin.

**Documentation:**
- `agents/skills/investigate/SKILL.md` (Task 1)
- `docs/history/backlog/EXEC-PROMPTS.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `docs/history/backlog/2026-10-26-exec-entry-prompt-shadows-adhoc-arm-machinery.md` (Task 2)

**Out of scope; reject unless plan-related:** repair of the witnessed `cb0e439c` landing, redesign of the Ad-hoc backlog arm, changes to mode binding, new mechanical prompt validation, and unrelated prompt-log entries.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-26-adhoc-entry-prompt-contract-and-plans-wording-preference.md
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-26-adhoc-entry-prompt-contract-and-plans-wording-preference.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-26-adhoc-entry-prompt-contract-and-plans-wording-preference.md
```

### Task 1: Bind emitted prompts to the existing Ad-hoc backlog arm

Context surface: Terms, Standing constraints, the origin's witnessed prompt shadowing, the Ad-hoc backlog arm in `agents/skills/maintenance/decisions.md`, Investigate Stage 4, and the EXEC-PROMPTS header.

Primary class anchors:
- `Stage 4: log entry emission` in `agents/skills/investigate/SKILL.md`
- `Prompt log header` in `docs/history/backlog/EXEC-PROMPTS.md`

Files:
- `agents/skills/investigate/SKILL.md`
- `docs/history/backlog/EXEC-PROMPTS.md`

Checklist:
- [ ] Replace Stage 4's existing entry-carries line with concise wording that requires the prompt to inherit the Ad-hoc backlog arm by reference and forbids restating or shortening its duties. [class: IMPLEMENTATION_REQUIRED]
- [ ] Replace the EXEC-PROMPTS header boilerplate with a shorter pointer to Investigate Stage 4 as the prompt-emission owner. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the maintenance pins suite, the em-dash added-lines gate, and the public hygiene scan. [class: REPOSITORY_TEST]

Acceptance criteria:
- Each emitted ad-hoc prompt directs its session to the Ad-hoc backlog arm by reference.
- Prompt content cannot narrow that arm's worktree, review, receipt, or landing duties.
- The EXEC-PROMPTS header identifies Investigate Stage 4 as the prompt-emission rule owner.

### Task 2: Prefer plans for plans-worded exec mandates

Context surface: Terms, Standing constraints, the origin's observed plans-worded mandate, the Exec-mode selection rule, and the Mode binding rule that distinguishes mode selection from candidate ordering.

Primary class anchors:
- `Exec-mode selection rule` in `agents/skills/maintenance/decisions.md`

Files:
- `agents/skills/maintenance/decisions.md`
- `docs/history/backlog/2026-10-26-exec-entry-prompt-shadows-adhoc-arm-machinery.md` (Task 2)

Checklist:
- [ ] For an exec mandate matching `exec N plan(s)`, consider dispatchable plans before EXEC-PROMPTS entries and ad-hoc items; a higher-urgency non-plan candidate does not take precedence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Fall through to non-plan segments only when no dispatchable candidate remains in the plans segment; for example, with only a ready EXEC-PROMPTS entry available, select it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Record the plans-segment preference in `decision_reason` without changing mode binding or in-segment ordering; an unqualified exec mandate keeps the existing merged-urgency order. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the maintenance pins suite, the em-dash added-lines gate, and the public hygiene scan. [class: REPOSITORY_TEST]
- [ ] After both contracts land, mark the origin covered by this plan and apply the plans skill completion disposition when archiving it. [class: IMPLEMENTATION_REQUIRED]

Acceptance criteria:
- An `exec N plan(s)` mandate selects a dispatchable plans target ahead of a higher-urgency non-plan candidate and falls through only when the plans segment has no dispatchable target.
- The recorded decision explains the `exec N plan(s)` segment preference; an unqualified mandate retains existing merged-urgency ordering.
- No new machinery or task execution is added.
