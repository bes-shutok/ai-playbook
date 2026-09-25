# Backlog: registry backfill for the 2026-09-08 to 09-16 archive-move wave

Status: rejected (2026-09-26; superseded: the closure records the backfill landed 2026-09-19 with zero-finding evidence)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; registry/catalog bookkeeping parity (re-fires only on a stale session base). Revive on the refire is witnessed blocking a real done run, or a project-priority-profile change.)

Workflow: backlog
Source: done Step 2.648 on 2026-09-18: `doc_registry_validator.py validate` reported 64 unregistered completed-history files and `check-writes` reported 16 unprotected immutable writes once a stale session-start base re-covered the 09-14 to 09-16 squash-merge archive moves (witnessed during the fixture-hygiene done run).

## The gap, precisely

The 09-08 to 09-16 wave of archive moves (backlog items to `completed/`, plans to `completed/`, from the squash-merged execution lanes) landed without registry rows or archive-license audit notes. The debt is invisible while the session-start base stays current, and re-fires as hard findings whenever a later done run re-covers those commits through a stale base.

## Suggested fix

One registry backfill pass over the wave: add rows (or archive-license audit notes) for the 64 unregistered completed-history files, license the 16 re-fragged moves, and clear the 9 stale standing-override audit notes whose licensed writes landed long ago. Re-run `validate` until the unregistered warn count returns to the standing baseline.

## Acceptance

- `doc_registry_validator.py validate` reports zero unregistered completed-history files dated 09-08 through 09-16.
- A done run with a deliberately stale session base re-covering those commits reports zero hard findings.

## Closure (2026-09-19, P13 Task 8)

Backfill landed in `docs/maintenance/document-registry.md` (commit 347ee78c + the r1 tail commit). Measured evidence:

- Before (authoring baseline drift re-derived at execution): 73 warns / 206 rows; 63 unregistered completed-history files dated in the wave 2026-09-08..09-16 (51 backlog + 12 plans), 10 more dated 09-17/09-18.
- Rows added: the 63 wave files in the existing backfill shape, plus the 10-file 09-17/09-18 tail (archived 2026-09-19 via consolidation commits 7baa8ce1/ef8a6408) after the stale-base witness surfaced them as hard findings; 4 new collided base names appended to the header scheme (7 collision-derived row identities).
- Stale standing-override audit notes cleared (11, each verified landed via git log before clearing): document-ownership-and-archive-lifecycle (7dcdf6c5), agent-agnostic-plan-prose-accuracy-residuals, execute-plan-runtime-r4/r5/r6-deferred-findings, runtime-hermeticity-witness-gaps (08570560), rfc-design-create-mode-identity-header-wiring (3ab1b364), execute-plan-runtime-residuals-recert-nonconvergence, vrs-quotepath-pin-vs-worktree-entries-reuse (c188b396), and 2 more cleared in the tail pass. Kept deliberately fresh: maintenance-scheduler-liveness (licensed writes landed same-day; not "landed long ago").
- Retroactive overrides minted (2, `user-approved 2026-09-19:` format, both real landed commits verified by diff inspection): backlog-gate-hardening (fd77a91a body edit), plans-facts-do-not-resolve-design-ambiguity (1230abc1 errata block).
- After: `doc_registry_validator.py validate` = 0 hard findings, 0 warns, 279 rows, exit 0; zero unregistered wave files.
- Stale-base acceptance witness: `docs/tmp/done-session/session-start-head.txt` pointed at pre-wave sha 5f6eee4; check-writes union (`status --porcelain` + `diff --name-status --no-renames BASE..HEAD`, 415 paths) = `check-writes: 0 unprotected immutable write(s) of 415 path(s), 0 registry audit-note defect(s)`, zero hard findings; base file restored to the then-HEAD (9ee7ece4).
