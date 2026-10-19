# Plan: discharged-without-successor verification for launchd clocked orders

Backlog origin: docs/history/backlog/2026-10-18-clocked-order-discharged-order-silent-strand.md
Driving force: reliability; off-taxonomy justification: the property this plan protects is continuity of the maintenance loop across a carrier fire whose payload session never records itself, a reliability property outside the five driving principles; park-triage would not take it because the class is witnessed twice in eight days and the 2026-10-18 recovery happened only because an unrelated live session ran a liveness check at its own closeout.
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-clocked-order-successor-verification-p4ed490a0-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

## Terms

- discharged order: a clocked order whose ledger state is `discharged`, meaning the launchd job fired and the discharge-on-fire operation consumed it exactly once.
- successor state record: a `children[]` entry in `.ai-playbook/scheduler-state.json` attributable to the discharged order (its `automation_id`, `cycle`, `target`, or note text names the order id or the order's carrier label, any outcome included), evidence that the fired turn actually ran and recorded itself regardless of when the entry was written.
- successor pointers: the state file's `next_turn_at` and `parent_automation_id`, the two fields whose re-pointing off the discharged order evidences a live successor.
- verification window: the half-open span from the order's `requested_epoch` to `requested_epoch` plus the grace window.
- grace window: 30 minutes; the delay past the order's requested minute before the consult starts flagging a discharged order with no attributable successor record (a record landing later still clears; derivation in Assumptions).
- clocked-order consult: the maintenance survey's consult over the order ledger (the missed leg, then the pickup arm, then this plan's verify-successor leg).
- verify-successor operation: the new read-only `clocked-order-verify-successor` CLI operation this plan adds; it never mutates the ledger.
- warning-shaped: a finding the consult reports in the survey output that blocks no lane, writes no ledger or state bytes, and routes its response through the overlay's existing re-arm vocabulary.
- stall: the overlay's classification of a flagged discharged order: a turn evidence failure, never healthy idle.
- overlay: the ZCode runtime overlay `agents/skills/maintenance/zcode.md` (Recurring automation recipe, Re-arm hygiene, turn-start carrier re-arm duty).
- missed-order detector: the existing `clocked-order-due` operation; it classifies only `pending` and `armed` orders, so a discharged order is invisible to it.
- launchd chain: the scheduler adapter chain behind `clocked-order-schedule`; its launchd form arms a calendar job whose fire command is the discharge operation invocation.
- touching session: a session whose rearm-on-touch or turn-start duty fires on state-file or repository contact (agents/skills/maintenance/zcode.md, Re-arm hygiene).
- carrier: the armed automation or launchd job that fires one loop turn.
- PLAN-PROMPTS entry: a ready-to-dispatch entry in the tracked rolling prompt log docs/history/backlog/PLAN-PROMPTS.md.
- checked-set growth: any addition to the set of consult or gate checks the maintenance loop runs.
- pins suite: scripts/check_maintenance_pins.sh, the pinned-span assertion suite over the maintenance skill files.
- span needle: one additive pin() span assertion registered in the pins suite for a file this plan edits, asserting the added text's distinctive span.

## Why

A launchd clocked order that fires and discharges leaves the ledger healthy even when its payload session never launches: the missed-order detector reads only `pending` and `armed` orders, so the lost turn is invisible. The class is witnessed twice (2026-10-10 and 2026-10-18); the second recovery armed the next carrier only because an unrelated session's closeout ran a liveness check. Disk evidence re-derived 2026-10-18 sharpens the mechanism: the deployed fire command is the discharge operation alone (no session-launch leg), so an unattended order discharge produces no session to record itself, and the detection arm must live outside the discharge path.

## Gist & Examples

TLDR: A warning-shaped discharged-without-successor check joins the clocked-order consult and the overlay's re-arm vocabulary, because a fired order whose turn never records itself currently strands the loop silently until an unrelated session runs a liveness check (driving force: reliability).

Before: order co-b3f5bb778d3448369e6ec145322d4577 discharges at 12:04:03 with a one-line job log; the ledger reads `discharged`, no children[] entry ever appears, `next_turn_at` keeps naming 12:04, and nothing machine-readable flags the lost turn until the 11:00 session's closeout happens to arm the repair order.

