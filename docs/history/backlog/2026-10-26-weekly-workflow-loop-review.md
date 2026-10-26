- **Status:** open
- **Workflow:** backlog
- **Priority:** low (no weekly recurrence pattern has been measured; this is a user-directed, non-blocking process review)
- **Severity:** low
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** simplicity (primary), efficiency (secondary)
- **Skill/step:** maintenance recurring-task registry; proposed `docs/maintenance/recurring-tasks/weekly-workflow-loop-review.md` and a local report under `.ai-playbook/metrics/`
- **Source:** 2026-10-26 operator decision after reviewing recent backlog prompts and commits for workflow improvement versus repeated small fixes; capture hygiene: `scan-public-hygiene --files` pass
- **Dedup probe:** searched open backlog filenames and Problem bodies for weekly review, workflow reflection, recurring review, recurrence, and process loop. `docs/maintenance/recurring-tasks/weekly-skill-review.md` reviews a rotating sample of skill text for overcomplication, repetition, and internal controversy, not the relation between incoming tasks and later fixes; the friction-audit task measures session/tool friction rather than backlog and commit outcomes; `docs/history/backlog/2026-10-26-investigate-cross-run-fix-recurrence.md` adds a per-item cross-run comparison and is already covered by `docs/history/backlog/EXEC-PROMPTS.md`, but it does not produce a periodic portfolio-level trend report. No existing task has this report scope.

## Problem

The recent workflow-loop assessment was useful but was requested manually. The existing maintenance registry has weekly tasks and durable `next_due` state, and `.ai-playbook/metrics/` is already used for local reports, but no task periodically compares backlog items, prompt entries, and commits to show whether work is adding capabilities, fixing defects, or revisiting earlier fixes. Without a recurring report, the operator must notice the gap and request the analysis again. The report must distinguish recurrence or regression from a missing complement and a separate follow-up; proximity in time alone does not establish a loop.

## Expected

Add a weekly, read-only, report-only maintenance audit using the existing recurring-task registry and its due state. Each run writes a dated report under `.ai-playbook/metrics/` that examines the period since the previous report (or a clearly labeled cold-start window), categorizes the observed work at a portfolio level, and compares plausible follow-ups with their earlier backlog origins and landed fixes. Every recurrence or regression claim cites both the earlier fix and later witness; uncertain relations are labeled inconclusive. The report states the evidence window and counts, separates new capability work from defect fixes and follow-ups, and summarizes whether the evidence supports improvement, repeated-root repair, or neither. It does not change priorities, dispatch work, create gates, or treat timing as proof. The first four reports are a pilot; review whether they produce actionable signal before extending or expanding the task.

## Suggested fix

Use one new `kind = "audit"` recurring-task procedure at a seven-day cadence. Reuse the maintenance registry's existing state and dispatch behavior as the due anchor; write dated reports under `.ai-playbook/metrics/`. Keep source collection to repository artifacts already used by the workflow: backlog origins, `PLAN-PROMPTS.md` and `EXEC-PROMPTS.md`, plans and their disposition records, and relevant commit history. Do not add a standalone skill or call this report from each `$investigate` run. After four reports, leave the task active only if the reports provide actionable trend evidence; otherwise remove or narrow the task.

## Why not fixed now

The operator authorized adding the recurring reflection, but the report's evidence window, classification rules, cold-start behavior, and pilot exit decision form a new recurring audit contract. Capture and investigate the scope before authoring that task so the scheduled review stays read-only and does not duplicate the existing weekly skill review or friction audit.
