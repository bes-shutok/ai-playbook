# Backlog: panel profile filename-date leg accepts calendar-invalid in-window dates

Status: done 2026-09-23 (fixed by docs/plans/completed/2026-09-23-review-staging-leftovers-disposition.md; filename leg aligned calendar-strict with no sidecar fallback, Task 2 of that plan)
Workflow: backlog
Source: Phase 3 r2 code review of the review-staging-infra-quality plan execution (staging doc docs/reviews/2026-09-23-review-staging-infra-quality-exec-code-review-r2.md, finding F1; triaged deferred per the backlog-deferral default).
Severity: Low
Exact location: scripts/validate_review_staging.py `_panel_profile_record_date`, filename-date leg
Why not fixed now: consciously narrowed remainder of the r1 F3 fix (the sidecar-date fallback was made calendar-strict; the filename leg was deliberately left format-only); a filename like `2026-01-99-foo.md` is format-valid, calendar-invalid, and sorts in-window, so a malformed-named record enters the lenient reduced path. Reachable only via hand-misnamed files; the lenient path is the documented fence behavior anyway.
Driving force: code-quality

## Problem

The panel profile's record-date selection treats a filename leading date as in-window on shape alone (`\d{4}-\d{2}-\d{2}`), without a calendar-validity check, while the r1 fix made the sidecar-date fallback strict (`date.fromisoformat`). The docstring justifies this by "date-format gates elsewhere", but those gates check shape/presence only. Align the two legs (apply the same strict validation to the filename date, meaning "no date" on failure) or document the asymmetry as intended.

Trigger: the next touch of `_panel_profile_record_date` or any change to `PANEL_PROFILE_MAX_DATE` semantics.
