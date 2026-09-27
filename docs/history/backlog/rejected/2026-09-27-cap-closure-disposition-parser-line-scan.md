# Backlog: cap-closure disposition parser scans whole ledger lines, so incidental vocabulary words shadow or phantom dispositions

Status: rejected (2026-09-28; cap-closure machinery polish; the 2026-09-28 metrics-first revision defers cap-closure retirement to an evidence-cited later decision, but the family stays rejected as unwitnessed machinery polish; no witnessed user-facing failure)
Priority: medium
Workflow: backlog
Class: certification machinery
Driving force: correctness (primary), reliability (secondary)

## Problem

`_cap_closure_entry_disposition` (scripts/plan_readiness.py:387-403) falls back to a bare-word scan of the ENTIRE ledger line when no explicit `disposition:` label exists. Hyphens are word boundaries, so a pattern slug or entry prose containing "accepted"/"folded" shadows the entry's real disposition. Live-verified both directions on the landed code: (false accept) an all-folded ledger whose slug contains "accepted" plus a false `residuals: 1` passes the count tie that the plan pins; (false reject) an honest all-folded ledger with such a slug and truthful `residuals: 0` fails with a count mismatch, stranding the landing path this plan unblocked until a reword plus re-bind. Negated prose ("no findings were accepted") also tallies as accepted. The suite never exercises the bare-word path (all fixtures use the label form).

## Suggested fix

Anchor the parse to the disposition slot: require the explicit `disposition(s)` label with a mandatory separator, or search the vocabulary only in text after the entry's pattern token / first `: ` separator; treat only lines matching the `- <pattern>` list grammar as disposition-bearing; pin both directions with tests (all-folded ledger whose slug contains "accepted" tallies 0; un-dispositioned entry whose slug contains "accepted" under-reports).

## Environment

Phase 3 code-review r1 of the certification-machinery execution (2026-09-27); correctness-completeness (Medium, live-verified) + risk (premortem phantom-word persona); deferred per the backlog-deferral default.
