# Plan: archive rider sweep-ordering report arm

Backlog origin: docs/history/backlog/2026-11-07-archive-ceremony-exec-review-record-gap.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-archive-rider-sweep-ordering-p856ffcb7-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: 2026-11-07-archive-ceremony-exec-review-record-gap.md (session sess_8f7f3dc8-57f5-4de4-876a-85293a5c788b)
Executed: yes (4ab896e12f33543b973b9a3deab68a25f8038efa)

Design input (prose only, never a Backlog origin): the PLAN-PROMPTS entry `archive-rider-sweep-ordering` in docs/history/backlog/PLAN-PROMPTS.md routes this item; its scope arms, urgency, and rejected alternatives are adopted here. The origin row is the incident witness.

## Terms

- Archive rider: a commit that lands an archived-plan surface (the plans-completed move, its ownership-registry row, or a rider edit to an archived twin) after the closeout sweep that should have accepted it; witnessed as fef5ebd2a (2026-11-07 01:36 UTC), the last commit of the plan-readiness-planned-path-lifecycle run.
- Archive-ceremony gate: the EXISTING landing-sweep gate `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py` (registry name `archive-ceremony`); it accepts an archive through two routes: a `*-plan-review-<slug>-exec-r<N>` filename-series record under the reviews home, or a bound review receipt whose sidecar binds the plan identity, the reviewed-bytes digest, and a yes verdict. The gate is correct and stays acceptance-identical.
- Owning closeout: the boundary at which the run that produced the archive reports complete (the done closeout's finalize tail); the last point where that run can still observe its own archive.
- Post-landing archive-ceremony report arm: the origin row's Suggested correction arm 1 (the row's post-rider re-sweep): after the archive surface lands, the owning closeout re-runs the archive-ceremony gate over the landed state and reports the finding instead of staying silent.
- Landing sweep: the pre-commit gate battery the done commit transaction runs over the staged set (the battery whose archive-ceremony member reds on an in-range archive). Closeout-side report step: the finalize-side step where the missing-review-record scan lives, after both locks release; the report arm wires into that step.
- Run manifest span: the diff range the archive derivation enumerates from the owning run's run manifest, start commit through the evaluated head (the derivation's shape families; shape (b) is the committed-archive shape that ranges over the run manifest's start commit and is the family the report arm exists to cover).
- Transfer-in copy: the reviews corpus transferred into the run worktree at setup; partial by construction (development lesson 74), which is why the report arm re-roots only the corpus at the primary reviews home.
- Missing-review-record scan: the EXISTING report-only finalize scan over archived plans' cited review records (the `cmd_finalize` composition in `scripts/done_run.sh`); it checks cited-record existence, not the archive-ceremony binding grammar; the report arm rides beside it and never replaces it.
- Primary writer: the next session whose primary-commit landing sweep runs after the archive lands; the writer whose checkout-wide red the report arm pre-empts with an owning-run report.
- Phase 0 freeze: the authoring session's entry-freeze log write at authoring start; the witnessed blocked-writer class the origin row records (two freeze writes blocked within minutes on 2026-11-07).
- Machinery registry: `scripts/machinery_registry.json`, the machinery admission protocol's row ledger (entries carrying disposition, paths, tests, witness, and note); `scripts/machinery_inventory.py --check` validates it.
- Range provenance: whether a surfaced archive lies inside this run's manifest span or was landed by a prior run; the two provenance classes the Task 4 finding message names.
- Pinned hybrid context: the report arm's evaluation context: the reviews corpus re-rooted at the primary reviews home only; repo_root, every git surface, and the span evidence stay at the running checkout.
- Primary reviews home: the primary checkout's gitignored `.ai-playbook/reviews/` directory, the shared corpus where acceptance evidence lives.
- Could-not-evaluate: the arm's distinct non-evaluated outcome line (an unresolvable span boundary, a derivation blocker, or an arm failure of its own); never a pass-shaped clean line.
- Warning-only arm: a check that reports its finding and never refuses; promotion to blocking runs only through the machinery admission protocol's pre-registered criteria after a true catch.

