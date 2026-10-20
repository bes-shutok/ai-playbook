# Backlog: prevent sensitive local facts from reaching agent output

- **Filed:** 2026-10-21, after a task-start full-file read exposed a local credential-like value in tool output
- **Status:** open
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
