# Backlog: done_run setup mixes status lines into the eval-able export stdout

- **Filed:** 2026-11-03, learn Step 1.8 skill-usage capture (authoring closeout session)
- **Status:** covered (docs/history/plans/2026-11-03-done-run-setup-stdout-export-emission-split.md)
Cluster: docs/maintenance/development_lessons.md #261 (the tee-source field failure of the same emission shape; the orphaned-release recovery)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** skill-usage issue capture (learn Step 1.8, second witnessed field failure)
Class: fix-class

## Observed versus expected

Observed: `scripts/done_run.sh setup` (and the done-lock acquire helpers it wraps) print one human-readable status line plus the eval-able `export` lines on the same stdout. The done skill's Step 0 prescribes evaluating only the `export`-prefixed lines, but whole-stdout consumption keeps failing in the field: a 2026-10-26/27 run sourced a tee'd capture and the non-export lines aborted `source` mid-file (lesson #261's witness), and a 2026-11-03 run ran `eval "$(bash scripts/done_run.sh setup ...)"` whole, which died on a shell parse error raised by a status line containing brace characters, after setup had already acquired the lock and written the boundary record. Both failures leak an acquired hold plus a partial boundary that a later invocation must re-enter or orphan-release.

Expected: the machine-consumed acquisition surface is eval-safe by construction. Status, advisory, and diagnostic lines belong on stderr; stdout carries only the parseable assignment lines, so the documented filter rule becomes a belt rather than the only thing standing between the caller and a leaked hold.

## Suspected root area

The setup emission shape in `scripts/done_run.sh` and its underlying `scripts/done-lock.sh` acquire echo: move status and diagnostic output to stderr, keep stdout to the `export` lines (or named key=value lines the wrapper evaluates), and mirror the split in the composed subcommand banners. The skill text's filter-the-export-lines prescription stays as the consumer-side guard.

## Environment

Playbook repo, repo-local scripts and vendored skill copy; runtime ZCode agent session; witnessed 2026-11-03 with the 2026-10-26/27 failure as the first witness (lesson #261).
