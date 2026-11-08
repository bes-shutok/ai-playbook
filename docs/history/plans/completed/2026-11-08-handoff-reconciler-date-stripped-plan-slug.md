# Plan: Reconcile dated plan handoffs by canonical slug

Backlog origin: docs/history/backlog/2026-10-31-handoff-reconciler-refusal-coverage-trio.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-11-08-plan-review-handoff-reconciler-date-stripped-plan-slug-r*.md
Authoring claim: 2026-10-31-handoff-reconciler-refusal-coverage-trio.md (session 01a1b272-f972-7623-ac4c-bde3b8c464ca)
Execution budget: 0.75h total, largest task 0.75h
Executed: yes (0973b23090ff7746576e8604d24947e962a482c8)

## Terms

- Canonical plan slug: the identity `plan_session_slug` derives for a dated single-file Markdown plan by removing its leading `YYYY-MM-DD-` prefix; this plan does not change directory-plan task resolution.
- Handoff receipt: the persisted evidence that reconciles one completed task into execution runtime state.

## Why

A normal dated single-file plan can be refused during done-pending reconciliation because runtime state stores the date-stripped slug while the helper compares it with the full dated filename stem. This blocks the run before its remaining evidence checks can complete.

## Gist & Examples

TLDR: Compare canonical plan slugs and retain exact path binding, for code-quality.

Before: `2026-11-08-example-plan.md` with runtime `plan_slug: example-plan` is refused as an identity mismatch. After: the dated file proceeds through the existing claim, review, and receipt checks; a genuinely different slug still refuses without mutation.

## Outcome

A dated plan with matching canonical runtime identity can reconcile safely, while mismatched identity continues to refuse.

- Dated single-file Markdown plans proceed to the existing claim, review, terminal-receipt, and state checks when their canonical slug matches runtime state.
- A mismatched slug is refused and runtime-state bytes remain unchanged.
- Receipt evidence remains bound to the exact resolved plan path and its reviewed bytes.

Gate delta: remove the false plan-identity-mismatch refusal for a matching date-stripped slug; retain the genuine mismatch refusal and all existing claim, review, receipt, atomic-write, and re-read checks; no new gates, fences, protocol layers, schema fields, dispatch conditions, or blocking review duties.

## Assumptions

- `scripts/done_run.sh::plan_session_slug` defines the canonical identity for dated single-file Markdown plans; the origin investigation observed this exact caller contract.
- The caller continues to provide the resolved dated plan path, and that full path remains the receipt identity.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: dated single-file plans with matching canonical slugs reconcile; different slugs refuse.
- Safety: refusal preserves runtime-state bytes, and accepted receipts retain the exact plan path and digest.

**Done when:**
- Focused regressions prove the successful dated-file path and genuine mismatch refusal without state mutation.
- Caller, claim, review lookup, and stored receipt continue to use the same resolved plan path and reviewed digest.

**Ship when:**
- None; all acceptance evidence is repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reconcile_execute_plan_handoff.py` (Task 1)

**Tests:**
- `scripts/test_reconcile_execute_plan_handoff.py` (Task 1)

**Documentation:**
- `docs/history/backlog/2026-10-31-handoff-reconciler-refusal-coverage-trio.md` (Task 2)
- `docs/history/backlog/2026-11-08-handoff-reconciler-residual-refusal-coverage.md` (Task 2) *(new)*

**Plan-related extension:** Treat a finding as in scope when it is causally related to the canonical identity comparison or its receipt binding. If the link to the plan is weak or speculative, drop it with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; the existing caller already supplies the resolved plan path, and this plan preserves that contract.
- Directory-shaped plans with a charter and separately stored task files; their task extraction and review identity require a distinct plan-shape-aware change.
- Other handoff refusal classes, runtime-state transitions, and unrelated execution guards.

## Validation Commands

```bash
set -euo pipefail
python3 -m pytest scripts/test_reconcile_execute_plan_handoff.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-11-08-handoff-reconciler-date-stripped-plan-slug.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Compare canonical slugs while preserving receipt identity

Context surface: `## Terms`, this task, and the existing handoff receipt and exact-path verification in `HandoffReconciler`.

Files:
- `scripts/reconcile_execute_plan_handoff.py`
- `scripts/test_reconcile_execute_plan_handoff.py`

Primary class anchors:
- `HandoffReconciler` in `scripts/reconcile_execute_plan_handoff.py`

- [x] Given a dated single-file Markdown plan path and matching date-stripped runtime identity, expect reconciliation to pass the identity check, complete the existing evidence checks, and store a receipt bound to the exact resolved plan path and digest. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a dated single-file plan path and a genuinely different runtime slug, expect `plan-identity-mismatch` and byte-identical runtime state after refusal. [class: REPOSITORY_TEST]
- [x] Given the normal caller path, expect claim verification, review lookup, and stored receipt to remain bound to that same resolved plan path and reviewed digest. [class: REPOSITORY_TEST]
- [x] Run the focused regression before the fix and observe the matching dated-file case fail with `plan-identity-mismatch`; after the fix, expect matching and mismatched cases to pass their respective outcomes. [class: REPOSITORY_TEST]
- [x] Commit: `fix: compare canonical handoff plan slug` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Preserve the remaining origin coverage gaps

Context surface: the selected plan scope and the existing origin row’s two refusal classes outside the identity defect.

Files:
- `docs/history/backlog/2026-10-31-handoff-reconciler-refusal-coverage-trio.md`
- `docs/history/backlog/2026-11-08-handoff-reconciler-residual-refusal-coverage.md` *(new)*

- [x] Before the origin is folded and deleted, expect the residual backlog item to retain both `artifact-slug-unusable` and `review-evidence-drift` with the origin’s test-only remedy and no identity-fix scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: preserve residual handoff refusal coverage` [class: IMPLEMENTATION_REQUIRED]

**Origin disposition:** At completion, fold the source origin into the archived plan and delete it per lifecycle. The residual item `docs/history/backlog/2026-11-08-handoff-reconciler-residual-refusal-coverage.md` keeps the two uncovered refusal classes open.
## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-31-handoff-reconciler-refusal-coverage-trio.md`: Task 1 fixed the dated-plan identity mismatch and added the matching-slug and genuine-mismatch regressions. The independent `artifact-slug-unusable` and `review-evidence-drift` coverage gaps remain tracked in `docs/history/backlog/2026-11-08-handoff-reconciler-residual-refusal-coverage.md`.
