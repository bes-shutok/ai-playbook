# Backlog: document how a successor session adopts a fresh stack-run claim

- **Filed:** 2026-11-05, witnessed while resuming a stacked execution from an operator handoff
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Company projects that hand a half-finished stack run from one agent session or runtime to another need a sanctioned way to continue it; without one the successor improvises with the claim gateway.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** reliability + clarity
- **Skill/step:** `agents/skills/execute-plan-stack/SKILL.md` Workflow step 2 (adopt the established claim); `agents/skills/execute-plan/SKILL.md` execution claim registration; `agents/skills/maintenance/template-execution.md` recovery procedure; `scripts/execution_claim.sh` take, claim and refresh modes
- **Catch frequency:** witnessed once.
- **False-positive cost:** loosening the claim fence could let two live sessions both believe they own a run; any fix must keep the foreign-live-claim refusal.
- **Review date:** 2026-12-05
- **Dedup probe:** searched open backlog names and bodies for the session status provider key, claim adoption, handoff and cross-runtime wording. The nearest items concern dead-run conversion coverage and handoff reconciliation internals; none covers the stack skill's "adopt the existing claim" step when the continuing session has a different session id and runtime than the claim holder.

## Problem

`execute-plan-stack` step 2 says to adopt the established run, worktree and claim and not create a competing claim. The claim gateway offers no matching mode for a different session id:

- `take` refuses while the foreign claim is fresher than two hours.
- The dead-run conversion arm needs a configured session status provider, which a typical company repository does not configure, so conversion refuses.
- `refresh` refuses a claim naming a foreign session.

The only workable route found was to call `refresh` with the claim's original run session id (the stable origin identity) and without a runtime flag so the recorded runtime was preserved. That works, but it is undocumented: the successor is acting under the previous session's identity, a different runtime than the claim records, and nothing says whether that is sanctioned, nor how to leave an audit trail beyond a manual manifest line.

## Observed versus expected

Observed: a successor session in a different runtime had to infer the adoption route by reading the gateway source and the recovery text. Expected: the stack skill (or the shared recovery procedure) names the sanctioned adoption route for a handoff, states which identity the successor uses for claim calls, how the recorded runtime is treated, and what record the successor writes.

## Suggested fix

Add a short adoption arm to the recovery procedure for "operator-directed handoff of a stack run": the successor may use the stable origin run session id for claim refresh, must write a manifest adoption row, and the runtime line stays that of the origin unless the gateway grows an explicit rebind. Alternatively add a gateway mode that rebinds a claim to a new session after verifying the manifest names the same run and the operator handoff record exists.

## Evidence

Environment: shared skills at the repository copy, 2026-11-05, successor session on a different agent runtime than the claim's recorded runtime. A refresh under the origin run session id succeeded and preserved the recorded runtime; no other route was available without waiting out the freshness window.
