# Backlog: registry backfill for the 2026-09-08 to 09-16 archive-move wave

Status: open
Priority: medium

Workflow: backlog
Source: done Step 2.648 on 2026-09-18: `doc_registry_validator.py validate` reported 64 unregistered completed-history files and `check-writes` reported 16 unprotected immutable writes once a stale session-start base re-covered the 09-14 to 09-16 squash-merge archive moves (witnessed during the fixture-hygiene done run).

## The gap, precisely

The 09-08 to 09-16 wave of archive moves (backlog items to `completed/`, plans to `completed/`, from the squash-merged execution lanes) landed without registry rows or archive-license audit notes. The debt is invisible while the session-start base stays current, and re-fires as hard findings whenever a later done run re-covers those commits through a stale base.

## Suggested fix

One registry backfill pass over the wave: add rows (or archive-license audit notes) for the 64 unregistered completed-history files, license the 16 re-fragged moves, and clear the 9 stale standing-override audit notes whose licensed writes landed long ago. Re-run `validate` until the unregistered warn count returns to the standing baseline.

## Acceptance

- `doc_registry_validator.py validate` reports zero unregistered completed-history files dated 09-08 through 09-16.
- A done run with a deliberately stale session base re-covering those commits reports zero hard findings.
