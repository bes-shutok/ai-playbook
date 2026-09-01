# Fence scanner consolidation follow-ups: cross-character close, dead reset-mode cell, duplicated fallback driver

Status: done
Workflow: backlog
Source: docs/reviews/2026-08-29-fence-scanner-consolidation-code-review-r1.md, round r1, findings F1 (backlog half), F5, F6 (validated as real; deliberately deferred to keep the branch aligned with the reviewed plan scope); item 4 added from the r5 round (quality#fence-close-info-string, verified repro, pre-existing debt)

## Problem

Four follow-ups on the consolidated fence classifier in `scripts/validate_review_staging.py`:

1. **Cross-character fence close (F1 backlog half)**: `classify_fence_lines` closes a fence on any equal-or-longer delimiter run without comparing the delimiter character, so a ```` ``` ```` fence is closed by a `~~~~` line. This diverges from CommonMark (char must match). Pre-existing debt: both pre-consolidation scanners had the same length-only rule, and the plan's r5 F5 contract pins length-only, so it was kept on this branch. Consequence when hit is fail-loud, not silent: a premature close leaks a fenced `#### F<N>.` line as a phantom finding that trips the conservation check. r3 repro evidence (verified): a finding whose metadata region contains a fenced example embedding a bare `~~~` line can let in-fence example bullets (for example `- **Blocking**: true`) overwrite real parsed values, yielding wrong readiness or a false conservation error; the silent-misparse path exists too, not only the fail-loud one.
2. **Redundant configuration axis and write-only payload (`simplification#yagni`, F5)**: `classify_fence_lines(lines, reset_at_headings, is_reset_heading)` carries a redundant `reset_at_headings` boolean that is fully derivable from `is_reset_heading is not None` (the `(True, None)` combination is rejected with a ValueError guard added in the r2 review folds, so the silent reset-on-every-heading mode cannot be constructed; no caller relies on the two-parameter shape), and the `fence_opener(delimiter_length)` payload is read by no consumer. Plan Task 3 wording mandates the current two-parameter shape and the event vocabulary, so this is a deliberate post-plan follow-up.
3. **Duplicated partial-fallback driver (`simplification#shrink`, F6)**: the driver shape (classify, filter pre-opener results, re-classify the suffix with the consumer's reset predicate, offset suffix indices by the opener) is duplicated in `split_finding_blocks` and `parse_markdown_findings`; a divergent future edit to one copy would re-create the drift class this consolidation removed.
4. **Fence close matches delimiter lines with trailing info strings (r5, `quality#fence-close-info-string`)**: the close test matches any line whose fence-character prefix is equal-or-longer, without requiring the line to be bare, so a quoted inner opener such as ```` ```python ```` closes an equal-length outer ```` ``` ```` fence and promotes the snippet's remaining lines to live structure (verified: a quoted `#### F99.` header after an inner ```` ```python ```` line becomes a phantom finding). CommonMark requires a bare closing fence. Pre-existing debt preserved byte-identical by the consolidation; consequence is fail-loud (conservation error naming quoted content).

## Location

- `scripts/validate_review_staging.py`: `classify_fence_lines` close branch (~line 337, length-only comparison) and signature (~line 294); duplicated fallback drivers in `split_finding_blocks` (~line 404) and `parse_markdown_findings` (~line 561).

## Suggested fix

1. Capture the delimiter character at the opener and require a character match (plus the existing equal-or-longer length rule) on close; add a characterization fixture pinning the new semantics (backtick fence whose inner `~~~` line stays `in_fence_content`, and the tilde-closed/backtick-unclosed fixtures kept green). Coordinates with the r1 F1 docstring note that already documents the length-only divergence.
2. Collapse the API to a single `is_reset_heading=None` parameter where None means content-preserving (dropping the now-redundant `reset_at_headings` boolean); drop the `delimiter_length` payload unless a consumer materializes.
3. Extract a shared module-level helper, for example `classify_with_fallback(lines, is_reset_heading)` returning `(events, opener, reset_events, offset)`, and drive both consumers from it so the offset arithmetic lives in one place.
4. Require the closing delimiter line to be bare (fence run plus optional whitespace to end of line) while keeping prefix-match for openers; pin with a fixture whose fenced snippet quotes an equal-length inner opener (for example ```` ```python ```` inside a ```` ``` ```` fence) and assert its following lines stay `in_fence_content`. Coordinates with the cross-character item (both are close-rule CommonMark divergences).

## Severity

Low (all four). Items 2 and 3 are simplification-only (no behavior change); items 1 and 4 are behavioral divergences from CommonMark whose primary consequence is a fail-loud conservation error, with a verified r3 silent-misparse path via in-fence example bullets overwriting parsed metadata (see Problem 1).

## Why not fixed now

Scope decision by the orchestrator (execute-plan Phase 3 r1 address pass, 2026-08-29): the r5 F5 contract and plan Task 3 wording pin the current length-only close and the two-parameter API shape, so changing them on this branch would drift from the reviewed spec; the fallback-driver dedup is a structural rework late in a review loop (fix-risk rule 2). Recorded here so the dead mode and the duplication are not silently relied upon.

## Closure note

Done 2026-09-01 by docs/plans/2026-08-31-fence-close-rules.md. Items 1 and 4 are fixed by the new close rule requiring a character match, equal-or-longer length, and a bare closing delimiter line (the plan's char+length+bare rule), pinned by the verified silent-misparse and phantom repros. Items 2 and 3 are fixed by collapsing to the predicate-only `is_reset_heading` axis and driving both consumers from the shared fallback driver. Residual follow-ups split out to docs/history/backlog/2026-08-31-fence-scanner-round-2.md.
