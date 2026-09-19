Status: open
Priority: Medium
Created: 2026-09-16

# Add a machine-readable recurrence index for non-converging reviews

Workflow: backlog
Severity: Medium
Class: review-loop and reconciliation observability
Source: cross-project review corpus audit, 2026-09-16

## Problem

The review-reconciliation skill requires a recurrence map and a mandatory
design-reflection gate after a third recurrence. The review-loop skill also
requires reconciliation before continued churn or a sixth full panel. These
rules are currently procedural: the corpus has no shared index or validator
that proves consecutive rounds were grouped by the same artifact, source
digest, invariant, or normalized Pattern ID.

The audit found 510 sidecar artifact families, 205 with at least two rounds,
and 115 families with a finding Pattern repeated in multiple rounds. The most
repeated classes are simplification, always-passing tests, stale
cross-references, unchecked coverage claims, and hermeticity gaps. One family
has 39 recorded sidecar rounds and several others have more than ten. These
counts do not prove every family is a live non-convergence incident, but they
do prove that manual recurrence detection is costly and error-prone.

## Exact location

- `agents/skills/review-reconciliation/SKILL.md`, recurrence map and
  design-reflection gate
- `agents/skills/review-loop/SKILL.md`, reconciliation trigger and round cap
- `agents/skills/review-staging/SKILL.md`, source digest, artifact identity,
  Pattern ID, and immutable statistics fields
- A new read-only recurrence-index helper and fixture tests

## Suggested fix

1. Build a read-only index from sidecars using repository-relative artifact
   identity, source kind, source digest, round, finding Pattern ID, anchor, and
   triage state. Treat artifact slugs as labels, not authoritative identity.
2. Normalize finding recurrence by invariant and canonical Pattern ID while
   preserving distinct owners, consequences, and fixes. Missing or invalid
   fields become explicit evidence gaps rather than guessed matches.
3. Detect consecutive recurrence, sibling recurrence, digest disagreement,
   missing-round artifacts, and cap exhaustion. Produce a compact report and
   a reconciliation handoff containing only safe identifiers and counts.
4. Add a hard gate or explicit warning when the third recurrence is reached:
   the reconciliation record must evaluate an alternative representation or
   record why the current representation is retained.
5. Add a post-reconciliation check that the original orchestrator, rather than
   reconciliation itself, owns the next fresh review and final verdict.

## Acceptance

- Reordering finding IDs or changing wording does not hide a recurrence when
  the invariant and Pattern ID remain the same.
- Different source digests or owners are not merged merely because their
  slugs match.
- A missing prior artifact, invalid Pattern ID, or absent sidecar appears as an
  evidence gap with a stable reason code.
- Fixtures cover two-round recurrence, third-recurrence design reflection,
  non-consecutive rounds, sibling residuals, digest disagreement, and a clean
  independent round.
- The report contains no review prose, emails, credentials, internal URLs, or
  absolute machine paths.
- The helper is read-only and does not certify a review or alter immutable
  staging statistics.

## Why not fixed now

The existing skills define the right human decision points, but adding an
index changes how review history is grouped and must be validated against
several artifact shapes first. It should be implemented with the record-kind
contract so the index does not encode filename-based guesses.