After: the next survey turn's consult runs the read-only verify-successor leg, which flags exactly that shape (discharged, no attributable successor record, `next_turn_at` still naming the order past the grace window); the survey output carries the warning, the overlay classifies it as a stall, and the touching session re-arms per the existing recipe instead of the loop waiting on a coincidence.

## Outcome

The loop's continuation no longer depends on an unrelated session noticing a lost carrier fire: the next touching session's consult flags the discharged-without-successor shape and its re-arm duty repairs the carrier.

- A discharged order whose turn produced no state record and whose successor pointer still names it is reported by the consult, warning-shaped, every survey turn until a successor exists.
- The overlay's re-arm hygiene treats that report as a stall, so a touching session re-arms per the recipe instead of reading the loop as healthy idle.
- The discharge path, the ledger schema, and the launchd promotion review's decision surface are untouched.

Gate delta: adds one warning-shaped consult arm (checked-set growth: the verify-successor leg joins the survey's clocked-order consult) and one prose duty sentence in the overlay's re-arm hygiene (prose-only requirement); registers one companion pins-suite span needle per edited skill file and one pre-registered machinery-registry admission-entry-plus-removals-row pair (bookkeeping rows, priced with the arm); no new refusal class, hard gate, fence, protocol layer, or state-schema field; removes nothing. The checked-set growth is priced by the machinery admission below and the two witnessed silent-strand incidents (2026-10-10 row and 2026-10-18 row), which are the completed-integrity-failure witness for this detection class.

Machinery admission (warning-only surface; the repository guidelines' Machinery admission protocol section): incident: the silent-strand class, docs/history/backlog/2026-10-18-clocked-order-discharged-order-silent-strand.md with its covered first witness docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md; expected catch: every launchd-carried turn whose session does not record itself, which the disk evidence says is every solo order discharge until a launch leg exists; false-positive cost: bounded by the successor-clearing predicate, an order stops flagging as soon as both successor pointers move off it or an attributable entry records itself, and the flag never blocks a lane; residual masking cost: a recovery that re-points the successor pointers without recording an attributable entry suppresses that order's flag, and the re-point is itself the repair; sunset and review: the arm lands warning-only and its promotion rides the launchd promotion review named by docs/history/plans/completed/2026-10-17-rearm-dispatch-ladder-incident-guards.md, in any case by 2027-01-18, with the pre-registered registry removals row's criteria applied at that review.

## Assumptions

- assume the scope is the dispatch entry's three scope arms (the consult arm warning-shaped, the overlay stall vocabulary, the chain-side auto-arming complement stays rejected-for-now); basis: the frozen PLAN-PROMPTS entry `clocked-order-successor-verification` is the prompt source of record and carries the operator's standing pre-authorization for unattended authoring.
- assume the launch-leg absence finding is orientation evidence, not new scope; basis: `build_clocked_order_fire_command` builds exports plus the discharge invocation only, the CLI wrapper passes through to `run_clocked_order_operation` with no launch leg, and all twelve order job out-logs on disk hold exactly the one discharge JSON line (re-derived 2026-10-18); adding a launch leg is the promotion review's decision surface and stays out of this plan.
- assume the grace window constant is 30 minutes; basis: derivation from recorded data, not a guess: the ledger's own discharge latencies over its twelve discharged orders run 2.4 to 7.7 seconds (launchd jitter tail), and the observed session-record latencies in the scheduler state file for the 2026-10-16 and 2026-10-18 one-shot fires run 5 to 10 minutes from fire to the session's first `children[]` write; 30 minutes is three times the observed tail with the whole bound far inside the two-hour cadence period the claim freshness uses, and the constant is revisited at the promotion review.
- assume a flagged order self-clears once recovery happens; basis: the predicate requires `next_turn_at` (or `parent_automation_id`) to still name the discharged order, and the witnessed recovery re-pointed both, so no flagged order can pile up across turns.

- assume two deviations from the dispatch entry's scope-arm letter are intentional and recorded here: (a) the entry's bare in-window children[] probe is replaced by the attribution-safe successor test (the pointer pair moving off the order, or an entry attributable to the order), because an un-attributed in-window entry from any unrelated session would permanently mask the exact witnessed strand (an unrelated live session rode the witnessed recovery); (b) the entry's turn-error escalation half is intentionally not carried because the arm lands warning-only, and the touching session re-arms through the recipe's existing escalation paths and the maintenance skill's attempt bound instead of recording a turn error.
- assume the flag's residual masking cost is accepted and named: a recovery that re-points the successor pointers without recording an attributable entry suppresses that order's flag, and the re-point is itself the repair, so the residual is the repair already happening.

Decision points requiring a grill: none remain.

## Standing constraints

- The pins suite must stay green: both edited skill files (`agents/skills/maintenance/survey-arms.md`, `agents/skills/maintenance/zcode.md`) are pinned files; additions are additive sentences inside existing bullets and no pinned span moves.
- The pins-suite edits this plan makes are additive span needle registrations (one per edited skill file, the suite's own same-edit pin convention); the schedule-ask pin re-key precondition already landed on main (covering witness commit `fix: bind archive decisions to the reviewed plan bytes`), so this plan's pins edits are additive only, never a weakening or removal of a pin's protected span; no gate behavior changes and the verify-successor operation is read-only over both files it reads.
- No em-dashes and no absolute user paths in committed files; the public-hygiene scan must exit 0 before every commit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the operation flags the witnessed 12:04 shape from fixtures and stays silent on the healthy, recovered, and not-yet-grace-expired shapes.
- restraint: the arm is read-only and warning-shaped end to end; no ledger write, no state write, no refusal class, no lane block anywhere in the path.
- single-sourcing: the stall vocabulary lives once in the overlay and the survey arm cites it, never restating it.

**Done when:**
- `python3 scripts/test_execute_plan_resume_watcher.py ClockedOrderSuccessorVerificationTest -v` passes with the new fixture-backed tests.
- `bash scripts/check_maintenance_pins.sh` exits 0 with both skill-file edits in place.
- The maintenance survey's clocked-order consult text names the verify-successor leg and the overlay's re-arm hygiene names the stall classification.

**Ship when:**
- The next survey turn after landing reports any live flagged order through the new consult leg and the touching session's re-arm duty discharges the stall; observed in the turn record, not by this plan's tasks.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py` *(one-line operation-name tuple extension only; the dispatch body is unchanged)*
- `scripts/check_maintenance_pins.sh` *(additive span needle registrations; the re-key precondition already landed on main)*
- `scripts/machinery_registry.json` *(one pre-registered admission-entry-plus-removals-row pair)*

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` *(new test class inside the existing file)*

**Documentation (skill text):**
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/zcode.md`
- `docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md` *(already deleted on main by the covering witness commit; cited as the re-key's origin)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the discharge-on-fire branch of `run_clocked_order_operation`; reason: the launch-leg decision belongs to the launchd promotion review, deliberately outside this plan
- the wrapper's dispatch body outside the operation-name tuple; reason: the tuple extension is the only wrapper change this plan makes
- `.ai-playbook/scheduler-state.json` schema; reason: read-only consumption, no state-schema change is admitted

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_execute_plan_resume_watcher.py ClockedOrderSuccessorVerificationTest -v
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: the verify-successor test suite

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `ClockedOrderFixture` in `scripts/test_execute_plan_resume_watcher.py`

- [x] Write the fixture-backed tests first (tests-first TDD; the class runs against not-yet-existing code) using the existing `ClockedOrderFixture` pattern, one criterion per arm family below [class: REPOSITORY_TEST]
- [x] Flag-shape arms: the witnessed 12:04 shape flags; the healthy shape stays empty (sanitized transcription of a captured real state-file entry: field structure real, values replaced with fixture equivalents); the recovered shape stays empty (parent present naming a different order); a discharge younger than the grace window stays empty [class: REPOSITORY_TEST]
- [x] Pointer arms: the parent-leg positive arm flags (next_turn_at re-pointed but parent still naming the discharged order); the absent-parent arm treats an absent or non-string `parent_automation_id` as unmoved; the masking arm flags (an unrelated session's `children[]` entry inside the verification window plus both pointers still naming the order) [class: REPOSITORY_TEST]
- [x] Attribution arms: the attributable-entry arm stays empty, parameterized across all four attribution routes the Terms and predicate admit (for each route in turn, an entry inside the verification window whose `automation_id`, `cycle`, `target`, or note text names the discharged order, both pointers still naming it, outcome `failed` included: expect empty) [class: REPOSITORY_TEST]
- [x] The late-recorded arm stays empty (an attributable entry whose `created_at` falls past the verification window with both pointers unmoved, pinning the windowless clearing semantics) [class: REPOSITORY_TEST]
- [x] Blocked-input arms: a malformed state file, a missing state file, an unreadable ledger, a zero or negative `grace_minutes`, a malformed `grace_minutes` parameter, and a malformed `scheduler_state_path` parameter each return their named blocked reason code or empty-result form [class: REPOSITORY_TEST]
- [x] The read-only restraint arm snapshots ledger and state bytes before and after a flagged-shape run and asserts both unchanged with no temp residue [class: REPOSITORY_TEST]
- [x] A CLI-level test drives the new kind through the wrapper's dispatch path with explicit `ledger_path`, `payload_home`, and `scheduler_state_path` in the payload and the fixture order's `requested_epoch` written relative to the real clock (one grace window plus a fixed five-minute margin in the past), so reachability past the argparse `choices` gate is witnessed and the ambient clock is the pinned input by construction [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new class fails with errors naming the absent `clocked-order-verify-successor` kind and its handler (attribute and value errors against not-yet-existing code), never a bare loader error or an assertion-free pass [class: REPOSITORY_TEST]

### Task 2: the read-only verify-successor operation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `run_clocked_order_operation` in `scripts/execute_plan_resume_watcher.py`
- `ClockedOrderLedger` in `scripts/execute_plan_resume_watcher.py`

- [x] Add the `clocked-order-verify-successor` operation kind as a module-level handler beside the `_rearm_order_carrier` precedent (for example `_run_clocked_order_verify_successor`), leaving a thin read-only branch in `run_clocked_order_operation` [class: IMPLEMENTATION_REQUIRED]
- [x] Handler inputs and validation: the handler accepts `scheduler_state_path` (default `.ai-playbook/scheduler-state.json` under the resolved repository root) and `grace_minutes` (default 30), validates `grace_minutes` as a positive number and `scheduler_state_path` as a string path (malformed values return the named blocked shape family, never a raised traceback) [class: IMPLEMENTATION_REQUIRED]
- [x] Handler result shape: the handler reads the ledger through a strict lock-held read and the state file from disk, and returns `status: success` with a `flagged` list; it performs no ledger mutation [class: IMPLEMENTATION_REQUIRED]
- [x] The ledger read is fail-closed for this operation: extend `ClockedOrderLedger` with a strict lock-held read variant (for example `read_strict()`, still inside `authoring_state_lock`, raising a named error on OSError, JSON decode failure, or non-dict bytes), and the handler consumes only that variant, never the fail-open `read()` [class: IMPLEMENTATION_REQUIRED]
- [x] The strict variant's timestamp parsing replicates the naive-as-UTC, Z-suffix-aware convention `parse_iso` in `scripts/rearm_on_touch.py` uses, mirrored locally rather than imported across modules [class: IMPLEMENTATION_REQUIRED]
- [x] The flag predicate per discharged order, evaluated only when now is past `requested_epoch` plus the grace window: the order state is `discharged`, AND the successor test fails [class: IMPLEMENTATION_REQUIRED]
- [x] The successor test passes when both successor pointers have moved off the order (`next_turn_at` parses to an instant other than the order's `requested_epoch`, and `parent_automation_id` compares by exact equality against neither the order's recorded carrier label nor the order id, an absent or non-string `parent_automation_id` counting as unmoved) [class: IMPLEMENTATION_REQUIRED]
- [x] The successor test also passes when a `children[]` entry attributable to the order exists (its `automation_id`, `cycle`, `target`, or note text names the order id or the order's carrier label; any outcome counts, `failed` included, because it evidences the turn ran) [class: IMPLEMENTATION_REQUIRED]
- [x] A malformed state file returns the operation's blocked shape with its own named reason code; a missing state file returns a named empty-result non-error mirroring the `no-scheduler-state-file` verdict class in `scripts/rearm_on_touch.py` (absence is the fresh-repo normal form, never an error finding); an unreadable or malformed ledger returns the blocked shape through the strict read instead of a silent empty `flagged` list [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a state file whose `next_turn_at` has been re-pointed by a recovery and whose `parent_automation_id` names a different order's carrier label (the real recovered shape on disk has the field present naming the new order), the operation returns an empty `flagged` list and exits success [class: IMPLEMENTATION_REQUIRED]
- [x] Register the new kind in `_CLOCKED_ORDER_OPERATIONS` in `scripts/execute_plan_runtime.py` (one tuple entry; the argparse `choices` derive from it and the dispatch body passes through unchanged) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the new test class passes and the full existing suite still passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: add read-only discharged-without-successor verification to the clocked-order operations` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the survey consult leg

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `Clocked-order consult` in `agents/skills/maintenance/survey-arms.md`

- [x] Verify the re-key precondition already landed before any other edit: the suite's former `schedule ask bullet 1 whole` pin at `scripts/check_maintenance_pins.sh` now keys to the distinctive short needle `list existing automations first` from the landed AGENTS.md sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the covering fix row docs/history/backlog/2026-10-18-maintenance-pin-stale-schedule-ask-contract.md is already deleted, with commit `fix: bind archive decisions to the reviewed plan bytes` as its covering witness; when either verification fails on the then-current tree, perform the re-key per the filed prescription instead and record the deviation in the run report [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite passes on the re-keyed baseline before any other edit [class: REPOSITORY_TEST]
- [x] Register the companion span needle in `scripts/check_maintenance_pins.sh` (one additive `pin()` entry asserting the consult leg's distinctive span), following the suite's own same-edit pin convention [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the new pin fails against the unedited survey-arms.md because the verify-successor leg is absent [class: REPOSITORY_TEST]
- [x] Extend the Clocked-order consult bullet with the verify-successor leg after the pickup arm (the Terms definition's third position): the turn runs the new read-only operation once per consult and reports each flagged order as a warning-shaped survey finding naming the order id, its requested time, and the state evidence, citing the overlay's stall classification for the touching session's response [class: IMPLEMENTATION_REQUIRED]
- [x] The leg performs no ledger or state write and blocks no lane; the stall classification this citation names is created by Task 4, so these two tasks' edits must not be split across runs [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite passes and the em-dash and hygiene scans pass over the edit [class: REPOSITORY_TEST]
- [x] Commit: `docs: add the discharged-without-successor leg to the clocked-order consult` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the overlay stall vocabulary

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/machinery_registry.json`

Primary class anchors:
- `Re-arm hygiene` in `agents/skills/maintenance/zcode.md`

- [x] Register the companion span needle in `scripts/check_maintenance_pins.sh` first (one additive pin asserting the stall sentence's distinctive span) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the new pin fails against the unedited overlay [class: REPOSITORY_TEST]
- [x] Add the stall sentence to the Re-arm hygiene bullet in citation form (the operation owns the predicate; the overlay never restates it): a discharged order the consult's verify-successor leg flags is a stall, never healthy idle [class: IMPLEMENTATION_REQUIRED]
- [x] The stall sentence continues: before acting on a flag the touching session cross-checks the state file and the automation listing for a live pending child of the order (the six-hour liveness shape), and otherwise treats the flag as a darkness input and re-arms per the recipe through the recipe's existing escalation paths and the maintenance skill's attempt bound, the duplicate-parent tripwire bounding any residual overlap [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite passes; the full Validation Commands block passes from the worktree root [class: REPOSITORY_TEST]
- [x] Pre-register the machinery-registry pair for the new consult arm in `scripts/machinery_registry.json`, mirroring the `duty:primary-freshness-sweep` precedent's two-row shape: an entries-array admission entry (disposition keep, witness class incident referencing the 2026-10-18 silent-strand row) plus a removals row carrying the admission's criteria (promotion rides the launchd promotion review, sunset in any case by 2027-01-18) [class: IMPLEMENTATION_REQUIRED]
- [x] The removals row's single witness ref points at this plan's completed twin with the second witnessed incident named in its note, and the landing carries the re-point duty for the admission entry's ref if the referenced backlog row is deleted in the landing range; after writing the pair, parse `scripts/machinery_registry.json` as JSON before the commit [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: classify the flagged discharged order as a stall in the re-arm hygiene` [class: IMPLEMENTATION_REQUIRED]
