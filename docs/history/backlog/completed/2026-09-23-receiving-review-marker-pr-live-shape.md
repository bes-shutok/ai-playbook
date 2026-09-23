# Backlog: receiving-review marker `pr` shape vs review_thread_gate --live

- Priority: high
- Status: open
- Workflow: backlog
- Scope: `receiving-review` marker writer + `scripts/review_thread_gate.py` live fetch
- Owner: playbook maintenance
- Source: done pre-docs review-thread closure (2026-09-23); marker carried numeric `pr` plus separate `repo`, while `--live` requires `owner/repo#N`
- Why not fixed now: dispositions already closed the gate via canned inventory; schema alignment needs a coordinated writer+gate change and fixture update, not a session-side patch
- Driving force: workflow reliability
- capture hygiene: pending scan

## Problem

`review_thread_gate.py --live` fails with `marker pr '63' is not owner/repo#N; cannot fetch live` when the marker uses the receiving-review session shape (`"pr": 63`, `"repo": "owner/name"`). The gate docstring canonical shape is `"pr": "owner/repo#N"`. Agents must fall back to `gh api graphql` + `--inventory`, which is easy to miss and blocks done when network-only `--live` is attempted.

## Expected

One agreed marker schema: either the writer always stores `pr` as `owner/repo#N`, or `--live` accepts numeric `pr` plus `repo` / `url`. Keep canned `--inventory` working. Add a unit covering both shapes.

## Skill / step

- Skill: `agents/skills/receiving-review/SKILL.md` (marker duty / schema)
- Script: `scripts/review_thread_gate.py` (`--live` parse)

## Suspected root area

Schema drift between marker writer and gate live path; Fix-risk / done docs cite `--live` without mentioning the dual shape.
