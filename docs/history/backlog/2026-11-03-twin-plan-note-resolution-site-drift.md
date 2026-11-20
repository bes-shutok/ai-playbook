# Backlog: twin plan's implementation notes misstate the active-dir resolution site

Status: open
Workflow: backlog
Priority: low
Origin class: self-serving
Class: fix-class
Driving force: consistency

## Problem

The plan `docs/history/plans/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md`'s implementation notes record the directory-exact twin comparison as "the active dir itself resolved at scan_dirs construction", but the landed code resolves the active plans directory at the `_find_covering_citers` call site (hoisted above the per-origin loop in 6ad2291d4). The notes introduce themselves as "decisions recorded, not guesses", so the placement detail should match the code. Behavior is unaffected.

Deferred from the run's code review r1 (record `.ai-playbook/reviews/2026-11-03-coverage-gate-checkpoint-twin-self-exemption-code-review-r1.md`, finding 7, pattern documentation#prose-plan-note-drift): the plan file is the review record's certification anchor, so a post-review plan-byte edit would invalidate the record's source digest and force recertification churn.

## Expected

The implementation-notes parenthetical names the call site, not scan_dirs construction.

## Suggested change

In the plan file (a future plan-update round, or the completion pass of a round that touches the plan for a real reason), replace "the active dir itself resolved at scan_dirs construction" with "the active dir itself resolved at the `_find_covering_citers` call site".

Cluster: docs/history/backlog/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md (same surface; its origin row)
