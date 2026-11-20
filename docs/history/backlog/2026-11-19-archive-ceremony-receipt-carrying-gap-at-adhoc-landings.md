# Backlog: ad-hoc landings that archive plans can leave the exec-review completion receipt unminted, red-ing later gated log-writes

- **Filed:** 2026-11-19, scheduler-turn session (the declared-log-path authoring landing arc)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** self-serving
- **Class:** fix-class

Cluster: docs/history/backlog/2026-11-07-archive-ceremony-exec-review-record-gap.md (covered: the sweep-ordering fix owns when the archive rider runs; this row owns the receipt-carrying gap that survives the ordering fix); the deferred row 2026-10-09-archive-ceremony-legacy-exec-review-name.md (the legacy name form, parked); docs/history/backlog/2026-11-13-producer-exec-record-grammar-arm-promotion.md (covered-pending-execution: same gate surface, the producer's write-time arm for the same acceptance grammar, its minted-filename leg witnessed 2026-11-19).
Cluster: docs/history/backlog/2026-11-20-record-gate-slug-grammar-divergence.md (same receipts: that row owns the cross-gate slug-form mismatches producers hit at the matchers, this row the receipt-carrying gap)

## Problem

An ad-hoc landing that archives an executed plan without minting or carrying its `*-plan-review-<slug>-exec-r<N>` completion receipt deposits a silent debt: the archive itself passes (nothing gates the receipt at landing time when the landing skips the sweep), and the debt surfaces later at the NEXT gated rolling-log write, whose archive-ceremony check refuses naming the missing series - blocking an unrelated lane's log-write until a backfill lands.

Witnessed: landing 7396e431e (2026-11-18 17:15) archived `docs/history/plans/completed/2026-11-13-authoring-claim-sweep-exemption-and-refresh-recipe.md` without the completion receipt; the next day's monitor log-write was refused by the archive-ceremony gate naming the missing series; the repair was the gate's own remedy arm - a marked backfill completion receipt (`produce_exec_review_record.py --kind exec-completion --certified-range <base>...<head>`, landed 36a960b71).

## Observed vs expected

Observed: the receipt-carrying duty lives nowhere in the ad-hoc landing path; the gate that enforces it runs only on later, unrelated log-writes, converting a landing-time omission into a foreign lane's blocker.
Expected: the archiving landing either carries an existing completion receipt or mints the marked reconstruction itself (the gate's remedy producer is the sanctioned shape), so the debt never outlives the landing.

## Scope arms (fix)

1. The ad-hoc landing closeout (and any path that archives an executed plan) verifies the completion receipt exists for the archived slug and either carries it into the landing or invokes the reconstruction producer as a landing rider.
2. The archive-ceremony gate's refusal message already names the remedy arm; keep the producer contract unchanged (the marked reconstruction is valid per the cited-review-receipt-integrity precedent).

## Rejected alternatives

- Gate every landing on the archive-ceremony check: rejected; the check is fail-open report-only by design outside the log-write path, and gating every landing adds a blocker for a debt one rider step closes.
