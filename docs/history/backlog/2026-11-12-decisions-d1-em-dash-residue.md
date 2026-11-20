# Backlog: a pre-existing em-dash in the D1 continue-loop paragraph trips every touched-scan over decisions.md

- **Filed:** 2026-11-12, execute-plan Task 1 intermediate review (off-plan capture; witnessed by the `check-no-em-dash.sh touched` hit at decisions.md:29, introduced by commit f25256301, 2026-11-04, before the run)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** hygiene-class
- **Skill/step:** `agents/skills/maintenance/decisions.md` (the continue-loop condition paragraph's em-dash-bearing line)
- **Driving force:** documentation hygiene (the em-dash write-time fence postdates the introducing commit, so operative text carries a U+2014 that every touched-scan over the file reports, parking boundaries on a pre-existing residue outside the editing run's own hunks)
- **Witness:** 2026-11-12: the Task 1 implement pass's touched scan exited 1 on decisions.md:29 while its added-lines gate was clean; the hit predates the run and sits outside the task's hunks, so it was parked rather than fixed in-task

## Problem

One line of the D1 continue-loop paragraph contains an em-dash. The em-dash scans (`touched`, `added-lines` over any base older than the introducing commit) report it on every pass over the file, so each editing run re-parks the same pre-existing residue and the touched-scan gate cannot serve as a clean authoring-time self-check for this file.

## Expected

The em-dash is replaced with fence-compliant punctuation (a comma or semicolon, preserving the sentence's meaning) in a one-line edit; afterwards `check-no-em-dash.sh touched` over the repository exits 0 and the touched scan stops parking on this residue.

## Suggested fix

One punctuation substitution on the em-dash-bearing line of the D1 paragraph; no other bytes change; run `bash scripts/check-no-em-dash.sh touched` after the edit and expect exit 0.
