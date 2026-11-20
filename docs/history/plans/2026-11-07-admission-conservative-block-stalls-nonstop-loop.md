# Plan: admission conservative block stalls nonstop loop

Backlog origin: docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-admission-conservative-block-stalls-nonstop-loop-p48ac8271-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1h
Executed: no
Authoring claim: 2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (session sess_edd477e1-e097-4cbc-a973-7ace838d677c)

## Terms

- admission consult: the target-disjointness dispatch gate `scripts/dispatch_admission.py` (`check_admission`), invoked by the maintenance loop before any new child dispatch.
- conservative verdict: the consult's fail-closed outcome for an outstanding run whose owned paths cannot be derived; treated as intersecting.
- manifest-less outstanding run: a mid-flight peer run with no done-setup manifest.
- done-setup manifest: the per-run record a peer execution mints at done setup (`docs/tmp/done-session/run-manifest-<run-id>.json`), the consult's outstanding-side evidence source today.
- covering-plan composition: the caller-side derivation of an outstanding exec run's owned paths from its covering plan's Files lists via the `owned_paths_from_plan` function (`scripts/dispatch_admission.py:147`), written as a synthetic consult-input manifest.
- claim surface: the peer's live execution claim file under the resolved tmp directory's `execution-claims/` (for example `docs/tmp/execution-claims/<plan-slug>.md`), the run's live witness.
- lanes: the maintenance loop's execution (exec), authoring (auth), and audit/re-triage dispatch lanes.
- in-session continuation: the D-6/D-17 autopilot duty to continue lane work in-session instead of stopping at a dispatch boundary; D-6's in-session-only wording is superseded by D-17 (operator-directives home), and both ids gloss the same standing nonstop direction.
- turn record: the scheduler state file's decision channels (`decision`, `decision_reason`, notes) a deciding turn writes.
- recovery exception: the sanctioned dispatch-admission exception for the deadlock case, bounded mechanically to admission-machinery-owned candidates.
- provably-disjoint in-session leg: an in-session continuation whose output surfaces are disjoint from every outstanding run's derived owned paths.
- recovery plan: `docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md`, the durable claim-keyed fix this plan is interim to.

## Why

The dispatch-admission consult's conservative verdict is global and lane-blind: one peer exec run without a done-setup manifest blocks every dispatch of both work lanes and the audit lane, and the fix vehicle itself cannot dispatch, so the loop stalls for as long as the peer runs. The nonstop mandate (D-6/D-17) is defeated by missing evidence that the caller can derive itself.

## Gist & Examples

TLDR: a caller-side consult convention plus scoped skill text lets dispatches and in-session lane work proceed while a manifest-less peer run is outstanding; why: efficiency, ending the witnessed all-day lane stall.

Before: 2026-11-07, two live peer exec runs, one without a done-setup manifest; the consult REFUSED globally (`OUTCOME: fail`); the exec lane, authoring lane, and the overdue audit dispatch all stood down with quota at 26 percent and fifteen ready unclaimed plans (scheduler-state census snapshot 2026-11-07T18:06Z); the recovery plan itself undeliverable under the same verdict.

After: the deciding turn composes the manifest-less exec run's owned paths from its covering plan and consults on real evidence; a run whose covering plan cannot be resolved still takes the conservative verdict; an in-session continuation whose outputs are provably disjoint runs without the consult; an audit-kind dispatch supplies its candidate owned paths from its declared write surface; the recovery plan's own execution is admitted through the recovery exception with the exception recorded in the turn record.

## Outcome

The maintenance loop keeps running its lanes while peers are mid-flight, and the conservative verdict keeps protecting only genuinely unresolvable ownership.

- A manifest-less exec-lane outstanding run with a resolvable covering plan consults on derived evidence instead of the conservative verdict.
- In-session lane work with provably disjoint outputs is never held by the consult.
- The deadlock case (executing the recovery plan itself) has a sanctioned, recorded, mechanically bounded admission path.

