# Plan: P37 context-budget probes and runtime-state contract hardening

Backlog origins (scope of record, under `docs/history/backlog/`):
`2026-09-20-context-budget-checkpoint-policy-residuals.md`,
`2026-09-20-context-budget-telemetry-tmp-dir-substitution.md`,
`2026-09-20-turn-usage-token-probe.md`,
`2026-09-20-waiting-capacity-reclaim-fence-exhausted-window-evidence.md`,
`2026-09-20-merge-lock-guard-wiring-residuals.md`,
`2026-09-20-merge-session-content-fixture.md`.
Review artifacts: `docs/reviews/2026-09-22-plan-review-p37-context-budget-probes-and-runtime-state-r<N>.md` (prefix reference, all rounds).

## Terms

- **Context budget checkpoint**: the safe-boundary measurement duty defined in execute-plan's `### Context budget checkpoints` section (threshold ladder plus one telemetry record per checkpoint).
- **Capped rung**: an above-85% checkpoint whose full-compaction attempt failed or was not resumed on a primitive-less runtime (`compactions_to_date` unchanged across records).
- **Capacity receipt**: a driver receipt whose reason code is `capacity-unavailable`, proving the worker never ran; it parks a single-task claim in `waiting-capacity` under a bounded retry policy.
- **Waiting-capacity / parked claim**: the durable claim state that carries `retry_policy` (`mode: bounded-resume`, `attempts_remaining`); reclaimable only after the budget exhausts into `blocked`.
- **Reclaim**: the driver's expired-lease release operation for `claimed`/`launched`/`blocked` claims.
- **Merge lock**: the landing-serialization lock family in `scripts/done-lock.sh` (`MERGE_LOCK_*` exports; session file `.ai-playbook/merge-lock.session`).
- **Session fence**: the key/value lines in a lock session file that a release or steal must match.
- **Measurement primitive**: the overlay's `## Context measurement primitive` section in `agents/skills/maintenance/zcode.md`, this runtime's measurement half.
- **Skill-gate marker; Session key**: refreshed before every plan-file write per `ai-playbook/agents/hooks/skill-gate/README.md` (Marker WRITE RECIPE); the recipe derives `project` via `facts_paths.resolve_project_key` and `session` per its Terms (emptiness check first, then `sha1(value)[:16]`), and invokes the shared `session_channel.py` subprocess VERBATIM; the CLI is `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker` run from the repository workspace root.

## Assumptions

