# A read-only audit arm for dated record fields against the carrying commit's date (lesson 124's audit rule has no vehicle)

- **Filed:** 2026-10-19, post-implementation-review session improvement sweep
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium (recurrence demonstrated after the writer-side lesson landed, but the stakes are record metadata and the candidate vehicle is report-only)
- **Origin class:** session-witnessed flow gap (dated-field stamping across backlog rows, section stamps, and ceremony records)
- **Class:** fix-class
- **Skill/step:** candidate homes named in Expected; the investigate pass owns the routing decision
- **Driving force:** reliability (a record's date field is identity-bearing: it reads as the record's truth to every later reader, sort, and retention pass)

## Problem

Lesson 124 (`docs/maintenance/development_lessons.md`) fixes the writer-side rule: a record's timestamp comes from the operation's own clock at write time, never a date carried from earlier-turn context. The rule also has an audit arm ("when auditing a landed stamp, cross-check it against the date of the commit that carried it, which is ground truth"), but nothing runs that arm: a probe over `agents/skills/review-plan/SKILL.md`, `agents/skills/review-agents/`, and the open backlog finds no validator, panel duty, or survey line that compares a dated field with its carrying commit's author date. The class re-bit hours after the lesson landed: the parked-run-continuation row was filed 2026-10-19 20:47 (7249dbacc) with its filename date prefix, Filed header, and commit message all carrying 2026-10-17 quoted from earlier-turn context; the row was then deleted as superseded with the misstamp still in it (517c4e4d7), so the corrective pass never needed a vehicle. The same day's original witness is e418023c2 (a resume-state section stamp two days stale, citation-only corrective). Writer-side discipline alone has now missed twice in one day in this repo.

## Expected

A vehicle that runs lesson 124's audit arm mechanically, landed read-only first per the machinery admission protocol (incident: this row plus the lesson's Why witnesses; expected catch frequency: twice in one day repo-wide at current volume; false-positive cost: one report-only line, since a truthful stamp's date equals its carrying commit's author date and never flags; sunset/review: promotion only after a true catch, with the pre-registered registry-removal row the protocol requires). Candidate homes for the investigate pass to route between: (a) a consultative mode on an existing maintenance survey, modeled on the prune audit's report-only survey posture (`scripts/check_prompt_log_origins.py --prune-audit` consultative arm), scanning a landing range's new dated fields (backlog row Filed/Updated headers, filename date prefixes, lesson stamp lines, ceremony records) against their carrying commits' author dates; (b) one finding-class line in the review panels' existing finding-class documentation, so a panel reviewing commits that touch dated records flags carried-date stamps; (c) writer-side only, in which case the row resolves as covered by lesson 124 with the recurrence accepted. Note for (a): a dated field later than its carrying commit's author date is wrong by construction, but both witnesses belong to the earlier-than-commit shape (the carried-date signature), so the signal must be commit-day mismatch, not post-dating alone.

## Why not fixed now

Binding the audit arm to a survey or a panel is new machinery over a lane, and the machinery admission protocol plus the skill-text anti-growth rules route that through an admission case and a routing decision this row reserves for its investigate pass; landing it ad hoc would also pick a home before the cheaper panel-line arm is priced.
