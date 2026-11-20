# Backlog: operator-directed loss plan leaves two flag partitions without a witness cell
Cluster: docs/history/backlog/2026-11-09-loss-flag-coverage-suggestions.md

Status: open
Priority: low
Class: fix-class
Origin class: self-serving
Added: 2026-11-09, certification-round residuals of the operator-directed loss plan review
Driving force: reliability

## Problem

The certified plan docs/history/plans/2026-11-09-interrupted-manifest-gitignored-witness-gap.md states two flag behaviors that no planned Task 1 cell drives, so a plausible wrong implementation passes the whole planned cell set:

- Reprint and racer arms: the plan says the flag is ignored and the existing record reprinted on an already-dispositioned manifest and when a concurrent stamp wins the compare-and-swap. An implementation that evaluates the flag and prints its unused notice before the pre-checks passes every planned cell while printing the notice on those arms.
- Mixed manifest: the loss reason applies when at least one deliverable is note-only. No planned cell mixes one tracked-resolved and one note-only deliverable under the flag, so an implementation that requires every deliverable to be note-only passes every planned cell while stamping `work-verified-landed` over lost work.

## Exact location

- `scripts/test_done_sweep_gates_lib.py`: the disposition-manifest cells Task 1 of the plan above adds.
- `scripts/done_sweep_gates_lib.py`: `_cmd_disposition_manifest` reprint arm, `_stamp_disposition_record_with_cas` racer branch, and the note-only collector the plan adds.

## Suggested fix

During the plan's execution, add three cells beside Task 1's flag-bearing cells: a flagged re-run on an already-dispositioned manifest and a flagged invocation that loses the compare-and-swap race (each expecting exit 0, the existing record reprinted, no unused-notice line, the manifest byte-identical), and a flagged invocation on a manifest owning one HEAD-resolvable `owned_paths` entry plus one note-only `owned_plan_paths` entry (expecting the `operator-directed-loss` reason and no notice). All three are RED until the flag exists.

## Severity and source

Medium and Low, non-blocking: the r3 certification record `.ai-playbook/reviews/2026-11-09-plan-review-interrupted-manifest-gitignored-witness-gap-pba23a018-r3.md`, findings F1 (reprint and racer arms) and F2 (mixed manifest), testing worker. Capture hygiene check: public hygiene scan run over the uncommitted draft before the authoring landing.

## Why not fixed now

Certification-round non-blocking findings never force a re-round or a plan fold (review-staging certification-residual routing); the cells belong to the plan's execution, which has not started.

Dedup probe: searched the open backlog corpus (filenames and Problem bodies) for "operator-directed-loss", "reprint arm", "racer", and "mixed manifest"; no open item matches. The nearest item is the plan's own origin row docs/history/backlog/2026-11-02-interrupted-manifest-gitignored-witness-gap.md, which owns the arm's design, not its witness cells; distinct, no merge.
