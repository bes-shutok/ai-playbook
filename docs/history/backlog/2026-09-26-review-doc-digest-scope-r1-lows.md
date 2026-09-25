# Backlog: review-doc digest-scope execution r1 deferred Lows

Status: open
Priority: low
Date filed: 2026-09-26
Origin: execute-plan Phase 3 round r1 of docs/plans/completed/2026-09-04-review-doc-digest-scope-fix.md (landed with the execution squash); two Low findings, echo-confirmed, deferred as out of the doc-only plan's scope.

## Finding 1: concatenation order is per-round deterministic only

`agents/skills/review-confluence-doc/SKILL.md` Step 5 item 4 says the scratch file is "concatenated in the order Step 2 fetched them", but Step 2 pins no child-page ordering rule and no join-separator convention, so byte-level digest stability across separate review rounds of the same document depends on fetch-order stability. The gate is a per-run self-attestation, so no misattribution is possible (verified live in r1: parent-only digest hard-fails), and review-staging's digest-mismatch path conservatively forces a new round. Fix idea: pin a canonical child ordering (e.g. the Step 2 fetch listing order, which it already is) and document it explicitly, or accept and note the per-round scoping in the guarantee sentence.

## Finding 2: two new clauses are pinned only by negated greps

The plan's Validation Commands cover the Step 4.7 item 1 phrase ("exact concatenated reviewed-content bytes") and the Integration-Points phrase ("full reviewed-content scratch file") only via the forbidden-string grep for "fetched page bytes". A revert is caught, but a future edit rewording either clause to a third phrasing passes silently. Fix idea: add one positive grep per clause to the maintenance pins suite.
