# claim deletion fence misses uppercase plan stems (case-sensitive match)
- **Cluster:** docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md; docs/history/plans/completed/2026-10-10-coordination-single-writer-ttl.md; docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md

Cluster: docs/history/plans/completed/2026-10-10-contract-single-sourcing.md (the same drift family: copied contracts disagreeing across surfaces; this row is a claims-surface instance that stays a separate small plan unless that family's plan budget fits a rider)

Driving force: reliability
Date filed: 2026-10-07
Origin: code review r1 address round (execution-claim-write-enforcement), finding F4, deferred per the recorded triage disposition
Severity: medium, latent (zero uppercase plan filenames in the corpus today); the first uppercase-named plan gets a claim the fence cannot see
Source reference: docs/history/reviews/2026-10-07-execution-claim-write-enforcement-code-review-r1.md, F4 (correctness-completeness, contract-docs CD-1 echo); capture hygiene: scan-public-hygiene pass recorded in the row source (run at capture time)

## Finding

The claim filename derives as the lowercased canonical artifact slug (`scripts/plan_readiness.py` `artifact_slug`, so an uppercase plan filename `2026-09-01-EXEC-CLAIM-Fixture-Story.md` yields the claim `exec-claim-fixture-story.md`), but the deletion fence (`scripts/reverse_squash_guard.py` check-claim-fence) matches claim files against the plan's stem case-sensitively: it looks for a claim named like the plan file's stem, so the lowercased claim of an uppercase-named plan never matches and a plan-file deletion sails past the fence while a live claim names it. The sibling dir-resolution drift row covers WHERE the claims root resolves; this row covers the fence's stem comparison INSIDE a correctly resolved root.

Exact location: `scripts/reverse_squash_guard.py` check-claim-fence stem match (the arm comparing claim filenames to the plan's stem) versus `scripts/execution_claim.sh` derive_slug (the lowercased writer side).

## Suggested direction

Make the fence's stem match case-insensitive (compare lowercased stem to lowercased claim filename), or have the fence enumerate claims through the same `artifact_slug` derivation instead of the raw stem; the derivation route keeps one SOT.

## Why not fixed now

Latent today (no uppercase plan filenames exist in the corpus), and the fence side sits outside this plan's must-fix scope; fixing the writer to preserve case would break the canonical-slug contract landed by 80ad2666, so the fix belongs on the fence side in its own change.

Class: fence-class (a guard reads a registry the writer populates under a different normalization, so the guard's evidence is silently absent; the default shape is a new refusal or a corrected gate)
Dedup probe: keyword search `stem|case-insensitive|lowercas|fence` over docs/history/backlog/*.md; nearest items are 2026-10-07-execution-claims-dir-resolution-drift.md (claims-root resolution drift between writer and fence, the declared sibling: that row is the path axis, this row the normalization axis) and 2026-10-06-claim-fence-test-coverage-gaps.md (fence test coverage, not fence behavior); distinct from both.
Origin class: self-serving
- **Cluster:** docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md; docs/history/backlog/landing 5865a50a5, carried into current history by rewrite commit f3894756d
