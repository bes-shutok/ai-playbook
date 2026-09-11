# Backlog: consolidate the review-staging freshness grandfathering fence into one helper

Status: done
Completed: 2026-09-11 via execute-plan run of docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md (review r1-r5, clean exit r5)
Workflow: backlog
Origin: execute-plan fresh-review coverage gaps plan, review round 3 overflow item O15 (design-simplicity), 2026-09-08
Severity: Low
Scope: `scripts/validate_review_staging.py` freshness gates (Markdown presence gate, sidecar extended-field gate, backdate refusal); behavior-neutral refactor

## Problem

The extended-field grandfathering fence (`EXTENDED_SIDECAR_MIN_DATE`) is one concept but is enforced as three coupled rules across two date keys: the Markdown presence gate keys on the staging filename's leading date, the sidecar extended-field exemption keys on the sidecar `date` field, and the backdate refusal compares the two keys against each other. Round 3 already had to patch gaps in this cluster (a dateless filename silently skipped the Markdown gate; a backdated sidecar date could strip the exemption), and each new edge lands in a different one of the three rules, so future changes risk re-introducing a split-brain fence where one rule drifts from the other two.

## Exact location

- `scripts/validate_review_staging.py`, `validate_date_keyed_freshness_lines` (filename-keyed presence gate plus the dateless-filename fail-closed branch)
- `scripts/validate_review_staging.py`, `validate_version1_payload` (sidecar `date`-keyed extended-field exemption)
- `scripts/validate_review_staging.py`, the backdate refusal inside `validate_version1_payload` (cross-check of the two date keys)

## Suggested fix

Extract a single helper that computes the effective freshness date of a record as the max of the filename's leading date and the sidecar `date` (a missing or malformed key on either surface counts as post-fence, fail-closed), and have the Markdown presence gate, the sidecar extended-field gate, and the backdate refusal all consume that one helper instead of each re-deriving their own fence. Keep the public behavior byte-identical: the full selftest suite (including the round 3 canaries) must pass unchanged before and after the consolidation.

## Why not fixed now

Deferred as a behavior-neutral consolidation during the round 3 address pass per receiving-review Backlog capture: the address pass spent its budget on the behavior-carrying fixes (false-green closures and fail-closed gates), and a pure refactor of frozen-date logic is lower risk done standalone with its own review round.

## Acceptance criteria

- One helper owns the effective-freshness-date computation; no freshness gate re-derives a date fence inline.
- `python3 scripts/validate_review_staging.py --selftest` exits 0 unchanged before and after.
- The three consumers (Markdown presence gate, sidecar extended-field gate, backdate refusal) read as thin calls; no duplicated date-comparison logic remains.
