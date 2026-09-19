# Backlog: budget-gate attribution isolation r5 review residuals (2 Lows)

Created: 2026-09-18 by the execute-plan run of docs/plans/2026-09-15-budget-gate-decision-table-attribution.md (review round 5, final at the cap; zero blocking; both residuals are the probe-coverage regenerating class per ADR-0002).

Status: open

## Origin 1 — three obligations deletable-while-green (testing, J1)

Mutation-confirmed against docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md at head b4236d44: the plan's Validation Commands block stays exit-0 when these are deleted:
1. the real-pause baseline disjunct "(a marker record already present at the boundary baseline whose content matches the pause's reset epoch, OR the marker's mtime inside the pause window with content matching that epoch)"
2. "and the concurrent-writer check at the pause boundary as the shared conjunct"
3. ", re-take the marker baseline and re-run the step-1 session check at the re-drive boundary" (contingency step 4)

Fix: add one flattened fixed-string probe per obligation to the plan's Validation Commands block (needles exist in current bytes, so probes are green today):
- *"whose content matches the pause's reset epoch, OR the marker's mtime inside the pause window"*
- *"check at the pause boundary as the shared conjunct"*
- *"re-take the marker baseline and re-run the step-1 session check at the re-drive boundary"*

## Origin 2 — standing order lacks a not-intentional-divergence terminal branch (risk, J2)

docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md, abort and retirement protocol: the superseded-edit branch covers only "confirms an intentional edit". A divergence judged NOT intentional leaves the standing order cycling idempotently (merge-only restore + snapshot each session; normal-path retirement unsatisfiable while the divergence persists). Harm bounded but the branch cannot converge.

Fix: one sentence in the protocol: "If the unexpected divergence is judged NOT intentional, restore per the merge granularity, then either remove the unexplained change (after which normal-path retirement applies on the next clean diff) or report the state for manual recovery and retire both fixed-name backups so the standing order cannot loop against a permanently dirty diff."
