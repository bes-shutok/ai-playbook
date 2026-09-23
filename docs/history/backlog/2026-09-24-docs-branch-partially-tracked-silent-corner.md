# docs-branch-partially-tracked-silent-corner

Driving force: code-quality + simplicity

Origin: P55 execution review round 2 (docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r2.md).

r2 F3: unignored partially-live-tracked dir candidate never warns (ls-files --error-unmatch succeeds if any file is tracked); new untracked files inside go unsynced unnamed. Contrived; revisit if a real case appears.

Suggested fix: see origin description; defer until the owning file is next touched.
