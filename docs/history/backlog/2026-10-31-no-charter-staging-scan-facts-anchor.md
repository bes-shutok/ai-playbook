# no-charter staging scan anchors at worktree-side facts values

Driving force: preservation (hardening note; same trust anchor as existing facts-driven guards)

`_no_charter_staging_refusal` resolves the staging reviews/review-certs homes via the worktree's facts; an out-of-band worktree facts edit (reviews_dir redirected post-provisioning) redirects the scan and a run-created record at the original transfer-in location goes unscanned (gitignored, porcelain-invisible). No in-contract writer edits worktree facts (transfer-in is noclobber), so this is a hardening note, not a gate change; a facts byte-equality check would be new machinery the plan forbids. Origin: intermediate review round 3 finding, execute-plan run 2026-10-31.
