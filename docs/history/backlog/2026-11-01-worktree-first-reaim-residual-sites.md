# Backlog: residual worktree-first re-aim sites

Driving force: correctness

Task 2 of docs/history/plans/2026-10-29-vendored-sync-module-twins.md re-aimed stale moved-content claims from execute-plan/SKILL.md to agents/skills/execute-plan/worktree-first.md within its Files list. The Task 2 intermediate review (r1) found same-class stale claims outside that scope, verified against worktree-first.md:

- `agents/skills/maintenance/template-authoring.md:15` — authoring dispatch payload still says "post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md"; implementation lives at worktree-first.md:59. Not pin-protected.
- `agents/skills/bootstrap-ai-playbook/SKILL.md:181` and `:245` — "Worktree-first standard policy paragraph (agents/skills/execute-plan/SKILL.md)"; the policy paragraph lives in the module.

Re-aim all three in one change; only the three bulleted sites above are in scope. Disposition of the r1 candidate at `projects/.ai-playbook/development_lessons.md:3132` (lesson 147's See-also): verified as a valid navigable hub pointer — the spine `agents/skills/execute-plan/SKILL.md` retains the Worktree-first anchors (`## Worktree-first standard` at SKILL.md:198) — deliberately preserved, no edit needed. Scope note: the exactly-once-pinned hub-class spans (`agents/skills/maintenance/template-authoring.md:13`, `agents/skills/maintenance/template-execution.md:27-28`, `agents/skills/maintenance/template-unblock.md:26-27`) are deliberately preserved as valid hub pointers OUTSIDE the re-aim scope (`SKILL.md:198` remains the hub); the pin re-keying constraint below applies only if a future change touches a pinned span. Constraint: each pinned span is exactly-once pinned by scripts/check_maintenance_pins.sh; any edit touching a pinned span must re-key the pin literals in the same change.
