# Plan: D-17 false terminal stop durable scenario suite

Backlog origin: docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md
Authoring claim: 2026-10-31-maintenance-cycle-gate-scenario-test.md (session sess_56d4cac8-82d5-4fbf-88b4-9fc36ebe6f8d)
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-maintenance-d17-false-terminal-stop-p1bd66ad3-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: no

## Terms

- **D-17**: the operator directive (docs/maintenance/operator-directives.md) to continue eligible maintenance picks without user turns; context-management stops clear with a dated trace, explicit user-paced directives stop, and the quota pause, empty queue, and explicit stop request remain terminal.
- **Cycle gate**: the maintenance scheduler state's `authoring_cycle_gate` pacing record and the SKILL.md section that decides when a run stops for a user action between cycles.
- **Continue-loop condition**: the decisions.md paragraph (condition home) that clears a context-only armed gate, stops on an explicit user-paced gate, and continues the loop while its four legs (quota, locks, guards, dispatchable target) hold.
- **Blocker recovery**: the decisions.md paragraph giving any non-user-only blocker one `self-heal` consultation before a stop is judged unrecoverable or the operator is asked.
- **Non-user-only blocker**: a routine guard refusal, failed tool, or unclear remedy, as opposed to a user-only decision (missing authority, ambiguous ownership, unsafe target, external-owner action, explicit operator stop), which stays blocking outside the consultation.
- **Terminal outcome**: a sanctioned end of the maintenance loop: explicit current stop request, empty eligible queue, primary quota pause, or user-only safety or authorization hold.
- **Scenario-agreement pin**: a region-scoped assertion on the operative clause bytes of one prose decision surface, following the frozen-span suite convention (scripts/test_claimed_target_skip_and_continue.py), kept durable per development_lessons.md #303 so the next fold over the same sites re-runs one scenario through every touched site.
- **Guard composition**: driving the repository's executable decision cores (quota probe, dispatch admission, rearm classification) with scenario fixtures to derive the inputs a real maintenance turn consults, without modifying those scripts.
- **Conservative verdict**: the dispatch-admission refusal class that treats an underivable or empty owned-path set as intersecting (the deferral input the loop records).
- **Lane decision**: the maintenance loop's normal per-pick guarded decision (guards, quota, admission, dispatch) that a continuation resumes into instead of stopping.
- **Pins suite**: scripts/check_maintenance_pins.sh and its region-scoped operative-token pin convention; the existing cycle-gate pin rows over the same SKILL.md section are its adjacent witness, and this plan's receipt rejects pins-only as insufficient while mirroring its re-pin-on-rewrite convention.

## Why

The D-17 termination and continuation behavior exists only as prose, and a 2026-11-07 Codex maintenance run ended after an unsupported blocker disposition while dispatchable work remained; the repository suite has no durable witness over that behavior (review finding F2, deferred 2026-10-31), so a later instruction edit could restore a false terminal stop while every phrase-level check stays green.

## Gist & Examples

TLDR: Land a test-only scenario suite that pins the D-17 continuation decision mapping across its prose decision surfaces and composes the scenario's guard inputs from the executable decision cores, closing the witnessed false-terminal-stop regression gap; driving force: automation.

Before: no durable check exercises the continuation behavior; the maintenance pins suite carries no D-17 pins, and the only prior assertions were run-specific phrase scans, so an instruction edit restoring a context-only stop or dropping the blocker consultation requirement goes undetected and an unattended run strands authorized work, as witnessed on 2026-11-07.

After: one focused pytest suite asserts, for each scenario (routine blocker with eligible work remaining, autopilot context-only gate, explicit user-paced gate, and each preserved terminal), that every owning prose site maps the scenario to the same outcome, and derives the scenario's quota, admission, and rearm inputs from the real decision scripts with fixtures; an edit that breaks a mapped clause turns the suite red in the normal focused run.

