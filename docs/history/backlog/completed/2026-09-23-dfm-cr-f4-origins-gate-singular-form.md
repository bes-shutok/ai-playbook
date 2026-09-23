# Backlog: dfm code-review r1 F4 — origins-closure gate blind to singular template form

- Backlog origin: docs/reviews/2026-09-23-driving-force-gist-tldr-metadata-code-review-r1.md F4 (Medium, non-blocking, deferred)
- Driving force: external (deferred finding from the driving-force/gist-tldr plan execution)
- Status: open

`scripts/check_plan_origins_closed.py` `ORIGINS_HEADER_RE` matches only the plural `Backlog origins (scope of record)` header; the new canonized template form (singular `Backlog origin: <path>` line in agents/skills/plans/SKILL.md) evades archive-gate enforcement for newly authored plans. Fix: extend the regex (and docstring) to accept the singular form, or annotate the template that the plural block remains the gate-parsed form for backlog-promoting plans.
