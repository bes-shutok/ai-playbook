# Plan: maintenance autopilot continuation
Backlog origin: none
Driving force: automation
Plan review record: .ai-playbook/reviews/2026-10-31-plan-review-maintenance-autopilot-continuation-r*.md
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: 2026-10-31-maintenance-autopilot-continuation.md (session 01a19171-0584-7930-b1ad-434c88bba61d)

## Terms

- **Autopilot mandate**: the user's direction that maintenance continues without asking the user to manage context.
- **Pick**: one eligible plan or backlog item that a maintenance lane selects for work.
- **Context stop**: a per-pick stop instruction used only to let the user manage context manually; the autopilot mandate supersedes it.
- **Cycle gate**: the existing scheduler-state hold that waits for a user action between work cycles.
- **Per-pick session**: a fresh session for each maintenance pick.
- **Same-session compaction**: continuing in the current Codex session after compacting at a safe boundary.
- **Primary quota pause**: the existing five-hour window pause at its configured thresholds.

## Why

The user previously had to tell maintenance to stop after a pick to manage context manually. That workaround should no longer require an operator turn. Maintenance needs one standing autopilot rule, with runtime-specific continuation work tracked separately.

## Gist & Examples

TLDR: Keep maintenance moving through automation without user turns, so eligible work continues after each pick.

Before: A maintenance run finishes one plan and stops because the user asked it to stop after the current pick to manage context. ZCode cannot compact its current session, while Codex can continue in the same session with compaction.

After this plan: The autopilot mandate supersedes the context stop, and the shared maintenance instructions continue eligible work without asking the user. A future ZCode plan will implement one fresh session per pick; a future Codex plan will implement same-session continuation with periodic compaction. Both runtime follow-ups are recorded as separate backlogs here.

Edge cases: An empty eligible queue still ends the loop. The primary quota pause still records a resume point and stops. A genuinely explicit pause or stop request remains effective. An old context stop must not leave an armed cycle gate that blocks the autopilot mandate.

## Outcome

Maintenance has an explicit unattended continuation policy and separate, runtime-owned implementation work for ZCode and Codex.

- A context-management stop no longer closes an autopilot maintenance loop.
- The existing cycle gate remains for directives that explicitly require user-paced cycles.
- The primary quota pause, empty-queue stop, and current user stop request remain respected.
- Codex and ZCode implementation work has a durable, runtime-affine backlog home.

Gate delta: supersede the in-session-only continuation wording with the autopilot mandate and limit the existing cycle gate to explicit user-paced directives; remove a context-management stop as a maintenance completion condition. The existing maintenance pins and cycle gate stay unchanged; no blocker, refusal class, fence, protocol layer, or scheduler state field is added.

## Assumptions

- assume the autopilot mandate supersedes earlier per-pick stop instructions that were used only for context management; basis: the user's 2026-10-31 clarification.
- assume ZCode should start a fresh session per pick and Codex should continue in-session with periodic compaction; basis: the user's 2026-10-31 runtime-specific direction.
- assume this plan updates shared policy text in the ZCode overlay but defers ZCode per-pick session spawning and Codex same-session compaction; basis: the user asked to leave those runtime mechanisms for later plans.
- assume the observed 2026-10-31 stop is not caused by an armed cycle gate; basis: `.ai-playbook/scheduler-state.json` records the gate as cleared and the live stop instruction as the reason, and the completed 2026-10-27 stop-boundary plan already aligned the child closeouts with D-6.
Decision points requiring a grill: none remain.
Scope extensions (grilled): none proposed.

## Evaluation Criteria

- **Correctness**: given the autopilot mandate, a completed pick, and another eligible target, expects the loop to proceed without a user message under the selected runtime continuation path; given an empty queue or primary quota pause, expects the existing stop and resume behavior.
- **Correctness**: given a stale cycle gate created by a prior context stop and the autopilot mandate, expects the gate to clear with its existing timestamp trace and the loop to continue; given a new explicit user-paced directive, expects the gate to remain effective.
- **Maintainability**: common continuation policy has one home, existing state and guards are reused, and each runtime follow-up declares its required agent type.

**Quality dimensions:**
- Correctness: shared instructions agree on autopilot, cycle-gate, quota, and stop behavior.
- Maintainability: no new state field or blocking check is introduced.

**Done when:** the operator directive and shared maintenance instructions express the autopilot contract, the existing maintenance pin suite passes unchanged as a regression check, and separate Codex and ZCode backlog rows exist with their required agent type.

**Ship when:** None for this shared-policy plan; runtime-specific implementation remains future backlog work and is not a release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none

**Tests and validation:**
- `scripts/check_maintenance_pins.sh` (unchanged regression validation in Task 1)

