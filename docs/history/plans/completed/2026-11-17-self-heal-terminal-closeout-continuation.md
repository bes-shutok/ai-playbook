# Plan: terminal closeout continuation and self-heal trigger

Backlog origins (scope of record):
- docs/history/backlog/2026-11-17-execute-plan-incomplete-closeout-terminal.md
- docs/history/backlog/2026-11-17-self-heal-trigger-misses-known-incomplete-workflow.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-17-plan-review-self-heal-terminal-closeout-continuation[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.0h total, largest task 0.5h
Executed: yes (6d114fef59ab13373c7a2bc4e717497dea7391ac)
Authoring claim: 2026-11-17-execute-plan-incomplete-closeout-terminal.md (session 01a1e73d-0784-7661-a2e2-91cd3296cc00)

## Terms

- **Required closeout work:** a remaining step or verification the active workflow requires before it may report terminal completion.
- **Normal authorized continuation:** required work whose next action is already within the caller's scope and authority and is not prevented by a current gate.
- **Recoverable obstacle:** an evidenced condition that prevents the next authorized step and may have a safe remedy within existing authority and limits.

## Why

The prior execution ended with required session closeout incomplete. The follow-up only invoked self-heal after the user explicitly asked for a workaround, leaving the workflow's own continuation obligation implicit at both the closeout and recovery boundaries.

## Gist & Examples

TLDR: make pending closeout continuation explicit and clarify self-heal's obstacle trigger, improving code quality by preventing premature terminal responses and missed recovery opportunities.

Before: required closeout work remained, but the response reported the run as incomplete and ended; self-heal was considered only after the user named the workaround search.

After: the executor continues authorized closeout work directly; if a concrete obstacle prevents the next required step, it invokes self-heal before ending, even if the tool did not explicitly refuse.

Edge cases: user-only decisions, missing authority, external-owner actions, retry exhaustion, worker-liveness rules, and failed integrity gates retain their existing stops and remedies. Pending work alone does not trigger self-heal.

## Outcome

A plan run continues its authorized closeout through every required gate and uses self-heal when an obstacle prevents that continuation.

- The closeout has an explicit final-response boundary tied to its existing success checklist.
- Self-heal distinguishes ordinary pending work from an obstacle that merits recovery.
- Existing authority, completion, and refusal semantics remain intact.

Gate delta: no new gate, validator, lock, ledger, fence, schema field, refusal class, or dispatch-pausing condition is added or removed; this plan clarifies the existing terminal boundary and self-heal trigger in their current owner skills, and preserves every present closeout and recovery gate.

## Assumptions

- assume both origins remain in scope because they describe the same premature-stop incident at the caller and recovery boundaries; basis: the user's explicit confirmation on 2026-11-17 and the grouped investigation entry.
- assume Task 2 may extend `self-heal`'s existing `execute-plan` Integration Points entry through the causal-extension scope in Review Scope; basis: plan-review r7 finding 1 and the repository's bidirectional Integration Points rule.
- assume no repository README update is needed because no skill name, path, or invocation changes; basis: the documentation impact scan.

Decision points requiring a grill: both backlog origins in one plan; explicitly confirmed by the user, 2026-11-17, Scope boundaries; correctness and maintainability checked through readiness and text-policy gates; explicitly confirmed by the user, 2026-11-17, Evaluation Criteria.

## Standing constraints

- Keep existing user authority, user-only decisions, retry budgets, worker-liveness rules, closeout gates, and completion boundary unchanged. Replace or remove operative words in each edited skill to pay for any additions, even when the file remains under its byte cap.
- Keep incident details in the backlog and investigation record; operative skill text cites the incident in at most one concise line.
- Apply the skill text byte-budget gate; if either edited skill grows past its cap, delete equivalent operative bytes from that same file in this change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the skills distinguish authorized pending work, a recovery-worthy obstacle, and a user-only or integrity stop.
- maintainability: the trigger and caller boundary each have one clear home and point to the other skill by name without duplicating its procedure.

**Done when:**
- both skills state the normal-continuation and obstacle-recovery behavior and preserve existing closeout checks.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-17-self-heal-terminal-closeout-continuation.md` and the plan's text-policy checks pass; skill text remains within budget.

**Ship when:**
- nothing external; all work is repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Skill text:**
- `agents/skills/self-heal/SKILL.md` (Task 1)
- `agents/skills/execute-plan/archive-and-cleanup.md` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above when causally required to implement these tasks, fix regressions, or align the changed contracts.

**Out of scope; reject unless plan-related:**
- `agents/skills/done/SKILL.md`; its Workflow continuity and operator-closeout rules remain authoritative and need no change.
- `agents/skills/using-skills/SKILL.md`; its existing routing remains authoritative and needs no change.
- validators, hooks, and tests; no new mechanism is admitted by these origins.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-17-self-heal-terminal-closeout-continuation.md
python3 scripts/plan_readiness.py docs/history/plans/2026-11-17-self-heal-terminal-closeout-continuation.md
python3 scripts/skill_text_budget.py --check
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/scan-public-hygiene.sh
```

### Task 1: make self-heal distinguish pending work from an obstacle

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/self-heal/SKILL.md`

- [x] Given required work remains and its next action is authorized and available, expect the workflow to continue directly without self-heal; given an evidenced obstacle blocks that action, expect self-heal before stopping even without an explicit tool refusal. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the next step requires a user-only decision or an integrity gate fails, expect the existing stop, ask, or report behavior with no self-heal bypass; existing authorization boundaries, retry limits, worker-liveness rules, and integration references remain intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Run self-heal with realistic sample context for (a) authorized pending work, (b) an evidenced obstacle without an explicit tool refusal, and (c) a user-only or integrity stop; confirm direct continuation, recovery before stopping, and preservation of the existing stop respectively. [class: REPOSITORY_TEST]
- [x] The changed skill balances any added operative wording with same-file deletion, then passes the text budget and hygiene gates. [class: REPOSITORY_TEST]
- [x] Commit: `docs: clarify self-heal continuation trigger` [class: IMPLEMENTATION_REQUIRED]

### Task 2: keep execute-plan active until closeout is complete

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/archive-and-cleanup.md`

- [x] Given any item in the existing success checklist or closeout gate remains false, expect the executor not to report completion and to continue the authorized closeout step or recover its obstacle. [class: IMPLEMENTATION_REQUIRED]
- [x] When required closeout work remains and the next step is authorized and available, the orchestrator continues it directly; when an obstacle blocks that step, it invokes self-heal under existing authority before a terminal stop. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a remaining step requires a user-only decision or an integrity gate fails, expect the existing stop, ask, or report disposition and no successful completion claim; given a retained worktree or branch, expect its existing closeout disposition to remain in force. [class: IMPLEMENTATION_REQUIRED]
- [x] Run execute-plan with realistic sample contexts for (a) an authorized, available closeout action, (b) an evidenced obstacle without an explicit tool refusal, and (c) a user-only decision or integrity stop; confirm direct continuation, self-heal before stopping, and preservation of the stop without a completion claim. [class: REPOSITORY_TEST]
- [x] The changed skill balances any added operative wording with same-file deletion, then passes the text budget and hygiene gates. [class: REPOSITORY_TEST]
- [x] Commit: `docs: enforce execute-plan closeout continuation` [class: IMPLEMENTATION_REQUIRED]


## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-17-execute-plan-incomplete-closeout-terminal.md`: implemented by the closeout continuation rule and validated in Phase 3; the origin is deleted in this completion pass.
- `docs/history/backlog/2026-11-17-self-heal-trigger-misses-known-incomplete-workflow.md`: implemented by the self-heal obstacle trigger and validated in Phase 3; the origin is deleted in this completion pass.