Gate delta: narrowing-shaped: no new gate, validator, lock, ledger, or schema field; four arms are added to existing skill text (three interim-narrowing arms: covering-plan composition, lane scoping, audit-kind derivation; plus the recorded recovery-exception arm; the composition and recovery-exception arms are interim-deleted at the recovery plan's landing); the conservative verdict's scope shrinks to the unresolvable residual (exec runs whose covering plan cannot resolve, plus non-exec manifest-less runs the exec-scoped interim arm cannot derive, the same residual the recovery plan keeps); the mirrored conservative sentences in `decisions.md` and `scheduling.md` are rewritten in place (replaced wording, not parallel arms), the growth paid by the in-place rewrites and the recorded removal duty on the origin row; no registry row added, removed, or re-classed, the entry-39 admission note rewritten in place.

## Assumptions

- assume caller-side composition with no `scripts/dispatch_admission.py` edit; basis: the origin's Ask (1) scopes "no gate edit" and names the existing `--outstanding-with-manifest` arm and a documented read-only composition as the mechanism (docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md)
- assume the consult contract's restatement homes are `agents/skills/maintenance/decisions.md` (D1 landing gate, D2 mirror), `agents/skills/maintenance/scheduling.md` (Step 5 final-slot precondition and the in-session second-leg bullet), the `survey-arms.md` parked-discharge validation arm, and the machinery registry admission note; `state-file.md` carries no dispatch-admission consult restatement (its consult words name the registry consult's park arbitration, the dedup rolling ledger, and the continue-loop quota-pause consult; verified); the tasks rewrite every restated sentence to the same arms in the same commits
- assume the plan is interim; basis: the origin Ask's closing "The sibling row owns the full claim-keyed recovery plan execution; this row owns the loop-liveness scope" (docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md)
- assume the off-plan-edit under-inclusion of the composed set is the accepted interim residual: the composed set is a floor derived fresh at each consult; a peer's off-plan worktree edits are unrepresented until the recovery plan's monotone record lands, which bounds the residual's lifetime to the recovery landing
- assume the lane-scoping arm is new skill text rather than an extension of guards.md's user-directed-override or the raced-pick continuation rule; basis: the origin Ask (2) names the per-lane scoping rule as consult-clause skill text, and the override rule is operator-directed while the raced-pick rule is authoring-pick-scoped
- assume the composition home is `<resolved tmp_dir>/admission-compositions/`; basis: the skill's facts-resolved tmp_dir configuration key
- assume the audit-kind candidate set derives from the task's declared write surface; basis: the re-triage task body's own write verbs (row moves, Status rewrites, filing) exceed a two-path set

Decision points requiring a grill: none remain; receipts: lane-scoping arm shape recorded above (origin Ask (2), guards override operator-directed, 2026-11-07, Task 2); composition write home recorded above (facts tmp_dir key, 2026-11-07, Task 1); audit-kind derivation inputs recorded above (task body write verbs, 2026-11-07, Task 2).

## Standing constraints

- The conservative verdict for a genuinely unresolvable outstanding run stays fail-closed byte-unchanged in behavior.
- Peer-session state is never touched; the composition reads only the peer's live claim surface and the covering plan in this repository's tree.
- The recovery plan's mechanism remains the durable fix; this plan's text names itself interim and must not contradict that plan's design, including its residual semantics (its source-less residual keeps the conservative verdict where the recovery plan keeps it, and the composition arm is scoped to exec-lane runs only).
- Operative-text growth mirrors in place: each restated conservative sentence is rewritten, not appended beside; the interim arms are deleted at the recovery landing.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the composition derives the same owned-path set the `owned_paths_from_plan` function returns for the covering plan; an unresolvable run (covering plan absent, unreadable, empty derivation, or claim/entry mismatch) still takes the conservative verdict
- loop liveness: the witnessed stall class (manifest-less exec peer, resolvable covering plan, disjoint candidate) no longer blocks dispatch or in-session continuation work
- maintainability: the three arms live in one consult clause with every restated reader sentence rewritten to the same arms; no diverging consult authority remains

