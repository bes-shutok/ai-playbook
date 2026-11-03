# Backlog: rebuild the candidate-root snapshot inside the citation-hold span
Cluster: docs/history/backlog/2026-11-02-docs-tmp-drain-hold-reacquisition.md (same-day review family)

Status: open
Priority: medium (promotion gate; MUST close before `docs_tmp_drain_arms` promotes past `report-only`)
Severity: Medium
Origin: code review r1 of plan `docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md` (risk, concurrency#stale-worktree-snapshot-across-hold-span).
- **Cluster:** docs/history/backlog/2026-11-02-docs-tmp-drain-hold-reacquisition.md

## Problem

The candidate-root snapshot (`_snapshot_candidate_checkout_roots`) is built outside the citation-hold merge-lock span, while `_closeout_reference_hold` re-parses the worktree registration fresh inside the lock but uses it only for manifest liveness. A worktree registered between the snapshot and the drain decision is invisible to the live-root fence: the dead-root arm can drain a now-live root's marker and the proof-family arm can classify a just-reregistered worktree as unregistered and drain a peer session's proof family.

## Direction

Feed the hold's fresh registration parse back into `_marker_root_matches_candidates` and `_proof_family_session_decision` (or rebuild the snapshot inside the lock span), and add a registration-freshness term to `session_remains_terminal_discardable`. Report-only posture never unlinks, so the default posture is safe today; this row gates the promotion.
