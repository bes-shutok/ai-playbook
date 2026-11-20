# Backlog: the byte-budget gate is advisory while review lenses treat its breaches as blocking

- **Filed:** 2026-11-10, learn Step 1.8 capture from the 24h session-pattern harvest (playbook repo)
- **Status:** covered (docs/history/plans/completed/2026-11-11-byte-budget-posture-alignment.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed posture divergence
- **Class:** fix-class
- **Skill/step:** `scripts/skill_text_budget.py` (warning-only posture) versus the review-plan lens rules and the root repository guidelines' skill-text anti-growth rules
- **Cluster:** docs/history/backlog/2026-11-10-review-fold-output-prevalidation.md (same review-round cost surface); docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md (same advisory-signal surface)
- **Source reference:** the session-rollout-retention-postmortem-evidence exec run: its r1 lens 1 declared the decisions.md over-cap breach blocking (not-ready), a fold fixed it, and r2 verified; the same gate run exits 0 by design ("breach lines never move the exit"); the anti-growth guidelines bind the same duty at review time
- **Witness addendum (2026-11-11, 24h harvest):** the operative-file-read-budget-gate landing (3f8dc5d1f) promoted the gate to blocking with single-read calibrated caps, landing this row's promotion arm; the remaining scope is the lens/authoring-side alignment, and the frozen `byte-budget-posture-alignment` PLAN entry (frozen 00:56, after the 00:34 landing) must re-derive its authoring against the landed posture before writing
- **Why not fixed now:** harvest-only session; the posture is pinned gate and lens text whose alignment belongs to its own authoring lane
- **Dedup probe:** the `stop-boundary-skill-text-growth-trim-deferral` EXEC entry owns trim deferral; lesson #421 owns the gate's two-class taxonomy (blocking ceiling class, advisory sub-ceiling growth watch); this row owns which surface enforces the duty, not the trim itself; no merge

## Problem

The mechanical gate and the review lens disagree about the same signal: the lens spends review capacity declaring a breach blocking while the gate records it advisory. The corpus holds two sources of truth for one duty, and every breach instance re-litigates the posture at review time instead of consuming one decided answer.

## Expected

One decided posture: either the gate emits a machine-diffable per-change breach signal (did this landing grow a capped file past its cap) that lens rules consume as the blocking input, or the lens stands down to advisory for sub-ceiling breaches and the anti-growth guideline cites the gate as its instrument. Any promotion of the gate to blocking carries the machinery admission protocol's four fields in the emitted entry.

## Suggested fix

Decision row for an authoring lane: run the admission test on the promotion arm, pick the posture, then align the script's output contract and the lens text in one change with the byte-budget plan's taxonomy updated where the decision rewrites it.
