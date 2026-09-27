# Backlog: P50 cross-reference and sibling-record reconciliation

- Status: rejected (2026-09-27; archived-record edits plus a new standing sweep without a live failure)

Driving force: code-quality

Captured 2026-09-24 during the P50 execution (Phase 3 r1 contract-docs + risk lenses; zero blocking; deferred).

- docs/history/backlog/2026-09-24-plans-watcher-schedule-fresh-install-cas-block.md (open, landed on main before the P50 branch base) records the same fresh-state plans-watcher-schedule blockage P50 fixed but with a wrong root theory ("CAS wants a pre-existing generation"); the landed test proves a fresh state schedules with the documented payload and the true cause was the missing plan_slug. Annotate the item with a Disposition line pointing at the P50 fix so no future processor reworks the healthy CAS fence (regression risk to the r3 F7 stale contract).
- docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md:15 cites the old path of durability-review-residuals (moved to completed/ by P50 Task 4); one-line path update.
- Repo-wide class: backlog archive moves orphan old-path references in historical docs (witnessed in docs/plans/completed/2026-09-21-maintenance-turn-self-scheduling-cadence.md and docs/plans/completed/2026-09-22-p36-scheduler-durability-audit.md, frozen historical records; p36 Task 6 precedent accepts). Candidate: a path-stability convention for archive moves or a periodic stale-ref sweep over docs/plans/completed/ and backlog cross-references.
