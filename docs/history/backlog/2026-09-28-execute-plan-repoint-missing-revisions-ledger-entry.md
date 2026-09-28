Status: open
Priority: low
Workflow: backlog
Class: documentation ledger drift (a re-point of a ledgered surface landed without its dated Revisions-ledger entry)
Driving force: docs

# maintenance SKILL.md:319 re-point lacks a dated Revisions-ledger entry

**Exact location:** `agents/skills/maintenance/SKILL.md` ~319, the "Execution-lane concurrency stance (supersession chain)" paragraph (the sentence re-pointing execute-plan Phase 0 to "the `## Worktree-first standard` section in `agents/skills/execute-plan/SKILL.md`"), and the file's `## Revisions` ledger, whose newest entry does not name the re-point.

## Problem

The 2026-09-28 worktree-first consolidation (plan `docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md`) re-pointed the supersession-chain paragraph's execute-plan Phase 0 description to the new canonical worktree-first standard section. The re-point landed, but the maintenance skill's `## Revisions` ledger gained no dated entry recording it, unlike the corpus convention that a substantive rewording of a ledgered surface (here: the supersession chain that future reworks navigate by) registers a dated entry naming the owning plan. A future reader reconciling the ledger against the paragraph sees the newest entry (2026-09-28, the maintenance autonomous pipeline plan) and, since no ledger entry names the worktree-first re-point, still cannot tell from the ledger alone that the stance prose was re-aimed on 2026-09-28.

## Observed versus expected

- Observed: the paragraph names the worktree-first standard section and the Phase 0 dedicated-branch tie, while no `## Revisions` ledger entry (newest: 2026-09-28, the maintenance autonomous pipeline plan) names the worktree-first re-point.
- Expected: the ledger records the re-point with its date and owning plan, so the supersession chain's edit history stays auditable from the ledger alone.

## Suggested fix

Append a dated `## Revisions` entry (or fold the re-point into the next maintenance SKILL.md edit's entry) naming the worktree-first consolidation plan and the re-aimed sentence set.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r1.md, round r1, finding F14 (deferred; Low). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r1-receiving-review.log.md). Why not fixed now: deferred by the round's triage (the ledger entry is additive history prose on a surface outside this round's allowed file set), captured as durable backlog per receiving-review Backlog capture.

Dedup probe: searched the open backlog corpus for "Revisions ledger", "ledger entry missing", "maintenance SKILL.md supersession"; nearest items are review-residual rollups, none owning this surface; no overlap.

Origin class: self-serving
