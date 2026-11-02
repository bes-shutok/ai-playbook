# Backlog: staged code reviews can miss branch behavior and outlive the PR head

Status: covered (docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md)
Priority: high
Consumer urgency: Consumer projects using the shared review skills need the staged review to match the current PR head and its coverage claims to cite real assertions; do not defer this as skills-repository-only formal-hardening.
Origin class: consumer-feedback (company)
Class: fence-class
Driving force: reliability
Added: 2026-11-02, user-directed follow-up to a code-review session; repository and PR identifiers omitted
Capture hygiene: `scan-public-hygiene.sh --files` pass.

## Problem

The initial five-worker review was tied to an earlier PR snapshot. Two actionable behaviors already present in that snapshot were not found: a blank business identifier bypassed the documented fallback, and a rejected result still incremented a legacy success counter. The testing worker described mapping coverage, but the reviewed tests exercised only populated identifiers and did not assert the rejected-result metric behavior.

A later PR commit added a throwing terminal retry hook after the application retry budget. The original panel could not find that behavior because it was absent from its snapshot. The old staged review was then used against the newer head without a fresh review. This is a review-freshness failure, not a miss by the original panel.

There were also two unsupported or incorrect comments in the review exchange. A later reviewer said an `invalid` counter was absent, although the conversion-failure path already emitted it. My earlier Low comment inferred a deduplication risk from identifiers emitted by separate live and baseline paths. The user established that those values can arrive through different paths and at different times, and no same-record relationship was verifiable in this project. The README expectation alone did not prove that consequence. Do not carry either claim forward as a valid finding.

## Exact location

- `agents/skills/doing-code-review/SKILL.md`, staged Metadata, review synthesis, and Posting Staged Findings.
- `agents/skills/github-pr-workflow/SKILL.md`, PR context resolution and active review posting.
- `agents/skills/review-staging/SKILL.md`, reviewed source digest and record Metadata.
- `agents/skills/review-agents/testing.md`, test evidence and edge-case coverage.
- `agents/skills/review-agents/quality.md` and `agents/skills/review-agents/review-panel-selection.md`, correctness ownership and worker coverage.

## Suggested direction

Keep the standard five-worker panel. In a focused plan, determine the smallest changes that make the existing review evidence more dependable:

1. Bind a staged PR review to the resolved head identity or another canonical identity for the exact reviewed bytes. Before posting, re-resolve the current head and mark the record stale if it moved. Choose whether the bounded recovery is a fresh full review or a reviewed delta that is proven to cover the new bytes.
2. When a changed mapping or fallback accepts identifiers, have the testing worker name the input partitions and cite the test name and assertion for each relevant behavior, including blank or absent values when the contract covers them.
3. When a changed terminal result feeds multiple metrics, have correctness-completeness trace each outcome through every emitted metric and cite the branch evidence. Do not infer metric omissions from a metric definition alone.
4. Require evidence of a real data relationship before comparing identifiers from separate event paths or claiming a deduplication consequence. A README expectation can establish intended behavior, but it does not establish that two independently sourced values identify the same record.

Preserve the existing panel size, worker ownership, and finding budget. Price any new required pre-post check under the machinery admission protocol. Do not add an automated blocker or a new worker without evidence that the smallest text and metadata change cannot address the witnessed failures.

## Evidence and scope

Impact: High, because a staged review can be posted as current after the PR changes, while branch-level behavior and its tests can be described as covered without evidence of the relevant input or assertion. The review chronology and the user's correction are the incident witness for this item; specific repository identifiers are omitted.

Why not fixed now: this request is to capture and investigate the process failure. The smallest owner and surface need to be chosen across the shared review orchestrator, panel prompts, staging record, and PR workflow before changing shared guidance.

## Dedup probe

Searched open backlog titles and problem text for review-head freshness, stale staged reviews, code-review coverage misses, and branch-to-assertion gaps. The archived-source-path item is about plan archival invalidating a historical review artifact and already has a PLAN-PROMPTS entry; it does not cover a PR head moving between review and posting. The staging scaffold and panel-selection pointer items are already represented in their rolling logs. The remaining producer and validator residuals concern record construction or schema, not current-head freshness or missed runtime branches. No eligible open sibling covers this defect class.
