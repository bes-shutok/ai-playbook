# Plan: audit-lane slot-take unblock

Backlog origin: docs/history/backlog/2026-10-08-audit-lane-slot-take-stalls-authoring.md (primary); rider origin (gate-clearing pins re-key): docs/history/backlog/2026-10-08-execute-plan-origin-head-pin-span-red.md
Driving force: automation (primary); reliability justification: the witnessed harm is loop continuity, a due-but-undispatchable audit read consuming a healthy authoring slot (the 2026-10-08 stall), so the work is implemented for loop continuity under the operator's D-5 direction despite continuity not being one of the ranked principles; park triage: not applicable, the origin row is an operator-directed direction, not a parked row
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-audit-lane-slot-take-unblock-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Authoring claim: docs/tmp/authoring-claims/2026-10-08-audit-lane-slot-take-unblock.md (session interactive-maintenance-auth-continuation)
Execution budget: 2.5h total, largest task 1.0h
Dispatch entry: PLAN-PROMPTS entry `audit-lane-slot-take-unblock` (frozen 2026-10-08); operator directive D-5 (docs/maintenance/operator-directives.md) carries the interim rule this plan makes durable

## Terms

- Dispatch-predicated slot take: the same-turn contention rule fires only when the audit child actually dispatches in the turn (a `children[]` entry exists); a due read alone never spends a work-lane slot.
- Work lane: the authoring or execution lane whose slot the contention rules govern (the D1/D2/D3 decision vocabulary, unchanged).
- D2/D3 (and D1): the maintenance scheduler turn's lane decisions in Step 3: D1 schedules an execution child, D2 schedules an authoring child, D3 authors in-session; the contention rules resolve D2 to D3 when an audit dispatch takes the authoring slot.
- Fallback leg: one step of the ordered carrier walk for a due registry audit-kind task: idle/off-peak first, then in-session, then retain.
- In-session leg conditions: the quota probe report is usable, `used_percent` is below the max-percent threshold, the probe decision is continue, and the session can carry the task's self-contained body; the same thresholds D2's in-session authoring uses.
- Self-contained body: the registry task file's body plus the resolved repository root, the same payload a scheduled audit child receives.
- Retained refusal evidence: the host refusal text and quota slug recorded in the retained `pending_dispatch` entry's additive note member.
- Additive note member: an optional free-form `note` member added to the `pending_dispatch` entry shape under the State-file section's additive-field pattern (no version bump, no existing member changes), so today's readers ignore it and tomorrow's readers can require it.
- Pending-dispatch-occupied: the audit park arbitration's skip reason when the single-valued `pending_dispatch` slot is already occupied; the skipped intent re-fires from its still-due `next_due`.
- Pins re-key: replacing a pin's expected span with its successor canonical wording after an owning edit changed the bytes, keeping the count semantics unchanged.
- Peer census: the discharging session's census write that stamps a registry task's `next_due` at its firing turn's opening boundary; the 2026-10-08 witness's discharge actor.
- Sanctioned discharge: a registry task's cadence-fired `next_due` stamp; the audit lane's legitimate dispatch trigger, never by itself a work-lane claim.
- Audit-kind: the registry task header kind (`audit`) whose due-read dispatches an audit child on the authoring lane; `rider`-kind tasks never consume the dispatch slot.
- Retriage-lane-due: the D2-to-D3 resolution reason literal the retriage same-turn contention rule records when the re-triage dispatch takes the authoring slot; pinned present-exactly-once.
- Interactive override set: the lane resolutions an interactive session's override may lift (the deferral-class trip set); the audit/retriage same-turn contention sits outside it, never liftable by override (unchanged by this plan).
- Step 1 pending-dispatch reader: the scheduler turn's Step 1 duty that validates a retained `pending_dispatch` target against the fresh survey and discharges it through the normal Step 5 path.
- Cold-start-reads-due: the rule that a registry task's missing state record reads due, so its first full dispatch happens at the next free slot under the same guards.
- Consult integrity caps: the registry consult's preserved bounds, byte-preserved by this plan: the one-audit-dispatch-per-turn bound, the 2-sub-agent fleet cap, the recorded token budget rule, the same-task in-flight guard with its 24-hour bound, the six-strike consecutive-failures deferral, the corruption arm, the dispatch-discipline parenthetical's claim check, and its queue-jump clause (a discharge due write takes the dispatch slot ahead of the cadence ordering).

