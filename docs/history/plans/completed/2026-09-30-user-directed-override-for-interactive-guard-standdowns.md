# Plan: User-directed override for interactive guard stand-downs

Backlog origin: docs/history/backlog/2026-09-28-user-direct-request-overrides-standdown.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-user-directed-override-for-interactive-guard-standdowns-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An interactive maintenance session whose current directive came from a live user message proceeds past a deferral-class guard instead of standing down, records the proceed with the literal `user-directed-override`, and unattended sessions keep every stand-down they have today.

- After this plan, a tripped `G1e`/`G1a` occupancy arm (including the plain fleet-cap arms, both discovery arms, and D2's fresh-foreign-claim consult skip), `G3`'s done-lock-held arm, `G3b`'s hold, and the landing gate (the Invariants post-review pre-landed cap) together with its Step 5 final-slot read no longer end an interactive turn in a stand-down: the turn states the tripped guard and its evidence in one line, chooses a non-colliding surface, and proceeds, recording `user-directed-override` plus the guard's name in `decision_reason`.
- Integrity protections and non-collision pacing or exactly-once trips stay unoverridable: the `G2` failure cap, `G3`'s merge-or-rebase-in-progress arm, corrupted merge-lock metadata, the foreign-dirt landing gates, the duplicate-parent and duplicate-user-directed-dispatch tripwires, rate pressure, and the cycle gate refuse the override.
- The state reader can surface every override mechanically, because the recorded `decision_reason` carries the grep-able literal, and a pins-suite pin holds the predicate durable after this plan's execution.

Gate delta: adds one interaction rule (a Step 2 guard-list bullet, D-lane recording clauses, and a runtime-overlay mirror section), one recorded literal (`user-directed-override`), and three pins-suite presence pins; removes no guard, no arm, and no unattended stand-down semantics; priced by the witnessed 2026-09-28 double correction - the 18:21 interactive turn stood down `D3` on a held done lock while the peer had already landed both runs by the 18:24 re-survey, and the operator corrected within the turn ("you shouldn't have done this"), after which the same session's override execution (state-ledger `children[24]`, "override of 18:21 stand-down") executed and closed a plan by 19:14.

## Terms

- **Interactive session**: a session whose current turn's directive arrived in a live user message - the same interactive sense the trigger-verb bindings paragraph pins ("interactive asks from a human-typed message; an unattended scheduler turn never blocks on questions regardless of wording"); an automation-born turn with no live user turn is unattended.
- **Deferral-class trip**: a guard arm whose verdict is defer, stand down, or skip and whose protection is serialization, not integrity: the `G1e`/`G1a` occupancy arms (state-file, armed, fired, widened, the plain fleet-cap arms, and both discovery arms, plus D2's fresh-foreign-claim consult skip), `G3`'s done-lock-held arm, `G3b`, and the landing gate (the Invariants post-review pre-landed cap) together with its Step 5 final-slot read.
- **Non-overridable trip**: everything else the guards resolve on: the `G2` failure cap, `G3`'s merge-or-rebase-in-progress arm (the shared checkout's index is mid-mutation), corrupted merge-lock metadata, the foreign-dirt landing gates (the done gate's refusal to land over a peer's uncommitted dirt), the duplicate-parent and duplicate-user-directed-dispatch tripwires, rate pressure, and the cycle gate; never overridable for any session kind.
- **Non-colliding surface**: the session's own per-execution worktree (P57 isolation), landing-completion work for a completed unlanded run, or a target verified disjoint from the peer's in-flight target, its fresh claim set, and its uncommitted dirt on shared paths.
- **User-directed override**: the recorded proceed decision; `decision_reason` carries the literal `user-directed-override` plus the tripped guard's name, for example `user-directed-override:G3 done-lock hold`.

## Assumptions

- assume the override predicate is user presence, never confidence; basis: the origin's fix shape and the witnessed 18:21 probe reading - the holder PID reported dead while the 35-second lock age ruled out a stale-crash steal, and the peer landed both runs by the 18:24 re-survey, so a mood-based or evidence-guessing predicate would have repeated the same loss.
- assume the current state file no longer carries the practice records (its `children[]` ledger pruned them), so the plan cites state-file history instead: commit `ff4dd322` of `.ai-playbook/scheduler-state.json` carries `children[13]` ("user override of G1a peer hold", the authoring override that landed b36d5e2a), `children[22]` (the 18:21:07 stand-down record: "stand-down D3: G3 tripped on live peer occupancy of the primary checkout - done-lock held (label main-exec-done, acquired 18:19:49 local, 35s old, holder PID reported dead but age rules out stale-crash steal)"), and `children[24]` (19:14:26, "in-session execution (user one-by-one exec directive, override of 18:21 stand-down)", executed the account-quota-governor plan to squash main 1f404537 and filed this origin, "backlog user-direct-request-overrides-standdown filed 8e877968"); the em dash the blob carries in `children[22]` is rendered as a plain hyphen throughout this plan per the repo's em-dash gate; basis: probed the historical blob on 2026-09-30.
- assume the existing `G1a` target-distinctness carve-out and D2's fresh-foreign-claim consult stay byte-untouched; basis: the carve-out is the standing-directive rule for authoring targets and the consult is a selection-time skip, while this plan adds the interactive-presence proceed for all deferral-class trips - neither restates nor rewords the other, and the override never authorizes a same-target proceed, so the two rules compose without overlap.
- assume `G3`'s two arms split: the done-lock-held arm is overridable (the lock serializes landings; disjoint work in the session's own worktree is safe and the landing still waits for the lock), while the merge-or-rebase-in-progress arm is integrity (the shared checkout's index is mid-mutation) and keeps standing the turn down; basis: the origin's exclusion list names the integrity family, and the 18:21 witness's held lock was a landing serialization, not an index mutation.
- assume rate pressure and the cycle gate are non-overridable pacing and resource trips (an interactive override answers peer-collision serialization, not permission to spend quota against operator pacing or to bypass a user-set compaction gate); basis: the origin's deferral list names only occupancy, done-lock, and landing-gate trips, and the p85 prompt's overridable set mirrors it.
- assume the authoring blueprints in `agents/skills/maintenance/prompt-templates.md` stay byte-untouched; the rule lives in the maintenance skill and its runtime overlay, and payloads inherit it through the skill text they already carry; basis: the pins suite pins those blueprints and the by-reference wiring precedent of the cycle-7 authoring-claim plan.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: an interactive session carrying a live user directive proceeds past a tripped occupancy, done-lock, or landing-deferral guard with a one-line recorded override and a non-colliding surface, instead of reporting a stand-down the operator must override by hand - while unattended turns keep every stand-down they have today and a pins-suite pin keeps the predicate durable.

**Before (today):** On 2026-09-28 18:21 an interactive session carrying the directive "execute plans one by one" surveyed a live peer (done-lock `main-exec-done` 35 seconds old, fresh peer dirt, a live authoring claim, two outstanding unlanded runs) and resolved the whole turn to a `D3` stand-down, reporting instead of working. The operator corrected within the turn. The re-survey at 18:24 showed the peer had already squash-landed both runs - the stand-down bought nothing, and a disjoint-target execution would have been safe and productive. The state ledger's own history records the practice working when the session dared it: `children[24]` executed a full plan to landing under "override of 18:21 stand-down" - but the rule exists nowhere in the skill text, and the literal `user-directed-override` matches zero files under `agents/` and `scripts/` today.

**After (this plan):** The same 18:21 survey states one line - `user-directed-override:G3 done-lock hold` with the lock's age and holder evidence in `decision_reason` - picks its own per-execution worktree for a plan disjoint from the peer's in-flight target, dirt, and claims, and dispatches, while the landing still serializes on the merge lock. An unattended turn running the identical survey stands down exactly as today, because its directive arrived from an automation payload, not a live user message.

## Evaluation Criteria

**Quality dimensions:**

- asymmetry correctness: the only trip condition for the proceed path is that the current directive arrived in a live user message; every unattended resolution (stand-down, deferral, skip, D3 record) is behaviorally identical to today's bytes, and no confidence, staleness-guess, or dead-PID reading ever substitutes for user presence.
- composition correctness: the `G1a` target-distinctness carve-out, D2's fresh-foreign-claim consult, the loop-mode enforcement precedence, the duplicate-parent and duplicate-user-directed-dispatch tripwires, and the pinned blueprints stay byte-untouched or are explicitly cross-referenced, never reworded.
- fail-closed recording: every override proceed writes `user-directed-override` plus the tripped guard's name into `decision_reason`; a proceed without the literal is a defect; the durable pins fail the pins suite when the predicate sentence or the integrity exclusion is edited away.

**Done when:**

- `bash scripts/check_maintenance_pins.sh` exits 0 including the three new pins.
- The Validation Commands block below exits 0 end to end.
- The em-dash gate (`scripts/check-no-em-dash.sh touched`) exits 0 on the changed tree, and the hygiene scan named by `public_hygiene_scan_script` in the user facts exits 0.

**Ship when:**

- None; skill prose and a pins-suite extension only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

**Tests:**

- the pins suite invocation (`bash scripts/check_maintenance_pins.sh`) is the test surface; no separate test file is added (the suite's pin helpers are the assertion mechanism)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/maintenance/prompt-templates.md`; byte-pinned child blueprints (pins suite) - payloads inherit the rule through the skill text they carry.
- The `G1a` target-distinctness carve-out and D2's fresh-foreign-claim consult wording; composition targets, not rewording candidates.
- `scripts/plan_readiness.py`; the certification oracle stays a byte-property gate.

## Validation Commands

```bash
# Tasks 1-3: per-file wiring obligations (each token below is verified absent from its file at authoring time, so a skipped task fails its grep; run from the repo root)
grep -qF 'user-directed-override' agents/skills/maintenance/SKILL.md || { echo "FAIL: override rule missing from the skill"; exit 1; }
grep -qF 'user-directed-override' agents/skills/maintenance/zcode.md || { echo "FAIL: override mirror missing from the overlay"; exit 1; }
grep -qF 'The override predicate is user presence, never confidence.' agents/skills/maintenance/SKILL.md || { echo "FAIL: predicate sentence missing from the skill"; exit 1; }
grep -qF 'The override predicate is user presence, never confidence.' agents/skills/maintenance/zcode.md || { echo "FAIL: predicate sentence missing from the overlay"; exit 1; }
grep -qF 'Integrity guards are never overridable' agents/skills/maintenance/SKILL.md || { echo "FAIL: integrity exclusion missing"; exit 1; }
grep -qF 'stand-down semantics unchanged' agents/skills/maintenance/SKILL.md || { echo "FAIL: unattended clause missing from the skill"; exit 1; }
grep -qF "Automation-born sessions keep today" agents/skills/maintenance/zcode.md || { echo "FAIL: unattended clause missing from the overlay"; exit 1; }
grep -qF 'the plain fleet-cap arms' agents/skills/maintenance/SKILL.md || { echo "FAIL: fleet-cap arms missing from the trip set"; exit 1; }
grep -qF 'proceed-per-this-rule' agents/skills/maintenance/SKILL.md || { echo "FAIL: precedence qualification missing"; exit 1; }
grep -qF 'outside the deferral-class trip set' agents/skills/maintenance/SKILL.md || { echo "FAIL: D3 scope clause missing"; exit 1; }
grep -qF 'proceeds its D4' agents/skills/maintenance/SKILL.md || { echo "FAIL: D4 fate clause missing"; exit 1; }
grep -qF "refusal to land over a peer" agents/skills/maintenance/SKILL.md || { echo "FAIL: foreign-dirt referent mapping missing"; exit 1; }
grep -qF 'distinct from the loop stand-down' agents/skills/maintenance/zcode.md || { echo "FAIL: sibling-sense cross-reference missing"; exit 1; }

# Task 4: the durable pin (RED until Tasks 1 and 3 land, GREEN after)
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins suite"; exit 1; }

# Composition guard: the edit must not remove or reword the carve-out or consult spans (diff-based; a removed line naming them fails)
if git diff main -- agents/skills/maintenance/SKILL.md | grep -qE '^-.*(target-distinctness carve-out|Fresh-foreign-claim consult)'; then echo "FAIL: pre-existing rule reworded"; exit 1; fi

# By-reference: the pinned blueprints stay byte-untouched
git diff --quiet main -- agents/skills/maintenance/prompt-templates.md || { echo "FAIL: blueprints changed"; exit 1; }

# Em-dash gate on the changed tree
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em dash in changed tree"; exit 1; }
```

### Task 1: Step 2 rule bullet

Files:

- `agents/skills/maintenance/SKILL.md`

Evidence:

- The Validation Commands block's skill wiring greps; each covers one prescribed literal below.

- [ ] Add one bullet as the last item of the Step 2 guard list, immediately after the `G3b (landing in flight)` bullet and before the `### Step 3: decision` heading, titled `- \`User-directed override (interactive sessions)\``, carrying a dated witness citation (2026-09-30, this plan's origin) per the skill's revision convention [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's trip condition reads: when the session is interactive - the current turn's directive arrived in a live user message, the same interactive sense the trigger-verb bindings paragraph pins - and a deferral-class trip fires (the `G1e`/`G1a` occupancy arms including the plain fleet-cap arms, both discovery arms, and D2's fresh-foreign-claim consult skip, `G3`'s done-lock-held arm, `G3b`, and the landing gate (the Invariants post-review pre-landed cap) together with its Step 5 final-slot read) [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's proceed duty reads: state the tripped guard and its evidence in one line in the lane's `decision_reason`, choose a non-colliding surface (its own per-execution worktree, landing-completion work for a completed unlanded run, or a target verified disjoint from the peer's in-flight target, fresh claim set, and uncommitted dirt on shared paths), and proceed instead of standing down [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's recording literal reads: the `decision_reason` line carries `user-directed-override` plus the tripped guard's name [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's exclusion sentence reads verbatim: "Integrity guards are never overridable: the `G2` failure cap, `G3`'s merge-or-rebase-in-progress arm, corrupted merge-lock metadata, the foreign-dirt landing gates (the done gate's refusal to land over a peer's uncommitted dirt), the duplicate-parent and duplicate-user-directed-dispatch tripwires, rate pressure, and the cycle gate refuse the override." [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's unattended clause reads verbatim as two sentences: "Unattended sessions keep today's stand-down semantics unchanged. The override predicate is user presence, never confidence." [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's precedence sentence names the unedited sites and qualifies them: for every site that resolves a deferral-class trip without naming this rule - `G3`'s whole-turn stand-down, the Step 3 guard-trip resolution mapping, the Step 5 final-slot precondition, and the in-session dispatch mode's done-lock pre-work gate - the resolution reads as today for an unattended session and as proceed-per-this-rule for an interactive one, while an integrity or non-overridable trip resolves as today everywhere [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet's collision floor reads: never a peer's in-flight target, never a stolen fresh lock, never a same-target proceed; isolation, not inaction, is the answer, and the merge lock still serializes every landing [class: IMPLEMENTATION_REQUIRED]

### Task 2: Step 3 decision clauses

Files:

- `agents/skills/maintenance/SKILL.md`

Evidence:

- The Validation Commands block's `outside the deferral-class trip set` and `proceeds its D4` greps.

- [ ] Append one clause to `D1 (execute)` and the matching clause to `D2 (author)`: an interactive session reading a deferral-class trip resolves that trip per the User-directed override rule instead of holding the lane, recording `user-directed-override:<guard name>` in `decision_reason`; no other precondition wording is reweighed [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the scoped clause to `D3 (no-op)`: a D3 record caused by a deferral-class guard trip is written only when the session is unattended; an interactive session proceeds per the User-directed override rule and records the override in `decision_reason` instead of that D3 record; D3 resolutions whose cause lies outside the deferral-class trip set are unchanged for every session kind - the cycle gate, audit and re-triage lane contention, log-entry authoring, rate pressure, the integrity guards and tripwires, and a plain no-dispatchable-target D3 [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the D4 fate sentence near the lane decisions: a lane's D4 resolution follows its lane decision - an interactive override that proceeds the lane proceeds its D4, while the `G2`/`G3`-driven D4 suppression stays integrity-governed; the loop-mode enforcement paragraph keeps its precedence over every lane decision [class: IMPLEMENTATION_REQUIRED]

### Task 3: Runtime overlay mirror

Files:

- `agents/skills/maintenance/zcode.md`

Evidence:

- The Validation Commands block's overlay greps (mirror, predicate, unattended clause, sibling-sense cross-reference).

- [ ] Add a short section `## User-directed override (interactive sessions)` between the end of the Interactive dispatch template section and the `## Child dispatch ladder` heading [class: IMPLEMENTATION_REQUIRED]
- [ ] The section states the rule is interactive-only and pinned in the maintenance skill's Step 2 (reference, no restatement of the full rule), and carries these verbatim sentences: "Automation-born sessions keep today's stand-down semantics unchanged. The override predicate is user presence, never confidence." [class: IMPLEMENTATION_REQUIRED]
- [ ] The section states the recording convention: an override-proceeding session records `user-directed-override:<guard name>` in `decision_reason`, so the state reader and the weekly rider surface every override [class: IMPLEMENTATION_REQUIRED]
- [ ] The section adds the sibling-sense cross-reference: this sense of user-directed override is distinct from the loop stand-down's Operator override (2026-09-21) and from the duplicate-user-directed-dispatch tripwire's payload-provenance sense of user-directed [class: IMPLEMENTATION_REQUIRED]

### Task 4: Durable predicate pins

Files:

- `scripts/check_maintenance_pins.sh`

Evidence:

- `bash scripts/check_maintenance_pins.sh`; RED until Tasks 1 and 3 land, GREEN after; covers the durability criterion.

- [ ] Add two presence pins using the suite's existing `pin()` helper with fixed-string greps: the predicate sentence `The override predicate is user presence, never confidence.` present in the skill AND in the overlay, described so a PIN FAIL names which file lost it [class: IMPLEMENTATION_REQUIRED]
- [ ] Add one presence pin for the integrity exclusion literal `Integrity guards are never overridable` in the skill [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the header comment's pin-family enumeration with the interactive-override predicate family [class: IMPLEMENTATION_REQUIRED]

### Task 5: Validation execution

Files:

- none (execution-only task)

Evidence:

- The Validation Commands block, run end to end from the executing worktree root; covers every Done-when criterion.

- [ ] Run the Validation Commands block end to end and record its exit 0 in the execution evidence, then run the hygiene scan named by `public_hygiene_scan_script` in the user facts over the changed tree and record exit 0 [class: REPOSITORY_TEST]
