# Plan: execute-plan dispatch failure resilience

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-subagent-followup-model-capacity-failure.md`

Driving force: reliability (three witnessed 2026-10-05 dispatch failures in one live execution: a follow-up to the done sub-agent failed at dispatch with a model-capacity error after the task commit landed, stranding the lock release and closeout report until the parent took over by hand; a review panel launched three of five lenses before the next spawn failed with an agent-thread-limit error; and a round-five worker failed before starting with a model-capacity error producing no work at all - in all three the provider error carried no automatic fallback and no typed continuation state, so the parent had to improvise the recovery from raw error text)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-execute-plan-dispatch-failure-resilience-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Pre-start dispatch failure: a worker launch that fails before the worker runs any step (provider capacity refusal, agent-thread-limit refusal, rate-limit refusal at dispatch); no worker state, claim, or work product exists, so recovery is a launch-side matter and never a review finding or a task failure.
- Follow-up dispatch: a continuation task sent to an existing worker thread (the done sub-agent's remaining closeout steps, a worker-slot reuse); its pre-start failure strands whatever the thread already completed, which the parent must adopt.
- Dispatch-failure record: the typed manifest line this plan defines, extending the existing `pre_restart:` free-text convention: `dispatch_failed: <ISO timestamp> <worker role> <reason code> pre-start` plus the already-mandated `pre_restart:`/`pre_restart_paths:` pair when a relaunch follows.
- Reason code: the closed four-value set this plan pins for the record: `model-capacity`, `thread-limit`, `rate-limit`, and `other` (provider text quoted); the first three name the witnessed provider shapes and `other` keeps the record total.
- Partial panel: a Phase 3 lens panel where some required lenses launched and some failed pre-start; the launched workers' work stands, the round is not invalidated, and the missing lenses are a resumable set; the round's required-lens set is the round's own per Step 3.1 (the five-worker fresh-adversarial panel plus the risk-signal floor on initial passes, the focused selection on post-fix rounds).
- Lens resume: relaunching the refused lenses after the fan-out backoff, or reusing a completed worker slot via follow-up where the host supports it, until the panel selection's required lenses are all launched or the bounded-retry budget escalates.
- Bounded-retry budget: the per-failure retry allowance this plan pins (three launch attempts per failed worker role per boundary across backoff waits before escalation), riding the Fan-out shaping rule's existing backoff.
- Takeover: the parent completing the stranded steps in its own session after a follow-up dispatch failure, per the done skill's own Step 6 and Step 7 duties, which remain the parent's obligations regardless of which session executes them.

## Why

The dispatch-mode paragraph already owns the cheapest shape - a refused background spawn is a cheap retry after backoff - and the pre-restart record already owns the state snapshot a restart worker verifies. What the three witnesses add is the rest of the failure surface: a follow-up dispatch failure after the task commit strands the closeout boundary with no typed record and no named takeover procedure, a partially launched panel has no resume contract so the orchestrator improvises from the provider error text, and nothing pins the reason vocabulary or the retry budget, so every failure shape produces a fresh improvisation. The fix is one contract over the failure surface the skill already half-owns: typed records for every pre-start failure, an actionable continuation per failure class, and a resumable partial panel.

## Outcome

- Every pre-start dispatch failure lands as a typed record with a reason code from the closed set, and the parent's continuation is a named procedure per failure class: spawn refusal retries within the bounded budget, follow-up failure after a commit triggers the lock check and the parent-owned takeover of the stranded closeout steps, and no failure shape is ever a silent retry loop, a review finding, or a task failure.
- A partially launched panel is a first-class resumable state: the launched set and the refused set are recorded, the refused lenses resume after backoff or via completed-slot reuse where the host supports it, the round proceeds on the panel selection's tier rules, and escalation past the retry budget is a named outcome rather than an invalidation of the launched work.

Gate delta: one new typed manifest line (the dispatch-failure record with its closed reason-code set), one named retry budget, and one resumable-state contract for partial panels. All are report-and-continuation duties over the manifest and dispatch flow the skill already owns; no existing mechanism weakens: the dispatch-mode default, the Fan-out shaping rule's backoff, the pre-restart record pair, the `run_address_fanout` entrypoint's ownership, and the done skill's Step 6 and Step 7 obligations all keep their semantics.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the row's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the plan contracts orchestrator behavior in skill text only, with no runtime driver change; basis: the witnessed failures are provider-side dispatch errors the host surfaces to the orchestrating session, the dispatch-mode paragraph and the pre-restart record convention are skill-text machinery, and the origin row's Why-not-fixed-now names shared orchestration tooling rather than the driver's claim machine.
- assume retrying on a compatible different model is recorded as a sanctioned option where the host supports model selection, never an obligation; basis: the origin row's Expected says retry on a compatible available model or return a typed failure, and model availability is host state the skill cannot inspect, so the contract records the option and the typed fallback rather than mandating a host capability.
- assume the three-attempt retry budget counts launch attempts per failed worker role per boundary, matching the prelaunch-reclaim budget's shape (initial plus bounded retries then a named escalation); basis: the skill already pins a two-attempt prelaunch-reclaim budget with a named cap outcome, and the same shape keeps the new budget recognizable.
- assume completed-slot reuse via follow-up is recorded as host-conditional (used where the host supports follow-up tasks to completed threads, per the witnessed thread-limit remedy); basis: the origin row's own evidence names it as the witnessed safe continuation, and slot semantics are host state.
- assume the takeover path adds no new lock semantics: the parent's lock check rides the done skill's existing status-then-takeover rules (a free lock allows the parent to continue; a held lock blocks), and the takeover itself executes the existing Step 6 and Step 7 duties; basis: the witnessed recovery showed exactly this shape, and the row asks for preserved continuation state, not new lock mechanics.
- assume Task 2's escalation anchor tracks the wave boundary's probe record as it exists when this plan executes: the `wave_boundary_probes` manifest line today, superseded by the wave-budget-receipt line once the landed sibling plan execute-plan-review-wave-contract-gaps executes (its Task 1 owns that supersession); basis: the sibling is landed but unexecuted, both plans edit the Phase 3 round procedure region, and this plan is strictly sequenced after the sibling's execution by that shared-region dependency.
- assume the partial panel's required-lens set is the Phase 3 panel's own requirement (the five-worker fresh-adversarial panel plus the risk-signal floor), not the Step 1.2b intermediate-review tier table; basis: the witnessed failures are Phase 3 panel launches, and the tier table governs the intermediate pass.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: every pre-start dispatch failure becomes a typed record with a named continuation, and a partially launched panel becomes a resumable state instead of an improvisation.

Before (today): a follow-up to the done sub-agent fails at dispatch with a model-capacity error after the task commit landed; no record names the failure, so the parent hand-inspects the lock and improvises the takeover. A panel launches three of five lenses and the fourth spawn fails with a thread-limit error; nothing records the partial state, and the orchestrator reasons from the raw provider text. A round-five worker fails before starting; the round's fate is undocumented.

After (this plan): the failure lands as `dispatch_failed: <timestamp> done-worker model-capacity pre-start` in the session manifest, the parent runs the named follow-up-failure procedure (lock check, parent-owned completion of the stranded Step 6 and Step 7 duties), and the record joins the pre-restart pair. A partial panel records its launched and refused lens sets, resumes the refused lenses within the three-attempt budget (backoff, or completed-slot reuse where the host supports it), and escalates as a named outcome that leaves the launched work standing.

Edge cases pinned: a failure with provider text matching none of the three reason codes records `other` with the text quoted; a retry that succeeds closes the failure with a relaunch note rather than erasing the record; a follow-up failure before the thread's commit lands takes the spawn-refusal path (nothing is stranded); a panel whose refused lenses exhaust the retry budget escalates as a named outcome and the launched lenses' findings still triage; a takeover finds the lock held and reports blocked per the done skill's status rules instead of bypassing; a pre-start failure is never recorded as a review finding, a task failure, or a worker error in any staging surface.

## Tasks

### Task 1: Typed dispatch-failure records and the follow-up takeover procedure

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the new pins row below and regression: no pinned span breaks
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-05-execute-plan-dispatch-failure-resilience.md`; structural gate

