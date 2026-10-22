# Plan: Broaden Safe Facts Credential Storage

Backlog origin: docs/history/backlog/2026-10-21-facts-values-safe-loading-and-audit.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-facts-values-safe-loading-and-audit-p5a8516da-r*.md
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Credential-like value: an API key, password, client secret, private key, access token, refresh token, or comparable authenticator.
- Facts store: a local user or repository facts file used for machine-specific configuration.
- OAuth-specific workflow: the existing backup, snapshot, restore, and status instructions in guideline sections 53.2-53.4.
- Sanitized audit: a local review that records only key classifications and owner or consumer categories, never values, account identifiers, or machine-specific paths.

## Why

The task-start rule to read relevant facts was interpreted as permission to print an entire local facts file, exposing a credential-like value. Section 50.6 now governs safe retrieval and output, but section 53.1 prohibits only OAuth access and refresh tokens, leaving other credential types unclear.

## Gist & Examples

TLDR: broaden the facts credential-storage rule after the witnessed disclosure, while keeping the owner-led local audit separate, for code quality.

Before: an agent starts a task and reads a needed facts key. Section 50.6 says to keep sensitive values out of output, but section 53.1 names only OAuth access and refresh tokens, so an API key or password in facts has no equally clear storage prohibition.

After: the agent reads only the needed facts and never prints a secret value under section 50.6. Section 53.1 also prohibits storing any credential-like literal in facts or shared records, while allowing non-secret location and workflow references. The OAuth backup and recovery steps remain in sections 53.2-53.4.

## Outcome

The storage rule clearly prohibits credential-like values in local facts and shared records while safe facts retrieval and the existing OAuth workflow remain clear.

- Agents can resolve local configuration without exposing values in tool output, logs, diffs, or reports.
- Owners have a separate private path to review any local facts and decide whether owner-approved remediation is needed.
- The OAuth-specific backup and recovery instructions remain usable.

Gate delta: none. No gate, validator, scanner, lock, ledger, schema field, or ceremony is added or changed; section 50.6 remains the output-safety rule, section 53.1 gains broader storage coverage, and sections 53.2-53.4 retain the OAuth-specific workflow. No new machinery is justified by one exposure witness without a measured safe catch rate or false-positive cost.

## Assumptions

- Section 50.6 and the task-start pointer in `docs/AGENTS.md` are already landed and remain the read and output contract; basis: current committed source.
- Local facts and credentials are owner-controlled operational data, outside this repository documentation task; basis: the origin backlog classifies the remaining review as owner-led.
- No local facts value is inspected, changed, or rotated by this documentation task; basis: local facts and credentials are owner-controlled.
- No reusable safe audit utility is available, and a new scanner is outside this plan; basis: repository script inventory and the machinery admission protocol.

Decision points requiring a grill: none remain.

## Standing constraints

- Never write local facts values, account identifiers, or machine-specific paths to tracked files, review artifacts, tool output, logs, or reports.
- Do not edit owner-controlled facts or credential stores, inspect remote state, or rotate credentials under this plan. Give owners only sanitized recommendations; any such action requires separate owner direction.
- Keep safe retrieval and output behavior in section 50.6. Do not duplicate its procedure or the OAuth workflow in lower-tier instructions.

## Evaluation Criteria

**Quality dimensions:**
- Confidentiality: the policy change exposes no credential values, account identifiers, or machine-specific paths.
- Correctness: the storage rule covers credential classes beyond OAuth tokens and keeps the current OAuth workflow intact.
- Simplicity: the fix reuses the existing safe-read guidance and adds no scanner or other machinery.

**Done when:**
- Section 53.1 clearly prohibits credential-like literals in facts and shared records while allowing non-secret references.
- Sections 53.2-53.4 preserve the existing OAuth backup, snapshot, restore, and status behavior.
- Section 50.6 remains the single safe-read and output rule, and `docs/AGENTS.md` retains its concise task-start pointer.

**Ship when:**
- Before the witnessed exposure is described as fully resolved, the facts owner privately reviews the applicable local stores and removes every confirmed credential-like literal. Any confirmed active credential is revoked or invalidated, a replacement is issued or migrated through its owner-approved secret workflow, and its consumers are verified against the replacement. If the owner accepts residual exposure, the documentation change may be complete, but the exposure remains unresolved and must not be reported as fully resolved. This remains a separate owner operation, not a task or release gate: `OPERATIONS_FOLLOW_UP`; owner: the facts or credential-store owner; completion evidence: the owner's private decision and, when applicable, private consumer verification. No values, identifiers, or machine paths enter this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none

**Tests:**
- none; the plan changes documentation only and adds no audit utility.

**Documentation:**
- `projects/.ai-playbook/agent_workflow_guidelines.md` (section 53.1; sections 50.6 and 53.2-53.4 are frozen except to correct a contradiction introduced by this task)
- `docs/AGENTS.md` (retain its one-line pointer to section 50.6; do not duplicate the procedure)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- User and repository facts files, credential directories, and machine-local credentials scripts; no values are changed under this plan.
- A new scanner, validator, gate, lock, ledger, or ceremony; no measured safe catch or false-positive evidence supports it.
- Remote state and credential rotation; these require a separate owner direction.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-22-facts-values-safe-loading-and-audit.md
python3 scripts/plan_readiness.py docs/history/plans/2026-10-22-facts-values-safe-loading-and-audit.md
bash scripts/scan-public-hygiene.sh --files projects/.ai-playbook/agent_workflow_guidelines.md docs/AGENTS.md
git diff --check
bash scripts/check-no-em-dash.sh touched
```

### Task 1: Generalize the facts credential-storage rule

Context surface: the plan's Terms, this task, and Standing constraints.

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `docs/AGENTS.md`

- [x] Given a local facts store contains an API key, password, client secret, private key, or comparable authenticator, section 53.1 prohibits storing the literal value while allowing only non-secret location or workflow references. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a shared record such as committed documentation, Jira, or Slack contains an API key, password, client secret, private key, or comparable authenticator, section 53.1 prohibits storing the literal value there while allowing only non-secret location or workflow references. [class: IMPLEMENTATION_REQUIRED]
- [x] Given task-start facts are needed, section 50.6 remains the only safe-read and output rule and `docs/AGENTS.md` points to it without duplicating its procedure. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the existing OAuth backup and recovery workflow, sections 53.2-53.4 retain its current backup, snapshot, restore, and status behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Given section 53.1 covers credential classes beyond OAuth, the section 53 heading describes credential storage generally while sections 53.2-53.4 remain clearly OAuth-specific. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: broaden safe facts credential storage rule` [class: IMPLEMENTATION_REQUIRED]
