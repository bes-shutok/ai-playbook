# Backlog: reverse-squash guard binary-record grammar lacks a log-producer witness

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-25
Class: test witness gap (review residual r6 F1 from the restaging-reverse-squash-guard plan authoring; the rule text itself is complete, only the fixture is single-sided)

## Problem statement

The certified plan (docs/plans/2026-09-25-restaging-reverse-squash-guard.md, landed main e7c3a95d) commits both of the detector's parse producers to the binary-record dash-placeholder rule (dash count columns contribute the path with no count pair: never mirrors, still egress-tested), but the plan's only binary witness drives a staged binary through the check-staged producer. An implementation that handles dashes in the check-staged numstat grammar yet crashes on the log grammar's identical dash rows (`git log --format=%H --numstat -z -M` records for landed binary commits inside the 30-day/2000-commit scan window) stays green while every real guard run parses such rows, and the uncaught interpreter exit reads as an exit-1 refusal that loops the done arm's unstage-and-rebuild remediation.

## Suggested fix

One fixture extension in `scripts/test_reverse_squash_guard.py`: a scratch fixture whose landed history carries a binary commit, then a benign staged edit, expecting `check-staged` exit 0 (the log-grammar dash rows parse without error on the positive path).

## Severity and source reference

- Severity: Low (defense-in-depth witness; the grammar rule itself is pinned in the certified plan text).
- Source: r6 risk worker finding on the final bytes (docs/reviews/2026-09-25-plan-review-restaging-reverse-squash-guard-r6.md, F1, verified against both producers in scratch repos).

## Why not fixed now

The plan bytes were frozen at r6 certification (digest 417eea6d28fa7f680b759afe01c999c1501e0db9d2d69d44897829046f3fca8a); a post-certification byte change would force a fresh certification round for a one-line fixture addition.
