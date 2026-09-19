Status: open
Priority: High
Created: 2026-09-16

# Distinguish canonical, reconciliation, worker, and legacy review records

Workflow: backlog
Severity: High
Class: review-staging contract
Source: cross-project review corpus audit, 2026-09-16

## Problem

The review staging contract describes one canonical Markdown record plus one
sidecar, while the corpus also contains reconciliation notes and worker-
specific evidence documents. The validator currently evaluates these shapes
as if they were all canonical records.

The post-2026-09-09 audit found 330 recent Markdown records. Thirty-nine fail
the current hard validator. Ten recent Markdown records have no matching
sidecar, and several recent failures are reconciliation or worker-specific
documents that intentionally do not have the full canonical hierarchy. Across
the full corpus there are 629 legacy sidecars, mostly predating the extended
freshness fields, plus 302 sidecars without a source digest.

This makes it difficult to tell whether a failure means a producer violated
the current standard, a historical record needs migration, or a supplemental
artifact was sent through the wrong validator mode. It also weakens the
review-loop claim that every round has a trustworthy, machine-readable record.

## Exact location

- `agents/skills/review-staging/SKILL.md`, canonical record and JSON sidecar
  contracts
- `agents/skills/review-reconciliation/SKILL.md`, supplemental reconciliation
  output and handoff contract
- `agents/skills/review-loop/SKILL.md`, every-round staging and clean-exit gate
- `scripts/validate_review_staging.py`, record validation and date-fenced rules
- Producer skills: `doing-code-review`, `review-plan`, `rfc-design`, and
  `review-confluence-doc`

## Evidence

- Recent hard-validator failures: 23 in the personal playbook corpus, 11 in a
  company platform corpus, and 5 in a company profile corpus.
- Recent Markdown records without a matching sidecar: 10.
- Repeated failures include missing Review Statistics, missing freshness
  metadata, invalid current Pattern IDs, and sidecars with legacy or
  incomplete shapes.
- The corpus contains 205 repeated sidecar families, so record identity and
  round lineage are not edge cases.

## Suggested fix

1. Add an explicit `record_kind` to the sidecar and Markdown Metadata, with
   values such as `canonical`, `reconciliation`, `worker-evidence`, and
   `legacy-import`.
2. Define the minimum contract for each kind. Canonical records keep the full
   Review Statistics and finding hierarchy. Reconciliation records carry the
   recurrence map, witness ledger, changes, decisions, and handoff. Worker
   evidence records carry their worker, lens, status, and source reference.
3. Require a sidecar for every new record kind, but validate it against the
   selected kind. Never infer the kind from a filename or silently downgrade a
   failed canonical record to legacy.
4. Add a migration report that classifies existing records without rewriting
   historical findings. Records before the freshness fence remain accepted as
   historical; new records must satisfy the appropriate current contract.
5. Add producer self-tests for canonical, reconciliation, worker-evidence,
   legacy-import, missing twin, wrong kind, and invalid Pattern ID cases.

## Acceptance

- Every post-fence producer output declares one record kind and has a matching
  sidecar.
- The hard validator accepts a valid reconciliation record without requiring
  canonical finding sections, while rejecting a canonical record that omits
  them.
- A missing twin, wrong kind, stale digest, or invalid current Pattern ID
  produces one actionable error naming the owning producer.
- Historical records remain readable and are reported as migration debt, not
  silently rewritten or treated as current clean evidence.
- A clean review-loop exit requires a valid canonical record for the review
  round; supplemental records cannot certify their own refactor.
- Tests cover both a valid record of each kind and each cross-kind failure.

## Why not fixed now

This is a shared contract change across several producer skills and the
validator. Applying ad hoc edits to the 39 recent failures would risk changing
the meaning of historical evidence and would create more format variants.
