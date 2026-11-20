# Plan: occupied-lane chaining keeps the loop working until no tasks or the 5h wall

Backlog origin: docs/history/backlog/2026-11-08-maintenance-capacity-aware-chaining.md
Driving force: efficiency
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-11-08-maintenance-capacity-aware-chaining.md (session sess_8ed699c9-426d-4cb9-8866-f4205be94098)
Executed: yes (9f86504f8cbe3f9a3b0b534c3e226d7bfc2db68f)

## Terms

- Occupied-lane chaining: the new turn-level duty (this plan's single addition) that arms a near-future retry one-shot for a lane whose deferral reason is occupancy- or lock-shaped, instead of letting the turn end dark until the recurring parent's next slot.
- Occupancy- or lock-shaped deferral: a lane deferral whose recorded reason is descriptive (no token vocabulary exists; the duty keys on predicates, never on literals): the `G1e`/`G1a` discovery arm held the lane on a fresh foreign claim or live peer entry; a merge or done lock observable reads held (`G3`/`G3b`); or the reason names `pending-landing (primary occupied by peer session)`.
- Near-future retry one-shot: a one-shot automation carrying the lane's dispatch-slice payload, armed at or after the freshest blocking claim's likely completion, default +45 minutes from the decision; one retry slot per lane per turn; recorded as a `children[]` entry with the automation id.
- Reset-anchored successor: the 5h-wall arm - when the stop's quota leg records the window as unfit for another run (the Quota-aware lane decisions' defer/near-reset outcomes), the turn arms the chain one-shot at the probe's `reset_at_epoch` + the standing 10-minute arming margin, reusing the quota-aligned cadence rule's arming shape (the recipe's own rule extended to lane-deferral and quota stops).
- Arming route: the retry one-shot uses the overlay's existing clocked-child shape; when the create is cap-refused in an automation-born session, the overlay's existing delete-own-spawner lifting discipline and the pending_rearm park path apply unchanged (this duty invents no new primitive).
- Typical run fit: the Quota-aware lane decisions' near-reset branch evidence standard (a window fits when a typical single-plan run completes inside the remaining minutes by that branch's evidence standard).
- Dark window: a stretch with no armed carrier and no live child where dispatchable work exists.

## Why