## Why

On 2026-10-08 ~20:35 the loop stalled with abundant quota: the peer census stamped the deferred re-triage task due (a sanctioned discharge), the retained target validated on the next reader, but the idle-time dispatch primitive refused on exhausted idle quota, and the retriage-lane same-turn contention rule had already resolved D2 to D3 (`retriage-lane-due`), a slot take listed outside the interactive override set. No audit child ran, no authoring ran, no execution dispatched; a healthy window produced zero work (docs/history/backlog/2026-10-08-audit-lane-slot-take-stalls-authoring.md). Directive D-5 carries the interim rule (a due-but-undispatchable audit entry never holds the work lanes); this plan makes it durable in the skill text the turns actually execute.

The same landing window is blocked on a second, independent defect: the pins suite is RED on main because the pet-company-project-profile execution landing (605761d54) deliberately removed the class-derived base-branch fallback arm from agents/skills/execute-plan/SKILL.md and re-keyed nothing, so the pin requiring the span "resolves its default branch via the origin HEAD symbolic ref" counts 0 (docs/history/backlog/2026-10-08-execute-plan-origin-head-pin-span-red.md). The suite is a hard gate for every skill-touching landing, including this plan's own. The pins script is on the ad-hoc denylist (plan route only), so the re-key rides this plan: this plan already edits the pins file for its own re-keys, and the row's own direction assigns the re-key to the plan that owns the edit.

## Gist & Examples

TLDR: makes the audit lane's same-turn slot take dispatch-predicated and gives registry audit-kind tasks an ordered fallback walk ending in evidence-carrying retention, so a due-but-undispatchable audit read stops consuming work lanes (automation: the loop keeps authoring and executing through refused audit dispatches).

Example 1: the consult lists the re-triage task due, the authoring lane is free, the idle leg refuses (idle quota exhausted), and the in-session leg conditions hold; the turn dispatches the audit child in-session (the `children[]` entry carries the `(in-session)` marker), the slot take fires legitimately, and the authoring lane is genuinely occupied that turn.

Example 2: the idle leg refuses and the in-session leg conditions do not hold; the turn retains the target in `pending_dispatch` with the exact refusal evidence in the entry's additive note member (skipping with `pending-dispatch-occupied` when the slot is taken), and the lane decision proceeds under the normal rules, so the authoring or execution lane dispatches in the same turn.

Example 3: a skill landing runs the pins suite on main and passes, because the origin-HEAD needle now requires the successor span the landed pet-company bytes actually carry.

## Outcome

The maintenance loop's audit-lane contention is dispatch-predicated (a due read alone never takes a work-lane slot), registry audit-kind tasks have an ordered quota-independent fallback walk ending in evidence-carrying retention, the `pending_dispatch` entry shape gains an additive note member carrying that evidence, and the pins suite is green on main with the origin-HEAD needle re-keyed to the landed successor span.

Gate delta: the contention rule's firing condition narrows (it now requires an actual dispatch); registry audit-kind tasks gain ordered fallback legs; the Step 1 pending-dispatch reader's audit-kind arm gains the refusal-evidence note and the occupied-slot skip; the `pending_dispatch` field paragraph gains the additive note member; the pins suite's origin-HEAD row changes its expected span. No guard threshold changes, and the re-keyed rows keep their count semantics (normalized, exactly once).

## Assumptions

