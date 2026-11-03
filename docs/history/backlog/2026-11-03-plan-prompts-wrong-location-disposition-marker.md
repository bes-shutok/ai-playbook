# Backlog: wrong-location race-resolution entry disposition lacks its evidence-basis marker

Status: open
Priority: normal
Class: fix-class
Origin class: learn Step 1.9 project-issue capture (2026-11-03 REM harvest closeout; standing checker report)
Added: 2026-11-03

## Observed versus expected

`python3 scripts/check_investigate_entries.py --log docs/history/backlog/PLAN-PROMPTS.md` reports (exit 0): "entry 'wrong-location-lead-clause-race-resolution': disposition line 706 lacks an evidence-basis marker" and "1 violation(s) in docs/history/backlog/PLAN-PROMPTS.md". The disposition ends on prose naming the sibling row without citing it in the accepted marker form ("...the SKILL.md bytes are the only live surface and the sibling row owns them."). Expected: every entry in both rolling logs passes the checker clean; the marker floor (landed 61e868979) requires each rejected-alternative disposition to close on a disk-verifiable basis.

## Reproduction evidence (trimmed)

- Checker run of 2026-11-03: 17 entries, 59 disposition lines, 1 violation, exit 0.
- The entry landed in commit 045335eef (foreign lineage, 2026-11-03 07:20Z); a same-day rerun by the capturing session confirms the violation stands at HEAD.

## Suspected root area

Entry authoring under investigate Stage 4: one rejected-alternative disposition was closed on prose whose named witness (the sibling row) was never cited as a marker the checker accepts.

## Fix shape (arms, priced at plan time)

One-line append closing the disposition on the sibling row it already names, for example "...the sibling row owns them (docs/history/backlog/2026-11-02-lead-clause-amendment-unlanded-skilled.md)." Single surface; the rolling-log Write boundary rule (done lock plus ref-bound commit) applies; no checker or template change; the violation count returns to zero.
