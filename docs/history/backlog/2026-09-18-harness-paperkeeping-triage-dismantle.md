# Backlog: Harness paperkeeping triage: dismantle dead weight, shrink over-built validators

Status: open
Workflow: backlog
Source: Andrey 2026-09-18: "weigh the pluses and minuses of keeping it in scope of the main principles used for plan assessments. If it's just for security and paperkeeping we should plan/backlog to dismantle it; if it helps efficiency, simplicity or quality we might keep and even plan/backlog to improve those". Full triage table in `docs/tmp/2026-09-18-harness-principles-triage.md`.
Severity: Low (maintenance cost, not correctness: the machinery works; it is bigger than its evidence justifies in a few places)
Scope: scripts/validate_review_staging.py, scripts/summarize_review_stats.py, scripts/review_usage_capture.py, scripts/doc_registry_validator.py, scripts/lessons_*.py, agents/skills/review-staging/SKILL.md

## Problem

Triage against the plan-assessment principles (efficiency, simplicity,
quality) found no case for dismantling the harness as a whole: the core
machinery (done-lock, manifest/launch records, digest binding, hygiene scan,
sidecar contract) each prevents a recorded incident class. But several
components are over-built relative to their evidence:

- `validate_review_staging.py`: 12k lines (largest file in the repo) to
  enforce the review-staging schema, 4x the size of the runtime driver.
- `summarize_review_stats.py` (6.2k) + `review_usage_capture.py` (1.3k):
  telemetry whose reports may have no readers.
- `doc_registry_validator.py`: 2.6k lines / 116 checks; unknown how many
  ever fired.
- Lessons corpus family: 5 scripts (~7.5k LOC) with overlapping entry
  points.
- Fail-open/dead probe paths: owned by the harness-detection/budgeting-skip
  plan executing 2026-09-18; verify its outcome before acting here.

## Proposed direction

1. Method for each candidate: does it prevent a recorded incident (quality),
   save more agent time than it costs (efficiency), and is it the cheapest
   such mechanism (simplicity)? Fails all three -> dismantle; passes but
   over-built -> shrink.
2. Use `review_usage_capture` output (or a one-off count) to list gates and
   validator checks with zero lifetime findings; prune those that guard no
   observed failure mode, keeping the incident-linked ones.
3. Shrink `validate_review_staging.py` toward deriving sidecars from review
   output instead of validating hand-written ones, or collapse redundant
   schema layers.
4. Consolidate the lessons scripts behind one entry point with subcommands.
5. Any single component whose trimmed form still fails the three-question
   test gets dismantled outright rather than maintained.
