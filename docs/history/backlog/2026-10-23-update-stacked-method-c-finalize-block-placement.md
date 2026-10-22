# update-stacked-branches: Method B finalize block sits inside the Method C subsection

Added: 2026-10-23, Task 1 intermediate review (off-plan finding) of docs/history/plans/2026-10-21-update-stacked-branch-promoted-commit-exclusion.md

Status: open
Priority: low

Driving force: code-quality. The "Required finalize: Method B..." block and its exit criteria describe Method B's commit reconstruction but sit inside the Method C subsection of agents/skills/update-stacked-branches/SKILL.md (around lines 157-169); the placement predates the promotion-subcase change and was left untouched by it.

Fix shape: move or re-label the finalize block so it reads as shared finalize guidance or belongs to Method B, without changing its operative steps.
