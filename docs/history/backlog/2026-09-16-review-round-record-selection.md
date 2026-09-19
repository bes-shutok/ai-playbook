# Backlog: enforce new review records for explicitly requested review rounds

Status: open
Priority: high

Workflow: backlog
Source: witnessed 2026-09-16 during a repeat pull-request review. The user explicitly requested that the review run again after additional commits. The review-staging and doing-code-review skills both state that an explicitly requested new round must use a new suffixed record, but the orchestrator reused the existing canonical path and rewrote the previous report.
Severity: High (the review history and evidence boundary were lost even though the workflow had a documented rule for preserving a new round)

## The gap, precisely

1. The current skills distinguish a review pass from a worker-lens update and permit a new suffixed record when the user explicitly requests a new round.
2. The orchestrator recognized the run as a new review over the complete commit range, but still selected the prior report path as the writable canonical artifact.
3. The resulting report mixed current findings with prior-round context and replaced the previous round instead of linking the rounds with `Supersedes` metadata.
4. Because review files are gitignored, the prior report could not be recovered from the product repository's Git history after replacement.

## Fix candidates

1. Make round detection explicit before worker launch. A repeat request such as “run the review again”, “review after these commits”, or a new reviewed head after a posted/final review must allocate the next available `-r<N>` path.
2. Add a small selection helper that enumerates matching Markdown and sidecar records, chooses the next round, and emits the selected paths before synthesis begins.
3. Require the new record to include `Supersedes: <prior-record>` and require the prior record to receive a `Superseded by: <new-record>` marker without changing its findings.
4. Add a regression test for an existing canonical record plus an explicitly requested repeat review. The test should fail if the first record is opened for write or if the new sidecar reuses the old round.

## Acceptance criteria

- An explicitly requested repeat review always creates a new Markdown and sidecar pair with a unique round suffix.
- The prior report and sidecar remain byte-for-byte unchanged except for an intentional, separately recorded supersession marker if that is the selected design.
- The new report links to the prior round, and the prior round links forward to the new round when the workflow supports bidirectional links.
- A worker-lens refresh within the same round still updates the existing canonical record, so the new-round rule does not create unnecessary sibling reports.
- The selection decision is made and recorded before workers launch.
