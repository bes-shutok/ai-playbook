# Backlog: parallel review-address workers grouped by file affinity

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-14
Class: execute-plan Phase 3 wall-clock reduction
Origin: wall-clock analysis of the execute-plan run of docs/plans/2026-09-13-budget-gate-quota-fixes.md (2026-09-13/14). Phase 1 (six serial tasks) took ~1.5 h; the Phase 3 review/fix loop consumed ~4.5 h and counting across four rounds. Within a round the five-lens review panel already runs in parallel (17-33 min), but the per-round tail is serial: synthesis, triage, a SINGLE receiving-review address worker, then done. Measured address passes: r1 38 min folding 14 findings across 8 files, r2 ~20 min, r3 ~12 min. Staging docs: docs/reviews/2026-09-13-budget-gate-quota-fixes-code-review-r1.md through -r4.md.

## Problem

The dominant per-round cost of Phase 3 is the single address worker that folds every accepted finding regardless of how many distinct files they touch. Round wall clock is therefore bounded by one worker's serial edit-verify cycle over the widest file spread in the round, while the panel that precedes it is already parallel. On the origin run, the address-plus-done tail was roughly 2-3x the panel time in three of four rounds.

## Proposed change

Allow the execute-plan parent to fan the Step 3.3 address pass across 2-3 receiving-review workers grouped by file affinity:

- Findings that share any file go to the same worker; workers receive pairwise-disjoint file sets, so parallel edits cannot conflict.
- Each worker runs a standard receiving-review pass over its finding subset only: implement fixes, per-finding verification, scope-limited validation re-run.
- The parent merges worker results: updates the staging doc triage fields itself, re-runs the FULL Validation Commands block once after all workers return, and keeps commit discipline unchanged: exactly one address commit per round, launched as the usual per-round done.

Fallback: when no disjoint grouping exists (all findings share files), run one worker as today. Single-worker behavior is the default when fan-out is not clearly beneficial.

## Contract updates required

- `agents/skills/execute-plan/SKILL.md` Step 3.3: the fan-out option, the deterministic grouping rule, the merge-and-single-commit rule, and per-worker log paths.
- `receiving-review`: a note that an orchestrated run may hand the pass a finding subset plus its allowed files; per-finding Fix/Triage semantics unchanged.
- `review-staging` and the staging validator: sidecar accounting when multiple address workers contribute (per-worker Low budgets, overflow, witness-ledger attribution per worker).
- `subagent-prompts.md`: an address-worker template variant taking the subset, the allowed files, and the log path.

## Guardrails

- Address workers never commit; the parent commits once per round.
- Never split same-file findings across workers; grouping must be derivable from the staging doc's per-finding file data (deterministic, not judgment).
- Cap fan-out at three workers to bound merge and verification overhead.
- A failed or timed-out worker is retried or re-run on its subset only; other workers' accepted results stand.

## Acceptance criteria

1. Grouping is computed deterministically from staging-doc finding data and recorded in the session manifest.
2. One address commit per round; working tree clean after the round's done.
3. The full Validation Commands block passes in a single parent run after the merge.
4. One append-only log per fan-out worker; staging triage fields complete for every finding.
5. Single-worker fallback when disjoint grouping is impossible; no behavior change for single-finding or single-file rounds.
6. Measured round wall-clock on a mixed-file round beats the single-worker baseline; record before/after on the first run after implementation.

## Why not fixed now

The origin run was mid-Phase-3 when captured; changing Step 3.3 mid-run is impossible, and the change touches four skill contracts at once, which deserves its own authored and reviewed plan.

## When to act

Before the next multi-finding execute-plan run. Natural companion to 2026-09-14-execute-plan-batched-implement-launch.md; the two fit one execution-efficiency plan.

Related: 2026-09-14-review-runner-bounded-timeout-fallback.md (per-worker bounded timeouts are what keep each fan-out address worker accountable).
