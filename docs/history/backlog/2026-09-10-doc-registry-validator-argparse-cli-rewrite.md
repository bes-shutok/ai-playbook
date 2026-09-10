# Doc registry validator: hand-rolled CLI parser duplicates argparse behavior

Status: open
Workflow: backlog
Source: docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r1.md (round 1 of docs/plans/2026-09-08-doc-ownership-lifecycle.md, finding F12)

## Problem

The CLI layer of `scripts/doc_registry_validator.py` (`_dispatch`, ~67 lines) is a hand-rolled parser with two duplicated flag loops (pre-subcommand and post-subcommand), an unreachable `elif arg in known_flags` branch, and channel-conflict logic duplicated between `--stdin` and `--diff`. No correctness bug is demonstrated; the cost is maintenance and an unreachable branch that suggests covered cases that are not.

## Location

`scripts/doc_registry_validator.py`, `_dispatch` (around the CLI section).

## Suggested fix

Rewrite the CLI with `argparse` subparsers (`validate`, `check-writes`, `inventory`) and a mutually-exclusive input-channel group (`--stdin` / `--diff`); argparse exits 2 on unknown flags natively, preserving the fail-closed contract pinned by `test_unknown_flag_fails_closed`. Behavior must be unchanged otherwise; the full `--selftest` fixture set is the regression net.

## Severity and source reference

Low (`simplification#shrink`); staging doc path and finding id above.

## Why not fixed now

Deferred in the doc-ownership-lifecycle review r1 fix pass: it is a structural rewrite of a component family that also received five behavioral fixes in the same pass (F2/F3/F5/F9/F16), so folding the rewrite here adds regression risk late in the loop (receiving-review fix-risk triage rule: prefer additive fail-closed fixes over structural rework). Decision by the r1 triage agent per the orchestrator's fix-pointer instruction ("defer to backlog; prefer backlog; classify honestly").
