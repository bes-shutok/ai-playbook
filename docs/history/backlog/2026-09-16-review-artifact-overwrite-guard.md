# Backlog: add an overwrite guard for review staging artifacts

Status: open
Priority: high

Workflow: backlog
Source: witnessed 2026-09-16 during a repeat pull-request review. The review orchestrator deleted and recreated the existing ignored Markdown review record and sidecar while refreshing findings for a later commit range. The previous round was not archived first.
Severity: High (review artifacts are evidence records, and an ignored-file overwrite is effectively destructive because Git cannot restore it)

## The gap, precisely

1. Review staging artifacts live under an ignored history directory, so normal repository status and Git recovery do not protect them.
2. The staging workflow permits updating a canonical record for the same pass, but it does not provide a mechanical pre-write check that distinguishes same-pass synthesis from a new round.
3. A full-file replacement can therefore erase the earlier panel statistics, findings, comments, and source digest before the new record is written.
4. The existing hard validator checks the resulting record but cannot detect that a prior record was destroyed.

## Fix candidates

1. Add a pre-write guard to the review staging helper: if the target exists and the source digest, head, or round differs, refuse replacement and require a new round path or an explicit archival operation.
2. Before any permitted replacement, create a timestamped immutable backup under the resolved reviews directory and record its path in the new metadata. Do not rely on `/tmp` or an untracked scratch location.
3. Extend the validator or a companion audit command to verify that matching historical rounds are still present and that their sidecars have matching names and digests.
4. Add a test that creates an ignored prior report, attempts a new-head refresh, and verifies that the original bytes remain available and the command selects a new round.

## Acceptance criteria

- No review workflow can overwrite an existing report when the reviewed commit range or round changes without an explicit new-round or archival decision.
- The Markdown and sidecar are treated as an atomic pair: both are preserved, created, or rejected together.
- A failed write leaves the prior report and sidecar intact.
- The guard produces a concise actionable error naming the existing record and the required next-round action.
- The behavior is covered by an automated regression test and documented in both `doing-code-review` and `review-staging`.
