# Backlog: prevent sensitive local facts from reaching agent output

- **Filed:** 2026-10-21, after a task-start full-file read exposed a local credential-like value in tool output
- **Status:** covered
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed confidentiality exposure
- **Class:** investigate-class (safe-read guidance now exists; current local facts still need an owner-led audit and any required remediation)
- **Driving force:** security
- **Source reference:** current session, sanitized; no credential value, key, or machine path retained
- **Dedup probe:** `agent_workflow_guidelines.md` §53.1 prohibits access and refresh tokens in facts, and `2026-10-11-done-sensitive-scan-neutral-token-assignment.md` covers scanner false positives; neither covers safe retrieval from facts or auditing other credential-like values already stored there.

## Problem

The task-start instruction to read facts was interpreted as permission to print an entire local facts file. That output included a credential-like value unrelated to the task. The instruction now requires retrieving only needed keys or sections, and keeping sensitive values out of tool output, logs, diffs, and reports. The stored facts still need a safe, owner-led review: existing policy names access and refresh tokens, while other credential forms may also be present. Do not copy values into this backlog, tool output, or reports.

## Expected

Determine which local facts stores may contain credential values, review them without printing values, and move or remove any such values through their owner-approved secret-storage workflow. Keep only paths or selectors in facts. Preserve required local workflow by verifying each consumer uses the approved secret source after remediation. Record only sanitized findings and the remediation outcome.

## Investigation scope

- Reconcile the existing facts storage rules with the newly added minimal-read rule.
- Identify applicable facts stores and their owners without publishing machine paths or values.
- Check whether the available secret-scanning method can inspect local facts without exposing matched content; if not, identify a safe alternative.
- Determine whether a reusable facts schema rule or checker is justified, with evidence for expected catch frequency and false-positive cost before recommending new machinery.
- Distinguish the completed instruction change from any remaining local data remediation.

## Review residual: preserve the remaining OAuth guidance

- **Status:** covered
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class (documentation scope gap; no new gate proposed)
- **Origin class:** self-serving
- **Driving force:** code-quality
- **Source reference:** `.ai-playbook/reviews/2026-10-22-plan-review-facts-values-safe-loading-and-audit-p5a8516da-r4.md`, overflow `consistency#oauth-guidance-scope`; capture hygiene: `scan-public-hygiene --files` pass.
- **Location:** `projects/.ai-playbook/agent_workflow_guidelines.md`, sections 53.5-53.7.
- **Problem and evidence:** The credential-storage plan changes section 53's heading and rule to cover all credential types, but its explicit frozen scope and acceptance checks preserve only sections 53.2-53.4. Sections 53.5-53.7 also contain OAuth-specific cross-reference and authentication/restore guidance. Omitting them from the preservation witness could leave those instructions out of the later implementation's review.
- **Suggested fix:** During plan execution, preserve all existing OAuth-specific guidance in sections 53.2-53.7 while broadening section 53.1; add explicit scope and acceptance witnesses for sections 53.5-53.7 if the implementation plan does not already cover them. Do not duplicate or rewrite the OAuth procedure without a demonstrated contradiction.
- **Why not fixed now:** The authoring plan has a clean terminal review with no blocking findings. This consequence-bearing, non-blocking scope extension is outside the certified plan's stated edit boundary; it is captured for separate triage rather than silently widening that boundary.
- **Dedup probe:** searched open backlog filenames and problem bodies for `facts-values-safe-loading`, `OAuth guidance`, and `sections 53.5-53.7`; the existing `2026-10-21-facts-values-safe-loading-and-audit.md` is the same root work item and already owns section 53 credential-storage guidance, so this residual is appended here rather than split into a micro-item.
