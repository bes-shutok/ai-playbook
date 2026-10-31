# Plan: Correct Quota Doctrine and Registry Witness References

## Disposition

Landed 2026-10-31 by exec run automation-7bb77c96 (commits 998b0ec50, 13a71db7a, 0fa387217). Code review exec r1: .ai-playbook/reviews/2026-10-31-doctrine-text-precision-residuals-code-review-exec-r1.md (PASS after one fixed blocking finding). Residual: machinery inventory regrowth red tracked in docs/history/backlog/2026-10-31-machinery-inventory-regrowth-red-two-release-scripts.md.

Backlog origin: docs/history/backlog/2026-10-30-doctrine-text-precision-residuals.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-31-plan-review-doctrine-text-precision-residuals-r*.md
Authoring claim: 2026-10-30-doctrine-text-precision-residuals.md (session 01a19102-3396-7662-b283-1fe0117de2f0)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- Durable witness: a path and commit reference that remains resolvable after its source plan is archived.
- Doctrine attribution: prose that identifies which existing record or behavior a contract sentence describes.

## Why

One machinery registry note points to a plan path that was moved to the completed archive, and several quota doctrine phrases contain stale or misleading references. These small inaccuracies make the source trail harder to verify and weaken the doctrine pin's value.

## Gist & Examples

TLDR: Repair four stale or misleading references, naming code quality because each correction makes the repository's written evidence match its current sources.

**Before:** The registry note links to a living plan path that no longer exists, the quota doctrine contrasts against an unused state field, and its attribution and lesson pointer are inaccurate.

**After:** The registry note names the archived plan and landing commit, the doctrine and its test pin use a self-contained contrast, and both the attribution and lesson pointer resolve to their actual sources.

**Edge cases:** Keep the doctrine's decision semantics unchanged; do not broaden registry cleanup beyond the identified citation or change the witness row's disposition.

## Outcome

The registry and quota doctrine point to current, verifiable evidence without changing runtime behavior.

- The removals-row note names the completed `phase2-baseline-repair` plan and its landing commit.
- The quota doctrine prose and its active test pin describe current evidence without the stale `wave_budget_receipts` term or false `dispatch_failed` attribution; historical fixture lines remain intact.
- The lesson containing the stale machinery witness See-also points to its existing completed plan.

Gate delta: runtime gates, refusal classes, fences, protocol layers, schema fields, and dispatch conditions added or removed: none; the existing plan review remains the blocking review-layer duty.

## Assumptions

- assume the completed plan path and commit `fe04f7a7b` are the durable witness for the registry citation; basis: the sibling registry row already uses this archived-plan-plus-commit form and the completed plan exists.
- assume the stale ordinal contrast and parenthetical attribution may be removed or rewritten as self-contained prose; basis: the origin's scoped options and current source inspection show these phrases add no runtime behavior.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Evidence accuracy: every changed path resolves and each prose attribution matches the cited source.
- Behavioral stability: no runtime decision or schema changes.

**Done when:**
- The registry check passes, the quota doctrine suite passes, and the source scan finds no remaining occurrence of `wave_budget_receipts` in the operational doctrine; the test explicitly pins the stale contrast's absence while preserving the valid per-round ordinal pin and historical fixture lines.
- The four corrections match the selected origin scope and the final plan digest receives a ready review.

**Ship when:**
- No external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_registry.json` (Task 1)
- `scripts/machinery_inventory.py` (Task 1)

**Tests:**
- `scripts/test_quota_wall_doctrine.py` (Task 2)

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Task 2)
- `docs/maintenance/development_lessons.md` (Task 1)
- `docs/history/plans/completed/2026-10-29-phase2-baseline-repair.md` (review-only)
- `docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md` (review-only)

**Plan-related extension:** implementation and review may change files not listed above only when causally related to a task or a changed contract.

**Out of scope; reject unless plan-related:**
- Other registry rows or quota doctrine sections; unrelated references and lessons.

## Validation Commands

```bash
python3 scripts/machinery_inventory.py --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_wall_doctrine.py -q
rg -n 'wave_budget_receipts' agents/skills/execute-plan/SKILL.md
```

### Task 1: Repair durable witness references

Context surface: the plan's Terms, this task, and the backlog origin.

Files:
- `scripts/machinery_registry.json`
- `docs/maintenance/development_lessons.md`
- `docs/history/plans/completed/2026-10-29-phase2-baseline-repair.md`
- `docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md`
- `scripts/machinery_inventory.py`

- [x] Update only the note on `guard:maintenance-pins-recorded-red-consult` to name `docs/history/plans/completed/2026-10-29-phase2-baseline-repair.md` and commit `fe04f7a7b`, Task 3; verify the cited commit and archived plan resolve. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point the See-also naming the nonexistent machinery receipt-witness backlog family to `docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md`, the durable witness after that origin row's disposition; leave the remaining lesson text unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] (backfilled 2026-10-31: command ran and its result was recorded; exit 1 carries exactly 2 pre-existing regrowth failures introduced by 0a3c1ee34, owned by docs/history/backlog/2026-10-31-machinery-inventory-regrowth-red-two-release-scripts.md; the plan forbids touching other registry rows, so the exit-0 expectation is discharged via the marked backfill record) Run `python3 scripts/machinery_inventory.py --check`; expect exit 0 and its `ok` summary. [class: REPOSITORY_TEST]

### Task 2: Make quota doctrine attributions self-contained

Context surface: the plan's Terms, this task, and the backlog origin.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/test_quota_wall_doctrine.py`

- [x] Reword or remove the residual ordinal contrast at the cited doctrine sentence; remove the stale `wave_budget_receipts` reference from operational prose while preserving fixture strings that deliberately exercise historical manifest lines. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the doctrine test to pin the surviving per-round ordinal wording and assert the stale contrast is absent from the operational doctrine; preserve the historical fixture data. [class: IMPLEMENTATION_REQUIRED]
- [x] Reword or remove the adjacent `dispatch_failed` parenthetical so it does not misidentify a pre-existing line as the doctrine's receipt; preserve the doctrine's operational requirements. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the quota doctrine suite and the scoped doctrine scan; expect all tests to pass, no stale field reference in the operational prose, and the stale-contrast absence assertion to pass. [class: REPOSITORY_TEST]
