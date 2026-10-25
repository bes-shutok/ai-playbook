# Backlog: reduce duplicate self-heal recovery guidance

- **Filed:** 2026-10-25, review-loop r12 F1 and r13 F1
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Owner:** self-heal and review-loop skill maintainers
- **Trigger:** next change to either skill or before the operative-text byte-budget gate is promoted
- **Origin class:** self-serving
- **Class:** fix-class (the recovery contract needs a simpler, balanced expression)
- **Driving force:** simplicity (primary), docs (secondary)
- **Source:** `.ai-playbook/reviews/2026-10-25-branch-review-main-code-review-r12.md` F1; `.ai-playbook/reviews/2026-10-25-branch-review-main-code-review-r13.md` F1; capture hygiene: `scan-public-hygiene.sh --files` pass

## Problem

The review-loop stop path can request a second self-heal assessment after active-churn handling already recorded its disposition. Across the same branch, the new self-heal skill and consumer edits also add substantially more operative text than they remove, with some recovery and integration guidance repeated. This makes ownership of the disposition and the maintenance cost harder to see.

## Exact location

- `agents/skills/review-loop/SKILL.md`, Exit criteria and orchestration rule 5.
- `agents/skills/self-heal/SKILL.md`, Recovery and Integration Points.
- Consumer integration lines in `plans`, `execute-plan`, `review-plan`, `using-skills`, and `maintenance` skills.

## Suggested fix

Consolidate recovery guidance so an active run reuses its recorded self-heal disposition before a standalone stop. Trim repeated wording across the skill and its consumer integrations, preserving caller budgets, hard gates, owner handoff, and bidirectional integration. When the byte-budget gate is promoted, pay for any growth past the cap with equivalent deletions in the same change.

## Why not fixed now

Both review findings were Low and non-blocking. The loop does not launch extra rounds solely to chase non-blocking findings, and the new skill's core behavior is covered by its current blocking-clean review. Preserve the simplification work for the next scoped edit rather than expanding this recovery change again.

## Dedup probe

Searched open backlog filenames and Problem sections for `review-loop self-heal duplicate invocation`, `self-heal disposition`, and `unbalanced operative-text growth`; no matching item found before this combined item. The two findings share the same redundant recovery-guidance root and are tracked together.
