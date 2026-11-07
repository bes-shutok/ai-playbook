# Plan: budget-resume carrier discharge and survey census

Backlog origin: docs/history/backlog/2026-11-04-budget-resume-carrier-gc.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-budget-resume-carrier-gc-pc377ff97-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: no
Authoring claim: 2026-11-04-budget-resume-carrier-gc.md (session sess_4b48377c-e34e-44ed-8c23-79ceb44684c6)

## Terms

- Budget-resume carrier: the launchd one-shot the plans-authoring standing resume watcher arms so a paused or interrupted authoring run can resume at the window reset; it is the only producer of an `armed_launchd` receipt (a Budget-gate pause boundary itself is non-schedulable: it writes no `resume_watcher` receipt and arms no launchd carrier, and a pause or supersede boundary already tears down the outgoing carrier through `supersede_carrier_teardown`); keyed label `ai-playbook.budget-resume.<key>` (legacy label without the key), job dir under `~/.ai-playbook/runtime/launchd/`, plist, out/err logs beside it, sentinel, and fired marker.
- Keyed identity: the per-(plan slug, repo root) key (`launchd_identity_key`) naming the label, job dir, sentinel, and fired marker; it separates concurrent runs of DIFFERENT plans or repos, and two concurrent runs of the same plan in the same repo share one identity, which is why every destructive actor verifies live ownership by the arm-unique discriminator (the receipt's `watcher_id`, the per-install `rw-<uuid4>` value, compared against the loaded payload's embedded segment; the window-scoped `reset_at_epoch` is shared by same-window arms and the arm-clock `scheduled_at_epoch` by same-second arms, so neither carries an ownership signal) before any destructive leg.
- Sentinel / fired marker: the self-disable pair; the job touches the sentinel at its first fire, and a terminal decision consumes the sentinel and writes `<sentinel>.fired`; the guards make every later fire inert, but the job itself stays loaded in launchd.
- Off-carrier resume: any resume of a paused run by a route other than its own carrier's verified fire: the automation prompt's manual-clear resume, a manual resume, a peer-resumed re-entry.
- Own carrier / foreign carrier: the carrier a run's own recorded receipt names versus any other lineage's carrier.
- Discharge: the receipt-only teardown applied at the resume and closeout boundaries: under the budget-guard lock (an unacquired or timed-out lock runs no destructive leg and reports lock-unavailable-retained), verify the loaded payload's embedded discriminator (the arm's `watcher_id`) against the discharging run's own receipt's value, boot out the job and read the bootout outcome through the loaded-label read primitive (pass, or not-loaded when the label is confirmed absent from the loaded view after bootout, so a nonzero exit with an absent label is not-loaded rather than failure; anything else is ambiguous), then only after a passing or not-loaded outcome remove the plist and the label's log files (log paths scoped to the launchd job-dir root by realpath containment like the plist and dir legs), consume the sentinel, then remove the fired marker again after that consume (the consume primitive re-creates the marker), and rmdir the keyed job dir once empty; a failed or ambiguous bootout retains the guards and reports carrier-retained.
- Census: the read-only enumeration of every budget-resume-family carrier under the runtime launchd job dir (keyed and legacy layouts; labels read from each candidate plist's `Label` key, with foreign-family co-tenants such as clocked-order carriers excluded as co-tenants, never census rows), plus the launchctl loaded-label view as the cross-check for carriers whose plist is absent, plus the sentinel/fired-marker state read from the runtime root `~/.ai-playbook/runtime/` (sentinels and their `<sentinel>.fired` markers live beside the job dirs, not inside them); it never repairs.
- Receipt-only: discharge input comes only from the recorded `armed_launchd` receipt fields (the run's `resume_watcher` record, or the fired supersede history event's retained `armed_launchd` fields when the fire-resume supersede cleared the record; this plan adds that retention, which does not exist on disk today) plus the discriminator trailing segment the arm itself adds to the carrier payload (the receipt's own `watcher_id`, already persisted on the receipt; the Gate delta's "no schema field" statement concerns record schemas, not this payload segment); no identity is derived outside the receipt (the teardown's receipt-is-the-sole-identity-source rule, the teardown's G2 discipline).
- Job dir: `~/.ai-playbook/runtime/launchd/<key>/` for a keyed carrier; the legacy label's plist sits in the flat root, which is shared storage and is never removed.
- Budget-guard lock: the `budget_guard_lock` file lock derived from the carrier's sentinel path, which the arm already holds while it writes the plist and bootstraps; it yields `False` after its 2.0s timeout instead of raising.
- Watcher-fire: the plans-watcher fire operation that consumes the sentinel on a terminal decision; on a resume decision it supersedes the run's receipt (clearing the `resume_watcher` record; this plan adds the fired supersede history event's retention of the outgoing record's `armed_launchd` fields, which the closeout discharge's fallback reads).
- Protocol home: a skill file carrying the pause protocol's text; this plan amends the canonical home (`agents/skills/execute-plan/SKILL.md`), the authoring mirror (`agents/skills/plans/SKILL.md`), the shared closeout home (`agents/skills/execute-plan/worktree-first.md`, one home serving both placements), and the review-loop restatement (`agents/skills/review-loop/SKILL.md`).
- Consult set: the survey consult arms listed in `agents/skills/maintenance/survey-arms.md`.
- Maintenance pins suite: `scripts/check_maintenance_pins.sh`, the standing span-token gate over pinned skill text.
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check`, the warning-only byte-budget report over skill files.

## Why

The plans-authoring standing resume watcher arms launchd carriers that its protocol never discharges on the paths where they become garbage: a run that resumes by any route other than its own carrier's fire, or is interrupted with the standing watcher still armed, leaves a loaded launchd job that fires once into a dead context and then stays loaded forever (the pause and supersede boundaries themselves already tear down the outgoing carrier; the garbage paths are the interrupted run that reaches no further boundary and the final-handoff arm that outlives closeout). The witnessed 2026-11-04 authoring-cycle closeout held five loaded carriers from finished lineages, one exiting 127; the accumulation is monotonic and invisible because no surface names the carrier list, and each stale fire is a spurious session start at an unpredictable time.

## Gist & Examples

TLDR: the plans-authoring resume paths and the run closeout gain a carrier discharge duty (carried by reference across the protocol homes, operative where a recorded `armed_launchd` receipt exists), and the maintenance survey gains a read-only budget-resume carrier census, so a run's own launchd carrier is booted out and removed when the run resumes off-carrier or reaches closeout, and accumulated carriers become visible per survey turn, because armed carriers from finished lineages fire into dead contexts and accumulate invisibly (code-quality).

Before (today): an authoring run that resumes manually, by an automation prompt, or is interrupted leaves its keyed launchd carrier armed; the job fires once into the dead context (the witnessed 127 exit) and then sits loaded but inert; the survey lists no carriers, so the accumulation is invisible and unbounded.

After (this plan): every resume path and the closeout boundary discharge the run's own armed carrier when a recorded `armed_launchd` receipt exists (bootout-first, guard-retaining, lock-serialized, receipt-only), riding the existing record surfaces; the survey's consult set gains a read-only census listing the budget-resume-family carriers under the runtime launchd job dir plus the loaded-label view, each turn; no arm ever discharges a foreign or newly re-armed carrier, which the arm-unique discriminator check and the census's no-reaper reporting enforce.

Example: an authoring run is interrupted mid-plan with its standing watcher still armed, and a peer session or a manually issued resume picks the run up. The resume path first reconciles the run's state as today and then discharges the interrupted run's own armed carrier through the new operation, recording the discharge outcome beside the reconciliation note; if bootout fails, the sentinel and marker stay in place and the outcome reports carrier-retained. A second run's carrier fires normally, its resume decision supersedes the receipt, and the run later reaches closeout: the closeout discharge reads the fired history event's retained record and boots out the inert loaded job there. At the next survey turn the census lists three carriers: one spent from a finished run, one inert-but-loaded, one loaded label whose plist was already unlinked by a prior teardown; the survey reports them and removes nothing.

Edge cases: the carrier's own verified fire consumes the sentinel through watcher-fire, so a fire-completed resume needs no resume-path discharge, and the closeout check then finds the inert loaded job and discharges it there; a receipt without an `armed_launchd` record tears nothing down, and a duty home whose run holds no recorded receipt (a Budget-gate pause arms no carrier; the review-loop home owns no watcher state) records the condition instead of improvising a discharge; a discharge is serialized under the budget-guard lock and refuses a loaded payload whose embedded `watcher_id` differs from the discharging run's own receipt's value (carrier-mismatch-retained), so a peer's re-armed carrier at the shared identity is never destroyed even when both arms fall in the same quota window, and the hardened supersede teardown enforces the same ownership check at its call sites; a payload with no embedded trailing segment (a pre-landing carrier) retains with legacy-unverifiable; a failed bootout retains the sentinel and fired marker and reports carrier-retained; a foreign carrier is census-only and operator-removed; no discharge step ever blocks the boundary it rides.

## Outcome

A run's own budget-resume carrier can no longer outlive the run silently, and accumulated carriers from finished lineages are visible to every survey turn.

- A resume by any route other than the carrier's own verified fire discharges the run's own armed carrier before work continues when a recorded `armed_launchd` receipt exists, with the outcome recorded on the resume's existing record surface.
- A run reaching its closeout boundary with its own carrier still armed (or loaded but inert) discharges it there, the receipt riding the closeout's existing receipt surface, for worktree and primary placements alike.
- The maintenance survey lists every budget-resume carrier under the runtime launchd job dir (keyed and legacy) plus the loaded-label view each turn, read-only, with loaded and sentinel/fired state.
- No arm removes another lineage's or a peer's live carrier autonomously: the ownership check refuses a live payload whose embedded `watcher_id` differs from the actor's own receipt's value at both destructive actors (the discharge and the hardened supersede teardown), and the census names stale foreign carriers for operator direction.
- Gate delta: two protocol duty additions (the resume-path discharge and the closeout discharge; both best-effort with reported outcomes, riding existing record surfaces, neither a refusal class nor a blocking gate), one read-only report-only survey consult (the census; carries no refusal), one additive carrier-payload segment (the arm carries its receipt's shell-quoted `watcher_id` in a dedicated optional request key that the scheduler appends as a fixed-marker no-op trailing segment after the manual command in the carrier payload, so every destructive actor can verify live ownership against the receipt value already persisted; report-only fall-throughs keep naming the exact manual resume command unchanged), and one additive history-event field (this plan adds the fire-resume supersede's history event retention of the outgoing record's `armed_launchd` fields, so the closeout discharge can read a fired-then-cleared receipt; priced by the same completed-integrity-failure witness, because the fired inert job is the witnessed accumulation's main path); no refusal class, hard gate, fence, record-schema field, or review-layer duty is added or removed; the duty pair and the discriminator are priced by the completed-integrity-failure witness docs/history/backlog/2026-11-04-budget-resume-carrier-gc.md (five loaded carriers from finished lineages at the 2026-11-04 closeout, one exiting 127), and the census consult by the served PLAN-PROMPTS entry's Machinery admission record (incident link docs/history/backlog/2026-11-04-budget-resume-carrier-gc.md; catch frequency: one stale carrier per off-carrier resume or dead pause run; false-positive cost: a census row naming a live paused run's carrier, bounded because the census never repairs; review date 2026-12-04).

## Assumptions

- assume the discharge and the supersede teardown share one hardened core: `supersede_carrier_teardown` gains the sanctioned-directory scope checks (its plist unlink scoped to the launchd job-dir root, its consume switched to the scoped variant) and an optional job-dir leg, and the discharge calls the hardened function, so the supersede call site and the new discharge enforce one strength; basis: the unscoped unlink/consume at lines 1040-1049 versus the scoped variants the module already provides (989-1014), and per-caller differential tests pinning each of the three supersede call sites' parameter mapping (the existing teardown tests cover only the clocked-order site).
- assume the new discharge keeps the receipt-only discipline: the destructive legs act only on the recorded `armed_launchd` paths plus the label-derived log names, and live ownership is verified by the arm-unique discriminator (the receipt's `watcher_id`, embedded in the carrier payload at arm time) before any destructive leg; basis: the teardown's G2 statement, the per-(plan, repo) key's shared-identity limitation recorded in `launchd_identity_key`, and neither `reset_at_epoch` (window-scoped, identical for same-window arms) nor `scheduled_at_epoch` (arm-clock, shared by same-second arms) being arm-unique, while the per-install `watcher_id` is.
- assume the census is read-only and report-only and shares the survey consult set's guard and fail-open semantics; basis: the survey's existing consult arms (machinery regrowth guard consult, clocked-order consult).
- assume the no-reaper constraint from the served entry's Scope arm 3: no arm deletes another lineage's carrier autonomously; the census names stale foreign carriers and removal stays operator-directed.
- assume hermetic tests fake the launchctl primitives and the new loaded-label read via the module's existing attribute-patch convention, and that the census enumeration root and the sanctioned roots are injectable for tests; basis: `scripts/test_execute_plan_resume_watcher.py`'s fakes and module-constant patching.
- assume a firing into a live-but-not-owning context stays possible until discharge runs; the duty narrows the window rather than proving it closed; basis: the conservative posture both protocols already take and the served entry's rejected-alternatives reasoning.

Decision points requiring a grill: none remain (all resolved by recorded receipt under the maintenance-selected standing authorization; the discharge placement in the resume and closeout arms, the census placement in the survey consult set, and the no-reaper constraint are fixed by the served PLAN-PROMPTS entry's "Scope arms:" records for budget-resume-carrier-gc).

## Standing constraints

- No reaper: no arm deletes another lineage's carrier autonomously; a stale foreign carrier is named in the census and removed only under operator direction.
- Receipt-only plus live ownership: destructive legs act on the run's own recorded `armed_launchd` paths only (the `resume_watcher` record, or the fired history event's retained record), after the ownership check passes (the loaded payload's embedded `watcher_id` equals the actor's own receipt's value) and the bootout outcome is known; a failed or ambiguous bootout retains the sentinel/fired pair and reports carrier-retained; an unacquired lock writes no plist and runs no bootstrap on the arm side, and runs no destructive leg on the discharge and supersede-teardown sides.
- Best-effort hygiene: discharge and census report outcomes and never block the boundary they ride on a best-effort failure; no new refusal class, gate, validator, lock, or ledger.
- Skill-text anti-growth: each touched skill file cites the origin row in at most one line; the byte-budget gate output is recorded in the run log (warning-only posture).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the discharge acts only on the receipt-named own carrier after the discriminator check and a known bootout outcome, preserves receipt-only and no-reaper, and the census never mutates
- completeness: the resume-path duty lands in the canonical execute-plan Budget gate and the plans mirror, the closeout duty in the worktree-first closeout home and the plans mirror, the review-loop home records the exclusion, and the census arm sits in the consult set with fail-open semantics
- economy: the operations reuse the hardened shared teardown core, the text edits cite by reference, and no machinery beyond the two operations and the payload discriminator prefix is added

**Done when:**
- the census and discharge operations exist in the watcher module and are reachable through the runtime CLI's operation dispatch, with hermetic tests passing
- the resume paths and the closeout boundary order the discharge with its outcome recorded, in the canonical, mirror, and closeout homes, with the review-loop home recording the exclusion
- the survey consult arm carries the census with the no-reaper reporting shape
- the watcher suite, the maintenance pins suite, and the hygiene scan pass; the byte-budget gate output is recorded

**Ship when:**
- none stated (repository-verifiable work only)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_resume_watcher.py` (Tasks 1-4)
- `scripts/execute_plan_runtime.py` (Tasks 1-4)
- `agents/skills/execute-plan/SKILL.md` (Task 6)
- `agents/skills/plans/SKILL.md` (Task 6)
- `agents/skills/execute-plan/worktree-first.md` (Task 6)
- `agents/skills/review-loop/SKILL.md` (Task 6)
- `agents/skills/maintenance/survey-arms.md` (Task 8)

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` (Tasks 1-4)
- `scripts/check_maintenance_pins.sh` (Tasks 6-8) (the new span pins land here, plus conditional span-token adjustment)

**Backlog:**
- `docs/history/backlog/2026-11-04-budget-resume-carrier-gc.md` (review-only) *(covered flip rides the landing)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/quota-policy.md`; reason: the quota leg's park arms already name carrier arming and its resume rule is unchanged; this plan is orientation-only there
- `agents/skills/maintenance/zcode.md`; reason: the overlay's launchd carrier recipe keeps its install-side shape and its missed-fire detector already classifies stale fires
- `agents/hooks/budget-guard/`; reason: the backstop hook's flag semantics are unchanged by this plan
- `scripts/done_run.sh`, `scripts/done-lock.sh`; reason: no closeout gate changes; the discharge rides the existing record surface without a new gate

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
```

### Task 1: carrier census operation in the watcher

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Add failing census tests: three enumeration sources (keyed job dirs with the label read from each candidate plist's `Label` key, legacy flat plists, loaded labels from a faked module-level read primitive), plist-less forms reported (loaded label with no plist; logs-only dir), a sentinel-only carrier whose job dir is already gone (fired marker in the runtime root, reported from the runtime-root sentinel state) [class: REPOSITORY_TEST]
- [ ] Add failing census exclusion and isolation tests: foreign-family co-tenants excluded (a `clocked-order-<key>` job dir, a flat `ai-playbook.clocked-order.plist`, a loaded clocked-order label, and a `clocked-order-<key>.sentinel` with its `.fired` marker in the runtime root are never reported as budget-resume rows), per-carrier error isolation (a corrupt plist yields an error row while healthy carriers still report), strictly read-only [class: REPOSITORY_TEST]
- [ ] Add the module-level loaded-label read primitive the census calls, injectable for tests; implement the census over the injectable root: keyed dir walk, legacy flat plists, merged loaded-label view, plist-less records, per-carrier error rows, no writes [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the census family filters: read each candidate's label from its plist's `Label` key (keyed dirs filtered to the 12-hex key shape) and report only `ai-playbook.budget-resume`-family labels, apply the same prefix filter to the loaded-label view, and filter the sentinel-only source by name (only `budget-resume.sentinel` and `budget-resume-<12hex>.sentinel` forms are budget-resume carriers; clocked-order co-tenants are never census rows) [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the discharge's marker scope and bootout outcome: the receipt's `fired_marker_path` must equal the derivation from its sentinel path and realpath-resolve inside the runtime root before the consume and the marker unlink, refusing and reporting otherwise; bootout first with the outcome interpreted through the loaded-label read primitive (pass, or not-loaded with the label confirmed absent; ambiguous retains) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the failing census CLI dispatch test: the runtime CLI dispatches `budget-carrier-census` through its own branch, the census dispatch test passes no `state_path` and asserts no subprocess is spawned, and the CLI dispatch tests patch `DEFAULT_LAUNCHD_JOB_DIR`, `DEFAULT_RESUME_SENTINEL`, the launchctl primitives, and the loaded-label read as the clocked-order CLI tests do [class: REPOSITORY_TEST]
- [ ] Run the watcher suite, expect the new tests RED and the existing suite green: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q` [class: REPOSITORY_TEST]