- assume the family splits 6 + 4 origins across two plans (this plan carries the six context-budget/runtime-state origins); basis: the family note "Split in two if >600 lines" and disjoint file sections per plan.
- assume merge-lock wiring item 2 (the Step 5 final-slot `G3b` arm) already landed: the Step 5 precondition bullet names "the `G3b` final-slot effect" and the 2026-09-20 changelog's r1 address records the wiring at all three effect sites; this plan pins the landed wiring instead of re-adding it. Basis: `agents/skills/maintenance/SKILL.md` Step 5 bullet and changelog line, verified 2026-09-22.
- assume the archive-vocabulary item takes the analysis-home option (record the child lanes' live paths as their analysis home with a retention owner) over extending the Phase 4 archive to sibling lanes; basis: standing pre-authorization for the recommended lower-machinery option, avoiding branch-slug/plan-slug path-key coupling.
- assume the capped-rung decision takes the origin's first option (a capped rung degrades to the 70-85% shedding rung instead of log-only) and the terminal rung bound is three consecutive capped checkpoints, matching the scheduler's G2 failure-cap precedent; basis: standing pre-authorization.
- assume the backlog item's own header-scoping residuals (its items 6 and 7, which widen the item's Exact location lines) are satisfied by this plan's Review Scope naming those same files, so no separate bookkeeping task exists; basis: the item requests triage visibility, which the plan's scope now provides.
- assume pinned freeze literals moved by prescribed edits are reconciled in the same edit (the pins suite's own freeze-note convention).
- Session constraints from the authoring task (worktree placement, no push, single-commit landing) are session-scoped process constraints, not plan content; the plan is branch-agnostic and push-agnostic.

Decision points requiring a grill: none remain.

## Gist & Examples

Six open backlog origins harden the context-budget measurement/policy layer and the runtime-state contracts around it. Nothing here changes dispatch behavior; every change makes an existing guarantee precise, measured, or pinned.

**Cap-semantics (origin 1).**
Before (today): the above-85% rung says a primitive-less run logs the record at later checkpoints when `compactions_to_date` is unchanged. Nothing pins when that counter may increment, the record's `action` vocabulary has no value for a capped rung, and a run can log capped rungs forever without stopping.
After (this plan): the section names the capped rung, degrades it to the 70-85% shedding behavior instead of log-only, carries `action: capped`, pins that `compactions_to_date` increments only when a compaction completes (a manual handoff counts when the run actually resumes from it), and adds the terminal rung: after three consecutive capped above-85% checkpoints the run stops at the next safe boundary with a surfaced budget report. Example: a run whose handoff document was written but never resumed now sheds cheaply each checkpoint and stops at the boundary after three capped records, instead of logging "capped, logged" indefinitely. The same task pins the two navigation headings other files anchor to and shrinks the duplicated archive-rationale prose (origin 1 items 4 and 5).

**Dual-lane coordination and archive vocabulary (origin 1 items 2-3).**
Before: review-loop's round-boundary paragraph restates the checkpoint duty without saying which lane's ladder action wins under execute-plan Phase 3, and the review-loop and authoring child telemetry lanes have no archive step or retention owner.
After: the paragraph states the parent's after-review-round checkpoint is authoritative for ladder actions (review-loop only logs) and pins the first-record baseline for its own counter comparison; the Phase 4 paragraph records the child lanes' live paths as their analysis home with the tmp-directory lifecycle as retention owner.

**tmp-dir substitution (origin 2).**
Before: a project whose facts override `{tmp_dir}` gets split telemetry: execute-plan substitutes the override for its own paths, but the per-skill paths named elsewhere read as literals.
After: the Telemetry bullet states the substitution rule governs every telemetry path this policy names (review-loop's lane file and the Phase 4 archive destination with its Phase 5 checklist wording), and records the boundary explicitly: the maintenance blueprints' payload paths keep their pinned literal-path rationale until that payload text is revisited in its own origin, and the narrowed remainder is captured as a backlog item in Task 3.

**turn-usage probe (origin 3).**
Before: the measurement primitive pins the chars/4 estimate while the session store carries a `turn_usage` table with per-turn token columns; the ratio rationale reads as though runtime-reported token stats do not exist on this host.
After: a live verification round compares `turn_usage` per-session sums against known quota-window totals; the primitive then either reads the verified runtime-reported column first (char-count proxy demoted to the `est_`-labeled fallback) or, if verification shows no column tracks context size, records that measured negative in the rationale instead of the current false implication. Either way the corpus stops implying runtime stats are absent.

**Waiting-capacity reclaim evidence (origin 4).**
Before: the reclaim fence refuses a parked claim with evidence claiming a live bounded retry policy and an in-place resume with attempts remaining, even in the exhausted window (`attempts_remaining: 0`, after the fourth capacity receipt, before the fifth lands the claim in `blocked`), and the contract sentence scopes the refusal to "while the retry policy is live", which that window contradicts.
After: the fence varies the evidence by remaining budget; the exhausted window's refusal names the exhausted budget and the pending `blocked` transition, and the contract sentence describes both windows. Example: an operator reading the refusal at attempts_remaining 0 now learns the truth (no attempts remain; the next capacity receipt makes the claim reclaimable) instead of being told to resume with attempts that do not exist.

**Merge-lock wiring and session fixture (origins 5-6).**
Before: the State-file note enumerates joint-state safety sources without the merge lock (a source `G3b` reads), and every merge selftest fixture asserts only session-file presence, so a mis-parameterized writer emitting `DONE_LOCK_*` keys into the merge session would pass the suite.
After: the note names the merge lock as the fourth source; the already-landed Step 5 `G3b` wiring gains a pin so it cannot silently regress; and a new selftest fixture asserts the merge session file carries exactly the two `MERGE_LOCK_*` keys, mirroring done fixture 15's shape pin.

Edge cases motivating the design: the exhausted window is behaviorally harmless today (continue still works, the fifth receipt lands `blocked`), which is exactly why the misdirecting evidence survived; the fixture guards a shape defect no behavior test can catch because the wrong keys would still "work".

## Evaluation Criteria

**Quality dimensions:**
- correctness: every prescribed sentence, evidence string, and fixture assertion is exercised by a RED-today gate that flips GREEN exactly when its task lands (pins suite, runtime tests, selftest).
- completeness: each of the six origins maps to an owning task; the final validation block covers every changed file.
- maintainability: new policy text lands in the section that already owns the rule; no restated definitions (the archive-rationale shrink removes a duplication instead of adding one).
- observability: telemetry vocabulary changes (`action: capped`) keep the newline-delimited record shape; nothing adds an unpinned unmeasurable duty.

**Done when:**
- all task checkboxes complete; `bash scripts/check_maintenance_pins.sh` exits 0 including the new pins; `python3 -m pytest scripts/test_execute_plan_runtime.py -q` exits 0; `bash scripts/done-lock.sh selftest` exits 0; the base-relative added-lines em-dash scan over this plan's insertions (`check-no-em-dash.sh added-lines --base "$BASE_SHA"`) exits 0; the public-hygiene scan exits 0.

**Ship when:**
- Nothing beyond Done when: every deliverable is repository-verifiable; there is no external release gate in this plan.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Context budget checkpoints section and the Phase 5 checklist item 6 only; all other sections frozen)
- `agents/skills/execute-plan/runtime-contract.md` (capacity-unavailable row/paragraph and the reclaim refusal sentence only; all other sections frozen)
- `agents/skills/review-loop/SKILL.md` (the round-boundary Context budget checkpoint paragraph only; frozen otherwise)
- `agents/skills/maintenance/zcode.md` (Context measurement primitive section only; frozen otherwise)
- `agents/skills/maintenance/SKILL.md` (the State-file advisory note line only; frozen otherwise)
- `scripts/execute_plan_runtime.py` (the reclaim operation's waiting-capacity fence branch and its docstring only; frozen otherwise)
- `scripts/check_maintenance_pins.sh` (new pins and the review-loop variable only)
- `scripts/done-lock.sh` (new merge selftest fixtures only)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (new exhausted-window reclaim test plus the touched contract-parity assertion; frozen otherwise)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.
- `docs/history/backlog/2026-09-22-blueprint-payload-telemetry-paths-keep-literal-prefix.md` *(new; the Task 3 backlog-capture item)*

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md` and `agents/skills/maintenance/prompt-templates.md`; reason: named surfaces of the sibling origins live in the companion plan's scope, and this plan's prose changes do not require touching them.
- `docs/history/backlog/*` lifecycle moves; reason: backlog archival happens at plan completion per the Plan Lifecycle, never inside a task.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && python3 -m pytest scripts/test_execute_plan_runtime.py -q )
( cd "$REPO" && bash scripts/done-lock.sh selftest )
# BASE_SHA must name the commit recorded in Task 1 (before any edit); an unset
# variable aborts instead of diffing against HEAD (which would scan nothing).
BASE_SHA="$(git rev-parse HEAD)" # executor: replace with the recorded pre-Task-1 commit
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE_SHA" )
( cd "$REPO" && bash scripts/scan-public-hygiene.sh )
```

### Task 1: Cap-semantics policy cluster (origin 1 items 1, 4, 5)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Record the base commit for Task 8's added-lines gate in the task notes: `BASE_SHA=$(git rev-parse HEAD)` (captured before any Task 1 edit) [class: REPOSITORY_TEST]
- [x] Add six pins to the `$E`/`$Z` section of `scripts/check_maintenance_pins.sh`: the two heading anchors `pin "context checkpoints section anchored" grep -qF '### Context budget checkpoints' "$E"` and `pin "measurement primitive section anchored" grep -qF '## Context measurement primitive' "$Z"` (these two hold today: characterization), and the four policy pins `pin "capped rung degrades to shedding" grep -qF 'a capped rung degrades to the 70-85% shedding rung' "$E"`, `pin "capped record action vocabulary" grep -qF 'action: capped' "$E"`, `pin "compaction completion timing pinned" grep -qF 'increments only when the compaction completes' "$E"`, `pin "terminal rung after consecutive capped checkpoints" grep -qF 'three consecutive capped above-85% checkpoints' "$E"` [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect RED: exactly the four new policy pins fail (the two heading pins hold) [class: REPOSITORY_TEST]
- [x] In the `Above 85%` bullet of `### Context budget checkpoints`, replace the sentence beginning `A run on a runtime without a compaction primitive attempts the manual handoff once;` (through `...instead of re-attempting full compaction.`) with: `A checkpoint whose full compaction attempt fails, or a run on a runtime without a compaction primitive whose single manual handoff attempt did not resume, is a capped rung: a capped rung degrades to the 70-85% shedding rung (cheap shedding and re-measure at the next checkpoint) instead of logging only, and its telemetry record carries action: capped (corpus vocabulary alongside shed/compact/no-primitive). compactions_to_date increments only when the compaction completes: a manual handoff counts as complete when the run actually resumes from the handoff document's survival list at a later defined step, not when the document is written. After three consecutive capped above-85% checkpoints, the run stops at the next safe boundary with a surfaced budget report instead of logging capped rungs indefinitely.` [class: IMPLEMENTATION_REQUIRED]
- [x] Shrink the Phase 4 archive-rationale duplication: in the **Phase 4 archive ordering** paragraph replace `this copy is what keeps the completed run's telemetry, because the archived telemetry file outlives the run directory it was copied from.` with `this copy is what keeps the completed run's telemetry.`; in the Phase 5 checklist item 6 replace the parenthetical tail `; the removal below deletes the run directory but never this copy)` with `)` keeping the provenance half of the parenthetical [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN: all six new pins hold and no prior pin moved (the shrink edits touch no pinned literal; if a freeze pin trips, reconcile it in the same edit per the suite's freeze-note convention) [class: REPOSITORY_TEST]
- [x] Commit: `feat: pin capped-rung semantics in context budget checkpoints` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Dual-lane coordination and archive vocabulary (origin 1 items 2, 3)

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `R="$repo/agents/skills/review-loop/SKILL.md"` beside the other path variables, include it in the existence-check loop, and add `pin "review-loop ladder precedence" grep -qF 'authoritative for ladder actions' "$R"` and `pin "review-loop first-record baseline" grep -qF 'the first record review-loop appends for a run is the baseline' "$R"`, plus `pin "child lanes analysis home" grep -qF 'as their analysis home' "$E"`; expect RED on all three [class: REPOSITORY_TEST]
- [x] Append to the review-loop round-boundary **Context budget checkpoint** paragraph: `Under execute-plan Phase 3 the parent's after-review-round checkpoint is authoritative for ladder actions: review-loop only logs its per-skill record and takes no ladder action of its own, and the first record review-loop appends for a run is the baseline for its own compactions_to_date comparison.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append to the **Phase 4 archive ordering** paragraph in execute-plan's `### Context budget checkpoints`: `The child telemetry lanes have no Phase 4 archive step: review-loop's docs/tmp/review-loop/<branch-slug>/context.jsonl and the authoring blueprint's docs/tmp/authoring/<plan-slug>/context.jsonl keep their live paths as their analysis home, retained by the tmp directory's own lifecycle rather than copied per run.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: pin review-loop checkpoint precedence and child-lane archive vocabulary` [class: IMPLEMENTATION_REQUIRED]

### Task 3: tmp-dir substitution sentence (origin 2)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-09-22-blueprint-payload-telemetry-paths-keep-literal-prefix.md` *(new; the Task 3 backlog-capture item)*

- [x] Add `pin "telemetry substitution rule scopes this policy's paths" grep -qF 'governs every telemetry path this policy names' "$E"`; expect RED [class: REPOSITORY_TEST]
- [x] Append to the **Telemetry** bullet in `### Context budget checkpoints` (after the existing substitution parenthetical): `This substitution rule governs every telemetry path this policy names: review-loop's docs/tmp/review-loop/<branch-slug>/context.jsonl and the Phase 4 archive destination docs/tmp/context-telemetry/<plan-slug>.log with its Phase 5 checklist wording. The maintenance blueprints' payload paths (docs/tmp/execute-plan/<plan-slug>/context.jsonl, docs/tmp/authoring/<plan-slug>/context.jsonl) keep their pinned literal-path rationale (automation payloads cannot resolve facts keys) until that payload text is revisited in its own origin.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Capture the narrowed remainder as a backlog item under `docs/history/backlog/` (Status/Workflow header lines per receiving-review Backlog capture): the two maintenance blueprint payload paths keep their pinned literal-path rationale, and a future substitution there must edit the payload text and its freeze-note pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: scope tmp_dir substitution to the paths this policy names` [class: IMPLEMENTATION_REQUIRED]

### Task 4: turn-usage live verification and measurement primitive outcome (origin 3)

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "measurement primitive names turn_usage" grep -qF 'turn_usage' "$Z"`; expect RED (the section never names the table today) [class: REPOSITORY_TEST]
- [x] Run the live verification round, read-only, and record the queried columns, per-session sums, and comparison numbers in the task notes under the resolved tmp dir: `sqlite3 -readonly ~/.zcode/cli/db/db.sqlite "PRAGMA table_info(turn_usage);"` then per-session sums of each numeric column for two recent sessions (one known-light, one known-heavy), compared against the known quota-window usage totals those sessions' windows reported; the comparison decides which column, if any, tracks context size [class: REPOSITORY_TEST]
- [x] Selection rule (objective, from the verification output): if exactly one column's per-session sums track the sessions' known context sizes within the observed ratio error, apply Variant A; otherwise apply Variant B [class: IMPLEMENTATION_REQUIRED]
- [x] Variant A: rewrite the Stats surface bullet to read the verified `turn_usage` column first via a pinned tilde-form locator (`~/.zcode/cli/db/db.sqlite`, table `turn_usage`, keyed by `session_id`, read-only), keep the char-count proxy as the `est_`-labeled fallback with its existing locator, and update the Proxy ratio bullet's rationale to name both sources; mirror the same order in the measurement sentence of execute-plan's threshold-ladder paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] Variant B: keep the char-count proxy as primary and replace the Proxy ratio bullet's closing clause (`so the corpus never mistakes proxy counts for runtime-reported token stats.`) with: `the store's turn_usage table (verified 2026-09-22 per task notes) carries per-turn token columns but none tracks context size, so the proxy stays the primary estimate and the est_ labeling remains load-bearing.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN under either variant [class: REPOSITORY_TEST]
- [x] Commit: `feat: verify turn_usage as context-size source and pin the outcome` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Waiting-capacity reclaim evidence in the exhausted window (origin 4)

Files:
- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] `ExecutePlanRuntimeTest#test_reclaim_refusal_names_exhausted_retry_budget`; given a manifest whose task claim was parked by four successive capacity receipts (the park plus three decrements, leaving `retry_policy.attempts_remaining` 0 with the claim still `waiting-capacity`), when the reclaim operation runs on it, expects the resumable `stale-claim` refusal whose evidence names the exhausted budget (`retry budget exhausted`) and the pending transition (`the next capacity receipt transitions the claim to blocked`), contains neither `live bounded retry policy` nor `while attempts remain`, and leaves the manifest unmutated (claim state still `waiting-capacity`) [class: REPOSITORY_TEST]
- [x] `ExecutePlanRuntimeTest#test_reclaim_refusal_keeps_live_budget_evidence`; given a claim parked by a single capacity receipt (`attempts_remaining` 3), when the reclaim operation runs, expects the existing evidence lines unchanged (`live bounded retry policy; reclaim refused` and `resume in place with continue while attempts remain`) [class: REPOSITORY_TEST]
- [x] Run `python3 -m pytest scripts/test_execute_plan_runtime.py -k "exhausted or live_budget or refuses_lease" -q`; expect RED: the new exhausted-window test fails, while the live-budget test and the existing `test_waiting_capacity_claim_refuses_lease_reclaim` pass (spaced `or` operators are required: an unspaced token selects nothing) [class: REPOSITORY_TEST]
- [x] In the reclaim operation's `waiting-capacity` fence branch, read the parked claim's `retry_policy.attempts_remaining`; when it is 0 or less, return the refusal with evidence lines `claim state 'waiting-capacity' is parked with its retry budget exhausted; reclaim refused` and `the next capacity receipt transitions the claim to blocked, whose recovery machinery applies`; when the budget is live, or the claim carries no well-formed `retry_policy` (absent or malformed keeps today's evidence rather than crashing the branch), keep the two existing evidence lines verbatim; update the operation docstring's waiting-capacity clause to name both evidence variants [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/execute-plan/runtime-contract.md`, replace `and reclaim refuses a parked claim with evidence naming `waiting-capacity` while the retry policy is live.` with `and reclaim refuses a parked claim with evidence naming `waiting-capacity` while the retry budget is live; in the exhausted window (attempts_remaining 0, before the next capacity receipt lands the claim in `blocked`) the refusal names the exhausted budget and the pending `blocked` transition instead.`; in the capacity-unavailable row's recovery cell, replace `reclaim refuses the parked state while the budget is live` with `reclaim refuses the parked state while the budget is live, naming the exhausted budget and the pending `blocked` transition in the exhausted window` (backticked state name, matching the contract's markup and the parity assertion) [class: IMPLEMENTATION_REQUIRED]
- [x] In `ContractContentParityTest#test_waiting_capacity_paragraph_carries_retry_resume_and_group_shape`, add `self.assertIn("the refusal names the exhausted budget and the pending `blocked` transition", block)` so the contract paragraph stays pinned, and add `self.assertIn("naming the exhausted budget and the pending `blocked` transition in the exhausted window", self.block_containing("reclaim refuses the parked state while the budget is live"))` so the capacity-unavailable row's new clause carries its own RED-today gate (the phrase is absent from the row today); run the full `python3 -m pytest scripts/test_execute_plan_runtime.py -q`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: vary waiting-capacity reclaim evidence by retry budget` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Merge-lock wiring pin and State-file note (origin 5)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Add `pin "state-file note names the merge lock" grep -qF 'the done-lock, the merge lock, and claim checks' "$S"` and a pin whose pattern is the raw single-quoted literal `the ` + backtick + `G3b` + backtick + ` final-slot effect` (backticks are literal inside single quotes; no backslash escapes) targeting `"$S"`; expect the first RED and the second GREEN today (the wiring already landed; the pin protects it) [class: REPOSITORY_TEST]
- [x] In the State-file advisory note (the line beginning `The state file is advisory for concurrency at large:`), replace `come from the runtime's automation listing, the done-lock, and claim checks` with `come from the runtime's automation listing, the done-lock, the merge lock, and claim checks` [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: name the merge lock in the state-file safety sources` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Merge session-content fixture M10 (origin 6)

Files:
- `scripts/done-lock.sh`

- [x] Add selftest fixture `M10) merge_session_carries_only_merge_lock_keys` after M9, mirroring done fixture 15's shape pin: inside the selftest's existing per-fixture temp repo root, run a fresh `merge-acquire`, then assert the merge session file carries exactly two key lines and both are `MERGE_LOCK_*` (count of lines matching the key-line pattern equals 2, count of `MERGE_LOCK_`-prefixed lines equals 2, and the file contains no `DONE_LOCK_` line); finish with the standard `selftest OK: merge session carries only merge lock keys` line and the fixture's own session cleanup [class: REPOSITORY_TEST]
- [x] Run `bash scripts/done-lock.sh selftest`; expect GREEN: M10 passes against today's `write_lock_session` (this is a characterization fixture guarding shape drift, per the origin: a mis-parameterized writer emitting done keys into the merge session must fail the suite) [class: REPOSITORY_TEST]
- [x] Mutation-proof the fixture once: temporarily emit a `DONE_LOCK_PROBE=1` line into a merge session from a scratch copy of the script (never the repo file) and confirm M10 fails, then discard the scratch copy; record the observed failure line in the task notes [class: REPOSITORY_TEST]
- [x] Commit: `test: merge session shape pin in done-lock selftest` [class: IMPLEMENTATION_REQUIRED]

### Task 8: Full validation

Files:
- none (verification only)

- [x] Run the whole `## Validation Commands` block from the repository root; expect every command GREEN, and record the first actually-failing gate with its exit code if any command fails instead of predicting a pass [class: REPOSITORY_TEST]
- [x] Confirm the plan's own insertions are em-dash-free with `bash scripts/check-no-em-dash.sh added-lines --base "$BASE_SHA"` (the base recorded in Task 1; at Task 8 the working-tree diff against HEAD is empty because every task committed, so the base-relative diff is the only scan that observes this plan's insertions), and `bash scripts/scan-public-hygiene.sh` exits 0 [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-10-runtime-budget-guard-hooks.md: disposition folded into 2026-09-22-p37-context-budget-probes-and-runtime-state.md (2026-09-25); per-item file deleted.
