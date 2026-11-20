# Plan: Scope maintenance integrity stops to dependent actions

Backlog origins (scope of record):
- docs/history/backlog/2026-11-15-maintenance-integrity-hold-overblocks-independent-lanes.md
- docs/history/backlog/2026-11-15-maintenance-integrity-stop-strands-successor.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-maintenance-integrity-stop-scope-and-retry-pbd95d644-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Authoring claim: 2026-11-15-maintenance-integrity-hold-overblocks-independent-lanes.md (session 01a1de3a-5a3d-7b51-a0e7-6259c1198bfb)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (8ca0b5a394f1f120c1818f680fadc77819dfb37d)

## Terms

- **Projection mismatch:** two disk-backed representations disagree on a target identity or progress value.
- **Dependent action:** an action whose target, owner, or recovery choice relies on the disputed representation.
- **Independent lane:** a separately selected maintenance lane whose target and guards can be established from fresh disk evidence without relying on the disputed representation.
- **D-17:** the active maintenance directive to continue eligible picks without user turns while normal guards and primary quota permit.
- **D-18:** the active maintenance directive that assigns each loop exit a successor or recorded exemption.
- **Codex reset wake:** the existing scheduled successor after a primary quota pause, anchored to the fresh reset time and carrying the pending target.
- **Bounded retry:** the existing D-18 successor for one blocked stop, with its existing two-consecutive-block operator park.
- **Primary quota wall:** the existing five-hour primary quota pause and Codex reset-anchored wake.

## Why

The current Step 0 integrity clause treats any projection mismatch as a turn-wide ban on mutation. That blocks unrelated work even when its target is independently verifiable, and it can prevent D-18 from recording its required blocked retry. The Codex five-hour wake already exists and does not explain the missed continuation.

## Gist & Examples

TLDR: Narrow the global mismatch stop to dependent actions, so safe D-17 continuation and D-18 retries remain available under their existing guards.

Before: a mismatch in one child projection blocks all state writes and stops both lanes, even when another lane has a fresh, independent target.

After: the disputed target stays held; unrelated work can continue only after fresh disk derivation and the normal lane, quota, ownership, and landing guards pass. If no safe independent work remains, the existing bounded retry is armed. At the primary five-hour wall, the existing Codex wake preserves the pending target and follows the fresh reset.

Edge cases: the disputed projection is never repaired or dispatched; a second consecutive blocked retry parks for the operator; an explicit operator stop remains final.

## Outcome

The maintenance loop keeps disputed records from directing unsafe changes while continuing independently verifiable work until the eligible queue is empty or the primary quota wall.

- A mismatch holds only actions that depend on its target, ownership, or recovery state.
- Independent eligible work continues through the existing D-17 decision and guard sequence.
- A blocked exit can use the existing D-18 retry, which re-derives its block from disk and retains the two-block operator park.
- The existing Codex five-hour wake keeps the pending target and schedules from the fresh primary reset.

Gate delta: no gate, validator, lock, ledger, state field, refusal class, or blocking review duty is added or removed; the blanket mismatch stop is narrowed to actions that depend on the disputed record.

## Assumptions

- The triggering mismatch affects a child projection while authoritative root state and other target evidence remain readable; basis: the observed run and both backlog origins, 2026-11-15.
- D-17 continuation, D-18 blocked retry, and Codex reset-wake behavior already have existing owners; basis: `docs/maintenance/operator-directives.md` D-17 and D-18, `agents/skills/maintenance/decisions.md`, and `agents/skills/maintenance/codex.md`, read 2026-11-15.
- The smallest repair belongs in the existing Step 0 disk-truth clause; that section already owns projection verification and its stop recording, so no new section is needed.
- Skill byte-budget compliance is measured by the existing blocking repository gate; any growth above the file cap is paid by an equivalent deletion in the same file.

Decision points requiring a grill: none remain.

## Standing constraints

- Never rewrite, normalize, delete, or dispatch the disputed projection.
- Continue only work whose target and required recovery facts are independently re-derived from disk; apply every existing lane, quota, ownership, safety, claim, and landing guard.
- Keep D-17, D-18, the two-consecutive-block park, and the Codex quota-wake contract unchanged except for making their existing behavior reachable around an unrelated projection mismatch.
- Add no machinery or new ceremony. Keep maintenance skill text at or under its existing byte caps through same-file deletion for any growth.

## Evaluation Criteria

**Quality dimensions:**
- safety: dependent actions remain held and disputed evidence stays byte-identical.
- continuity: independent eligible work can reach the normal D-17 decision; blocked exits can reach the existing D-18 retry and park.
- quota: the five-hour Codex pause still preserves `pending_dispatch` and arms the existing reset wake.
- simplicity: no new state, scheduling, gates, validators, locks, ledgers, or review duties appear.
- pin coverage: Step 0 pins run without a failure line; later checker failures, if any, meet the bounded skip-with-report condition in Done when.
- byte balance: `python3 scripts/skill_text_budget.py --check` passes.