## Why

Since the witnessed rider fef5ebd2a landed after its own closeout sweep had passed, an archive surface can reach main without any sweep ever accepting it: the archive-ceremony gate then reds checkout-wide on the primary writer's landing sweep, and two authoring sessions' Phase 0 freeze writes were blocked on that red within minutes of each other on 2026-11-07 (the origin row records both catches). The run that owned the archive reported complete before the red existed, so the defect always surfaces on a writer that owns nothing about the archive. The completion passes already carry prose duties aimed at this shape (the plans skill's commit-then-inspect archive-egress check and execute-plan's pre-archive pointer record), and both witnessed runs skipped them; the report arm's value is mechanical, script-enforced enforcement that a skipped prose duty cannot reproduce, and this plan records that reconciliation here.

## Gist & Examples

TLDR: the run that lands an archive surface re-runs the existing archive-ceremony gate over its own landed state at its owning closeout and reports the finding there instead of staying silent, naming code-quality as the driving force.

Before (today): the plan-readiness run's closeout sweep passed, its archive rider landed last, and the primary writer (an authoring session's Phase 0 freeze) hit the checkout-wide archive-ceremony red with no run owning the repair; the same shape repeated for the authoring-continuation-owner-attribution archive about eight hours later.

After (this plan): the owning closeout evaluates its own archive after the archive surface lands and reports the archive-ceremony finding in its own completion output (warning-only first), so the gap between the archive landing and the primary writer's red closes at the boundary that owns the archive; the finding names whether the archive came from this run's manifest span or a prior run.

Example: a run lands an archived plan whose execution round record is code-review-kind (no `-plan-review-` infix, no binding sidecar); its post-landing report arm reports the archive-ceremony finding at the closeout with the failing route and the repair producer named, instead of the primary writer's sweep failing first.

