Status: open
Priority: low
Workflow: backlog
Class: validation-gate pin coverage (a pins-suite re-key narrowed a pinned span's semantic scope)
Driving force: correctness

# S15 re-key narrowed the pinned gate span (done-lock keying mechanic unpinned)

**Exact location:** `scripts/check_maintenance_pins.sh` pin "per-run pre-work gate span (re-keyed 2026-09-28; was P57 S15)" (the pin grepping `the run's own per-worktree done lock is free` in `agents/skills/maintenance/prompt-templates.md`), protecting the execution blueprint's per-run pre-work gate paragraph.

## Problem

The 2026-09-28 worktree-first consolidation (plan `docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md` Task 4, commit 5cb09eb1) re-keyed the P57 S15 pin from the old span `the run's own done lock is free (done locks are keyed per-worktree` to the shorter rewritten tail `the run's own per-worktree done lock is free`. The old pinned span carried the done-lock keying mechanic ("done locks are keyed per-worktree"); the re-keyed span pins only the stand-down clause. A wholesale loss or rewrite of the keying-mechanic phrasing in that gate region no longer fails the suite, so the invariant the original S15 pin protected (the gate names its keying basis) is now unpinned: the pin suite would stay green while the prose drifts.

## Observed versus expected

- Observed: the re-keyed pin fails only when the stand-down clause tail disappears; deleting the keying-mechanic phrasing from the gate paragraph leaves the suite green.
- Expected: every span whose deletion would silently change the gate's documented semantics stays pinned, per the suite's own convention that a re-key preserves the old pin's protection scope (the suite's freeze-literal comments state a wording change to a pinned span must reconcile pin and text in the same edit; the re-key narrowed the protected semantics instead of preserving them).

## Suggested fix

Extend the re-keyed pin (or add a companion presence pin) so the execution blueprint's keying phrase (`done locks are keyed per-worktree on --show-toplevel`, present in the execution body's done-skill sentence) is itself count-gated, restoring the keying-mechanic coverage the old S15 span carried.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r1.md, round r1, finding F12 (deferred; Low). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r1-receiving-review.log.md). Why not fixed now: deferred by the round's triage (fix-risk bound; the pin suite is green as re-keyed and the miss is a coverage narrowing, not a live gate defect), captured as durable backlog per receiving-review Backlog capture.

Dedup probe: searched the open backlog corpus for "S15", "per-worktree done lock pin", "pins suite span narrowing"; nearest item is docs/history/backlog/2026-09-27-em-dash-whole-file-mode-frozen-span-trip.md (gate-mode structure, different surface); no overlap.

Origin class: self-serving
