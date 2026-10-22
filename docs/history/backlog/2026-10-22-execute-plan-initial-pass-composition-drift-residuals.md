# Backlog: execute-plan initial-pass composition drift residuals after the panel-selection deferral

- **Filed:** 2026-10-22, ad-hoc execute-plan-phase3-initial-pass-panel-selection-reference code review r1 (finding F1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** docs/history/backlog/2026-10-10-code-review-panel-worker-capacity.md (same surface: Phase 3 panel composition)
- **Origin class:** review finding residual
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/subagent-prompts.md` (Review lens worker template, Panel launch paragraph); `agents/skills/execute-plan/SKILL.md` (Verify-fix vs fresh review table, Fresh review row); `agents/skills/review-agents/review-panel-selection.md` (orchestrator list parenthetical)
- **Driving force:** cost (composition authority stays with the panel-selection single source, so a fresh run never re-pays the five-worker default on a Tier L delta)

## Problem

The execute-plan-phase3-initial-pass-panel-selection-reference ad-hoc landing replaced the Step 3.1 item 2 inline five-worker sentence with a deferral to `review-panel-selection.md` (Focused panels arm when every task resolved Tier L with no cumulative risk signal). Three sibling surfaces still speak the pre-edit shape: the worker template's Panel launch paragraph says "The initial pass launches the recommended five-worker panel." with no focused arm (its operative instruction already defers to the supplied `<REVIEW_MODE_NOTES>` set, and two sentences later it carries "A focused pass must record its selection reason"); the Verify-fix vs fresh review table's Fresh review row still reads "Initial full panel or post-fix targeted panel"; and the panel-selection document's orchestrator parenthetical still scopes its execute-plan reference to "per-task intermediate selection" only, not naming the Phase 3 initial-pass deferral.

## Expected

Each surface consolidates toward the single source: the template's Panel launch paragraph defers the initial pass to the supplied worker set without restating a five-worker default; the framing table's Fresh review row reads "Initial panel or post-fix targeted panel"; the panel-selection parenthetical names the Phase 3 initial pass beside per-task selection. Any byte growth in the touched skill files pays with equivalent deletion per the anti-growth rules.

## Why not fixed now

The entry's standing pre-authorization covered only the one sentence swap in Step 3.1 item 2, and the panel-selection document is explicitly not edited by that entry. The finding is Low with no decision-authority loss: the composition decision is orchestrator-side and is now fixed by the item 2 deferral, while the worker template receives its set through `<REVIEW_MODE_NOTES>`.

## Source

- Review record `.ai-playbook/reviews/2026-10-22-execute-plan-phase3-initial-pass-panel-selection-reference-code-review-r1.md` (focused panel, contract-docs plus correctness-completeness, 1 Low staged, 0 blocking).
