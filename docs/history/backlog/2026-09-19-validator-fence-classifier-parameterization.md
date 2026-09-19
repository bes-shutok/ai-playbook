# Backlog: parameterize the two-surface fence classifier and the declared non-canonical predicate in validate_review_staging.py

Status: open
Severity: Low
Origin: review records contract code review r1 (F14 + F15, design-simplicity; accepted for backlog deferral); staging doc docs/reviews/2026-09-16-review-records-contract-code-review-r1.md; capture hygiene: scan-public-hygiene --files pass (2026-09-19)
Date: 2026-09-19

`_record_kind_fence` is a verbatim copy of `_freshness_fence` (and the coverage fence classifier is a third copy): three hand-copied two-surface date-fence classifiers that can drift, including the malformed-date nuance already missing from the newest copy's docstring. Separately, the declared non-canonical arming predicate (a present, enum-valid `record_kind` different from `canonical`) is re-derived inline at four gate-skip sites, so a future arming-rule change must be replicated four times or the surfaces diverge.

The helper mirror (r3 F1) belongs to the same single-sourcing scope: `scripts/review_record_selection.py` carries its own `_fence_mask` hand-copy of the fence state machine for the mark-superseded marker and Metadata scans. As of r3 it mirrors only the close rule (bare, equal-or-longer, same-delimiter); its opener regex (`[ \t]*` prefix) intentionally diverges from the classifier's `\s*` opener spelling, and an unclosed fence is refused there instead of using the classifier's partial fallback. The parameterization refactor should fold the helper's mask onto the one shared classifier (or an explicitly declared seam for it) so the grammars cannot drift further.

Fix shape: extract one parameterized two-surface date-fence classifier (fence constant as the parameter) owned by a single helper and consumed by the EXTENDED, COVERAGE, and RECORD_KIND fences, plus a `_declared_noncanonical_kind(payload)` helper called from all four gate-skip sites; keep every existing selftest arm green as the regression net.

Trigger: the next date-fence addition, or the next change to the non-canonical arming rule, or the next change to the helper's fence grammar (r3 F1). Deferred (not fixed in r1) because the refactor rewrites validators adjacent to frozen legacy regions and deserves its own reviewed change with the full selftest as the gate.
