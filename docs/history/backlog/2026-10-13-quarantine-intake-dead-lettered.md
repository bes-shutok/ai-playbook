# Backlog: the landed quarantine intake has never stamped a row (dead-lettered disposal loop)

- **Filed:** 2026-10-13, corpus-vs-audit alignment investigate pass (commit 661a9e1fa)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class (process-intake defect in the machinery admission protocol's own loop)
- **Driving force:** reliability
- **Skill/step:** `agents/skills/maintenance/survey-arms.md` quarantine skip; `docs/maintenance/recurring-tasks/weekly-skill-review.md` quarantine batch presentation

## Problem

The machinery admission protocol landing (commit 98e1a1c76, 2026-10-10) made origin-class self-serving open rows a quarantined class: the survey's quarantine skip records `machinery-quarantine` for them, and the landed text requires that "the routing session adds or refreshes the item's `Quarantine:` header line (naming the date) as a targeted row edit" (`agents/skills/maintenance/survey-arms.md`). The weekly skill review's batch presentation reads exactly the open rows carrying that header and stages proposed dispositions for one operator batch decision (`docs/maintenance/recurring-tasks/weekly-skill-review.md`).

The intake has never fired. No open row carries a `Quarantine:` header, and no commit in the repository's history has ever added one, so the weekly batch has never presented anything and the audit's Part 5.1 disposal loop — one operator decision disposes many machinery-internal rows — has never run. Meanwhile the open corpus grew from the audit's 107 rows past 160, at least 14 of which carry `Origin class: self-serving` (the rule's own trigger) and sit unstamped.

## Evidence

- Working-tree grep and `git grep` at HEAD both return zero `^Quarantine:` lines under `docs/history/backlog/` (two-command re-derivation, 2026-10-13).
- `git log -S 'Quarantine:' -- docs/history/backlog` returns no commits: the stamping duty has never executed on any row since the mechanism landed.
- 14 open rows carry `Origin class: self-serving` (grep count, 2026-10-13); the names are held in the routed exec entry's Origins line (`docs/history/backlog/EXEC-PROMPTS.md`, entry `backlog-quarantine-stamping-pass`).
- The mechanism text: the quarantine-skip paragraph in `agents/skills/maintenance/survey-arms.md`; the D2 machinery-quarantine selection exclusion in `agents/skills/maintenance/decisions.md`; the quarantine batch presentation section in `docs/maintenance/recurring-tasks/weekly-skill-review.md`.

## Expected

Survey and routing turns stamp self-serving rows with the dated header as they classify them, and the weekly review presents the accumulated batch for one operator decision. The gap is not the rule's text — it is landed and unambiguous — but its exercise: no turn since the landing has performed the stamping over the standing corpus.

## Fix shape

Dispatch the corpus stamping pass already routed for this defect: the `backlog-quarantine-stamping-pass` entry in `docs/history/backlog/EXEC-PROMPTS.md` (this row is one of that entry's origins). The pass applies the landed rule as targeted one-line row edits over the open corpus in one scoped commit; no new machinery. After the pass, the standing loop owns the headers: surveys stamp newly classified self-serving rows, and the weekly batch presents and disposes.

## Rejected alternatives

- Author the machinery-internal rows into plans: rejected because the audit's Part 5.1 quarantines them for one weekly batch operator decision instead (`docs/maintenance/machinery-blocker-audit-2026-10-09.md`).
- Bulk-dispose the unstamped rows directly: rejected because a row's quarantine disposition is recorded only by an operator-driven turn acting on the presented batch (`docs/maintenance/recurring-tasks/weekly-skill-review.md`).
- Add a stamping script or validator: rejected because the survey arm already owns the add-or-refresh duty every survey turn; the witnessed defect is that the duty never ran, which the dispatched pass repairs — no witnessed incident shows a one-line row edit needs tooling (`agents/skills/maintenance/survey-arms.md`).
