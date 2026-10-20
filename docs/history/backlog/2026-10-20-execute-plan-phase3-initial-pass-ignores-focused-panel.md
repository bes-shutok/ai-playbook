# Backlog: execute-plan Phase 3 initial pass reads as a mandatory five-worker panel, overriding the panel-selection focused arm for narrow execution deltas

- **Filed:** 2026-10-20, operator-directed resume of the done-immediate-commit-single-homing closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-10-code-review-panel-worker-capacity.md (same surface: Phase 3 panel launch cost and worker capacity)
- **Cluster:** docs/history/backlog/2026-10-05-execute-plan-risk-floor-panel-cap-conflict.md (same surface: Phase 3 panel composition rules in tension)
- **Origin class:** observed cost gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` (Step 3.1 item 2 "Initial pass: fresh adversarial five-worker review"; verification gate item 7); `agents/skills/review-agents/review-panel-selection.md` (Focused panels; Per-task intermediate review selection)
- **Driving force:** cost (review tokens proportional to the delta's risk, not to the ceremony)

## Problem

`review-panel-selection.md` is the declared single source for panel composition and permits a focused Phase 3 panel when work is demonstrably narrow and the risk-signal floor allows it (docs-only prose: `contract-docs` plus `correctness-completeness`). The execute-plan Step 3.1 text states the initial pass as "fresh adversarial five-worker review" with no pointer to that arm, and the gate's item 7 names the five rows a full-panel pass needs. Read together in a run, the inline sentence wins: the 2026-10-20 done-immediate-commit-single-homing Phase 3 launched five parallel lens workers (about 2.6 million sub-agent tokens, 7 minutes wall) over a delta of two placement-pin operand swaps and three archive records whose intermediate review had already resolved to the derived single-reviewer tier. All five findings were Low and non-blocking; three lenses re-ran the same pins suite, hygiene scan, and registry validator. The sibling run worktree-rebase-feature-start-boundary the same day chose a focused four-lens panel, so the two runs read the same text differently.

## Expected

Step 3.1 item 2 names the panel-selection document as the composition source for the initial pass too (not only the per-task tier), carrying the Tier L signal forward: when every task's intermediate review resolved to Tier L and the cumulative diff adds no risk signal, the initial Phase 3 pass is the focused docs-only or test-only panel with `panel_mode: focused` and a recorded selection reason, and the five-worker panel remains the default whenever evidence does not justify narrowing. Gate item 7 already accepts a focused pass with its selection reason; no gate change.

## Why not fixed now

The sentence sits in the shared execute-plan monolith and touches how the gate reads a clean round; a one-clause edit still needs the review panel to confirm it does not weaken the risk-signal floor. The anti-growth rules apply: the fix replaces the inline composition sentence with the reference, deleting bytes.

## Source

- Phase 3 r1 record `.ai-playbook/reviews/2026-10-20-done-immediate-commit-single-homing-code-review-r1.md` (five lenses, 5 Low, 0 blocking); landing cfb909995.
