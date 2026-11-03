# Backlog: certification gates report one defect at a time and mint a review round per violation

Status: covered (docs/history/plans/2026-11-03-certification-gates-full-violation-reporting.md)
Priority: high
Class: fix-class
Origin class: learn Step 1.8 skills-corpus capture (2026-11-03 session-pattern harvest over the 2026-11-02 07:00 to 2026-11-03 07:15 UTC window)
Added: 2026-11-03

## Observed versus expected

Multiple gates in the plan certification loop stop at their first violation or reject legitimate caller-produced record shapes, so each defect costs a full fix-then-rerun round:

- Readiness and certification validators surfaced failures one at a time across reviewed runs (in-window landing subjects certify r2 through r8; one run still carried blocking findings at r7, and one certification worker died on a turn failure with the round standing).
- The review staging validator's run-id chain rule ("run_id cannot change after r1") rejected coordinator-supplied identifiers in four of seven reviewed sessions; every later-round review worker independently rediscovers the accepted form by trial.
- Closed enums and filename rules forced record-side adaptations in one round of a reviewed session: a "focused-re-review" round kind absent from the enum, a "below-threshold" discard code outside the closed set, an identity-token filename rename after the fact, and a missing certification seal entry patched manually so the gate could pass.
- A pinned change-set expectation anchored to a moving ref was re-falsified across three rounds after its first fold fixed only the scoping half (lesson 379's own witness).
- The plan delta classifier refused reclassification on 22 unclassified hunks, converting a mechanical corrections row into a fresh five-worker round.
- A byte cap sat at 505 of 512 after a fold, so any later fold re-trips the executability gate (lesson 374's family, sixth witness in window).

Expected: one gate pass enumerates every violation with its evidence before exiting non-zero; legitimate later-round record shapes are accepted or named in the report; an authoring-time preflight runs every pinned validation command once before the first review round.

## Reproduction evidence (trimmed)

- Session-scan receipts (2026-11-03 harvest subagent outputs over the window's session records): four of seven small sessions hit the run-id rejection; one session's later round lists four record-side adaptations in a single round; a plan was mechanically refused at r3 on the byte cap after the prior fold missed a second over-cap item.
- Corpus witnesses in window: lessons 321 and 376 fourth witness (commit 21f2cd2ce), lesson 374 (commit bf6e14189), lesson 379 (commit 981c62cc3 lineage).
- In-window landing subjects carrying multi-round certification churn: a8116afe2 (certified r3), e42a0ac78 (r3 after r1 full-fold 6, r2 fold 4), ec4e61e39 (r5 ready=yes), plus an r8-round run recorded standing at r7 blocking.

## Suspected root area

scripts/plan_readiness.py and the review staging validator's first-failure reporting loop, the run-id chain and enum contracts in the review staging validator, the plan delta classifier's unclassified-hunk default, and the plans/review-staging skill text's preflight duty (authoring-time execution of pinned validation commands, generalizing lesson 374 beyond byte balance).

## Fix shape (arms, priced at plan time)

(1) Fail-all-at-once: each gate enumerates its full violation set with per-violation evidence before exit. (2) Contract naming: a rejected record shape gets a report line naming the accepted forms (run-id chain, round-kind enum, discard codes). (3) Authoring-time preflight: the plans skill's validation-commands assembly runs every pinned gate once before the first review round. (4) Classifier corrections-row eligibility review. Arms are separable and a plan prices them independently; arm 1 is a reporting change to existing gates, not a new gate, so the machinery admission protocol prices it as a guardrail-shape change, not machinery growth.
