---
name: review-reconciliation
description: "Reconcile recurring, contradictory, or non-converging review artifacts before another review round. Use when a review loop re-finds the same root issue, fixes generate new findings, review artifacts disagree, or a review cap is reached without a trustworthy closure."
---

# Review Reconciliation

Use this skill when ordinary review and fix cycles have stopped producing trustworthy progress. It is a reconciliation pass, not another independent review. Its job is to explain why the review is stuck, repair the review artifact or review machinery when authorized, and hand the result back to the original orchestrator for a fresh review.

## Trigger

Invoke this skill when any of these conditions holds:

- the same root issue appears in two consecutive rounds, even when finding wording or IDs change;
- a fix to one component or contract family regenerates findings in the next round;
- staged artifacts, triage records, or source digests disagree about what was reviewed or what was fixed;
- the review cap is reached with unresolved blocking findings;
- a clean round is not credible because the panel did not re-probe changed or "settled" mechanisms;
- the panel cannot agree whether the issue is a real defect, a missing test, a scope error, or a review-catalog gap.

Do not invoke it for one ordinary finding, one failed worker, or a normal requested review. A worker timeout is handled by the caller's relaunch rule unless the timeout has left competing or incomplete review artifacts that affect the verdict.

## Inputs

The caller supplies, or this skill discovers from the current workspace:

1. The artifact under review and its current source digest when one exists.
2. Every relevant prior review artifact, sidecar, triage record, fix log, and user decision for the affected rounds.
3. The caller's review type, round counter, configured cap, unresolved findings, and mutation scope.
4. The applicable review-staging rules and any project or user instructions that define ownership or evidence.

Read the artifact history in chronological order. If a prior round cannot be located or its source digest cannot be established, record that as an evidence gap instead of treating the latest prose as authoritative.

## Reconciliation method

### 1. Build the recurrence map

Normalize each finding to a root issue, not its finding ID or exact wording. Group findings that share a violated invariant, data flow, owner, or missing witness. Preserve distinct issues when they have different consequences, owners, or fixes.

For every group, record:

| Field | Required question |
|---|---|
| History | In which rounds did it appear, disappear, or return? |
| Current truth | Does the issue reproduce against the current artifact or source? |
| Change relation | Did the prior fix touch the affected path, or is this a surviving sibling? |
| Owner | Which artifact, implementation layer, test, guideline, or external decision owns closure? |
| Witness | What exact test, structural check, runtime path, or decision receipt proves closure? |
| Failure mode | Incomplete fix, split source of truth, ambiguous contract, missing class coverage, stale review, wrong owner, or catalog gap? |

Use the actual reviewed bytes and execution evidence where the finding depends on them. Treat statements such as "covered," "inherited," "validated," or "unchanged" as claims to re-probe, not closure evidence.

### 2. Separate the kinds of stuckness

Classify each recurring group as exactly one primary disposition, with secondary causes if needed:

- **Real residual**: the current artifact still permits the reported failure.
- **Sibling residual**: the fix covered one member of a broader class; enumerate and close the class.
- **Verification gap**: behavior is correct or likely correct, but the stated witness cannot prove it.
- **Artifact contradiction**: plan, review, sidecar, source digest, or triage state describes different realities.
- **Ownership or scope error**: the finding belongs to another artifact or an external decision.
- **Review-catalog gap**: the panel lacked a lens or prompt that could detect the issue reliably.
- **Evidence blocked**: the required environment, owner, or decision is unavailable.

Do not downgrade a real residual to a verification gap merely because a test is missing. Do not change product behavior to make a review artifact easier to close.

### 3. Refactor only the authoritative layer

When mutation is authorized, make the smallest coherent change at the owning layer:

- revise the plan, RFC, or review artifact when the design or closure contract is incomplete;
- revise the review staging or sidecar when the recorded review state is stale or contradictory;
- revise the responsible review catalog or orchestrator rule when the panel missed a reusable defect class;
- record a decision gate when closure depends on a material architecture, scope, rollout, or external-owner choice.

Keep one source of truth for each invariant. Replace local wording patches with a matrix, ledger, state transition, or explicit witness when the repeated problem is caused by distributed prose. Preserve historical artifacts; link the reconciliation result to them rather than rewriting their findings into a new verdict.

This skill does not implement production code, commit, push, post review comments, or silently accept an external prerequisite. If the caller did not authorize edits, return a concrete patch plan and closure ledger instead.

### 4. Return control to the original orchestrator

After any artifact, catalog, or rule change, the original caller must launch a new review using its normal worker selection, staging format, source-digest gate, and exit criteria. The reconciliation pass cannot approve its own refactor, convert its own findings to a clean result, or replace the caller's review panel.

The caller must reset the recurrence counter only after that fresh review is complete. If the fresh review reopens the same root group, retain the previous recurrence chain and escalate to the user or the caller's configured stop condition instead of looping silently.

## Output contract

Return a concise result with these sections, and write the durable artifact when the caller's review workflow requires staging:

1. **Trigger**: the exact non-convergence condition and affected rounds.
2. **Recurrence map**: one row per root issue, including disposition, owner, and current status.
3. **Invariant and witness ledger**: the authoritative statement and observable proof required for each unresolved group.
4. **Changes made or proposed**: files, sections, and why the selected layer owns the correction.
5. **Decision requests**: only material choices that cannot be resolved from the available evidence.
6. **Handoff**: the original orchestrator, fresh source digest to review, worker set, and the condition for resuming or stopping.

Use these terminal statuses:

- `reconciled`: the artifact or review machinery was coherently refactored and is ready for a fresh caller-owned review;
- `needs-decision`: a material user or external-owner choice blocks a safe refactor;
- `catalog-gap`: a reusable detection gap was identified and its catalog change is still pending;
- `evidence-blocked`: closure depends on unavailable measurement or environment access;
- `no-recurrence`: the supplied history does not support a stuck-review diagnosis.

## Caller handoff template

Review orchestrators should pass this context when invoking the skill:

```text
Review reconciliation handoff
- Artifact under review: <path or external identifier>
- Review type and original orchestrator: <type>, <skill>
- Current digest: <digest or unknown>
- Review artifacts: <chronological paths or identifiers>
- Fix and triage history: <paths or summaries>
- Recurring trigger: <same root, regeneration, contradiction, cap, or evidence gap>
- Mutation scope: <read-only | named artifact/catalog paths>
- Required return: recurrence map, closure ledger, changes, decisions, and fresh-review handoff
```

The caller owns the next review. Its final report must link the reconciliation artifact and the fresh review that follows it.

## Integration Points

### With review orchestrators

`review-loop`, `review-plan`, `execute-plan`, `rfc-design`, and `receiving-review` invoke this skill at their documented non-convergence trigger. They provide the history and mutation scope, then resume only after the reconciliation result is recorded. After a change, the same original orchestrator runs the fresh review.

### With review-staging

Use the resolved `{reviews_dir}` and the existing staging hierarchy. Reconciliation supplements review artifacts with a recurrence and closure ledger; it does not replace the original round's immutable findings or sidecar statistics.

### With receiving-review

Use the existing triage and backlog rules for valid findings that are deferred. Reconciliation explains recurrence or ownership; it does not turn a blocking finding into a backlog item without the caller's normal triage decision.

### With review-agents

When a review-catalog gap is confirmed, identify the smallest abstract lens or orchestrator rule that should be updated. Keep repository-specific details in project overlays or guidelines, not in a generic catalog.
