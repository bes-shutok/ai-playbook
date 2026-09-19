Status: open
Priority: High
Created: 2026-09-16

# Add a privacy and secret-redaction gate to review backlog capture

Workflow: backlog
Severity: High
Class: review evidence handling
Source: cross-project review corpus audit, 2026-09-16

Approach update 2026-09-18: the covering plan
(docs/plans/2026-09-16-review-records-contract.md, Task 4) reuses the
existing public-hygiene scanner at backlog-capture time (new explicit-paths
mode on the same script; the shared deny-patterns file stays the single rule
surface) instead of a dedicated redaction script with its own category set,
and adds no done-workflow arm. The fuller policy below (placeholder
conversion, counts-and-field-paths-only reporting, nested sidecar scanning)
remains this item's open scope.

## Problem

Review artifacts are often richer than the durable backlog item needs to be.
The current backlog rules require a problem statement, evidence, location,
severity, source reference, and reason for deferral, but they do not define a
sanitization step or a safe evidence schema. A review-corpus scan found 18
email-like values, 123 absolute user-path occurrences, and 35
credential-assignment-like patterns. These are pattern counts only and were
not copied into this backlog.

An agent synthesizing a deferred finding could accidentally copy reviewer
prose, logs, source excerpts, local paths, or configuration values into a
durable backlog item. The request for PII-free and sensitive-data-free
backlogs therefore needs a repeatable producer gate, not only careful prose.

## Exact location

- `agents/skills/receiving-review/SKILL.md`, Backlog capture
- `agents/skills/review-staging/SKILL.md`, Comment versus Analysis split and
  source references
- `agents/skills/review-reconciliation/SKILL.md`, safe handoff output
- A new shared sanitization helper and tests, used before backlog writes

## Suggested fix

1. Define an allowlist for backlog fields: abstract problem, consequence,
   repository-relative skill or contract location, severity, source kind,
   round class, and validation criteria.
2. Redact or reject email addresses, phone numbers, names, bearer tokens,
   private-key material, passwords, API keys, database endpoints, internal
   URLs, absolute home paths, and raw log or source excerpts unless an
   explicit safe placeholder conversion is applied.
3. Replace source references containing sensitive identifiers with a stable
   local review-family alias and a relative skill path. Keep exact evidence in
   the protected review artifact, not in the backlog.
4. Run the gate before writing the backlog file and again in the hygiene or
   done workflow. Fail closed with counts and field names, never with matched
   values.
5. Add a documented exception for standard license headers and other
   non-PII public text so redaction does not corrupt valid legal metadata.

## Acceptance

- A fixture containing each deny category is rejected or transformed without
  printing the matched value.
- A sanitized backlog item retains enough detail to identify the owning skill,
  the failure mode, the consequence, and the validation needed for closure.
- Standard license text and neutral placeholders pass unchanged.
- The gate scans Markdown and structured fields, including nested sidecar
  values used during synthesis.
- Reports and errors contain counts and field paths only, never raw matched
  values.
- The current four backlog items from this audit pass the gate.

## Why not fixed now

The immediate audit can be completed safely by writing aggregate summaries,
but introducing a reusable redaction policy requires a shared deny-list and
false-positive tests. That policy should be reviewed independently before it
is used to transform existing review history.
