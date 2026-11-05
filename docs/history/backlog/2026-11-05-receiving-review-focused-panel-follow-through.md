Status: open
Priority: high
Consumer urgency: This affects consumer projects that use the shared review workflow; do not park or defer it as formal-hardening for the skills repository alone.
Class: fix-class
Origin class: consumer-feedback (company)

# Review reception does not make the final focused panel pass explicit

## Problem

`agents/skills/receiving-review/SKILL.md` handles evaluating and implementing review feedback, but does not clearly connect completed review fixes to the focused code-review panel over the final changed diff. In a recent review-fix session, the user had to ask whether the focused panel had been run. The omission leaves uncertainty about whether the edits received the expected fresh review after the fix.

Expected: after applying review fixes, the worker invokes the existing focused-panel workflow on the exact final diff unless that same diff has already received a qualifying panel review in the current cycle. This should be a short pointer to the existing panel skill, not a duplicate panel procedure or an extra review round when one already happened.

## Exact location

- `agents/skills/receiving-review/SKILL.md`, feedback-fix workflow and completion criteria.
- `agents/skills/doing-code-review/SKILL.md`, existing focused-panel procedure.

## Suggested fix

Add a concise handoff to the existing focused-panel procedure at the point review fixes are complete. Reuse the current workflow's freshness and completion rules so this does not add redundant rounds or another review gate.

## Severity and source

Severity: High; the user had to intervene to confirm the final changes received the expected focused review.
Source: user correction in an anonymized consumer-project review-fix session, 2026-11-05; capture hygiene: `scan-public-hygiene --files` pass.

## Why not fixed now

This request is for incident analysis and backlog capture. The handoff should be compared with the existing code-review panel procedure before editing either skill.

## Driving force

reliability + maintainability

## Dedup probe

Searched open backlog names and Problem bodies for `focused panel`, `review reception`, `final review`, and `doing-code-review`. `docs/history/backlog/2026-11-05-doing-code-review-worker-return-persistence.md` covers worker finding/report persistence, not invoking the panel after review fixes. `docs/history/backlog/2026-10-30-doing-code-review-staging-doc-scaffold-pointer.md` concerns staging-document setup, not the missing follow-through handoff. No open item covers this failure mode.