- [x] Skill text, typed records: the dispatch-mode paragraph of agents/skills/execute-plan/SKILL.md extends its failure surface: every pre-start dispatch failure (spawn or follow-up, before the worker runs any step) is recorded in manifest.md as a `dispatch_failed: <ISO timestamp> <worker role> <reason code> pre-start` line with the reason code from the closed set `model-capacity`, `thread-limit`, `rate-limit`, `other` (provider text quoted for `other`), alongside the existing `pre_restart:`/`pre_restart_paths:` pair when a relaunch follows; a successful retry closes the failure with a relaunch note and never erases the record; a pre-start failure is never recorded as a review finding, a task failure, or a worker error in any staging surface [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, retry budget: the same region pins the bounded-retry budget (three launch attempts per failed worker role per boundary across the Fan-out shaping rule's backoff waits, mirroring the prelaunch-reclaim budget's named-cap shape); exhausting the budget is a named escalation outcome reported in the turn, and retrying on a compatible available model is recorded as a sanctioned option where the host supports model selection, never an obligation [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, follow-up takeover: the done-handoff region of agents/skills/execute-plan/SKILL.md gains the follow-up-failure procedure (primary home the Step 1.4 region, with a one-line cross-reference at Hard Gate 4's list entry): when a follow-up dispatch to a worker thread fails pre-start after that thread completed its commit, the parent runs the lock check per the done skill's status rules, and with the lock free completes the stranded closeout steps in its own session (the done skill's Step 6 release and Step 7 report duties stay the parent's obligations regardless of which session executes them), recording the takeover beside the dispatch_failed line; a held lock reports blocked instead of bypassing; a follow-up failure before the thread's commit lands takes the ordinary spawn-refusal path [class: IMPLEMENTATION_REQUIRED]
- [x] Template citation: the subagent-prompts.md shared worker contract's pre-restart line region gains the matching sentence: a restart prompt after a recorded dispatch failure names both the pre-restart record and the dispatch_failed line so the restart verifies the orphaned state and the failure history from disk [class: IMPLEMENTATION_REQUIRED]
- [x] Pins witness: the same edit adds a pins row over the `dispatch_failed:` line literal (the operative sentence of Task 1's first checkbox) in scripts/check_maintenance_pins.sh, the repository's established witness class for skill-text contracts, satisfying the origin row's pin clause for the worker-follow-up failure shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: pre-start dispatch failures land as typed records with named continuations` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Resumable partial panels

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-05-execute-plan-dispatch-failure-resilience.md`; structural gate

- [x] Skill text, partial-panel state: the Phase 3 round procedure of agents/skills/execute-plan/SKILL.md gains the partial-panel rule: when some of a panel's required lenses launch and others fail pre-start, the round is a resumable partial panel, not a failed round - the session manifest records the launched set and the refused set (per lens, beside each dispatch_failed line), the launched workers' work stands and triages normally, and the refused lenses resume after the fan-out backoff or via completed-slot reuse where the host supports follow-up to completed threads; the round's required-lens set is the round's own per the Step 3.1 gate (the five-worker fresh-adversarial panel plus the risk-signal floor on initial passes, the focused selection on post-fix rounds), not the Step 1.2b tier table [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, resume completion and escalation: the same region pins the completion condition: the round proceeds when every lens the round's required-lens set requires (per the Step 3.1 gate: the five-worker panel plus risk-signal floor on initial passes, the focused selection on post-fix rounds) is launched or its refusal has exhausted the bounded-retry budget and escalated as a named outcome recorded beside the wave boundary's probe record (the `wave_boundary_probes` manifest line as this plan lands it; the sibling landed plan execute-plan-review-wave-contract-gaps supersedes that line with the wave-budget-receipt when it executes, and the anchor moves with it); an escalated round never invalidates the launched lenses' findings, and the escalation names the missing lenses so a later boundary (or the operator) can complete the panel deliberately; the same edit gives the Step 3.1 verification gate's panel-ran item the partial-panel arm (an escalated round records its launched and refused sets and proceeds to triage); Task 1's pins row over the shared `dispatch_failed:` record literal is the origin pin clause's witness for both failure shapes, this panel-launch half included [class: IMPLEMENTATION_REQUIRED]
- [x] Template guidance: the subagent-prompts.md Review lens worker fan-out guidance region gains the matching sentence: a lens launch refusal is a pre-start dispatch failure recorded per the dispatch-mode paragraph, never a lens verdict, and the worker slot it would have occupied stays reusable for the resumed launch [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: partially launched review panels record and resume their missing lenses` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `agents/skills/execute-plan/SKILL.md`, `agents/skills/execute-plan/subagent-prompts.md`, `scripts/check_maintenance_pins.sh`.

Reviewers judge: fail-closed preservation (the dispatch-mode default, the Fan-out shaping rule's backoff, the pre-restart record pair, the `run_address_fanout` entrypoint's ownership, the prelaunch-reclaim budget's shape, and the done skill's Step 6 and Step 7 obligations keep their semantics), the record contract's coherence with the existing manifest line conventions (one typed line format, one closed reason-code set, no second state home), the takeover path's lock safety (status-then-act, never a bypass), the partial-panel rule's coherence with the tier-based panel selection and the wave receipts, scope discipline (no task reaches beyond its Files list), and contract honesty (the Evidence blocks claim only gates and pins this repository can actually run, with no fictional unit tests for agent-behavior text).

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-dispatch-failure-resilience.md
```
