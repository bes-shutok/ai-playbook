# Backlog: review-name probe round-number shape diverges from the gate glob on r0/r05

- Status: rejected (2026-09-27; fail-closed shape divergence between two consumers; unwitnessed formal hardening)

Driving force: code-quality

The `--check-review-name` probe fullmatches round filenames against the discovery shape with `N >= 1` (so `r05` or `r0` are rejected), while the readiness gate's `latest_review_round` glob plus its round-number regex accept some of those spellings. A round staged under a glob-visible but fullmatch-invisible name is fail-closed (the probe demands the canonical shape), but it is a residual divergence between the two consumers of the same discovery contract.

Origin: execution review r1 of docs/history/plans/2026-09-27-plans-authoring-loop-contract-gates.md, finding F2 (Low, non-blocking), worktree branch 2026-09-27-execute-plans-authoring-loop-contract-gates, commit 68ec20fb.

Acceptance sketch: either the shared shape source's round-number grammar and the gate's glob/regex accept exactly the same name set, or the divergence is documented at the shared helper as fail-closed-by-design with the probe as the stricter consumer; a test pins whichever set is chosen.
