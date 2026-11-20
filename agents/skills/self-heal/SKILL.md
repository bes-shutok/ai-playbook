---
name: self-heal
description: >
  Recover useful progress when a workflow is about to stop on a blocker, repeated review cycles,
  a failed tool, or another obstacle that may have a remedy. Diagnose first, find the smallest
  safe workaround, and carry it out within the caller's authority and existing gates. Use before
  judging the stop unrecoverable, pausing, or asking the user for direction; it cannot replace a
  required user decision or authorization.
---

# Self-heal

Before ending a workflow on a blocker or routine failure, determine whether the obstacle can be resolved from repository evidence, available tools, or an already-authorized alternative. Prefer a bounded recovery over a premature stop. Preserve the caller's scope, permissions, hard gates, worker-liveness rules, retry budget, and completion boundary.

## Recovery

1. State the concrete blocker, its evidence, and the exact next action it prevents. Read the relevant workflow instructions and inspect the source of the refusal; do not infer that it is unavoidable from the refusal message alone. Review findings themselves use the Repeated review cycles path; do not backlog an in-scope blocking finding merely because it blocks review exit.
2. If no existing backlog item or prompt-log entry covers it, create one durable backlog item recording the observed refusal, why the workflow stopped before checking for a workaround, the evidence-backed cause, and the smallest proposed correction. Invoke `investigate` on an open item when no investigation entry or covering plan exists, including an item that predates this run, when the caller's remaining investigation allowance permits it; read its evidence and alternative dispositions before choosing a workaround. If the caller's allowance is spent, leave the item open for the next eligible invocation and continue only with recovery supported by available evidence and existing authority.
3. Search the current repository, documented recovery paths, and available tool capabilities for a workaround. Classify the refusal first: a refused method is evidence about that operation, so re-derive the caller's target and authorization from the task's own direction and distinguish a method-level refusal from missing authority or an unsafe target. Prefer the smallest change at the owning layer, with the fewest new steps and least chance of blocking other workflows. Do not edit or bypass a gate or validator to make it pass.
4. When an authorized workaround exists, apply it, run the refused gate again, and continue from durable state under the caller's retry and landing rules. Use another supported, narrower method only when it remains permitted under that authorization, and after it succeeds re-run the original gate and verify the caller's complete terminal conditions before continuing dependent work. Do not repeat an exhausted retry or self-heal allowance; one recorded recovery disposition ends the handoff for that stop, and the calling workflow makes no second self-heal call for it. Record the recovery result; keep the origin and investigation prompt open while the root cause remains unresolved or lacks the completion witness required by its owning workflow. Close the origin only when that existing witness is present, and let maintenance apply its prompt-log freeze and prune procedure when its conditions are met. Do not invent a witness, edit the log outside its owner procedure, or leave ready work for a completed origin.
5. If no safe action is possible without user input, external-owner action, or new authorization, report the specific decision or evidence needed and preserve the run for resumption; ask only when the refusal exposes missing authority, ambiguous ownership, or an unsafe target. Do not treat elapsed time or the user's silence as authorization. An authoring-run continuation is ambiguous ownership when the plans skill's Phase 0 authoring-run continuation ownership rule finds no pass condition: verify that rule before any step 3-4 workaround, and preserve the run's work while the owner-recognized transfer or operator decision is pending.

After `investigate` commits its log entry, mutate the prompt's origin only under the caller's existing owner-recognized freeze or live claim. Do not create machinery merely to avoid a stop: any proposed gate, validator, lock, ledger, or required ceremony must follow the repository's Machinery admission protocol.

## Resource cleanup disposition

A request to clean up agent-created resources ends with one disposition per in-scope resource (every worktree registration or local branch ref the request names or plausibly owns) before any completion claim. The inventory is read only from the runtime-neutral sources already on disk: the worktree list, branch ancestry, and the run and claim records that own the resources. Build no new inventory surface beside those sources. The disposition vocabulary:

- **Verified removal**: the resource is gone, confirmed from the inventory sources.
- **Named retention**: the resource stays; the response names its owner (the run or claim record bound to it) and the exact unmerged work it holds.
- **Continuation through the owning authorized closeout**: the resource's disposition belongs to its owning run's authorized closeout; route it there instead of disposing of it in this cleanup.

A completion claim is valid only when it matches the full inventory: it enumerates every in-scope resource with its disposition, and a partial result never reads as complete. A resource that cannot be dispositioned ends the request under Recovery's existing terminal condition (step 5); this section adds no second stop rule.

## Repeated review cycles

When a plans, execute-plan, or other review loop has gone through repeated correction rounds, inspect the chronological review artifacts, sidecars, fix history, and current digest. Use `review-reconciliation` when its recurrence, contradiction, or churn trigger applies. Decide from the evidence whether findings are converging, fixes are producing new defects, the witness is inadequate, or the review surface is misdesigned.

Recommend and carry out the smallest coherent correction that the active workflow already authorizes. If results are converging, continue under that workflow's review budget and exit criteria. If fixes regenerate findings or blocker counts stop improving, simplify or refactor the responsible mechanism before another review when the caller's run-wide attempt state is unused and its bounded allowance permits it; a consumed or unknown state reuses its recorded evidence and pauses without another assessment. Do not reset its allowance or relax its review gate. When reporting to the operator, preserve the evidence and ask only the specific question the stop turns on.

## Integration Points

- `using-skills` routes any skill-workflow stop here for the before-judgment recovery check; user-only decisions stay with the user.
- `plans` calls this skill once before judging a non-converging plan-review loop or an authoring stop unrecoverable; its review budgets and cap-closure rules remain authoritative.
- `done` invokes this handoff once before judging a closeout failure unrecoverable; its fail-closed runner refusals, staging decisions, and user-only stops stay authoritative.
- `done`'s Operator branch closeout report answers a multi-resource cleanup request under `## Resource cleanup disposition`; its sanctioned branch-closeout sequence stays authoritative for each removal.
- `execute-plan`'s ad-hoc-worktree closeout reports its run's resource dispositions under `## Resource cleanup disposition` when the closeout answers a multi-resource cleanup request; its removal gates and Terminal closeout ownership stay authoritative.
- `plans`' landing handoff reports the authoring worktree's and branch's dispositions under `## Resource cleanup disposition` when the handoff answers a multi-resource cleanup request; its landing order stays authoritative and its claim policy stays procedure-owned.
- `plans`' Phase 0 Authoring-run continuation ownership entry boundary owns the ambiguity verdict for authoring-run continuations; Recovery step 5 verifies that rule and preserves the run pending the owner-recognized transfer or operator decision (this skill never restates the pass conditions).
- `execute-plan` calls this skill before a Phase 3 review stop for recurring or regenerated findings, escalation, or re-entry limits; its review-reconciliation and fix-risk gates remain authoritative.
- `review-plan` calls this skill at its active churn or recurrence trigger, before any pause; its one-attempt self-heal state and authorization contract remain authoritative.
- `review-loop` reaches this skill only through `review-plan`'s churn sequence, never a direct call before its standalone fix-risk stop; its review-round, escalation, budget, and authorization limits remain authoritative.
- `maintenance` invokes this skill once per non-user-only blocker before a stop or ask, per `maintenance/decisions.md`; maintenance retains its lane and authorization rules, and owns prompt-log retirement when its existing completion witness is present.
- `investigate` supplies backlog archaeology and alternatives for an unresolved blocker. After its log-entry commit, self-heal continues origin work under an existing owner claim; otherwise it leaves the ready prompt for maintenance and continues only independent recovery. It consumes investigation evidence and never dispatches the prompt.
