# Backlog: exec-dispatch-claim-recheck plan carries six non-blocking certification residuals

Status: open
Priority: low
Class: fix-class
Origin class: self-serving
Added: 2026-11-11, certification-round residuals of the exec-dispatch-claim-recheck plan review (r3 focused delta, review record series .ai-playbook/reviews/2026-11-10-plan-review-exec-dispatch-claim-recheck-pb31c7809-r1/r2/r3)
Driving force: efficiency

## Problem

The certified plan docs/history/plans/2026-11-10-exec-dispatch-claim-recheck.md leaves five non-blocking wording-precision residuals (r3 staged findings plus one r6 finding, deferred per the review-loop budget policy; zero blocking):

- Fresh-own literal: Task 1 bullet 1 pins `claim: fresh-own session=<own-id>` as exact bytes while bullet 2's single-sourced rule requires `updated=<stamp>` on every classification line whenever a claim file exists, and fresh-own is reachable only when the file exists. Follow bullet 2's rule (the single source): the fresh-own line carries the stamp; the plan text gains `updated=<stamp>` in the bullet 1 literal or an exemption clause in bullet 2 at execution prep.
- Sibling-row attribution: the Why's sentence "records the second dispatch's take refused at the conversion scan" over-states the sibling row, which records the refusal and the operator reconciliation without labeling the refused take as the second dispatch (its timestamps sit at the 22:15 opening). The second-dispatch identification is the derivation clause's own work; treat the sibling-row clause as recording only refusal, preservation, and reconciliation.
- TLDR posture compression: the Gist TLDR's "mirrored advisorially in the maintenance dispatch ladder" understates the two-posture ladder that Task 3 and Outcome bullet 3 build (refusing at the idle leg and execution-lane fallback legs, advisory at the clocked legs). Read the normative sections as authoritative.
- Pricing witness attribution: the Gate delta's "quoted as written" covers verbatim only the expected-catch and false-positive-cost fields; the incident field is paraphrased and the review date concretizes the frozen relative date. Read the quote marks as scoping the two verbatim fields.
- Primary class anchors entry: Task 1's anchors block entry "- `probe` mode in `scripts/execution_claim.sh`" does not match the canonical `- `ClassName` in `path` " shape; the pre-round anchors probe refuses it and the same parser runs at execution create/seeding time. Rewrite the entry into the canonical form (a mode is a class of the script) at execution prep or the next sanctioned plan-text touch (r6 finding).
- Occupied-class vocabulary: "distinct from occupied" (Gist edge cases) and "recorded distinguishable from occupied" (Evaluation fail-safety) name an outcome class the folded contract no longer has; read "occupied" as "the fresh-foreign refusal record".

## Exact location

- `docs/history/plans/2026-11-10-exec-dispatch-claim-recheck.md` (after landing, its completed twin): Task 1 bullets 1-2; the Why paragraph's second sentence; the Gist TLDR and edge cases; the Outcome Gate delta pricing-witness sentence; the Evaluation fail-safety row.

## Suggested fix

At execution prep, apply the six wording corrections to the plan text in one small change before Task 1's RED step (or, post-landing, to the completed twin when the text is next touched), each per the fix direction above.
