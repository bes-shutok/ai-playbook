# Backlog: learn appends repeat witnesses without routing heavy recurrence to a fix

Status: open
Priority: normal
Class: fix-class
Origin class: learn Step 1.8 skills-corpus capture (2026-11-03 session-pattern harvest)
Added: 2026-11-03

## Observed versus expected

The project lessons corpus accumulates ordinal witness marks without a utilization route: appending the Nth witness to a lesson records that the rule was re-needed, but nothing then opens or refreshes a fix row for the owning surface, so heavy lessons keep re-accruing witnesses. In-window tally: one lesson family reached its seventh witness (two landing in the window), another holds eight, another five, another four; fourth-witness marks landed via three separate learn commits in the window (66b083310, 21f2cd2ce, a7ac36303), none of which opened a row.

Expected: a learn run appending an ordinal witness at or beyond the third to a lesson creates or refreshes a backlog row for that lesson's owning surface in the same run (or records in the run output why not), so recorded recurrence becomes fix pressure instead of corpus growth.

## Reproduction evidence (trimmed)

- Corpus ordinal-witness marks visible in docs/maintenance/development_lessons.md (exact numbers re-derived at plan time).
- In-window witness commits: 66b083310 (fourth witness), 21f2cd2ce (fourth witness on two lessons), a7ac36303 (fourth witness), 0767d38ca (seventh witness), bf6e14189 (sixth witness).

## Suspected root area

agents/skills/learn/SKILL.md Step 1 extraction and the Step 1.8/1.9 capture gates: the witness-append rule has no recurrence threshold and no routing duty.

## Fix shape

One sentence family in learn Step 1 (SKILL.md plus step-1-extract.md if needed): when a learn run appends an ordinal witness at or beyond the third to a lesson, the same run opens or refreshes a Step 1.8/1.9 row for the owning surface, or records the decline reason in the run output. Text-only, no validator, no state change. Machinery admission: incident = the seventh-witness family still recurring (corpus marks); expected catch = every third-plus witness append; false-positive cost = one row per heavy family, bounded by the decline reason; sunset and review = when no lesson family holds more than three live witnesses.
