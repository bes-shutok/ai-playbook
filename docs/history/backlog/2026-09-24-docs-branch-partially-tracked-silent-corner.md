# docs-branch-partially-tracked-silent-corner

Driving force: code-quality + simplicity

Status: closed
Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md, Task 7): closed by that plan's Task 4 — the Step 1 loop gained the partial-track warning arm (candidate exists, the shared probe returned nonzero, tracked content under it, untracked files inside, and the candidate is absent from the docs-branch tree) naming that the untracked files are not shadowed and will not reach the docs branch; live needle re-run on the execution base: the warning fires exactly once on the one-tracked-one-untracked unbranched fixture and stays silent when the candidate is branch-tracked or fully tracked.

Origin: P55 execution review round 2 (docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r2.md).

r2 F3: unignored partially-live-tracked dir candidate never warns (ls-files --error-unmatch succeeds if any file is tracked); new untracked files inside go unsynced unnamed. Contrived; revisit if a real case appears.

Suggested fix: see origin description; defer until the owning file is next touched.
