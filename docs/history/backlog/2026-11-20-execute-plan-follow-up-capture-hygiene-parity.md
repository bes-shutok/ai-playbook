# Backlog: execute-plan follow-up conversion keeps an unconditional capture-hygiene scan

- **Filed:** 2026-11-20, capture-hygiene-private-owning-repo review overflow
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** consumer-contract drift (a second capture consumer keeps a stricter scan rule)
- **Class:** fix-class
- **Driving force:** consistency + reliability
- **Skill/step:** `agents/skills/execute-plan/archive-and-cleanup.md` Phase 4, Follow-up conversion duty; its capture-hygiene scan sentence
- **Dedup probe:** searched open backlog rows for execute-plan follow-up conversion, private-owning capture hygiene, and consumer-surface-scan-mandate-drift; no existing row owns this consumer mismatch

Cluster: docs/history/backlog/2026-11-08-plan-execution-no-candidate-follow-up-disposition-certification-residuals.md (same Phase 4 follow-up-conversion capture procedure; this row owns destination-based scan scope, sibling owns the prior field-remap certification residuals)

## Problem

The execute-plan follow-up conversion duty requires the capture-hygiene scan before an item counts as captured. The receiving-review capture procedure now allows a private repository that owns the finding to skip that scan, while preserving scanning and scrubbing for artifacts sent to shared or public destinations. The two capture consumers therefore give different instructions for the private-owning case.

## Observed versus expected

Observed: `agents/skills/execute-plan/archive-and-cleanup.md:5` states the scan requirement unconditionally. The receiving-review R1 review record filed this as `consistency#consumer-surface-scan-mandate-drift`; the R2 overflow manifest confirms it remains outside the landed branch's owned scope. Expected: follow-up conversion uses the same destination-visibility rule as receiving-review, retaining the scan for shared or public destinations and the private-owner exception for private owning repositories.

## Suggested correction

Align the Phase 4 follow-up conversion scan instruction with receiving-review's destination-visibility rule. Keep foreign-origin items going to shared or public destinations on the scan-and-scrub path. No new machinery is proposed.

## Evidence

- `.ai-playbook/reviews/2026-11-20-capture-hygiene-private-owning-repo-code-review-r1.md`, F1.
- `.ai-playbook/reviews/2026-11-20-capture-hygiene-private-owning-repo-code-review-r2.md`, overflow manifest.
- `agents/skills/execute-plan/archive-and-cleanup.md:5`.
- `agents/skills/receiving-review/SKILL.md`, capture-hygiene destination rule.

## Acceptance

The follow-up conversion and receiving-review capture instructions resolve the private-owning case consistently, while shared and public destinations still require the scanner and foreign-origin scrub.
