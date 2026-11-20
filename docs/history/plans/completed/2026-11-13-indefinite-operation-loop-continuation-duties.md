# Plan: indefinite-operation wall-continuation arms and the authoring closeout continue-loop pointer

Backlog origins (scope of record):
- docs/history/backlog/2026-11-13-mid-run-usage-wall-resume-carrier-arm.md
- docs/history/backlog/2026-11-13-continue-loop-rerun-invisible-at-authoring-closeout.md
- docs/history/backlog/2026-11-13-quota-reset-timestamp-timezone-conversion-loop-text.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-indefinite-operation-loop-continuation-duties[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.75h
Executed: yes (65342d435304cd570e5eca7ecc1dc513a07d9903)
Authoring claim: indefinite-operation-loop-continuation-duties.md (session sess_7b19dc51-0e25-403f-a413-65c4fce59330)

## Terms

- Mid-run usage-wall refusal: the harness "[1308] Usage limit reached for 5 hour" class refusal that names a reset timestamp and arrives mid-run at any used percent; distinct from the stop-before-exhaustion arm's at-or-above-95-percent pre-exhaustion park.
- Stop-before-exhaustion arm: the quota leg's hard park arm (agents/skills/maintenance/quota-policy.md, Step 4) that parks the remaining mandate at a primary-binding used_percent at or above 95, with the timed resume at window start; this plan edits beside it and leaves it byte-unchanged.
- Quota leg: the Step 4 quota section of agents/skills/maintenance/quota-policy.md, the arm family (probe economy, stop-before-exhaustion, runtime-fit, pricing) this plan's Task 1 extends.
- Window-start minute: the local wall-clock minute the 5h usage window resets at, taken from the window probe's `reset_at_epoch` when its output is usable, otherwise converted from the provider-displayed reset string read as GMT+8.
- Resume carrier: a one-shot automation armed at the reset-anchored minute (the converted window start plus the standing 10-minute arming margin, never inside the exhausted window) whose fired continuation re-enters the interrupted work from the boundary the wall was recorded at.
- Loop-exit token: the D-18 exit-record class (directive D-18 recorded in docs/maintenance/operator-directives.md: every exit arms its successor or records its exemption); a quota-wall exit records the literal `loop-exit:quota-wall` token with the armed carrier's id and fire time named on the closing report's `loop-liveness:` line; distinct from the quota_signal token (a decision-record slug, never an exit token).
- Mid-run wall arm: the quota leg arm this plan adds beside the stop-before-exhaustion arm, owning the mid-run usage-wall refusal class, composing the landed 5h-wall arm's arming shape.
- 5h-wall arm: the reset-anchored successor inside decisions.md's occupied-lane chaining duty (its one home): a maintenance-lane stop whose evidence records a quota wall no standing carrier resumes arms a one-shot at the probe's `reset_at_epoch` plus the standing 10-minute margin, guarded by the one-listing coverage consult and the never-stack rule.
- Coverage consult: the one-automation-listing check run before an arming create (decisions.md, occupied-lane chaining duty): it matches an ENABLED repository-contained one-shot whose prompt carries the resolved repository root and the lane's marker (or the scheduler prompt opening) with a fire time inside the coverage window; found coverage records the existing carrier and skips the arm.
- Lane marker: the child-classification marker span a lane's carrier prompt carries (the runtime overlay's Child classification markers section, cited by reference), the token the coverage consult matches on.
- GMT+8 note: the operator-level instruction that provider-displayed quota reset timestamps are Singapore time (GMT+8), re-checked 2026-07-25, living in user-level instructions rather than repository text; the conversion sentence cites the note and its re-check clause by reference, never the date literal.
- Budget-gate pause boundary: the authoring run's Budget gate section in `agents/skills/plans/budget-gate.md` ("Budget gate (plan-authoring pause and resume)"), which owns the pause protocol, the `budget_pause` record sink (pause protocol step 4), and the Boundaries paragraph routing a wall that kills the run off-boundary to the 5h-wall arm; the execute-plan Budget gate section remains the canonical home of the shared pause protocol (deltas owned by the plans file, per its canonical-home note).
- Pause surface: the record surface a boundary owns; `budget_pause` where the boundary owns a Budget-gate sink, the turn output otherwise (the stop-before-exhaustion arm's existing scoping vocabulary, reused unchanged).
- AUTHORING CLAIM duty: the claim procedure in `agents/skills/maintenance/template-authoring.md`; its placement-owned deletion boundaries at closeout are the authoring closeout boundary this plan wires, and its foreign-claim gate (the fresh-foreign-claim refusal within the 2-hour cadence freshness window) is the gate the fired continuation's claim adoption addresses.
- Claim adoption: the arm this plan adds to the AUTHORING CLAIM duty: a fired authoring continuation whose matched claim file names the walling session refreshes or re-writes that claim as its own (its session id, fresh updated:) before the foreign-claim gate reads it, recorded in its own claim surfaces; the adoption mutation is sanctioned outside the ownership re-check's own-claim scope, the adoption re-reads the claim file immediately before the mutation and adopts only while its `session:` line still names the walling session id carried in the carrier prompt (anything else leaves the file untouched and takes the ordinary foreign-claim gate path), and the re-write variant amends the duty's one-sanctioned-foreign-delete sentence to two situations (the stale-foreign-claim takeover and the claim adoption).
- Continue-loop re-run (D-17): the in-session authoring primitive's mandate (agents/skills/maintenance/zcode-scheduling-primitives.md, the in-session authoring primitive paragraph; directive D-17 recorded in docs/maintenance/operator-directives.md; decisions.md housing the continue-loop condition that applies it, D-6's quota clauses active): after an in-session authoring run lands, the turn re-runs the execution-lane decision on the freshly landed plan, never ending at the authoring boundary while dispatchable work remains and the primary 5h limit is not low.
- quota_signal token: the literal `quota_signal=` followed by one slug from the quota leg's slug vocabulary; the re-run's decision records it inside `decision_reason.execution` per the execution-lane ordered rule's existing shape.
- EXEC-PROMPTS entries: the execution-side rolling log (docs/history/backlog/EXEC-PROMPTS.md), the queued execution items whose presence makes the continue-loop condition's "dispatchable work remains" test true.
- Dispatch primitive: an existing carrier-arming shape of the dispatch ladder (the clocked one-shot, the idle-time primitive, or the launchd resume carrier); the mid-run wall arm composes them and adds none.
- Revisions ledger: `agents/skills/maintenance/CHANGELOG.md`, the one-line-per-change record whose entries name the plan, the task, and the origin row(s).
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check`, blocking posture; its advisory ratchet breach lines are growth-watch signals, never review-time blocking inputs.
- Pins suite: `bash scripts/check_maintenance_pins.sh`, which pins literals in the guarded maintenance modules this plan edits.
- One-line pointer: an insertion that names its owning rule by reference (module path plus rule label), carries no operational restatement of that rule, and reads as one sentence.
- Frozen entry: the PLAN-PROMPTS.md entry `indefinite-operation-loop-continuation-duties` whose `Frozen:` line names this plan's claim file; the entry cited in Assumptions as the scope-of-record witness.

## Why

Three witnessed stop gaps from the 2026-11-12/13 authoring arc leave the indefinite-operation loop dark or skipped at exactly the boundaries where allowance was abundant: a mid-run 5h usage-limit refusal ended the turn with no armed carrier and the lane slept 6.5 hours despite a reset 49 minutes later; the session then landed a certified plan and ended at the authoring closeout boundary with 12 EXEC-PROMPTS entries queued and hours of allowance, skipping the continue-loop re-run the scheduling module already mandates; and both walls' reset timestamps were converted manually from an operator-level GMT+8 note that no loop text carries, so any carrier without that user-memory note arms its resume hours off.

## Gist & Examples

TLDR: the quota leg gains the mid-run wall arm with its own timezone-anchored conversion sentence (composing the landed 5h-wall arm's arming shape so one wall has one arming answer), the authoring closeout boundary and the authoring Budget-gate pause boundary gain one-line pointers to the rules they must consume, and the Revisions ledger records each change, so every wall arms its own resume and every authoring landing re-runs the execution-lane decision.

Before: at a mid-run refusal the turn ends with no carrier (lane dark until the operator types resume); at the authoring closeout the session deletes its claim and ends without the D-17 re-run (the execution queue full); the reset conversion depends on user memory.

After: the same refusal converts its displayed reset to the local window-start minute (never a past instant), runs the coverage consult, arms a one-shot resume carrier through an existing dispatch primitive with the lane marker and the walling session id its prompt carries, records the wall on the boundary's pause surface and the quota-wall loop-exit token, and ends the turn; the fired continuation adopts the walling session's claim and re-enters the interrupted work. The same closeout re-runs the execution-lane decision on the freshly landed plan (quota_signal token in decision_reason.execution) before its deletes fire, then starts the continuation; a mid-run wall at the authoring Budget-gate pause boundary arms its carrier per the same quota leg arm.

## Outcome

- A mid-run usage-wall refusal at any percent produces an armed resume carrier at the reset-anchored minute, recorded on the boundary's own pause surface, without operator presence, reconciled with the landed 5h-wall arm and the Quota-wall dispatch doctrine so no wall arms twice and no restart-fidelity evidence is skipped.
- The authoring closeout boundary re-runs the execution-lane decision under the continue-loop condition before its placement-owned deletes fire, then starts the continuation; a fired authoring continuation adopts the walling session's claim instead of being refused by the fresh-foreign-claim gate.
- The authoring Budget-gate pause boundary's wall route points at the same quota leg arm, so the authoring run's own wall class is covered at the boundary the pausing session actually executes.
- The quota leg's text carries its own reset-to-local conversion recipe, ending the user-scoped dependency between a wall and its resume carrier.
- No new gate, validator, primitive, or schema field: every arming and recording shape cited by reference to its existing owner; the one new pins-suite row pins a span this plan promises byte-unchanged.

Gate delta: duty-text arms and by-reference pointers only; removals: none. Machinery delta: one pins-suite presence row (the existing instrument, pinning the stop-before-exhaustion arm span Task 1 promises byte-unchanged), no validator, no gate, no schema field.

## Assumptions

- The dispatch primitives the mid-run wall arm composes already exist and the second 2026-11-13 wall armed such a carrier ad hoc through the clocked one-shot; basis: the wall origin row's reproduction evidence (automation-8f1664a2, deleted on operator resume).
- The 2026-11-12/13 arc is the single incident set for each row and no validator or machinery is warranted; basis: the frozen entry's Verdict line (guard-bearing scheduling text, arms reusing existing primitives) and the repository guidelines' Machinery admission protocol.
- The GMT+8 note stays user-level; the conversion sentence cites rather than copies it so the re-check clause lives in one place; basis: the timezone origin row's expected section.
- The landed arming routes (the 5h-wall arm in decisions.md, the budget-gate.md off-boundary route, the execute-plan Quota-wall dispatch doctrine) predate the origin rows and stay operative; this plan reconciles with them rather than re-pricing them; basis: decisions.md's occupied-lane chaining duty and plans/budget-gate.md's Boundaries paragraph, verified at authoring.
- The timezone origin row's Expected wording ("with the note's own re-check date cited") is deliberately narrowed by this plan to citing the re-check clause by reference, never the date literal: the date literal stays user-level so repo text cannot go stale at the note's next re-check; the delta from the row's letter is recorded here as the plan's reading, affects Task 1.

Decision points requiring a grill: arm placement (a new arm beside the stop-before-exhaustion arm rather than widening the stop arm's threshold) chosen because the classes differ in trigger, posture, and discharge, basis the origin rows' observed sections, affects Task 1; reconciliation shape (compose the 5h-wall arm's coverage consult and lane-marker shape rather than defining a parallel consult) chosen because one wall must have one arming answer and the consult's marker matching already recognizes lane carriers, basis the risk round-1 finding, affects Task 1; fire-minute contract (the reset-anchored minute, the converted window start plus the standing 10-minute arming margin, rather than the bare window-start minute) chosen because D-18's arming order and the 5h-wall arm fix that minute and the margin absorbs reset-reading skew, basis the risk round-2 finding, affects Task 1; re-entry shape (claim adoption in the AUTHORING CLAIM duty rather than bypassing the foreign-claim gate) chosen because the gate's two-hour freshness refusal is the witnessed common path and adoption preserves the witness chain without opening the gate to foreign claims generally, basis the risk round-1 finding, affects Tasks 1 and 2; pointer depth (one-line by-reference pointers rather than restated duties) chosen because the rules' homes are correct and complete and restatement would create a second wording home, basis the repository guidelines' merge rule, affects Task 2.

## Standing constraints

- Skill-text anti-growth rules (repository guidelines): each amendment lands in its named home; the incident story stays in the origin rows; operative text cites an incident in at most one line.
- The pins suite (`scripts/check_maintenance_pins.sh`) pins literals in the guarded maintenance modules this plan edits; run it after each task's edit and after the last task; Task 1 registers one new pin (the stop-arm span) in the same change.
- The byte-budget gate (`python3 scripts/skill_text_budget.py --check`) runs at authoring time over the touched operative files; the ceiling class blocks.
- No new top-level section in any edited module: each insertion extends the section the origin row names.
- Pay for growth (repository guidelines' skill-text anti-growth rules): template-authoring.md already sits on an advisory ratchet breach line (51,559 bytes against its 42,066 advisory cap, 9,493 over), so Task 2's template-authoring insertions pair with an equivalent same-module compression recorded in the task evidence; agents/skills/plans/budget-gate.md sits under its cap (19,412 bytes against its 26,390 cap, 6,978 under), so its pointer growth needs no paired compression; where no faithful compression exists, the residual ratchet delta is accepted and the gate's advisory breach line is the record. quota-policy.md sits under its cap; Task 1's growth is still priced tight (one arm, one sentence).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the mid-run wall arm covers the refusal class at any percent, converts through probe-or-GMT+8 in that order with the past-instant guard, composes the coverage consult and the lane-marker shape, names the pause surface, the exit-token interface, and the re-entry boundary including the claim adoption; the closeout pointer fires before the placement-owned deletes and pins the continuation's position after them; the Budget-gate pointer reaches the same arm at the boundary the pausing session executes; all verified by reading the amended text against the witnessed scenario.
- compatibility: pins suite, public hygiene scan, and the byte-budget gate's blocking posture all exit 0.
- maintainability: one-line pointers by reference; no second wording home for D-17, the wall arm, or the conversion recipe; no new top-level section.

**Done when:**
- pins, hygiene, and the byte-budget gate exit 0 over the changed files.
- the full readiness gate passes on the certified plan bytes.

**Ship when:** the next mid-run usage-wall refusal on the live loop arms a resume carrier at the converted window-start minute, recognized by the coverage consult, and the next authoring landing's session re-runs the execution-lane decision before ending (human-owned observation on the live loop).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/quota-policy.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 2)
- `agents/skills/plans/budget-gate.md` (Task 2)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3)
- `docs/history/backlog/2026-11-13-mid-run-usage-wall-resume-carrier-arm.md` (Task 2)
- `scripts/check_maintenance_pins.sh` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above when causally related to a task (for example a sibling reference that names the wall arm's wording). Otherwise out of scope.

**Out of scope; reject unless plan-related:**
- new dispatch primitives, validators, gates, or state-file schema fields; reason: the arms compose existing shapes and the machinery admission protocol prices single-incident duty text below machinery.
- changes to the stop-before-exhaustion arm's own thresholds or scoping; reason: the row's scope is the uncovered mid-run class, not a re-price of the pre-exhaustion park.
- changes to the 5h-wall arm's own trigger, fire-minute, or consult shape in decisions.md; reason: reconciliation reads that arm by reference, it is not this plan's edit surface.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-13-indefinite-operation-loop-continuation-duties.md
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
rg -c "mid-run wall arm" agents/skills/maintenance/quota-policy.md
rg -c "continue-loop" agents/skills/maintenance/template-authoring.md
rg -c "mid-run wall arm" agents/skills/plans/budget-gate.md
rg -c "claim-adoption" agents/skills/maintenance/template-authoring.md
```

