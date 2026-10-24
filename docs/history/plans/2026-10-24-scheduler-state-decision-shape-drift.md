# Plan: Normalize Scheduler State Decision Fields
Backlog origin: docs/history/backlog/2026-10-09-scheduler-state-decision-shape-drift.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-24-plan-review-scheduler-state-decision-shape-drift-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-scheduler-state-decision-shape-drift.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Per-lane decision maps:** the top-level `decision` and `decision_reason` objects, each keyed by `execution` and `authoring`.
- **Legacy scalar:** a string found where one of those per-lane objects belongs.
- **State notes:** the existing top-level `notes` array used to retain prior scheduler messages.

## Why

The documented scheduler state stores per-lane decision maps, but the live state has stored turn-summary strings in those fields. A later lane update can index a string and fail, while preserving the summary as a valid lane value can misattribute a decision from an earlier turn.

## Gist & Examples

TLDR: Restore per-lane decision maps and preserve legacy summaries safely, for code quality.

Before, `decision` and `decision_reason` may be strings such as a turn summary, although lane decisions read them as objects. After, readers recognize a string as unscoped legacy text, and the next sanctioned write restores both maps while preserving the old text in `notes`.

For example, a scalar `decision` beside a valid `decision_reason` map is handled without lane indexing; the writer records the scalar in `notes` and emits both canonical maps from the current turn's decisions. It does not guess the old summary's lane from stale or conflicting state.

## Outcome

Scheduler state reads and writes keep the decision fields in their documented per-lane shape while retaining legacy summaries.

- A legacy string never causes a lane-key access failure or gets mistaken for a current lane decision.
- A sanctioned write restores both per-lane maps and retains each replaced scalar in `notes`.
- The state schema checker guards the prose and shape contract.

Gate delta: declare the existing `notes` array in the schema-4 example and carry-forward contract; add no refusal path, scheduler gate, fence, review duty, or dispatch pause; add no writer class or schema-version bump.

## Assumptions

- Assume a legacy scalar is an unscoped historical summary; writers rebuild both lane maps from the current turn and preserve the scalar in `notes`, because the current runtime state has a summary beside a differently scoped `last_run` record, so inferring its lane is unsafe; basis: the live state and the backlog's recorded TypeError and propagation witness.

Decision points requiring a grill: maintenance-selected standing authorization selects preserving ambiguous strings in `notes` and rebuilding maps from current turn results; this is simpler and safer than lane inference or a new reader-only compatibility layer; source: live scheduler state and backlog evidence; 2026-10-24; Assumptions and Task 1.

## Standing constraints

- Keep the change within the existing State file section and scheduler-turn writer class. Until the byte-budget gate lands, treat operative-text growth without a deletion as a review-time finding under the existing finding-class documentation; add no separate panel duty.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the schema example keeps both lane maps keyed by exactly `execution` and `authoring`, and legacy strings cannot be indexed as maps.
- Data preservation: each replaced scalar is appended once to `notes`, and pre-existing notes survive targeted edits and Step 6 rewrites.
- Maintainability: one State file contract owns tolerance and repair; no new writer class or runtime helper is introduced.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` passes with checks for the canonical schema and the documented legacy-read and repair contract.
- The next sanctioned scheduler write can rebuild both maps from current-turn decisions without guessing from legacy text.

**Ship when:**
- No external release step; the next maintenance scheduler turn applies the documented repair to live state through its sanctioned write.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `agents/skills/maintenance/state-file.md`

**Tests:**
- `scripts/check_maintenance_pins.sh`

**Plan-related extension:** findings that directly complete the state-file contract or its pin are in scope.

**Out of scope; reject unless plan-related:**
- `.ai-playbook/scheduler-state.json`; the live runtime file is repaired by a later sanctioned scheduler write after the rule lands, not by this plan authoring or execution session.
- Other maintenance schema fields; this plan is limited to `decision`, `decision_reason`, and the existing `notes` array required to preserve their legacy values.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
```

### Task 1: Make legacy decision state readable and self-repairing

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/state-file.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Given either top-level decision field is a string, expect readers to treat it as unscoped legacy text and never index it by lane. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a non-Step-6 scheduler-turn targeted write touches either field, expect that same targeted atomic edit to restore both maps from the current turn's lane decisions and reasons; do not infer lane values from legacy strings. [class: IMPLEMENTATION_REQUIRED]
- [ ] Name this repair as a mode of the existing Scheduler turns writer class; create no additional writer class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given one or both values are legacy strings, expect each original string to be retained once as a timestamped `notes` entry; existing notes remain intact. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the Step 6 whole-document rewrite runs, expect its existing temporary-file atomic replacement to restore both maps from current-turn decisions and reasons, carry `notes`, and retain schema version 4. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the existing maintenance pin to require the `notes` array in the schema example and to fail when the state-file prose omits the legacy tolerance, repair, writer-class, or carry-forward rules. [class: REPOSITORY_TEST]
- [ ] Run the pin checker and expect it to pass for the canonical schema and fail when either map shape or repair contract is removed. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: repair scheduler decision state shape` [class: IMPLEMENTATION_REQUIRED]