**Done when:** the Step 0 text states the dependent-action boundary and independent-lane conditions; the existing D-18 retry and Codex reset wake remain linked by reference; the maintenance skill byte-budget, hygiene, and no-em-dash checks pass; and the pin check either passes or follows the bounded skip-with-report path: every Step 0 pin passes, each later failure is an exact previously documented unrelated baseline pin with its observed time and existing owner recorded, and no checker or log is changed. Any new or unowned pin failure blocks completion. The implementation adds no new machinery.

**Ship when:** none (repository-only skill change).

## Documentation Impact Assessment

Update only the existing maintenance skill's operative Step 0 clause. The directives and Codex quota adapter already own continuation, blocked-retry, and quota-wake policies, so they remain unchanged. No README or runtime-layout change is needed because the skill name, path, and invocation do not change.

## Design Invariants

Step 0 in `agents/skills/maintenance/SKILL.md` owns scheduler context and disk-truth checks. The mismatch boundary extends that existing rule because its predicate already handles projection integrity; a separate section cannot improve ownership and would duplicate the same hold. `agents/skills/maintenance/decisions.md` remains the home for continuation and blocked-retry selection, and `agents/skills/maintenance/codex.md` remains the home for Codex quota evidence and reset scheduling.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Task 1)

**Tests:**
- none; no test file is added or changed by this plan.

**Plan-related extension:** implementation and review may change files not listed above when a finding is causally related to the scoped mismatch boundary or its existing continuation and quota owners. If that link is weak or speculative, drop the finding with a one-line reason.

**Documentation:** `agents/skills/maintenance/SKILL.md` is the sole operative surface in scope. Do not duplicate this rule in `decisions.md`, `codex.md`, or the operator directives.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/state-file.md`; reason: the plan adds no scheduler field or state-file behavior.
- `agents/skills/maintenance/decisions.md`; reason: existing D-17 and D-18 lane continuation and blocked-retry owners remain unchanged.
- `agents/skills/maintenance/codex.md`; reason: the existing five-hour reset-wake behavior remains unchanged.
- `scripts/` and test files; reason: no code, validator, or test suite is in the requested scope.

## Validation Commands

Validation preamble (authoring record, rule 29): the pre-round readiness command passed after correcting the Review Scope annotation. `bash scripts/check-no-em-dash.sh added-lines --base 2c1b679f5061a8ce68de4628b6c1e20dd98d9f91` passed. `bash scripts/scan-public-hygiene.sh` passed with three report-only existing-path notices and no hygiene findings. `python3 scripts/skill_text_budget.py --check` passed with zero blocking cap breaches; its listed ratchet and missing-cap notices are advisory. `bash scripts/check_maintenance_pins.sh` reported the existing `EXEC-PROMPTS receipt delta named in the log header` failure; the Step 0 pins are earlier in the script and produced no failure line before that unrelated pin. Rule 19 RED-today evidence is not applicable because this plan prescribes no forbidden-phrase sweep or new regression phrase. Rule 22 exact-text pin auditing is not applicable because no literal spans are pinned to task snippets; the Validation Commands block passed `bash -n`.

Execution validation observations: at 10:09Z, the pin suite failed at `prompt log has no all-served (stale) entry` (line 2898); its existing owner is `docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md` and `docs/history/plans/2026-11-13-known-red-gates-consumed-baseline.md`. A fresh run at 10:37Z failed at `EXEC-PROMPTS receipt delta named in the log header` (line 3579); its existing owner is `docs/history/plans/2026-11-15-plan-readiness-seal-leg-diagnostics-separation.md`. Step 0 pins emitted no failure before either result. These are time-specific reports; the suite remains reported failed, not passed.

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
```

### Task 1: Narrow the integrity hold to dependent actions

Context surface: the plan's Terms, this task, Standing constraints, `agents/skills/maintenance/SKILL.md` Step 0, `agents/skills/maintenance/decisions.md` continue-loop condition and occupied-lane chaining owner, `agents/skills/maintenance/codex.md` Primary quota pause, and D-17/D-18 in `docs/maintenance/operator-directives.md`.

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Given a projection mismatch for target A and an independently selected eligible target B, the rule holds mutations whose target, owner, or recovery relies on A and permits B to continue only after fresh disk derivation and every existing lane and quota guard passes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given no safe independent work while the mismatch remains, the existing D-18 blocked-exit retry can record one successor whose payload re-derives the block from disk before dispatch, and the existing two-consecutive-block park remains intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a primary five-hour quota pause with a pending target, the existing Codex wake keeps that target and uses the fresh reset-anchored schedule. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the disputed projection unchanged and undispatched; retain all existing safety, ownership, claim, quota, and landing gates. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the edited maintenance skill file within its existing byte cap; pay for any growth with same-file deletions in this change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the four commands in Validation Commands and inspect the final diff for new machinery. [class: REPOSITORY_TEST]
- [x] Commit: `docs: scope maintenance integrity hold to dependent actions` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-15-maintenance-integrity-hold-overblocks-independent-lanes.md`: executed by this plan; Step 0 now holds only target-dependent actions and permits independently verified work through existing guards.
- `docs/history/backlog/2026-11-15-maintenance-integrity-stop-strands-successor.md`: executed by this plan; the bounded D-18 retry and Codex reset wake remain reachable by reference around a projection mismatch.