Authoring preflight record (rule 29, 2026-11-13, placement root = the authoring worktree):
- pre-round structural gate: OUTCOME pass (advisory warnings recorded at authoring, if any).
- no-em-dash: `touched` and `added-lines` scans OUTCOME pass at authoring.
- public hygiene scan: OUTCOME pass; maintenance pins suite: OUTCOME pass; byte-budget gate: OUTCOME pass (0 blocking breaches; advisory ratchet breach lines pre-existing, template-authoring.md 51,559 bytes against its 42,066 advisory cap, 9,493 over, among them; agents/skills/plans/budget-gate.md 19,412 bytes against its 26,390 cap, 6,978 under).
- rule 22 mechanical audit: bash -n over this block OK; no literal pinned-span contracts in this plan.
- execution-time commands (pytest suites): not applicable to this plan's skill-text scope; the pins and byte-budget gates are the executable battery.

Round-start state for r1: branch authoring/indefinite-operation-loop-continuation-duties; base main.

### Task 1: the mid-run wall arm and the GMT+8 conversion sentence in the quota leg

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/quota-policy.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `stop-before-exhaustion arm` in `agents/skills/maintenance/quota-policy.md`

- [x] `quota leg` delivers `mid-run wall arm`: given a mid-run 5h usage-limit refusal naming a reset timestamp at any used percent, expects the amended quota leg text beside the stop-before-exhaustion arm to arm a one-shot resume carrier at the reset-anchored minute (the converted window start plus the standing 10-minute arming margin, never inside the exhausted window) through an existing dispatch primitive, record the wall in the boundary's own pause surface, and end the turn [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `probe-first conversion`: given the reset value source, expects the arm to convert the displayed reset into the local window-start minute, taking the window probe's `reset_at_epoch` when its output is usable and otherwise the displayed string as GMT+8 per the standing operator note cited by reference with its re-check clause (never the date literal) [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `past-instant guard`: given a converted window-start minute, expects the arm text to never arm a past instant (the runtime's silent year-roll): a past conversion checks the lane live and otherwise leaves the resume to the first fresh-probe boundary after the reset [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `5h-wall reconciliation`: given the landed arming routes, expects the arm text to name the 5h-wall arm (decisions.md's reset-anchored successor) and the budget-gate off-boundary route by reference and state the precedence (the walling boundary's immediate arm here; the 5h-wall arm owns the later-turn evidence-driven arm) so one wall arms once [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `doctrine reconciliation`: given the Quota-wall dispatch doctrine (directive D-13, launch-rules-and-gates.md), expects the arm text to name that doctrine by reference and state the split: the doctrine owns the in-flight execution child's pre_restart pair and manifest lines, the quota-leg arm owns the boundary arming, no restart-fidelity evidence is skipped [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `coverage consult composition`: given the arming create, expects the arm text to run the coverage consult before the create, never stack a second retry, and carry the lane marker and the walling session's id in the carrier's prompt [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `re-entry shape`: given the fired resume carrier, expects the arm text to have the continuation re-enter the interrupted work from the boundary the wall was recorded at, the authoring-boundary continuation adopting the walling session's claim per the AUTHORING CLAIM duty's claim-adoption arm, and the carrier's minute riding the stop-before-exhaustion arm's spacing exemption by reference [class: IMPLEMENTATION_REQUIRED]
- [x] `mid-run wall arm` keeps `D-18 interface`: given a wall recorded at a loop-owned boundary, expects the arm text to record the quota-wall loop-exit token class (directive D-18 recorded in docs/maintenance/operator-directives.md) with the armed carrier named on the loop-liveness line, the carrier satisfying the D-18 arming order at the reset-anchored minute instead of duplicating it [class: IMPLEMENTATION_REQUIRED]
- [x] `quota leg` keeps `stop arm unchanged`: given the existing stop-before-exhaustion arm, expects its thresholds, scoping, and discharge to read byte-unchanged after the edit [class: REPOSITORY_TEST]
- [x] `pins suite` delivers `stop-arm pin`: given the byte-unchanged promise, expects one new pins-suite presence row pinning a distinctive stop-before-exhaustion arm span (for example the never-discharges sentence) registered in the same change [class: IMPLEMENTATION_REQUIRED]
- [x] Pins + hygiene + byte-budget gate exit 0 after the edit; the task evidence records a git-diff inspection of quota-policy.md confirming the stop arm byte-unchanged before the commit [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: add the quota leg's mid-run wall arm with its GMT+8 conversion sentence` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the closeout continue-loop pointer, the claim-adoption arm, and the Budget-gate wall pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/plans/budget-gate.md`
- `docs/history/backlog/2026-11-13-mid-run-usage-wall-resume-carrier-arm.md`

Primary class anchors:
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`
- `Budget gate (plan-authoring pause and resume)` in `agents/skills/plans/budget-gate.md`

- [x] `AUTHORING CLAIM duty` delivers `closeout continue-loop pointer`: given the placement-owned deletion boundaries at closeout, expects the duty text to carry a one-line pointer that has the closing session re-run the execution-lane decision on the freshly landed plan under the continue-loop condition (D-17 by reference to the in-session authoring primitive, the condition named verbatim) [class: IMPLEMENTATION_REQUIRED]
- [x] `closeout continue-loop pointer` keeps `ordering pin`: given the closeout sequence, expects the pointer to pin the order: the re-run's decision recorded, then the placement-owned deletes fire, then the continuation starts [class: IMPLEMENTATION_REQUIRED]
- [x] `closeout continue-loop pointer` keeps `directive citation`: given the pointer's D-17 label, expects it to cite the directive's recorded home (docs/maintenance/operator-directives.md) with D-6's quota clauses active and never cite decisions.md as the D-17 record home [class: IMPLEMENTATION_REQUIRED]
- [x] `closeout continue-loop pointer` keeps `signal surface`: given the re-run's decision record, expects the pointer to name the quota_signal token recorded inside `decision_reason.execution` per the execution-lane ordered rule's existing shape [class: IMPLEMENTATION_REQUIRED]
- [x] `AUTHORING CLAIM duty` delivers `claim-adoption arm`: given a fired authoring continuation whose matched claim file names the walling session, expects the duty text to let that continuation adopt the walling session's claim (refresh or re-write it as its own before the foreign-claim gate reads it) so the mid-run wall arm's re-entry is not refused on the fresh-claim path, the adoption sanctioned outside the ownership re-check's own-claim scope [class: IMPLEMENTATION_REQUIRED]
- [x] `claim-adoption arm` keeps `serialization discipline`: given the adoption's mutation, expects it to re-read the claim file immediately before the mutation and adopt only while its `session:` line still names the walling session id carried in the carrier prompt, anything else leaving the file untouched and taking the ordinary foreign-claim gate path, and the re-write variant amending the one-sanctioned-foreign-delete sentence to two situations [class: IMPLEMENTATION_REQUIRED]
- [x] `Budget-gate pause boundary` delivers `wall-class pointer`: given a mid-run usage-wall refusal at the authoring Budget gate boundary in `agents/skills/plans/budget-gate.md`, expects that section's wall text (the Boundaries paragraph's off-boundary wall route) to carry a one-line pointer to the quota leg's mid-run wall arm (conversion, coverage consult, carrier arming, and pause-surface recording per that arm by reference) [class: IMPLEMENTATION_REQUIRED]
- [x] the two pointers keep `pointer depth`: given both insertions, expects each to name its owning rule by reference in one sentence without restating the rule's operational steps [class: IMPLEMENTATION_REQUIRED]
- [x] the edited modules keep `growth payment`: given the touched modules' advisory ratchet state (template-authoring.md over its 42,066 advisory cap), expects Task 2's template-authoring insertions paired with an equivalent same-module compression recorded in the task evidence (pre-edit and post-edit byte counts, the candidate compression spans considered, pinned-span avoidance noted), the residual delta accepted only where no faithful compression exists [class: IMPLEMENTATION_REQUIRED]
- [x] Pins + hygiene + byte-budget gate exit 0 after the edit [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: wire the authoring closeout continue-loop re-run, the claim-adoption arm, and the Budget-gate wall pointer` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the Revisions ledger lines

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `Revisions` in `agents/skills/maintenance/CHANGELOG.md`

- [x] `Revisions ledger` delivers `one line per task`: given Tasks 1 and 2's changes, expects one dated Revisions entry per task in the ledger's existing entry shape, Task 1's entry naming both the wall-arm origin row and the timezone origin row, Task 2's entry naming both the closeout origin row and the wall origin row [class: IMPLEMENTATION_REQUIRED]
- [x] `Revisions ledger` keeps `no story growth`: given the ledger's one-line-per-change convention, expects each entry to carry the change and its origin citations only, the incident narrative staying in the origin rows [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: record the wall-continuation arms in the Revisions ledger` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- `agents/skills/maintenance/quota-policy.md` (Task 1): the Step 4 quota leg's arm family gains the mid-run wall arm and the conversion sentence; the stop-before-exhaustion arm is unchanged (newly pinned).
- `scripts/check_maintenance_pins.sh` (Task 1): one new presence row pinning the stop-before-exhaustion arm span.
- `agents/skills/maintenance/template-authoring.md` (Task 2): the AUTHORING CLAIM duty's placement-owned deletion boundaries gain the closeout continue-loop pointer and the claim-adoption arm; no new section.
- `agents/skills/plans/budget-gate.md` (Task 2): the Budget gate section's off-boundary wall route gains the one-line pointer to the mid-run wall arm; no new section.
- `agents/skills/maintenance/CHANGELOG.md` (Task 3): two Revisions entries, one per operative task, each naming both of its origin rows.
- The origin row docs/history/backlog/2026-11-13-mid-run-usage-wall-resume-carrier-arm.md carries the authoring wall-pointer's mis-home in its Skill/step line (template-authoring.md where the real boundary is agents/skills/plans/budget-gate.md); the execution corrects that line's home in the row before its completion disposition, with the correction recorded in Task 2's evidence.
- README and catalogs: unchanged (no skill names, paths, or usage change).
