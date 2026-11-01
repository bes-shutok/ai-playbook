# Backlog: quota-wall byte-level witness accepts any committed record rewrite permanently

- **Filed:** 2026-10-30 during the phase2-baseline-repair Phase 3 review-fix round (r1)
- **Status:** covered (docs/history/plans/2026-11-01-quota-doctrine-committed-rewrite-narrowing.md)
- **Workflow:** backlog
- **Priority:** normal
- **Skill-step:** `scripts/test_quota_wall_doctrine.py` `test_witness_every_preexisting_record_is_textually_unchanged_against_baseline` (the directives-file byte-level witness, records D-1..D-12 in `docs/maintenance/operator-directives.md`)
- **Class:** fence-class
- **Cluster:** docs/history/backlog/2026-10-30-inventory-count-reconciliation.md (concern 1 corrects this row's D-1..D-12 record-range mention to D-1..D-16; shared operator-directives witness surface)
- **Origin class:** self-serving
- **Driving force:** code-quality (primary), reliability (secondary: the pin exists so silent erosion of the operator directives is visible, and the committed class currently erodes invisibly)
- **Severity:** low; a hypothetical future committed rewrite would silently become the permanent standard, with no red and no named id.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `quota-wall`, `quota wall`, `operator-directives`, `byte-level witness`, `bounded-retry budget`, and `D-7`. The nearest open item is `2026-10-10-quota-wall-stop-account-mismatch.md` (stop-record cause attribution, a different defect surface); no open item covers the doctrine witness's committed-revision acceptance semantics. `2026-10-30-machinery-witness-ref-validation.md` is the sibling witness-quality family but targets the machinery inventory's witness refs, not this suite's revision model.
- **Source:** review round r1 of plan 2026-10-29-phase2-baseline-repair (the panel's Fix 1 finding, code-traced, non-blocking); capture hygiene: public-hygiene explicit-path scan passed.

## Problem

The witness holds every pre-existing directive record (D-1..D-12) byte-identically against the baseline revision, and when the working tree differs from that baseline it accepts the newest committed (HEAD) revision as the alternative (`test_quota_wall_doctrine.py`, the committed-revision acceptance arm; the same acceptance exists for the preamble). That arm means any committed rewrite of any pre-existing record passes the witness permanently: once the rewrite lands, HEAD becomes the standard the record is held to, and every later revision inherits it. Enforcement for the committed class thereby narrows to pre-commit discipline only (uncommitted drift still goes red with the id named); there is no post-hoc red for committed drift against the last sanctioned revision. Evidence: code-traced by the review round against the current acceptance structure; no actual committed rewrite has occurred yet, so the failure class is witnessed by inspection, not by a landed incident.

## Direction

Hold post-edited records to the newest sanctioned revision instead of to HEAD: anchor each record at the 2026-10-27 em-dash formatting pass (the witnessed sanctioned revision for D-3..D-6) or at an explicit named sanction list (per record, the newest commit a sanctioned landing touched), so a future committed rewrite outside that anchor goes red with the record id named. The baseline-resolution helper (`_baseline_revision`) already walks the file's commit history, so the anchor has a mechanical home.

## Regression pin

When the anchor lands, commit a one-word edit to D-7 (outside any sanction) and assert the suite goes red naming D-7; that mutation is the witness that the committed class is actually fenced, not just re-anchored on paper.

## Why not fixed now

The fix round's authorized edit set for this suite was exactly the two panel arms (extend the committed-revision acceptance to the preamble, and name the red on a committed record deletion); re-anchoring the committed class to a named sanction list is a design change over the witness's revision model, deferred by the round's scope boundary, not by invalidity.
