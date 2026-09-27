# Backlog: cap-closure diagnostics and docs (decode reason under-enumerates; loop rule 16 dual-list ambiguity)

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: low
Workflow: backlog
Class: certification machinery
Driving force: observability (primary), docs (secondary)

## Problem

Two low findings from the Phase 3 code review. (1) The shared plan-bytes decode's failure reason still names only "(trailer, Review Scope, and/or plan ownership)" although its trigger set gained the cap-closure declaration; a declaration-routed decode failure misattributes the trigger. Reword (or derive the text from the fired flags) and update the pinned arm. (2) The plans skill now has two numbered rule lists and the new cap-closure loop rule 16 collides with authoring rule 16; six completed plans cite "plans rule 16" meaning stage-scoped interim validation, and bare-number citations now resolve ambiguously. Do not renumber (the skill's internal rule references would break); add a one-line scope note above one list requiring cross-references to name the list, and cite the list explicitly going forward.

## Suggested fix

Both are one-line-ish edits in a follow-up docs/scripts pass.

## Environment

Phase 3 code-review r1 (2026-09-27), design-simplicity + risk + contract-docs workers; deferred per the backlog-deferral default.
