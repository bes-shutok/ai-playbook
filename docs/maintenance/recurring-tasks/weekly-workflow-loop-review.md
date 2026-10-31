```toml
id = "weekly-workflow-loop-review"
cadence_days = 7
kind = "audit"
```

# Recurring task: weekly workflow-loop review

Run this task as a read-only portfolio review through the maintenance recurring-task registry. The registry owns due selection and the default per-task state record. This task writes one dated report under the facts-resolved `metrics_dir` (fallback `.ai-playbook/metrics/`); it changes no tracked project file, backlog priority, dispatch decision, gate, or validator.

## Evidence window

Use UTC timestamps. Find the most recent `workflow-loop-review-*.md` report in the resolved metrics directory and read its `Evidence window end` value. If one exists, the next window starts at that value and ends at this run's start time. On cold start, use the prior 30 complete UTC days. State the exact start and end in the report. Write a unique filename using the run's UTC timestamp so a same-day rerun does not overwrite the earlier report.

## Sources and counting

Read repository artifacts: dated origin rows in the resolved backlog, entries and their origins in `PLAN-PROMPTS.md` and `EXEC-PROMPTS.md`, plans and their backlog disposition records, and commits in the evidence window. For a plausible follow-up, use its origin path or recorded plan disposition to inspect only the earlier commits needed to verify the alleged origin or fix, even when they predate the window; these commits support relationship classification only and do not enter the window counts. Do not read session databases, transcripts, or user-level logs.

Use one distinct backlog origin or explicitly clustered origin group as the work unit. Include it once when its origin is created, a prompt for it is written or changed, its plan disposition changes, or an associated fix/landing commit occurs within the window; multiple events for the same group count once. Do not count an older still-open origin again unless one of those events occurs in the window; its current status may be reported as context. Count prompt entries and commits separately from work units; link them only when their origin paths or a plan's recorded backlog origins establish the relation. Keep work with no durable origin link in an `unclassified` count. Do not infer intent or causality from commit subjects or timing alone.

For each work unit in the window, classify its intent as `new capability`, `defect fix`, `workflow follow-up`, or `unknown`, and record whether it remains open, has a ready prompt, or has a landed disposition. Count these disposition states as independent flags; a unit may be both open and have a ready prompt, so report the distinct unit total and never sum the flags to derive it. For each plausible follow-up to earlier work, classify the relation as `recurrence after fix`, `regression from fix`, `missing complement`, `separate root`, or `inconclusive`. A recurrence or regression requires an earlier origin, the landed fix, and a later witness. If any link is missing, mark the relation inconclusive and name the missing evidence.

## Report

Write `workflow-loop-review-<UTC timestamp>.md` under the resolved metrics directory. Include:

- report time, exact evidence window, and sources read;
- counts of distinct origin groups by intent and current disposition, plus prompt-entry and associated/unclassified-commit counts;
- every plausible follow-up relationship with the earlier origin/fix, later witness, classification, and evidence links;
- data gaps and the number of units left unclassified;
- one evidence-rated conclusion: `improving`, `repeat-root pattern`, `mixed`, or `insufficient evidence`.

Use `improving` only when comparable reports show fewer confirmed repeat-root cases and the cited origin groups have landed or closed. Use `repeat-root pattern` only for confirmed later witnesses after an earlier fix. Use `mixed` when the window contains both confirmed repeat-root cases and independently landed work. Use `insufficient evidence` when the records do not support those conclusions or the report windows are not comparable. Compare rates only when the windows and denominators match; otherwise report counts without a trend claim.

Count this report with prior reports to identify the fourth report. On report four, add a `Pilot review` recommendation to keep, narrow, or remove the task, with evidence for whether it produced actionable trend information. The task continues unchanged until an operator acts on that recommendation. Never create backlog items or change priorities from this report.

## State advance

On success, update the registry's default per-task state record with `last_run_at`, `next_due` at completion plus seven days, a one-line `last_result`, and `consecutive_failures = 0`, using the registry's atomic-replace discipline. Do not add task-specific state fields. On failure, record the failure result and use the registry's one-day failure advance; do not fabricate a normal report or conclusion.