Witnessed 2026-11-08 12:24Z (sess_8ed699c9): both lanes held by fresh peer claims and a held done lock, so the turn recorded two D3 deferrals and went dark for ~22 hours (the recurring parent's next slot was the following day 11:00 UTC) while the 5h allowance had abundant room and every peer hold was minutes-to-completion work. The quota leg was recorded `unknown/fail-open` without running the probe, so no capacity reasoning happened at all. Occupancy is a timing input, not a terminal state; the loop's own quota-aligned cadence rule already proves the arming shape ("no arming path may end with the loop dark") - the lane-deferral and quota-wall stops simply never inherited it.

## Gist & Examples

TLDR: when a scheduler turn's lanes are held by peer occupancy or locks, it runs the quota probe and arms one near-future retry one-shot per held lane; when the stop is the 5h wall, it arms the successor right after the window reset; recorded in the state file so the next turn reads them state-first.

Before: lanes busy at 12:24Z, turn defers, loop dark until next day 11:00, hours of 5h capacity unused while peers land within minutes.

After: same 12:24Z turn runs the probe (abundant room), arms one exec retry one-shot at ~13:10Z and, had the authoring hold been its only hold, one authoring retry the same way; the peer lands at 12:40Z; the 13:10Z child picks the next open plan immediately.

Edge cases: the create primitive is unavailable (reduced toolset) - the duty parks `pending_rearm` with the assembled payload copy per the existing park path and the next capable turn discharges it; a duplicate-carrier refusal - treat an existing ENABLED recognition match as success per the recipe's verification arm; quota probe unusable - the duty records `quota-probe-unusable` and arms the retry at the default slot only when the last known probe is fresh enough to clear the fit test, otherwise parks; every armed retry lands before the turn's own 5h wall because the duty checks the fit test before arming; the recurring parent stays the recognition-match carrier - a retry one-shot never becomes a second parent (the recipe's one-carrier rule and the duplicate-parent tripwire are unchanged).

## Outcome

- Gate delta: none - no gate, refusal, or checked surface is added or changed; the duty is an arming path recorded through existing writer classes (message-only prose doctrine; the failure it prevents is the dark window, and no existing gate is demoted or removed because none polices this shape today).

The loop keeps working whenever capacity and dispatchable work exist: occupied-lane holds produce a bounded near-future retry instead of a dark window, and 5h-wall stops produce a reset-anchored successor. No gate changes, no new script, no state-schema change.

## Assumptions

- assume skill-text-only change, no script and no machinery registry row: the duty arms existing automation primitives and records through existing writer classes (children[] entries, pending_rearm park); no new checked surface is created (the machinery admission protocol's no-incident-no-gate rule prices this as non-blocking prose doctrine, and the incident it prevents - the 22-hour dark window - is the origin row, linked in the registry sense only through the backlog row).
- assume the duty lives in `decisions.md` (Step 3 owns lane decisions and their deferral reasons; this duty refines the existing D3 deferral shape) with the runtime primitives (delayMinutes one-shot shape, reset_at_epoch margin) referenced by name from the zcode overlay, which already owns the scheduling primitives: basis: the maintenance skill's module dispatch contract (each concern single-homed; the decisions module owns lane decisions, the overlay owns scheduling primitives).
- assume the existing guards are unchanged: `G1e`/`G1a` keep their point-in-time reads and the fleet cap keeps its count; the duty acts only on the deferral outcome, never re-runs a guard: basis: the guards' fixed-order contract and the machinery admission protocol's default-to-fewer-blockers.
- assume one retry slot per lane per turn and no retry stacking: a turn that already finds a standing retry one-shot for the lane (children[] entry with a future fire time and matching target class) refreshes nothing and records the existing carrier: basis: the scheduling module's one-child-per-lane invariant and the duplicate-carrier verification arm.

Decision points requiring a grill: none remain (the trigger predicate shape, the fit-test source, the arming route, and the growth balance are resolved by the review's descriptive-predicate finding, the Quota-aware lane decisions' evidence standard, the overlay's existing child dispatch shapes, and the dark-window outcome this duty replaces, under the operator's standing interactive directive).

## Standing constraints

- No new blocker: the duty is an arming path, never a refusal path; it cannot block a lane, a landing, or a turn (machinery admission protocol: no blocking gate without an incident-backed admission row).
- The one-carrier rule is untouched: a retry one-shot is a child, never a parent; the recognition rule, the duplicate-parent tripwire, and the ownership allowlist apply to its creation exactly as to any child dispatch.
- The 5h wall is respected: the duty arms only when the fit test passes, so a retry one-shot always lands inside the current window; the reset-anchored successor is the only cross-window arm, and it reuses the recipe's margin.
- Single-homing: the duty text lives once (decisions.md); the overlay gains only the concrete primitive sentences that reference it; no rule is restated in both files.
- Growth balance: the additions are priced against the dark-window stop shape they retire (a turn that defers on occupancy no longer ends the loop's work for the day); Task 2's sentences add two sentences only, and no operative rule is duplicated.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the duty fires exactly on occupancy- or lock-shaped deferrals with a passing quota fit test, and the reset-anchored successor fires exactly on quota-wall stops
- minimality: two files touched, no script, no registry row, no state-schema change
- maintainability: the duty names its home and its primitive references by name (module dispatch contract)

**Done when:**
- the duty text exists in decisions.md with the descriptive trigger predicates, the fit test, the one-slot-per-lane bound, and the park fallback
- the overlay carries the concrete primitive sentences (delayMinutes one-shot shape, reset_at + 10-minute margin, recognition-match verification on already-exists)
- the pins suite, hygiene scan, and the plan's grep validations pass

**Ship when:** none; every condition is repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on the two Files: paths below are always in scope.

**Production code:**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/zcode.md` (Task 2)

**Tests / validation surfaces:**
- the plan's own Validation Commands (grep assertions over the two files, pins suite, hygiene scan)

**Plan-related extension:** implementation and review may change files not listed above; a finding is in scope when causally related to this plan. Otherwise reject.

**Out of scope; reject unless plan-related:**
- any script under `scripts/`, the machinery registry, the state-file schema, the guards module (`guards.md`), the survey module, the scheduling module: reason: the doctrine is skill-text-only by assumption and those surfaces are owned by other admissions.
- the backlog origin row beyond its `Status:` flip at execution closeout.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
grep -c "Occupied-lane chaining" agents/skills/maintenance/decisions.md
grep -c "reset-anchored successor" agents/skills/maintenance/zcode.md
```

## Tasks

### Task 1: Add the occupied-lane chaining duty to the decisions module

Context surface: the plan's Terms, this task, and `## Standing constraints`.


Files:
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `Step 3 lane-decision rules` in `agents/skills/maintenance/decisions.md`

- [x] The duty paragraph `Occupied-lane chaining` exists in decisions.md beside the Step 3 lane-decision rules, keying its trigger on the descriptive predicates (a `G1e`/`G1a` discovery-arm hold on a fresh foreign claim or live peer entry; a held merge or done lock observable; a deferral reason naming `pending-landing (primary occupied by peer session)`) - never on token literals, which no producer emits [class: IMPLEMENTATION_REQUIRED]
- [x] The duty runs the quota probe and applies the typical-run fit test before arming; a failing or unusable probe parks per the fallback instead of arming [class: IMPLEMENTATION_REQUIRED]
- [x] The duty arms at most one near-future retry one-shot per held lane per turn (default slot +45 minutes from the decision, at or after the freshest blocking claim's likely completion), records the armed automation id in the lane's `children[]` entry, and never stacks a second retry when a standing one exists for the lane [class: IMPLEMENTATION_REQUIRED]
- [x] The 5h-wall arm: a stop whose quota leg records the window as unfit for another run (the Quota-aware lane decisions' defer/near-reset/outcomes) arms the chain one-shot at the probe's reset time + the standing 10-minute margin (the reset-anchored successor), never inside the exhausted window [class: IMPLEMENTATION_REQUIRED]
- [x] The reduced-toolset park path: when the create primitive is unavailable, the duty parks `pending_rearm` with the payload copy per the existing park shape instead of arming [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: occupied-lane chaining duty keeps the loop off dark windows` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Carry the concrete primitive sentences in the runtime overlay

Context surface: the plan's Terms, this task, and `## Standing constraints`.


Files:
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `Scheduling primitives` in `agents/skills/maintenance/zcode.md`

- [x] The overlay's Scheduling primitives section gains the retry-one-shot sentence: the near-future retry one-shot uses the delayMinutes relative form (no cron), `recurring: false`, and its create verifies the returned fire time before treating the arm as landed [class: IMPLEMENTATION_REQUIRED]
- [x] The overlay gains the reset-anchored successor sentence: the 5h-wall successor uses the probe's `reset_at_epoch` + 10 minutes in the recipe's arming shape, with the already-exists refusal verified as success via the ENABLED recognition match [class: IMPLEMENTATION_REQUIRED]
- [x] Both sentences reference the decisions-module duty by name (single-homing; no rule restated) [class: IMPLEMENTATION_REQUIRED]
- [x] Validation: pins suite exit 0, hygiene scan exit 0, both grep counts positive [class: REPOSITORY_TEST]
- [x] Commit: `docs: runtime primitives for occupied-lane retry and reset-anchored successor` [class: IMPLEMENTATION_REQUIRED]
