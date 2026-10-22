# Plan: Restore ownership for the maintenance loop carrier

Backlog origin: docs/history/backlog/2026-10-23-pending-rearm-undischargeable-across-automation-born-carriers.md
Driving force: automation
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-loop-carrier-restore-surface-for-reduced-toolset-carriers-r*.md
Execution budget: 1.5h total, largest task 0.5h

## Terms

- **D-3 carrier:** the recurring maintenance scheduler automation, named `Maintenance scheduler turn` and scheduled at `0 11 * * *`.
- **Automation-born session:** a session started by a scheduled carrier and limited to the primitives granted to that carrier.
- **Reduced-toolset session:** a carrier session that can inspect automations but cannot create one.
- **Pending re-arm:** the state record and payload copy that preserve the work needed to recreate the D-3 carrier.
- **Interactive session:** a user-started session with the automation creation primitive.

## Why

Four overnight carrier sessions could not restore the D-3 carrier because their reduced toolset did not include automation creation. The parked recovery record remained, but the instructions did not assign a capable session to consume it or settle its competition with a one-shot scheduling ask.

## Gist & Examples

TLDR: assign carrier restoration by session type and make re-arm take the available creation, improving automation recovery.

When a user-started session receives both a standing pending re-arm and a new request to schedule an execution, it restores the recurring carrier first and reports the execution request as unscheduled. When an automation-born session lacks creation capability, it keeps the pending record and payload for the next capable session. The recurring carrier remains the restore target; the launchd route stays waiting while its headless provider configuration failure remains undiagnosed.

## Outcome

The repository's scheduling and re-arm instructions assign one capable owner for restoring the recurring maintenance carrier and state what happens when that work competes with a new scheduling ask.

- A user-started session with creation capability restores the pending carrier before creating a one-shot execution, and reports that execution ask as unscheduled.
- A reduced-toolset automation-born session preserves the pending re-arm record and payload so the next capable session can restore the carrier.
- The existing recurring form remains the target, while launchd promotion stays behind its recorded diagnosis condition.

Gate delta: one new normative precedence in the existing scheduling contract: when a pending re-arm and a one-shot ask compete for a session's sole automation creation, the re-arm consumes it and the ask is reported unscheduled; this adds no gate, refusal class, fence, protocol layer, schema field, blocking review duty, or new machinery.

## Assumptions

- A user-started session that has the creation primitive can discharge a standing pending re-arm; basis: the origin's recorded idle period and the 2026-10-23 11:40 state note showing a capable interactive session discharged it.
- A simultaneous operator scheduling ask remains unscheduled when the one available creation is used to restore the carrier; basis: the scheduling contract requires session-owned satisfaction and forbids silent defer.
- Automation-born reduced-toolset sessions retain the pending record and payload; basis: the four carrier witnesses and the origin's rejected alternative.

Decision points requiring a grill: carrier re-arm precedes a simultaneous one-shot scheduling ask because a single creation cannot serve both and deterministic restoration resumes the dark loop while explicitly reporting the unscheduled ask; source: PLAN-PROMPTS entry and root scheduling-asks contract; standing maintenance authorization, 2026-10-23; Tasks 1-3; keep launchd promotion closed until the recorded headless provider-configuration failure is diagnosed because two fire-time failures are recorded; the existing interactive restore is demonstrated and does not add an unverified path; source: PLAN-PROMPTS entry and scheduler-state notes dated 2026-10-13 and 2026-10-16; standing maintenance authorization, 2026-10-23; Task 3 and Ship when.

## Standing constraints

- Keep the existing D-3 recurring carrier form and the paired pending record and payload recovery input.
- Do not add a gate or machinery, widen host-granted tools, or promote launchd before its recorded blocker is diagnosed.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each of the three doctrine surfaces assigns the same restore owner and scheduling-ask outcome for the relevant session class.
- Maintainability: the wording reuses the existing recurring recipe, park path, and scheduling contract without creating another mechanism.

**Done when:**
- The three doctrine surfaces agree on owner, precedence, unscheduled reporting, and the preserved recurring form.
- The plan's scoped docs checks and repository pin checks pass.

**Ship when:** none; this repository-local doctrine change has no deployment or external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:** none.

**Tests:** none.

**Documentation:**
- `AGENTS.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/duties-core.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract this plan changes. If the link is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md`; its scheduler selection and lane guards are unchanged.
- `docs/maintenance/operator-directives.md`; the D-3 form of record is unchanged.
- `scripts/` and scheduler state; this plan changes doctrine text only.

## Validation Commands

```bash
git diff --check
bash scripts/check_maintenance_pins.sh
```

### Task 1: Set precedence in the scheduling-asks contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `AGENTS.md`

- [x] Given a user-started session with a pending re-arm and one creation available, expects the contract to assign carrier restoration first and the competing execution ask an unscheduled report. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an automation-born reduced-toolset session, expects the contract to preserve session-owned satisfaction and forbid treating another carrier as satisfaction. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: prioritize maintenance carrier restoration` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Align the interactive dispatch and restore guidance

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Given an interactive payload with both pending re-arm and an execution schedule ask, expects re-arm to consume the available creation and the ask to be reported unscheduled. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an automation-born session without creation capability, expects the existing park and payload path to remain the handoff to a capable session. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: assign interactive carrier restore owner` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Align the shared FIRST ACTION duty

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/duties-core.md`

- [x] Given a reduced-toolset FIRST ACTION duty, expects it to keep the pending record and paired payload when it cannot create the recurring carrier. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a later capable interactive session reading that pending recovery input, expects it to restore the D-3 recurring carrier before a competing one-shot ask. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: define shared re-arm escalation owner` [class: IMPLEMENTATION_REQUIRED]
