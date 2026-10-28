# Backlog: the landing critical section runs no prune-audit leg, so a receipt-less entry removal lands when the session skips the documented pre-landing audit

- **Cluster:** docs/history/backlog/2026-10-28-pending-receipt-removal-warning-promotion.md (same prune-audit surface, different arm: that row owns receipt-ledger-line deletion invisibility inside the audit, this row owns the audit not being run by the landing machinery at all); docs/history/backlog/completed/2026-10-22-prune-audit-landing-token-never-resolves.md (the landed-damage founding witness); docs/history/backlog/EXEC-PROMPTS.md EXEC-PROMPTS-PRUNE receipt learn-router-dispatch-pin-step19-heading (landed ec894fff0; the near-miss witness, panel-caught)
- **Filed:** 2026-10-28, learn Step 1.9 over the 2026-10-28 interactive exec session
- **Status:** covered (docs/history/plans/2026-10-28-landing-gate-prune-audit-leg.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** execution-run finding
- **Class:** fix-class

## Problem

Lesson 234's rule requires running `scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>` before landing and requiring `PRUNE-OK`, but the discipline is prose only: the landing critical section's wired gate set (the land-worktree class: check-landing base freshness, check-archive plan egress, tree equality, the parentage gates) includes no prune-audit leg. A branch whose entry-removal commit lacks its receipt lands clean whenever the executing session skips or mis-runs the documented audit. The removal commit in a squash landing is the landing commit itself, immutable once landed, so the post-landing discovery shape has no in-place repair.

Two witnesses bracket the gap:

1. Landed damage (2026-10-23, the founding incident): two ad-hoc log prunes flagged `REMOVED-WITHOUT-WITNESS` after landing; the removal commit was the squash itself and could not be repaired without rewriting landed main (see the completed 2026-10-22 sibling and its lesson family).
2. Near miss (2026-10-28): an ad-hoc landing's entry removal and receipt sat in different commits on the branch; nothing mechanical refused it, and the catch came only because the round's focused review panel ran the live audit at the branch tip (`REMOVED-WITHOUT-WITNESS`, exit 1) and the branch was rebuilt before the landing. A session that trusted its own gate summary without the panel would have landed it.

## Expected behavior

A landing whose branch delta touches a rolling prompt log runs the prune audit over that log inside the landing critical section and refuses on `OUTCOME: fail`, the same way check-landing refuses a stale base; a clean audit prints its `PRUNE-OK` line in the landing receipt. The existing documented discipline (lesson 234) stays the session-side duty; the wired leg is the enforcement backstop, not a replacement.

## Evidence

- `scripts/land_squash.sh` usage text: the land-worktree gate list names check-landing, check-archive, tree equality, and the parentage gates; no prompt-log leg exists.
- The 2026-10-28 near-miss: the panel's live audit at the branch tip printed `REMOVED-WITHOUT-WITNESS` (exit 1) for a branch the session was about to land; after the receipt was folded into the removal commit the same audit printed `PRUNE-OK` (in-commit receipt), so the audit discriminates correctly at pre-landing tips.
- Lesson 234's two witnesses (2026-10-25, 2026-10-28) both show the audit doing its job only when a session or panel remembers to run it.

## Suspected root area

`scripts/land_squash.sh` (the wired gate set) plus `scripts/check_prompt_log_origins.py` invocation plumbing; the audit itself is correct and needs no change.

## Fix shape

Add a wired prune-audit leg to the landing critical section for log-touching branches: when the branch's changed paths include a rolling prompt log, run the audit over that log with the landing's own merge base and fold its outcome into the landing's refusal set and receipt. The fix is a plan-routed change (it edits a guard-bearing path); the ad-hoc arm's denylist excludes it.

## Machinery admission

- Incident: the 2026-10-23 landed-damage pair (repairs recorded beside the completed 2026-10-22 row) and the 2026-10-28 panel-caught near-miss; the class is "a documented pre-landing audit that only fires when a session remembers it".
- Expected catch frequency: every landing whose branch carries a prompt-log entry removal without its receipt; witnessed once as landed damage and once as a pre-landing catch in thirteen days.
- False-positive cost: a landing of a log-touching branch that would have passed the documented manual audit now runs it mechanically; a genuinely red branch refuses until fixed (the bounded repair is the lesson 234 squash-and-recommit, witnessed working). No false positive is known: the audit's classification arms are already production.
- Net growth: this wires an existing mandated check into an existing gate set rather than adding a check; per the Machinery admission protocol the landing still needs the operator's net-growth approval (or a same-change demotion pairing) recorded at dispatch time.
- Sunset/review: review beside the pending-receipt-removal-warning-promotion row's surface touch.
