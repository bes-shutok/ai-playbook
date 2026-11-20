# Plan: Self-Heal Acts Before Scheduled Continuation

Backlog origins (scope of record):
- `docs/history/backlog/2026-11-20-self-heal-explicit-recovery-direction-recurrence.md`
- `docs/history/backlog/2026-11-20-self-heal-scheduled-continuation-as-stop.md`

Driving force: efficiency
Plan review record: the staging series `.ai-playbook/reviews/YYYY-MM-DD-plan-review-self-heal-recovery-direction-continuation-r*.md` (highest round for this source plan is authoritative)
Execution budget: 0.5h total, largest task 0.5h
Executed: no
Authoring claim: 2026-11-20-self-heal-explicit-recovery-direction-recurrence (session 01a1f45a-3820-70b3-8c2c-91b7b6b3d313)

## Terms

- **Scheduled continuation:** A future maintenance or recovery run already arranged to resume work.
- **Current action:** Work that can proceed in this session after checking its actual prerequisites and owner-defined gates.

## Why

The reported interaction deferred requested recovery to a scheduled continuation without a preserved explanation of which current prerequisite prevented action. The current self-heal instructions already require immediate continuation of authorized work and explicit workaround carry-through, so the likely gap is applying those rules to a future scheduled time, not missing recovery machinery.

## Gist & Examples

TLDR: Clarify immediate action in self-heal, because efficiency improves when available work does not wait on a future run.

Today, a future continuation is discussed without answering whether the next requested action is available now. After this change, a future scheduled time alone does not stop current authorized work; an actual unmet prerequisite still does.

## Outcome

Self-heal clearly directs the agent to assess and perform available authorized work before relying on a future continuation.

- A scheduled continuation no longer substitutes for checking the current next action.
- A live owner, safety condition, or closeout gate still prevents any action that depends on it.
- The skill remains concise and adds no machinery.

Gate delta: no refusal classes, hard gates, fences, protocol layers, schema fields, or paused dispatch conditions are added or removed; no blocking review duty is added; the wording adds no new check and replaces existing text without net growth.

## Assumptions

- The first-pass runtime trace is unavailable; basis: no original probe or decision log is present in the session artifacts.
- Naming scheduled continuation time as non-blocking by itself can help apply the existing next-action rule; basis: the reported explanation named a future fire time and current skill text does not mention scheduled continuations.
- The scheduled time does not prove current ownership or cleanup prerequisites; basis: the existing self-heal and closeout contracts require those checks independently.
Decision points requiring a grill: none remain.

## Standing constraints

- Preserve the user's requested scope, authority, ownership checks, safety conditions, retry limits, resource-retention rules, and owner-specific closeout gates.
- Do not claim that any particular earlier gate passed or failed without the missing runtime evidence.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the wording distinguishes a future fire time from actual prerequisites for current work and preserves all existing stop conditions.
- Maintainability: the change is one replacement of the existing opening recovery paragraph with no net byte growth; no incident narrative or new machinery enters operative text.
- Documentation integrity: both backlog origins follow the existing authoring and execution lifecycle.

**Done when:**
- The skill directly states that a scheduled continuation alone does not prevent current authorized action.
- A realistic self-heal walkthrough continues when its next action is available and stops with a named prerequisite when a real closeout gate blocks it.
- Plan readiness, public hygiene, and the skill text byte-budget check pass.

**Ship when:** No external deployment or human-owned condition.

## Documentation Impact Assessment

`agents/skills/self-heal/SKILL.md` is the owning workflow document and the only operative document needing a change. The incident and uncertainty are already captured in the two backlog origins and investigation log; no README or other reference update is needed.

## Review Scope

**Explicit must-fix:**

**Production code:** none.

**Tests:** none; validate the instruction behavior with the realistic scenarios listed in Task 1.

**Documentation:**
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Plan-related extension:** Review may include related wording in the same recovery procedure when needed to keep the instruction clear and consistent.

**Out of scope; reject unless plan-related:**
- Scheduler and maintenance machinery; no runtime evidence shows those need changes.
- Cleanup ownership, branch accounting, or closeout gates; those remain governed by their owning workflows.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-20-self-heal-recovery-direction-continuation.md --pre-round
python3 scripts/skill_text_budget.py --check
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Clarify action before a future continuation

Context surface: Terms, this task, and Standing constraints.

Files:
- `agents/skills/self-heal/SKILL.md`

Primary class anchors:
- `Recovery opening rule` in `agents/skills/self-heal/SKILL.md`

- [ ] Recovery opening rule clarifies future continuation timing: given an explicit recovery request and a scheduled future run but no unmet prerequisite for the next action, expects the authorized next action to proceed in the current session. [class: IMPLEMENTATION_REQUIRED]
- [ ] Existing stop condition remains binding: given a verified live owner or owner-defined closeout prerequisite blocks the requested action, expects self-heal to name that prerequisite and preserve the protected resource. [class: IMPLEMENTATION_REQUIRED]
- [ ] Replace the existing opening paragraph with concise wording that states: continue authorized work when its next action is available; a scheduled continuation alone is no blocker; invoke self-heal when an evidenced obstacle stops work; preserve the caller's scope, permissions, hard gates, worker-liveness rules, retry budget, and completion boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run self-heal against the two scenarios above and confirm the instructions lead to the expected outcomes without weakening any existing gate. [class: REPOSITORY_TEST]
- [ ] Run the listed validation commands and record their results. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: clarify self-heal continuation timing` [class: IMPLEMENTATION_REQUIRED]
