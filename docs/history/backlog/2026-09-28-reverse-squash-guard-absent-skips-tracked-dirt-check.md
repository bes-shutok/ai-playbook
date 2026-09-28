Status: open
Priority: low
Workflow: backlog
Class: fail-open degradation in a fail-closed deletion gate (tool-absence path skips the check instead of standing down)
Driving force: correctness

# Reverse-squash guard-absent path silently skips the tracked-dirt check in the canonical deletion gate

**Exact location:** `agents/skills/execute-plan/SKILL.md`, the Worktree-first standard section's "Tracked-dirt inversion check (between migration and removal)" recipe, the `if [ -z "$GUARD" ]; then echo "reverse-squash guard absent; tracked-dirt check skipped"` branch.

## Problem

The tracked-dirt inversion check gates worktree removal and manual transplant decisions: a tracked diff in a source worktree must pass the reverse-squash guard before any removal decision, and a guard refusal keeps the worktree. When the guard script is absent (no repo-local `scripts/reverse_squash_guard.py` and no deployed home copy), the recipe prints "reverse-squash guard absent; tracked-dirt check skipped" and falls through, so the deletion gate silently degrades to no check exactly where the corpus's own convention is fail-closed (a missing validator is a stop-and-report condition everywhere else in this skill, for example the Step 0.5 readiness gate's deployment-gap signature and the closeout migration's refusal). A consumer repo without the deployed copy removes worktrees with unverified tracked dirt and never learns the check did not run.

## Observed versus expected

- Observed: guard absence prints a skip note and continues toward removal with the tracked diff unexamined.
- Expected: a missing guard in a fail-closed gate stops the removal path and reports (keep the worktree, name the missing script), mirroring the readiness gate's missing-validator treatment; at minimum the skip must be surfaced as a report duty, never a silent fall-through.

## Suggested fix

Change the guard-absent branch to the stop-and-report shape (echo the missing-script condition and exit non-zero so the removal is refused), or gate the branch on an explicit recorded decision that the repo runs without the guard; keep the two-tier resolution arms unchanged.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r1.md, round r1, finding F15 (deferred; Low). Capture hygiene: scan-public-hygiene --files pass (see execution log review-r1-receiving-review.log.md). Why not fixed now: deferred by the round's triage (changing the branch's exit semantics alters the recipe's behavior beyond this round's prose-fix scope and deserves its own failure-direction evidence), captured as durable backlog per receiving-review Backlog capture.

Dedup probe: searched the open backlog corpus for "reverse squash guard", "guard absent", "tracked dirt"; no existing item owns the guard-absent path; no overlap.

Origin class: self-serving
