# Plan: parked-dependency visibility for the execution lane

Backlog origin: docs/history/backlog/2026-09-25-execution-serialization-stall-visibility.md (Priority: high, class real)
Driving force: new-capability (the parked-dependency visibility surface) with primary motivation reliability (loop liveness). Secondary: efficiency.
Justification (non-principle primary force): on 2026-09-25 the only live execution plan froze behind a parked branch with no surface reporting the wait, and the unblock was hours of unowned work resolved only by a human question; park-triage would not take this item because the loss is witnessed, the class is real, and no existing plan owns scheduler-side dependency visibility.

## Terms
- **Parked-dependency ledger** (`parked_dependencies`): the state-file array recording every live "plan waits on an unlanded branch or origin ref" relation; additive under schema 4.
- **Ledger entry**: one object `{"plan", "blocked_on", "since", "boundary_arm"}` plus four optional keys: `deferred_until` (ISO 8601; set by a gate-refusal deferral, honored by the survey arm's actionable proposal and D1's unblock selection), `refusal_count` and `refused_tip` (the consecutive refused unblock attempts and the resolving-ref tip sha at the last refusal; the survey arm resets the count when the tip differs), and `landed_as` (the squash commit sha the unblock child records in its own targeted edit at verified landing, BEFORE the separate clear edit, so the sha is durably observable and the resolution probe's ancestry arm can fire on a lost clear write); `plan` is the resolved plans_dir-relative plan path, `blocked_on` is the BARE ref name as a probe namespace prefix consumes it (a local branch name like `main`, or a remote-qualified name like `origin/foo`), `since` is the ISO 8601 wait start, `boundary_arm` is the task or gate identifier that recorded the wait.
- **Liveness state**: the survey arm's per-entry classification: `actionable` (a ref resolves in either namespace with a positive ahead count and no live session work exists for the plan; evaluated first and wins over the aging states), else `stale` (the entry's `since` is at or past the stale threshold), else `waiting` (younger than the stale threshold).
- **Stale threshold**: two cadence periods; the maintenance skill's cadence period is 2 hours per the rearm-on-touch mirror in `scripts/rearm_on_touch.py`.
- **Unblock dispatch**: the execution-kind child that lands the blocking branch (rebase onto current main, the branch's validation gates, merge-locked landing), then re-queues the serialized plan.
- **Dependency-branch landing**: a merge-locked landing whose squashed content is a dependency branch rather than a plan-execution branch; subject to the landing-race discipline of Task 5.
- **Boundary arm**: the plan task or gate whose recorded wait is the serialization boundary; the named instance is the recovery-contract plan's Task 1 drift gate ("land-after-workstream, with the re-cert obligation on drift", docs/plans/completed/2026-09-25-execute-plan-recovery-contract-preflight.md).

## Assumptions
1. The ledger is a new additive state field `parked_dependencies`, not a reshaping of `execution_queue` entries into objects; basis: the schema-4 additive precedent (`execution_queue`, `execution_priority`, `pending_landing`, `rate_limited_events` each added with no version bump, per the Revisions ledger) and every `execution_queue` consumer treating entries as plain path strings.
2. The origin item's exact-location path `projects/.ai-playbook/scheduler-state.json` is a path slip; the live state file is `.ai-playbook/scheduler-state.json` at the repository root and is gitignored; basis: the State file section's path sentence and `git ls-files .ai-playbook/` returning nothing tracked. This plan edits only the skill prose that defines the schema, never the runtime file.
3. The stale threshold is two cadence periods; basis: the child lane-hold horizon is 6 hours (three periods), so a stale mark cannot race a live child's own horizon, and the cadence period is the skill's established aging unit.
4. The unblock dispatch is an execution-kind child sharing the existing execution dispatch discipline (guards, quota leg, fleet cap, landing gate, rate-pressure condition), not a new child kind; basis: it is a member of the execution-blueprint family in prompt-templates.md (the same family whose dispatch slice, re-arm carriage, and guard classification it reuses), distinct from the audit-lane analogy.
5. The re-cert obligation after a dependency-branch landing names a fresh focused review-plan round over the re-baselined touched surfaces with the digest re-bound before implementation resumes; basis: the drift-gate re-cert semantics the recovery-contract plan's Task 1 records and the execute-plan PRE-STEP re-cert's design role as the drift handler.
6. The origin item's non-goals hold: no automatic landing of parked branches outside the normal gates (the unblock dispatch IS the gated path), and no change to plan-authoring serialization itself (Task 1-style drift gates stay as they are); basis: the origin item's Non-goals section.

Decision points requiring a grill: none remain.

Residual findings (cap round r5, deferred by the finalize-at-cap rule; each is recorded for the implementation review or a backlog follow-up, none blocks the design):
- Medium: the origin's "green and landable" actionable conjunct is carried only as the branch-resolves-plus-ahead probe, and "the branch's own validation gate set" has no enumerated gate list for a dependency branch; the implementation review should name the gate set or route it through the unblock child's own final gates.
- Medium: the dependency-landing `landed_path` record identity has no defined fill for a branch whose changes are modify-only against paths already on the default branch (the "absent from the default branch" test fails); the implementation should widen the identity test to a path whose content the branch changes, verified by diff, not by absence.
- Medium: the unblock child's manifest-update duty (the refreshes its progress witness reads) is implied by the execute-plan skill's general manifest discipline rather than prescribed in the template; the implementation should name it in the work order.
- Medium: the two new `turn_error` liveness tokens (`parked-dependency-entry-stale`, `parked-dependency-unblock-stuck`) have no dedicated pins or validation greps; add needles when implementing Task 6.
- Low: the multi-actionable selection order when two entries are actionable in one survey is unspecified; propose oldest-`since`-first.
- Low (overflow, 2): recorded in the r5 staging doc verbatim; disposition at implementation review.

## Gist & Examples
TLDR: give the scheduler loop durable parked-dependency visibility, so every "plan blocked on an unlanded branch" wait is recorded at the boundary, aged and reported by each turn's survey, and cleared by a first-class gated unblock dispatch instead of silently freezing the execution lane (driving force: new-capability serving loop liveness).
Example: on 2026-09-25 the only live execution plan ended at its Task 1 drift gate with the wait recorded in execution notes only; no ledger aged it, no survey arm flagged it, and the loop kept authoring plans while the execution lane stayed frozen until a human asked why. After this plan the run itself writes a ledger entry at the boundary, the next turn's survey classifies the wait as waiting, stale, or actionable using mechanical git probes, and an actionable wait dispatches the unblock child that lands the branch under the merge lock and re-queues the plan through the normal PRE-STEP re-cert.

## Evaluation Criteria
**Quality dimensions:**
- Correctness: every ledger lifecycle transition (boundary write, survey classification, clear on plan exit or branch resolution) is prescribed against the real state-file writer classes and the Step 6 carry-forward list, with no writer outside the sanctioned enumeration.
- Reliability: a run ending at a serialization boundary leaves a durable state-file entry that outlives the recording session; each turn's survey output and decision_reason carry the classification.
- Simplicity: the unblock dispatch reuses the existing execution-child machinery; no new lane, no new automation primitive, no new state machine.
- Maintainability: the pins suite guards the new schema literal, field paragraph, survey arm, D1 integration, boundary writer, and template opener.

**Done when:**
- The State file example JSON, the `parked_dependencies` field paragraph, the sanctioned-writer enumeration, and the Step 6 carry-forward list all name the field.
- The execute-plan skill prescribes the serialization-boundary write, and the maintenance survey prescribes the three liveness states with the mechanical probes and the clear arms.
- D1 skips plans named by live entries and selects the unblock dispatch for actionable entries.
- The unblock template exists in prompt-templates.md carrying the re-cert naming and the dependency-branch landing discipline.
- `bash scripts/check_maintenance_pins.sh` exits 0 with the new needles, and every dedicated validation grep in Validation Commands is GREEN.

**Ship when:**
- The next real serialization-boundary end records its entry and the following turn's survey reports the wait without human action; evidence is the loop's own state file and decision_reason records (operational follow-up, observed in the loop's records, not a checklist item).

## Review Scope
**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill prose and its mechanical pins):**
- `agents/skills/maintenance/SKILL.md` (State file section: example JSON block, new field paragraph, sanctioned-writer enumeration, Step 6 carry-forward list, Revisions entry; Step 1 survey: the parked-dependency liveness arm; Step 3 D1: the parked-dependency skip and unblock selection; Step 5: the unblock child's entry shape)
- `agents/skills/maintenance/prompt-templates.md` (the unblock dispatch template; the execution blueprint's final-merge gate list extension)
- `agents/skills/execute-plan/SKILL.md` (the serialization-boundary ledger-write paragraph after the Orchestration state table)

**Tests:**
- `scripts/check_maintenance_pins.sh` *(the implementation and test surface are the same file: the new needles are both the deliverable and this plan's repository test surface; existing pins and their spans are frozen EXCEPT the exact-count and enumeration literals Task 6 amends by name)*

**Mutator failure-mode matrix:** N/A: no mutating APIs in this plan (skill prose, template prose, and shell pins only).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py` and the driver adapters; reason: the item is scheduler-side visibility; the driver's recovery paths just landed with the reconciliation workstream and no task touches them.
- `agents/skills/maintenance/zcode.md`; reason: the carrier recipe and the dispatch ladder are unchanged; the unblock child rides the existing Step 5 dispatch path.
- `.ai-playbook/scheduler-state.json` (runtime, gitignored); reason: the plan edits schema-defining prose, never the runtime file (Assumption 2).

## Validation Commands

```bash
#!/usr/bin/env bash
# Post-implementation gate: every check must pass against the implemented tree.
# RED-today proof (authoring time, 2026-09-25): each dedicated grep below fails
# against the pre-plan tree because the quoted spans are absent from the target
# files; the pins suite passes today and gains its new needles only in Task 6.
# The greps target the skill files, never this plan, so the plan's own quoted
# spans cannot self-satisfy a gate (self-match immunity by target choice).
set -u
fail=0
S="agents/skills/maintenance/SKILL.md"
P="agents/skills/maintenance/prompt-templates.md"
D="agents/skills/execute-plan/SKILL.md"
PIN="scripts/check_maintenance_pins.sh"
for f in "$S" "$P" "$D" "$PIN"; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done

grep_q() { # grep_q <label> <pattern> <file>: fails closed when the span is absent
  local label="$1" pat="$2" f="$3"
  if grep -qF -- "$pat" "$f"; then return 0; fi
  echo "FAIL: $label"
  fail=1
}

grep_q "schema literal in example JSON" '"parked_dependencies": [],' "$S"
grep_q "field paragraph opener" 'parked_dependencies is the ordered array of parked-dependency ledger entries' "$S"
grep_q "boundary write class" 'the execute-plan serialization-boundary write' "$S"
grep_q "carry-forward naming" 'plus `parked_dependencies` (the boundary-write' "$S"
grep_q "survey arm anchor" 'parked-dependency liveness arm' "$S"
grep_q "survey state vocabulary" 'waiting, stale, or actionable' "$S"
grep_q "D1 live-entry skip" 'live parked_dependencies entry' "$S"
grep_q "boundary writer duty" 'parked-dependency ledger entry' "$D"
grep_q "unblock template opener" 'parked-dependency unblock dispatch' "$P"
grep_q "landing-race discipline" 'actual pre-landing main' "$P"

if bash "$PIN"; then :; else echo "FAIL: pins suite"; fail=1; fi

if [ "$fail" -eq 1 ]; then
  echo "VALIDATION FAILED"
  exit 1
fi
echo "VALIDATION OK"
```

### Task 1: parked_dependencies state field (schema, writers, carry-forward) [H]

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Add the `"parked_dependencies": [],` line to the State file example JSON block, directly after the `"execution_priority": null,` line [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `parked_dependencies` field paragraph directly after the `execution_priority` field paragraph, with opener "parked_dependencies is the ordered array of parked-dependency ledger entries"; the paragraph defines the entry object and each key's semantics (per Terms, including both `blocked_on` ref forms and the optional `deferred_until` and `landed_as` keys), states additive under schema 4 with no version bump, makes writes idempotent per (plan, blocked_on) pair with earliest `since` retention on re-record (the `parent_absent_since` earliest-value precedent), names every writer class the plan prescribes (the execute-plan serialization-boundary write, written by the ending run dispatched or interactive alike; the unblock child's clear-on-landing write; the unblock deferral's entry update setting `deferred_until`, `refusal_count`, and `refused_tip`, joining the clear-on-landing class as its own targeted entry edit; the survey liveness arm's clear and reset writes), names the unblock gate-refusal deferral carrier (the child's own `children[]` entry outcome write, an existing sanctioned class), and defines the two clear arms (the entry's plan absent from the top-level plans survey as parked, completed, or archived; the branch probes showing the wait resolved, meaning zero commits ahead on the resolving ref, or the recorded `landed_as` squash commit now an ancestor of the default branch, or the name unresolvable in both ref namespaces with the plan otherwise dispatchable) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the sanctioned-writer enumeration: the execute-plan serialization-boundary write joins as its own entry (the ending run's write, dispatched or interactive, the P57 `worktree` field writer's explicit-rooted targeted-edit precedent), the unblock child's clear-on-landing write joins the completing-execution-child class in the same targeted-edit family as the successor-dispatch queue-prepend, and the survey arm's clear writes join the scheduler-turn class; the enumeration's count lead-in literal changes from "six sanctioned writer classes" to "seven sanctioned writer classes" (the pins suite pins the literal; Task 6 amends the pin in the same change); extend the Step 6 carry-forward list with "plus `parked_dependencies` (the boundary-write, unblock-clear, and survey-clear writers above, so the rewrite must carry the field)" [class: IMPLEMENTATION_REQUIRED]
- [x] Record the dated Revisions-ledger entry for the field following the P54 entry's shape (date, plan reference, the surfaces gained, additive under schema 4, no version bump) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the dedicated validation greps for this task's spans (schema literal, field paragraph opener, boundary-write class, carry-forward naming) → expect GREEN for Task 1 spans while later tasks' spans stay RED (stage-scoped tree state) [class: REPOSITORY_TEST]

### Task 2: execute-plan serialization-boundary writer [M]

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a paragraph immediately after the Orchestration state table: when a run ends at a plan-task boundary whose gate recorded a wait on an unlanded branch or origin ref (the Task-1 drift-gate shape), the run writes or refreshes the parked-dependency ledger entry for the (plan, blocked_on) pair in one targeted state edit addressed to the primary checkout's `.ai-playbook/scheduler-state.json` (the P57 `worktree` field writer's explicit-rooted precedent): `blocked_on` is the bare ref name the boundary task records as its wait, namespace prefixes stripped; sets `boundary_arm` to the recording task's identifier, keeps the earliest `since` on refresh, records the write in `manifest.md`, and reports it; the write happens only when the primary checkout path resolves AND the state file already exists (the file's existence is the loop's own run-here predicate, so a repo that never ran the loop never gains a schema-partial state file); a run that cannot resolve the primary checkout path or finds no state file records the skip in `manifest.md` and writes nothing [class: IMPLEMENTATION_REQUIRED] [Review tier: M]
- [x] Run the boundary-writer validation grep → expect GREEN [class: REPOSITORY_TEST]

### Task 3: survey liveness arm and D1 integration [H]

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Add the parked-dependency liveness arm bullet to Step 1 (after the plan-coverage bullet): for each `parked_dependencies` entry classify mechanically with the branch probes `git rev-parse --verify refs/heads/<blocked_on>` first and `git rev-parse --verify refs/remotes/<blocked_on>` when the local probe fails (the bare `blocked_on` name is prefixed into each namespace; remote-qualified names like `origin/foo` resolve in the remote namespace), then `git rev-list --count <default-branch>..<resolving-ref>` (ahead count) and `git log -1 --format=%ct <resolving-ref>` (last touch) against the ref that resolved, plus the live-work check (an execute-plan session manifest for the plan under the resolved tmp_dir fresher than one cadence period, or a fresh execution claim for the plan); the actionable conjuncts are evaluated FIRST and win: a ref resolving in either namespace with a positive ahead count and a negative live-work check is actionable regardless of age, and only a non-actionable entry is classified by age as stale (at or past the stale threshold) or waiting (younger), with the entry's `deferred_until` honored throughout (a future `deferred_until` suppresses the actionable proposal and D1's unblock selection until it passes); the clear arms are evaluated BEFORE the classification, so a resolved entry is removed from the array and only a surviving entry is classified; the arm also owns the refusal-cycle reset mechanically: when an entry carries `refused_tip` and the resolving-ref tip differs from it, the arm resets `refusal_count` to 0 in the same targeted-edit pass (the branch has moved since the last refusal, so the refused gate is re-testable); each classification is one of waiting, stale, or actionable and rides the survey output as a `parked-dep:<plan-slug>:<state>` token in decision_reason (the class-token precedent); a stale classification proposes resume-or-close in the survey output, an actionable one proposes the unblock dispatch; the arm performs the field paragraph's clear arms as targeted state edits with the reason recorded in decision_reason, and the unresolvable-ref clear requires the name to be unresolvable in both namespaces with the plan otherwise dispatchable, so an origin-ref wait can never be erased by a local-namespace probe failure; an entry older than six cadence periods with a negative live-work check and no future `deferred_until` records `turn_error: parked-dependency-entry-stale` naming the entry (joining the human clear procedure's escalation list), so a lost clear write degrades to a visible alert instead of a silent livelock [class: IMPLEMENTATION_REQUIRED] [Review tier: H]
- [x] Extend D1: a plan named by a live parked_dependencies entry joins the dependency-blocked skip class with the same self-heal (live means any entry not yet cleared by the field paragraph's clear arms; the arm's resolution clear releases the plan without human action); when the arm marked an entry actionable, the execution lane selects the parked-dependency unblock dispatch for that entry before ordinary D1 selection, still through the guards, the quota leg, the landing gate, and the rate-pressure condition; waiting and stale entries are sanctioned dependency reasons in the must-dispatch exemption list, so no dispatch-defect turn_error fires for a lane held by a live entry [class: IMPLEMENTATION_REQUIRED] [Review tier: H]
- [x] Carry the same live parked_dependencies skip into every living D1 restatement: the execution blueprint's SUCCESSOR DISPATCH paragraph carries its own self-contained D1-rule restatement, so extend its skip list with the live-entry skip (a finishing child's successor selection never chains a plan a live ledger entry blocks), register the paragraph edit in prompt-templates.md's deviation list, and state the queue-prepend dedup rule (the successor duty prepends the next target only when it is not already queued) [class: IMPLEMENTATION_REQUIRED] [Review tier: H]
- [x] Run the survey-arm and D1 validation greps → expect GREEN [class: REPOSITORY_TEST]

### Task 4: unblock dispatch template and wiring [H]

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/SKILL.md`

- [x] Add the parked-dependency unblock dispatch template to prompt-templates.md (execution-blueprint family) with its payload wrapped in a dedicated `<prompt for the parked-dependency unblock session>` block (a distinct wrapper, so the pins suite's exact-count on the execution blueprint's own wrapper stays satisfied). Guard classification is prescribed explicitly: the payload opens with the execution blueprint's payload opening literal VERBATIM (the Step 2 tripwire's negative-shape test and the pins suite's payload-opening confinement both read that literal, so it is never reworded), and the sentence immediately after it scopes the chaining clause to the duties this payload actually carries: the re-arm duty below is carried in recipe-delegating form and the single successor-dispatch duty is the unblock child's own queue-prepend plus re-dispatch; the payload carries the overlay-pinned execution markers, so the Step 2 widened arm classifies it as an execution payload. The template carries the per-execution worktree paragraph (the P57 duty every execution payload carries) and PARAPHRASES the pinned done-lock, label, and gate literals per the deviation-list convention ("pinned and paraphrased here, never quoted") so no frozen exact-count pin over prompt-templates.md moves except the four Task 6 amends by name. Child-duty carriage is prescribed explicitly: the payload carries a re-arm FIRST ACTION duty in the compact recipe-delegating sentence form the authoring payload's RE-ARM DUTY uses (delegating to agents/skills/maintenance/zcode.md's recipe, never a verbatim copy of the execution blueprint's FIRST ACTION paragraph, so the re-arm parity pin's two-paragraph regex count stays 2), a closing park-discharge duty, and the compaction step; it deliberately omits the successor-chaining duty (the unblock child's own queue-prepend plus re-dispatch specified below IS its successor duty, and the scoping sentence says so). Work order: acquire the execution claim per the normal claim duty (the plan slug every slug-keyed surface resolves is the target's leading plan path before " (unblock"); verify the blocked_on ref resolves (fetching when only the remote form resolves); BEFORE any rebase, check `git worktree list` for a worktree holding the blocked_on branch checked out: when one exists, take the gate-refusal deferral path with the peer checkout named (a branch another worktree holds is never moved: `git update-ref` would succeed where `git branch -f` refuses and would corrupt the peer worktree's branch underneath it); otherwise perform the rebase in a temporary worktree detached at the blocked_on tip (detached rebase onto the current default-branch ref, then one compare-and-swap update-ref of the blocked_on ref), never by checking the branch out, a refused ref update taking the gate-refusal deferral path; run the branch's own validation gate set; land the branch under the merge landing lock applying the dependency-branch landing discipline (Task 5); any landing deferral runs through the execution blueprint's deferred-landing record duty with the dependency-landing record identity (bullet below) so a stranded dependency-branch landing stays under the landing gate and the fleet invariant; on a verified landing, record the landing's squash commit sha as the entry's `landed_as` in its own targeted edit FIRST (the sha must be durably observable before any clear, so the survey arm's ancestry resolution can fire when the later clear write is lost), then clear the ledger entry in a second targeted edit, and queue-prepend the serialized plan to `execution_queue` per the successor-dispatch write family (prepend only when not already queued), then dispatch or record per the normal successor duty; the payload states the re-cert obligation the drift gate records by name: a fresh focused review-plan round over the re-baselined touched surfaces with the digest re-bound before implementation resumes; on any gate refusal the child records the deferral as its own `children[]` entry outcome write using outcome `failed` (the existing enum value) with a NEW named `outcome_reason` value "deferred" plus the refused gate named in the same field (the same task extends the schema note and the exclusion lists, bullet below), sets the entry's `deferred_until` to one cadence period out, and stands down, never landing without the gates (origin non-goal) [class: IMPLEMENTATION_REQUIRED] [Review tier: H]
- [x] Bound the refusal cycle: the ledger entry counts consecutive refused unblock attempts (a `refusal_count` the deferral write increments, with `refused_tip` recording the resolving-ref tip sha at the refusal; the survey arm owns the mechanical reset when the tip differs, per Task 3); when the count reaches 3, the survey arm classifies the entry as needing human disposition instead of actionable (no further auto re-selection) and the turn records `turn_error: parked-dependency-unblock-stuck` naming the entry (joining the human clear procedure's escalation list), so a doomed dependency branch cannot re-dispatch a child every cadence forever; the deferral's entry update (deferred_until, refusal_count, refused_tip) is the unblock child's own targeted entry edit, joining the clear-on-landing writer class in Task 1's enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Add the dependency-landing record identity for the deferred-landing duty's dependency-branch case: `landed_path` must be a path the dependency branch itself changes (a path absent from the default branch until the landing lands), the record's `plan` field names the serialized plan path with the unblock target recorded in the note, and the read-back's content-equality arm compares the branch tip's copy of `landed_path`; a record fill whose landed-commit plus content-equality test can pass without the landing is forbidden, so teardown of the recorded branch and worktree stays gated on a verified dependency-branch landing [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the unblock deferral's failure-cap treatment: the children-entry schema note and both failure-cap exclusion enumerations gain the new named `outcome_reason` value "deferred", excluded from failure credit only while the value names the refused gate, so persistent refusals park with the bounded re-selection of the refusal-cycle rule instead of accruing credit [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the dispatch in SKILL.md Step 5: the unblock child is an execution-kind `children[]` entry whose target is `"<plan path> (unblock <blocked_on>)"` so the execution-claim check's plan-slug keying resolves against the leading plan path; extend the Step 5 dispatch slice so an unblock child's scheduled automation prompt is the content of the unblock template's own payload block (the slice's existing sentence keeps naming the execution blueprint for ordinary execution children), with the deciding turn filling `{REPO_ROOT}` and deriving the plan path and blocked_on from the dispatch target exactly as the execution slice's fill sentence derives its fills; extend the Step 1 pending-dispatch reader's execution-target validation to accept the unblock target form (validate the leading plan path against the fresh survey plus the entry's live parked_dependencies liveness, preserving the suffix through retention and re-dispatch); scope the progress-mark checkbox-grep consumer to plan-execution children (an unblock child's progress is its manifest-refresh witness, never a checkbox count against the serialized plan); register the new template in prompt-templates.md's deviation list; and give the child kind its progress witness in the failure-detection section's progress definition: manifest refreshes count as progress for unblock children, and the evidenced-completion pair (ledger entry cleared plus the serialized plan queued) is the terminal witness [class: IMPLEMENTATION_REQUIRED]
- [x] Give the unblock child its failure-cap completion evidence in the lane-hold release rules (the Step 2 State-file arm bullet where the per-kind completion-evidence enumeration lives): an unblock child's completion evidence is its ledger entry cleared plus the serialized plan present in `execution_queue`, with the branch landing verified through the landed-commit test; evidenced completion releases the execution lane immediately instead of holding `G1e` to the six-hour horizon, and the horizon plus failure cap otherwise read the entry like any execution child [class: IMPLEMENTATION_REQUIRED]
- [x] Run the unblock-template validation grep → expect GREEN [class: REPOSITORY_TEST]

### Task 5: dependency-branch landing-race discipline [M]

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [x] Extend the execution blueprint's final-merge gate list (the source of record the landing-completion work references): a dependency-branch landing verifies its squash against the actual pre-landing main, meaning the merge base re-read from the default-branch ref at the commit moment, never the branch lineage; when a parallel landing is detected between lock acquisition and commit (the default-branch ref moved), the landing gate set re-runs against the moved main before the landed-bytes verification: the PII and hygiene gates, the peer-byte guard with its merge base recomputed from the moved default-branch ref, the gmail-author check, the dirt regression gate against the new merge base, and the landed-commit test probing the dependency-landing record identity's `landed_path` (Task 4) [class: IMPLEMENTATION_REQUIRED] [Review tier: M]
- [x] Run the landing-race validation grep → expect GREEN [class: REPOSITORY_TEST]

### Task 6: pins and full validation [M]

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Amend the frozen pins this plan's insertions move, each by name with its measured old and new count (measured by the joint insertion re-simulation of Tasks 1 through 5 on a temp copy, pins suite run against it): the "six sanctioned writer classes" literal becomes "seven sanctioned writer classes" (its superseded-literal absent pin gains "six sanctioned writer classes"); the re-arm sentence-set count at the suite's re-arm line goes 1 to 2 (the template's recipe-delegating re-arm sentences); the FINAL STEP count goes 3 to 4 (the closing park-discharge duty); the `</prompt>` pair count goes 1 to 2 (the new wrapper's closing tag); the discharge-anchor count goes 2 to 3 (the park-discharge carriage); plus a count pin for the new `<prompt for the parked-dependency unblock session>` wrapper (exactly 1) beside the existing wrapper-count pin; verify the re-arm parity pin still passes over the template's final text (the recipe-delegating sentence form matches no FIRST ACTION paragraph, so the byte-identical-paragraph count stays 2) and that the whole-file counts the suite pins stay exact ("assert the session actually owns" exactly 5, "SUCCESSOR DISPATCH" exactly 1, HOST CAVEAT 2 and 1); add pins naming the Step 5 dispatch slice's unblock-template sentence, the seven-class carry-forward span, the amended SUCCESSOR DISPATCH skip clause, the deferred landing-duty's dependency-branch record-identity wording, the progress-witness span, the lane-hold completion-evidence span, and the new "deferred" outcome_reason value in the schema note; the remaining new pins follow the pending_landing pins' shape: the schema literal, the field-paragraph opener span, a SKILL.md occurrence count for `parked_dependencies` of at least 5, the survey-arm anchor span, the survey state vocabulary span, the D1 skip span, the carry-forward span, the execute-plan boundary-writer span, the unblock-template opener span, and the landing-race discipline span [class: REPOSITORY_TEST] [Review tier: M]
- [x] Run `bash scripts/check_maintenance_pins.sh` → expect GREEN exit 0 [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block → expect VALIDATION OK exit 0 [class: REPOSITORY_TEST]

## Execution record (2026-09-25)

Executed in ad-hoc worktree `ai-playbook-exec-parkeddep` off local main c1ca503d, one commit per task group. All six tasks completed as specified; no deviations from task text. Notes for the record:
- Validation-grep needles pinned by the plan required unbackticked literals at two spans (the field-paragraph opener and the D1 live-entry skip); the implemented prose carries the needles verbatim without backticks there.
- Task 6 pin amendments: six→seven sanctioned-writer literal with the six literal frozen absent; re-arm sentence-set count 1→2; FINAL STEP count 3→4; `</prompt>` closer count 1→2 (the unblock wrapper's closer) with the new wrapper opener count-pinned at exactly 1; discharge-anchor count 2→3; plus the new needle pins named in the task (execute-plan boundary-writer pin resolves the execute-plan SKILL.md variable the suite defines later in the file).
- The new deviation bullet was worded to avoid reintroducing the pinned SUCCESSOR DISPATCH literal outside the blueprint body (whole-file exact-count pin stays satisfied).
- Full Validation Commands block: VALIDATION OK exit 0; pins suite exit 0; hygiene scan exit 0.

## Origin disposition

Origin docs/history/backlog/2026-09-25-execution-serialization-stall-visibility.md: implemented in full by this plan (executed 2026-09-25, squash 817acbee); the backlog file is deleted per the plans-skill completion step rather than archived per-item.
