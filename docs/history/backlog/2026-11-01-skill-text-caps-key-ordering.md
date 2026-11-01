# Backlog: skill_text_budget_caps.json key ordering normalization

Driving force: code-quality

Task 1 of docs/history/plans/2026-10-29-vendored-sync-module-twins.md appended the two new module caps at the end of the `files` map, adding exactly one new adjacent-key inversion (`agents/skills/maintenance/template-unblock.md` before `agents/skills/execute-plan/worktree-first.md`); the baseline was not fully sorted either — main's `files` map already held 3 adjacent-key inversions (`agents/skills/doc-hierarchy/migration-map.md` before `agents/skills/doc-hierarchy-migrate/SKILL.md`, `agents/skills/using-skills/SKILL.md` before `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/survey-arms.md` before `agents/skills/maintenance/duties-core.md`) — and the script never self-normalizes since it preserves load order on write-back. Normalize key order next time the caps file is touched; nothing enforces order today, so this is cosmetic-only.
