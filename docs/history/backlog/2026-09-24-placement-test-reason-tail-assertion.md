# Backlog: placement test under-asserts the {line!r} reason tail

- Priority: low
- Status: open
- Workflow: backlog
- Scope: `scripts/test_plan_readiness.py` (`test_continuation_line_tag_reports_placement`)
- Owner: playbook maintenance
- Source: code review r1 F7 for plan 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots (Low, non-blocking)
- Driving force: code-quality + simplicity

Origin: docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r1.md, finding F7. The placement test asserts the reason contains `non-checkbox line` and the task label, but never asserts the `{line!r}` tail of the message ("...first (checkbox-marker) line: {line!r}"). A regression that returns the right prefix while naming the WRONG line (e.g. quoting the checkbox-marker line instead of the continuation line that carries the tag) would pass the suite, so the test under-pins the operator-facing payload of the check.

Suggested fix: add an `assertIn` of the offending line's distinguishing text (the wrapped tag line itself) to `test_continuation_line_tag_reports_placement`, so the reason is pinned to quote the actual non-checkbox line.
