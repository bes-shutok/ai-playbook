# Backlog: make review-record selection honor the requested review family

- **Filed:** 2026-10-10, execute-plan Phase 3 post-rebase review selection
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed selector-family mismatch
- **Class:** fix-class
- **Driving force:** reliability (primary); operability (secondary)
- **Skill/step:** `agents/skills/doing-code-review/SKILL.md`, Step 1; `agents/skills/review-staging/SKILL.md`, record selection; `scripts/review_record_selection.py`, `select`
- **Severity:** medium; the documented execute-plan review-record naming shape cannot be selected directly with the plan slug and `--kind code-review`
- **Cluster:** docs/history/backlog/2026-10-17-review-selector-root-derivation-refusal.md (same surface: `scripts/review_record_selection.py` selection refusals)

## Problem

The execute-plan branch-review convention names its record `YYYY-MM-DD-<plan-slug>-code-review-r<N>`. Passing `<plan-slug>` with `--kind code-review` to `review_record_selection.py select` enumerates the shared slug's other review-kind families and preserves the highest matching predecessor stem. In this run it emitted `YYYY-MM-DD-plan-review-<plan-slug>-r13.md`, even though the current branch review record is `YYYY-MM-DD-<plan-slug>-code-review-r1.md`.

The run continued by passing the complete suffix-form slug `<plan-slug>-code-review` and omitting `--kind`; the selector then found the intended r1 record and emitted the correct r2 path. This workaround is usable, but the caller contract and helper's family matching are not aligned and the workaround is undocumented.

## Expected

The selector scopes candidates to the requested review family and emits the canonical path shape documented by its caller, without treating another review kind's records as predecessors.

## Evidence

- Execute-plan Phase 3 path convention: `agents/skills/review-staging/SKILL.md`, doing-code-review path row.
- Observed helper outcomes: `scripts/review_record_selection.py select --slug plan-scope-gist-surface --kind code-review` selected the `plan-review` predecessor family; `--slug plan-scope-gist-surface-code-review` without `--kind` selected the intended code-review family.

## Acceptance

- A branch review for a plan slug with `--kind code-review` selects only the code-review family and emits the documented suffix-form path.
- Plan-review, branch-review, code-review, and exec-review families with the same artifact slug do not advance or supersede one another.
- Existing review records remain discoverable, and backup/orphan protections continue to apply.
- Tests cover mixed review-family records sharing an artifact slug and verify each family allocates its own next round.
