# Backlog: record gates enforce divergent slug grammars for the same artifact identity, so producers guess wrong and pay a re-mint cycle per mismatch

- **Filed:** 2026-11-20, 24h session-pattern harvest learn run (learn Step 1.8; record-receipt grammar family)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** witnessed defect (three in-run refusal and re-mint cycles in one 24h window, each resolved in-run by trial)
- **Skill/step:** the completion-receipt and seal matchers across landing and archive gates: the archive-egress evidence leg's slug form (landing gate), the exec-completion receipt's hyphen-bounded slug match (landing gate), the certification seal's `artifact:` comparison (`scripts/produce_exec_review_record.py` consumer `scripts/corrections_record.py`), and the mint-time acceptance grammar (`scripts/produce_exec_review_record.py`, the warning arm landed 2026-11-19)
- **Cluster:** docs/history/backlog/2026-11-19-archive-ceremony-receipt-carrying-gap-at-adhoc-landings.md (same receipts, the carrying gap); docs/history/backlog/2026-10-31-gate-removal-shared-slug-second-witness.md (shared-slug identity collisions at a sibling gate); docs/history/backlog/2026-11-16-execute-plan-reconciler-slug-normalization.md (the consumer-side normalizer precedent this row generalizes); the executed producer-exec-record-grammar plan (mint-time leg of the same acceptance grammar, warning arm landed with a live first catch)

## Observed versus expected

Observed: the same identity, a plan's slug, must match three different canonical forms at three different gates, and producers keep guessing wrong. Three witnessed cycles in one day: (1) an ad-hoc landing's archive-egress evidence leg refused twice because the gate's slug form strips the plan's date prefix; the run backfilled completion receipts in the date-stripped form to pass; (2) an amendment run's certification seal refused the bare slug for the `artifact:` field and required the full plan relpath (a strict-equality comparison in the corrections-record producer); (3) a clocked-order run's exec-completion receipt minted with the dated-slug form failed the landing gate's hyphen-bounded slug match and was re-minted with the bare-slug form, which passed. Each mismatch surfaced late in a run (landing, seal, or archive boundary), cost a re-mint or backfill cycle, and was resolved by trial rather than by a stated contract. The mint-time leg of the same class (dated-stem producer output refused by the acceptance grammar) was recorded 2026-11-19 as the third incident on the producer-grammar row and the mint-time warning arm landed 2026-11-19 with a live first catch the same day.

Expected: one stated per-artifact-class canonical slug form, cited by every matcher, with normalization owned by a shared helper in the record producers' seam, so a producer emits the right form the first time and a mismatch is a named contract violation, not a trial-and-error re-mint.

## Suggested direction

Single-home the contract: one paragraph per artifact class (completion receipt, seal artifact reference, egress evidence reference) naming the canonical form and one normalization helper in the producers' seam that every matcher calls instead of its private match. Docs plus helper first, no new gate; per-gate matcher updates follow with their own test cells. The 2026-11-16 reconciler-slug-normalization row is the shape precedent on the consumer side.

## Machinery admission

No machinery proposed: the fix removes divergent private matchers in favor of one cited contract and one helper. The witnessed cost is three re-mint or backfill cycles in one day (each a late-run refusal round-trip); no gate is added, so no admission fields are owed. Removal-shaped on the divergence itself.

## Rejected alternatives

- Teach every producer all current gate forms (a compatibility table): rejected; it freezes the divergence into documentation and grows every new gate's doc burden instead of removing the divergence.
- Relax every matcher to accept any slug form: rejected; the strict forms carry real bindings (the seal comparison exists so a seal names exactly the bytes it certifies), and loosening them trades a witnessed friction cost for an unwitnessed integrity cost.
- Keep per-gate private matchers and add a lint over them: rejected as machinery ahead of need; the contract-plus-helper removes the divergence the lint would police, and no lint-shaped incident exists beyond the three re-mint cycles this row witnesses.

## Evidence

- The 16:06 run's closing report: two archive-egress evidence-leg refusals, the gate's slug form stripping the plan's date prefix, backfilled `-exec-r2`/`-exec-r3` receipts unblocking the landing.
- The amendment run's wrap-up (~21:36): the seal `artifact:` field comparison refused the bare slug (`corrections_record.py` strict comparison), full plan relpath required.
- The 00:39 run's deviations section: the exec-completion receipt re-minted once, dated-slug form failing the landing gate's hyphen-bounded slug match, bare-slug form passing.
- The producer-grammar row's 2026-11-19 third incident: dated-stem producer output refused by the mint acceptance grammar, slug-named copies passed.

## Acceptance

- One contract paragraph per artifact class exists, each matcher cites it and normalizes through the shared helper, and a producer emitting the wrong form gets the mint-time warning (or a named refusal) instead of a late gate refusal; suites stay green.

## Dedup probe

Searched open backlog rows for slug grammar, slug normalization, dated-slug, date-prefix, and receipt re-mint phrasing: the archive-ceremony row owns the receipt-carrying gap (not the form mismatch), the reconciler row owns one consumer-side normalizer, the gate-removal row owns shared-slug collisions; no open row owns the cross-gate grammar divergence itself.
