# Plan: Quota-state-aware authoring primitive selection

Backlog origin: docs/history/backlog/2026-09-19-quota-blind-dispatch-primitive-choice.md
Live witness at authoring time: the 2026-09-21 scheduler turn's OffPeakCreate was
refused (idle-time task quota exhausted) and pivoted to in-session authoring, recorded
in .ai-playbook/scheduler-state.json decision_reason.authoring; this plan makes that
pivot the rule instead of an ad-hoc rescue.

## Terms

- D2: the maintenance skill's authoring decision (Step 3); selects the backlog item and requests a carrier for authoring it.
- Idle-time dispatch: creating the authoring child through the idle-time task primitive (OffPeakCreate); no clock, runs when off-peak compute is granted.
- In-session authoring: the deciding session performs the authoring itself under the authoring blueprint's duties, instead of dispatching a child.
- Carrier: which of the two carries the authoring work for a decided D2 target.
- Quota signal: the observed state of the 5-hour model quota window at decision time, named by one slug.
- Covered stand-down: an authoring child's edit-nothing outcome when the payload re-verification finds the target item covered or gone; machine surface .ai-playbook/last-authoring-stand-down.json; excluded from the failure cap.

## Assumptions

- assume the quota-state sources are the window probe percent/minutes-to-reset fields when its output is usable, the idle-time dispatch primitive's refusal message, the user's own report, and the state file's rate_pressure as a scarcity proxy; no new probe primitive is built; basis: the origin item's fix text ("user-reportable or host-surfaced; no independent probe primitive exists") and the existing probe vocabulary the related lane-decisions item reuses.
- assume the decision record carries the literal token `quota_signal=<slug>` inside decision_reason.authoring rather than a new top-level state field; basis: the acceptance criterion asks the decision record to name the observed signal as a grep-able field, and decision_reason already carries per-lane decision provenance, so no schema bump is needed.
- assume in-session authoring runs under the same blueprint duties as an idle child (ad-hoc worktree, pre-work gate, review loop, done skill, merge-locked self-landing) and records the standard children[] entry with the target suffixed `(in-session)`; basis: the four prior in-session authoring runs in the scheduler state children history recorded the same entry shape under the earlier suffix `(authoring, in-session)`, which the new arm's marker matching therefore also covers.
- assume executions never route in-session; basis: the origin item scopes the fix to the authoring carrier choice, and the execution lane's strictly-sequential child stance is unchanged.
- assume the recurring parent automation prompt's AUTHORING-ONLY MODE paragraph is out of scope; it lives in the automation record, not tracked files, and the loop-mode durable carrier backlog item owns its durability; basis: repo survey 2026-09-21.
- assume the related open item docs/history/backlog/2026-09-18-maintenance-quota-aware-lane-decisions.md (decision-layer percent/reset recording and lane branches) stays a separate origin; this plan only names the carrier-choice signal and does not implement percent/reset recording; basis: the origin item's Related section draws this boundary.

Decision points requiring a grill: none remain.

## Gist & Examples

The maintenance loop's authoring dispatch had a design-default bias: the idle-time
queue was treated as the primary carrier and in-session authoring as a fallback
reserved for idle-quota refusal. The 2026-09-19 incident dispatched work to an
unguaranteed queue slot while the deciding session was alive and the 5-hour quota
window had full capacity available; Andrey's correction ("why don't you run it right
now?") is the origin item. The loop's decision procedure never consults any quota
signal, so the bias cannot be audited either.

This plan adds three things.

