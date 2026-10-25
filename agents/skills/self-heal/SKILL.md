---
name: self-heal
description: >
  Recover useful progress when a workflow is about to stop on a blocker, repeated review cycles,
  a failed tool, or another recoverable obstacle. Diagnose first, find the smallest safe workaround,
  and carry it out within the caller's authority and existing gates. Use before pausing or asking
  the user for direction; it cannot replace a required user decision or authorization.
---

# Self-heal

Before ending a workflow on a blocker or routine failure, determine whether the obstacle can be resolved from repository evidence, available tools, or an already-authorized alternative. Prefer a bounded recovery over a premature stop. Preserve the caller's scope, permissions, hard gates, worker-liveness rules, retry budget, and completion boundary.

## Recovery

1. State the concrete blocker, its evidence, and the exact next action it prevents. Read the relevant workflow instructions and inspect the source of the refusal; do not infer that it is unavoidable from the refusal message alone. Review findings themselves use the Repeated review cycles path; do not backlog an in-scope blocking finding merely because it blocks review exit.
2. If no existing backlog item or prompt-log entry covers it, create one durable backlog item recording the observed refusal, why the workflow stopped before checking for a workaround, the evidence-backed cause, and the smallest proposed correction. Invoke `investigate` on an open item when no investigation entry or covering plan exists, including an item that predates this run, when the caller's remaining investigation allowance permits it; read its evidence and alternative dispositions before choosing a workaround. If the caller's allowance is spent, leave the item open for the next eligible invocation and continue only with recovery supported by available evidence and existing authority. Reuse an existing investigation or plan instead of repeating it.
3. Search the current repository, documented recovery paths, and available tool capabilities for a workaround. Prefer the smallest change at the owning layer, with the fewest new steps and least chance of blocking other workflows. Do not edit or bypass a gate or validator to make it pass.
4. When an authorized workaround exists, apply it, run the refused gate again, and continue from durable state under the caller's retry and landing rules. Do not repeat an exhausted retry or self-heal allowance. A passing gate proves the immediate block is cleared, not that the backlog origin is complete. Record the recovery result; keep the origin and investigation prompt open while the root cause remains unresolved or lacks the completion witness required by its owning workflow. Close the origin only when that existing witness is present, and let maintenance apply its prompt-log freeze and prune procedure when its conditions are met. Do not invent a witness, edit the log outside its owner procedure, or leave ready work for a completed origin.
5. If no safe action is possible without user input, external-owner action, or new authorization, report the specific decision or evidence needed and preserve the run for resumption. Do not treat elapsed time or the user's silence as authorization.

After `investigate` commits its log entry, mutate the prompt's origin only under the caller's existing owner-recognized freeze or live claim. If none is active, leave the ready prompt untouched for maintenance to own and defer origin changes; continue only independent recovery within the caller's authority. Use the investigation evidence; do not dispatch its emitted prompt. Do not create duplicate backlog items or repeat an investigation already represented by a prompt-log entry or covering plan. Do not create machinery merely to avoid a stop: any proposed gate, validator, lock, ledger, or required ceremony must follow the repository's Machinery admission protocol.

## Repeated review cycles

When a plans, execute-plan, or other review loop has gone through repeated correction rounds, inspect the chronological review artifacts, sidecars, fix history, and current digest. Use `review-reconciliation` when its recurrence, contradiction, or churn trigger applies. Decide from the evidence whether findings are converging, fixes are producing new defects, the witness is inadequate, or the review surface is misdesigned.

Recommend and carry out the smallest coherent correction that the active workflow already authorizes. If results are converging, continue under that workflow's review budget and exit criteria. If fixes regenerate findings or blocker counts stop improving, simplify or refactor the responsible mechanism before another review when the workflow's bounded self-heal allowance permits it. Do not reset its allowance, relax its review gate, or keep making micro-fixes after the allowance is spent. If safe resolution requires a material user decision or the existing policy requires operator direction, preserve the evidence and ask only that specific question.

## Integration Points

- `using-skills` routes any recoverable skill-workflow stop here before asking the user or ending work.
- `plans` calls this skill before pausing a non-converging plan-review loop; its configured review budgets and cap-closure rules remain authoritative.
- `execute-plan` calls this skill before a Phase 3 review stop for recurring findings, regenerated findings, escalation limits, or re-entry limits; its review-reconciliation and fix-risk gates remain authoritative.
- `review-plan` calls this skill at its active churn or recurrence trigger. The existing one-attempt self-heal state and authorization contract remain authoritative.
- `review-loop` calls this skill before a standalone fix-risk stop for operator direction; its review-round, escalation, budget, and authorization limits remain authoritative.
- `maintenance` invokes this skill for unexpected issues with safe workarounds, as stated in `maintenance/decisions.md`; maintenance retains its lane and authorization rules, and owns prompt-log retirement when its existing completion witness is present.
- `investigate` supplies backlog archaeology and alternatives for an unresolved blocker. After its log-entry commit, self-heal continues origin work under an existing owner claim; otherwise it leaves the ready prompt for maintenance and continues only independent recovery. It consumes investigation evidence and never dispatches the prompt.
