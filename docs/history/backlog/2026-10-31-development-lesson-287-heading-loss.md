# Backlog: restore the heading for maintenance lesson 287

- **Filed:** 2026-10-31 during the maintenance-autopilot-continuation Phase 3 review
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fence-class (lesson 287's record text exists but its heading and identity are lost)
- **Driving force:** docs (secondary: maintainability)
- **Severity:** low; the lesson cannot be reliably found or distinguished from lesson 286 by heading-based lookup.
- **Source:** `.ai-playbook/reviews/2026-10-31-maintenance-autopilot-continuation-code-review-r4.md`, finding F2; capture hygiene: `scan-public-hygiene --files` pass
- **Why not fixed now:** This is a valid but unrelated lesson-corpus defect outside the plan's changed paths and continuation-policy scope; the Phase 3 review's scope summary routes it to backlog.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `lesson 287`, `missing lesson heading`, `heading-based lookup`, `merged into lesson`, and `Archive-Egress Evidence Leg Reads the Resolving Checkout`; no open item covers this lost heading.

## Problem

`docs/maintenance/development_lessons.md` contains lesson 287's title appended to lesson 286's `See also` line, followed by lesson 287's Principle and body without a heading. The completed record therefore lacks its `## 287.` identity; heading-based lookup cannot reliably find the lesson, and a reader can misattribute it to lesson 286. The defect is visible at the boundary around lines 4568–4570.

## Suggested fix

Split lesson 286's `See also` line after its existing references, then restore lesson 287's title as a standalone `## 287. ...` heading before its Principle paragraph. Keep the lesson's existing body under that heading.

## Acceptance criteria

- Lesson 286's `See also` line contains only its references.
- Lesson 287 has its own heading, Principle, body, Why, and See also structure.
- Heading-based lookup for `## 287.` returns exactly one lesson.
