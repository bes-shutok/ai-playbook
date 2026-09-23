# Backlog: check_backlog_claimed unittest portability and unprescribed coverage gaps

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-24
Class: non-blocking review Low (testing hardening; deferred default per run contract)
Source: P51 plans/authoring surface hygiene code review r1 F9
Driving force: code-quality

## Observed

`scripts/test_check_backlog_claimed.py` `test_unreadable_plans_dir_exits_two` makes the fixture plans directory unreadable with `chmod(0o000)`, which is ineffective when the suite runs as root (root reads despite the mode bits), so the test can pass vacuously on a root-run CI or developer machine; it has no skip or platform guard acknowledging that. The suite also leaves small coverage gaps the plan did not prescribe: a relative `--plans-dir` value (anchoring at the repo root, never the process CWD), a duplicate `--slug` passed twice in one invocation, and a non-`.md` entry sitting in the plans directory top level.

## Expected

The unreadable-directory test is root-portable: skip with a stated reason when effective uid is 0 (or simulate the permission error another way), so the test never passes vacuously. The three unprescribed cases get one focused test each, asserting today's intended semantics (relative dir resolves against the repo root; a repeated slug is deduplicated or explicitly rejected; a non-`.md` top-level entry is ignored by the scan).

## Direction

Land all four in one small hardening pass on the same suite (no production-code change expected unless the duplicate-slug run reveals a defect; if it does, fix and record the deviation). Keep the suite stdlib-only per the checker's authoring constraint.

## Evidence

- Code review r1 F9 (docs/reviews/2026-09-24-p51-plans-authoring-surface-hygiene-code-review-r1.md), lens: testing; triaged valid non-blocking, routed to backlog per the r1 triage.
- `scripts/test_check_backlog_claimed.py` `test_unreadable_plans_dir_exits_two` uses `locked.chmod(0o000)` with no root guard (observed 2026-09-24).
