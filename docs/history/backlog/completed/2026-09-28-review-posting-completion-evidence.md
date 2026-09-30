# Review completion can be reported before inline comments are verified

Captured: 2026-09-28 (source: consumer PR review session)
Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-review-posting-landing-receipt.md, squash main 294d1297, exec review r3 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: consumer-feedback (company)
Consumer urgency: Any consumer using staged PR reviews needs the completion claim and staging status to reflect comments observed on the live pull request, not merely a successful submission response.

## Problem

The review workflow requires a post-submission fetch and a comparison between the intended findings and the live PR comments. In one recent review session, the agent reported that all four approved findings had been posted after submitting the review, but the user could see only the approval. The missing inline comments were posted only after the user challenged the completion report.

The written instruction already prohibits treating a successful submission response as completion. The incident shows that this procedural requirement can be skipped while both the user-facing report and staging state imply success.

## Expected

- A PR review cannot be reported complete, and its staging record cannot transition to `POSTED`, until each intended finding has matching live comment evidence.
- The posting workflow records the intended finding set and the observed landed set, with a clear incomplete outcome for missing comments.
- A missing comment triggers the existing individual-repost recovery path, followed by verification of the full intended set.
- A focused check or validator rejects a completion receipt whose landed evidence is absent, incomplete, or mismatched by path, line, and distinctive body fragment.

## Evidence

In a recent PR review session, the user requested posting all pending findings and an approval. The agent reported that four inline findings had landed, but the user observed only the approval. The agent then posted the four findings separately and verified them. This is a witnessed skip of the existing post-submission landing-verification requirement, not a gap in the stated policy.

## Exact location

- `agents/skills/doing-code-review/SKILL.md`, Posting Staged Findings and Direct Mode.
- The posting helper or review staging validator, if a machine-readable landing receipt can be added without duplicating the source of truth.

## Why not fixed now

This capture reviews recent sessions and records improvement work; it does not change the review posting contract or its implementation.

## Dedup probe

Search terms: `inline comment posting verification`, `intended-vs-landed`, `POSTED without landing evidence`, `silent batch drop`. The existing `doing-code-review` skill already specifies live verification and recovery. No open, completed, or deferred backlog item was found that addresses enforcement or auditable evidence for that requirement.

## Suggested fix

Trace the current posting and staging-validation path. Add the smallest machine-checkable receipt that binds the intended finding identities to comments fetched from the PR after submission, and allow `POSTED` only when the complete set matches. Keep the existing individual-repost recovery and incomplete-status behavior. Add focused coverage for a successful batch, a silently dropped finding, a mismatched comment, and successful recovery; do not weaken the current verification rule.
