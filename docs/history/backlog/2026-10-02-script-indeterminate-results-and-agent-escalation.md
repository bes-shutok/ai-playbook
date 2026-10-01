# Return uncertain script findings for agent decisions

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** user-request
- **Class:** fix-class
- **Driving force:** code-quality

## Problem

Scripts used by agents often classify repository state and recommend or gate consequential actions. A binary result can overstate what the evidence proves: a false positive can make the agent discard valid work, while a false negative can let unsafe or incomplete work proceed. When the observed state is mixed, inconsistent, incomplete, or outside the script's modeled cases, returning a definitive pass or failure can cause the agent to follow the wrong result without investigating.

The recent dirt-regression gate incident is one example. Per-hunk comparison treated removed imports and exact lines moved between hunks as behavioral regressions. The agent followed the gate's result and stopped closeout before committing, even though the reported files did not represent reverted behavior.

## Expected

Define a shared outcome contract for scripts that classify or gate agent work. It distinguishes:

- **Pass:** evidence satisfies the script's stated condition.
- **Fail:** evidence establishes a modeled violation, with the offending evidence identified.
- **Indeterminate:** available evidence is insufficient, contradictory, partially parsed, or outside the modeled cases. The script reports what it observed and what it could not determine, and leaves the decision to the agent.
- **Tool error:** the script could not perform its check reliably, such as missing inputs, unsupported data, an internal failure, or an unheld operating-context assumption. It must not be represented as a pass or as a domain finding.

An agent must not treat `indeterminate` or `tool error` as pass/fail, or continue a dependent destructive or landing action on that result. Known cases keep deterministic behavior; escalation is for uncertainty, not a substitute for implementing expected cases.

Each script also declares the operating-context assumptions its result depends on (repository root and checkout context, branch or lock state, input presence and freshness, invocation outside the modeled context) and classifies the violation of an unheld assumption as a tool error or an indeterminate outcome, never as a domain pass or fail: a script run under wrong assumptions or unexpected circumstances must not produce a confidently wrong classification. (Operator direction, 2026-10-02: adopt this for all decision-making scripts, not only the gate that prompted the item.)

## Suggested fix

Inventory ai-playbook scripts that make decisions about edits, staging, commits, restoration, cleanup, archival, review closure, or other workflow transitions. Rank them by the consequence of a wrong classification and by how easily their operating-context assumptions are violated in use, then define a common machine-readable outcome shape with a short human-readable explanation and evidence references. Keep each script's domain-specific criteria explicit while making uncertain and execution-error states distinguishable from positive and negative findings.

Update the highest-risk scripts first, beginning with `scripts/dirt_regression_gate.py`. For each updated script, add fixtures for established pass/fail cases, boundary cases, malformed or unsupported input, mixed evidence, and at least one previously unmodeled shape. Verify its callers branch explicitly on every outcome and return the evidence to the agent when a decision is required. Do not silently widen a classifier's pass or fail rules to make an unexpected case fit.

Provide a migration path for existing scripts, such as a shared result type or a documented compatibility adapter. The adapter must preserve old behavior only for cases that are explicitly classified as known; it must not collapse `indeterminate` into success or failure.

## Evidence and related work

- In this session, the dirt-regression gate classified import cleanup and line movement across diff hunks as reversion. Focused fixtures and a classifier change corrected those known cases, but the incident exposed the lack of a general outcome for cases the classifier had not modeled.
- Completed work such as `docs/history/plans/completed/2026-09-24-p55-audit-deployment-gaps-gate-blind-spots.md` makes specific gates report known deployment gaps and blind spots. It does not establish a shared uncertainty contract for all decision scripts and their callers.
- The separate open item `docs/history/backlog/2026-10-02-project-configurable-worktree-policy.md` covers how work dispatch selects a checkout; this item covers how scripts communicate what their evidence supports.

## Dedup probe

Searched open backlog items and completed plans for false-positive or false-negative handling, indeterminate outcomes, and agent escalation from script results. Existing work adds local fail-loud checks and remedies for named conditions, but no open item defines a shared outcome contract and caller obligation across decision scripts.

## Why not fixed now

The change crosses many scripts and callers with different result formats and risk levels. A scoped inventory and staged migration are needed to avoid changing expected behavior, overlooking a consumer that still interprets uncertainty as pass/fail, or introducing an unreviewable rewrite of every helper at once.
