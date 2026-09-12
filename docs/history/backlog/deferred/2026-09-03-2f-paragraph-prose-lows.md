# Backlog: 2f prescribed-paragraph prose Lows (code-review r3, 6 findings)

Status: backlog
Workflow: backlog (promote via `plans` skill as a one-clause rider on the next pass touching the residue-pass plan's Task 2f text)
Source: docs/reviews/2026-09-02-r5-residuals-fixes-code-review-r3.md (certification round, zero blocking, ready to exit)

## Problem

Six Low, non-blocking prose-clarity findings, all in the prescribed Task 2f first paragraph of `docs/plans/2026-09-02-phase3-residue-pass.md` (~line 236-240):

1. (r3-ds-1 + R3-RISK-1) "Such an uncounted re-entry advances neither..." dangles: the preceding sentence's subject is the counted re-entry, so "Such" mis-binds; replace with e.g. "An uncounted re-entry of the first kind advances neither...".
2. (r3-ds-2) "continues the same round's `-r<N>` staging doc" appears in both the counted-re-entry sentence and the sentence before it; the later sentence could carry only its new facts (no new round, no counter reset).
3. (r3-ds-3) The counted/uncounted labels name the wrong distinction (both kinds increment `re_entry_count`; the real distinction is `review_round` advancement).
4. (CD-F1) The r5-residuals plan's Task 5 Superseded note records the re-folded sentences but not the synced `$EP` pin strings; extend it with "the two `$EP` pin strings were synced to the re-folded sentence spans (commit 0b32d08)".
5. (R3-RISK-2) "(reset each round)" never states the reset's positive firing condition; make it "(reset only when a new round starts, i.e. at the next `-r<N>` staging doc)".

## Location

- `docs/plans/2026-09-02-phase3-residue-pass.md` (prescribed Task 2f first paragraph; Authoring-time proof pin spans must be re-derived in the same edit if wording changes)
- `docs/plans/2026-09-02-r5-residuals-fixes.md` (Task 5 Superseded note extension only)

Warning: this paragraph regenerated wording findings in every review round (r1-r3). If promoted, fold all six clauses in ONE edit and re-run the r5-residuals plan's Validation block plus a mechanical pin-vs-prescription audit before review.
