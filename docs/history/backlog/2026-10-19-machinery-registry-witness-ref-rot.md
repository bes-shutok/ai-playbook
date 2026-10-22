# Backlog: machinery-registry witness references rot when their backlog rows are deleted on landing

- **Filed:** 2026-10-19, maintenance exec-run learn capture
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** formal
- **Skill/step:** scripts/machinery_registry.json (admission and removals records); repo guidelines Commit & Pull Request Guidelines (covered-row deletion rule)
- **Driving force:** correctness

Cluster: docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md (same defect class: a living record citing a backlog path that moved)
Cluster: none live (the sibling docs/history/backlog/2026-10-22-exec-prompts-entry-cites-deleted-backlog-row.md, the prompt-log rejected-alternative citation case, was resolved by events and deleted; witness 466cf9739, whose closeout prune removed the citing entry with the citation inside)
Cluster: EXEC-PROMPTS.md entry prompt-log-payload-targets-and-verdict-test-statement (covered 2026-10-22; the payload-target and verdict-application duty sentences landed, the origin row deleted per the covered-row rule)

## Problem

Machinery-registry admission and removals entries cite their motivating backlog rows by path. The repo's covered-row rule deletes a backlog row in the same change that lands its plan, so every such citation rots at its own landing: the registry holds twelve distinct `docs/history/backlog/*.md` references, of which seven point at paths that no longer exist (verified per reference by a filesystem probe plus `git cat-file -e` at HEAD, agreeing on all twelve); five resolve (four still-open rows and one already re-pointed `completed/` path).

The rot class has already bit operationally: an execution review refused (r1, blocking) when a freshly added admission entry cited a backlog row path that the same plan's landing rider was about to delete; the fix re-pointed the reference to the row's completed home. The seven stale references are the same failure, accumulated silently.

## Expected

Either the registry's witness references get a durable home convention (cite the surviving record - the completed plan or the completed backlog row - not the deletable open row), with the seven stale references repaired in one pass; or a matching check joins an existing scan surface. Any new blocking gate faces the machinery admission protocol and needs a witnessed incident (this row is that witness), expected catch frequency, false-positive cost, and a sunset.

## Evidence

- Filesystem plus `git cat-file -e HEAD:<path>` probes over every `docs/history/backlog/...md` string in `scripts/machinery_registry.json`: 12 total, 5 resolve, 7 miss (both probes agree per reference).
- Witnessed blocking refusal: execution review r1 of the 2026-10-19 clocked-order-successor-verification run, finding on the admission entry's witness reference.

## Why not fixed now

Out of the exec mandate's scope: the run's three picks were plan-bound, and the repair choice (convention change versus scan arm) is a design decision.

## Source

learn capture 2026-10-19, maintenance exec run (three plans landed; the registry ref rot witnessed at pick 2's review r1 and re-derived corpus-wide the same day).
