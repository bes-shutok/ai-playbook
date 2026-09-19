# Backlog: selection-helper suffix shadowing in record enumeration

Status: open
Severity: Low
Origin: r4 code-review round of the review-records-contract execution (2026-09-19), staged finding F1 (two-worker echo: correctness-completeness, risk); staging doc `docs/reviews/2026-09-16-review-records-contract-code-review-r4.md` (gitignored); capture hygiene: scan-public-hygiene --files pass (2026-09-19)

## Problem

`scripts/review_record_selection.py` `_pair_pattern` uses a loose `(?:.+-)?` prefix, so a slug that is a hyphen-suffix of another slug (e.g. `plan` vs `review-plan`) enumerates the other family's record pair as its own round history. The no-flag path fails closed but names the foreign record in the overwrite-guard refusal; with `--explicit-new-round` the helper emits a `new-round` decision whose `prior`/`supersedes` point at the foreign record (probed end-to-end 2026-09-19). No overwrite, no data loss; audit-trail integrity only.

## Fix shape

Anchor the pair grammar to the helper-emitted shape (`^\d{4}-\d{2}-\d{2}-<slug>-r(\d+)$`-style) OR document the suffix-match rule. CAUTION: the loose prefix is load-bearing for legacy `...-plan-review-<slug>-rN` record names, so this is a behavior tradeoff, not a pure bug fix; pin both the legacy-name positive and the cross-slug negative with tests.

## Trigger

The next change to the helper's enumeration grammar, or the first observed suffix-collision between two real slugs sharing one reviews directory.
