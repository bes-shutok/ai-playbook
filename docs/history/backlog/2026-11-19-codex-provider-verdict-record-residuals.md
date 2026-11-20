# Backlog: Codex provider verdict record residuals from the certification round

- **Filed:** 2026-11-19, plans authoring closeout (plan 2026-11-19-codex-incomplete-run-owner-status-unavailable, r2 certification round)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class (docs precision)
- **Origin class:** certification residual routing
- **Witness:** the r2 review record `.ai-playbook/reviews/2026-11-19-plan-review-codex-incomplete-run-owner-status-unavailable-r2.md` (gitignored reviews home; this row is the durable copy per the terminal certification duties)

## Problem

Two Low non-blocking findings from the certification round are consequence-bearing residuals routed here per the certification-residual duties (the certification round folds blocking findings only; its non-blocking findings never force a re-round or a plan fold):

1. Task 1's grouped-status exclusion checkbox still attributes its reason to "the origin row's reason", but the origin row never mentions that surface; the re-anchored reason lives in the plan's Terms entry, so the checkbox now contradicts the entry it should cite.
2. Task 1's evidence-record pinned-field enumeration writes the executable path and provider response fields unconditionally, while they are only producible in the supported arm; an unsupported-arm execution faces a literally unsatisfiable acceptance item.

## Expected

A future edit of the plan (or its execution run, if it hits the items) re-anchors the checkbox reason to the plan's own Terms entry and qualifies the two record fields as supported-arm-only (or splits them into a supported-conditional item), preserving acceptance coverage.

## Suggested fix

Two sentence-level edits on `docs/history/plans/2026-11-19-codex-incomplete-run-owner-status-unavailable.md` (or its completed twin if already archived): re-anchor the attribution; arm-condition the field list. No machinery.
