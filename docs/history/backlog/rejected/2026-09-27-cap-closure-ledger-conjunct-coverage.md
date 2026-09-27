# Backlog: cap-closure ledger grammar gaps (hard-wrapped entries false-reject; overflow rows unconjunct)

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: reliability (primary), completeness (secondary)

## Problem

Two coverage gaps in the cap-closure terminal-state probe (scripts/plan_readiness.py). (1) Entries are individual non-blank lines and the conjunct requires pattern and disposition on the SAME line, so a hard-wrapped ledger entry fails with the misleading under-reporting reason (live-verified); nothing documents the single-line entry grammar. Join continuation lines before parsing, or document the grammar in the review-staging subsection. (2) The staged-pattern set is built solely from the sidecar `findings` array; `overflow[]` rows (real non-blocking findings over the presentation budget) need not appear in the ledger, so the review-staging contract "every staged finding of the cap round is listed" is unmet for them. Extend the pattern set with overflow rows (they carry canonical patterns) or scope the contract explicitly to the findings array.

## Suggested fix

Either code change is small; pair with a witness arm each.

## Environment

Phase 3 code-review r1 (2026-09-27), correctness-completeness and risk workers; deferred per the backlog-deferral default.
