# Backlog: strengthen the intermediate-task-reviews plan's validation-gate pins

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; gate strength (gates auditing gates). Revive on a witnessed deletion or paraphrase passing the block, or a project-priority-profile change.)
Workflow: backlog
Source: code review round r1 of docs/plans/2026-09-20-execute-plan-intermediate-task-reviews.md (staging doc docs/reviews/2026-09-20-execute-plan-intermediate-task-reviews-code-review-r1.md, finding G1, testing lens F1-F5; triaged valid and deferred to backlog). Tree content is correct today; these are durable gate-strength gaps in the certified plan's `## Validation Commands`.
Severity: Medium (bundle of five Low-to-Medium gate-strength gaps)
Exact location: `## Validation Commands` in docs/plans/2026-09-20-execute-plan-intermediate-task-reviews.md, gates V1, V2, V4, V7, and V8, over the pinned fragments in agents/skills/review-agents/review-panel-selection.md, agents/skills/receiving-review/SKILL.md, agents/skills/execute-plan/subagent-prompts.md, agents/skills/execute-plan/agent-logs.md, and agents/skills/execute-plan/SKILL.md.
Why not fixed now: the plan was certified against a passing V-block and this review round captured the residuals instead of editing certified validation commands; widening the gates is its own change set and needs a fresh review round after the digest moves (decision: r1 triage, 2026-09-20).
Driving force: testability

## Problem

The plan's validation gates pin less than the behavior they claim to protect, so a regression that deletes, abridges, or paraphrases protected content can still pass the full block:

1. **V1 pins tier labels, not row content.** The gates grep `Tier L`, `Tier M`, `Tier H` as bare fragments; a tier row whose trigger or worker-set cells are edited or emptied still matches, so the tier table's operative content is unprotected.
2. **V2 lacks integration-point and amendment-suffix pins.** The taxonomy region pins each force line, but nothing pins the plans-taxonomy mapping sentence's gated wording or the amendment rule's rename-or-removal suffix, so those clauses can drift silently.
3. **V4 leaves the worker template's operative fragments unpinned.** The template heading and two done-template clauses are pinned, but the changed-context diff command, the verdict enum, and the backlog-candidate return fields are not, so the operative parts of the Step 1.2b template can change without any gate failing.
4. **V7 covers only execute-plan verbatim duplication.** The negative gate fires on `| Tier | Trigger |` in execute-plan/SKILL.md only; the same table duplicated into subagent-prompts.md or agent-logs.md, and any paraphrased restatement of the tier policy anywhere, both pass.
5. **Residual prefix-only pins.** The Gate 25 pin, the `inter_review` field list, and the V8 precedence pin match lead-in prefixes only; their operative clauses (the positive launch condition, the recorded field set, the precedence wording) are unprotected.

## Suggested fix

In a follow-up plan (any edit to the certified Validation Commands moves the plan digest and requires a fresh review round), extend each gate to pin one operative fragment per protected clause: V1 pins one trigger fragment and one worker-set fragment per tier row; V2 pins the gated plans-taxonomy mapping sentence and the amendment rule's rename-or-removal suffix; V4 pins the diff command, the verdict enum, and the return fields; V7 extends the negative scan to subagent-prompts.md and agent-logs.md and adds a paraphrase probe over the tier-policy vocabulary; the Gate 25, `inter_review`, and V8 pins gain their clause-level continuations. Derive every new fragment byte-exact from the then-current tree, and keep the block exit 0 on the unchanged tree first so the strengthened gates are proven not to over-pin.