**Done when:**
- the four arms are landed in the consult clause and every mirrored conservative sentence in `decisions.md` and `scheduling.md`, the survey-arms.md parked-discharge pointer, and the machinery registry admission note are rewritten to the same arms
- the pins suite shows no new PIN FAIL versus the pre-edit baseline (the unrelated prompt-log pin fails pre-existing on both surfaces and is not this plan's to fix)
- an executed probe over the witnessed 2026-11-07 inputs records the peer run id and covering-plan path in the origin row beside the observed `OUTCOME:` lines (run ids recoverable from the sibling row; covering plan from the claim filename's plan slug), showing the REFUSED shape converting to an evidence-based verdict through the convention

**Ship when:**
- the recovery plan executes; its landing deletes the interim composition and recovery-exception arms and re-derives the lane-scoping and audit-kind arms against the record operand (the per-arm disposition is recorded on this plan's origin row)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Task 1) *(existing, consult clause)*
- `agents/skills/maintenance/SKILL.md` (Task 2) *(existing, consult clause)*
- `agents/skills/maintenance/SKILL.md` (Task 3) *(existing, consult clause)*
- `agents/skills/maintenance/decisions.md` (Task 1) *(existing, D1/D2 restated sentences)*
- `agents/skills/maintenance/decisions.md` (Task 2) *(existing, D1/D2 restated sentences)*
- `agents/skills/maintenance/decisions.md` (Task 3) *(existing, D1/D2 restated sentences)*
- `agents/skills/maintenance/scheduling.md` (Task 2) *(existing, Step 5 + second-leg sentences)*

**Tests:**
- `scripts/check_maintenance_pins.sh` (Task 1) *(existing; new arm pins)*
- `scripts/test_dispatch_admission.py` (Task 1) *(existing; composition-input cases)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:**
- `docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md` (Task 1, Task 3) *(existing origin row; probe receipts and per-arm dispositions)*
- `agents/skills/maintenance/survey-arms.md` (Task 2) *(existing; parked-discharge consult pointer)*
- `scripts/machinery_registry.json` (Task 2) *(existing; admission note wording)*

**Out of scope; reject unless plan-related:**
- `scripts/dispatch_admission.py`; reason: the gate's logic is deliberately untouched (origin Ask (1)); a finding here routes to the recovery plan
- `docs/maintenance/operator-directives.md`; reason: the directives home is operator-owned; D-6/D-17 text is not edited by this plan

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_dispatch_admission.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
```

### Task 1: covering-plan composition convention across the consult clause and its restatements

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/test_dispatch_admission.py`

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [ ] The consult clause gains the composition arm: given a manifest-less exec-lane outstanding run, the deciding turn resolves its covering plan through the peer's live claim surface, derives owned paths via the `owned_paths_from_plan` function, and writes a synthetic consult-input manifest at `<resolved tmp_dir>/admission-compositions/<run-id>.json` through an atomic temp-plus-replace write, recording the covering-plan path and derivation time [class: IMPLEMENTATION_REQUIRED]
- [ ] The composed manifest feeds the existing `--outstanding-with-manifest` arm; the composition is derived fresh at every consult, never reuses a pre-existing file, and is deleted after the verdict is recorded; the run id is validated as a bare filename component [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given an exec run whose covering plan cannot be resolved (absent from the plans root), expects the turn to pass `--outstanding-without-manifest` and record the conservative verdict [class: REPOSITORY_TEST]
- [ ] Safety witness: given a derivation ToolError (unreadable plan, or a readable plan with no parseable Files lists) or a claim/entry mismatch, expects no composed manifest and the conservative verdict [class: REPOSITORY_TEST]
- [ ] The clause records the composed set as a floor: the verdict proves disjointness only against the covering plan's declared Files lists, off-plan peer edits stay unrepresented, and the arm is interim, deleted at the recovery plan's landing [class: IMPLEMENTATION_REQUIRED]
- [ ] The D1 landing-gate and D2-mirror conservative sentences in `decisions.md` are rewritten in place to the same composition arm [class: IMPLEMENTATION_REQUIRED]
- [ ] New pin rows over each arm's distinctive span land in `scripts/check_maintenance_pins.sh` in the same edit; composition-input cases (derived-set verdict, conservative fallback, composed intersect REFUSED) land in `scripts/test_dispatch_admission.py` with fixtures in the suite's tmp_path idiom [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new pins fail before the consult-clause edit [class: REPOSITORY_TEST]
- [ ] Executed probe: run the `owned_paths_from_plan` derivation over the witnessed covering plan, invoke the consult through the convention, and record the peer run id, covering-plan path, and observed `OUTCOME:` lines in the origin row [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN on the new pins and the composition cases [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: consult convention derives manifest-less exec-run owned paths from the covering plan` [class: IMPLEMENTATION_REQUIRED]

### Task 2: lane scoping, audit-kind derivation, and restatement rewrites

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/survey-arms.md`
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh`
- `scripts/test_dispatch_admission.py`

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [ ] The clause gains the lane-scoping arm: given an in-session continuation whose output surfaces are disjoint from every outstanding run's derived owned paths, the leg proceeds without a consult invocation and records the disjointness in the turn record; where an outstanding run's derivation is unresolvable, the leg records an advisory disjointness note and proceeds, while a child dispatch in the same state still takes the conservative verdict [class: IMPLEMENTATION_REQUIRED]
- [ ] The clause gains the audit-kind derivation arm: given an audit-kind or re-triage-kind registry dispatch, the deciding turn passes the candidate's owned paths via the existing repeatable `--owned-path` arm, derived from the task's declared write surface (task file, state record, plus the sweep or filing targets the task body names) [class: IMPLEMENTATION_REQUIRED]
- [ ] The scheduling.md Step 5 final-slot sentence and the in-session second-leg consult mention, the survey-arms.md parked-discharge consult pointer, and the machinery registry admission note are rewritten in place to resolve through the consult clause's arms [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given an audit-kind dispatch whose derived owned paths intersect an outstanding run's set, expects the consult REFUSED verdict and the D-5 retention unchanged [class: REPOSITORY_TEST]
- [ ] Safety witness: given a re-triage-kind dispatch whose declared write surface includes deferred-corpus row paths an outstanding run owns, expects REFUSED on the derived set [class: REPOSITORY_TEST]
- [ ] New pin rows over the lane-scoping, audit-kind, and restatement-rewrite spans land in `scripts/check_maintenance_pins.sh` in the same edit; the two intersect-refusal witnesses land as pytest cases in `scripts/test_dispatch_admission.py` (tmp_path idiom) [class: REPOSITORY_TEST]
- [ ] Run → expect no new PIN FAIL versus the pre-edit baseline and GREEN on this task's new pins and pytest cases [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: consult lane scoping and audit-kind derivation with restatement rewrites` [class: IMPLEMENTATION_REQUIRED]

### Task 3: mechanically bounded recovery-exception arm for the fix-vehicle deadlock

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/scheduling.md`
- `scripts/test_dispatch_admission.py`
- `docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md`

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [ ] The clause gains the recovery-exception arm: given a candidate whose covering plan is the recovery plan and an outstanding manifest-less run, the turn may dispatch despite the conservative refusal only when the candidate's `owned_paths_from_plan` derivation is a subset of the recovery plan's own Files-derived set, with both derived sets recorded in the turn record beside the refusal receipt [class: IMPLEMENTATION_REQUIRED]
- [ ] The D1 landing-gate sentence in `decisions.md` and the scheduling.md Step 5 final-slot sentence are rewritten in the same commit to carry the exception (the conservative verdict resolves to D3 except the recorded recovery-exception arm, exercised with both derived sets recorded beside the refusal receipt); D2 stays unexceptioned (exec-lane bounded) [class: IMPLEMENTATION_REQUIRED]
- [ ] The non-subset witness lands as a pytest case in `scripts/test_dispatch_admission.py` (tmp_path idiom) [class: REPOSITORY_TEST]
- [ ] The exception arm is interim: it is deleted in the same change that lands the recovery plan's record operand [class: IMPLEMENTATION_REQUIRED]
- [ ] The origin row records the per-arm disposition: composition arm removed at recovery landing; lane-scoping and audit-kind arms kept, re-derived against the record operand; recovery-exception arm removed at recovery landing; the composition-arm and recovery-exception pin rows are removed in the same recovery-landing change as their arms [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a candidate whose derived owned paths are not a subset of the recovery plan's set, expects no exception path and the existing deferral to stand [class: REPOSITORY_TEST]
- [ ] Run → expect no new PIN FAIL versus the pre-edit baseline and GREEN on this task's pytest case [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: mechanically bounded recovery exception for the admission deadlock case` [class: IMPLEMENTATION_REQUIRED]