1. A carrier-selection rule in D2 (SKILL.md): after selecting the target item,
   consult the live quota signal before choosing the carrier, deriving the signal at
   decision time (the window probe when the turn has not already run it; the
   dispatch primitive's refusal, the user's report, and rate_pressure as they
   occur). Quota available plus a session able to carry the work resolves to
   in-session authoring; idle queue refused or unavailable plus a session able to
   carry resolves to in-session as the pivot instead of parking a retry; quota
   scarce, near pause, peak-priced, or a session unable to carry resolves to the
   idle queue or defers the lane; an unknown signal keeps the existing defaults.
   The rule re-derives the carrier at every decision instead of reverting to a
   standing default, which is the failure family the origin item names ("defaults
   overriding narrower intent").
2. A grep-able record: every authoring decision names the observed signal as
   `quota_signal=<slug>` in decision_reason.authoring. Two conforming examples:
   `"authoring": "dispatch target X; quota_signal=probe-available; carrier:
   in-session"` and `"authoring": "dispatch target X; quota_signal=peak-window;
   carrier: idle-time dispatch"`. A no-op that cites quota names the signal too,
   so "plenty of quota" can never silently coexist with an idle lane.
3. A payload-side defense: idle authoring payloads gain a pre-execution
   re-verification stand-down gate in the authoring blueprint. A queued idle task
   cannot be cancelled or amended and may start long after the deciding turn's
   coverage check, so the payload re-checks, before any plan work, that the target
   item still sits at the backlog top level and is still plan-uncovered by an open
   top-level plan; when covered or gone, the child stands down writing nothing,
   writes the machine marker .ai-playbook/last-authoring-stand-down.json, and
   reports one line opening with STAND-DOWN; the checking turn qualifies the
   stand-down by the marker (never by report text), the authoring progress
   predicate yields to the carve-out so a covered stand-down never reads as
   progress, and the failure cap excludes outcome_reason covered-stand-down, so
   correct defensive behavior never trips the three-strike alert.

Signal slug vocabulary: `probe-available`, `probe-scarce`, `probe-near-reset`,
`probe-paused`, `rate-pressure-scarce`, `queue-refused`, `user-reported-available`,
`user-reported-scarce`, `peak-window`, `unknown`.

Out of scope: the execution lane (never routed in-session), the parent automation
prompt's mode paragraph (untracked), the lane-decisions item's percent/reset
decision-layer recording (separate origin), and any new quota probe primitive.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the D2 rule, the Quota signal definition, and the overlay carrier text are mutually consistent, name the signal sources, and never route the execution lane in-session; the maintenance pins suite exits 0 after every task.
- auditability: every carrier-bearing authoring decision record (dispatch, in-session pivot, or quota-citing no-op) names the observed signal via the `quota_signal=` token; the token, the slug vocabulary, the decision-time probe binding, the carrier-selection rule, and the in-session hold are documented in SKILL.md and pinned.
- protection: every idle authoring payload carries the still-uncovered stand-down gate; the gate sentence is countable in prompt-templates.md via a pin; the stood-down child's machine surface (.ai-playbook/last-authoring-stand-down.json) is documented with explicit precedence over the authoring progress predicate.
- compatibility: no state schema bump; the authoring blueprint body's placeholder set is unchanged; all pre-existing pins stay green.

**Done when:**
- The whole Validation Commands block exits 0 on the changed tree (gates 1 through 12).
- The pins suite carries and passes pins for the payload gate, the token, the slug vocabulary, the carrier-selection rule, the decision-time probe binding, and the in-session marker and hold.
- The plan passes the readiness gate on the final reviewed digest (plan_readiness.py exit 0, sidecar digest match).

**Ship when:**
- A later dispatch decision made under a full quota window runs in-session instead of queueing, witnessed in the scheduler state history [class: OPERATIONS_FOLLOW_UP]; evidence owner: the maintenance loop's own state file (decision_reason.authoring); closure condition: a children[] entry whose decision_reason names an available-window signal with an in-session carrier. The 2026-09-21 queue-refused pivot is the first witness; the rule makes the shape standard rather than exceptional.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`

**Tests:**
- `scripts/check_maintenance_pins.sh` *(new pins only; existing pins frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `.ai-playbook/scheduler-state.json`; reason: runtime state, gitignored, never edited by this plan's tasks.
- `docs/history/backlog/2026-09-18-maintenance-quota-aware-lane-decisions.md`; reason: separate origin with its own scope (decision-layer percent/reset recording).
- `agents/skills/maintenance/SKILL.md` Revisions entries older than this plan's; reason: frozen history.

## Validation Commands

```bash
#!/usr/bin/env bash
# Every gate is dedicated to one structural obligation (development_lessons #187)
# and aborts non-zero on miss (#191). Execute the whole block at authoring time
# and record the first failing gate (user-level lesson #337).
S=agents/skills/maintenance/SKILL.md
O=agents/skills/maintenance/zcode.md
P=agents/skills/maintenance/prompt-templates.md
PIN=scripts/check_maintenance_pins.sh

# Gate 1: D2 carries the quota-state-aware carrier-selection rule.
grep -qF 'quota-state-aware carrier-selection rule' "$S" \
  || { echo 'FAIL gate 1: D2 carrier-selection rule missing from SKILL.md'; exit 1; }

# Gate 2: the grep-able quota signal token is documented as a required record.
grep -qF 'quota_signal=' "$S" \
  || { echo 'FAIL gate 2: quota_signal token missing from SKILL.md'; exit 1; }

# Gate 3: the in-session children[] marker is documented for the G1a arm.
grep -qF '(in-session)' "$S" \
  || { echo 'FAIL gate 3: in-session marker missing from SKILL.md'; exit 1; }

# Gate 4: the overlay names the queue-refusal in-session pivot.
grep -qF 'author in-session under the authoring blueprint' "$O" \
  || { echo 'FAIL gate 4: queue-refusal pivot missing from zcode.md'; exit 1; }

# Gate 5: the overlay bans in-session routing for the execution lane.
grep -qF 'never routes in-session' "$O" \
  || { echo 'FAIL gate 5: execution-lane in-session ban missing from zcode.md'; exit 1; }

# Gate 6: the idle authoring payload carries the still-uncovered stand-down gate.
grep -qF 're-verify the target backlog item still sits at the backlog top level and is still plan-uncovered' "$P" \
  || { echo 'FAIL gate 6: payload re-verification gate missing from prompt-templates.md'; exit 1; }

# Gate 7: the deviation ledger registers the payload gate.
grep -qF 'Idle-payload re-verification stand-down gate' "$P" \
  || { echo 'FAIL gate 7: deviation entry missing from prompt-templates.md'; exit 1; }

# Gate 8: the pins suite is green (the countable mechanical surface).
bash "$PIN" \
  || { echo 'FAIL gate 8: maintenance pins suite failed'; exit 1; }

# Gate 9: the covered-stand-down carve-out and its cap exclusion are documented.
grep -qF 'outcome_reason is covered-stand-down' "$S" \
  || { echo 'FAIL gate 9: covered-stand-down exclusion missing from SKILL.md'; exit 1; }

# Gate 10: the SKILL.md-side execution-lane in-session ban.
grep -qF 'the execution lane is never routed in-session' "$S" \
  || { echo 'FAIL gate 10: execution-lane ban missing from SKILL.md'; exit 1; }

# Gate 11: the overlay excludes in-session entries from idle-listing attribution.
grep -qF 'excluded from idle-listing attribution' "$O" \
  || { echo 'FAIL gate 11: lane-visibility exclusion missing from zcode.md'; exit 1; }

# Gate 12: the in-session write modes are named in the sanctioned-writer wiring.
grep -qF 'in-session children[] append and its completion-time outcome update are scheduler-turn write modes' "$S" \
  || { echo 'FAIL gate 12: in-session write-mode wiring missing from SKILL.md'; exit 1; }

echo 'VALIDATION OK'
```

### Task 1: SKILL.md carrier-selection rule and quota-signal recording

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] In Step 3 D2, after the selection sentence, insert the quota-state-aware carrier-selection rule paragraph: the carrier is re-derived at every D2 decision from the live quota signal (defined in Step 4) before choosing between idle-time dispatch and in-session authoring; the signal is derived at decision time, never inherited from a standing default: when the turn has not already run the window probe (Step 4's clocked path), D2 runs scripts/quota_window_probe.py once (harness-supported per the detection helper; unusable output records unknown), and the refusal and user-report sources apply when they occur; idle queue refused or unavailable while the session can carry the work, or a fresh window with the session alive, resolves to in-session authoring performed under the authoring blueprint's duties (ad-hoc worktree, pre-work gate, review loop, done skill, merge-locked self-landing); quota scarce, near the pause thresholds, or peak-priced, or a session unable to carry the work, resolves to the idle-time queue or defers the lane; an unknown signal keeps the existing defaults; a deciding session is able to carry the work unless it cannot run the authoring blueprint's duties in-session (worktree creation unavailable, or the pre-work gate's merge or done-lock check failing at start), the blueprint's own pre-work gate being the observable that makes the branch mechanically decidable, quota scarcity belonging to the signal branches and not to this predicate; the inserted paragraph opens with the literal name quota-state-aware carrier-selection rule so the gate 1 span lands verbatim; the execution lane is never routed in-session [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 4 (quota leg), add the Quota signal definition paragraph: the signal sources are the window probe percent and minutes-to-reset when its output is usable, the idle-time dispatch primitive's refusal, the user's own report, and the state file's rate_pressure as a scarcity proxy, unknown otherwise; the probe read at the D2 carrier decision reuses this same probe (one invocation per turn when the clocked path has not already run it; no new primitive); the peak-window slug's named producer is the pricing calendar (the pricing_cache peak window, when the proposed carrier's run would start into or straddle it); list the slug vocabulary (probe-available, probe-scarce, probe-near-reset, probe-paused, rate-pressure-scarce, queue-refused, user-reported-available, user-reported-scarce, peak-window, unknown), mapping the rule's peak-priced wording to the peak-window slug and probe scarcity readings between available and near-reset to probe-scarce; state the precedence for conflicting sources at one decision: the dispatch-primitive refusal outranks the probe reading (it concerns the carrier path itself and is the most recent host-surfaced fact), a user report given at or after the probe read outranks the probe, otherwise the probe outranks the rate_pressure proxy, and unknown is recorded only when no source is readable; require every carrier-bearing authoring decision record (a dispatch, an in-session pivot, or a quota-citing no-op; guard-tripped stand-down no-ops excluded) to name the observed signal as the literal token `quota_signal=` followed by one slug, inside decision_reason.authoring [class: IMPLEMENTATION_REQUIRED]
- [x] In the State file section, extend the decision_reason field documentation and the children[] target-marker vocabulary with the `(in-session)` marker and prescribe the in-session state path: an in-session authoring run records the standard children[] entry (kind author, null automation id, null fire_at) and the G1a state-file arm gains an in-session branch holding the lane from created_at while the entry's outcome is pending, or progress without completion evidence, released on the certification oracle pass or the six-hour created_at horizon, idle-listing attribution inapplicable; the in-session branch's marker matching covers both the `(in-session)` suffix and the legacy `(authoring, in-session)` spelling the prior in-session entries carry, so live legacy-spelled entries hold the lane too; the early authoring outcome check evaluates in-session entries each turn from created_at (the run itself updates its outcome at completion); an idle authoring child standing down under the payload re-verification gate records outcome failed with outcome_reason covered-stand-down, qualified by the machine test: .ai-playbook/last-authoring-stand-down.json present with exactly the keys {"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}, the item key naming the child's target, and the justification still holding at check time (the item is covered by an open top-level plan or has left the backlog top level); the authoring progress predicate yields to this carve-out, so a qualified covered-stand-down never reads as progress despite the shared trigger conditions; the checking turn consumes the marker file only after the outcome record write has survived; a stale or unqualified marker (justification no longer holding, item key mismatch) accrues failure credit like any other child; the failure cap's count excludes entries whose outcome_reason is covered-stand-down; the in-session children[] append and its completion-time outcome update are scheduler-turn write modes (targeted edits under the existing retry rule), named in the sanctioned-writer enumeration and the Step 6 carry-forward list, overlap with the next cadence turn being covered by the existing carry-forward and lost-update rules; the children-entry schema note for outcome_reason names the new value covered-stand-down beside the existing stand-down value [class: IMPLEMENTATION_REQUIRED]
- [x] Append the Revisions ledger entry for the carrier-selection rule, dated 2026-09-21, naming the origin item and the queue-refusal witness [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 5, extend the authoring-lane carrier sentence ("the authoring lane takes the idle-time primitive or defers to the next turn") with the in-session carrier per the D2 rule, so the enumeration is complete: the authoring lane takes the in-session carrier, the idle-time primitive, or defers to the next turn [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: gates 1, 2, 3 pass in a block run; the block's first failing gate is gate 4 (the overlay is not yet edited); the gate 9, 10, and 12 spans are verified present in SKILL.md by direct grep (the block aborted before reaching them); gate 8 passes (additive SKILL.md prose breaks no existing pin) [class: REPOSITORY_TEST]

### Task 2: overlay carrier selection in the dispatch ladder

Files:
- `agents/skills/maintenance/zcode.md`

- [x] In "Child dispatch ladder" step 3 (second lane, authoring), insert the carrier-selection sentence: apply the skill's quota-state-aware carrier-selection rule before the OffPeakCreate call, deriving the signal per the skill's decision-time probe read (the overlay names the read), and on a refusal naming the exhausted idle-time task quota, author in-session under the authoring blueprint's duties instead of parking a retry when the session can carry the work, recording the standard children[] entry with the `(in-session)` marker and `quota_signal=queue-refused` in decision_reason [class: IMPLEMENTATION_REQUIRED]
- [x] In the same bullet, state the lane ban: the execution lane never routes in-session (its strictly sequential clocked-child stance is unchanged) [class: IMPLEMENTATION_REQUIRED]
- [x] In the "Idle-time lane visibility" bullet, add the sentence excluding `(in-session)` entries from idle-listing attribution while naming the state-file arm's in-session branch as their hold; the sentence carries the literal span "excluded from idle-listing attribution" so the gate 11 span lands verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: gates 1 to 5 pass in a block run; the block's first failing gate is gate 6 (the blueprint is not yet edited); the gate 11 span is verified present in zcode.md by direct grep (the block aborted before reaching it); gate 8 passes [class: REPOSITORY_TEST]

### Task 3: payload re-verification gate in the authoring blueprint

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [x] In the authoring blueprint's pre-work paragraph, immediately after the fire-time gate sentence, insert: before any plan work, re-verify the target backlog item still sits at the backlog top level and is still plan-uncovered by an open top-level plan (grep the resolved plans directory top level for the item's filename); when an open top-level plan now covers the item or the item has left the backlog top level, stand down writing nothing, write .ai-playbook/last-authoring-stand-down.json with exactly the keys {"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"} as the last action before reporting (an ad-hoc-worktree run writes the json into the primary checkout's .ai-playbook/ and verifies it present there), and report the stand-down in one line opening with the literal marker STAND-DOWN: <item-path> <covered|gone>; on any other outcome the marker line must not appear anywhere in the report and the file must not be written, so an ordinary failure report can never fake a stand-down (the json is the machine surface the checking turn reads; the marker line is only the human-visible witness) [class: IMPLEMENTATION_REQUIRED]
- [x] Register the deviation-list entry titled "Idle-payload re-verification stand-down gate (2026-09-21, quota-blind dispatch primitive choice plan)" with the rationale: a queued idle task cannot be cancelled or amended and may start long after the deciding turn's coverage check, so the payload carries the last-line defense; not part of the backlog source text [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full gate set passes at this point (1 to 12); gate 8 passes with the current pin set (the new pins arrive in Task 4; the authoring body's placeholder set is unchanged and no existing count pin covers the pre-work paragraph) [class: REPOSITORY_TEST]

### Task 4: pins for the new invariants

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Add pin "authoring payload re-verification gate": fixed-string grep over prompt-templates.md for the gate 6 span, so the payload gate is countable [class: REPOSITORY_TEST]
- [x] Add pins "quota signal token documented" (fixed-string grep over SKILL.md for `quota_signal=`) and "in-session marker documented" (fixed-string grep over SKILL.md for `(in-session)`) [class: REPOSITORY_TEST]
- [x] Add pins "carrier-selection rule present" (fixed-string grep over SKILL.md for the gate 1 span), "decision-time probe binding" (fixed-string grep over SKILL.md for `the signal is derived at decision time`), "in-session lane hold branch" (fixed-string grep over SKILL.md for `idle-listing attribution inapplicable`), "quota signal slug vocabulary" (fixed-string grep over SKILL.md for `probe-scarce, probe-near-reset`), and "covered-stand-down marker schema parity" (fixed-string grep over SKILL.md AND over prompt-templates.md for the exact marker key schema `{"item": "<backlog item path>", "reason": "<covered|gone>", "date": "<iso date>"}`, each file matching exactly once, so the two prescriptions cannot drift) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the whole pins suite exits 0 with the new pins included and no pre-existing pin affected; a stripped-sentence mutation probe (temporarily removing the payload gate sentence, then the D2 rule sentence) flips the corresponding new pin to FAIL each time, then restore [class: REPOSITORY_TEST]

### Task 5: full validation sweep

- [x] Run → expect GREEN: the whole Validation Commands block (gates 1 to 12) exits 0 with VALIDATION OK [class: REPOSITORY_TEST]
- [x] Run the no-em-dash scan and the public hygiene scan over the changed files; both exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `skills: quota-state-aware authoring carrier selection + idle payload re-verification gate` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-19-quota-blind-dispatch-primitive-choice.md: disposition folded into 2026-09-21-quota-blind-dispatch-primitive-choice.md (2026-09-25); per-item file deleted.
