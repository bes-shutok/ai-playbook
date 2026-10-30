# execute-plan recovery index does not route the wait-cancelled worker state

Cluster: execute-plan recovery routing

Driving force: code-quality

Origin: Task 1 intermediate review of docs/history/plans/2026-10-30-reconcile-worker-start-recovery-catalog.md (r1, correctness-completeness lens, 2026-10-30). The recovery-route index added beside `## Orchestrator Responsibilities` routes three interrupted states but not the `User Interruption` row "Wait cancelled after launch; worker may be live", whose action shape (re-observe the same worker; no edits, no relaunch) differs from the failed-worker row already routed. The re-observe rule sits two paragraphs above the index, so discoverability loss is partial.

Fix shape: add a fourth index bullet pointing at the wait-cancelled row, or fold the wait-cancelled state into the existing failed-worker bullet with its distinct action named. Keep the index compact; no owner-section restatement.
