## rolling-log-write-foreign-staged-refusal

Added: 2026-11-02, self-heal recovery of the operator-directed investigate entry landing blocked three times by the same refusal

Cluster: scripts/done_run.sh (rolling-log pre-stage guard; the transaction mandate lives in the Write boundary rule at the top of docs/history/backlog/PLAN-PROMPTS.md)

Status: covered (docs/history/plans/2026-11-02-rolling-log-write-foreign-staged-remedy.md)

Witness: this session's refusal transcript (three `done_run.sh commit` refusals naming "a staged path outside the declared owned log set"); the recovery disposition and completion witness (the blocked entry landed as 0ec10c5bd through the blob-preserving unstage/restage workaround under explicit operator direction); the guard leg's introduction commit b5c3ad6ca (2026-10-29 window-dispatch hardening landing); the transaction mandate's own plan docs/history/plans/completed/2026-10-25-primary-log-branch-drift-at-commit.md

Dedup probe: docs/history/backlog/2026-10-20-done-run-authorized-restoration-hardening-candidates.md covers restoration authorization inside done runs, and docs/history/backlog/2026-10-25-closeout-skip-record-producer-residuals.md covers skip-record producers; neither covers a foreign staged index entry blocking a primary rolling-log write.

## Problem

The rolling-log pre-stage guard enumerates every path staged against HEAD and refuses the transaction when any lies outside the declared owned set, with no acknowledgment arm and no documented self-service remedy. A peer session's unrelated backlog row sat staged in the shared primary for roughly five hours (its author session quota-dead; the staged blob never changed), blocking a sanctioned monitor-class investigate write three times. The sanctioned responses at refusal time reduced to stand-down or park-for-operator, and the composed entry survived only as a conversational fallback record, which the log's artifact rule does not recognize as durable (no side record under docs/tmp).

The recovery that worked, applied under explicit operator direction: record the staged blob sha, `git restore --staged` the foreign path (worktree bytes untouched), rerun the refused transaction, then `git add` the path back and verify the staged blob sha is byte-identical. The guard itself was never edited or bypassed; it passed on genuinely clean state.

## Expected

A primary rolling-log writer blocked by unrelated staged dirt should have a sanctioned, documented remedy: either the blob-preserving unstage/restage recipe recorded in the log's Write boundary rule (the smallest arm), or a runner acknowledgment arm that names the foreign path and proceeds without staging it (the machinery admission protocol applies to any new arm).

## Suggested investigation and direction

Trace the guard's refusal class against the shared-primary postures it protects (the 2026-10-25 branch-drift plan's incident, the lesson 351 ride-along class), then price the two arms: the documented recipe (no code, operator-gated, reversible, sha-verified) versus a runner acknowledgment flag (new machinery: admission fields, catch frequency, false-positive cost, sunset). State what each arm cannot protect against (a peer that restages mid-transaction; a foreign path whose worktree bytes drift from its staged blob inside the window). Do not weaken the guard's staged-set enumeration and do not add a second ledger.
