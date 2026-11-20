# Backlog: maintenance revisions ledger top block still breaks reverse-chronological date order

- **Filed:** 2026-11-19, deferred residual of the twin-slot exec run's code review r2 (finding 1, Low, non-blocking; record .ai-playbook/reviews/2026-11-19-twin-slot-carrier-fixed-overhead-waste-code-review-r2.md + .stats.json; supersedes r1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** self-serving
- **Skill/step:** `agents/skills/maintenance/CHANGELOG.md` (revisions ledger, top block ordering)
- **Cluster:** docs/history/plans/2026-11-13-twin-slot-carrier-fixed-overhead-waste.md (the plan whose Task 3 entry introduced the misordered block; finding pattern documentation#prose-ledger-date-order)

## Observed versus expected

**Observed:** the revisions ledger's reverse-chronological order still breaks at its top block: the newly added 2026-11-13 entry (twin-slot lane-state sharing and pinned ordering) sits above the newer 2026-11-16 and 2026-11-14 entries, so a newest-first scan lands on the 2026-11-13 entry first. Witnessed by the exec code review r2 focused panel (correctness-completeness worker, finding 1, severity Low, non-blocking, triage deferred).

**Expected:** the ledger's top block reads in strict newest-first date order; the 2026-11-13 entry sits below the 2026-11-16 and 2026-11-14 entries. Fix is a bounded reorder of the misdated entry within the same file.

## Exact location

`agents/skills/maintenance/CHANGELOG.md`, ledger top block: the dated 2026-11-13 twin-slot entry positioned above the dated 2026-11-16 entries.

## Suggested fix

Move the 2026-11-13 entry block below the 2026-11-16 entries in the same file; no wording changes. Then rerun `python3 scripts/skill_text_budget.py --check` (the file participates in the byte accounting) and the maintenance pins suite.

## Severity and source reference

Low, non-blocking, deferred. Source: `.ai-playbook/reviews/2026-11-19-twin-slot-carrier-fixed-overhead-waste-code-review-r2.md` (round r2, finding id 1, fresh-adversarial, focused panel; verdict yes with this one non-blocking residual). capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The run's review-fix cycle closed on zero blocking findings; fixing the residual after the r2 verdict would change reviewed file bytes and trigger another full review round for a Low ordering nit, so the run defers it. Owner: the next maintenance exec session that touches `agents/skills/maintenance/CHANGELOG.md` for any other reason folds the reorder into that change.

## Driving force

docs (source-of-truth ordering drift in a prose ledger); secondary: simplicity.

## Dedup probe

Keyword search over the open backlog corpus (filenames plus problem bodies) for date-order, reverse-chronological, and changelog ledger themes: nearest hits (2026-11-19-exec-pick-survey-under-vetting, 2026-10-29-done-final-only-plan-validation-residuals) cover survey vetting and validation residuals, not ledger date ordering; no open row covers this file's block order. No merge; distinct item.

## Environment context

One prose reorder inside a tracked skill-side ledger file; no machinery, no schema, no gate change.
