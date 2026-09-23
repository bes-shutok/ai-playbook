# Backlog: review_thread_gate resolver accepts int-subclass and negative pr

- Priority: low
- Status: open
- Workflow: backlog
- Scope: `scripts/review_thread_gate.py` (`_resolve_live_target` shape-(b) guard)
- Owner: playbook maintenance
- Source: P56 execution review r1 F1 (non-blocking Low; quality#bool-int-pr-passes-digit-gate)
- Driving force: code-quality
- capture hygiene: pending scan

## Problem

`_resolve_live_target`'s shape-(b) guard `isinstance(pr, int)` lets Python int-subclasses (e.g. `True`) and negative ints through the "all digits" gate: `{"pr": true, "repo": "owner/name"}` resolves to PR 1 and `{"pr": -5}` resolves to -5 instead of failing closed.

## Expected

`type(pr) is int and pr >= 0` in shape (b), plus unit cases for `True` and a negative `pr` asserting the error arm.

## Skill / step

- Script: `scripts/review_thread_gate.py` (resolver)
