# Sync diagnostics-script docstrings with the corrected machinery registry notes

Added: 2026-10-27, intermediate review of Task 2 (docs/history/plans/2026-10-04-maintenance-doc-hygiene-review.md, finding F3)

Origin class: improvement
Driving force: the Task 2 registry correction renamed weekly-skill-review as the real consumer of the duplication and byte-budget reports, but the scripts' docstrings (scripts/skill_text_duplication.py, scripts/skill_text_budget.py) still carry the pre-correction wording (rider as cadence home; "until the growth-telemetry consumer lands"), lagging the registry notes and misleading a fresh reader of the scripts.

## Acceptance

- Both docstrings name weekly-skill-review as the consumer with the same six-weekly-window sunset wording the registry notes carry; no behavioral change.

Cluster: 2026-10-27-emdash-residuals-open-rows-and-literal
