# Backlog: Memoize the coverage archive-twin anchor and plans-layout resolution

Driving force: efficiency

Captured from: intermediate task review (Task 1, implementation + contract lenses) of the run `review-staging-archived-plan-source-identity`, worktree branch `2026-11-06-review-staging-archived-source`, 2026-11-06.

`_coverage_archive_twin` in `scripts/validate_review_staging.py` runs `repository_root(cwd)` (a `git rev-parse` subprocess) plus two `.ai-playbook/facts.md` parses for every relative non-empty coverage-link value, before the scoping gate; the contract check and readiness gate each re-run the helpers, so a record with N links spawns roughly 2N git processes. Memoize the anchor and the resolved plans layout per cwd (chdir-safe for the embedded battery), or compute once per `validate_coverage_contract` call. No contract impact; performance follow-up only.