### Task 2: receipt-only discharge operation in the watcher

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Add the failing round-trip test: an arm-then-fire-resume-then-closeout-discharge round trip boots out and removes the carrier through the fired history event fallback (the event's retained `watcher_id` satisfies the ownership check) [class: REPOSITORY_TEST]
- [ ] Define the discharge input contract: the operation takes the run's machine-state path (`state_path`) and reads the run's own `resume_watcher` record (its `armed_launchd` fields) through the module's existing plans-watcher adapter pattern, never a hand-copied receipt JSON; a state with neither a record nor a fired history event tears nothing down [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the fired history event fallback: when the `resume_watcher` record is null because the run's own fire-resume supersede cleared it, the discharge falls back to the latest fired supersede history event's recorded `armed_launchd` fields (the run's own recorded machine state, so receipt-only holds) [class: IMPLEMENTATION_REQUIRED]
- [ ] Read the loaded payload from disk: the discriminator check's payload is the recorded `plist_path`'s `ProgramArguments` read from disk (the arm writes the plist and bootstraps it under the same budget-guard lock, so the on-disk plist is the loaded payload) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the fired history event's retention: on a supersede whose transition reason is `fired`, `PlansAuthoringWatcherAdapter.compare_and_swap_supersede`'s `resume-watcher-superseded` history event keeps the outgoing record's `armed_launchd` fields beside the `watcher_id` it already records, so the closeout discharge's fallback can run the ownership check and act on the recorded paths; pin the stored event's fields with a test assertion [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the discharge's lock and payload reads: budget-guard lock from the receipt's sentinel path, running no destructive leg when the lock is not acquired (lock-unavailable-retained; the shared core takes no lock of its own); the discriminator check reads the recorded plist's `ProgramArguments`, skipped when the recorded plist is absent (nothing is loaded at this path) [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the discharge ownership outcomes: carrier-mismatch-retained when the payload's embedded `watcher_id` differs from the receipt's value; legacy-unverifiable retention for a payload with no embedded trailing segment (the census names these for operator direction) [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the discharge's marker scope and bootout outcome: the receipt's `fired_marker_path` must equal the derivation from its sentinel path and realpath-resolve inside the runtime root before the consume and the marker unlink, refusing and reporting otherwise; bootout first with the outcome interpreted through the loaded-label read primitive (pass, or not-loaded with the label confirmed absent; ambiguous retains) [class: IMPLEMENTATION_REQUIRED]
- [ ] Implement the discharge's removal legs: on pass or not-loaded unlink plist, label-derived logs (scoped to the launchd job-dir root by realpath containment), consume scoped, then remove the leftover fired marker only after that consume (the consume primitive re-creates the marker), rmdir keyed dir only (never the legacy flat root), report job-dir-retained when not emptyable [class: IMPLEMENTATION_REQUIRED]

### Task 3: discriminator embed and shared-core hardening in the watcher

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Make the launchd arm serialize fail-closed: when `budget_guard_lock` does not acquire (it yields `False` after its 2.0s timeout), the arm returns not-scheduled with the named reason `launchd-guard-lock-unavailable` so the chain falls through to report-only, instead of writing the plist and bootstrapping unlocked; a discharge holding the lock across its launchctl legs then cannot overlap a peer's unlocked re-arm at the shared identity [class: IMPLEMENTATION_REQUIRED]
- [ ] Register only `budget-carrier-discharge` in `scripts/execute_plan_runtime.py`'s plans-watcher operation family (the `_PLANS_WATCHER_OPERATIONS`-dispatched path with its `state_path` requirement, inside the plans-watcher kind ladder before the watcher-operation fall-through), and give `budget-carrier-census` its own explicit `main()` dispatch branch that requires no `state_path`, builds no authoring adapter, and takes an optional injectable root [class: IMPLEMENTATION_REQUIRED]
- [ ] Embed the receipt's `watcher_id` in the carrier payload at arm time as a fixed-marker no-op trailing segment: the budget-resume request carries it in a dedicated optional request key (shell-quoted, in hand in the `record_budget_boundary` request construction), and the scheduler appends that segment after the `manual_command` it passes to `fire_command` when the key is present [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the embed guards-first and report-only-clean: the fired and sentinel guards stay first (the existing guard-first assertion keeps its form), report-only fall-throughs keep naming the exact manual resume command unchanged, and clocked-order requests carry `order_id` and embed no segment [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the embed parse positional: the discharge parses the trailing segment at its fixed position only (`shlex.split` at the known segment, never a whole-string search), so a legacy payload containing a fake segment stays legacy-unverifiable [class: IMPLEMENTATION_REQUIRED]
- [ ] Add failing arm-side embed tests: driving the scheduler (bootstrap faked) with the budget-resume request embeds the fixed-marker trailing segment carrying the shell-quoted `watcher_id` after the manual command in the plist's `ProgramArguments`, with the fired guard still the first executable segment so the existing guard-first assertion keeps its form; a clocked-order schedule with no embedded segment still schedules with the fired guard first [class: REPOSITORY_TEST]
- [ ] Harden `supersede_carrier_teardown` into the shared core: scope its plist unlink to the launchd job-dir root, switch its consume to the scoped variant, add the optional rmdir-when-empty leg; keep its receipt-only no-op arm; existing supersede tests pass or their span expectations are adjusted in the same change [class: IMPLEMENTATION_REQUIRED]
- [ ] Give the shared core the ownership gate the discharge uses: read the recorded plist's `ProgramArguments` embedded trailing segment and refuse all destructive legs with carrier-mismatch-retained when its `watcher_id` differs from the caller's receipt's value; a prefix-less payload routes through a named per-caller legacy parameter that states that caller's behavior (the present unconditional teardown for the three existing call sites) [class: IMPLEMENTATION_REQUIRED]
- [ ] Give the shared core its per-caller lock parameter: each call site acquires the budget-guard lock derived from the receipt's sentinel path and runs no leg when it yields `False` (lock-unavailable-retained) [class: IMPLEMENTATION_REQUIRED]
- [ ] Give the shared core its per-caller behavior parameters: per-caller parameters for the bootout-outcome gate and the log-leg behavior keep the three existing supersede call sites' present semantics for those two parameters when they move onto the core, the scoping and ownership changes being the named intended deltas each caller's differential test pins [class: IMPLEMENTATION_REQUIRED]

### Task 4: discharge and hardening verification suite in the watcher

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Add failing arm-side embed hygiene tests: a report-only fall-through names the exact manual resume command without the segment; an id containing shell metacharacters cannot execute (the value is `shlex.quote`d) [class: REPOSITORY_TEST]
- [ ] Add the failing arm lock test: a faked lock yielding False on the arm writes no plist and runs no bootstrap, reporting `launchd-guard-lock-unavailable` [class: REPOSITORY_TEST]
- [ ] Add failing discharge tests: keyed happy path with ordered legs (bootout, then plist, logs, scoped consume, leftover marker, rmdir when empty; the marker unlink asserts after the consume because `consume_resume_sentinel` re-creates the marker, and asserts no marker remains at the end); explicit-path unkeyed receipt whose recorded paths deviate from any derivation, asserting no derived-default path is touched; receipt without an `armed_launchd` record tears nothing down [class: REPOSITORY_TEST]
- [ ] Add failing discharge guard tests: a faked failing bootout retains the sentinel and fired marker and reports carrier-retained; a spent pair (sentinel absent, plist and dir gone) runs the remaining legs with each leg's outcome reported and the discriminator check skipped because no payload exists; paths outside a sanctioned root refuse per family (sentinel legs vs runtime root, plist, dir, and log legs vs launchd root, including a log label with a traversal component) [class: REPOSITORY_TEST]
- [ ] Add failing discharge ownership tests: a loaded payload whose embedded `watcher_id` differs from the receipt's refuses with carrier-mismatch-retained (two same-window re-arms at one identity); a payload present with no embedded trailing segment (a pre-landing carrier) retains with legacy-unverifiable and tears nothing down, and a legacy payload containing a fake segment string still classes legacy-unverifiable (the parse is positional, never a search) [class: REPOSITORY_TEST]
- [ ] Add failing discharge marker and bootout tests: a recorded `fired_marker_path` deviating from the sentinel derivation or resolving outside the runtime root refuses before the consume and the marker unlink; a not-loaded bootout outcome (nonzero exit, label confirmed absent from the loaded view) runs the remaining legs; an ambiguous bootout outcome retains the guards [class: REPOSITORY_TEST]
- [ ] Add the failing round-trip test: an arm-then-fire-resume-then-closeout-discharge round trip boots out and removes the carrier through the fired history event fallback (the event's retained `watcher_id` satisfies the ownership check) [class: REPOSITORY_TEST]
- [ ] Add failing discharge lock tests: the discharge holds the budget-guard lock derived from the receipt's sentinel path across its legs, and a faked lock yielding False runs no destructive leg and reports lock-unavailable-retained; a legacy discharge leaves the shared flat root in place [class: REPOSITORY_TEST]
- [ ] Add the failing discharge CLI dispatch test: the runtime CLI dispatches `budget-carrier-discharge` through the plans-watcher family [class: REPOSITORY_TEST]
- [ ] Run the watcher suite, expect GREEN including all new tests, and record the summary in the run log [class: REPOSITORY_TEST]
- [ ] Commit: `feat: budget-resume carrier census and receipt-only discharge operations` [class: IMPLEMENTATION_REQUIRED]

### Task 5: supersede hardening verification at the three call sites

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_resume_watcher.py`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

- [ ] Add failing per-caller differential tests for the three supersede call sites (the watcher supersede boundary, the CLI supersede success path, and clocked-order cancel; currently around watcher lines 1405, 1588, 2986): each asserts an inside-root receipt runs every leg (bootout on the recorded plist, plist unlink, sentinel consume); the existing teardown tests cover only the clocked-order site, so these three are the behavior pins for the hardening [class: REPOSITORY_TEST]
- [ ] Add failing per-caller scoping tests at the same three supersede call sites: an explicit-path receipt whose paths sit outside the sanctioned roots gets the hardened outcome (bootout still runs; the plist unlink and the scoped consume are refused, each with its named reported reason) [class: REPOSITORY_TEST]
- [ ] Add failing per-caller ownership and lock tests at the same three supersede call sites: a mismatched live payload (an embedded `watcher_id` differing from the caller's receipt's value) refuses every destructive leg with carrier-mismatch-retained, and a faked lock yielding `False` runs no leg with lock-unavailable-retained [class: REPOSITORY_TEST]

### Task 6: the discharge duty's span pins

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/review-loop/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Add a failing span pin to `scripts/check_maintenance_pins.sh`'s budget-gate mirror family: heading-bounded extraction of the canonical Budget gate section pinning the duty-name token `carrier discharge` and the trigger span `other than its own carrier's verified fire` (the landing paragraph below uses both verbatim) [class: REPOSITORY_TEST]
- [ ] Add a failing worktree-first pin to the same family: extract the worktree-first.md duty span as the substring of the single physical line from the `Terminal closeout ownership (added` lead token through the `Drained-run closeout` marker (a `grep -o` span or a python pin block, not a heading-to-heading awk region, because both anchors sit mid-line on one physical line), pinning `carrier discharge` with `never blocking` scoped inside the new duty sentence [class: REPOSITORY_TEST]
- [ ] Add a failing plans-mirror pin to the same family: extract the plans Budget gate section pinning two named spans of the mirror discharge clause (one carrying the resume-path duty, one carrying the closeout duty via the closeout-specific span `still armed or still loaded`, both from the clause text the landing bullet prescribes) [class: REPOSITORY_TEST]
- [ ] Add a failing review-loop exclusion pin to the same family: extract the review-loop budget-gate paragraph pinning the single contiguous exclusion span `owns no watcher state and holds no `armed_launchd` receipt` of the landing sentence below (contiguous, not two token assertions, because `owns no watcher state` already occurs in that paragraph today and only the contiguous span is RED before landing and discriminating after) [class: REPOSITORY_TEST]
- [ ] Run the pins suite, expect RED on the new duty pins while every pre-existing pin stays green [class: REPOSITORY_TEST]
- [ ] Run the pins suite, the hygiene scan, and the byte-budget gate as their pinned commands `bash scripts/check_maintenance_pins.sh`, `bash scripts/scan-public-hygiene.sh`, and `python3 scripts/skill_text_budget.py --check` (Task 8 re-runs the same commands by reference to this bullet's pinned forms) [class: REPOSITORY_TEST]
- [ ] Apply the run expectations: exit 0 on the first two and a recorded output on the third, adjusting span-scoped pin expectations to the amended text where an existing assertion fails over the amended paragraphs, never deleting an assertion [class: REPOSITORY_TEST]
- [ ] Run the pins suite, expect RED on the new duty pins while every pre-existing pin stays green [class: REPOSITORY_TEST]

### Task 7: the discharge duty in the pause protocol's resume and closeout arms

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/review-loop/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In the canonical Budget gate section of `agents/skills/execute-plan/SKILL.md`, add a dated carrier discharge paragraph whose lead-in contains the contiguous span `carrier discharge` and whose body uses the trigger span `other than its own carrier's verified fire` verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] State the canonical paragraph's conditional: a resume by any route other than its own carrier's verified fire first discharges the run's own armed carrier through the budget-carrier-discharge operation when a recorded `armed_launchd` receipt exists in the run's machine-state home, or the run's own fired history event retained one after a fire-resume (the plans-authoring standing resume watcher is the receipt's only producer; a Budget-gate pause arms no launchd carrier) [class: IMPLEMENTATION_REQUIRED]
- [ ] State the canonical paragraph's posture: the outcome recorded on the resume's existing record surface, best-effort, never blocking the resume [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `Terminal closeout ownership` paragraph (lifecycle step 6) of `agents/skills/execute-plan/worktree-first.md`, add one dated closeout carrier discharge sentence before the `Drained-run closeout` marker, with a dated lead-in of the file's existing `(added DATE; plan ...)` convention that contains the contiguous span `carrier discharge` [class: IMPLEMENTATION_REQUIRED]
- [ ] State the closeout sentence's conditional: a run reaching its closeout boundary with its own carrier still armed or still loaded, when a recorded `armed_launchd` receipt exists (or the fired history event retained one), discharges it through the same receipt-only operation, placement-agnostic (worktree and primary placements alike), the outcome riding the closeout's existing receipt surface, best-effort, never blocking the closeout [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/plans/SKILL.md`'s Budget gate mirror, extend the existing resume-reconciliation sentence with one by-reference clause carrying both duties verbatim (the resume-path span `other than its own carrier's verified fire` and the closeout span `still armed or still loaded`), naming the canonical Budget gate section as the resume-path duty's home and the `Terminal closeout ownership` paragraph of worktree-first.md as the closeout duty's home [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/review-loop/SKILL.md`'s budget-gate paragraph, add one dated recorded exclusion line instead of a discharge clause: review-loop owns no watcher state and holds no `armed_launchd` receipt (its carrier is the resume automation its clean-probe arm already deletes), so the carrier discharge duty does not apply in this home; the existing clean-probe own-carrier deletion arm is preserved [class: IMPLEMENTATION_REQUIRED]
- [ ] Cite the origin row in exactly one dated line per touched skill file [class: REPOSITORY_TEST]
- [ ] Commit: `docs: budget-resume carrier discharge duty in resume and closeout arms` [class: IMPLEMENTATION_REQUIRED]

### Task 8: the read-only carrier census consult in the maintenance survey

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `budget-resume carrier census` in `agents/skills/maintenance/survey-arms.md`

- [ ] Add a failing span pin to `scripts/check_maintenance_pins.sh`: extract the census arm's own bullet from survey-arms.md (not the whole consult set) and pin the arm-name token `budget-resume carrier census`, the read-only token beside it, the no-reaper span `removed only under operator direction`, and `consultative finding` scoped inside the new bullet [class: REPOSITORY_TEST]
- [ ] Run the pins suite, expect RED on the census-arm pin while every pre-existing pin stays green [class: REPOSITORY_TEST]
- [ ] Add the census consult arm to the consult set: run the census operation once per survey turn, invoked as the census operation with `--repo-root` and no `state_path` (the sibling clocked-order consult's invocation shape; the census dispatch branch requires no authoring state; repo-local script resolution first, then the deployed home copy) [class: IMPLEMENTATION_REQUIRED]
- [ ] State the census arm's reporting shape: one row per carrier (label, loaded state, sentinel/fired state read from the runtime root `~/.ai-playbook/runtime/`, where sentinels and their `.fired` markers live beside the job dirs), sharing the survey's guard and fail-open semantics (a tool error is a reported consultative finding, never a blocked turn) [class: IMPLEMENTATION_REQUIRED]
- [ ] State the census arm's posture in the same bullet: read-only, never repairs, and the no-reaper rule that a stale foreign carrier is named for operator direction and removed only under operator direction [class: IMPLEMENTATION_REQUIRED]
- [ ] Cite the origin row in one dated line; run the pins suite and the hygiene scan, expects exit 0 on both with the same conditional-adjustment rule, and record the byte-budget gate output in the run log [class: REPOSITORY_TEST]
- [ ] Commit: `docs: read-only budget-resume carrier census consult in the survey` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

The review loop closed at its configured round cap (r5, the certification round) under the operator's 2026-11-07 direction to resume and complete; every staged finding of the cap round carries its disposition below, each with its pattern id, and none remains open.

- security#supersede-teardown-ownership-unverified: folded (the shared core gained the discharge's ownership gate; each supersede call site refuses a mismatched live payload with carrier-mismatch-retained)
- implementation#missing-producer-for-consumed-field: folded (the fired history event's retention is now its own implementation bullet, and the discriminator is the per-install `watcher_id` alone, which the event already records)
- security#supersede-teardown-unserialized: folded (the shared core gained a per-caller lock parameter; each call site runs no leg when the lock yields `False`)
- consistency#goal-vs-mechanism: folded (the same retention bullet and the Watcher-fire term now use this-plan-adds tense)
- testing#coverage-claim-unchecked: folded (the census's sentinel-only source filters by sentinel name and the co-tenant test row covers a clocked-order sentinel pair)
- testing#missing-gate-needle: folded (the standing constraint now states exactly what the lock tests prove on each side)
- simplification#delete: folded (the epoch left the discriminator; `watcher_id` alone is arm-unique)
- architecture#leaky-payload-concern: folded (the segment rides a dedicated request key the scheduler appends after the manual command; report-only fall-throughs stay clean)
- consistency#stale-cross-reference: folded (the mirror clause names each duty's own home)