Edge cases: the preserved terminals (explicit stop request, empty eligible queue, primary quota pause, user-only blocker) each keep a pinned stop clause and, where an executable surface exists, a fixture verdict; a sanctioned clause rewrite re-pins the suite and the adjacent pins-suite rows in the same change (scripts/check_maintenance_pins.sh carries cycle-gate section pins beside this suite's frozen spans), mirroring the existing pins-suite convention.

## Outcome

The maintenance loop's D-17 termination and continuation contract gains a durable, test-only behavior witness that fails when a decision surface stops mapping a scenario to its mandated outcome.

- A focused suite walks one scenario table through every owning prose site (decisions.md, SKILL.md, operator-directives.md, template-authoring.md) and asserts one outcome per scenario per site.
- The same suite derives the scenario's quota, admission, and rearm inputs from the executable decision cores with fixtures, grounding the scenario in realistic maintenance context.
- The suite adds no production change, no prose edit, and no new gate, validator, lock, ledger, or dispatch-pausing condition.
- Residual witness posture, recorded deliberately: the terminals without an executable surface (explicit stop request, empty eligible queue, user-only blocker) are witnessed by region-scoped clause pins only, because no executable surface exists for them and the origin forbids a runtime API; the receipt for the rejected LLM runner covers this residual.

Gate delta: none; no refusal class, gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; the plan adds one test file and edits no production or prose surface, and the origin row's acceptance criteria sanction the test-suite-only posture explicitly.

## Assumptions

- assume the intended D-17 behavior already exists in prose and this plan edits no instruction file; basis: the origin row's Problem section states the current instructions already state the intended behavior, and the operative clauses were verified 2026-11-07 at decisions.md Blocker recovery and continue-loop condition, SKILL.md Cycle gate, and operator-directives.md D-17.
- assume the frozen-span suite shape is the repository's durable witness convention for prose-defined behavior; basis: scripts/test_claimed_target_skip_and_continue.py (region-scoped operative-token pins inside the owning bullet span) and the same-scenario agreement doctrine in docs/maintenance/development_lessons.md #303.
- assume the three consulted scripts keep fixture-driven public callables and the suite modifies none of them; basis: existing fixture suites scripts/test_quota_window_probe.py, scripts/test_dispatch_admission.py, and scripts/test_rearm_on_touch.py each already drive their script in-process or through its CLI with tmp_path fixtures.
- Decision receipt (maintenance-selected arm), harness choice: scenario-agreement frozen spans plus executable guard composition, recorded as the best-supported in-scope option; rejected alternative: additional pin rows in scripts/check_maintenance_pins.sh, because that suite carries no D-17 pins today (grep count 0 over the suite, 2026-11-07) and review finding F2 explicitly rejects phrase-presence assertions as the durable witness; rejected alternative: an LLM-driven scenario runner, because the repository's suites are hermetic and the origin forbids inventing a runtime API; simpler-design comparison recorded, proceeding under standing authorization.
- Decision receipt (maintenance-selected arm), scope shape: one new test file owning both the prose-scenario pins and the fixture composition; simpler than a two-file split because both layers assert one scenario table, and the seam rule keeps same-file work in one plan.
- Sources inspected: the origin row docs/history/backlog/2026-10-31-maintenance-cycle-gate-scenario-test.md; review finding F2 in .ai-playbook/reviews/2026-10-31-maintenance-autopilot-continuation-code-review-r1.md; the completed continuation plan docs/history/plans/completed/2026-11-02-maintenance-codex-continuation.md; docs/maintenance/operator-directives.md (D-17); agents/skills/maintenance/SKILL.md (Cycle gate, Invariants, Integration Points self-heal entry); agents/skills/maintenance/decisions.md (Blocker recovery; continue-loop condition); agents/skills/maintenance/template-authoring.md (FINAL STEP); scripts/test_claimed_target_skip_and_continue.py; scripts/check_maintenance_pins.sh; scripts/test_quota_window_probe.py; scripts/test_dispatch_admission.py; scripts/test_rearm_on_touch.py; the 2026-11-07 repository survey of scripts/test_*.py conventions.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every pinned span matches the owning surface's current operative clause bytes verbatim, region-scoped so a hit elsewhere cannot satisfy the pin; every fixture verdict comes from the real script callable, never a test-local reimplementation.
- regression sensitivity: removing or rewriting any pinned operative clause, or remapping a scenario's outcome at any owning site, fails the focused suite.
- maintainability: a sanctioned clause rewrite re-pins the suite in the same change (the pins-suite convention), and the scenario table stays one readable structure.

**Done when:**
- the focused suite passes through the repository's pytest collector command; the plan readiness pre-round gate and the hygiene scan exit 0.

**Ship when:**
- none; test-only local workflow behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none; this plan adds a test-only suite and changes no production surface.

**Tests:**
- scripts/test_maintenance_d17_continuation_scenarios.py (Task 1) *(new)*

**Pin sources (review-only; the suite asserts against their current bytes):**
- agents/skills/maintenance/decisions.md (Blocker recovery; continue-loop condition) (review-only)
- agents/skills/maintenance/SKILL.md (Cycle gate; Integration Points self-heal entry) (review-only)
- docs/maintenance/operator-directives.md (D-17 directive clause; D-6 active quota-pause clause as the quota terminal's surviving home) (review-only)
- agents/skills/maintenance/template-authoring.md (FINAL STEP D-17 application and chaining guard) (review-only)
- scripts/quota_window_probe.py (review-only) consulted through its public callable
- scripts/dispatch_admission.py (review-only) consulted through its public callable
- scripts/rearm_on_touch.py (review-only) consulted through its public callable

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- edits to any prose decision surface (agents/skills/maintenance/*, docs/maintenance/operator-directives.md); the clauses already state the behavior and the origin sanctions a test-only posture; reason: prose growth is priced by the skill text anti-growth rules and no witnessed defect in the prose itself.
- new gates, validators, locks, ledgers, runtime continuation primitives, or dispatch-pausing conditions; reason: machinery admission protocol and the origin's acceptance criteria.
- modifications to the consulted decision scripts; reason: the suite consumes their public callables, and script changes would widen the blast radius beyond the witness gap.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-07-maintenance-d17-false-terminal-stop.md ) || exit $?
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_d17_continuation_scenarios.py -q ) || exit $?
( cd "$REPO" && bash scripts/scan-public-hygiene.sh --files scripts/test_maintenance_d17_continuation_scenarios.py ) || exit $?
```

### Task 1: Scenario-agreement pins over the D-17 decision surfaces

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/test_maintenance_d17_continuation_scenarios.py` *(new)*

Primary class anchors:
- `MaintenanceD17ScenarioAgreementTest` in `scripts/test_maintenance_d17_continuation_scenarios.py`

- [ ] Scenario table, blocker leg: a routine blocker or no-op disposition with another eligible pick present is pinned to its mandated outcome, one self-heal consultation then the normal guarded lane decision, never a terminal stop [class: REPOSITORY_TEST]
- [ ] Scenario table, context-gate leg: an autopilot run finding the gate armed only for context management is pinned to clear with the existing dated trace, record the D-17 disposition, resume the normal lane decision without a prompt [class: REPOSITORY_TEST]
- [ ] Scenario table, user-paced leg: an explicit user-paced directive gate is pinned to readiness report and stop until a real user directive clears it [class: REPOSITORY_TEST]
- [ ] Scenario table, terminals leg: the four preserved terminals (explicit stop request, empty eligible queue, primary quota pause, user-only blocker) are each pinned to stop or hold with their owning clause [class: REPOSITORY_TEST]
- [ ] Pins are region-scoped with a span mechanism prescribed per surface shape: bullet-line spans use the precedent's line-prefix helper (scripts/test_claimed_target_skip_and_continue.py); heading-scoped clauses (decisions.md paragraphs, SKILL.md sections, operator-directives.md directive blocks) use an explicit heading-to-heading or paragraph-index extraction [class: REPOSITORY_TEST]
- [ ] A pin asserts against the extracted span, never the whole-file text, and list-bullet clauses use the bullet-prefix span helper keyed on the clause's leading token, so a hit outside the owning span cannot satisfy a pin [class: REPOSITORY_TEST]
- [ ] The agreement matrix is scenario-to-sites keyed: the blocker leg pins at decisions.md Blocker recovery and the SKILL.md Integration Points self-heal entry; the context-gate, user-paced, and empty-queue legs pin at decisions.md continue-loop condition, SKILL.md Cycle gate, operator-directives.md D-17, and template-authoring.md FINAL STEP; the quota terminal pins at the D-17 preserve clause and the D-6 active quota clause [class: REPOSITORY_TEST]
- [ ] The terminals matrix completes the keyed agreement: the explicit-stop-request terminal pins at SKILL.md Cycle gate and the D-17 preserve clause; the user-only-blocker terminal pins at decisions.md Blocker recovery; the quota and empty-queue terminals are keyed in the row above [class: REPOSITORY_TEST]
- [ ] Each scenario is asserted only over the sites that own it, and a site that stops mapping its listed scenario fails the suite [class: REPOSITORY_TEST]
- [ ] Hygiene self-check: before pinning, the pinned spans and fixture strings are checked against the deny patterns and the hygiene-scan report output must list zero hits for the new file; a reported hit is treated as a failure even though the scan's exit code stays 0 for tracked files outside agents/skills [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the operative clauses exist today; the suite is a regression witness, so the first run passes and its value is detection of future clause edits (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin D-17 continuation scenario agreement across decision surfaces` [class: REPOSITORY_TEST]

### Task 2: Executable guard composition with fixtures

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/test_maintenance_d17_continuation_scenarios.py`

Primary class anchors:
- `MaintenanceD17GuardCompositionTest` in `scripts/test_maintenance_d17_continuation_scenarios.py`

- [ ] Quota leg fixture: the pure `evaluate_pause` core of scripts/quota_window_probe.py is driven in-process the way scripts/test_quota_window_probe.py drives it, returning the continue input under a fixture with quota headroom and the pause verdict under a fixture at the quota wall [class: REPOSITORY_TEST]
- [ ] Quota leg isolation: the host-touching surfaces (run_probe, probe_zcode, write_flag_if_paused defaults, any ~/.zcode config read, the budget-guard flag or lock write, any network transport) are forbidden, with fixture data injected and any transport faked, mirroring the existing suite's credential-read guard [class: REPOSITORY_TEST]
- [ ] Admission leg fixture: the dispatch admission consult (scripts/dispatch_admission.py `check_admission`, driven the way scripts/test_dispatch_admission.py drives it) returns a pass for the scenario's disjoint eligible pick and the conservative verdict for an intersecting outstanding run, grounding the deferral input the loop records [class: REPOSITORY_TEST]
- [ ] Rearm leg fixture: the rearm classification in scripts/rearm_on_touch.py is driven the way scripts/test_rearm_on_touch.py actually drives it (in-process module import for classification seams, subprocess or main() with a tmp_path root for the CLI shape; call signatures taken from the source), returning the armed-parent verdict for a fixture state file plus listing whose recorded parent is present and enabled, the loop-liveness input the continue-loop condition presumes [class: REPOSITORY_TEST]
- [ ] No consulted script is modified: the task's diff touches only the suite file, and each fixture verdict asserts the scripts' real outputs [class: REPOSITORY_TEST]
- [ ] Hermeticity constraints: every fixture state file, manifest, listing, and root lives under pytest tmp_path; no leg reads or writes repo-relative defaults (the rearm state path, live authoring claims, the live scheduler state) or inherits ambient environment; a subprocess leg copies the precedent's env hygiene explicitly [class: REPOSITORY_TEST]
- [ ] Cross-layer binding: each fixture leg asserts its derived verdict is the input the pinned prose clause names for that scenario leg (quota pause vs continue, admission pass vs conservative deferral, armed-parent liveness), so the composition layer tests the scenario's composition and not the consulted scripts' already-covered behavior [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [ ] Commit: `test: compose D-17 scenario guard inputs from executable decision surfaces` [class: REPOSITORY_TEST]
