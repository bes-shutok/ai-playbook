# Backlog: residual-alias docstring paragraph over-scopes to the guarded review- infix

- **Status:** open
- **Class:** DOCUMENTATION_PRECISION
- **Discovered:** 2026-09-20, review round 3 (focused re-cert) of the same plan.
- **Finding:** scripts/review_record_selection.py:175-177 - the alias sentence "a slug that itself begins with an offered infix string ... enumerates the same legacy-shaped records as bare Y" reads over all five offered infixes, but for the guarded bare `review-` infix it is false (slug `review-demo` hits `2026-09-15-review-demo-r1`, bare `demo` hits none; pinned by test_pair_pattern_review_shape_stays_bare_owned). The shadowing paragraph above pins the carve-out, so behavior is never misdescribed.
- **Driving force:** the alias paragraph is the documented contract for slug spelling; an over-broad quantifier makes the docstring contradict a pinned test for one of the five kinds, which a future refactor could "fix" in the wrong direction (code instead of doc).
- **Fix shape:** scope the alias paragraph to the four literal review-kind infixes (plan-review-, branch-review-, code-review-, exec-review-) and name the guarded bare review- carve-out explicitly in the same sentence.
- **Trigger:** next edit to the _pair_pattern docstring or REVIEW_KIND_* constants.