- assume the successor span for the origin-HEAD needle is the pet-company landed wording, dictated by the bytes already on main; basis: `git log -S` names 605761d54 as the removing commit, and the successor span counts exactly 1 normalized at the current tip.
- assume the refusal evidence lands in an additive `note` member on the `pending_dispatch` entry with no version bump and no behavior change for existing consumers (today's readers ignore unknown members); basis: the State-file section's additive-field pattern and the r1 panel's field-paragraph verification (r1 finding F3, worker A, folded).
- assume the in-session leg's quota thresholds are D2's existing in-session authoring thresholds, not new numbers; basis: the dispatch entry's "mirroring the execution lane's carrier-selection ordering" wording and the ordering bullet's own threshold sentence.
- assume the pins re-key rider belongs in this plan because this plan's landing gate needs the suite green and this plan already edits the pins file; basis: the pins row's "re-keyed by the plan that owns that edit" direction and the denylist's plan-route-only rule.

Decision points requiring a grill: folding the gate-clearing pins re-key into this plan: operator standing direction to continue authoring or execution without stops plus directive D-5's never-lose-time rule, operator chat and docs/maintenance/operator-directives.md D-5, 2026-10-08, affected: Task 3; successor needle taken as dictated-by-landed-bytes with no design choice: git trace naming the removing commit 605761d54 plus the normalized count verification, authoring session, 2026-10-08, affected: Task 3; in-session leg thresholds mirrored from D2 rather than newly chosen: the PLAN-PROMPTS entry audit-lane-slot-take-unblock mirroring wording, 2026-10-08, affected: Task 2.


## Standing constraints

- The consult integrity caps stay byte-preserved: the one-audit-dispatch-per-turn bound, the 2-sub-agent fleet cap, the recorded token budget rule, the same-task in-flight guard (both arms, the 24-hour bound), the six-strike consecutive-failures deferral, the corruption arm, the cold-start-reads-due rule, the dispatch-discipline parenthetical's claim check, and its queue-jump clause.
- The `retriage-lane-due` reason literal stays present exactly once in agents/skills/maintenance/SKILL.md (pins "retriage-lane-due reason literal present" and "exactly-once"); `audit-lane-due` stays present.
- The interactive override set stays as written; this plan changes when the contention fires, never the override set.
- Idle/off-peak stays the preferred carrier for audit-kind tasks; the in-session leg runs only when the idle leg is unavailable.
- No state-schema version change: the refusal evidence reuses the `pending_dispatch` entry's shape plus the additive note member only; the `children[]` kind enum is unchanged; the `(in-session)` marker machinery is reused as-is.
- Pins edits happen only through this plan (the ad-hoc denylist bans the pins suite path; plan route only).
- D-5 remains the operator will of record; the skill text becomes its durable form and the record's pointer is updated at landing; the record is never deleted.

## Evaluation Criteria

**Done when:**

- Tasks 1 through 3 are checked.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- `bash scripts/check-no-em-dash.sh added-lines --base main` is clean over the landing range.
- The public hygiene scan passes (exit 0).
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-audit-lane-slot-take-unblock.md` passes, binding the final review round.

**Ship when:** the next witnessed due-but-undispatchable audit read leaves the work lanes free (the deciding turn's `decision_reason` records the retention with the refusal evidence while the authoring or execution lane dispatches the same turn), and a skill-touching landing passes the pins suite on unmodified main bytes.

## Review Scope

**Production code:**

- agents/skills/maintenance/SKILL.md

**Tests:**

- scripts/check_maintenance_pins.sh

**Documentation:**

- docs/maintenance/operator-directives.md

## Validation Commands

- `bash scripts/check_maintenance_pins.sh`
- `bash scripts/check-no-em-dash.sh added-lines --base main`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-08-audit-lane-slot-take-unblock.md`

Validation preamble: authoring-time mechanical gates, 2026-10-08: fixer total 0 substitutions; em-dash `touched` OUTCOME: pass; public hygiene OUTCOME: pass; `plan_readiness.py --pre-round` OUTCOME: pass (structural checks clean, review record not consulted). Rule 19 RED-today execution evidence: the pins suite on the authoring base exits 1 with exactly "PIN FAIL: base-branch origin-HEAD fallback arm count 0 != 1 in execute-plan SKILL.md" (the pre-existing RED this plan's Task 3 clears; origin row docs/history/backlog/2026-10-08-execute-plan-origin-head-pin-span-red.md). Round-start state for r1: worktree branch 2026-10-08-audit-lane-slot-take-unblock at commit 3eb095b5a, plan digest c3433ec03762208189def6f2598c96b3721fd13c6024f05dcd44ff20830ef34a.

## Tasks

### Task 1: Dispatch-predicated slot take, occupied-slot arm, and retained-refusal evidence

Files: agents/skills/maintenance/SKILL.md (the Audit-lane same-turn contention bullet, the Retriage-lane same-turn contention bullet, the Pending dispatch bullet's audit-kind validation arm, the `pending_dispatch` field paragraph in the State-file section).

- [x] Rewrite the Audit-lane same-turn contention bullet so the slot take fires only when the audit child actually dispatches in the turn (a `children[]` entry exists); when the consult lists a due audit-kind entry but every dispatch leg refuses (the idle queue refuses or is unavailable, or the host one-pending-idle-task-per-session limit blocks the idle dispatch leg), retain the target in `pending_dispatch` (audit kind) with the refusal recorded as its quota signal and the refusal evidence in the entry's additive note member; the retention writes only into a null `pending_dispatch` slot, and when the slot is occupied the retention skips with the arbitration's `pending-dispatch-occupied` reason, letting the task re-fire from its still-due `next_due`; the lane decision then proceeds under the normal rules; the retained-park re-dispatch on a freed lane and the cold-start-reads-due rule stay byte-preserved [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the Retriage-lane same-turn contention bullet to the same dispatch-predicated shape, keeping the `retriage-lane-due` reason literal present exactly once, the co-due oldest-`next_due`-first ordering, and the audit arbitration park unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Step 1 pending-dispatch reader's audit-kind validation arm: a retained audit-kind target whose dispatch legs refuse again is retained with the exact refusal evidence (host message, quota slug) written into the retained entry's additive note member so the next reader chooses retry-versus-switch-leg without re-deriving the failure, and a retained target never resolves a work lane to the audit dispatch by its due read alone [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the `pending_dispatch` field paragraph in the State-file section with the additive optional `note` member (free-form state such as refusal evidence) under the section's additive-field pattern, no version bump, no existing member of the shape changed [class: IMPLEMENTATION_REQUIRED]
- [x] Name directive D-5 in the two contention bullets and the pending-dispatch reader arm as the operator will of record with this text as its durable form, so a turn reading the directives home first binds both [class: IMPLEMENTATION_REQUIRED]

### Task 2: In-session fallback leg for registry audit-kind tasks

Files: agents/skills/maintenance/SKILL.md (the Recurring-task registry consult bullet's dispatch discipline).

- [x] Give the registry consult's audit-kind dispatch discipline the ordered fallback legs mirroring the Execution-lane carrier-selection ordering: the idle/off-peak leg first (unchanged, preferred), then the in-session leg when the idle leg is unavailable (the idle queue refuses or the primitive is absent after the precheck) and the in-session leg conditions hold, recording the `children[]` entry with the `(in-session)` marker, null id and fire times, and `quota_signal`; a lower leg never runs while a higher leg is available, and the same-task in-flight guard applies to the in-session leg unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] State the retain leg after the in-session leg: when every dispatch leg refuses, retain in `pending_dispatch` per Task 1's arm with the refusal evidence and the occupied-slot skip, never holding the turn's work lanes behind the audit task [class: IMPLEMENTATION_REQUIRED]
- [x] Verify by inspection that the consult integrity caps are byte-preserved after the edits (the one-audit-dispatch-per-turn bound, the 2-sub-agent fleet cap, the token budget rule, the same-task in-flight guard, the six-strike deferral, the corruption arm, the dispatch-discipline parenthetical's claim check, and its queue-jump clause), recording the verification in the execution evidence log [class: REPOSITORY_TEST]

### Task 3: Pins re-key (gate-clearing rider) and D-5 pointer

Files: scripts/check_maintenance_pins.sh; docs/maintenance/operator-directives.md (D-5 record pointer line only).

- [x] Re-key the `base-branch origin-HEAD fallback arm` pin needle from "resolves its default branch via the origin HEAD symbolic ref" to the landed successor span "the branch named by `origin/HEAD` when that ref is available" (normalized count exactly 1, wrap-tolerant per the block's normalized-count convention), and update the block comment to name the successor span with its provenance (the pet-company-project-profile execution landing 605761d54 removed the class-derived fallback arm; origin docs/history/backlog/2026-10-08-execute-plan-origin-head-pin-span-red.md) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-key any pin over the edited spans (the two contention bullets, the pending-dispatch reader arm, and the registry consult bullet's dispatch discipline, including its `dispatches at most one overdue audit-kind task` span pin) that the Task 1 and Task 2 rewrites invalidated, in the same change [class: IMPLEMENTATION_REQUIRED]
- [x] After the re-keys, verify the `retriage-lane-due` pins (present, exactly-once) pass and record the per-pin verification in the execution evidence log [class: REPOSITORY_TEST]
- [x] Run the full pins suite to exit 0 and record the receipt in the execution evidence log [class: REPOSITORY_TEST]
- [x] Update the D-5 record in docs/maintenance/operator-directives.md with a pointer line naming the landed skill spans (the two contention bullets, the pending-dispatch reader arm, and the registry consult bullet) as the durable form of the interim rule; the record's status stays active and nothing else in the record changes [class: IMPLEMENTATION_REQUIRED]