Edge cases: an archive that passes the gate's two acceptance routes reports clean and the closeout proceeds unchanged; a red found by the report arm is report-only under this plan's posture (no refusal, no known-red ledger), with the promotion criteria and review date pre-registered in the machinery registry row this plan adds; when neither the owning run manifest nor ORIG_HEAD resolves as the span boundary, the arm reports a distinct could-not-evaluate line, never a pass-shaped clean line; an arm failure of its own (facts resolution, gate exception) emits the neighboring scan's fail-open warning posture and never blocks the closeout; the stale complete-but-undispositioned manifest class the row's arm 4 prices already has its disposition route (the setup classification's finalize-manifest remedy, exercised 2026-11-07) and self-heals on the window shift the origin row records, so no build lands for it; the producer write-time check arm (row arm 2) is deferred out of this plan's scope and stays priced by the origin row; the pointer half of the row's message-text arm (open blocker rows) stays priced by the origin row too, the plan's finding line naming the repair producer instead of tracking-row pointers.

## Outcome

The owning closeout observes its own archive before reporting complete, so an archive rider can no longer land silently red: the owning run reports the archive-ceremony finding itself before the primary writer's sweep reds, while the arm stays report-only (the block itself is prevented only after the pre-registered promotion criteria are met by a true catch).

- Gate delta: one warning-only post-landing archive-ceremony report arm is added at the owning closeout boundary (a new checked surface, priced by the origin row's completed-integrity-failure witness: two catches on 2026-11-07, checkout-wide freeze blocks, the witnessed runs having skipped the existing prose duties the arm makes mechanically enforced); the archive-ceremony gate's finding message gains range-provenance text backed by an internal derivation-row provenance tag (message-visible only); no refusal class is added, no acceptance route changes, nothing is removed.
- The red the primary writer sees today becomes a finding the owning run reports first.
- The gate's two acceptance routes and its refusal semantics stay byte-identical.

## Assumptions

- assume the report arm invokes the existing `gate_archive_ceremony` through a lib-level entry point rather than adding a second evaluation implementation, and evaluates through a pinned hybrid context resolved exactly the way the missing-review-record scan resolves its surfaces: ONLY the reviews corpus re-roots at the primary reviews home (the scan's facts-rooted re-root of reviews_dir at the primary checkout, the lesson-74 arm, because the worktree's transfer-in copy is partial while the acceptance evidence lives in the shared primary home); repo_root, every git surface (the derivation's porcelain and diff reads, the archive-state dirs), and the span evidence stay anchored at the running checkout, with span evidence being the owning run's own bound run manifest, which the entry point takes from the finalize's pre-release bound manifest resolution (the `--manifest` input or the resolver selection passed in by the wrapper) as the primary route, falling back to the checkout-local newest-marker re-derivation only when no manifest was bound (a post-release re-derivation races a peer setup that acquires the just-freed lock and flips the newest marker): basis: the manifest loader root-matches every record to one checkout by contract (a manifest from another checkout of the same repo is never this run's record), so a primary-rooted span load can never return the owning manifest; the scan itself is the in-file mixed-context precedent (it re-roots only reviews_dir and keeps tracked surfaces local), and the wrapper suite's per-checkout manifest staging pins the same shape.
- assume the wiring boundary is pinned, not derived at execution: the arm wires at the `cmd_finalize` tail of `scripts/done_run.sh`, into the closeout-side report step beside the missing-review-record scan, after the done-lock and merge-lock releases, and that is the only boundary this plan wires; the landing reconcile tail is excluded as structurally pre-rider (it runs inside `scripts/land_squash.sh`'s merge-lock critical section at or before the landing commit, whereas both witnessed riders are separate commits after their run's landings), and the completion-pass rider step stays prose in the skills, outside this plan's Files: basis: the witnessed riders both postdate their landings (fef5ebd2a after cdfa34626; 8cdc8ef65 after 6b97eb59b), and at a finalize-tail boundary the owning manifest is already bound so the run manifest span includes the landing commit and the post-landing rider.
- assume warning-only first with the promotion criteria pre-registered in the machinery registry: basis: the origin row's machinery-admission constraint (each arm lands warning-only or message-only first) and the repository guidelines' machinery admission protocol.
- assume the stale-manifest arm (row arm 4) needs no build: basis: two grounds, both on record: the done setup classification's own remedy set names the finalize-manifest operation for an unadopted current-boundary manifest (exercised 2026-11-07 to disposition a wedged peer boundary while unblocking this plan's own freeze write), and the widening self-heals when a newer content-confirmed run-start marker shifts the derivation window (the origin row's second-witness evidence records exactly that retirement without any repair).
- assume the producer write-time check arm (row arm 2) is deferred, not dropped: basis: the entry's scope arm prices a single ordering change, and the producer surface (`scripts/produce_exec_review_record.py`) is a distinct admission with its own warning-only landing; the origin row keeps it priced.

Decision points requiring a grill: none remain (the report-arm posture, the pinned wiring boundary and hybrid evaluation context, the registry pre-registration, the stale-manifest no-build outcome, and the producer-arm deferral are resolved by the origin row's Suggested correction arms and machinery-admission constraint, the repository guidelines' machinery admission protocol, the exercised finalize-manifest duty, and the scan's in-file mixed-context precedent, under the maintenance-selected standing authorization).

## Standing constraints

- The gate stays acceptance-identical: no route narrowing, no new acceptance condition, no known-red ledger, no authoring-lane blocker (the origin row's own constraint); the only gate-code changes this plan makes are the Task 2 lib-level entry point (which carries no acceptance logic; span-boundary resolution and could-not-evaluate reporting are context work, not acceptance logic, and no bash code string-matches the gate's note text) and the Task 4 provenance tag and message text; the acceptance routes and verdict semantics stay byte-identical.
- The arm is warning-only in this plan's landing: it reports findings and never refuses; the machinery registry row this plan touches carries the promotion criteria (a true catch produced by the arm's own re-sweep output, with the repair witnessing it), the false-catch ledger duty (each reported finding that the primary writer's sweep would not have produced is recorded with its witness, in the registry row's note; the row is the ledger's recording home), the demotion-pairing and operator-approval requirements, and the review date 2026-12-07.
- The arm runs after the done-lock and merge-lock releases and is fail-open: any arm failure emits a distinct could-not-evaluate warning on the failure channel (the neighboring scan's posture), never a pass-shaped or bare-clean line, never mutating the finalize exit code; every finding line and the always-present evaluation summary line are stamped with the evaluated commit and evaluation time so a later-green re-check is decidable.
- The existing missing-review-record scan stays as-is; the report arm never replaces or re-scopes it; the entry point is the owning home of the pinned-context resolution, and the scan's inline worktree-list primary selection plus facts-rooted reviews re-root is a deliberate byte-frozen twin of that resolution (a future scan edit must re-derive the parity, never drift it silently).
- No second gate: the arm reuses the gate invocation; no new script file is created.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm reports every archive-ceremony red reachable within the owning run's own run manifest span under the pinned hybrid evaluation context (the reviews corpus re-rooted at the primary reviews home; the span anchored at the running checkout's own manifest), verified by the characterization checks replaying the witnessed shape
- minimality: the gate's acceptance-route helpers and refusal semantics are unchanged outside the Task 2 entry point and the Task 4 provenance tag and message text; the arm adds one invocation, not an evaluation implementation
- maintainability: the machinery registry row carries the admission fields and promotion criteria so the warning-only posture is discoverable

**Done when:**
- the characterization checks pass: the replayed incident shape reports the finding at the owning closeout; the primary-only-record, foreign-manifest, and could-not-evaluate shapes report their pinned outcomes; a bound-record archive reports clean; no finding produces a refusal
- the finding message states the range provenance, proven two-sided (this run's manifest span and a prior run)
- the machinery registry row records the arm's warning-only posture, admission fields, promotion criteria, and review date

**Ship when:**
- none; every condition is repository-verifiable in this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 2)
- `scripts/done_sweep_gates_lib.py` (Task 4)
- `scripts/done_run.sh` (Task 2)
- `scripts/machinery_registry.json` (Task 3) *(new row entry in the existing registry)*

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_done_run_wrapper.py` (Task 2)
- `scripts/test_machinery_inventory.py` (Task 3)
- `scripts/test_done_sweep_gates_lib.py` (Task 2)
- `scripts/test_done_sweep_gates_lib.py` (Task 4)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/produce_exec_review_record.py`, `scripts/machinery_inventory.py`, and `scripts/maintenance_fire_outcomes.py`; reason: all three are quoted commands and pointers in the task items (the repair producer, the registry battery, and the known pre-existing regrowth), never edited by any task, so no Files declaration is claimed for them; the row's arm 2 (producer write-time checks) is deferred and stays priced by the origin row
- `scripts/land_squash.sh`; reason: the landing reconcile tail is excluded as a wiring boundary (structurally pre-rider) and the landing helper is otherwise untouched
- the rolling prompt logs and their prune and freeze duties; reason: the row's recovery section already disposed the live red, and rolling-log governance is owned by its existing duties

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_done_sweep_gates_lib.py scripts/test_machinery_inventory.py -q
python3 scripts/machinery_inventory.py --check
```

## Tasks

### Task 1: Characterize the ordering gap in the closeout harness suites

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] Characterization check, gap closed: given a completed run whose landing span carries an archived plan whose only execution-round record is code-review-kind (no `-plan-review-` infix, no binding sidecar), expects the owning closeout's post-landing archive-ceremony evaluation reports the finding in the run's completion output instead of silence [class: REPOSITORY_TEST]
- [x] Characterization check, gap-closed harness: the gap-closed, pinned-context, span-anchored, and could-not-evaluate witnesses are all written against the wrapper suite's bash finalize harness (`FixtureMixin.run_finalize`), patterned on the missing-review-record scan witnesses; the clean-archive control rides the same harness as its green-from-birth layer [class: REPOSITORY_TEST]
- [x] Characterization check, pinned context: given an archive whose accepting record exists only in the primary reviews home (absent from the worktree's transfer-in copy), expects the evaluation under the pinned hybrid context observes it, and the always-present evaluation summary line names the resolved reviews root (the primary home) with a clean outcome for that archive; the check fails for a worktree-rooted corpus evaluation [class: REPOSITORY_TEST]
- [x] Characterization check, span anchored at the owning checkout: given the owning run manifest present only in the owning checkout's session dir and the primary session dir holding a newer foreign manifest (the required fixture shape; an empty primary session dir is an optional additional control, never a substitute), expects the evaluation's run manifest span still comes from the owning run's manifest (the finding reports) and the foreign manifest never becomes the span base [class: REPOSITORY_TEST]
- [x] Characterization check, could-not-evaluate: given neither the owning run manifest nor ORIG_HEAD resolves as the span boundary and a red committed archive is present, expects a distinct could-not-evaluate report, never a pass-shaped clean line [class: REPOSITORY_TEST]
- [x] Characterization check, blocker-class posture: given a fixture driving a derivation blocker (an unreadable plan-deliverables file beside a red committed archive), expects the could-not-evaluate posture line and no archive-finding line naming the reconstruction producer for it [class: REPOSITORY_TEST]
- [x] Characterization check, clean archive: given an archive whose execution evidence satisfies either acceptance route (a `-plan-review-<slug>-exec-r<N>` filename-series record, or a binding receipt whose sidecar carries the plan identity, the reviewed-bytes digest, and a yes verdict), expects the evaluation reports no finding; a negative control expected green from birth (it guards against false positives, not against the gap) [class: REPOSITORY_TEST]
- [x] Run → expect RED: the gap-closed, pinned-context, span-anchored, and could-not-evaluate witnesses fail on the current digest because no post-landing evaluation arm exists; the clean-archive witness is expected green from birth (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [x] Commit: `test: characterize the archive-rider sweep-ordering gap (red)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Wire the post-landing archive-ceremony report arm into the owning closeout

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`
- `cmd_finalize` in `scripts/done_run.sh`

- [x] The owning closeout delivers the post-landing archive-ceremony report arm wired into the closeout-side report step at the `cmd_finalize` tail, beside the missing-review-record scan, after the done-lock and merge-lock releases [class: IMPLEMENTATION_REQUIRED]
- [x] Arm behavior: given an archive surface landed by the run (absorbed in the squash landing or committed as a post-landing rider), expects the arm re-runs the archive-ceremony gate through a lib-level entry point under the pinned hybrid context when archive surfaces changed in the run's span [class: IMPLEMENTATION_REQUIRED]
- [x] Arm context: the pinned hybrid context re-roots only the reviews corpus at the primary reviews home (repo_root, git surfaces, and the run manifest span anchored at the running checkout; span evidence resolved pre-release from the finalize's bound manifest resolution passed in by the wrapper as the primary route, the newest-marker re-derivation fallback-only when no manifest was bound, never re-derived post-release because that races a peer setup flipping the newest marker) [class: IMPLEMENTATION_REQUIRED]
- [x] Arm summary: the arm emits an always-present evaluation summary line (evaluated commit, evaluation time, resolved reviews root) plus the finding [class: IMPLEMENTATION_REQUIRED]
- [x] Span-boundary classification: the entry point resolves the span boundary itself and classifies an unresolvable boundary (neither the owning run manifest nor ORIG_HEAD resolves) into a distinct could-not-evaluate result reported like a finding, without string-matching the gate's note text; no bash code classifies the boundary [class: IMPLEMENTATION_REQUIRED]
- [x] Blocker-class posture: a gate result whose message carries no surfaced archive (a derivation blocker) is classified into the same could-not-evaluate posture, never into the archive-finding line [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, warning-only: given the evaluation finding a red archive, expects the finalize boundary completes with exit 0, the finding reported (never refused), and the finding line (the arm's own report line in done_run.sh, not a gate-message change) naming the archive path, the failing acceptance route, the repair producer (`scripts/produce_exec_review_record.py` reconstruction path), and the evaluated commit and evaluation time [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, arm failure posture: given the arm itself failing (facts resolution, gate exception), expects a distinct could-not-evaluate warning on the failure channel (the neighboring scan's fail-open guard posture), never a pass-shaped or bare-clean line, no finalize exit-code mutation, and the boundary completes [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness, no false report: given a closeout whose archive surfaces all pass the gate, expects the completion output carries no archive-ceremony finding (the always-present summary line is not a finding) and the arm adds no refusal path [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 characterization checks pass [class: REPOSITORY_TEST]
- [x] Commit: `feat: own-closeout archive-ceremony report arm closes the archive-rider sweep-ordering gap` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Record the admission row and run the registry battery

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] The machinery registry row (`scripts/machinery_registry.json`) records the arm's warning-only posture, the concrete incident link (the origin row's durable home per the citation rule: the docs/history/backlog/completed/ twin when one exists at landing time, otherwise this covering plan's docs/history/plans/completed/ twin once this plan archives; the incident is the two catches on 2026-11-07), the expected catch frequency, and the review date 2026-12-07 [class: IMPLEMENTATION_REQUIRED]
- [x] The registry row also records the false-positive cost (a spurious report line at the owning closeout; report-only), the promotion criteria (a true catch produced by the arm's own re-sweep output with the repair witnessing it, plus demotion pairing and operator approval), and the false-catch ledger duty [class: IMPLEMENTATION_REQUIRED]
- [x] Registry-content witness: a focused battery check asserts the new row's note carries the named admission fields (incident link, catch frequency, false-positive cost, promotion criteria, false-catch ledger duty, review date), expected GREEN, so the battery distinguishes the prescribed row from a structural-only row [class: REPOSITORY_TEST]
- [x] Registry battery: `python3 scripts/machinery_inventory.py --check` reports no failure attributable to the row this plan adds; any other reported failure (today the known pre-existing unregistered `scripts/maintenance_fire_outcomes.py` regrowth from the unrelated 2026-11-06 landing) is triaged against its own priced route and never absorbed into this plan's commits [class: REPOSITORY_TEST]
- [x] Commit: `feat: record the archive-rider report arm admission row in the machinery registry` [class: IMPLEMENTATION_REQUIRED]

### Task 4: State range provenance in the archive-ceremony finding message

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `gate_archive_ceremony` in `scripts/done_sweep_gates_lib.py`

- [x] The gate tags its derivation rows with the range-provenance class and the finding message states whether the surfaced archive came from this run's manifest span or a prior run: given the replayed incident shape (a this-run committed archive), expects the message names the this-run class; given a prior-run archive, expects the message names the prior-run class [class: IMPLEMENTATION_REQUIRED]
- [x] The prior-run fixture is a red variant of the stale-deliverables twin (the twin shape with no binding record), so the prior-run class surfaces on a finding message the assertion can pin [class: REPOSITORY_TEST]
- [x] The provenance tag is an internal derivation-row extension that changes no acceptance route and no verdict semantics [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 checks plus the two-sided message-shape checks selected at execution from repository evidence (the gate-level checks live in the gates-lib suite, where `run_gate` returns the message) [class: REPOSITORY_TEST]
- [x] Commit: `feat: archive-ceremony finding message names range provenance` [class: IMPLEMENTATION_REQUIRED]