**Documentation:**
- `agents/skills/maintenance/zcode.md` (Task 1)
- `docs/maintenance/operator-directives.md` (Task 1)
- `agents/skills/maintenance/SKILL.md` (Task 1)
- `agents/skills/maintenance/state-file.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-execution.md` (Task 1)
- `agents/skills/maintenance/template-unblock.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md` (Task 2) *(new)*
- `docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md` (Task 2) *(new)*

**Plan-related extension:** implementation and review may change files not listed above when a finding is causally related to the autopilot contract or its runtime follow-up records. If the connection is weak or speculative, drop it with a one-line reason.

**Out of scope; reject unless plan-related:**
- ZCode per-pick session spawning; the shared policy update to `agents/skills/maintenance/zcode.md` is in scope.
- Changes to `scripts/check_maintenance_pins.sh` or its existing pins; run it as a regression check only.
- Codex runtime configuration or scripts; runtime implementation is deferred to the Codex backlog.
- Quota thresholds, lane guards, session-spawn machinery, and compaction machinery.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
PIN_TMP="$(mktemp -d)" || exit 1
PIN_REGISTER="$PIN_TMP/recorded-reds.json"
printf '%s\n' '{"schema":1,"guards":{"check_maintenance_pins":{"rows":[]}}}' > "$PIN_REGISTER" || exit 1
PIN_OUTPUT="$(env -i PATH="$PATH" HOME="$HOME" TMPDIR="$PIN_TMP" PINS_RECORDED_RED_REGISTER="$PIN_REGISTER" PINS_RECORDED_RED_AS_OF="2026-10-31" bash "$REPO/scripts/check_maintenance_pins.sh")" || exit $?
case "$PIN_OUTPUT" in *"PIN RECORDED REDS SUPPRESSED THIS RUN"*) echo "$PIN_OUTPUT"; exit 1;; esac
( cd "$REPO" && python3 scripts/plan_readiness.py docs/history/plans/2026-10-31-maintenance-autopilot-continuation.md ) || exit $?
( cd "$REPO" && bash scripts/scan-public-hygiene.sh --files docs/maintenance/operator-directives.md agents/skills/maintenance/SKILL.md agents/skills/maintenance/state-file.md agents/skills/maintenance/template-authoring.md agents/skills/maintenance/template-execution.md agents/skills/maintenance/template-unblock.md agents/skills/maintenance/decisions.md scripts/check_maintenance_pins.sh agents/skills/maintenance/zcode.md docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md ) || exit $?
```

### Task 1: Establish unattended continuation as the shared maintenance policy

Files:
- `docs/maintenance/operator-directives.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/template-unblock.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/zcode.md`

- [x] Supersede D-6's in-session-only continuation wording with a new autopilot directive. Allocate its directive identifier from the current directives file at implementation time; name the runtime continuation strategies and require no user prompt. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an autopilot mandate and an armed gate recorded for a context-management stop, expects the existing gate-clear trace and the next eligible pick to proceed without a user turn, including after a ZCode continuation-summary resume; given an explicit user-paced directive, expects the cycle gate to remain effective. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the Cycle gate, its state-field writer, the three child closeout paragraphs, the continue-loop condition in `agents/skills/maintenance/decisions.md`, and the ZCode continuation-summary rule to apply the autopilot directive after normal completion and summary continuation, while retaining the primary quota pause, empty-work stop, and explicit current stop request. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the unchanged maintenance pin suite with an empty recorded-red register, isolated temporary directory, and fixed date `2026-10-31`; require exit 0 and no suppression summary as a regression check, then verify the autopilot and explicit-user-stop scenarios against the revised instructions. [class: REPOSITORY_TEST]
- [x] Commit: `docs: define maintenance autopilot continuation` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Record runtime-specific continuation work for future plans

Files:
- `docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md` *(new)*
- `docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md` *(new)*

- [x] Create an open ZCode backlog item with `Required agent type: zcode`, describing one fresh session per maintenance pick, durable target handoff, parent-loop re-arming, and unattended recovery when a session cannot start; distinguish it from the covered ZCode session-channel derivation item. [class: IMPLEMENTATION_REQUIRED]
- [x] Create an open Codex backlog item with `Required agent type: codex`, describing same-session continuation with periodic compaction at safe boundaries, durable progress, and unattended recovery when compaction is unavailable. [class: IMPLEMENTATION_REQUIRED]
- [x] Ensure both rows use the repository backlog format, cite the autopilot directive as the origin context, name the runtime-specific work deferred from this plan, and pass the public-hygiene scan. [class: REPOSITORY_TEST]
- [x] Commit: `backlog: record runtime-specific maintenance continuation work` [class: IMPLEMENTATION_REQUIRED]
