# Plan: Align the done direct-landing advisory and placement pins

Backlog origin: docs/history/backlog/2026-10-17-done-skill-text-economy.md
Driving force: simplicity
Authoring claim: docs/tmp/authoring-claims/2026-10-17-done-skill-text-economy.md (session 01a15484-176a-70a1-814d-785fd68e1975)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Immediate-commit rule: the execute-plan Worktree-first standard's primary-placement rule requiring each change to be committed immediately after it is made.
- Direct-landing advisory: the done skill's warning-only report for a primary-checkout landing whose cumulative change exceeds the direct-commit class bounds.
- Placement pins: the existing warning-only fixed-string checks in the placement section of the maintenance pins script.

## Why

The backlog prompt records two economy issues, but current `main` has already single-homed the immediate-commit rule: execute-plan owns its full wording and the done advisory refers to it by name. The done advisory still carries its incident explanation after the measurement clause, and its placement pins still expect a removed duplicate span plus a less direct advisory span.

## Gist & Examples

TLDR: trim the done advisory and retarget its two placement pins to the surviving wording, reducing duplicate operative text and preserving useful drift detection (driving force: simplicity).

**Before:** the warning-only advisory ends with a historical incident parenthetical; one placement pin searches the done skill for the removed `committed right after the change` wording, and another pins only a threshold fragment rather than the measurement clause.

**After:** the advisory ends at its measurement clause; the two existing placement pins cover the done skill's by-name reference to the immediate-commit rule and the advisory's cumulative-diff measurement clause.

**Edge cases:** preserve the warning-only exit behavior, the direct-commit class bounds, and the advisory's distinction between direct primary-checkout landings and worktree transfer-out landings.

## Outcome

The done skill carries only the operative direct-landing measurement guidance, and its two placement pins guard the live wording without restoring duplicate rule text.

- The full immediate-commit rule remains owned by the execute-plan Worktree-first standard.
- The done skill's advisory retains its existing warning-only scope and measurement behavior.
- The placement pins continue to report drift if either retained span changes.

Gate delta: no new refusal class, hard gate, fence, protocol layer, schema field, or pausing condition; the existing warning-only placement-pin rows are retargeted to retained text; no gate is removed or promoted.

## Assumptions

- Current `main` already satisfies the single-home outcome: execute-plan states the full immediate-commit rule and the done advisory uses the by-name phrase `immediate-commit rule`; basis: the current skill files.
- The only remaining scope from the origin is removal of the incident parenthetical and same-change placement-pin retargeting; basis: the current done advisory and the two placement rows.
- The placement-pin family remains warning-only; basis: its existing `placement_pin` helper and summary contract.

Decision points requiring a grill: none remain.

## Standing constraints

- Do not change the immediate-commit rule's owner or meaning.
- Do not change the direct-commit class thresholds, the warning-only posture, or the exception for worktree transfer-out landings.
- Do not add a new pin family, validator, or acceptance mechanism.

## Evaluation Criteria

**Done when:** the done advisory ends at the measurement clause; both placement rows pin retained done-skill text; the existing placement-pin suite reports all placement pins holding.

**Ship when:** none; this is a repository-local documentation and pin update.

## Review Scope

**Must fix:**
- `agents/skills/done/SKILL.md` - the live warning-only advisory and its redundant tail.
- `scripts/check_maintenance_pins.sh` - the two placement-pin operands that target the removed or overly broad spans.

**Out of scope:**
- `agents/skills/execute-plan/SKILL.md` - its canonical rule is already correct and remains unchanged.
- Other placement-pin rows and the suite's warning-only exit contract.

## Validation Commands

- Run the existing placement-pin suite and confirm both retargeted rows hold while its warning-only exit contract remains unchanged.
- Run plan readiness on the final plan and record any non-blocking pre-round advisory.

### Task 1: Trim the done advisory and retarget its two placement pins

Context surface: this task, `## Outcome`, and `## Standing constraints`.

Files:
- `agents/skills/done/SKILL.md` *(edited)*
- `scripts/check_maintenance_pins.sh` *(edited)*

Primary class anchors:
- `Direct-landing advisory` in `agents/skills/done/SKILL.md`
- `placement_pin` in `scripts/check_maintenance_pins.sh`

- [x] Remove the historical incident parenthetical so the advisory ends after the cumulative-diff measurement clause; preserve its warning-only label, threshold conditions, and worktree-transfer exception. [class: IMPLEMENTATION_REQUIRED]
- [x] Retarget the first placement row to the done skill's retained by-name reference to the `immediate-commit rule`; do not restore the removed full rule wording. [class: IMPLEMENTATION_REQUIRED]
- [x] Retarget the second placement row to a distinctive span within the advisory's cumulative-diff measurement clause, so drift in that behavior remains visible. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the existing placement-pin suite and record its result; confirm the two pins hold and the suite remains warning-only. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: trim done advisory and align placement pins` [class: IMPLEMENTATION_REQUIRED]
