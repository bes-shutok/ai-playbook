# Backlog: define focused-review timing for skill edits

- **Filed:** 2026-10-23, user feedback
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Projects that use shared skills need a clear review point for skill changes; do not defer this solely under the skills repository's personal priority profile.
- **Origin class:** consumer-feedback (company)
- **Class:** fence-class
- **Skill/step:** `agents/skills/how-to-write-skills/SKILL.md`, existing-skill maintenance and revision; review selection in `agents/skills/review-agents/review-panel-selection.md`
- **Severity:** low; the focused panel reviewed the resulting diff before commit and found no actionable issue. The unresolved question is when that panel must run and where the rule belongs.
- **Source reference:** User direction in this session; focused panel record `.ai-playbook/reviews/2026-10-23-branch-review-main-r1.md`, round r1, zero findings. Capture hygiene: `scan-public-hygiene --files` pass.
- **Driving force:** primary: code-quality
- **Dedup probe:** Searched open backlog filenames and Problem bodies for skill-edit review timing. No matching item was found. The nearby panel-capacity item (`docs/history/backlog/2026-10-10-code-review-panel-worker-capacity.md`) concerns launching a required panel, and the panel-composition residual (`docs/history/backlog/2026-10-22-execute-plan-initial-pass-composition-drift-residuals.md`) concerns inconsistent execute-plan wording; neither decides when a skill edit must be reviewed.

## Problem

The skill-authoring guidance covers drafting, evaluating, and revising skills, and says to apply changes using its conventions. It does not specify when a focused review panel must inspect skill changes. In this session, the user required a focused panel for skill changes; the files were edited in the working tree, then the panel reviewed the diff before commit and found no actionable issue. The guidance leaves open whether the panel must review a proposed diff before canonical skill files are written, whether review before commit is sufficient, and whether this is a user preference or a shared authoring rule.

## Expected

Choose the smallest durable home and scope for the review point. If the shared skill-authoring workflow changes, define which skill changes trigger a focused panel, what exact diff it reviews, and whether review must precede writes or only commit. If this belongs only to the operator's user-level instructions, keep shared guidance unchanged. Preserve the current review-panel selection policy and price any added ceremony against the `how-to-write-skills` rule to keep workflow gates short and domain-specific.

## Options to investigate

- Add a focused-panel step to the shared skill-authoring workflow, with the panel reviewing a proposed diff before the canonical skill files change.
- Record the requirement at user level and keep shared skill-authoring guidance unchanged, since the request may be an operator preference rather than a shared workflow contract.
- Clarify that a focused panel may review the working-tree diff before commit, avoiding a separate proposal/apply cycle while keeping review in the change path.

## Why not fixed now

The user asked that skill changes not proceed without a focused review panel and requested a backlog or plan instead of direct skill edits. The panel already reviewed the current changes before commit; choosing the durable scope and timing rule needs its own design decision.
