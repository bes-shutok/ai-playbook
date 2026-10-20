# Backlog: vendored-sync landing path, the two extracted skill module twins

Status: open
Priority: low
Class: vendored-sync landing path
Origin class: docs/history/plans/2026-10-14-skill-monolith-module-extraction.md Task 3
Driving force: token-usage

The execution of docs/history/plans/2026-10-14-skill-monolith-module-extraction.md changed the two spine monoliths and created two new modules beside them, and the sync payload is all four files, not the two new modules alone: both spines' runtime twins still carry the removed inline blocks, so syncing the modules only would strand copy-not-move twins.

- agents/skills/plans/SKILL.md
- agents/skills/execute-plan/SKILL.md
- agents/skills/plans/validation-authoring-rules.md
- agents/skills/execute-plan/worktree-first.md

Their runtime twin destinations are the same relative paths under the shared skills registry ~/.agents/skills (the runtime agent surfaces reach it through their symlinks; see projects/.ai-playbook/agent-runtime-layout.md for the per-agent mapping). This row is the tracked vendored-sync landing path keyed to that plan's landing as the trigger: when the execution landing integrates, sync all four files to those destinations per the repository AGENTS.md Vendored Asset Sync Rules (full bidirectional sync with rsync --delete semantics, then the post-sync scan of changed files for absolute paths and sensitive information). Until that sync lands, the runtime twins are a tracked handoff (this row), never orphan dirt.

Twin-receipt note: scripts/test_done_sweep_gates_lib.py test_execute_plan_skill_receipt_pins_and_vendored_twin is expected red on twin-deployed machines after this landing and clears when the sync lands.

## Follow-up riders on this landing

- Seed the byte caps for the two new module files: run `python3 scripts/skill_text_budget.py --ratchet` on this landing (three review lenses flagged the caps gap; seeding closes the coverage gap, and the gate stays advisory until a true catch promotes it).
- Re-point every cross-corpus reference that asserts a moved sub-block lives spine-internally in agents/skills/execute-plan/SKILL.md to the module home (agents/skills/execute-plan/worktree-first.md); re-derive the site set from disk at execution time (r2 found the class spans more than the five r1 named: docs/maintenance/development_lessons.md:76 area, agents/skills/maintenance/template-unblock.md:80 and :23, agents/skills/maintenance/decisions.md:26, agents/skills/maintenance/template-execution.md:167, :195 and :231, scripts/reconcile_post_landing.py:28-29 docstring, scripts/reverse_squash_guard.py:118 docstring, projects/.ai-playbook/development_lessons.md:3130). The spine hubs keep the targets navigable until then.
