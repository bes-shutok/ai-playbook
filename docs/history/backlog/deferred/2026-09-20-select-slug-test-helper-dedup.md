# Backlog: select_slug test helper duplicates select_in body; a defaulted slug parameter would deduplicate

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; test-helper dedup (code-quality polish). Revive on the test file is next edited under a live plan, or a project-priority-profile change.)
Workflow: backlog
Class: test-code design polish (no contract change, no coverage change)
Discovered: 2026-09-20, review r1 of `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (five-lens panel, simplicity lens, deferred as Low)

## Finding

In `scripts/test_review_record_selection.py`, the `select_slug` helper (added in the pair-grammar pass, originally around line 111) duplicates the body of `select_in` except for the hardcoded `"demo"` slug argument. A defaulted parameter on `select_in` (`def select_in(self, directory, digest, *extra, slug="demo")`) would collapse the two helpers into one; `select` would then be the only thin wrapper left (`return self.select_in(self.reviews, digest, *extra)`).

## Driving force

Simplicity: two near-identical helpers make the next grammar-pass contributor guess which one to extend (the r1 F1 pass extended `select_slug` and left `select_in` behind, which is exactly the drift the duplication invites).

## Fix shape

Add the keyword-only `slug="demo"` parameter to `select_in`, delete `select_slug`, and rewrite its call sites (the pair-grammar and live-family tests) to `self.select_in(self.reviews, digest, *extra, slug=slug)`. Purely mechanical; the suite must stay at the same case count and green.

## Trigger

Next edit of `scripts/test_review_record_selection.py` that touches the helper seam or adds another slug-parameterized case (fold into the same pass; not worth a dedicated execution on its own).
